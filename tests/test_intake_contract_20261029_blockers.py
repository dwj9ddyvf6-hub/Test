"""Blockers for the desk intake contracts (2026-10-29): anti fixture
source rejection and the evidence CSV intake contract, adopted from
the Codex terminal deep pass (DEEP-PASS.md 3.1 items 4 and 5) as
desk3/intake.py, the desk research loaders' standing CSV contract.

Fail direction: desk3/intake.py did not exist before this adoption,
so every test errors pre-fix and passes post-fix.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from desk3 import intake  # noqa: E402


class TestAntiFixture(unittest.TestCase):
    def test_fixture_labels_refused(self):
        for label in ("synthetic", "SYNTHETIC SAMPLE", "fixture",
                      "Fixture_v2", "sample"):
            self.assertTrue(intake.is_fixture_source(label), label)

    def test_real_labels_pass(self):
        for label in ("exchange-tape", "Alpaca SIP", "SEC EDGAR",
                      "sampleson & co", None, ""):
            self.assertFalse(intake.is_fixture_source(label), label)

    def test_guarded_reader_refuses_fixture_row(self):
        with self.assertRaises(intake.IntakeError) as ctx:
            intake.read_csv_dicts_guarded(
                "date,close,source\n2026-10-29,10,synthetic\n")
        self.assertIn("row 2", str(ctx.exception))

    def test_guarded_reader_clean_and_caps(self):
        rows = intake.read_csv_dicts_guarded("date,close\n2026-10-29,10\n")
        self.assertEqual(rows, [{"date": "2026-10-29", "close": "10"}])
        with self.assertRaises(intake.IntakeError):
            intake.read_csv_dicts_guarded(b"x" * (intake.MAX_BYTES + 1))


class TestEvidenceContract(unittest.TestCase):
    def test_good_row_three_clocks_absent_stays_none(self):
        out = intake.parse_evidence_csv(
            "ObservedAt,PublicAt,ReceivedAt,Entity,Source,Metric,Value\n"
            "2026-10-29T14:00:00Z,2026-10-29T14:01:00Z,"
            "2026-10-29T14:02:00Z,SPY,tape,close,601.25\n")
        self.assertEqual(out["accepted_count"], 1)
        self.assertIsNone(out["accepted"][0]["Unit"])

    def test_unknown_column_refuses_whole_file(self):
        with self.assertRaises(intake.IntakeError):
            intake.parse_evidence_csv(
                "ObservedAt,Entity,Source,Metric,Value,Bogus\n"
                "2026-10-29T14:00:00Z,SPY,tape,close,1,x\n")

    def test_per_row_reasons_with_lines(self):
        out = intake.parse_evidence_csv(
            "ObservedAt,Entity,Source,Metric,Value\n"
            "2026-10-29T14:00:00Z,SPY,tape,close,1\n"
            "2026-10-29T14:00:00Z,SPY,fixture,close,1\n"
            "bad-time,SPY,tape,close,1\n")
        self.assertEqual(out["accepted_count"], 1)
        reasons = {r["line"]: r["reason"] for r in out["rejected"]}
        self.assertEqual(reasons[3], "fixture_source")
        self.assertEqual(reasons[4], "invalid_timestamp:ObservedAt")


if __name__ == "__main__":
    unittest.main()
