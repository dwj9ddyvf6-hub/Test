"""v3 sleeve module for em_1587 — faithful port (batch 2).

Strategy + v2 adapter are byte-identical copies under sleeves/ and
adapters/ (hash-pinned by tests/test_port_batch2_blockers.py). This
module is only the v3 worker entrypoint: evaluate(view, ctx) rebuilds
the v2 SleeveContext from the cycle snapshot and delegates.

EXPECTED-MOVE-FILING-20261030 (deep-dive defect 3 cure):

1. Feed contract. The sleeve's declared input was the bare key
   "extra", which no live producer emits (the batch-2 declaration
   imagined a producer publishing a snapshot "extra" channel; the
   live desk never registered one), so the registry marked the
   sleeve UNFED forever. The sleeve's real external dependency is
   the VIX daily series, which the live VixProducer already emits
   under its own true names: the scalar "vix" and the literal
   "bars:VIX:1Day" rows. INPUTS below declares exactly those
   (the t_cci_corr pattern), and evaluate() translates the literal
   VIX rows into the extra["vix_series"] channel the v2 adapter
   reads. No "extra" producer was added: that would be a second
   source of truth for data the VIX producer already carries.

2. Filing bridge. In the old desk, every em_1587 evaluation's
   sleeve_stamp (with its expected-move map) was filed into the
   permanent ledger the Expected Move Map page reads
   (femto-lean/state/ledger.jsonl). The v3 port discarded the
   stamp (the strategy module's signal() builds a throwaway
   instance per call), so the filing lane went dark at the desk
   migration. This entrypoint wraps that module-level signal so
   the stamp survives the call (the same capture the port4 bridge
   performs by running the class directly), and appends ONE tick
   row per distinct (session, map) to the same permanent ledger,
   at evaluation time, with the evaluation's own timestamp.
   Forward accrual only: the bridge never writes a row for a
   session it did not evaluate, and it files only for live
   pool evaluations (the ctx carries the cycle's
   snapshot_hash); fixture and test drives never file. Filing
   is fail-soft: a filing error is journaled and never breaks
   the evaluation.
"""
import hashlib
import json
import os
from datetime import datetime, timezone

from adapters3._snapshot_ctx import evaluate_ported

SLEEVE_ID = "em_1587"
INPUTS = ["bars", "positions", "options", "vix", "bars:VIX:1Day"]

# The permanent filing log the Expected Move Map refresh reads.
# Exactly one filing path exists: this bridge, at evaluation time.
# WORKER-HOME-FILING-20261110: the path is anchored to this file's
# own tree, never to the process HOME. Desk workers run with HOME
# set to the desk state root by design (pool.py), so the old
# expanduser form resolved into a shadow ledger under
# state/workspace/ and every filing from 2026-11-02 onward landed
# there while the permanent log stayed frozen at 2026-11-04.
_DESK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WORKSPACE_ROOT = os.path.dirname(_DESK_ROOT)
FILING_LOG_PATH = os.path.join(
    _WORKSPACE_ROOT, "femto-lean", "state", "ledger.jsonl")
_FILING_STATE_NAME = "expected_move_filing.json"

_LAST_STAMP = {}


def _capture_stamp_once():
    """Wrap sleeves.em_1587.signal so the per-call instance's
    last_evaluation stamp survives. The module-level signal is
    literally `return Em1587().signal(...)`; the wrapper performs
    the identical call on its own instance and keeps the stamp."""
    try:
        import sleeves.em_1587 as strat

        if getattr(strat.signal, "_em_filing_capture", False):
            return
        cls = strat.Em1587

        def _capturing_signal(bars, slice_state, context):
            inst = cls()
            out = inst.signal(bars, slice_state, context)
            stamp = getattr(inst, "last_evaluation", None)
            if isinstance(stamp, dict) and stamp:
                _LAST_STAMP.clear()
                _LAST_STAMP.update(stamp)
            return out

        _capturing_signal._em_filing_capture = True
        strat.signal = _capturing_signal
    except Exception:
        pass


def _with_vix_series(view):
    """Translate the snapshot's literal VIX daily rows into the
    extra["vix_series"] channel the v2 adapter consumes. Returns
    a shallow-copied view; the frozen snapshot is never mutated.
    An explicit vix_series already on the view wins."""
    try:
        rows = (view or {}).get("bars:VIX:1Day") or []
        if not rows:
            return view
        extra = dict((view or {}).get("extra") or {})
        if extra.get("vix_series"):
            return view
        series = []
        for r in rows:
            try:
                series.append((str(r["t"])[:10], float(r["c"])))
            except (KeyError, TypeError, ValueError):
                continue
        if not series:
            return view
        extra["vix_series"] = series
        out = dict(view)
        out["extra"] = extra
        return out
    except Exception:
        return view


def _journal(ctx, event, **fields):
    try:
        from runtime.journal import append_line
        state_dir = (ctx or {}).get("state_dir")
        if state_dir:
            append_line(os.path.join(state_dir, "journal.jsonl"),
                        {"event": event, "sleeve": SLEEVE_ID, **fields})
    except Exception:
        pass


def _file_stamp(view, ctx, stamp):
    """Append this evaluation's map to the permanent filing log,
    once per distinct (session, map). Returns a status word."""
    m = stamp.get("map")
    session = stamp.get("session")
    if not m or not session:
        return "no_map"
    map_key = hashlib.sha256(json.dumps(
        m, sort_keys=True, default=str).encode()).hexdigest()
    state_dir = (ctx or {}).get("state_dir") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "state", SLEEVE_ID)
    state_path = os.path.join(state_dir, _FILING_STATE_NAME)
    try:
        with open(state_path, "r", encoding="utf-8") as fh:
            last = json.load(fh)
    except Exception:
        last = {}
    if last.get("session") == session and last.get("map_key") == map_key:
        return "already_filed"
    now_raw = (view or {}).get("now")
    try:
        now_dt = datetime.fromisoformat(
            str(now_raw).replace("Z", "+00:00"))
        if now_dt.tzinfo is None:
            now_dt = now_dt.replace(tzinfo=timezone.utc)
        epoch = now_dt.timestamp()
    except (TypeError, ValueError):
        return "no_clock"
    bars = (view or {}).get("bars") or {}
    row = {
        "kind": "tick",
        "session": session,
        "now": epoch,
        "source_desk": "muse-desk-v3",
        "filing": "filed_at_time",
        "evaluations": {
            SLEEVE_ID: {
                "bars_served": {
                    sym: len(bars.get(f"{sym}|5Min") or [])
                    for sym in ("SPY", "QQQ")},
                "sleeve_stamp": stamp,
            }
        },
    }
    os.makedirs(os.path.dirname(FILING_LOG_PATH), exist_ok=True)
    with open(FILING_LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True, default=str) + "\n")
    try:
        os.makedirs(state_dir, exist_ok=True)
        with open(state_path, "w", encoding="utf-8") as fh:
            json.dump({"session": session, "map_key": map_key,
                       "filed_at_utc": now_dt.isoformat()}, fh)
    except Exception:
        pass
    return "filed"


def evaluate(view, ctx):
    from desk3.enhance14 import filter_entries
    _capture_stamp_once()
    _LAST_STAMP.clear()
    view = _with_vix_series(view)
    out = filter_entries(SLEEVE_ID, evaluate_ported(
        SLEEVE_ID, view, ctx), view)
    # Live evaluations only: a pool task carries the cycle's
    # snapshot_hash; fixture and test drives do not, and must
    # never file into the permanent log (a fixture drive's map
    # is not a filed map).
    if _LAST_STAMP and (ctx or {}).get("snapshot_hash"):
        try:
            status = _file_stamp(view, ctx, dict(_LAST_STAMP))
            _journal(ctx, "expected_move_filing", status=status,
                     session=_LAST_STAMP.get("session"))
        except Exception as exc:  # filing never breaks evaluation
            _journal(ctx, "expected_move_filing",
                     status=f"error:{type(exc).__name__}:{exc}",
                     session=_LAST_STAMP.get("session"))
    return out
