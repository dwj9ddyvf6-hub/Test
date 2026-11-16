"""Adapter for free_kraken_ada_breakdown — interface glue ONLY (DESIGN §4).

Translates the v2 ctx (local bar cache, own positions, slice) into the
ported strategy's native interface signal(bars, slice_state, Context)
from core.sleeve, and translates its Intent objects into v2 §4c intent
dicts. No strategy math, thresholds, sizing, stops or exits live here;
those are verbatim in sleeves/free_kraken_ada_breakdown.py.
Extra producer inputs the old desk supplied via context.extra (chains,
quotes, scan rows, funding prints, ...) arrive via ctx.params["extra"]
in v2 and are passed through untouched.
"""
import importlib
from datetime import datetime, timezone

SLEEVE_ID = "free_kraken_ada_breakdown"
WARMUP_BARS = {"240Min": 22}
_SYMBOLS = ["PF_ADAUSD"]
_TFS = ["240Min"]
_NBARS = 400
_ENTER_SIDE = "sell"
_EXIT_SIDE = "buy"
_ENTER_PI = None
_EXIT_PI = None
_KIND = "kraken"

_strat = importlib.import_module("sleeves.free_kraken_ada_breakdown")


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
    elif _KIND == "free_etf":
        bars = {}
    elif _KIND == "kraken":
        if "quote" not in extra:
            try:
                _kd = ctx.kraken_inputs() or {}
                _q = ((_kd.get("sleeves") or {}).get("free_kraken_ada_basis") or {}).get("quote")
                if _q is not None: extra["quote"] = _q
            except Exception:
                pass
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
        if getattr(it, "legs", None):
            d["legs"] = [dict(x) for x in it.legs]
        if getattr(it, "package_id", None):
            d["package_id"] = it.package_id
        out.append(d)
    return out
