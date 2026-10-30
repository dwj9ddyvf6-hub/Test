"""v3 port of v2 sleeve fwd_alpaca_ada_rsi2 (batch 4).

Strategy: desk3/vendor/sleeves/fwd_alpaca_ada_rsi2.py — byte-identical copy of the v2
sleeve (sha256-pinned by tests/test_port_batch4_blockers.py).
Adapter: the v2 adapter body below, copied with import lines rewritten
to the vendored bridge (desk3/port4_bridge.py) only; logic untouched,
including every Edge enhancement switch/default and gap-audit cure.
Inputs are re-expressed as the INPUTS producer-registry declaration;
evaluate(view, ctx) serves them from the v3 snapshot via
desk3/port4_context.py.
"""
from desk3.port4_context import evaluate_via

INPUTS = ('bars:ADA/USD:1Hour', 'positions')

from desk3.port4_bridge import build_extra
from desk3.port4_bridge import bars_v2 as old_bars
from desk3.port4_bridge import old_context_v2 as old_context
from desk3.port4_bridge import to_v2_intents
from desk3.port4_context import load_strategy
_signal = load_strategy("fwd_alpaca_ada_rsi2").signal

SLEEVE_ID = "fwd_alpaca_ada_rsi2"
WARMUP_BARS = {"1Hour": 200}

def _evaluate_v2(ctx):
    extra = build_extra(ctx)
    bars = {"ADA/USD": old_bars(ctx, "ADA/USD", "1Hour", 400)}
    return to_v2_intents(ctx, SLEEVE_ID, _signal(bars, {}, old_context(ctx, extra)))


def evaluate(view, ctx):
    return evaluate_via(view, ctx, _evaluate_v2)
