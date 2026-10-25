"""v3 port of v2 sleeve fwd_coinbase_sma200 (batch 4).

Strategy: desk3/vendor/sleeves/fwd_coinbase_sma200.py — byte-identical copy of the v2
sleeve (sha256-pinned by tests/test_port_batch4_blockers.py).
Adapter: the v2 adapter body below, copied with import lines rewritten
to the vendored bridge (desk3/port4_bridge.py) only; logic untouched,
including every Edge enhancement switch/default and gap-audit cure.
Inputs are re-expressed as the INPUTS producer-registry declaration;
evaluate(view, ctx) serves them from the v3 snapshot via
desk3/port4_context.py.
"""
from desk3.port4_context import evaluate_via

INPUTS = ('bars:BTC-USD:1Day', 'positions', 'journal:self')

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from desk3.port4_bridge import CANDIDATES, ET, OldContext
from desk3.port4_bridge import bar_dict_common as bar_dict
from desk3.port4_bridge import epoch_common as _epoch
from desk3.port4_bridge import fetch_bars, held_map, make_old_context
from desk3.port4_bridge import state_common as sleeve_state_from_positions
from desk3.port4_bridge import symbols_for
from desk3.port4_bridge import translate_common as translate_intents

from datetime import datetime, timezone
from desk3.port4_bridge import build_extra, serve_journal
from desk3.port4_context import load_strategy
strat = load_strategy("fwd_coinbase_sma200")
SLEEVE_ID = "fwd_coinbase_sma200"
WARMUP_BARS = {"1Day": 200}
def _evaluate_v2(ctx):
    bars = fetch_bars(ctx, ["BTC-USD", "BTC/USD"], "1Day", 260)
    raw = bars.get("BTC-USD") or bars.get("BTC/USD") or []
    derived = {}
    if raw:
        today = ctx.now.astimezone(timezone.utc).date().isoformat()
        hist = []
        for b in raw:
            d = datetime.fromtimestamp(float(b["t"]), tz=timezone.utc).date().isoformat()
            if d >= today:
                continue  # decision-day bar is forming, not completed
            hist.append({"date": d, "close": float(b["c"]), "complete": True, "forming": False})
        if hist:
            derived["history"] = hist
            last_close = hist[-1]["close"]
            derived["quote"] = {"as_of": ctx.now.isoformat(), "bid": last_close, "ask": last_close}
    held_extra = build_extra(ctx)
    for k in ("held_qty", "sleeve_state", "sleeve_state_flat"):
        if k in held_extra:
            derived.setdefault(k, held_extra[k])
    served = serve_journal(ctx, "coinbase_sma200_exp_journal")
    if served is not None:
        derived.setdefault("coinbase_sma200_exp_journal", served)
    old = make_old_context(ctx, derived)
    inst = strat.FwdCoinbaseSma200()
    intents = inst.signal({}, {}, old)
    stamp = getattr(inst, "last_evaluation", None) or {}
    if stamp and hasattr(ctx, "log"):
        try:
            ctx.log("last_evaluation", stamp=stamp)
        except Exception:
            pass
        journal = stamp.get("coinbase_sma200_exp_journal")
        if isinstance(journal, dict):
            try:
                ctx.log("coinbase_sma200_exp_journal", journal=journal)
            except Exception:
                pass
    return translate_intents(intents, SLEEVE_ID, ctx, held_map(ctx))


def evaluate(view, ctx):
    return evaluate_via(view, ctx, _evaluate_v2)
