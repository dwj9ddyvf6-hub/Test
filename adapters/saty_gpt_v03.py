"""Adapter for saty_gpt_v03 (batch 7) -- interface glue only (DESIGN S4).

Strategy lives, ported faithfully and unedited, in sleeves/saty_gpt_v03.py.
This file only re-shapes v2 cache/positions into the old signal()
inputs (see adapters/_old_bridge.py) and old Intents into v2 dicts.
"""
from adapters._old_bridge import first_bars, old_bars, run_old_signal, run_old_persisted

SLEEVE_ID = "saty_gpt_v03"
WARMUP_BARS = {'1Day': 1000, '5Min': 1000}

def _frames_extra(ctx):
    spy5 = first_bars(ctx, "SPY", ["5Min"], 6000)
    spy1 = first_bars(ctx, "SPY", ["1Min"], 2000)
    from adapters._bridge import serve_options, session_fills_of, latest_quotes_of
    extra = {"bars_5m_long": {"SPY": spy5}, "bars_1m": {"SPY": spy1},
            "bars_10m": {"SPY": first_bars(ctx, "SPY", ["10Min"], 3000)},
            "bars_1h": {"SPY": first_bars(ctx, "SPY", ["1Hour", "60Min"], 1500)},
            "bars_daily": {"SPY": first_bars(ctx, "SPY", ["1Day"], 1200)},
            # GAP-CURE: hardcoded {} blocked every quote gate; the warmed
            # latest-quote cache + SPY options payload + own-journal
            # session fills are the documented producers.
            "latest_quote": latest_quotes_of(ctx),
            "session_fills": session_fills_of(ctx)}
    _ch, _qu = serve_options(ctx, ["SPY"])
    if _ch: extra["chains"] = _ch
    if _qu:
        extra["quotes"] = _qu
        extra["fresh_quotes"] = _qu
    return extra

def evaluate(ctx):
    bars = {"SPY": first_bars(ctx, "SPY", ["1Day", "5Min"], 6000)}
    return run_old_persisted(ctx, "sleeves.saty_gpt_v03", bars, _frames_extra(ctx), "gpt_v03_journal")
