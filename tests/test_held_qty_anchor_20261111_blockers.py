"""Firing-line blocker: the port4 bridge's symbol-less held anchors.

Defect (found by the OPERATION FIRING LINE fixture drives,
2026-11-11): desk3/port4_bridge.build_extra synthesized
extra["held_qty"] (and extra["entry_close_at"]) from the FIRST row
of ctx.positions. In v3 those positions are the aggregate broker
book, not the sleeve's own lots, so fwd_coinbase_sma200 read
held_qty = 1.0 from an ALAB row and stamped treatment_action
"hold" for a BTC position it does not hold (fixture drive 4,
live-shaped view; the same stamp is in its live journal). A
symbol-less anchor cannot name whose quantity it is; the cure is
that build_extra never synthesizes one. Sleeves that need a held
quantity derive it from held_map(ctx) for their own symbol (the
fwd_alpaca_link_ai_volume wrapper already did; ada and coinbase
now do the same).
"""
import os
import sys
import unittest
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from desk3.port4_bridge import build_extra  # noqa: E402


def _ctx(positions, extra=None):
    return SimpleNamespace(
        positions=positions,
        params={"extra": extra or {}},
        slice={"cash_usd": 10000.0},
        bars=lambda *a, **k: [],
        _journal=None)


class TestNoSymbolLessHeldAnchor(unittest.TestCase):
    def test_aggregate_positions_yield_no_generic_held_qty(self):
        ctx = _ctx([
            {"symbol": "ALAB", "qty": 1.0, "avg_price": 10.0,
             "opened_at": "2026-11-10T14:00:00+00:00"},
            {"symbol": "BTCUSD", "qty": 0.132675707, "avg_price": 100.0,
             "opened_at": "2026-11-09T14:00:00+00:00"},
        ])
        extra = build_extra(ctx)
        # The symbol-keyed state maps still carry every position.
        self.assertIn("ALAB", extra["sleeve_state_flat"])
        self.assertIn("BTCUSD", extra["sleeve_state_flat"])
        # But no symbol-less anchor may be synthesized from them.
        self.assertNotIn("held_qty", extra)
        self.assertNotIn("entry_close_at", extra)

    def test_explicit_param_held_qty_is_preserved(self):
        ctx = _ctx([], extra={"held_qty": 3.5})
        extra = build_extra(ctx)
        self.assertEqual(extra["held_qty"], 3.5)

    def test_coinbase_claim_falls_back_only_to_symbol_specific_qty(self):
        from desk3.port4_context import load_strategy
        strat = load_strategy("fwd_coinbase_sma200")
        # No BTC-USD flat row and no symbol-specific held_qty: no claim.
        claimed, qty = strat._held_claim(
            {"sleeve_state_flat": {"ALAB": {"qty": 1.0}}})
        self.assertFalse(claimed)
        self.assertIsNone(qty)
        # The wrapper's symbol-specific held_qty (from held_map,
        # BTCUSD row) is claimed through the documented fallback.
        claimed, qty = strat._held_claim(
            {"sleeve_state_flat": {"BTCUSD": {"qty": 0.132675707}},
             "held_qty": 0.132675707})
        self.assertTrue(claimed)
        self.assertEqual(qty, 0.132675707)


if __name__ == "__main__":
    unittest.main()
