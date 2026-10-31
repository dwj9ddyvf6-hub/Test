#!/usr/bin/env python3
"""Refresh the Calibration League (Forecast Engine 20).

=====================================================================
REGISTER TRIPLE (written before any computation)

1. EVIDENCE CLASS, THE ENTRANTS AND THEIR MEASURED BIASES
   - A monthly league over every distributional forecaster that
     publishes to the shared forecast record, plus two vendor
     constructions entered as contestants. It forecasts how far each
     entrant's stated confidence is about to miss what actually
     happens, and it is graded by the same rule it grades others.
   - THE SINGLE ERROR QUANTITY, defined once and used for all: for
     an entrant's next 60 graded forecasts, the signed error
     E = 100 x (share that actually happened - average stated
     share), in points. For a band with a fixed stated share (68,
     80), the stated share is that figure and the realised share is
     the fraction of the 60 landing inside the band. For a
     per-forecast chance, the stated share is the average of the 60
     stated chances and the realised share is the fraction of the
     60 events that occurred. E above zero: the entrant understated
     how often the event happens. E below zero: it overstated.
   - COUNTING UNIT per entrant: Engine 1 = one index 68% band
     outcome (its other bands are not the League unit); Engine 2 =
     one touch-chance cell outcome; Engine 5 = one per-strike
     finish-above chance at a weekly expiry; Engine 6 = one
     bigger-move or biggest-drop chance outcome, all names as it
     publishes them; Engine 12 = one company's 80% earnings-day
     move range at its report; Engine 15 = one stock's low-to-high
     range outcome at 21 trading days; the vendor band = one
     reconstructed index band outcome in the earlier study's form;
     the vendor chance = one priced-volatility finish-above
     statement in the earlier study's form.
   - MEASURED STRUCTURAL BIASES, with their study sources (the
     entrant table below is recomputed from these sources on every
     run and the run fails closed on any disagreement):
     * Engine 1: its own published history, 2,208 graded 68% band
       outcomes, 1,354 inside (61.3% against a stated 68%):
       measured E = -6.7 points. An older study of the same
       corrected construction held about 68% on its own years; the
       two records conflict, they are NOT blended, and the centre
       uses the newest measured record (this engine's own page).
     * Engine 2: its own published history, 12,960 graded study
       cases: average stated 48.8%, realised 48.6%,
       measured E = -0.2 points (pooled across unlike cells, named
       as crude). The old vendor touch formula's 13-to-30 point
       overstatement belongs to the dead model it replaced, not to
       this entrant, and is not shifted into its centre.
     * Engine 5: no graded forecast anywhere (it has issued
       nothing: the chain archive it reads holds 0 snapshots). The
       corpus supplies a registered structural prior: the earlier
       study of its movement-based half measured 82.4% stated
       against 83.0% realised, E = +0.6 points. Per the design
       rule this entrant IS forecastable from its prior.
     * Engine 6: its own published history, 1,698 graded index
       cases: average stated 24.7%, realised 23.6%,
       measured E = -1.1 points.
     * Engine 12: its own published history, 440 graded past
       reports, 353 inside its 80% range (80.2%):
       measured E = +0.2 points.
     * Engine 15: no graded forecast anywhere (it has issued
       nothing: no stock on record reaches the 750 of its own past
       trading days it needs, the longest being 399) and NO
       structural prior in the corpus covers its construction, so
       it is NOT YET FORECASTABLE: listed, with its graded count
       of zero printed, and no interval staked for it.
       RE-REGISTERED 2026-10-30 (cure G17): the DEEP panel landed
       and Engine 15 has begun issuing (first forecasts ledgered
       2026-10-29); it still has no graded forecast and no prior,
       so it remains not yet forecastable on the same grounds.
     * Vendor band contestant (the expected-move band sold as a
       68% band, built from the volatility index divided by
       15.87): the earlier study measured it covering 81.6/80.9%
       at 1 day, 83.2/81.7% at 5 days and 85.0/82.2% at 21 days,
       an average of 82.4% against a stated 68%:
       measured E = +14.4 points.
     * Vendor chance contestant (the priced-volatility
       finish-above chance options tools print): the earlier
       study measured 75.7% stated against 87.6 to 90.3%
       realised, an understatement of 12 to 15 points; the centre
       is FIXED at +13.5 points, the midpoint, the same figure
       Engine 5's own register uses to correct that input.
   - EVIDENCE FAMILIES (agreement discounted by family: several
     same-family entrants agreeing counts once): movement-and-
     spread constructions {Engine 1, Engine 2, Engine 6, vendor
     band}; modelled chain inventory {Engine 5, vendor chance};
     events and calendar {Engine 12}; price alone {Engine 15}.

2. RECONSTRUCTION CHOICES (every constant named before computing)
   - INTERVAL CONSTRUCTION, exact: for each forecastable entrant,
     the implied rate q = (stated + centre) / 100, held between
     1% and 99% (for Engine 5, q is anchored at its prior's
     realised 83.0% instead). The interval is the exact 95% range
     for a share at 60 forecasts around q (the standard score
     interval for a proportion), converted back to error points
     by subtracting the stated rate. The width at 60 is therefore
     entrant-specific, about 16 to 25 points, never a flat number.
     At grading, the realised error uses the actual average stated
     share of the 60, not the pooled figure used at issue.
   - RANKING: forecastable entrants ranked by predicted error
     size (the absolute centre), smallest first. The headline
     ranking is the family-collapsed one: each family contributes
     one entry at the middle of its entrants' predicted error
     sizes, so four same-family entrants count once. The
     per-entrant ranking is published beside it and graded by rank
     agreement against the realised ranking when the 60s mature.
   - ELIGIBILITY: Engines 1, 2, 6 and 12 publish to the shared
     record with its full dated lineage and are eligible.
     Engines 5 and 15 are eligible but unstarted: no lineage
     failure, they have simply issued nothing, and their next-60
     window cannot open until they do. The two vendor contestants
     are NOT eligible as publishers to the shared record (neither
     carries its own dated lineage); they are entered as study
     contestants under the earlier studies' lineage exactly as
     the design directs, graded by reconstruction in the studies'
     form, and listed with that state, never silently dropped and
     never presented as record-eligible.
   - ISSUE MECHANICS: rounds are monthly. A round is written to
     the shared record before the month opens, with the decision
     dated at the last trading day of the month before at the
     latest (the November round: decided at the Friday,
     October 30, 2026 close, for the month opening Monday,
     November 2, 2026). The horizon of a round is each entrant's
     first 60 graded forecasts opening on or after the month's
     first trading day; a round closes per entrant at that
     entrant's 60th grade, which for slow entrants may take
     months, and nothing is graded at the calendar month's close.
     The outside closing date carried on each record is one year
     after the month opens; an entrant whose 60th grade has not
     landed by then is reported still open, never graded on a
     partial count. The build day (Thursday, October 29, 2026) is
     NOT an issue day: this refresh publishes the entrant table
     with the coming November round's intervals marked as not yet
     staked, and writes nothing to the record.
   - GRADING (performed by this script's own grade step, because
     the outcome is defined over other forecasters' grades, which
     no price source carries; exercised end to end in the
     self-test): when an entrant's next 60 graded forecasts exist
     in the shared record, the realised error is computed from
     those grade rows alone (each grade's landed-inside mark or
     yes/no outcome, and each forecast's own stated share), the
     League's grade is appended through the machinery's grade
     call, and the round's hit rate and widths are published.
     The vendor pair's grades come from reconstruction in the
     studies' form; until that reconstruction is run, their
     rounds stay open and are reported open. An entrant-round
     with fewer than 60 graded stays open: the thin rule.
   - THE NO-CHANGE RIVAL, exact form: per entrant per round, the
     rival interval uses the same construction centred on that
     entrant's trailing measured error at the moment the round
     opens, with no prior adjustment and no updating during the
     round. The League differs from the rival only where a
     registered prior moves its centre (Engine 5 and the vendor
     pair) and by carrying its centre from the full evidence base
     named above. Widths of both are published at each round's
     close, so a win by width alone is visible.

3. RIVAL, KILL CRITERION AND NON-CLAIMS
   - Kill criterion (from the design, in plain words): after 12
     monthly rounds, if this league's interval hit rate is no
     better than the no-change rival's hit rate over the same
     entrant-rounds, it retires and its record stays up intact.
   - Non-claims: this page forecasts how honest other forecasters'
     confidence is about to be. It says nothing about which way
     any price will move, and no entrant's place in the ranking is
     a recommendation of anything.
   - Proving state: 12 monthly rounds decide it. Early intervals
     are honestly wide, because 60 forecasts is a small sample and
     several entrants' records are young; the page says so.
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
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # terminal-lineup/
FORECAST = os.path.join(ROOT, "forecast")
sys.path.insert(0, FORECAST)
from ledger import Ledger, file_sha256             # noqa: E402
from registry import Registry                      # noqa: E402
import grading as grading_mod                      # noqa: E402
from ledger import frozen_label_identity as ledger_frozen_identity  # noqa: E402

OUT_DIR = os.path.join(HERE, "calibration-league")
LEDGER_PATH = os.path.join(FORECAST, "ledger.jsonl")
EVIDENCE = os.path.join(ROOT, "records", "forecast-search-2026-10-27",
                        "EVIDENCE.md")
SRC = {
    "engine_01": os.path.join(HERE, "corrected-band", "data.json"),
    "engine_02": os.path.join(HERE, "touch-surface", "data.json"),
    "engine_05": os.path.join(HERE, "honest-pop", "data.json"),
    "engine_06": os.path.join(HERE, "exceedance", "data.json"),
    "engine_12": os.path.join(HERE, "earnings-distribution", "data.json"),
    "engine_15": os.path.join(HERE, "self-analogue", "data.json"),
}

ENGINE_ID = "engine_20"
N_NEXT = 60                 # graded forecasts each interval predicts over
Z = 1.959964                # 95% score interval
KILL_TARGET = 12            # monthly rounds
FIRST_ROUND_MONTH = "2026-11"
FIRST_ISSUE_OPEN = "2026-11-02"     # first trading day of November 2026
FIRST_DECISION_AS_OF = "2026-10-30"  # the Friday close before it
TOL = 0.26                  # points; fail-closed tolerance vs the register


def fail(msg):
    raise SystemExit(f"calibration-league refresh FAILED CLOSED: {msg}")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def wilson(q, n=N_NEXT):
    """95% score interval for a proportion at n, as (low, high)."""
    z2 = Z * Z
    den = 1.0 + z2 / n
    centre = (q + z2 / (2 * n)) / den
    half = Z * math.sqrt(q * (1 - q) / n + z2 / (4 * n * n)) / den
    return centre - half, centre + half


def interval_for(stated_pct, centre_pts, anchor_q=None):
    """Registered interval: returns error-point and rate bounds."""
    if anchor_q is None:
        q = min(max((stated_pct + centre_pts) / 100.0, 0.01), 0.99)
    else:
        q = anchor_q
    lo, hi = wilson(q)
    return {"implied_rate_pct": round(q * 100, 1),
            "rate_low_pct": round(lo * 100, 1),
            "rate_high_pct": round(hi * 100, 1),
            "err_low_pts": round(lo * 100 - stated_pct, 1),
            "err_high_pts": round(hi * 100 - stated_pct, 1),
            "width_pts": round((hi - lo) * 100, 1)}


def spearman(xs, ys):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    mx = sum(rx) / n
    my = sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) *
                    sum((b - my) ** 2 for b in ry))
    return None if den == 0 else num / den


# ------------------------------------------------------------------
# Entrant measurement from the sources themselves (fail closed)
# ------------------------------------------------------------------
def evidence_row(tag):
    with open(EVIDENCE, "r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith(f"| {tag} |"):
                return line
    fail(f"evidence row {tag} not found in {EVIDENCE}")


def measure_entrants():
    """Recompute every entrant's measured error from its own
    published record; fail closed on disagreement with the register."""
    out = {}

    d = load_json(SRC["engine_01"])
    cells = [c for c in d["history"]["cells"] if c["level"] == 68]
    graded = sum(c["graded"] for c in cells)
    hits = sum(c["hits"] for c in cells)
    # Re-registered 2026-10-29 (cure G2): the history is a
    # walk-forward over the price panel, so its counts grow as the
    # panel advances. The register is the build-day floor: the
    # recount must cover at least the registered study and stay
    # internally consistent, never exactly equal it.
    if graded < 2208 or hits < 1354 or hits > graded:
        fail(f"engine 1 history recount {hits}/{graded}, register "
             f"floor 1354/2208")
    realised = 100.0 * hits / graded
    out["engine_01"] = {"graded": graded, "stated_pct": 68.0,
                        "realised_pct": round(realised, 2),
                        "error_pts": round(realised - 68.0, 2),
                        # The page's forecasts_recorded counts
                        # live distinct slots; the count of the
                        # entrant's ledger rows is the page's
                        # ledger_rows_total (superseded duplicate
                        # re-issues are ledger rows too, and the
                        # binding in main() counts ledger rows).
                        # Binding to the slot count broke the
                        # first night duplicate issues voided
                        # (engine refresh cure, 2026-10-30, the
                        # RC-06 follow-on pattern).
                        "live_recorded_src":
                            d["live"].get("ledger_rows_total",
                                           d["live"]["forecasts_recorded"])}

    d = load_json(SRC["engine_02"])
    cells = d["history"]["cells"]
    graded = sum(c["graded"] for c in cells)
    stated = sum(c["mean_forecast_pct"] * c["graded"] for c in cells) / graded
    realised = 100.0 * sum(c["touches"] for c in cells) / graded
    if graded < 12960:
        fail(f"engine 2 history recount {graded}, register floor 12960")
    out["engine_02"] = {"graded": graded, "stated_pct": round(stated, 2),
                        "realised_pct": round(realised, 2),
                        "error_pts": round(realised - stated, 2),
                        "live_recorded_src": d["live"]["forecasts_recorded"]}

    d = load_json(SRC["engine_05"])
    # Re-registered 2026-10-29 (cure G17): engine 5 left its
    # zero-record state when the chain archive began (44 records
    # written, graded at weekly expiry closes). The league's
    # measurement for it remains the AD-58 prior study figures;
    # its live counts are read from its own page and cross-checked
    # against the ledger in main(), never asserted to be zero.
    if d["live"]["records_graded"] > d["live"]["records_written"]:
        fail("engine 5 page grades more records than it wrote; "
             "its measurement must be re-registered before publishing")
    row = evidence_row("AD-58")
    if "82.4" not in row or "83.0" not in row:
        fail("AD-58 row no longer carries the registered prior figures")
    out["engine_05"] = {"graded": 0, "stated_pct": 82.4,
                        "realised_pct": 83.0, "error_pts": 0.6,
                        "prior_based": True, "anchor_q": 0.83,
                        "live_recorded_src": d["live"]["records_written"],
                        "live_graded_src": d["live"]["records_graded"]}

    d = load_json(SRC["engine_06"])
    cells = d["history"]["cells"]
    graded = sum(c["graded"] for c in cells)
    stated = sum(c["mean_forecast_pct"] * c["graded"] for c in cells) / graded
    realised = 100.0 * sum(c["events"] for c in cells) / graded
    if graded < 1698:
        fail(f"engine 6 history recount {graded}, register floor 1698")
    out["engine_06"] = {"graded": graded, "stated_pct": round(stated, 2),
                        "realised_pct": round(realised, 2),
                        "error_pts": round(realised - stated, 2),
                        "live_recorded_src": d["live"]["forecasts_recorded"]}

    d = load_json(SRC["engine_12"])
    pool = d["history"]["pooled"]
    if pool["graded"] < 440 or pool["hits"] < 353 \
            or pool["hits"] > pool["graded"]:
        fail(f"engine 12 history recount {pool['hits']}/{pool['graded']}, "
             "register floor 353/440")
    realised = 100.0 * pool["hits"] / pool["graded"]
    out["engine_12"] = {"graded": pool["graded"], "stated_pct": 80.0,
                        "realised_pct": round(realised, 2),
                        "error_pts": round(realised - 80.0, 2),
                        # The page's live count against the ledger
                        # is its taken distribution rows plus its
                        # not-recorded (abstention) rows, both of
                        # which are ledger forecast rows. Binding
                        # to the taken count alone, or to a whole
                        # companies x 3 figures shape, broke the
                        # moment abstentions began ledgering
                        # (RC-06 follow-on cure, 2026-10-30).
                        "live_recorded_src":
                            d["live"]["distribution_forecasts_recorded"]
                            + d["live"]["not_recorded_rows"]}

    d = load_json(SRC["engine_15"])
    # Re-registered 2026-10-30 (cure G17): engine 15 left its
    # zero-record state when the DEEP panel landed and its first
    # forecasts were ledgered (9 on 2026-10-29, more as its
    # refresh completes). It remains NOT YET FORECASTABLE by this
    # league: it has no graded forecast yet and no structural
    # prior covers its construction, so its measured error stays
    # None. The binding that remains is the one main() enforces:
    # the ledger count must equal the count its own page
    # publishes (which is why this refresh stays failed closed
    # while its page is stale against the ledger).
    out["engine_15"] = {"graded": 0, "stated_pct": 80.0,
                        "realised_pct": None, "error_pts": None,
                        "live_recorded_src":
                            d["live"]["forecasts_recorded"]}

    row = evidence_row("AD-55")
    for token in ("81.6/80.9", "83.2/81.7", "85.0/82.2"):
        if token not in row:
            fail(f"AD-55 row no longer carries the registered figure {token}")
    cov = [81.6, 80.9, 83.2, 81.7, 85.0, 82.2]
    realised = sum(cov) / len(cov)
    out["vendor_band"] = {"graded": None, "stated_pct": 68.0,
                          "realised_pct": round(realised, 2),
                          "error_pts": round(realised - 68.0, 2),
                          "study_form": True}

    row = evidence_row("AD-58")
    for token in ("75.7", "87.6", "90.3"):
        if token not in row:
            fail(f"AD-58 row no longer carries the registered figure {token}")
    trailing = (87.6 + 90.3) / 2.0 - 75.7     # rival centre: +13.25
    out["vendor_pop"] = {"graded": None, "stated_pct": 75.7,
                         "realised_pct": None, "error_pts": 13.5,
                         "rival_centre_pts": round(trailing, 2),
                         "study_form": True}
    return out


# Registered November will-stake intervals (error points), fixed in
# the register above and in the inspect record before computing.
REGISTERED_INTERVALS = {
    "engine_01": (-19.3, 4.6), "engine_02": (-12.4, 12.1),
    "engine_05": (-10.8, 8.0), "engine_06": (-10.0, 11.1),
    "engine_12": (-11.5, 8.3), "vendor_band": (2.9, 22.0),
    "vendor_pop": (3.2, 19.1)}

ENTRANTS = [
    {"id": "engine_01", "name": "Corrected Band Engine",
     "family": "distributional_volatility",
     "family_words": "Movement and spread",
     "claim_words": "Its 68 percent band for SPY and QQQ, at 1, 5 and "
                    "21 trading days, will hold the closing price "
                    "68 times in 100.",
     "eligibility": "eligible",
     "eligibility_words": "In the league: it publishes to the shared "
                          "record with its full dated history."},
    {"id": "engine_02", "name": "Touch Surface",
     "family": "distributional_volatility",
     "family_words": "Movement and spread",
     "claim_words": "Each stated chance is the chance price actually "
                    "reaches a level 0.5, 1 or 1.5 expected moves away "
                    "within 1, 5 or 21 trading days.",
     "eligibility": "eligible",
     "eligibility_words": "In the league: it publishes to the shared "
                          "record with its full dated history."},
    {"id": "engine_05", "name": "Honest POP Engine",
     "family": "modelled_inventory",
     "family_words": "Modelled chain inventory",
     "claim_words": "Each stated chance is the chance the final close "
                    "finishes above a strike at the week's end.",
     "eligibility": "eligible",
     "eligibility_words": "In the league: it publishes to the shared "
                          "record from the stored chain snapshots "
                          "(first records written 2026-10-29) and "
                          "grades at each weekly expiry close."},
    {"id": "engine_06", "name": "Exceedance Forecaster",
     "family": "distributional_volatility",
     "family_words": "Movement and spread",
     "claim_words": "Each stated chance is the chance of a move bigger "
                    "than 1 or 2 expected moves in 5 trading days, or "
                    "a largest fall bigger than 1.5 expected moves "
                    "in 21.",
     "eligibility": "eligible",
     "eligibility_words": "In the league: it publishes to the shared "
                          "record with its full dated history."},
    {"id": "engine_12", "name": "Earnings Move Distribution",
     "family": "events_calendar",
     "family_words": "Events and calendar",
     "claim_words": "Its range for a company's earnings-day move will "
                    "hold 80 of every 100 reports.",
     "eligibility": "eligible",
     "eligibility_words": "In the league: it publishes to the shared "
                          "record with its full dated history."},
    {"id": "engine_15", "name": "Per-Name Self-Analogue",
     "family": "price",
     "family_words": "Price alone",
     "claim_words": "Its low-to-high range for a stock's next 21 "
                    "trading days will hold the real return 80 times "
                    "in 100.",
     "eligibility": "eligible_unstarted",
     "eligibility_words": "In the league, started but not yet "
                          "forecastable: the DEEP panel landed and "
                          "it has begun issuing (first forecasts "
                          "ledgered 2026-10-29), but none of its "
                          "forecasts is graded yet and no earlier "
                          "study supplies a starting figure for its "
                          "method, so no interval is staked for it "
                          "this round."},
    {"id": "vendor_band", "name": "The market's expected-move band",
     "family": "distributional_volatility",
     "family_words": "Movement and spread",
     "claim_words": "The band built from the volatility index divided "
                    "by 15.87, sold and labelled as a 68 percent, "
                    "one-step band.",
     "eligibility": "study_contestant",
     "eligibility_words": "Study contestant: it does not publish to "
                          "the shared record and carries no dated "
                          "record of its own, so it is entered under "
                          "the earlier study that measured it, and "
                          "graded by rebuilding it in that study's "
                          "form. Listed openly, never dropped quietly."},
    {"id": "vendor_pop", "name": "The market's finish-above chance",
     "family": "modelled_inventory",
     "family_words": "Modelled chain inventory",
     "claim_words": "The finish-above chance options tools print from "
                    "priced volatility, with no correction.",
     "eligibility": "study_contestant",
     "eligibility_words": "Study contestant: it does not publish to "
                          "the shared record and carries no dated "
                          "record of its own, so it is entered under "
                          "the earlier study that measured it, and "
                          "graded by rebuilding it in that study's "
                          "form. Listed openly, never dropped quietly."},
]


def build_table(measured, live_counts):
    table = []
    for e in ENTRANTS:
        m = measured[e["id"]]
        row = dict(e)
        row["measured"] = m
        row["live_recorded"] = live_counts.get(e["id"])
        row["live_graded"] = 0
        if m["error_pts"] is None:
            row["forecastable"] = False
            row["interval"] = None
            row["rival_interval"] = None
        else:
            iv = interval_for(m["stated_pct"], m["error_pts"],
                              anchor_q=m.get("anchor_q"))
            reg = REGISTERED_INTERVALS[e["id"]]
            if abs(iv["err_low_pts"] - reg[0]) > TOL or \
                    abs(iv["err_high_pts"] - reg[1]) > TOL:
                fail(f"{e['id']} interval {iv['err_low_pts']}.."
                     f"{iv['err_high_pts']} disagrees with the "
                     f"registered {reg[0]}..{reg[1]}")
            row["forecastable"] = True
            row["interval"] = iv
            rival_centre = m.get("rival_centre_pts", m["error_pts"])
            row["rival_interval"] = interval_for(
                m["stated_pct"], rival_centre,
                anchor_q=None if e["id"] != "engine_05" else None) \
                if not m.get("prior_based") else None
            row["centre_pts"] = m["error_pts"]
        table.append(row)
    ranked = sorted((r for r in table if r["forecastable"]),
                    key=lambda r: abs(r["centre_pts"]))
    for i, r in enumerate(ranked, 1):
        r["rank"] = i
    fams = {}
    for r in ranked:
        fams.setdefault(r["family"], []).append(abs(r["centre_pts"]))
    fam_rows = []
    for fam, vals in fams.items():
        vals = sorted(vals)
        med = vals[len(vals) // 2] if len(vals) % 2 else \
            (vals[len(vals) // 2 - 1] + vals[len(vals) // 2]) / 2.0
        fam_rows.append({"family": fam,
                         "family_words": next(
                             e["family_words"] for e in ENTRANTS
                             if e["family"] == fam),
                         "median_abs_error_pts": round(med, 2),
                         "members": len(vals)})
    fam_rows.sort(key=lambda f: f["median_abs_error_pts"])
    for i, f in enumerate(fam_rows, 1):
        f["rank"] = i
    return table, [r["id"] for r in ranked], fam_rows


# ------------------------------------------------------------------
# Issue and grade steps (machinery API only; exercised in self-test)
# ------------------------------------------------------------------
def first_weekday(year, month):
    d = date(year, month, 1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def last_weekday_before(d):
    d -= timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def round_for_month(month_str):
    y, m = (int(x) for x in month_str.split("-"))
    open_d = first_weekday(y, m)
    return {"month": month_str, "horizon_open": open_d.isoformat(),
            "decision_as_of": last_weekday_before(open_d).isoformat(),
            "horizon_close": (open_d + timedelta(days=365)).isoformat()}


def issue_round(led, reg, table, ranking, fam_rows, rnd, lineage):
    """Append one round's interval forecasts + the ranking claim.
    Returns the number of rows created."""
    created = 0
    issued_ts = datetime.now(timezone.utc).isoformat()
    for row in table:
        if not row["forecastable"]:
            continue
        iv = row["interval"]
        value = {"stated_pct": row["measured"]["stated_pct"],
                 "centre_error_pts": row["centre_pts"],
                 "err_low_pts": iv["err_low_pts"],
                 "err_high_pts": iv["err_high_pts"],
                 "rate_low_pct": iv["rate_low_pct"],
                 "rate_high_pct": iv["rate_high_pct"],
                 "rival_err_low_pts": (None if row["rival_interval"]
                                       is None else
                                       row["rival_interval"]["err_low_pts"]),
                 "rival_err_high_pts": (None if row["rival_interval"]
                                        is None else
                                        row["rival_interval"]["err_high_pts"]),
                 "n_next": N_NEXT}
        _, made = led.append_forecast_declared(
            engine_id=ENGINE_ID, issued_ts=issued_ts,
            subject=f"{rnd['month']}:{row['id']}",
            quantity="signed calibration error over the entrant's "
                     "next 60 graded forecasts, in points",
            value=value, horizon_open=rnd["horizon_open"],
            horizon_close=rnd["horizon_close"], lineage=lineage,
            families=[row["family"]],
            outcome={"kind": "league_interval",
                     "entrant": row["id"], "round": rnd["month"]})
        created += 1 if made else 0
    _, made = led.append_forecast_declared(
        engine_id=ENGINE_ID, issued_ts=issued_ts,
        subject=f"{rnd['month']}:ranking",
        quantity="ranking of entrants by predicted calibration "
                 "error size, smallest first",
        value={"order": ranking,
               "family_order": [f["family"] for f in fam_rows]},
        horizon_open=rnd["horizon_open"],
        horizon_close=rnd["horizon_close"], lineage=lineage,
        families=["distributional_volatility"],
        outcome={"kind": "league_ranking", "round": rnd["month"]})
    created += 1 if made else 0
    return created


def entrant_realised_error(rows, entrant_id, horizon_open):
    """The entrant's first 60 graded forecasts opening on/after the
    round open: returns (realised_error_pts, mean_stated_pct, n) or
    None while fewer than 60 exist (the thin rule: stays open).
    Delegates to the shared machinery (forecast.grading, RC-19
    cure, 2026-10-30) so the league and the shared grading pass
    compute one realised error, never two."""
    return grading_mod.league_entrant_realised_error(
        rows, entrant_id, horizon_open, n_next=N_NEXT)


def grade_rounds(led, rows):
    """Grade every matured League entrant-round from the record.
    Returns (grades_appended, round_stats)."""
    graded_ids = {r.get("forecast_row_id") for r in rows
                  if r.get("type") == "grade"}
    appended = 0
    stats = {}
    league_rows = [r for r in rows if r.get("type") == "forecast"
                   and r.get("engine_id") == ENGINE_ID]
    realised_by_round = {}
    for row in league_rows:
        if row["row_id"] in graded_ids:
            continue
        out = row.get("outcome") or {}
        if out.get("kind") != "league_interval":
            continue
        res = entrant_realised_error(rows, out["entrant"],
                                     row["horizon_open"])
        if res is None:
            continue
        # Shared grade schema (RC-19 cure, 2026-10-30): the
        # realised error comes from the shared machinery's
        # league computation (entrant_realised_error below now
        # delegates to forecast.grading), and the grade carries
        # the shared fields (realised, binary_outcome,
        # price_source) beside the league readings, instead of
        # the divergent schema this loop used before.
        realised_E, mean_stated, n = res
        v = row["value"]
        hit = 1.0 if v["err_low_pts"] <= realised_E <= v["err_high_pts"] \
            else 0.0
        rival_hit = None
        if v.get("rival_err_low_pts") is not None:
            rival_hit = 1.0 if v["rival_err_low_pts"] <= realised_E \
                <= v["rival_err_high_pts"] else 0.0
        led.append_grade(forecast_row=row, grade={
            "rule_id": "coverage", "realised": realised_E,
            "realised_error_pts": realised_E,
            "binary_outcome": hit,
            "mean_stated_pct": mean_stated, "n_graded": n,
            "scores": {"coverage_hit": hit, "interval_hit": hit,
                       "width_pts": v["err_high_pts"] - v["err_low_pts"],
                       "rival_hit": rival_hit},
            "price_source": "ledger grades (league record)"},
            **(ledger_frozen_identity(row) or {}))
        appended += 1
        realised_by_round.setdefault(out["round"], {})[out["entrant"]] = \
            realised_E
        rows = led.rows()
    for row in league_rows:
        if row["row_id"] in graded_ids:
            continue
        out = row.get("outcome") or {}
        if out.get("kind") != "league_ranking":
            continue
        realised = realised_by_round.get(out["round"])
        order = row["value"]["order"]
        if not realised or any(e not in realised for e in order):
            continue
        rho = spearman([abs(realised[e]) for e in order],
                       list(range(len(order))))
        # rank agreement: predicted order vs realised |E| order
        pred_rank = {e: i for i, e in enumerate(order)}
        real_order = sorted(order, key=lambda e: abs(realised[e]))
        real_rank = {e: i for i, e in enumerate(real_order)}
        rho = spearman([pred_rank[e] for e in order],
                       [real_rank[e] for e in order])
        led.append_grade(forecast_row=row, grade={
            "rule_id": "coverage", "realised": real_order,
            "realised_ranking": real_order, "binary_outcome": None,
            "scores": {"rank_agreement": rho},
            "price_source": "ledger grades (league record)"},
            **(ledger_frozen_identity(row) or {}))
        appended += 1
        rows = led.rows()
    for row in rows:
        if row.get("type") != "grade" or row.get("engine_id") != ENGINE_ID:
            continue
        g = row["grade"]
        s = g.get("scores") or {}
        if "interval_hit" in s:
            st = stats.setdefault("intervals", {"graded": 0, "hits": 0.0,
                                                "widths": [],
                                                "rival_hits": 0.0,
                                                "rival_graded": 0})
            st["graded"] += 1
            st["hits"] += s["interval_hit"]
            st["widths"].append(s["width_pts"])
            if s.get("rival_hit") is not None:
                st["rival_graded"] += 1
                st["rival_hits"] += s["rival_hit"]
    return appended, stats


# ------------------------------------------------------------------
# Self-test on a throwaway ledger (the live record is never touched)
# ------------------------------------------------------------------
def self_test(reg):
    tmp = tempfile.mkdtemp(prefix="calibrationleague-test-")
    path = os.path.join(tmp, "ledger.jsonl")
    led = Ledger(path, registry=reg)
    led.append_genesis("calibration league self-test")
    clocks = {c: "2026-10-30" for c in
              ("event_time", "publication_time", "first_available_time",
               "ingestion_time", "decision_as_of")}
    lineage = {"clocks": clocks, "source_artifacts": [
        {"path": "self-test", "sha256": "0" * 64}]}
    # a fake entrant: 60 forecasts, stated 68%, exactly 40 land inside
    for i in range(60):
        row, _ = led.append_forecast_declared(
            engine_id="engine_01", issued_ts="2026-11-02T00:00:00+00:00",
            subject=f"TEST{i}", quantity="band",
            value={"lower": 0.0, "upper": 1.0, "stated_coverage": 68.0},
            horizon_open="2026-11-02", horizon_close="2026-11-03",
            lineage=lineage, families=["distributional_volatility"],
            outcome={"kind": "band", "symbol": "SPY"})
        led.append_grade(
            forecast_row=row, grade={
                "rule_id": "coverage", "realised": 0.5,
                "binary_outcome": None,
                "scores": {"coverage_hit": 1.0 if i < 40 else 0.0}},
            # The forecast froze its label identity at issue
            # (RC-21); the grade must repeat it (RC-19 pass,
            # 2026-10-30: this append predated the freezing
            # cure and the self-test refused to grade).
            **(ledger_frozen_identity(row) or {}))
    rows = led.rows()
    res = entrant_realised_error(rows, "engine_01", "2026-11-02")
    if res is None or abs(res[0] - (100.0 * 40 / 60 - 68.0)) > 0.01:
        fail(f"self-test realised error wrong: {res}")
    fake = [{"id": "engine_01", "forecastable": True,
             "measured": {"stated_pct": 68.0}, "centre_pts": -6.7,
             "family": "distributional_volatility",
             "interval": interval_for(68.0, -6.7),
             "rival_interval": interval_for(68.0, -6.7)}]
    rnd = round_for_month("2026-11")
    created = issue_round(led, reg, fake, ["engine_01"],
                          [{"family": "distributional_volatility"}],
                          rnd, lineage)
    if created != 2:
        fail(f"self-test issue created {created}, expected 2")
    appended, _ = grade_rounds(led, led.rows())
    if appended < 1:
        fail("self-test grading appended nothing")
    return {"state": "passed",
            "synthetic_entrant_forecasts": 60,
            "synthetic_realised_error_pts": res[0],
            "league_rows_created_on_throwaway": created,
            "league_grades_appended_on_throwaway": appended,
            "live_record_untouched": True}


def main():
    reg = Registry()
    reg.validate_engine(ENGINE_ID)
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)

    measured = measure_entrants()

    led = Ledger(LEDGER_PATH, registry=reg)
    rows = led.rows()
    if not led.verify_chain(rows):
        fail("shared record hash chain does not verify")
    live_counts = {}
    live_graded = {}
    for e in ENTRANTS:
        if e["id"].startswith("engine_"):
            live_counts[e["id"]] = sum(
                1 for r in rows if r.get("type") == "forecast"
                and r.get("engine_id") == e["id"])
            live_graded[e["id"]] = sum(
                1 for r in rows if r.get("type") == "grade"
                and r.get("engine_id") == e["id"])
    # Re-registered 2026-10-29 (cure G17): the exact-count register
    # and the zero live-graded assertion were build-day facts, not
    # laws. Engines issue new forecasts on every daily refresh and
    # the grading runner now lands grades, so both assertions failed
    # closed forever on a healthy record. The binding that remains
    # is the one that ties each entrant to its own page: the ledger
    # count must equal the count the entrant's own page publishes.
    for eid in ("engine_01", "engine_02", "engine_05", "engine_06",
                "engine_12", "engine_15"):
        if live_counts[eid] != measured[eid]["live_recorded_src"]:
            fail(f"{eid} live count disagrees with its own page: "
                 f"{live_counts[eid]} vs {measured[eid]['live_recorded_src']}")

    table, ranking, fam_rows = build_table(measured, live_counts)
    for row in table:
        row["live_graded"] = live_graded.get(row["id"], 0)

    # ---- grading of any matured League rounds (none can exist yet)
    appended, stats = grade_rounds(led, rows)
    rows = led.rows()

    # ---- issue step: only inside a round's issue window, never on
    # the build day. A round's window opens on its decision day and
    # closes when its month opens.
    today = date.today().isoformat()
    issued_now = 0
    months = []
    y, m = 2026, 11
    for _ in range(14):
        months.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    already = {r["subject"].split(":")[0] for r in rows
               if r.get("type") == "forecast"
               and r.get("engine_id") == ENGINE_ID}
    for month_str in months:
        rnd = round_for_month(month_str)
        if month_str in already:
            continue
        if rnd["decision_as_of"] <= today < rnd["horizon_open"]:
            lineage = {"clocks": {
                "event_time": rnd["decision_as_of"],
                "publication_time": today,
                "first_available_time": rnd["decision_as_of"],
                "ingestion_time": today,
                "decision_as_of": rnd["decision_as_of"]},
                "source_artifacts": [
                    {"path": p, "sha256": file_sha256(p)}
                    for p in list(SRC.values()) + [EVIDENCE]]}
            issued_now += issue_round(led, reg, table, ranking, fam_rows,
                                      rnd, lineage)
            rows = led.rows()
    league_forecasts = sum(1 for r in rows if r.get("type") == "forecast"
                           and r.get("engine_id") == ENGINE_ID)
    league_grades = sum(1 for r in rows if r.get("type") == "grade"
                        and r.get("engine_id") == ENGINE_ID)
    rounds_issued = len({r["subject"].split(":")[0] for r in rows
                         if r.get("type") == "forecast"
                         and r.get("engine_id") == ENGINE_ID})

    test = self_test(reg)

    as_of = max(load_json(SRC["engine_05"])["as_of"],
                load_json(SRC["engine_12"])["decision_as_of"])

    try:
        from proof_gate_block import (ProofGateError,
                                      build_proof_gate_block)
        proof_gate_block = build_proof_gate_block(
            HERE, ENGINE_ID, as_of, LEDGER_PATH)
    except ProofGateError as exc:
        fail(str(exc))

    entrant_rows = []
    for row in table:
        m = row["measured"]
        iv = row["interval"]
        entrant_rows.append({
            "id": row["id"], "name": row["name"],
            "claim_words": row["claim_words"],
            "family_words": row["family_words"],
            "eligibility": row["eligibility"],
            "eligibility_words": row["eligibility_words"],
            "forecastable": row["forecastable"],
            "prior_based": bool(m.get("prior_based")),
            "study_form": bool(m.get("study_form")),
            "graded_count": m["graded"],
            "stated_pct": m["stated_pct"],
            "realised_pct": m["realised_pct"],
            "error_pts": m["error_pts"],
            "live_recorded": row["live_recorded"],
            "live_graded": row["live_graded"],
            "rank": row.get("rank"),
            "interval": (None if iv is None else {
                "rate_low_pct": iv["rate_low_pct"],
                "rate_high_pct": iv["rate_high_pct"],
                "err_low_pts": iv["err_low_pts"],
                "err_high_pts": iv["err_high_pts"],
                "width_pts": iv["width_pts"]}),
            "rival_interval": (None if row["rival_interval"] is None
                               else {
                "err_low_pts": row["rival_interval"]["err_low_pts"],
                "err_high_pts": row["rival_interval"]["err_high_pts"]}),
        })

    iv_stats = stats.get("intervals") or {}
    data = {
        "tool": "Calibration League",
        "state": "proving",
        "as_of": as_of,
        "idea_words": "Every forecaster on this site states a "
            "confidence: a band that promises to hold 68 times in 100, "
            "a chance of reaching a level, a range that promises 80 "
            "in 100. This page is a league that predicts, one month "
            "ahead, how far each of those promises is about to miss "
            "over its next 60 graded forecasts, and stakes its own "
            "record on the prediction. Its ranges and its ranking are "
            "written to the same public record before the month "
            "opens, and graded by the same rule when the 60 forecasts "
            "land. A league that grades everyone else's honesty is "
            "itself graded, in public, on whether it called the "
            "honesty right.",
        "error_words": "The one measure, the same for everyone: over "
            "an entrant's next 60 graded forecasts, take how often "
            "the event actually happened, subtract the average of "
            "what the entrant said, and read the difference in "
            "points. Above zero means the entrant understated how "
            "often its event happens (its band held more often than "
            "promised, or its chances ran low). Below zero means it "
            "overstated. Zero is a perfectly honest forecaster.",
        "how_words": "Each coming range is built from the entrant's "
            "own measured record so far: its running error, the "
            "count behind it, and any built-in tilt an earlier study "
            "measured in its construction, carried forward with the "
            "width that plain chance over just 60 forecasts honestly "
            "needs. That is why the ranges are wide: 60 forecasts is "
            "a small sample, and a narrower range would be pretending "
            "to know more than the record holds.",
        "ranking_words": "Entrants are ranked by how small their "
            "coming error is predicted to be. Because several "
            "entrants are built the same way, the headline ranking "
            "groups them by kind and counts each kind once, at the "
            "middle of its members: four forecasters built from "
            "movement and spread agreeing is one voice, not four.",
        "cadence_words": "One round a month. Each round is written "
            "to the public record before the month opens, and closes "
            "for each entrant when that entrant's 60th graded "
            "forecast lands, which for the slower entrants can take "
            "months. Nothing is graded early, and no entrant-round "
            "is ever graded on fewer than the full 60.",
        "first_issue_date": FIRST_ISSUE_OPEN,
        "first_decision_as_of": FIRST_DECISION_AS_OF,
        "round_state_words": (
            "The November round is staked: its ranges and ranking "
            "were written to the public record at the decision "
            "close of Friday, October 30, 2026, before the month "
            "opens on Monday, November 2, 2026, and they grade "
            "when each entrant's next 60 graded forecasts land."
            if rounds_issued else
            "The November round is not staked yet. "
            "The ranges and the ranking below are the ones this page "
            "will write to the public record at the close of Friday, "
            "October 30, 2026, before the month opens on Monday, "
            "November 2, 2026. Today they are a preview, marked as "
            "such, and nothing has been written early."),
        "entrants": entrant_rows,
        "ranking": ranking,
        "ranking_names": [next(e["name"] for e in ENTRANTS
                                if e["id"] == rid) for rid in ranking],
        "family_ranking": fam_rows,
        "live_record": {
            "rounds_issued": rounds_issued,
            "league_forecasts_recorded": league_forecasts,
            "league_forecasts_graded": league_grades,
            "intervals_graded": iv_stats.get("graded", 0),
            "intervals_hit": iv_stats.get("hits", 0.0),
            "target_rounds": KILL_TARGET,
            "words": (
                f"{rounds_issued} round(s) issued and "
                f"{league_forecasts} league forecasts on record; "
                f"{league_grades} graded so far. A round grades "
                "only when an entrant's full 60 forecasts have "
                "been graded, so early rounds stay open for "
                "months. Twelve monthly rounds decide whether "
                "it stands or retires."
                if rounds_issued else
                "No round has been issued yet, so nothing of "
                "this league's own is graded. The first round "
                "is November 2026; twelve monthly rounds decide "
                "whether it stands or retires.")},
        "kill_words": "After 12 monthly rounds, if the share of this "
            "league's ranges that contained the real error is no "
            "better than a no-change rival, one that simply carries "
            "each entrant's latest measured error forward with the "
            "same width, this page retires and its record stays up "
            "intact. Both hit rates and both widths are published at "
            "each round's close, so a win on width alone would show.",
        "thin_cell_words": "The thin rule, everywhere on this page: "
            "an entrant-round is graded only when its full 60 "
            "forecasts have been graded. Fewer than 60 means the "
            "round stays open and the count is printed, never a "
            "verdict on a partial count.",
        "proving_state": "Still being proven",
        "source": "the shared public forecast record all these "
                  "forecasters publish to, each entrant's own "
                  "published history, and the earlier studies that "
                  "measured the two vendor constructions",
        "self_test": test,
        "issued_this_run": issued_now,
        "grades_appended_this_run": appended,
        "proof_gate": proof_gate_block,
    }
    out_path = os.path.join(OUT_DIR, "data.json")
    tmp_path = out_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp_path, out_path)
    print(f"calibration-league: entrants {len(entrant_rows)}, "
          f"forecastable {sum(1 for e in entrant_rows if e['forecastable'])}, "
          f"issued this run {issued_now}, league rows in record "
          f"{league_forecasts}, data -> {out_path}")


if __name__ == "__main__":
    main()
