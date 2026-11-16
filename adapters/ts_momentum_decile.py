"""Adapter for ts_momentum_decile (batch 7) -- interface glue only (DESIGN S4).

Strategy lives, ported faithfully and unedited, in sleeves/ts_momentum_decile.py.
This file only re-shapes v2 cache/positions into the old signal()
inputs (see adapters/_old_bridge.py) and old Intents into v2 dicts.
"""
from adapters._old_bridge import first_bars, old_bars, run_old_persisted

SLEEVE_ID = "ts_momentum_decile"
WARMUP_BARS = {'1Day': 253}

def _symbols(ctx):
    from sleeves.ts_momentum_decile import SECTOR_MAP
    syms = list(SECTOR_MAP)
    for p in ctx.positions or []:
        if p["symbol"] not in syms:
            syms.append(p["symbol"])
    return syms

def evaluate(ctx):
    bars = {s: first_bars(ctx, s, ["1Day"], 600) for s in _symbols(ctx)}
    return run_old_persisted(ctx, "sleeves.ts_momentum_decile", bars, {}, None)
