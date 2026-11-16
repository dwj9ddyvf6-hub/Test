"""DURABLE-FILL-LEDGER blockers (2026-11-11, FIX-ALL WAVE).

The defect: fills live only as dispatcher journal events across four
journal generations; there is no durable fill record of its own.
First increment: desk3/fill_ledger.py builds the durable form
(immutable segments + manifest, per the 2026-10-23 ledger standard)
from journal generations, deduping re-journaled fills on their
natural key. Nothing live consumes the ledger yet; the register row
closes when a live cycle consumes it with reconcile imported_rows
staying 0 against it.

Fail direction: a builder that keeps duplicates, or writes segments
whose bytes change between rebuilds, fails the idempotence and
dedupe tests below.
"""

import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from desk3 import fill_ledger  # noqa: E402


def fill(intent, order, ts, sleeve="a", qty=1.0):
    return {
        "event": "fill",
        "intent_id": intent,
        "broker_order_id": order,
        "ts": ts,
        "sleeve": sleeve,
        "symbol": "SPY",
        "side": "buy",
        "qty": qty,
        "price": 100.0,
    }


def write_journal(path, rows):
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


class TestFillLedger(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gen1 = os.path.join(self.tmp, "dispatcher.jsonl.1")
        self.gen2 = os.path.join(self.tmp, "dispatcher.jsonl")
        self.out = os.path.join(self.tmp, "ledger")
        f1 = fill("i-1", "o-1", "2026-11-10T14:00:00Z")
        f2 = fill("i-2", "o-2", "2026-11-10T14:01:00Z", sleeve="b", qty=2.0)
        f3 = fill("i-3", "o-3", "2026-11-10T14:02:00Z", sleeve="a", qty=3.0)
        write_journal(
            self.gen1,
            [f1, f2, {"event": "order_submitted", "intent_id": "i-9"}],
        )
        # gen2 re-journals f2 (the heal path) and adds f3.
        write_journal(self.gen2, [f2, f3])

    def test_build_dedupes_and_verifies(self):
        manifest = fill_ledger.build_ledger(
            [self.gen1, self.gen2], self.out, rows_per_segment=2
        )
        self.assertEqual(manifest["total_fills"], 3)
        self.assertEqual(manifest["duplicates_dropped"], 1)
        self.assertEqual(len(manifest["segments"]), 2)
        result = fill_ledger.verify_ledger(self.out)
        self.assertTrue(result["ok"], result["problems"])
        self.assertEqual(result["total_fills"], 3)

    def test_rebuild_is_byte_identical(self):
        first = fill_ledger.build_ledger(
            [self.gen1, self.gen2], self.out, rows_per_segment=2
        )
        second = fill_ledger.build_ledger(
            [self.gen1, self.gen2], self.out, rows_per_segment=2
        )
        self.assertEqual(
            [s["sha256"] for s in first["segments"]],
            [s["sha256"] for s in second["segments"]],
        )

    def test_tamper_is_caught_by_verify(self):
        fill_ledger.build_ledger([self.gen1, self.gen2], self.out)
        seg = os.path.join(self.out, "fills-000001.jsonl")
        with open(seg, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(fill("i-x", "o-x", "2026-11-10T15:00:00Z")) + "\n")
        result = fill_ledger.verify_ledger(self.out)
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
