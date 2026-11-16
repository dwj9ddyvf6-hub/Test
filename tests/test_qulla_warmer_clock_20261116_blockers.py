"""QULLA-WARMER-CLOCK-20261116 blocker.

Defect: the two Qulla warmer relaunch blocker files
(test_qulla_dead_launch_20261112_blockers and
TestQullaWarmerRetriesErrorDoc in
test_sleeve_firing_20261111_blockers) drove QullaScanWarmer with
wall-clock now. QULLA-PREOPEN-DEFERRAL-20261113 suppresses every
launch before 09:47 ET on a trading day, so the launch-expecting
tests passed or failed by the hour the gate ran: green Sunday
2026-11-15 23:50 ET (a non-trading day), red Monday 2026-11-16
00:06 to 00:20 ET with exactly 5 failures, and the same files
would go green again after 09:47 ET with no code change at all.

Cure: the tests inject the clock through the warmer's production
time source, the producer context's "now" value (the same value
cycle.py supplies live), pinned to a fixed trading day. Nothing
in production code changes and the deferral path is exercised,
not mocked: this file pins both simulated hours against the real
warmer and the real scan_deferred rule.

Pins:
1. Simulated pre-09:47 on a trading day (08:00 ET): no launch,
   no attempt marker, no error.
2. Simulated 09:47 ET exactly: the deferral lifts and the launch
   happens (the boundary the production rule names).
3. Simulated post-09:47 (15:00 ET): the launch happens and the
   marker is stamped with the simulated session and time.
4. A rolled-back session on a weekend is never deferred, at any
   simulated hour (the deferral's own scope rule).

Fail direction: on the pre-cure tree these pins pass too (the
production warmer was never wrong); the fail direction for this
cure lives in the two repaired files, whose launch-expecting
tests fail on the pre-cure tree whenever the gate runs before
09:47 ET on a trading day and pass on the cured tree at every
hour. This file exists so the simulated-hour behavior itself is
pinned by name and cannot silently drift.
"""
import json, os, sys, tempfile, unittest
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
from desk3.producers_g4 import QullaScanWarmer, _expected_qulla_session  # noqa: E402

ET = ZoneInfo("America/New_York")
MONDAY = (2026, 11, 16)   # a trading day
SATURDAY = (2026, 11, 14)  # rolled-back session (Friday 2026-11-13)


def _root(session):
    root = tempfile.mkdtemp()
    qdir = os.path.join(root, "cache", "qulla")
    os.makedirs(qdir)
    doc = {"session": session, "proposals": [],
           "evidence": {"error": "RuntimeError: qulla frames "
                                 "incomplete",
                        "intraday_rows": 0}}
    with open(os.path.join(qdir, "proposals.json"), "w") as fh:
        json.dump(doc, fh)
    return root


def _at(day, hour, minute):
    return datetime(day[0], day[1], day[2], hour, minute, tzinfo=ET)


class TestWarmerSimulatedClock(unittest.TestCase):
    def _run(self, now):
        session = _expected_qulla_session(now.date())
        root = _root(session)
        launches = []
        w = QullaScanWarmer(root, launcher=lambda r: launches.append(r),
                            retry_s=3600)
        out = w({"now": now})
        marker_path = os.path.join(root, "cache", "qulla",
                                   "scan_attempt.json")
        marker = None
        if os.path.exists(marker_path):
            with open(marker_path) as fh:
                marker = json.load(fh)
        return out, launches, marker, w

    def test_pre_open_simulated_no_launch_no_marker(self):
        out, launches, marker, w = self._run(_at(MONDAY, 8, 0))
        self.assertEqual(out, {})
        self.assertEqual(launches, [])
        self.assertIsNone(marker)
        self.assertIsNone(w.last_error)

    def test_boundary_0947_simulated_launches(self):
        out, launches, marker, w = self._run(_at(MONDAY, 9, 47))
        self.assertEqual(len(launches), 1)
        self.assertIsNotNone(marker)

    def test_post_open_simulated_launches_and_stamps(self):
        now = _at(MONDAY, 15, 0)
        out, launches, marker, w = self._run(now)
        self.assertEqual(len(launches), 1)
        self.assertEqual(marker.get("session"), "2026-11-16")
        self.assertEqual(marker.get("ts"), now.isoformat())

    def test_weekend_rolled_back_session_never_deferred(self):
        out, launches, marker, w = self._run(_at(SATURDAY, 8, 0))
        self.assertEqual(len(launches), 1)


if __name__ == "__main__":
    unittest.main()
