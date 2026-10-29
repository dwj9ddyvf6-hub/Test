"""Adapter for przm_fade_edges - v3 plumbing only, no strategy math.

Strategy lives in sleeves/przm_fade_edges.py (PRZM-RECREATION-SPEC-2026-10-29,
frozen). Channels:
  bars   <- ctx.bars("SPY", "1Min", 4000) via the bridge (warm SPY
            1-minute SIP product; one session plus grading history
            is all the engine reads).
  chain  <- ctx.options_chain("SPY") rows via the bridge
            (desk3.producers options_chain: delta-only rows today,
            feed=indicative carries no greeks/OI), normalized by
            serve_options into extra["przm_chain"]. Gamma levels
            therefore come back None live and the sleeve runs its
            named WAITING_NO_GAMMA_LEVELS state (parked in config
            for the same reason). Nothing here fabricates gamma.
  state  <- przm_fade_state persisted in state/<id>/przm_fade_state.json beside
            the sleeve journal (cursor + call ledger round-trip).
"""
from __future__ import annotations

import json
import os
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from adapters._bridge import bars_old, serve_options  # noqa: E402

ET = ZoneInfo("America/New_York")
SLEEVE_ID = "przm_fade_edges"
_STATE_FILE = "przm_fade_state.json"
_BARS_N = 4000


def _state_path(ctx):
    jpath = getattr(ctx, "_journal", None)
    if not jpath:
        return None
    return os.path.join(os.path.dirname(os.path.abspath(jpath)), _STATE_FILE)


def _load_state(ctx):
    path = _state_path(ctx)
    if not path or not os.path.exists(path):
        return {"cursor": {}, "intents": {}, "przm_fade_state": {}}, path, False
    try:
        with open(path) as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise ValueError("state not a dict")
        for k in ("cursor", "intents", "przm_fade_state"):
            data.setdefault(k, {})
        return data, path, True
    except Exception:
        return {"cursor": {}, "intents": {}, "przm_fade_state": {}}, path, False


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
    from sleeves import przm_fade_edges as strat

    state, state_path, _ok = _load_state(ctx)
    params = ctx.params or {}
    pextra = dict(params.get("extra") or {})
    session = ctx.now.astimezone(ET).date().isoformat() \
        if ctx.now.tzinfo else ctx.now.date().isoformat()

    bars = {}
    b = bars_old(ctx, "SPY", "1Min", _BARS_N)
    if b:
        bars["SPY"] = b

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
    if "przm_chain" not in pextra:
        chains = serve_options(ctx, ["SPY"])[0]
        rows = chains.get("SPY") or []
        if rows:
            extra["przm_chain"] = rows
    if "przm_fade_state" not in pextra:
        extra["przm_fade_state"] = dict(state.get("przm_fade_state") or {})
    extra["meta"] = {"last_evaluated_bar_by_symbol": dict(state.get("cursor") or {})}
    if "bar_cursor_ready" not in pextra:
        extra["bar_cursor_ready"] = bool(state_path)

    old_ctx = OldContext(now=ctx.now.timestamp(), session=session,
                         equity=equity, extra=extra)
    sleeve = strat.PrzmFadeEdgesSleeve()
    intents = sleeve.signal(bars, slice_state, old_ctx) or []

    cursor = dict(state.get("cursor") or {})
    for sym, rows in bars.items():
        if rows:
            cursor[sym] = rows[-1]["t"]
    state["cursor"] = cursor
    state["przm_fade_state"] = sleeve.przm_fade_state
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
