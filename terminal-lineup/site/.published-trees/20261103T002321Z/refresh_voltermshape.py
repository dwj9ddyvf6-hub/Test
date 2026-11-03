#!/usr/bin/env python3
"""Refresh the Realised-Vol Term Shape Forecaster (Forecast Engine 7).

=====================================================================
CANDIDATE-REGISTER TRIPLE (written before any computation, per the
lineup's adopted standards)

1. EVIDENCE CLASS
   Study evidence on record: V1, grade A, the strongest volatility
   result in the record (recent-movement forecasting from its own
   past: long-scale explanatory gain +0.127 and +0.116, t 19 and
   20); V2, grade B (the volatility priced into options is the best
   single guide to later actual movement but runs high: actual
   divided by priced came to 0.87 for the most-traded names); V4,
   grade B (shapes forecast how much prices move, not which way).
   This engine's own live record: none before today; it starts here.

2. RECONSTRUCTION CHOICES (every constant, named before computing)
   - Recent-movement (HAR) recipe: EXACTLY the Corrected Band
     Engine's recipe, reused, never forked: daily log returns on
     closes; squared-return parts over the last 1, last 5 and last
     22 sessions ending at the base close; forecast daily variance
     = the equal-weight mean of the three parts; yearly-rate
     movement = sqrt(252 x forecast variance). A reading needs at
     least 22 prior returns.
   - Actual movement over the next h sessions at base day i:
     sqrt(252 x mean of the squared log returns of the h sessions
     after i). All movement figures are yearly rates.
   - Weekly cohorts: base days every 5 sessions, starting at the
     first day with a full recent-movement reading (session index
     22 of the history on record).
   - Percentile construction (the forecast): for a base day T and
     horizon h, the training cohorts are the earlier weekly
     cohorts j whose h-session outcome window had fully closed by
     T (j + h <= T). For each, the ratio of what actually happened
     to that day's recent-movement reading is collected. The
     published 25th, 50th and 75th percentiles for T are T's own
     recent-movement reading multiplied by the 25th, 50th and 75th
     percentiles of those ratios. Percentiles use straight-line
     interpolation between the two nearest sorted ratios (the
     common type-7 rule). At least 20 training cohorts are
     required, or no forecast is issued for that horizon.
   - Term-shape call: the chance that actual movement over the
     next 21 sessions exceeds actual movement over the next 5.
     Training cohorts are the earlier weekly cohorts whose
     21-session window had closed by T. They are split by whether
     their own recent week (last 5 sessions) was calmer than
     their own recent month (last 21 sessions) or not; today's
     call uses the split matching today's state, softened toward
     the overall training share with a prior strength of 20
     training cohorts: (split hits + 20 x overall share) /
     (split cohorts + 20), held inside 0.01 and 0.99.
   - The priced-volatility level prior (the design's 0.87
     correction): INCLUDED ONLY IF a real priced-volatility series
     with a usable span exists on record. What exists was measured
     before any forecast was computed: the volatility-index file
     on record holds 23 daily closes, September 21 to October 21,
     2026, for the S&P 500 index only; there is no Nasdaq-100
     priced-volatility series on record at all, and no priced
     series covers the 399-session history this engine is checked
     against. That span cannot set or be checked as a level prior
     across the record, so the prior is ABSENT, named absent on
     the page, the 0.87 correction is applied nowhere, and the
     recent-movement projection stands alone. The index file is
     read only to establish that absence and its dates.
   - Per-name leg: HISTORY-BUILDING ONLY, with a stale flag, per
     the design. The per-name priced-volatility record on record
     (the file behind the IV Weather page) stopped on October 14,
     2026, with 60 distinct names and at most 12 readings for any
     name. The design requires 20 fresh readings per name before
     any per-name forecast, so no per-name forecast is issued,
     for any name, and none is implied.
   - History evaluation: walk-forward over the same weekly
     cohorts on the history on record: each cohort's percentiles
     and shape call are built only from earlier cohorts whose
     outcome windows had closed by that cohort's day, then
     checked against what actually happened. Coverage for a
     percentile is the share of graded cohorts whose actual
     movement landed at or below the published percentile figure,
     shown beside its stated rate (25, 50 or 75). The shape call
     is scored with a Brier score (0 would be perfect; larger is
     worse). Nothing from the history run is written to the live
     ledger.
   - Thin-cell rule: any graded cell with fewer than 30 graded
     cohorts shows its count only, no percentage and no score.
   - Ledger shape: one row per fund per horizon carrying the
     three percentiles as a quantile set (the engine's registered
     grading rule), plus one row per fund for the shape call
     carrying its chance. Known grading note, stated like the
     earlier engines stated theirs: the shared grading runner
     cannot yet resolve an actual-movement outcome over a future
     window or the shape event, so both outcome specs carry the
     plain events stated and grading follows when the runner is
     next extended. No live row can mature until the price source
     passes its horizon close in any case.
   - Panel: the only daily history on record on this box is
     ~/workspace/morgue/data_cache/board_bt_bars.json (SPY and
     QQQ, 399 sessions each, March 25, 2025 to October 23, 2026).
     The 2010 to 2026 span in the design exists only as study
     summaries here, not as computable data, so the history
     evaluation runs on the 399-session record and says so.
     Nothing is claimed for 2010 to 2026 from this script.

3. NON-CLAIMS
   - No direction is forecast, ever. No claim about any single
     stock: the per-name leg publishes nothing.
   - The priced-volatility correction (0.87) is not applied
     anywhere in these numbers, because no usable priced series
     is on record; the page says so in plain words.
   - The earlier studies' figures (grade A and B rows above) are
     those studies' record, shown labelled as the studies'; they
     are not this engine's results.
   - The history evaluation is a backfill computed today, not a
     live record; it ledgers nothing. Weekly cohorts at the
     63-session horizon overlap each other, so its graded counts
     are not independent cases, and the page does not call them
     independent.

=====================================================================
Behaviour: walk-forward history evaluation over the shipped
history (ledgers nothing), then this week's live cohort for SPY
and QQQ ledgered through forecast/ledger.py append_forecast
(never hand-edited), then data.json written from the panel plus
figures recomputed from the ledger alone. Idempotent: rerunning
with the same panel appends nothing and rewrites the same
data.json. Fails closed on any disagreement with the sources or
the ledger. Timestamps come from the sources, never the clock.
"""

import json
import math
import os
import sys
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(HERE)
PANEL_PATH = os.path.expanduser("~/workspace/morgue/data_cache/board_bt_bars.json")
VIX_PATH = os.path.expanduser(
    "~/workspace/opt/rea-teardowns/azrael-1587/source/yahoo-vix-daily.json")
IV_PATH = os.path.join(HERE, "iv-weather", "data.json")
OUT_PATH = os.path.join(HERE, "vol-term-shape", "data.json")
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

ENGINE_ID = "engine_07"
SYMBOLS = ("SPY", "QQQ")
NAMES = {"SPY": "SPY (the big S&P 500 fund)",
         "QQQ": "QQQ (the big Nasdaq-100 fund)"}
HORIZONS = (5, 21, 63)
WARMUP = 22
STEP = 5
MIN_TRAIN = 20
PRIOR_STRENGTH = 20.0
P_MIN, P_MAX = 0.01, 0.99
THIN = 30
KILL_COHORTS = 52
PER_NAME_FRESH_NEEDED = 20

QUANTITIES = {
    5: "actual movement over the next 5 sessions, percentiles",
    21: "actual movement over the next 21 sessions, percentiles",
    63: "actual movement over the next 63 sessions, percentiles",
}
SHAPE_QUANTITY = ("actual movement over the next 21 sessions "
                  "exceeds actual movement over the next 5 sessions")


def fail(msg):
    print(f"Vol Term Shape refresh: {msg}", file=sys.stderr)
    return 1


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


def build_series(rows):
    dates = [r[0] for r in rows]
    closes = [float(r[4]) for r in rows]
    n = len(rows)
    sq = [math.log(closes[i] / closes[i - 1]) ** 2
          for i in range(1, n)]
    har = [None] * n
    for i in range(WARMUP, n):
        daily = sq[i - 1]
        weekly = sum(sq[i - 5:i]) / 5.0
        monthly = sum(sq[i - WARMUP:i]) / WARMUP
        har[i] = math.sqrt(252.0 * (daily + weekly + monthly) / 3.0)
    rv_future = {}
    for h in HORIZONS:
        col = [None] * n
        for i in range(n - h):
            col[i] = math.sqrt(252.0 * sum(sq[i:i + h]) / h)
        rv_future[h] = col
    trail = {}
    for h in (5, 21):
        col = [None] * n
        for i in range(h, n):
            col[i] = math.sqrt(252.0 * sum(sq[i - h:i]) / h)
        trail[h] = col
    return {"dates": dates, "closes": closes, "har": har,
            "rv_future": rv_future, "trail": trail, "n": n}


def weekly_cohorts(n):
    return list(range(WARMUP, n, STEP))


def forecast_at(s, t, h, cohorts):
    train = [j for j in cohorts if j + h <= t]
    if len(train) < MIN_TRAIN:
        return None, len(train)
    ratios = [s["rv_future"][h][j] / s["har"][j] for j in train]
    base = s["har"][t]
    return ({q: base * quantile(ratios, q)
             for q in (0.25, 0.5, 0.75)}, len(train))


def shape_at(s, t, cohorts):
    train = [j for j in cohorts if j + 21 <= t]
    if len(train) < MIN_TRAIN:
        return None, 0, None
    today_calmer = s["trail"][5][t] < s["trail"][21][t]
    overall_hits = sum(1 for j in train
                       if s["rv_future"][21][j] > s["rv_future"][5][j])
    overall = overall_hits / len(train)
    bucket = [j for j in train
              if (s["trail"][5][j] < s["trail"][21][j]) == today_calmer]
    hits = sum(1 for j in bucket
               if s["rv_future"][21][j] > s["rv_future"][5][j])
    p = (hits + PRIOR_STRENGTH * overall) / (len(bucket) + PRIOR_STRENGTH)
    p = min(max(p, P_MIN), P_MAX)
    info = {"bucket_cohorts": len(bucket), "training_cohorts": len(train),
            "today_calmer": today_calmer,
            "overall_pct": round(overall * 100.0, 1)}
    return p, len(train), info


def load_vix_span():
    with open(VIX_PATH, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    result = doc["chart"]["result"][0]
    days = []
    for ts, close in zip(result["timestamp"],
                         result["indicators"]["quote"][0]["close"]):
        if close is None:
            continue
        day = datetime.fromtimestamp(ts, tz=timezone.utc).date()
        days.append((day.isoformat(), float(close)))
    days.sort()
    return days


def build():
    for path in (PANEL_PATH, VIX_PATH, IV_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")
    with open(PANEL_PATH, "r", encoding="utf-8") as fh:
        panel = json.load(fh)
    series = {}
    # Panel-derived count (cure G17, 2026-10-29): the check binds
    # every symbol to the panel's own SPY count, the pattern
    # refresh_exceedance uses, instead of the hardcoded 399-session
    # register that froze this engine the day the G2 panel lane
    # advanced the panel past 2026-10-23.
    expected_sessions = len(panel.get("SPY") or [])
    for sym in SYMBOLS:
        rows = panel.get(sym) or []
        if len(rows) != expected_sessions:
            return fail(f"panel count disagreement: {sym} has "
                        f"{len(rows)} sessions, expected "
                        f"{expected_sessions} (the panel's own count)")
        dates = [r[0] for r in rows]
        if dates != sorted(dates) or len(set(dates)) != len(dates):
            return fail(f"panel dates for {sym} are not a clean "
                        f"increasing session list")
        series[sym] = build_series(rows)
    span = (series["SPY"]["dates"][0], series["SPY"]["dates"][-1])
    if (series["QQQ"]["dates"][0], series["QQQ"]["dates"][-1]) != span:
        return fail("panel span disagreement between SPY and QQQ")
    as_of = span[1]
    n = series["SPY"]["n"]
    cohorts = weekly_cohorts(n)

    # ---- Priced-volatility record: measured, prior absent ----
    vix_days = load_vix_span()
    vix_info = {
        "readings": len(vix_days),
        "first_date": vix_days[0][0] if vix_days else None,
        "last_date": vix_days[-1][0] if vix_days else None,
        "last_close": (round(vix_days[-1][1], 2) if vix_days else None),
    }
    # A usable prior needs a long span for both funds. Neither holds:
    # the index file is short and S&P-only; no Nasdaq-100 series exists.
    implied_prior_present = False

    # ---- Per-name priced-volatility record (building) ----
    with open(IV_PATH, "r", encoding="utf-8") as fh:
        iv = json.load(fh)
    per_name = {
        "names_on_record": iv["distinct_names"],
        "fullest_readings": iv["fullest_history"],
        "freshest_date": iv["freshest_date"],
        "oldest_date": iv.get("oldest_date"),
        "fresh_readings_needed": PER_NAME_FRESH_NEEDED,
    }
    # Source changed by ruling 2026-10-30 (engine refresh cure):
    # IV Weather now reads the modelled IV ledger, not the
    # retired 20-name lane this block's original counts (60
    # names, at most 12 readings) described. The block carries
    # the IV page's own figures verbatim and nothing here
    # computes from them, so the guard is presence and sanity,
    # not a pinned shape the accruing ledger would outgrow.
    if not isinstance(per_name["names_on_record"], int) \
            or per_name["names_on_record"] < 1 \
            or not isinstance(per_name["fullest_readings"], int) \
            or per_name["fullest_readings"] < 1 \
            or not per_name["freshest_date"]:
        return fail("per-name record does not hold together on "
                    "the IV page's own figures")

    # ---- Walk-forward history evaluation (ledgers nothing) ----
    hist_cells = []
    shape_cells = []
    for sym in SYMBOLS:
        s = series[sym]
        for h in HORIZONS:
            graded = 0
            below = {25: 0, 50: 0, 75: 0}
            for t in cohorts:
                if t + h > n - 1:
                    continue
                fc, ntrain = forecast_at(s, t, h, cohorts)
                if fc is None:
                    continue
                graded += 1
                realised = s["rv_future"][h][t]
                for level, q in ((25, 0.25), (50, 0.5), (75, 0.75)):
                    if realised <= fc[q]:
                        below[level] += 1
            first_train = MIN_TRAIN - 1
            expect = sum(
                1 for t in cohorts
                if t + h <= n - 1
                and sum(1 for j in cohorts if j + h <= t) >= MIN_TRAIN)
            if graded != expect:
                return fail(f"history count disagreement for {sym} "
                            f"h={h}: {graded} != {expect}")
            for level in (25, 50, 75):
                hist_cells.append({
                    "symbol": sym, "horizon": h, "percentile": level,
                    "stated_pct": level, "graded": graded,
                    "at_or_below": below[level],
                    "coverage_pct": (
                        round(below[level] / graded * 100.0, 1)
                        if graded >= THIN else None),
                })
        graded = 0
        brier_sum = 0.0
        events = 0
        for t in cohorts:
            if t + 21 > n - 1:
                continue
            p, ntrain, _info = shape_at(s, t, cohorts)
            if p is None:
                continue
            graded += 1
            y = 1.0 if s["rv_future"][21][t] > s["rv_future"][5][t] else 0.0
            events += int(y)
            brier_sum += (p - y) ** 2
        expect = sum(
            1 for t in cohorts
            if t + 21 <= n - 1
            and sum(1 for j in cohorts if j + 21 <= t) >= MIN_TRAIN)
        if graded != expect:
            return fail(f"history count disagreement for {sym} shape: "
                        f"{graded} != {expect}")
        shape_cells.append({
            "symbol": sym, "graded": graded, "events": events,
            "event_pct": (round(events / graded * 100.0, 1)
                          if graded >= THIN else None),
            "brier": (round(brier_sum / graded, 4)
                      if graded >= THIN else None),
        })

    # ---- Live cohort: the freshest close ----
    future = next_sessions(as_of, 63)
    horizon_open = future[0]
    t_live = n - 1
    live = []
    for sym in SYMBOLS:
        s = series[sym]
        horizons = []
        for h in HORIZONS:
            fc, ntrain = forecast_at(s, t_live, h, cohorts)
            if fc is None:
                return fail(f"live forecast for {sym} h={h} has only "
                            f"{ntrain} training cohorts")
            horizons.append({
                "sessions": h,
                "horizon_close": future[h - 1],
                "training_cohorts": ntrain,
                "p25": round(fc[0.25], 6), "p50": round(fc[0.5], 6),
                "p75": round(fc[0.75], 6),
                "p25_pct": round(fc[0.25] * 100.0, 1),
                "p50_pct": round(fc[0.5] * 100.0, 1),
                "p75_pct": round(fc[0.75] * 100.0, 1),
            })
        p, ntrain_shape, sinfo = shape_at(s, t_live, cohorts)
        if p is None:
            return fail(f"live shape call for {sym} has too little "
                        f"training history")
        live.append({
            "symbol": sym, "name": NAMES[sym],
            "close": s["closes"][-1], "close_date": as_of,
            "recent_movement_pct": round(s["har"][t_live] * 100.0, 1),
            "trailing_week_pct": round(s["trail"][5][t_live] * 100.0, 1),
            "trailing_month_pct": round(s["trail"][21][t_live] * 100.0, 1),
            "horizons": horizons,
            "shape": {
                "p": round(p, 4), "p_pct": round(p * 100.0, 1),
                "horizon_close": future[20],
                "training_cohorts": ntrain_shape,
                "bucket_cohorts": sinfo["bucket_cohorts"],
                "recent_week_calmer": sinfo["today_calmer"],
                "overall_training_pct": sinfo["overall_pct"],
            },
        })

    # ---- Ledger the live cohort (API only, never by hand) ----
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
            {"path": VIX_PATH,
             "sha256": ledger_mod.file_sha256(VIX_PATH)},
            {"path": IV_PATH,
             "sha256": ledger_mod.file_sha256(IV_PATH)},
        ],
        "clocks": {
            "event_time": as_of,
            "publication_time": horizon_open,
            "first_available_time": as_of,
            "ingestion_time": as_of,
            "decision_as_of": as_of,
        },
        "note": ("Weekly cohort from the close of the as-of session, "
                 "for the sessions starting on the horizon open date. "
                 "The priced-volatility index file on record holds "
                 f"{vix_info['readings']} closes, "
                 f"{vix_info['first_date']} to {vix_info['last_date']}, "
                 "for the S&P 500 index only; it was read only to "
                 "establish that no usable priced level prior exists, "
                 "and it changed no number. The per-name priced "
                 "record was read only for its stale counts."),
    }
    created = 0
    for entry in live:
        sym = entry["symbol"]
        for hz in entry["horizons"]:
            h = hz["sessions"]
            row, was_created = led.append_forecast_declared(
                engine_id=ENGINE_ID,
                issued_ts=horizon_open,
                subject=sym,
                quantity=QUANTITIES[h],
                value={"quantiles": {"0.25": hz["p25"],
                                     "0.5": hz["p50"],
                                     "0.75": hz["p75"]}},
                horizon_open=horizon_open,
                horizon_close=hz["horizon_close"],
                lineage=lineage,
                families=["distributional_volatility", "price"],
                outcome={"symbol": sym, "kind": "realised_vol",
                         "base_date": as_of,
                         "window_open": horizon_open,
                         "window_close": hz["horizon_close"],
                         "sessions": h},
            )
            if row.get("quantity") != QUANTITIES[h]:
                return fail(f"ledger write for {sym} h={h} landed on "
                            f"a different forecast row")
            created += 1 if was_created else 0
        sh = entry["shape"]
        row, was_created = led.append_forecast_declared(
            engine_id=ENGINE_ID,
            issued_ts=horizon_open,
            subject=sym,
            quantity=SHAPE_QUANTITY,
            value={"p": sh["p"]},
            horizon_open=horizon_open,
            horizon_close=sh["horizon_close"],
            lineage=lineage,
            families=["distributional_volatility", "price"],
            outcome={"symbol": sym, "kind": "vol_shape",
                     "base_date": as_of,
                     "window_open": horizon_open,
                     "window_close": sh["horizon_close"],
                     "sessions": 21,
                     "event": ("21-session actual movement exceeds "
                               "5-session actual movement")},
        )
        if row.get("quantity") != SHAPE_QUANTITY:
            return fail(f"ledger write for {sym} shape landed on a "
                        f"different forecast row")
        created += 1 if was_created else 0

    # ---- Figures recomputed from the ledger alone ----
    rows = led.rows()
    if not led.verify_chain(rows):
        return fail("the forecast record failed verification after "
                    "writing; not publishing figures from it")
    figures = ledger_mod.recompute_figures(rows)
    mine = figures.get(ENGINE_ID, {"forecasts": 0, "graded": 0})
    cohort_dates = sorted({
        r["lineage"]["clocks"]["decision_as_of"]
        for r in rows
        if r.get("type") == "forecast" and r.get("engine_id") == ENGINE_ID})
    if mine["forecasts"] != 8 * len(cohort_dates):
        return fail(f"ledger count disagreement: {mine['forecasts']} "
                    f"forecasts for {len(cohort_dates)} weekly "
                    f"cohorts, expected {8 * len(cohort_dates)}")
    if not cohort_dates:
        return fail("no live cohort was recorded")

    data = {
        "tool": "Vol Term Shape Forecaster",
        "state": "proving",
        "as_of_session": as_of,
        "next_session": horizon_open,
        "source": (f"Daily closing prices for SPY and QQQ from the "
                   f"price history on record ({n} trading days, "
                   f"{span[0]} to {span[1]}). The "
                   "volatility priced into S&P 500 options is on "
                   "record for only 23 days, September 21 to "
                   "October 21, 2026, and no such series for QQQ is "
                   "on record, so no priced level is used in these "
                   "numbers."),
        "live": {
            "weekly_cohorts_recorded": len(cohort_dates),
            "kill_target_cohorts": KILL_COHORTS,
            "forecasts_recorded": mine["forecasts"],
            "forecasts_graded": mine["graded"],
            "names": live,
            "implied_prior": {
                "state": "absent",
                "readings": vix_info["readings"],
                "first_date": vix_info["first_date"],
                "last_date": vix_info["last_date"],
                "last_close": vix_info["last_close"],
                "note": ("The design for this page calls for the "
                         "volatility priced into options, corrected "
                         "by the measured 0.87 factor, to guide the "
                         "level of these bands. That priced series "
                         "is not on record in a usable form: the "
                         "index file holds 23 daily closes, "
                         "September 21 to October 21, 2026, for the "
                         "S&P 500 only, and nothing at all for QQQ. "
                         "Twenty-three days cannot set a level for "
                         f"a record that runs {n} trading days, so "
                         "the correction is not applied and these "
                         "bands are built from actual past movement "
                         "alone."),
            },
            "per_name": {
                "state": "history_building",
                "names_on_record": per_name["names_on_record"],
                "fullest_readings": per_name["fullest_readings"],
                "freshest_date": per_name["freshest_date"],
                "oldest_date": per_name["oldest_date"],
                "fresh_readings_needed": per_name[
                    "fresh_readings_needed"],
                "note": ("Bands for single stocks are not published. "
                         "The record of priced volatility for single "
                         f"stocks is current to "
                         f"{per_name['freshest_date']} and holds "
                         f"{per_name['names_on_record']} names with "
                         f"at most {per_name['fullest_readings']} "
                         "readings each. This engine needs 20 fresh "
                         "readings for a name before it will publish "
                         "a band for that name, so the single-stock "
                         "part of this page is still building its "
                         "history."),
            },
        },
        "history": {
            "label": "History, not live forecasts",
            "span_start": span[0], "span_end": span[1],
            "sessions": n,
            "note": ("Worked out week by week over the price history "
                     "on record: each week's bands were built only "
                     "from earlier weeks whose results were already "
                     "known by then, then checked against what "
                     "actually happened. Weeks are counted every 5 "
                     "trading days, so the longer stretches overlap "
                     "each other and the counts are not separate "
                     "independent cases. These are study figures "
                     "from the past, not the live record above."),
            "cells": hist_cells,
            "shape_cells": shape_cells,
            "study_record": {
                "note": ("The earlier study this engine is built "
                         "from found that how much prices have been "
                         "moving is the strongest guide to how much "
                         "they will move next, across every stretch "
                         "it tested. That is the study's result, "
                         "from its own longer history. It is the "
                         "reason this engine exists; it is not this "
                         "engine's result."),
            },
        },
        "kill_criterion": (
            "This tool is retired if, after 52 weekly sets of "
            "forecasts have been graded, the share of times actual "
            "movement landed at or below a stated percentile misses "
            "that percentile's rate by more than 10 points at two "
            "or more of the three stretches (5, 21 and 63 trading "
            "days)."),
        "thin_cell_rule": (
            "Any graded cell with fewer than 30 graded weeks shows "
            "its count only, with no percentage and no score."),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH}: live weekly cohort as of {as_of}, "
          f"{mine['forecasts']} recorded forecasts ({created} new), "
          f"{len(cohort_dates)} of {KILL_COHORTS} weekly cohorts; "
          f"history cells {len(hist_cells)} over {span[0]} to "
          f"{span[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
