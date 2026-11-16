"""Blockers: QULLA-DEAD-LAUNCH-20261112.

Live artifact 2026-11-12: QullaScanWarmer stamped the per-session
attempt marker at 15:38:27Z (the runner's first pass after the
15:38Z host boot) and launched the detached scan; the child
produced NOTHING — no bar file touched (AAPL/NVDA 1Min and AAPL
1Day mtimes stayed at their pre-boot stamps), no scan.log append,
no proposals.json rewrite, no qulla process alive at the 16:03Z
and 16:05Z checks, and no OOM or kill record in the boot journal.
Its death left no trace anywhere, and the marker — written BEFORE
the launch, carrying no pid — suppressed every retry for the full
3600 s window while QullaFileProducer kept naming the stale
pre-open evidence error and qullamaggie_paper sat UNFED well after
the 09:30 ET open. The BUGLOG's QULLA-PREOPEN-FRAMES clearance
("the warmer's first post-open hourly retry can first produce an
error-None file") was falsified on destination evidence.

Cure (desk3/producers_g4.py, QullaScanWarmer only — plumbing):
the default launcher returns the child pid; the warmer launches
FIRST and stamps the marker after, recording the pid; a launcher
exception leaves NO marker (the failure stays named in last_error
and is retried on the next call instead of being masked by a
marker); and the retry suppression no longer shields a launch
that is PROVEN dead — marker pid not alive (a zombie counts as
dead) and proposals.json not rewritten since the marker. Markers
without a pid (pre-cure shape, injected test launchers) keep the
exact old suppression semantics, and a live recorded pid still
bounds relaunches to one per window.

Fail direction: pre-cure, the dead-launch tests launch nothing
(the marker shields the dead child), a failed launch still leaves
a marker behind, and no pid is ever recorded.
"""
import json, os, subprocess, sys, tempfile, time, unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from desk3.producers_g4 import QullaScanWarmer, _expected_qulla_session  # noqa: E402

ET = ZoneInfo("America/New_York")

# QULLA-WARMER-CLOCK-20261116: this file drives the warmer through
# its production time source (the producer context's "now"), pinned
# to a fixed trading-day afternoon: Monday 2026-11-16, 15:00 ET.
# The pre-cure file used wall-clock now, and QULLA-PREOPEN-
# DEFERRAL-20261113 suppresses every launch before 09:47 ET on a
# trading day, so the launch-expecting tests passed or failed by
# the hour the gate ran (the gate's 5 standing failures at the
# 2026-11-16 00:06 to 00:20 ET runs). The deferral path itself is
# exercised, not bypassed: the warmer still reads scan_deferred
# against this same clock, and the simulated pre-09:47 behavior is
# pinned in test_qulla_warmer_clock_20261116_blockers.py.
FIXED_NOW = datetime(2026, 11, 16, 15, 0, tzinfo=ET)


def _today():
    return FIXED_NOW.date().isoformat()


class Launcher:
    def __init__(self, pid=None, fail=False):
        self.calls = []
        self.pid = pid
        self.fail = fail

    def __call__(self, root):
        self.calls.append(root)
        if self.fail:
            raise RuntimeError("boom")
        return self.pid


def _reaped_pid():
    """A pid that provably does not exist (child run and reaped)."""
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    return proc.pid


class QullaDeadLaunchTests(unittest.TestCase):
    def _root(self, marker=None, marker_after_proposals=True):
        root = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(root, True))
        qdir = os.path.join(root, "cache", "qulla")
        os.makedirs(qdir)
        session = _expected_qulla_session(FIXED_NOW.date())
        doc = {"session": session, "proposals": [],
               "evidence": {"error": "RuntimeError: qulla frames "
                                     "incomplete",
                            "intraday_rows": 0}}
        with open(os.path.join(qdir, "proposals.json"), "w") as fh:
            json.dump(doc, fh)
        if marker is not None:
            with open(os.path.join(qdir, "scan_attempt.json"), "w") as fh:
                json.dump(marker, fh)
            if not marker_after_proposals:
                # proposals rewritten AFTER the marker: the scan did
                # produce its terminal output, suppression must hold
                # even with a dead recorded pid.
                mtime = os.path.getmtime(
                    os.path.join(qdir, "scan_attempt.json"))
                os.utime(os.path.join(qdir, "proposals.json"),
                         (mtime + 10, mtime + 10))
        return root

    def _marker(self, root):
        path = os.path.join(root, "cache", "qulla", "scan_attempt.json")
        with open(path) as fh:
            return json.load(fh)

    def _now(self):
        return {"now": FIXED_NOW}

    def test_dead_launch_relaunches_inside_window(self):
        dead = _reaped_pid()
        root = self._root(marker={"session": _today(),
                                  "ts": FIXED_NOW.isoformat(),
                                  "pid": dead})
        L = Launcher(pid=os.getpid())
        w = QullaScanWarmer(root, launcher=L, retry_s=3600)
        self.assertEqual(w(self._now()), {})
        self.assertEqual(len(L.calls), 1,
                         "a proven-dead launch must not be shielded "
                         "by its own attempt marker")
        # the fresh marker names the live replacement launch
        self.assertEqual(self._marker(root).get("pid"), os.getpid())

    def test_live_launch_still_suppresses(self):
        root = self._root(marker={"session": _today(),
                                  "ts": FIXED_NOW.isoformat(),
                                  "pid": os.getpid()})
        L = Launcher()
        w = QullaScanWarmer(root, launcher=L, retry_s=3600)
        w(self._now())
        self.assertEqual(L.calls, [])

    def test_dead_pid_with_output_since_marker_still_suppresses(self):
        dead = _reaped_pid()
        root = self._root(marker={"session": _today(),
                                  "ts": FIXED_NOW.isoformat(),
                                  "pid": dead},
                          marker_after_proposals=False)
        L = Launcher()
        w = QullaScanWarmer(root, launcher=L, retry_s=3600)
        w(self._now())
        self.assertEqual(L.calls, [])

    def test_legacy_marker_without_pid_still_suppresses(self):
        root = self._root(marker={"session": _today(),
                                  "ts": FIXED_NOW.isoformat()})
        L = Launcher()
        w = QullaScanWarmer(root, launcher=L, retry_s=3600)
        w(self._now())
        self.assertEqual(L.calls, [])

    def test_launch_failure_leaves_no_marker(self):
        root = self._root(marker=None)
        w = QullaScanWarmer(root, launcher=Launcher(fail=True))
        self.assertEqual(w(self._now()), {})
        self.assertIn("qulla_scan_launch", w.last_error or "")
        self.assertFalse(os.path.exists(
            os.path.join(root, "cache", "qulla", "scan_attempt.json")),
            "a failed launch must not stamp the marker that would "
            "suppress its own retry")

    def test_marker_records_launched_pid(self):
        root = self._root(marker=None)
        L = Launcher(pid=424242)
        w = QullaScanWarmer(root, launcher=L)
        w(self._now())
        self.assertEqual(len(L.calls), 1)
        marker = self._marker(root)
        self.assertEqual(marker.get("pid"), 424242)
        self.assertEqual(marker.get("session"), _today())

    def test_pid_alive_semantics(self):
        self.assertTrue(QullaScanWarmer._pid_alive(os.getpid()))
        self.assertFalse(QullaScanWarmer._pid_alive(_reaped_pid()))
        # a zombie child (exited, not yet reaped) counts as dead
        proc = subprocess.Popen([sys.executable, "-c", "pass"])
        try:
            deadline = time.time() + 5
            state = ""
            while time.time() < deadline:
                try:
                    with open(f"/proc/{proc.pid}/stat", "rb") as fh:
                        state = fh.read().decode(
                            errors="replace").rsplit(")", 1)[-1].split()[0]
                except OSError:
                    state = ""
                if state == "Z":
                    break
                time.sleep(0.05)
            if state != "Z":
                self.skipTest("zombie state not observable on this host")
            self.assertFalse(QullaScanWarmer._pid_alive(proc.pid))
        finally:
            proc.wait()


if __name__ == "__main__":
    unittest.main()
