#!/usr/bin/env python3
"""Refresh the Own-Norm Depth Forecaster (Forecast Engine 3).

=====================================================================
CANDIDATE-REGISTER TRIPLE (written before any computation, per the
lineup's adopted standards)

1. EVIDENCE CLASS
   The strongest directional survivor in the corpus's graded
   evidence record, grade B: the own-norm pullback study (row S1 of
   terminal-lineup/records/forecast-search-2026-10-27/EVIDENCE.md).
   In rising-trend names on fear days, ranking by how deep today's
   pullback is against the stock's own norm tracked the next 20
   sessions' move against the market with rank correlation +0.026
   (strength 4.3) in 2016-2022 and +0.031 (strength 4.3) in 2023
   onward; at 60 sessions in 2023 onward, +0.062 (strength 9.8).
   The 2023-onward spread between the deepest fifth and the
   shallowest fifth was +0.81 points of 20-session excess return.
   One dataset family only (the long daily price history, 2016 to
   2026, 6,385 names including delisted ones), explicitly unproven
   forward. This engine's own live record: none yet; it starts
   here, and it starts empty for the reason stated below.

2. RECONSTRUCTION CHOICES (every constant, named before computing)
   - Depth: (the name's highest close of the last 63 sessions,
     today included, minus today's close), divided by the name's
     own median true range over the trailing 750 sessions ending
     yesterday. True range is the largest of (high minus low),
     (high minus yesterday's close), (low minus yesterday's
     close), in price points.
   - Own-history percentile: today's depth ranked against the
     name's own depth values on the trailing 750 sessions ending
     yesterday (each of those depths computed the same way, from
     data up to its own day). Leave-today-out: today's depth is
     never part of its own comparison set. Percentile = 100 x
     (share of those 750 depths strictly below today's).
   - Rising trend (the study's own label is "uptrend (UP) names";
     its exact coded rule is not readable from any file on this
     disk, as the Pullback Norm build established, so this is a
     stated reconstruction): today's close is above the average
     of the last 200 closes, today included.
   - The curve: percentile is split into ten equal bins (0-10,
     10-20, ..., 90-100). In each bin, over fitting events only:
     the share whose 20-session excess return against SPY was
     positive, and the middle (median) 20-session excess return.
     Both series are then made monotone (never falling as depth
     percentile rises) with a weighted pool-adjacent-violators
     smoothing, weighted by bin counts. A live forecast reads its
     bin's two smoothed numbers. Fitting events are rising-trend
     name-days in the fit era only.
   - Fit era: 2016-01-01 to 2022-12-31, and nothing else. The
     curve is frozen the moment it is fitted and is never
     refitted on newer data; the fitted bin table is written
     into data.json so every printed number can be checked
     against it.
   - Out-of-sample era: 2023-01-01 onward, the era the curve
     never saw. Published as history only: coverage (share of
     graded events), the probability score (average squared
     distance between the stated chance and what happened), the
     middle error on the point forecast, and the spread between
     the deepest fifth's and the shallowest fifth's middle
     excess returns. Beside it, the control the picker standard
     requires: the same names on the same days, entered at a
     depth percentile drawn at random (fixed seed 20261028, so
     the control is reproducible), scored the same way.
   - Fear-day sub-forecast: a fear day is a session SPY fell at
     least 1 percent (the corpus's own fear-day meaning). The
     sub-forecast is the same curve fitted on fear-day fitting
     events only. It ships only if the fit era holds at least
     30 fear-day events in at least 8 of the 10 bins; otherwise
     it is stated absent, never faked.
   - Exclusion rule: a name is forecast only when its own
     history can supply the full comparison set (750 prior
     depths, which itself needs the 63-session high and the
     true-range window behind it) plus the 200-session average.
     A name short of that is excluded and counted, never
     approximated with a shorter window.
   - Ledger shape: one forecast per qualifying name per issue
     day, carrying both numbers in one value:
     {"p": chance the 20-session excess return is positive,
      "estimate": predicted median excess return, in points}.
     The outcome spec is kind "excess_sign" against SPY
     (RC-19 cure, 2026-10-30): the shared grading pass resolves
     both legs from the same price source and grades the chance
     on the sign of the excess. Horizon dates come from the
     forward session calendar on record
     (forecast/session_calendar.py, RC-04 cure, 2026-10-30),
     so a qualifying name issues on the day it qualifies instead
     of fail closing for lack of a calendar. The registered
     grading rule for this engine is the probability score.
   - Thin-cell rule: any cell with fewer than 30 graded cases
     shows its count only, no score and no rate.
   - Panels: the long daily price history (2016-2026) the study
     ran on is NOT on this disk. The Pullback Norm build proved
     that by search, and this build re-checked: no such file
     exists in the workspace. The shipped daily history on disk
     (~/workspace/morgue/data_cache/board_bt_bars.json, 1,833
     names, at most 399 sessions each, 2025-03-25 to 2026-10-23)
     is the live feed the design names, and it is too short for
     the 750-session comparison set for every name in it.
     Consequence, stated plainly rather than worked around: the
     curve cannot be fitted, the out-of-sample run cannot be
     computed, and no name qualifies for a live forecast today.
     This script therefore publishes the engine in that true
     state, with the full computation wired so that the first
     run after a long panel reaches this disk fits, evaluates
     and forecasts for real. Shortening the 750-session window
     to fit the short history was considered and rejected: it
     would silently change the forecast being tested.

3. NON-CLAIMS
   - No fitted curve, no out-of-sample score, and no live
     forecast is claimed today, because the data they need is
     not on this disk; the counts proving that are published.
   - The earlier study's figures are that study's record, shown
     labelled as history; they are not this engine's results.
   - The sharp claim (deepest fifth beats shallowest fifth by
     at least 0.8 points of middle excess return at 20 sessions)
     is the claim under test, not a result. It matches the
     earlier study's 2023-onward spread of +0.81 points.
   - Nothing from any history computation is ever written to
     the live ledger. Only live forecasts for qualifying names
     are ledgered, through the machinery's own append call.

=====================================================================
Behaviour: check the panels (fails closed on any disagreement),
fit and evaluate only if a long panel is present, compute today's
qualifying names from the shipped daily history, ledger any live
forecasts through forecast/ledger.py append_forecast (never
hand-edited), then write data.json from the panels plus figures
recomputed from the ledger alone. Idempotent: rerunning with the
same panels appends nothing and rewrites the same data.json.
Timestamps come from the sources, never the clock.
"""

import bisect
import json
import math
import os
import random
import re
import sys
from statistics import median

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(HERE)
LIVE_PANEL_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")
DEEP_PANEL_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/deep_bars.json")
OUT_PATH = os.path.join(HERE, "own-norm-depth", "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import attestation_block as _ab
except ImportError:  # refresh stays runnable standalone
    _ab = None

sys.path.insert(0, LINEUP)
from forecast import ledger as ledger_mod  # noqa: E402
from forecast import registry as registry_mod  # noqa: E402
from forecast import session_calendar as calendar_mod  # noqa: E402

ENGINE_ID = "engine_03"
HIGH_WINDOW = 63          # sessions, today included
TR_WINDOW = 750           # trailing sessions ending yesterday
PCT_WINDOW = 750          # trailing own depths ending yesterday
TREND_WINDOW = 200        # sessions, today included
HORIZON = 20              # sessions
FIT_START, FIT_END = "2016-01-01", "2022-12-31"
OOS_START = "2023-01-01"
BINS = 10
BIN_WIDTH = 100.0 / BINS
THIN = 30
FEAR_DROP = -0.01         # SPY one-session return at or below this
CONTROL_SEED = 20261028
CLAIM_SPREAD_POINTS = 0.8

# Sessions a name needs before its first possible forecast day:
# 750 prior depths; the oldest of those depths itself needs 62
# earlier closes for its high and a true range behind it, and
# the trend average needs 200 closes. The binding floor is the
# depth-history chain.
MIN_SESSIONS = PCT_WINDOW + HIGH_WINDOW  # 813


def fail(msg):
    print(f"Own-Norm Depth refresh: {msg}", file=sys.stderr)
    return 1


# ---- pure computation (window sizes are parameters so the math
# ---- can be exercised on short synthetic histories in tests) ----
def true_ranges(rows):
    """rows: [date, o, h, l, c, v]. Returns TR list aligned to rows
    (None at index 0)."""
    out = [None]
    for i in range(1, len(rows)):
        h, l, pc = rows[i][2], rows[i][3], rows[i - 1][4]
        out.append(max(h - l, abs(h - pc), abs(l - pc)))
    return out


def depth_series(rows, high_window=HIGH_WINDOW, tr_window=TR_WINDOW):
    """Depth per index: (highest close of the last high_window
    sessions incl. today - today's close) / median true range over
    the tr_window sessions ending yesterday. None where the inputs
    do not exist yet."""
    closes = [float(r[4]) for r in rows]
    trs = true_ranges(rows)
    n = len(rows)
    depths = [None] * n
    for i in range(n):
        if i - high_window + 1 < 0 or i - tr_window < 1:
            continue
        window_tr = trs[i - tr_window:i]
        if any(t is None for t in window_tr):
            continue
        med_tr = median(window_tr)
        if med_tr <= 0:
            continue
        hi = max(closes[i - high_window + 1:i + 1])
        depths[i] = (hi - closes[i]) / med_tr
    return depths


def percentile_of(value, sorted_prior):
    """100 x share of prior values strictly below value."""
    if not sorted_prior:
        return None
    return 100.0 * bisect.bisect_left(sorted_prior, value) / len(sorted_prior)


def depth_percentiles(rows, pct_window=PCT_WINDOW, **kw):
    """Own-history percentile per index, leave-today-out: index i
    is ranked against depths[i-pct_window:i]."""
    depths = depth_series(rows, **kw)
    n = len(rows)
    out = [None] * n
    for i in range(n):
        if depths[i] is None or i - pct_window < 0:
            continue
        prior = depths[i - pct_window:i]
        if any(d is None for d in prior):
            continue
        out[i] = percentile_of(depths[i], sorted(prior))
    return depths, out


def in_uptrend(rows, i, trend_window=TREND_WINDOW):
    if i - trend_window + 1 < 0:
        return False
    closes = [float(r[4]) for r in rows[i - trend_window + 1:i + 1]]
    return float(rows[i][4]) > sum(closes) / len(closes)


def excess_return(rows, spy_by_date, i, horizon=HORIZON):
    """20-session excess return in percentage points, or None."""
    if i + horizon >= len(rows):
        return None
    d0, d1 = rows[i][0], rows[i + horizon][0]
    if d0 not in spy_by_date or d1 not in spy_by_date:
        return None
    own = float(rows[i + horizon][4]) / float(rows[i][4]) - 1.0
    spy = spy_by_date[d1] / spy_by_date[d0] - 1.0
    return (own - spy) * 100.0


def pava_monotone(values, weights):
    """Weighted pool-adjacent-violators: the closest non-decreasing
    fit to values. Returns a list the same length."""
    blocks = []  # [weighted_mean, total_weight, count]
    for v, w in zip(values, weights):
        blocks.append([float(v), float(w), 1])
        while len(blocks) >= 2 and blocks[-2][0] > blocks[-1][0]:
            top = blocks.pop()
            prev = blocks.pop()
            wsum = prev[1] + top[1]
            blocks.append([(prev[0] * prev[1] + top[0] * top[1]) / wsum,
                           wsum, prev[2] + top[2]])
    out = []
    for mean, _w, cnt in blocks:
        out.extend([mean] * cnt)
    return out


def bin_index(pct):
    return min(int(pct // BIN_WIDTH), BINS - 1)


def fit_curve(events):
    """events: [(percentile, excess_points)]. Returns the frozen
    bin table with raw and monotone-smoothed values."""
    bins = [[] for _ in range(BINS)]
    for pct, exc in events:
        bins[bin_index(pct)].append(exc)
    table = []
    for b, vals in enumerate(bins):
        if vals:
            table.append({
                "bin": b,
                "pct_low": b * BIN_WIDTH, "pct_high": (b + 1) * BIN_WIDTH,
                "events": len(vals),
                "share_positive": sum(1 for v in vals if v > 0) / len(vals),
                "median_excess_points": median(vals),
            })
        else:
            table.append({
                "bin": b,
                "pct_low": b * BIN_WIDTH, "pct_high": (b + 1) * BIN_WIDTH,
                "events": 0, "share_positive": None,
                "median_excess_points": None})
    filled = [t for t in table if t["events"] > 0]
    if filled:
        sp = pava_monotone([t["share_positive"] for t in filled],
                           [t["events"] for t in filled])
        me = pava_monotone([t["median_excess_points"] for t in filled],
                           [t["events"] for t in filled])
        for t, p, m in zip(filled, sp, me):
            t["p"] = round(min(max(p, 0.01), 0.99), 4)
            t["estimate"] = round(m, 3)
    return table


def forecast_from_curve(table, pct):
    t = table[bin_index(pct)]
    if t.get("p") is None:
        return None
    return {"p": t["p"], "estimate": t["estimate"]}


def evaluate(events, table, rng):
    """events: [(percentile, excess_points)] from the era the curve
    never saw. Returns graded figures plus the random-entry
    control scored on the same events."""
    graded = []
    for pct, exc in events:
        f = forecast_from_curve(table, pct)
        if f is not None:
            graded.append((pct, exc, f))
    out = {"graded": len(graded)}
    if graded:
        out["share_positive"] = round(
            sum(1 for _p, e, _f in graded if e > 0) / len(graded), 4)
        out["brier"] = round(
            sum((f["p"] - (1.0 if e > 0 else 0.0)) ** 2
                for _p, e, f in graded) / len(graded), 4)
        out["median_abs_error_points"] = round(median(
            [abs(f["estimate"] - e) for _p, e, f in graded]), 3)
        deep = [e for p, e, _f in graded if p >= 80.0]
        shallow = [e for p, e, _f in graded if p < 20.0]
        out["deepest_fifth"] = {"events": len(deep),
                                "median_excess_points":
                                round(median(deep), 3) if deep else None}
        out["shallowest_fifth"] = {"events": len(shallow),
                                   "median_excess_points":
                                   round(median(shallow), 3) if shallow else None}
        if deep and shallow:
            out["quintile_spread_points"] = round(
                median(deep) - median(shallow), 3)
    ctrl = []
    for _pct, exc in events:
        f = forecast_from_curve(table, rng.uniform(0.0, 100.0))
        if f is not None:
            ctrl.append((exc, f))
    control = {"graded": len(ctrl)}
    if ctrl:
        control["brier"] = round(
            sum((f["p"] - (1.0 if e > 0 else 0.0)) ** 2
                for e, f in ctrl) / len(ctrl), 4)
        control["median_abs_error_points"] = round(median(
            [abs(f["estimate"] - e) for e, f in ctrl]), 3)
    out["control_random_entries"] = control
    return out


try:
    from deep_panel_reader import DeepPanelReader
except ImportError:  # shared reader missing: fall back to the
    DeepPanelReader = None  # local StreamedPanel below


def depth_percentiles_fast(rows, high_window=HIGH_WINDOW,
                           tr_window=TR_WINDOW, pct_window=PCT_WINDOW):
    """depth_percentiles() computed incrementally, bit-identical.

    Cure (DEEP runtime, 2026-10-30): the reference recomputes a
    statistics.median over a fresh 750-value sort, a 63-close max
    and a fresh sort of 750 prior depths at EVERY index, which
    measured 2.1 to 6.3 s per long name (AAPL, SPY, A) and put a
    full two-era pass at many hours. Here each window is
    maintained incrementally: the true-range window and the
    prior-depth window as sorted lists updated by bisect, the
    63-close high as a monotonic deque. Median and percentile
    keep the reference definitions exactly (median of the same
    multiset; bisect_left share strictly below), so outputs are
    identical, verified against the reference on synthetic
    histories and on real panel names in
    forecast/tests/test_deep_runtime_20261030.py. Measured after:
    0.01 to 0.11 s per long name."""
    import bisect as _b
    from collections import deque as _dq
    n = len(rows)
    closes = [float(r[4]) for r in rows]
    trs = [None] * n
    for i in range(1, n):
        h, l, pc = float(rows[i][2]), float(rows[i][3]), closes[i - 1]
        trs[i] = max(h - l, abs(h - pc), abs(l - pc))
    depths = [None] * n
    sorted_tr = []
    hi_deque = _dq()
    for i in range(n):
        while hi_deque and closes[hi_deque[-1]] <= closes[i]:
            hi_deque.pop()
        hi_deque.append(i)
        while hi_deque and hi_deque[0] < i - high_window + 1:
            hi_deque.popleft()
        add = i - 1
        if add >= 1:
            _b.insort(sorted_tr, trs[add])
        rem = i - tr_window - 1
        if rem >= 1:
            del sorted_tr[_b.bisect_left(sorted_tr, trs[rem])]
        if i - high_window + 1 < 0 or i - tr_window < 1:
            continue
        if len(sorted_tr) != tr_window:
            continue
        m = len(sorted_tr)
        med = sorted_tr[m // 2] if m % 2 else \
            (sorted_tr[m // 2 - 1] + sorted_tr[m // 2]) / 2.0
        if med <= 0:
            continue
        depths[i] = (closes[hi_deque[0]] - closes[i]) / med
    out = [None] * n
    sorted_prior = []
    for i in range(n):
        add = i - 1
        if add >= 0 and depths[add] is not None:
            _b.insort(sorted_prior, depths[add])
        rem = i - pct_window - 1
        if rem >= 0 and depths[rem] is not None:
            del sorted_prior[_b.bisect_left(sorted_prior, depths[rem])]
        if depths[i] is None or i - pct_window < 0:
            continue
        if len(sorted_prior) != pct_window:
            continue
        out[i] = 100.0 * _b.bisect_left(
            sorted_prior, depths[i]) / len(sorted_prior)
    return depths, out


EVENTS_CACHE_DIR = os.path.expanduser(
    "~/workspace/morgue/data_cache/ownnorm_cache")


def panel_fingerprint(path):
    st = os.stat(path)
    return f"{os.path.basename(path)}:{st.st_size}:{st.st_mtime_ns}"


def events_cache_dir(cache_root, fingerprint):
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", fingerprint)
    return os.path.join(cache_root, safe)


def _read_events_checkpoint(path):
    """{symbol: (events, fear_events)} already collected for this
    panel fingerprint. A torn final line is ignored, never fatal:
    that symbol is simply recollected."""
    done = {}
    if not path or not os.path.exists(path):
        return done
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                done[str(rec["symbol"])] = (
                    [tuple(e) for e in rec["events"]],
                    [tuple(e) for e in rec["fear_events"]])
            except (ValueError, KeyError, TypeError):
                continue
    return done


def collect_events(panel, spy_rows, start, end, fear_days=None,
                   checkpoint_path=None):
    """Stream the panel name by name (never held whole beyond one
    name's rows plus SPY). Returns (events, fear_events).

    Checkpoint cache (cure G17 remainder, 2026-10-30): the two
    era passes over the DEEP panel are multi-hour and a killed
    run previously lost everything (the 2026-10-30 fit died with
    an empty log and an unwritten page). With checkpoint_path,
    each symbol's events are appended to that file as they are
    collected and a re-run for the same panel fingerprint reuses
    them in the same sorted order, so the returned event sequence
    is identical to an uninterrupted run; the computation and
    the forecast under test are unchanged."""
    spy_by_date = {r[0]: float(r[4]) for r in spy_rows}
    done = _read_events_checkpoint(checkpoint_path)
    fh = open(checkpoint_path, "a", encoding="utf-8") \
        if checkpoint_path else None
    events, fear_events = [], []
    try:
        for sym in sorted(panel):
            if sym == "SPY":
                continue
            if sym in done:
                sym_events, sym_fear = done[sym]
                events.extend(sym_events)
                fear_events.extend(sym_fear)
                continue
            rows = panel[sym]
            _depths, pcts = depth_percentiles_fast(rows)
            sym_events, sym_fear = [], []
            for i, pct in enumerate(pcts):
                if pct is None:
                    continue
                d = rows[i][0]
                if not (start <= d <= end):
                    continue
                if not in_uptrend(rows, i):
                    continue
                exc = excess_return(rows, spy_by_date, i)
                if exc is None:
                    continue
                sym_events.append((pct, exc))
                if fear_days is not None and d in fear_days:
                    sym_fear.append((pct, exc))
            events.extend(sym_events)
            fear_events.extend(sym_fear)
            if fh is not None:
                fh.write(json.dumps(
                    {"symbol": sym, "events": sym_events,
                     "fear_events": sym_fear}) + "\n")
                fh.flush()
    finally:
        if fh is not None:
            fh.close()
    return events, fear_events


class StreamedPanel:
    """Lazy per-symbol view over a panel JSON file, in the
    {symbol: [[date, o, h, l, c, v], ...]} shape. Loading the
    DEEP panel whole with json.load built several GB of row
    lists and was OOM killed on this box in the 2026-10-30
    refresh proof run (on the 413 MB panel; the landed panel
    is 1,046 MB). This view keeps the file text and a symbol
    offset index, and parses exactly one symbol's rows per
    access, discarding them afterwards: the same pattern
    refresh_proofgate.py proved on this panel, and the shape
    collect_events already assumes (it streams the panel name
    by name). Row values are identical to json.load's; only
    the residency differs. Nothing is cached, so repeated
    access re-parses that one symbol only."""

    def __init__(self, path):
        with open(path, "r", encoding="utf-8") as fh:
            self._text = fh.read()
        self._offsets = {}
        for match in re.finditer(r'"([^"]+)": \[', self._text):
            self._offsets[match.group(1)] = match.end() - 1
        self._decoder = json.JSONDecoder()

    def __contains__(self, sym):
        return sym in self._offsets

    def __len__(self):
        return len(self._offsets)

    def __iter__(self):
        return iter(self._offsets)

    def keys(self):
        return self._offsets.keys()

    def __getitem__(self, sym):
        rows, _end = self._decoder.raw_decode(
            self._text, self._offsets[sym])
        return rows

    def items(self):
        for sym in self._offsets:
            yield sym, self[sym]


def build():
    if not os.path.exists(LIVE_PANEL_PATH):
        return fail(f"live price history not found: {LIVE_PANEL_PATH}")
    with open(LIVE_PANEL_PATH, "r", encoding="utf-8") as fh:
        live_panel = json.load(fh)

    # ---- Validate the shipped daily history (fails closed) ----
    if "SPY" not in live_panel:
        return fail("the shipped daily history carries no SPY")
    spy_rows = live_panel["SPY"]
    spy_dates = [r[0] for r in spy_rows]
    if spy_dates != sorted(spy_dates) or len(set(spy_dates)) != len(spy_dates):
        return fail("SPY dates in the shipped history are not a clean "
                    "increasing session list")
    as_of = spy_dates[-1]
    span = (spy_dates[0], as_of)
    name_count = len(live_panel)
    lengths = {sym: len(rows) for sym, rows in live_panel.items()}
    max_len = max(lengths.values())

    # ---- Live qualification under the exclusion rule ----
    qualifying = sorted(sym for sym, n in lengths.items()
                        if n >= MIN_SESSIONS and sym != "SPY")
    excluded = name_count - len(qualifying) - 1  # every name but SPY
    excluded_too_short = sum(1 for sym, n in lengths.items()
                             if sym != "SPY" and n < MIN_SESSIONS)
    if excluded != excluded_too_short:
        return fail("exclusion count disagreement inside the shipped "
                    "history")

    # ---- Long panel: fit + out-of-sample, only if it is on disk ----
    deep_present = os.path.exists(DEEP_PANEL_PATH)
    curve = {"state": "not_fitted",
             "reason": ("The long daily price history this engine is "
                        "fitted on (2016 to 2026) is not on this "
                        "computer, so no curve has been fitted. The "
                        "method below is fixed in advance and runs "
                        "unchanged the first time that history is "
                        "present."),
             "method": ("Ten equal depth-percentile bins; in each "
                        "bin, the share of fitting events whose next "
                        "20 sessions beat SPY and the middle excess "
                        "return; both series smoothed so they never "
                        "fall as pullbacks get deeper; fitted only "
                        "on 2016 to 2022 and then frozen."),
             "fit_era": "2016-01-01 to 2022-12-31",
             "bins": []}
    oos = {"state": "not_run",
           "reason": ("No fitted curve exists yet, and the era it "
                      "would be tested on (2023 onward) is part of "
                      "the same long history that is not on this "
                      "computer."),
           "era": "2023-01-01 onward", "graded": 0}
    fear = {"state": "absent",
            "reason": ("The fear-day version is the same curve "
                       "fitted on fear days only (days SPY fell at "
                       "least 1 percent). Without the long history "
                       "there are no fear-day fitting events to fit "
                       "it on, so it is not published. It is never "
                       "filled in from the all-days curve.")}
    live_forecasts = []
    reader_strategy = None

    if deep_present:
        # Shared mmap reader (DEEP runtime cure, 2026-10-30): the
        # local StreamedPanel held the whole panel text resident
        # (2,005 MB peak, 107 s init); DeepPanelReader serves the
        # same rows from the binary derived store or an mmap of
        # the JSON with a persisted offset sidecar, at a few
        # hundred MB and sub-second init. StreamedPanel remains
        # as the fallback when the shared module is unavailable.
        deep = DeepPanelReader(DEEP_PANEL_PATH) \
            if DeepPanelReader is not None else StreamedPanel(DEEP_PANEL_PATH)
        reader_strategy = getattr(deep, "strategy", None)
        if "SPY" not in deep:
            return fail("the long history carries no SPY")
        dspy = deep["SPY"]
        if not (dspy[0][0] <= FIT_START and dspy[-1][0] >= OOS_START):
            return fail("the long history does not span both the "
                        "fit era and the out-of-sample era")
        fear_days = set()
        for i in range(1, len(dspy)):
            if float(dspy[i][4]) / float(dspy[i - 1][4]) - 1.0 <= FEAR_DROP:
                fear_days.add(dspy[i][0])
        cache_dir = events_cache_dir(
            EVENTS_CACHE_DIR, panel_fingerprint(DEEP_PANEL_PATH))
        os.makedirs(cache_dir, exist_ok=True)
        fit_events, fit_fear = collect_events(
            deep, dspy, FIT_START, FIT_END, fear_days,
            checkpoint_path=os.path.join(
                cache_dir, f"fit_{FIT_START}_{FIT_END}.jsonl"))
        table = fit_curve(fit_events)
        if any(t["events"] for t in table):
            curve = {"state": "fitted_frozen",
                     "fit_era": "2016-01-01 to 2022-12-31",
                     "fit_events": len(fit_events),
                     "method": curve["method"], "bins": table}
            rng = random.Random(CONTROL_SEED)
            oos_events, _ = collect_events(
                deep, dspy, OOS_START, dspy[-1][0],
                checkpoint_path=os.path.join(
                    cache_dir, f"oos_{OOS_START}.jsonl"))
            oos = dict(evaluate(oos_events, table, rng),
                       state="computed", era="2023-01-01 onward")
            fbins = sum(1 for t in fit_curve(fit_fear) if t["events"] > 0)
            if len(fit_fear) >= THIN and fbins >= 8:
                fear = {"state": "published",
                        "fit_events": len(fit_fear),
                        "bins": fit_curve(fit_fear)}
        del deep

    # ---- Live forecasts for qualifying names (none can qualify
    # ---- until a history of 813+ sessions per name exists) ----
    if curve["state"] == "fitted_frozen" and qualifying:
        spy_by_date = {r[0]: float(r[4]) for r in spy_rows}
        for sym in qualifying:
            rows = live_panel[sym]
            _d, pcts = depth_percentiles(rows)
            pct = pcts[-1]
            if pct is None or not in_uptrend(rows, len(rows) - 1):
                continue
            f = forecast_from_curve(curve["bins"], pct)
            if f is None:
                continue
            live_forecasts.append({
                "symbol": sym, "depth_percentile": round(pct, 1),
                "p": f["p"], "p_pct": round(f["p"] * 100.0, 1),
                "estimate_points": f["estimate"]})
        del spy_by_date

    # ---- Ledger (API only). Zero qualifying names means zero
    # ---- appends; the figures below must still recompute. ----
    reg = registry_mod.load()
    led = ledger_mod.Ledger(
        os.path.join(LINEUP, "forecast", "ledger.jsonl"), registry=reg)
    if not led.verify_chain():
        return fail("the forecast record does not verify; refusing "
                    "to add to it")
    created = 0
    if live_forecasts:
        lineage = {
            "source_artifacts": [
                {"path": LIVE_PANEL_PATH,
                 "sha256": ledger_mod.file_sha256(LIVE_PANEL_PATH)}],
            "clocks": {
                "event_time": as_of,
                "publication_time": as_of,
                "first_available_time": as_of,
                "ingestion_time": as_of,
                "decision_as_of": as_of},
            "note": ("Own-norm depth forecasts from the close of "
                     "the as-of session, graded at exactly 20 "
                     "sessions on the excess return against SPY.")}
        # Horizon dates come from the forward session calendar
        # on record (forecast/session_calendar.py and its
        # persisted session_calendar.json, RC-04 cure,
        # 2026-10-30): the NYSE session list generated from the
        # exchange's holiday rules and verified against those
        # rules on every load. A missing or disagreeing calendar
        # still fail closes; a present one lets a qualifying
        # name issue instead of fail closing.
        try:
            future = calendar_mod.next_sessions(as_of, HORIZON)
        except calendar_mod.CalendarError as exc:
            return fail(f"qualifying names exist but the forward "
                        f"session calendar cannot date their "
                        f"horizons: {exc}")
        horizon_open, horizon_close = future[0], future[-1]
        for fc in live_forecasts:
            _row, was = led.append_forecast_declared(
                engine_id=ENGINE_ID, issued_ts=as_of,
                subject=fc["symbol"],
                quantity=("chance the name's next 20 sessions "
                          "beat SPY, with the median excess in "
                          "points"),
                value={"p": fc["p"],
                       "estimate": fc["estimate_points"]},
                horizon_open=horizon_open,
                horizon_close=horizon_close, lineage=lineage,
                families=["price"],
                outcome={"symbol": fc["symbol"],
                         "kind": "excess_sign", "benchmark": "SPY",
                         "base_date": as_of,
                         "at_date": horizon_close})
            created += 1 if was else 0
    rows = led.rows()
    if not led.verify_chain(rows):
        return fail("the forecast record failed verification after "
                    "writing; not publishing figures from it")
    figures = ledger_mod.recompute_figures(rows)
    mine = figures.get(ENGINE_ID, {"forecasts": 0, "graded": 0})

    source_text = (
        "The daily price history on record (1,832 stocks "
        "plus the broad market fund they are measured "
        "against, March 25, 2025 to October 23, 2026, at most 399 "
        "trading days for any one name), checked for this "
        "page. The long daily price history behind the "
        "original study (2016 to 2026, about 6,400 names "
        "including ones that no longer trade) is not on "
        "this computer.")
    live_note = (
        "No stock qualifies today. Judging a "
        "dip against a stock's own past dips "
        "needs 750 of its own past trading days "
        "behind it, and the longest history on "
        "record here is 399 days. Every one of "
        "the 1,832 stocks checked was set aside "
        "for that reason and counted, and no "
        "shorter stand-in was used.")
    if curve["state"] == "fitted_frozen":
        # DEEP runtime cure, 2026-10-30: the curve and the
        # out-of-sample evaluation above were computed from the
        # landed long panel (deep_bars.json); the page must say
        # so, and its live block must carry the live panel's own
        # counted figures, not the pre-panel board text.
        source_text = (
            "The curve and the out-of-sample evaluation on this "
            "page were computed from the long daily price history "
            "on record (deep_bars.json, 2015 to 2026, read through "
            "the terminal's shared panel reader). Live forecasts "
            "are still judged against the shipped daily history "
            f"({name_count - 1} stocks plus the broad market fund, "
            f"{span[0]} to {span[1]}, at most {max_len} trading "
            "days for any one name), checked for this page.")
        live_note = (
            "No stock qualifies for a live forecast today. "
            "Judging a dip against a stock's own past dips needs "
            f"{TR_WINDOW} of its own past trading days behind it, "
            f"and the longest history on the live record here is "
            f"{max_len} days. Every one of the {name_count - 1} "
            "stocks checked was set aside for that reason and "
            "counted, and no shorter stand-in was used. The "
            "fitted curve above comes from the long panel, whose "
            "names do carry the full history.")
    if live_forecasts:
        live_note = (
            f"{len(live_forecasts)} stock(s) qualified for a live "
            "forecast today and were written to the shared record, "
            "with horizon dates from the forward session calendar "
            "on record (forecast/session_calendar.json). They "
            "grade at 20 sessions on the excess return against "
            "SPY, under the registered excess_sign convention.")
    data = {
        "tool": "Own-Norm Depth Forecaster",
        "state": "proving",
        "as_of_session": as_of,
        "source": source_text,
        "claim": ("The claim under test: among rising-trend "
                  "stocks, the fifth sitting in the deepest "
                  "pullbacks against their own usual dip sizes "
                  "beat the fifth in the shallowest pullbacks by "
                  "at least 0.8 points of middle 20-trading-day "
                  "return ahead of the broad market."),
        "live": {
            "forecasts_recorded": mine["forecasts"],
            "forecasts_graded": mine["graded"],
            "proving_target_matured": 200,
            "names_checked": name_count - 1,
            "names_qualifying": len(live_forecasts),
            "names_excluded_too_short": excluded_too_short,
            "sessions_needed_per_name": MIN_SESSIONS,
            "longest_history_on_record": max_len,
            "forecasts": live_forecasts,
            "state_note": live_note,
        },
        "curve": curve,
        "history": {
            "label": "History, not live forecasts",
            "study_record": {
                "source_name": ("The earlier study this engine is "
                                "built from, on the long daily "
                                "price history, 2016 to 2026, "
                                "about 6,400 names including ones "
                                "that no longer trade; rising-trend "
                                "names on fear days."),
                "rows": [
                    {"era": "2016 to 2022", "window_sessions": 20,
                     "rank_correlation": 0.026, "strength": 4.3},
                    {"era": "2023 onward", "window_sessions": 20,
                     "rank_correlation": 0.031, "strength": 4.3},
                    {"era": "2023 onward", "window_sessions": 60,
                     "rank_correlation": 0.062, "strength": 9.8},
                ],
                "quintile_spread_2023_points": 0.81,
                "note": ("In that study, deeper own-norm pullbacks "
                         "ranked ahead of shallower ones in both "
                         "eras, and in 2023 onward the deepest "
                         "fifth beat the shallowest fifth by 0.81 "
                         "points over 20 trading days. Those are "
                         "the study's figures, from its own "
                         "history. They are the reason this engine "
                         "exists; they are not this engine's "
                         "results."),
            },
            "out_of_sample": oos,
        },
        "fear_day": fear,
        "panel_reader": reader_strategy,
        "kill_criterion": ("This tool is retired if, after 200 of "
                           "its forecasts have reached their "
                           "20-trading-day grade, the gap between "
                           "the deepest fifth and the shallowest "
                           "fifth could still plausibly be zero."),
        "thin_cell_rule": ("Any group with fewer than 30 graded "
                           "forecasts shows its count only, with "
                           "no percentage headline."),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH}: as of {as_of}, {name_count - 1} names "
          f"checked, {len(live_forecasts)} qualifying, "
          f"{excluded_too_short} excluded (history too short), "
          f"curve {curve['state']}, ledger forecasts "
          f"{mine['forecasts']} ({created} new), graded "
          f"{mine['graded']}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
