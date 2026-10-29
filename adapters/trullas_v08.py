"""Adapter for trullas_v08 (S8: pyramiding on strength) — v3 plumbing only, no strategy math.
Variant of trullas_divergence per TRULLAS-VARIANTS-SPEC-2026-10-29.

Strategy lives in sleeves/trullas_divergence.py (PRIMARY ARM of
TRULLAS-SPEC-2026-10-25 v1.0, frozen). This file re-expresses the v2
context channels in v3 snapshot terms, following adapters/bb_rsi_divergence.py:

  bars              <- ctx.bars("QQQ", "1Min", 4000) via the bridge
                       (view['bars']['QQQ|1Min'], served by desk3/warm.py
                       WarmBars: QQQ 1Min, 10 days, Alpaca SIP)
  positions         -> slice_state qty map
  trullas_state     <- the strategy's pending-setup / plan / day-counter
                       state, persisted in the sleeve's own state file
                       state/<id>/trullas_state.json beside its journal
                       (cursor meta.last_evaluated_bar persisted there too;
                       bar_cursor_ready only when that file round-trips)
  session_orders /  <- recorded emitted intents + journal fills, scoped
  session_fills        to the session (params["extra"] overrides win)

Contexts without a journal (direct unit drives) get cursor_ready=False
unless params say otherwise — entries then fail closed, as designed.
"""
from __future__ import annotations

import json
import os
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from adapters._bridge import bars_old, epoch_old  # noqa: E402

ET = ZoneInfo("America/New_York")
SLEEVE_ID = "trullas_v08"
_STATE_FILE = "trullas_state.json"


def _state_path(ctx):
    jpath = getattr(ctx, "_journal", None)
    if not jpath:
        return None
    return os.path.join(os.path.dirname(os.path.abspath(jpath)), _STATE_FILE)


def _load_state(ctx):
    path = _state_path(ctx)
    if not path or not os.path.exists(path):
        return {"cursor": {}, "plans": {}, "intents": {}, "trullas_state": {}}, path, False
    try:
        with open(path) as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise ValueError("state not a dict")
        for k in ("cursor", "plans", "intents", "trullas_state"):
            data.setdefault(k, {})
        return data, path, True
    except Exception:
        return {"cursor": {}, "plans": {}, "intents": {}, "trullas_state": {}}, path, False


def _save_state(path, data):
    if not path:
        return False
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        json.dump(data, open(tmp, "w"), sort_keys=True)
        os.replace(tmp, path)
        return True
    except Exception:
        return False


def evaluate(ctx):
    from core.sleeve import Context as OldContext
    from sleeves import trullas_v08 as strat

    state, state_path, _state_ok = _load_state(ctx)
    params = ctx.params or {}
    pextra = dict(params.get("extra") or {})
    session = ctx.now.astimezone(ET).date().isoformat() \
        if ctx.now.tzinfo else ctx.now.date().isoformat()

    bars = {}
    b = bars_old(ctx, "QQQ", "1Min", 4000)
    if b:
        bars["QQQ"] = b

    slice_state = {}
    for p in ctx.positions or []:
        qty = float(p.get("qty") or 0)
        if qty != 0:
            slice_state[p["symbol"]] = qty

    equity = float((ctx.slice or {}).get("capital_usd")
                   or (ctx.slice or {}).get("cash_usd") or 0.0)
    if params.get("equity"):
        equity = float(params["equity"])

    extra = dict(pextra)
    if "trullas_state" not in pextra:
        extra["trullas_state"] = dict(state.get("trullas_state") or {})
    extra["meta"] = {"last_evaluated_bar_by_symbol": dict(state.get("cursor") or {})}
    if "bar_cursor_ready" not in pextra:
        extra["bar_cursor_ready"] = bool(state_path)

    old_ctx = OldContext(now=ctx.now.timestamp(), session=session,
                         equity=equity, extra=extra)
    sleeve = strat.TrullasDivergenceSleeve()
    intents = sleeve.signal(bars, slice_state, old_ctx) or []

    # persist cursor, strategy state, plans, emitted-intent records
    cursor = dict(state.get("cursor") or {})
    for sym, rows in bars.items():
        if rows:
            cursor[sym] = rows[-1]["t"]
    state["cursor"] = cursor
    state["trullas_state"] = sleeve.trullas_state
    plan = (sleeve.trullas_state or {}).get("plan")
    if plan:
        state.setdefault("plans", {})["QQQ"] = {
            "stop_px": plan.get("stop"), "target_px": plan.get("tp2"),
            "tp1_px": plan.get("tp1"), "entry_px": plan.get("entry"),
            "direction": plan.get("direction"), "session": session}
    stamp = ctx.now.strftime("%Y%m%dT%H%M%S")
    out = []
    for i, it in enumerate(intents, 1):
        iid = f"{SLEEVE_ID}-{stamp}-{i}"
        qty = it.qty if it.qty is not None else it.qty_hint
        d = {"intent_id": iid,
             "kind": "entry" if it.kind == "enter" else "exit",
             "symbol": it.symbol, "side": it.side, "qty": qty,
             "order_type": "limit" if it.limit_price else "market",
             "limit_price": float(it.limit_price) if it.limit_price else None,
             "stop_price": float(it.stop) if it.stop else None,
             "target": float(it.target) if it.target else None,
             "exit_rules": [{"kind": r.kind, "value": r.value}
                            for r in (it.exit_rules or ())],
             "reason": (it.reason or SLEEVE_ID)[:500],
             "time_in_force": "day"}
        if it.position_intent:
            d["position_intent"] = it.position_intent
        if it.price_hint:
            d["price_hint"] = it.price_hint
        out.append(d)
        state.setdefault("intents", {})[iid] = {
            "symbol": it.symbol, "position_intent": it.position_intent,
            "qty": qty, "session": session, "kind": d["kind"]}
    _save_state(state_path, state)
    try:
        ctx.log("adapter_eval", sleeve=SLEEVE_ID, intents=len(out),
                last_evaluation=sleeve.last_evaluation)
    except Exception:
        pass
    return out
