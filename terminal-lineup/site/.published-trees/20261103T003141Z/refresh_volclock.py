#!/usr/bin/env python3
"""Refresh the Own-Volatility Normalisation Clock (Forecast Engine 14).

=====================================================================
CANDIDATE-REGISTER TRIPLE (written before any computation, per the
lineup's adopted standards)

CORRECTION RECORD (2026-10-28): this build corrects the first build,
which an independent check found deviating from the construction
registered at inspection in three named ways:
  (A) the first build measured movement as a root-mean-square,
      sqrt(252 x mean of squared log returns); the registered
      measure, restored here, is the sample standard deviation
      (ddof 1) of the last 10 daily log close-to-close returns
      x sqrt(252);
  (B) the first build used an own library at 8 or more past times
      and a pooled size-band x jaggedness-half cell with a floor
      of 20; the registered rule, restored here, is an own library
      at 5 or more prior matured episodes, else a pooled
      spike-size-tercile library with a floor of 100 episodes,
      else abstain, counted;
  (C) the first build substituted a pooled median as the plain
      comparison where a name had no plain figure of its own; the
      registered baseline, restored here, is the name's OWN
      unconditional median over all its own past matured episodes
      only. A name with no own past matured episode carries NO
      plain figure anywhere: it is excluded from every plain and
      average-error figure, and it is never shown a plain figure.
The first build's 26 ledger forecasts are voided by correction
rows through the ledger machinery (never by hand) and superseded
by the corrected issue from this build.

1. EVIDENCE CLASS
   Study evidence on record: V1, grade A (how much prices have been
   moving, forecast from movement's own past, is the strongest
   volatility result in the record: long-scale explanatory gain
   +0.127 and +0.116, t 19 and 20); V4, grade B (shapes and weak
   internals forecast how much prices move, not which way); AD-56
   (the calibration method for stated bands, transferred here from
   index bands to per-name decay times); V6, grade C (snap-back
   size on fear days scales with a name's own jaggedness) - a
   covariate only, never a driver, and NOT a split in the library
   rule below. This engine's own live record: none before today;
   it starts here. No direction is forecast anywhere in this
   engine.

2. RECONSTRUCTION CHOICES (every constant, named before computing)
   - Movement (realised vol) for a name on a session: the sample
     standard deviation (ddof 1) of the last 10 daily log
     close-to-close returns ending that session, x sqrt(252),
     annualised (the annualising factor cancels in every
     percentile comparison and is stated for readability). The
     first movement reading for a name is its 11th session
     (10 returns).
   - THE WINDOW DIFFERENCE, stated plainly: the design calls for
     each name's movement to be judged against its own 3-year
     (about 750-session) movement history. That long history is
     NOT on this disk. The shipped daily history on record
     (~/workspace/morgue/data_cache/board_bt_bars.json) holds at
     most 399 sessions per name (March 25, 2025 to October 23,
     2026), so the longest own-history window any name can offer
     is 388 earlier movement readings. This engine therefore
     judges each name against the EXPANDING trailing set of ALL
     of its prior movement readings on record, today left out,
     exactly as registered at inspection, and the page names the
     actual window in plain words wherever the design's three
     years would otherwise be implied. Nothing is silently
     shortened: the register, the data file and the page all
     carry this difference and its reason.
   - Minimum-reading floor: a name is judged on a session only
     when at least 126 of its own earlier movement readings exist
     (leave-today-out: today's reading is never in its own
     comparison set). Names below that floor are set aside and
     counted, with the reason.
   - Own usual level and own high line for a session: the middle
     (median) and the 90th percentile of those earlier readings,
     percentiles by straight-line interpolation between the two
     nearest sorted readings (the common type-7 rule).
   - Spike and episode: a spike session is one whose movement
     reading is strictly above its own high line (the type-7
     90th percentile of its own prior readings). An EPISODE is
     the first spike session after a non-spike session (a run of
     spike sessions is one episode, never re-ledgered). A name
     whose movement is already above its high line at its latest
     session because its episode started earlier is counted as
     already running, and no new forecast is made for it.
   - Normalisation, exact: the first later session whose movement
     reading is strictly below the usual level (median) frozen
     at spike time (the median of the same trailing distribution
     that called the spike); sessions until = that session's
     distance in sessions from the spike session. Censoring: at
     spike + 63 sessions; a censored case stays in the coverage
     denominator as a band miss when the band's top (90th
     percentile forecast) is under 63 (when the band's top
     reaches 63 or beyond, the censored case, whose true time is
     past 63, is counted inside the band). An episode with under
     63 sessions available at the end of the record and no
     normalisation seen is unresolved at panel end, never counted
     as matured or censored.
   - The forecast for an episode (a middle figure and a
     low-to-high band, in sessions): the type-7 10th/50th/90th
     percentiles of a library of past normalisation times chosen
     by this registered rule, fixed in advance:
       (a) the name's OWN library, when the name has at least 5
           prior matured episodes (its own past normalisation
           times, already known by the spike day: a past episode
           counts only once its normalisation session is on
           record; censored episodes supply no time, because
           their true time is past 63 and unknown);
       (b) else a POOLED library: matured episodes from all
           names, already known by the spike day, whose spike
           size in own units (spike movement divided by its own
           frozen median) falls in the same third of the pooled
           spike-size distribution as today's spike. The third
           edges, computed from the pooled matured record and
           stamped here before any live forecast is computed,
           are 1.6312 and 1.9255 (type-7 thirds of the spike
           sizes of all 7,595 matured episodes in the panel).
           Pool floor: 100 episodes;
       (c) else the engine abstains for this episode and the
           abstention is counted with its reason.
   - The plain comparison (baseline), exact: the name's own
     unconditional normalisation time = the median duration over
     ALL of that name's own past matured episodes already known
     by the spike day, no conditioning on spike size or decay.
     Names with no own past matured episode have NO baseline:
     they may still receive a pooled-library band under rule (b),
     but they carry no plain figure anywhere, in the history
     figures or on the page.
   - Claim test, exact: the forecast median's average absolute
     error at most 0.8 x the plain figure's average absolute
     error (the at-least-20-percent bar), computed over the
     PAIRED own-baseline subset only: episodes that matured,
     received a band, and had an own baseline. The kill test as
     registered is weaker (the middle figure's average error no
     better than the plain figure's at all, after 200 matured)
     and both bars are printed as written.
   - The claims under test, printed on the page: (1) the real
     normalisation time falls inside the published low-to-high
     band 80 percent of the time, give or take 5 points; (2) the
     forecast's middle figure beats the plain comparison above
     by at least 20 percent in average absolute error.
   - History evaluation: walk-forward over every episode in the
     history on record. Each episode's forecast and plain
     comparison are built only from episodes already known by
     that episode's day, then checked against what actually
     happened. Coverage counts every gradeable episode (matured
     or censored) that received a band, with the censoring rule
     above. Average absolute errors run over the paired
     own-baseline subset only, as registered. Nothing from the
     history run is written to the live ledger.
   - Thin-cell rule: any graded group with fewer than 30 graded
     cases shows its count only, with no percentage and no
     error figure.
   - Ledger shape: one forecast per name whose episode starts at
     its latest session on record, carrying the three percentiles
     as a quantile set (the engine's registered grading rule),
     its plain comparison figure (or no figure, as registered)
     and its library source and count inside the value. Known
     grading note, stated like the earlier engines stated
     theirs: the shared grading runner cannot yet resolve a
     sessions-to-normalisation outcome, so the outcome spec
     carries the plain event stated and grading follows when
     the runner is next extended. No live row can mature until
     the price source passes its horizon in any case. The
     horizon close written on each row is the 63rd weekday
     after the spike day (the censor date).
   - Panel: the only daily history on record on this box is the
     shipped panel above: 1,833 names including the broad
     market fund, at most 399 sessions each. Every name in the
     panel is checked, the fund included, because this engine
     is per name and the fund is a name here. A name is judged
     at its own latest session on record; most names' latest
     session is the panel's freshest session, and the few whose
     history ends earlier are counted at their own last session
     and named with that date wherever they appear.

3. NON-CLAIMS
   - No direction, no price level, and no claim that a spike
     ending sooner or later is good or bad for anyone holding
     the name.
   - The 3-year own-history window in the design is not claimed
     anywhere: the actual window is the expanding trailing own
     history inside a 399-session record, with a 126-reading
     floor, and the page says so.
   - The earlier studies' figures are those studies' record,
     labelled as such; they are not this engine's results.
   - The history evaluation is a backfill computed today, not
     a live record; it ledgers nothing.

=====================================================================
Behaviour: walk-forward history evaluation over the shipped
history (ledgers nothing), then the corrected live cohort
ledgered through forecast/ledger.py only (correction rows voiding
the first build's forecasts first, then append_forecast; the
ledger file is never hand-edited), then data.json written from
the panel plus figures recomputed from the ledger alone.
Idempotent: rerunning with the same panel appends nothing new
beyond the one correction set and the one corrected cohort, and
rewrites the same data.json. Fails closed on any disagreement
with the sources or the ledger. Timestamps come from the
sources, never the clock.
"""

import bisect
import json
import math
import os
import statistics
import sys
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(HERE)
PANEL_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")
OUT_PATH = os.path.join(HERE, "vol-clock", "data.json")
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

ENGINE_ID = "engine_14"
MIN_HIST = 126
CENSOR = 63
OWN_MIN = 5
POOL_MIN = 100
TERCILE_EDGES = (1.6312302840519397, 1.9254924109967222)
THIN = 30
KILL_MATURED = 200
QUANTITY = ("sessions until the name's 10-session movement "
            "returns below its own usual level")
VOID_NOTE = ("Void: issued under a deviating construction, "
             "superseded by the corrected issue")
VOID_REASON = ("issued under a deviating construction, "
               "superseded by the corrected issue")


def fail(msg):
    print(f"Vol Clock refresh: {msg}", file=sys.stderr)
    return 1


def quantile_sorted(s, q):
    pos = q * (len(s) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return s[lo]
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def tercile_of(ratio):
    if ratio <= TERCILE_EDGES[0]:
        return 0
    if ratio <= TERCILE_EDGES[1]:
        return 1
    return 2


def next_weekdays(after_iso, count):
    d = date.fromisoformat(after_iso)
    out = []
    while len(out) < count:
        d += timedelta(days=1)
        if d.weekday() < 5:
            out.append(d.isoformat())
    return out


def build_name(sym, rows):
    """Return (episodes, today_info) for one name."""
    dates = [r[0] for r in rows]
    closes = [float(r[4]) for r in rows]
    n = len(rows)
    rets = [None] * n
    for i in range(1, n):
        rets[i] = math.log(closes[i] / closes[i - 1])
    rv = [None] * n
    for i in range(10, n):
        rv[i] = statistics.stdev(rets[i - 9:i + 1]) * math.sqrt(252.0)
    hist = []  # sorted earlier movement readings
    episodes = []
    prev_spike = False
    today = None
    for t in range(n):
        if rv[t] is None:
            continue
        if len(hist) >= MIN_HIST:
            p90 = quantile_sorted(hist, 0.9)
            med = quantile_sorted(hist, 0.5)
            spike = rv[t] > p90
            if t == n - 1:
                today = {
                    "symbol": sym, "date": dates[t],
                    "sessions_on_record": n,
                    "earlier_readings": len(hist),
                    "rv": rv[t], "p90": p90, "median": med,
                    "spike": spike, "start": bool(
                        spike and not prev_spike),
                    "ratio": rv[t] / med,
                }
            if spike and not prev_spike:
                norm = None
                for k in range(1, CENSOR + 1):
                    if t + k < n and rv[t + k] is not None \
                            and rv[t + k] < med:
                        norm = k
                        break
                complete = norm is not None or (t + CENSOR < n)
                if norm is not None:
                    res_date = dates[t + norm]
                elif complete:
                    res_date = dates[t + CENSOR]
                else:
                    res_date = None
                episodes.append({
                    "symbol": sym, "date": dates[t], "t": t,
                    "ratio": rv[t] / med,
                    "norm": norm, "complete": complete,
                    "res_date": res_date,
                })
            prev_spike = spike
        else:
            if t == n - 1:
                today = {
                    "symbol": sym, "date": dates[t],
                    "sessions_on_record": n,
                    "earlier_readings": len(hist),
                    "rv": rv[t], "p90": None, "median": None,
                    "spike": False, "start": False,
                    "ratio": None,
                }
        bisect.insort(hist, rv[t])
    if today is None:  # name too short to have any movement reading
        today = {"symbol": sym, "date": dates[-1] if dates else None,
                 "sessions_on_record": n, "earlier_readings": 0,
                 "rv": None, "p90": None, "median": None,
                 "spike": False, "start": False, "ratio": None}
    return episodes, today


class Libraries:
    """Past matured-episode times known by a given day, sorted."""

    def __init__(self):
        self.by_tercile = {}    # tercile -> sorted times
        self.own = {}           # symbol -> sorted times

    def add(self, ep):
        if ep["norm"] is None:
            return
        v = float(ep["norm"])
        bisect.insort(
            self.by_tercile.setdefault(tercile_of(ep["ratio"]), []), v)
        bisect.insort(self.own.setdefault(ep["symbol"], []), v)

    def forecast(self, sym, ratio):
        own = self.own.get(sym, [])
        if len(own) >= OWN_MIN:
            return own, "own", len(own)
        pool = self.by_tercile.get(tercile_of(ratio), [])
        if len(pool) >= POOL_MIN:
            return pool, "pooled_same_size", len(pool)
        return None, "too_few_past_spikes", len(pool)

    def baseline(self, sym):
        own = self.own.get(sym, [])
        if own:
            return quantile_sorted(own, 0.5)
        return None

    def own_count(self, sym):
        return len(self.own.get(sym, []))


def band_of(sorted_times):
    return (quantile_sorted(sorted_times, 0.1),
            quantile_sorted(sorted_times, 0.5),
            quantile_sorted(sorted_times, 0.9))


def build():
    if not os.path.exists(PANEL_PATH):
        return fail(f"source not found: {PANEL_PATH}")
    with open(PANEL_PATH, "r", encoding="utf-8") as fh:
        panel = json.load(fh)
    if len(panel) != 1833:
        return fail(f"panel name count disagreement: {len(panel)}, "
                    f"expected 1833")
    spy_rows = panel.get("SPY") or []
    if len(spy_rows) < 399:
        return fail(f"panel count disagreement: SPY has "
                    f"{len(spy_rows)} sessions, expected at least "
                    f"the original 399 (cure G2 2026-10-29)")
    span = (spy_rows[0][0], spy_rows[-1][0])
    as_of = span[1]
    # Source-string cure (VOLCLOCK-SOURCE-20261031): the published
    # source description is computed from the panel actually read
    # (name count, the longest per-name session count, and the
    # SPY span), as refresh_voltermshape.py already does. The
    # earlier string was hardcoded to the original 399-session
    # panel and stayed six sessions stale after the panel lane
    # advanced it.
    max_sessions = max(len(rows) for rows in panel.values())
    long_span = (
        date.fromisoformat(span[0]).strftime("%B %d, %Y")
        .replace(" 0", " ")
        + " to "
        + date.fromisoformat(span[1]).strftime("%B %d, %Y")
        .replace(" 0", " "))

    all_episodes = []
    todays = {}
    for sym in sorted(panel):
        rows = panel[sym]
        dates = [r[0] for r in rows]
        if dates != sorted(dates) or len(set(dates)) != len(dates):
            return fail(f"panel dates for {sym} are not a clean "
                        f"increasing session list")
        eps, today = build_name(sym, rows)
        all_episodes.extend(eps)
        todays[sym] = today

    matured_eps = [e for e in all_episodes if e["norm"] is not None]
    censored_eps = [e for e in all_episodes
                    if e["norm"] is None and e["complete"]]
    unresolved_eps = [e for e in all_episodes if not e["complete"]]

    # ---- Walk-forward history evaluation (ledgers nothing) ----
    by_date = sorted(all_episodes, key=lambda e: e["date"])
    by_res = sorted(matured_eps, key=lambda e: e["res_date"])
    libs = Libraries()
    ptr = 0
    graded = hits = censored = pending = abstained = 0
    mae_f = mae_b = 0.0
    mae_n = 0
    src_counts = {}
    for ep in by_date:
        while ptr < len(by_res) and by_res[ptr]["res_date"] <= ep["date"]:
            libs.add(by_res[ptr])
            ptr += 1
        if not ep["complete"]:
            pending += 1
            continue
        lib, src, _cnt = libs.forecast(ep["symbol"], ep["ratio"])
        if lib is None:
            abstained += 1
            continue
        lo, medf, hi = band_of(lib)
        base = libs.baseline(ep["symbol"])
        src_counts[src] = src_counts.get(src, 0) + 1
        graded += 1
        if ep["norm"] is None:
            censored += 1
            if hi >= CENSOR:
                hits += 1
        else:
            if lo <= ep["norm"] <= hi:
                hits += 1
            if base is not None:
                mae_f += abs(medf - ep["norm"])
                mae_b += abs(base - ep["norm"])
                mae_n += 1
    hist = {
        "graded": graded, "hits": hits, "censored": censored,
        "pending": pending, "abstained": abstained,
        "episodes_total": len(all_episodes),
        "matured_episodes": len(matured_eps),
        "censored_episodes": len(censored_eps),
        "unresolved_episodes": len(unresolved_eps),
        "coverage_pct": (round(hits / graded * 100.0, 1)
                         if graded >= THIN else None),
        "mae_forecast": (round(mae_f / mae_n, 2) if mae_n >= THIN
                         else None),
        "mae_baseline": (round(mae_b / mae_n, 2) if mae_n >= THIN
                         else None),
        "mae_cases": mae_n,
        "source_counts": src_counts,
    }
    if mae_n >= THIN and mae_b > 0:
        hist["mae_improvement_pct"] = round(
            (1.0 - (mae_f / mae_n) / (mae_b / mae_n)) * 100.0, 1)
    else:
        hist["mae_improvement_pct"] = None

    # ---- Live cohort: episode starts at each name's latest ----
    # ---- session on record (most names: the freshest session) ----
    on_as_of = {s: t for s, t in todays.items() if t["date"] == as_of}
    checked = len(on_as_of)
    below_floor = sorted(
        s for s, t in on_as_of.items()
        if t["earlier_readings"] < MIN_HIST)
    earlier_last = sorted(
        ({"symbol": s, "last_session": t["date"]}
         for s, t in todays.items() if t["date"] != as_of),
        key=lambda x: x["symbol"])
    in_spike = sorted(s for s, t in todays.items() if t["spike"])
    starts = sorted(s for s, t in todays.items() if t["start"])
    already_running = sorted(set(in_spike) - set(starts))

    def libs_at(day):
        out = Libraries()
        for ep in by_res:
            if ep["res_date"] <= day:
                out.add(ep)
            else:
                break
        return out

    live_names = []
    live_abstained = []
    for sym in starts:
        t = todays[sym]
        day_libs = libs_at(t["date"])
        lib, src, cnt = day_libs.forecast(sym, t["ratio"])
        if lib is None:
            live_abstained.append({
                "symbol": sym, "spike_session": t["date"],
                "reason": "too_few_past_spikes",
                "past_spikes_known": cnt})
            continue
        lo, medf, hi = band_of(lib)
        base = day_libs.baseline(sym)
        live_names.append({
            "symbol": sym,
            "spike_session": t["date"],
            "movement_pct": round(t["rv"] * 100.0, 1),
            "usual_pct": round(t["median"] * 100.0, 1),
            "high_line_pct": round(t["p90"] * 100.0, 1),
            "times_usual": round(t["ratio"], 2),
            "band_low": round(lo, 1), "median_sessions": round(medf, 1),
            "band_high": round(hi, 1),
            "plain_median_sessions": (
                round(base, 1) if base is not None else None),
            "library_source": src,
            "library_spikes": cnt,
            "own_past_spikes": day_libs.own_count(sym),
        })
    live_names.sort(key=lambda x: x["symbol"])

    # ---- Ledger cure, through the machinery API only ----
    reg = registry_mod.load()
    led = ledger_mod.Ledger(
        os.path.join(LINEUP, "forecast", "ledger.jsonl"), registry=reg)
    if not led.verify_chain():
        return fail("the forecast record does not verify; refusing "
                    "to add to it")
    rows_before = led.rows()
    corrected_ids = {
        r.get("corrects_row_id") for r in rows_before
        if r.get("type") == "correction"}
    voided = 0
    for row in rows_before:
        if row.get("type") != "forecast" \
                or row.get("engine_id") != ENGINE_ID:
            continue
        src = (row.get("value") or {}).get("library_source")
        if src in ("own", "pooled_same_size"):
            continue  # already a corrected-construction row
        if row["row_id"] in corrected_ids:
            continue  # already voided by an earlier run
        led.append_correction(
            corrects_row_id=row["row_id"],
            note=VOID_NOTE,
            payload={"engine_id": ENGINE_ID, "reason": VOID_REASON,
                     "superseded_by": "corrected issue, registered "
                                      "construction"})
        voided += 1

    lineage = {
        "source_artifacts": [
            {"path": PANEL_PATH,
             "sha256": ledger_mod.file_sha256(PANEL_PATH)},
        ],
        "clocks": {
            "event_time": as_of,
            "publication_time": None,
            "first_available_time": as_of,
            "ingestion_time": as_of,
            "decision_as_of": as_of,
        },
        "note": ("Spike start at the close of the name's latest "
                 "session on record. Each name is judged against "
                 "all of its earlier movement readings on record "
                 "(at least 126), not a 3-year window: the shipped "
                 f"history holds at most {max_sessions} sessions "
                 "per name. "
                 "Corrected issue under the registered "
                 "construction (sample standard deviation of the "
                 "last 10 daily log returns; own library at 5 or "
                 "more prior matured episodes, else the pooled "
                 "spike-size-third library with a floor of 100; "
                 "plain figure from the name's own past only)."),
    }
    created = 0
    for entry in live_names:
        sym = entry["symbol"]
        spike_day = entry["spike_session"]
        future = next_weekdays(spike_day, CENSOR)
        horizon_open = future[0]
        horizon_close = future[-1]
        row_lineage = dict(lineage)
        row_lineage["clocks"] = dict(lineage["clocks"])
        row_lineage["clocks"]["event_time"] = spike_day
        row_lineage["clocks"]["publication_time"] = horizon_open
        row_lineage["clocks"]["first_available_time"] = spike_day
        row_lineage["clocks"]["ingestion_time"] = spike_day
        row_lineage["clocks"]["decision_as_of"] = spike_day
        row, was_created = led.append_forecast_declared(
            engine_id=ENGINE_ID,
            issued_ts=horizon_open,
            subject=sym,
            quantity=QUANTITY,
            value={
                "quantiles": {
                    "0.1": entry["band_low"], "0.5":
                    entry["median_sessions"], "0.9":
                    entry["band_high"]},
                "plain_median_sessions":
                    entry["plain_median_sessions"],
                "library_source": entry["library_source"],
                "library_spikes": entry["library_spikes"],
                "own_past_spikes": entry["own_past_spikes"],
            },
            horizon_open=horizon_open,
            horizon_close=horizon_close,
            lineage=row_lineage,
            families=["price", "distributional_volatility"],
            outcome={"symbol": sym, "kind": "normalisation_sessions",
                     "base_date": spike_day,
                     "window_open": horizon_open,
                     "window_close": horizon_close,
                     "censor_sessions": CENSOR,
                     "event": ("sessions until the name's "
                               "10-session movement first falls "
                               "below the usual level recorded at "
                               "the spike start")},
        )
        if row.get("quantity") != QUANTITY:
            return fail(f"ledger write for {sym} landed on a "
                        f"different forecast row")
        created += 1 if was_created else 0

    # ---- Figures recomputed from the ledger alone ----
    rows = led.rows()
    if not led.verify_chain(rows):
        return fail("the forecast record failed verification after "
                    "writing; not publishing figures from it")
    figures = ledger_mod.recompute_figures(rows)
    mine = figures.get(ENGINE_ID, {"forecasts": 0, "graded": 0})
    voided_ids = {
        r.get("corrects_row_id") for r in rows
        if r.get("type") == "correction"}
    my_rows = [r for r in rows if r.get("type") == "forecast"
               and r.get("engine_id") == ENGINE_ID]
    valid_rows = [r for r in my_rows if r["row_id"] not in voided_ids]
    voided_total = len(my_rows) - len(valid_rows)
    cohort_dates = sorted({
        r["lineage"]["clocks"]["decision_as_of"]
        for r in valid_rows})
    future_asof = next_weekdays(as_of, CENSOR)

    data = {
        "tool": "Own-Volatility Normalisation Clock",
        "state": "proving",
        "as_of_session": as_of,
        "next_session": future_asof[0],
        "source": (f"Daily closing prices from the price history "
                   f"on record ({len(panel):,} names, at most "
                   f"{max_sessions} trading days each, "
                   f"{long_span})."),
        "window_note": ("The original design judges each stock "
                        "against three years of its own past. Only "
                        "about nineteen months of daily history is "
                        "on record here, so this clock judges each "
                        "stock against all of its own past that "
                        "exists, once at least six months of its "
                        "own readings exist. Stocks without six "
                        "months of readings are left out and "
                        "counted."),
        "claims": {
            "band": ("The real time for a spike to settle back "
                     "falls inside the published range 80 percent "
                     "of the time, give or take 5 points."),
            "median": ("The middle figure beats the stock's own "
                       "plain middle settling time by at least 20 "
                       "percent in average error."),
        },
        "live": {
            "forecasts_recorded": len(valid_rows),
            "forecasts_recorded_total_rows": mine["forecasts"],
            "forecasts_voided": voided_total,
            "correction_note": (
                "An earlier set of forecasts, made with a "
                "different way of measuring movement, was struck "
                "from the record and replaced by the forecasts "
                "above. The struck forecasts do not count in "
                "this record."),
            "forecasts_graded": mine["graded"],
            "matured_target": KILL_MATURED,
            "cohort_dates": cohort_dates,
            "names_checked": checked,
            "names_on_record": len(panel),
            "names_without_session_today": len(panel) - checked,
            "names_with_earlier_last_session": earlier_last,
            "names_below_floor": len(below_floor),
            "below_floor_symbols": below_floor,
            "names_in_spike": len(in_spike),
            "names_already_running": len(already_running),
            "already_running_symbols": already_running,
            "spike_starts": len(starts),
            "forecasts_today": len(live_names),
            "abstained_today": live_abstained,
            "names": live_names,
        },
        "history": {
            "label": "History, not live forecasts",
            "span_start": span[0], "span_end": span[1],
            "note": ("Worked out spike by spike over the price "
                     "history on record: each spike's forecast was "
                     "built only from earlier spikes whose settling "
                     "times were already known by then, then checked "
                     "against what actually happened. Spikes that "
                     "had not settled within 63 trading days count "
                     "in the coverage figure exactly as the rules "
                     "on this page state. The average-error figures "
                     "run only over spikes that settled and had "
                     "their own plain figure to compare with. "
                     "These are study figures from the past, not "
                     "the live record."),
            **hist,
            "study_record": {
                "note": ("The earlier studies this clock is built "
                         "from found that how much prices have been "
                         "moving is the strongest guide to how much "
                         "they will move next, and that a name's "
                         "snap-back after a shock scales with how "
                         "jagged that name usually is. Those are "
                         "the studies' results, from their own "
                         "longer histories. They are the reason "
                         "this clock exists; they are not this "
                         "clock's results."),
            },
        },
        "kill_criterion": (
            "This tool is retired if, after 200 of its forecasts "
            "have matured, the share of real settling times that "
            "fell inside the published range is off by more than "
            "10 points from the promised 80 percent, or its "
            "middle figure's average error is no better than the "
            "stock's own plain middle settling time."),
        "thin_cell_rule": (
            "Any graded group with fewer than 30 graded cases "
            "shows its count only, with no percentage and no "
            "error figure."),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH}: as of {as_of}, {len(live_names)} "
          f"spike-start forecasts ({created} new, {voided} voided), "
          f"{len(valid_rows)} valid recorded in total, history "
          f"graded {hist['graded']} spikes, coverage "
          f"{hist['coverage_pct']}%, MAE {hist['mae_forecast']} vs "
          f"plain {hist['mae_baseline']} over {hist['mae_cases']} "
          f"paired spikes")
    return 0


if __name__ == "__main__":
    sys.exit(build())
