"""v3 port of v2 sleeve fwd_alpaca_enj_iu_body (batch 4).

Strategy: desk3/vendor/sleeves/fwd_alpaca_enj_iu_body.py — byte-identical copy of the v2
sleeve (sha256-pinned by tests/test_port_batch4_blockers.py).
Adapter: the v2 adapter body below, copied with import lines rewritten
to the vendored bridge (desk3/port4_bridge.py) only; logic untouched,
including every Edge enhancement switch/default and gap-audit cure.
Inputs are re-expressed as the INPUTS producer-registry declaration;
evaluate(view, ctx) serves them from the v3 snapshot via
desk3/port4_context.py.
"""
from desk3.port4_context import evaluate_via

INPUTS = ('bars:ENJ/USD:1Min',)

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
strat = load_strategy("fwd_alpaca_enj_iu_body")
SLEEVE_ID = "fwd_alpaca_enj_iu_body"
WARMUP_BARS = {}
def _evaluate_v2(ctx):
    # Evaluation + journaling path (WIRING §6): the sleeve is a blocked
    # monitor (ENJ/USD unlisted at Alpaca, provider-proven — see
    # proof/enj-provider-2026-10-24.json); journal its status record on
    # every evaluation, then translate its (always empty) signal.
    ctx.log("monitor_status", **strat.status())
    bars = fetch_bars(ctx, ["ENJ/USD"], "1Min", 10)
    old = make_old_context(ctx)
    return translate_intents(strat.signal(bars, {}, old), SLEEVE_ID, ctx, held_map(ctx))


def evaluate(view, ctx):
    return evaluate_via(view, ctx, _evaluate_v2)
