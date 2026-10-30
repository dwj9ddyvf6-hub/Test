"""v3 adapter for free_kraken_enj_spot: faithful port of the v2 adapter
(interface glue only). Strategy math in desk3/strategies/free_kraken_enj_spot.py.
Producer inputs: view["extra"]["book"] (fixture/params channel, precedence)
else view["kraken_inputs"]["sleeves"][id]["book"]; bars from the snapshot."""
import importlib
from datetime import datetime

from desk3.bridge import ViewCtx

SLEEVE_ID = "free_kraken_enj_spot"
INPUTS = ("kraken.book", "bars")
_SYMBOLS = ["ENJUSD"]
_TFS = ["240Min"]
_NBARS = 10
_ENTER_SIDE = "buy"
_EXIT_SIDE = "sell"
_strat = importlib.import_module("desk3.strategies.free_kraken_enj_spot")


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
            "entry_date": str(p.get("opened_at") or "")[:10] or None}}
    return state


def evaluate(view, ctx):
    from desk3.contract import Context as OldContext
    c = ViewCtx(view, ctx)
    params = c.params or {}
    extra = dict(params.get("extra") or {})
    if "book" not in extra:
        try:
            data = c.kraken_inputs() or {}
            _k = dict((data.get("sleeves") or {}).get(SLEEVE_ID) or {}).get("book")
        except Exception:
            _k = None
        if _k is not None:
            extra["book"] = _k
    stamp = c.now.strftime("%Y%m%dT%H%M%S")
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
    for s in symbols:
        rows = _bar_dicts(c, s)
        if rows:
            bars[s] = rows
    if "sleeve_state" not in extra:
        st = {}
        for p in c.positions or []:
            st[p["symbol"]] = {"qty": p.get("qty"),
                               "entry_due_at": p.get("opened_at")}
        if st:
            extra["sleeve_state"] = st
    if "sleeve_state" not in extra:
        derived = _derived_state(c)
        if derived:
            extra["sleeve_state"] = derived
    slice_state = {p["symbol"]: p.get("qty") for p in (c.positions or [])}
    old_ctx = OldContext(now=c.now.timestamp(), session=c.now.date().isoformat(),
                         equity=float((c.slice or {}).get("capital_usd") or 0.0),
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
        pi = getattr(it, "position_intent", None)
        if pi:
            d["position_intent"] = pi
        if getattr(it, "price_hint", None):
            d["price_hint"] = float(it.price_hint)
        if getattr(it, "legs", None):
            d["legs"] = [dict(x) for x in it.legs]
        if getattr(it, "package_id", None):
            d["package_id"] = it.package_id
        out.append(d)
    from desk3.enhance15 import filter_entries
    return filter_entries(SLEEVE_ID, out, view, extra)
