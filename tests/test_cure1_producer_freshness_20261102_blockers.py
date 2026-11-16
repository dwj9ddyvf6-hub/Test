"""CURE1-DESK-20261102 blockers, stale file-served producers.

State invariant (the swing-watch precedent: state/data invariants
are blockers too). On 2026-11-02 health cycle 51 carried
producer_error:buyback_scan:buyback_scan_stale and
producer_error:qulla:stale_qulla_session: cache/qulla/proposals.json
was session 2026-10-23 and cache/scan/buyback.json was scanned
2026-10-25, because the generators (desk3.qulla_scan,
desk3.buyback_scan) are manual-only and nothing had run them since
2026-10-25. The freshness GATES were correct (they failed closed);
the defect was the missing refresh. This blocker pins the live
state: the qulla session is a trading day no more than 4 calendar
days behind today ET (a Friday session stays valid across the
weekend) or pre-generated for a coming trading day, and the
buyback scan is inside the sleeve's own 8-day gate. It goes red
the moment either file ages out again.
"""
import json
import os
import sys
import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")


class TestLiveProducerFilesFresh(unittest.TestCase):
    def test_qulla_session_current(self):
        path = os.path.join(ROOT, "cache", "qulla", "proposals.json")
        if not os.path.exists(path):
            # Live-state invariant: the cache is runtime state (not
            # tracked), so a code-only export structurally cannot
            # carry it. Skip by name there; on the live tree the
            # freshness gate runs at full strength. (Clean-export
            # cure, 2026-11-08.)
            self.skipTest("live qulla cache absent (code-only export)")
        doc = json.load(open(path))
        session = datetime.fromisoformat(doc["session"]).date() \
            if isinstance(doc.get("session"), str) else None
        self.assertIsNotNone(session, doc.get("session"))
        from core.data import is_trading_day
        self.assertTrue(is_trading_day(session),
                        f"qulla session {session} is not a trading day")
        today = datetime.now(ET).date()
        self.assertGreaterEqual(session, today - timedelta(days=4),
                                f"qulla session {session} stale at {today}")
        self.assertLessEqual(session, today + timedelta(days=4),
                             f"qulla session {session} implausibly future")

    def test_buyback_scan_inside_gate(self):
        path = os.path.join(ROOT, "cache", "scan", "buyback.json")
        if not os.path.exists(path):
            self.skipTest(
                "live buyback cache absent (code-only export)")
        doc = json.load(open(path))
        self.assertIsInstance(doc.get("scan_signals"), list)
        when = datetime.fromisoformat(
            str(doc["scanned_at"]).replace("Z", "+00:00"))
        age_days = (datetime.now(when.tzinfo) - when).total_seconds() \
            / 86400.0
        self.assertGreaterEqual(age_days, 0)
        self.assertLessEqual(age_days, 8.0,
                             f"buyback scan age {age_days:.2f}d > 8d gate")


if __name__ == "__main__":
    unittest.main()
