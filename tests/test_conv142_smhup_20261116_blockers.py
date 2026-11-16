"""CONV142-SMHUP-20261116 blockers: the smhUp definition record.

Pre-cure state (GOING-LIVE-2026-11-15, CONV-142 BLOCKED): the desk
consumed the rule_fires_1h field "smhUp" — rule_1h_cyan_raw passes
a fire only when smhUp == 1 — without holding the external Node 1H
scorer's definition of it anywhere in the repo, so the leg could
not be reproduced, audited or re-implemented. Cure pinned here:
the exact definition, hunted to the scorer's own source
(alpaca-swing-desk/dcg_scorer/dcg_rule_1h.mjs, vendored engine.mjs)
and proven by verbatim reproduction on every archived drop row
carrying the field, is recorded at the desk producer that ingests
the drop (desk3/producers3.py, RuleFiresProducer) — the producer
only, because the consuming sleeve file is sha256-pinned
byte-identical to its v2 source (test_port_batch6_blockers) and
must not carry the note. The reproduction itself runs the
scorer's engine, which is not vendored into this repo (a copy here
would be a second source of truth); per the desk's blocker
convention these pins are source-assertions over the record's
load-bearing elements, plus the behavioral pin that the producer
ingests the field untouched and the sleeve's guard is unchanged.
The 2026-11-16 reproduction evidence (778 archived rows, all six
field-present dates, regime discrimination around them) is stated
in the producer record and in BUGLOG_2026-11-16.md
(CONV142-SMHUP-20261116).
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

ROOT = os.path.join(os.path.dirname(__file__), "..")


def _read(rel):
    with open(os.path.join(ROOT, rel)) as fh:
        return fh.read()


class TestSmhUpDefinitionRecord(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.producer = _read("desk3/producers3.py")
        cls.sleeve = _read("sleeves/rule_1h_cyan_raw.py")

    def test_record_present_at_producer(self):
        self.assertIn("CONV142-SMHUP-20261116", self.producer)
        self.assertIn("dcg_rule_1h.mjs", self.producer)

    def test_definition_load_bearing_elements(self):
        # The definition, element by element: SMH weekly UT Bot
        # regime == 1 on the fire's calendar date; weekly
        # aggregation by the engine's weekly(); PRODUCTION markers;
        # the lastIndex week-span mapping; the two null gates.
        for token in ("UT Bot regime equals 1",
                      "weekly()",
                      "markers(PRODUCTION)",
                      "ut.regime",
                      "lastIndex[w-1]+1 .. lastIndex[w]",
                      "300 valid SMH daily bars",
                      "10 weekly bars",
                      "null when the date is unmapped"):
            self.assertIn(token, self.producer, token)

    def test_verification_evidence_recorded(self):
        for token in ("778 rows", "2026-11-06", "2026-11-09..13",
                      "2026-09-21..10-09", "2026-10-12"):
            self.assertIn(token, self.producer, token)

    def test_sleeve_guard_unchanged(self):
        # The consumption rule the definition serves: a fire passes
        # the smhUp leg only at exactly 1.
        self.assertIn('f.get("smhUp") != 1', self.sleeve)


class TestProducerIngestsFieldUntouched(unittest.TestCase):
    def test_rule_fires_1h_passes_through_verbatim(self):
        from desk3.producers3 import RuleFiresProducer
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        ingest = os.path.join(root, "state", "ingest")
        os.makedirs(ingest)
        fires_1h = {"AEHR": [{"t": "2026-11-13T14:00:00+00:00",
                              "rangeatr": 3.45, "wtgap": -3.1942,
                              "smhUp": 0},
                             {"t": "2026-09-25T14:00:00+00:00",
                              "rangeatr": 2.5, "wtgap": 7.5,
                              "smhUp": 1},
                             {"t": "2026-11-14T14:00:00+00:00",
                              "rangeatr": 2.5, "wtgap": 7.5,
                              "smhUp": None}]}
        doc = {"generated_at": "2026-11-16T12:00:00+00:00",
               "rule_fires": {}, "rule_fires_1h": fires_1h,
               "log_mcap": {}, "trading_days": ["2026-11-16"]}
        with open(os.path.join(ingest, "rule_fires.json"), "w") as fh:
            json.dump(doc, fh)
        out = RuleFiresProducer(root)(
            {"now": datetime(2026, 11, 16, 12, 5,
                             tzinfo=timezone.utc)})
        self.assertEqual(out["rule_fires_1h"], fires_1h)


if __name__ == "__main__":
    unittest.main()
