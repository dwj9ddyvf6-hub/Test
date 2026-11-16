"""Blockers: full-audit cure pass 2026-10-25 (A-01/A-02/A-04/B3/B4).

A-01/A-02: the watchdog relaunched BESIDE a live runner because the
180 s heartbeat grace was shorter than the real ~275 s cycle period —
33 restarts in one day, two desk3.run_live processes racing the same
state. Law now: grace 600 s; a live runner is never duplicated
(stale-but-alive is named; a wedged pid is terminated and verified
dead before one relaunch); the runner itself holds a single-instance
flock; the guardian counts runners.

B3: Binance funding (HTTP 451 from this egress) failed all-or-nothing
and invisibly — producer_errors stayed {} while 46 sleeves sat UNFED.
Law now: per-symbol isolation, and a producer that returns nothing
with a last_error is named in producer_errors.

B4: config rows with adapter_dir passed their BARE module name to the
worker, importing sleeves/<name> (no evaluate) instead of
desk_sleeves/<name>. Law now: build_desk qualifies the module with
adapter_dir at the source.
"""
import importlib, json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from desk3 import watchdog  # noqa: E402

NOW = datetime(2026, 10, 25, 20, 0, 0, tzinfo=timezone.utc)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def mkroot(test, hb=None):
    root = tempfile.mkdtemp(dir=os.environ.get("TMPDIR") or None)
    state = os.path.join(root, "state")
    os.makedirs(state)
    if hb is not None:
        with open(os.path.join(state, "runner.json"), "w") as fh:
            json.dump(hb, fh)
    test.addCleanup(lambda: __import__("shutil").rmtree(root, True))
    return root, state


def hb(age_s, pid=4242, mode="evaluate-only"):
    return {"pid": pid, "cycle": 3, "mode": mode,
            "ts": (NOW - timedelta(seconds=age_s)).isoformat()}


class Launcher:
    def __init__(self):
        self.calls = []

    def __call__(self, root, mode):
        self.calls.append((root, mode))
        return 777


class DuplicateRunnerTests(unittest.TestCase):
    def setUp(self):
        self._alive = watchdog.pid_alive_desk
        self.addCleanup(setattr, watchdog, "pid_alive_desk", self._alive)
        watchdog.pid_alive_desk = lambda pid: pid == 4242

    def test_grace_covers_measured_cycle_period(self):
        # Measured live period ~275 s; the old 180 s grace misjudged
        # every slow cycle stale. Grace must exceed the measurement
        # with margin, and wedged must exceed grace.
        self.assertGreaterEqual(watchdog.GRACE_S, 550)
        self.assertGreater(watchdog.WEDGED_S, watchdog.GRACE_S)

    def test_stale_but_alive_is_named_never_duplicated(self):
        root, state = mkroot(self, hb(watchdog.GRACE_S + 60))
        L = Launcher()
        row = watchdog.check_once(root, launcher=L, now=NOW,
                                  live_pids={4242})
        self.assertEqual(row["status"], "stale_but_alive")
        self.assertEqual(L.calls, [])

    def test_stranger_runner_alive_blocks_any_launch(self):
        # Heartbeat pid dead, but ANOTHER runner pid is alive (the
        # A-01 end state): launching a third is refused by name.
        watchdog.pid_alive_desk = lambda pid: False
        root, state = mkroot(self, hb(30))
        L = Launcher()
        row = watchdog.check_once(root, launcher=L, now=NOW,
                                  live_pids={9999})
        self.assertEqual(row["status"], "duplicate_alive")
        self.assertEqual(L.calls, [])

    def test_wedged_runner_terminated_before_single_relaunch(self):
        root, state = mkroot(self, hb(watchdog.WEDGED_S + 60))
        L = Launcher()
        killed = []
        row = watchdog.check_once(
            root, launcher=L, now=NOW, live_pids={4242},
            killer=lambda pid: killed.append(pid) or True)
        self.assertEqual(killed, [4242])
        self.assertEqual(row["status"], "restarted")
        self.assertEqual(len(L.calls), 1)

    def test_wedged_runner_unkillable_means_no_launch(self):
        root, state = mkroot(self, hb(watchdog.WEDGED_S + 60))
        L = Launcher()
        row = watchdog.check_once(
            root, launcher=L, now=NOW, live_pids={4242},
            killer=lambda pid: False)
        self.assertEqual(row["status"], "degraded")
        self.assertEqual(L.calls, [])

    def test_dead_runner_still_relaunched_once(self):
        watchdog.pid_alive_desk = lambda pid: False
        root, state = mkroot(self, hb(30))
        L = Launcher()
        row = watchdog.check_once(root, launcher=L, now=NOW,
                                  live_pids=set())
        self.assertEqual(row["status"], "restarted")
        self.assertEqual(len(L.calls), 1)


class RunnerLockTests(unittest.TestCase):
    def test_second_runner_lock_is_refused(self):
        from desk3.run_live import acquire_runner_lock
        d = tempfile.mkdtemp(dir=os.environ.get("TMPDIR") or None)
        self.addCleanup(lambda: __import__("shutil").rmtree(d, True))
        first = acquire_runner_lock(d)
        self.assertIsNotNone(first)
        self.assertIsNone(acquire_runner_lock(d))
        first.close()


class GuardianDuplicateTests(unittest.TestCase):
    def test_guardian_counts_runners(self):
        script = open(os.path.join(
            ROOT, "desk3", "systemd",
            "v3_supervision_guardian.sh")).read()
        self.assertIn("duplicate_runner", script)
        self.assertIn("runner_count", script)
        self.assertIn("/proc", script)


class FundingVisibilityTests(unittest.TestCase):
    # R1 RULING 2026-10-25 supersedes the Binance fetch these two
    # tests pinned: the per-symbol isolation law (B3) is preserved
    # and re-pinned on the Coinalyze parse/producer; the detailed
    # Coinalyze blockers live in
    # tests/test_coinalyze_snapshot_funding_blockers.py.
    def test_fetch_funding_isolates_per_symbol_failures(self):
        from desk3 import producers
        out = producers.parse_coinalyze_current([
            {"symbol": "ADAUSDT_PERP.A", "value": "not-a-number"},
            {"symbol": "ENJUSDT_PERP.A", "value": 0.01},
            {"symbol": "LINKUSDT_PERP.A", "value": 0.01}])
        self.assertEqual(set(out), {"ENJUSDT", "LINKUSDT"})

    def test_fetch_funding_raises_only_when_all_fail(self):
        from desk3 import producers

        class FakeResp:
            status = 451

            def read(self):
                return b"{}"

        class FakeConn:
            def putrequest(self, method, path):
                pass

            def putheader(self, name, value):
                pass

            def endheaders(self):
                pass

            def getresponse(self):
                return FakeResp()

            def close(self):
                pass
        with self.assertRaises(RuntimeError):
            producers.fetch_coinalyze_current(
                "K", ("ADAUSDT",), conn_factory=lambda t: FakeConn())

    def test_silent_empty_producer_is_named_in_producer_errors(self):
        from desk3.cycle import Desk
        from desk3.broker import FakeBroker
        root = tempfile.mkdtemp(dir=os.environ.get("TMPDIR") or None)
        self.addCleanup(lambda: __import__("shutil").rmtree(root, True))
        desk = Desk(root, broker=FakeBroker(), sleeve_path=root)

        class SilentFail:
            last_error = "FetchError:HTTP 451"

            def __call__(self, pctx):
                return {}
        desk.add_producer("binance_funding", SilentFail(),
                          ["funding"], 28800)
        roll = desk.run_cycle(now=NOW)
        self.assertEqual(roll["producer_errors"].get("binance_funding"),
                         "FetchError:HTTP 451")
        desk.close()


class AdapterDirTests(unittest.TestCase):
    def test_adapter_dir_rows_are_qualified_and_evaluate(self):
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        bare = [r for r in cfg["sleeves"]
                if r.get("adapter_dir") and "." not in r["module"]]
        self.assertGreaterEqual(len(bare), 10)
        for row in bare:
            mod = importlib.import_module(
                f"{row['adapter_dir']}.{row['module']}")
            self.assertTrue(hasattr(mod, "evaluate"),
                            f"{row['id']}: adapter has no evaluate")

    def test_build_desk_qualifies_adapter_modules(self):
        # Source-level: build_desk must not hand the worker a bare
        # name for adapter_dir rows (the B4 root cause).
        src = open(os.path.join(ROOT, "desk3", "run_live.py")).read()
        self.assertIn('f"{adapter_dir}.{module}"', src)


if __name__ == "__main__":
    unittest.main()
