"""Adapter for free_kraken_ada_basis_varspot — interface glue ONLY.

Translates the v2 ctx into the variation strategy's native
interface signal(bars, slice_state, Context) from core.sleeve and
its Intent objects into v2 intent dicts. No strategy math lives
here (sleeves/free_kraken_ada_basis_varspot.py).

Producer inputs, from the snapshot only:
- extra["basis"]: the PARENT sleeve's kraken basis entry
  (kraken_inputs sleeves[free_kraken_ada_basis]) — the parent's
  own perp-vs-spot series, the variation's unchanged signal.
- extra["spot_reference"]: {price, bar_t} from the newest bar of
  the served ADA/USD spot tape (ctx.bars ADA/USD 240Min).
- sleeve_state: from ctx.positions, keyed by symbol (ADA/USD).
"""
import importlib
from datetime import datetime, timezone

SLEEVE_ID = "free_kraken_ada_basis_varspot"
PARENT_ID = "free_kraken_ada_basis"
WARMUP_BARS = {}
_SYMBOLS = ["ADA/USD"]
_TFS = ["240Min"]
_NBARS = 400
_ENTER_SIDE = "buy"
_EXIT_SIDE = "sell"
_ENTER_PI = None
_EXIT_PI = None

_strat = importlib.import_module("sleeves.free_kraken_ada_basis_varspot")


def _epoch(t):
    return datetime.fromisoformat(str(t).replace("Z", "+00:00")).timestamp()


def _bar_dicts(ctx, sym):
    for tf in _TFS:
        bars = ctx.bars(sym, tf, _NBARS)
        if bars:
            return [{"t": _epoch(b.t), "o": b.o, "h": b.h, "l": b.l,
                     "c": b.c, "v": b.v} for b in bars]
    return []


def evaluate(ctx):
    from core.sleeve import Context as OldContext
    params = ctx.params or {}
    extra = dict(params.get("extra") or {})
    stamp = ctx.now.strftime("%Y%m%dT%H%M%S")
    spot_rows = _bar_dicts(ctx, "ADA/USD")
    if spot_rows:
        last = spot_rows[-1]
        extra["spot_reference"] = {
            "price": last["c"],
            "bar_t": datetime.fromtimestamp(last["t"],
                                            tz=timezone.utc).isoformat()}
    if "basis" not in extra:
        try:
            _kd = ctx.kraken_inputs() or {}
            _b = ((_kd.get("sleeves") or {}).get(PARENT_ID) or {}).get("basis")
            if _b is not None:
                extra["basis"] = _b
        except Exception:
            pass
    if "sleeve_state" not in extra:
        st = {}
        for p in ctx.positions or []:
            st[p["symbol"]] = {"qty": p.get("qty"),
                               "entry_due_at": p.get("opened_at")}
        if st:
            extra["sleeve_state"] = st
    slice_state = {p["symbol"]: p.get("qty") for p in (ctx.positions or [])}
    old_ctx = OldContext(now=ctx.now.timestamp(),
                         session=ctx.now.date().isoformat(),
                         equity=float((ctx.slice or {}).get("capital_usd")
                                      or 0.0),
                         extra=extra)
    intents = _strat.signal({}, slice_state, old_ctx) or []
    out = []
    for i, it in enumerate(intents):
        kind = "entry" if it.kind == "enter" else "exit"
        qty = it.qty if getattr(it, "qty", None) is not None else it.qty_hint
        qty = int(qty) if float(qty) == int(float(qty)) else float(qty)
        side = getattr(it, "side", None) or (_ENTER_SIDE if kind == "entry"
                                             else _EXIT_SIDE)
        d = {"intent_id": f"{SLEEVE_ID}-{stamp}-{i+1}", "kind": kind,
             "symbol": it.symbol, "side": side, "qty": qty,
             "order_type": "limit" if getattr(it, "limit_price", None)
             else "market",
             "limit_price": float(it.limit_price)
             if getattr(it, "limit_price", None) else None,
             "stop_price": float(it.stop) if getattr(it, "stop", None)
             else None,
             "reason": it.reason or SLEEVE_ID, "time_in_force": "day"}
        pi = getattr(it, "position_intent", None) or (
            _ENTER_PI if kind == "entry" else _EXIT_PI)
        if pi:
            d["position_intent"] = pi
        if getattr(it, "price_hint", None):
            d["price_hint"] = float(it.price_hint)
        out.append(d)
    return out
