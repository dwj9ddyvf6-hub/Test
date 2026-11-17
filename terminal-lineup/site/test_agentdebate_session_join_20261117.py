#!/usr/bin/env python3
"""Regression blocker for AGENTDEBATE-SESSION-JOIN-20261117.

Defect (every 17:30 tape lane run, 2026-11-10 through
2026-11-16): Agent Debate fail-closed with "Flow Board carries
no figures from the tape card the Second Opinion's prints were
built from ... for SPY", so tape_family_run.py exited 1 and the
family was reported NOT synced, even though the final state
after the 19:00 tools lane re-sync was current every night.

Root cause: the prints join keyed on the tape card generation
stamp (Second Opinion's prints_published_at_utc). The Flow
Board carries that stamp only on its freshest session's cell;
for older sessions its cells carry the tape run log's run-end
stamp (refresh_premiummeter.py). At 17:30 the Second Opinion
is by lane design built from the previous session's card, so
its generation stamp matches no cell, ever, at that hour.

Cure: select_prints_cell in refresh_agentdebate.py joins by
generation first, then by the Second Opinion's own session;
the exact integer parity checks in the refresh (call-side,
put-side, net sum, print count) remain the like-for-like proof
and still stop the refresh on any figure disagreement, and a
session with no cell still stops it.

Fail direction: against the pre-cure module this test errors
(select_prints_cell did not exist; the only join was the
generation equality that failed the 2026-11-16 run).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import refresh_agentdebate as ad


CELLS = [
    {"session": "2026-11-13",
     "published_at_utc": "2026-11-13T21:54:33.384752+00:00",
     "call_net_premium_usd": 100, "put_net_premium_usd": -40,
     "prints_examined": 1000},
    {"session": "2026-11-16",
     "published_at_utc": "2026-11-16T21:47:19.380113+00:00",
     "call_net_premium_usd": 200, "put_net_premium_usd": -50,
     "prints_examined": 2000},
]


class SelectPrintsCellTests(unittest.TestCase):
    def test_generation_join_preferred_when_stamp_carried(self):
        cell, by = ad.select_prints_cell(
            CELLS, "2026-11-16T21:47:19.380113+00:00", "2026-11-16")
        self.assertEqual(by, "generation")
        self.assertEqual(cell["session"], "2026-11-16")

    def test_session_join_when_generation_stamp_not_carried(self):
        # The 2026-11-16 17:30 state: the Second Opinion was
        # built from the 2026-11-13 card (generation stamp
        # 21:47:06), the Flow Board's 2026-11-13 cell carries
        # the run-end stamp 21:54:33. Pre-cure this joined to
        # nothing and the refresh stopped.
        cell, by = ad.select_prints_cell(
            CELLS, "2026-11-13T21:47:06.269868+00:00", "2026-11-13")
        self.assertEqual(by, "session")
        self.assertEqual(cell["session"], "2026-11-13")

    def test_no_cell_for_session_joins_to_nothing(self):
        cell, by = ad.select_prints_cell(
            CELLS, "2026-11-12T21:47:06+00:00", "2026-11-12")
        self.assertIsNone(cell)
        self.assertIsNone(by)

    def test_no_card_stamp_joins_own_session_not_freshest(self):
        cell, by = ad.select_prints_cell(CELLS, None, "2026-11-13")
        self.assertEqual(by, "session")
        self.assertEqual(cell["session"], "2026-11-13")


if __name__ == "__main__":
    unittest.main()
