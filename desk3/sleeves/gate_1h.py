"""v3 port of v2 sleeve gate_1h (batch 4).

Strategy: desk3/vendor/sleeves/gate_1h.py — byte-identical copy of the v2
sleeve (sha256-pinned by tests/test_port_batch4_blockers.py).
Adapter: the v2 adapter body below, copied with import lines rewritten
to the vendored bridge (desk3/port4_bridge.py) only; logic untouched,
including every Edge enhancement switch/default and gap-audit cure.
Inputs are re-expressed as the INPUTS producer-registry declaration;
evaluate(view, ctx) serves them from the v3 snapshot via
desk3/port4_context.py.
"""
from desk3.port4_context import evaluate_via

INPUTS = ('bars:*:1Day', 'bars:*:1Hour', 'positions', 'journal:self')

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
strat = load_strategy("gate_1h")

def _serve_last_event(ctx):
    path = getattr(ctx, "_journal", None)
    if not path: return {}
    try:
        from desk3.vendor.runtime.journal import tail_lines
        out = {}
        for rec in tail_lines(path, 4000):
            if rec.get("event") == "leader_last_event" and rec.get("symbol"):
                out[rec["symbol"]] = rec.get("event_date")
        return out
    except Exception:
        return {}

def _file_last_event(ctx, intents):
    import re as _re
    for it in intents or []:
        if it.get("kind") != "entry": continue
        m = _re.search(r"event (\d{4}-\d{2}-\d{2})", it.get("reason") or "")
        if m:
            try: ctx.log("leader_last_event", symbol=it["symbol"], event_date=m.group(1))
            except Exception: pass
SLEEVE_ID = "gate_1h"
WARMUP_BARS = {"1Day": 252, "1Hour": 22}
def _evaluate_v2(ctx):
    syms = symbols_for(ctx)
    bars = fetch_bars(ctx, syms, "1Day", 300)
    h1 = fetch_bars(ctx, syms, "1Hour", 200)
    state = sleeve_state_from_positions(ctx)
    # GAP-CURE: bars_1h must be the RTH-only grid (13:00-19:00Z starts)
    # the sleeve's hold/de-overlap counts are defined on; the cache
    # holds full extended-hours bars.
    h1 = {s: [b for b in rows if 13 <= datetime.fromtimestamp(float(b["t"]), tz=timezone.utc).hour < 20] for s, rows in h1.items()}
    derived = {"sleeve_state": state, "bars_1h": h1,
               "last_event": _serve_last_event(ctx), "last_entry_bar": {s: (v["position"] or {}).get("entry_bar_t") for s, v in state.items() if v.get("position")}}
    old = make_old_context(ctx, derived)
    out = translate_intents(strat.signal(bars, {}, old), SLEEVE_ID, ctx, held_map(ctx))
    _file_last_event(ctx, out)
    return out


def evaluate(view, ctx):
    return evaluate_via(view, ctx, _evaluate_v2)
