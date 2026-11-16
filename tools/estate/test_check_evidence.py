#!/usr/bin/env python3
"""Tests for check_evidence.py (ADOPT A2), including the fail direction."""
import json, os, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_evidence, research_capture


SOURCE_TEXT = ("The fleet counted 42,000 units on 2026-01-15 and grew 12% "
               "to a total of 47000 units.\n")


class CheckEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.program = root / "prog"
        self.program.mkdir()
        src = root / "fleet.txt"
        src.write_text(SOURCE_TEXT, encoding="utf-8")
        research_capture.capture(src, self.program, captured="2026-11-02")

    def tearDown(self):
        self.tmp.cleanup()

    def write_page(self, name, body):
        p = self.program / name
        p.write_text(body, encoding="utf-8")
        return p

    def test_verbatim_page_reports_clean(self):
        self.write_page("clean.md",
                        "# Clean\n\nSources: sources/raw/fleet.txt\n\n"
                        "The fleet counted 42,000 units on 2026-01-15 and grew 12%.\n")
        result = check_evidence.run(self.program)
        rep = result["pages"][0]
        self.assertEqual(rep.suspects, [])
        self.assertEqual(rep.errors, [])
        self.assertEqual(result["unreferenced"], [])

    def test_planted_altered_number_flagged_as_suspect(self):
        self.write_page("altered.md",
                        "# Altered\n\nSources: sources/raw/fleet.txt\n\n"
                        "The fleet counted 43,000 units on 2026-01-15.\n")
        result = check_evidence.run(self.program)
        rep = result["pages"][0]
        self.assertIn("43,000", rep.suspects)

    def test_missing_source_field_is_evidence_error(self):
        self.write_page("nosrc.md", "# No source\n\nA page with 99,999 things.\n")
        result = check_evidence.run(self.program)
        rep = result["pages"][0]
        self.assertTrue(any("no Sources or Raw field" in e for e in rep.errors))

    def test_no_material_capture_not_reported_unreferenced(self):
        (self.program / "INGEST-LOG.md").write_text(
            "## [2026-11-02] ingest | No material: sources/raw/fleet.txt\n",
            encoding="utf-8")
        self.write_page("other.md",
                        "# Other\n\nSources: sources/raw/fleet.txt\n\n"
                        "The fleet counted 42,000 units on 2026-01-15.\n")
        result = check_evidence.run(self.program)
        self.assertEqual(result["unreferenced"], [])
        # And with the page removed, the No material exemption still holds.
        (self.program / "other.md").unlink()
        result2 = check_evidence.run(self.program)
        self.assertEqual(result2["unreferenced"], [])

    def test_malformed_status_block_flagged(self):
        self.write_page("status.md",
                        "# S\n\nSources: sources/raw/fleet.txt\n\n"
                        "The fleet counted 42,000 units on 2026-01-15.\n\n"
                        "> **Status: Outdated**\n")
        result = check_evidence.run(self.program)
        rep = result["pages"][0]
        self.assertTrue(rep.malformed_status)


if __name__ == "__main__":
    unittest.main()
