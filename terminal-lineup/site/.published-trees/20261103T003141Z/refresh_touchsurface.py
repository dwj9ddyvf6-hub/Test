#!/usr/bin/env python3
"""Refresh the Touch Surface (Forecast Engine 2).

=====================================================================
CANDIDATE-REGISTER TRIPLE (written before any computation, per the
lineup's adopted standards)

1. EVIDENCE CLASS
   Calibration evidence on record, grade B: AD-57 in the
   terminal-lineup evidence record (the vendor reflection touch model
   killed as calibrated: it overstates touch probability by 13 to 30
   points and saturates near 100 percent for bands narrower than
   about plus or minus 0.7 expected moves; at plus or minus 1 expected
   move it says 63.5 percent against 32 to 33 percent realised on the
   volatility-index-based move and about 50 percent realised on
   movement-based measures), plus AD-55 and AD-56 (the corrected
   expected-move calibration behind Engine 1). The live record of
   this engine itself: none yet; it starts here.

2. RECONSTRUCTION CHOICES (every constant, named before computing)
   - Expected move (EM): 1 EM for a horizon is the half-width of
     Engine 1's 68 percent band for that same horizon, taken from
     Engine 1's ledgered bands (site/corrected-band/data.json) and
     recomputed here from Engine 1's own recipe (recent-movement
     forecast times sqrt(h/252) times k, k = 0.87 / 0.88 / 0.91 for
     h = 1 / 5 / 21). A barrier at distance d is the as-of close
     plus or minus d times that half-width, rounded to cents. The
     d = 1 barriers must match Engine 1's published 68 percent band
     edges to the cent or this script fails closed. Engine 1's
     published live edges carry its FE12 session quality guard
     widening when that guard is recorded (its half-width is
     multiplied by the guard's band widen factor before rounding,
     exactly as Engine 1's own bands_for does); the check below
     applies the factor Engine 1 publishes on its own page (1.0
     when no guard widening is recorded) to the recomputed
     half-width and states the factor in the page's
     engine1_band_check block, so the widening is never absorbed
     silently. This engine's own barriers stay on the unwidened
     recipe, as its history study was built.
   - Cells: distances +0.5, +1.0, +1.5, -0.5, -1.0, -1.5 expected
     moves, and either side at 0.5, 1.0 and 1.5, at horizons 1, 5
     and 21 sessions: 27 cells per index, 54 live forecasts per
     issue day.
   - Touch: decided from daily high and low bars only. The up level
     is touched if any high in the window is at or above it; the
     down level if any low is at or below it; either side if
     either happens.
   - Movement regime (the vol-regime conditioner): each base day is
     labelled "jumpy" if its recent-movement forecast (the same
     annualised figure Engine 1's recipe produces) is above the
     median of its own trailing 126 values up to and including that
     day, otherwise "calm". Labels use only data up to the base day.
   - Empirical rate: first-passage frequencies over training base
     days j whose whole touch window has closed by the forecast day
     (j + h on or before the forecast day), so no outcome is used
     before it could have been known. Bucket order, first bucket
     with at least 30 training days wins: (1) same index, same
     horizon, same cell, same regime; (2) same index, same horizon,
     same cell, any regime; (3) both indices pooled, same horizon,
     same cell, any regime; (4) bucket 3 whatever its count.
   - Driftless barrier estimate: for a single side,
     2 x Phi(-d x k_h), Phi the standard normal curve, treating the
     price as a driftless walk with the day's movement forecast as
     its spread (the distance in spread units is d x k_h because
     1 EM is k_h times that spread). For either side, the two
     single-side estimates added and capped at 1.
   - Blend (shrinkage): forecast = 0.80 x empirical rate + 0.20 x
     barrier estimate, then held inside 0.01 to 0.99. The barrier
     estimate is shrunk hard toward the empirical rate, per spec.
   - Benchmark (never our number): the vendor reflection formula
     2N(.), reconstructed in the form that reproduces AD-57's own
     headline: for a single side, 2 x Phi(-d), treating 1 EM as
     exactly one standard step as the vendor labelled it; for
     either side, twice that, capped at 1 (at d = 1 that gives the
     recorded 63.5 percent). Haircut treatment: no haircut is
     applied to our forecast and no adjusted benchmark is
     published; the benchmark is shown raw, labelled as the old
     model, with its measured 13 to 30 point overstatement at plus
     or minus 1 EM stated beside it, because 13 to 30 is a measured
     range, not a fixed constant, and inventing a point haircut
     would add an unmeasured constant.
   - Dealer-positioning (GEX) conditioning: ABSENT, stated, never
     faked. No daily sign series on record covers the 399-session
     panel, so no forecast here is split by it, in the history
     study or live.
   - History study: walk-forward over the panel. Evaluation base
     days start at session index 150 (0-based), the first point
     where the regime buckets reach the 30-day floor with room to
     spare; every evaluation day's probabilities use training days
     whose windows had already closed by that day only. Nothing
     from the study is written to the live ledger.
   - Ledger value shape: {"p": chance}. The shared ledger's
     dedupe key does not include the quantity, so two different
     cells that happen to share the same rounded chance and the
     same horizon would be merged as one republication. Where
     that collision occurs, the value also carries the cell name
     ({"p": chance, "cell": quantity}) so distinct forecasts stay
     distinct; the grading rule reads the chance field either way.
     This was not hypothetical: on the first live run, SPY down
     1.0 in 5 sessions and QQQ down 1.5 in 5 sessions collided
     with other cells at identical chances and were written with
     the cell name carried, the other 52 exactly as above.
   - Thin-cell rule: a cell with fewer than 30 graded cases shows
     its count only, no score and no rate.
   - Panel: the only index panel on record on this box is
     ~/workspace/morgue/data_cache/board_bt_bars.json (SPY and QQQ,
     399 sessions, 2025-03-25 to 2026-10-23). Nothing is claimed
     beyond that span.

3. NON-CLAIMS
   - No direction is forecast: a touch chance for the up level and
     the down level are separate questions, and neither says which
     side comes first or where price ends. No claim about any name
     beyond SPY and QQQ. The benchmark's numbers are never our
     forecast. The history study is a backfill computed today, not
     a live record; it ledgers nothing. No dealer-positioning split
     is claimed or shown.

=====================================================================
Behaviour: walk-forward history study over the panel (ledgers
nothing), then today's live probabilities ledgered through
forecast/ledger.py append_forecast (never hand-edited), then
data.json written from the panel plus figures recomputed from the
ledger alone. Idempotent: rerunning with the same panel appends
nothing and rewrites the same data.json. Fails closed on any
disagreement with the bar source, Engine 1's bands, or the ledger.

Known grading note: the shared grading runner's touch rule checks
a single level. Either-side ledger rows carry both levels in their
outcome spec (level = up level, plus level_down and either_side);
they must be graded as the either-of-two-levels outcome they state
when the runner is next extended, and until a horizon closes in
the price source they cannot mature in any case.
"""

import json
import math
import os
import sys
from datetime import date, timedelta
from statistics import NormalDist, median

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(HERE)
PANEL_PATH = os.path.expanduser("~/workspace/morgue/data_cache/board_bt_bars.json")
BAND_PATH = os.path.join(HERE, "corrected-band", "data.json")
OUT_PATH = os.path.join(HERE, "touch-surface", "data.json")
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

ENGINE_ID = "engine_02"
SYMBOLS = ("SPY", "QQQ")
NAMES = {"SPY": "SPY (the big S&P 500 fund)",
         "QQQ": "QQQ (the big Nasdaq-100 fund)"}
K_BY_H = {1: 0.87, 5: 0.88, 21: 0.91}
HORIZONS = (1, 5, 21)
DISTANCES = (0.5, 1.0, 1.5)
SIDES = ("up", "down", "either")
WARMUP = 22
REGIME_WINDOW = 126
BUCKET_FLOOR = 30
EVAL_START = 150
EMPIRICAL_WEIGHT = 0.80
BARRIER_WEIGHT = 0.20
P_MIN, P_MAX = 0.01, 0.99
PROVING_TARGET = 100

_ND = NormalDist()


def fail(msg):
    print(f"Touch Surface refresh: {msg}", file=sys.stderr)
    return 1


def next_sessions(after_iso, count):
    d = date.fromisoformat(after_iso)
    out = []
    while len(out) < count:
        d += timedelta(days=1)
        if d.weekday() < 5:
            out.append(d.isoformat())
    return out


def har_annualised_vol(sq_returns, i):
    """Engine 1's recipe, verbatim: sq_returns[j] is the squared log
    return into closes[j+1]; forecast at base index i uses returns
    sq[i-22:i] only."""
    daily = sq_returns[i - 1]
    weekly = sum(sq_returns[i - 5:i]) / 5.0
    monthly = sum(sq_returns[i - WARMUP:i]) / WARMUP
    return math.sqrt(252.0 * (daily + weekly + monthly) / 3.0)


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


def barrier_estimate(d, side, h):
    p_single = 2.0 * _ND.cdf(-d * K_BY_H[h])
    if side == "either":
        return min(1.0, 2.0 * p_single)
    return p_single


def benchmark_p(d, side):
    p_single = 2.0 * _ND.cdf(-d)
    if side == "either":
        return min(1.0, 2.0 * p_single)
    return p_single


def cell_label(d, side):
    if side == "either":
        return f"either side {d:g}"
    return f"{'+' if side == 'up' else '-'}{d:g}"


def build():
    for path in (PANEL_PATH, BAND_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")
    with open(PANEL_PATH, "r", encoding="utf-8") as fh:
        panel = json.load(fh)
    with open(BAND_PATH, "r", encoding="utf-8") as fh:
        band_data = json.load(fh)

    # ---- Load and validate the panel (fails closed) ----
    series = {}
    for sym in SYMBOLS:
        rows = panel.get(sym) or []
        if len(rows) != len(panel[SYMBOLS[0]]):
            return fail(f"panel count disagreement: {sym} has "
                        f"{len(rows)} sessions, expected "
                        f"{len(panel[SYMBOLS[0]])} (the panel's own "
                        f"count; cure G2 2026-10-29)")
        dates = [r[0] for r in rows]
        if dates != sorted(dates) or len(set(dates)) != len(dates):
            return fail(f"panel dates for {sym} are not a clean "
                        f"increasing session list")
        closes = [float(r[4]) for r in rows]
        highs = [float(r[2]) for r in rows]
        lows = [float(r[3]) for r in rows]
        rets = [math.log(closes[i] / closes[i - 1])
                for i in range(1, len(closes))]
        sq = [r * r for r in rets]
        vols = [None] * len(closes)
        for i in range(WARMUP, len(closes)):
            vols[i] = har_annualised_vol(sq, i)
        regimes = [None] * len(closes)
        for i in range(WARMUP, len(closes)):
            window = [v for v in vols[max(WARMUP, i - REGIME_WINDOW + 1):i + 1]
                      if v is not None]
            regimes[i] = "jumpy" if vols[i] > median(window) else "calm"
        series[sym] = {"dates": dates, "closes": closes, "highs": highs,
                       "lows": lows, "vols": vols, "regimes": regimes}
    span = (series["SPY"]["dates"][0], series["SPY"]["dates"][-1])
    if (series["QQQ"]["dates"][0], series["QQQ"]["dates"][-1]) != span:
        return fail("panel span disagreement between SPY and QQQ")
    as_of = span[1]
    n = len(series["SPY"]["dates"])

    # ---- Fail closed on disagreement with Engine 1's bands ----
    if band_data.get("as_of_session") != as_of:
        return fail(f"Engine 1 band file is as of "
                    f"{band_data.get('as_of_session')}, panel ends {as_of}")
    band68 = {}
    for entry in band_data["live"]["names"]:
        for hz in entry["horizons"]:
            b = [x for x in hz["bands"] if x["level"] == 68][0]
            band68[(entry["symbol"], hz["sessions"])] = (b["lower"], b["upper"])
    # Engine 1's published live bands carry its FE12 session
    # quality guard widening when the guard is recorded (cure
    # 2026-10-30: the guard went live at factor 1.2838 and this
    # check, written while the guard stood not recorded, refused
    # the widened bands forever: SPY h=1 recomputed (765.97,
    # 772.75) against published (765.0, 773.72), which is the
    # recomputed half-width times 1.2838 to the cent on every
    # symbol and horizon). The comparison applies the factor
    # Engine 1 itself publishes, as the Completion Clock cure
    # does, and states it on the page.
    guard_factor = engine1_guard_factor(band_data)
    for sym in SYMBOLS:
        s = series[sym]
        for h in HORIZONS:
            half = s["vols"][-1] * math.sqrt(h / 252.0) * K_BY_H[h]
            expected = expected_published_edges(
                s["closes"][-1], half, guard_factor)
            if expected != band68[(sym, h)]:
                return fail(f"Engine 1 band disagreement for {sym} "
                            f"h={h}: recomputed {expected} "
                            f"(unwidened half-width times Engine 1 "
                            f"guard factor {guard_factor}) vs "
                            f"published {band68[(sym, h)]}")

    # ---- Precompute barriers and touch outcomes per base day ----
    # barriers[sym][h][i] = (up_by_d, down_by_d) dicts keyed by d
    # outcomes[sym][h][(d, side)][j] = bool, for j with j+h < n
    barriers, outcomes = {}, {}
    for sym in SYMBOLS:
        s = series[sym]
        barriers[sym], outcomes[sym] = {}, {}
        for h in HORIZONS:
            barriers[sym][h], outcomes[sym][h] = {}, {}
            for i in range(WARMUP, n):
                half = s["vols"][i] * math.sqrt(h / 252.0) * K_BY_H[h]
                barriers[sym][h][i] = (
                    {d: round(s["closes"][i] * (1.0 + d * half), 2)
                     for d in DISTANCES},
                    {d: round(s["closes"][i] * (1.0 - d * half), 2)
                     for d in DISTANCES})
            for d in DISTANCES:
                for side in SIDES:
                    col = {}
                    for j in range(WARMUP, n - h):
                        up = barriers[sym][h][j][0][d]
                        down = barriers[sym][h][j][1][d]
                        hit_up = any(s["highs"][t] >= up
                                     for t in range(j + 1, j + h + 1))
                        hit_down = any(s["lows"][t] <= down
                                       for t in range(j + 1, j + h + 1))
                        col[j] = (hit_up if side == "up" else
                                  hit_down if side == "down" else
                                  (hit_up or hit_down))
                    outcomes[sym][h][(d, side)] = col

    def empirical(sym, i, h, d, side):
        """(rate, bucket_n, bucket_level) from training days whose
        windows closed on or before day i. Walk-forward pure."""
        col = outcomes[sym][h][(d, side)]
        cand = [j for j in col if j + h <= i]
        regime_i = series[sym]["regimes"][i]
        same_regime = [j for j in cand
                       if series[sym]["regimes"][j] == regime_i]
        if len(same_regime) >= BUCKET_FLOOR:
            pool, level = same_regime, 1
        elif len(cand) >= BUCKET_FLOOR:
            pool, level = cand, 2
        else:
            pooled = []
            for s2 in SYMBOLS:
                col2 = outcomes[s2][h][(d, side)]
                pooled += [col2[j] for j in col2 if j + h <= i]
            if pooled:
                return sum(pooled) / len(pooled), len(pooled), 3
            return None, 0, 0
        return (sum(1 for j in pool if col[j]) / len(pool),
                len(pool), level)

    def forecast(sym, i, h, d, side):
        emp, bucket_n, bucket_level = empirical(sym, i, h, d, side)
        bar = barrier_estimate(d, side, h)
        if emp is None:
            p = bar
        else:
            p = EMPIRICAL_WEIGHT * emp + BARRIER_WEIGHT * bar
        p = min(max(p, P_MIN), P_MAX)
        return {"p": round(p, 4), "empirical": emp,
                "bucket_n": bucket_n, "bucket_level": bucket_level,
                "barrier_estimate": round(bar, 4),
                "benchmark": round(benchmark_p(d, side), 4)}

    # ---- Walk-forward history study (ledgers nothing) ----
    hist_cells = []
    pooled = {"n": 0, "brier_ours": 0.0, "brier_benchmark": 0.0}
    for sym in SYMBOLS:
        for h in HORIZONS:
            for d in DISTANCES:
                for side in SIDES:
                    col = outcomes[sym][h][(d, side)]
                    cnt = 0
                    sum_p = sum_y = sb = sbb = 0.0
                    for i in range(EVAL_START, n - h):
                        f = forecast(sym, i, h, d, side)
                        y = 1.0 if col[i] else 0.0
                        cnt += 1
                        sum_p += f["p"]
                        sum_y += y
                        sb += (f["p"] - y) ** 2
                        sbb += (f["benchmark"] - y) ** 2
                    expect = n - h - EVAL_START
                    if cnt != expect:
                        return fail(f"history count disagreement for "
                                    f"{sym} h={h} {side} {d}: {cnt} "
                                    f"!= {expect}")
                    cell = {
                        "symbol": sym, "horizon": h, "distance": d,
                        "side": side, "graded": cnt,
                        "touches": int(sum_y),
                        "realised_pct": round(sum_y / cnt * 100.0, 1),
                        "mean_forecast_pct": round(sum_p / cnt * 100.0, 1),
                        "brier_ours": (round(sb / cnt, 4)
                                       if cnt >= BUCKET_FLOOR else None),
                        "brier_benchmark": (round(sbb / cnt, 4)
                                            if cnt >= BUCKET_FLOOR else None),
                        "benchmark_pct": round(
                            benchmark_p(d, side) * 100.0, 1),
                    }
                    hist_cells.append(cell)
                    pooled["n"] += cnt
                    pooled["brier_ours"] += sb
                    pooled["brier_benchmark"] += sbb
    pooled_out = {
        "graded": pooled["n"],
        "brier_ours": round(pooled["brier_ours"] / pooled["n"], 4),
        "brier_benchmark": round(
            pooled["brier_benchmark"] / pooled["n"], 4),
    }

    # ---- Live forecasts from the freshest close ----
    future = next_sessions(as_of, 21)
    horizon_open = future[0]
    live = []
    for sym in SYMBOLS:
        s = series[sym]
        i = n - 1
        cells = []
        for h in HORIZONS:
            for d in DISTANCES:
                for side in SIDES:
                    f = forecast(sym, i, h, d, side)
                    up = barriers[sym][h][i][0][d]
                    down = barriers[sym][h][i][1][d]
                    cells.append({
                        "symbol": sym, "horizon": h, "distance": d,
                        "side": side, "label": cell_label(d, side),
                        "p": f["p"],
                        "p_pct": round(f["p"] * 100.0, 1),
                        "benchmark_p": f["benchmark"],
                        "benchmark_pct": round(f["benchmark"] * 100.0, 1),
                        "level_up": up, "level_down": down,
                        "level": (up if side == "up" else
                                  down if side == "down" else None),
                        "empirical_pct": (round(f["empirical"] * 100.0, 1)
                                          if f["empirical"] is not None
                                          else None),
                        "bucket_n": f["bucket_n"],
                        "horizon_close": future[h - 1],
                    })
        live.append({
            "symbol": sym, "name": NAMES[sym], "close": s["closes"][-1],
            "close_date": as_of, "regime": s["regimes"][i],
            "cells": cells,
        })

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
        "note": ("Touch probabilities from the close of the as-of "
                 "session, for the sessions starting on the horizon "
                 "open date. Expected-move units are Engine 1's 68 "
                 "percent band half-widths for the same horizon, "
                 "checked to the cent against Engine 1's published "
                 "bands before writing. No dealer-positioning split "
                 "is applied: no daily sign series on record covers "
                 "this panel."),
    }
    created = 0
    for entry in live:
        for c in entry["cells"]:
            if c["side"] == "either":
                outcome = {
                    "symbol": entry["symbol"], "kind": "touch",
                    "level": c["level_up"], "level_down": c["level_down"],
                    "either_side": True,
                    "window_open": horizon_open,
                    "window_close": c["horizon_close"],
                    "at_date": c["horizon_close"]}
            else:
                outcome = {
                    "symbol": entry["symbol"], "kind": "touch",
                    "level": c["level"],
                    "window_open": horizon_open,
                    "window_close": c["horizon_close"],
                    "at_date": c["horizon_close"]}
            quantity = (f"touch {c['label']} expected moves within "
                        f"{c['horizon']} sessions")
            row, was_created = led.append_forecast_declared(
                engine_id=ENGINE_ID,
                issued_ts=horizon_open,
                subject=entry["symbol"],
                quantity=quantity,
                value={"p": c["p"]},
                horizon_open=horizon_open,
                horizon_close=c["horizon_close"],
                lineage=lineage,
                families=["price", "distributional_volatility"],
                outcome=outcome,
            )
            if row.get("quantity") != quantity:
                # The ledger dedupe key merged this cell into a
                # different cell with the same rounded chance and
                # horizon. Write it with the cell name carried in
                # the value so it stays a distinct forecast.
                row, was_created = led.append_forecast_declared(
                    engine_id=ENGINE_ID,
                    issued_ts=horizon_open,
                    subject=entry["symbol"],
                    quantity=quantity,
                    value={"p": c["p"], "cell": quantity},
                    horizon_open=horizon_open,
                    horizon_close=c["horizon_close"],
                    lineage=lineage,
                    families=["price", "distributional_volatility"],
                    outcome=outcome,
                )
                if row.get("quantity") != quantity:
                    return fail(f"ledger write for {quantity} landed "
                                f"on a different forecast row")
            created += 1 if was_created else 0

    # ---- Figures recomputed from the ledger alone ----
    rows = led.rows()
    if not led.verify_chain(rows):
        return fail("the forecast record failed verification after "
                    "writing; not publishing figures from it")
    figures = ledger_mod.recompute_figures(rows)
    mine = figures.get(ENGINE_ID, {"forecasts": 0, "graded": 0})
    issue_days = len({
        r["lineage"]["clocks"]["decision_as_of"]
        for r in rows
        if r.get("type") == "forecast" and r.get("engine_id") == ENGINE_ID})
    if mine["forecasts"] != 54 * issue_days:
        return fail(f"ledger count disagreement: {mine['forecasts']} "
                    f"forecasts for {issue_days} issue days, expected "
                    f"{54 * issue_days}")
    if issue_days < 1:
        return fail("no live forecast was recorded")

    data = {
        "tool": "Touch Surface",
        "state": "proving",
        "as_of_session": as_of,
        "next_session": horizon_open,
        "source": ("Daily prices for SPY and QQQ from the price "
                   "history on record (399 trading days, March 25, "
                   "2025 to October 23, 2026), and the expected-move "
                   "bands published by the Corrected Band Engine "
                   "from the same history."),
        "live": {
            "issue_days": issue_days,
            "proving_target_sessions": PROVING_TARGET,
            "forecasts_recorded": mine["forecasts"],
            "forecasts_graded": mine["graded"],
            "names": live,
            "engine1_band_check": {
                "guard_widen_factor": guard_factor,
                "basis": ("Engine 1's published 68 percent band "
                          "edges matched to the cent after "
                          "applying the FE12 session quality "
                          "guard widen factor Engine 1 publishes "
                          "on its own page to the recomputed "
                          "unwidened half-width (factor 1.0 when "
                          "no guard widening is recorded). This "
                          "engine's own barriers stay on the "
                          "unwidened recipe.")},
            "positioning_split": {
                "state": "absent",
                "note": ("No split by dealer positioning is shown. "
                         "There is no daily record of whether options "
                         "dealers would speed up or slow down a move "
                         "covering these trading days, so the chances "
                         "above are not split that way, here or in the "
                         "history below."),
            },
        },
        "history": {
            "label": "History, not live forecasts",
            "span_start": span[0], "span_end": span[1],
            "sessions": 399,
            "evaluation_start": series["SPY"]["dates"][EVAL_START],
            "note": ("Worked out day by day over the price history on "
                     "record: each day's chances were built only from "
                     "earlier days whose touch results were already "
                     "known by that day, then checked against what "
                     "the highs and lows actually did. These are "
                     "study figures from the past, not the live "
                     "record above. The old model's score is worked "
                     "out on exactly the same days."),
            "cells": hist_cells,
            "pooled": pooled_out,
        },
        "kill_criterion": (
            "This tool is retired if, after 100 trading days of live "
            "forecasts for each index and each cell, its score is not "
            "better than the old model's score on the same days, or "
            "its stated chances are more than 10 points away from how "
            "often touches actually happened."),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH}: live as of {as_of}, {mine['forecasts']} "
          f"recorded forecasts ({created} new), {issue_days} issue "
          f"day(s); history pooled Brier ours "
          f"{pooled_out['brier_ours']} vs old model "
          f"{pooled_out['brier_benchmark']} over {pooled_out['graded']} "
          f"graded study cases")
    return 0


if __name__ == "__main__":
    sys.exit(build())
