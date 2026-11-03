#!/usr/bin/env python3
"""Refresh the Exceedance Forecaster (Forecast Engine 6).

=====================================================================
CANDIDATE-REGISTER TRIPLE (written before any computation, per the
lineup's adopted standards)

1. EVIDENCE CLASS
   Study evidence on record, grade C: AD-30 in the terminal-lineup
   evidence record (size-only precursors measured on the earlier
   study's own data: overnight gap size carrying a 1.6 to 1.9 times
   tail multiplier, a surge in the count of trades on a losing day,
   and a weekly divergence at the low), plus V4 (shape and internal
   readings forecast how much prices move, not which way: 172 of
   384 movement cells against 2 of 384 directional cells) and V3
   (volatility-term readings precede bigger moves). The target
   class, move size, is the corpus's validated class; the precursor
   evidence itself is grade C. This engine's own live record: none
   before today; it starts here.

2. RECONSTRUCTION CHOICES (every constant, named before computing)
   - THE CLAIM, FIXED BEFORE COMPUTING: this engine's chances for
     a move larger than 2 expected moves in 5 sessions must score
     a Brier score at least 0.005 points better (lower) than the
     plain overall rate's Brier score, worked out on the same
     days, pooled across SPY, QQQ and IWM. If they do not, in the
     history run below or in the live record once it can be
     graded, the engine reports itself failed on its own page.
     0.005 is a small, round, absolute margin, fixed here, not
     after seeing any result.
   - Expected move (EM): for SPY and QQQ, 1 EM at a horizon is the
     half-width of the Corrected Band Engine's 68 percent band for
     that same horizon, checked to the cent against that engine's
     published bands or this script fails closed. That engine's
     published live bands carry its FE12 session quality guard
     widening when the guard is recorded (its half-width times
     the guard's band widen factor, before rounding); the check
     applies the factor that engine publishes on its own page
     (1.0 when no guard widening is recorded) to the recomputed
     half-width and states the factor in the page's
     engine1_band_check block. This engine's own expected moves
     stay on the unwidened recipe, as its history run was built.
     For IWM and for
     every other name, 1 EM is built the same way from that name's
     own recent movement: the same recent-movement recipe the
     Corrected Band Engine uses (squared daily log returns over
     the last 1, last 5 and last 22 sessions, equal-weight mean,
     annualised), times sqrt(h/252), times k (0.88 at 5 sessions,
     0.91 at 21 sessions, the same k values the band engine uses).
   - The three forecasts, per name: (a) the chance the size of the
     5-session return (either way, size only) is larger than
     1 EM at 5 sessions; (b) the chance it is larger than 2 EM;
     (c) the chance the largest peak-to-trough drop inside the
     next 21 sessions (measured on closing prices, the peak
     starting at the as-of close) is larger than 1.5 EM at
     21 sessions.
   - Precursors THAT SHIP (each computable from the shipped daily
     history, which carries date, open, high, low, close and share
     volume per session, nothing else):
     (1) Overnight gap size: the size of the move from the
         previous close to the as-of session's open, size only.
     (2) Recent-movement level: the recent-movement (HAR) figure
         above, for the name itself.
     (3) Breadth washout: the share of names on record that ended
         the as-of session below their previous close, counted
         from the same history.
     Each of the first two is flagged when it sits in the top
     fifth of its own prior 126 sessions; the washout is flagged
     when that share reaches 65 percent. A day's precursor score
     is the count of flags (0 to 3). Bucket edges are exactly
     those counts; there are no other buckets.
   - Precursors THAT DO NOT SHIP, named absent, never faked:
     (a) the surge in the count of trades on a losing day: the
         shipped history carries share volume, not a count of
         trades, so this reading is not on record and no volume
         stand-in is substituted for it;
     (b) the weekly divergence at the low: the shipped history is
         daily only, with no intraday record and no coded
         definition of that divergence anywhere on this disk, so
         it is not on record;
     (c) the volatility-term reading (short-dated volatility
         above longer-dated): no three-month volatility series is
         on record on this disk (the same gap the Corrected Band
         Engine records), so it is not on record.
     The 1.6 to 1.9 times tail multiplier from the earlier study
     is NOT applied as a constant anywhere: it is that study's
     measured range on its own data, and this engine instead
     measures its own rates from the history on record.
   - Forecast from buckets: for a name and an outcome, the
     training days are the earlier days of that same name whose
     outcome window had fully closed by the forecast day and
     whose precursor score could be measured (score needs 148
     prior sessions: 22 for the movement recipe plus 126 for the
     top-fifth comparisons). The forecast is the exceedance rate
     among training days with the same precursor score, shrunk
     toward that name's overall training rate with a prior
     strength of 20 training days: (bucket hits + 20 x overall
     rate) / (bucket days + 20), held inside 0.01 to 0.99.
   - The plain overall rate (the comparison): the same name's
     overall training exceedance rate on the same training days,
     used as a constant chance. In the history run its Brier
     score is worked out walk-forward on exactly the same days
     as this engine's chances.
   - History run: walk-forward over the shipped history for SPY,
     QQQ and IWM only (the claim and the retirement rule are
     stated on the index record). Evaluation days start at
     session index 200 of each index's 399 sessions, the first
     point with at least 50 training days behind it. Nothing
     from the history run is written to the live ledger.
   - Live eligibility, per name: at least 253 sessions on record
     (so at least 100 closed 5-session training windows exist),
     a session on the as-of date, and a measurable precursor
     score on the as-of session. Every other name in the shipped
     list is excluded and counted, by reason.
   - Thin-cell rule: any graded cell with fewer than 30 graded
     cases shows its count only, no score.
   - Ledger shape: one row per name per forecast, value
     {"p": chance}, through the machinery's append call only.
     The shared ledger's dedupe key does not include the
     quantity, so where two different forecasts for the same
     name and horizon round to the same chance, the value also
     carries the forecast's name so the rows stay distinct; the
     grading rule reads the chance field either way. Known
     grading note, stated like the earlier engines stated
     theirs: the shared grading runner's Brier rule needs a
     binary outcome its resolver can produce; the 5-session
     rows carry the size of the return plus the threshold in
     their outcome spec, and the 21-session rows carry a
     largest-drop outcome the current resolver cannot express,
     so both must be graded by the events they state when the
     runner is next extended. No live row can mature until the
     price source passes its horizon close in any case.
   - Panel: the only daily history on record on this box is
     ~/workspace/morgue/data_cache/board_bt_bars.json (1,833
     names including SPY, QQQ and IWM, 399 sessions for the
     indices, 2025-03-25 to 2026-10-23). Nothing is claimed
     beyond that span.

3. NON-CLAIMS
   - No direction is forecast, ever, by construction: every
     forecast is about the size of a move or the size of a drop
     from a peak, never about which way prices go, and no
     wording on the page presents a size reading as a direction.
   - The earlier study's figures (grade C, its 1.6 to 1.9 times
     tail multiplier) are that study's record, shown labelled
     as the study's; they are not this engine's results.
   - The history run is a backfill computed today, not a live
     record; it ledgers nothing.
   - Share volume is never presented as a count of trades.

=====================================================================
Behaviour: walk-forward history run over the shipped history for
the three index funds (ledgers nothing), then today's live
chances for the index funds and every qualifying name ledgered
through forecast/ledger.py append_forecast (never hand-edited),
then data.json written from the panel plus figures recomputed
from the ledger alone. Idempotent: rerunning with the same panel
appends nothing and rewrites the same data.json. Fails closed on
any disagreement with the bar source, the Corrected Band
Engine's bands, or the ledger. Timestamps come from the sources,
never the clock.
"""

import json
import math
import os
import sys
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(HERE)
PANEL_PATH = os.path.expanduser("~/workspace/morgue/data_cache/board_bt_bars.json")
BAND_PATH = os.path.join(HERE, "corrected-band", "data.json")
OUT_PATH = os.path.join(HERE, "exceedance", "data.json")
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

ENGINE_ID = "engine_06"
INDEXES = ("SPY", "QQQ", "IWM")
INDEX_NAMES = {"SPY": "SPY (the big S&P 500 fund)",
               "QQQ": "QQQ (the big Nasdaq-100 fund)",
               "IWM": "IWM (the big small-company fund)"}
K_BY_H = {5: 0.88, 21: 0.91}
WARMUP = 22
FLAG_WINDOW = 126
FLAG_START = WARMUP + FLAG_WINDOW   # 148
TOP_FIFTH = 0.80
WASHOUT_SHARE = 0.65
PRIOR_STRENGTH = 20.0
P_MIN, P_MAX = 0.01, 0.99
EVAL_START = 200
THIN = 30
MIN_SESSIONS = 253
BRIER_MARGIN = 0.005
KILL_INDEX_FORECASTS = 120

QUANTITIES = {
    "ex1": "size of the 5-session return larger than 1 expected move",
    "ex2": "size of the 5-session return larger than 2 expected moves",
    "dd": "largest drop from a peak within 21 sessions larger than "
          "1.5 expected moves",
}
HORIZON_OF = {"ex1": 5, "ex2": 5, "dd": 21}


def fail(msg):
    print(f"Exceedance refresh: {msg}", file=sys.stderr)
    return 1


def engine1_guard_factor(band_data):
    """The FE12 guard widen factor Engine 1 publishes on its own
    page, or 1.0 when no widening is recorded. Mirrors Engine 1's
    own bands_for: the factor applies only when the guard carries
    a deterioration reading."""
    guard = (band_data.get("live") or {}).get(
        "session_quality_guard") or {}
    if guard.get("deterioration") is not None and \
            guard.get("band_widen_factor"):
        return float(guard["band_widen_factor"])
    return 1.0


def expected_published_edges(close, half, guard_factor):
    """Engine 1's published 68 percent band edges for an
    unwidened half-width: the half-width multiplied by the guard
    factor before rounding, exactly as Engine 1's bands_for
    rounds its live bands."""
    widened = half * guard_factor
    return (round(close * (1.0 - widened), 2),
            round(close * (1.0 + widened), 2))


def quantile(vals, q):
    s = sorted(vals)
    pos = q * (len(s) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return s[lo]
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def next_sessions(after_iso, count):
    d = date.fromisoformat(after_iso)
    out = []
    while len(out) < count:
        d += timedelta(days=1)
        if d.weekday() < 5:
            out.append(d.isoformat())
    return out


def har_vol(sq_returns, i):
    daily = sq_returns[i - 1]
    weekly = sum(sq_returns[i - 5:i]) / 5.0
    monthly = sum(sq_returns[i - WARMUP:i]) / WARMUP
    return math.sqrt(252.0 * (daily + weekly + monthly) / 3.0)


def _quantile_sorted(s, q):
    """quantile() on an already sorted list: same interpolation."""
    pos = q * (len(s) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return s[lo]
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def build_series(rows, breadth_flag_by_date):
    """Per-symbol arrays: dates, closes, score (or None), em by
    horizon, and the three outcome columns (or None).

    Runtime cure (2026-10-29 hookup): the original recomputed each
    flag threshold by sorting the full 126 session window at every
    session, and each HAR volume by re-summing its slices, for
    every one of the 1,833 names: the dominant cost in the leg
    that took 6,365 seconds against a 3,600 second job timeout.
    The thresholds are now read from sliding sorted windows
    (bisect insort and delete, same values, same interpolation)
    and the HAR sums from a prefix sum of squared returns. The
    construction, constants and outputs are unchanged; the
    fail-closed band check against Engine 1 below still guards
    the SPY and QQQ expected moves to the cent."""
    dates = [r[0] for r in rows]
    opens = [float(r[1]) for r in rows]
    closes = [float(r[4]) for r in rows]
    n = len(rows)
    rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, n)]
    sq = [r * r for r in rets]
    # Prefix sums of sq: pref[k] is sum(sq[:k]).
    pref = [0.0] * (len(sq) + 1)
    for i, v in enumerate(sq):
        pref[i + 1] = pref[i] + v
    vols = [None] * n
    for i in range(WARMUP, n):
        daily = sq[i - 1]
        weekly = (pref[i] - pref[i - 5]) / 5.0
        monthly = (pref[i] - pref[i - WARMUP]) / WARMUP
        vols[i] = math.sqrt(252.0 * (daily + weekly + monthly) / 3.0)
    abs_gap = [None] * n
    for i in range(1, n):
        abs_gap[i] = abs(opens[i] / closes[i - 1] - 1.0)
    score = [None] * n
    gap_flag = [None] * n
    vol_flag = [None] * n
    import bisect
    g_win = sorted(abs_gap[FLAG_START - FLAG_WINDOW:FLAG_START])
    v_win = sorted(vols[FLAG_START - FLAG_WINDOW:FLAG_START])
    for t in range(FLAG_START, n):
        if t > FLAG_START:
            for win, arr in ((g_win, abs_gap), (v_win, vols)):
                out_v = arr[t - FLAG_WINDOW - 1]
                del win[bisect.bisect_left(win, out_v)]
                bisect.insort(win, arr[t - 1])
        g_thr = _quantile_sorted(g_win, TOP_FIFTH)
        v_thr = _quantile_sorted(v_win, TOP_FIFTH)
        gap_flag[t] = abs_gap[t] >= g_thr
        vol_flag[t] = vols[t] >= v_thr
        score[t] = (int(gap_flag[t]) + int(vol_flag[t])
                    + int(breadth_flag_by_date.get(dates[t], False)))
    em = {h: [None] * n for h in K_BY_H}
    for h, k in K_BY_H.items():
        f = math.sqrt(h / 252.0) * k
        for i in range(WARMUP, n):
            em[h][i] = vols[i] * f
    outcomes = {"ex1": [None] * n, "ex2": [None] * n, "dd": [None] * n}
    for j in range(n):
        if j + 5 < n and em[5][j] is not None:
            size = abs(closes[j + 5] / closes[j] - 1.0)
            outcomes["ex1"][j] = size > em[5][j]
            outcomes["ex2"][j] = size > 2.0 * em[5][j]
        if j + 21 < n and em[21][j] is not None:
            peak = closes[j]
            worst = 0.0
            for t in range(j + 1, j + 22):
                c = closes[t]
                if c > peak:
                    peak = c
                d = 1.0 - c / peak
                if d > worst:
                    worst = d
            outcomes["dd"][j] = worst > 1.5 * em[21][j]
    return {"dates": dates, "closes": closes, "vols": vols,
            "abs_gap": abs_gap, "score": score, "gap_flag": gap_flag,
            "vol_flag": vol_flag, "em": em, "outcomes": outcomes}


def training_stats(series, t, outcome_key):
    """(bucket_hits, bucket_n, base_hits, base_n) over training days
    j in [FLAG_START, t-h] for the outcome at base day t."""
    h = HORIZON_OF[outcome_key]
    col = series["outcomes"][outcome_key]
    score_t = series["score"][t]
    bh = bn = th = tn = 0
    for j in range(FLAG_START, t - h + 1):
        y = col[j]
        if y is None or series["score"][j] is None:
            continue
        tn += 1
        th += 1 if y else 0
        if series["score"][j] == score_t:
            bn += 1
            bh += 1 if y else 0
    return bh, bn, th, tn


def forecast_from_stats(bh, bn, th, tn):
    if tn == 0:
        return None, None
    base = th / tn
    p = (bh + PRIOR_STRENGTH * base) / (bn + PRIOR_STRENGTH)
    return round(min(max(p, P_MIN), P_MAX), 4), round(base, 4)


def build():
    for path in (PANEL_PATH, BAND_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")
    with open(PANEL_PATH, "r", encoding="utf-8") as fh:
        panel = json.load(fh)
    with open(BAND_PATH, "r", encoding="utf-8") as fh:
        band_data = json.load(fh)
    if len(panel) != 1833:
        return fail(f"panel count disagreement: {len(panel)} names, "
                    f"expected 1833")
    for sym in INDEXES:
        rows = panel.get(sym) or []
        if len(rows) != len(panel["SPY"]):
            return fail(f"panel count disagreement: {sym} has "
                        f"{len(rows)} sessions, expected "
                        f"{len(panel['SPY'])} (the panel's own count; "
                        f"cure G2 2026-10-29)")
        dates = [r[0] for r in rows]
        if dates != sorted(dates) or len(set(dates)) != len(dates):
            return fail(f"panel dates for {sym} are not a clean "
                        f"increasing session list")
    as_of = panel["SPY"][-1][0]
    if panel["QQQ"][-1][0] != as_of or panel["IWM"][-1][0] != as_of:
        return fail("panel span disagreement among the index funds")
    span = (panel["SPY"][0][0], as_of)

    # ---- Breadth, counted from the same history ----
    below = {}
    counted = {}
    for rows in panel.values():
        for i in range(1, len(rows)):
            d = rows[i][0]
            counted[d] = counted.get(d, 0) + 1
            if float(rows[i][4]) < float(rows[i - 1][4]):
                below[d] = below.get(d, 0) + 1
    breadth_share = {d: below.get(d, 0) / c for d, c in counted.items()}
    breadth_flag = {d: s >= WASHOUT_SHARE
                    for d, s in breadth_share.items()}

    # ---- Fail closed on disagreement with Engine 1's bands ----
    if band_data.get("as_of_session") != as_of:
        return fail(f"Engine 1 band file is as of "
                    f"{band_data.get('as_of_session')}, panel ends {as_of}")
    band68 = {}
    for entry in band_data["live"]["names"]:
        for hz in entry["horizons"]:
            b = [x for x in hz["bands"] if x["level"] == 68][0]
            band68[(entry["symbol"], hz["sessions"])] = (b["lower"], b["upper"])

    # ---- Series for the index funds ----
    # Engine 1's published live bands carry its FE12 session
    # quality guard widening when the guard is recorded (cure
    # 2026-10-30: the guard went live at factor 1.2838 and this
    # check, written while the guard stood not recorded, refused
    # the widened bands forever: SPY h=5 recomputed (761.68,
    # 777.04) against published (759.5, 779.22), which is the
    # recomputed half-width times 1.2838 to the cent). The
    # comparison applies the factor Engine 1 itself publishes,
    # as the Completion Clock cure does, and states it below.
    guard_factor = engine1_guard_factor(band_data)
    index_series = {}
    for sym in INDEXES:
        s = build_series(panel[sym], breadth_flag)
        index_series[sym] = s
        if sym in ("SPY", "QQQ"):
            for h in (5, 21):
                half = s["em"][h][-1]
                expected = expected_published_edges(
                    s["closes"][-1], half, guard_factor)
                if expected != band68[(sym, h)]:
                    return fail(f"Engine 1 band disagreement for {sym} "
                                f"h={h}: recomputed {expected} "
                                f"(unwidened half-width times Engine 1 "
                                f"guard factor {guard_factor}) vs "
                                f"published {band68[(sym, h)]}")

    # ---- Walk-forward history run, index funds only ----
    hist_cells = []
    pooled2 = {"n": 0, "hits": 0, "brier_ours": 0.0, "brier_base": 0.0}
    for sym in INDEXES:
        s = index_series[sym]
        n = len(s["dates"])
        for key in ("ex1", "ex2", "dd"):
            h = HORIZON_OF[key]
            cnt = hits = 0
            sum_p = sum_b = sb = sbb = 0.0
            for t in range(EVAL_START, n - h):
                if s["score"][t] is None:
                    continue
                stats = training_stats(s, t, key)
                p, base = forecast_from_stats(*stats)
                if p is None:
                    continue
                y = 1.0 if s["outcomes"][key][t] else 0.0
                cnt += 1
                hits += int(y)
                sum_p += p
                sum_b += base
                sb += (p - y) ** 2
                sbb += (base - y) ** 2
            expect = n - h - EVAL_START
            if cnt != expect:
                return fail(f"history count disagreement for {sym} "
                            f"{key}: {cnt} != {expect}")
            cell = {
                "symbol": sym, "forecast": key, "graded": cnt,
                "events": hits,
                "realised_pct": round(hits / cnt * 100.0, 1),
                "mean_forecast_pct": round(sum_p / cnt * 100.0, 1),
                "mean_base_pct": round(sum_b / cnt * 100.0, 1),
                "brier_ours": (round(sb / cnt, 4) if cnt >= THIN else None),
                "brier_base": (round(sbb / cnt, 4) if cnt >= THIN else None),
            }
            hist_cells.append(cell)
            if key == "ex2":
                pooled2["n"] += cnt
                pooled2["hits"] += hits
                pooled2["brier_ours"] += sb
                pooled2["brier_base"] += sbb
    pooled2_out = {
        "graded": pooled2["n"], "events": pooled2["hits"],
        "brier_ours": round(pooled2["brier_ours"] / pooled2["n"], 4),
        "brier_base": round(pooled2["brier_base"] / pooled2["n"], 4),
        "margin_needed": BRIER_MARGIN,
    }
    pooled2_out["improvement"] = round(
        pooled2_out["brier_base"] - pooled2_out["brier_ours"], 4)
    pooled2_out["margin_met"] = (
        pooled2_out["improvement"] >= BRIER_MARGIN)

    # ---- Live forecasts: index funds and every qualifying name ----
    future = next_sessions(as_of, 21)
    horizon_open = future[0]
    live_indexes = []
    live_names = []
    excluded = {"too_little_history": 0, "no_session_on_as_of": 0,
                "no_measurable_score": 0}
    qualifying = []
    for sym in sorted(panel):
        rows = panel[sym]
        if len(rows) < MIN_SESSIONS:
            excluded["too_little_history"] += 1
            continue
        if rows[-1][0] != as_of:
            excluded["no_session_on_as_of"] += 1
            continue
        s = index_series.get(sym) or build_series(rows, breadth_flag)
        t = len(rows) - 1
        if s["score"][t] is None:
            excluded["no_measurable_score"] += 1
            continue
        entry = {"symbol": sym, "sessions": len(rows),
                 "close": s["closes"][-1], "score": s["score"][t],
                 "em5_pct": round(s["em"][5][t] * 100.0, 2),
                 "em21_pct": round(s["em"][21][t] * 100.0, 2)}
        for key in ("ex1", "ex2", "dd"):
            stats = training_stats(s, t, key)
            p, base = forecast_from_stats(*stats)
            if p is None:
                return fail(f"no training data behind the live "
                            f"forecast for {sym} {key}")
            entry[key] = {"p": p, "p_pct": round(p * 100.0, 1),
                          "base_pct": round(base * 100.0, 1),
                          "bucket_days": stats[1],
                          "training_days": stats[3]}
        entry["_series"] = s
        qualifying.append(entry)
        if sym in INDEXES:
            live_indexes.append({k: v for k, v in entry.items()
                                 if k != "_series"})
        else:
            live_names.append({k: v for k, v in entry.items()
                               if k != "_series"})
    live_indexes.sort(key=lambda e: INDEXES.index(e["symbol"]))
    total_excluded = sum(excluded.values())
    if len(qualifying) + total_excluded != len(panel):
        return fail("live count disagreement: qualifying plus "
                    "excluded does not equal the shipped list")
    if len(live_indexes) != 3:
        return fail("not all three index funds qualified")

    # ---- Precursor readings behind today's numbers ----
    readings = []
    for sym in INDEXES:
        s = index_series[sym]
        t = len(s["dates"]) - 1
        readings.append({
            "symbol": sym,
            "gap_size_pct": round(s["abs_gap"][t] * 100.0, 2),
            "gap_flag": bool(s["gap_flag"][t]),
            "movement_pct": round(s["vols"][t] * 100.0, 1),
            "movement_flag": bool(s["vol_flag"][t]),
            "score": s["score"][t],
        })
    breadth_today = {
        "share_below_pct": round(breadth_share[as_of] * 100.0, 1),
        "names_counted": counted[as_of],
        "flag": bool(breadth_flag[as_of]),
        "threshold_pct": int(WASHOUT_SHARE * 100),
    }

    # ---- Ledger the live forecasts (API only, never by hand) ----
    reg = registry_mod.load()
    led = ledger_mod.Ledger(
        os.path.join(LINEUP, "forecast", "ledger.jsonl"), registry=reg)
    if not led.verify_chain():
        return fail("the forecast record does not verify; refusing "
                    "to add to it")
    lineage = {
        "source_artifacts": [
            {"path": PANEL_PATH,
             "sha256": ledger_mod.file_sha256(PANEL_PATH)},
            {"path": BAND_PATH,
             "sha256": ledger_mod.file_sha256(BAND_PATH)},
        ],
        "clocks": {
            "event_time": as_of,
            "publication_time": horizon_open,
            "first_available_time": as_of,
            "ingestion_time": as_of,
            "decision_as_of": as_of,
        },
        "note": ("Exceedance chances from the close of the as-of "
                 "session, for the sessions starting on the horizon "
                 "open date. Expected moves for SPY and QQQ are the "
                 "Corrected Band Engine's 68 percent band "
                 "half-widths, checked to the cent; for every other "
                 "name the same construction from that name's own "
                 "recent movement."),
    }
    created = 0
    for entry in qualifying:
        sym = entry["symbol"]
        s = entry["_series"]
        t = len(s["dates"]) - 1
        for key in ("ex1", "ex2", "dd"):
            h = HORIZON_OF[key]
            if key == "dd":
                outcome = {
                    "symbol": sym, "kind": "max_drawdown",
                    "base_date": as_of, "at_date": future[h - 1],
                    "window_open": horizon_open,
                    "window_close": future[h - 1],
                    "threshold_fraction": round(1.5 * s["em"][21][t], 6)}
            else:
                mult = 1.0 if key == "ex1" else 2.0
                outcome = {
                    "symbol": sym, "kind": "abs_return",
                    "base_date": as_of, "at_date": future[h - 1],
                    "threshold_fraction": round(mult * s["em"][5][t], 6)}
            row, was_created = led.append_forecast_declared(
                engine_id=ENGINE_ID,
                issued_ts=horizon_open,
                subject=sym,
                quantity=QUANTITIES[key],
                value={"p": entry[key]["p"]},
                horizon_open=horizon_open,
                horizon_close=future[h - 1],
                lineage=lineage,
                families=["price", "distributional_volatility"],
                outcome=outcome,
            )
            if row.get("quantity") != QUANTITIES[key]:
                row, was_created = led.append_forecast_declared(
                    engine_id=ENGINE_ID,
                    issued_ts=horizon_open,
                    subject=sym,
                    quantity=QUANTITIES[key],
                    value={"p": entry[key]["p"],
                           "quantity": QUANTITIES[key]},
                    horizon_open=horizon_open,
                    horizon_close=future[h - 1],
                    lineage=lineage,
                    families=["price", "distributional_volatility"],
                    outcome=outcome,
                )
                if row.get("quantity") != QUANTITIES[key]:
                    return fail(f"ledger write for {sym} {key} landed "
                                f"on a different forecast row")
            created += 1 if was_created else 0

    # ---- Figures recomputed from the ledger alone ----
    rows = led.rows()
    if not led.verify_chain(rows):
        return fail("the forecast record failed verification after "
                    "writing; not publishing figures from it")
    figures = ledger_mod.recompute_figures(rows)
    mine = figures.get(ENGINE_ID, {"forecasts": 0, "graded": 0})
    todays = [r for r in rows
              if r.get("type") == "forecast"
              and r.get("engine_id") == ENGINE_ID
              and r["lineage"]["clocks"]["decision_as_of"] == as_of]
    if len(todays) != 3 * len(qualifying):
        return fail(f"ledger count disagreement: {len(todays)} live "
                    f"forecasts for the as-of session, expected "
                    f"{3 * len(qualifying)}")
    issue_days = len({
        r["lineage"]["clocks"]["decision_as_of"]
        for r in rows
        if r.get("type") == "forecast" and r.get("engine_id") == ENGINE_ID})
    index_forecasts = sum(
        1 for r in rows if r.get("type") == "forecast"
        and r.get("engine_id") == ENGINE_ID and r["subject"] in INDEXES)

    data = {
        "tool": "Exceedance Forecaster",
        "state": "proving",
        "as_of_session": as_of,
        "next_session": horizon_open,
        "source": ("Daily prices for 1,833 names from the price "
                   "history on record (399 trading days for the "
                   "index funds, March 25, 2025 to October 23, "
                   "2026), and the expected-move bands published "
                   "by the Corrected Band Engine from the same "
                   "history."),
        "claim": ("The promise, written down in advance: the "
                  "chances this page gives for a move larger than "
                  "2 expected moves in 5 trading days must score "
                  "at least 0.005 points better than simply using "
                  "the plain overall rate every time, measured the "
                  "same way on the same days. If they do not, this "
                  "page reports itself failed."),
        "live": {
            "issue_days": issue_days,
            "kill_target_index_forecasts": KILL_INDEX_FORECASTS,
            "index_forecasts_recorded": index_forecasts,
            "forecasts_recorded": mine["forecasts"],
            "forecasts_graded": mine["graded"],
            "engine1_band_check": {
                "guard_widen_factor": guard_factor,
                "basis": ("Engine 1's published 68 percent band "
                          "edges for SPY and QQQ matched to the "
                          "cent after applying the FE12 session "
                          "quality guard widen factor Engine 1 "
                          "publishes on its own page to the "
                          "recomputed unwidened half-width (factor "
                          "1.0 when no guard widening is "
                          "recorded). This engine's own expected "
                          "moves stay on the unwidened recipe.")},
            "indexes": live_indexes,
            "names": live_names,
            "names_qualifying": len(live_names),
            "names_checked": len(panel),
            "excluded_total": total_excluded,
            "excluded": {
                "too_little_history": excluded["too_little_history"],
                "no_session_on_as_of": excluded["no_session_on_as_of"],
                "no_measurable_score": excluded["no_measurable_score"],
            },
            "readings": readings,
            "breadth": breadth_today,
            "absent_readings": [
                {"name": "Surge in the count of trades on a losing day",
                 "state": "not on record",
                 "why": ("The price history on record carries how "
                         "many shares changed hands each day, not "
                         "how many separate trades there were, so "
                         "this reading cannot be counted and no "
                         "stand-in is used for it.")},
                {"name": "Weekly divergence at the low",
                 "state": "not on record",
                 "why": ("The price history on record is daily "
                         "only. There is no within-day record and "
                         "no written definition of this reading "
                         "on record, so it is not counted.")},
                {"name": "Short-dated volatility above longer-dated "
                         "volatility",
                 "state": "not on record",
                 "why": ("No three-month volatility reading is on "
                         "record, so this comparison cannot be "
                         "made and nothing is widened for it.")},
            ],
        },
        "history": {
            "label": "History, not live forecasts",
            "span_start": span[0], "span_end": span[1],
            "sessions": len(panel["SPY"]),
            "evaluation_start": panel["SPY"][EVAL_START][0],
            "note": ("Worked out day by day over the price history "
                     "on record, for the three index funds only: "
                     "each day's chances were built only from "
                     "earlier days whose results were already known "
                     "by that day, then checked against what "
                     "actually happened. The plain overall rate was "
                     "scored on exactly the same days. These are "
                     "study figures from the past, not the live "
                     "record above."),
            "cells": hist_cells,
            "claim_cell_pooled": pooled2_out,
            "study_record": {
                "note": ("The earlier study this engine is built "
                         "from measured, on its own data, that a "
                         "large overnight gap was followed by outsized "
                         "moves 1.6 to 1.9 times as often. Those are "
                         "the study's figures, from its own years. "
                         "They are the reason this engine exists; "
                         "they are not this engine's results, and no "
                         "multiplier from that study is used in the "
                         "numbers on this page."),
            },
        },
        "kill_criterion": (
            "This tool is retired if, after 120 index forecasts "
            "have been graded, its chances score no better than "
            "the plain overall rate scored on the same days."),
        "thin_cell_rule": (
            "Any graded cell with fewer than 30 graded cases shows "
            "its count only, with no score."),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH}: live as of {as_of}, {mine['forecasts']} "
          f"recorded forecasts ({created} new), {len(qualifying)} "
          f"qualifying names, {total_excluded} excluded; history "
          f"claim cell Brier ours {pooled2_out['brier_ours']} vs "
          f"plain rate {pooled2_out['brier_base']} over "
          f"{pooled2_out['graded']} graded study cases, margin "
          f"{'met' if pooled2_out['margin_met'] else 'NOT met'}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
