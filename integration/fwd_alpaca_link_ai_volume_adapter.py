"""v3 port of v2 sleeve fwd_alpaca_link_ai_volume (batch 4).

Strategy: desk3/vendor/sleeves/fwd_alpaca_link_ai_volume.py — byte-identical copy of the v2
sleeve (sha256-pinned by tests/test_port_batch4_blockers.py).
Adapter: the v2 adapter body below, copied with import lines rewritten
to the vendored bridge (desk3/port4_bridge.py) only; logic untouched,
including every Edge enhancement switch/default and gap-audit cure.
Inputs are re-expressed as the INPUTS producer-registry declaration;
evaluate(view, ctx) serves them from the v3 snapshot via
desk3/port4_context.py.
"""
from desk3.port4_context import evaluate_via

INPUTS = ('bars:LINK/USD:4Hour', 'positions')

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from desk3.port4_bridge import CANDIDATES, ET, OldContext
from desk3.port4_bridge import bar_dict_common as bar_dict
from desk3.port4_bridge import epoch_common as _epoch
from desk3.port4_bridge import fetch_bars, held_map, make_old_context
from desk3.port4_bridge import state_common as sleeve_state_from_positions
from desk3.port4_bridge import symbols_for
from desk3.port4_bridge import translate_common as translate_intents

from desk3.port4_context import load_strategy
strat = load_strategy("fwd_alpaca_link_ai_volume")
SLEEVE_ID = "fwd_alpaca_link_ai_volume"
WARMUP_BARS = {"4Hour": 60}
def _evaluate_v2(ctx):
    bars = fetch_bars(ctx, ["LINK/USD"], "4Hour", 300)
    derived = {}
    held = held_map(ctx)
    if "LINK/USD" in held:
        derived["held_qty"] = held["LINK/USD"]
        for p in ctx.positions or []:
            if p["symbol"] == "LINK/USD" and p.get("opened_at"):
                derived["entry_close_at"] = str(p["opened_at"])
    # A quote product is not in the v2 cache; params.extra may carry one.
    # Absent it, decide() returns its QUOTE/BLOCKED outcomes (no intent).
    old = make_old_context(ctx, derived)
    return translate_intents(strat.signal(bars, {}, old), SLEEVE_ID, ctx, held)


def evaluate(view, ctx):
    return evaluate_via(view, ctx, _evaluate_v2)
