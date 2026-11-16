"""Adapter for spx_premium (batch 7) -- interface glue only (DESIGN S4).

Strategy lives, ported faithfully and unedited, in sleeves/spx_premium.py.
This file only re-shapes v2 cache/positions into the old signal()
inputs (see adapters/_old_bridge.py) and old Intents into v2 dicts.
"""
from adapters._old_bridge import first_bars, old_bars, run_old_persisted

SLEEVE_ID = "spx_premium"
WARMUP_BARS = {'1Week': 20}

def _options_extra(ctx):
    chain = ctx.options_chain("XSP") or ctx.options_chain("SPY") or {}
    # W-1 cure: traded_dates = sessions with SPY 1Hour bars (the sleeve's own
    # definition); the hardcoded [] made entries unreachable (market_closed).
    from runtime.options_warm import traded_dates_from_bars
    try:
        traded = traded_dates_from_bars(ctx.bars("SPY", "1Hour", 100000))
    except Exception:
        traded = []
    extra = {"weekly_bars": first_bars(ctx, "SPY", ["1Week"], 60), "traded_dates": traded}
    if isinstance(chain, dict):
        if chain.get("chains"):
            extra["chains"] = chain["chains"]
        if chain.get("quotes"):
            extra["quotes"] = chain["quotes"]
    return extra

def evaluate(ctx):
    bars = {"XSP": first_bars(ctx, "XSP", ["1Day"], 60),
            "SPY": first_bars(ctx, "SPY", ["1Day"], 60)}
    return run_old_persisted(ctx, "sleeves.spx_premium", bars, _options_extra(ctx), "spx_premium_enh_journal")
