#!/usr/bin/env python3
"""Regression blocker: MEMORY-CANARY-RANK-20261110.

Failure class: memory_search.query multiplied bm25 scores by
factors below 1 intending to promote curated sources. FTS5 bm25
scores are negative and smaller-is-better, so multiplying by 0.9
moved a curated chunk's score toward zero, which ranks it WORSE:
the "boost" was an arithmetic demotion of every curated source.
It stayed invisible while raw score gaps were small and bit when
corpus growth widened them: the 2026-11-09 nightly canary fell to
hit@1 10/14 and hit@5 13/14, with the three-way dead-drop group
page pushed to rank 6 by chart-study and dated-log chunks.

Cure pinned here: promotion factors are above 1 (groups 1.25,
people 1.15, MEMORY.md and USER.md 1.05), and the canary suite
holds its 2026-11-06 baseline of hit@1 11/14 and hit@5 14/14.

Amendment (2026-11-10, GLORY Item 3, glory-memory lane): corpus
growth let a daily-note chunk outrank the dead-drop group page,
so the groups factor was raised 1.25 -> 1.6 in memory_search.py
(restoring hit@1 11/14, hit@5 unchanged). This blocker's groups
assertion follows the cured value; it was not updated in that
pass and failed stale until the W3 cure (SYS-4) on 2026-11-10.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import memory_search as ms  # noqa: E402


class CanaryRank(unittest.TestCase):
    def test_dead_drop_group_page_in_top5(self):
        res = ms.query("three way dead drop five beats B0 B4 Claude", k=5)
        paths = [r["path"] for r in res]
        self.assertTrue(any("three-way-dead-drop" in p for p in paths),
                        f"group page missing from top 5: {paths}")

    def test_canary_baseline_holds(self):
        self.assertEqual(ms.canary(), 14)

    def test_query_source_uses_promoting_factors(self):
        src = open(os.path.join(HERE, "memory_search.py"),
                   encoding="utf-8").read()
        # Groups factor as cured 2026-11-10 (GLORY Item 3,
        # glory-memory lane): raised 1.25 -> 1.6; see docstring.
        self.assertIn("THEN 1.6", src)
        self.assertIn("THEN 1.15", src)
        q = src[src.index("def query("):src.index("def snippet(")]
        self.assertNotIn("THEN 0.", q)


if __name__ == "__main__":
    unittest.main()
