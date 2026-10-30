"""v3 adapter for free_kraken_link_breakdown: snapshot view -> v2 old-contract signal ->
v3 intent dicts. Faithful port of the muse-desk-v2 adapter; strategy
math lives unedited in desk3/strategies/free_kraken_link_breakdown.py (single import-line
diff vs v2). Producer inputs arrive in the snapshot (view["extra"],
view["kraken_inputs"], view["options_chain"], view["bars"])."""
from desk3.bridge import ViewCtx, build_extra, old_bars, old_context, to_v2_intents

from desk3.strategies.free_kraken_link_breakdown import signal as _signal
SLEEVE_ID = "free_kraken_link_breakdown"
INPUTS = ("bars", "kraken.quote")

def _kraken_extra(c):
    try: return dict((c.kraken_inputs() or {}).get("sleeves") or {})
    except Exception: return {}

def evaluate(view, ctx):
    c = ViewCtx(view, ctx)
    extra = build_extra(c)
    if "sleeve_state_flat" in extra:
        extra["sleeve_state"] = extra["sleeve_state_flat"]
    if "quote" not in extra:
        _q = (_kraken_extra(c).get("free_kraken_link_basis") or {}).get("quote")
        if _q is not None: extra["quote"] = _q
    bars = {"PF_LINKUSD": old_bars(c, "PF_LINKUSD", "4Hour", 500)}
    return to_v2_intents(c, SLEEVE_ID, _signal(bars, {}, old_context(c, extra)))
