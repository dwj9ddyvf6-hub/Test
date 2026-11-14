#!/usr/bin/env python3
"""Regression blocker: EMAP-REFILE-SUPERSESSION-20261113.

Failure class: for the session of 2026-11-13 the desk filed
two different expected-move maps, both stamped filed_at_time
and both matching the prior volatility close on record
(18.70): one at 16:11 ET on an anchor of 757.21 drawn from
8,418 SPY bars served, and a re-filing at 00:20 ET on an
anchor of 757.20 drawn from 8,439 SPY bars served (QQQ
8,445 against 8,424). The maps agree on the volatility
close, the session move and the weekly move; only the
anchor and its lines differ. The provenance tiebreak
(EMAP-PROVENANCE-TIEBREAK-20261110) resolves at-time against
reconstructed only, so two at-time filings tied and
refresh_expected_move refused to choose, freezing the page
(the tools runs of 2026-11-12 and 2026-11-13 both failed on
it, the second in the run of record for this cure).

Cure pinned here: among VIX-matching maps with equal
provenance, a filing that strictly supersedes the other
(later, and drawn from a strictly fuller evaluation: more
bars served in total, no name served fewer) is the
session's map of record, in either candidate order. Every
other equal-provenance tie still refuses (fail code 1): a
later filing whose evaluation served no more bars, a fuller
filing that is not later, and a tie with no bars-served
record on either side.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.expanduser("~/workspace/femto-lean"))

import refresh_expected_move as R  # noqa: E402

LEDGER = os.path.expanduser("~/workspace/femto-lean/state/ledger.jsonl")
SESSION = "2026-11-13"
PRIOR = "2026-11-12"


def real_pair():
    """The session's two genuine at-time filings, read from
    the permanent log: {anchor_close: (map, epoch, served)}."""
    out = {}
    with open(LEDGER, encoding="utf-8") as fh:
        for line in fh:
            if '"em_1587"' not in line:
                continue
            row = json.loads(line)
            if row.get("session") != SESSION:
                continue
            ev = (row.get("evaluations") or {}).get("em_1587") or {}
            m = (ev.get("sleeve_stamp") or {}).get("map")
            if m and (row.get("filing") or "filed_at_time") \
                    == "filed_at_time":
                out[m["anchor_close"]] = (
                    m, row["now"], ev.get("bars_served") or {})
    return out


class RefileSupersession(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pair = real_pair()
        assert 757.21 in cls.pair and 757.20 in cls.pair, \
            "the 2026-11-13 at-time pair is missing from the log"
        cls.vix = {PRIOR: cls.pair[757.20][0]["vix_close"]}

    def _filed(self, first_anchor, second_anchor):
        a = self.pair[first_anchor]
        b = self.pair[second_anchor]
        return {SESSION: {
            "k1": (a[0], a[1], a[2], "filed_at_time"),
            "k2": (b[0], b[1], b[2], "filed_at_time")}}

    def test_fuller_later_refiling_wins(self):
        r = R.resolve_sessions(self._filed(757.21, 757.20),
                               self.vix)
        self.assertIsInstance(r, dict)
        self.assertEqual(r[SESSION][0]["anchor_close"], 757.20)

    def test_fuller_later_refiling_wins_in_reverse_order(self):
        r = R.resolve_sessions(self._filed(757.20, 757.21),
                               self.vix)
        self.assertIsInstance(r, dict)
        self.assertEqual(r[SESSION][0]["anchor_close"], 757.20)

    def test_later_refiling_without_fuller_evaluation_refused(self):
        a = self.pair[757.21]
        b = self.pair[757.20]
        filed = {SESSION: {
            "k1": (a[0], a[1], a[2], "filed_at_time"),
            "k2": (b[0], b[1], a[2], "filed_at_time")}}  # same bars
        self.assertEqual(R.resolve_sessions(filed, self.vix), 1)

    def test_fuller_refiling_that_is_not_later_refused(self):
        a = self.pair[757.21]
        b = self.pair[757.20]
        filed = {SESSION: {
            "k1": (a[0], b[1], a[2], "filed_at_time"),
            "k2": (b[0], a[1], b[2], "filed_at_time")}}  # swapped times
        self.assertEqual(R.resolve_sessions(filed, self.vix), 1)

    def test_tie_with_no_bars_record_still_refused(self):
        a = self.pair[757.21]
        b = self.pair[757.20]
        filed = {SESSION: {
            "k1": (a[0], a[1], {}, "filed_at_time"),
            "k2": (b[0], b[1], {}, "filed_at_time")}}
        self.assertEqual(R.resolve_sessions(filed, self.vix), 1)


if __name__ == "__main__":
    unittest.main()
