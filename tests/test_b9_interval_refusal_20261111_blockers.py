"""B9 INTERVAL REFUSAL SURFACING blockers (CR-2, 2026-11-11;
DIAGNOSIS.md S2).

The defect: the six INTERVAL sleeves (aster_etf_b9.py) refuse
silently. When bars_secondary is absent, evaluate() returns []
with nothing recorded; when the secondary eligible set disagrees
with the primary, select() raises PROVIDER_ELIGIBILITY_DISAGREEMENT
and evaluate() swallows it into the same silent []. The sleeves
read FED in health (bars_secondary has a registered producer,
desk3/producers_g4.py SecondaryBars) yet fourteen sessions
produced no orders and no record of why.

The cure (desk3/aster_etf_b9.py): every refused in-window INTERVAL
evaluation appends an adapter_eval refusal record (reason:
bars_secondary_absent, or the select() verdict verbatim, with the
eligible-set sizes) to the engine's exp-journal channel
(extra["aster_etf_b9_exp_journal"]["records"]). Selection logic,
targets and sizing are untouched; a agreeing secondary still
selects and emits exactly as before (the third test is also the
class's fixture drive: recorded-shape inputs that satisfy the
engine produce intents end to end).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desk3 import aster_etf_b9 as b9  # noqa: E402

SID = "aster_etf_interval1_c098"


def _bars(symbols, days=300, drift=0.001):
    out = {}
    for i, sym in enumerate(symbols):
        rows = []
        px = 100.0 + i
        for d in range(days):
            px *= (1.0 + drift * (1 + (i % 3)))
            rows.append({"t": f"2026-{(d // 28) % 12 + 1:02d}-01",
                         "c": round(px, 4)})
        out[f"{sym}|1Day"] = rows
    return out


def _view(bars, secondary=None):
    v = {"bars": bars, "positions": [], "now": "2026-11-11",
         "slice": {"cash_usd": 10000.0, "capital_usd": 10000.0},
         "extra": {"aster_etf_b9_exp_journal": {"records": []}}}
    if secondary is not None:
        v["bars_secondary"] = secondary
    return v


def _refusals(view):
    recs = view["extra"]["aster_etf_b9_exp_journal"]["records"]
    return [r for r in recs if r.get("event") == "adapter_eval"
            and r.get("refusal")]


class TestIntervalRefusalSurfacing(unittest.TestCase):
    def test_absent_secondary_is_named_not_silent(self):
        v = _view(_bars(b9.UNIVERSE))
        out = b9.evaluate(SID, v, {})
        self.assertEqual(out, [])
        refs = _refusals(v)
        self.assertEqual(len(refs), 1, refs)
        self.assertEqual(refs[0]["reason"], "bars_secondary_absent")
        self.assertEqual(refs[0]["sleeve"], SID)

    def test_disagreement_is_named_not_silent(self):
        # Secondary history for only half the universe: the
        # eligible sets disagree and select() refuses by name.
        v = _view(_bars(b9.UNIVERSE),
                  secondary=_bars(b9.UNIVERSE[:7]))
        out = b9.evaluate(SID, v, {})
        self.assertEqual(out, [])
        refs = _refusals(v)
        self.assertEqual(len(refs), 1, refs)
        self.assertEqual(refs[0]["reason"],
                         "PROVIDER_ELIGIBILITY_DISAGREEMENT")

    def test_agreeing_secondary_selects_and_emits(self):
        bars = _bars(b9.UNIVERSE)
        v = _view(bars, secondary=_bars(b9.UNIVERSE))
        out = b9.evaluate(SID, v, {})
        self.assertTrue(out, "agreeing inputs must emit intents")
        self.assertTrue(all(i["kind"] == "entry" for i in out))
        self.assertEqual(_refusals(v), [])


if __name__ == "__main__":
    unittest.main()
