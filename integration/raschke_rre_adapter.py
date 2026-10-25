"""Adapter for raschke_rre (v3 port of v2 batch 5) -- interface glue only.

Strategy lives, ported faithfully and byte-identical, in
sleeves/raschke_rre.py (with its core/raschke_rre engine package).
This file only re-shapes the v3 snapshot view into the old signal()
inputs (port/bridge.py, v2 'batch5' profile) and old Intents into v3
dicts. The rre_journal durable state is served from / persisted to the
sleeve's own journal file in its v3 state_dir (the GAP-CURE channel).
"""
from port.bridge import (ViewCtx, bar_dicts, run_old_persisted,
                         state_from_positions)
from sleeves import raschke_rre as _strat

SLEEVE_ID = "raschke_rre"
WARMUP_BARS = {"5Min": 100}
INPUTS = ("bars_5min", "positions", "session_fills", "latest_quotes")


def _fills(vctx):
    try:
        return vctx.session_fills() or []
    except Exception:
        return []


def _quotes(vctx):
    try:
        return vctx.latest_quotes() or {}
    except Exception:
        return {}


def _extra(vctx):
    p = vctx.params or {}
    ex = p.get("extra") or {}
    bars5 = bar_dicts(vctx, "SPY", "5Min", 2000)
    return {"bars_5m_long": {"SPY": bars5},
            "sleeve_state": p.get("sleeve_state") or ex.get("sleeve_state")
                            or state_from_positions(vctx),
            "session_fills": p.get("session_fills") or ex.get("session_fills")
                             or _fills(vctx),
            "latest_quote": p.get("latest_quote") or ex.get("latest_quote")
                            or _quotes(vctx)}


def evaluate(view, ctx):
    vctx = ViewCtx(view, ctx, SLEEVE_ID)
    bars = {"SPY": bar_dicts(vctx, "SPY", "5Min", 2000)}
    return run_old_persisted(vctx, _strat, bars, _extra(vctx), ("rre_journal",))
