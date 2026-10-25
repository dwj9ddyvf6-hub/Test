"""Adapter (glue only): v2 ctx -> old signal(bars, slice_state, context). Strategy in sleeves/momentum.py is a faithful copy."""
from adapters._common import *

from sleeves import momentum as strat
SLEEVE_ID = "momentum"
WARMUP_BARS = {"1Day": 127}
def evaluate(ctx):
    syms = symbols_for(ctx)
    bars = fetch_bars(ctx, syms, "1Day", 300)
    derived = {"sleeve_state": sleeve_state_from_positions(ctx),
               "now_hm": (ctx.now.astimezone(ET).hour, ctx.now.astimezone(ET).minute)}
    vix = fetch_bars(ctx, ["VIX", "^VIX"], "1Day", 10)
    vrows = vix.get("VIX") or vix.get("^VIX") or []
    if len(vrows) >= 2:
        from datetime import datetime, timezone
        asof = datetime.fromtimestamp(float(vrows[-1]["t"]), tz=timezone.utc).date().isoformat()
        derived["vix"] = (float(vrows[-1]["c"]), float(vrows[-2]["c"]), asof, "cache")
    old = make_old_context(ctx, derived)
    return translate_intents(strat.signal(bars, {}, old), SLEEVE_ID, ctx, held_map(ctx))
