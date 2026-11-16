"""TENSOR FIRE ENVELOPE blockers (CURE-3 envelope layer, 2026-11-11).

Diagnosis (TENSOR-FIRE-PATH.md Sections 3.1-3.3): the variant families
(batch13/14/15) discard every served fire at their first field gates
because the swing rows name their own facts differently from the
consumers: the price sits under "entry" (consumers read "price"), the
session date under "bar_date" (consumers read "date" / "signal_end"),
and the fire time under the epoch "t" (consumers read "fired_at" /
"ts"). The FEATURE fields (markers, depth60, ret60, vol20, dv20,
atr_ratio, native_close) are a separate, canonical-mapping question
and are NOT derived here — the joint lane (Claude's canonical field
answer; GrokBot md2 post grokbot-inbox:2026-11-11-tensor-fire-md2)
confirmed the cure for those is a real feature producer with a
verified mapping, not guessed fields.

Cure pinned here: at bundle build time each fire gains, ONLY from its
own values, price := entry, date := bar_date, signal_end := bar_date,
ts := t, fired_at := ISO-8601 of t. Every original key is preserved
verbatim. A fire lacking a source value gains nothing for that key —
nothing is fabricated.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

T = 1762900000  # 2025-11-11T17:46:40Z; only its ISO rendering matters
SIGNAL = {"symbol": "ARM", "decision": "TRADE", "confidence": 0.9,
          "phenotype": "swing", "regime": "trend", "bar_date": "2026-11-11",
          "t": T, "entry": 250.5, "stop": 240.0, "target": 300.0}
BARE = {"symbol": "MSFT", "decision": "TRADE"}


class FakeProducer:
    def extra_for(self, sleeve_id, ctx):
        if sleeve_id == "tensor_swing":
            return {"tensor_signals": [dict(SIGNAL), dict(BARE)],
                    "tensor_exit": {}}
        return {"tensor_signals": [], "qqq_day_return": 0.0,
                "day_returns": {}, "nyse_holidays": []}


class TestTensorFireEnvelope(unittest.TestCase):
    def _root(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        return tmp

    def test_fire_gains_envelope_fields_from_its_own_values(self):
        from desk3.tensor_warm import build_bundle
        tmp = self._root()
        payload = build_bundle(tmp, session="2026-11-11",
                               producer=FakeProducer())
        fire = payload["fires"][0]
        self.assertEqual(fire["price"], 250.5)
        self.assertEqual(fire["date"], "2026-11-11")
        self.assertEqual(fire["signal_end"], "2026-11-11")
        self.assertEqual(fire["ts"], T)
        self.assertEqual(fire["fired_at"],
                         datetime.fromtimestamp(T, timezone.utc).isoformat())
        # originals preserved verbatim
        for k, v in SIGNAL.items():
            self.assertEqual(fire[k], v)

    def test_fire_without_source_values_gains_nothing(self):
        from desk3.tensor_warm import build_bundle
        tmp = self._root()
        payload = build_bundle(tmp, session="2026-11-11",
                               producer=FakeProducer())
        bare = payload["fires"][1]
        self.assertEqual(bare, BARE)
        for k in ("price", "date", "signal_end", "ts", "fired_at",
                  "markers", "depth60", "ret60", "vol20", "dv20",
                  "atr_ratio", "native_close"):
            self.assertNotIn(k, bare)


if __name__ == "__main__":
    unittest.main()
