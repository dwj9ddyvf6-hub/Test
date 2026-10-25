"""Adapter for vix_hedge (v3 port, batch 8) — interface glue only.

Strategy lives, ported faithfully, in sleeves/vix_hedge.py (v2 sha256
7e04e844...801ec7). This file re-expresses the v2 adapter
(adapters/vix_hedge.py @ v2, sha256 bb409c44...f78) + the batch-7
_old_bridge profile (state_old / equity_of / old_context_old /
translate_old / run_old_persisted) against the v3 snapshot view:

  view["bars"]      {"VXX": [bar...], "VIX"|"^VIX": [bar...]}
  view["options"]   {"chains": {"VXX": [...]}, "quotes": {OCC: {...}}}
  view["positions"] [broker position dicts]
  ctx               {sleeve_id, session, now (ISO), equity, extra,
                     positions} — ctx/view "extra" is the fixture /
                     producer channel (params["extra"] in v2) and is
                     merged setdefault-style, adapter values winning,
                     exactly as v2 run_old_persisted did.

Producer-registry declaration: INPUTS / PRODUCERS below; the same row
is registered in config/sleeves.json.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from sleeves.vix_hedge import VixHedge

SLEEVE_ID = "vix_hedge"
INPUTS = ("bars", "options", "positions")
PRODUCERS = (
    {"name": "bars", "outputs": ("bars",), "freshness_sla_s": 900},
    {"name": "options", "outputs": ("options",), "freshness_sla_s": 900},
    {"name": "positions", "outputs": ("positions",), "freshness_sla_s": 900},
)
DEFAULT_EQUITY = 10000.0  # v2 equity_of: slice capital_usd ($10k row)

LAST_EVALUATION = {}

_PI_SIDE = {"buy_to_open": "buy", "buy_to_close": "buy",
            "sell_to_open": "sell", "sell_to_close": "sell"}
_OCC_RE = re.compile(r"^([A-Z]{1,6})\d{6}[CP]\d{8}$")


class _Context:
    def __init__(self, now, session, equity, extra):
        self.now = now
        self.session = session
        self.equity = equity
        self.account_equity = None
        self.extra = extra


def _state_old(positions):
    """v2 state_old, verbatim semantics: position record carried, plus
    entry_px/entry_premium/entry_date aliases and OCC-underlying alias."""
    state = {}
    for p in positions or []:
        pos = dict(p)
        if pos.get("avg_price") is not None:
            pos.setdefault("entry_px", pos.get("avg_price"))
            pos.setdefault("entry_premium", pos.get("avg_price"))
        if pos.get("opened_at"):
            pos.setdefault("entry_date", str(pos["opened_at"])[:10])
        state[pos["symbol"]] = {"position": pos}
        m = _OCC_RE.match(pos["symbol"] or "")
        if m:
            pos.setdefault("occ", pos["symbol"])
            state.setdefault(m.group(1), {"position": pos})
    return state


def _options_extra(view, positions):
    """v2 adapter _options_extra, re-sourced from the snapshot view."""
    options = view.get("options") or {}
    if isinstance(options.get("VXX"), dict):  # per-underlying shape
        options = options["VXX"]
    bars_map = view.get("bars") or {}
    vix_bars = bars_map.get("VIX") or bars_map.get("^VIX") or []
    extra = {"vix_closes": [b["c"] for b in vix_bars]}
    # ENH (IMPROVE-vix_hedge): held imported OCC = the fresh broker read.
    for pos in positions or []:
        if pos.get("symbol") == "VXX261218C00020000":
            extra["vix_hedge_import"] = {
                "occ": "VXX261218C00020000",
                "contracts": int(float(pos.get("qty") or 8)),
                "expiry": "2026-12-18",
                "entry_premium": float(pos.get("avg_price") or 1.10)}
    chains = options.get("chains") or view.get("chains")
    quotes = options.get("quotes") or view.get("quotes")
    if chains:
        extra["chains"] = chains
    if quotes:
        extra["quotes"] = quotes
    return extra


def _translate(intent, sleeve_id, stamp, seq):
    """v2 translate_old (batch-7 profile), verbatim semantics."""
    kind = "entry" if intent.kind == "enter" else "exit"
    qty = intent.qty if getattr(intent, "qty", None) is not None else intent.qty_hint
    note = ""
    if qty is None:
        qty = 1
        note = " [adapter: qty defaulted to 1 - strategy declared no qty]"
    qty = int(round(float(qty)))
    if qty <= 0:
        return None
    side = getattr(intent, "side", None) or _PI_SIDE.get(
        getattr(intent, "position_intent", None) or "")
    if not side:
        side = "sell" if kind == "exit" else "buy"
    symbol = intent.symbol
    position_intent = getattr(intent, "position_intent", None)
    m = re.search(r"occ=([A-Z]{1,6}\d{6}[CP]\d{8})", intent.reason or "")
    if m:
        symbol = m.group(1)
        if position_intent is None:
            position_intent = "buy_to_open" if kind == "entry" else "sell_to_close"
        side = "buy" if position_intent.startswith("buy") else "sell"
    out = {"intent_id": f"{sleeve_id}-{stamp}-{seq}",
           "kind": kind, "symbol": symbol, "side": side, "qty": qty,
           "order_type": "limit" if getattr(intent, "limit_price", None) else "market",
           "limit_price": (float(intent.limit_price)
                           if getattr(intent, "limit_price", None) else None),
           "stop_price": (float(intent.stop)
                          if getattr(intent, "stop", None) else None),
           "reason": ((intent.reason or intent.kind) + note)[:500],
           "time_in_force": "day"}
    if position_intent:
        out["position_intent"] = position_intent
    if getattr(intent, "price_hint", None):
        out["price_hint"] = float(intent.price_hint)
    if getattr(intent, "exit_rules", None):
        out["exit_rules"] = [{"kind": r.kind, "value": float(r.value)}
                             for r in intent.exit_rules]
    if getattr(intent, "legs", None):
        out["legs"] = [dict(leg) for leg in intent.legs]
    return out


def evaluate(view, ctx):
    view = view or {}
    ctx = ctx or {}
    sleeve_id = ctx.get("sleeve_id") or SLEEVE_ID
    positions = view.get("positions")
    if positions is None:
        positions = ctx.get("positions") or []
    bars_map = view.get("bars") or {}
    bars = {"VXX": list(bars_map.get("VXX") or [])}
    extra = _options_extra(view, positions)
    extra["sleeve_state"] = _state_old(positions)
    for src in (view.get("extra"), ctx.get("extra")):
        if isinstance(src, dict):
            for k, v in src.items():
                extra.setdefault(k, v)
    session = ctx.get("session") or view.get("session")
    now_iso = ctx.get("now") or view.get("now")
    if not session and now_iso:
        session = str(now_iso)[:10]
    if not session:
        session = "1970-01-01"
    if now_iso:
        try:
            now_dt = datetime.fromisoformat(str(now_iso).replace("Z", "+00:00"))
            if now_dt.tzinfo is None:
                now_dt = now_dt.replace(tzinfo=timezone.utc)
            now_ts, stamp = now_dt.timestamp(), now_dt.strftime("%Y%m%dT%H%M%S")
        except ValueError:
            now_ts, stamp = 0.0, str(now_iso)[:10].replace("-", "") + "T000000"
    else:
        now_ts, stamp = 0.0, session.replace("-", "") + "T000000"
    equity = ctx.get("equity") or view.get("equity") or DEFAULT_EQUITY
    old_ctx = _Context(now=now_ts, session=session,
                       equity=float(equity), extra=extra)
    inst = VixHedge()
    intents = inst.signal(bars, extra["sleeve_state"], old_ctx) or []
    global LAST_EVALUATION
    LAST_EVALUATION = getattr(inst, "last_evaluation", None) or {}
    out, seq = [], 0
    for it in intents:
        seq += 1
        t = _translate(it, sleeve_id, stamp, seq)
        if t is not None:
            out.append(t)
    return out
