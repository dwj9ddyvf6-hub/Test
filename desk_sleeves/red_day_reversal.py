"""Adapter for red_day_reversal (v3 port of v2 batch 6) -- interface glue only.

Strategy lives, ported faithfully and byte-identical, in sleeves/red_day_reversal.py.
This file only re-shapes the v3 snapshot view into the old signal()
inputs (see port/bridge.py, v2 'old' profile) and old Intents into v3
dicts. Producer inputs arrive via the snapshot: bars / positions /
extra (rule fires, earnings, chains/quotes) -- the v2 params["extra"]
and options-cache channels, re-expressed as registry declarations.
"""
from port.bridge import CANDIDATES, ViewCtx, old_bars, run_old_signal
from desk3.enhance18 import filter_entries

SLEEVE_ID = "red_day_reversal"
WARMUP_BARS = {'1Day': 202}
INPUTS = ("bars_1day", "positions")
BASKET_41 = ['AEHR', 'NBIS', 'SKYQ', 'SHAZ', 'LITE', 'SOXL', 'WYFI', 'CRML', 'AAOI', 'WDC', 'VELO', 'ANF', 'SATL', 'ASPI', 'IREN', 'AG', 'AXTI', 'LASR', 'ARQQ', 'OUST', 'ALAB', 'CRDO', 'FCEL', 'HIVE', 'POET', 'SNDK', 'TEM', 'CORZ', 'HUT', 'TSEM', 'ARM', 'KEEL', 'FFIV', 'MU', 'CLS', 'TE', 'TTMI', 'CVNA', 'VRT', 'OKLO', 'USAR']

def _state(vctx):
    state = {}
    for p in vctx.positions or []:
        pos = dict(p)
        if pos.get("avg_price") is not None:
            pos.setdefault("entry_px", pos.get("avg_price"))
            pos.setdefault("entry_premium", pos.get("avg_price"))
        if pos.get("opened_at"):
            pos.setdefault("entry_date", str(pos["opened_at"])[:10])
            pos.setdefault("entry_time", pos["opened_at"])
        state[pos["symbol"]] = {"position": pos if float(pos.get("qty") or 0) != 0 else None}
    return state

def _symbols(vctx):
    syms = list(BASKET_41) + [s for s in CANDIDATES if s not in BASKET_41]
    for s in (vctx.params or {}).get("universe") or []:
        if s not in syms: syms.append(s)
    for p in vctx.positions or []:
        if p["symbol"] not in syms: syms.append(p["symbol"])
    ex = (vctx.params or {}).get("extra") or {}
    for key in ("rule_fires", "rule_fires_1h", "chains", "sleeve_state"):
        d = ex.get(key) or {}
        if isinstance(d, dict):
            for s in d:
                if s not in syms: syms.append(s)
    return syms

def _bars(vctx, tf, n):
    out = {}
    for sym in _symbols(vctx):
        b = old_bars(vctx, sym, tf, n)
        if b: out[sym] = b
    return out

def evaluate(view, ctx):
    vctx = ViewCtx(view, ctx, SLEEVE_ID)
    bars = _bars(vctx, "1Day", 400)
    return filter_entries("red_day_reversal", run_old_signal(vctx, "sleeves.red_day_reversal", bars, {"sleeve_state": _state(vctx)}), view)

