"""Adapter for raschke_rre (v3 port of v2 batch 5) -- interface glue only.

Strategy lives, ported faithfully and byte-identical, in
sleeves/raschke_rre.py (with its core/raschke_rre engine package).
This file only re-shapes the v3 snapshot view into the old signal()
inputs (port/bridge.py, v2 'batch5' profile) and old Intents into v3
dicts. The rre_journal durable state is served from / persisted to the
sleeve's own journal file in its v3 state_dir (the GAP-CURE channel).
"""
from datetime import datetime, time as _dtime, timedelta
from zoneinfo import ZoneInfo

from port.bridge import (ViewCtx, bar_dicts, run_old_persisted,
                         serve_journal, state_from_positions)
from sleeves import raschke_rre as _strat

_ET = ZoneInfo("America/New_York")
_RTH_OPEN = _dtime(9, 30)


def _bar_epoch(raw):
    try:
        return float(raw)
    except (TypeError, ValueError):
        pass
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_ET)
    return dt.timestamp()


def _rth_only(rows):
    """CR-5 (2026-11-14): shape the bar door's SPY 5Min series to the
    sleeve's RTH session before the strategy sees it. The warm door
    serves extended hours (04:00-19:55, 192 bars/day); his Session
    grid is 09:30-close, so the strategy's frozen prior-session
    reference could never read complete (first bar 04:00 != session
    open) and its warmup accumulator (core features / baseline) was
    gated off on every pass, in every session, across every runner
    restart -- stamps pinned at core_features 0/27, baseline_count
    0/20 after 13 sessions. Filtering here is adapter shaping only:
    session close (incl. early closes) is the strategy's own
    session_close_dt; no strategy rule, threshold or engine code
    changes."""
    out = []
    for b in rows or []:
        if not isinstance(b, dict):
            continue
        t = _bar_epoch(b.get("t"))
        if t is None:
            continue
        start = datetime.fromtimestamp(t, tz=_ET)
        if start.time() < _RTH_OPEN:
            continue
        close_dt = _strat.session_close_dt(start.date().isoformat())
        if start + timedelta(minutes=5) > close_dt:
            continue
        out.append(b)
    return out

SLEEVE_ID = "raschke_rre"
WARMUP_BARS = {"5Min": 100}
INPUTS = ("bars_5min", "positions", "session_fills", "quotes",
          "macro_events")


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
    bars5 = _rth_only(bar_dicts(vctx, "SPY", "5Min", 2000))
    return {"bars_5m_long": {"SPY": bars5},
            "sleeve_state": p.get("sleeve_state") or ex.get("sleeve_state")
                            or state_from_positions(vctx),
            "session_fills": p.get("session_fills") or ex.get("session_fills")
                             or _fills(vctx),
            "latest_quote": p.get("latest_quote") or ex.get("latest_quote")
                            or _quotes(vctx),
            # MIDNA RULING R2-RRE-20261025: the macro-release
            # calendar payload (producer key macro_events) that
            # drives the sleeve's section-7 event gates.
            "macro_events": p.get("macro_events") or ex.get("macro_events")
                            or vctx.view.get("macro_events")}


def evaluate(view, ctx):
    vctx = ViewCtx(view, ctx, SLEEVE_ID)
    bars = {"SPY": _rth_only(bar_dicts(vctx, "SPY", "5Min", 2000))}
    extra = _extra(vctx)
    # CR-5: load the persisted warmup accumulator (the rre_journal,
    # carrying the router snapshot whose context history / baseline
    # and lane feature state ARE the accumulator) at evaluate start,
    # here in the adapter, so a runner restart resumes the counters
    # instead of re-deriving them from a cold router. The bridge's
    # own serve remains as the fallback for any caller that reaches
    # run_old_persisted without this adapter.
    served = serve_journal(vctx, "rre_journal")
    if isinstance(served, dict):
        extra["rre_journal"] = served
    return run_old_persisted(vctx, _strat, bars, extra, ("rre_journal",))
