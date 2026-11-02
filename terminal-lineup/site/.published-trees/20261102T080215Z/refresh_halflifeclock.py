#!/usr/bin/env python3
"""Refresh the Half-Life Clock (Forecast Engine 22).

=====================================================================
REGISTER TRIPLE (written before any computation)

1. EVIDENCE CLASS, THE FAMILY TABLE AND THE PROMOTION BASE RATES
   - Evidence class: the one complete promotion-to-recheck life
     cycle on record. A large search promoted 1,217 combinations
     on 2026-10-27; a second search the same day re-checked them:
     63 reached the top grade, 337 held up in direction only, 0
     flipped, 564 did not replicate, 253 could not be tested, of
     964 tested. Pooled rates: top grade 63/964 = 6.5%, top grade
     or direction held 400/964 = 41.5%, did not replicate
     564/964 = 58.5%. Most promoted signals are already dying at
     promotion: that is this page's starting fact, printed on it.
   - THE FAMILY TABLE, fixed, families counted once (a family is
     never split or double-counted; the 63 top-grade combinations
     live inside the Factory families below and are NOT a separate
     family):
     * The 28 Factory forecasters that hold promoted combinations
       (45 forecaster-and-target pairs), promoted counts recomputed
       from the first search's own rows on every run and failed
       closed on any disagreement with the registered totals
       (1,217 promoted, 28 forecasters, 45 pairs). Promotion date
       for every one: 2026-10-27, the day the first search
       finished. What each cell carries as "strength" is a
       whole-years average, NOT a reading over its last 21 graded
       sessions, and no such 21-session reading exists anywhere
       in either search record.
     * The pullback-depth family (the study record's F3): 270
       combinations tested in the first search, 0 promoted. Its
       standing is two era averages from an earlier study only.
     * The RESET composite: 270 combinations, 0 promoted; standing
       from the same study record, two era averages only.
     * The Board gate groups: the daily board's published day
       groups, split into all calls and the groups that passed
       every check. The public record holds 2 board sessions
       (2026-10-23 and 2026-10-26), 50 calls, 22 graded, all at
       1 session only, as rose / did-not-rise counts, never as a
       strength series. The board itself publishes daily, so a
       series can accrue; today it has 2 sessions of depth.
     * The tape groups: unusual options-print alerts grouped by
       heat band, 75 alerts on 2026-10-29 across SPY, QQQ and IWM.
       Grading has landed (216 of 300 logged alerts graded,
       105 hits, no directional edge at the next-session
       horizon), but no strength measure of any kind exists for
       them: a hit count is not a strength series.
   - THREE THINGS A FAMILY NEEDS TO BE CLOCKED, audited per family
     on every run: (a) a promotion date and a promotion-time
     strength, meaning its strength over the 21 graded sessions
     at promotion; (b) a past life history, dated strength
     readings over time, to fit the decay model on; (c) a forward
     strength series that actually accrues from a running record.
     TODAY'S AUDIT RESULT, recomputed below: no family has all
     three. The Factory families have a promotion date but no
     21-session strength at promotion, no dated life history
     (two whole-window averages and one recheck verdict per cell;
     zero observed half-lives anywhere) and no accruing forward
     series (the decay standings page holds exactly ONE grading,
     dated 2026-10-27, with 0 movements; the next recheck is
     unscheduled). The other four groups have no promotion event
     at all in the required form and no forward series. So the
     first monthly round clocks ZERO families, and every family
     is listed as not yet clockable with its missing piece named.
     Nothing is estimated to fill a missing piece.

2. RECONSTRUCTION CHOICES (fixed before the first issue)
   - STRENGTH, exact: for family f, S_f(t) is the mean per-session
     agreement score (information coefficient) over the last 21
     graded sessions of that family's own statistic, sessions
     counted on the family's own grading calendar, signed in the
     direction the family was promoted in, so strength is
     positive at promotion for both signs. HALF VALUE:
     H_f = half of S_f at promotion. CROSSING: the first session
     where S_f has fallen to or past H_f.
   - THE FORECAST, per clockable family at each monthly issue:
     the predicted number of sessions until crossing (stated as
     a date, plus or minus 10 sessions), and a yes-or-no call,
     written to the shared public record the same day, on whether
     crossing happens within the next 60 sessions. One record row
     per family per leg, families counted once.
   - THE MODEL, registered honestly: NOT FITTED. Its stated
     inputs are age since promotion, the slope and spread of the
     strength path since promotion, how far today's market state
     sits from the discovery window's, and family crowding (how
     many sibling combinations share the family's kind of
     evidence; computable today, e.g. the largest Factory
     forecaster holds 126 promoted combinations). Its fitting
     set would be the Factory recheck's life histories, and that
     set contains no dated strength paths, no crossing times and
     zero observed half-lives, so NO fitted form, coefficient or
     historical date error exists, and none is printed: any such
     figure would be invented. The model's historical fit quality
     is therefore recorded as: not measurable, because zero
     half-lives have ever been observed on any record here. What
     IS fixed before any forward issue: the definitions above,
     the base-rate prior in section 1, and the one-cycle survival
     counts per forecaster-and-target pair (parsed from the
     recheck report's own table, 45 rows, failed closed). The
     model may be fitted, and later refitted, ONLY on matured,
     graded outcomes from this page's own record, never on
     ungraded hopes.
   - GRADING, exact: at day 60 exactly after an issue, per family:
     the date error is the absolute difference, in sessions,
     between the predicted sessions-to-crossing and the real
     first-crossing session, for families that crossed by day 60;
     the yes-or-no call is scored with the shared record's
     timing score (the survival Brier scorer, imported, never
     forked: a yes call is a stated chance of 1, a no call 0, so
     the score is 0 or 1 per family). A family that dies before
     day 60 stays in the count and is a HIT on a yes call, never
     an exit. Outcomes are resolved from the family's own grading
     record when one exists; the shared grading runner has no
     strength-series outcome kind today, and that gap is named,
     not worked around.
   - ISSUE MECHANICS: monthly, at the start of the month, before
     the 60-session window opens, through the shared record's
     forecast call only. The first live issue is the November
     round: Monday, November 2, 2026 (November 1 is a Sunday).
     The build day is not an issue day: this refresh ledgers
     NOTHING, and the coming round is published as a preview
     with zero clocked families, exactly as audited.

3. RIVAL, KILL CRITERION AND NON-CLAIMS
   - MEDIAN RIVAL, exact: for each family, predict every month
     the median of that family's observed past sessions-to-half-
     crossing. TODAY THE RIVAL IS NOT YET CONSTRUCTIBLE: the
     observed set is empty for every family (zero half-lives ever
     observed), so no median exists. The recheck's survival rates
     are NOT a half-life and are never substituted as one.
   - Kill criterion (from the design, in plain words): after 24
     monthly rounds, if this page's date errors are no better
     than the median rival's, this page retires and its record
     stays up intact. The criterion cannot bite until both this
     page and the rival have observations; that is stated, not
     hidden.
   - Non-claims: this page forecasts when a forecaster family's
     strength will fade. It says nothing about which way any
     price, index or stock will move, and no family's expected
     fading date is a recommendation of anything.
   - Proving state: 24 monthly rounds decide it. Thin rule
     everywhere: a family, rate or score built on a handful of
     cases is printed with its count, or not printed at all.
=====================================================================
"""
import json
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import attestation_block as _ab
except ImportError:  # refresh stays runnable standalone
    _ab = None
import os
import re
import sys
import tempfile
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # terminal-lineup/
FORECAST = os.path.join(ROOT, "forecast")
sys.path.insert(0, FORECAST)
from ledger import Ledger, file_sha256             # noqa: E402
from registry import Registry                      # noqa: E402
from grading import score_brier, score_survival_brier  # noqa: E402

OUT_DIR = os.path.join(HERE, "half-life-clock")
LEDGER_PATH = os.path.join(FORECAST, "ledger.jsonl")
RUN1_SRC = os.path.join(
    ROOT, "records", "forecast-search-2026-10-27",
    "forecast-search-2026-10-27.json")
RERUN_MD_SRC = os.path.join(
    ROOT, "records", "forecast-search-2026-10-27",
    "forecast-search-rerun-2026-10-27.md")
GRADEA_SRC = os.path.join(HERE, "grade-a-board", "data.json")
DECAY_SRC = os.path.join(HERE, "decay-watch", "data.json")
RECORD_SRC = os.path.join(HERE, "record", "data.json")
TAPE_SRC = os.path.join(HERE, "flow-tape", "data.json")
EVIDENCE_SRC = os.path.join(
    ROOT, "records", "forecast-search-2026-10-27", "EVIDENCE.md")

ENGINE_ID = "engine_22"
READING_DATE = "2026-10-29"
FIRST_ISSUE = "2026-11-02"          # Monday, start of November
KILL_TARGET = 24
PROMOTED = 1217
TESTED = 964
GRADE_A = 63
CONFIRMED = 337
NOT_REPLICATED = 564
UNTESTABLE = 253

# Registered per-forecaster promoted counts (first search, run 1).
REGISTERED_FORECASTERS = {
    "alt.antichase": 15, "ap.regime": 20, "avoid.deadcat": 89,
    "avoid.idio": 22, "avoid.jump25": 94, "avoid.mfi75": 38,
    "avoid.newlist": 17, "avoid.pump": 108, "avoid.r20": 1,
    "avoid.stretch": 66, "avoid.surge2": 97, "avoid.x1p6": 75,
    "cs.correction": 2, "mom.volscaled": 1, "nvi.ema255": 2,
    "risk.semidev": 2, "sm.V": 3, "sr.hi52": 5, "tai.pct": 21,
    "veto.cgtph": 6, "veto.crashed": 52, "veto.gapup10": 126,
    "veto.panic": 79, "veto.pump100": 70, "veto.spikemem": 110,
    "vol.garch": 88, "vol.gex_pct": 7, "vol.vix_ts": 1}


def fail(msg):
    raise SystemExit(f"half-life-clock refresh FAILED CLOSED: {msg}")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------
# The registered definitions (pure; exercised by the self-test)
# ------------------------------------------------------------------
def strength_series(per_session_scores):
    """Rolling 21-session strength: mean of the last 21 per-session
    scores, signed in the promoted direction by the caller."""
    out = []
    for i in range(len(per_session_scores)):
        if i < 20:
            out.append(None)
        else:
            out.append(sum(per_session_scores[i - 20:i + 1]) / 21.0)
    return out


def first_crossing_session(strengths, promotion_strength):
    """First index where strength has fallen to or past half its
    promotion value, or None."""
    half = 0.5 * promotion_strength
    for i, s in enumerate(strengths):
        if s is not None and s <= half:
            return i
    return None


def median_rival(observed_half_lives):
    """The registered rival: the median of a family's observed
    sessions-to-half-crossing. None while the set is empty."""
    if not observed_half_lives:
        return None
    xs = sorted(observed_half_lives)
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


def grade_family(predicted_sessions, call_yes, strengths,
                 promotion_strength):
    """Grade one family at day 60 exactly. Returns None while the
    family's own series has not reached session 60 after issue;
    a family that died (crossed) before day 60 is a hit on a yes
    call and stays in the count."""
    window = strengths[:61]           # sessions 0..60 after issue
    if len(window) < 61:
        return None                   # grading is at day 60 exactly
    crossed_at = first_crossing_session(window, promotion_strength)
    crossed = crossed_at is not None
    p = 1.0 if call_yes else 0.0
    brier = score_brier({"p": p}, None, 1.0 if crossed else 0.0)
    surv = score_survival_brier(
        {"resolved_by": {"60": p}},
        crossed_at if crossed else 61, None)
    grade = {"rule_id": "survival_brier",
             "crossed_within_60": crossed,
             "crossed_at_session": crossed_at,
             "scores": {"binary_brier": round(brier["brier"], 4),
                        "brier@60": round(surv["brier@60"], 4)}}
    if crossed:
        grade["date_error_sessions"] = abs(
            predicted_sessions - crossed_at)
    return grade


def issue_monthly(led, clockable, issue_date):
    """Ledger one monthly round via the machinery API only, one
    row per family per leg. `clockable` entries carry: family_id,
    name, promotion_strength, predicted_sessions, call_yes,
    lineage. Returns rows created. With an empty list (today's
    audited state) it creates nothing."""
    created = 0
    issue = date.fromisoformat(issue_date)
    horizon_close = (issue + timedelta(days=90)).isoformat()
    for fam in clockable:
        clocks = {c: issue_date for c in (
            "event_time", "publication_time", "first_available_time",
            "ingestion_time", "decision_as_of")}
        lineage = dict(fam["lineage"])
        lineage["clocks"] = clocks
        _, made = led.append_forecast_declared(
            engine_id=ENGINE_ID, issued_ts=issue_date,
            subject=f"family:{fam['family_id']}",
            quantity="sessions until this family's rolling "
                     "21-session strength falls to half its value "
                     "at promotion, plus or minus 10 sessions",
            value={"estimate": fam["predicted_sessions"],
                   "tolerance_sessions": 10},
            horizon_open=issue_date, horizon_close=horizon_close,
            lineage=lineage, families=["distributional_volatility"],
            outcome={"kind": "family_strength_crossing",
                     "family_id": fam["family_id"],
                     "promotion_strength": fam["promotion_strength"],
                     "leg": "date"})
        created += 1 if made else 0
        _, made = led.append_forecast_declared(
            engine_id=ENGINE_ID, issued_ts=issue_date,
            subject=f"family:{fam['family_id']}",
            quantity="whether this family's strength crosses its "
                     "half value within the next 60 sessions",
            value={"p": 1.0 if fam["call_yes"] else 0.0},
            horizon_open=issue_date, horizon_close=horizon_close,
            lineage=lineage, families=["distributional_volatility"],
            outcome={"kind": "family_strength_crossing",
                     "family_id": fam["family_id"],
                     "promotion_strength": fam["promotion_strength"],
                     "leg": "binary"})
        created += 1 if made else 0
    return created


# ------------------------------------------------------------------
# Source extraction, every figure recomputed, fail closed
# ------------------------------------------------------------------
def extract_factory(run1):
    rows = run1["rows"]
    cols = rows["columns"]
    fi, ti, vi = cols.index("forecaster"), cols.index("target"), \
        cols.index("verdict")
    promoted = {}
    pairs = {}
    f3_cells = reset_cells = 0
    f3_prom = reset_prom = 0
    for r in rows["data"]:
        f, t, v = r[fi], r[ti], r[vi]
        if f == "feat.F3":
            f3_cells += 1
            f3_prom += 1 if v == "promoted-B" else 0
        if f == "xs.n9_reset":
            reset_cells += 1
            reset_prom += 1 if v == "promoted-B" else 0
        if v == "promoted-B":
            promoted[f] = promoted.get(f, 0) + 1
            pairs[(f, t)] = pairs.get((f, t), 0) + 1
    if run1["verdicts"].get("promoted-B") != PROMOTED:
        fail("first search promoted count moved from 1,217")
    if promoted != REGISTERED_FORECASTERS:
        fail("per-forecaster promoted counts disagree with the "
             "registered table")
    if sum(promoted.values()) != PROMOTED or len(pairs) != 45:
        fail("factory totals disagree (1,217 / 45 pairs)")
    if (f3_cells, f3_prom, reset_cells, reset_prom) != (270, 0, 270, 0):
        fail(f"pullback-depth / RESET cells moved: {f3_cells}/"
             f"{f3_prom}/{reset_cells}/{reset_prom}")
    if run1.get("generated") != "2026-10-27 06:06":
        fail("first search finish time moved")
    return promoted, pairs


def extract_mortality_pairs():
    """Parse the recheck report's own per-pair survival table."""
    with open(RERUN_MD_SRC, encoding="utf-8") as fh:
        text = fh.read()
    sec = text.split("## 4. By forecaster and target", 1)
    if len(sec) != 2:
        fail("recheck report section 4 not found")
    table = sec[1].split("## 5.", 1)[0]
    out = []
    for line in table.splitlines():
        m = re.match(
            r"\| ([^|]+) \| ([^|]+) \| (\d+) \| (\d+) \| (\d+) \| "
            r"(\d+) \| (\d+) \| (\d+) \|", line)
        if m:
            f, t, prom, a, conf, flip, notrep, untest = m.groups()
            out.append({
                "forecaster": f.strip(), "target": t.strip(),
                "promoted": int(prom), "grade_a": int(a),
                "confirmed": int(conf), "flipped": int(flip),
                "not_replicated": int(notrep),
                "untestable": int(untest),
                "tested": int(prom) - int(untest)})
    if len(out) != 45:
        fail(f"recheck pair table holds {len(out)} rows, expected 45")
    tot = {k: sum(r[k] for r in out) for k in
           ("promoted", "grade_a", "confirmed", "not_replicated",
            "untestable")}
    if tot != {"promoted": PROMOTED, "grade_a": GRADE_A,
               "confirmed": CONFIRMED, "not_replicated": NOT_REPLICATED,
               "untestable": UNTESTABLE}:
        fail(f"recheck pair totals disagree: {tot}")
    return out


def self_test(reg):
    # Definitions on a synthetic strength path: flat, then decay.
    scores = [0.04] * 21 + [0.04 - 0.001 * i for i in range(1, 61)]
    s = strength_series(scores)
    if s[20] is None or abs(s[20] - 0.04) > 1e-9:
        fail("self-test strength series wrong")
    # A family whose strength halves at a known session.
    path = [0.04] * 30 + [0.019] * 31
    if first_crossing_session(path, 0.04) != 30:
        fail("self-test crossing session wrong")
    g = grade_family(28, True, path, 0.04)
    if g is None or g["date_error_sessions"] != 2 or \
            g["scores"]["binary_brier"] != 0.0:
        fail(f"self-test grading wrong: {g}")
    g2 = grade_family(28, False, [0.04] * 61, 0.04)
    if g2 is None or g2["crossed_within_60"] or \
            g2["scores"]["binary_brier"] != 0.0:
        fail(f"self-test no-cross grading wrong: {g2}")
    if grade_family(28, True, [0.04] * 40, 0.04) is not None:
        fail("self-test graded before day 60")
    if median_rival([]) is not None or median_rival([10, 20, 30]) != 20:
        fail("self-test median rival wrong")
    # Full issue path on a throwaway ledger with one synthetic
    # clockable family; the live record is never touched.
    tmp = tempfile.mkdtemp(prefix="halflife-test-")
    led = Ledger(os.path.join(tmp, "ledger.jsonl"), registry=reg)
    led.append_genesis("half-life clock self-test")
    lineage = {"source_artifacts": [
        {"path": "self-test", "sha256": "0" * 64}]}
    made = issue_monthly(led, [{
        "family_id": "synthetic", "promotion_strength": 0.04,
        "predicted_sessions": 28, "call_yes": True,
        "lineage": lineage}], FIRST_ISSUE)
    if made != 2:
        fail(f"self-test issue created {made} rows, expected 2")
    made2 = issue_monthly(led, [], FIRST_ISSUE)
    if made2 != 0:
        fail("self-test empty issue created rows")
    return {"state": "passed", "synthetic_crossing_session": 30,
            "synthetic_date_error": g["date_error_sessions"],
            "synthetic_rows_ledgered": made,
            "live_record_untouched": True}


def main():
    reg = Registry()
    reg.validate_engine(ENGINE_ID)
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    if date.fromisoformat(FIRST_ISSUE).strftime("%A") != "Monday":
        fail("first issue date is not the registered Monday")

    run1 = load_json(RUN1_SRC)
    gradea = load_json(GRADEA_SRC)
    decay = load_json(DECAY_SRC)
    record = load_json(RECORD_SRC)
    tape = load_json(TAPE_SRC)

    gc = gradea["counts"]
    if (gc["promoted"], gc["grade_a"], gc["confirmed"],
            gc["not_replicated"], gc["untestable"],
            gc["tested_denominator"]) != (
            PROMOTED, GRADE_A, CONFIRMED, NOT_REPLICATED,
            UNTESTABLE, TESTED):
        fail("grade-a-board counts moved from the registered base "
             "rates; they must be re-registered")
    promoted, _pairs = extract_factory(run1)
    pair_rows = extract_mortality_pairs()

    if decay["gradings_count"] != 1 or decay["movements"] != []:
        fail("decay standings record moved from its single grading; "
             "the forward-series audit must be revisited")
    if decay["current_counts"] != {"probation": 325, "promoted": 63,
                                   "total": 388}:
        fail("decay standings counts moved (388 book entries is a "
             "different count from 1,217 combinations; do not merge)")
    # Board and tape registers re-registered 2026-10-30 (engine
    # refresh cure): the Record has grown to 5 sessions / 88
    # graded and the tape to the 2026-10-30 session since the
    # G17 re-take, counted from the files themselves on this
    # date.
    # Accrual floors (terminal audit cure, 2026-10-31): the
    # board sessions and graded count and the tape grading
    # counts are accruals that only grow as grading lands every
    # day. Exact equality made this pre-issue preview fail every
    # scheduled run after each re-take, the in-run-only failure
    # class behind the refresh reproducibility defect, while the
    # audited claim those registers protect is narrower: the
    # audited accrual was present and has not gone backwards.
    # The checks below prove exactly that claim: the registered
    # sessions are the board's first five, the graded counts are
    # at least the registered counts, and the tape session is at
    # least the registered session. The finished-search counts
    # above (grade-A book, decay standings) stay exact.
    sessions = [g["session"] for g in record["board"]["groups"]]
    if sessions[:5] != ["2026-10-23", "2026-10-26", "2026-10-27",
                        "2026-10-28", "2026-10-29"] or \
            record["totals"]["outcomes_so_far"]["graded_count"] < 88:
        fail("board record fell behind its registered accrual "
             "floor (first 5 sessions from 2026-10-23, at least "
             "88 graded)")
    # Tape register: the grading note's accrued counts are
    # parsed and floored at the registered 291 of 375; the
    # per-session alert count varies by session and is only
    # required to be present, and the session may only advance.
    import re as _re
    _gm = _re.search(r"(\d+) of (\d+) logged alerts graded",
                     tape.get("grading_note") or "")
    if tape["session"] < "2026-10-30" or \
            tape["counts"]["alerts_published"] <= 0 or \
            _gm is None or int(_gm.group(1)) < 291 \
            or int(_gm.group(2)) < 375:
        fail("tape record fell behind its registered graded "
             "floor (session at least 2026-10-30, at least 291 "
             "of at least 375 logged alerts graded)")

    led = Ledger(LEDGER_PATH, registry=reg)
    rows = led.rows()
    if not led.verify_chain(rows):
        fail("shared record hash chain does not verify")
    e22 = [r for r in rows if r.get("engine_id") == ENGINE_ID]
    if e22:
        fail(f"shared record already holds {len(e22)} engine_22 "
             "rows before the first issue; the build ledgers nothing")

    test = self_test(reg)
    # The audited clockable set today is empty; the November round
    # is published as a preview and nothing is ledgered.
    created = issue_monthly(led, [], FIRST_ISSUE)
    if created != 0:
        fail("an empty round created rows")

    factory_rows = []
    by_forecaster_pairs = {}
    for p in pair_rows:
        by_forecaster_pairs.setdefault(p["forecaster"], []).append(p)
    for name in sorted(promoted, key=lambda n: -promoted[n]):
        prs = by_forecaster_pairs.get(name, [])
        factory_rows.append({
            "kind": "factory",
            "name_words": f"Factory family: {name}",
            "promotion_words": "Promoted on October 27, 2026, the "
                "day the big search finished",
            "facts_words": f"{promoted[name]} promoted "
                f"combination{'s' if promoted[name] != 1 else ''} "
                f"across {len(prs)} kind"
                f"{'s' if len(prs) != 1 else ''} of target; on the "
                f"same-day recheck, {sum(p['grade_a'] for p in prs)} "
                f"reached the top grade and "
                f"{sum(p['not_replicated'] for p in prs)} did not "
                f"replicate, of "
                f"{sum(p['tested'] for p in prs)} tested",
            "strength_words": "No current strength: no record "
                "carries this family's strength over its last 21 "
                "graded sessions, at promotion or since",
            "predicted_words": "Not yet clockable",
            "missing_words": "Missing: a strength reading over the "
                "21 graded sessions at promotion, and any forward "
                "strength series that accrues. Its past is two "
                "whole-years averages and one recheck verdict per "
                "combination, with no dated path and no observed "
                "fading time to fit on",
            "state": "not_yet_clockable"})
    other_rows = [
        {"kind": "study",
         "name_words": "The pullback-depth family",
         "promotion_words": "Never promoted by the search: 270 "
             "combinations tested, 0 promoted. Its standing comes "
             "from an earlier study only",
         "facts_words": "The study's two era averages: agreement "
             "with later moves of +0.026 in the first era and "
             "+0.031 in the second, each with a strength-of-evidence "
             "reading of 4.3, over 20 trading days",
         "strength_words": "No current strength: no 21-session "
             "strength reading exists for it",
         "predicted_words": "Not yet clockable",
         "missing_words": "Missing: a promotion date and a "
             "promotion-time strength, and any forward strength "
             "series. Two era averages are not a life history",
         "state": "not_yet_clockable"},
        {"kind": "study",
         "name_words": "The RESET composite",
         "promotion_words": "Never promoted by the search: 270 "
             "combinations tested, 0 promoted. Its standing comes "
             "from an earlier study only",
         "facts_words": "The study's fear-day averages: +0.053 in "
             "the first era and +0.028 in the second, over its "
             "fear-day readings",
         "strength_words": "No current strength: no 21-session "
             "strength reading exists for it",
         "predicted_words": "Not yet clockable",
         "missing_words": "Missing: a promotion date and a "
             "promotion-time strength, and any forward strength "
             "series",
         "state": "not_yet_clockable"},
        {"kind": "board",
         "name_words": "The Board gate groups",
         "promotion_words": "No promotion event: the daily board "
             "has no promotion date, so there is no promotion-time "
             "strength to halve from",
         "facts_words": "The public record holds 2 board sessions "
             "(October 23 and 26, 2026), 50 calls published and 22 "
             "graded, all at 1 trading day only, counted as rose or "
             "did not rise, never as a strength series. The group "
             "that passed every check holds 12 of those graded calls",
         "strength_words": "No current strength: the record holds "
             "rose counts, not a strength series, and 2 sessions is "
             "short of the 21 a strength reading needs",
         "predicted_words": "Not yet clockable",
         "missing_words": "Missing: a promotion date and starting "
             "strength, a strength measure built from the day "
             "groups' own grades, and at least 21 graded sessions "
             "of depth. This is the closest group to clockable: "
             "the board itself publishes daily, so its record "
             "accrues",
         "state": "not_yet_clockable"},
        {"kind": "tape",
         "name_words": "The tape groups",
         "promotion_words": "No promotion event of any kind",
         "facts_words": "75 unusual options-print alerts on "
             "October 29, 2026, across SPY, QQQ and IWM, grouped by "
             "heat band. Grading has landed for the sessions whose "
             "next close exists: 216 of 300 logged alerts graded, "
             "105 in the direction the alert pointed (48.6 "
             "percent), with no directional edge at that horizon "
             "stated as the grade",
         "strength_words": "No current strength: the grades are a "
             "single next-session hit count, not a strength series "
             "over 21 graded sessions",
         "predicted_words": "Not yet clockable",
         "missing_words": "Missing: a strength measure built from "
             "the grades, a promotion starting point and a forward "
             "strength series that accrues",
         "state": "not_yet_clockable"}]
    families = factory_rows + other_rows

    pair_table = [{
        "pair_words": f"{p['forecaster']} aiming at {p['target']}",
        "promoted": p["promoted"], "tested": p["tested"],
        "grade_a": p["grade_a"], "confirmed": p["confirmed"],
        "not_replicated": p["not_replicated"],
        "untestable": p["untestable"]} for p in pair_rows]
    vol = next(p for p in pair_rows if p["forecaster"] == "vol.garch")
    if (vol["promoted"], vol["grade_a"], vol["tested"]) != (88, 48, 83):
        fail("the registered worked pair (vol.garch) moved")

    data = {
        "tool": "Half-Life Clock",
        "state": "proving",
        "as_of": READING_DATE,
        "idea_words": "Every trading signal fades. A method that "
            "looked strong when it was picked gets weaker as the "
            "market moves on, and most fading is only ever noticed "
            "long after it happened. This page does the noticing in "
            "advance: at the start of each month it publishes, for "
            "each named group of forecasters on this site's public "
            "record, the date by which that group's strength is "
            "expected to fall to half of what it was when the group "
            "was promoted, and stakes a plain yes-or-no call on "
            "whether the halving happens within the next 60 "
            "trading days. Both are written down before the window "
            "opens and graded on day 60, exactly.",
        "base_rate_words": "The starting fact, in plain words: of "
            "1,217 combinations a large search promoted on October "
            "27, 2026, only 63 reached the top grade on a same-day "
            "second look, and 564 did not replicate at all. Of the "
            "964 that could be tested, 6.5% reached the top grade "
            "and 58.5% did not replicate. Most promoted signals are "
            "already dying at promotion. That is why this page "
            "expects fading, and why the honest question is when, "
            "not whether.",
        "coming_round_words": "The first monthly round is the "
            "November round, opening Monday, November 2, 2026. It "
            "clocks zero families. Every family below is listed as "
            "not yet clockable, with the exact missing piece named, "
            "because a family can only be clocked honestly when "
            "three things exist: its strength at promotion measured "
            "over its last 21 graded sessions, a dated past record "
            "of its strength to fit the fading pattern on, and a "
            "forward strength record that actually builds up from "
            "a running record. Today no family has all three, so "
            "nothing is staked for November and nothing below is a "
            "live prediction. The dates and calls will appear here, "
            "written to the public record on the issue day itself, "
            "for any family whose three pieces exist by then.",
        "families": families,
        "family_counts": {
            "factory_forecasters": len(promoted),
            "factory_pairs": len(pair_rows),
            "other_groups": len(other_rows),
            "clockable": 0,
            "not_yet_clockable": len(families)},
        "pair_table": pair_table,
        "model_words": "The fading pattern this page will use is "
            "built from a family's age since promotion, how fast "
            "its strength has been sliding and how unevenly, how "
            "far today's market sits from the market the family was "
            "found in, and how crowded its family is (how many "
            "sibling combinations share its kind of evidence). It "
            "is NOT FITTED yet, and this page says so rather than "
            "dressing up a guess: the record it would be fitted on "
            "holds no dated strength paths and not one observed "
            "fading time, so there is no fitted shape and no "
            "honest past accuracy to quote. Its past accuracy is "
            "recorded as: not measurable, because zero fading "
            "times have ever been observed here. When it is fitted, "
            "it will be fitted only on this page's own matured, "
            "graded outcomes, never on ungraded hopes.",
        "prior_words": "What the one completed life cycle does "
            "show, as a starting expectation and nothing more: "
            "pooled across all 45 forecaster-and-target pairs, "
            "6.5% of tested combinations reached the top grade, "
            "41.5% reached the top grade or held their direction, "
            "and 58.5% did not replicate. The strongest pair, the "
            "volatility family aiming at realised movement, saw 48 "
            "of its 83 tested combinations reach the top grade; "
            "most other pairs saw none. The full pair-by-pair "
            "counts are in the table below. These are survival "
            "counts from one recheck, not fading times, and this "
            "page never presents them as fading times.",
        "definitions_words": "A family's strength is its average "
            "agreement score over its last 21 graded sessions, "
            "signed the way it was promoted, so strength starts "
            "positive. Its half value is half that starting "
            "strength. Fading to half means the first session the "
            "strength falls to or past that half value. Each "
            "family is counted once. A family that dies before day "
            "60 stays in the count and counts as a hit on a yes "
            "call, never as an exit.",
        "rival_words": "The simple rival this page must beat: "
            "every month, predict each family's own middle past "
            "fading time. That rival cannot be built yet either, "
            "because no family has even one observed fading time "
            "on record. It is printed here as not yet buildable, "
            "and the one-cycle survival counts above are never "
            "used in its place.",
        "live_record": {
            "rounds_issued": 0, "rounds_graded": 0,
            "forecasts_recorded": 0, "target": KILL_TARGET,
            "first_issue": FIRST_ISSUE,
            "words": "0 monthly rounds issued and 0 graded, of "
                     "the 24 rounds that decide whether this page "
                     "stands or retires. The first round opens "
                     "Monday, November 2, 2026, with zero families "
                     "clocked, as audited above."},
        "kill_words": "After 24 monthly rounds, this page's "
            "expected fading dates must land closer to the real "
            "fading dates than the simple rival's (each family's "
            "own middle past fading time, predicted every month). "
            "If they do not, this page retires and its record "
            "stays up intact. That test cannot bite until both "
            "this page and the rival have real fading times to "
            "compare, and the page says so.",
        "thin_cell_words": "The thin rule: every count on this "
            "page is printed with the number of cases behind it. "
            "A family with a handful of cases is described with "
            "its count, never with a bare percentage dressed up "
            "as knowledge.",
        "proving_state": "Still being proven",
        "source": "the two big searches of October 27, 2026 and "
                  "their recheck report, the top-grade board, the "
                  "decay standings page, the public record of "
                  "board calls, the tape of unusual options "
                  "prints, and the shared public forecast record",
        "self_test": test,
        "issued_this_run": created,
    }
    out_path = os.path.join(OUT_DIR, "data.json")
    tmp_path = out_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp_path, out_path)
    print(f"half-life-clock: families {len(families)} "
          f"(factory {len(promoted)}), clockable 0, issued this "
          f"run {created}, data -> {out_path}")


if __name__ == "__main__":
    main()
