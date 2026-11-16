"""Blockers: LAUNCH-KILL-LOOP cure (2026-11-04).

Live failure, 2026-11-03: after the first afternoon relaunch, every
fresh runner was terminated at LAUNCH_GRACE_S (900 s) mid-first-cycle
(reason launched_no_heartbeat, 32 terminations in state/watchdog.jsonl)
because first cycles under load ran longer than the launch grace:
median cycle 861 s, warm phase alone up to ~440 s. Each kill made the
next first cycle slower (backlog), so the desk completed no cycle for
300.5 minutes (21:03Z to 02:03Z) while sleeves' journals proved work
was landing the whole time.

Cure: past launch grace, a launched runner whose desk shows journaled
activity inside the hold window (sleeve journal writes, or the warm
product landing) is HELD, status launch_hold, never terminated and
never relaunched beside. A launched runner with NO activity inside
the window keeps the old behaviour exactly (terminated, relaunched),
which test_launched_runner_past_launch_grace_is_relaunched in
test_harden_supervision_blockers.py already pins.

Fail direction: on the pre-cure watchdog the two hold tests fail
(the runner is restarted); the stale-activity test passes both
before and after.
"""
import json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from desk3 import watchdog  # noqa: E402

NOW = datetime(2026, 10, 25, 3, 0, 0, tzinfo=timezone.utc)


def mkroot(test):
    root = tempfile.mkdtemp(dir=os.environ.get("TMPDIR") or None)
    state = os.path.join(root, "state")
    os.makedirs(state)
    with open(os.path.join(state, "runner.json"), "w") as fh:
        json.dump({"pid": 999999, "cycle": 7, "mode": "evaluate-only",
                   "ts": (NOW - timedelta(seconds=30)).isoformat()}, fh)
    test.addCleanup(lambda: __import__("shutil").rmtree(root, True))
    return root, state


class Launcher:
    def __init__(self):
        self.calls = []

    def __call__(self, root, mode):
        self.calls.append((root, mode))
        return 424242


class Killer:
    def __init__(self):
        self.calls = []

    def __call__(self, pid):
        self.calls.append(pid)
        return True


def launched_past_grace(state):
    watchdog._write_launched(
        state, 555, "evaluate-only",
        NOW - timedelta(seconds=watchdog.LAUNCH_GRACE_S + 60))


def journal_with_mtime(state, when, sleeve="sleeve_x"):
    d = os.path.join(state, sleeve)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "journal.jsonl")
    with open(path, "w") as fh:
        fh.write("{}\n")
    ts = when.timestamp()
    os.utime(path, (ts, ts))
    return path


class LaunchHoldTests(unittest.TestCase):
    def setUp(self):
        self._alive = watchdog.pid_alive_desk
        self.addCleanup(setattr, watchdog, "pid_alive_desk", self._alive)
        watchdog.pid_alive_desk = lambda pid: pid == 555

    def test_past_grace_with_fresh_journal_activity_is_held(self):
        root, state = mkroot(self)
        launched_past_grace(state)
        journal_with_mtime(state, NOW - timedelta(seconds=120))
        L, K = Launcher(), Killer()
        row = watchdog.check_once(root, launcher=L, now=NOW,
                                  live_pids={555}, killer=K)
        self.assertEqual(row["status"], "launch_hold")
        self.assertEqual(row["action"], "none")
        self.assertEqual(L.calls, [])
        self.assertEqual(K.calls, [])

    def test_past_grace_with_warm_product_landing_is_held(self):
        root, state = mkroot(self)
        launched_past_grace(state)
        path = os.path.join(state, "warm_bars.json")
        with open(path, "w") as fh:
            fh.write("{}")
        ts = (NOW - timedelta(seconds=60)).timestamp()
        os.utime(path, (ts, ts))
        L, K = Launcher(), Killer()
        row = watchdog.check_once(root, launcher=L, now=NOW,
                                  live_pids={555}, killer=K)
        self.assertEqual(row["status"], "launch_hold")
        self.assertEqual(L.calls, [])
        self.assertEqual(K.calls, [])

    def test_past_grace_with_stale_activity_still_restarts(self):
        root, state = mkroot(self)
        launched_past_grace(state)
        journal_with_mtime(state, NOW - timedelta(seconds=7200))
        L, K = Launcher(), Killer()
        row = watchdog.check_once(root, launcher=L, now=NOW,
                                  live_pids={555}, killer=K)
        self.assertEqual(row["status"], "restarted")
        self.assertEqual(row["reason"], "launched_no_heartbeat")
        self.assertEqual(len(L.calls), 1)
        self.assertEqual(K.calls, [555])


class LaunchHoldCpuTests(unittest.TestCase):
    """LAUNCH-HOLD-CPU-20261104: the warm/startup phase writes no
    journals, so CPU progress between checks is the activity signal
    there. Advancing jiffies hold; static jiffies do not."""

    def setUp(self):
        self._alive = watchdog.pid_alive_desk
        self._jiffies = getattr(watchdog, "_pid_cpu_jiffies", None)
        self.addCleanup(setattr, watchdog, "pid_alive_desk", self._alive)
        if self._jiffies is not None:
            self.addCleanup(setattr, watchdog, "_pid_cpu_jiffies",
                            self._jiffies)
        watchdog.pid_alive_desk = lambda pid: pid == 555

    def launched_with_cpu(self, state, cpu):
        watchdog._write_launched(
            state, 555, "evaluate-only",
            NOW - timedelta(seconds=watchdog.LAUNCH_GRACE_S + 60))
        path = os.path.join(state, "watchdog_launched.json")
        rec = json.load(open(path))
        rec["cpu_jiffies"] = cpu
        with open(path, "w") as fh:
            json.dump(rec, fh)

    def test_cpu_advancing_is_held_without_journals(self):
        root, state = mkroot(self)
        self.launched_with_cpu(state, 100)
        watchdog._pid_cpu_jiffies = lambda pid: 500
        L, K = Launcher(), Killer()
        row = watchdog.check_once(root, launcher=L, now=NOW,
                                  live_pids={555}, killer=K)
        self.assertEqual(row["status"], "launch_hold")
        self.assertEqual(L.calls, [])
        self.assertEqual(K.calls, [])

    def test_cpu_static_still_restarts(self):
        root, state = mkroot(self)
        self.launched_with_cpu(state, 500)
        watchdog._pid_cpu_jiffies = lambda pid: 500
        L, K = Launcher(), Killer()
        row = watchdog.check_once(root, launcher=L, now=NOW,
                                  live_pids={555}, killer=K)
        self.assertEqual(row["status"], "restarted")
        self.assertEqual(len(L.calls), 1)
        self.assertEqual(K.calls, [555])


if __name__ == "__main__":
    unittest.main()
