#!/usr/bin/env python3
"""Regression blocker for CHAIN-SPOT-OPEN-WAIT-20261113.

Defect (2026-11-13 09:30 ET collector run): all three symbols
(SPY, QQQ, IWM) refused with spot quote_ts at the prior session's
16:00 ET close (2026-11-12T21:00:00Z). The run started at
09:29:36 ET inside the 5-minute dispatch tolerance, and Yahoo's
regularMarketTime still carried the prior close print; the old
re-fetch budget (3 fetches, sleeps 10 + 30 seconds) expired
before the new session's first prints advanced the timestamp.

Cure: fetch_spot_fresh polls up to SPOT_ATTEMPTS fetches with
SPOT_RETRY_SLEEPS spanning about five minutes, still fail-closed:
a quote stale after the last attempt is returned stale so the
caller's refusal fires. The 90-second freshness gate is unchanged.

Fail direction: against the pre-cure module (SPOT_ATTEMPTS = 3),
test_waits_through_open_lag fails: the poll stops after 3 fetches
and returns the stale quote.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collect_chains as cc


def make_fetch(states):
    """Fake fetch returning (price, source, ts, state) tuples,
    walking the given state list and then repeating its last."""
    calls = {"n": 0}

    def fetch(symbol):
        calls["n"] += 1
        state = states[min(calls["n"] - 1, len(states) - 1)]
        return (100.0, "fake", "ts", state)

    return fetch, calls


class SpotOpenWaitTests(unittest.TestCase):
    def test_waits_through_open_lag(self):
        # Prior-close stamp persists for five fetches after the
        # open, then the first prints turn the quote fresh.
        fetch, calls = make_fetch(
            ["stale", "stale", "stale", "stale", "stale", "fresh"])
        sleeps = []
        result = cc.fetch_spot_fresh("SPY", fetch=fetch,
                                     sleep=sleeps.append)
        self.assertEqual(result[3], "fresh")
        self.assertEqual(calls["n"], 6)
        self.assertEqual(len(sleeps), 5)

    def test_still_fail_closed_after_budget(self):
        fetch, calls = make_fetch(["stale"])
        result = cc.fetch_spot_fresh("SPY", fetch=fetch,
                                     sleep=lambda s: None)
        self.assertEqual(result[3], "stale")
        self.assertEqual(calls["n"], cc.SPOT_ATTEMPTS)

    def test_budget_spans_first_print_lag(self):
        self.assertGreaterEqual(cc.SPOT_ATTEMPTS, 6)
        self.assertGreaterEqual(sum(cc.SPOT_RETRY_SLEEPS), 240)
        self.assertEqual(len(cc.SPOT_RETRY_SLEEPS),
                         cc.SPOT_ATTEMPTS - 1)

    def test_fresh_first_try_no_retry(self):
        fetch, calls = make_fetch(["fresh"])
        sleeps = []
        result = cc.fetch_spot_fresh("SPY", fetch=fetch,
                                     sleep=sleeps.append)
        self.assertEqual(result[3], "fresh")
        self.assertEqual(calls["n"], 1)
        self.assertEqual(sleeps, [])

    def test_no_freshness_requirement_single_fetch(self):
        fetch, calls = make_fetch(["stale"])
        result = cc.fetch_spot_fresh("SPY", fetch=fetch,
                                     sleep=lambda s: None,
                                     require_fresh=False)
        self.assertEqual(result[3], "stale")
        self.assertEqual(calls["n"], 1)


if __name__ == "__main__":
    unittest.main()
