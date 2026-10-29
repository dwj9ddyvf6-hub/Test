import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from backend.store import DeskError, Store
from backend.providers import exchange_calendar
from backend.trading import TradingDesk


UTC = timezone.utc


class FakeBroker:
    def __init__(self):
        self.cash = "1000"
        self.remote_positions = []
        self.remote_orders = []
        self.submits = 0
        self.ambiguous = False
        self.fail_read = False
        self.identity = "PAPER-FIXTURE"
        self.cancels = 0

    def account(self):
        if self.fail_read:
            raise RuntimeError("Read failed")
        return {"cash": self.cash, "equity": self.cash, "account_number": self.identity}

    def positions(self):
        return list(self.remote_positions)

    def orders(self):
        return list(self.remote_orders)

    def get_order(self, client_id):
        return next((r for r in self.remote_orders if r["client_order_id"] == client_id), None)

    def submit(self, intent):
        self.submits += 1
        row = {"id": "broker-" + str(self.submits), "client_order_id": intent["client_id"], "symbol": intent["symbol"], "side": intent["side"], "qty": str(intent["quantity"]), "type": intent["order_type"], "time_in_force": intent["time_in_force"], "status": "accepted", "filled_qty": "0", "filled_avg_price": None, "submitted_at": datetime.now(UTC).isoformat(), "legs": []}
        row.update({field: intent[field] for field in ("limit_price", "stop_price") if intent.get(field) is not None})
        self.remote_orders.append(row)
        if self.ambiguous:
            self.ambiguous = False
            raise TimeoutError("Reply was lost")
        return row

    def cancel(self, order_id):
        self.cancels += 1
        row = next(r for r in self.remote_orders if r["id"] == order_id)
        row["status"] = "canceled"


class FakeProviders:
    def __init__(self, broker=None):
        self.broker = broker
        self.clock = datetime.now(UTC)
        self.open = self.clock - timedelta(hours=1)
        self.close = self.clock + timedelta(hours=6)
        self.is_open = True

    def calendar(self, clock=None):
        return {"is_session": True, "is_open": self.is_open, "session_date": self.open.date().isoformat(), "open_at": self.open.isoformat(), "close_at": self.close.isoformat(), "next_session": (self.open + timedelta(days=1)).date().isoformat(), "next_open_at": (self.open + timedelta(days=1)).isoformat(), "next_close_at": (self.close + timedelta(days=1)).isoformat()}


class TradingTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "paper.sqlite")
        self.trading = TradingDesk(self.store)
        self.providers = FakeProviders()

    def tearDown(self):
        self.temp.cleanup()

    def quote(self, price=10, sym="AAPL", age=0):
        return self.store.ingest_quote(sym, Decimal(str(price)), datetime.now(UTC) - timedelta(seconds=age), "Manual fixture observation")

    def fund(self, amount=1000, book="main", key="fund"):
        return self.trading.fund_book(book, amount, key)

    def intent(self, side="buy", qty=10, key="intent", book="main", **fields):
        return self.trading.submit_intent({"book_id": book, "symbol": "AAPL", "side": side, "quantity": qty, "client_id": key, "order_type": "market", "time_in_force": "gtc", **fields})

    def book(self, rid="main"):
        return next(b for b in self.trading.snapshot()["books"] if b["id"] == rid)

    def order(self, rid):
        return next(i for i in self.trading.snapshot()["intents"] if i["id"] == rid)

    def process(self):
        return self.trading.process(self.providers)

    def test_books_are_independent_empty_and_strategy_free(self):
        s = self.trading.snapshot()
        self.assertEqual(s["books"][0]["account"]["cash"], 0)
        self.assertFalse(s["strategy_extension"]["enabled"])
        self.assertEqual(s["intents"], [])
        forward = self.trading.create_book({"name": "Forward", "kind": "forward", "broker": "local"})
        self.fund(100, book=forward["id"])
        self.assertEqual(self.book()["account"]["cash"], 0)
        self.assertEqual(self.book(forward["id"])["account"]["cash"], 100)
        self.assertEqual(self.store.snapshot({"provider": "local", "configured": False, "model": None})["account"]["cash"], 0)

    def test_funding_identity_and_policy_history(self):
        first = self.fund(100)
        self.assertEqual(self.fund(100), first)
        with self.assertRaises(DeskError):
            self.fund(101)
        initial = self.book()
        updated = self.trading.set_book("main", {"policy": {"allow_short": True, "gross_exposure_cap": 500}})
        self.assertEqual(updated["policy_version"], initial["policy_version"] + 1)
        self.assertNotEqual(updated["policy_hash"], initial["policy_hash"])
        self.assertEqual(len(self.trading.snapshot()["policy_history"]), 2)

    def test_authorized_intent_executes_unattended_without_approval(self):
        self.fund()
        self.quote()
        intent = self.intent()
        self.assertEqual(intent["status"], "queued")
        self.assertEqual(self.book()["account"]["reserved_cash"], 100)
        result = self.process()
        self.assertEqual(result["fills"], 1)
        self.assertEqual(self.order(intent["id"])["status"], "filled")
        self.assertEqual(self.book()["account"]["cash"], 900)
        fill = self.trading.snapshot()["fills"][0]
        self.assertIn("simulation", fill["source"])
        self.assertIsNotNone(fill["quote_as_of"])
        self.assertEqual(self.process()["fills"], 0)

    def test_intent_idempotency_includes_authorization_fields(self):
        self.fund()
        self.quote()
        first = self.intent()
        self.assertEqual(self.intent(), first)
        with self.assertRaises(DeskError):
            self.intent(reason="Changed authorization")
        with self.assertRaises(DeskError):
            self.intent(qty=11)

    def test_concurrent_cash_and_short_exposure_reservations(self):
        self.fund(100)
        self.quote()

        def buy(i):
            try:
                return self.intent(qty=6, key=str(i))
            except DeskError:
                return None

        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(buy, range(6)))
        self.assertEqual(sum(r is not None for r in results), 1)
        self.trading.cancel_intent(next(r for r in results if r)["id"])
        self.trading.set_book("main", {"allow_short": True, "gross_exposure_cap": 150})
        self.intent(side="sell", qty=10, key="short-1")
        with self.assertRaisesRegex(DeskError, "gross exposure"):
            self.intent(side="sell", qty=10, key="short-2")

    def test_halt_blocks_entries_but_services_existing_risk_reduction(self):
        self.fund()
        self.quote()
        self.intent()
        self.process()
        exit_intent = self.intent("sell", 10, "exit")
        self.trading.set_book("main", {"halted": True, "halt_reason": "Operator parked entries"})
        with self.assertRaisesRegex(DeskError, "halted"):
            self.intent(qty=1, key="new")
        self.assertEqual(self.process()["fills"], 1)
        self.assertEqual(self.order(exit_intent["id"])["status"], "filled")

    def test_short_entry_cover_flip_and_realized_pnl(self):
        self.fund()
        self.quote(10)
        with self.assertRaisesRegex(DeskError, "Short"):
            self.intent("sell", 10, "no-short")
        self.trading.set_book("main", {"allow_short": True})
        self.intent("sell", 10, "short")
        self.process()
        self.assertEqual(self.book()["account"]["cash"], 1100)
        self.assertEqual(self.trading.snapshot()["positions"][0]["quantity"], -10)
        self.assertEqual(self.trading.snapshot()["positions"][0]["average_cost"], 10)
        self.quote(8)
        self.intent("buy", 4, "cover")
        self.process()
        self.assertEqual(self.book()["account"]["realized_pnl"], 8)
        self.assertEqual(self.trading.snapshot()["positions"][0]["quantity"], -6)
        self.quote(12)
        self.intent("buy", 8, "flip")
        self.process()
        self.assertEqual(self.book()["account"]["realized_pnl"], -4)
        self.assertEqual(self.trading.snapshot()["positions"][0]["quantity"], 2)
        self.assertEqual(self.trading.snapshot()["positions"][0]["average_cost"], 12)

    def test_explicit_partial_fills_and_fee_once_survive_restart(self):
        self.fund()
        self.quote()
        self.trading.set_book("main", {"fees_per_order": 1, "max_fill_quantity": 4})
        intent = self.intent(qty=10)
        self.process()
        self.assertEqual(self.order(intent["id"])["filled_quantity"], 4)
        self.assertEqual(self.order(intent["id"])["status"], "partially_filled")
        self.trading = TradingDesk(Store(self.store.path))
        self.process()
        self.process()
        self.assertEqual(self.order(intent["id"])["filled_quantity"], 10)
        self.assertEqual(len(self.trading.snapshot()["fills"]), 3)
        self.assertEqual(self.book()["account"]["cash"], 899)
        self.assertEqual(self.book()["account"]["fees"], 1)

    def test_protective_oco_partial_exit_keeps_remaining_protection(self):
        self.fund()
        self.quote(10)
        entry = self.intent(qty=10, take_profit=12, stop_loss=9)
        self.process()
        children = [i for i in self.trading.snapshot()["intents"] if i["parent_id"] == entry["id"]]
        self.assertEqual(len(children), 2)
        self.trading.set_book("main", {"max_fill_quantity": 4, "halted": True})
        self.quote(12)
        self.process()
        children = [i for i in self.trading.snapshot()["intents"] if i["parent_id"] == entry["id"]]
        stop = next(i for i in children if i["order_type"] == "stop")
        self.assertEqual(stop["quantity"], 6)
        self.assertEqual(self.trading.snapshot()["positions"][0]["quantity"], 6)
        self.process()
        self.process()
        self.assertEqual(self.trading.snapshot()["positions"], [])
        self.assertEqual(self.book()["account"]["realized_pnl"], 20)
        children = [i for i in self.trading.snapshot()["intents"] if i["parent_id"] == entry["id"]]
        self.assertEqual({i["status"] for i in children}, {"filled", "cancelled"})

    def test_limit_stop_and_persistent_stop_limit_trigger(self):
        self.fund()
        self.quote(10)
        limit = self.intent(qty=1, key="limit", order_type="limit", limit_price=9)
        self.assertEqual(self.process()["fills"], 0)
        self.quote(9)
        self.process()
        self.assertEqual(self.order(limit["id"])["status"], "filled")
        stop_limit = self.intent(qty=1, key="stoplimit", order_type="stop_limit", stop_price=11, limit_price=11.5)
        self.quote(12)
        self.process()
        self.assertTrue(self.order(stop_limit["id"])["triggered"])
        self.assertEqual(self.order(stop_limit["id"])["filled_quantity"], 0)
        self.quote(10)
        self.process()
        self.assertEqual(self.order(stop_limit["id"])["status"], "filled")

    def test_slippage_never_breaches_explicit_limit(self):
        self.fund()
        self.quote(10)
        self.trading.set_book("main", {"slippage_bps": 100})
        intent = self.intent(qty=1, order_type="limit", limit_price=10)
        self.assertEqual(self.process()["fills"], 0)
        self.quote(9.8)
        self.process()
        self.assertLessEqual(self.trading.snapshot()["fills"][0]["price"], 10)
        self.assertEqual(self.order(intent["id"])["status"], "filled")

    def test_expiry_and_auction_missed_window_do_not_replay(self):
        self.fund()
        self.quote()
        expired = self.intent(key="expired", expires_at=(datetime.now(UTC) - timedelta(seconds=1)).isoformat())
        self.process()
        self.assertEqual(self.order(expired["id"])["status"], "expired")
        self.providers.open = datetime.now(UTC) - timedelta(minutes=2)
        auction = self.intent(key="auction", time_in_force="opg")
        self.process()
        self.assertEqual(self.order(auction["id"])["status"], "expired")
        self.assertEqual(self.trading.snapshot()["fills"], [])

    def test_auction_quotes_require_documented_actual_window(self):
        self.fund()
        self.quote(age=90)
        self.providers.close = datetime.now(UTC) + timedelta(seconds=30)
        intent = self.intent(qty=1, time_in_force="cls")
        self.process()
        self.assertEqual(self.order(intent["id"])["status"], "blocked")
        self.quote()
        self.process()
        self.assertEqual(self.order(intent["id"])["status"], "filled")

    def test_stale_price_never_fills_and_cancel_releases_reservation(self):
        self.fund()
        self.quote()
        intent = self.intent()
        self.store.update_settings({"quote_max_age_seconds": 1})
        with self.store.transaction() as con:
            con.execute("UPDATE quotes SET as_of=?", ((datetime.now(UTC) - timedelta(seconds=2)).isoformat(),))
        self.process()
        self.assertEqual(self.order(intent["id"])["status"], "blocked")
        self.assertEqual(self.trading.snapshot()["fills"], [])
        self.trading.cancel_intent(intent["id"])
        self.assertEqual(self.book()["account"]["reserved_cash"], 0)

    def test_cashflow_performance_does_not_report_deposit_as_profit(self):
        self.fund(100)
        self.fund(50, key="second")
        performance = self.trading.snapshot()["performance"][0]
        self.assertEqual(performance["net_external_cashflows"], 150)
        self.assertEqual(performance["net_profit"], 0)
        self.assertEqual(performance["simple_return_percent"], 0)
        self.assertTrue(all(b["return_percent"] is None for b in performance["benchmarks"]))
        self.assertIsNone(performance["alpha_claim"])

    def broker_book(self):
        broker = FakeBroker()
        self.providers.broker = broker
        book = self.trading.create_book({"name": "Connected", "kind": "main", "broker": "alpaca"})
        self.trading.reconcile(self.providers)
        self.quote()
        return broker, book["id"]

    def test_broker_only_one_binding_and_no_local_funding_or_simulation(self):
        broker, book = self.broker_book()
        with self.assertRaises(DeskError):
            self.trading.create_book({"name": "Other", "broker": "alpaca"})
        with self.assertRaises(DeskError):
            self.fund(100, book=book)
        intent = self.intent(book=book)
        self.process()
        self.assertEqual(broker.submits, 1)
        self.assertEqual(self.order(intent["id"])["status"], "open")
        self.assertEqual(self.trading.snapshot()["fills"], [])

    def test_ambiguous_broker_submit_looks_up_identity_before_resending(self):
        broker, book = self.broker_book()
        broker.ambiguous = True
        intent = self.intent(book=book)
        self.process()
        self.assertEqual(self.order(intent["id"])["status"], "submitting")
        self.process()
        self.assertEqual(broker.submits, 1)
        self.assertEqual(self.order(intent["id"])["status"], "open")

    def test_broker_cumulative_fill_notional_delta_and_idempotent_reconciliation(self):
        broker, book = self.broker_book()
        intent = self.intent(qty=2, book=book)
        self.process()
        remote = broker.remote_orders[0]
        remote.update(status="partially_filled", filled_qty="1", filled_avg_price="10", updated_at=datetime.now(UTC).isoformat())
        broker.cash = "990"
        broker.remote_positions = [{"symbol": "AAPL", "qty": "1", "avg_entry_price": "10", "side": "long"}]
        self.trading.reconcile(self.providers)
        remote.update(status="filled", filled_qty="2", filled_avg_price="15", filled_at=datetime.now(UTC).isoformat())
        broker.cash = "970"
        broker.remote_positions = [{"symbol": "AAPL", "qty": "2", "avg_entry_price": "15", "side": "long"}]
        self.trading.reconcile(self.providers)
        self.trading.reconcile(self.providers)
        fills = self.trading.snapshot()["fills"]
        self.assertEqual(len(fills), 2)
        self.assertEqual(sorted(f["price"] for f in fills), [10, 20])
        self.assertEqual(sum(f["notional"] for f in fills), 30)
        self.assertEqual(self.book(book)["account"]["cash"], 970)
        self.assertEqual(self.order(intent["id"])["filled_quantity"], 2)

    def test_external_position_unknown_locked_and_failed_reads_preserve_truth(self):
        broker, book = self.broker_book()
        broker.remote_positions = [{"symbol": "AAPL", "qty": "3", "avg_entry_price": "9", "side": "long"}]
        self.trading.reconcile(self.providers)
        position = next(p for p in self.trading.snapshot()["positions"] if p["book_id"] == book)
        self.assertTrue(position["locked"])
        self.assertIsNone(position["sleeve"])
        with self.assertRaisesRegex(DeskError, "locked"):
            self.intent("sell", 1, "external-exit", book=book)
        broker.fail_read = True
        self.assertTrue(self.trading.reconcile(self.providers)["errors"])
        self.assertEqual(next(p for p in self.trading.snapshot()["positions"] if p["book_id"] == book)["quantity"], 3)
        self.trading.set_book(book, {"acknowledge_external_symbols": ["AAPL"]})
        self.assertFalse(next(p for p in self.trading.snapshot()["positions"] if p["book_id"] == book)["locked"])

    def test_owned_orphan_adoption_is_idempotent(self):
        broker, book = self.broker_book()
        broker.remote_orders = [{"id": "lost-order", "client_order_id": "aster_lost-identity", "symbol": "AAPL", "side": "buy", "qty": "2", "type": "market", "time_in_force": "day", "status": "filled", "filled_qty": "2", "filled_avg_price": "10", "submitted_at": datetime.now(UTC).isoformat(), "filled_at": datetime.now(UTC).isoformat()}]
        broker.remote_positions = [{"symbol": "AAPL", "qty": "2", "avg_entry_price": "10", "side": "long"}]
        broker.cash = "980"
        first = self.trading.reconcile(self.providers)
        self.assertEqual(first["adopted"], 1)
        self.assertEqual(self.trading.reconcile(self.providers)["adopted"], 0)
        self.assertEqual(len([i for i in self.trading.snapshot()["intents"] if i["book_id"] == book]), 1)
        self.assertEqual(len(self.trading.snapshot()["fills"]), 1)

    def test_broker_cancel_retains_reservation_until_receipt_confirmed(self):
        broker, book = self.broker_book()
        intent = self.intent(book=book)
        self.process()
        cancelled = self.trading.cancel_intent(intent["id"])
        self.assertEqual(cancelled["status"], "cancel_requested")
        self.assertEqual(self.book(book)["account"]["reserved_cash"], 100)
        self.process()
        self.trading.reconcile(self.providers)
        self.assertEqual(self.order(intent["id"])["status"], "cancelled")
        self.assertEqual(self.book(book)["account"]["reserved_cash"], 0)

    def test_multiple_paper_connections_keep_cash_orders_and_positions_separate(self):
        research, forward = FakeBroker(), FakeBroker()
        research.identity, forward.identity = "PAPER-RESEARCH", "PAPER-FORWARD"
        research.cash, forward.cash = "1000", "500"
        brokers = {"research": research, "forward": forward}
        self.providers.broker_for = lambda connection: brokers.get(connection)
        first = self.trading.create_book({"name": "Research account", "broker": "alpaca", "connection_id": "research"})
        second = self.trading.create_book({"name": "Forward account", "broker": "alpaca", "connection_id": "forward"})
        self.trading.reconcile(self.providers)
        self.quote()
        a = self.intent(qty=1, key="same-key", book=first["id"])
        b = self.intent(qty=2, key="same-key", book=second["id"])
        self.process()
        self.assertEqual((research.submits, forward.submits), (1, 1))
        self.assertEqual(self.order(a["id"])["broker_id"], "broker-1")
        self.assertEqual(self.order(b["id"])["broker_id"], "broker-1")
        research.remote_orders[0].update(status="filled", filled_qty="1", filled_avg_price="10", filled_at=datetime.now(UTC).isoformat())
        research.remote_positions = [{"symbol": "AAPL", "qty": "1", "avg_entry_price": "10", "side": "long"}]
        research.cash = "990"
        self.trading.reconcile(self.providers)
        self.assertEqual(self.order(a["id"])["status"], "filled")
        self.assertEqual(self.order(b["id"])["status"], "open")
        self.assertEqual(self.book(first["id"])["account"]["cash"], 990)
        self.assertEqual(self.book(second["id"])["account"]["cash"], 500)

    def test_same_actual_broker_account_cannot_bind_two_aliases(self):
        broker = FakeBroker()
        self.providers.broker_for = lambda connection: broker
        self.trading.create_book({"name": "First alias", "broker": "alpaca", "connection_id": "first"})
        second = self.trading.create_book({"name": "Second alias", "broker": "alpaca", "connection_id": "second"})
        result = self.trading.reconcile(self.providers)
        self.assertTrue(result["errors"])
        self.assertEqual(self.book(second["id"])["account"]["cash"], 0)

    def test_policy_compare_and_swap_preserves_newer_operator_override(self):
        original = self.book()["policy_hash"]
        proposal = self.trading.set_book("main", {"halted": True}, expected_hash=original, actor="proposal:approved-1")
        self.trading.set_book("main", {"halted": False})
        with self.assertRaisesRegex(DeskError, "compare-and-swap"):
            self.trading.set_book("main", {"halted": False}, expected_hash=proposal["policy_hash"], actor="proposal_guard:approved-1")
        self.assertFalse(self.book()["policy"]["halted"])

    def test_signed_local_reconciliation_detects_corruption_and_preserves_history(self):
        self.fund()
        self.quote()
        self.trading.set_book("main", {"allow_short": True})
        self.intent("sell", 3)
        self.process()
        self.quote(8)
        self.intent("buy", 1, "cover")
        self.process()
        self.assertFalse(self.trading.reconcile(self.providers)["errors"])
        with self.store.transaction() as con:
            con.execute("UPDATE p_books SET cash_cents=cash_cents+1 WHERE id='main'")
        self.assertTrue(self.trading.reconcile(self.providers)["errors"])
        self.assertEqual(len(self.trading.snapshot()["fills"]), 2)

    def test_failed_book_does_not_freeze_healthy_independent_book(self):
        self.fund()
        self.quote()
        good = self.intent()
        self.trading.create_book({"name": "Waiting broker", "broker": "alpaca", "connection_id": "not-configured"})
        self.assertTrue(self.trading.reconcile(self.providers)["errors"])
        self.assertEqual(self.process()["fills"], 1)
        self.assertEqual(self.order(good["id"])["status"], "filled")

    def test_corrupt_local_book_is_fenced_from_further_execution(self):
        self.fund()
        self.quote()
        intent = self.intent()
        with self.store.transaction() as con:
            con.execute("UPDATE p_books SET cash_cents=cash_cents+1 WHERE id='main'")
        self.trading.reconcile(self.providers)
        self.assertEqual(self.process()["fills"], 0)
        self.assertEqual(self.order(intent["id"])["status"], "blocked")

    def test_funding_has_clean_pre_and_post_flow_valuation_receipts(self):
        funding = self.fund(100)
        history = self.trading.snapshot()["equity_history"]
        self.assertEqual(len(history), 2)
        self.assertEqual((history[0]["equity"], history[1]["equity"]), (0, 100))
        self.assertLess(history[0]["timestamp"], funding["timestamp"])
        self.assertLess(funding["timestamp"], history[1]["timestamp"])
        self.assertEqual(history[0]["stale_marks"], 0)

    def test_first_pass_after_restart_does_not_reanchor_old_auction_to_today(self):
        self.fund()
        # A first pass at today's actual opening would fill a newly anchored
        # auction. Both old session and after-close authorizations must retain
        # their original exchange calendar, including its historical next open.
        current = datetime(2026, 10, 9, 13, 30, 2, tzinfo=UTC)
        originals = (datetime(2026, 10, 5, 18, 30, tzinfo=UTC),
                     datetime(2026, 10, 5, 21, 0, tzinfo=UTC))
        with self.store.transaction() as con:
            con.execute("INSERT OR REPLACE INTO quotes VALUES(?,?,?,?)",
                        ("AAPL", "10", current.isoformat(), "Synthetic opening quote fixture"))
            intents = []
            for index, original in enumerate(originals):
                payload = self.trading._normalize_intent({"book_id": "main", "symbol": "AAPL", "side": "buy",
                    "quantity": 1, "client_id": "old-auction-" + str(index), "order_type": "market", "time_in_force": "opg"})
                intent = self.trading._submit_normalized_intent(con, payload, clock=current)
                con.execute("UPDATE p_intents SET created_at=? WHERE id=?", (original.isoformat(), intent["id"]))
                intents.append(intent)
            payload = self.trading._normalize_intent({"book_id": "main", "symbol": "AAPL", "side": "buy",
                "quantity": 1, "client_id": "current-auction-control", "order_type": "market", "time_in_force": "opg"})
            control = self.trading._submit_normalized_intent(con, payload, clock=current)

        class DatedCalendar(FakeProviders):
            def calendar(self, clock=None):
                return exchange_calendar(current if clock is None else clock)

        self.trading = TradingDesk(Store(self.store.path))
        self.trading.process(DatedCalendar(), current)
        for index, intent in enumerate(intents):
            with self.subTest(original=originals[index]):
                saved = self.order(intent["id"])
                self.assertEqual(saved["status"], "expired")
                self.assertEqual(saved["session_open"], "2026-10-0" + str(5 + index) + "T13:30:00+00:00")
                self.assertEqual(saved["session_close"], "2026-10-0" + str(5 + index) + "T20:00:00+00:00")
        self.assertEqual(self.order(control["id"])["status"], "filled")
        self.assertEqual(self.order(control["id"])["session_open"], "2026-10-09T13:30:00+00:00")
        fills = self.trading.snapshot()["fills"]
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0]["intent_id"], control["id"])

    def test_descending_orphan_history_reconstructs_average_cost_in_source_order(self):
        broker, book = self.broker_book()
        base = datetime.now(UTC) - timedelta(minutes=10)
        rows = []
        for index, (side, qty, price) in enumerate((("buy", 10, 10), ("buy", 10, 20), ("sell", 5, 25))):
            ts = (base + timedelta(minutes=index)).isoformat()
            rows.append({"id": f"history-{index}", "client_order_id": f"aster_history-{index}", "symbol": "AAPL", "side": side, "qty": str(qty), "type": "market", "time_in_force": "day", "status": "filled", "filled_qty": str(qty), "filled_avg_price": str(price), "submitted_at": ts, "filled_at": ts})
        broker.remote_orders = list(reversed(rows))
        broker.remote_positions = [{"symbol": "AAPL", "qty": "15", "avg_entry_price": "15", "side": "long"}]
        broker.cash = "825"
        result = self.trading.reconcile(self.providers)
        self.assertFalse(result["errors"])
        self.assertIsNone(self.book(book)["account"]["realized_pnl"])
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT realized_cents FROM p_books WHERE id=?", (book,)).fetchone()[0], 5000)
        position = next(p for p in self.trading.snapshot()["positions"] if p["book_id"] == book)
        self.assertEqual(position["average_cost"], 15)
        self.assertFalse(position["locked"])

    def test_ambiguous_auction_submission_recovers_before_expiry_gate(self):
        broker, book = self.broker_book()
        self.providers.open = datetime.now(UTC)
        broker.ambiguous = True
        intent = self.intent(qty=1, book=book, time_in_force="opg")
        self.process()
        self.assertEqual(self.order(intent["id"])["status"], "submitting")
        future = datetime.now(UTC) + timedelta(minutes=2)
        broker.remote_orders[0].update(status="filled", filled_qty="1", filled_avg_price="10", filled_at=self.providers.open.isoformat())
        self.trading.process(self.providers, future)
        self.assertEqual(self.order(intent["id"])["status"], "filled")
        self.assertEqual(broker.submits, 1)

    def test_turning_off_short_entries_still_allows_partial_risk_reduction(self):
        self.fund()
        self.quote()
        self.trading.set_book("main", {"allow_short": True})
        self.intent("sell", 10, "short")
        self.process()
        self.trading.set_book("main", {"allow_short": False, "halted": True})
        cover = self.intent("buy", 4, "partial-cover")
        self.process()
        self.assertEqual(self.order(cover["id"])["status"], "filled")
        self.assertEqual(self.trading.snapshot()["positions"][0]["quantity"], -6)

    def test_unowned_external_pending_order_locks_even_a_flat_symbol(self):
        broker, book = self.broker_book()
        broker.remote_orders = [{"id": "foreign", "client_order_id": "another-application", "symbol": "AAPL", "side": "buy", "qty": "1", "type": "market", "time_in_force": "day", "status": "accepted", "filled_qty": "0"}]
        self.trading.reconcile(self.providers)
        with self.assertRaisesRegex(DeskError, "Unattributed external broker orders"):
            self.intent(book=book)

    def test_cover_with_protection_never_creates_a_new_position(self):
        self.fund()
        self.quote()
        self.trading.set_book("main", {"allow_short": True})
        self.intent("sell", 10, "short")
        self.process()
        cover = self.intent("buy", 10, "cover", take_profit=12, stop_loss=8)
        self.process()
        self.assertEqual(self.trading.snapshot()["positions"], [])
        self.assertEqual([i for i in self.trading.snapshot()["intents"] if i["parent_id"] == cover["id"]], [])
        self.quote(12)
        self.assertEqual(self.process()["fills"], 0)
        self.assertEqual(self.trading.snapshot()["positions"], [])

    def test_protected_flip_covers_only_the_newly_opened_quantity(self):
        self.fund()
        self.quote()
        self.trading.set_book("main", {"allow_short": True})
        self.intent("sell", 10, "short")
        self.process()
        flip = self.intent("buy", 15, "flip", take_profit=12, stop_loss=8)
        self.process()
        children = [i for i in self.trading.snapshot()["intents"] if i["parent_id"] == flip["id"]]
        self.assertEqual([i["quantity"] for i in children], [5, 5])
        self.quote(12)
        self.process()
        self.assertEqual(self.trading.snapshot()["positions"], [])
        self.assertEqual(self.book()["account"]["realized_pnl"], 10)

    def test_partial_limit_fill_retains_worst_authorized_cash_bound(self):
        self.fund()
        self.quote(10)
        intent = self.intent(qty=100, order_type="limit", limit_price=10, max_fill_quantity=10)
        self.quote(8)
        self.process()
        self.assertEqual(self.order(intent["id"])["filled_quantity"], 10)
        self.assertEqual(self.book()["account"]["cash"], 920)
        self.assertEqual(self.book()["account"]["reserved_cash"], 900)
        with self.assertRaisesRegex(DeskError, "unreserved cash"):
            self.intent(qty=20, key="cannot-spend-price-improvement")

    def test_accepted_broker_entry_cancels_after_expiry_or_policy_withdrawal(self):
        for gate in ("expiry", "halt", "gross_cap", "short_permission"):
            with self.subTest(gate=gate):
                with tempfile.TemporaryDirectory() as directory:
                    store = Store(Path(directory) / "case.sqlite")
                    desk = TradingDesk(store)
                    broker = FakeBroker()
                    providers = FakeProviders(broker)
                    book = desk.create_book({"name": "Paper", "broker": "alpaca"})["id"]
                    desk.reconcile(providers)
                    store.ingest_quote("AAPL", Decimal(10), datetime.now(UTC), "Test observation")
                    if gate == "short_permission":
                        desk.set_book(book, {"allow_short": True})
                    start = datetime.now(UTC)
                    fields = {"expires_at": (start + timedelta(seconds=5)).isoformat()} if gate == "expiry" else {}
                    intent = desk.submit_intent({"book_id": book, "symbol": "AAPL", "side": "sell" if gate == "short_permission" else "buy", "quantity": 10, "client_id": "authorized", **fields})
                    desk.process(providers, start)
                    if gate == "halt":
                        desk.set_book(book, {"halted": True})
                    elif gate == "gross_cap":
                        desk.set_book(book, {"gross_exposure_cap": 50})
                    elif gate == "short_permission":
                        desk.set_book(book, {"allow_short": False})
                    desk.process(providers, start + timedelta(seconds=6))
                    self.assertEqual(broker.cancels, 1)
                    self.assertEqual(broker.submits, 1)
                    pending = next(i for i in desk.snapshot()["intents"] if i["id"] == intent["id"])
                    self.assertEqual(pending["status"], "cancel_requested")
                    desk.reconcile(providers)
                    self.assertEqual(desk.snapshot()["intents"][0]["status"], "cancelled")

    def test_cancel_and_identity_recovery_survive_failed_reconciliation_and_calendar(self):
        broker, book = self.broker_book()
        intent = self.intent(book=book)
        self.process()
        self.trading.cancel_intent(intent["id"])
        broker.fail_read = True
        self.trading.reconcile(self.providers)
        self.providers.calendar = lambda clock=None: (_ for _ in ()).throw(RuntimeError("Calendar down"))
        self.process()
        self.assertEqual(broker.cancels, 1)
        self.assertEqual(self.order(intent["id"])["status"], "cancel_requested")
        self.assertEqual(self.book(book)["account"]["reserved_cash"], 100)
        broker.fail_read = False
        self.trading.reconcile(self.providers)
        self.assertEqual(self.order(intent["id"])["status"], "cancelled")

    def test_missing_adapter_keeps_the_operator_cancel_request(self):
        broker, book = self.broker_book()
        intent = self.intent(book=book)
        self.process()
        self.trading.cancel_intent(intent["id"])
        self.providers.broker = None
        self.process()
        self.assertEqual(self.order(intent["id"])["status"], "cancel_requested")
        self.providers.broker = broker
        self.process()
        self.assertEqual(broker.cancels, 1)

    def test_ambiguous_identity_is_recovered_even_when_market_calendar_fails(self):
        broker, book = self.broker_book()
        broker.ambiguous = True
        intent = self.intent(book=book)
        self.process()
        broker.fail_read = True
        self.trading.reconcile(self.providers)
        self.providers.calendar = lambda clock=None: (_ for _ in ()).throw(RuntimeError("Calendar down"))
        self.process()
        self.assertEqual(broker.submits, 1)
        self.assertEqual(self.order(intent["id"])["status"], "open")

    def test_broker_oco_legs_reserve_shares_once_after_complete_position_truth(self):
        broker, book = self.broker_book()
        parent = self.intent(book=book, take_profit=12, stop_loss=9)
        self.process()
        remote = broker.remote_orders[0]
        before_fill = (datetime.now(UTC) - timedelta(seconds=2)).isoformat()
        remote.update(status="filled", filled_qty="10", filled_avg_price="10", filled_at=datetime.now(UTC).isoformat(), order_class="bracket")
        remote["legs"] = [{"id": "tp", "client_order_id": "native-tp", "symbol": "AAPL", "side": "sell", "qty": "10", "type": "limit", "limit_price": "12", "time_in_force": "gtc", "status": "accepted", "filled_qty": "0", "submitted_at": before_fill}, {"id": "sl", "client_order_id": "native-sl", "symbol": "AAPL", "side": "sell", "qty": "10", "type": "stop", "stop_price": "9", "time_in_force": "gtc", "status": "accepted", "filled_qty": "0", "submitted_at": before_fill}]
        broker.remote_positions = [{"symbol": "AAPL", "qty": "10", "avg_entry_price": "10", "side": "long"}]
        broker.cash = "900"
        self.trading.reconcile(self.providers)
        children = [i for i in self.trading.snapshot()["intents"] if i["parent_id"] == parent["id"]]
        self.assertEqual([i["reserved_quantity"] for i in children], [10, 10])
        self.assertEqual(len({i["oco_group"] for i in children}), 1)
        with self.assertRaisesRegex(DeskError, "unreserved shares"):
            self.intent("sell", 1, "cannot-double-sell", book=book)

    def test_pending_flip_reserves_its_closing_component(self):
        self.fund()
        self.quote()
        self.trading.set_book("main", {"allow_short": True})
        self.intent(qty=10, key="holding")
        self.process()
        flip = self.intent("sell", 15, "flip", order_type="limit", limit_price=12)
        self.assertEqual(self.order(flip["id"])["reserved_quantity"], 10)
        with self.assertRaisesRegex(DeskError, "unreserved shares"):
            self.intent("sell", 10, "duplicate-close")

    def test_partial_cover_and_flip_retains_remaining_cash_and_closing_reservations(self):
        self.fund()
        self.quote()
        self.trading.set_book("main", {"allow_short": True})
        self.intent("sell", 10, "short")
        self.process()
        flip = self.intent("buy", 15, "flip", max_fill_quantity=5)
        self.process()
        self.assertEqual(self.trading.snapshot()["positions"][0]["quantity"], -5)
        pending = self.order(flip["id"])
        self.assertEqual(pending["reserved"], 100)
        self.assertEqual(pending["reserved_quantity"], 5)
        with self.assertRaisesRegex(DeskError, "unreserved short shares"):
            self.intent("buy", 5, "overlapping-cover")

    def test_broker_native_bracket_cannot_cover_or_flip_an_existing_opposite_position(self):
        broker, book = self.broker_book()
        broker.remote_positions = [{"symbol": "AAPL", "qty": "10", "avg_entry_price": "10", "side": "short"}]
        self.trading.reconcile(self.providers)
        self.trading.set_book(book, {"acknowledge_external_symbols": ["AAPL"]})
        for quantity in (10, 15):
            with self.assertRaisesRegex(DeskError, "cannot cover or flip"):
                self.intent("buy", quantity, str(quantity), book=book, take_profit=12, stop_loss=8)
        self.assertEqual(broker.submits, 0)

    def test_protection_is_serviced_ahead_of_two_hundred_waiting_entries(self):
        self.fund(10000)
        self.quote()
        parent = self.intent(qty=10, stop_loss=9, key="protected")
        for index in range(200):
            self.intent(qty=1, key=f"waiting-{index}", order_type="limit", limit_price=1)
        self.process()
        self.quote(8)
        result = self.process()
        self.assertEqual(result["fills"], 1)
        self.assertEqual(self.trading.snapshot()["positions"], [])
        stop = next(i for i in self.trading.snapshot()["intents"] if i["parent_id"] == parent["id"])
        self.assertEqual(stop["status"], "filled")

    def test_waiting_entry_rotation_survives_restart(self):
        self.fund(10000)
        self.quote()
        for index in range(205):
            self.intent(qty=1, key=f"waiting-{index}", order_type="limit", limit_price=1)
        first = self.trading._service_ids()
        self.assertEqual(len(first), 200)
        self.trading = TradingDesk(Store(self.store.path))
        second = self.trading._service_ids()
        self.assertEqual(len(set(first) | set(second)), 205)

    def test_slow_identity_lookup_rechecks_wall_clock_and_operator_policy_before_send(self):
        for gate in ("expiry", "halt"):
            with self.subTest(gate=gate):
                broker, book = self.broker_book() if gate == "expiry" else (self.providers.broker, next(b["id"] for b in self.trading.snapshot()["books"] if b["broker"] == "alpaca"))
                current = [datetime.now(UTC) + timedelta(seconds=1)]
                intent = self.intent(qty=1, key=gate, book=book, expires_at=(current[0] + timedelta(seconds=5)).isoformat())
                original_lookup = broker.get_order
                def delayed_lookup(client_id):
                    if gate == "expiry":
                        current[0] += timedelta(seconds=10)
                    else:
                        self.trading.set_book(book, {"halted": True})
                    return original_lookup(client_id)
                broker.get_order = delayed_lookup
                with patch("backend.trading.clock_time", side_effect=lambda supplied: supplied or current[0]):
                    self.process()
                self.assertEqual(broker.submits, 0)
                self.assertEqual(self.order(intent["id"])["filled_quantity"], 0)
                self.assertEqual(self.order(intent["id"])["status"], "expired" if gate == "expiry" else "submitting")
                broker.get_order = original_lookup

    def test_production_clock_refreshes_between_local_intents(self):
        self.fund()
        self.quote()
        current = [datetime.now(UTC) + timedelta(seconds=1)]
        first = self.intent(qty=1, key="first")
        second = self.intent(qty=1, key="expires-during-first", expires_at=(current[0] + timedelta(seconds=5)).isoformat())
        original_fill = self.trading._fill
        def advancing_fill(*args, **kwargs):
            result = original_fill(*args, **kwargs)
            current[0] += timedelta(seconds=10)
            return result
        with patch("backend.trading.clock_time", side_effect=lambda supplied: supplied or current[0]), patch.object(self.trading, "_fill", side_effect=advancing_fill):
            result = self.process()
        self.assertEqual(result["fills"], 1)
        self.assertEqual(self.order(first["id"])["status"], "filled")
        self.assertEqual(self.order(second["id"])["status"], "expired")

    def test_portfolio_policy_is_opt_in_versioned_durable_and_compare_and_swap(self):
        initial = self.trading.snapshot()["global_policy"]
        self.assertIsNone(initial["gross_exposure_cap"])
        self.assertIsNone(initial["symbol_exposure_cap"])
        updated = self.trading.set_portfolio_policy({"gross_exposure_cap": 150, "expected_hash": initial["hash"]})
        self.assertEqual(updated["version"], initial["version"] + 1)
        self.assertNotEqual(updated["hash"], initial["hash"])
        with self.assertRaisesRegex(DeskError, "compare-and-swap"):
            self.trading.set_portfolio_policy({"gross_exposure_cap": 100, "expected_hash": initial["hash"]})
        self.trading = TradingDesk(Store(self.store.path))
        self.assertEqual(self.trading.snapshot()["global_policy"], updated)
        self.assertEqual(len(self.trading.snapshot()["global_policy_history"]), 2)
        for invalid in (0, -1, 10.001, float("inf"), True):
            with self.assertRaises(DeskError):
                self.trading.set_portfolio_policy({"gross_exposure_cap": invalid})
        self.assertEqual(self.trading.set_portfolio_policy({"gross_exposure_cap": None})["gross_exposure_cap"], None)

    def test_portfolio_cash_and_share_books_stay_separate_while_gross_caps_reserve_atomically(self):
        other = self.trading.create_book({"name": "Other book"})["id"]
        self.fund(1000)
        self.fund(1000, book=other)
        self.quote()
        self.trading.set_portfolio_policy({"gross_exposure_cap": 150})
        def authorize(pair):
            key, book = pair
            try:
                return self.intent(qty=10, key=key, book=book)
            except DeskError:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            intents = list(pool.map(authorize, [("first", "main"), ("second", other)]))
        self.assertEqual(sum(row is not None for row in intents), 1)
        pending = next(row for row in intents if row)
        exposure = self.trading.snapshot()["global_exposure"]
        self.assertEqual(exposure["projected_gross_exposure"], 100)
        self.assertEqual(exposure["gross_exposure"], 0)
        self.process()
        self.assertEqual(self.trading.snapshot()["global_exposure"]["gross_exposure"], 100)
        untouched = other if pending["book_id"] == "main" else "main"
        self.assertEqual(self.book(untouched)["account"]["cash"], 1000)
        self.assertEqual(self.book(untouched)["account"]["reserved_cash"], 0)

    def test_portfolio_symbol_cap_never_nets_opposite_positions_across_books(self):
        short_book = self.trading.create_book({"name": "Independent short"})["id"]
        self.fund()
        self.fund(book=short_book)
        self.quote()
        self.trading.set_book(short_book, {"allow_short": True})
        self.intent(qty=10, key="long")
        self.process()
        self.trading.set_portfolio_policy({"symbol_exposure_cap": 150})
        with self.assertRaisesRegex(DeskError, "portfolio symbol exposure"):
            self.intent("sell", 10, "short", book=short_book)
        self.trading.set_portfolio_policy({"symbol_exposure_cap": 200})
        self.intent("sell", 10, "short", book=short_book)
        self.process()
        exposure = self.trading.snapshot()["global_exposure"]
        self.assertEqual(exposure["gross_exposure"], 200)
        self.assertEqual(exposure["symbols"][0]["gross_exposure"], 200)
        self.assertEqual(sum(p["quantity"] for p in self.trading.snapshot()["positions"]), 0)

    def test_portfolio_gate_requires_fresh_marks_across_books_but_preserves_exits(self):
        other = self.trading.create_book({"name": "Other"})["id"]
        self.fund()
        self.fund(book=other)
        self.quote(sym="MSFT")
        holding = self.trading.submit_intent({"book_id": other, "symbol": "MSFT", "side": "buy", "quantity": 5, "client_id": "holding", "time_in_force": "gtc"})
        self.process()
        self.quote()
        self.intent(qty=5, key="main-holding")
        self.process()
        self.trading.set_portfolio_policy({"gross_exposure_cap": 500})
        with self.store.transaction() as con:
            con.execute("UPDATE quotes SET as_of=? WHERE symbol='MSFT'", ((datetime.now(UTC) - timedelta(hours=1)).isoformat(),))
        with self.assertRaisesRegex(DeskError, "coherent fresh marks"):
            self.intent(qty=1, key="new-entry")
        self.assertIsNone(self.trading.snapshot()["global_exposure"]["gross_exposure"])
        exit_order = self.intent("sell", 5, "risk-reduction")
        self.process()
        self.assertEqual(self.order(exit_order["id"])["status"], "filled")
        self.assertEqual(self.order(holding["id"])["status"], "filled")
        self.quote(sym="MSFT")
        self.assertEqual(self.trading.snapshot()["global_exposure"]["valuation_status"], "complete")
        self.intent(qty=1, key="entry-after-refresh")

    def test_portfolio_unknown_broker_gate_is_opt_in_and_reducing_exits_remain_available(self):
        self.fund()
        self.quote()
        self.intent(qty=5, key="holding")
        self.process()
        self.trading.create_book({"name": "Unconfigured account", "broker": "alpaca"})
        self.intent(qty=1, key="no-global-cap")
        self.trading.set_portfolio_policy({"gross_exposure_cap": 500})
        with self.assertRaisesRegex(DeskError, "Broker state is unknown"):
            self.intent(qty=1, key="global-risk-cannot-see-account")
        exit_order = self.intent("sell", 5, "exit")
        self.process()
        self.assertEqual(self.order(exit_order["id"])["status"], "filled")
        self.assertEqual(self.trading.snapshot()["global_exposure"]["valuation_status"], "incomplete")

    def test_portfolio_known_broker_truth_becomes_stale_and_failed_reads_block_new_entries(self):
        broker, book = self.broker_book()
        self.fund()
        self.trading.set_portfolio_policy({"gross_exposure_cap": 500})
        allowed = self.intent(qty=1, key="known-state")
        self.trading.cancel_intent(allowed["id"])
        with self.store.transaction() as con:
            con.execute("UPDATE p_broker_truth SET observed_at=? WHERE book_id=?", ((datetime.now(UTC) - timedelta(hours=1)).isoformat(), book))
        with self.assertRaisesRegex(DeskError, "Broker state is stale"):
            self.intent(qty=1, key="stale-state")
        self.trading.reconcile(self.providers)
        broker.fail_read = True
        self.trading.reconcile(self.providers)
        with self.assertRaisesRegex(DeskError, "Broker state is unknown"):
            self.intent(qty=1, key="failed-read")

    def test_portfolio_cap_lowered_after_authorization_blocks_local_entry_until_reduction(self):
        self.fund()
        self.quote()
        pending = self.intent(qty=10, key="pending")
        self.trading.set_portfolio_policy({"gross_exposure_cap": 50})
        self.assertEqual(self.process()["fills"], 0)
        self.assertEqual(self.order(pending["id"])["status"], "blocked")
        self.assertEqual(self.book()["account"]["reserved_cash"], 100)
        self.trading.set_portfolio_policy({"gross_exposure_cap": 100})
        self.assertEqual(self.process()["fills"], 1)
        self.trading.set_portfolio_policy({"gross_exposure_cap": 10})
        exit_order = self.intent("sell", 10, "exit")
        self.process()
        self.assertEqual(self.order(exit_order["id"])["status"], "filled")

    def test_portfolio_cap_cancels_accepted_broker_entries_without_assuming_a_fill(self):
        broker, book = self.broker_book()
        entry = self.intent(book=book)
        self.process()
        self.trading.set_portfolio_policy({"gross_exposure_cap": 50})
        self.process()
        self.assertEqual(broker.cancels, 1)
        self.assertEqual(self.order(entry["id"])["status"], "cancel_requested")
        self.assertEqual(self.trading.snapshot()["fills"], [])
        self.assertEqual(self.book(book)["account"]["reserved_cash"], 100)

    def test_portfolio_foreign_pending_broker_exposure_is_unknown_not_zero(self):
        broker, book = self.broker_book()
        self.fund()
        broker.remote_orders = [{"id": "foreign", "client_order_id": "another-desk", "symbol": "MSFT", "side": "buy", "qty": "100", "type": "market", "time_in_force": "day", "status": "accepted", "filled_qty": "0"}]
        self.trading.reconcile(self.providers)
        self.trading.set_portfolio_policy({"gross_exposure_cap": 500})
        with self.assertRaisesRegex(DeskError, "pending exposure unknown"):
            self.intent(qty=1, key="cannot-ignore-foreign-order")
        aggregate = self.trading.snapshot()["global_exposure"]
        self.assertIsNone(aggregate["gross_exposure"])
        self.assertIsNone(next(row for row in aggregate["books"] if row["book_id"] == book)["projected_gross_exposure"])

    def test_accepted_broker_entry_can_cancel_for_global_policy_with_no_quote(self):
        broker, book = self.broker_book()
        entry = self.intent(book=book)
        self.process()
        with self.store.transaction() as con:
            con.execute("DELETE FROM quotes WHERE symbol='AAPL'")
        self.trading.set_portfolio_policy({"gross_exposure_cap": 50})
        self.process()
        self.assertEqual(broker.cancels, 1)
        self.assertEqual(self.order(entry["id"])["status"], "cancel_requested")
        self.assertEqual(self.book(book)["account"]["reserved_cash"], 100)

    def test_accepted_broker_entry_can_cancel_for_global_policy_after_account_read_failure(self):
        broker, book = self.broker_book()
        entry = self.intent(book=book)
        self.process()
        broker.fail_read = True
        self.trading.reconcile(self.providers)
        self.trading.set_portfolio_policy({"gross_exposure_cap": 50})
        self.process()
        self.assertEqual(broker.cancels, 1)
        self.assertEqual(self.order(entry["id"])["status"], "cancel_requested")

    def test_foreign_nested_bracket_protection_is_unattributed_pending_exposure(self):
        broker, book = self.broker_book()
        self.fund()
        stamp = datetime.now(UTC).isoformat()
        broker.remote_orders = [{"id": "foreign-parent", "client_order_id": "foreign-parent", "symbol": "AAPL", "side": "buy", "qty": "10", "type": "market", "time_in_force": "gtc", "status": "filled", "filled_qty": "10", "filled_avg_price": "10", "submitted_at": stamp, "legs": [{"id": "foreign-stop", "client_order_id": "foreign-stop", "symbol": "AAPL", "side": "sell", "qty": "10", "type": "stop", "stop_price": "9", "time_in_force": "gtc", "status": "accepted", "filled_qty": "0", "submitted_at": stamp}]}]
        self.trading.reconcile(self.providers)
        self.trading.set_portfolio_policy({"gross_exposure_cap": 500})
        with self.assertRaisesRegex(DeskError, "pending exposure unknown"):
            self.intent(qty=1, key="new-entry")
        self.assertEqual(self.trading.snapshot()["global_exposure"]["valuation_status"], "incomplete")

    def test_owned_broker_protection_after_external_flatten_is_unknown_pending_exposure(self):
        broker, book = self.broker_book()
        self.fund()
        parent = self.intent(book=book, stop_loss=9)
        self.process()
        stamp = datetime.now(UTC).isoformat()
        remote = broker.remote_orders[0]
        remote.update(status="filled", filled_qty="10", filled_avg_price="10", filled_at=stamp, order_class="bracket", legs=[{"id": "owned-stop", "client_order_id": "owned-native-stop", "symbol": "AAPL", "side": "sell", "qty": "10", "type": "stop", "stop_price": "9", "time_in_force": "gtc", "status": "accepted", "filled_qty": "0", "submitted_at": stamp}])
        broker.remote_positions = [{"symbol": "AAPL", "qty": "10", "avg_entry_price": "10", "side": "long"}]
        broker.cash = "900"
        self.trading.reconcile(self.providers)
        broker.remote_positions = []
        self.trading.reconcile(self.providers)
        self.trading.set_portfolio_policy({"gross_exposure_cap": 500})
        with self.assertRaisesRegex(DeskError, "protection no longer matches"):
            self.intent(qty=1, key="entry-cannot-ignore-orphan-stop")
        protection = next(row for row in self.trading.snapshot()["intents"] if row["parent_id"] == parent["id"])
        self.assertEqual(protection["reserved_quantity"], 0)
        self.assertEqual(broker.cancels, 0)
        self.assertFalse(self.trading.snapshot()["protection_capability"]["automatic_broker_repair"])



    def test_per_book_caps_include_other_pending_explicit_price_bounds(self):
        self.fund()
        self.quote()
        for field in ("symbol_exposure_cap", "gross_exposure_cap"):
            with self.subTest(field=field):
                self.trading.set_book("main", {"allow_short": True, "symbol_exposure_cap": None, "gross_exposure_cap": None, field: 150})
                pending = self.intent("sell", 1, "limit-" + field, order_type="limit", limit_price=100)
                with self.assertRaisesRegex(DeskError, "exposure cap"):
                    self.intent("sell", 1, "second-" + field)
                self.trading.cancel_intent(pending["id"])

    def test_buy_stop_reserves_explicit_trigger_before_any_transport(self):
        self.fund(100)
        self.quote()
        with self.assertRaisesRegex(DeskError, "unreserved cash"):
            self.intent(qty=10, order_type="stop", stop_price=30)
        self.fund(200, key="extra")
        order = self.intent(qty=10, order_type="stop", stop_price=30)
        self.assertEqual(order["reserved"], 300)
        self.assertEqual(self.process()["fills"], 0)
        self.quote(30)
        self.assertEqual(self.process()["fills"], 1)
        self.assertEqual(self.book()["account"]["cash"], 0)

    def test_stop_limit_reserves_limit_without_inventing_trigger_execution(self):
        self.fund(120)
        self.quote()
        order = self.intent(qty=10, order_type="stop_limit", stop_price=30, limit_price=12)
        self.assertEqual(order["reserved"], 120)
        self.quote(30)
        self.assertEqual(self.process()["fills"], 0)
        self.assertTrue(self.order(order["id"])["triggered"])

    def test_cheap_limit_does_not_discount_current_held_exposure(self):
        self.fund()
        self.quote()
        self.intent(qty=10)
        self.process()
        self.quote(100)
        self.trading.set_book("main", {"gross_exposure_cap": 1000})
        with self.assertRaisesRegex(DeskError, "gross exposure cap"):
            self.intent(qty=1, key="cheap-limit", order_type="limit", limit_price=1)

    def test_integer_range_failure_blocks_only_affected_order_without_partial_fill(self):
        self.trading.set_book("main", {"allow_short": True})
        self.quote(90_000_000)
        self.intent("sell", 1_000_000_000, "first-huge")
        self.assertEqual(self.process()["fills"], 1)
        self.quote(90_000_000, "MSFT")
        huge = self.trading.submit_intent({"symbol": "MSFT", "side": "sell", "quantity": 1_000_000_000, "time_in_force": "gtc", "client_id": "second-huge"})
        healthy = self.trading.create_book({"name": "Healthy isolated book"})["id"]
        self.fund(100, healthy)
        self.quote(10, "AMD")
        good = self.trading.submit_intent({"book_id": healthy, "symbol": "AMD", "side": "buy", "quantity": 1, "time_in_force": "gtc", "client_id": "small"})
        result = self.process()
        self.assertEqual(result["fills"], 1)
        self.assertEqual(self.order(huge["id"])["filled_quantity"], 0)
        self.assertEqual(self.order(huge["id"])["status"], "blocked")
        self.assertEqual(self.order(good["id"])["status"], "filled")
        with self.store.connect() as con:
            cash, kind = con.execute("SELECT cash_cents,typeof(cash_cents) FROM p_books WHERE id='main'").fetchone()
            self.assertEqual((cash, kind), (9_000_000_000_000_000_000, "integer"))
            self.assertFalse(con.execute("SELECT 1 FROM p_positions WHERE book_id='main' AND symbol='MSFT'").fetchone())

    def test_reconciliation_rejects_preexisting_real_money_without_rewriting_it(self):
        self.fund()
        with self.store.transaction() as con:
            # SQLite keeps a non-integer-typed numeric value when it cannot be
            # represented as an INTEGER. Equality alone must not certify it.
            con.execute("UPDATE p_books SET peak_equity_cents=1e20 WHERE id='main'")
        self.assertTrue(self.trading.reconcile(self.providers)["errors"])
        self.assertEqual(self.book()["reconciliation_health"]["status"], "failed")
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT typeof(peak_equity_cents) FROM p_books WHERE id='main'").fetchone()[0], "real")

    def test_broker_receipts_must_match_saved_identity_and_authorized_economics(self):
        broker, book = self.broker_book()
        order = self.intent(qty=2, book=book)
        self.process()
        original = dict(broker.remote_orders[0])
        changes = ({"symbol": "MSFT"}, {"side": "sell"}, {"qty": "3"}, {"client_order_id": "aster_different"}, {"id": "other-order"}, {"type": "stop"}, {"time_in_force": "day"}, {"limit_price": "20"}, {"status": "filled", "filled_qty": "0"})
        for change in changes:
            with self.subTest(change=change):
                broker.remote_orders[:] = [{**original, **change}]
                result = self.trading.reconcile(self.providers)
                self.assertTrue(result["errors"])
                self.assertEqual(self.order(order["id"])["filled_quantity"], 0)
                self.assertEqual(self.order(order["id"])["broker_id"], original["id"])
                self.assertEqual(self.trading.snapshot()["fills"], [])

    def test_terminal_broker_receipt_does_not_regress_or_drop_late_measured_fill(self):
        broker, book = self.broker_book()
        order = self.intent(qty=2, book=book)
        self.process()
        self.trading.cancel_intent(order["id"])
        self.process()
        self.trading.reconcile(self.providers)
        completed = self.order(order["id"])["completed_at"]
        remote = broker.remote_orders[0]
        remote["status"] = "accepted"
        self.trading.reconcile(self.providers)
        self.assertEqual(self.order(order["id"])["status"], "cancelled")
        self.assertEqual(self.order(order["id"])["completed_at"], completed)
        remote.update(status="partially_filled", filled_qty="1", filled_avg_price="10")
        broker.cash = "990"
        broker.remote_positions = [{"symbol": "AAPL", "qty": "1", "avg_entry_price": "10", "side": "long"}]
        self.assertFalse(self.trading.reconcile(self.providers)["errors"])
        self.assertEqual(self.order(order["id"])["status"], "cancelled")
        self.assertEqual(self.order(order["id"])["filled_quantity"], 1)
        self.assertEqual(self.order(order["id"])["completed_at"], completed)
        self.assertEqual(self.book(book)["account"]["reserved_cash"], 0)
        self.assertEqual(len(self.trading.snapshot()["fills"]), 1)

    def test_fractional_broker_deltas_preserve_subcent_receipts_and_positive_prices(self):
        broker, book = self.broker_book()
        order = self.intent(qty=1, book=book)
        self.process()
        remote = broker.remote_orders[0]
        for cumulative in ("0.0001", "0.0005", "0.001", "1"):
            remote.update(status="filled" if cumulative == "1" else "partially_filled", filled_qty=cumulative, filled_avg_price="10")
            broker.remote_positions = [{"symbol": "AAPL", "qty": cumulative, "avg_entry_price": "10", "side": "long"}]
            broker.cash = str(Decimal(1000) - Decimal(cumulative) * 10)
            self.assertFalse(self.trading.reconcile(self.providers)["errors"])
        fills = self.trading.snapshot()["fills"]
        self.assertEqual(len(fills), 4)
        self.assertTrue(all(fill["price"] == 10 for fill in fills))
        self.assertTrue(any(fill["notional"] == 0 for fill in fills))
        self.assertEqual(sum(fill["notional_cents"] for fill in fills), 1000)
        self.assertEqual(self.order(order["id"])["filled_quantity"], 1)
        self.assertEqual(self.trading.reconcile(self.providers)["fills"], 0)

    def test_nine_decimal_owned_broker_orphan_is_observed_without_rounding(self):
        broker, book = self.broker_book()
        ts = datetime.now(UTC).isoformat()
        broker.remote_orders = [{"id": "fractional-owned", "client_order_id": "aster_fractional-owned", "symbol": "AAPL", "side": "buy", "qty": "0.123456789", "type": "market", "time_in_force": "gtc", "status": "filled", "filled_qty": "0.123456789", "filled_avg_price": "10", "submitted_at": ts, "filled_at": ts}]
        broker.remote_positions = [{"symbol": "AAPL", "qty": "0.123456789", "avg_entry_price": "10", "side": "long"}]
        self.assertFalse(self.trading.reconcile(self.providers)["errors"])
        with self.store.connect() as con:
            self.assertEqual(Decimal(con.execute("SELECT quantity FROM p_fills WHERE book_id=?", (book,)).fetchone()[0]), Decimal("0.123456789"))
        with self.assertRaises(DeskError):
            self.intent(qty="0.123456789", key="operator-still-six")

    def test_reconciliation_observation_time_follows_completed_provider_reads(self):
        broker, book = self.broker_book()
        beginning = datetime.now(UTC)
        completed = beginning + timedelta(seconds=30)
        with patch("backend.trading.clock_time", side_effect=[beginning, completed]):
            self.assertFalse(self.trading.reconcile(self.providers)["errors"])
        truth = next(row for row in self.trading.snapshot()["broker_truth"] if row["book_id"] == book)
        self.assertEqual(truth["observed_at"], completed.isoformat())
        self.trading.reconcile(self.providers, beginning)
        truth = next(row for row in self.trading.snapshot()["broker_truth"] if row["book_id"] == book)
        self.assertEqual(truth["observed_at"], beginning.isoformat())

    def test_execution_fence_is_atomic_with_each_local_fill(self):
        self.fund()
        self.quote()
        first = self.intent(qty=1, key="first")
        second = self.intent(qty=1, key="second")
        original = self.trading._fill
        def fill_then_pause(con, *args, **kwargs):
            result = original(con, *args, **kwargs)
            self.store.setting(con, "fixture_running", False)
            return result
        def fence(con):
            self.assertTrue(con.in_transaction)
            if not self.store.settings(con).get("fixture_running", True):
                exc = DeskError("Operator paused")
                exc.paused = True
                raise exc
        self.providers.execution_fence = fence
        with patch.object(self.trading, "_fill", fill_then_pause):
            with self.assertRaisesRegex(DeskError, "paused"):
                self.process()
        self.assertEqual(self.order(first["id"])["status"], "filled")
        self.assertEqual(self.order(second["id"])["status"], "queued")
        self.assertEqual(len(self.trading.snapshot()["fills"]), 1)

    def test_local_reconciliation_uses_mutation_order_when_wall_clock_moves_backwards(self):
        self.fund()
        beginning = datetime.now(UTC)
        for index, (side, qty, price, offset) in enumerate((("buy", 10, 10, 0), ("buy", 10, 20, 1), ("sell", 5, 25, -1))):
            self.quote(price)
            self.intent(side, qty, str(index))
            self.assertEqual(self.trading.process(self.providers, beginning + timedelta(seconds=offset))["fills"], 1)
        self.assertEqual(self.book()["account"]["realized_pnl"], 50)
        self.assertFalse(self.trading.reconcile(self.providers)["errors"])

    def test_owned_orphan_replay_normalizes_source_timezones_before_ordering(self):
        broker, book = self.broker_book()
        rows = []
        records = (("buy", 10, 10, "2026-10-08T10:00:00+02:00"), ("buy", 10, 20, "2026-10-08T09:00:00+00:00"), ("sell", 5, 25, "2026-10-08T10:00:00+00:00"))
        for index, (side, qty, price, ts) in enumerate(records):
            rows.append({"id": f"tz-{index}", "client_order_id": f"aster_tz-{index}", "symbol": "AAPL", "side": side, "qty": str(qty), "type": "market", "time_in_force": "gtc", "status": "filled", "filled_qty": str(qty), "filled_avg_price": str(price), "submitted_at": ts, "filled_at": ts})
        broker.remote_orders = list(reversed(rows))
        broker.remote_positions = [{"symbol": "AAPL", "qty": "15", "avg_entry_price": "15", "side": "long"}]
        broker.cash = "825"
        self.assertFalse(self.trading.reconcile(self.providers)["errors"])
        self.assertIsNone(self.book(book)["account"]["realized_pnl"])
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT realized_cents FROM p_books WHERE id=?", (book,)).fetchone()[0], 5000)
        position = next(row for row in self.trading.snapshot()["positions"] if row["book_id"] == book)
        self.assertEqual(position["average_cost"], 15)
        self.assertFalse(position["locked"])

    def test_same_quantity_broker_notional_correction_preserves_prior_ledger(self):
        broker, book = self.broker_book()
        order = self.intent(qty=1, book=book)
        self.process()
        broker.remote_orders[0].update(status="filled", filled_qty="1", filled_avg_price="10")
        broker.remote_positions = [{"symbol": "AAPL", "qty": "1", "avg_entry_price": "10", "side": "long"}]
        broker.cash = "990"
        self.assertFalse(self.trading.reconcile(self.providers)["errors"])
        broker.remote_orders[0]["filled_avg_price"] = "11"
        self.assertTrue(self.trading.reconcile(self.providers)["errors"])
        self.assertEqual(self.order(order["id"])["filled_notional"], 10)
        self.assertEqual(self.book(book)["account"]["cash"], 990)
        self.assertEqual(len(self.trading.snapshot()["fills"]), 1)

    def test_completed_broker_fill_never_becomes_a_cancellation(self):
        broker, book = self.broker_book()
        order = self.intent(qty=1, book=book)
        self.process()
        broker.remote_orders[0].update(status="filled", filled_qty="1", filled_avg_price="10")
        broker.remote_positions = [{"symbol": "AAPL", "qty": "1", "avg_entry_price": "10", "side": "long"}]
        broker.cash = "990"
        self.trading.reconcile(self.providers)
        broker.remote_orders[0]["status"] = "canceled"
        self.trading.reconcile(self.providers)
        self.assertEqual(self.order(order["id"])["status"], "filled")
        self.assertEqual(self.order(order["id"])["broker_status"], "canceled")

    def test_native_protective_quantity_shrink_is_adopted_but_increase_is_refused(self):
        broker, book = self.broker_book()
        parent = self.intent(qty=10, book=book, stop_loss=9)
        self.process()
        remote = broker.remote_orders[0]
        ts = datetime.now(UTC).isoformat()
        leg = {"id": "shrinking-stop", "client_order_id": "native-stop", "symbol": "AAPL", "side": "sell", "qty": "10", "type": "stop", "stop_price": "9", "time_in_force": "gtc", "status": "accepted", "filled_qty": "0", "submitted_at": ts}
        remote.update(status="filled", filled_qty="10", filled_avg_price="10", order_class="bracket", legs=[leg])
        broker.remote_positions = [{"symbol": "AAPL", "qty": "10", "avg_entry_price": "10", "side": "long"}]
        broker.cash = "900"
        self.assertFalse(self.trading.reconcile(self.providers)["errors"])
        child = next(row for row in self.trading.snapshot()["intents"] if row["parent_id"] == parent["id"])
        leg["qty"] = "6.123456789"
        self.assertFalse(self.trading.reconcile(self.providers)["errors"])
        self.assertEqual(self.order(child["id"])["quantity"], 6.123456789)
        self.assertEqual(self.order(child["id"])["reserved_quantity"], 6.123456789)
        leg["qty"] = "11"
        self.assertTrue(self.trading.reconcile(self.providers)["errors"])
        self.assertEqual(self.order(child["id"])["quantity"], 6.123456789)

    def test_cumulative_broker_order_chronology_withholds_basis_dependent_realized_values(self):
        broker, book = self.broker_book()
        self.quote(20)
        broker.remote_orders = [
            {"id": "buy-two", "client_order_id": "aster_buy-two", "symbol": "AAPL", "side": "buy", "qty": "2", "type": "market", "time_in_force": "gtc", "status": "filled", "filled_qty": "2", "filled_avg_price": "15", "submitted_at": "2026-10-08T10:00:00Z", "filled_at": "2026-10-08T10:02:00Z"},
            {"id": "sell-one", "client_order_id": "aster_sell-one", "symbol": "AAPL", "side": "sell", "qty": "1", "type": "market", "time_in_force": "gtc", "status": "filled", "filled_qty": "1", "filled_avg_price": "20", "submitted_at": "2026-10-08T10:01:00Z", "filled_at": "2026-10-08T10:01:00Z"},
        ]
        broker.remote_positions = [{"symbol": "AAPL", "qty": "1", "avg_entry_price": "20", "side": "long"}]
        broker.cash = "990"
        self.assertFalse(self.trading.reconcile(self.providers)["errors"])
        state = self.trading.snapshot()
        account = next(row["account"] for row in state["books"] if row["id"] == book)
        position = next(row for row in state["positions"] if row["book_id"] == book)
        self.assertIsNone(account["realized_pnl"])
        self.assertEqual(account["realized_pnl_coverage"]["status"], "withheld")
        self.assertIsNone(position["realized_pnl"])
        self.assertEqual((position["average_cost"], position["cost_basis"], position["unrealized_pnl"]), (20, 20, 0))
        self.assertEqual(position["cost_basis_coverage"]["status"], "known")
        self.assertTrue(position["locked"])
        self.assertTrue(all(fill["realized_pnl"] is None and fill["realized_cents"] is None for fill in state["fills"] if fill["book_id"] == book))
        events = [event for event in self.store.snapshot({})["events"] if event["event_type"] == "autonomous_paper_fill" and event["payload"].get("book_id") == book]
        self.assertTrue(events)
        self.assertTrue(all(event["payload"]["realized_pnl"] is None for event in events))
        # The order aggregate reconstructs $5, while the possible true source
        # sequence buy 1@$10, sell 1@$20, buy 1@$20 realizes $10. Preserve the
        # internal estimate as evidence, but never present it as verified P&L.
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT realized_cents FROM p_books WHERE id=?", (book,)).fetchone()[0], 500)

    def test_broker_basis_waits_for_complete_position_truth_after_transport_fill(self):
        broker, book = self.broker_book()
        entry = self.intent(qty=1, book=book)
        self.process()
        remote = broker.remote_orders[0]
        remote.update(status="filled", filled_qty="1", filled_avg_price="10")
        with self.store.transaction() as con:
            intent = con.execute("SELECT * FROM p_intents WHERE id=?", (entry["id"],)).fetchone()
            self.trading._apply_remote_order(con, intent, remote, datetime.now(UTC))
        position = next(row for row in self.trading.snapshot()["positions"] if row["book_id"] == book)
        self.assertIsNone(position["average_cost"])
        self.assertIsNone(position["cost_basis"])
        self.assertIsNone(position["unrealized_pnl"])
        self.assertEqual(position["cost_basis_coverage"]["status"], "withheld")
        self.assertIsNone(self.book(book)["account"]["unrealized_pnl"])
        broker.remote_positions = [{"symbol": "AAPL", "qty": "1", "avg_entry_price": "10", "side": "long"}]
        broker.cash = "990"
        self.assertFalse(self.trading.reconcile(self.providers)["errors"])
        position = next(row for row in self.trading.snapshot()["positions"] if row["book_id"] == book)
        self.assertEqual((position["average_cost"], position["cost_basis"], position["unrealized_pnl"]), (10, 10, 0))


if __name__ == "__main__":
    unittest.main()
