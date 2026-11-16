"""ALT-DATA producer blockers (2026-11-12, Firing Line follow-up).

Defect: s_cl_qm_small declares input alt_data and reads exactly one
field, (alt_data[sym] or {}).get("mcap_band") == "small"; no producer
anywhere in the estate emitted alt_data, so the sleeve sat UNFED on a
product whose source data (EDGAR shares outstanding x warm close) was
already computed daily by the rule-fires build as log_mcap.

Cure: desk3/producers3.py gains AltDataProducer (batch-3 wiring,
fail-closed over the validated state/ingest/alt_data.json drop) and
the research-lane builder bands log_mcap on the estate's own table
(desk3/q07_engine.py CAP_BANDS_USD: mi < $300M, sm $300M-$2B named
"small" for this consumer, ml >= $2B).

Fail direction: pre-cure there is no AltDataProducer and no alt_data
row in BATCH3_PRODUCERS, so the import/registration tests error out.
"""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from desk3 import producers3  # noqa: E402

NOW = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)


def _mkroot(doc=None, name="alt_data.json"):
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "state", "ingest"), exist_ok=True)
    if doc is not None:
        with open(os.path.join(root, "state", "ingest", name),
                  "w") as fh:
            json.dump(doc, fh)
    return root


def _doc(rows, gen=NOW):
    return {"generated_at": gen.isoformat(), "alt_data": rows}


class TestAltDataProducer(unittest.TestCase):

    def test_registered_in_batch3_with_alt_data_output(self):
        rows = {name: (factory, outputs)
                for name, factory, outputs, _sla
                in producers3.BATCH3_PRODUCERS}
        self.assertIn("alt_data", rows)
        factory, outputs = rows["alt_data"]
        self.assertIs(factory, producers3.AltDataProducer)
        self.assertEqual(tuple(outputs), ("alt_data",))

    def test_consumer_declares_alt_data(self):
        from laz_sleeves import s_cl_qm_small
        self.assertIn("alt_data", s_cl_qm_small.INPUTS)

    def test_band_table_matches_estate_cap_bands(self):
        # The builder bands on these thresholds; if the estate table
        # moves, this pin fails and the builder mapping is revisited.
        from desk3.q07_engine import CAP_BANDS_USD
        self.assertEqual(CAP_BANDS_USD["mi"], (0.0, 300_000_000.0))
        self.assertEqual(CAP_BANDS_USD["sm"],
                         (300_000_000.0, 2_000_000_000.0))
        self.assertEqual(CAP_BANDS_USD["ml"][0], 2_000_000_000.0)

    def test_serves_valid_rows_narrowed_to_mcap_band(self):
        root = _mkroot(_doc({
            "AAA": {"mcap_band": "small", "mcap_usd": 9.5e8},
            "BBB": {"mcap_band": "midlarge"},
            "CCC": {"mcap_band": "micro"},
        }))
        out = producers3.AltDataProducer(root)({"now": NOW})
        self.assertEqual(out, {"alt_data": {
            "AAA": {"mcap_band": "small"},
            "BBB": {"mcap_band": "midlarge"},
            "CCC": {"mcap_band": "micro"},
        }})

    def test_malformed_rows_dropped_never_repaired(self):
        root = _mkroot(_doc({
            "AAA": {"mcap_band": "small"},
            "BAD1": {"mcap_band": "huge"},
            "BAD2": {"no_band": True},
            "BAD3": "small",
            "BAD4": None,
        }))
        out = producers3.AltDataProducer(root)({"now": NOW})
        self.assertEqual(out,
                         {"alt_data": {"AAA": {"mcap_band": "small"}}})

    def test_missing_drop_fails_closed(self):
        root = _mkroot(None)
        self.assertEqual(producers3.AltDataProducer(root)(
            {"now": NOW}), {})

    def test_stale_drop_fails_closed(self):
        old = NOW - timedelta(days=9)
        root = _mkroot(_doc({"AAA": {"mcap_band": "small"}}, gen=old))
        self.assertEqual(producers3.AltDataProducer(root)(
            {"now": NOW}), {})

    def test_band_vocabulary_is_the_estate_three(self):
        self.assertEqual(producers3.AltDataProducer.BANDS,
                         ("micro", "small", "midlarge"))


if __name__ == "__main__":
    unittest.main()
