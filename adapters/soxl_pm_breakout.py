"""Adapter for soxl_pm_breakout - v3 plumbing only, no strategy math.

Strategy lives in sleeves/soxl_pm_breakout.py (frozen from the
TrendSpider share and the desk's own replication in
research_notes/trendspider-soxl-pmhigh-test-20261103/). This file
re-expresses the v2 context channels in v3 snapshot terms,
following adapters/bta_onebar_qqq.py:

  bars              <- ctx.bars("SOXL", "15Min", 3000) via the bridge
                       (view['bars']['SOXL|15Min']). 3000 bars of the
                       all-session SIP product cover roughly a month:
                       today's premarket segment, today's RTH bars,
                       and the 20-bar RTH volume SMA lookback with
                       wide margin. Until a producer serves that key
                       the sleeve is UNFED by name (see the core's
                       docstring); bars simply arrive empty here.
  positions         -> slice_state qty map
  soxl_state        <- the strategy's plan / entry-count state,
                       persisted in the sleeve's own state file
                       state/<id>/soxl_state.json beside its journal.

Sizing fallback: the live cycle snapshot may carry no 'slice' key
(the dmac F1 lesson, 2026-10-29), so equity falls back to this
sleeve's configured $10,000 slice when no slice is supplied; a
supplied slice still governs.
"""
from __future__ import annotations

import json
import os
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from adapters._bridge import bars_old  # noqa: E402

ET = ZoneInfo("America/New_York")
SLEEVE_ID = "soxl_pm_breakout"
SYMBOLS = ("SOXL",)
SLICE_FALLBACK_USD = 10000.0
_STATE_FILE = "soxl_state.json"
_BARS_N = 3000


def _state_path(ctx):
    jpath = getattr(ctx, "_journal", None)
    if not jpath:
        return None
    return os.path.join(os.path.dirname(os.path.abspath(jpath)), _STATE_FILE)


def _load_state(ctx):
    path = _state_path(ctx)
    if not path or not os.path.exists(path):
        return {"cursor": {}, "intents": {}, "soxl_state": {}}, path, False
    try:
        with open(path) as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise ValueError("state not a dict")
        for k in ("cursor", "intents", "soxl_state"):
            data.setdefault(k, {})
        return data, path, True
    except Exception:
        return {"cursor": {}, "intents": {}, "soxl_state": {}}, path, False


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
    from sleeves import soxl_pm_breakout as strat

    state, state_path, _state_ok = _load_state(ctx)
    params = ctx.params or {}
    pextra = dict(params.get("extra") or {})
    session = ctx.now.astimezone(ET).date().isoformat() \
        if ctx.now.tzinfo else ctx.now.date().isoformat()

    bars = {}
    for sym in SYMBOLS:
        b = bars_old(ctx, sym, "15Min", _BARS_N)
        if b:
            bars[sym] = b

    slice_state = {}
    for p in ctx.positions or []:
        qty = float(p.get("qty") or 0)
        if qty != 0:
            slice_state[p["symbol"]] = qty

    equity = float((ctx.slice or {}).get("capital_usd")
                   or (ctx.slice or {}).get("cash_usd")
                   or SLICE_FALLBACK_USD)
    if params.get("equity"):
        equity = float(params["equity"])

    extra = dict(pextra)
    if "soxl_state" not in pextra:
        extra["soxl_state"] = dict(state.get("soxl_state") or {})
    extra["meta"] = {"last_evaluated_bar_by_symbol": dict(state.get("cursor") or {})}
    if "bar_cursor_ready" not in pextra:
        extra["bar_cursor_ready"] = bool(state_path)

    old_ctx = OldContext(now=ctx.now.timestamp(), session=session,
                         equity=equity, extra=extra)
    sleeve = strat.SoxlPmBreakoutSleeve()
    intents = sleeve.signal(bars, slice_state, old_ctx) or []

    cursor = dict(state.get("cursor") or {})
    for sym, rows in bars.items():
        if rows:
            cursor[sym] = rows[-1]["t"]
    state["cursor"] = cursor
    state["soxl_state"] = sleeve.soxl_state
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
