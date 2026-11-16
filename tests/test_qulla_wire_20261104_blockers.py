"""Blockers: QULLA-WIRE cure (2026-11-04).

Built-not-wired defect: desk3/qulla_scan.py runs the Qullamaggie
engine and writes cache/qulla/proposals.json, but NOTHING invoked
it — no caller in run_live, cycle, scheduler, or any cron — so the
file sat at session 2026-11-02, QullaFileProducer named
stale_qulla_session in producer_errors every cycle, and
qullamaggie_paper stayed UNFED missing its qulla input.

Cure: QullaScanWarmer (desk3/producers_g4.py), a producer-shaped
warmer registered immediately before the qulla file producer,
mirroring TensorWarmer's posture. When the served file's session is
not today's ET session it launches `python3 -m desk3.qulla_scan`
DETACHED (the scan runs up to its own 1800 s timeout; it must never
block a cycle) and records a per-session attempt marker that bounds
relaunches to one per retry window. Fresh file: no launch, no
error. Launch failure: named in last_error, {} returned.

Fail direction: pre-cure the class does not exist (import error).
"""
import json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from desk3.producers_g4 import QullaScanWarmer  # noqa: E402

ET = ZoneInfo("America/New_York")
# QULLA-PREOPEN-DEFERRAL-20261113: the fixture clock sits at 10:00
# ET, after the 09:31 ET scan deferral window. The original 06:00
# ET fixture encoded the defective timing itself: a launch then
# cannot succeed (no RTH 1Min bars for the session exist yet) and
# is now deferred by design; the deferral has its own blocker
# (test_qulla_preopen_deferral_20261113_blockers.py).
NOW = datetime(2026, 11, 4, 10, 0, tzinfo=ET).astimezone(timezone.utc)
TODAY = NOW.astimezone(ET).date().isoformat()
YESTERDAY = (NOW.astimezone(ET).date() - timedelta(days=1)).isoformat()


def mkroot(test, session):
    root = tempfile.mkdtemp(dir=os.environ.get("TMPDIR") or None)
    qdir = os.path.join(root, "cache", "qulla")
    os.makedirs(qdir)
    if session is not None:
        with open(os.path.join(qdir, "proposals.json"), "w") as fh:
            json.dump({"session": session, "proposals": []}, fh)
    test.addCleanup(lambda: __import__("shutil").rmtree(root, True))
    return root


class Launcher:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def __call__(self, root):
        self.calls.append(root)
        if self.fail:
            raise RuntimeError("boom")


class QullaWarmerTests(unittest.TestCase):
    def test_fresh_session_launches_nothing(self):
        root = mkroot(self, TODAY)
        L = Launcher()
        w = QullaScanWarmer(root, launcher=L)
        self.assertEqual(w({"now": NOW}), {})
        self.assertEqual(L.calls, [])
        self.assertIsNone(w.last_error)

    def test_stale_session_launches_once_per_window(self):
        root = mkroot(self, YESTERDAY)
        L = Launcher()
        w = QullaScanWarmer(root, launcher=L)
        self.assertEqual(w({"now": NOW}), {})
        self.assertEqual(len(L.calls), 1)
        self.assertEqual(w({"now": NOW + timedelta(minutes=5)}), {})
        self.assertEqual(len(L.calls), 1)

    def test_missing_file_launches(self):
        root = mkroot(self, None)
        L = Launcher()
        w = QullaScanWarmer(root, launcher=L)
        w({"now": NOW})
        self.assertEqual(len(L.calls), 1)

    def test_launch_failure_is_named_not_raised(self):
        root = mkroot(self, YESTERDAY)
        w = QullaScanWarmer(root, launcher=Launcher(fail=True))
        self.assertEqual(w({"now": NOW}), {})
        self.assertIn("qulla_scan_launch", w.last_error or "")


if __name__ == "__main__":
    unittest.main()
