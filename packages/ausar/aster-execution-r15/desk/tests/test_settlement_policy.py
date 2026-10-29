"""Dated independent-calendar witnesses and isolated policy-aware paper ledgers."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from backend.providers import exchange_calendar
from backend.settlement_calendar import settlement_terms, is_settlement_day, SettlementCalendarError, POLICY_VERSION
from backend.store import DeskError, Store
from backend.trading import TradingDesk

UTC = timezone.utc
FIXTURES = Path(__file__).resolve().parent / "fixtures"


class CalendarCases(unittest.TestCase):
    def test_hand_authored_external_dated_witnesses(self):
        rows = json.loads((FIXTURES / "settlement-expected-v2.json").read_text())
        for row in rows["normal_cases"]:
            with self.subTest(row=row["id"]):
                terms = settlement_terms(datetime.fromisoformat(row["sale_clock"]))
                self.assertEqual(terms["economic_settlement_date"], row["economic_maturity"])
                self.assertEqual(terms["settlement_cycle_business_days"], row["cycle_sessions"])
                self.assertEqual(terms["cash_release_at"], row["paper_release_at"])
                self.assertFalse(terms["actual_broker_settlement_or_cash_observed"])
        for row in rows["fail_closed_cases"]:
            with self.subTest(row=row["id"]), self.assertRaises(SettlementCalendarError):
                settlement_terms(datetime.fromisoformat(row["sale_clock"]))

    def test_processing_days_are_not_a_generic_employee_or_exchange_calendar(self):
        self.assertTrue(is_settlement_day(datetime(2023, 11, 10).date()))
        self.assertTrue(is_settlement_day(datetime(2025, 1, 9).date()))
        self.assertFalse(is_settlement_day(datetime(2026, 7, 3).date()))
        self.assertFalse(is_settlement_day(datetime(2024, 3, 29).date()))
        self.assertFalse(is_settlement_day(datetime(2026, 10, 12).date()))


class Providers:
    broker = None
    def calendar(self, clock=None): return exchange_calendar(clock)


class LedgerCases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "isolated.sqlite"
        self.clock = datetime(2026, 10, 9, 19, tzinfo=UTC)
        self.store = Store(self.path)
        self.trading = TradingDesk(self.store)
        self.book = self.trading.create_book({"name": "settlement isolated", "kind": "forward", "broker": "local"})["id"]
        self.owner = "settlement-fixture"
        self.trading.fund_book(self.book, 100, "fixture-capital")
        self.trading.claim_strategy_book(self.book, self.owner)

    def quote(self, clock):
        with self.store.transaction() as con:
            con.execute("INSERT OR REPLACE INTO quotes VALUES('AAPL','10',?,'synthetic settlement quote')", (clock.isoformat(),))

    def order(self, side, key, quantity=10):
        return self.trading.submit_strategy_intent({"book_id": self.book, "symbol": "AAPL", "side": side, "quantity": quantity, "client_id": key, "order_type": "market", "time_in_force": "gtc"}, self.owner, clock=self.clock)

    def sale(self, quantities=(10,)):
        self.quote(self.clock)
        self.order("buy", "buy")
        self.assertEqual(self.trading.process(Providers(), self.clock)["fills"], 1)
        for i, quantity in enumerate(quantities):
            self.order("sell", "sell"+str(i), quantity)
            self.assertEqual(self.trading.process(Providers(), self.clock)["fills"], 1)

    def rows(self, table):
        with self.store.connect() as con: return [dict(r) for r in con.execute("SELECT * FROM "+table)]

    def cash(self, clock, release=True):
        context = self.store.transaction if release else self.store.connect
        with context() as con: return self.trading.strategy_cash(con, self.book, clock, release=release)

    def test_october_boundary_holds_cash_and_new_policy_survives_restart(self):
        self.sale()
        row = self.rows("a_strategy_settlements")[0]
        self.assertEqual(row["release_at"], "2026-10-13T13:30:00+00:00")
        receipt = self.rows("a_strategy_settlement_policy_receipts")[0]
        self.assertEqual(receipt["policy_version"], POLICY_VERSION)
        self.assertEqual(json.loads(receipt["definition"])["economic_settlement_date"], "2026-10-13")
        monday = datetime(2026, 10, 12, 13, 30, tzinfo=UTC)
        self.assertEqual(self.cash(monday, release=False)["available_cents"], 0)
        self.assertIsNone(self.rows("a_strategy_settlements")[0]["released_at"])
        self.clock = monday
        self.quote(monday)
        with self.assertRaises(DeskError): self.order("buy", "premature")
        self.trading = TradingDesk(Store(self.path))
        self.assertEqual(self.cash(monday)["available_cents"], 0)
        self.assertEqual(self.trading.reconcile(Providers(), monday)["errors"], [])
        tuesday = datetime(2026, 10, 13, 13, 30, tzinfo=UTC)
        self.assertEqual(self.cash(tuesday)["available_cents"], 10000)
        self.assertEqual(self.rows("a_strategy_settlements")[0]["released_at"], tuesday.isoformat())

    def test_unknown_policy_validated_before_any_release_mutation(self):
        self.sale((5, 5))
        before = self.rows("a_strategy_settlements")
        with self.store.transaction() as con:
            con.execute("UPDATE a_strategy_settlement_policy_receipts SET policy_version='unsupported' WHERE fill_id=?", (before[-1]["fill_id"],))
        tuesday = datetime(2026, 10, 13, 14, tzinfo=UTC)
        with self.assertRaises(DeskError): self.cash(tuesday)
        self.assertEqual(self.rows("a_strategy_settlements"), before)
        self.assertTrue(self.trading.reconcile(Providers(), tuesday)["errors"])

    def test_policy_hash_and_missing_post_rollout_receipt_fail_closed(self):
        self.sale()
        receipts = self.rows("a_strategy_settlement_policy_receipts")
        with self.store.transaction() as con:
            con.execute("UPDATE a_strategy_settlement_policy_receipts SET definition_sha256='bad'")
        with self.assertRaises(DeskError): self.cash(self.clock)
        with self.store.transaction() as con:
            con.execute("DELETE FROM a_strategy_settlement_policy_receipts")
        with self.assertRaisesRegex(DeskError, "Post-rollout"):
            self.cash(self.clock)
        self.assertIsNone(self.rows("a_strategy_settlements")[0]["released_at"])

    def test_calendar_failure_cannot_half_commit_owned_sale(self):
        self.quote(self.clock)
        self.order("buy", "buy")
        self.trading.process(Providers(), self.clock)
        self.order("sell", "sell")
        with patch.object(self.trading, "_strategy_settlement_release_at", side_effect=DeskError("calendar fixture unavailable")):
            result = self.trading.process(Providers(), self.clock)
        self.assertTrue(result["errors"])
        self.assertEqual(len(self.rows("p_fills")), 1)
        self.assertEqual(self.rows("a_strategy_settlements"), [])
        self.assertEqual(self.rows("a_strategy_settlement_policy_receipts"), [])
        self.assertEqual(self.rows("p_positions")[0]["quantity"], "10")

    def legacy(self, already_released=False):
        # Create an actual isolated ledger with the retained old operating
        # implementation, then load the new policy without rewriting rows.
        path = Path(self.tmp.name) / "actual-legacy-fixture.sqlite"
        source = FIXTURES / "trading-before-settlement-v2.py"
        spec = importlib.util.spec_from_file_location("backend.r15_legacy_trading_fixture", source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.path, self.store = path, Store(path)
        self.trading = module.TradingDesk(self.store)
        self.book = self.trading.create_book({"name": "retained legacy implementation", "kind": "forward", "broker": "local"})["id"]
        self.trading.fund_book(self.book, 100, "legacy-fixture-capital")
        self.trading.claim_strategy_book(self.book, self.owner)
        self.sale()
        if already_released:
            self.cash(datetime(2026, 10, 12, 13, 30, tzinfo=UTC))
        before = self.rows("a_strategy_settlements")
        self.trading = TradingDesk(Store(path))
        return before

    def test_legacy_unreleased_early_due_gets_explicit_hold_without_timestamp_rewrite(self):
        before = self.legacy()
        monday = datetime(2026, 10, 12, 13, 30, tzinfo=UTC)
        self.assertEqual(self.cash(monday)["available_cents"], 0)
        self.assertEqual(self.rows("a_strategy_settlements"), before)
        reviews = self.rows("a_strategy_settlement_legacy_reviews")
        self.assertEqual(len(reviews), 1)
        review = json.loads(reviews[0]["definition"])
        self.assertEqual(review["original_release_at"], "2026-10-12T13:30:00+00:00")
        self.assertEqual(review["cash_release_not_before"], "2026-10-13T13:30:00+00:00")
        self.assertFalse(review["legacy_ledger_timestamps_rewritten"])
        self.assertEqual(self.trading.reconcile(Providers(), monday)["errors"], [])
        self.cash(monday)
        self.assertEqual(len(self.rows("a_strategy_settlement_legacy_reviews")), 1)

    def test_legacy_already_early_released_cash_is_withheld_preserving_original_marker(self):
        before = self.legacy(already_released=True)
        monday = datetime(2026, 10, 12, 14, tzinfo=UTC)
        self.assertEqual(self.cash(monday)["available_cents"], 0)
        self.assertEqual(self.rows("a_strategy_settlements"), before)
        self.assertEqual(self.trading.reconcile(Providers(), monday)["errors"], [])
        tuesday = datetime(2026, 10, 13, 13, 30, tzinfo=UTC)
        self.assertEqual(self.cash(tuesday)["available_cents"], 10000)
        self.assertEqual(self.rows("a_strategy_settlements"), before)


if __name__ == "__main__": unittest.main()
