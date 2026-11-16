"""ASTER-INTAKE-1 blockers: ASTER-BUILD-MAP.md coverage + archive verdict.

The map must cover every genuinely-new catalog row exactly once, its
batch list must partition the 155 rows, and the staged-archive hash
verdict recorded in the map must reproduce while the archive exists.
"""
import csv
import hashlib
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAP = ROOT / "ASTER-BUILD-MAP.md"
TSV = pathlib.Path.home() / "workspace/user/files/sleeve-catalog.tsv"
ARCHIVE = pathlib.Path.home() / "workspace/.scratch-ausar-archive/handoff-20261024"


def new_rows():
    rows = list(csv.DictReader(TSV.open(), delimiter="\t"))
    return [r for r in rows if not r["family"].startswith("midna_")]


class TestAsterBuildMap(unittest.TestCase):
    def setUp(self):
        self.text = MAP.read_text()

    def test_155_rows_present(self):
        self.assertEqual(len(new_rows()), 155)
        for r in new_rows():
            key = f"{r['family']}::{r['exact_variant']}"
            self.assertIn(f"`{key}`", self.text, key)

    def test_row_table_count(self):
        table_rows = re.findall(r"^\| \d+ \| Paper book", self.text, re.M)
        self.assertEqual(len(table_rows), 155)

    def test_batches_partition(self):
        batch_lines = re.findall(r"- \*\*Batch \d+ \(\d+\):\*\* (.+)", self.text)
        keys = []
        for line in batch_lines:
            keys += re.findall(r"`([^`]+)`", line)
        self.assertEqual(len(keys), 155)
        self.assertEqual(
            sorted(keys),
            sorted(f"{r['family']}::{r['exact_variant']}" for r in new_rows()),
        )

    def test_slice_convention_recorded(self):
        self.assertIn("$10,000", self.text)
        self.assertIn("entry_cap_equity", self.text)
        self.assertIn("gross_target", self.text)

    def test_saty_missing_named(self):
        self.assertIn("saty_research", self.text)
        self.assertIn("SOURCE ABSENT", self.text)
        self.assertIn("TSV-as-spec", self.text)


@unittest.skipUnless(ARCHIVE.exists(), "staged archive not present")
class TestArchiveVerdict(unittest.TestCase):
    def test_r25_204_exact_only_readme_mismatch(self):
        manifest = json.loads((ARCHIVE / "provenance/SOURCE_FILES_R25.json").read_text())
        exact, mismatched = 0, []
        for f in manifest["files"]:
            hit = None
            for root in (ARCHIVE, ARCHIVE / "source", ARCHIVE / "sleeves"):
                cand = root / f["path"]
                if cand.exists():
                    hit = cand
                    break
            if hit is None:
                continue
            digest = hashlib.sha256(hit.read_bytes()).hexdigest()
            if digest == f["sha256"]:
                exact += 1
            else:
                mismatched.append(f["path"])
        self.assertEqual(exact, 204)
        self.assertEqual(mismatched, ["README.md"])


if __name__ == "__main__":
    unittest.main()
