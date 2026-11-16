"""Adapter for capitulation — v2 interface glue ONLY (DESIGN §4a).

Bridges the v2 SleeveContext to the ported strategy module's native
contract: signal(bars, slice_state, core.sleeve.Context). Strategy math
in sleeves/capitulation.py is copied faithfully and never edited here; all
translation (timeframes, position state, Intent -> v2 intent dict,
OCC handling for options sleeves) lives in this file.
"""
from __future__ import annotations
import json
import os
import re
from datetime import timezone

SLEEVE_ID = "capitulation"
WARMUP_BARS = {'1Day': 200, '1Hour': 20}

# --- ENH2 2026-10-24 (Edge pass batch 14) ------------------------------
# The sleeve's tranche-2 rule reads pos["tranche2_qty"] /
# pos["signal_date"], which no desk record carries (the journal
# position's fixed field list omits them; _build_state translates only
# qty/entry_px/entry_date/intent_id). The adapter therefore keeps the
# tranche plan itself — recorded when it translates a tranche-1 entry
# (whose reason states the full size verbatim, "tranche1 (of full N)")
# — in a state file beside the sleeve journal (the bb_rsi_divergence
# adapter's recorded-entry-plan pattern), and serves it merged into
# the position until the position reaches the full size. Switch:
# extra["capitulation_improve"]["tranche_plan_feed"], default ON;
# OFF serves the pre-change starved record exactly.
_PLAN_FILE = "capitulation_tranche_plans.json"
_TRANCHE1_RE = re.compile(r"tranche1 \(of full (\d+(?:\.\d+)?)\)")  # WS4: fractional full


def _plan_path(ctx):
    jpath = getattr(ctx, "_journal", None)
    if not jpath:
        return None
    return os.path.join(os.path.dirname(str(jpath)), _PLAN_FILE)


def _plan_feed_enabled(extra):
    ov = (extra or {}).get("capitulation_improve")
    if isinstance(ov, dict) and "tranche_plan_feed" in ov:
        return bool(ov["tranche_plan_feed"])
    return True


def _load_plans(ctx):
    path = _plan_path(ctx)
    if not path:
        return {}
    try:
        with open(path) as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_plans(ctx, plans):
    path = _plan_path(ctx)
    if not path:
        return
    try:
        with open(path, "w") as fh:
            json.dump(plans, fh, sort_keys=True)
    except Exception:
        pass


LAST_PAIRED = []


def _record_paired(ctx, rec):
    """Paired control/treatment record for the tranche-plan feed:
    kept in-module and appended to a JSONL beside the sleeve journal
    (the durable paired channel for this adapter-layer cure)."""
    LAST_PAIRED.append(rec)
    jpath = getattr(ctx, "_journal", None)
    if not jpath:
        return
    try:
        with open(os.path.join(os.path.dirname(str(jpath)),
                               "capitulation_enh2_paired.jsonl"),
                  "a") as fh:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
    except Exception:
        pass

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
    import sleeves.capitulation as strat
    params = dict(ctx.params or {})
    extra = dict(params.get("extra") or {})
    for k, v in params.items():
        if k not in ("extra", "universe", "symbols"):
            extra.setdefault(k, v)
    state = _build_state(ctx)
    # ENH2: serve recorded tranche plans into the positions they
    # belong to; a plan is complete (and dropped) once the held qty
    # reaches the tranche-1 intent's stated full size, and orphaned
    # plans (position gone) are pruned.
    _feed_on = _plan_feed_enabled(extra)
    _plans = _load_plans(ctx) if _feed_on else {}
    if _plans:
        _dirty = False
        for _sym in list(_plans):
            _row = state.get(_sym)
            _pos = (_row or {}).get("position")
            if not _pos:
                del _plans[_sym]
                _dirty = True
                continue
            _plan = _plans[_sym]
            if float(_pos.get("qty") or 0) >= float(_plan.get("full_qty") or 0):
                del _plans[_sym]
                _dirty = True
                continue
            _pos.setdefault("tranche2_qty", _plan.get("tranche2_qty"))
            _pos.setdefault("signal_date", _plan.get("signal_date"))
            _record_paired(ctx, {
                "exp_id": "ENH2-CAPITULATION-20261024", "symbol": _sym,
                "gate": "tranche_plan_feed", "switch_on": True,
                "control_decision": "tranche2_impossible",
                "treatment_decision": "tranche2_armed",
                "tranche2_qty": _plan.get("tranche2_qty"),
                "signal_date": _plan.get("signal_date")})
        if _dirty:
            _save_plans(ctx, _plans)
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
    bars = {}
    h1 = {}
    for s in universe:
        bars[s] = _bar_dicts(ctx.bars(s, "1Day", 300))
        h1[s] = _bar_dicts(ctx.bars(s, "1Hour", 300))
    extra.setdefault("bars_1h", h1)
    # GAP-CURE: earnings calendar produced at warm (ctx.earnings_calendar)
    # but never injected (phase_daily precedent); params keep precedence.
    if "earnings" not in extra:
        try:
            _cal = ctx.earnings_calendar() or {}
        except Exception:
            _cal = {}
        if _cal.get("earnings"):
            extra["earnings"] = _cal["earnings"]
            extra.setdefault("earnings_fresh", bool(_cal.get("fresh")))

    raw_intents = strat.signal(bars, {}, old_ctx)
    # ENH2: record the tranche plan for every tranche-1 entry this
    # pass emits (full size is stated in the intent reason verbatim).
    if _feed_on:
        _session = now.strftime("%Y-%m-%d")
        _changed = False
        for _r in raw_intents or []:
            if getattr(_r, "kind", None) != "enter":
                continue
            _m = _TRANCHE1_RE.search(getattr(_r, "reason", "") or "")
            if not _m:
                continue
            _full = float(_m.group(1))
            _t1 = getattr(_r, "qty", None)
            if _t1 is None:
                _t1 = getattr(_r, "qty_hint", None)
            try:
                _t1 = float(_t1)
            except (TypeError, ValueError):
                continue
            if _full - _t1 > 0:
                _plans[_r.symbol] = {
                    "tranche2_qty": _full - _t1,
                    "signal_date": _session,
                    "full_qty": _full}
                _changed = True
        if _changed:
            _save_plans(ctx, _plans)
    out = []
    for i, r in enumerate(raw_intents or [], start=1):
        t = _translate(ctx, r, i)
        if t is not None:
            out.append(t)
    return out
