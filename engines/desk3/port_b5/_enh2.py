"""ENH2 shared cure for batch-5 ported sleeves (Edge pass batch 17,
ENH-CBAR-20261024): completed-bar-only inputs.

Binding leak (perception/execution): the v2 adapters serve the
snapshot's bars verbatim, including the CURRENT session's still-forming
bar (daily bars are stamped 04:00Z and accumulate all session; intraday
candles accumulate until their span closes). Several batch-5
strategies read bars[-1] as if it were a completed close:

  - momentum: rank/pricing already filter via last_completed, but the
    -40% circuit breaker and the book-notional reference read bl[-1]
    raw — the breaker can fire (or fail to fire) on an incomplete bar,
    contradicting the sleeve's own completed-bar law.
  - momentum_rotation: compute_ranks / momentum_60d / buy pricing /
    disaster-stop checks all read bars[-1] with NO completed-bar
    filter — intraday passes rank and trade on a forming close.
  - qullamaggie: compute_features (base window, ATR, gap stats),
    stop-breach and trail checks all read bars[-1]; the spec is
    close-based ("trail breach at close vs 10MA").
  - morning_dip: indicators() is documented "on the last closed
    candle" but the served 3Min series includes the still-forming
    candle, so ER/ATR and the arm are computed on a partial candle.

Treatment (default ON): the wrapper trims, from a COPY of the view,
every bar that cannot be completed at the cycle's `now` — a 1Day bar
dated the current ET session (the desk's own convention, cf.
sleeves/momentum.py last_completed: a bar is completed iff its date <
session), and an intraday bar whose span has not closed
(start + timeframe > now). The strategy then sees exactly the
completed series its rules were written for. Switch OFF
(view.extra["<sleeve>_enh2"]["completed_bars"] = False, or
view.extra["enh2_completed_bars"] = False) restores the pre-change
rule exactly: the untrimmed view is served untouched and no shadow
runs.

Shadow control: with the switch ON, the sleeve is ALSO evaluated on
the untrimmed view inside a throwaway state dir; its intents are
never emitted, only summarized into a paired record stamped on each
treatment intent's "enhance_exp" (and returned when no treatment
intent exists, the record rides a trimmed-count-only stamp on the
first intent; when neither side emits, nothing is stamped).
"""
from __future__ import annotations

import copy
import os
import tempfile
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
EXP_ID = "ENH-CBAR-20261024"


def enh2_enabled(view, sleeve_id):
    extra = (view or {}).get("extra") or {}
    ov = extra.get(f"{sleeve_id}_enh2")
    if isinstance(ov, dict) and "completed_bars" in ov:
        return bool(ov["completed_bars"])
    if isinstance(extra.get("enh2_completed_bars"), bool):
        return bool(extra["enh2_completed_bars"])
    return True


def _epoch(t):
    try:
        return float(t)
    except (TypeError, ValueError):
        pass
    try:
        dt = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def _now_dt(view):
    now = (view or {}).get("now")
    if isinstance(now, datetime):
        dt = now
    else:
        dt = datetime.fromisoformat(str(now).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def trimmed_view(view, intraday_tf_s=None):
    """(view_copy, {bars_key: n_trimmed}) with un-completed bars cut."""
    now = _now_dt(view)
    now_ep = now.timestamp()
    session_date = now.astimezone(ET).date()
    out = dict(view or {})
    bars = dict((view or {}).get("bars") or {})
    trimmed = {}
    for key, rows in bars.items():
        if not isinstance(rows, list) or not rows:
            continue
        tf = key.rsplit("|", 1)[-1] if "|" in key else ""
        keep = []
        cut = 0
        for b in rows:
            ep = _epoch((b or {}).get("t"))
            if ep is None:
                keep.append(b)
                continue
            if tf == "1Day":
                if datetime.fromtimestamp(ep, tz=ET).date() == session_date:
                    cut += 1
                    continue
            elif intraday_tf_s and tf in intraday_tf_s:
                if ep + intraday_tf_s[tf] > now_ep:
                    cut += 1
                    continue
            keep.append(b)
        if cut:
            trimmed[key] = cut
            bars[key] = keep
    out["bars"] = bars
    return out, trimmed


def _summary(intents):
    return [{"kind": i.get("kind"), "symbol": i.get("symbol"),
             "qty": i.get("qty"),
             "px": i.get("limit_price") or i.get("price_hint")}
            for i in intents or []]


def run_enh2(sleeve_id, view, ctx, run_fn, intraday_tf_s=None):
    """run_fn(sleeve_id, view, ctx) is desk3.port_b5._ctx.run."""
    if not enh2_enabled(view, sleeve_id):
        return run_fn(sleeve_id, view, ctx)
    tview, trimmed = trimmed_view(view, intraday_tf_s)
    if not trimmed:
        return run_fn(sleeve_id, view, ctx)
    control = None
    if isinstance(ctx, dict):
        try:
            td = tempfile.mkdtemp(prefix="enh2_shadow_")
            cctx = dict(ctx)
            cctx["state_dir"] = td
            control = run_fn(sleeve_id, view, cctx)
        except Exception:
            control = None
    treatment = run_fn(sleeve_id, tview, ctx)
    rec = {"exp_id": EXP_ID, "sleeve": sleeve_id,
           "treatment": "completed_bars_only",
           "control": "untrimmed_view_incl_forming_bar",
           "trimmed": trimmed,
           "control_intents": _summary(control) if control is not None
                              else "shadow_unavailable",
           "treatment_intents": _summary(treatment)}
    for it in treatment or []:
        it["enhance_exp"] = {"exp_id": EXP_ID, "records": [rec]}
    return treatment
