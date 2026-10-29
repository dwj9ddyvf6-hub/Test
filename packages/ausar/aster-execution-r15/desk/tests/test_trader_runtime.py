import copy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from backend.providers import exchange_calendar
from backend.store import DeskError, Store
from backend.tensor_runtime import _dt, _ms, _native_period, _session, _sessions, latest_native_clock
from backend.tensor_actions import TensorActions
from backend.trader_runtime import TraderRuntimeManager
from backend.trading import TradingDesk

UTC = timezone.utc
OPEN = datetime(2026, 10, 9, 13, 30, 2, tzinfo=UTC)


def payload(sym, clock, count=260):
    latest = latest_native_clock("1d", clock)
    rows = []
    for day in _sessions((clock.date() - timedelta(days=800)).isoformat(), clock.date().isoformat()):
        stamp = _ms(datetime.fromisoformat(day).replace(tzinfo=UTC))
        _, complete = _native_period(stamp, "1d")
        if complete <= latest["completed_at_ms"]:
            rows.append({"timestamp": _dt(stamp).isoformat(), "open": 50., "high": 51., "low": 49., "close": 50., "volume": 2000000.})
    rows = rows[-count:]
    digest = hashlib.sha256(json.dumps(rows).encode()).hexdigest()
    return {"symbol": sym, "interval": "1d", "provider": "fixture", "source": "Causal completed fixture",
            "adjustment": "raw OHLCV", "vendor_interval": "1d", "bars": rows,
            "revision_id": digest, "content_sha256": digest, "observed_at": clock.isoformat(), "fetched_at": clock.isoformat(),
            "provider_asof": rows[-1]["timestamp"], "truncated": False, "omitted_rows": 0,
            "stale_cache": False, "completeness": {"status": "complete_vendor_response"}}


class Source:
    kind = "fixture"
    broker = None
    brokers = {}

    def __init__(self, store, symbols, clock=OPEN):
        self.store, self.symbols, self.clock = store, symbols, clock
        self.data = {sym: payload(sym, clock) for sym in symbols}
        self.fail = set()
        self.calls = []
        self.price = Decimal(50)

    def bars(self, sym, period, interval):
        self.calls.append((sym, period, interval))
        if sym in self.fail:
            raise RuntimeError("Observed fixture outage")
        return copy.deepcopy(self.data[sym])

    def calendar(self, clock=None):
        return exchange_calendar(clock)

    def status(self):
        return {"kind": "fixture", "connected": True}

    def refresh(self, symbols):
        with self.store.transaction() as con:
            for sym in symbols:
                con.execute("INSERT OR REPLACE INTO quotes VALUES(?,?,?,?)", (sym, str(self.price), self.clock.isoformat(), "Observed fixture intraday trade"))

    def advance(self, clock):
        self.clock = clock
        self.data = {sym: payload(sym, clock) for sym in self.symbols}


class TraderRuntimeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "desk.sqlite")
        self.trading = TradingDesk(self.store)
        self.symbols = ["AAA", "BBB"]
        self.definition = {"test-rule": {"sleeve": "TEST", "name": "Test public rule", "symbols": self.symbols,
                           "minimum_bars": 252, "max_hold_bars": 2, "rule_config": {"frozen": 1}}}
        self.source = Source(self.store, self.symbols)
        self.exit_signal = False
        self.stop_distance = None
        self.runtime = self.make_runtime()

    def tearDown(self):
        self.temp.cleanup()

    def evaluate(self, rule_id, bars, rule_config, held_symbols=()):
        return {"candidates": [{"symbol": sym, "score": 1., "dollar_volume20": 100000000.,
                                "reason": "Test causal opportunity", "stop_distance": self.stop_distance,
                                "risk_budget_fraction": .005 if self.stop_distance else None} for sym in self.symbols],
                "exits": [{"symbol": sym, "reason": "frozen_close_exit"} for sym in held_symbols] if self.exit_signal else []}

    def make_runtime(self):
        return TraderRuntimeManager(self.store, self.trading, self.source, evaluator=self.evaluate, definitions=self.definition)

    def install(self, enabled=True, funded=True, **config):
        book = self.trading.create_book({"name": "Test book", "broker": "local", "kind": "forward"})
        self.trading.set_book(book["id"], {"policy": {"slippage_bps": 10}})
        if funded:
            self.trading.fund_book(book["id"], 100000, "test-capital")
        return self.runtime.install({"id": "test-install", "rule_id": "test-rule", "book_id": book["id"], "enabled": enabled, "max_fetch_per_run": 16, **config})

    def fills(self):
        with self.store.connect() as con:
            return [dict(row) for row in con.execute("SELECT * FROM p_fills ORDER BY rowid")]

    def test_empty_constructor_has_no_strategy_or_capital(self):
        self.assertEqual(self.runtime.snapshot()["strategy_count"], 0)
        self.assertEqual(self.runtime.run_once(OPEN)["status"], "empty")
        self.assertEqual(self.trading.snapshot()["books"][0]["account"]["cash"], 0)

    def test_install_claims_book_without_implicit_funding_and_is_idempotent(self):
        row = self.install(funded=False)
        repeat = self.runtime.install(row["config"])
        self.assertEqual(repeat["config_sha256"], row["config_sha256"])
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_strategy_ownership").fetchone()[0], 1)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_fundings").fetchone()[0], 0)
        changed = {**row["config"], "max_fetch_per_run": 8}
        with self.assertRaises(DeskError):
            self.runtime.install(changed)

    def test_configuration_rejects_parameter_universe_window_and_boolean_changes(self):
        book = self.trading.create_book({"name": "Empty", "broker": "local", "kind": "forward"})
        self.trading.set_book(book["id"], {"policy": {"slippage_bps": 10}})
        base = {"rule_id": "test-rule", "book_id": book["id"]}
        for change in ({"rule_config": {}}, {"symbols": ["AAA"]}, {"opening_window_seconds": 301}, {"enabled": 1}):
            with self.subTest(change=change), self.assertRaises(DeskError):
                self.runtime.install({**base, **change})

    def test_ranked_orders_have_whole_shares_cap_and_no_duplicate_restart(self):
        row = self.install()
        result = self.runtime.run_once(OPEN)
        self.assertEqual(result["entries"], 2)
        self.assertEqual(self.trading.process(self.source, OPEN)["fills"], 2)
        fills = self.fills()
        self.assertEqual(sorted(fill["symbol"] for fill in fills), self.symbols)
        for fill in fills:
            self.assertEqual(Decimal(fill["quantity"]), 199)
            self.assertLessEqual(fill["notional_cents"] + fill["fee_cents"], 1000000)
            self.assertEqual(Decimal(fill["price"]), Decimal("50.05"))
        self.runtime = self.make_runtime()
        self.assertEqual(self.runtime.run_once(OPEN)["entries"], 0)
        self.assertEqual(len(self.fills()), 2)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_trader_assessments").fetchone()[0], 1)

    def test_complete_census_failure_blocks_healthy_candidates(self):
        self.install()
        self.source.fail.add("BBB")
        result = self.runtime.run_once(OPEN)
        self.assertEqual(result["status"], "data_blocked")
        self.assertEqual(result["entries"], 0)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_intents").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_trader_source_receipts WHERE status='failed'").fetchone()[0], 1)

    def test_budget_and_priority_flag_prevent_broad_fetch(self):
        self.install(max_fetch_per_run=1)
        self.assertEqual(self.runtime.run_once(OPEN, allow_acquisition=False)["acquired"], 0)
        self.assertEqual(self.source.calls, [])
        self.assertEqual(self.runtime.run_once(OPEN)["acquired"], 1)
        self.assertEqual(self.runtime.run_once(OPEN)["entries"], 2)

    def test_expired_opening_never_replays_history(self):
        self.install()
        late = OPEN + timedelta(minutes=6)
        self.source.advance(late)
        self.assertEqual(self.runtime.run_once(late)["entries"], 0)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_trader_decisions WHERE status='expired'").fetchone()[0], 2)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_intents").fetchone()[0], 0)

    def test_stale_or_preopening_quote_is_deferred_then_current_quote_can_retry(self):
        self.install()
        self.source.clock = OPEN - timedelta(minutes=1)
        first = self.runtime.run_once(OPEN)
        self.assertEqual(first["entries"], 0)
        self.source.clock = OPEN
        self.assertEqual(self.runtime.run_once(OPEN)["entries"], 2)

    def test_disable_blocks_entries_and_strict_boolean(self):
        row = self.install(enabled=False)
        self.assertEqual(self.runtime.run_once(OPEN)["entries"], 0)
        with self.assertRaises(DeskError):
            self.runtime.set_enabled(row["id"], 1)
        self.runtime.set_enabled(row["id"], True)
        self.assertEqual(self.runtime.run_once(OPEN)["entries"], 2)

    def test_initial_atr_risk_sizes_shares_and_binds_actual_fill_stop(self):
        self.stop_distance = 10.
        self.install()
        self.assertEqual(self.runtime.run_once(OPEN)["entries"], 2)
        self.trading.process(self.source, OPEN)
        self.runtime.service_exits(OPEN, acquire_native_clocks=False)
        with self.store.connect() as con:
            self.assertEqual([r[0] for r in con.execute("SELECT quantity FROM p_positions ORDER BY symbol")], ["50", "50"])
            states = list(con.execute("SELECT * FROM a_trader_position_state"))
            self.assertTrue(all(Decimal(r["initial_stop_price"]) == Decimal("40.05") for r in states))
        # The candle low is not inspected. Only this actual later quote stops.
        mid = OPEN + timedelta(hours=2)
        self.source.clock, self.source.price = mid, Decimal(39)
        self.source.refresh(self.symbols)
        self.runtime.set_enabled("test-install", False)
        self.assertEqual(self.runtime.service_exits(mid, acquire_native_clocks=False)["exits"], 2)
        self.assertEqual(self.trading.process(self.source, mid)["fills"], 2)
        self.assertTrue(all(fill["side"] == "sell" and Decimal(fill["price"]) == Decimal("38.961") for fill in self.fills()[2:]))

    def test_time_exit_counts_observed_actual_bars_and_survives_disabled_restart(self):
        self.install()
        self.runtime.run_once(OPEN)
        self.trading.process(self.source, OPEN)
        self.runtime.set_enabled("test-install", False)
        monday = datetime(2026, 10, 12, 20, 5, tzinfo=UTC)
        self.source.advance(monday)
        self.runtime = self.make_runtime()
        self.assertEqual(self.runtime.run_once(monday)["exits"], 0)
        tuesday = datetime(2026, 10, 13, 13, 30, 2, tzinfo=UTC)
        self.source.clock = tuesday
        self.assertEqual(self.runtime.service_exits(tuesday, acquire_native_clocks=False)["exits"], 2)
        self.assertEqual(self.trading.process(self.source, tuesday)["fills"], 2)
        with self.store.connect() as con:
            unsettled = self.trading.strategy_cash(con, con.execute("SELECT book_id FROM a_trader_installations").fetchone()[0], tuesday, release=False)
            self.assertGreater(unsettled["unsettled_cents"], 0)

    def test_missed_close_exit_remains_owed_at_later_actual_opening(self):
        self.install()
        self.runtime.run_once(OPEN)
        self.trading.process(self.source, OPEN)
        self.exit_signal = True
        close = datetime(2026, 10, 9, 20, 5, tzinfo=UTC)
        self.source.advance(close)
        self.runtime.run_once(close)
        monday_late = datetime(2026, 10, 12, 14, 0, tzinfo=UTC)
        self.source.clock = monday_late
        self.assertEqual(self.runtime.service_exits(monday_late, acquire_native_clocks=False)["exits"], 0)
        tuesday = datetime(2026, 10, 13, 13, 30, 2, tzinfo=UTC)
        self.source.clock = tuesday
        self.runtime.set_enabled("test-install", False)
        self.runtime = self.make_runtime()
        self.assertEqual(self.runtime.service_exits(tuesday, acquire_native_clocks=False)["exits"], 2)
        with self.store.connect() as con:
            receipts = [json.loads(r[0]) for r in con.execute("SELECT data FROM a_trader_decisions WHERE role='exit' AND status='queued'")]
            self.assertTrue(all(r["overdue"] for r in receipts))

    def test_history_revision_and_inserted_prefix_are_quarantined(self):
        self.install(enabled=False)
        self.runtime.run_once(OPEN)
        later = datetime(2026, 10, 9, 20, 5, tzinfo=UTC)
        self.source.advance(later)
        self.source.data["AAA"]["bars"][-3]["close"] = 50.5
        result = self.runtime.run_once(later)
        self.assertEqual(result["status"], "data_blocked")
        self.assertTrue(any("revision" in r["error"] for r in result["errors"]))

    def test_fence_failure_rolls_back_acquisition_and_no_financial_effects(self):
        self.install()
        def guard(con):
            raise RuntimeError("Lease lost")
        with self.assertRaises(RuntimeError) as raised:
            self.runtime.run_once(OPEN, transaction_guard=guard)
        self.assertTrue(getattr(raised.exception, "trader_fence_failure", False))
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_trader_coverage").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_intents").fetchone()[0], 0)

    def test_tensor_book_collision_is_rejected_inside_writer_boundary(self):
        book = self.trading.create_book({"name": "Tensor", "broker": "local", "kind": "forward"})
        self.trading.set_book(book["id"], {"policy": {"slippage_bps": 10}})
        with self.store.transaction() as con:
            con.execute("CREATE TABLE a_tensor_installations(id TEXT,book_id TEXT)")
            con.execute("INSERT INTO a_tensor_installations VALUES(?,?)", ("same-id", book["id"]))
        with self.assertRaises(DeskError):
            self.runtime.install({"id": "same-id", "rule_id": "test-rule", "book_id": book["id"]})

    def test_cached_assessment_cannot_bypass_later_failed_census(self):
        self.install(enabled=False)
        self.runtime.run_once(OPEN)
        self.runtime.set_enabled("test-install", True)
        with self.store.transaction() as con:
            con.execute("UPDATE a_trader_coverage SET status='failed',error='new observed failure' WHERE symbol='BBB'")
        result = self.runtime.run_once(OPEN, allow_acquisition=False)
        self.assertEqual(result["entries"], 0)
        self.assertEqual(result["status"], "collecting")

    def test_atomic_entry_rechecks_binding_after_assessment(self):
        self.install(enabled=False)
        self.runtime.run_once(OPEN)
        self.runtime.set_enabled("test-install", True)
        install = self.runtime._install_rows()[0]
        with self.store.transaction() as con:
            assessment = json.loads(con.execute("SELECT data FROM a_trader_assessments").fetchone()[0])
            con.execute("UPDATE a_trader_coverage SET status='failed' WHERE symbol='BBB'")
            self.assertEqual(self.runtime._entry(con, install, assessment["candidates"][0], assessment, OPEN, None), 0)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_intents").fetchone()[0], 0)

    def test_earlier_future_usable_clock_blocks_even_if_final_bar_is_causal(self):
        self.install(enabled=False)
        self.runtime.run_once(OPEN)
        with self.store.transaction() as con:
            blob = con.execute("SELECT bars FROM a_trader_coverage WHERE symbol='AAA'").fetchone()[0]
            bars = list(self.runtime._unpack(blob))
            from dataclasses import replace
            bars[3] = replace(bars[3], usable_at_ms=_ms(OPEN) + 100000)
            con.execute("UPDATE a_trader_coverage SET bars=? WHERE symbol='AAA'", (self.runtime._pack(bars),))
        self.runtime.set_enabled("test-install", True)
        self.assertEqual(self.runtime.run_once(OPEN, allow_acquisition=False)["entries"], 0)

    def test_stored_config_tamper_is_detected_before_evaluation_or_orders(self):
        self.install()
        with self.store.transaction() as con:
            config = json.loads(con.execute("SELECT config FROM a_trader_installations").fetchone()[0])
            config["entry_cap_equity"] = 1.
            con.execute("UPDATE a_trader_installations SET config=?", (json.dumps(config),))
        self.assertEqual(self.runtime.run_once(OPEN)["status"], "data_blocked")
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_intents").fetchone()[0], 0)

    def test_applied_split_transforms_stop_units_without_false_trigger(self):
        self.stop_distance = 10.
        row = self.install()
        self.runtime.run_once(OPEN)
        self.trading.process(self.source, OPEN)
        self.runtime.service_exits(OPEN, acquire_native_clocks=False)
        monday = datetime(2026, 10, 12, 13, 30, 2, tzinfo=UTC)
        actions = TensorActions(self.store, self.trading, self.source, transport=lambda *args: {})
        for sym in self.symbols:
            result = actions.apply_event(row["book_id"], sym, {"kind": "split", "date": "2026-10-12", "numerator": 2, "denominator": 1}, "Dated issuer fixture", monday)
            self.assertEqual(result["status"], "applied")
        self.source.clock, self.source.price = monday, Decimal(25)
        self.source.refresh(self.symbols)
        self.assertEqual(self.runtime.service_exits(monday, acquire_native_clocks=False)["exits"], 0)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_trader_exit_obligations WHERE reason='observed_initial_atr_stop'").fetchone()[0], 0)
            self.assertTrue(all(Decimal(r[0]) == Decimal("40.05") for r in con.execute("SELECT initial_stop_price FROM a_trader_position_state")))
        breach = monday + timedelta(hours=1)
        self.source.clock, self.source.price = breach, Decimal(19)
        self.source.refresh(self.symbols)
        with self.store.transaction() as con:
            for sym in self.symbols:
                con.execute("INSERT OR REPLACE INTO a_strategy_action_probes VALUES(?,?,'ok',NULL,'synthetic')", (sym, breach.isoformat()))
        self.assertEqual(self.runtime.service_exits(breach, acquire_native_clocks=False)["exits"], 2)
        with self.store.connect() as con:
            data = json.loads(con.execute("SELECT data FROM a_trader_exit_obligations WHERE reason='observed_initial_atr_stop' LIMIT 1").fetchone()[0])
            self.assertEqual(Decimal(data["current_unit_stop_price"]), Decimal("20.025"))

    def test_gap_fill_rechecks_original_max_debit(self):
        self.install()
        self.runtime.run_once(OPEN)
        self.source.price = Decimal(100)
        self.source.refresh(self.symbols)
        result = self.trading.process(self.source, OPEN)
        self.assertEqual(self.fills(), [])
        self.assertTrue(all("debit budget" in row["detail"] for row in result["errors"]))
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT cash_cents FROM p_books WHERE name='Test book'").fetchone()[0], 10000000)

    def test_ten_slots_include_pending_and_preserve_symbol_tie_break(self):
        self.symbols[:] = [chr(65 + i) * 3 for i in range(12)]
        self.source = Source(self.store, self.symbols)
        self.runtime = self.make_runtime()
        self.install()
        self.assertEqual(self.runtime.run_once(OPEN)["entries"], 10)
        self.assertEqual(self.trading.process(self.source, OPEN)["fills"], 10)
        self.assertEqual(sorted(f["symbol"] for f in self.fills()), self.symbols[:10])
        with self.store.connect() as con:
            self.assertEqual([r[0] for r in con.execute("SELECT symbol FROM a_trader_decisions WHERE role='entry' AND status='queued' ORDER BY rowid")], self.symbols[:10])

    def test_book_halt_recovers_inside_same_opening_without_replaying_later(self):
        row = self.install()
        self.trading.set_book(row["book_id"], {"policy": {"halted": True}})
        self.assertEqual(self.runtime.run_once(OPEN)["entries"], 0)
        resumed = OPEN + timedelta(seconds=20)
        self.source.clock = resumed
        self.trading.set_book(row["book_id"], {"policy": {"halted": False}})
        self.assertEqual(self.runtime.run_once(resumed)["entries"], 2)

    def test_cli_invalid_capital_does_not_create_or_fund_any_books(self):
        from backend.trader_cli import install_all
        for value in (float("nan"), -1, 1.001):
            with self.subTest(value=value), self.assertRaises(DeskError):
                install_all(self.store, self.trading, self.runtime, virtual_capital=value)
        self.assertEqual(self.runtime.snapshot()["strategy_count"], 0)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_books").fetchone()[0], 1)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM p_fundings").fetchone()[0], 0)

    def test_partial_policy_rejected_and_first_measured_partial_remainder_cancelled(self):
        self.stop_distance = 10.
        row = self.install()
        self.runtime.run_once(OPEN)
        self.trading.set_book(row["book_id"], {"policy": {"max_fill_quantity": 2}})
        # Simulate one actual measured first partial before supervisor preflight.
        self.assertEqual(self.trading.process(self.source, OPEN)["fills"], 2)
        self.assertEqual(self.runtime.prepare_fills(OPEN)["cancelled"], 2)
        later = OPEN + timedelta(seconds=20)
        self.source.clock, self.source.price = later, Decimal(70)
        self.source.refresh(self.symbols)
        self.assertEqual(self.trading.process(self.source, later)["fills"], 0)
        with self.store.connect() as con:
            self.assertTrue(all(Decimal(r[0]) == 2 for r in con.execute("SELECT quantity FROM p_positions")))
            self.assertTrue(all(Decimal(r[0]) == Decimal("40.05") for r in con.execute("SELECT initial_stop_price FROM a_trader_position_state")))
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_trader_decisions WHERE role='entry_remainder' AND status='cancelled'").fetchone()[0], 2)

    def test_partial_policy_change_before_first_fill_cancels_without_exposure(self):
        row = self.install()
        self.runtime.run_once(OPEN)
        self.trading.set_book(row["book_id"], {"policy": {"max_fill_quantity": 2}})
        self.assertEqual(self.runtime.prepare_fills(OPEN)["cancelled"], 2)
        self.assertEqual(self.trading.process(self.source, OPEN)["fills"], 0)
        self.assertEqual(self.fills(), [])

    def test_held_close_exit_survives_unrelated_failure_and_entry_pause(self):
        self.install()
        self.runtime.run_once(OPEN)
        self.trading.process(self.source, OPEN)
        self.runtime.set_enabled("test-install", False)
        self.exit_signal = True
        close = datetime(2026, 10, 9, 20, 5, tzinfo=UTC)
        self.source.advance(close)
        self.source.fail.add("BBB")
        self.runtime = self.make_runtime()
        result = self.runtime.service_exits(close)
        self.assertEqual(result["status"], "data_blocked")
        with self.store.connect() as con:
            self.assertEqual([r[0] for r in con.execute("SELECT symbol FROM a_trader_exit_obligations WHERE reason='frozen_close_exit'")], ["AAA"])
        monday = datetime(2026, 10, 12, 13, 30, 2, tzinfo=UTC)
        self.source.clock = monday
        self.assertEqual(self.runtime.service_exits(monday, acquire_native_clocks=False)["exits"], 1)
        self.assertEqual(self.trading.process(self.source, monday)["fills"], 1)
        self.assertEqual(self.fills()[-1]["symbol"], "AAA")

    def test_bad_cached_blob_quarantines_name_but_services_actual_quote_stops(self):
        self.stop_distance = 10.
        self.install()
        self.runtime.run_once(OPEN)
        self.trading.process(self.source, OPEN)
        self.runtime.prepare_fills(OPEN)
        with self.store.transaction() as con:
            con.execute("UPDATE a_trader_coverage SET bars=? WHERE symbol='AAA'", (b"broken-zlib",))
        later = datetime(2026, 10, 9, 20, 5, tzinfo=UTC)
        self.source.advance(later)
        self.runtime.service_exits(later)
        monday = datetime(2026, 10, 12, 14, 0, tzinfo=UTC)
        self.source.clock, self.source.price = monday, Decimal(39)
        self.source.refresh(self.symbols)
        result = self.runtime.service_exits(monday)
        self.assertEqual(result["exits"], 2)
        self.assertTrue(result["errors"])

    def test_actual_frozen_rsi_rule_ma5_exit_ignores_unrelated_failed_etf(self):
        from backend.trader_signals import DEFINITIONS, RSI2, UNIVERSE, evaluate
        self.source = Source(self.store, list(UNIVERSE))
        for sym in UNIVERSE:
            self.source.data[sym] = payload(sym, OPEN, count=300)
        closes = [100 + .1 * i for i in range(300)]
        closes[-2:] = [126.8, 125.8]
        for row, close in zip(self.source.data["SPY"]["bars"], closes):
            row.update(open=close, high=close + 1, low=close - 1, close=close)
        self.source.price = Decimal("125.8")
        self.runtime = TraderRuntimeManager(self.store, self.trading, self.source, evaluator=evaluate, definitions=copy.deepcopy(DEFINITIONS))
        book = self.trading.create_book({"name": "Actual RSI rule", "broker": "local", "kind": "forward"})
        self.trading.set_book(book["id"], {"policy": {"slippage_bps": 10}})
        self.trading.fund_book(book["id"], 100000, "rsi-fixture")
        self.runtime.install({"id": RSI2, "rule_id": RSI2, "book_id": book["id"], "enabled": True, "max_fetch_per_run": 16})
        self.assertEqual(self.runtime.run_once(OPEN)["entries"], 1)
        self.assertEqual(self.trading.process(self.source, OPEN)["fills"], 1)
        self.assertEqual(self.fills()[0]["symbol"], "SPY")
        self.runtime.set_enabled(RSI2, False)
        close_clock = datetime(2026, 10, 9, 20, 5, tzinfo=UTC)
        prior = copy.deepcopy(self.source.data)
        self.source.advance(close_clock)
        for sym in UNIVERSE:
            newest = self.source.data[sym]["bars"][-1]
            if sym == "SPY":
                newest.update(open=130., high=131., low=129., close=130.)
            self.source.data[sym]["bars"] = prior[sym]["bars"] + [newest]
        self.source.fail.add("QQQ")
        self.assertEqual(self.runtime.run_once(close_clock)["status"], "data_blocked")
        self.runtime.service_exits(close_clock)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT status FROM a_trader_coverage WHERE symbol='QQQ'").fetchone()[0], "failed")
            owed = con.execute("SELECT reason FROM a_trader_exit_obligations WHERE symbol='SPY'").fetchone()
            self.assertEqual(owed[0], "close_above_sma5")
        monday = datetime(2026, 10, 12, 13, 30, 2, tzinfo=UTC)
        self.source.clock, self.source.price = monday, Decimal(130)
        self.runtime = TraderRuntimeManager(self.store, self.trading, self.source, evaluator=evaluate, definitions=copy.deepcopy(DEFINITIONS))
        self.assertEqual(self.runtime.service_exits(monday, acquire_native_clocks=False)["exits"], 1)
        self.assertEqual(self.trading.process(self.source, monday)["fills"], 1)
        self.assertEqual(self.fills()[-1]["side"], "sell")

    def test_atomic_census_availability_race_can_recover_exact_same_binding(self):
        self.install(enabled=False)
        self.runtime.run_once(OPEN)
        self.runtime.set_enabled("test-install", True)
        install = self.runtime._install_rows()[0]
        with self.store.transaction() as con:
            assessment = json.loads(con.execute("SELECT data FROM a_trader_assessments").fetchone()[0])
            con.execute("UPDATE a_trader_coverage SET status='failed' WHERE symbol='BBB'")
            self.assertEqual(self.runtime._entry(con, install, assessment["candidates"][0], assessment, OPEN, None), 0)
            con.execute("UPDATE a_trader_coverage SET status='ready' WHERE symbol='BBB'")
        later = OPEN + timedelta(seconds=20)
        self.source.clock = later
        self.assertEqual(self.runtime.run_once(later, allow_acquisition=False)["entries"], 2)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_trader_assessments").fetchone()[0], 1)

    def test_invalid_configuration_quarantines_only_its_owned_active_entry(self):
        self.install()
        self.runtime.run_once(OPEN)
        with self.store.transaction() as con:
            con.execute("UPDATE a_trader_installations SET config_sha256='wrong'")
        result = self.runtime.prepare_fills(OPEN)
        self.assertTrue(result["fills_safe"])
        self.assertEqual(result["cancelled"], 2)
        self.assertEqual(self.trading.process(self.source, OPEN)["fills"], 0)
        self.assertEqual(self.runtime.snapshot()["installations"][0]["readiness"]["status"], "configuration_integrity_blocked")

    def test_explicit_cli_install_creates_strategy_schedule_without_unpausing_runtime(self):
        from backend.trader_cli import install_all
        from backend.autonomy import AutonomyRuntime
        from backend.reasoning import Reasoning
        autonomy = AutonomyRuntime(self.store, self.trading, None, Reasoning(), self.source)
        autonomy.configure({"running": False})
        install_all(self.store, self.trading, self.runtime, enabled=True)
        with self.store.connect() as con:
            rows = list(con.execute("SELECT * FROM a_schedules WHERE kind='strategies'"))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["enabled"], 1)
        self.assertFalse(autonomy.status()["running"])


if __name__ == "__main__":
    unittest.main()
