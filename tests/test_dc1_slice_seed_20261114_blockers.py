"""DC-1 blockers (2026-11-14, desk sweep HUNT-desk-core DC-1, High).

Defect: the READINESS-CYC3 slice seed charged each sleeve's
LIFETIME net journal spend against its slice capital. Net spend
folds in realised P&L and short proceeds, so on the hunt's live
read 25 sleeves seeded cash below zero (every entry rejected
insufficient_slice_bp forever, silently) and 34 seeded above
capital (the BP gate admitting against cash the slice does not
have; extreme: $6,427,962 seeded on a $10,000 slice).

Cure (desk3/cycle.py seed_slices): cash = capital minus OPEN
position cost (journal_open_costs FIFO average x open qty, OCC
lots at premium x 100), floored at 0, capped at capital.

Fail direction: on the pre-cure tree seed_slices does not exist
and the inline seed reproduces both wrong directions; the
direction assertions below are checked against the pre-cure
formula in test_precure_formula_exhibits_both_defects, which
passes on both trees as the defect's documentation, while the
cure tests fail pre-cure (ImportError) and pass cured.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from desk3.cycle import seed_slices
from desk3.reconcile import journal_derived


def _fill(sid, sym, side, qty, px, iid):
    return {"event": "fill", "intent_id": iid, "sleeve": sid,
            "symbol": sym, "side": side, "qty": qty, "price": px,
            "ts": "2026-11-12T15:00:00+00:00"}


def _journal(tmp, rows):
    path = os.path.join(tmp, "dispatcher.jsonl")
    with open(path, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    return path


def _sleeves(*sids_caps):
    return {sid: {"slice_usd": cap} for sid, cap in sids_caps}


class TestDc1SeedDirections(unittest.TestCase):
    def test_bricked_sleeve_is_admitted_against_true_remaining(self):
        # Lifetime spend dwarfs capital (bought 100@100, sold 95@50:
        # net spend 5,250 on a 1,000 slice) but only 5 shares @100
        # remain open: true remaining slice cash is 500.
        tmp = tempfile.mkdtemp()
        path = _journal(tmp, [
            _fill("s1", "TEST", "buy", 100, 100.0, "a"),
            _fill("s1", "TEST", "sell", 95, 50.0, "b")])
        out = seed_slices(_sleeves(("s1", 1000.0)), path)
        self.assertAlmostEqual(out["s1"]["cash_usd"], 500.0)
        self.assertEqual(out["s1"]["positions"]["TEST"]["qty"], 5.0)

    def test_net_short_seed_never_exceeds_capital(self):
        # Short 50@100, nothing covered: net spend is -5,000, so the
        # pre-cure seed was 6,000 on a 1,000 slice. Cured: the open
        # short's cost (5,000) floors the seed at 0, never above cap.
        tmp = tempfile.mkdtemp()
        path = _journal(tmp, [
            _fill("s1", "TEST", "sell", 50, 100.0, "a")])
        out = seed_slices(_sleeves(("s1", 1000.0)), path)
        self.assertLessEqual(out["s1"]["cash_usd"], 1000.0)
        self.assertAlmostEqual(out["s1"]["cash_usd"], 0.0)

    def test_profitable_closed_history_does_not_inflate_seed(self):
        # Bought 10@100, sold 10@300 (realised +2,000): nothing
        # open, seed is exactly capital, not capital + profit.
        tmp = tempfile.mkdtemp()
        path = _journal(tmp, [
            _fill("s1", "TEST", "buy", 10, 100.0, "a"),
            _fill("s1", "TEST", "sell", 10, 300.0, "b")])
        out = seed_slices(_sleeves(("s1", 1000.0)), path)
        self.assertAlmostEqual(out["s1"]["cash_usd"], 1000.0)
        self.assertNotIn("positions", out["s1"])

    def test_open_long_charges_open_cost_only(self):
        tmp = tempfile.mkdtemp()
        path = _journal(tmp, [
            _fill("s1", "TEST", "buy", 8, 100.0, "a")])
        out = seed_slices(_sleeves(("s1", 1000.0)), path)
        self.assertAlmostEqual(out["s1"]["cash_usd"], 200.0)

    def test_occ_open_cost_uses_cash_multiplier(self):
        # 2 long calls @ 2.50 premium commit 2 x 2.50 x 100 = 500.
        tmp = tempfile.mkdtemp()
        path = _journal(tmp, [
            _fill("s1", "SPY261218C00500000", "buy", 2, 2.50, "a")])
        out = seed_slices(_sleeves(("s1", 1000.0)), path)
        self.assertAlmostEqual(out["s1"]["cash_usd"], 500.0)


class TestPreCureFormulaDocumentsDefect(unittest.TestCase):
    def test_precure_formula_exhibits_both_defects(self):
        tmp = tempfile.mkdtemp()
        path = _journal(tmp, [
            _fill("brick", "TEST", "buy", 100, 100.0, "a"),
            _fill("brick", "TEST", "sell", 95, 50.0, "b"),
            _fill("short", "TEST", "sell", 50, 100.0, "c")])
        _pos, spend = journal_derived(path)
        # The pre-cure seed, capital - lifetime net spend:
        self.assertLess(1000.0 - spend["brick"], 0.0)
        self.assertGreater(1000.0 - spend["short"], 1000.0)


if __name__ == "__main__":
    unittest.main()
