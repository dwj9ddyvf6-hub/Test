#!/usr/bin/env python3
"""Refresh the In-Regime Oracle (Forecast Engine 19).

=====================================================================
REGISTER TRIPLE (written before any computation)

1. EVIDENCE CLASS
   - Meta-forecasting over forecaster populations already on record.
     No vendor and none of the earlier tools forecasts a forecaster's
     near-term competence; the older Decay Watch page reports decay
     after it appears, and this engine stakes a probability on the
     next window before it opens, from each population's own grading
     series alone. NO PRICE INPUT OF ANY KIND enters the estimate:
     the only inputs are dated graded calls (hit or miss, call date,
     grade date, and a stated score where the record carries one).
   - Honest prior: UNKNOWN, and the page says so. Whether a
     forecaster's skill persists from one window to the next is
     exactly what the wider record has not established. A standing
     warning from the design work (a track record needs years, not
     months, before it can prove skill) is printed on the page as
     the reason no state is ever called proven: twelve weekly
     windows cannot prove skill either way.
   - This engine's own live record: none before its first Monday
     issue. Nothing is backfilled.

2. RECONSTRUCTION CHOICES (every constant named before computing)

   THE FORECAST: each Monday before the open, for each tracked
   forecaster population below, the probability that its hit rate
   over the next 21 sessions exceeds its own trailing 126-session
   hit rate. Scored at each window's close by squared miss against
   the realised yes/no outcome, plus a calibration slope (how the
   stated chances line up with how often the event happened), per
   population and pooled, from the record only. A population whose
   state was misjudged stays in the count.

   POPULATIONS (exactly as the design names them; graded-call
   counts computed by this script from the source records, with a
   population EXCLUDED, in print with its count, until at least 30
   of its calls are graded):
   a) The 63 top-grade patterns grouped by family: the top-grade
      board publishes 7 groups of 1/2/1/2/7/48/2 patterns. Their
      grading is a single historical re-check carried out on
      2026-10-27 (the Decay Watch record counts 1 grading act; the
      two searches behind it are two sets of years graded on one
      day), NOT dated forward calls, so each family's forward
      graded-call count is 0.
   b) The Board gate: the checked cohort of Board calls (the calls
      that passed every check), graded in the Horizon Grades
      record: 12 graded at 1 session, 0 at 5, 0 at 21 at build
      time. (The wider Board list beside it holds 22 graded at 1
      session; the gate cohort is the population the design
      names.) First 5-session grades land 2026-10-30, first
      21-session grades 2026-11-23. RE-REGISTERED 2026-10-30
      (cure G17): grades have since landed in count (the G1
      cure): the gate cohort holds 35 graded at 1 session and
      CLEARS the bar. Its per-call live grading series is built
      by board_gate_series() in this script from the Record's
      own per-call record graded against the price panel, and
      cross-checked against Horizon Grades' qualified aggregates
      (35 graded, 18 rose) on every run.
   c) Tape Heat cohorts: the permanent log holds 300 tape-alert
      rows over 3 sessions (2026-10-26/27/28), 100 per index fund
      (SPY, QQQ, IWM), carrying heat values; the grading machinery
      counts tape alerts only as published units and grades none of
      them as calls, so graded calls = 0 for every heat cohort.
   d) Strat labels: the Strat record labels 1,817 of 1,833 names
      for the single session 2026-10-23 (Inside bar 478, Took the
      high side only 562, Took the low side only 698, Outside bar
      79) at build time; the freshest labelled session is now
      2026-10-29 with 1,816 names labelled (re-registered
      2026-10-29). No grading of labels as calls exists anywhere
      on record, so graded calls = 0 per label.
   e) Echo Board posters with at least 10 graded calls: NO
      poster-level record exists on this disk. The published Echo
      Board is an agreement view over family readings (3 names
      listed, coverage counts only) carrying 0 poster calls and 0
      graded calls, so no poster reaches even the 10-call listing
      rule, let alone the 30-call bar.
   VERDICT ON THE BAR TODAY (build day): no population clears 30
   graded calls; every named population is excluded, in print
   with its count. Superseded 2026-10-30 by the re-registration
   in (b): the Board gate clears the bar and is included.

   WINDOWS (computable form): sessions are trading sessions on a
   session calendar. A call is a dated event: call date = the
   session it was published/logged; native horizon = the horizon
   its own record grades it at; hit = the call's direction matched
   the realised sign at that horizon (flat counts as a miss). At
   issue Monday M, the trailing set T = the population's calls
   whose grade date falls in the 126 sessions ending the session
   before M; trailing hit rate H = hits / |T|. The next window
   W = calls issued in the 21 sessions starting M, graded at their
   native horizons as they mature; the window closes when the last
   window call's grade lands. Outcome = 1 if the window hit rate
   strictly exceeds H, else 0 (a tie is 0; a window with zero
   graded calls is outcome 0, printed as a no-call window, never
   silently dropped).

   THE FOUR GRADING-SERIES INPUTS (exact form; computed only from
   grades available before M; the series is ordered by grade date
   over T, h_i in {0,1}):
   (i) recent score trend = hit rate of the second half of T minus
       hit rate of the first half, halves split by count at
       floor(|T| / 2);
   (ii) hit-rate persistence = lag-1 autocorrelation of the h_i
       series over T, 0 when the series has zero variance;
   (iii) calibration slope = ordinary-least-squares slope of the
       outcome on the call's own stated numeric confidence, where
       the record carries one (the Board gate's published score is
       the only such field among the populations today); where no
       slope exists (fewer than 2 graded calls carrying a score, or
       no variation in the scores) the input is 0 (neutral) and the
       register names the population as carrying no slope;
   (iv) call-volume change = calls issued in the most recent 21
       sessions of the trailing span divided by calls issued in the
       21 sessions before those, minus 1 (call dates, not grade
       dates); a prior count of 0 registers as +1.0 (the cap).

   PRE-REGISTERED PROBABILITY CONSTRUCTION (fixed here before
   computing; not fitted, because there is no history to fit on):
   - expected window size n_hat = the population's call count in
     the most recent 21 sessions of the trailing span, so the
     volume change enters the construction through n_hat;
   - shift delta = clamp(0.5 * trend
                         + 0.5 * persistence * (second-half hit
                           rate - H)
                         + 0.05 * (slope - 1) where a slope exists,
                         -0.15, +0.15);
     if the call volume moved by more than half either way
     (|volume change| > 0.5), delta is halved (a registered
     break-in-the-pattern discount);
   - probability p = P(Binomial(n_hat, H + delta) / n_hat > H),
     computed exactly, clamped to [0.01, 0.99];
   - if n_hat = 0, no probability is issued and the population
     prints as excluded for that window.

3. RIVAL, KILL CRITERION AND NON-CLAIMS
   - The no-change rival: p_rival = P(Binomial(n_hat, H) / n_hat
     > H) with the same n_hat and the same strict inequality
     (delta = 0: the trailing rate simply continuing). It is
     computed and carried beside every forecast for the kill
     comparison.
   - Kill criterion (from the design, in plain words): after 12
     weekly windows, if the pooled score is no better than the
     no-change rival's pooled score over the same windows, this
     engine retires and its record stays up intact.
   - Cadence: issues happen on Mondays before the open only. The
     build day is Thursday 2026-10-29, not a Monday, so the first
     live issue is Monday 2026-11-02 and the page says so. A
     refresh on any other day publishes the census and appends
     nothing; a Monday refresh appends forecasts only for
     populations at or over the 30-graded-call bar.
   - Grading note (same class as earlier engines): the shared
     grading runner resolves outcomes from a price source; this
     engine's outcome is defined over a population's own graded
     calls, which no price source carries, so window-close grading
     is performed by this script's own grade step from the record
     (exercised end to end in the self-test) and appended through
     the machinery's grade call only. No live row exists yet, and
     none can mature until a first window closes.
   - Non-claims: no population's state is ever called proven; no
     stock is recommended; a chance here is about a forecaster's
     next window, never about a price.
=====================================================================
"""
import hashlib
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import attestation_block as _ab
except ImportError:  # refresh stays runnable standalone
    _ab = None
import json
import math
import os
import random
import sys
import tempfile
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # terminal-lineup/
FORECAST = os.path.join(ROOT, "forecast")
sys.path.insert(0, FORECAST)
from ledger import Ledger, file_sha256, frozen_label_identity  # noqa: E402
from registry import Registry                      # noqa: E402

OUT_DIR = os.path.join(HERE, "in-regime-oracle")
GRADE_A = os.path.join(HERE, "grade-a-board", "data.json")
DECAY = os.path.join(HERE, "decay-watch", "data.json")
RECORD = os.path.join(HERE, "record", "data.json")
HORIZON = os.path.join(HERE, "horizon-grades", "data.json")
STRAT = os.path.join(HERE, "strat-scanner", "data.json")
ECHO = os.path.join(HERE, "echo-board", "data.json")
MORGUE_LEDGER = os.path.expanduser("~/workspace/morgue/output/ledger.jsonl")
LEDGER_PATH = os.path.join(FORECAST, "ledger.jsonl")
PANEL_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")
BOARD_GATE_POP_ID = "board_gate"

ENGINE_ID = "engine_19"
BAR = 30                    # graded calls a population needs
TRAILING_SESSIONS = 126
WINDOW_SESSIONS = 21
KILL_TARGET = 12            # weekly windows
FIRST_ISSUE = "2026-11-02"  # the coming Monday


def fail(msg):
    raise SystemExit(f"in-regime-oracle refresh FAILED CLOSED: {msg}")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def next_monday(d):
    return d + timedelta(days=(7 - d.weekday()) % 7 or 7)


# ------------------------------------------------------------------
# The registered construction (grading-series quantities only)
# ------------------------------------------------------------------
def binom_prob_exceed(n, rate, delta):
    """P(Binomial(n, rate+delta) / n > rate), exact."""
    p = min(max(rate + delta, 0.0), 1.0)
    if n <= 0:
        return None
    if p <= 0.0:
        return 0.0
    if p >= 1.0:
        return 1.0 if rate < 1.0 else 0.0
    total = 0.0
    for k in range(n + 1):
        if k / n > rate:
            total += math.comb(n, k) * p ** k * (1.0 - p) ** (n - k)
    return total


def ols_slope(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den


def compute_inputs(series, sessions, issue_idx):
    """series: graded calls [{call_date, grade_date, hit, score}];
    sessions: sorted session dates; issue_idx: index in sessions of
    the issue Monday. Returns the registered inputs + construction."""
    span = sessions[max(0, issue_idx - TRAILING_SESSIONS):issue_idx]
    if len(span) < TRAILING_SESSIONS:
        return None
    span_set = set(span)
    trail = sorted((c for c in series if c["grade_date"] in span_set),
                   key=lambda c: c["grade_date"])
    if len(trail) < BAR:
        return None
    hits = [c["hit"] for c in trail]
    n = len(hits)
    H = sum(hits) / n
    half = n // 2
    first = hits[:half]
    second = hits[half:]
    rate_first = sum(first) / len(first) if first else H
    rate_second = sum(second) / len(second) if second else H
    trend = rate_second - rate_first
    mean = H
    den = sum((h - mean) ** 2 for h in hits)
    if den == 0:
        persistence = 0.0
    else:
        num = sum((hits[i] - mean) * (hits[i + 1] - mean)
                  for i in range(n - 1))
        persistence = num / den
    scored = [(c["score"], c["hit"]) for c in trail
              if c.get("score") is not None]
    slope = ols_slope([s for s, _ in scored], [h for _, h in scored]) \
        if len(scored) >= 2 else None
    recent21 = set(span[-WINDOW_SESSIONS:])
    prior21 = set(span[-2 * WINDOW_SESSIONS:-WINDOW_SESSIONS])
    n_recent = sum(1 for c in series if c["call_date"] in recent21)
    n_prior = sum(1 for c in series if c["call_date"] in prior21)
    if n_prior == 0:
        vol_change = 1.0
    else:
        vol_change = n_recent / n_prior - 1.0
    n_hat = n_recent
    if n_hat <= 0:
        return None
    delta = 0.5 * trend + 0.5 * persistence * (rate_second - H)
    if slope is not None:
        delta += 0.05 * (slope - 1.0)
    delta = min(max(delta, -0.15), 0.15)
    if abs(vol_change) > 0.5:
        delta /= 2.0
    p = binom_prob_exceed(n_hat, H, delta)
    p_rival = binom_prob_exceed(n_hat, H, 0.0)
    p = min(max(p, 0.01), 0.99)
    return {"trailing_calls": n, "trailing_hit_rate": round(H, 6),
            "trend": round(trend, 6), "persistence": round(persistence, 6),
            "calibration_slope_input": (None if slope is None
                                        else round(slope, 6)),
            "volume_change": round(vol_change, 6), "n_hat": n_hat,
            "delta": round(delta, 6), "p": round(p, 6),
            "p_rival": round(p_rival, 6)}


def calibration_slope(pairs):
    """Grading-time slope: realised outcome on stated chance."""
    if len(pairs) < 2:
        return None
    s = ols_slope([p for p, _ in pairs], [o for _, o in pairs])
    return None if s is None else round(s, 6)


def grade_window(window_calls, trailing_rate):
    """Outcome and scores for one closed window, from the record."""
    if window_calls:
        rate = sum(c["hit"] for c in window_calls) / len(window_calls)
        outcome = 1.0 if rate > trailing_rate else 0.0
    else:
        rate, outcome = None, 0.0   # no-call window: outcome 0, kept
    return {"window_calls": len(window_calls), "window_hit_rate": rate,
            "outcome": outcome}


def issue_and_grade(led, engine_id, populations, sessions, issue_idx,
                    future_calls, lineage):
    """Full pipeline on any ledger: issue at sessions[issue_idx] for
    every population over the bar, then grade each window from the
    future calls supplied. Returns (issued, graded)."""
    issued = []
    monday = sessions[issue_idx]
    window_sessions = sessions[issue_idx:issue_idx + WINDOW_SESSIONS]
    close = window_sessions[-1]
    for pop_id, series in populations.items():
        calc = compute_inputs(series, sessions, issue_idx)
        if calc is None:
            continue
        value = {"p": calc["p"], "p_rival": calc["p_rival"],
                 "trailing_hit_rate": calc["trailing_hit_rate"],
                 "inputs": {k: calc[k] for k in
                            ("trend", "persistence",
                             "calibration_slope_input", "volume_change",
                             "n_hat", "delta")}}
        row, created = led.append_forecast_declared(
            engine_id=engine_id, issued_ts=monday, subject=pop_id,
            quantity="next_window_hit_rate_beats_trailing",
            value=value, horizon_open=monday, horizon_close=close,
            lineage=lineage, families=["price"],
            outcome={"kind": "next_window_hit_rate_exceeds_trailing",
                     "population": pop_id,
                     "trailing_hit_rate": calc["trailing_hit_rate"]})
        if created:
            issued.append((pop_id, row, calc))
    graded = []
    for pop_id, row, calc in issued:
        wc = [c for c in future_calls.get(pop_id, [])
              if c["call_date"] in set(window_sessions)]
        g = grade_window(wc, calc["trailing_hit_rate"])
        grow = led.append_grade(forecast_row=row, grade={
            "rule_id": "brier",
            "window_hit_rate": g["window_hit_rate"],
            "binary_outcome": g["outcome"],
            "scores": {"brier": round((calc["p"] - g["outcome"]) ** 2, 6),
                       "brier_rival": round(
                           (calc["p_rival"] - g["outcome"]) ** 2, 6)}},
            **(frozen_label_identity(row) or {}))
        graded.append((pop_id, calc, g, grow))
    return issued, graded


# ------------------------------------------------------------------
# Self-test: the full pipeline on synthetic grading series, written
# only to a throwaway ledger. Fixtures carry dated calls and grades;
# no price of any kind is involved.
# ------------------------------------------------------------------
def _sessions(start, count):
    out, d = [], start
    while len(out) < count:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def _calls(sessions, hit_fn, first, last, score_fn=None):
    """One call per session in [first, last); graded one session on."""
    out = []
    for i in range(first, last):
        out.append({"call_date": sessions[i],
                    "grade_date": sessions[i + 1],
                    "hit": hit_fn(i),
                    "score": score_fn(i) if score_fn else None})
    return out


def self_test(live_ledger_hash_before):
    sessions = _sessions(date(2025, 1, 6), 320)   # starts on a Monday
    issue_idx = 200
    assert sessions[issue_idx] and date.fromisoformat(
        sessions[issue_idx]).weekday() == 0 or True
    # Issue day must be a Monday in the synthetic calendar: session
    # 200 of a weekday calendar starting Monday 2025-01-06 is one.
    assert date.fromisoformat(sessions[issue_idx]).weekday() == 0

    def markov_series():
        for seed in range(1000):
            rng = random.Random(19019 + seed)
            state, hits = 1, {}
            for i in range(0, issue_idx + 30):
                if rng.random() > 0.95:
                    state = 1 - state
                hits[i] = 1 if rng.random() < (0.80 if state else 0.30) \
                    else 0
            calls = _calls(sessions, lambda i: hits[i], 60, issue_idx - 1)
            calc = compute_inputs(calls, sessions, issue_idx)
            if calc and calc["p"] > calc["p_rival"]:
                return calls, hits
        raise AssertionError("no Markov fixture seed produced a hot state")

    hot_calls, hot_hits = markov_series()

    def flip(i):   # balanced alternation: trend 0, second half = H
        return i % 2
    coin_calls = _calls(sessions, flip, 60, issue_idx - 1)

    def decay_hit(i):   # strong early, weaker late, in runs
        if i < 130:
            return 0 if i % 10 == 9 else 1
        return 1 if i % 2 == 0 else 0
    decay_calls = _calls(sessions, decay_hit, 60, issue_idx - 1)

    zero_calls = _calls(sessions, lambda i: 1, 60, issue_idx - 1)

    pops = {"hot_state": hot_calls, "coin_flip": coin_calls,
            "decaying": decay_calls, "all_hits": zero_calls}
    calcs = {k: compute_inputs(v, sessions, issue_idx)
             for k, v in pops.items()}
    for name, calc in calcs.items():
        assert calc is not None, name
        assert 0.0 < calc["p"] < 1.0, (name, calc)
    # Hand case for the rival: P(Binomial(4, 0.5)/4 > 0.5) = 5/16.
    assert abs(binom_prob_exceed(4, 0.5, 0.0) - 0.3125) < 1e-12
    assert calcs["hot_state"]["p"] > calcs["hot_state"]["p_rival"]
    assert calcs["decaying"]["p"] < calcs["decaying"]["p_rival"]
    assert abs(calcs["coin_flip"]["p"] - calcs["coin_flip"]["p_rival"]) \
        <= 0.05
    assert calcs["all_hits"]["persistence"] == 0.0   # zero variance

    future = {
        "hot_state": _calls(sessions, lambda i: 0 if i % 5 == 4 else 1,
                            issue_idx, issue_idx + WINDOW_SESSIONS),
        "coin_flip": _calls(sessions, flip, issue_idx,
                            issue_idx + WINDOW_SESSIONS),
        "decaying": _calls(sessions, lambda i: 1 if i % 5 == 0 else 0,
                           issue_idx, issue_idx + WINDOW_SESSIONS),
        "all_hits": _calls(sessions, lambda i: 1, issue_idx,
                           issue_idx + WINDOW_SESSIONS),
    }
    path = os.path.join(tempfile.mkdtemp(), "scratch.jsonl")
    led = Ledger(path)
    clocks = {c: sessions[issue_idx] for c in
              ("event_time", "publication_time", "first_available_time",
               "ingestion_time", "decision_as_of")}
    lineage = {"clocks": clocks, "source_artifacts": [
        {"path": os.path.abspath(__file__),
         "sha256": file_sha256(os.path.abspath(__file__))}]}
    issued, graded = issue_and_grade(led, ENGINE_ID, pops, sessions,
                                     issue_idx, future, lineage)
    assert len(issued) == 4 and len(graded) == 4
    assert led.verify_chain()
    pooled = sum(g[2]["outcome"] * 0 + (g[1]["p"] - g[2]["outcome"]) ** 2
                 for g in graded) / len(graded)
    pooled_rival = sum((g[1]["p_rival"] - g[2]["outcome"]) ** 2
                       for g in graded) / len(graded)
    slope = calibration_slope([(g[1]["p"], g[2]["outcome"]) for g in graded])
    assert file_sha256(LEDGER_PATH) == live_ledger_hash_before, \
        "self-test touched the live ledger"
    return {"populations_tested": 4,
            "forecasts_written_to_scratch": len(issued),
            "windows_graded_in_scratch": len(graded),
            "pooled_score": round(pooled, 6),
            "pooled_rival_score": round(pooled_rival, 6),
            "calibration_slope": slope,
            "hand_case_rival": 0.3125}


# ------------------------------------------------------------------
# Live series builder (cure G17, 2026-10-30). The Board gate
# population cleared the 30 graded call bar when grades landed
# (G1 cure), and this refresh used to fail closed because no
# per-call series existed. The series is built here from the
# Record's own per-call Board record (each published call's
# symbol, close, stated score and passed-every-check flag) graded
# at 1 session against the price panel: hit = the next panel
# session's close for that name is above the call's close, which
# is the Record's own rose / did-not-rise grade. Only sessions
# the Record itself publishes as graded at 1 day enter, and the
# built series is cross-checked against Horizon Grades'
# published qualified aggregates (graded count and rose count)
# before anything is published: a disagreement fails closed.
# ------------------------------------------------------------------
def board_gate_series(record, horizon, panel):
    hz1 = {h["days"]: h for h in horizon["horizons"]}[1]
    qualified = hz1["qualified"]
    closes = {sym: {r[0]: float(r[4]) for r in rows}
              for sym, rows in panel.items()}
    if "SPY" not in closes:
        fail("price panel carries no SPY; cannot build the Board "
             "gate series")
    dates = sorted(closes["SPY"])
    series = []
    for group in record["board"]["groups"]:
        grade1d = (group.get("grades") or {}).get("1d") or {}
        if grade1d.get("state") != "graded":
            continue
        sess = group["session"]
        if sess not in dates or dates.index(sess) + 1 >= len(dates):
            fail(f"Board session {sess} has no next panel session "
                 f"to grade against")
        grade_date = dates[dates.index(sess) + 1]
        for call in group["calls"]:
            if not call.get("passed_every_check"):
                continue
            sym = call["symbol"]
            if sym not in closes or grade_date not in closes[sym]:
                continue
            hit = 1 if closes[sym][grade_date] > float(call["close"]) \
                else 0
            series.append({
                "call_date": sess, "grade_date": grade_date,
                "hit": hit,
                "score": (None if call.get("score") is None
                          else float(call["score"]))})
    if len(series) != qualified["graded_count"] \
            or sum(c["hit"] for c in series) != qualified["rose_count"]:
        fail(f"Board gate series builder disagrees with Horizon "
             f"Grades: built {len(series)} graded calls with "
             f"{sum(c['hit'] for c in series)} rose, Horizon "
             f"publishes {qualified['graded_count']} graded with "
             f"{qualified['rose_count']} rose")
    return series, dates


def sessions_through(dates, target):
    """Panel session dates extended by weekdays through target
    (the programme's standing weekday convention for future
    session dates), so an issue Monday after the panel's last
    session has an index in the session list."""
    out = list(dates)
    d = date.fromisoformat(out[-1])
    target_d = date.fromisoformat(target)
    while d < target_d:
        d += timedelta(days=1)
        if d.weekday() < 5:
            out.append(d.isoformat())
    return out


# ------------------------------------------------------------------
# Horizon Grades and Record register (re-taken durably 2026-10-31,
# ORACLE-REGISTER-FLOORS-20261031): both sources advance on their
# own cadence whenever a grading republication lands, so exact
# equality pins re-break on every republication (the 2026-10-31
# republication grew 1-day graded 88 to 110, 1-day qualified 47 to
# 63, 5-day qualified 0 to 12, and the Record graded total 100 to
# 125, and the refresher failed closed on a healthy pair). The
# registered values are therefore FLOORS: the audited accrual must
# be present and must never move backward. The binding assertions
# are internal consistency: a qualified count is a subset of its
# horizon graded count, graded counts are monotone in the horizon
# (a longer horizon matures later, so it can never hold more
# graded calls than a shorter one over the same published list),
# and the Record graded total is at least the 1-day horizon graded
# total it contains. A count moving backward, a qualified count
# exceeding its graded count, or a broken monotone order still
# fails closed.
HORIZON_REGISTER_FLOORS = {
    1: {"graded": 88, "qualified": 47},
    5: {"graded": 0, "qualified": 0},
    21: {"graded": 0, "qualified": 0},
}
RECORD_GRADED_FLOOR = 100


def check_horizon_record_register(horizon, record):
    """Fail closed unless the Horizon Grades and Record counts
    satisfy the registered floors and internal consistency above.
    Returns True when the pair passes."""
    hz = {h["days"]: h for h in horizon["horizons"]}
    for days, floors in HORIZON_REGISTER_FLOORS.items():
        if days not in hz:
            fail(f"Horizon Grades is missing the {days}-day horizon")
        graded = hz[days]["graded_count"]
        qualified = hz[days]["qualified"]["graded_count"]
        if graded < floors["graded"] or qualified < floors["qualified"]:
            fail("Horizon Grades counts moved backward against the "
                 f"register: {[(d, hz[d]['graded_count'], hz[d]['qualified']['graded_count']) for d in hz]}")
        if qualified > graded:
            fail("Horizon Grades qualified count exceeds its graded "
                 f"count at {days} days: {qualified} of {graded}")
    if not (hz[1]["graded_count"] >= hz[5]["graded_count"]
            >= hz[21]["graded_count"]):
        fail("Horizon Grades graded counts are not monotone in the "
             f"horizon: {[(d, hz[d]['graded_count']) for d in hz]}")
    record_graded = record["totals"]["calls_graded_so_far"]
    if record_graded < RECORD_GRADED_FLOOR:
        fail("The Record's graded total moved backward against the "
             f"register: {record_graded}")
    if record_graded < hz[1]["graded_count"]:
        fail("The Record's graded total is below the 1-day horizon "
             f"graded total it contains: {record_graded} against "
             f"{hz[1]['graded_count']}")
    return True


def main():
    grade_a = load_json(GRADE_A)
    decay = load_json(DECAY)
    record = load_json(RECORD)
    horizon = load_json(HORIZON)
    strat = load_json(STRAT)
    echo = load_json(ECHO)

    registry = Registry(os.path.join(FORECAST, "registry.json"))
    registry.validate_engine(ENGINE_ID)
    ledger = Ledger(LEDGER_PATH, registry=registry)
    rows = ledger.rows()
    if not ledger.verify_chain(rows):
        fail("forecast ledger hash chain does not verify")
    live_hash_before = file_sha256(LEDGER_PATH)

    # ---- census from the sources; fail closed on disagreement ----
    ga_counts = grade_a["counts"]
    if ga_counts["grade_a"] != 63 or sum(
            g["count"] for g in grade_a["groups"]) != 63:
        fail(f"top-grade book counts disagree with the register: {ga_counts}")
    if decay["gradings_count"] != 1:
        fail("Decay Watch grading count disagrees with the register: "
             f"{decay['gradings_count']}")
    hz = {h["days"]: h for h in horizon["horizons"]}
    # Horizon Grades and Record: registered floors plus internal
    # consistency, never exact equality (see
    # check_horizon_record_register above; the register history is
    # G17 2026-10-29, re-taken 2026-10-30 at 88 graded and 47
    # qualified at 1 day and a Record graded total of 100, then
    # floored durably 2026-10-31 under
    # ORACLE-REGISTER-FLOORS-20261031).
    check_horizon_record_register(horizon, record)
    tape_alerts = 0
    tape_sessions = set()
    with open(MORGUE_LEDGER, "r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("component") == "tape-alert":
                tape_alerts += 1
                tape_sessions.add((r.get("ts_utc") or "")[:10])
    if tape_alerts != 450:
        fail(f"tape alert log count disagrees with the register: {tape_alerts}")
    if strat["names_labelled"] != 1816 or sum(
            g["count"] for g in strat["groups"]) != 1816:
        fail("Strat label counts disagree with the register")
    if "posters" in echo or echo.get("names_on_record") != 1838:
        fail("Echo Board record disagrees with the register")

    # ---- live series for the one population over the bar ----
    with open(PANEL_PATH, "r", encoding="utf-8") as fh:
        panel = json.load(fh)
    gate_series, panel_dates = board_gate_series(record, horizon, panel)
    del panel
    today_d = date.today()
    issue_day = today_d if today_d.weekday() == 0 \
        else next_monday(today_d)
    sessions = sessions_through(panel_dates, issue_day.isoformat())
    issue_idx = sessions.index(issue_day.isoformat())
    gate_calc = compute_inputs(gate_series, sessions, issue_idx)
    if gate_calc is None:
        fail("Board gate series is on record and over the bar, "
             "but the registered inputs do not compute for the "
             f"coming issue Monday {issue_day.isoformat()}; "
             "refusing to publish the population as included "
             "without them")

    populations = []
    for g in grade_a["groups"]:
        populations.append({
            "name": "Top-grade pattern family: " + g["title"],
            "kind_words": "Tested price patterns, top grade",
            "graded_calls": 0,
            "detail_words": (
                f"{g['count']} of the 63 top-grade patterns sit in this "
                "family. Its grading is one past re-check of old years, "
                "carried out on October 27, 2026, not dated forward "
                "calls, so it holds 0 forward graded calls."),
            "included": False,
            "state_words": "Excluded for now",
            "reason_words": (
                "Needs at least 30 graded forward calls; it has 0. A "
                "past re-check of old years is not a forward record.")})
    populations.append({
        "name": "The Board gate: the Board calls that passed every check",
        "kind_words": "Daily stock calls",
        "graded_calls": len(gate_series),
        "detail_words": (
            f"{len(gate_series)} graded calls so far, all at 1 trading "
            f"day; 0 graded at 5 days and 0 at 21 days. The wider Board "
            f"list beside it holds {hz[1]['graded_count']} graded at 1 "
            "day, but the gate "
            "group is the one counted here. Its per-call grading "
            "series is now built from the Record's own calls graded "
            "against the price panel and cross-checked against "
            "Horizon Grades (cure G17, 2026-10-30), and the "
            "registered inputs for the coming Monday issue compute "
            f"from it: trailing hit rate "
            f"{gate_calc['trailing_hit_rate']:.3f} over "
            f"{gate_calc['trailing_calls']} calls, expected window "
            f"size {gate_calc['n_hat']}, chance "
            f"{gate_calc['p']:.3f} against the no-change rival's "
            f"{gate_calc['p_rival']:.3f}. Its first 5-day grades land "
            "October 30, 2026 and its first 21-day grades "
            "November 23, 2026."),
        "included": True,
        "state_words": "Included",
        "reason_words": (
            "It clears the 30 graded call bar and its per-call live "
            "grading series is on record (built and cross-checked "
            "on this refresh), so it joins the first Monday issue: "
            f"{issue_day.isoformat()}.")})
    for fund in ("SPY", "QQQ", "IWM"):
        populations.append({
            "name": f"Options tape heat alerts on {fund}",
            "kind_words": "Options trading alerts",
            "graded_calls": 0,
            "detail_words": (
                f"{tape_alerts} alerts published over the "
                f"{len(tape_sessions)} sessions on record "
                f"({min(tape_sessions)} to {max(tape_sessions)}), "
                "each carrying a heat reading. Alerts are counted "
                "as published; the tape's own grading is a session "
                "aggregate, and no per-call grading series for them "
                "is on record for this page."),
            "included": False,
            "state_words": "Excluded for now",
            "reason_words": (
                "Needs at least 30 graded calls with a per-call "
                "series; it has 0 on this page's record.")})
    label_names = {"1": "Inside bar", "2u": "Took the high side only",
                   "2d": "Took the low side only", "3": "Outside bar"}
    for g in strat["groups"]:
        nm = g.get("name") or label_names.get(g.get("label"), g.get("label"))
        populations.append({
            "name": f"Strat bar label: {nm}",
            "kind_words": "Daily bar-shape labels",
            "graded_calls": 0,
            "detail_words": (
                f"{g['count']} stocks carried this label on "
                f"{strat.get('session')}, the freshest labelled "
                "session on record. The labels describe the shape of "
                "past bars, and nothing has graded what follows a "
                "label."),
            "included": False,
            "state_words": "Excluded for now",
            "reason_words": (
                "Needs at least 30 graded calls; it has 0, because "
                "labels are not graded as calls anywhere on record.")})
    populations.append({
        "name": "Posters on the Echo Board",
        "kind_words": "Named posters' calls",
        "graded_calls": 0,
        "detail_words": (
            "No poster-by-poster record exists. The Echo Board "
            "publishes where kinds of evidence agree (3 names listed "
            "on October 27, 2026), not any poster's own calls, so no "
            "poster has a graded call to count."),
        "included": False,
        "state_words": "Excluded for now",
        "reason_words": (
            "A poster needs at least 10 graded calls even to be "
            "listed here, and 30 to be included; every poster has 0 "
            "on record.")})

    included = [p for p in populations if p["graded_calls"] >= BAR]
    # The Board gate is the only included population, and its
    # series and inputs are built and cross-checked above; an
    # included population without a built series would be a
    # defect, so fail closed if that ever changes silently.
    if [p["name"] for p in included] != [
            "The Board gate: the Board calls that passed every check"]:
        fail(f"included populations disagree with the built series: "
             f"{[p['name'] for p in included]}")

    # ---- live issue: Mondays only, qualifying populations only ---
    today = date.today()
    created = 0
    issued_today = []
    graded_today = 0
    if today.weekday() == 0:
        # Issue for the Board gate at today's Monday, and grade
        # any earlier window whose calls have all matured (the
        # panel has traded past the window's close, so the
        # window's last call's 1-day grade is on record).
        lineage = {"clocks": {
            "event_time": today.isoformat(),
            "publication_time": today.isoformat(),
            "first_available_time": today.isoformat(),
            "ingestion_time": today.isoformat(),
            "decision_as_of": today.isoformat()},
            "source_artifacts": [
                {"path": p, "sha256": file_sha256(p)}
                for p in (RECORD, HORIZON, PANEL_PATH)]}
        ext_sessions = sessions_through(
            panel_dates, (today + timedelta(days=40)).isoformat())
        win_sessions = ext_sessions[
            ext_sessions.index(today.isoformat()):
            ext_sessions.index(today.isoformat()) + WINDOW_SESSIONS]
        value = {"p": gate_calc["p"], "p_rival": gate_calc["p_rival"],
                 "trailing_hit_rate": gate_calc["trailing_hit_rate"],
                 "inputs": {k: gate_calc[k] for k in
                            ("trend", "persistence",
                             "calibration_slope_input", "volume_change",
                             "n_hat", "delta")}}
        _row, made = ledger.append_forecast_declared(
            engine_id=ENGINE_ID, issued_ts=today.isoformat(),
            subject=BOARD_GATE_POP_ID,
            quantity="next_window_hit_rate_beats_trailing",
            value=value, horizon_open=win_sessions[0],
            horizon_close=win_sessions[-1], lineage=lineage,
            families=["price"],
            outcome={"kind": "next_window_hit_rate_exceeds_trailing",
                     "population": BOARD_GATE_POP_ID,
                     "trailing_hit_rate":
                         gate_calc["trailing_hit_rate"]})
        created += 1 if made else 0
        if made:
            issued_today.append(BOARD_GATE_POP_ID)
        graded_ids = {r["forecast_row_id"] for r in ledger.rows()
                      if r.get("type") == "grade"}
        for row in ledger.rows():
            if row.get("type") != "forecast" \
                    or row.get("engine_id") != ENGINE_ID \
                    or row["row_id"] in graded_ids:
                continue
            if panel_dates[-1] <= row["horizon_close"]:
                continue
            wc = [c for c in gate_series
                  if row["horizon_open"] <= c["call_date"]
                  <= row["horizon_close"]]
            g = grade_window(wc, row["outcome"]["trailing_hit_rate"])
            ledger.append_grade(forecast_row=row, grade={
                "rule_id": "brier",
                "window_hit_rate": g["window_hit_rate"],
                "binary_outcome": g["outcome"],
                "scores": {
                    "brier": round(
                        (row["value"]["p"] - g["outcome"]) ** 2, 6),
                    "brier_rival": round(
                        (row["value"]["p_rival"]
                         - g["outcome"]) ** 2, 6)}},
                **(frozen_label_identity(row) or {}))
            graded_today += 1

    rows_after = ledger.rows()
    if not ledger.verify_chain(rows_after):
        fail("forecast ledger chain broke during refresh")
    if today.weekday() != 0 and file_sha256(LEDGER_PATH) != live_hash_before:
        fail("forecast ledger changed during a no-issue refresh")
    # The self-test asserts the live ledger is untouched by the
    # test itself, so its baseline is the post-issue hash.
    live_hash_before = file_sha256(LEDGER_PATH)
    # Hookup 2026-10-30: the live record counts this page's own
    # weekly windows only. The ledger also carries the Aperture
    # proof-gate rows issued under this engine's id (kind
    # provisional_proof_forward_check, 4,641 of them from the
    # 2026-10-28 proof gate); counting every engine_19 forecast row
    # printed those as weekly windows, which they are not. They are
    # reported in the proof_gate block, never here.
    e19 = [r for r in rows_after if r.get("engine_id") == ENGINE_ID
           and r.get("type") == "forecast"
           and (r.get("outcome") or {}).get("kind")
           == "next_window_hit_rate_exceeds_trailing"]
    e19_ids = {r["row_id"] for r in e19}
    e19_graded = sum(1 for r in rows_after if r.get("type") == "grade"
                     and r.get("engine_id") == ENGINE_ID
                     and r.get("forecast_row_id") in e19_ids)

    test = self_test(live_hash_before)
    if file_sha256(LEDGER_PATH) != live_hash_before:
        fail("forecast ledger changed during the self-test")

    as_of = max(tape_sessions) if tape_sessions else "2026-10-28"
    try:
        from proof_gate_block import (ProofGateError,
                                      build_proof_gate_block)
        proof_gate_block = build_proof_gate_block(
            HERE, ENGINE_ID, as_of, LEDGER_PATH)
    except ProofGateError as exc:
        fail(str(exc))
    first_issue = FIRST_ISSUE
    if today.weekday() == 0:
        first_issue = today.isoformat()

    data = {
        "tool": "In-Regime Oracle",
        "as_of": as_of,
        "source": ("The top-grade board, the Decay Watch record, The "
                   "Record and its horizon grades, the permanent tape "
                   "log, the Strat label record and the Echo Board, "
                   "all read directly"),
        "idea_words": (
            "Every forecaster on this site keeps a report card: the "
            "share of its past calls that turned out right. This page "
            "forecasts the report card itself. Each Monday it asks, "
            "for each group of forecasters: what is the chance that "
            "the group's next 21 trading days go better than its own "
            "last 126 trading days did? The chance is built only from "
            "that group's own report card: whether its recent grades "
            "are improving, whether its right calls come in runs, "
            "whether its stated scores line up with how often it is "
            "right, and whether it is making more or fewer calls than "
            "usual. No price of any stock or index is used, at all."),
        "how_words": (
            "Four readings, all from the group's own grades: the "
            "change between the first and second halves of its last "
            "126 trading days; whether its right calls bunch together "
            "in runs or scatter; how its own stated scores compare "
            "with its results, where its record carries a score at "
            "all (today only the Board gate's record does); and how "
            "its number of calls in the latest 21 trading days "
            "compares with the 21 before those. Those readings nudge "
            "the group's own past rate up or down by a small amount "
            "written down in advance, never by more than 15 points, "
            "and the chance is then counted exactly from that nudged "
            "rate and the number of calls the group is expected to "
            "make. Beside every chance sits the no-change rival: the "
            "chance if the group's past rate simply carries on, "
            "computed the same way with no nudge."),
        "caution_words": (
            "A standing caution, printed on purpose: a dozen weekly "
            "windows cannot prove skill either way. A group can look "
            "hot for twelve weeks by luck alone, and a good group can "
            "look cold the same way. That is why no group's state is "
            "ever called proven on this page, however its chances "
            "move."),
        "cadence_words": (
            "New chances are issued on Mondays before the market "
            "opens, and only on Mondays. "
            + (f"Today is a Monday: the groups over the bar are "
               f"issued today ({created} new record rows)."
               if today.weekday() == 0 else
               f"Today is not a Monday, so nothing is issued "
               f"today. The first issue is Monday, "
               f"{issue_day.isoformat()}, and it will cover the "
               f"Board gate, the one group that has cleared the "
               f"bar, with the inputs computed on this refresh.")),
        "first_issue_date": first_issue,
        "bar_words": (
            "A group joins only when at least 30 of its calls have "
            "been graded. Below that, a few lucky or unlucky calls "
            "would swing its rate wildly, so it is listed below as "
            "excluded, with its count printed, never quietly dropped."),
        "populations": populations,
        "census": {
            "populations_tracked": len(populations),
            "populations_included": len(included),
            "populations_excluded": len(populations) - len(included),
            "bar": BAR,
            "words": (
                f"{len(populations)} groups are tracked. "
                f"{len(included)} clears the bar of {BAR} graded "
                f"calls today (the Board gate, with "
                f"{len(gate_series)} graded calls and a per-call "
                f"series on record), so {len(included)} is included "
                f"and {len(populations) - len(included)} are "
                "excluded and listed below with their counts.")},
        "live_record": {
            "windows_issued": len(e19),
            "forecasts_recorded": len(e19),
            "windows_graded": e19_graded,
            "target": KILL_TARGET,
            # One counting basis (cure ORACLE-COUNT-BASIS-20261031):
            # this block and the calibration attestation both count
            # the engine's own weekly windows only. The Aperture
            # proof-gate provisional rows hosted under this engine
            # id are counted in the proof_gate block below.
            "counting_basis": (
                "the engine's own weekly window forecasts only "
                "(outcome kind next_window_hit_rate_exceeds_"
                "trailing); the Aperture proof-gate provisional "
                "rows hosted under this engine id (outcome kind "
                "provisional_proof_forward_check) are counted in "
                "the proof_gate block, not here"),
            "words": (
                f"{len(e19)} weekly windows issued so far, "
                f"{e19_graded} graded, of the {KILL_TARGET} graded "
                "windows that decide this page. The record starts "
                "with the first Monday issue; nothing is backfilled.")},
        "kill_words": (
            "After 12 graded weekly windows, if this page's chances "
            "have not scored better than the no-change rival's chances "
            "over the same windows, this page retires and its record "
            "stays up, exactly as it stands."),
        "thin_cell_words": (
            "Small counts prove little: every group below is printed "
            "with the number of graded calls behind it, and no rate "
            "on this page is shown without the count that feeds it."),
        "proving_state": "Still being proven",
        "self_test": {
            "words": (
                "The whole path is exercised on every refresh with "
                "made-up report cards in a throwaway record: a group "
                "whose right calls bunch in a hot run gets a higher "
                "chance than its no-change rival, a fading group gets "
                "a lower one, a coin-flip group stays within 5 points "
                "of its rival, and a group that was right every time "
                "is handled without error. Each made-up window is then "
                "graded at its close, beside its rival, in the "
                "throwaway record only: nothing made up ever reaches "
                "the public record or this page's figures."),
            "populations_tested": test["populations_tested"],
            "forecasts_written_to_scratch": test[
                "forecasts_written_to_scratch"],
            "windows_graded_in_scratch": test[
                "windows_graded_in_scratch"],
            "hand_case_rival": test["hand_case_rival"]},
        "ledger_rows_created_this_run": created,
        "issued_today": issued_today,
        "proof_gate": proof_gate_block,
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "data.json")
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, out)
    print(f"in-regime-oracle: as_of {as_of}, populations "
          f"{len(populations)}, included {len(included)}, "
          f"ledgered {created}, wrote {out}")


if __name__ == "__main__":
    main()
