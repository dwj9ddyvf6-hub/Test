"""CURE2-QULLA-WARM-TIMEOUT-20261102 blocker.

Cure round 1 launched qulla_scan for session 2026-11-02 and the
run died on its 1800s timeout, leaving the producer dead. The
timeout's root cause is in how the warmer is driven:
runtime.qulla_warm.warm_missing delegates to
runtime.cache_warm.warm(), whose defaults run the ENTIRE desk
warm (the 40-symbol bb_rsi 1Hour expansion plus quotes, the
options chain warm, kraken, earnings, account read-back) on
every call, once per timeframe. Measured in Cure 2: fetching
exactly the missing (symbol, timeframe) pairs for the session
takes 45s and the produce step 9s. The fat warm is the defect.

The producer contract (desk3/producers_g4.QullaFileProducer)
serves the file only when its session is today's ET date: the
session names the DECISION date, with engine features fenced to
completed sessions before it. So default_session() must name
today on a trading day, and a future session (no bars can ever
exist for it yet) is refused.

Pins:
1. default_session() names today ET when today is a trading
   day, else the most recent trading day; never a future date.
2. run_scan() refuses a session after today ET immediately
   (no warmer subprocess is launched).
3. The scan snippet drives the LEAN warm: it fetches only the
   missing (symbol, timeframe) pairs through the door and runs
   the producer with warm_first=False; the fat cache_warm.warm
   path (warm_first=True) is never used.
"""
import os
import sys
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

from core.data import is_trading_day  # noqa: E402
from desk3 import qulla_scan  # noqa: E402


class TestQullaWarmTimeout(unittest.TestCase):
    def test_default_session_names_decision_date(self):
        today = datetime.now(ZoneInfo("America/New_York")).date()
        s = qulla_scan.default_session()
        d = datetime.fromisoformat(s).date()
        self.assertTrue(is_trading_day(d), s)
        self.assertLessEqual(d, today)
        if is_trading_day(today):
            self.assertEqual(d, today)

    def test_future_session_refused_before_warm(self):
        with self.assertRaises(RuntimeError) as ctx:
            qulla_scan.run_scan(os.getcwd(), session="2999-01-01",
                                timeout_s=5)
        self.assertIn("future", str(ctx.exception))

    def test_snippet_uses_lean_warm_only(self):
        src = open(qulla_scan.__file__).read()
        self.assertIn("warm_first=False", src)
        self.assertNotIn("warm_first=True", src)
        self.assertIn("_has_session", src)
        self.assertIn("get_bars", src)


if __name__ == "__main__":
    unittest.main()
