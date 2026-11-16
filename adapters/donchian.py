"""Adapter for donchian — v2 interface glue ONLY (DESIGN §4a).

Bridges the v2 SleeveContext to the ported strategy module's native
contract: signal(bars, slice_state, core.sleeve.Context). Strategy math
in sleeves/donchian.py is copied faithfully and never edited here; all
translation (timeframes, position state, Intent -> v2 intent dict,
OCC handling for options sleeves) lives in this file.
"""
from __future__ import annotations
import re
from datetime import timezone

SLEEVE_ID = "donchian"
WARMUP_BARS = {'1Day': 25}

_OCC_RE = re.compile(r"^([A-Z]{1,6})(\d{6})[CP]\d{8}$")

def _epoch(t):
    # Old sleeves read bar timestamps as epoch seconds (float(b["t"]));
    # the v2 cache stores ISO strings - convert here, in the adapter.
    if isinstance(t, (int, float)):
        return float(t)
    from datetime import datetime as _dt
    dt = _dt.fromisoformat(str(t).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        from datetime import timezone as _tz
        dt = dt.replace(tzinfo=_tz.utc)
    return dt.timestamp()

def _bar_dicts(bars):
    return [{"t": _epoch(b.t), "o": b.o, "h": b.h, "l": b.l, "c": b.c, "v": b.v} for b in bars]

def _occ_expiry(sym):
    m = _OCC_RE.match(sym or "")
    if not m:
        return None
    d = m.group(2)
    return "20%s-%s-%s" % (d[:2], d[2:4], d[4:6])

def _occ_underlying(sym):
    m = _OCC_RE.match(sym or "")
    return m.group(1) if m else sym

def _build_state(ctx):
    """ctx.positions -> old sleeve_state shape: {symbol: {"position": {...}}}."""
    state = {}
    for p in ctx.positions or []:
        sym = p.get("symbol")
        qty = p.get("qty") or 0
        if not sym or not qty:
            continue
        pos = {"qty": qty, "entry_px": p.get("avg_price"),
                "entry_premium": p.get("avg_price"),
                "entry_date": (str(p.get("opened_at") or "")[:10] or None),
                "intent_id": p.get("intent_id")}
        if _OCC_RE.match(sym):
            pos["occ"] = sym
            pos["expiry"] = _occ_expiry(sym)
            key = _occ_underlying(sym)
        else:
            key = sym
        state[key] = {"position": pos, "qty": qty}  # aurelia rows read qty directly; others read ["position"]
    return state

def _translate(ctx, raw, seq):
    kind = "entry" if raw.kind == "enter" else "exit"
    qty = raw.qty if getattr(raw, "qty", None) is not None else raw.qty_hint
    if qty is None:
        return None
    symbol = raw.symbol
    reason = raw.reason or ""
    position_intent = getattr(raw, "position_intent", None)
    # Options sleeves encode the OCC contract in the reason (old dispatch
    # resolved the same encoding); v2 §4c wants the OCC symbol on the intent.
    m = re.search(r"occ=([A-Z]{1,6}\d{6}[CP]\d{8})", reason)
    if m:
        symbol = m.group(1)
        if position_intent is None:
            position_intent = "buy_to_open" if kind == "entry" else "sell_to_close"
    side = getattr(raw, "side", None)
    if side is None:
        if position_intent:
            side = "buy" if position_intent.startswith("buy") else "sell"
        else:
            side = "buy" if kind == "entry" else "sell"
    stamp = ctx.now.strftime("%Y%m%dT%H%M%S")
    out = {"intent_id": "%s-%s-%d" % (SLEEVE_ID, stamp, seq),
            "kind": kind, "symbol": symbol, "side": side, "qty": qty,
            "order_type": "limit" if getattr(raw, "limit_price", None) else "market",
            "limit_price": (round(float(raw.limit_price), 2) if getattr(raw, "limit_price", None) else None),
            "stop_price": None,
            "reason": ("%s: %s" % (SLEEVE_ID, reason))[:300] or SLEEVE_ID,
            "time_in_force": "day"}
    if position_intent:
        out["position_intent"] = position_intent
    if out["order_type"] == "market":
        del out["limit_price"]
    if getattr(raw, "price_hint", None):
        out["price_hint"] = float(raw.price_hint)
    _er = getattr(raw, "exit_rules", None)
    if _er:
        out["exit_rules"] = [{"kind": r.kind, "value": float(r.value)} for r in _er]
    return out

def evaluate(ctx):
    from core.sleeve import Context as OldContext
    import sleeves.donchian as strat
    params = dict(ctx.params or {})
    extra = dict(params.get("extra") or {})
    for k, v in params.items():
        if k not in ("extra", "universe", "symbols"):
            extra.setdefault(k, v)
    state = _build_state(ctx)
    if state:
        extra.setdefault("sleeve_state", state)
    equity = float((ctx.slice or {}).get("capital_usd") or (ctx.slice or {}).get("cash_usd") or 0.0)
    now = ctx.now if ctx.now.tzinfo else ctx.now.replace(tzinfo=timezone.utc)
    old_ctx = OldContext(now=now.timestamp(), session=now.strftime("%Y-%m-%d"),
                         equity=equity, market=dict(params.get("market") or {}), extra=extra)
    universe = list(params.get("universe") or extra.get("universe") or [])
    if not universe:
        # GAP-CURE: documented basket_41 (config/universes.json provenance)
        # was never wired; held-only default made entries impossible.
        try:
            from core.bars_universe import load_universes
            universe = list(load_universes().get("basket_41") or [])
        except Exception:
            universe = []
        for s in sorted(state.keys()):
            if s not in universe: universe.append(s)
    extra.setdefault("universe", universe)
    bars = {s: _bar_dicts(ctx.bars(s, "1Day", 300)) for s in universe}

    raw_intents = strat.signal(bars, {}, old_ctx)
    out = []
    for i, r in enumerate(raw_intents or [], start=1):
        t = _translate(ctx, r, i)
        if t is not None:
            out.append(t)
    return out
