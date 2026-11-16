"""Adapter for milkman_0dte — v3 plumbing only, no strategy math.

Strategy lives in sleeves/milkman_0dte.py (the v3-native expression
of the vendored authored sleeve; provenance in
desk3/milkman_0dte/PROVENANCE.md). This file re-expresses the v3
snapshot channels in the strategy's ctx.extra terms, following
adapters/trullas_divergence.py:

  milkman_state  <- the strategy's state dict, persisted in the
                    sleeve's own state file
                    state/<id>/milkman_state.json beside its journal
  spx_probe      <- desk3.milkman_0dte.spx_probe.availability() over
                    state/probes/spx_0dte.json (no record -> inert
                    with the named reason, as authored)
  chain_rows     <- ctx.options_chain("SPX") rows, normalized to the
                    authored row shape; delta stays None when the
                    snapshot carries no greeks (this tier), never
                    fabricated
  quotes         <- the same chain payload's quotes map
  lane_signals / <- the Milkman intraday study, ported
  lane_exits        MILKMAN-0DTE-PORT-20261116 (PROVENANCE gap 1
                    CLOSED): desk3.milkman_0dte.intraday_study (the
                    logic-identical port of Femto-lean
                    desk/sleeves/milkman/intraday.py) over a Panel
                    built from the snapshot's SPY bars (1Min /
                    1Hour / 1Day), applying the vendored authored
                    sleeve's own eligibility rules (same_bar /
                    missed / LATE) exactly as
                    desk3/milkman_0dte/milkman_0dte.py applied
                    them. ESMON and OPX4 are never asked for (the
                    authored EXCLUDED). params["extra"] overrides
                    still win in tests. On any study failure (no
                    bars, no live panel, exception) both stay EMPTY
                    and the failure is logged — fail-closed, never
                    a fabricated signal.
  book_pnl       <- the sleeve book's recorded session P&L from its
                    state file (0.0 while the book is empty, which is
                    always while parked); the daily stop reads it
                    exactly as authored.
"""
from __future__ import annotations

import json
import os
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

ET = ZoneInfo("America/New_York")
SLEEVE_ID = "mk_zerodte_spx"
_STATE_FILE = "milkman_state.json"
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _state_path(ctx):
    jpath = getattr(ctx, "_journal", None)
    if not jpath:
        return None
    return os.path.join(os.path.dirname(os.path.abspath(jpath)), _STATE_FILE)


def _load_state(ctx):
    path = _state_path(ctx)
    if not path or not os.path.exists(path):
        return {"cursor": {}, "intents": {}, "milkman_state": {},
                "book_pnl": 0.0}, path
    try:
        with open(path) as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise ValueError("state not a dict")
        for k in ("cursor", "intents", "milkman_state"):
            data.setdefault(k, {})
        data.setdefault("book_pnl", 0.0)
        return data, path
    except Exception:
        return {"cursor": {}, "intents": {}, "milkman_state": {},
                "book_pnl": 0.0}, path


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


def _chain_rows(ctx):
    """Normalize ctx.options_chain('SPX') to authored row dicts."""
    try:
        chain = ctx.options_chain("SPX") or {}
    except Exception:
        return None, {}
    rows_raw, quotes = [], {}
    if isinstance(chain, dict):
        chains = chain.get("chains") if isinstance(chain.get("chains"), dict) else None
        if chains:
            rows_raw = chains.get("SPX") or next(
                (v for v in chains.values() if isinstance(v, list)), [])
        elif isinstance(chain.get("rows"), list):
            rows_raw = chain["rows"]
        if isinstance(chain.get("quotes"), dict):
            quotes = {k: {"bid": (v or {}).get("bid"), "ask": (v or {}).get("ask")}
                      for k, v in chain["quotes"].items()}
    if not rows_raw:
        return None, quotes
    rows = []
    for r in rows_raw:
        if not isinstance(r, dict) or not r.get("symbol"):
            continue
        sym = r["symbol"]
        rows.append({"symbol": sym,
                     "root": r.get("root") or sym[:-15],
                     "expiration": r.get("expiration"),
                     "type": r.get("type"),
                     "strike": r.get("strike"),
                     "bid": r.get("bid"), "ask": r.get("ask"),
                     "delta": r.get("delta"),
                     "t": r.get("t") or r.get("greeks_received_at") or 0})
    return rows or None, quotes


def _epoch(t):
    """Snapshot bar stamps (ISO text) -> epoch seconds; numeric
    stamps pass through."""
    if isinstance(t, (int, float)):
        return float(t)
    from datetime import datetime
    dt = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ET)
    return dt.timestamp()


def _bar_dicts(ctx, symbol, tf, n):
    rows = ctx.bars(symbol, tf, n) or []
    out = []
    for b in rows:
        try:
            out.append({"t": _epoch(b.t), "o": float(b.o),
                        "h": float(b.h), "l": float(b.l),
                        "c": float(b.c), "v": float(b.v or 0.0)})
        except Exception:
            continue
    return out


def lane_signals_for(ctx, session, open_keys):
    """The study's lane trades for the live session, in the
    vendored authored sleeve's signal shape and eligibility
    (desk3/milkman_0dte/milkman_0dte.py signal()):

      sigs = lane_trades over every SETUPS lane except EXCLUDED,
             keyed f"{setup}:{'L'|'S'}|{session}|{t['key']}"
      exits: an open key whose trade carries an exit
      entries: a trade is enterable only while its exit has not
             fired and its deciding bar is at most LATE bars old
             (decide >= jmax - LATE); a trade that opened and
             closed inside its deciding bar (exit bar <= decide)
             is same_bar and never enterable.

    Returns (lane_signals, lane_exits, note); note names why the
    study produced nothing when it did. Raises nothing: the
    caller fails closed on an exception note."""
    from sleeves import milkman_0dte as strat
    try:
        from desk3.milkman_0dte import intraday_study as I
    except Exception as e:
        return [], [], f"study import failed: {type(e).__name__}: {e}"
    try:
        if not I.full_day(session):
            return [], [], "not a full session: the study does not trade it"
        m1 = _bar_dicts(ctx, "SPY", "1Min", 30000)
        if not m1:
            return [], [], "no SPY 1Min bars in the snapshot"
        d1 = _bar_dicts(ctx, "SPY", "1Day", 1000)
        h1 = _bar_dicts(ctx, "SPY", "1Hour", 6000)
        P = I.Panel(m1, d1, h1, today=session)
        if P.today != session or P.live_di is None:
            return [], [], "no live SPY panel for the session"
        jmax = int(P.E0[P.live_di])
        signals, exits = [], []
        for setup in I.SETUPS:
            if setup in strat.EXCLUDED:
                continue
            for sd, cell in I.SETUPS[setup][1]:
                lane = f"{setup}:{'L' if sd > 0 else 'S'}"
                for t in I.lane_trades(setup, P, P.live_di, cell, sd):
                    key = f"{lane}|{session}|{t['key']}"
                    ex = t.get("exit")
                    if key in open_keys and ex is not None:
                        exits.append(key)
                    if ex is not None and ex[0] <= t["decide"]:
                        continue  # same_bar
                    if t["decide"] < jmax - I.LATE or ex is not None:
                        continue  # missed / already exited
                    signals.append({"key": key, "side": sd})
        return signals, exits, ""
    except Exception as e:
        return [], [], f"study failed: {type(e).__name__}: {e}"


def evaluate(ctx):
    from core.sleeve import Context as OldContext
    from sleeves import milkman_0dte as strat

    state, state_path = _load_state(ctx)
    params = ctx.params or {}
    pextra = dict(params.get("extra") or {})
    session = ctx.now.astimezone(ET).date().isoformat() \
        if ctx.now.tzinfo else ctx.now.date().isoformat()

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
    if "milkman_state" not in pextra:
        extra["milkman_state"] = dict(state.get("milkman_state") or {})
    if "spx_probe" not in pextra:
        from desk3.milkman_0dte import spx_probe
        under, why = spx_probe.availability(_ROOT, session)
        extra["spx_probe"] = {"available": bool(under), "underlying": under,
                              "why": why}
    if "chain_rows" not in pextra or "quotes" not in pextra:
        chain_rows, quotes = _chain_rows(ctx)
        extra.setdefault("chain_rows", chain_rows)
        extra.setdefault("quotes", quotes)
    if "lane_signals" not in pextra or "lane_exits" not in pextra:
        open_keys = set((extra.get("milkman_state") or {}).get("open") or {})
        signals, exits, note = lane_signals_for(ctx, session, open_keys)
        extra.setdefault("lane_signals", signals)
        extra.setdefault("lane_exits", exits)
        if note:
            extra.setdefault("lane_study_note", note)
    extra.setdefault("lane_signals", [])
    extra.setdefault("lane_exits", [])
    if "book_pnl" not in pextra:
        extra["book_pnl"] = float(state.get("book_pnl") or 0.0)

    old_ctx = OldContext(now=ctx.now.timestamp(), session=session,
                         equity=equity, extra=extra)
    sleeve = strat.Milkman0DTESleeve()
    intents = sleeve.signal({}, slice_state, old_ctx) or []

    state["milkman_state"] = sleeve.milkman_state
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
