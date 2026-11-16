"""Blockers: GATE-CURES-20261110 (the 2026-11-10 morning gate).

The morning gate of Tue 2026-11-10 ran 1817 tests, FAILED with
1 failure + 2 errors. Two independent defects:

1. BUYBACK-WIRE-20261110. test_cure1_producer_freshness's
   test_buyback_scan_inside_gate failed: buyback scan age 8.27d at
   the gate (8.38d at reproduction) against the sleeve's 8-day
   gate. Root cause, proven from artifacts: desk3/buyback_scan.py
   is a manual-only scanner with NO caller anywhere (no cycle,
   scheduler, or cron invocation; grep of desk3 + the goal cron
   definitions finds only the serving producer and mentions in
   inspection charters). Its last run was the manual CURE1 refresh
   of 2026-11-02T05:35:05Z recorded in cache/scan/buyback.json, so
   the gate expired by the clock at 2026-11-10T05:35Z. The qulla
   channel had the identical built-not-wired defect and was cured
   2026-11-04 with a producer-shaped warmer (QULLA-WIRE-20261104);
   buyback never got one. Cure: BuybackScanWarmer in
   desk3/producers_g4.py, mirroring QullaScanWarmer, registered
   immediately before the buyback file producer: it launches
   `python3 -m desk3.buyback_scan` DETACHED when the scan's age
   passes 1 day (far inside the 8-day gate), bounded by an attempt
   marker to one launch per retry window. Fail direction: pre-cure
   the class does not exist (import error).

2. NIGHT-RECEIPT-REPORT-20261110. Both night tests of
   test_inspection_crons_v3_20261027_blockers ERRORED with
   KeyError: 'report' at last["report"]. Root cause: the
   2026-11-10 v3-night-inspection final receipt row
   (started 2026-11-10T00:15:00-05:00) is status complete with a
   verdict but carries NO "report" field, breaking the receipts
   ledger's own schema of record (22 of 26 complete rows carry
   report, including every complete row since the blocker was
   wired on 2026-11-08 until this one). The report itself was
   filed on time (inspection-night-2026-11-10.md); the producer
   row was the defect, and the charters' RUN RECEIPT paragraphs
   never named the report field, so the omission had no
   instruction-level block. Cure at the producer side: a
   correction receipt row appended to the ledger restating that
   run's completion WITH the report field (the ledger's own
   correction precedent, 2026-10-29), and both inspection
   charters' RUN RECEIPT paragraphs amended to require the
   report field in the final row. The consumer test was NOT
   widened and NOT weakened. The live-state tests below pin the
   schema: the latest complete receipt for each inspection job
   carries report + verdict and the named report exists. Fail
   direction: on the pre-cure ledger the night half fails with
   the missing field named.
"""
import json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from desk3.producers_g4 import BuybackScanWarmer  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOW = datetime(2026, 11, 10, 15, 0, tzinfo=timezone.utc)

GOAL_DIR = os.environ.get(
    "MUSE_DESK_GOAL_DIR",
    os.path.expanduser("~/workspace/goals/muse-desk-v3"))
RECEIPTS = os.path.join(GOAL_DIR, "hidden_files", "inspection_receipts.jsonl")


def mkroot(test, scanned_at):
    root = tempfile.mkdtemp(dir=os.environ.get("TMPDIR") or None)
    sdir = os.path.join(root, "cache", "scan")
    os.makedirs(sdir)
    if scanned_at is not None:
        with open(os.path.join(sdir, "buyback.json"), "w") as fh:
            json.dump({"scanned_at": scanned_at.isoformat(),
                       "scan_signals": []}, fh)
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


class BuybackWarmerTests(unittest.TestCase):
    def test_fresh_scan_launches_nothing(self):
        root = mkroot(self, NOW - timedelta(hours=12))
        L = Launcher()
        w = BuybackScanWarmer(root, launcher=L)
        self.assertEqual(w({"now": NOW}), {})
        self.assertEqual(L.calls, [])
        self.assertIsNone(w.last_error)

    def test_aged_scan_launches_once_per_window(self):
        root = mkroot(self, NOW - timedelta(days=2))
        L = Launcher()
        w = BuybackScanWarmer(root, launcher=L)
        self.assertEqual(w({"now": NOW}), {})
        self.assertEqual(len(L.calls), 1)
        self.assertEqual(w({"now": NOW + timedelta(minutes=5)}), {})
        self.assertEqual(len(L.calls), 1)

    def test_gate_expired_scan_launches(self):
        root = mkroot(self, NOW - timedelta(days=9))
        L = Launcher()
        w = BuybackScanWarmer(root, launcher=L)
        w({"now": NOW})
        self.assertEqual(len(L.calls), 1)

    def test_missing_file_launches(self):
        root = mkroot(self, None)
        L = Launcher()
        w = BuybackScanWarmer(root, launcher=L)
        w({"now": NOW})
        self.assertEqual(len(L.calls), 1)

    def test_launch_failure_is_named_not_raised(self):
        root = mkroot(self, NOW - timedelta(days=9))
        w = BuybackScanWarmer(root, launcher=Launcher(fail=True))
        self.assertEqual(w({"now": NOW}), {})
        self.assertIn("buyback_scan_launch", w.last_error or "")

    def test_warmer_registered_before_file_producer(self):
        import desk3.producers_g4 as g4

        class FakeDesk:
            def __init__(self):
                self.names = []

            def add_producer(self, name, prod, keys, ttl):
                self.names.append(name)

        desk = FakeDesk()
        g4.register_all_g4(desk, ROOT, env={})
        self.assertIn("buyback_warmer", desk.names)
        self.assertLess(desk.names.index("buyback_warmer"),
                        desk.names.index("buyback_scan"))


class LiveBuybackScanTests(unittest.TestCase):
    def test_live_buyback_scan_inside_gate(self):
        path = os.path.join(ROOT, "cache", "scan", "buyback.json")
        if not os.path.exists(path):
            self.skipTest("live buyback cache absent (code-only export)")
        with open(path) as fh:
            doc = json.load(fh)
        when = datetime.fromisoformat(
            str(doc["scanned_at"]).replace("Z", "+00:00"))
        age_days = (datetime.now(when.tzinfo) - when).total_seconds() / 86400.0
        self.assertLessEqual(age_days, 8.0,
                             f"buyback scan age {age_days:.2f}d > 8d gate")


class LatestReceiptSchemaTests(unittest.TestCase):
    def _latest_complete(self, job):
        rows = []
        with open(RECEIPTS) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        done = [r for r in rows
                if r.get("job") == job and r.get("status") == "complete"]
        self.assertTrue(done, "no complete receipt for %s" % job)
        return done[-1]

    def _check_latest(self, job):
        last = self._latest_complete(job)
        self.assertIn("report", last,
                      "latest complete %s receipt carries no report "
                      "field (NIGHT-RECEIPT-REPORT-20261110)" % job)
        self.assertIn("verdict", last,
                      "latest complete %s receipt carries no verdict" % job)
        report = os.path.expanduser(last["report"])
        self.assertTrue(os.path.exists(report),
                        "receipt report does not exist: %s" % report)

    def test_latest_night_receipt_carries_report(self):
        self._check_latest("v3-night-inspection")

    def test_latest_morning_receipt_carries_report(self):
        self._check_latest("v3-morning-inspection")


if __name__ == "__main__":
    unittest.main()
