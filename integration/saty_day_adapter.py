"""Adapter for saty_day (v3 port of v2 batch 6) -- interface glue only.

Strategy lives, ported faithfully and byte-identical, in sleeves/saty_day.py.
This file only re-shapes the v3 snapshot view into the old signal()
inputs (see port/bridge.py, v2 'old' profile) and old Intents into v3
dicts. Producer inputs arrive via the snapshot: bars / positions /
extra (rule fires, earnings, chains/quotes) -- the v2 params["extra"]
and options-cache channels, re-expressed as registry declarations.
"""
from port.bridge import CANDIDATES, ViewCtx, old_bars, run_old_signal

SLEEVE_ID = "saty_day"
WARMUP_BARS = {'5Min': 1000, '1Min': 100}
INPUTS = ("bars_5min", "bars_1min", "positions", "options_chains", "options_quotes", "session_fills")
BASKET_41 = ['SPY', 'QQQ']

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

def _fills(vctx):
    try: return vctx.session_fills() or []
    except Exception: return []

def evaluate(view, ctx):
    vctx = ViewCtx(view, ctx, SLEEVE_ID)
    extra = {"sleeve_state": _state(vctx),
             "bars_5m_long": {"SPY": old_bars(vctx, "SPY", "5Min", 30000),
                              "QQQ": old_bars(vctx, "QQQ", "5Min", 30000)},
             "bars_1m": {"SPY": old_bars(vctx, "SPY", "1Min", 3000),
                         "QQQ": old_bars(vctx, "QQQ", "1Min", 3000)},
             "session_fills": _fills(vctx)}
    payload = None
    try: payload = vctx.options_chain("SPY")
    except Exception: payload = None
    if isinstance(payload, dict):
        for k in ("chains", "quotes", "fresh_quotes", "latest_quote"):
            if k in payload: extra[k] = payload[k]
    try:
        from port.bridge import serve_options
        _ch, _qu = serve_options(vctx, ["SPY"])
        if _ch: extra.setdefault("chains", _ch)
        if _qu:
            extra.setdefault("quotes", _qu)
            extra.setdefault("fresh_quotes", _qu)
    except Exception:
        pass
    pex = (vctx.params or {}).get("extra") or {}
    if isinstance(pex, dict):
        for k, v in pex.items(): extra[k] = v
    return run_old_signal(vctx, "sleeves.saty_day", {}, extra)

