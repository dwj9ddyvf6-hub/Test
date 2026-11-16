"""FEED80-MIDNA-20261114 regression blockers.

Defect: midna_signals / hedge_signal were declared as outputs of
the Tensor bundle producer (desk3/laz_batch7.py) but no producer
ever served them — the bundle carries no such fields — so
s_mn_hourly, s_mn_nostop and s_mn_hedge sat UNFED on a declaration
that was never true in code.

Cure: desk3.producers3.MidnaSignalsProducer serves both keys from
state/ingest/midna_signals.json (a drop computed from the desk's
own swing machinery, provenance stamped in the drop), registered
in BATCH3_PRODUCERS; the laz_batch7 declaration now names the real
serving route.

Fail-first: pre-cure, MidnaSignalsProducer does not exist
(ImportError), BATCH3_PRODUCERS has no midna_signals row, and the
laz_batch7 declaration still assigns the keys to tensor_bundle.
"""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

NOW = datetime(2026, 11, 14, 20, 0, tzinfo=timezone.utc)


def _root_with_drop(doc):
    td = tempfile.mkdtemp()
    os.makedirs(os.path.join(td, "state", "ingest"))
    with open(os.path.join(td, "state", "ingest",
                           "midna_signals.json"), "w") as fh:
        json.dump(doc, fh)
    return td


def _doc(**kw):
    doc = {"generated_at": NOW.isoformat(),
           "signals": {"AAPL": {"signal": True},
                       "MSFT": {"signal": False}},
           "hedge_signal": True}
    doc.update(kw)
    return doc


class TestMidnaProducer(unittest.TestCase):
    def test_serves_both_keys(self):
        from desk3.producers3 import MidnaSignalsProducer
        out = MidnaSignalsProducer(_root_with_drop(_doc()))(
            {"now": NOW})
        self.assertEqual(out["midna_signals"],
                         {"AAPL": {"signal": True},
                          "MSFT": {"signal": False}})
        self.assertIs(out["hedge_signal"], True)

    def test_malformed_rows_dropped_never_repaired(self):
        from desk3.producers3 import MidnaSignalsProducer
        doc = _doc(signals={"AAPL": {"signal": "yes"},
                            "MSFT": {"signal": True},
                            "ZZZ": {"nope": 1}},
                   hedge_signal="yes")
        out = MidnaSignalsProducer(_root_with_drop(doc))({"now": NOW})
        self.assertEqual(out["midna_signals"],
                         {"MSFT": {"signal": True}})
        self.assertNotIn("hedge_signal", out)

    def test_stale_drop_fails_closed(self):
        from desk3.producers3 import MidnaSignalsProducer
        old = (NOW - timedelta(days=3)).isoformat()
        out = MidnaSignalsProducer(
            _root_with_drop(_doc(generated_at=old)))({"now": NOW})
        self.assertEqual(out, {})

    def test_registered_in_batch3(self):
        from desk3.producers3 import (BATCH3_PRODUCERS,
                                      MidnaSignalsProducer)
        rows = {r[0]: r for r in BATCH3_PRODUCERS}
        self.assertIn("midna_signals", rows)
        self.assertIs(rows["midna_signals"][1], MidnaSignalsProducer)
        self.assertEqual(tuple(rows["midna_signals"][2]),
                         ("midna_signals", "hedge_signal"))

    def test_batch7_declaration_names_real_route(self):
        from desk3 import laz_batch7
        self.assertEqual(laz_batch7.PRODUCERS["tensor_bundle"][0],
                         ("tensor_fires",))
        self.assertEqual(laz_batch7.PRODUCERS["midna_signals"][0],
                         ("midna_signals", "hedge_signal"))


if __name__ == "__main__":
    unittest.main()
