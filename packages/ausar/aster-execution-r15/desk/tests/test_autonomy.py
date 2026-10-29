import json
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from backend.autonomy import AutonomyRuntime, _FencedProviders
from backend.providers import exchange_calendar, utc_clock as real_utc_clock
from backend.store import DeskError, Store
from backend.trading import TradingDesk


UTC = timezone.utc


class FakeProviders:
    broker = None
    MAX_SYMBOLS = 16
    def __init__(self):
        self.refreshes = []
    def calendar(self, clock=None):
        return exchange_calendar(clock)
    def status(self):
        return {"market_data": {"kind": "fake", "connected": False}, "broker": {"configured": False}}
    def refresh(self, symbols):
        self.refreshes.append(list(symbols))
        return {"refreshed": 0, "errors": []}
    def bars(self, sym, range='1mo', interval='1d'):
        return {"symbol": sym, "range": range, "interval": interval, "bars": [{"timestamp": "2025-01-02T14:30:00+00:00", "close": 100, "adjusted_close": 99}, {"timestamp": "2025-01-03T14:30:00+00:00", "close": 110, "adjusted_close": 110}], "source": "fixture bars", "stale_cache": False, "revision_id": "fixture-" + sym}


class FakeTrading:
    def __init__(self):
        self.calls = []
        self.fail = False
        self.block = None
    def reconcile(self, provider, clock):
        self.calls.append("reconcile")
        if self.fail:
            raise RuntimeError("Fixture failure")
        return {"errors": []}
    def process(self, provider, clock):
        self.calls.append("process")
        if self.block:
            self.block()
        return {"processed": 0, "errors": []}
    def snapshot(self):
        return {"books": [], "intents": [], "positions": [], "fills": []}


class FakeLab:
    def __init__(self):
        self.alerts = []
        self.runs = 0
        self.resolved = []
    def operate(self, **kwargs):
        self.runs += 1
        return {"operated": True}
    def alert(self, *args):
        self.alerts.append(args)
    def resolve_key(self, key):
        self.resolved.append(key)


class FakeReasoning:
    configured = False
    def status(self):
        return {"configured": self.configured, "provider": "fixture" if self.configured else "local"}


class AutonomyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "desk.sqlite")
        self.trading, self.lab, self.reasoning, self.providers = FakeTrading(), FakeLab(), FakeReasoning(), FakeProviders()
        self.runtime = AutonomyRuntime(self.store, self.trading, self.lab, self.reasoning, self.providers)
        self.clock = datetime(2025, 1, 6, 13, 0, tzinfo=UTC)  # Before all NYSE session slots.

    def tearDown(self):
        self.runtime.stop()
        self.temp.cleanup()

    def job(self):
        with self.store.connect() as con:
            return dict(con.execute("SELECT * FROM a_jobs WHERE schedule_id='default-operations' ORDER BY due_at DESC LIMIT 1").fetchone())

    def test_on_by_default_reconcile_precedes_execution_and_no_invented_trades(self):
        self.assertTrue(self.runtime.status()["running"])
        self.assertFalse(self.runtime.status()["worker_alive"])
        self.assertTrue(self.runtime.run_once(self.clock))
        self.assertEqual(self.trading.calls, ["reconcile", "process"])
        self.assertEqual(self.job()["status"], "succeeded")
        self.assertIn("runtime-job-" + self.job()["id"], self.lab.resolved)
        self.assertEqual(self.lab.runs, 1)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM orders").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT cash_cents FROM account").fetchone()[0], 0)
        self.assertFalse(self.runtime.run_once(self.clock + timedelta(seconds=1)))
        benchmarks = self.runtime.snapshot()["benchmarks"]
        self.assertEqual({b["symbol"] for b in benchmarks}, {"SPY", "QQQ"})
        self.assertTrue(all(b["scope"] == "vendor adjusted close return" for b in benchmarks))

    def test_failure_remains_due_with_backoff_until_success(self):
        self.trading.fail = True
        self.runtime.run_once(self.clock)  # Independent benchmark collection may succeed.
        job = self.job()
        self.assertEqual(job["status"], "retry")
        self.assertEqual(job["attempts"], 1)
        self.assertEqual(job["next_attempt_at"], self.clock.timestamp() + 5)
        self.assertNotIn("runtime-job-" + job["id"], self.lab.resolved)
        self.assertNotIn("process", self.trading.calls)
        with self.store.connect() as con:
            schedule = con.execute("SELECT * FROM a_schedules WHERE id='default-operations'").fetchone()
            self.assertIsNone(schedule["last_success_at"])
            self.assertEqual(schedule["next_due"], 0)
        self.assertFalse(self.runtime.run_once(self.clock + timedelta(seconds=4)))
        self.trading.fail = False
        self.assertTrue(self.runtime.run_once(self.clock + timedelta(seconds=5)))
        self.assertEqual(self.job()["id"], job["id"])
        self.assertEqual(self.job()["attempts"], 2)
        self.assertEqual(self.job()["status"], "succeeded")
        self.assertIn("runtime-job-" + job["id"], self.lab.resolved)

    def test_one_account_reconciliation_error_does_not_strand_healthy_books(self):
        self.trading.reconcile = lambda provider, clock: {"errors": ["Forward account fixture outage"], "books": 1}
        self.runtime.run_once(self.clock)
        self.assertIn("process", self.trading.calls)
        job = self.job()
        self.assertEqual(job["status"], "retry")
        receipt = json.loads(job["result"])
        self.assertTrue(receipt["reconcile"]["errors"])
        self.assertEqual(receipt["process"]["processed"], 0)

    def test_failed_journal_integrity_blocks_execution_but_preserves_data_research(self):
        with self.store.transaction() as con:
            self.store.event(con, "fixture_evidence", "operator", "Original immutable message")
            con.execute("UPDATE events SET message='tampered' WHERE event_type='fixture_evidence'")
        self.assertEqual(self.store.verify_ledger()["status"], "failed")
        self.runtime.run_once(self.clock)
        self.assertEqual(self.trading.calls, ["reconcile"])
        self.assertTrue(self.providers.refreshes)
        self.assertEqual(self.lab.runs, 1)
        self.assertEqual(self.job()["status"], "retry")
        self.assertFalse(self.runtime.status()["healthy"])

    def test_expired_running_job_is_recovered_without_new_occurrence(self):
        self.trading.fail = True
        self.runtime.run_once(self.clock)
        job = self.job()
        with self.store.transaction() as con:
            con.execute("UPDATE a_jobs SET status='running',owner='crashed',lease_until=0 WHERE id=?", (job["id"],))
            con.execute("UPDATE a_runtime_lock SET owner=NULL,expires=0 WHERE id=1")
        recovered = AutonomyRuntime(self.store, self.trading, self.lab, self.reasoning, self.providers)
        self.trading.fail = False
        self.assertTrue(recovered.run_once(self.clock + timedelta(seconds=1)))
        self.assertEqual(self.job()["id"], job["id"])
        self.assertEqual(self.job()["status"], "succeeded")
        recovered.stop()

    def test_single_worker_even_if_database_lease_expires_mid_pass(self):
        entered, release = threading.Event(), threading.Event()
        self.trading.block = lambda: (entered.set(), release.wait(5))
        thread = threading.Thread(target=lambda: self.runtime.run_once(self.clock))
        thread.start()
        self.assertTrue(entered.wait(3))
        other = AutonomyRuntime(self.store, FakeTrading(), FakeLab(), self.reasoning, FakeProviders())
        with self.store.transaction() as con:
            con.execute("UPDATE a_runtime_lock SET expires=?", (time.time() + 0.1,))
        self.assertFalse(other.run_once(self.clock))
        release.set()
        thread.join(3)
        self.assertFalse(thread.is_alive())
        other.stop()

    def test_stale_fence_blocks_broker_mutations(self):
        self.runtime._claim()
        class Broker:
            def submit(self, value):
                raise AssertionError("Must never reach broker")
        self.providers.broker = Broker()
        guarded = _FencedProviders(self.providers, self.runtime._fence)
        with self.store.transaction() as con:
            con.execute("UPDATE a_runtime_lock SET owner='new-worker' WHERE id=1")
        with self.assertRaises(DeskError):
            guarded.broker.submit({})

    def test_named_account_cannot_bypass_fence_or_fall_back_to_default(self):
        self.runtime._claim()
        class Broker:
            def submit(self, value):
                raise AssertionError("Must not reach a stale broker")
            def cancel(self, value):
                raise AssertionError("Must not reach a stale broker")
        self.providers.brokers = {"research": Broker()}
        self.providers.broker_for = lambda name='default': self.providers.brokers.get(name)
        guarded = _FencedProviders(self.providers, self.runtime._fence)
        self.assertIsNone(guarded.broker_for("unconfigured"))
        with self.store.transaction() as con:
            con.execute("UPDATE a_runtime_lock SET owner='new-worker' WHERE id=1")
        with self.assertRaises(DeskError):
            guarded.broker_for("research").submit({})
        with self.assertRaises(DeskError):
            guarded.brokers["research"].cancel("order")

    def test_missed_windows_are_recorded_not_replayed_and_holiday_has_no_slots(self):
        self.runtime.run_once(self.clock)
        self.trading.calls.clear()
        clock = datetime(2025, 1, 6, 22, 0, tzinfo=UTC)
        self.runtime.run_once(clock)
        with self.store.connect() as con:
            jobs = con.execute("SELECT j.status,s.phase FROM a_jobs j JOIN a_schedules s ON s.id=j.schedule_id WHERE s.cadence='session'").fetchall()
            self.assertTrue(jobs)
            self.assertTrue(all(j["status"] == "skipped" for j in jobs))
        self.assertEqual(self.trading.calls, ["reconcile", "process"])
        self.runtime.run_once(datetime(2025, 7, 4, 20, 0, tzinfo=UTC))
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_jobs j JOIN a_schedules s ON s.id=j.schedule_id WHERE s.cadence='session' AND j.due_at>=?", (datetime(2025, 7, 4, tzinfo=UTC).timestamp(),)).fetchone()[0], 0)

    def test_model_brief_is_independent_durable_enqueue_and_reuses_existing_task(self):
        self.reasoning.configured = True
        self.runtime.configure({"brief_enabled": True, "brief_seconds": 60})
        self.runtime.run_once(self.clock)
        with self.store.transaction() as con:
            tasks = con.execute("SELECT * FROM tasks WHERE kind='desk_brief'").fetchall()
            self.assertEqual(len(tasks), 1)
            brief = con.execute("SELECT * FROM a_jobs WHERE schedule_id='default-brief'").fetchone()
            self.assertEqual(json.loads(brief["result"])["task_id"], tasks[0]["id"])
            con.execute("UPDATE a_jobs SET status='retry',next_attempt_at=0 WHERE id=?", (brief["id"],))
        self.runtime.run_once(self.clock + timedelta(seconds=1))
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM tasks WHERE kind='desk_brief'").fetchone()[0], 1)

    def test_disabled_runtime_requires_explicit_cycle_and_schedule_validation(self):
        self.runtime.configure({"running": False})
        self.assertFalse(self.runtime.run_once(self.clock))
        self.assertTrue(self.runtime.run_once(self.clock, force=True))
        with self.assertRaises(DeskError):
            self.runtime.schedule({"kind": "generate_strategy"})
        with self.assertRaises(DeskError):
            self.runtime.configure({"refresh_seconds": 0})
        schedule = self.runtime.schedule({"kind": "bars", "label": "Operator bar collection", "interval_seconds": 3600, "payload": {"symbols": ["AAPL"]}})
        self.assertEqual(schedule["kind"], "bars")
        self.assertEqual(schedule["payload"]["symbols"], ["AAPL"])

    def test_production_slow_refresh_cannot_fill_an_expired_real_intent(self):
        trading = TradingDesk(self.store)
        trading.fund_book("main", 100, "clock-fixture-fund")
        start = datetime.now(UTC)
        self.store.ingest_quote("AAPL", Decimal("10"), start, "Manual clock fixture")
        intent = trading.submit_intent({"book_id": "main", "symbol": "AAPL", "side": "buy", "quantity": 1, "order_type": "market", "time_in_force": "gtc", "client_id": "clock-fixture-intent", "expires_at": (start + timedelta(seconds=5)).isoformat()})
        live = [start]
        self.providers.calendar = lambda clock=None: {"is_session": True, "is_open": True, "open_at": (start - timedelta(hours=1)).isoformat(), "close_at": (start + timedelta(hours=6)).isoformat()}
        def slow_refresh(symbols):
            live[0] += timedelta(seconds=30)
            return {"errors": [], "refreshed": 0}
        self.providers.refresh = slow_refresh
        runtime = AutonomyRuntime(self.store, trading, self.lab, self.reasoning, self.providers)
        with self.store.transaction() as con:
            con.execute("UPDATE a_schedules SET enabled=0 WHERE id!='default-operations'")
        def current(value=None):
            return live[0] if value is None else real_utc_clock(value)
        with patch("backend.autonomy.utc_clock", side_effect=current), patch("backend.trading.clock_time", side_effect=current):
            runtime.run_once()
        snapshot = trading.snapshot()
        self.assertEqual(snapshot["fills"], [])
        self.assertEqual(next(i for i in snapshot["intents"] if i["id"] == intent["id"])["status"], "expired")
        self.assertEqual(self.job()["completed_at"], live[0].isoformat())
        with self.store.connect() as con:
            due = con.execute("SELECT next_due FROM a_schedules WHERE id='default-operations'").fetchone()[0]
        self.assertEqual(due, live[0].timestamp() + 60)
        runtime.stop()

    def test_production_retry_backoff_starts_after_slow_failure(self):
        start, live = datetime.now(UTC), [datetime.now(UTC)]
        live[0] = start
        def slow_refresh(symbols):
            live[0] += timedelta(seconds=30)
            return {"errors": [], "refreshed": 0}
        self.providers.refresh = slow_refresh
        self.trading.fail = True
        with self.store.transaction() as con:
            con.execute("UPDATE a_schedules SET enabled=0 WHERE id!='default-operations'")
        def current(value=None):
            return live[0] if value is None else real_utc_clock(value)
        with patch("backend.autonomy.utc_clock", side_effect=current):
            self.runtime.run_once()
        self.assertEqual(self.job()["next_attempt_at"], (start + timedelta(seconds=35)).timestamp())

    def test_session_window_expiring_during_reads_skips_financial_execution(self):
        start, live = datetime.now(UTC), [datetime.now(UTC)]
        live[0] = start
        self.providers.calendar = lambda clock=None: {"is_session": True, "is_open": True, "open_at": start.isoformat(), "close_at": (start + timedelta(hours=6)).isoformat()}
        def slow_refresh(symbols):
            live[0] += timedelta(minutes=6)
            return {"errors": [], "refreshed": 0}
        self.providers.refresh = slow_refresh
        with self.store.transaction() as con:
            con.execute("UPDATE a_schedules SET enabled=0 WHERE id!='session-open'")
        def current(value=None):
            return live[0] if value is None else real_utc_clock(value)
        with patch("backend.autonomy.utc_clock", side_effect=current):
            self.runtime.run_once()
        self.assertEqual(self.trading.calls, ["reconcile"])
        with self.store.connect() as con:
            job = con.execute("SELECT * FROM a_jobs WHERE schedule_id='session-open'").fetchone()
        self.assertEqual(job["status"], "skipped")
        self.assertEqual(job["completed_at"], live[0].isoformat())
        self.assertEqual(job["attempts"], 1)

    def test_held_and_active_symbols_precede_watchlist_and_terminal_history_is_excluded(self):
        trading = TradingDesk(self.store)
        trading.fund_book("main", 1000, "coverage-fixture-fund")
        self.store.ingest_quote("ZZENTRY", Decimal("10"), datetime.now(UTC), "Manual coverage fixture")
        trading.submit_intent({"book_id": "main", "symbol": "ZZENTRY", "side": "buy", "quantity": 1, "order_type": "market", "time_in_force": "gtc", "client_id": "coverage-active"})
        self.store.ingest_quote("OLD", Decimal("10"), datetime.now(UTC), "Manual coverage fixture")
        old = trading.submit_intent({"book_id": "main", "symbol": "OLD", "side": "buy", "quantity": 1, "order_type": "market", "time_in_force": "gtc", "client_id": "coverage-terminal"})
        trading.cancel_intent(old["id"])
        self.store.remove_watch("OLD")
        with self.store.transaction() as con:
            for sym, qty in (("ZZHELD", "1"), ("OLDZERO", "0.0")):
                con.execute("INSERT INTO p_positions VALUES(?,?,?,?,?,?,?,?,?)", ("main", sym, qty, 1000, 0, None, "fixture", 0, datetime.now(UTC).isoformat()))
        for i in range(40):
            self.store.add_watch("OBS" + str(i))
        for _ in range(5):
            symbols = self.runtime._symbols()
            self.assertIn("ZZHELD", symbols)
            self.assertIn("ZZENTRY", symbols)
            self.assertNotIn("OLD", symbols)
            self.assertNotIn("OLDZERO", symbols)
            self.assertEqual(len(symbols), self.providers.MAX_SYMBOLS)
        self.assertFalse(self.runtime.status()["quote_coverage"]["capacity_limited"])

    def test_excess_active_coverage_is_rotated_and_explicitly_alerted(self):
        TradingDesk(self.store)
        held = {"HELD" + str(i) for i in range(20)}
        with self.store.transaction() as con:
            for sym in held:
                con.execute("INSERT INTO p_positions VALUES(?,?,?,?,?,?,?,?,?)", ("main", sym, "1", 1000, 0, None, "fixture", 0, datetime.now(UTC).isoformat()))
        first, second = self.runtime._symbols(), self.runtime._symbols()
        self.assertEqual(set(first) | set(second), held)
        coverage = self.runtime.status()["quote_coverage"]
        self.assertTrue(coverage["capacity_limited"])
        self.assertEqual(coverage["deferred_active_count"], 4)
        self.assertTrue(any(a[0] == "runtime-quote-capacity" for a in self.lab.alerts))

    def test_invalid_schedule_inputs_are_rejected_before_persistence(self):
        for payload in (
            {"interval_seconds": 0}, {"interval_seconds": False},
            {"payload": {"symbols": ["INVALID/SYMBOL"]}},
            {"kind": "bars", "payload": {"range": "century"}},
            {"kind": "bars", "payload": {"interval": "1h"}},
            {"kind": "desk_brief", "payload": {"instructions": ["wrong-type"]}},
            {"kind": []}, {"kind": {}}, {"cadence": []}, {"cadence": {}},
            {"cadence": "session", "phase": []},
        ):
            with self.subTest(payload=payload), self.assertRaises(DeskError):
                self.runtime.schedule(payload)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_schedules").fetchone()[0], 9)

    def test_disabling_selected_schedule_prevents_its_later_execution(self):
        def disable():
            with self.store.transaction() as con:
                con.execute("UPDATE a_schedules SET enabled=0 WHERE id='benchmark-history'")
        self.trading.block = disable
        self.runtime.run_once(self.clock)
        with self.store.connect() as con:
            job = con.execute("SELECT status FROM a_jobs WHERE schedule_id='benchmark-history'").fetchone()
        self.assertEqual(job[0], "pending")

    def test_pause_during_refresh_fences_financial_processing_and_resumes_due_job(self):
        def pause(symbols):
            self.runtime.configure({"running": False})
            return {"errors": [], "refreshed": 0}
        self.providers.refresh = pause
        self.assertFalse(self.runtime.run_once(self.clock))
        self.assertEqual(self.trading.calls, [])
        self.assertEqual(self.job()["status"], "pending")
        self.runtime.configure({"running": True})
        self.providers.refresh = lambda symbols: {"errors": [], "refreshed": 0}
        self.assertTrue(self.runtime.run_once(self.clock + timedelta(seconds=1)))
        self.assertEqual(self.trading.calls, ["reconcile", "process"])

    def test_interval_change_during_execution_controls_next_due(self):
        self.trading.block = lambda: self.runtime.configure({"refresh_seconds": 5})
        self.runtime.run_once(self.clock)
        with self.store.connect() as con:
            schedule = con.execute("SELECT * FROM a_schedules WHERE id='default-operations'").fetchone()
        self.assertEqual(schedule["interval_seconds"], 5)
        self.assertEqual(schedule["next_due"], self.clock.timestamp() + 5)

    def test_shorter_interval_recalculates_pending_due_from_last_success(self):
        self.runtime.run_once(self.clock)
        self.runtime.configure({"refresh_seconds": 5})
        self.assertTrue(self.runtime.run_once(self.clock + timedelta(seconds=5)))

    def test_execution_fence_can_use_existing_financial_transaction(self):
        self.runtime._claim()
        wrapper = _FencedProviders(self.providers, self.runtime._fence)
        with self.store.transaction() as con:
            wrapper.execution_fence(con)
            self.assertEqual(con.execute("SELECT owner FROM a_runtime_lock").fetchone()[0], self.runtime.owner)
        with self.store.transaction() as con:
            con.execute("UPDATE a_runtime_lock SET owner='new-worker'")
            with self.assertRaises(DeskError):
                wrapper.execution_fence(con)

    def test_extreme_benchmark_ratio_is_withheld_without_poisoning_runtime_json(self):
        def extreme(sym, *args):
            history = FakeProviders().bars(sym)
            history["bars"][0]["adjusted_close"] = 1e-308
            history["bars"][1]["adjusted_close"] = 1e308
            return history
        self.providers.bars = extreme
        self.runtime.run_once(self.clock)
        snapshot = self.runtime.snapshot()
        self.assertTrue(all(b["return_pct"] is None and b["return_status"] == "withheld" for b in snapshot["benchmarks"]))
        json.dumps(snapshot, allow_nan=False)

    def test_offline_weekend_catches_up_known_friday_windows_without_replay(self):
        friday = datetime(2025, 3, 7, 13, 0, tzinfo=UTC)
        monday = datetime(2025, 3, 10, 12, 0, tzinfo=UTC)
        self.runtime.run_once(friday)
        self.trading.calls.clear()
        restarted = AutonomyRuntime(self.store, self.trading, self.lab, self.reasoning, self.providers)
        self.runtime.stop()
        self.assertTrue(restarted.run_once(monday))
        with self.store.connect() as con:
            windows = con.execute("SELECT j.*,s.phase FROM a_jobs j JOIN a_schedules s ON s.id=j.schedule_id WHERE s.cadence='session'").fetchall()
        self.assertTrue(windows)
        self.assertTrue(all(j["status"] == "skipped" for j in windows))
        opened = next(j for j in windows if j["phase"] == "open")
        self.assertEqual(datetime.fromtimestamp(opened["due_at"], UTC).isoformat(), "2025-03-07T14:30:00+00:00")
        self.assertEqual(self.trading.calls, ["reconcile", "process"])
        self.assertTrue(restarted.status()["session_catchup"]["complete"])
        restarted.stop()

    def test_new_desk_does_not_invent_precreation_missed_windows(self):
        self.runtime.run_once(datetime(2025, 1, 6, 22, 0, tzinfo=UTC))
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_jobs j JOIN a_schedules s ON s.id=j.schedule_id WHERE s.cadence='session'").fetchone()[0], 0)

    def test_session_catchup_is_bounded_visible_and_eventually_complete(self):
        self.runtime.run_once(self.clock)
        later = self.clock + timedelta(days=18)
        self.runtime.run_once(later)
        self.assertFalse(self.runtime.status()["session_catchup"]["complete"])
        self.runtime.run_once(later)
        self.assertFalse(self.runtime.status()["session_catchup"]["complete"])
        self.runtime.run_once(later)
        self.assertTrue(self.runtime.status()["session_catchup"]["complete"])
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_jobs j JOIN a_schedules s ON s.id=j.schedule_id WHERE s.cadence='session' AND j.status!='skipped'").fetchone()[0], 0)

    def test_first_observation_can_join_still_active_window(self):
        opened = datetime(2025, 1, 6, 14, 30, tzinfo=UTC)
        self.runtime.run_once(opened + timedelta(minutes=1))
        with self.store.connect() as con:
            job = con.execute("SELECT * FROM a_jobs WHERE schedule_id='session-open'").fetchone()
        self.assertEqual(job["status"], "succeeded")
        self.assertEqual(job["due_at"], opened.timestamp())

    def test_reenabled_schedule_does_not_invent_disabled_period_jobs(self):
        friday = datetime(2025, 3, 7, 13, 0, tzinfo=UTC)
        self.runtime.run_once(friday)
        config = {"id": "session-open", "kind": "operations", "cadence": "session", "phase": "open", "enabled": False}
        self.runtime.schedule(config)
        self.runtime.schedule({**config, "enabled": True})
        self.runtime.run_once(datetime(2025, 3, 10, 12, 0, tzinfo=UTC))
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM a_jobs WHERE schedule_id='session-open'").fetchone()[0], 0)

    def test_shutdown_after_reads_preserves_due_work_and_prevents_financial_effects(self):
        def shutdown(symbols):
            self.runtime.stop_event.set()
            return {"errors": [], "refreshed": 0}
        self.providers.refresh = shutdown
        self.assertFalse(self.runtime.run_once(self.clock))
        self.assertEqual(self.trading.calls, [])
        self.assertEqual(self.job()["status"], "pending")


if __name__ == "__main__":
    unittest.main()
