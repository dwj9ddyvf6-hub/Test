"""Adapter for t_cci_corr — v3 plumbing only, no strategy math.

Strategy lives in sleeves/t_cci_corr.py (faithful port of the
reference in quant-research-backup research/cci_correction/).
This file re-expresses the v3 snapshot in the strategy's terms,
following adapters/trullas_divergence.py:

  bars        <- the snapshot's daily rows (view['bars']['SYM|1Day'],
                 Alpaca SIP via desk3/warm.py), every equity symbol
                 the warm product carries = the screening universe
  vix_rows    <- view['bars:VIX:1Day'] (Yahoo ^VIX daily closes,
                 price only — the desk's sanctioned use)
  positions   -> slice_state qty map (broker read-back, own fills)
  cci_state   <- the strategy's position/pending state, persisted
                 in state/<id>/cci_state.json beside its journal
"""
from __future__ import annotations

import json
import os
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

ET = ZoneInfo("America/New_York")
SLEEVE_ID = "t_cci_corr"
_STATE_FILE = "cci_state.json"


def _state_path(ctx):
    jpath = getattr(ctx, "_journal", None)
    if not jpath:
        return None
    return os.path.join(os.path.dirname(os.path.abspath(jpath)), _STATE_FILE)


def _load_state(ctx):
    path = _state_path(ctx)
    if not path or not os.path.exists(path):
        return {"cci_state": {}, "intents": {}}, path
    try:
        with open(path) as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise ValueError("state not a dict")
        data.setdefault("cci_state", {})
        data.setdefault("intents", {})
        return data, path
    except Exception:
        return {"cci_state": {}, "intents": {}}, path


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


def _rows(raw):
    out = []
    for r in raw or []:
        out.append({"t": str(r["t"]), "o": float(r["o"]), "h": float(r["h"]),
                    "l": float(r["l"]), "c": float(r["c"]),
                    "v": float(r.get("v", 0.0))})
    out.sort(key=lambda x: x["t"])
    return out


def evaluate(ctx):
    from core.sleeve import Context as OldContext
    from sleeves import t_cci_corr as strat

    state, state_path = _load_state(ctx)
    params = ctx.params or {}
    pextra = dict(params.get("extra") or {})
    session = ctx.now.astimezone(ET).date().isoformat() \
        if ctx.now.tzinfo else ctx.now.date().isoformat()

    view = getattr(ctx, "_view", {}) or {}
    bars = {}
    for key, raw in (view.get("bars") or {}).items():
        if not key.endswith("|1Day"):
            continue
        sym = key[:-5]
        if "/" in sym or sym.endswith("-USD"):
            continue  # equities only (crypto mirrors excluded)
        rows = _rows(raw)
        if rows:
            bars[sym] = rows
    vix_rows = _rows(view.get("bars:VIX:1Day"))

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
    if "cci_state" not in pextra:
        extra["cci_state"] = dict(state.get("cci_state") or {})
    extra["vix_rows"] = vix_rows

    old_ctx = OldContext(now=ctx.now.timestamp(), session=session,
                         equity=equity, extra=extra)
    sleeve = strat.TcciCorrSleeve()
    intents = sleeve.signal(bars, slice_state, old_ctx) or []

    state["cci_state"] = sleeve.cci_state
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
