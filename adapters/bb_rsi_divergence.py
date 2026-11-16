"""Adapter for bb_rsi_divergence — v2 plumbing only, no strategy math.

Strategy lives in sleeves/bb_rsi_divergence.py (faithful port of the
Test package v2.2 sleeve plus the switch-gated expansion). This file
re-expresses the old context.extra channels in v2 terms:

  active_universe   <- config params / the sleeve's CONFIG universe
  sleeve_state      <- ctx.positions enriched with the entry plan the
                       adapter recorded at entry-intent time (stop /
                       target / exit rules / entry bar) in the sleeve's
                       own state file; params["extra"]["sleeve_state"]
                       overrides win per symbol (fixture drives)
  session_orders /  <- the dispatcher's lifecycle as this sleeve can
  session_fills        see it locally: intents the adapter emitted
                       (recorded with their position_intent) plus fill
                       events in the sleeve journal, scoped to the
                       session. Explicit params["extra"] values —
                       including None — pass through verbatim, so the
                       sleeve's fail-closed lifecycle gates keep their
                       exact original meaning in fixture drives. When
                       neither source exists the values stay None.
  meta.last_evaluated_bar_by_symbol + bar_cursor_ready
                    <- persisted in the sleeve state file beside its
                       journal (v2's per-sleeve state machinery); the
                       cursor advances to each evaluated symbol's
                       latest bar after every evaluation. Ready only
                       when that file is readable/writable.
  latest_quote      <- the warm cache's latest SIP quotes
                       (cache/quotes/latest.json, written at warm time
                       by runtime/quotes_warm.py); params override wins.

The state file is state/<sleeve>/bb_rsi_state.json, derived from the
journal path the runner injects (ctx._journal); contexts without a
journal (direct unit drives) get cursor_ready=False unless params say
otherwise — the sleeve then fails entries closed, as designed.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from adapters._bridge import bars_old, epoch_old  # noqa: E402

ET = ZoneInfo("America/New_York")
SLEEVE_ID = "bb_rsi_divergence"
WARMUP_BARS = {"1Hour": 200}
_STATE_FILE = "bb_rsi_state.json"


def _state_path(ctx):
    jpath = getattr(ctx, "_journal", None)
    if not jpath:
        return None
    return os.path.join(os.path.dirname(os.path.abspath(jpath)), _STATE_FILE)


def _load_state(ctx):
    path = _state_path(ctx)
    if not path or not os.path.exists(path):
        return {"cursor": {}, "plans": {}, "intents": {}}, path, False
    try:
        with open(path) as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise ValueError("state not a dict")
        data.setdefault("cursor", {})
        data.setdefault("plans", {})
        data.setdefault("intents", {})
        return data, path, True
    except Exception:
        return {"cursor": {}, "plans": {}, "intents": {}}, path, False


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


def _symbols(ctx, state):
    from sleeves.bb_rsi_divergence import CONFIG, expansion_enabled
    extra = (ctx.params or {}).get("extra") or {}
    if isinstance(extra.get("active_universe"), (list, tuple)):
        syms = [str(s).upper() for s in extra["active_universe"]]
    elif expansion_enabled(extra):
        syms = list(CONFIG.universe)
    else:
        from sleeves.bb_rsi_divergence import UNIVERSE_12
        syms = list(UNIVERSE_12)
    for p in ctx.positions or []:
        # READINESS-D9-20261112 (ENTER-EXIT-CENSUS D9 remainder):
        # ctx.positions is the broker ACCOUNT view. Only a row
        # attributable to THIS sleeve (its intent_id carries the
        # sleeve's prefix — the CR-4 attribution) may add its
        # symbol to the candidate universe, so the sleeve's own
        # holdings keep their bars for exit evaluation. Other
        # sleeves' symbols, OCC option contracts included, never
        # become candidates for this sleeve.
        iid = str(p.get("intent_id") or "")
        if iid.startswith("bb_rsi_divergence-") \
                and p["symbol"] not in syms:
            syms.append(p["symbol"])
    for s in (state.get("plans") or {}):
        if s not in syms:
            syms.append(s)
    return syms


def _lifecycle(ctx, state, session):
    """(session_orders, session_fills) from params or local records."""
    extra = (ctx.params or {}).get("extra") or {}
    if "session_orders" in extra or "session_fills" in extra:
        return extra.get("session_orders"), extra.get("session_fills")
    intents = state.get("intents") or {}
    if not intents and not _state_path(ctx):
        return None, None
    fills = []
    jpath = getattr(ctx, "_journal", None)
    filled_ids = set()
    if jpath and os.path.exists(jpath):
        from runtime.journal import tail_lines
        for rec in tail_lines(jpath, 100000):
            if rec.get("event") != "fill":
                continue
            iid = rec.get("intent_id")
            meta = intents.get(iid) or {}
            if meta.get("session") not in (None, session):
                continue
            filled_ids.add(iid)
            fills.append({
                "symbol": rec.get("symbol"),
                "position_intent": meta.get("position_intent"),
                "qty": rec.get("qty"),
                "price": rec.get("price"),
            })
    orders = []
    for iid, meta in intents.items():
        if meta.get("session") != session:
            continue
        if iid in filled_ids:
            orders.append({"symbol": meta.get("symbol"),
                           "position_intent": meta.get("position_intent"),
                           "status": "filled", "filled_qty": meta.get("qty")})
        else:
            orders.append({"symbol": meta.get("symbol"),
                           "position_intent": meta.get("position_intent"),
                           "status": "accepted", "filled_qty": 0})
    return orders, fills


def evaluate(ctx):
    from core.sleeve import Context as OldContext
    from sleeves import bb_rsi_divergence as strat

    state, state_path, state_ok = _load_state(ctx)
    params = ctx.params or {}
    pextra = dict(params.get("extra") or {})
    session = ctx.now.astimezone(ET).date().isoformat() \
        if ctx.now.tzinfo else ctx.now.date().isoformat()

    syms = _symbols(ctx, state)
    bars = {}
    for sym in syms:
        b = bars_old(ctx, sym, "1Hour", 2000)
        if b:
            bars[sym] = b

    # positions -> slice_state (qty map) + sleeve_state (plan-enriched)
    slice_state = {}
    sleeve_state = {}
    plans = state.get("plans") or {}
    for p in ctx.positions or []:
        qty = float(p.get("qty") or 0)
        if qty == 0:
            continue
        slice_state[p["symbol"]] = qty
        pos = {"qty": qty, "avg_price": p.get("avg_price"),
               "entry_px": p.get("avg_price"),
               "intent_id": p.get("intent_id")}
        if p.get("opened_at"):
            pos["entry_t"] = epoch_old(p["opened_at"])
            pos["fill_t"] = pos["entry_t"]
        plan = plans.get(p["symbol"]) or {}
        for k in ("stop_px", "target_px", "exit_rules", "entry_bar_t"):
            if plan.get(k) is not None:
                pos[k] = plan[k]
        sleeve_state[p["symbol"]] = {"position": pos}
    for sym, entry in (pextra.get("sleeve_state") or {}).items():
        sleeve_state[sym] = entry

    orders, fills = _lifecycle(ctx, state, session)

    quotes = {}
    read_quotes = getattr(getattr(ctx, "_cache", None), "read_quotes", None)
    if callable(read_quotes):
        try:
            quotes = read_quotes() or {}
        except Exception:
            quotes = {}
    if isinstance(pextra.get("latest_quote"), dict):
        quotes = pextra["latest_quote"]

    equity = float((ctx.slice or {}).get("capital_usd")
                   or (ctx.slice or {}).get("cash_usd") or 0.0)
    if params.get("equity"):
        equity = float(params["equity"])

    extra = dict(pextra)
    extra["active_universe"] = pextra.get("active_universe") or syms
    extra["sleeve_state"] = sleeve_state
    extra["session_orders"] = orders
    extra["session_fills"] = fills
    extra["latest_quote"] = quotes
    extra["meta"] = {"last_evaluated_bar_by_symbol": dict(state.get("cursor") or {})}
    if "bar_cursor_ready" not in pextra:
        extra["bar_cursor_ready"] = bool(state_path)

    old_ctx = OldContext(now=ctx.now.timestamp(), session=session,
                         equity=equity, extra=extra)
    sleeve = strat.BbRsiDivergenceSleeve()
    intents = sleeve.signal(bars, slice_state, old_ctx) or []
    strat.signal.last_evaluation = sleeve.last_evaluation

    # persist cursor (latest evaluated bar per symbol), entry plans and
    # emitted-intent lifecycle records for the next evaluation
    cursor = dict(state.get("cursor") or {})
    for sym, rows in bars.items():
        if rows:
            cursor[sym] = rows[-1]["t"]
    state["cursor"] = cursor
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
        if it.kind == "enter":
            rows = bars.get(it.symbol) or []
            state.setdefault("plans", {})[it.symbol] = {
                "stop_px": float(it.stop) if it.stop else None,
                "target_px": float(it.target) if it.target else None,
                "exit_rules": d["exit_rules"],
                "entry_bar_t": rows[-1]["t"] if rows else None,
                "direction": 1 if it.side == "buy" else -1,
                "session": session}
    _save_state(state_path, state)
    try:
        ctx.log("adapter_eval", sleeve=SLEEVE_ID, intents=len(out),
                last_evaluation=sleeve.last_evaluation)
    except Exception:
        pass
    return out
