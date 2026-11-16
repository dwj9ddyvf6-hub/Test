"""Adapter for investandbefree_dmac_deep (DMAC variant; base adapter shape, variant sleeve module) — v3 plumbing only, no strategy math.

Strategy lives in sleeves/investandbefree_dmac.py
(INVESTANDBEFREE-DMAC-SPEC-2026-10-29, frozen). This file re-expresses
the v2 context channels in v3 snapshot terms, following
adapters/grok_sr_spy.py for persisted sleeve state and
adapters/capitulation_options.py for options state/translation:

  bars (all frames) <- filtered through the core's closed_bars()
                       at this boundary (and again in the core):
                       any bar whose period has not ended as of
                       ctx.now is dropped, so the forming daily,
                       the current weekly and the in-progress hour
                       never reach the sleeve
  bars (daily)      <- ctx.bars(sym, "1Day", 400) via the bridge
                       (served by desk3/warm.py: 500-calendar-day fetch,
                       ~346 closed rows for SPY/QQQ)
  bars_weekly       <- ctx.bars(sym, "1Week", 200) (warm window widened
                       to 1000 calendar days at this install: ~143 rows)
  bars_1h           <- ctx.bars(sym, "1Hour", 3000) (SPY/QQQ targeted
                       200-calendar-day 1Hour fetch added at this
                       install: ~120+ RTH sessions for 4H aggregation)
  chains / quotes   <- ctx.options_chain(sym) normalized by the
                       bridge serve_options helper (the established
                       'options' input shape)
  sleeve_state      <- ctx.positions (OCC positions mapped to their
                       underlying) merged with the persisted
                       dmac_state.json beside the sleeve journal:
                       entry premium, qty, direction, contract
                       identity and the partial-done flag
  dmac_state        <- persisted plan per underlying in the same
                       state file (cursor meta persisted there too)
"""
from __future__ import annotations

import json
import os
import re
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from adapters._bridge import bars_old, serve_options  # noqa: E402

ET = ZoneInfo("America/New_York")
SLEEVE_ID = "investandbefree_dmac_deep"

# F1 cure (2026-10-29): the live cycle snapshot carries no 'slice'
# key (no producer emits one, the worker injects none), so sizing
# must fall back to this sleeve's own configured $10,000 slice
# (config/sleeves.json) - the aster adapters' `or 10000.0`
# convention. A supplied slice still governs when present.
SLICE_FALLBACK_USD = 10000.0
_STATE_FILE = "dmac_state.json"
_SYMBOLS = ("SPY", "QQQ")
_OCC_RE = re.compile(r"^([A-Z]{1,6})(\d{6})[CP]\d{8}$")


def _state_path(ctx):
    jpath = getattr(ctx, "_journal", None)
    if not jpath:
        return None
    return os.path.join(os.path.dirname(os.path.abspath(jpath)), _STATE_FILE)


def _load_state(ctx):
    path = _state_path(ctx)
    if not path or not os.path.exists(path):
        return {"cursor": {}, "dmac_state": {}, "intents": {}}, path, False
    try:
        with open(path) as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise ValueError("state not a dict")
        for k in ("cursor", "dmac_state", "intents"):
            data.setdefault(k, {})
        return data, path, True
    except Exception:
        return {"cursor": {}, "dmac_state": {}, "intents": {}}, path, False


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


def _occ_expiry(sym):
    m = _OCC_RE.match(sym or "")
    if not m:
        return None
    d = m.group(2)
    return "20%s-%s-%s" % (d[:2], d[2:4], d[4:6])


def _build_sleeve_state(ctx, dmac_state):
    """ctx.positions -> {UND: {"position": {...}}} merging the
    persisted plan (direction, partial-done flag)."""
    state = {}
    for p in ctx.positions or []:
        sym = p.get("symbol")
        qty = float(p.get("qty") or 0)
        if not sym or qty == 0 or not _OCC_RE.match(sym):
            continue
        und = _OCC_RE.match(sym).group(1)
        if und not in _SYMBOLS:
            continue
        plan = dmac_state.get(und) or {}
        state[und] = {"position": {
            "occ": sym, "qty": abs(qty),
            "entry_premium": float(p.get("avg_price") or plan.get("entry_premium") or 0),
            "entry_px": float(p.get("avg_price") or 0),
            "expiry": _occ_expiry(sym) or plan.get("expiry"),
            "direction": plan.get("direction") or 1,
            "partial_done": bool(plan.get("partial_done")),
            "intent_id": p.get("intent_id")}}
    return state


def _translate(ctx, raw, seq):
    kind = "entry" if raw.kind == "enter" else "exit"
    qty = raw.qty if getattr(raw, "qty", None) is not None else raw.qty_hint
    if qty is None:
        return None
    symbol = raw.symbol
    reason = raw.reason or ""
    m = re.search(r"occ=([A-Z]{1,6}\d{6}[CP]\d{8})", reason)
    position_intent = getattr(raw, "position_intent", None)
    if m:
        symbol = m.group(1)
        if position_intent is None:
            position_intent = "buy_to_open" if kind == "entry" else "sell_to_close"
    side = getattr(raw, "side", None)
    if side is None:
        side = "buy" if kind == "entry" else "sell"
    stamp = ctx.now.strftime("%Y%m%dT%H%M%S")
    out = {"intent_id": "%s-%s-%d" % (SLEEVE_ID, stamp, seq),
           "kind": kind, "symbol": symbol, "side": side, "qty": qty,
           "order_type": "limit" if getattr(raw, "limit_price", None) else "market",
           "limit_price": (round(float(raw.limit_price), 2)
                           if getattr(raw, "limit_price", None) else None),
           "stop_price": None,
           "reason": ("%s: %s" % (SLEEVE_ID, reason))[:500] or SLEEVE_ID,
           "time_in_force": "day"}
    if position_intent:
        out["position_intent"] = position_intent
    if out["order_type"] == "market":
        del out["limit_price"]
    if getattr(raw, "price_hint", None):
        out["price_hint"] = float(raw.price_hint)
    am = re.search(r"ask=([0-9]+(?:\.[0-9]+)?)", reason)
    if am and symbol != raw.symbol and kind == "entry":
        out["order_type"] = "limit"
        out["limit_price"] = round(float(am.group(1)), 2)
    return out


def evaluate(ctx):
    from core.sleeve import Context as OldContext
    from sleeves import investandbefree_dmac_deep as strat

    state, state_path, _ok = _load_state(ctx)
    params = ctx.params or {}
    pextra = dict(params.get("extra") or {})
    session = ctx.now.astimezone(ET).date().isoformat() \
        if ctx.now.tzinfo else ctx.now.date().isoformat()

    now_ts = ctx.now.timestamp()
    bars, weekly, h1 = {}, {}, {}
    for sym in _SYMBOLS:
        d = strat.closed_bars(bars_old(ctx, sym, "1Day", 400),
                              "1Day", now_ts)
        if d:
            bars[sym] = d
        w = strat.closed_bars(bars_old(ctx, sym, "1Week", 200),
                              "1Week", now_ts)
        if w:
            weekly[sym] = w
        h = strat.closed_bars(bars_old(ctx, sym, "1Hour", 3000),
                              "1Hour", now_ts)
        if h:
            h1[sym] = h

    chains = dict(pextra.get("chains") or {})
    quotes = dict(pextra.get("quotes") or {})
    if not chains:
        served_chains, served_quotes = serve_options(ctx, list(_SYMBOLS))
        chains = served_chains
        for occ, q in served_quotes.items():
            quotes.setdefault(occ, q)

    dmac_state = dict(pextra.get("dmac_state") or state.get("dmac_state") or {})
    sleeve_state = _build_sleeve_state(ctx, dmac_state)
    for sym, st in (pextra.get("sleeve_state") or {}).items():
        sleeve_state.setdefault(sym, st)

    # Sizing equity: a supplied slice governs; when the live
    # snapshot carries no slice (F1, 2026-10-29) fall back to this
    # sleeve's own configured $10,000 slice.
    equity = float((ctx.slice or {}).get("capital_usd")
                   or (ctx.slice or {}).get("cash_usd")
                   or SLICE_FALLBACK_USD)
    if params.get("equity"):
        equity = float(params["equity"])

    extra = dict(pextra)
    extra["bars_weekly"] = weekly
    extra["bars_1h"] = h1
    extra["chains"] = chains
    extra["quotes"] = quotes
    extra["sleeve_state"] = sleeve_state
    extra["dmac_state"] = dmac_state

    old_ctx = OldContext(now=ctx.now.timestamp(), session=session,
                         equity=equity, extra=extra)
    sleeve = strat.InvestAndBeFreeDmacSleeve()
    intents = sleeve.signal(bars, {}, old_ctx) or []

    cursor = dict(state.get("cursor") or {})
    for sym, rows in bars.items():
        if rows:
            cursor[sym] = rows[-1]["t"]
    state["cursor"] = cursor
    # Positions that vanished close out their persisted plan; the
    # core's post-signal dmac_state is authoritative otherwise.
    new_state = dict(sleeve.dmac_state or {})
    state["dmac_state"] = new_state
    out = []
    for i, raw in enumerate(intents, 1):
        d = _translate(ctx, raw, i)
        if d is not None:
            out.append(d)
            state.setdefault("intents", {})[d["intent_id"]] = {
                "symbol": d["symbol"], "qty": d["qty"],
                "session": session, "kind": d["kind"]}
    _save_state(state_path, state)
    try:
        ctx.log("adapter_eval", sleeve=SLEEVE_ID, intents=len(out),
                last_evaluation=sleeve.last_evaluation)
    except Exception:
        pass
    return out
