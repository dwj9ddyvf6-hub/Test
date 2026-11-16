#!/usr/bin/env python3
"""Tests for research_capture.py (ADOPT A1)."""
import hashlib, json, os, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import research_capture


class ResearchCaptureTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.program = root / "prog"
        self.program.mkdir()
        self.src = root / "note.txt"
        self.src.write_text("alpha content 12345\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_capture_and_manifest_hash_matches_sha256sum(self):
        r = research_capture.capture(self.src, self.program, captured="2026-11-02")
        self.assertEqual(r["status"], "captured")
        captured = self.program / r["raw_path"]
        independent = hashlib.sha256(captured.read_bytes()).hexdigest()
        manifest = json.loads((self.program / "sources" / "MANIFEST.json").read_text())
        self.assertEqual(len(manifest["entries"]), 1)
        entry = manifest["entries"][0]
        self.assertEqual(entry["sha256"], independent)
        self.assertEqual(entry["byte_size"], captured.stat().st_size)
        self.assertEqual(entry["original_filename"], "note.txt")
        self.assertEqual(entry["captured"], "2026-11-02")

    def test_duplicate_capture_is_noop(self):
        research_capture.capture(self.src, self.program, captured="2026-11-02")
        r2 = research_capture.capture(self.src, self.program, captured="2026-11-02")
        self.assertEqual(r2["status"], "already_captured")
        manifest = json.loads((self.program / "sources" / "MANIFEST.json").read_text())
        self.assertEqual(len(manifest["entries"]), 1)
        self.assertEqual(len(list((self.program / "sources" / "raw").iterdir())), 1)

    def test_changed_content_creates_second_capture_first_byte_identical(self):
        r1 = research_capture.capture(self.src, self.program, captured="2026-11-02")
        first_bytes = (self.program / r1["raw_path"]).read_bytes()
        self.src.write_text("beta changed content 67890\n", encoding="utf-8")
        r2 = research_capture.capture(self.src, self.program, captured="2026-11-02")
        self.assertEqual(r2["status"], "captured")
        self.assertNotEqual(r1["raw_path"], r2["raw_path"])
        self.assertEqual((self.program / r1["raw_path"]).read_bytes(), first_bytes)
        manifest = json.loads((self.program / "sources" / "MANIFEST.json").read_text())
        self.assertEqual(len(manifest["entries"]), 2)


if __name__ == "__main__":
    unittest.main()
