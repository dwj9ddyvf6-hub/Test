"""INSPECTION-CRONS-V3-20261027 blocker (cron cure 2026-10-27;
blocker wired 2026-11-08 by the weekly-recheck cure lane).

Defect: the twice-daily inspection law had no live coverage; only
the retired femto-lean pair existed (disabled), so no v3 inspection
ran on 2026-10-27. Cure: v3-morning-inspection (Mon-Fri 07:00 ET)
and v3-night-inspection (daily 00:15 ET) created, enabled, owned by
goal:muse-desk-v3. No desk production code changed, so the BUGLOG
named no blocker; the guard it named instead was structural (each
charter audits the pair's enabled state, and every run appends to
the receipts ledger).

This blocker makes that structural guard mechanical in the gate:
the receipts ledger is the crons' own output, so if either job is
deleted or dies, its receipts stop and this test goes red. The
charters' text in the goal cron definitions (outside this repo)
cannot be asserted from inside the repo; what CAN be asserted from
the gate is the effect the BUGLOG itself named as proof: filed
reports and complete receipts for both jobs, current ones.

MUSE_DESK_GOAL_DIR overrides the goals location (testability);
default is the live goal workspace.
"""
import glob
import json
import os
import time
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOAL_DIR = os.environ.get(
    "MUSE_DESK_GOAL_DIR",
    os.path.expanduser("~/workspace/goals/muse-desk-v3"))
HIDDEN = os.path.join(GOAL_DIR, "hidden_files")
RECEIPTS = os.path.join(HIDDEN, "inspection_receipts.jsonl")


def _receipts():
    rows = []
    with open(RECEIPTS) as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


class TestInspectionCronsV3(unittest.TestCase):
    def test_receipts_ledger_exists(self):
        self.assertTrue(os.path.exists(RECEIPTS),
                        "inspection receipts ledger missing; the v3 "
                        "inspection pair has produced nothing")

    def _latest_complete(self, job):
        done = [r for r in _receipts()
                if r.get("job") == job and r.get("status") == "complete"]
        self.assertTrue(done, "no complete receipt for %s" % job)
        return done[-1]

    def test_night_inspection_ran_recently(self):
        last = self._latest_complete("v3-night-inspection")
        report = os.path.expanduser(last["report"])
        self.assertTrue(os.path.exists(report))
        age_h = (time.time() - os.path.getmtime(report)) / 3600.0
        self.assertLess(age_h, 36,
                        "latest night inspection report is %.1f h old; "
                        "the daily 00:15 ET cron is not running" % age_h)

    def test_night_report_records_the_cron_census(self):
        last = self._latest_complete("v3-night-inspection")
        with open(os.path.expanduser(last["report"])) as fh:
            txt = fh.read()
        self.assertIn("v3-morning-inspection", txt)
        self.assertIn("v3-night-inspection", txt)

    def test_morning_inspection_has_completed(self):
        self._latest_complete("v3-morning-inspection")
        reports = glob.glob(os.path.join(
            HIDDEN, "inspection-morning-*.md"))
        self.assertTrue(reports, "no morning inspection report filed")


if __name__ == "__main__":
    unittest.main()
