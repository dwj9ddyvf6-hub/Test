"""Adapter for free_kraken_ada_crowded_varspot — interface glue
ONLY. Translates the v2 ctx into the variation strategy's native
interface and its Intent objects into v2 intent dicts. No strategy
math lives here (sleeves/free_kraken_ada_crowded_varspot.py).

Producer inputs, from the snapshot only:
- the served ADA/USD spot 4h tape (ctx.bars ADA/USD 240Min),
  keyed under the traded symbol ADA/USD — the spot substitution
  for the parent's PF_ADAUSD bars;
- extra["funding_rates"]: the PF_ADAUSD series of the snapshot's
  kraken.funding key — the parent's own funding gate input,
  carried unchanged (a PF-market conditioner, named in the
  strategy docstring, never replaced with a spot proxy);
- the served BTC/USD spot 4h tape (ctx.bars BTC/USD 240Min) —
  the paired relative-value anchor leg's tape (PF-PAIRED-RV-20261116,
  MAKE-IT-WORK Decision C 2026-11-16), served by the same bars
  producer (warm CRYPTO_FETCHES BTC/USD 4Hour). The config row's
  inputs already declare "bars", which covers both tapes. The
  paired leg's wire shape is buy-to-open / sell-to-close, so the
  side defaults below are the paired form's (buy entry, sell
  exit); the strategy's intents also declare their side
  explicitly.
"""
import importlib
from datetime import datetime, timezone

SLEEVE_ID = "free_kraken_ada_crowded_varspot"
PF_INSTRUMENT = "PF_ADAUSD"
WARMUP_BARS = {"240Min": 22}
_SYMBOLS = ["ADA/USD", "BTC/USD"]
_TFS = ["240Min"]
_NBARS = 400
_ENTER_SIDE = "buy"
_EXIT_SIDE = "sell"
_ENTER_PI = None
_EXIT_PI = None

_strat = importlib.import_module("sleeves.free_kraken_ada_crowded_varspot")


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
    if "funding_rates" not in extra:
        view = getattr(ctx, "_view", None) or {}
        fund = view.get("kraken.funding") or {}
        rates = fund.get(PF_INSTRUMENT) if isinstance(fund, dict) else None
        if rates is not None:
            extra["funding_rates"] = rates
    bars = {}
    rows = _bar_dicts(ctx, "ADA/USD")
    if rows:
        bars["ADA/USD"] = rows
    btc_rows = _bar_dicts(ctx, "BTC/USD")
    if btc_rows:
        bars["BTC/USD"] = btc_rows
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
    intents = _strat.signal(bars, slice_state, old_ctx) or []
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
