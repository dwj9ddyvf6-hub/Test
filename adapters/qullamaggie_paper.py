"""Adapter for qullamaggie_paper (batch 5): v2 ctx -> ported qullamaggie_paper signal(). Strategy
module sleeves/qullamaggie_paper.py is byte-identical to source; this file is glue only.

Wiring (2026-10-24, WIRING-SOURCE-MAP §3): proposals are a core
product, produced warmer-side by core/qulla_feeds.QullaProducer
(runtime/qulla_warm.py) and persisted to cache/qulla/proposals.json.
_extra serves them only when the persisted session equals today's
session (a stale file never trades); config params remain an
override (the fixture channel). sleeve_state.orders — used by the
sleeve for dedupe + cumulative-budget spent math — is served from
params when present, else synthesized from the sleeve's own journal
positions (runtime/journal.positions_from_journal via ctx.positions):
each open position becomes one sent order row whose client_id
reconstructs the sleeve's qulla-{session}-{symbol}-buy dedupe key
from its fill date.

EXIT CANON wiring (QULLA-EXIT-CANON-20261116): _extra also serves
"positions" — the cycle's position dicts verbatim (params override)
— and evaluate() serves 1Day bars for the held symbols only, so the
sleeve's in-signal exit management (stop breach / 1/3 scale / MA
trail, playbook section 1.10 step 6) has its inputs. With no open
positions both servings are empty and the entry path is untouched.
"""
from datetime import datetime
from adapters._batch5_common import (bar_dicts, bars_map, run_old,
                                      state_from_positions)
from adapters._bridge import session_of
from sleeves import qullamaggie_paper as _strat

SLEEVE_ID = "qullamaggie_paper"
WARMUP_BARS = {}

def _orders_from_positions(ctx):
    orders = []
    for p in ctx.positions or []:
        opened = str(p.get("opened_at") or "")[:10] or session_of(ctx)
        orders.append({
            "client_id": _strat.client_id(opened, p["symbol"]),
            "status": "sent",
            "quantity": abs(float(p.get("qty") or 0)),
            "entry": float(p.get("avg_price") or 0),
            "symbol": p["symbol"]})
    return orders

def _extra(ctx):
    p = ctx.params or {}
    proposals = p.get("proposals")
    if proposals is None:
        proposals = []
        reader = getattr(ctx, "qulla_proposals", None)
        if callable(reader):
            try:
                persisted = reader() or {}
            except Exception:
                persisted = {}
            if persisted.get("session") == session_of(ctx):
                proposals = persisted.get("proposals") or []
    state = p.get("sleeve_state")
    if state is None:
        state = {"orders": _orders_from_positions(ctx)}
    positions = p.get("positions")
    if positions is None and isinstance(state, dict):
        positions = state.get("positions")
    if positions is None:
        positions = list(ctx.positions or [])
    return {"proposals": proposals, "sleeve_state": state,
            "positions": positions}

def evaluate(ctx):
    held = []
    for p in ctx.positions or []:
        if p.get("symbol") and p["symbol"] not in held:
            held.append(p["symbol"])
    bars = bars_map(ctx, held, "1Day", 60) if held else {}
    return run_old(ctx, SLEEVE_ID, _strat, bars, _extra(ctx))
