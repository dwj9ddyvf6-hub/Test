#!/usr/bin/env python3
"""Refresh the Completion Clock (Forecast Engine 29).

=====================================================================
CANDIDATE-REGISTER TRIPLE (written before any computation)

1. EVIDENCE CLASS
   Timing evidence on record: the picker replay corpus (296,093
   graded cases, 3,446 names, 2019-12-20 to 2026-10-15) passed no
   setup family, and its own stored record on this disk is summary
   aggregates only, with a 20-session time stop, so it cannot be
   re-timed case by case here; it stands as shape context (what the
   setup families paid, tool 46's distributions) and as the warning
   that nothing directional is claimed. E3 (grade B): the corpus's
   best horizon sits near 60 sessions, which sets this engine's
   60-session cap. The X family's 1-to-5-session decay facts shape
   the early hazard. The settled fear-day definition (tool 16,
   reused verbatim by Engines 24 and 25, never re-derived here):
   SPY fell more than 1.5 percent in a day, or the fear gauge rose
   more than 15 percent in a day, or the fear gauge closed at or
   above 25, or it closed at or above 20 on a SPY/QQQ down day;
   22 such days stand in the settled record. Engine 25's exact
   coded deep-reset composite (found study code, followed here
   exactly, not the design text): a name counts as washed out when
   its close is at or below 65 percent of its highest high of the
   last 252 sessions and at or below 110 percent of its lowest low
   of the last 252; liquid means close above 5 and 20-session mean
   dollar volume above 5 million; a name needs at least 320
   bars on record and its own session index at least 260; the
   score is the mean of two signed
   percentile ranks (10-session return minus SPY's, sign negative;
   last-10 down-volume sum against its own prior-30 average, sign
   positive); the cohort is the top fifth, and days with fewer
   than 10 scored names form no group. Under that exact code only
   4 fear days in the shipped history form a pool at all (123, 127,
   61 and 153 names; 25, 26, 12 and 31 in the top fifth).
   Wall-break class record: 9 map cards, 6 graded one-session
   tests, the small-company fund's ceiling level reached and broke
   in both its tests (Engine 8's record, cross-checked here
   against the wall-grading page's own counters).
   This engine shares Engine 2's first-passage machinery and its
   price evidence family: the two are never counted as two
   confirmations, and the page says so wherever both appear.

2. RECONSTRUCTION CHOICES (every constant, named before computing)
   - Fusion reading (registered, not silent): the second panel's
     "resolution" is the SAME event as the first panel's, the
     first barrier reached. Its hazard at session k is the chance
     a cohort resolves exactly at elapsed session k given it was
     still unresolved before k, for k = 1 to 21, plus the median
     sessions to resolution. The parent candidate's other form
     (first close back above the event-day high, or below the
     event-day low for losers) is NOT used and NOT merged in.
   - Cohort median name: at each session after entry, the
     cohort's median close, median high and median low measured
     against each member's entry close. That median path races
     barriers at plus and minus 1 expected move (EM), where the
     EM is the median member's own EM. A member needs a bar on
     the entry day and at least 23 earlier sessions (the movement
     recipe's warm-up). The median path is followed while at
     least half the members still have bars, up to 60 sessions.
   - Expected move: Engine 1's construction, reused, never
     forked: recent-movement (HAR) forecast times sqrt(21/252)
     times 0.91, the 21-session figure. For SPY and QQQ the
     median EM is checked against Engine 1's published 68
     percent band half-width at 21 sessions to within 0.01
     points or this script fails closed. Per name, the same
     construction from the name's own recent movement (the
     Engine 6 precedent). HAR recipe copied from Engine 1:
     annualised vol = sqrt(252 * (daily + weekly + monthly)/3)
     over squared log returns, daily = last, weekly = mean of
     last 5, monthly = mean of last 22.
   - First passage: decided from the median path's daily high
     and low. Up first if the median high reaches +1 EM before
     the median low reaches -1 EM; if both levels are reached
     on the same session the race is recorded as its own
     "both on one day" class, never silently ordered (the
     picker corpus's stop-first rule is a trade rule and is
     not imported).
   - Market state (vol state): Engine 2's label verbatim,
     "jumpy" if SPY's recent-movement forecast on the entry day
     is above its own trailing-126 median, else "calm".
   - Buckets and floors (thin-cell rule everywhere, floor 30
     cohorts, the Engines 2/6/8 precedent): in order, (1) event
     class and market state, (2) event class any state, (3) all
     classes pooled; the first bucket with at least 30
     historical cohorts whose race could be followed for the
     full 60 sessions wins. The published picture is that
     bucket's picture pulled toward the event class's own
     unconditional picture with prior strength 20 (when the
     winning bucket IS the class, nothing is pulled). The
     wall-break class is always prior-dominated and stamped as
     such until its own graded count reaches 30: it has no
     historical cohorts of its own on this disk, so its picture
     is the pooled picture pulled toward a driftless barrier
     estimate (symmetric: the either-side chance by each
     horizon from the reflection estimate 4 x Phi(-1 EM /
     (daily spread x sqrt(h))), capped at 1, split evenly
     between the sides) with prior strength 20.
   - Hazard panel: from the winning bucket's resolution times,
     h(k) = resolved at k / still unresolved before k, k = 1
     to 21, pulled toward the class's own hazard the same way.
     Median sessions to resolution comes from the cumulative
     resolved share; when that share never crosses half by 60
     the median is stated as "past 60 / not reached", never
     invented. Deciles of sessions to first barrier come from
     the winning bucket's resolution times; the unresolved-at
     -60 share is printed as its own class beside them.
   - Denominators: a cohort counts at horizon h only when its
     median path could be followed for at least h sessions.
     Unresolved-at-60 cohorts stay in the denominator as their
     own outcome class; censored cohorts (path ran out early)
     are never dropped from the counts printed.
   - Event classes shipped:
     * Fear day: cohort = every name on record with a bar on a
       settled fear day (SPY itself excluded). History: all 22
       settled days, replayed over the shipped panel, ledgers
       nothing.
     * Deep reset: cohort = Engine 25's exact composite top
       fifth on a fear day. Engine 25's extra conditions (its
       market gate and its filings backing) are that engine's
       arms, NOT this engine's entry rule, and the page says so.
     * Wall break: fires forward only from new map cards whose
       grading record names a dated break. None stands open.
     * Earnings day: cohort = the names dated that day on the
       earnings calendar on record. A day needs at least 3 dated
       names present in the price history to form a cohort; a
       single-name day (one name is dated on the freshest
       session on record) is named on the page and never
       ledgered, because one name is not a cohort picture.
     * Big gap day: REGISTERED HERE, by this build, because no
       coded definition exists on disk: a name gaps at least
       1 times its own norm when |open / previous close - 1|
       is at least the median daily range share ((high - low)
       / previous close) over its own prior 60 sessions.
       Sanity guard: gaps over 25 percent are excluded as
       likely bad prints or splits. A session forms a cohort
       with at least 5 such names. Because this definition is
       registered today, this class fires only on sessions
       after today; earlier sessions are history, never
       backfilled.
     * First tag of a stock's own deepest past dip: CANNOT
       fire in its stated form today. It needs 750 of a stock's
       own past sessions (an 813-session floor with the rest of
       the recipe); the longest history on record is 399
       sessions and the long panel is not on this disk. The
       class ships named as waiting on that panel, exactly as
       Engine 3 does; a shorter-window substitute is never
       silently used.
   - Priors: computed by replaying the cohort definitions
     above over the shipped daily history (399 sessions, 1,833
     names, 2025-03-25 to 2026-10-23, a survivors roster),
     exactly as Engines 24 and 25 ran their history. That
     replay ledgers nothing. What this narrows, stated plainly:
     the picker corpus's per-case rows and the long price
     panel are not on this disk, so the 60-session tail rests
     on the shipped panel's span alone and the claim narrows
     to match.
   - Ledger shape: ONE forecast per cohort through the shared
     machinery only (forecast/ledger.py append_forecast).
     Subject = event class + entry session. The value carries
     both panels in one object: barrier-race chances at 5, 10,
     21 and 60 (up first, down first, both on one day, neither
     yet), the sessions-to-first-barrier deciles plus the
     unresolved-at-60 share, the hazard panel h(1..21) and the
     median sessions, the event class, market state, cohort
     size, bucket used and its count, and a "resolved_by"
     sub-object (cumulative resolved share at 5/10/21/60) in
     the exact shape the shared survival scorer reads.
     Outcome spec: kind "cohort_barrier_race" naming the
     cohort-median race; the shared grading runner resolves
     that kind through the record path built 2026-10-30
     (RC-19 cure): the cohort race record (its
     sessions_to_resolution) is supplied to the grading pass
     and scored by the shared survival Brier rule. No live
     row can mature until its horizon passes in any case.
   - Live rule: a cohort ledgers only when its entry session
     is the freshest session the machinery reaches AND that
     session is on or after this engine's ship date
     (2026-10-29). Anything older is history, labelled, never
     ledgered. Ship date is before the freshest panel session
     can qualify today: the freshest session on record is
     2026-10-23, which is not a fear day (SPY fell 0.52 percent
     that day), forms no deep-reset cohort (deep reset is
     fear-day gated), has no graded wall break standing open,
     and carries exactly one dated earnings name; so the
     expected live outcome of this build is the standing
     machinery with the classes and their priors, and 0 new
     ledger rows.
   - Kill criterion (registry, verbatim): after 30 matured
     cohorts, its timing Brier is no better than the
     unconditional hazard. A cohort matures at resolution or
     at 60 sessions, unresolved-at-60 counting as matured with
     its own outcome class. Proving threshold: 30 matured
     cohorts.
   - Thin-cell rule: any picture built on fewer than 30
     cohorts shows its count and is labelled thin; a class
     with no cohorts shows no picture at all.

3. NON-CLAIMS
   - No direction is forecast for any stock, and no average
     payoff is stated: this engine times a race, it does not
     price one. No claim beyond the shipped panel's span for
     the priors. The history replay is a backfill computed
     today, not a live record; it ledgers nothing. Agreement
     with Engine 2 is never a second confirmation (same
     machinery, same family). The wall-break picture is a
     labelled starting estimate, not a track record. The
     deep-reset class borrows Engine 25's entry composite
     only, not its gate, its filings arms, or its claim.

=====================================================================
Behaviour: history priors computed from the corpus records and
the shipped panel (ledgers nothing); the live pipeline ledgers,
via the machinery API only, a timing forecast for any cohort
genuinely entered at the freshest session, and otherwise
publishes the standing machinery with the classes and their
priors. data.json is idempotent; timestamps come from the
sources only; the script fails closed on any disagreement with
a source record or the ledger.
"""

import bisect
import json
import math
import os
import sys
from datetime import date, timedelta
from statistics import NormalDist, median

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(HERE)
PANEL_PATH = os.path.expanduser("~/workspace/morgue/data_cache/board_bt_bars.json")
LEDGER_PATH = os.path.join(LINEUP, "forecast", "ledger.jsonl")
FEARDAY_PATH = os.path.join(HERE, "fear-day-triangulation", "data.json")
BAND_PATH = os.path.join(HERE, "corrected-band", "data.json")
EARNINGS_PATH = os.path.join(HERE, "earnings-calendar", "data.json")
WALLCHECK_PATH = os.path.join(HERE, "wall-check", "data.json")
WALLLIFE_PATH = os.path.join(HERE, "wall-lifetime", "data.json")
MAPCARD_PATH = os.path.expanduser("~/workspace/morgue/output/map_card.json")
PICKER_PATH = os.path.join(
    LINEUP, "records", "picker-replay-2026-10-27",
    "picker-replay-2026-10-27.json")
OUT_PATH = os.path.join(HERE, "completion-clock", "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import attestation_block as _ab
except ImportError:  # refresh stays runnable standalone
    _ab = None

SHIP_DATE = "2026-10-29"
ENGINE_ID = "engine_29"
HORIZONS = (5, 10, 21, 60)
HAZARD_K = 21
FLOOR = 30
PRIOR_STRENGTH = 20.0
WARMUP = 22
K21 = 0.91

sys.path.insert(0, LINEUP)
from forecast import ledger as ledger_mod  # noqa: E402
from forecast import registry as registry_mod  # noqa: E402
from forecast import grading as grading_mod  # noqa: E402


def fail(msg):
    print(f"Completion Clock refresh: {msg}", file=sys.stderr)
    return 1


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def next_weekdays(after_iso, count):
    d = date.fromisoformat(after_iso)
    out = []
    while len(out) < count:
        d += timedelta(days=1)
        if d.weekday() < 5:
            out.append(d.isoformat())
    return out


# ---- movement recipe (Engine 1's, reused) ---------------------------------
def har_annualised_vol(sq_returns, i):
    """sq_returns[j] is the squared log return into closes[j+1].
    Forecast at base close index i uses sq[i-22:i] only."""
    daily = sq_returns[i - 1]
    weekly = sum(sq_returns[i - 5:i]) / 5.0
    monthly = sum(sq_returns[i - WARMUP:i]) / WARMUP
    return math.sqrt(252.0 * (daily + weekly + monthly) / 3.0)


def sq_log_returns(closes):
    return [math.log(closes[j + 1] / closes[j]) ** 2
            for j in range(len(closes) - 1)]


def em21_pct(closes, i):
    """21-session expected move in percent at close index i."""
    if i < WARMUP:
        return None
    sq = sq_log_returns(closes[:i + 1])
    vol = har_annualised_vol(sq, i)
    return vol * math.sqrt(21 / 252.0) * K21 * 100.0


# ---- deep-reset composite (Engine 25's exact coded form) ------------------
def down_volumes(closes, vols):
    out = [0.0]
    for j in range(1, len(closes)):
        out.append(vols[j] if closes[j] < closes[j - 1] else 0.0)
    return out


def reset_features(closes, highs, lows, vols, i, spy_r10):
    if len(closes) < 320 or i < 260 or i < 251 or i < 39 or i < 10:
        return None
    close = closes[i]
    hi = max(highs[i - 251:i + 1])
    lo = min(lows[i - 251:i + 1])
    if not (close <= 0.65 * hi and close <= 1.10 * lo):
        return None
    dv20 = sum(closes[j] * vols[j] for j in range(i - 19, i + 1)) / 20.0
    if not (close > 5.0 and dv20 > 5_000_000.0):
        return None
    dv = down_volumes(closes, vols)
    recent = sum(dv[i - 9:i + 1])
    prior = sum(dv[i - 39:i - 9]) / 3.0
    if prior <= 0 or spy_r10 is None:
        return None
    f6 = recent / prior
    f7 = closes[i] / closes[i - 10] - 1.0 - spy_r10
    return {"f6": f6, "f7": f7}


def composite_top_fifth(scored):
    """scored: [(symbol, f7, f6)]. Top fifth under the study
    code's grouping; [] under 10 scored."""
    n = len(scored)
    if n < 10:
        return []

    def pct_ranks(vals):
        order = sorted(range(n), key=lambda k: vals[k])
        ranks = [0.0] * n
        k = 0
        while k < n:
            j = k
            while j + 1 < n and vals[order[j + 1]] == vals[order[k]]:
                j += 1
            avg = (k + j) / 2.0 + 1.0
            for t in range(k, j + 1):
                ranks[order[t]] = avg / n
            k = j + 1
        return ranks

    r7 = pct_ranks([s[1] for s in scored])
    r6 = pct_ranks([s[2] for s in scored])
    scores = [(-r7[k] + r6[k]) / 2.0 for k in range(n)]
    order = sorted(range(n), key=lambda k: (scores[k], k))
    first_rank = [0] * n
    for pos, k in enumerate(order):
        first_rank[k] = pos + 1
    vals = sorted(first_rank)

    def quantile(q):
        pos = q * (n - 1)
        base = int(pos)
        frac = pos - base
        if base + 1 >= n:
            return float(vals[-1])
        return vals[base] + frac * (vals[base + 1] - vals[base])

    edges = [quantile(q / 5.0) for q in range(1, 5)]
    return [scored[k][0] for k in range(n)
            if bisect.bisect_left(edges, first_rank[k]) == 4]


# ---- the cohort race -------------------------------------------------------
def cohort_race(members, entry_date, spy_dates, spy_pos):
    """members: list of (symbol, rows, date->index, em_pct), rows
    in panel tuple form (date, open, high, low, close, volume).
    Returns a record dict or None when no member can be followed."""
    usable = []
    for sym, rows, pos, em in members:
        if entry_date in pos and em is not None:
            usable.append((sym, rows, pos, em,
                           rows[pos[entry_date]][4]))
    if not usable:
        return None
    em_med = median([u[3] for u in usable])
    start = spy_pos[entry_date]
    path = []  # (median_high_ret, median_low_ret) per session
    for t in range(1, 61):
        if start + t >= len(spy_dates):
            break
        day = spy_dates[start + t]
        hs, ls = [], []
        for sym, rows, pos, em, c0 in usable:
            k = pos.get(day)
            if k is None:
                continue
            hs.append(rows[k][2] / c0 - 1.0)
            ls.append(rows[k][3] / c0 - 1.0)
        if len(hs) < max(1, len(usable) // 2):
            break
        path.append((median(hs) * 100.0, median(ls) * 100.0))
    t_up = t_down = None
    for t, (mh, ml) in enumerate(path, 1):
        if t_up is None and mh >= em_med:
            t_up = t
        if t_down is None and ml <= -em_med:
            t_down = t
        if t_up is not None and t_down is not None:
            break
    if t_up is not None and t_down is not None and t_up == t_down:
        outcome, t_res = "both", t_up
    elif t_up is not None and (t_down is None or t_up < t_down):
        outcome, t_res = "up", t_up
    elif t_down is not None:
        outcome, t_res = "down", t_down
    else:
        outcome, t_res = "unresolved", None
    return {"size": len(usable), "em_pct": em_med, "observable": len(path),
            "outcome": outcome, "t_res": t_res,
            "t_up": t_up, "t_down": t_down}


def picture(records, pooled_records, driftless=None,
            driftless_hazard=None):
    """Build the published timing picture for one class.
    records: the class's own cohort race records. pooled_records:
    every class's records. driftless: optional resolved-by curve
    {horizon: share} used as the pull target instead of the
    pooled picture (wall-break class)."""
    def full(rs):
        return [r for r in rs if r["observable"] >= 60]

    def race_probs(rs):
        out = {}
        for h in HORIZONS:
            sub = [r for r in rs if r["observable"] >= h]
            n = len(sub)
            if n == 0:
                out[h] = None
                continue
            up = sum(1 for r in sub if r["outcome"] == "up"
                     and r["t_res"] <= h) / n
            dn = sum(1 for r in sub if r["outcome"] == "down"
                     and r["t_res"] <= h) / n
            bo = sum(1 for r in sub if r["outcome"] == "both"
                     and r["t_res"] <= h) / n
            out[h] = {"up": up, "down": dn, "both": bo,
                      "neither": max(0.0, 1.0 - up - dn - bo), "n": n}
        return out

    def hazard(rs):
        sub = [r for r in rs if r["observable"] >= HAZARD_K]
        out = []
        for k in range(1, HAZARD_K + 1):
            risk = sum(1 for r in sub
                       if r["t_res"] is None or r["t_res"] >= k)
            res = sum(1 for r in sub if r["t_res"] == k)
            out.append(res / risk if risk else 0.0)
        return out

    def res_times(rs):
        return sorted(r["t_res"] for r in full(rs)
                      if r["t_res"] is not None)

    class_full = full(records)
    pooled_full = full(pooled_records)
    if len(class_full) >= FLOOR:
        bucket, base, base_n = "class", records, len(class_full)
    elif len(pooled_full) >= FLOOR:
        bucket, base, base_n = "pooled", pooled_records, len(pooled_full)
    else:
        bucket, base, base_n = "pooled_thin", pooled_records, len(pooled_full)
    base_race = race_probs(base)
    class_race = race_probs(records)
    if driftless is not None:
        target_race = {h: {"up": driftless[h] / 2.0,
                           "down": driftless[h] / 2.0, "both": 0.0,
                           "neither": 1.0 - driftless[h], "n": 0}
                       for h in HORIZONS}
    else:
        target_race = class_race
    race = {}
    for h in HORIZONS:
        b, t = base_race[h], target_race[h]
        if b is None:
            race[h] = None
            continue
        if bucket == "class" or t is None:
            race[h] = b
        else:
            race[h] = {k: (base_n * b[k] + PRIOR_STRENGTH * t[k])
                       / (base_n + PRIOR_STRENGTH)
                       for k in ("up", "down", "both", "neither")}
            race[h]["n"] = b["n"]
    base_haz = hazard(base)
    class_haz = driftless_hazard if driftless is not None \
        else hazard(records)
    if bucket == "class":
        haz = base_haz
    else:
        haz = [(base_n * b + PRIOR_STRENGTH * c) / (base_n + PRIOR_STRENGTH)
               if base_n else c for b, c in zip(base_haz, class_haz)]
    times = res_times(base)
    deciles = []
    for q in range(1, 10):
        if not times:
            deciles.append(None)
        else:
            pos = q / 10.0 * (len(times) - 1)
            lo_i, frac = int(pos), pos - int(pos)
            deciles.append(round(times[lo_i] + frac * (
                times[min(lo_i + 1, len(times) - 1)] - times[lo_i]), 1))
    unresolved60 = (sum(1 for r in class_full if r["t_res"] is None)
                    / len(class_full)) if class_full else None
    # median sessions from the published hazard's cumulative
    # resolved share; past 21 fall back to the 60-session share
    med = None
    surv = 1.0
    for k, hk in enumerate(haz, 1):
        surv *= (1.0 - hk)
        if 1.0 - surv >= 0.5:
            med = k
            break
    if med is None and race[60] and (race[60]["up"] + race[60]["down"]
                                     + race[60]["both"]) >= 0.5:
        med = 60
    resolved_by = {str(h): (round(race[h]["up"] + race[h]["down"]
                                  + race[h]["both"], 4) if race[h] else None)
                   for h in HORIZONS}
    return {"bucket": bucket, "bucket_cohorts": base_n,
            "class_cohorts": len(records),
            "class_cohorts_full60": len(class_full),
            "race": race, "hazard": [round(x, 4) for x in haz],
            "deciles": deciles, "unresolved60_share": unresolved60,
            "median_sessions": med, "resolved_by": resolved_by,
            "thin": len(class_full) < FLOOR and bucket != "class"}


def self_test():
    """Synthetic race: median path hits +1 EM at session 3 and the
    survival scorer accepts the published value shape."""
    nd = NormalDist()
    assert abs(nd.cdf(0.0) - 0.5) < 1e-12
    dates = next_weekdays("2026-01-01", 70)
    spy_pos = {d: i for i, d in enumerate(dates)}
    members = []
    for s in range(3):
        rows = []
        pos = {}
        for i, d in enumerate(dates):
            close = 100.0 * (1.01 ** i)
            pos[d] = i
            rows.append((d, close, close * 1.002, close * 0.999,
                         close, 1000))
        members.append((f"S{s}", rows, pos, 2.0))
    rec = cohort_race(members, dates[0], dates, spy_pos)
    ok = (rec is not None and rec["outcome"] == "up"
          and rec["t_res"] is not None and rec["t_res"] <= 5)
    val = {"resolved_by": {"5": 0.4, "10": 0.5, "21": 0.6, "60": 0.7}}
    scores = grading_mod.score_survival_brier(val, 61, None)
    ok = ok and set(scores) == {"brier@5", "brier@10",
                                "brier@21", "brier@60"}
    return {"passed": bool(ok),
            "words": ("A made-up group whose middle stock climbs "
                      "steadily reaches the upper barrier first, "
                      "and the timing value this page publishes is "
                      "read correctly by the shared scoring rule."
                      if ok else "The self-test FAILED; see the "
                      "refresh output.")}


def build():
    for path in (PANEL_PATH, FEARDAY_PATH, BAND_PATH, EARNINGS_PATH,
                 WALLCHECK_PATH, WALLLIFE_PATH, MAPCARD_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")
    panel_raw = load_json(PANEL_PATH)
    fearday = load_json(FEARDAY_PATH)
    bands = load_json(BAND_PATH)
    earnings = load_json(EARNINGS_PATH)
    wallcheck = load_json(WALLCHECK_PATH)
    walllife = load_json(WALLLIFE_PATH)
    mapcard = load_json(MAPCARD_PATH)

    # ---- panel, cross-checked ---------------------------------------------
    panel = {}
    for sym, rows in panel_raw.items():
        panel[sym] = [(r[0], float(r[1]), float(r[2]), float(r[3]),
                       float(r[4]), float(r[5])) for r in rows]
    spy = panel.get("SPY")
    if not spy:
        return fail("the shipped panel carries no SPY history")
    spy_dates = [r[0] for r in spy]
    spy_pos = {d: i for i, d in enumerate(spy_dates)}
    freshest = spy_dates[-1]
    if any(rows[-1][0] > freshest for rows in panel.values()):
        return fail("a name's history runs past SPY's freshest "
                    "session; sources disagree")
    by_date = {sym: {r[0]: r for r in rows}
               for sym, rows in panel.items()}
    closes = {sym: [r[4] for r in rows] for sym, rows in panel.items()}
    highs = {sym: [r[2] for r in rows] for sym, rows in panel.items()}
    lows = {sym: [r[3] for r in rows] for sym, rows in panel.items()}
    vols = {sym: [r[5] for r in rows] for sym, rows in panel.items()}

    # ---- settled fear days, cross-checked, never re-derived ---------------
    fear_entries = (fearday.get("fear_days_in_record") or {}).get("days") or []
    fear_days = [e["date"] for e in fear_entries]
    # The register's 22 days was the settled record's count at
    # design time, not a pin (cure 2026-10-30, the coverage pin
    # class): the VIX capture cure legitimately grew the gauge
    # record and Engine 24's detection now settles 65 days, so
    # an equality demand refuses a healthy record forever. The
    # check binds the floor the register names and the panel
    # agreement, and the SPY arm cross-check below still binds.
    if len(fear_days) < 22 or any(d not in spy_pos for d in fear_days):
        return fail("the settled fear-day record does not hold "
                    "even the 22 days this engine's register "
                    "names, or holds a day the panel does not")
    spy_fear_check = [d for d in fear_days
                      if spy[spy_pos[d]][4] / spy[spy_pos[d] - 1][4] - 1
                      <= -0.015]
    if len(spy_fear_check) < 20:
        return fail("the panel disagrees with the settled fear-day "
                    "record on the SPY arm")

    # ---- Engine 1 band cross-check for SPY/QQQ EM --------------------------
    band_half = {}
    for nm in (bands.get("live") or {}).get("names") or []:
        for hz in nm.get("horizons") or []:
            if hz.get("sessions") == 21:
                for b in hz.get("bands") or []:
                    if b.get("level") == 68:
                        band_half[nm.get("symbol") or nm.get("name")] = \
                            b["half_pct"]
    # Engine 1's published live band carries its FE12 session
    # quality guard widening when the guard is recorded (cure
    # 2026-10-30: the guard went live and this cross-check,
    # written while the guard stood not_recorded at factor
    # 1.0, refused the widened band forever). The comparison
    # is made on the un widened basis, using the widen factor
    # Engine 1 publishes on its own page; the factor is stated
    # in the check so the widening is never absorbed silently.
    guard_factor = 1.0
    _guard = (bands.get("live") or {}).get("session_quality_guard") \
        or {}
    if _guard.get("band_widen_factor"):
        guard_factor = float(_guard["band_widen_factor"])
    em_check = {}
    for sym in ("SPY", "QQQ"):
        i = spy_pos[freshest] if sym == "SPY" else None
        rows = panel[sym]
        j = len(rows) - 1
        if rows[j][0] != freshest:
            return fail(f"{sym}'s freshest session is not the "
                        "panel's freshest session")
        mine = em21_pct(closes[sym], j)
        theirs = band_half.get(sym)
        if theirs is None or mine is None \
                or abs(mine - theirs / guard_factor) > 0.01:
            return fail(f"the 21-session expected move for {sym} "
                        "disagrees with Engine 1's published band")
        em_check[sym] = {"ours_pct": round(mine, 4),
                         "engine1_pct": theirs,
                         "engine1_guard_widen_factor": guard_factor}

    # ---- market state labels (Engine 2's verbatim rule on SPY) -------------
    spy_sq = sq_log_returns(closes["SPY"])
    spy_har = {}
    for i in range(WARMUP, len(spy_dates)):
        spy_har[spy_dates[i]] = har_annualised_vol(spy_sq, i)

    def market_state(day):
        i = spy_pos[day]
        if i < WARMUP + 126:
            return "calm"
        today = spy_har.get(day)
        past = [spy_har[spy_dates[j]] for j in range(i - 126, i + 1)
                if spy_dates[j] in spy_har]
        return "jumpy" if today is not None and past \
            and today > median(past) else "calm"

    # ---- member builder -----------------------------------------------------
    sym_pos = {sym: {r[0]: k for k, r in enumerate(rows)}
               for sym, rows in panel.items()}

    def members_for(symbols, entry_date):
        out = []
        for sym in symbols:
            if sym == "SPY" or sym not in panel:
                continue
            i = sym_pos[sym].get(entry_date)
            if i is None or i < WARMUP:
                continue
            em = em21_pct(closes[sym], i)
            if em is None or em <= 0:
                continue
            out.append((sym, panel[sym], sym_pos[sym], em))
        return out

    all_records = {}
    class_meta = {}

    # ---- history: fear-day cohorts ------------------------------------------
    fear_records = []
    for day in fear_days:
        rec = cohort_race(members_for(list(panel.keys()), day),
                          day, spy_dates, spy_pos)
        if rec:
            rec["date"] = day
            rec["state"] = market_state(day)
            fear_records.append(rec)
    all_records["fear_day"] = fear_records

    # ---- history: deep-reset cohorts (Engine 25's exact composite) ----------
    spy_r10 = {}
    for i in range(10, len(spy_dates)):
        spy_r10[spy_dates[i]] = closes["SPY"][i] / closes["SPY"][i - 10] \
            - 1.0
    reset_records = []
    reset_days = []
    for day in fear_days:
        i = spy_pos[day]
        scored = []
        for sym in panel:
            if sym == "SPY":
                continue
            rows = panel[sym]
            idx = None
            for k, r in enumerate(rows):
                if r[0] == day:
                    idx = k
                    break
            if idx is None:
                continue
            feat = reset_features(closes[sym], highs[sym], lows[sym],
                                  vols[sym], idx, spy_r10.get(day))
            if feat:
                scored.append((sym, feat["f7"], feat["f6"]))
        top = composite_top_fifth(scored)
        if top:
            reset_days.append({"date": day, "pool": len(scored),
                               "matching": len(top)})
            rec = cohort_race(members_for(top, day), day,
                              spy_dates, spy_pos)
            if rec:
                rec["date"] = day
                rec["state"] = market_state(day)
                reset_records.append(rec)
    # Registered pool days (terminal audit cure, 2026-10-31):
    # the exact-equality demand on the count broke the first
    # time a new fear day settled (2026-10-30, SPY down 1.77
    # percent, the 66th settled day), because a settled record
    # only grows. The audited claim is narrower and stays exact:
    # each registered pool day reproduces with its registered
    # pool and matching counts under the exact composite. New
    # pool days beyond the register are new settled history and
    # are published, not refused.
    _REGISTERED_RESET = {"2026-06-05": (123, 25),
                         "2026-06-10": (127, 26),
                         "2026-07-29": (61, 12),
                         "2026-10-16": (153, 31)}
    _by_day = {r["date"]: r for r in reset_days}
    for _day, (_pool, _matching) in _REGISTERED_RESET.items():
        _got = _by_day.get(_day)
        if _got is None or _got["pool"] != _pool \
                or _got["matching"] != _matching:
            return fail("the deep-reset history does not "
                        "reproduce the registered pool day "
                        f"{_day} (pool {_pool}, matching "
                        f"{_matching}) under the exact composite: "
                        f"got {_got}")
    all_records["deep_reset"] = reset_records

    # ---- history: earnings-day cohorts --------------------------------------
    earn_by_date = {}
    for nm in earnings.get("names") or []:
        earn_by_date.setdefault(nm["date"], []).append(nm["symbol"])
    earn_records = []
    for day, syms in sorted(earn_by_date.items()):
        if day not in spy_pos or len(syms) < 3:
            continue
        rec = cohort_race(members_for(syms, day), day,
                          spy_dates, spy_pos)
        if rec:
            rec["date"] = day
            rec["state"] = market_state(day)
            earn_records.append(rec)
    all_records["earnings_day"] = earn_records
    fresh_earn = earn_by_date.get(freshest) or []

    # ---- history: big-gap cohorts (definition registered above) -------------
    gap_records = []
    gap_cohorts = {}
    for sym, rows in panel.items():
        if sym == "SPY" or len(rows) < 62:
            continue
        rng = [(rows[j][2] - rows[j][3]) / rows[j - 1][4]
               for j in range(1, len(rows))]
        for j in range(61, len(rows)):
            prev_close = rows[j - 1][4]
            if prev_close <= 0:
                continue
            gap = rows[j][1] / prev_close - 1.0
            if abs(gap) > 0.25:
                continue
            norm = median(rng[j - 61:j - 1])
            if norm > 0 and abs(gap) >= norm:
                gap_cohorts.setdefault(rows[j][0], []).append(sym)
    for day, syms in sorted(gap_cohorts.items()):
        if len(syms) < 5 or day not in spy_pos:
            continue
        rec = cohort_race(members_for(syms, day), day,
                          spy_dates, spy_pos)
        if rec:
            rec["date"] = day
            rec["state"] = market_state(day)
            gap_records.append(rec)
    all_records["gap_day"] = gap_records

    pooled = [r for rs in all_records.values() for r in rs]

    # ---- wall-break record, cross-checked -----------------------------------
    wc_tests = sum(n.get("tests") or 0
                   for n in wallcheck.get("by_name") or [])
    wc_broke = sum(n.get("upper_broke") or 0
                   for n in wallcheck.get("by_name") or [])
    # Wall register re-registered 2026-10-30 (engine refresh
    # cure): the wall-grading record grew from 9 graded tests /
    # 4 breaks to 12 / 4 when the 2026-10-30 session's tests
    # graded; counts counted from wall-check/data.json by_name
    # on this date. (First registered 2026-10-29, cure G17.)
    if wc_tests != 12 or wc_broke != 4:
        return fail("the wall-grading record disagrees with the "
                    "12 graded tests and 4 breaks on record")
    cards_on_record = 9  # SPY/QQQ/IWM x 2026-10-26/27/28, Engine 8 record
    wall_asof = walllife.get("published_at_utc")
    nd = NormalDist()
    spy_daily_spread = (spy_har.get(freshest) or 0.0) / math.sqrt(252.0)
    em_frac = (em21_pct(closes["SPY"], len(spy_dates) - 1) or 0.0) / 100.0
    driftless = {}
    drift_cum = {}
    for h in list(HORIZONS) + list(range(1, HAZARD_K + 1)):
        if spy_daily_spread > 0:
            drift_cum[h] = min(1.0, 4.0 * nd.cdf(
                -em_frac / (spy_daily_spread * math.sqrt(h))))
        else:
            drift_cum[h] = 0.0
    driftless = {h: drift_cum[h] for h in HORIZONS}
    driftless_hazard = []
    prev = 0.0
    for k in range(1, HAZARD_K + 1):
        cum = drift_cum[k]
        driftless_hazard.append(
            (cum - prev) / (1.0 - prev) if prev < 1.0 else 0.0)
        prev = cum

    # ---- pictures -------------------------------------------------------------
    def pct(x):
        return None if x is None else round(x * 100.0, 1)

    def class_block(cid, records, drift=None, drift_haz=None):
        pic = picture(records, pooled, driftless=drift,
                      driftless_hazard=drift_haz)
        race = []
        for h in HORIZONS:
            r = pic["race"][h]
            race.append({"sessions": h,
                         "up_first_pct": pct(r["up"]) if r else None,
                         "down_first_pct": pct(r["down"]) if r else None,
                         "both_one_day_pct": pct(r["both"]) if r else None,
                         "neither_yet_pct": pct(r["neither"]) if r else None,
                         "cohorts_counted": r["n"] if r else 0})
        return {"picture": pic, "race": race,
                "hazard_pct": [pct(x) for x in pic["hazard"]]}

    blocks = {}
    blocks["fear_day"] = class_block("fear_day", fear_records)
    blocks["deep_reset"] = class_block("deep_reset", reset_records)
    blocks["earnings_day"] = class_block("earnings_day", earn_records)
    blocks["gap_day"] = class_block("gap_day", gap_records)
    blocks["wall_break"] = class_block("wall_break", [], drift=driftless,
                                       drift_haz=driftless_hazard)
    test = self_test()
    if not test["passed"]:
        return fail("the self-test failed; nothing was published")

    # ---- live pipeline ---------------------------------------------------------
    reg = registry_mod.load()
    led = ledger_mod.Ledger(LEDGER_PATH, registry=reg)
    rows_before = led.rows()
    if not led.verify_chain(rows_before):
        return fail("the shared ledger's chain does not verify")
    existing29 = [r for r in rows_before
                  if r.get("engine_id") == ENGINE_ID
                  and r.get("type") == "forecast"]
    ledgered_now = []
    fresh_is_fear = freshest in fear_days
    live_note_parts = []
    if freshest >= SHIP_DATE:
        fires = []
        if fresh_is_fear:
            fires.append(("fear_day", list(panel.keys())))
            scored = []
            i = spy_pos[freshest]
            for sym in panel:
                if sym == "SPY":
                    continue
                rows = panel[sym]
                idx = None
                for k, r in enumerate(rows):
                    if r[0] == freshest:
                        idx = k
                        break
                if idx is None:
                    continue
                feat = reset_features(closes[sym], highs[sym],
                                      lows[sym], vols[sym], idx,
                                      spy_r10.get(freshest))
                if feat:
                    scored.append((sym, feat["f7"], feat["f6"]))
            top = composite_top_fifth(scored)
            if top:
                fires.append(("deep_reset", top))
        if len(fresh_earn) >= 3:
            fires.append(("earnings_day", fresh_earn))
        gap_today = [s for s in gap_cohorts.get(freshest) or []]
        if len(gap_today) >= 5:
            fires.append(("gap_day", gap_today))
        lineage = {
            "clocks": {
                "event_time": freshest,
                "publication_time": freshest,
                "first_available_time": freshest,
                "ingestion_time": freshest,
                "decision_as_of": freshest},
            "source_artifacts": [
                {"path": PANEL_PATH,
                 "sha256": ledger_mod.file_sha256(PANEL_PATH)},
                {"path": FEARDAY_PATH,
                 "sha256": ledger_mod.file_sha256(FEARDAY_PATH)}]}
        for cid, syms in fires:
            members = members_for(syms, freshest)
            if not members:
                continue
            pic = blocks[cid]["picture"]
            value = {
                "event_class": cid,
                "market_state": market_state(freshest),
                "cohort_size": len(members),
                "median_em_pct": round(median([m[3] for m in members]), 4),
                "barrier_race": {str(r["sessions"]): {
                    "up_first": r["up_first_pct"],
                    "down_first": r["down_first_pct"],
                    "both_one_day": r["both_one_day_pct"],
                    "neither_yet": r["neither_yet_pct"]}
                    for r in blocks[cid]["race"]},
                "deciles_sessions": pic["deciles"],
                "unresolved_at_60_share": pic["unresolved60_share"],
                "hazard_1_21": pic["hazard"],
                "median_sessions": pic["median_sessions"],
                "resolved_by": pic["resolved_by"],
                "bucket_used": pic["bucket"],
                "bucket_cohorts": pic["bucket_cohorts"]}
            horizon_open = next_weekdays(freshest, 1)[0]
            horizon_close = next_weekdays(freshest, 60)[-1]
            row, created = led.append_forecast_declared(
                engine_id=ENGINE_ID,
                issued_ts=freshest,
                subject=f"{cid}:{freshest}",
                quantity="cohort timing density: barrier race at "
                         "5/10/21/60 sessions plus sessions-since "
                         "hazard panel",
                value=value,
                horizon_open=horizon_open,
                horizon_close=horizon_close,
                lineage=lineage,
                families=["price"] if cid != "wall_break"
                         else ["price", "modelled_inventory"],
                outcome={"kind": "cohort_barrier_race",
                         "event_class": cid,
                         "entry_session": freshest,
                         "note": "graded by survival calibration and "
                                 "barrier-race Brier at 5/10/21/60 "
                                 "against the class's unconditional "
                                 "hazard through the shared runner's "
                                 "record path (RC-19 cure, "
                                 "2026-10-30); unresolved-at-60 "
                                 "stays as its own outcome class"})
            if created:
                ledgered_now.append(cid)
    rows_after = led.rows()
    if not led.verify_chain(rows_after):
        return fail("the shared ledger's chain broke after append")
    live_rows = [r for r in rows_after
                 if r.get("engine_id") == ENGINE_ID
                 and r.get("type") == "forecast"]
    grade_rows = [r for r in rows_after
                  if r.get("engine_id") == ENGINE_ID
                  and r.get("type") == "grade"]
    matured = len(grade_rows)

    if freshest < SHIP_DATE:
        live_words = (
            "No group stands open. The freshest session on record "
            f"({freshest}) predates this page's first day "
            f"({SHIP_DATE}), and it was not a fear day in any case: "
            "SPY fell 0.52 percent that day, no deep-reset group "
            "can form without a fear day, no graded wall break "
            "stands open, and exactly one earnings name was dated "
            "that day, which is a single stock, not a group. The "
            "first group will be the first qualifying event on a "
            "session this page can reach in time, written down "
            "before its first barrier session opens. Anything "
            "older is history, never backfilled.")
    elif ledgered_now:
        live_words = ("Cohorts were written to the public record "
                      "today for: " + ", ".join(ledgered_now) + ".")
    else:
        live_words = ("No qualifying event fired on the freshest "
                      "session, so nothing was written down today.")

    def fmt_day(iso):
        return date.fromisoformat(iso).strftime("%A, %B %-d, %Y")

    classes_out = [
        {"id": "fear_day", "name": "Fear day",
         "words": ("A day the settled fear test flags: SPY fell "
                   "more than 1.5 percent, or the fear gauge jumped "
                   "more than 15 percent, or closed at 25 or more, "
                   "or at 20 or more on a down day for the big "
                   "funds. The group is every stock on record that "
                   "day."),
         "can_fire": ("Yes, from the price history and the fear "
                      "gauge readings as they accrue."),
         **blocks["fear_day"]},
        {"id": "deep_reset", "name": "Deep reset",
         "words": ("On a fear day, the washed-out stocks that top "
                   "the combined score of trailing weakness and "
                   "heavy falling-day trading: at least 35 percent "
                   "below their highest high of the past year and "
                   "sitting near their lowest low. This page uses "
                   "that entry rule only; the sister tool's extra "
                   "market test and filings backing are its own "
                   "arms, not this page's entry rule."),
         "can_fire": ("Yes, but only on a fear day, and only 4 "
                      "fear days in the history on record formed a "
                      "scored group at all."),
         **blocks["deep_reset"]},
        {"id": "wall_break", "name": "Wall break",
         "words": ("A morning map level, the ceiling, the floor "
                   "or the flip level, is reached and closed "
                   "through. The group is the fund whose level "
                   "broke."),
         "can_fire": ("Yes, from new morning map cards as their "
                      "grading lands."),
         "prior_stamp": ("Starting estimate only: this class's "
                         "own record is 9 map cards and 6 graded "
                         "tests with 2 breaks, so the starting "
                         "estimate carries the picture until its "
                         "own graded count reaches 30."),
         "record_counts": {"cards": cards_on_record,
                           "graded_tests": wc_tests,
                           "breaks": wc_broke,
                           "as_of": wall_asof},
         **blocks["wall_break"]},
        {"id": "earnings_day", "name": "Earnings day",
         "words": ("A day when at least 3 companies on the "
                   "earnings calendar on record report. The group "
                   "is those companies. A day with a single dated "
                   "company never forms a group here: one stock "
                   "is not a group picture."),
         "can_fire": ("Yes, from the earnings calendar and the "
                      "price history."),
         **blocks["earnings_day"]},
        {"id": "gap_day", "name": "Big gap day",
         "words": ("A day when at least 5 stocks open at least "
                   "their own usual daily range away from the "
                   "previous close (gaps over 25 percent are set "
                   "aside as likely bad prints). The group is "
                   "those stocks. This exact cut was written down "
                   "today, so this class can only fire on sessions "
                   "from today onward."),
         "can_fire": "Yes, from the price history, from today onward.",
         **blocks["gap_day"]},
        {"id": "pullback_tag", "name": "Deepest past dip, first tag",
         "words": ("A stock reaching the deepest dip of its own "
                   "past. Judging that needs 750 of the stock's "
                   "own past trading days; the longest history on "
                   "record here is 399 days and the long history "
                   "is not on this disk, so this class cannot fire "
                   "yet and no shorter substitute is used."),
         "can_fire": ("Not yet: waiting for the long price "
                      "history to reach this disk."),
         "picture": None, "race": [], "hazard_pct": []},
    ]
    # strip the bulky picture internals from the published classes,
    # keeping the plain fields the page prints
    for c in classes_out:
        pic = c.pop("picture", None)
        if pic:
            c["bucket_words"] = {
                "class": "Built from this class's own past groups.",
                "pooled": ("Built from all classes pooled, pulled "
                           "toward this class's own record, because "
                           "this class's own groups number under "
                           "the 30 needed to stand alone."),
                "pooled_thin": ("Built from all classes pooled, "
                                "and even the pooled count is under "
                                "30, so this picture is thin and "
                                "shows its count."),
            }[pic["bucket"]]
            c["history_cohorts"] = pic["class_cohorts"]
            c["history_cohorts_full60"] = pic["class_cohorts_full60"]
            c["bucket_cohorts"] = pic["bucket_cohorts"]
            c["deciles_sessions"] = pic["deciles"]
            c["unresolved60_pct"] = pct(pic["unresolved60_share"])
            c["median_sessions"] = pic["median_sessions"]
            c["thin"] = pic["thin"]

    data = {
        "tool": "Completion Clock",
        "state": "proving",
        "as_of": freshest,
        "ship_date": SHIP_DATE,
        "source": ("the shipped daily price history (1,833 names, "
                   "March 25, 2025 to October 23, 2026), the "
                   "settled fear-day record, the earnings calendar "
                   "on record, and the morning map card record"),
        "idea": ("Other pages ask what a move pays. This one asks "
                 "how long it takes, and which side gives way "
                 "first. When a defined event gathers a group of "
                 "stocks (a fear day, a deep-reset group, a wall "
                 "break, an earnings day, a big gap day), this "
                 "page writes down, before the race starts, the "
                 "chance the group's middle stock reaches one "
                 "expected move up before one expected move down "
                 "within 5, 10, 21 and 60 trading days, how the "
                 "waiting time spreads out, and the chance the "
                 "race settles on each day from 1 to 21."),
        "shared_family_note": ("This page and the Touch Surface "
                               "page use the same first-passage "
                               "machinery and the same kind of "
                               "evidence (prices). When the two "
                               "agree, that is one confirmation, "
                               "never two."),
        "classes": classes_out,
        "history": {
            "words": ("The pictures above come from replaying "
                      "each class's own entry rule over the price "
                      "history on record. That replay is history, "
                      "computed today; it wrote nothing to the "
                      "public record. The study corpus behind the "
                      "design holds 296,093 graded cases, but its "
                      "per-case rows are not on this disk and its "
                      "own races stopped at 20 sessions, so the "
                      "long end of these pictures rests on the "
                      "shipped history's span alone, and the claim "
                      "is narrowed to match."),
            "fear_days_settled": len(fear_days),
            "fear_cohorts_replayed": len(fear_records),
            "fear_days_set_aside": (
                f"{len(fear_days) - len(fear_records)} of the "
                f"{len(fear_days)} settled fear days produce no "
                "group picture: they fall inside the movement "
                "recipe's first 22 sessions, when no stock has "
                "enough of its own past to measure an expected "
                "move, or their day's group is empty; they are "
                "counted here, not dropped quietly."),
            "deep_reset_days": reset_days,
            "earnings_cohorts": len(earn_records),
            "gap_cohorts": len(gap_records),
            "pooled_cohorts": len(pooled),
            "em_check": em_check,
        },
        "live": {
            "words": live_words,
            "cohorts_recorded": len(live_rows),
            "cohorts_entered_dates": sorted(
                {r["lineage"]["clocks"]["decision_as_of"]
                 for r in live_rows}),
            "matured": matured,
            "counted_toward_30": matured,
            "ledgered_today": ledgered_now,
            "freshest_is_fear_day": fresh_is_fear,
            "freshest_earnings_names": fresh_earn,
        },
        "kill_criterion": ("After 30 matured groups, if this "
                           "page's timing score is no better "
                           "than the plain past rate for the same "
                           "kind of event, it retires. A group "
                           "matures when its race settles or at "
                           "60 trading days; a group still "
                           "unsettled at 60 counts as matured, in "
                           "its own outcome class, never dropped."),
        "thin_cell_rule": ("Any picture built on fewer than 30 "
                           "past groups shows its count and is "
                           "labelled thin. A class with no past "
                           "groups shows no picture at all."),
        "grading_words": ("Every group is written down at entry, "
                          "before its first race day opens. It is "
                          "scored at 5, 10, 21 and 60 trading "
                          "days on how well its timing chances "
                          "matched what happened, against the "
                          "plain past rate for its kind of event. "
                          "Groups still unsettled at 60 stay in "
                          "the count as their own outcome."),
        "self_test": test,
    }
    # Depth cohort timing leg on the DEEP panel (RC-25 cure,
    # 2026-10-30): the pullback study's record carries the fear
    # day deepest fifth cohort's first passage races computed
    # against the landed panel. Absence of the record keeps the
    # page exactly as it was.
    try:
        with open(os.path.join(HERE, "pullback-norm",
                               "study_record.json"),
                  encoding="utf-8") as fh:
            _study = json.load(fh)
        if _study.get("engine_29_depth_leg"):
            data["depth_cohort_timing_deep_panel"] = \
                _study["engine_29_depth_leg"]
    except (OSError, ValueError):
        pass
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH}: pooled history cohorts {len(pooled)} "
          f"(fear {len(fear_records)}, reset {len(reset_records)}, "
          f"earnings {len(earn_records)}, gap {len(gap_records)}), "
          f"live rows {len(live_rows)}, ledgered today "
          f"{len(ledgered_now)}, matured {matured}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
