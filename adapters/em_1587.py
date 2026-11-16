"""Adapter for em_1587 — interface glue ONLY (DESIGN §4).

Translates the v2 ctx (local bar cache, own positions, slice) into the
ported strategy's native interface signal(bars, slice_state, Context)
from core.sleeve, and translates its Intent objects into v2 §4c intent
dicts. No strategy math, thresholds, sizing, stops or exits live here;
those are verbatim in sleeves/em_1587.py.
Extra producer inputs the old desk supplied via context.extra (chains,
quotes, scan rows, funding prints, ...) arrive via ctx.params["extra"]
in v2 and are passed through untouched.
"""
import importlib
from datetime import datetime, timezone

SLEEVE_ID = "em_1587"
WARMUP_BARS = {"5Min": 78}
_SYMBOLS = ["SPY", "QQQ"]
_TFS = ["5Min"]
_NBARS = 5000
_ENTER_SIDE = "buy"
_EXIT_SIDE = "sell"
_ENTER_PI = None
_EXIT_PI = None
_KIND = "em1587"

_strat = importlib.import_module("sleeves.em_1587")


def _epoch(t):
    return datetime.fromisoformat(str(t).replace("Z", "+00:00")).timestamp()


def _bar_dicts(ctx, sym):
    for tf in _TFS:
        bars = ctx.bars(sym, tf, _NBARS)
        if bars:
            return [{"t": _epoch(b.t), "o": b.o, "h": b.h, "l": b.l,
                     "c": b.c, "v": b.v} for b in bars]
    return []


def _derived_state(ctx):
    state = {}
    for p in ctx.positions or []:
        state[p["symbol"]] = {"position": {
            "entry_px": p.get("avg_price"), "qty": p.get("qty"),
            "entry_date": str(p.get("opened_at") or "")[:10] or None,
        }}
    return state


def evaluate(ctx):
    from core.sleeve import Context as OldContext
    params = ctx.params or {}
    extra = dict(params.get("extra") or {})
    stamp = ctx.now.strftime("%Y%m%dT%H%M%S")
    if _KIND == "monitor_basis":
        ctx.log("monitor_status", **_strat.basis_status(extra))
        return []
    if _KIND == "monitor_enj":
        ctx.log("monitor_status", **_strat.enj_status(extra.get("book") or {}, ctx.now.isoformat()))
        return []
    symbols = list(params.get("symbols") or extra.get("symbols") or _SYMBOLS)
    for src in (extra.get("chains") or {}, extra.get("sleeve_state") or {}):
        for s in src:
            if s not in symbols:
                symbols.append(s)
    if extra.get("universe"):
        for s in extra["universe"]:
            if s not in symbols:
                symbols.append(s)
    bars = {}
    if _KIND == "em1587":
        extra.setdefault("bars_5m_long", {s: _bar_dicts(ctx, s) for s in ("SPY", "QQQ")})
        # GAP-CURE: warmed SPY chain/VIX bars/quotes/session fills existed
        # in cache+journal but the adapter never served them -> NO_TRADE_DAY.
        try:
            from adapters._bridge import serve_options, session_fills_of, latest_quotes_of
            _ch, _qu = serve_options(ctx, ["SPY"])
            if _ch: extra.setdefault("chains", _ch)
            if _qu:
                extra.setdefault("quotes", _qu)
                extra.setdefault("fresh_quotes", {k: {"bp": v.get("bid"), "ap": v.get("ask"), "t": ctx.now.isoformat()} for k, v in _qu.items() if v.get("bid") and v.get("ask")})
            _fills = session_fills_of(ctx)
            if _fills is not None: extra.setdefault("session_fills", _fills)
        except Exception:
            pass
        try:
            _vb = ctx.bars("VIX", "1Day", 500) or []
            if _vb: extra.setdefault("vix_series", [(str(b.t)[:10], float(b.c)) for b in _vb])
        except Exception:
            pass
    elif _KIND == "free_etf":
        bars = {}
    elif _KIND == "kraken":
        for s in symbols:
            rows = _bar_dicts(ctx, s)
            if rows:
                bars[s] = rows
        if "sleeve_state" not in extra:
            st = {}
            for p in ctx.positions or []:
                st[p["symbol"]] = {"qty": p.get("qty"),
                                    "entry_due_at": p.get("opened_at")}
            if st:
                extra["sleeve_state"] = st
    else:
        for s in symbols:
            rows = _bar_dicts(ctx, s)
            if rows:
                bars[s] = rows
    if "sleeve_state" not in extra:
        derived = _derived_state(ctx)
        if derived:
            extra["sleeve_state"] = derived
    slice_state = {p["symbol"]: p.get("qty") for p in (ctx.positions or [])}
    old_ctx = OldContext(now=ctx.now.timestamp(), session=ctx.now.date().isoformat(),
                         equity=float((ctx.slice or {}).get("capital_usd") or 0.0),
                         extra=extra)
    intents = _strat.signal(bars, slice_state, old_ctx) or []
    out = []
    for i, it in enumerate(intents):
        kind = "entry" if it.kind == "enter" else "exit"
        qty = it.qty if getattr(it, "qty", None) is not None else it.qty_hint
        qty = int(qty) if float(qty) == int(float(qty)) else float(qty)
        side = getattr(it, "side", None) or (_ENTER_SIDE if kind == "entry" else _EXIT_SIDE)
        d = {"intent_id": f"{SLEEVE_ID}-{stamp}-{i+1}", "kind": kind,
              "symbol": it.symbol, "side": side, "qty": qty,
              "order_type": "limit" if getattr(it, "limit_price", None) else "market",
              "limit_price": float(it.limit_price) if getattr(it, "limit_price", None) else None,
              "stop_price": float(it.stop) if getattr(it, "stop", None) else None,
              "reason": it.reason or SLEEVE_ID, "time_in_force": "day"}
        pi = getattr(it, "position_intent", None) or (_ENTER_PI if kind == "entry" else _EXIT_PI)
        if pi:
            d["position_intent"] = pi
        if getattr(it, "price_hint", None):
            d["price_hint"] = float(it.price_hint)
        _occ_m = None
        try:
            import re as _re2
            _occ_m = _re2.search(r"occ=([A-Z]{1,6}\d{6}[CP]\d{8})", it.reason or "")
        except Exception:
            _occ_m = None
        if _occ_m:
            # GAP-CURE: sleeve encodes its option contract as occ= in the
            # reason (translate_old precedent); without this the intent
            # traded the UNDERLYING shares instead of the option.
            d["symbol"] = _occ_m.group(1)
            if not pi:
                d["position_intent"] = "buy_to_open" if kind == "entry" else "sell_to_close"
                d["side"] = "buy" if kind == "entry" else "sell"
            _ask_m = None
            try:
                _ask_m = _re2.search(r"ask=([0-9]+(?:\.[0-9]+)?)", it.reason or "")
            except Exception:
                _ask_m = None
            if _ask_m and kind == "entry":
                d["order_type"] = "limit"; d["limit_price"] = round(float(_ask_m.group(1)), 2)
        if getattr(it, "legs", None):
            d["legs"] = [dict(x) for x in it.legs]
        if getattr(it, "package_id", None):
            d["package_id"] = it.package_id
        out.append(d)
    return out
