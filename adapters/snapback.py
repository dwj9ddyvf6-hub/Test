"""Adapter for snapback (batch 7) -- interface glue only (DESIGN S4).

Strategy lives, ported faithfully and unedited, in sleeves/snapback.py.
This file only re-shapes v2 cache/positions into the old signal()
inputs (see adapters/_old_bridge.py) and old Intents into v2 dicts.
"""
from adapters._old_bridge import first_bars, old_bars, run_old_persisted

SLEEVE_ID = "snapback"
WARMUP_BARS = {'1Day': 260, '1Week': 60}

WATCHLIST = ("SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "AMD", "TSLA",
             "AMZN", "META", "NFLX", "GOOGL")

def _symbols(ctx):
    syms = list((ctx.params or {}).get("universe") or WATCHLIST)
    for p in ctx.positions or []:
        if p["symbol"] not in syms:
            syms.append(p["symbol"])
    return syms

def evaluate(ctx):
    syms = _symbols(ctx)
    bars = {s: first_bars(ctx, s, ["1Day"], 400) for s in syms}
    weekly = {s: first_bars(ctx, s, ["1Week"], 120) for s in syms}
    return run_old_persisted(ctx, "sleeves.snapback", bars, {"weekly": weekly}, "snapback_enh_journal")
