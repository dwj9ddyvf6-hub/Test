#!/usr/bin/env python3
"""Tests for freshness_lint.py (ADOPT A3), including the fail direction."""
import os, sys, tempfile, unittest
from datetime import date
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import freshness_lint

REF = date(2026, 11, 2)


class FreshnessLintTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        p = self.dir / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_planted_unstamped_claim_errors_fresh1(self):
        p = self.write("STATE.md",
                       "# State\n\n## Prog (p1)\n- Headline: The roster holds 336 sleeves.\n")
        f = freshness_lint.lint_file(p, REF, "state")
        self.assertTrue(f["FRESH-1"])

    def test_stamped_claim_passes_fresh1(self):
        p = self.write("STATE.md",
                       "# State\n\n## Prog (p1)\n"
                       "- Headline: The roster holds 336 sleeves, as of 2026-11-01.\n"
                       "- Last verified: 2026-11-01\n")
        f = freshness_lint.lint_file(p, REF, "state")
        self.assertEqual(f["FRESH-1"], [])
        self.assertEqual(f["FRESH-2"], [])

    def test_aged_stamp_listed_fresh2(self):
        p = self.write("STATE.md",
                       "# State\n\n## Prog (p1)\n- Last verified: 2026-10-01 by audit.\n")
        f = freshness_lint.lint_file(p, REF, "state")
        self.assertTrue(f["FRESH-2"])

    def test_broken_proof_pointer_errors_fresh3(self):
        p = self.write("STATE.md",
                       "# State\n\n## Prog (p1)\n"
                       "- Proof: ~/workspace/definitely-not-here-xyz/missing.json as of 2026-11-01.\n")
        f = freshness_lint.lint_file(p, REF, "state")
        self.assertTrue(f["FRESH-3"])

    def test_resolving_proof_pointer_passes_fresh3(self):
        target = self.write("evidence.json", "{}\n")
        p = self.write("STATE.md",
                       f"# State\n\n## Prog (p1)\n- Proof: {target} as of 2026-11-01.\n")
        f = freshness_lint.lint_file(p, REF, "state")
        self.assertEqual(f["FRESH-3"], [])

    def test_aged_snapshot_stamp_warns(self):
        p = self.write("CONTEXT-SNAPSHOT.md",
                       "# Context Snapshot\n\nSnapshot: 2026-10-20 21:46 ET by audit.\n")
        f = freshness_lint.lint_file(p, REF, "snapshot")
        self.assertTrue(f["FRESH-2"])

    def test_due_claim_computed(self):
        p = self.write("STATE.md",
                       "# State\n\n## Prog (p1)\n"
                       "- Gate runs nightly. asserts-current-behavior: true; verified: 2026-01-01\n"
                       "- Old decision. asserts-current-behavior: false\n")
        f = freshness_lint.lint_file(p, REF, "state")
        self.assertEqual(len(f["due"]), 1)
        self.assertIn("DUE", f["due"][0])


if __name__ == "__main__":
    unittest.main()
