"""EC-B16 segmented-ledger fixture blockers (2026-11-11, FIX-ALL WAVE).

The D09 precondition: a memory-bounded migration path demonstrated
on a fixture before any re-attempt against the live monolith
(femto-lean state/ledger_sidecar.jsonl, 888 MB). desk3/
ledger_segments.py is that path: it streams the source line by line
(constant memory per line), writes fixed-row-count segments, and its
verification proves the segments' concatenation is byte-identical to
the source. Cutover is NOT landed; the fixture proof is what these
tests pin, graded at the Fri 2026-11-13 night inspection.

Fail direction: a segmentation that reorders, drops, or alters a
single byte fails the round-trip hash test.
"""

import hashlib
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from desk3 import ledger_segments  # noqa: E402


def sidecar_row(i):
    # Faithful shape to the live sidecar: a hash-chained state row.
    return json.dumps(
        {
            "base_hash": "sha256:%064x" % i,
            "base_state": [{"kind": "outcome", "payload": {"episode": i}}],
        },
        sort_keys=True,
    )


class TestLedgerSegments(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.src = os.path.join(self.tmp, "ledger_sidecar.jsonl")
        self.out = os.path.join(self.tmp, "segments")
        with open(self.src, "w", encoding="utf-8") as fh:
            for i in range(250):
                fh.write(sidecar_row(i) + "\n")

    def test_segmentation_round_trips_byte_identical(self):
        manifest = ledger_segments.segment_file(
            self.src, self.out, rows_per_segment=100
        )
        self.assertEqual(manifest["total_rows"], 250)
        self.assertEqual(len(manifest["segments"]), 3)
        with open(self.src, "rb") as fh:
            self.assertEqual(
                manifest["source_sha256"], hashlib.sha256(fh.read()).hexdigest()
            )
        result = ledger_segments.verify_segments(self.out)
        self.assertTrue(result["ok"], result["problems"])
        self.assertEqual(result["total_rows"], 250)

    def test_row_order_is_preserved_across_segments(self):
        ledger_segments.segment_file(self.src, self.out, rows_per_segment=100)
        seen = []
        for name in sorted(os.listdir(self.out)):
            if name.startswith("segment-"):
                with open(os.path.join(self.out, name), encoding="utf-8") as fh:
                    for line in fh:
                        seen.append(json.loads(line)["base_state"][0]["payload"]["episode"])
        self.assertEqual(seen, list(range(250)))

    def test_tampered_segment_fails_verify(self):
        ledger_segments.segment_file(self.src, self.out, rows_per_segment=100)
        seg = os.path.join(self.out, "segment-000002.jsonl")
        with open(seg, "ab") as fh:
            fh.write(b"{}\n")
        result = ledger_segments.verify_segments(self.out)
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
