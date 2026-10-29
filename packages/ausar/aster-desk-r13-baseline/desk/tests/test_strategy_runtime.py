"""Family isolation, supervisor ordering and source-neutral registry projection."""
import hashlib
import json
import base64
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from backend.store import DeskError, Store
from backend.providers import exchange_calendar
from backend.strategy_contract import installed_strategies
from backend.strategy_runtime import StrategyRuntimeManager, _EmptyTraderRuntime
from backend.trading import TradingDesk


SCHEMA = """(id TEXT PRIMARY KEY,sleeve TEXT NOT NULL,book_id TEXT NOT NULL UNIQUE,
enabled INTEGER NOT NULL,config TEXT NOT NULL,config_sha256 TEXT NOT NULL,
created_at TEXT NOT NULL,updated_at TEXT NOT NULL)"""


class FakeRuntime:
    def __init__(self, family, calls, rows=(), priority=False):
        self.family, self.calls, self.rows, self.priority = family, calls, list(rows), priority
        self.actions = None

    def snapshot(self):
        return {"installations": self.rows, "definitions": [{"id": self.family}],
                "decisions": [{"id": self.family, "created_at": "2026-10-09T15:00:00+00:00"}],
                "strategy_count": len(self.rows), "status": "installed" if self.rows else "empty"}

    def install(self, config):
        self.calls.append((self.family, "install", config))
        return {"id": config.get("id", "default"), "config": config}

    def set_enabled(self, rid, enabled):
        self.calls.append((self.family, "enable", rid, enabled))
        return {"id": rid, "enabled": enabled}

    def _h1_window_priority(self, installs, clock):
        self.calls.append((self.family, "priority", len(installs)))
        return self.priority

    def run_once(self, **kwargs):
        self.calls.append((self.family, "run", kwargs))
        return {"status": "ok", "entries": 1, "acquired": 2, "errors": []}

    def service_exits(self, **kwargs):
        self.calls.append((self.family, "exits", kwargs))
        return {"status": "ok", "exits": 1, "observed_periods": 2, "errors": []}

    def prepare_fills(self, **kwargs):
        self.calls.append((self.family, "prepare", kwargs))
        return {"status": "ok", "cancelled": 0, "fills_safe": True, "errors": []}


class FakeTrading:
    def __init__(self, calls):
        self.calls = calls

    def process(self, providers, clock=None):
        self.calls.append(("execution", "process", {"providers": providers, "clock": clock}))
        return {"processed": 0, "fills": 0, "submitted": 0, "errors": []}


class FixtureProviders:
    broker = None

    def calendar(self, clock=None):
        return exchange_calendar(clock)


class StrategyCompositionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "composition.sqlite")
        self.calls = []
        self.tensor = FakeRuntime("tensor", self.calls)
        self.trader = FakeRuntime("trader", self.calls)
        self.trading = FakeTrading(self.calls)
        self.manager = StrategyRuntimeManager(self.store, self.trading, None, tensor=self.tensor, trader=self.trader)

    def tearDown(self):
        self.temp.cleanup()

    def insert(self, table, rid, book, config, enabled=True):
        raw = json.dumps(config, sort_keys=True, separators=(",", ":"), allow_nan=False)
        with self.store.transaction() as con:
            con.execute("CREATE TABLE IF NOT EXISTS " + table + SCHEMA)
            con.execute("INSERT INTO " + table + " VALUES(?,?,?,?,?,?,?,?)",
                        (rid, config.get("sleeve", rid), book, enabled, raw,
                         hashlib.sha256(raw.encode()).hexdigest(), "2026-10-09", "2026-10-09"))
        return raw

    def test_explicit_family_dispatch_preserves_legacy_config_bytes(self):
        original = {"id": "legacy", "sleeve": "H1STATE", "book_id": "book"}
        self.manager.install(original)
        self.manager.install({**original, "family": "tensor"})
        self.assertEqual(self.calls[0][2], original)
        self.assertEqual(self.calls[1][2], original)
        result = self.manager.install({"family": "trader", "id": "new", "rule_id": "public"})
        self.assertEqual(result["family"], "trader")
        self.assertEqual(self.calls[-1][0], "trader")
        self.assertNotIn("family", self.calls[-1][2])
        for value in (None, [], {}, "model", True):
            with self.subTest(value=value), self.assertRaises(DeskError) as error:
                self.manager.install({"family": value})
            self.assertEqual(error.exception.status, 422)

    def test_cross_family_id_and_book_collisions_are_rejected_before_dispatch(self):
        self.insert("a_tensor_installations", "existing", "owned", {"frame": "1h", "symbols": ["AMD"]})
        for config in ({"id": "existing", "book_id": "new"}, {"id": "new", "book_id": "owned"}):
            with self.subTest(config=config), self.assertRaises(DeskError):
                self.manager.install({"family": "trader", **config})
        self.assertEqual(self.calls, [])

    def test_enable_routes_owned_family_and_rejects_ambiguous_identity(self):
        self.insert("a_tensor_installations", "tensor-id", "tensor-book", {})
        self.insert("a_trader_installations", "trader-id", "trader-book", {})
        self.assertEqual(self.manager.set_enabled("trader-id", False)["family"], "trader")
        self.assertEqual(self.manager.set_enabled("tensor-id", True)["family"], "tensor")
        with self.assertRaises(DeskError):
            self.manager.set_enabled("trader-id", "false")
        self.insert("a_trader_installations", "tensor-id", "other-book", {})
        with self.assertRaises(DeskError):
            self.manager.set_enabled("tensor-id", False)

    def test_h1_priority_preserves_existing_first_and_blocks_only_new_broad_acquisition(self):
        raw = self.insert("a_tensor_installations", "hourly", "hourly-book", {"frame": "1h", "symbols": ["AMD"]})
        self.tensor.priority = True
        guard, provider = object(), object()
        result = self.manager.run_once(clock="2026-10-09T15:30:00+00:00", transaction_guard=guard, providers=provider)
        self.assertEqual(self.calls[0][0:2], ("tensor", "run"))
        self.assertEqual(self.calls[1][0:2], ("trader", "prepare"))
        self.assertEqual(self.calls[2][0:2], ("execution", "process"))
        trader_call = next(call for call in self.calls if call[:2] == ("trader", "run"))
        self.assertFalse(trader_call[2]["allow_acquisition"])
        self.assertIs(trader_call[2]["transaction_guard"], guard)
        self.assertIs(trader_call[2]["providers"], provider)
        self.assertEqual(result["entries"], 2)
        self.assertTrue(result["trader_broad_acquisition_deferred_for_tensor_h1"])
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT config FROM a_tensor_installations").fetchone()[0], raw)
        self.calls.clear()
        self.tensor.priority = False
        self.manager.run_once(clock="2026-10-09T16:00:00+00:00")
        self.assertTrue(next(call for call in self.calls if call[:2] == ("trader", "run"))[2]["allow_acquisition"])

    def test_both_owned_exit_passes_keep_fence_even_when_entries_disabled(self):
        self.tensor.rows = [{"id": "tensor", "enabled": False}]
        self.trader.rows = [{"id": "trader", "enabled": False}]
        guard = object()
        self.manager.actions = "shared-action-service"
        self.assertEqual(self.tensor.actions, self.trader.actions)
        for acquire in (False, True):
            self.calls.clear()
            result = self.manager.service_exits(clock="2026-10-09T15:30:00+00:00",
                                                transaction_guard=guard, acquire_native_clocks=acquire)
            self.assertEqual(result["exits"], 2)
            self.assertEqual(result["observed_periods"], 4)
            self.assertEqual([call[:2] for call in self.calls], [("tensor", "exits"), ("trader", "prepare"),
                            ("execution", "process"), ("trader", "exits"), ("trader", "prepare")])
            for call in (call for call in self.calls if call[1] == "exits"):
                self.assertEqual(call[2]["acquire_native_clocks"], acquire)
                self.assertIs(call[2]["transaction_guard"], guard)

    def test_schema_neutral_registry_verifies_both_configs_and_omits_arbitrary_fields(self):
        self.assertEqual(installed_strategies(self.store), ())
        self.insert("a_tensor_installations", "t", "bt", {"frame": "1h", "symbols": ["AMD"], "private_note": "omit"})
        self.insert("a_trader_installations", "r", "br", {"frame": "1d", "symbols": ["SPY", "QQQ"], "rule_id": "public", "rules_sha256": "pin", "private_note": "omit"})
        registry = installed_strategies(self.store)
        self.assertEqual(len(registry), 2)
        self.assertEqual({row["family"] for row in registry}, {"tensor", "trader"})
        for row in registry:
            self.assertEqual(row["config_status"], "verified")
            self.assertNotIn("private_note", row)
            self.assertNotIn("config", row)
        with self.store.transaction() as con:
            con.execute("UPDATE a_trader_installations SET config_sha256='mismatch'")
        self.assertEqual(installed_strategies(self.store)[0]["config_status"], "identity_mismatch")

    def test_empty_projection_does_not_create_public_schema_or_financial_state(self):
        manager = StrategyRuntimeManager(self.store, None, None, tensor=FakeRuntime("tensor", []), trader=_EmptyTraderRuntime())
        self.assertEqual(manager.snapshot()["strategy_count"], 0)
        self.assertEqual(installed_strategies(self.store), ())
        with self.store.connect() as con:
            self.assertIsNone(con.execute("SELECT 1 FROM sqlite_master WHERE name='a_trader_installations'").fetchone())

    def test_one_family_data_failure_does_not_strand_other_owned_exits(self):
        with patch.object(self.tensor, "service_exits", side_effect=RuntimeError("credential must never be echoed")):
            result = self.manager.service_exits(acquire_native_clocks=False)
        self.assertEqual(result["status"], "data_blocked")
        self.assertEqual(result["exits"], 1)
        self.assertIn(("trader", "exits"), [call[:2] for call in self.calls])
        self.assertNotIn("credential", json.dumps(result))
        self.calls.clear()
        with patch.object(self.trader, "service_exits", side_effect=ValueError("signed secret URL")):
            result = self.manager.service_exits(acquire_native_clocks=True)
        self.assertEqual(result["status"], "data_blocked")
        self.assertEqual(result["exits"], 1)
        self.assertEqual(self.calls[0][0:2], ("tensor", "exits"))
        self.assertNotIn("signed secret", json.dumps(result))

    def test_bounded_run_records_component_fault_and_still_services_other_family(self):
        with patch.object(self.tensor, "run_once", side_effect=RuntimeError("secret")):
            result = self.manager.run_once(clock="2026-10-09T16:00:00+00:00")
        self.assertEqual(result["status"], "data_blocked")
        self.assertEqual(result["entries"], 1)
        self.assertIn(("trader", "run"), [call[:2] for call in self.calls])
        self.assertNotIn("secret", json.dumps(result))

    def test_fence_loss_or_pause_propagates_before_other_family_can_originate_orders(self):
        for flag in ("tensor_fence_failure", "trader_fence_failure", "paused"):
            with self.subTest(flag=flag):
                failure = DeskError("Execution authority lost")
                setattr(failure, flag, True)
                self.calls.clear()
                with patch.object(self.tensor, "run_once", side_effect=failure), self.assertRaises(DeskError):
                    self.manager.run_once()
                self.assertEqual(self.calls, [])
                with patch.object(self.tensor, "service_exits", side_effect=failure), self.assertRaises(DeskError):
                    self.manager.service_exits()
                self.assertEqual(self.calls, [])

    def test_priority_failure_blocks_broad_acquisition_and_marks_result_failed(self):
        with patch.object(self.manager, "_tensor_opening_priority", side_effect=ValueError("bad cache")):
            result = self.manager.run_once()
        self.assertFalse(next(call for call in self.calls if call[:2] == ("trader", "run"))[2]["allow_acquisition"])
        self.assertEqual(result["status"], "data_blocked")
        self.assertTrue(result["errors"])

    def test_public_process_fills_timely_tensor_intent_before_other_family_io_and_expires_late_one(self):
        trading, providers = TradingDesk(self.store), FixtureProviders()
        for offset, expected in (("15:34:59", "filled"), ("15:35:00", "expired")):
            with self.subTest(clock=offset):
                clock = datetime.fromisoformat("2026-10-09T" + offset + "+00:00")
                book = trading.create_book({"name": expected, "kind": "forward", "broker": "local"})["id"]
                trading.fund_book(book, 1000, "fund-" + expected)
                installation = "tensor-test-" + expected
                trading.claim_strategy_book(book, installation)
                with self.store.transaction() as con:
                    con.execute("INSERT OR REPLACE INTO quotes VALUES(?,?,?,?)",
                                ("AMD", "10", clock.isoformat(), "Synthetic quote fixture"))
                intent = trading.submit_strategy_intent({"book_id": book, "symbol": "AMD", "side": "buy",
                    "quantity": 1, "client_id": "timing-" + expected, "order_type": "market", "time_in_force": "day",
                    "not_before": "2026-10-09T15:30:00+00:00", "expires_at": "2026-10-09T15:35:00+00:00"},
                    installation, clock=clock)
                manager = StrategyRuntimeManager(self.store, trading, providers, tensor=self.tensor, trader=self.trader)
                guards = []
                def fence(con):
                    self.assertTrue(con.in_transaction)
                    guards.append("writer")
                def observe_before_io(**kwargs):
                    with self.store.connect() as con:
                        self.assertEqual(con.execute("SELECT status FROM p_intents WHERE id=?", (intent["id"],)).fetchone()[0], expected)
                        fill_count = con.execute("SELECT COUNT(*) FROM p_fills WHERE intent_id=?", (intent["id"],)).fetchone()[0]
                        self.assertEqual(fill_count, int(expected == "filled"))
                    return {"status": "ok", "entries": 0, "errors": []}
                with patch.object(self.trader, "run_once", side_effect=observe_before_io):
                    result = manager.run_once(clock=clock, transaction_guard=fence)
                self.assertTrue(guards)
                self.assertEqual(result["process_between_families"]["fills"], int(expected == "filled"))

    def test_raw_provider_is_fenced_at_real_fill_boundary_and_no_fill_after_loss(self):
        trading, providers = TradingDesk(self.store), FixtureProviders()
        clock = datetime(2026, 10, 9, 15, 30, tzinfo=timezone.utc)
        book = trading.create_book({"name": "Fence fixture", "kind": "forward", "broker": "local"})["id"]
        trading.fund_book(book, 1000, "fence-fund")
        trading.claim_strategy_book(book, "fence-installed")
        with self.store.transaction() as con:
            con.execute("INSERT OR REPLACE INTO quotes VALUES(?,?,?,?)", ("AMD", "10", clock.isoformat(), "Synthetic quote fixture"))
        trading.submit_strategy_intent({"book_id": book, "symbol": "AMD", "side": "buy", "quantity": 1,
                                       "client_id": "fenced", "order_type": "market", "time_in_force": "gtc"},
                                      "fence-installed", clock=clock)
        manager = StrategyRuntimeManager(self.store, trading, providers, tensor=self.tensor, trader=self.trader)
        def lost(con):
            self.assertTrue(con.in_transaction)
            raise DeskError("Lease lost")
        self.calls.clear()
        with self.assertRaises(DeskError) as error:
            manager.run_once(clock=clock, transaction_guard=lost)
        self.assertTrue(getattr(error.exception, "trader_fence_failure", False))
        self.assertNotIn(("trader", "run"), [call[:2] for call in self.calls])
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_fills").fetchone()[0], 0)

    def test_intermediate_process_fault_is_visible_and_preserves_other_owned_service(self):
        with patch.object(self.trading, "process", side_effect=RuntimeError("private signed URL")):
            result = self.manager.service_exits()
        self.assertEqual(result["exits"], 2)
        self.assertEqual(result["status"], "data_blocked")
        self.assertTrue(result["process_between_families"]["errors"])
        self.assertNotIn("signed URL", json.dumps(result))

    def test_direct_and_http_export_preserve_new_rule_state_and_exact_blob_bytes(self):
        from fastapi.testclient import TestClient
        from backend.app import create_app
        app = create_app(Path(self.temp.name) / "export.sqlite", start_worker=False)
        blob = b"\x00\xff\x80public-rule-native-receipt\x00"
        with app.state.store.transaction() as con:
            con.execute("CREATE TABLE a_trader_export_fixture(id TEXT PRIMARY KEY,data BLOB NOT NULL)")
            con.execute("INSERT INTO a_trader_export_fixture VALUES(?,?)", ("exact", blob))
        direct = app.state.store.export({"configured": False})
        direct_value = direct["tables"]["a_trader_export_fixture"][0]["data"]
        self.assertEqual(direct_value["bytes"], len(blob))
        self.assertEqual(base64.b64decode(direct_value["data"], validate=True), blob)
        with TestClient(app) as client:
            exported = client.get("/api/export")
            self.assertEqual(exported.status_code, 200)
            http_value = exported.json()["autonomous_tables"]["a_trader_export_fixture"][0]["data"]
            self.assertEqual(http_value, direct_value)

    def _real_trader_fixture(self):
        from backend.trader_runtime import TraderRuntimeManager
        from tests.test_trader_runtime import Source, OPEN
        trading = TradingDesk(self.store)
        source = Source(self.store, ["AAA", "BBB"])
        definitions = {"risk-fixture": {"sleeve": "RISKFIXTURE", "name": "Two-share recovery fixture",
            "symbols": ["AAA", "BBB"], "minimum_bars": 252, "max_hold_bars": 20, "rule_config": {"frozen": 1}}}
        def evaluator(rule_id, bars, rule_config, held_symbols=()):
            return {"candidates": [{"symbol": sym, "score": 1, "dollar_volume20": 100000000,
                    "reason": "Causal risk fixture", "stop_distance": 10, "risk_budget_fraction": .005}
                    for sym in ("AAA", "BBB")], "exits": []}
        trader = TraderRuntimeManager(self.store, trading, source, evaluator=evaluator, definitions=definitions)
        book = trading.create_book({"name": "Risk recovery book", "kind": "forward", "broker": "local"})["id"]
        trading.set_book(book, {"policy": {"slippage_bps": 10}})
        trading.fund_book(book, 4000, "recovery-fund")
        trader.install({"id": "recovery-install", "rule_id": "risk-fixture", "book_id": book,
                        "enabled": True, "max_fetch_per_run": 16})
        self.assertEqual(trader.run_once(OPEN)["entries"], 2)
        manager = StrategyRuntimeManager(self.store, trading, source, tensor=self.tensor, trader=trader)
        return trading, source, trader, manager, book, OPEN

    def test_all_composite_and_outer_fill_boundaries_cancel_first_partial_before_doubled_quote(self):
        trading, source, trader, manager, book, clock = self._real_trader_fixture()
        # Simulate an operator policy race after admission/preflight and before
        # the previous public outer fill. This first measured partial is real
        # paper-engine evidence, rather than an inserted fill or position.
        trading.set_book(book, {"policy": {"max_fill_quantity": 1}})
        self.assertEqual(trading.process(source, clock)["fills"], 2)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_intents WHERE status='partially_filled'").fetchone()[0], 2)
        source.clock, source.price = clock + timedelta(seconds=3), Decimal(100)
        source.refresh(["AAA", "BBB"])
        passes = [manager.service_exits(clock=source.clock, acquire_native_clocks=False),
                  manager.service_exits(clock=source.clock, acquire_native_clocks=True),
                  manager.run_once(clock=source.clock)]
        for result in passes:
            self.assertEqual(result["process_between_families"]["fills"], 0)
            self.assertTrue(result["process_between_families"]["trader_fill_recovery"]["fills_safe"])
            self.assertTrue(result["trader_fill_recovery_after_component"]["fills_safe"])
            self.assertEqual(trading.process(source, source.clock)["fills"], 0)
        self.assertEqual(passes[0]["process_between_families"]["trader_fill_recovery"]["cancelled"], 2)
        with self.store.connect() as con:
            fills = list(con.execute("SELECT * FROM p_fills ORDER BY rowid"))
            self.assertEqual(len(fills), 2)
            for fill in fills:
                self.assertEqual(Decimal(fill["quantity"]), 1)
                self.assertEqual(Decimal(fill["price"]), Decimal("50.050"))
            intents = list(con.execute("SELECT * FROM p_intents WHERE book_id=?", (book,)))
            for intent in intents:
                self.assertEqual(intent["status"], "cancelled")
                self.assertEqual(Decimal(intent["quantity"]), 2)
                self.assertEqual(Decimal(intent["filled_quantity"]), 1)
                self.assertEqual(intent["reserved_cents"], 0)
                self.assertEqual(Decimal(intent["reserved_quantity"]), 0)
            states = list(con.execute("SELECT * FROM a_trader_position_state"))
            self.assertEqual(len(states), 2)
            for state in states:
                self.assertEqual(Decimal(state["initial_stop_price"]), Decimal("40.050"))
                self.assertEqual(Decimal(state["stop_distance"]), 10)
                position = con.execute("SELECT * FROM p_positions WHERE book_id=? AND symbol=?", (book, state["symbol"])).fetchone()
                self.assertEqual(Decimal(position["quantity"]), 1)
                self.assertLessEqual(Decimal(position["quantity"]) * Decimal(state["stop_distance"]), Decimal(20))
                hypothetical_second_fill_risk = Decimal(10) + Decimal("100.10") - Decimal(state["initial_stop_price"])
                self.assertGreater(hypothetical_second_fill_risk, Decimal(20))

    def test_changed_partial_policy_is_cancelled_before_first_composite_fill(self):
        trading, source, trader, manager, book, clock = self._real_trader_fixture()
        trading.set_book(book, {"policy": {"max_fill_quantity": 1}})
        result = manager.run_once(clock=clock)
        self.assertEqual(result["process_between_families"]["trader_fill_recovery"]["cancelled"], 2)
        self.assertEqual(result["process_between_families"]["fills"], 0)
        self.assertEqual(trading.process(source, clock)["fills"], 0)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_fills").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_positions").fetchone()[0], 0)

    def test_recovery_failure_aborts_before_intermediate_or_outer_financial_process(self):
        for failure in (RuntimeError("private signed URL"), {"status": "data_blocked", "fills_safe": False, "errors": ["unsafe"]}):
            with self.subTest(failure=type(failure).__name__):
                self.calls.clear()
                kwargs = {"side_effect": failure} if isinstance(failure, Exception) else {"return_value": failure}
                with patch.object(self.trader, "prepare_fills", **kwargs), self.assertRaises(DeskError) as error:
                    self.manager.run_once()
                self.assertEqual(error.exception.status, 503)
                self.assertNotIn("signed URL", str(error.exception))
                self.assertNotIn(("execution", "process"), [call[:2] for call in self.calls])
                self.assertNotIn(("trader", "run"), [call[:2] for call in self.calls])

    def test_managed_invalid_book_errors_do_not_strand_healthy_family_after_quarantine(self):
        receipt = {"status": "data_blocked", "fills_safe": True, "cancelled": 1,
                   "errors": [{"installation_id": "bad-rule", "reason": "quarantined"}]}
        with patch.object(self.trader, "prepare_fills", return_value=receipt):
            result = self.manager.service_exits()
        self.assertEqual(result["exits"], 2)
        self.assertEqual(result["status"], "data_blocked")
        self.assertIn(("execution", "process"), [call[:2] for call in self.calls])

    def test_recovery_fence_loss_propagates_before_fills(self):
        failure = DeskError("Lease lost during recovery")
        failure.trader_fence_failure = True
        with patch.object(self.trader, "prepare_fills", side_effect=failure), self.assertRaises(DeskError) as error:
            self.manager.service_exits()
        self.assertIs(error.exception, failure)
        self.assertNotIn(("execution", "process"), [call[:2] for call in self.calls])


if __name__ == "__main__":
    unittest.main()
