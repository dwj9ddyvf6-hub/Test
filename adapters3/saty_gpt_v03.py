"""v3 sleeve module for saty_gpt_v03 — faithful port (batch 7).

Strategy + v2 adapter are byte-identical copies under sleeves/ and
adapters/ (hash-pinned by tests/test_port_b7_blockers.py). This module
is only the v3 worker entrypoint: evaluate(view, ctx) rebuilds the v2
SleeveContext from the cycle snapshot and delegates. The journal path
is set on the context so the v2 persisted-journal channel
(serve_journal / gpt_v02_journal) works across cycles.

CR6-RTH-SHAPE-20261114 (producer half of CR-6): the v2 data contract
served regular-session intraday bars; the v3 warm door serves the
extended-hours tape (04:00-19:55 ET) into the shared snapshot. The
strategy's FeatureBook accepts only bars fully inside a registered
regular session (core/saty_gpt_v03/structure.py) and raises on the
first bar outside it, so every RTH evaluation since 2026-10-26 died
in the book rebuild ("observation rejected (C-1/C-10)") before any
strategy logic ran; the C-3 "no valid day reference" stamp seen
out of hours is the same sleeve truthfully reporting that the day
reference's validity window is the session itself. The daily door
was never the defect (SPY|1Day builds 332 references, one covering
the live session). A second, deeper mismatch sits in the same
series: the strategy's 1H frame is session-aligned by design (its
own fallback builds hourly buckets from its 10m bars, anchored at
the 09:30 open; the book's calendar bridge and previous-session
carry both expect that alignment). Clock-hour 1H bars, even shaped
to the session, break the bridge at every overnight seam, the
indicator segment resets daily, and the 1H warmup count (1000)
can never accumulate. The adapter's own request caps close the
trap: it asks for 6000 5Min bars (~76 sessions), so the sleeve's
internal resample path tops out near 455 1H bars — under the v2
contract the 1H door itself (1500 bars requested) carried the
depth, session-aligned. Cure at this seam, following the CR-5
precedent (door bars shaped at the consumer) and the F4 precedent
(a missing frame supplied by honest resample of the served finer
tape at the consumer seam): the SPY 5Min/10Min series in this
sleeve's view are shaped to regular-session bars (09:30 ET open,
16:00 ET close or the shared early-close table), and the SPY
1Hour series is rebuilt session-aligned from the shaped 5Min
tape with the strategy's own bucketing rule (complete
09:30-anchored buckets only), over the full depth the warm door
now serves (desk3/warm.py SPY 5Min window widened 60 -> 300 days
for this install, ~215 sessions, ~1290 resampled 1H bars against
the pinned 1000-bar warmup). All on a copy — the snapshot is
shared and is never mutated. Daily and weekly series pass
through untouched; the shared warm product keeps serving the
extended tape and the clock-aligned 1Hour series to its other
consumers.
"""
import os
from datetime import datetime, time as dtime, timedelta, timezone
from zoneinfo import ZoneInfo

from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "saty_gpt_v03"
INPUTS = ['bars', 'quotes', 'options', 'session_fills']

_ET = ZoneInfo("America/New_York")
_OPEN = dtime(9, 30)
_TF_MINUTES = {"5Min": 5, "10Min": 10}
_SYMBOL = "SPY"


def _bar_start(row):
    t = row.get("t")
    if isinstance(t, (int, float)):
        return datetime.fromtimestamp(float(t), tz=timezone.utc)
    d = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d


def _in_regular_session(row, minutes):
    from core.data import is_trading_day
    from core.early_close import EARLY_CLOSES
    start = _bar_start(row).astimezone(_ET)
    d = start.date()
    if not is_trading_day(d):
        return False
    close = EARLY_CLOSES.get(d.isoformat(), dtime(16, 0))
    end = (start + timedelta(minutes=minutes)).time()
    return start.time() >= _OPEN and end <= close and end > start.time()


def _session_aligned_1h(shaped_5m_rows):
    """Session-aligned 1H bars resampled from RTH-shaped 5Min
    rows, using the strategy's own bucketing rule (complete
    09:30-anchored buckets only; incomplete buckets dropped,
    never filled). Returns snapshot-shaped bar dicts."""
    from sleeves.saty_gpt_v03 import _complete_buckets
    tuples = [(_bar_start(r).timestamp(), float(r["o"]), float(r["h"]),
               float(r["l"]), float(r["c"]), float(r.get("v", 0.0)))
              for r in shaped_5m_rows]
    out = []
    for b in _complete_buckets(tuples, 60):
        t = datetime.fromtimestamp(b[0], tz=timezone.utc)
        out.append({"t": t.isoformat().replace("+00:00", "Z"),
                    "o": b[1], "h": b[2], "l": b[3], "c": b[4],
                    "v": b[5]})
    return out


def _rth_shaped_view(view):
    """Copy of `view` with the SPY intraday bar series this sleeve
    consumes shaped to its data contract: 5Min/10Min shaped to
    regular-session bars, and the 1Hour series rebuilt
    session-aligned from the shaped 5Min tape (withheld empty
    when no complete hourly bucket exists). Returns the original
    object when nothing needs shaping (weekend/empty views keep
    their identity)."""
    bars = (view or {}).get("bars")
    if not isinstance(bars, dict):
        return view
    new_bars = None

    def _put(key, rows):
        nonlocal new_bars
        if new_bars is None:
            new_bars = dict(bars)
        new_bars[key] = rows

    shaped_5m = None
    for key, rows in bars.items():
        sym, sep, tf = key.rpartition("|")
        if not sep or sym != _SYMBOL or tf not in _TF_MINUTES:
            continue
        if not isinstance(rows, list) or not rows:
            continue
        shaped = [r for r in rows
                  if _in_regular_session(r, _TF_MINUTES[tf])]
        if tf == "5Min":
            shaped_5m = shaped
        if len(shaped) != len(rows):
            _put(key, shaped)
    key_1h = f"{_SYMBOL}|1Hour"
    if key_1h in bars:
        rebuilt = _session_aligned_1h(shaped_5m) \
            if shaped_5m else []
        if rebuilt != bars.get(key_1h):
            _put(key_1h, rebuilt)
    if new_bars is None:
        return view
    out = dict(view)
    out["bars"] = new_bars
    return out


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, _rth_shaped_view(view), ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return importlib.import_module("adapters.saty_gpt_v03").evaluate(sctx) or []
