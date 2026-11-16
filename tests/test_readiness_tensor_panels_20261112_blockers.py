"""READINESS-TENSOR-PANELS-20261112 blockers.

Defect: desk3.aster_batch1._tensor_panels admitted ANY list-valued
top-level entry of the Tensor bundle as a sleeve panel. The bundle
carries "tensor_universe": a list of symbol STRINGS. Those strings
became panel "rows"; _eval_tensor then called .get on a string and
died with AttributeError ('str' object has no attribute 'get'),
which its (TypeError, ValueError, KeyError) guard does not catch.
aster_tensor_h1_recovery and aster_tensor_w1_recovery errored every
cycle once the bundle carried the key, and the sleeve-surface census
join failed downstream (errored sleeves count as needs_attention,
not ready). A panel is a list of bar/feature DICTS; anything else is
not a panel.

Fail direction: proven on the preserved pre-cure copy
(~/workspace/.gatecure-20261112/pre/readiness-tensor-panels/) and on
a worktree at the pre-cure HEAD: every test below fails there (the
panel map carries the string list; evaluate raises AttributeError).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from desk3.aster_batch1 import _tensor_panels, _eval_tensor, SPECS


def _bundle():
    """Bundle-shaped dict: one real per-symbol features panel plus
    the non-panel top-level keys the live bundle carries."""
    feats = [{"close": 12.0, "atr14": 0.5, "dollar_volume20": 5_000_000,
              "volume": 1000.0, "obv_slope5": 3.0, "total_votes": 7,
              "balance": b, "votes": {"stoch": 1, "aroon": 1, "di": 1,
                                      "obv": 1, "squeeze": 1, "pivot": 1,
                                      "wave": w},
              "frame": "1wk", "bar_index": 300 + i}
             for i, (b, w) in enumerate(((0, 1), (1, 1), (2, 1), (3, 1)))]
    return {
        "session": "2026-11-12",
        "generated_at": "2026-11-12T20:00:00+00:00",
        "tensor_universe": ["AAOI", "AEHR", "AG", "ALAB", "ANF"],
        "fires": [{"symbol": "AG", "signal": "x"}],
        "TESTSYM": {"features": feats, "frame": "1wk"},
    }


class TestTensorPanelsStringList(unittest.TestCase):
    def test_string_list_key_is_not_a_panel(self):
        panels = _tensor_panels({"tensor": _bundle()}, "1wk")
        self.assertNotIn("tensor_universe", panels)
        self.assertNotIn("fires", panels)
        self.assertNotIn("session", panels)

    def test_every_panel_row_is_a_dict(self):
        panels = _tensor_panels({"tensor": _bundle()}, "1wk")
        self.assertIn("TESTSYM", panels)
        for sym, rows in panels.items():
            for row in rows:
                self.assertIsInstance(row, dict,
                                      f"panel {sym} carries a non-dict row")

    def test_evaluate_survives_bundle_with_string_list(self):
        view = {"tensor": _bundle(), "positions": [],
                "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
                "bars": {}}
        ctx = {"now": "2026-11-12T15:00:00+00:00", "state_dir": None}
        from datetime import datetime, timezone
        now = datetime(2026, 11, 12, 15, 0, tzinfo=timezone.utc)
        out = _eval_tensor("aster_tensor_w1_recovery",
                           SPECS["aster_tensor_w1_recovery"], view, ctx, now)
        self.assertIsInstance(out, list)


if __name__ == "__main__":
    unittest.main()
