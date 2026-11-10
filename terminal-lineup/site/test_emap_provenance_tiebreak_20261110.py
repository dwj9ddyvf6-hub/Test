#!/usr/bin/env python3
"""Regression blocker: EMAP-PROVENANCE-TIEBREAK-20261110.

Failure class: the permanent expected-move filing log can hold two
different maps for one session that both match the prior volatility
close on record: the map the desk filed at the time (provenance
"filed_at_time") and a later reconstruction rebuilt from saved
closes (provenance "reconstructed"), whose anchor close can differ
by cents. refresh_expected_move refused to choose between any two
matching maps, so sessions 2026-11-02 through 2026-11-09 all became
unpublishable once their at-time filings reached the log, and the
Expected Move page froze.

Cure pinned here: resolve_sessions prefers the filed_at_time map
when exactly one of the tied maps carries that stamp, in either
candidate order, and still refuses (fail code 1) when provenance
is equal on both sides.
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


def real_maps(session="2026-11-02"):
    """The session's two genuine maps, read from the permanent log."""
    out = {}
    with open(LEDGER, encoding="utf-8") as fh:
        for line in fh:
            if '"em_1587"' not in line:
                continue
            row = json.loads(line)
            if row.get("session") != session:
                continue
            ev = (row.get("evaluations") or {}).get("em_1587") or {}
            m = (ev.get("sleeve_stamp") or {}).get("map")
            if m:
                out[row.get("filing") or "filed_at_time"] = m
    return out


class ProvenanceTiebreak(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maps = real_maps()
        assert "filed_at_time" in cls.maps and "reconstructed" in cls.maps, \
            "the 2026-11-02 provenance pair is missing from the log"
        cls.vix = {"2026-10-30": cls.maps["filed_at_time"]["vix_close"]}

    def test_at_time_map_wins(self):
        a, b = self.maps["filed_at_time"], self.maps["reconstructed"]
        filed = {"2026-11-02": {"k1": (a, 1.0, {}, "filed_at_time"),
                                "k2": (b, 2.0, {}, "reconstructed")}}
        r = R.resolve_sessions(filed, self.vix)
        self.assertIsInstance(r, dict)
        self.assertEqual(r["2026-11-02"][0]["anchor_close"],
                         a["anchor_close"])
        self.assertEqual(r["2026-11-02"][3], "filed_at_time")

    def test_at_time_map_wins_in_reverse_order(self):
        a, b = self.maps["filed_at_time"], self.maps["reconstructed"]
        filed = {"2026-11-02": {"k1": (b, 2.0, {}, "reconstructed"),
                                "k2": (a, 1.0, {}, "filed_at_time")}}
        r = R.resolve_sessions(filed, self.vix)
        self.assertIsInstance(r, dict)
        self.assertEqual(r["2026-11-02"][0]["anchor_close"],
                         a["anchor_close"])

    def test_equal_provenance_tie_still_refused(self):
        a, b = self.maps["filed_at_time"], self.maps["reconstructed"]
        filed = {"2026-11-02": {"k1": (a, 1.0, {}, "filed_at_time"),
                                "k2": (b, 2.0, {}, "filed_at_time")}}
        self.assertEqual(R.resolve_sessions(filed, self.vix), 1)


if __name__ == "__main__":
    unittest.main()
