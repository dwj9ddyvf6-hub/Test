#!/usr/bin/env python3
"""Refresh the Streak Trap (Forecast Engine 21).

=====================================================================
REGISTER TRIPLE (written before any computation)

1. EVIDENCE CLASS, THE TRIGGER RULE AND THE FULL ENUMERATION
   - Evidence class: the young-figure record itself (the corpus's
     C10/C11 pattern: headline shares quoted at face value on a
     handful of matured outcomes, with very wide honest ranges).
     This engine aims that lesson at the publisher: it forecasts
     the future value of this site's own young headline numbers.
   - TRIGGER RULE, fixed: whenever a terminal surface displays a
     hit rate or success share (a proportion with a success count
     over a count of matured outcomes, shown as a share, a percent
     or an x-of-y count) computed on FEWER THAN 30 matured
     outcomes, that figure triggers one forecast at its first
     display. Price changes, cross-sectional shares, scores and
     progress counts are not hit rates and never trigger.
   - THE CURRENT ENUMERATION (16 triggers), every figure recomputed
     from its published data file at issuance and failed closed on
     any disagreement; issuance for every trigger is 2026-10-29,
     this engine's first reading of them, never backdated to the
     figures' first display (they were displayed earlier, before
     this engine existed):
     * Wall Check (wall-check/data.json, published
       2026-10-28T12:52Z): family = wall and flip respect. NO
       long-run base rate exists on record for this family (the
       wall validation record's windows are empty), so the base
       is the neutral 0.50, stamped as neutral wherever used.
       T1 all-index flip respected 6/6; T2 all-index lower wall
       held 6/6 (held counts never-reached as held, per the
       surface's own fields; that definition is frozen below);
       T3 all-index upper wall held 4/6; per index, 2 tests each:
       T4-T6 SPY flip/lower/upper 2/2, 2/2, 2/2; T7-T9 QQQ 2/2,
       2/2, 2/2; T10-T12 IWM 2/2, 2/2, 0/2. The positioning split
       repeats the same 6 tests and is NOT a separate trigger;
       the dampening split has 0 tests and no figure.
     * The Record (record/data.json, generated 2026-10-27T20:50Z):
       family = Board calls, share that rose over 1 session
       (a flat close counts as not rose, the surface's own
       method). Base rate 0.5046, computed at the first reading
       from the grading price source (723,481 name-day pairs over
       1,833 symbols, next close above this close): T13 all Board
       calls rose 14/22; T14 the strongest, fully-checked calls
       rose 8/12. The 5-session and 21-session grades have 0
       graded calls: no figure, no trigger.
     * Replication Wire (replication-wire/data.json, graded
       2026-10-28T12:52Z): family = checked claims holding up.
       Bases from the one complete replication cycle on record
       (grade-a-board/data.json): fully held 63/964 = 0.0654;
       held-or-partly (63+337)/964 = 0.4149. Graded claims are
       the 21 with a held, partly or did-not verdict (not-yet
       claims are not matured outcomes): T15 fully held 3/21;
       T16 held or partly held 10/21.
   - NOT TRIGGERING, named so nothing is silently included or
     dropped: the top-grade share 63/964 and the held-or-partly
     share 400/964 on the Grade-A Board (denominators at least
     30); the Golden Sweep Wire (2 sessions recorded, 0 prints:
     a progress count, no success share displayed); the
     Calibration League's one unstarted entrant figure (a stated
     83.0% from an earlier study, published with no matured count
     behind it: it cannot trigger, and the gap is named, never
     estimated); every other displayed share on the site sits on
     at least 30 matured outcomes or is not a success share.

2. RECONSTRUCTION CHOICES (constants fixed before any figure was
   examined; stdlib only)
   - SHRINKAGE CONSTRUCTION, exact: for a figure p_hat = k/n with
     family base rate b: w is the Wilson score interval width of
     (p_hat, n) at z = 1.96; the effective sample size
     ESS = z^2 * b(1-b) / (w/2)^2; the prior pseudo-count
     M = clamp(round(ESS - n), 1, 60); alpha = k + b*M;
     beta = (n-k) + (1-b)*M. The next-30 success count X follows
     a beta-binomial(30, alpha, beta), computed exactly with
     log-gamma. The future figure is P' = (k+X)/(n+30).
     The staked range is the central 80% of P' (the 10% and 90%
     points of its exact distribution); the staked centre is
     (k + 30*alpha/(alpha+beta)) / (n+30).
   - MOVE LEG, exact: d = |p_hat - b|; the event E is that P'
     reaches at least one third of the way from p_hat toward b
     (p_hat above b: P' <= p_hat - d/3; below: P' >= p_hat + d/3);
     p_move = P(E) from the same distribution, ledgered as
     computed. The design's "at least 0.7" wording holds only
     where the computed p_move reaches 0.7; the page prints the
     computed chance for every figure and never claims 0.7 where
     the computed value is lower. If a future trigger ever has
     d = 0, no move leg is ledgered and the page says so (no
     current trigger has d = 0).
   - ONE ROW PER TRIGGER in the shared record, value {lower,
     upper, stated_coverage: 0.80, p_move, centre}; re-readings
     of a figure already under forecast append nothing: the
     forecast stands until its 30 outcomes mature.
   - FROZEN DEFINITIONS AND VOID: each row's lineage freezes the
     figure's definition text, its source path and that file's
     sha256, plus a signature over the definition text and the
     relevant field structure of the source record. At grading,
     the current signature is recomputed; if it differs, the
     grade is appended as void-by-redefinition, counted in a
     separate void tally, never in the kill denominator, never
     silently dropped. A fresh trigger may then issue under the
     new definition.
   - GRADING SLICING, exact: graded at the first refresh where
     the figure's matured count reaches n+30, through the shared
     record's grade call only. Where item-level records exist
     (Wall Check tests in session order; Replication Wire claims
     in published order), P' uses exactly outcomes n+1 to n+30.
     The two Record figures publish no per-call outcomes (their
     calls are graded in whole session groups), so their P' is
     computed over the whole window that carried the count past
     n+30, with the window size printed on the grade. Other
     surfaces' daily refreshes moving the underlying figures
     after issuance is the forecast working, not an error.
   - Registered worked centres (recomputed exactly on every run
     before anything is written; disagreement fails closed):
     T1/T2 M=19 centre 0.683; T3 M=5 centre 0.604; T4-T12 M=7,
     centres 0.635 (2/2) and 0.365 (0/2); T13 M=6 centre 0.620;
     T14 M=5 centre 0.633; T15 M=1 centre 0.141; T16 M=3
     centre 0.472.

3. RIVAL, KILL CRITERION AND NON-CLAIMS
   - NO-CHANGE RIVAL, exact: the range is the single point p_hat
     (zero width), the centre is p_hat, and its move chance is 0.
   - Kill criterion (from the design, in plain words): over the
     first 10 matured triggers, if the shrinkage forecasts are
     not better than the no-change forecast on BOTH measures
     (average distance from centre to the realised figure, and
     the move-chance score), this page retires and its record
     stays up intact. Range coverage and widths are published
     beside the scores, so a win by width alone would show.
   - Non-claims: this page forecasts the future value of young
     numbers this site itself displays. It says nothing about
     which way any price, index or stock will move, and no
     figure's predicted range is a recommendation of anything.
   - Proving state: the first 10 matured triggers decide it.
     This page's own counts are printed on it, thin rule and all:
     a trigger matures only when its full next 30 outcomes land.
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
import sys
import tempfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # terminal-lineup/
FORECAST = os.path.join(ROOT, "forecast")
sys.path.insert(0, FORECAST)
from ledger import Ledger, file_sha256, frozen_label_identity  # noqa: E402
from registry import Registry                      # noqa: E402

OUT_DIR = os.path.join(HERE, "streak-trap")
LEDGER_PATH = os.path.join(FORECAST, "ledger.jsonl")
WALL_SRC = os.path.join(HERE, "wall-check", "data.json")
RECORD_SRC = os.path.join(HERE, "record", "data.json")
REPL_SRC = os.path.join(HERE, "replication-wire", "data.json")
GRADEA_SRC = os.path.join(HERE, "grade-a-board", "data.json")
BARS_SRC = os.path.expanduser("~/workspace/morgue/data_cache/board_bt_bars.json")
WALLVAL_SRC = os.path.expanduser("~/workspace/morgue/output/wall_validation.json")

ENGINE_ID = "engine_21"
ISSUANCE_DATE = "2026-10-29"        # the engine's first reading
HORIZON_OPEN = "2026-10-29"
HORIZON_CLOSE = "2027-10-29"        # outside date; grading is count-driven
Z = 1.96
M_NEXT = 30
STATED_COVERAGE = 0.80
KILL_TARGET = 10
BOARD_BASE = 0.5046
BOARD_PAIRS = 723481
WALL_BASE = 0.50
REPL_BASE_FULL = 63 / 964
REPL_BASE_PART = 400 / 964

# Registered centres from the register above (4 dp).
REGISTERED = {
    "T1": (19, 0.6833), "T2": (19, 0.6833), "T3": (5, 0.6035),
    "T4": (7, 0.6354), "T5": (7, 0.6354), "T6": (7, 0.6354),
    "T7": (7, 0.6354), "T8": (7, 0.6354), "T9": (7, 0.6354),
    "T10": (7, 0.6354), "T11": (7, 0.6354), "T12": (7, 0.3646),
    "T13": (6, 0.6201), "T14": (5, 0.6326),
    "T15": (1, 0.1408), "T16": (3, 0.4717)}


def fail(msg):
    raise SystemExit(f"streak-trap refresh FAILED CLOSED: {msg}")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------
# The registered shrinkage construction (stdlib only)
# ------------------------------------------------------------------
def wilson_width(p, n):
    z2 = Z * Z
    den = 1.0 + z2 / n
    half = Z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / den
    return 2.0 * half


def _bb_pmf(x, m, a, b):
    return math.exp(
        math.lgamma(m + 1) - math.lgamma(x + 1) - math.lgamma(m - x + 1)
        + math.lgamma(x + a) + math.lgamma(m - x + b)
        - math.lgamma(m + a + b)
        - (math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)))


def shrinkage_forecast(k, n, b):
    """The registered construction. Returns the full forecast dict."""
    p_hat = k / n
    w = wilson_width(p_hat, n)
    ess = Z * Z * b * (1 - b) / (w / 2.0) ** 2
    M = min(60, max(1, round(ess - n)))
    alpha = k + b * M
    beta = (n - k) + (1 - b) * M
    pmf = [_bb_pmf(x, M_NEXT, alpha, beta) for x in range(M_NEXT + 1)]
    cdf, s = [], 0.0
    for v in pmf:
        s += v
        cdf.append(s)
    x_lo = next(x for x in range(M_NEXT + 1) if cdf[x] >= 0.10)
    x_hi = next(x for x in range(M_NEXT + 1) if cdf[x] >= 0.90)
    centre = (k + M_NEXT * alpha / (alpha + beta)) / (n + M_NEXT)
    d = abs(p_hat - b)
    p_move, threshold = None, None
    if d > 0:
        if p_hat > b:
            threshold = p_hat - d / 3.0
            p_move = sum(v for x, v in enumerate(pmf)
                         if (k + x) / (n + M_NEXT) <= threshold)
        else:
            threshold = p_hat + d / 3.0
            p_move = sum(v for x, v in enumerate(pmf)
                         if (k + x) / (n + M_NEXT) >= threshold)
    return {"lower": round((k + x_lo) / (n + M_NEXT), 4),
            "upper": round((k + x_hi) / (n + M_NEXT), 4),
            "stated_coverage": STATED_COVERAGE,
            "p_move": (None if p_move is None else round(p_move, 4)),
            "centre": round(centre, 4),
            "prior_count_M": M, "p_hat": round(p_hat, 4),
            "base_rate": b, "deviation": round(d, 4),
            "move_threshold": (None if threshold is None
                               else round(threshold, 4))}


def move_event(p_hat, b, realised):
    """Did the realised figure move at least 1/3 of the way to b?"""
    d = abs(p_hat - b)
    if d == 0:
        return None
    if p_hat > b:
        return 1.0 if realised <= p_hat - d / 3.0 else 0.0
    return 1.0 if realised >= p_hat + d / 3.0 else 0.0


def grade_from_outcomes(k, n, b, p_hat, value, outcomes):
    """Pure grading over an ordered outcome list (1/0). Returns the
    grade dict, or None while fewer than n+30 outcomes exist."""
    if len(outcomes) < n + M_NEXT:
        return None
    x = sum(outcomes[n:n + M_NEXT])
    realised = (k + x) / (n + M_NEXT)
    return _grade_dict(p_hat, b, value, realised, M_NEXT)


def grade_from_window(k, n, b, p_hat, value, window_successes,
                      window_count):
    """Grading over a whole published window (Record figures)."""
    if window_count < M_NEXT:
        return None
    realised = (k + window_successes) / (n + window_count)
    return _grade_dict(p_hat, b, value, realised, window_count)


def _grade_dict(p_hat, b, value, realised, window):
    e = move_event(p_hat, b, realised)
    scores = {"coverage_hit": 1.0 if value["lower"] <= realised
              <= value["upper"] else 0.0,
              "width": round(value["upper"] - value["lower"], 4),
              "centre_abs_error": round(abs(value["centre"] - realised), 4),
              "rival_centre_abs_error": round(abs(p_hat - realised), 4)}
    if e is not None and value.get("p_move") is not None:
        scores["move_brier"] = round((value["p_move"] - e) ** 2, 4)
        scores["rival_move_brier"] = round(e, 4)   # rival p_move = 0
    return {"rule_id": "coverage", "realised": round(realised, 4),
            "move_event": e, "window_outcomes": window,
            "scores": scores}


# ------------------------------------------------------------------
# Trigger specifications: frozen definitions and source extraction
# ------------------------------------------------------------------
def _sig(definition, structure):
    return hashlib.sha256(
        (definition + "|" + structure).encode()).hexdigest()


TRIGGERS = [
    # Wall Check: totals and per-name, family base neutral 0.50.
    {"id": "T1", "kind": "wall_total", "field": "flip_respected",
     "figure": "Share of graded wall tests where the flip level was respected, all three indexes together",
     "surface": "Wall Check", "family_words": "Wall and flip respect",
     "family": "modelled_inventory", "base": WALL_BASE,
     "base_words": "No long-run record exists for this family yet, so the neutral 50% is used and stamped as neutral",
     "definition": "flip_respected true over tests in wall-check totals; one test is one index map card graded against the session that followed it"},
    {"id": "T2", "kind": "wall_total", "field": "lower_held",
     "figure": "Share of graded wall tests where the lower wall held, all three indexes together",
     "surface": "Wall Check", "family_words": "Wall and flip respect",
     "family": "modelled_inventory", "base": WALL_BASE,
     "base_words": "No long-run record exists for this family yet, so the neutral 50% is used and stamped as neutral",
     "definition": "lower_held true over tests in wall-check totals; held includes a wall that was never reached, per the surface's own fields"},
    {"id": "T3", "kind": "wall_total", "field": "upper_held",
     "figure": "Share of graded wall tests where the upper wall held, all three indexes together",
     "surface": "Wall Check", "family_words": "Wall and flip respect",
     "family": "modelled_inventory", "base": WALL_BASE,
     "base_words": "No long-run record exists for this family yet, so the neutral 50% is used and stamped as neutral",
     "definition": "upper_held true over tests in wall-check totals; held includes a wall that was never reached, per the surface's own fields"},
    {"id": "T13", "kind": "record_all",
     "figure": "Share of all Board calls that rose over the next session",
     "surface": "The Record", "family_words": "Board calls, next-session rise",
     "family": "price", "base": BOARD_BASE,
     "base_words": "50.46%, the share of all stock days in the grading price record (723,481 stock days) whose next close was higher; a flat close counts as not rose",
     "definition": "rose_count over graded_count in the 1-session grades of every Board group on The Record; a flat close counts as not rose"},
    {"id": "T14", "kind": "record_strongest",
     "figure": "Share of the strongest, fully-checked Board calls that rose over the next session",
     "surface": "The Record", "family_words": "Board calls, next-session rise",
     "family": "price", "base": BOARD_BASE,
     "base_words": "50.46%, the share of all stock days in the grading price record (723,481 stock days) whose next close was higher; a flat close counts as not rose",
     "definition": "rose_count over graded_count in the 1-session grades of The Record's strongest (passed every check) Board calls; a flat close counts as not rose"},
    {"id": "T15", "kind": "repl", "mode": "held",
     "figure": "Share of checked claims that fully held up on a second look",
     "surface": "Replication Wire", "family_words": "Checked claims holding up",
     "family": "distributional_volatility", "base": REPL_BASE_FULL,
     "base_words": "6.54%, the fully-held share (63 of 964) in the one complete re-check cycle on record",
     "definition": "claims with verdict held over claims with a held, partly or did-not verdict on the Replication Wire; not-yet claims are not matured outcomes"},
    {"id": "T16", "kind": "repl", "mode": "held_or_partly",
     "figure": "Share of checked claims that held up fully or partly on a second look",
     "surface": "Replication Wire", "family_words": "Checked claims holding up",
     "family": "distributional_volatility", "base": REPL_BASE_PART,
     "base_words": "41.49%, the held-or-partly share (400 of 964) in the one complete re-check cycle on record",
     "definition": "claims with verdict held or partly over claims with a held, partly or did-not verdict on the Replication Wire; not-yet claims are not matured outcomes"},
]
# Per-name wall triggers T4-T12 are generated from the same fields.
for _i, _name in enumerate(("SPY", "QQQ", "IWM")):
    for _j, (_field, _word) in enumerate((
            ("flip_respected", "the flip level was respected"),
            ("lower_held", "the lower wall held"),
            ("upper_held", "the upper wall held"))):
        TRIGGERS.append({
            "id": f"T{4 + 3 * _i + _j}", "kind": "wall_name",
            "name": _name, "field": _field,
            "figure": f"Share of graded {_name} wall tests where {_word}",
            "surface": "Wall Check", "family_words": "Wall and flip respect",
            "family": "modelled_inventory", "base": WALL_BASE,
            "base_words": "No long-run record exists for this family yet, so the neutral 50% is used and stamped as neutral",
            "definition": f"{_field} true over {_name} tests in wall-check by_name; held includes a wall that was never reached, per the surface's own fields"})
TRIGGERS.sort(key=lambda t: int(t["id"][1:]))

EXPECTED_KN = {"T1": (6, 6), "T2": (6, 6), "T3": (4, 6),
               "T4": (2, 2), "T5": (2, 2), "T6": (2, 2),
               "T7": (2, 2), "T8": (2, 2), "T9": (2, 2),
               "T10": (2, 2), "T11": (2, 2), "T12": (0, 2),
               "T13": (14, 22), "T14": (8, 12),
               "T15": (3, 21), "T16": (10, 21)}


def extract_wall(d):
    """Recount every wall figure from item-level tests; fail closed
    on any disagreement with the published totals."""
    tests = []
    for sess in sorted(d["sessions"], key=lambda s: s["session"]):
        tests.extend(sess["tests"])
    out = {}
    tot = d["totals"]
    if tot["tests"] != len(tests):
        fail(f"wall totals tests {tot['tests']} != item tests {len(tests)}")
    for field in ("flip_respected", "lower_held", "upper_held"):
        recount = sum(1 for t in tests if t[field])
        key = {"flip_respected": "flip_respected",
               "lower_held": "lower_held",
               "upper_held": "upper_held"}[field]
        if tot[key] != recount:
            fail(f"wall totals {key} {tot[key]} != recount {recount}")
    for t in TRIGGERS:
        if t["kind"] == "wall_total":
            out[t["id"]] = (tot[t["field"]], tot["tests"])
        elif t["kind"] == "wall_name":
            rows = [x for x in tests if x["name"] == t["name"]]
            pub = next(r for r in d["by_name"] if r["name"] == t["name"])
            if pub["tests"] != len(rows):
                fail(f"wall by_name {t['name']} tests disagree")
            if pub[t["field"]] != sum(1 for x in rows if x[t["field"]]):
                fail(f"wall by_name {t['name']} {t['field']} disagrees")
            out[t["id"]] = (pub[t["field"]], pub["tests"])
    outcomes = {}
    for t in TRIGGERS:
        if t["kind"] == "wall_total":
            outcomes[t["id"]] = [1 if x[t["field"]] else 0 for x in tests]
        elif t["kind"] == "wall_name":
            outcomes[t["id"]] = [1 if x[t["field"]] else 0
                                 for x in tests if x["name"] == t["name"]]
    structure = ",".join(sorted(tot.keys()))
    return out, outcomes, structure


def extract_record(d):
    groups = sorted(d["board"]["groups"], key=lambda g: g["session"])
    k = n = 0
    for g in groups:
        gr = g["grades"]["1d"]
        if gr.get("state") == "graded":
            k += gr["rose_count"]
            n += gr["graded_count"]
    st = d["board"]["strongest"]["horizons"]["1d"]
    out = {"T13": (k, n), "T14": (st["rose_count"], st["graded_count"])}
    if d["totals"]["outcomes_so_far"]["rose_count"] != k or \
            d["totals"]["outcomes_so_far"]["graded_count"] != n:
        fail("record totals disagree with the group recount")
    structure = ",".join(sorted(d["board"].keys())) + "|" + \
        ",".join(sorted(st.keys()))
    return out, structure


def extract_repl(d, gradea):
    counts = d["counts"]
    graded = [c for c in d["claims"]
              if c["verdict"] in ("held", "partly", "did_not")]
    held = sum(1 for c in graded if c["verdict"] == "held")
    partly = sum(1 for c in graded if c["verdict"] == "partly")
    if held != counts["held"] or partly != counts["partly"] or \
            len(graded) != held + partly + counts["did_not"]:
        fail("replication-wire counts disagree with the claims recount")
    gc = gradea["counts"]
    if (gc["grade_a"], gc["confirmed"], gc["tested_denominator"]) != \
            (63, 337, 964):
        fail("grade-a-board base counts moved from the registered "
             "63 / 337 / 964; the base rates must be re-registered")
    out = {"T15": (held, len(graded)),
           "T16": (held + partly, len(graded))}
    outcomes = {
        "T15": [1 if c["verdict"] == "held" else 0 for c in graded],
        "T16": [1 if c["verdict"] in ("held", "partly") else 0
                for c in graded]}
    structure = ",".join(sorted(counts.keys())) + "|" + \
        ",".join(sorted(d["claims"][0].keys()))
    return out, outcomes, structure


def board_base_check():
    """Recompute the Board base rate from the grading price source
    (issuance only; the registered value is frozen afterwards)."""
    raw = load_json(BARS_SRC)
    pairs = rose = 0
    for _sym, rows in raw.items():
        rows = sorted(rows, key=lambda r: r[0])
        for a, b in zip(rows, rows[1:]):
            pairs += 1
            if float(b[4]) > float(a[4]):
                rose += 1
    if pairs != BOARD_PAIRS:
        fail(f"board base pairs {pairs}, registered {BOARD_PAIRS}")
    base = rose / pairs
    if abs(base - BOARD_BASE) > 0.0005:
        fail(f"board base recomputed {base:.4f}, registered {BOARD_BASE}")
    return round(base, 4)


SRC_FOR = {"wall_total": WALL_SRC, "wall_name": WALL_SRC,
           "record_all": RECORD_SRC, "record_strongest": RECORD_SRC,
           "repl": REPL_SRC}
STRUCT_FOR = {}


def trigger_signature(t, structure):
    return _sig(t["definition"], structure)


def issue_triggers(led, reg, figures, structures, sources_meta):
    """Ledger every not-yet-forecast trigger via the machinery API
    only. Returns rows created. Fails closed on any disagreement
    with the registered enumeration at issuance."""
    existing = {r["outcome"]["trigger_id"] for r in led.rows()
                if r.get("type") == "forecast"
                and r.get("engine_id") == ENGINE_ID}
    created = 0
    for t in TRIGGERS:
        if t["id"] in existing:
            continue
        k, n = figures[t["id"]]
        if (k, n) != EXPECTED_KN[t["id"]]:
            fail(f"{t['id']} source figure {k}/{n} disagrees with the "
                 f"registered {EXPECTED_KN[t['id']]} at issuance")
        fc = shrinkage_forecast(k, n, t["base"])
        reg_m, reg_c = REGISTERED[t["id"]]
        if fc["prior_count_M"] != reg_m or abs(fc["centre"] - reg_c) > 0.0015:
            fail(f"{t['id']} recomputed M={fc['prior_count_M']} centre "
                 f"{fc['centre']} disagrees with the registered "
                 f"M={reg_m} centre {reg_c}")
        src = SRC_FOR[t["kind"]]
        lineage = {"clocks": {
            "event_time": sources_meta[t["kind"]],
            "publication_time": sources_meta[t["kind"]],
            "first_available_time": sources_meta[t["kind"]],
            "ingestion_time": ISSUANCE_DATE,
            "decision_as_of": ISSUANCE_DATE},
            "source_artifacts": [
                {"path": src, "sha256": file_sha256(src)}],
            "definition": {
                "text": t["definition"], "source_path": src,
                "signature": trigger_signature(
                    t, structures[t["kind"]])},
            "note": "Issued 2026-10-29, this engine's first reading of "
                    "a figure first displayed earlier; never backdated."}
        value = {"lower": fc["lower"], "upper": fc["upper"],
                 "stated_coverage": fc["stated_coverage"],
                 "p_move": fc["p_move"], "centre": fc["centre"]}
        _, made = led.append_forecast_declared(
            engine_id=ENGINE_ID, issued_ts=ISSUANCE_DATE,
            subject=f"{t['surface']}:{t['id']}",
            quantity="the displayed figure's value after its next "
                     "30 matured outcomes, and the chance it moves "
                     "at least one third of the way to its family's "
                     "long-run base rate",
            value=value, horizon_open=HORIZON_OPEN,
            horizon_close=HORIZON_CLOSE, lineage=lineage,
            families=[t["family"]],
            outcome={"kind": "young_figure", "trigger_id": t["id"],
                     "k": k, "n": n, "p_hat": fc["p_hat"],
                     "base_rate": t["base"]})
        created += 1 if made else 0
    return created


def grade_triggers(led, figures_now, outcomes_now, structures):
    """Grade every matured, ungraded trigger from its source's own
    refreshed record. Returns grades appended (void included)."""
    rows = led.rows()
    graded_ids = {r.get("forecast_row_id") for r in rows
                  if r.get("type") == "grade"}
    by_trigger = {t["id"]: t for t in TRIGGERS}
    appended = 0
    for row in rows:
        if row.get("type") != "forecast" or \
                row.get("engine_id") != ENGINE_ID or \
                row["row_id"] in graded_ids:
            continue
        t = by_trigger[row["outcome"]["trigger_id"]]
        frozen_sig = row["lineage"]["definition"]["signature"]
        if trigger_signature(t, structures[t["kind"]]) != frozen_sig:
            led.append_grade(forecast_row=row, grade={
                "rule_id": "coverage", "void": True,
                "reason": "void-by-redefinition", "realised": None,
                "scores": {}},
                **(frozen_label_identity(row) or {}))
            appended += 1
            continue
        k, n = row["outcome"]["k"], row["outcome"]["n"]
        b, p_hat, value = row["outcome"]["base_rate"], \
            row["outcome"]["p_hat"], row["value"]
        grade = None
        if t["kind"] in ("wall_total", "wall_name", "repl"):
            grade = grade_from_outcomes(
                k, n, b, p_hat, value, outcomes_now[t["id"]])
        else:
            k_now, n_now = figures_now[t["id"]]
            grade = grade_from_window(
                k, n, b, p_hat, value, k_now - k, n_now - n)
        if grade is None:
            continue
        led.append_grade(forecast_row=row, grade=grade,
                         **(frozen_label_identity(row) or {}))
        appended += 1
    return appended


def kill_stats(rows):
    graded = void = 0
    ce = rce = mb = rmb = hits = 0.0
    for r in rows:
        if r.get("type") != "grade" or r.get("engine_id") != ENGINE_ID:
            continue
        g = r["grade"]
        if g.get("void"):
            void += 1
            continue
        s = g.get("scores") or {}
        if "centre_abs_error" not in s:
            continue
        graded += 1
        ce += s["centre_abs_error"]
        rce += s["rival_centre_abs_error"]
        hits += s.get("coverage_hit", 0.0)
        if "move_brier" in s:
            mb += s["move_brier"]
            rmb += s["rival_move_brier"]
    out = {"matured": graded, "void": void}
    if graded:
        out.update({
            "mean_centre_error": round(ce / graded, 4),
            "rival_mean_centre_error": round(rce / graded, 4),
            "mean_move_brier": round(mb / graded, 4),
            "rival_mean_move_brier": round(rmb / graded, 4),
            "coverage_hits": hits})
    return out


# ------------------------------------------------------------------
# Self-test on a throwaway ledger (the live record is never touched)
# ------------------------------------------------------------------
def self_test(reg):
    # construction against the registered worked values
    for tid, (k, n) in EXPECTED_KN.items():
        t = next(x for x in TRIGGERS if x["id"] == tid)
        fc = shrinkage_forecast(k, n, t["base"])
        reg_m, reg_c = REGISTERED[tid]
        if fc["prior_count_M"] != reg_m or \
                abs(fc["centre"] - reg_c) > 0.0015:
            fail(f"self-test construction mismatch on {tid}")
        if not (0.0 <= fc["lower"] <= fc["centre"] <= fc["upper"] <= 1.0):
            fail(f"self-test range ordering broken on {tid}")
    tmp = tempfile.mkdtemp(prefix="streaktrap-test-")
    led = Ledger(os.path.join(tmp, "ledger.jsonl"), registry=reg)
    led.append_genesis("streak trap self-test")
    figures = dict(EXPECTED_KN)
    structures = {"wall_total": "test", "wall_name": "test",
                  "record_all": "test", "record_strongest": "test",
                  "repl": "test"}
    meta = {k: ISSUANCE_DATE for k in structures}
    # issuance mechanics exercised with the real trigger set but a
    # stubbed source check: monkeypatching is avoided by issuing
    # one synthetic row in the same shape instead.
    clocks = {c: ISSUANCE_DATE for c in
              ("event_time", "publication_time", "first_available_time",
               "ingestion_time", "decision_as_of")}
    t1 = next(x for x in TRIGGERS if x["id"] == "T1")
    fc = shrinkage_forecast(6, 6, 0.5)
    row, made = led.append_forecast_declared(
        engine_id=ENGINE_ID, issued_ts=ISSUANCE_DATE,
        subject="Wall Check:T1", quantity="synthetic",
        value={"lower": fc["lower"], "upper": fc["upper"],
               "stated_coverage": 0.80, "p_move": fc["p_move"],
               "centre": fc["centre"]},
        horizon_open=HORIZON_OPEN, horizon_close=HORIZON_CLOSE,
        lineage={"clocks": clocks, "source_artifacts": [
            {"path": "self-test", "sha256": "0" * 64}],
            "definition": {"text": t1["definition"],
                           "source_path": "self-test",
                           "signature": trigger_signature(t1, "test")}},
        families=["modelled_inventory"],
        outcome={"kind": "young_figure", "trigger_id": "T1",
                 "k": 6, "n": 6, "p_hat": 1.0, "base_rate": 0.5})
    if not made:
        fail("self-test synthetic issue failed")
    outcomes = [1] * 6 + [1] * 15 + [0] * 15     # next 30: 15 of 30
    g = grade_from_outcomes(6, 6, 0.5, 1.0, row["value"], outcomes)
    if g is None or abs(g["realised"] - 21 / 36) > 0.001:
        fail(f"self-test grading wrong: {g}")
    if g["move_event"] != 1.0:
        fail("self-test move event wrong (21/36 is past the 5/6 line)")
    led.append_grade(forecast_row=row, grade=g,
                     **(frozen_label_identity(row) or {}))
    if kill_stats(led.rows())["matured"] != 1:
        fail("self-test kill stats wrong")
    return {"state": "passed",
            "registered_centres_recomputed": len(EXPECTED_KN),
            "synthetic_realised": g["realised"],
            "synthetic_move_event": g["move_event"],
            "live_record_untouched": True}


def main():
    reg = Registry()
    reg.validate_engine(ENGINE_ID)
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)

    wall = load_json(WALL_SRC)
    record = load_json(RECORD_SRC)
    repl = load_json(REPL_SRC)
    gradea = load_json(GRADEA_SRC)

    wall_figs, wall_outcomes, wall_struct = extract_wall(wall)
    rec_figs, rec_struct = extract_record(record)
    repl_figs, repl_outcomes, repl_struct = extract_repl(repl, gradea)
    figures = {}
    figures.update(wall_figs)
    figures.update(rec_figs)
    figures.update(repl_figs)
    outcomes_now = {}
    outcomes_now.update(wall_outcomes)
    outcomes_now.update(repl_outcomes)
    structures = {"wall_total": wall_struct, "wall_name": wall_struct,
                  "record_all": rec_struct, "record_strongest": rec_struct,
                  "repl": repl_struct}
    sources_meta = {"wall_total": wall["published_at_utc"],
                    "wall_name": wall["published_at_utc"],
                    "record_all": record["generated_at_utc"],
                    "record_strongest": record["generated_at_utc"],
                    "repl": repl["grading_run_at"]}

    led = Ledger(LEDGER_PATH, registry=reg)
    rows = led.rows()
    if not led.verify_chain(rows):
        fail("shared record hash chain does not verify")
    already = sum(1 for r in rows if r.get("type") == "forecast"
                  and r.get("engine_id") == ENGINE_ID)

    # Issuance-only source proofs (frozen afterwards, per register).
    if already == 0:
        board_base_check()
        wv = load_json(WALLVAL_SRC)
        if wv.get("windows"):
            fail("wall validation record now carries windows; the "
                 "neutral-base register must be revisited")

    created = issue_triggers(led, reg, figures, structures, sources_meta)
    rows = led.rows()
    appended = grade_triggers(led, figures, outcomes_now, structures)
    rows = led.rows()
    stats = kill_stats(rows)

    test = self_test(reg)

    forecast_rows = {r["outcome"]["trigger_id"]: r for r in rows
                     if r.get("type") == "forecast"
                     and r.get("engine_id") == ENGINE_ID}
    if len(forecast_rows) != len(TRIGGERS):
        fail(f"record holds {len(forecast_rows)} engine_21 forecasts, "
             f"expected {len(TRIGGERS)}")
    graded_by = {}
    for r in rows:
        if r.get("type") == "grade" and r.get("engine_id") == ENGINE_ID:
            graded_by[r["forecast_row_id"]] = r["grade"]

    trig_rows = []
    for t in TRIGGERS:
        row = forecast_rows[t["id"]]
        v, o = row["value"], row["outcome"]
        k_now, n_now = figures[t["id"]]
        g = graded_by.get(row["row_id"])
        trig_rows.append({
            "id": t["id"], "figure_words": t["figure"],
            "surface_words": t["surface"],
            "family_words": t["family_words"],
            "definition_words": t["definition"],
            "k": o["k"], "n": o["n"],
            "value_pct": round(100 * o["p_hat"], 1),
            "base_pct": round(100 * t["base"], 2),
            "base_words": t["base_words"],
            "lower_pct": round(100 * v["lower"], 1),
            "upper_pct": round(100 * v["upper"], 1),
            "centre_pct": round(100 * v["centre"], 1),
            "p_move_pct": (None if v["p_move"] is None
                           else round(100 * v["p_move"], 1)),
            "current_k": k_now, "current_n": n_now,
            "moved_since_issue": (k_now, n_now) != (o["k"], o["n"]),
            "state": ("void" if (g or {}).get("void") else
                      "graded" if g else "open"),
            "realised_pct": (None if not g or g.get("void")
                             else round(100 * g["realised"], 1))})

    data = {
        "tool": "Streak Trap",
        "state": "proving",
        "as_of": ISSUANCE_DATE,
        "idea_words": "A young number looks surer than it is. A rate "
            "built on 6 tests can read 100%, and a rate built on 22 "
            "can read 64%, while the honest range around each is "
            "very wide. This page watches every young success rate "
            "displayed anywhere on this site, meaning any rate built "
            "on fewer than 30 finished outcomes, and stakes a dated "
            "prediction on what each one will read after its next "
            "30 outcomes land. Young numbers usually drift back "
            "toward the long-run rate for their kind; each "
            "prediction below is built by pulling the young number "
            "part of the way toward that long-run rate, by an amount "
            "fixed in advance from how wide the young number's own "
            "honest range is, never adjusted figure by figure.",
        "issuance_words": "Every figure below was already on display "
            "before this page existed. Their predictions are dated "
            "October 29, 2026, the day this page first read them, "
            "and are written in the same public record as every "
            "other forecast on this site. Nothing is backdated to "
            "when a figure was first displayed, and a figure already "
            "under prediction is never re-staked: its prediction "
            "stands until its next 30 outcomes land.",
        "how_words": "For each figure: take its long-run family "
            "rate, measure how wide the honest range around the "
            "young figure is, and let that width decide how much "
            "weight the long-run rate gets. A very young figure "
            "gets pulled a long way; an older one barely moves. The "
            "range staked is the middle 80% of where that arithmetic "
            "puts the figure after 30 more outcomes, and the chance "
            "printed beside it is the chance the figure moves at "
            "least one third of the way back toward its long-run "
            "rate. Where no long-run record exists yet for a family, "
            "the neutral 50% is used and stamped as neutral.",
        "triggers": trig_rows,
        "not_triggering": [
            {"figure_words": "Share of recipes earning the top grade, and share holding up fully or partly, on the Grade-A Board",
             "count_words": "63 of 964 and 400 of 964: at least 30 finished outcomes behind each, so no prediction is triggered. These two shares are used here only as the long-run rates for the Replication Wire figures."},
            {"figure_words": "Golden Sweep Wire session count",
             "count_words": "2 sessions recorded and 0 qualifying prints: a progress count, not a success rate, so it never triggers."},
            {"figure_words": "One forecaster's starting accuracy figure in the Calibration League",
             "count_words": "A stated 83.0% carried from an earlier study, published with no count of finished outcomes behind it, so it cannot trigger. The gap is named here, never filled in with an estimate."},
            {"figure_words": "Every other success rate on this site",
             "count_words": "Each sits on at least 30 finished outcomes, or is not a success rate at all."}],
        "live_record": {
            "triggers_staked": len(forecast_rows),
            "matured": stats["matured"], "void": stats["void"],
            "target": KILL_TARGET,
            "stats": stats,
            "words": ("%d young figures are staked. "
                      % len(forecast_rows))
                     + ("None has matured yet: a figure matures only "
                        "when its full next 30 outcomes have landed, "
                        "and the first 10 to mature decide whether "
                        "this page stands or retires."
                        if not stats["matured"] else
                        "%d figure(s) have matured so far; the first "
                        "10 to mature decide whether this page stands "
                        "or retires." % stats["matured"])},
        "kill_words": "Over the first 10 figures to mature, this "
            "page's pulled-toward-normal predictions must beat a "
            "simple no-change prediction, one that says each figure "
            "simply stays where it is, on both measures: how close "
            "the middle of the prediction lands to the real figure, "
            "and how well the move-toward-normal chance scores. "
            "Failing either measure retires this page, and its "
            "record stays up intact.",
        "void_words": "Each figure's exact meaning is frozen on "
            "the day its prediction is staked. If a figure's "
            "meaning later changes, its prediction is marked void "
            "by that change of meaning, counted separately on this "
            "page, never in the retirement count and never quietly "
            "dropped, and a fresh prediction may be staked under "
            "the new meaning.",
        "thin_cell_words": "The thin rule, on this page above all: "
            "nothing here is graded on a partial count. A figure "
            "with some of its next 30 outcomes in is still open, "
            "and its count is printed as open.",
        "proving_state": "Still being proven",
        "source": "the published records of the Wall Check, The "
                  "Record and the Replication Wire pages, the "
                  "Grade-A Board's completed re-check cycle, and "
                  "the shared public forecast record",
        "self_test": test,
        "issued_this_run": created,
        "grades_appended_this_run": appended,
    }
    out_path = os.path.join(OUT_DIR, "data.json")
    tmp_path = out_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp_path, out_path)
    print(f"streak-trap: triggers {len(trig_rows)}, issued this run "
          f"{created}, grades appended {appended}, matured "
          f"{stats['matured']}, void {stats['void']}, data -> {out_path}")


if __name__ == "__main__":
    main()
