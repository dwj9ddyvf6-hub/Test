#!/usr/bin/env python3
"""Refresh the Promoted-Book Mortality Curve (Forecast Engine 23).

=====================================================================
REGISTER TRIPLE (written before any computation; the model form
below was fixed in the inspect registration BEFORE the backcast
was run, and the backcast is run exactly once under it)

1. EVIDENCE CLASS
   - The one complete promotion-to-recheck life cycle on record.
     A first search (finished 2026-10-27) promoted 1,217
     combinations; a second search the same day re-checked them
     under a rule written down before it ran: 63 reached the top
     grade, 337 held up in direction only, 0 flipped, 564 did not
     replicate, 253 could not be tested. Tested denominator 964.
     Shares of all 1,217: top grade 5.18%, direction held 27.69%,
     did not replicate 46.34%, could not be tested 20.79% (the
     printed prior of about 21 percent). Could-not-be-tested is a
     predicted outcome class with its own share in every count,
     never dropped.
   - The recheck is not independent in calendar time (its later
     years are the first search's held-back days); a top grade
     means replicated on a second pull, universe and split, not
     in new years. The backcast inherits this: one cycle, fitted
     and checked on the same cycle. It is a consistency check of
     a form fixed in advance, not out-of-sample proof, and the
     page says so.

2. RECONSTRUCTION CHOICES (the feature table, the form, the gate)
   - FEATURES, promotion-time only, audited against the first
     search's record for all 1,217 promoted combinations:
     * pass margin: EXISTS for 1,217 of 1,217. Fixed as 0.10
       minus the combination's false-alarm-adjusted score (the
       first search's gate was that score at or under 0.10 over
       11,150 tested combinations).
     * family: EXISTS for 1,217 of 1,217. The combination's
       (forecaster, target) pair; 28 forecasters, 45 pairs. This
       is the search's own grouping, not a kind of evidence.
     * horizon: EXISTS for 1,217 of 1,217, read from the target
       (5, 20 or 60 trading days; the pair already carries it).
     * stretch consistency: EXISTS for 1,217 of 1,217. The share
       of the first search's stretch-after-stretch checks whose
       direction agreed (gate: at least 0.70).
     * capacity margin: DOES NOT EXIST at promotion grain for
       the full group. DROPPED from the form, drop registered
       here, never filled in. The capacity and trading figures
       exist only for the 1,077 stock-direction combinations
       (missing for exactly the 140 movement combinations), and
       even where a capacity level exists no capacity floor is
       recorded, so no margin is computable for any combination.
     * family redundancy: EXISTS as a derived promotion-time
       count for 1,217 of 1,217: the number of promoted
       combinations sharing the combination's pair, computed
       from the promoted list alone (range 1 to 88). Near
       duplicates share one fate (the study record's redundancy
       finding: weak 6-month momentum is 97 percent distance
       from the 250-day high).
     * wider-record support: EXISTS ONLY as a forecaster-level
       lookup, frozen in the table below BEFORE the backcast,
       each row citing a study-record row that predates the
       recheck. A forecaster with no citable top-or-second grade
       row gets 0, a recorded value, not missing data. Forbidden
       source: any post-recheck grade. This is the weakest of
       the surviving features and is used only as a tie-break.
       SUPPORT TABLE (forecaster: value, citation):
         alt.antichase 0 (no citable row)
         ap.regime     1 (study record V1, grade A: movement is
                          forecastable from its own past)
         avoid.deadcat 1 (A7, grade B: dead-cat bounce warning)
         avoid.idio    1 (A15, grade B: company-specific
                          declines do worse)
         avoid.jump25  1 (A2, grade A: loud attention days fade)
         avoid.mfi75   1 (A4, grade B: overbought warnings)
         avoid.newlist 0 (listing-age finding is grade C only)
         avoid.pump    1 (A2, grade A: fresh pumps fade)
         avoid.r20     0 (no citable row)
         avoid.stretch 1 (A3, grade A: stretched names fade)
         avoid.surge2  1 (A9, grade B: trade-count surges)
         avoid.x1p6    1 (A3, grade A: stretched names fade)
         cs.correction 0 (no citable row)
         mom.volscaled 1 (S11, grade B: vol-scaled momentum)
         nvi.ema255    1 (S13, grade B: quiet-day accumulation
                          measure above its yearly average)
         risk.semidev  0 (no citable row)
         sm.V          0 (no citable row)
         sr.hi52       0 (no citable row at this exact form)
         tai.pct       0 (no citable row)
         veto.cgtph    0 (no citable row)
         veto.crashed  1 (A1, grade A: crashed, volatile,
                          illiquid names keep losing)
         veto.gapup10  1 (A12, grade B: gap moves fade)
         veto.panic    0 (panic flush graded X as a buy; no
                          A/B row as a warning)
         veto.pump100  1 (A2, grade A: fresh pumps fade)
         veto.spikemem 0 (spike memory graded X as a buy)
         vol.garch     1 (V1, grade A)
         vol.gex_pct   0 (no citable row naming this measure)
         vol.vix_ts    1 (V3, grade B: volatility-index term
                          shape and bigger moves)
   - LEAKAGE RULE: model inputs come only from the first
     search's rows, the promoted list, and the frozen support
     table above. Second-search fields are outcomes, never
     features.
   - THE MODEL FORM, fixed before the backcast: grouped rates.
     Four outcome classes (top grade, direction held, did not
     replicate, could not be tested; flipped folds into
     not-top-grade for the forward arms; flipped was 0 in this
     cycle). For each (forecaster, target) pair with n promoted
     combinations and class counts, a combination's chance for
     class c is (count_c + 25 * base_share_c) / (n + 25), where
     base shares are the whole group's (63, 337, 564, 253) /
     1,217 and the pull strength 25 is fixed. A group count's
     expected value is the sum of its chances; its 90 percent
     range is that sum plus or minus 1.645 times the square
     root of the sum of chance times (1 - chance) over the
     group (a stated normal approximation to the sum of
     independent different-chance outcomes), clipped to the
     group's size. No widening after the fact.
   - Pass margin, stretch consistency and support do NOT change
     the chances (chances are pair-level by construction). They
     order combinations inside a pair in the event-arm ranking,
     in this fixed order: lower pass margin first, then lower
     stretch consistency, then higher redundancy, then no
     wider support before wider support, then names in
     alphabetical order. The page states this division openly.
   - Forward-arm fallback for unseen groups, fixed: pair unseen
     but forecaster seen -> the forecaster-level pulled rate
     (same pull 25 and base shares); forecaster unseen -> the
     base shares themselves.
   - THE GATE, first and binding: run the form back over the
     same 1,217 combinations (a backcast, labelled as one,
     exactly once under this registration). PASS only if the
     top-grade count range covers the realised 63 AND the
     did-not-replicate range covers the realised 564. If it
     fails, the form is rejected before any forward use: this
     script then writes nothing to the shared record and the
     page ships in the rejected state with the missed ranges
     and realised counts printed. No refit, no second run.
     Also printed, not gate criteria: predicted against
     realised counts for direction-held and could-not-be-tested,
     and the per-pair table.
   - EVENT ARM (active today, quarterly until the next
     recheck): the 63 current top-grade combinations, taken
     from the top-grade board's published record and checked
     combination for combination against the recheck rule's
     own output, ranked by their chance of failing the next
     recheck, where failing means anything except reaching
     the top grade again (a combination that cannot be tested
     at that recheck counts as failed and stays in the count).
     Each combination's chance of failing is 1 minus its top-
     grade chance under the fitted form, using its first-search
     promotion-time row unchanged. Predicted failure count:
     the sum of the 63 chances, with the same 90 percent range.
     Written to the shared record now, before any recheck data
     for the next cycle is touched: one row per combination
     carrying its failure chance, plus one group row carrying
     the predicted failure count and range. Re-issues each
     quarter are identical (same features, same form), so the
     shared record counts them once; that is stated, not
     disguised as new forecasts.
   - FORWARD ARM (armed, event-bound): at any future promotion
     event (a new search publishing a new promoted list; a
     recheck of an existing group is the grading event, not a
     promotion), within 24 hours of that record's timestamp
     and before any recheck data for that group is read, one
     row per promoted combination carrying its chance of
     reaching the top grade at its recheck plus its full
     four-class spread, and one group row with the predicted
     top-grade count and 90 percent range. If 24 hours pass
     unwritten, the arm records a missed window honestly
     rather than backdating. This refresh only arms the arm;
     no promotion event has occurred since the first search.
   - GRADING, at the next recheck, by its own published rule:
     all 63 (event arm) or all promoted (forward arm) in the
     count, could-not-be-tested never dropped. Three scores:
     how closely the predicted failure order matches the
     realised failure order (realised order registered here:
     failed combinations first, weakest first by the recheck's
     held-back strength signed by the original direction;
     combinations that reached the top grade again last), a
     per-combination score on the failure chance against what
     happened, and the group count error. The shared grading
     runner grades this kind through the shared path built
     2026-10-30 (RC-19 cure): forecast.grading resolves
     recheck_replication from the recheck record supplied to
     the grading pass (record_outcomes carrying each
     combination's failed bit) and scores it with the shared
     Brier scorer, imported, never forked. Until a recheck
     record exists, the resolver refuses with the record
     named, so the rows stay ungraded honestly.
   - HORIZON for today's written rows: the quarter window from
     the issue day (the event arm's re-issue cadence); the
     grading event is the next recheck whenever it lands, and
     the outcome rows carry that in words.

3. NON-CLAIMS AND PROVING STATE
   - This page prices the survival of promoted combinations.
     It says nothing about which way any price will move, and
     no combination's survival chance is a recommendation.
   - Thin rule: the 63 are one group from one cycle, 55 of
     them in just three pairs, so the ranking is coarse and
     pair-driven; the page says so.
   - Proving state is in part unmet until a recheck or a
     promotion event grades it: the backcast gate is the only
     verdict available today, and it is a consistency check on
     one cycle, not proof.
   - Kill wording (the registry's grading protocol, in plain
     words): the backcast verdict is published first; if the
     next recheck's three scores show the ranking no better
     than the plain base rates it started from, this page's
     record stays up and its claim is retired.
=====================================================================
"""
import hashlib
import json
import math
import os
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(
    ROOT, "records", "forecast-search-2026-10-27"))

from forecast.ledger import Ledger, file_sha256          # noqa: E402
from forecast.registry import Registry                    # noqa: E402
import replicate                                          # noqa: E402

ENGINE_ID = "engine_23"
RUN1 = os.path.join(ROOT, "records", "forecast-search-2026-10-27",
                    "forecast-search-2026-10-27.json")
RUN2 = os.path.join(ROOT, "records", "forecast-search-2026-10-27",
                    "forecast-search-rerun-2026-10-27.json")
EVID = os.path.join(ROOT, "records", "forecast-search-2026-10-27",
                    "EVIDENCE.md")
BOARD = os.path.join(HERE, "grade-a-board", "data.json")
REGJ = os.path.join(ROOT, "forecast", "registry.json")
LEDGER_PATH = os.path.join(ROOT, "forecast", "ledger.jsonl")
OUT_DIR = os.path.join(HERE, "mortality-curve")
OUT_PATH = os.path.join(OUT_DIR, "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import attestation_block as _ab
except ImportError:  # refresh stays runnable standalone
    _ab = None
ISSUE = "2026-10-29"
PROMOTION_DAY = "2026-10-27"
PULL = 25.0
CLASSES = ("A", "confirmed", "not-replicated", "untestable")
REALISED = {"A": 63, "confirmed": 337, "not-replicated": 564,
            "untestable": 253}
BASE = {c: REALISED[c] / 1217.0 for c in CLASSES}
SUPPORT = {
    "alt.antichase": 0, "ap.regime": 1, "avoid.deadcat": 1,
    "avoid.idio": 1, "avoid.jump25": 1, "avoid.mfi75": 1,
    "avoid.newlist": 0, "avoid.pump": 1, "avoid.r20": 0,
    "avoid.stretch": 1, "avoid.surge2": 1, "avoid.x1p6": 1,
    "cs.correction": 0, "mom.volscaled": 1, "nvi.ema255": 1,
    "risk.semidev": 0, "sm.V": 0, "sr.hi52": 0, "tai.pct": 0,
    "veto.cgtph": 0, "veto.crashed": 1, "veto.gapup10": 1,
    "veto.panic": 0, "veto.pump100": 1, "veto.spikemem": 0,
    "vol.garch": 1, "vol.gex_pct": 0, "vol.vix_ts": 1}
FAMILIES = ["events_calendar", "filings_positioning"]


def fail(msg):
    raise SystemExit("refresh_mortalitycurve: FAIL: " + msg)


def horizon_of(target):
    for suffix, h in (("_60", 60), ("_20", 20), ("_5", 5)):
        if target.endswith(suffix):
            return h
    if target in ("realized_vol_20",):
        return 20
    fail("no horizon readable from target %r" % target)


def count_range(ps):
    mean = sum(ps)
    var = sum(p * (1.0 - p) for p in ps)
    half = 1.645 * math.sqrt(var)
    return mean, max(0.0, mean - half), min(float(len(ps)),
                                            mean + half)


def main():
    for p in (RUN1, RUN2, EVID, BOARD, REGJ, LEDGER_PATH):
        if not os.path.exists(p):
            fail("source missing: %s" % p)
    rep1, rep2 = replicate.load(RUN1), replicate.load(RUN2)
    rows1 = [r for r in replicate.rows_of(rep1)
             if r.get("verdict") == "promoted-B"]
    if len(rows1) != 1217:
        fail("promoted count %d, expected 1217" % len(rows1))
    cmp_ = replicate.compare(rep1, rep2)
    summ = cmp_["summary"]
    got = {c: summ["A" if c == "A" else c] for c in CLASSES}
    got = {"A": summ["A"], "confirmed": summ["confirmed"],
           "not-replicated": summ["not-replicated"],
           "untestable": summ["untestable"]}
    if got != REALISED or summ["flipped"] != 0 or \
            summ["promoted"] != 1217 or summ["denominator"] != 964:
        fail("recheck counts disagree with the register: %r" % summ)
    grade_of = {(c["forecaster"], c["target"], c["cell"]): c["grade"]
                for c in cmp_["cells"]}
    forecasters = sorted({r["forecaster"] for r in rows1})
    if len(forecasters) != 28 or set(forecasters) != set(SUPPORT):
        fail("forecaster set disagrees with the frozen support table")
    # Features, promotion-time only, completeness fail-closed.
    feats = {}
    pair_cells = defaultdict(list)
    for r in rows1:
        key = (r["forecaster"], r["target"], r["cell"])
        if r.get("q") is None or r.get("wf_agree") is None:
            fail("a promoted row lacks pass margin or consistency")
        feats[key] = {
            "margin": 0.10 - float(r["q"]),
            "wf_agree": float(r["wf_agree"]),
            "wf_folds": r.get("wf_folds"),
            "horizon": horizon_of(r["target"]),
            "support": SUPPORT[r["forecaster"]]}
        pair_cells[(r["forecaster"], r["target"])].append(key)
    if len(pair_cells) != 45:
        fail("pair count %d, expected 45" % len(pair_cells))
    for key, f in feats.items():
        f["redundancy"] = len(pair_cells[(key[0], key[1])])
    # Fit the registered form on cycle 1 (grades as target only).
    pair_p = {}
    pair_table = []
    for pair, keys in sorted(pair_cells.items()):
        counts = Counter(grade_of[k] for k in keys)
        n = len(keys)
        ps = {c: (counts.get(c, 0) + PULL * BASE[c]) / (n + PULL)
              for c in CLASSES}
        pair_p[pair] = ps
        pair_table.append({
            "pair_words": "%s, %s" % pair, "promoted": n,
            "grade_a": counts.get("A", 0),
            "confirmed": counts.get("confirmed", 0),
            "not_replicated": counts.get("not-replicated", 0),
            "untestable": counts.get("untestable", 0),
            "top_grade_chance_pct": round(100 * ps["A"], 1)})
    # ---- THE BACKCAST: exactly once under this registration.
    # A rerun of this script carries the first run's verdict and
    # numbers forward from its own published data file instead of
    # running the backcast again.
    backcast = None
    if os.path.exists(OUT_PATH):
        try:
            prev = json.load(open(OUT_PATH))
            if prev.get("backcast", {}).get("ran_once"):
                backcast = prev["backcast"]
        except Exception:
            backcast = None
    if backcast is None:
        pred = {}
        for c in CLASSES:
            mean, lo, hi = count_range(
                [pair_p[(k[0], k[1])][c] for k in feats])
            pred[c] = {"predicted": round(mean, 1),
                       "low": round(lo, 1), "high": round(hi, 1),
                       "realised": REALISED[c],
                       "covers": lo <= REALISED[c] <= hi}
        passed = pred["A"]["covers"] and \
            pred["not-replicated"]["covers"]
        backcast = {"ran_once": True, "passed": passed,
                    "classes": pred}
    gate_passed = backcast["passed"]
    # The 63, from the board's published record cross-checked
    # against the recheck rule's own output.
    board = json.load(open(BOARD))
    if board["counts"]["grade_a"] != 63 or \
            board["counts"]["movement_cells"] != 57 or \
            board["counts"]["warning_cells"] != 6 or \
            sorted(g["count"] for g in board["groups"]) != \
            [1, 1, 2, 2, 2, 7, 48]:
        fail("the board's published record disagrees with the register")
    a_keys = sorted(k for k, g in grade_of.items() if g == "A")
    if len(a_keys) != 63:
        fail("top-grade set has %d, expected 63" % len(a_keys))
    if Counter(k[0] for k in a_keys) != Counter({
            "vol.garch": 48, "tai.pct": 7, "veto.gapup10": 3,
            "avoid.pump": 2, "vol.gex_pct": 2, "avoid.deadcat": 1}):
        fail("top-grade mix disagrees with the board's record")
    # Event arm.
    ranked = []
    for k in a_keys:
        f = feats[k]
        p_fail = 1.0 - pair_p[(k[0], k[1])]["A"]
        ranked.append({"key": k, "p_fail": p_fail, **f})
    ranked.sort(key=lambda x: (
        -x["p_fail"], x["margin"], x["wf_agree"], -x["redundancy"],
        x["support"], x["key"]))
    fmean, flo, fhi = count_range([x["p_fail"] for x in ranked])
    # Ledger, machinery API only, and only if the gate passed.
    reg = Registry(REGJ)
    led = Ledger(LEDGER_PATH, registry=reg)
    if not led.verify_chain():
        fail("shared record chain does not verify")
    created = 0
    if gate_passed:
        lineage = {"source_artifacts": [
            {"path": os.path.relpath(p, ROOT), "sha256": file_sha256(p)}
            for p in (RUN1, RUN2, EVID, BOARD, REGJ)],
            "clocks": {"event_time": PROMOTION_DAY,
                       "publication_time": PROMOTION_DAY,
                       "first_available_time": PROMOTION_DAY,
                       "ingestion_time": ISSUE,
                       "decision_as_of": ISSUE}}
        horizon_close = (date.fromisoformat(ISSUE) +
                         timedelta(days=90)).isoformat()
        for i, x in enumerate(ranked, 1):
            f, t, cell = x["key"]
            _, made = led.append_forecast_declared(
                engine_id=ENGINE_ID, issued_ts=ISSUE,
                subject="cell:%s|%s|%s" % (f, t, cell),
                quantity="chance this top-grade combination fails "
                         "the next recheck (anything except reaching "
                         "the top grade again; cannot-be-tested "
                         "counts as failed)",
                value={"p": round(x["p_fail"], 6), "rank": i,
                       "forecaster": f, "target": t, "cell": cell},
                horizon_open=ISSUE, horizon_close=horizon_close,
                lineage=lineage, families=FAMILIES,
                outcome={"kind": "recheck_replication",
                         "grading_event": "next pre-registered recheck",
                         "leg": "cell_failure"})
            created += 1 if made else 0
        _, made = led.append_forecast_declared(
            engine_id=ENGINE_ID, issued_ts=ISSUE,
            subject="cohort:grade_a_63_next_recheck",
            quantity="how many of the 63 current top-grade "
                     "combinations fail the next recheck",
            value={"estimate": round(fmean, 2),
                   "lower": round(flo, 2), "upper": round(fhi, 2),
                   "stated_coverage": 0.90},
            horizon_open=ISSUE, horizon_close=horizon_close,
            lineage=lineage, families=FAMILIES,
            outcome={"kind": "recheck_replication",
                     "grading_event": "next pre-registered recheck",
                     "leg": "cohort_failure_count"})
        created += 1 if made else 0
    rows_now = led.rows()
    if not led.verify_chain(rows_now):
        fail("shared record chain broke after writing")
    mine = [r for r in rows_now if r.get("engine_id") == ENGINE_ID
            and r.get("type") == "forecast"]
    graded = [r for r in rows_now if r.get("engine_id") == ENGINE_ID
              and r.get("type") == "grade"]
    bc = backcast["classes"]
    data = {
        "tool": "mortality-curve", "as_of": ISSUE,
        "source": "the two search records of October 27, 2026 and "
                  "the top-grade board's published list",
        "idea_words": (
            "A big search promoted 1,217 combinations, and a second "
            "search checked them: only 63 reached the top grade and "
            "564 did not hold up at all. A promotion headline should "
            "never travel alone again. This page attaches a predicted "
            "survival to every promoted claim: how likely each one is "
            "to reach the top grade again at the next check, and how "
            "many of today's 63 top-grade combinations are expected "
            "to fall."),
        "cycle_words": (
            "The one full life cycle on record: 1,217 promoted; 63 "
            "reached the top grade (about 5 of every 100); 337 held "
            "up in direction only; 564 did not replicate; 253 could "
            "not be tested (about 21 of every 100). Combinations "
            "that cannot be tested keep their own share in every "
            "prediction on this page; they are never quietly dropped. "
            "One caution travels with the record: the second search "
            "re-used some of the same years, so a top grade means "
            "held up on a second look, not proven in new years."),
        "feature_words": (
            "Each combination is priced only from what was known on "
            "its promotion day: how comfortably it passed, its "
            "search family and time horizon, how steadily it pointed "
            "one way across stretch after stretch, how many near "
            "duplicates were promoted beside it, and whether its "
            "kind of claim had strong support in the earlier study "
            "record. One planned input was dropped and the drop is "
            "on the record: how much money could trade each "
            "combination exists for only 1,077 of the 1,217 and no "
            "floor was ever recorded, so no room-to-trade margin "
            "could be worked out for any of them, and nothing was "
            "filled in. Chances are set family by family; the "
            "promotion-day details order combinations inside a "
            "family without changing its chances."),
        "backcast": backcast,
        "gate_words": (
            ("The check the method had to pass first: pointed back "
             "at the same 1,217 combinations (a look backwards, "
             "labelled as one), its top-grade range had to contain "
             "the real 63 and its did-not-replicate range had to "
             "contain the real 564. It passed: top grade predicted "
             "%.1f, range %.1f to %.1f, real 63; did not replicate "
             "predicted %.1f, range %.1f to %.1f, real 564. The "
             "method, its pull toward the overall rates and its "
             "range method were all fixed in writing before this "
             "check was run once, and may not be adjusted after "
             "seeing the result. Because the method was built and "
             "checked on the same single cycle, passing is a "
             "consistency check, not proof.")
            if gate_passed else
            ("The check the method had to pass first: pointed back "
             "at the same 1,217 combinations (a look backwards, "
             "labelled as one), its top-grade range had to contain "
             "the real 63 and its did-not-replicate range had to "
             "contain the real 564. It failed: top grade predicted "
             "%.1f, range %.1f to %.1f, real 63; did not replicate "
             "predicted %.1f, range %.1f to %.1f, real 564. The "
             "method is therefore rejected before any forward use: "
             "nothing has been written to the public record, and "
             "this page ships in that rejected state.")) % (
            bc["A"]["predicted"], bc["A"]["low"], bc["A"]["high"],
            bc["not-replicated"]["predicted"],
            bc["not-replicated"]["low"], bc["not-replicated"]["high"]),
        "gate_passed": gate_passed,
        "other_counts": [
            {"label": "Reached the top grade", **bc["A"]},
            {"label": "Held up in direction only", **bc["confirmed"]},
            {"label": "Did not replicate", **bc["not-replicated"]},
            {"label": "Could not be tested", **bc["untestable"]}],
        "event_arm": {
            "active": gate_passed,
            "predicted_failures": round(fmean, 1),
            "low": round(flo, 1), "high": round(fhi, 1),
            "words": (
                "Today's 63 top-grade combinations, ranked by their "
                "chance of failing the next check. Of the 63, %.1f "
                "are expected to fail, with a 90 percent range of "
                "%.1f to %.1f. A combination that cannot be tested "
                "at that check counts as failed and stays in the "
                "count. This list was written to the public record "
                "today, before any data from the next check exists. "
                "It is re-issued every three months until that "
                "check; the re-issues are identical, so the record "
                "counts them once." % (fmean, flo, fhi))
                if gate_passed else
                "No ranked list is published: the method failed its "
                "first check, so no forward list is issued from it.",
            "ranked": [{
                "rank": i, "forecaster": x["key"][0],
                "target": x["key"][1], "cell": x["key"][2],
                "fail_chance_pct": round(100 * x["p_fail"], 1),
                "margin": round(x["margin"], 4),
                "consistency": x["wf_agree"],
                "redundancy": x["redundancy"],
                "support": x["support"],
                "horizon": x["horizon"]}
                for i, x in enumerate(ranked, 1)] if gate_passed
            else []},
        "forward_arm_words": (
            "Armed for the next promotion: whenever a future search "
            "promotes a new group of combinations, each one gets a "
            "written chance of reaching the top grade at its own "
            "check, and the group gets a predicted top-grade count "
            "with a 90 percent range, all written within 24 hours "
            "of the promotion and before any check data for that "
            "group is read. If those 24 hours ever pass unwritten, "
            "the missed window is recorded as missed, never "
            "backdated. No new promotion has happened since "
            "October 27, 2026, so this arm has not fired yet."),
        "pair_table": pair_table,
        "live_record": {
            "forecasts_recorded": len(mine), "graded": len(graded),
            "created_this_run": created,
            "words": (
                "%d forecasts are written in the public record (%d "
                "combination chances and 1 group count), %d graded. "
                "Nothing can be graded until the next check or the "
                "next promotion happens; both are events, not dates, "
                "so this page's proving state is in part unmet until "
                "one of them lands." % (
                    len(mine), max(0, len(mine) - 1), len(graded)))
                if gate_passed else
                "0 forecasts are written in the public record, "
                "because the method was rejected at its first check. "
                "Nothing is graded."},
        "grading_words": (
            "When the next check lands, all 63 stay in the count. "
            "Three scores are published: how closely the predicted "
            "order of failure matches the real order (failed "
            "combinations first, weakest first; combinations that "
            "reach the top grade again last), a score for each "
            "combination's failure chance against what actually "
            "happened, and the error in the predicted failure "
            "count. If those scores show the ranking is no better "
            "than the plain overall rates it started from, this "
            "page's claim is retired and its record stays up."),
        "thin_cell_words": (
            "Thin record, stated plainly: the 63 are one group from "
            "one cycle, and 55 of them sit in just three families, "
            "so the ranking is coarse and family-driven. One life "
            "cycle is one sample."),
        "proving_state": "Proving, in part unmet: the first check "
                         "is passed, and the forward record is "
                         "waiting on an event" if gate_passed else
                         "Rejected at its first check, shown as "
                         "rejected",
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_PATH, "w") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print("refresh_mortalitycurve: gate_passed=%s created=%d "
          "recorded=%d data=%s" % (gate_passed, created, len(mine),
                                   OUT_PATH))


if __name__ == "__main__":
    main()
