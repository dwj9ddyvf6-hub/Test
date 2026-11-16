#!/usr/bin/env python3
"""Tests for verify_quotes.py (ADOPT A4)."""
import os, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_quotes


class VerifyQuotesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.f = Path(self.tmp.name) / "src.md"
        self.f.write_text("line one is here now\nthe exact quoted line stands\nthird line\n",
                          encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_exact_quote_passes(self):
        r = verify_quotes.verify_triples([(str(self.f), 2, "the exact quoted line stands")])
        self.assertTrue(r[0]["ok"])

    def test_one_character_mutation_fails(self):
        r = verify_quotes.verify_triples([(str(self.f), 2, "the exact quoted line standz")])
        self.assertFalse(r[0]["ok"])

    def test_short_quote_refused(self):
        r = verify_quotes.verify_triples([(str(self.f), 1, "line one")])
        self.assertFalse(r[0]["ok"])
        self.assertIn("shorter", r[0]["reason"])


if __name__ == "__main__":
    unittest.main()
