"""QULLA-PREOPEN-DEFERRAL-20261113 blockers (Closure Program,
Workstream A, 2026-11-13): the qulla producer's clear-then-recur.

Root cause, proven from code and the live artifact: the engine's
intraday frame (muse-desk-v2 core/qulla_feeds.intraday_frame,
read-only upstream) is built ONLY from the decision session's own
RTH 1Min bars. The warmer launched the new session's first scan
pre-open (live artifact 2026-11-13: cache/qulla/proposals.json
written 14:00:02Z = 09:00 ET, 30 minutes before the open;
evidence daily_rows 10794, intraday_rows 0, error "RuntimeError:
qulla frames incomplete"), so the scan necessarily failed, the
errored file made QullaFileProducer fail closed
(qulla_scan_evidence_error) and qullamaggie_paper read UNFED, and
the attempt marker stamped by that doomed launch suppressed the
first post-open retry for the full 3600 s retry window. The prior
session reads clean at the night roll only because by then its
own RTH bars exist; the session date rolling at midnight re-arms
the defect every trading day.

Cure (desk3/qulla_scan.py + desk3/producers_g4.py): one shared
rule, scan_deferred(session, now_et) — a scan for today's session
is deferred until 09:47 ET (the first completed RTH 1Min bar at
09:31 ET plus the door's measured 15-minute SIP serve lag) on a
trading day. run_scan refuses with a named deferral BEFORE the
engine is invoked (no errored file can be written by any caller),
and QullaScanWarmer launches nothing and stamps no marker inside
the window. Rolled-back sessions (weekend/holiday) are never
deferred: their RTH bars all exist.

Fail direction on the pre-cure tree: scan_deferred does not exist
(import error), run_scan has no now_et parameter (TypeError), and
the warmer launches at 09:00 ET (the shape the qulla-wire fixture
originally encoded at 06:00 ET).
"""
import json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from desk3 import qulla_scan  # noqa: E402
from desk3.producers_g4 import QullaScanWarmer  # noqa: E402

ET = ZoneInfo("America/New_York")
# 2026-11-04 is a Wednesday (trading day); 2026-11-07 a Saturday.
WED_0900 = datetime(2026, 11, 4, 9, 0, tzinfo=ET)
WED_0947 = datetime(2026, 11, 4, 9, 47, tzinfo=ET)
WED_1000 = datetime(2026, 11, 4, 10, 0, tzinfo=ET)
SAT_0900 = datetime(2026, 11, 7, 9, 0, tzinfo=ET)


def _root_with_file(doc):
    root = tempfile.mkdtemp(prefix="qulladef_")
    qdir = os.path.join(root, "cache", "qulla")
    os.makedirs(qdir, exist_ok=True)
    if doc is not None:
        with open(os.path.join(qdir, "proposals.json"), "w") as fh:
            json.dump(doc, fh)
    return root


class Launcher:
    def __init__(self):
        self.calls = []

    def __call__(self, root):
        self.calls.append(root)
        return 4242


class TestScanDeferredRule(unittest.TestCase):

    def test_preopen_today_trading_day_is_deferred(self):
        self.assertTrue(qulla_scan.scan_deferred("2026-11-04", WED_0900))

    def test_at_0947_no_longer_deferred(self):
        self.assertFalse(qulla_scan.scan_deferred("2026-11-04", WED_0947))
        self.assertFalse(qulla_scan.scan_deferred("2026-11-04", WED_1000))

    def test_rolled_back_session_never_deferred(self):
        # Saturday 09:00 ET naming Friday's completed session: its
        # RTH bars all exist, so an early scan is legitimate.
        self.assertFalse(qulla_scan.scan_deferred("2026-11-06", SAT_0900))
        # A past session named on a trading-day morning, likewise.
        self.assertFalse(qulla_scan.scan_deferred("2026-11-03", WED_0900))

    def test_run_scan_refuses_preopen_without_invoking_engine(self):
        root = _root_with_file(None)
        with self.assertRaises(RuntimeError) as cm:
            qulla_scan.run_scan(root, session="2026-11-04",
                                now_et=WED_0900)
        self.assertIn("deferred", str(cm.exception))
        # Nothing was written: no errored proposals file can exist.
        self.assertFalse(os.path.exists(
            os.path.join(root, "cache", "qulla", "proposals.json")))


class TestWarmerDeferral(unittest.TestCase):

    def _warmer(self, doc):
        root = _root_with_file(doc)
        launcher = Launcher()
        return root, launcher, QullaScanWarmer(root, launcher=launcher)

    def test_warmer_launches_nothing_and_stamps_no_marker_preopen(self):
        stale = {"session": "2026-11-03", "proposals": []}
        root, launcher, w = self._warmer(stale)
        out = w({"now": WED_0900.astimezone(timezone.utc)})
        self.assertEqual(out, {})
        self.assertEqual(launcher.calls, [])
        self.assertIsNone(w.last_error)
        self.assertFalse(os.path.exists(
            os.path.join(root, "cache", "qulla", "scan_attempt.json")))

    def test_warmer_launches_once_window_opens(self):
        stale = {"session": "2026-11-03", "proposals": []}
        root, launcher, w = self._warmer(stale)
        w({"now": WED_0900.astimezone(timezone.utc)})
        self.assertEqual(launcher.calls, [])
        w({"now": WED_0947.astimezone(timezone.utc)})
        self.assertEqual(len(launcher.calls), 1)

    def test_errored_today_doc_still_deferred_preopen(self):
        # Yesterday's lesson: an errored doc must not be retried
        # into another errored write before bars can exist.
        errored = {"session": "2026-11-04", "proposals": [],
                   "evidence": {"error": "RuntimeError: qulla frames "
                                         "incomplete"}}
        root, launcher, w = self._warmer(errored)
        w({"now": WED_0900.astimezone(timezone.utc)})
        self.assertEqual(launcher.calls, [])


if __name__ == "__main__":
    unittest.main()
