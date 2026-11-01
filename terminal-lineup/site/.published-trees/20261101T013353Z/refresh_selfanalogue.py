#!/usr/bin/env python3
"""Refresh the Per-Name Self-Analogue (Forecast Engine 15).

=====================================================================
CANDIDATE-REGISTER TRIPLE (written before any computation)

1. EVIDENCE CLASS
   Poor to fair, named plainly. The nearest relative in the graded
   record, the cross-sectional analogue study (row S21), was killed:
   analogies mined across other names carried a rank correlation of
   only +0.0046. This engine is a different construction, matching a
   name only against its own past, and it must beat that prior in
   public or join it. Its parts come from the S6 state record
   (SqueezeMetrics published coordinates A106 to A110, recombined in
   morgue/studies.py as S6): the normalisation there is stamped OURS
   (median and spread over the name's own prior sessions, the fixed
   constant 1.4826 turning that spread into a z-score, squashed
   through tanh(z/3)), and its nearest-neighbour rule takes the
   nearest one-sixth of past states. No forward record of this
   engine's own exists yet; it starts here, and it starts empty for
   the reason stated below.

2. RECONSTRUCTION CHOICES (every constant, named before computing)
   - The state is four own-history coordinates. The design and the
     SR-2 candidate name five plain words (price position, volume,
     gap, drawdown, range) and say the state vector is four price
     coordinates once the volatility coordinate is dropped, but no
     file on this disk gives formulas, windows, or how drawdown and
     range compress into one coordinate. The definitions below are
     therefore stated reconstructions, named as such on the page:
       1. Price position: the name's 21-session log return (this is
          S6's own P coordinate, taken verbatim).
       2. Volume: the log of the name's average daily share volume
          over the last 21 sessions.
       3. Gap: the name's average overnight gap (today's open over
          yesterday's close, minus 1) over the last 21 sessions.
       4. Drawdown for its range: how far today's close sits below
          the name's highest close of the last 63 sessions, divided
          by the name's average daily high-to-low range (as a share
          of price) over the last 21 sessions. This is the drawdown
          and range pair compressed into one number, as the design
          describes.
   - Each coordinate is turned into an own-history score with S6's
     normalise() imported from morgue/studies.py, never forked: the
     score compares today's raw coordinate with that coordinate's
     own earlier values only (at least 126 of them, or no state).
   - The dropped coordinate: S6 also carries a market-wide
     short-selling coordinate, and the design's fifth coordinate was
     implied volatility. The implied-volatility record stopped on
     October 14, 2026 with 60 names at at most 12 readings each, so
     it cannot support a per-name state; it is dropped and the page
     says so. No coordinate is filled in from anything else.
   - Matching: only within the same name's own history. A past state
     is usable when all four of its scores exist and the 21 sessions
     after it are on record, so what followed it is known. Distance
     is the straight-line distance between today's four scores and
     the past state's four scores (S6's own form). The matched set
     is the nearest one-sixth of usable past states:
     k = max(1, ceil(usable / 6)), S6's rule verbatim.
   - The forecast: the 10th, 50th and 90th percentiles (straight-line
     interpolation between the two nearest ranked values) of the
     21-session returns that followed the matched states, stated in
     percent. The 10th-to-90th band is the published band.
   - The minimum: a name is forecast only when at least 750 of its
     own sessions are on the shipped record. 750 is the design's
     stated minimum, not a constant found in any code on this disk.
     Shortening it was considered and rejected in advance: at the
     shipped record's longest history (399 sessions) the usable
     library would be roughly 250 states and the matched set about
     42 returns instead of about 121, a noisier and different
     forecast from the one under test.
   - The shipped record: this engine reads the same daily price
     history the whole forecast programme reads and grades from
     (~/workspace/morgue/data_cache/board_bt_bars.json, 1,833 names
     including the broad market fund, at most 399 sessions each,
     March 25, 2025 to October 23, 2026). A 42-name research cache
     from a different desk programme does hold longer histories for
     its own names; it is not this engine's record, it is not the
     long history the design names (2016 to 2026, about 6,400 names
     including delisted ones, which is not on this disk), and its
     forecasts could not be graded by the shared record, so it is
     not adopted. Every count on the page is scoped to the shipped
     record and says so.
   - Ledger shape: one forecast per qualifying name per issue day,
     value {"quantiles": {"0.1": ..., "0.5": ..., "0.9": ...}} in
     percent, outcome the name's own 21 session return in
     percent (kind "return_percent" on new rows, base the
     as-of close; rows issued under kind "return" resolve
     through the registered legacy map, RC-19 cure,
     2026-10-30). The registered grading rule
     is the quantile score, which also records whether the real
     return landed inside the 10-to-90 band. Horizon dates are the
     next weekdays after the as-of session (the programme's
     standing convention); grading itself waits until the price
     record actually contains the closing session.
   - Coverage and suspension: coverage is counted pooled and per
     name. A name whose band coverage misses the stated 80 percent
     by more than 15 points over 100 of its own graded forecasts is
     suspended, and the suspension is published, never silent.
   - Thin-cell rule: any group with fewer than 30 graded forecasts
     shows its count only, no percentage headline.
   - One price family. This engine is never counted as independent
     of Engines 3 or 16 in any agreement count.

3. NON-CLAIMS
   - No live forecast is claimed today: zero names on the shipped
     record meet the 750-session minimum, so every name is counted
     as waiting with that one reason and nothing is written to the
     live record.
   - The end-to-end check on made-up data proves the machinery
     runs; it is not evidence the forecast is any good. Its numbers
     are published labelled as a machinery check.
   - The calibration claim (real returns land inside the published
     band 80 percent of the time, give or take 5 points) is the
     claim under test, not a result.

=====================================================================
Behaviour: validate the shipped record (fails closed on any
disagreement), run the synthetic end-to-end check on a throwaway
record, evaluate every name on the shipped record (all wait today),
ledger live forecasts for qualifying names through
forecast/ledger.py append_forecast only, then write data.json from
the record plus figures recomputed from the live ledger alone.
Idempotent. Timestamps come from the sources, never the clock.

ADDENDUM (2026-10-29, terminal total hookup, CURE-LEDGER G3
staging): the record this engine reads is now the landed DEEP
panel (deep_bars.json) when that file is present, with the board
panel as fallback; the register above describes the shipped record
as it stood at build time. Page source and waiting text are
computed from the record actually read, so they stay true under
either panel.
"""

import json
import math
import os
import random
import re
import sys
import tempfile
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(HERE)
PANEL_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")
# DEEP panel pointing (CURE-LEDGER G3 staging, landed by the
# terminal total hookup 2026-10-29): when the long daily history
# (deep_bars.json, new filename, board panel never overwritten) is
# on disk, it is the record this engine reads; the shipped board
# panel remains the fallback when it is absent.
DEEP_PANEL_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/deep_bars.json")
STUDIES_PATH = os.path.expanduser("~/workspace/morgue/studies.py")
OUT_PATH = os.path.join(HERE, "self-analogue", "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import attestation_block as _ab
except ImportError:  # refresh stays runnable standalone
    _ab = None
LEDGER_PATH = os.path.join(LINEUP, "forecast", "ledger.jsonl")

sys.path.insert(0, LINEUP)
sys.path.insert(0, os.path.expanduser("~/workspace/morgue"))
from forecast import grading as grading_mod  # noqa: E402
from forecast import ledger as ledger_mod  # noqa: E402
from forecast import registry as registry_mod  # noqa: E402
import studies as s6  # noqa: E402  (S6 normalise / MAD_TO_Z, imported never forked)

ENGINE_ID = "engine_15"
MIN_SESSIONS = 750        # the design's stated minimum, never shortened
HORIZON = 21              # sessions
THIN = 30
CLAIM_COVERAGE_PCT = 80.0
SUSPEND_MISS_POINTS = 15.0
SUSPEND_MIN_FORECASTS = 100
KILL_FORECASTS = 200
KILL_ERROR_POINTS = 10.0


def fail(msg):
    print(f"Self-Analogue refresh: {msg}", file=sys.stderr)
    return 1


# ---- the four reconstructed coordinates (raw series per name) ----
def coordinate_series(rows):
    """rows: [date, o, h, l, c, v]. Returns four raw series aligned
    to rows (None where a window does not exist yet)."""
    n = len(rows)
    opens = [float(r[1]) for r in rows]
    highs = [float(r[2]) for r in rows]
    lows = [float(r[3]) for r in rows]
    closes = [float(r[4]) for r in rows]
    vols = [float(r[5]) for r in rows]
    price_pos = [None] * n
    volume = [None] * n
    gap = [None] * n
    dd_range = [None] * n
    for i in range(n):
        if i >= 21 and closes[i - 21] > 0:
            price_pos[i] = math.log(closes[i] / closes[i - 21])
            vwin = vols[i - 20:i + 1]
            if all(v > 0 for v in vwin):
                volume[i] = math.log(sum(vwin) / len(vwin))
            gaps = [opens[j] / closes[j - 1] - 1.0
                    for j in range(i - 20, i + 1)]
            gap[i] = sum(gaps) / len(gaps)
            rng = [(highs[j] - lows[j]) / closes[j]
                   for j in range(i - 20, i + 1) if closes[j] > 0]
            if len(rng) == 21:
                mean_rng = sum(rng) / len(rng)
                if mean_rng > 0 and i >= 62:
                    hi = max(closes[i - 62:i + 1])
                    dd_range[i] = (closes[i] / hi - 1.0) / mean_rng
    return [price_pos, volume, gap, dd_range]


def state_vectors(rows):
    """Normalised four-score state per index, via S6 normalise()
    against that coordinate's own earlier values only."""
    series = coordinate_series(rows)
    n = len(rows)
    vectors = [None] * n
    for i in range(n):
        vec = []
        ok = True
        for s in series:
            if s[i] is None:
                ok = False
                break
            v = s6.normalise(s[i], s[:i])
            if v is None:
                ok = False
                break
            vec.append(v)
        if ok:
            vectors[i] = vec
    return vectors


def forward_returns(rows, horizon=HORIZON):
    closes = [float(r[4]) for r in rows]
    n = len(rows)
    out = [None] * n
    for i in range(n - horizon):
        if closes[i] > 0:
            out[i] = (closes[i + horizon] / closes[i] - 1.0) * 100.0
    return out


def percentile(sorted_vals, q):
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = q * (len(sorted_vals) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def self_analogue_forecast(rows, horizon=HORIZON):
    """The full pipeline for one name at its freshest session.
    Returns a dict with the band, or None when no usable state
    library exists."""
    vectors = state_vectors(rows)
    fwds = forward_returns(rows, horizon)
    current = vectors[-1]
    if current is None:
        return None
    usable = [(vectors[i], fwds[i]) for i in range(len(rows))
              if vectors[i] is not None and fwds[i] is not None
              and i != len(rows) - 1]
    if not usable:
        return None

    def dist(vec):
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(current, vec)))

    usable.sort(key=lambda pair: dist(pair[0]))
    k = max(1, math.ceil(len(usable) / 6))
    matched = sorted(f for _v, f in usable[:k])
    return {"usable_states": len(usable), "matched": k,
            "p10": percentile(matched, 0.10),
            "p50": percentile(matched, 0.50),
            "p90": percentile(matched, 0.90)}


def next_weekdays(after_iso, count):
    d = date.fromisoformat(after_iso)
    out = []
    while len(out) < count:
        d += timedelta(days=1)
        if d.weekday() < 5:
            out.append(d.isoformat())
    return out


# ------------------------------------------------------------------
# Fast path (cure G17, 2026-10-30). The reference implementations
# above take about 66 seconds per name on a 2,973-session DEEP
# history (the S6 normalise() call is O(history) per index, so a
# name is O(n^2)); over the DEEP panel's 8,857 qualifying names
# that is weeks, and loading the panel whole was OOM-killed on
# this box. The functions below compute EXACTLY the same values
# (verified bit-identical against the reference implementations
# on real names in forecast/tests/test_deep_streaming_20261030.py):
# the coordinate series via sliding-window numpy, and the S6
# normalisation via a maintained sorted history whose median is
# O(1) and whose MAD is the median of two sorted deviation runs,
# read by binary-search order statistics instead of a re-sort.
# The panel is streamed symbol by symbol (iter_panel_symbols),
# never held whole.
# ------------------------------------------------------------------
import bisect as _bisect  # noqa: E402
import re as _re  # noqa: E402

import numpy as _np  # noqa: E402
from numpy.lib.stride_tricks import sliding_window_view as _swv  # noqa: E402


def _mad_from_sorted(sh, med):
    """Median of |x - med| over the sorted list sh, exactly as
    statistics.median computes it, without materialising the
    deviations: they form two sorted runs (below/at med and
    above med), and the median is an order statistic of their
    union, found by binary search."""
    m = len(sh)
    cut = _bisect.bisect_right(sh, med)
    na, nb = cut, m - cut

    def kth(k):
        # 0-indexed k-th smallest of the union: the partition
        # takes k+1 elements in total.
        lo, hi = max(0, k + 1 - nb), min(k + 1, na)
        while lo <= hi:
            i = (lo + hi) // 2
            j = k + 1 - i
            a_left = (med - sh[cut - i]) if i > 0 else -math.inf
            b_left = (sh[cut + j - 1] - med) if j > 0 else -math.inf
            a_right = (med - sh[cut - 1 - i]) if i < na else math.inf
            b_right = (sh[cut + j] - med) if j < nb else math.inf
            if a_left <= b_right and b_left <= a_right:
                return a_left if a_left >= b_left else b_left
            if a_left > b_right:
                hi = i - 1
            else:
                lo = i + 1
        raise AssertionError("kth of deviation runs failed")

    if m % 2:
        return kth(m // 2)
    return (kth(m // 2 - 1) + kth(m // 2)) / 2.0


def _normalise_series_fast(series):
    """[s6.normalise(series[i], series[:i]) for i] computed with a
    maintained sorted history. Identical outputs, including the
    >=126 finite-history floor and the MAD==0 refusal."""
    out = [None] * len(series)
    sh = []
    for i, v in enumerate(series):
        if v is not None and math.isfinite(v):
            if len(sh) >= 126:
                m = len(sh)
                med = sh[m // 2] if m % 2 else \
                    (sh[m // 2 - 1] + sh[m // 2]) / 2.0
                mad = _mad_from_sorted(sh, med)
                if mad != 0:
                    out[i] = math.tanh(
                        s6.MAD_TO_Z * (float(v) - med) / mad / 3.0)
            _bisect.insort(sh, float(v))
    return out


def _coordinate_series_fast(rows):
    """coordinate_series() computed with sliding windows. Returns
    four lists aligned to rows, None where the reference returns
    None (the i>=21 gate on every coordinate is preserved)."""
    n = len(rows)
    o = _np.array([r[1] for r in rows], dtype=float)
    h = _np.array([r[2] for r in rows], dtype=float)
    lo_ = _np.array([r[3] for r in rows], dtype=float)
    c = _np.array([r[4] for r in rows], dtype=float)
    v = _np.array([r[5] for r in rows], dtype=float)
    price_pos = _np.full(n, _np.nan)
    volume = _np.full(n, _np.nan)
    gap = _np.full(n, _np.nan)
    dd_range = _np.full(n, _np.nan)
    if n > 21:
        with _np.errstate(divide="ignore", invalid="ignore"):
            price_pos[21:] = _np.where(
                c[:-21] > 0, _np.log(c[21:] / _np.where(
                    c[:-21] > 0, c[:-21], 1.0)), _np.nan)
            vw = _swv(v, 21)
            vmean = vw.mean(axis=1)
            vall = (vw > 0).all(axis=1)
            volume[21:] = _np.where(
                vall[1:], _np.log(_np.where(
                    vmean[1:] > 0, vmean[1:], 1.0)), _np.nan)[:n - 21]
            g = _np.full(n, _np.nan)
            g[1:] = o[1:] / c[:-1] - 1.0
            gw = _swv(g, 21)
            gap[21:] = gw.mean(axis=1)[1:n - 20]
            rng = _np.where(c > 0, (h - lo_) / _np.where(
                c > 0, c, 1.0), _np.nan)
            rw = _swv(rng, 21)
            rmean = rw.mean(axis=1)
            rcount = _np.isfinite(rw).sum(axis=1)
            hw = _swv(c, 63)
            hmax = hw.max(axis=1)
            idx = _np.arange(62, n)
            mr = rmean[idx - 20]
            cnt = rcount[idx - 20]
            hm = hmax[idx - 62]
            dd_range[idx] = _np.where(
                (cnt == 21) & (mr > 0),
                (c[idx] / hm - 1.0) / _np.where(mr > 0, mr, 1.0),
                _np.nan)

    def to_list(arr):
        return [None if not _np.isfinite(x) else float(x) for x in arr]

    return [to_list(price_pos), to_list(volume), to_list(gap),
            to_list(dd_range)]


def state_vectors_fast(rows):
    """state_vectors() via the fast coordinate + normalise path."""
    series = _coordinate_series_fast(rows)
    normalised = [_normalise_series_fast(s) for s in series]
    n = len(rows)
    vectors = [None] * n
    for i in range(n):
        vec = [normalised[k][i] for k in range(4)]
        if all(x is not None for x in vec):
            vectors[i] = vec
    return vectors


def self_analogue_forecast_fast(rows, horizon=HORIZON):
    """self_analogue_forecast() on the fast state vectors; the
    matching, percentiles and return shapes are the reference
    code's, unchanged."""
    vectors = state_vectors_fast(rows)
    fwds = forward_returns(rows, horizon)
    current = vectors[-1]
    if current is None:
        return None
    usable = [(vectors[i], fwds[i]) for i in range(len(rows))
              if vectors[i] is not None and fwds[i] is not None
              and i != len(rows) - 1]
    if not usable:
        return None

    def dist(vec):
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(current, vec)))

    usable.sort(key=lambda pair: dist(pair[0]))
    k = max(1, math.ceil(len(usable) / 6))
    matched = sorted(f for _v, f in usable[:k])
    return {"usable_states": len(usable), "matched": k,
            "p10": percentile(matched, 0.10),
            "p50": percentile(matched, 0.50),
            "p90": percentile(matched, 0.90)}


# ------------------------------------------------------------------
# Resumable checkpoint cache (cure G17 remainder, 2026-10-30).
# Even on the fast path a full build is hours (about 1s per name
# over 8,857 qualifying names, plus a full streamed parse for the
# lengths pass), and this box restarts often enough that an
# all-or-nothing run had already been lost once (9 names ledgered,
# page never written, Calibration League fail-closed on the
# disagreement). The cache stores ONLY deterministic recompute
# results, keyed by the panel fingerprint (basename, size,
# mtime_ns): the per-symbol row lengths and each symbol's fast
# forecast (or None). A re-run with the same panel reuses them
# verbatim; a changed panel fingerprints differently and the
# cache is ignored. The ledger remains the only record of the
# forecasts themselves; nothing is ever read back from the cache
# into a figure the ledger does not recompute.
# ------------------------------------------------------------------
FC_CACHE_DIR = os.path.expanduser(
    "~/workspace/morgue/data_cache/selfanalogue_cache")


def panel_fingerprint(path):
    st = os.stat(path)
    return f"{os.path.basename(path)}:{st.st_size}:{st.st_mtime_ns}"


def fc_cache_dir(cache_root, fingerprint):
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", fingerprint)
    return os.path.join(cache_root, safe)


def read_lengths_cache(path, fingerprint):
    """{symbol: row count} stored for exactly this fingerprint,
    or None (missing, unreadable, or a different panel)."""
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return None
    if not isinstance(doc, dict) or doc.get("fingerprint") != fingerprint:
        return None
    lengths = doc.get("lengths")
    if not isinstance(lengths, dict):
        return None
    return {str(k): int(v) for k, v in lengths.items()}


def write_lengths_cache(path, fingerprint, lengths):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"fingerprint": fingerprint, "lengths": lengths}, fh)
    os.replace(tmp, path)


def read_fc_cache(path):
    """{symbol: forecast dict or None} from the append-only
    results file. A torn final line (a run killed mid-append) is
    ignored, never fatal: that symbol is simply recomputed."""
    out = {}
    try:
        fh = open(path, encoding="utf-8")
    except OSError:
        return out
    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                out[str(rec["symbol"])] = rec["fc"]
            except (ValueError, KeyError, TypeError):
                continue
    return out


def append_fc_cache(path, symbol, fc):
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"symbol": symbol, "fc": fc}) + "\n")
        fh.flush()


def iter_panel_symbols(path):
    """Stream a {symbol: rows} JSON panel one symbol at a time
    (the proofgate loader's slicing method): the file is read as
    text and each symbol's array is parsed on its own, so peak
    memory is the text plus one symbol's rows, never the whole
    parsed panel."""
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    decoder = json.JSONDecoder()
    for match in _re.finditer(r'"([^"]+)": \[', text):
        rows, _end = decoder.raw_decode(text, match.end() - 1)
        if rows:
            yield match.group(1), rows


# ---- synthetic end-to-end check (throwaway record only) ---------
def synthetic_self_test(ledger_before_md5):
    """Build one made-up name with 850 sessions, run the whole
    pipeline, write its forecast to a THROWAWAY ledger, grade it at
    21 sessions through the shared grading runner against a made-up
    price file, and recompute figures from that throwaway ledger
    alone. The live ledger is never touched."""
    rng = random.Random(20261028)
    days = next_weekdays("2023-01-02", 850)
    rows = []
    price = 100.0
    for i, d in enumerate(days):
        drift = 0.0004 + 0.004 * math.sin(i / 40.0)
        shock = rng.gauss(0.0, 0.011)
        open_ = price * (1.0 + rng.gauss(0.0, 0.002))
        close = price * math.exp(drift + shock)
        high = max(open_, close) * (1.0 + abs(rng.gauss(0.0, 0.004)))
        low = min(open_, close) * (1.0 - abs(rng.gauss(0.0, 0.004)))
        vol = 1_000_000 * (1.0 + 0.3 * math.sin(i / 25.0)
                           + abs(rng.gauss(0.0, 0.1)))
        rows.append([d, round(open_, 4), round(high, 4), round(low, 4),
                     round(close, 4), int(vol)])
        price = close
    fc = self_analogue_forecast(rows)
    assert fc is not None and fc["usable_states"] > 0
    assert fc["p10"] <= fc["p50"] <= fc["p90"], "band out of order"

    issue_idx = len(rows) - 1 - HORIZON  # so the outcome has matured
    hist_rows = rows[:issue_idx + 1]
    fc_issue = self_analogue_forecast(hist_rows)
    assert fc_issue is not None
    assert fc_issue["p10"] <= fc_issue["p50"] <= fc_issue["p90"]
    as_of = rows[issue_idx][0]
    close_date = rows[issue_idx + HORIZON][0]

    tmp = tempfile.mkdtemp(prefix="selfanalogue-test-")
    scratch_ledger = os.path.join(tmp, "ledger.jsonl")
    bars_path = os.path.join(tmp, "bars.json")
    with open(bars_path, "w", encoding="utf-8") as fh:
        json.dump({"TEST": rows}, fh)

    reg = registry_mod.load()
    led = ledger_mod.Ledger(scratch_ledger, registry=reg)
    lineage = {
        "source_artifacts": [{"path": bars_path,
                              "sha256": ledger_mod.file_sha256(bars_path)}],
        "clocks": {"event_time": as_of, "publication_time": as_of,
                   "first_available_time": as_of,
                   "ingestion_time": as_of, "decision_as_of": as_of},
        "note": "Synthetic self-test forecast on made-up data."}
    row, created = led.append_forecast_declared(
        engine_id=ENGINE_ID, issued_ts=as_of, subject="TEST",
        quantity="own_return_21s_percent_distribution",
        value={"quantiles": {"0.1": round(fc_issue["p10"], 4),
                             "0.5": round(fc_issue["p50"], 4),
                             "0.9": round(fc_issue["p90"], 4)}},
        horizon_open=as_of, horizon_close=close_date, lineage=lineage,
        families=["price"],
        outcome={"symbol": "TEST", "kind": "return_percent",
                 "base_date": as_of, "at_date": close_date})
    assert created
    prices = grading_mod.PriceSource(bars_path)
    graded = grading_mod.run_grading(led, prices, reg)
    assert len(graded) == 1, f"expected 1 graded, got {len(graded)}"
    figures = ledger_mod.recompute_figures(led.rows())
    mine = figures[ENGINE_ID]
    assert mine["forecasts"] == 1 and mine["graded"] == 1
    grade_row = [r for r in led.rows() if r.get("type") == "grade"][0]
    score = grade_row["grade"]["scores"]
    realised = (rows[issue_idx + HORIZON][4] / rows[issue_idx][4]
                - 1.0) * 100.0
    inside = fc_issue["p10"] <= realised <= fc_issue["p90"]
    assert ("coverage_hit" in score
            and abs(score["coverage_hit"] - (1.0 if inside else 0.0)) < 1e-9)
    import hashlib
    with open(LEDGER_PATH, "rb") as fh:
        after = hashlib.md5(fh.read()).hexdigest()
    assert after == ledger_before_md5, "live ledger changed in self-test"
    return {
        "state": "passed",
        "what_it_proves": (
            "On made-up data for one invented stock with 850 made-up "
            "trading days, the whole chain ran: the four own-history "
            "scores were built, today's state was matched against the "
            "nearest one-sixth of that stock's own past states, the "
            "low, middle and high figures came out in order, the "
            "forecast was written to a throwaway record (never the "
            "live one), it was graded 21 trading days later by the "
            "shared grading machinery, and the published figures were "
            "recomputed from that throwaway record alone. The live "
            "record was checked unchanged afterwards."),
        "usable_states": fc_issue["usable_states"],
        "matched_states": fc_issue["matched"],
        "band_percent": {"low": round(fc_issue["p10"], 2),
                         "middle": round(fc_issue["p50"], 2),
                         "high": round(fc_issue["p90"], 2)},
        "realised_percent": round(realised, 2),
        "landed_inside_band": bool(inside),
        "live_record_untouched": True,
    }


class StreamedPanel:
    """Lazy per-symbol view over a panel JSON file, in the
    {symbol: [[date, o, h, l, c, v], ...]} shape. Loading the
    DEEP panel whole with json.load built several GB of row
    lists and was OOM killed on this box (exit -9 at 404s in
    the 2026-10-30 refresh proof run, on the 413 MB panel; the
    landed panel is 1,046 MB). This view keeps the file text
    and a symbol offset index, and parses exactly one symbol's
    rows per access, discarding them afterwards: the same
    pattern refresh_proofgate.py proved on this panel. Row
    values are identical to json.load's; only the residency
    differs. Nothing is cached, so repeated access re-parses
    that one symbol only."""

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
    panel_path = (DEEP_PANEL_PATH if os.path.exists(DEEP_PANEL_PATH)
                  else PANEL_PATH)
    if not os.path.exists(panel_path):
        return fail(f"shipped price history not found: {panel_path}")
    # Shared mmap reader (DEEP runtime cure, 2026-10-30): the
    # local StreamedPanel held the whole panel text resident
    # (2,005 MB peak, 107 s init) and its lengths pass parsed
    # every symbol in the panel just to count rows.
    # DeepPanelReader serves the same rows from the binary
    # derived store or an mmap of the JSON with a persisted
    # offset sidecar, and lengths() comes from its index with
    # no parsing at all. StreamedPanel remains as the fallback
    # when the shared module is unavailable.
    try:
        from deep_panel_reader import DeepPanelReader
    except ImportError:
        DeepPanelReader = None
    panel = DeepPanelReader(panel_path) \
        if DeepPanelReader is not None else StreamedPanel(panel_path)
    if "SPY" not in panel:
        return fail("the shipped price history carries no SPY")
    spy_dates = [r[0] for r in panel["SPY"]]
    if spy_dates != sorted(spy_dates) or len(set(spy_dates)) != len(spy_dates):
        return fail("SPY dates in the shipped history are not a clean "
                    "increasing session list")
    as_of = spy_dates[-1]

    fingerprint = panel_fingerprint(panel_path)
    cache_dir = fc_cache_dir(FC_CACHE_DIR, fingerprint)
    os.makedirs(cache_dir, exist_ok=True)
    lengths_path = os.path.join(cache_dir, "lengths.json")
    fc_path = os.path.join(cache_dir, "results.jsonl")
    lengths = read_lengths_cache(lengths_path, fingerprint)
    if lengths is None:
        if hasattr(panel, "lengths"):
            lengths = panel.lengths()
        else:
            lengths = {sym: len(rows) for sym, rows in panel.items()}
        write_lengths_cache(lengths_path, fingerprint, lengths)
    name_count = len(panel)
    max_len = max(lengths.values())
    qualifying = sorted(sym for sym, n in lengths.items()
                        if n >= MIN_SESSIONS)
    abstaining = name_count - len(qualifying)
    if abstaining == name_count:
        waiting_reason = (
            "Every name on the record is waiting for the same "
            "single reason: its own history here is shorter than "
            f"the {MIN_SESSIONS} trading days this forecast "
            f"needs. The longest own history on the record is "
            f"{max_len} trading days. The minimum is not "
            "shortened to fit: with fewer past days the closest "
            "matches are fewer and rougher, and the range would "
            "be a different, noisier forecast from the one being "
            f"tested. The first refresh after a {MIN_SESSIONS}-day "
            "own history reaches this record issues real "
            "forecasts with no other change.")
    else:
        waiting_reason = (
            f"{abstaining} names are still waiting for the same "
            "single reason: their own history here is shorter "
            f"than the {MIN_SESSIONS} trading days this forecast "
            f"needs. The longest own history on the record is "
            f"{max_len} trading days. The minimum is not "
            "shortened to fit: with fewer past days the closest "
            "matches are fewer and rougher, and the range would "
            "be a different, noisier forecast from the one being "
            "tested.")
    if qualifying and any(lengths[s] < MIN_SESSIONS for s in qualifying):
        return fail("qualification count disagreement inside the "
                    "shipped history")

    import hashlib
    with open(LEDGER_PATH, "rb") as fh:
        ledger_md5_before = hashlib.md5(fh.read()).hexdigest()

    # ---- synthetic end-to-end check (throwaway only) ----
    try:
        self_test = synthetic_self_test(ledger_md5_before)
    except Exception as exc:  # machinery must prove itself or stop
        return fail(f"synthetic end-to-end check failed: {exc}")

    # ---- live forecasts for qualifying names (none today) ----
    reg = registry_mod.load()
    led = ledger_mod.Ledger(LEDGER_PATH, registry=reg)
    if not led.verify_chain():
        return fail("the forecast record does not verify; refusing "
                    "to add to it")
    live_forecasts = []
    created = 0
    if qualifying:
        future = next_weekdays(as_of, HORIZON)
        lineage = {
            "source_artifacts": [
                {"path": panel_path,
                 "sha256": ledger_mod.file_sha256(panel_path)}],
            "clocks": {"event_time": as_of, "publication_time": as_of,
                       "first_available_time": as_of,
                       "ingestion_time": as_of, "decision_as_of": as_of},
            "note": ("Per-name self-analogue forecasts from the close "
                     "of the as-of session, graded at exactly 21 "
                     "sessions on the name's own return.")}
        cached_fc = read_fc_cache(fc_path)
        for sym in qualifying:
            # Fast path (cure G17 remainder, 2026-10-30): the
            # reference self_analogue_forecast is O(n^2) per name
            # (about 66s on a full history, weeks over the DEEP
            # panel's qualifying names); self_analogue_forecast_fast
            # is bit-identical to it (equivalence pinned in
            # forecast/tests/test_refresh_remainders_20261030.py)
            # at about 1s per name. The forecast under test is
            # unchanged; only its computation route is.
            # Checkpoint cache (same cure, later the same day): a
            # symbol already computed for this exact panel is
            # reused verbatim instead of recomputed, so a killed
            # run resumes where it stopped and a same-panel daily
            # re-run is minutes, not hours.
            if sym in cached_fc:
                fc = cached_fc[sym]
            else:
                fc = self_analogue_forecast_fast(panel[sym])
                append_fc_cache(fc_path, sym, fc)
            if fc is None:
                continue
            value = {"quantiles": {"0.1": round(fc["p10"], 4),
                                   "0.5": round(fc["p50"], 4),
                                   "0.9": round(fc["p90"], 4)}}
            _row, was = led.append_forecast_declared(
                engine_id=ENGINE_ID, issued_ts=future[0], subject=sym,
                quantity="own_return_21s_percent_distribution",
                value=value, horizon_open=future[0],
                horizon_close=future[-1], lineage=lineage,
                families=["price"],
                outcome={"symbol": sym, "kind": "return_percent",
                         "base_date": as_of, "at_date": future[-1]})
            created += 1 if was else 0
            live_forecasts.append({
                "symbol": sym, "usable_states": fc["usable_states"],
                "matched_states": fc["matched"],
                "low_percent": round(fc["p10"], 2),
                "middle_percent": round(fc["p50"], 2),
                "high_percent": round(fc["p90"], 2)})
    rows = led.rows()
    if not led.verify_chain(rows):
        return fail("the forecast record failed verification after "
                    "writing; not publishing figures from it")
    figures = ledger_mod.recompute_figures(rows)
    mine = figures.get(ENGINE_ID, {"forecasts": 0, "graded": 0})

    data = {
        "tool": "Per-Name Self-Analogue",
        "state": "proving",
        "as_of_session": as_of,
        "source": ("The daily price history this programme "
                   "reads from: "
                   f"{name_count} names, {spy_dates[0]} to "
                   f"{as_of}, at most {max_len} trading "
                   "days for any one name, checked for this "
                   "page. Source file: "
                   f"{os.path.basename(panel_path)}."),
        "claim": ("The claim under test: when a stock's next 21 "
                  "trading days are forecast from the times that same "
                  "stock was last in the state it is in now, the "
                  "real return lands inside the published low-to-high "
                  "range 80 percent of the time, give or take 5 "
                  "points."),
        "forecast_explained": (
            "For each stock, today is described by four readings of "
            "that stock's own past: where its price sits, how much it "
            "has been trading, how it has been opening, and how far "
            "it has fallen measured against how widely it usually "
            "swings. Each reading is scored against that stock's own "
            "earlier readings only. The engine then finds the past "
            "days whose scores sit closest to today's, the nearest "
            "one-sixth of them, and looks at what the stock did over "
            "the 21 trading days that followed each of those days. "
            "The low figure is the point only 1 in 10 of those "
            "follow-ups fell below, the middle figure is the "
            "halfway follow-up, and the high figure is the point "
            "only 1 in 10 rose above."),
        "dropped_reading": (
            "One reading the original design named is left out: how "
            "expensive the stock's options say its future swings "
            "will be. That record stopped on October 14, 2026, with "
            "60 names carrying at most 12 readings each, far too "
            "little to score a stock against its own past, so the "
            "state is built from the four price readings only and "
            "this page says so rather than filling the gap in."),
        "waiting": {
            "names_checked": name_count,
            "names_qualifying": len(qualifying),
            "names_waiting": abstaining,
            "sessions_needed_per_name": MIN_SESSIONS,
            "longest_history_on_record": max_len,
            "reason": waiting_reason,
        },
        "live": {
            "forecasts_recorded": mine["forecasts"],
            "forecasts_graded": mine["graded"],
            "proving_target_graded": KILL_FORECASTS,
            "forecasts": live_forecasts,
        },
        "coverage_rule": (
            "Coverage is counted across all graded forecasts "
            "together and again stock by stock. Any group with "
            "fewer than 30 graded forecasts shows its count only, "
            "with no percentage headline."),
        "suspension_rule": (
            "If one stock's real returns land inside its published "
            "range at a rate more than 15 points away from the "
            "stated 80 percent across 100 of that stock's own graded "
            "forecasts, that stock is suspended: it stops receiving "
            "forecasts, and the suspension is published here, never "
            "done quietly."),
        "kill_criterion": (
            "This tool is retired if, after 200 graded forecasts, "
            "the share of real returns landing inside the published "
            "ranges is more than 10 points away from the stated 80 "
            "percent."),
        "family_note": (
            "This forecast is built from prices alone, one kind of "
            "evidence. Where other tools agree with it, that "
            "agreement counts once alongside the other price-based "
            "forecast engines, never as separate confirmations."),
        "self_test": self_test,
        "panel_reader": getattr(panel, "strategy", None),
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
    print(f"Wrote {OUT_PATH}: as of {as_of}, {name_count} names "
          f"checked, {len(qualifying)} qualifying, {abstaining} "
          f"waiting (own history under {MIN_SESSIONS} sessions, "
          f"longest {max_len}), self-test {self_test['state']}, "
          f"ledger forecasts {mine['forecasts']} ({created} new), "
          f"graded {mine['graded']}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
