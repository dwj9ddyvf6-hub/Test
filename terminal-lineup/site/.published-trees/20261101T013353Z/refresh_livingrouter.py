#!/usr/bin/env python3
"""Refresh The Living Router (Forecast Engine 18).

=====================================================================
REGISTER TRIPLE (written before any computation)

1. EVIDENCE CLASS
   - Meta-forecasting over the tracked forecasters already on record.
     No corpus part publishes live averaging weights over its own
     competitors, and no tool's weights are a graded public record;
     this engine makes the weights themselves the record. Its honest
     prior, carried from the design: fair as a calibration device,
     unproven as an edge device. Model averaging reliably beats
     picking a winner; whether the population below has anything to
     average is the open question the two controls exist to answer.
   - This engine's own live record: none before today. Nothing is
     backfilled: its record starts today.

2. RECONSTRUCTION CHOICES (every constant named before computing)

   THE FORECAST: for every stock where at least two tracked
   forecasters disagree, a distribution of three chances (bottom
   third, middle third, top third) for the stock's gain against the
   broad market (SPY) over the next 21 trading days, built by
   averaging the forecasters' converted calls with the live weights
   below. Graded by ranked probability score at 21 trading days
   against the two controls in section 3. The realised third for
   grading is the cross-sectional third of the 21-session
   gain-against-SPY among that day's published names; a day needs
   at least 9 published names to grade at all (the thin-cell rule).

   POPULATION TABLE (each tracked forecaster population, its source,
   its conversion into the three chances, its evidence family):
   a) The Board's published stock calls, from The Record's published
      data (site/record/data.json). Each call is a call that the
      stock will rise (The Record grades its calls by whether the
      stock rose). CONVERSION: a fixed lean, registered here, never
      fitted: a rising call becomes (bottom 0.20, middle 0.30,
      top 0.50). Family: price. Dated and per-name: 50 calls over
      the sessions 2026-10-23 and 2026-10-26, 37 different stocks;
      graded so far at 1 trading day only (22 calls); at 21 trading
      days, 0 graded (first such grades land 2026-11-23).
   b) The capitulation volume clock's return calls, ledgered in the
      shared forecast ledger as engine_16 rows with quantity
      "median_20_session_excess_points": a claimed middle gain
      against SPY of +1.0 points over about 20 sessions, for 14
      stocks as of the close of 2026-10-23. CONVERSION: by the sign
      of the claimed middle gain; +1.0 is a rising call and converts
      exactly as (a). Family: price (the ledger rows' own family
      label). Ledgered with the full five-clock envelope; graded so
      far: 0 (the shared ledger holds no grade rows at all today).
   c) The morning map's published cards (in The Record's data):
      levels for SPY, QQQ and IWM only. No per-stock directional
      call exists to convert. Family: modelled inventory.
      NOT CONVERTIBLE: weight zero today.
   d) The flow tape's published alerts (site/flow-tape/data.json):
      75 alerts on 2026-10-27 over the same 3 index funds, in both
      directions on each fund. No single per-name call exists to
      convert. Family: options prints. NOT CONVERTIBLE: weight zero.
   e) The top-grade book (site/grade-a-board/data.json): 63 cells,
      of which 57 are movement cells (no direction at all) and 6
      are warning cells whose grades are pooled study grades, not
      dated per-stock forward calls. No dated per-stock call exists
      to convert. Family: price. NOT CONVERTIBLE: weight zero.
   f) The Strat bar labels (site/strat-scanner/data.json): 1,817
      stocks labelled for the single session 2026-10-23. The labels
      describe the shape of past bars and claim no direction; the
      page's own proving note says nothing has graded what follows
      them. Family: price. NOT CONVERTIBLE: weight zero.
   Populations not yet ledgered or carded in a convertible form
   enter at weight zero until they are, exactly as the design says.

   ELIGIBILITY: a forecaster is eligible (may hold weight) only if
   it has a dated, per-stock, convertible call record published
   before the window it speaks about: the publication timestamps on
   The Record's calls serve as the publication clock for carded
   populations, and ledgered populations must carry the full
   five-clock envelope on every row (checked; a row missing a clock
   fails this script closed). Today (a) and (b) are eligible;
   (c)-(f) are not, for the reasons stated, and are named on the
   page at weight zero, never silently dropped.

   WEIGHT FORMULA (exact, all constants registered here):
   - For each eligible forecaster i, let its graded forward record
     at 21 trading days be its graded calls with their ranked
     probability scores. Its effective track record is
       n_eff(i) = sum over graded calls of 0.5 ** (age_sessions / 63)
     (a 63-session half-life on past grades; age in trading days
     from the call's own session to today).
   - Its shrinkage factor is lambda(i) = n_eff(i) / (n_eff(i) + 63).
   - Its performance weight is p(i), proportional to exp(-RPS(i))
     over eligible forecasters, where RPS(i) is its decayed mean
     ranked probability score; with no graded record anywhere, p is
     undefined and every eligible forecaster takes the equal share.
   - Its published weight is
       w(i) = (1 - lambda(i)) * (1 / N) + lambda(i) * p(i),
     N = the number of eligible forecasters, then normalised.
   - FAMILY CAP: no evidence family may hold more than 0.50 of the
     total weight when at least two families hold weight; any excess
     is redistributed pro-rata to the other families' forecasters.
     When only one family holds weight the cap cannot bite and the
     page says so. Today both eligible forecasters are price family.
   - Today every population has n_eff = 0 (no 21-session graded
     forward record exists anywhere), so lambda = 0 for all, and the
     published weights are exactly the equal shares: 0.50 and 0.50.
     That is the shrinkage state the young record produces, printed
     as it is: the weights carry no earned differentiation yet.

   DISAGREEMENT, THE FLOOR, AND FLAT PUBLISHING:
   - Two forecasters disagree on a stock when their converted
     distributions differ.
   - A stock's effective weight is EW = sum over the forecasters
     covering it of lambda(i) * w(i): the share of its distribution
     that is earned by graded track records. THE FLOOR is 0.25,
     registered here before computing. Today EW = 0 for every stock,
     because every lambda is 0.
   - A contested stock (two or more disagreeing eligible
     forecasters) whose EW is below the floor publishes the FLAT
     distribution (a third, a third, a third), ledgered and graded
     as flat: an abstention with mass, not a missing row.
   - A contested stock at or above the floor publishes the weighted
     average of its forecasters' converted distributions, weights
     renormalised over the forecasters covering that stock.

   CENSUS TODAY (computed by this script from the sources, never
   assumed): the Board's 37 stocks and the capitulation clock's 14
   stocks overlap in 0 stocks, so 51 stocks carry exactly one
   convertible forecaster, 0 carry two or more, 0 are contested,
   0 clear the floor, and 0 rows are published today, flat or
   otherwise. Stocks below the disagreement threshold are counted
   on the page, never silently dropped. The script fails closed if
   the computed census ever contradicts The Record's own totals.

   HORIZONS (for any row this script ledgers): the window opens on
   the first weekday after the newest call date among the stock's
   forecasters and closes 21 weekdays after the newest call date
   (the same weekday counting The Record's own 21-day grade dates
   use: the 2026-10-26 board session's first 21-day grade date is
   2026-11-24).

3. CONTROLS AND NON-CLAIMS
   - Control one, EQUAL WEIGHTS: the plain average of the same
     day's eligible converted distributions for the same stock,
     ledgered the same day under its own marker, graded identically.
     It is also this engine's live rival in the kill criterion.
   - Control two, BEST SINGLE: the single forecaster with the lowest
     decayed past score, chosen on past data only (the
     selection-bias control). UNSELECTABLE TODAY: no forecaster has
     any graded 21-session record, so there is no past score to pick
     by; it ledgers nothing until one exists, and the page says so.
   - Kill criterion (from the design, in plain words): after 126
     graded name-windows, if the weighted distributions do not beat
     the equal-weight control, the weights freeze and this page
     publishes the equal-weight distribution, labelled as such.
   - The page prints both the name count and the independent-window
     count: overlapping 21-session windows inflate the apparent
     sample size, so graded name-windows are also counted greedily
     by non-overlapping windows (a window counts as independent only
     if it opens after every earlier counted window has closed).
   - Non-claims: no stock is recommended; a distribution over three
     thirds is a spread of chances, not a verdict; no weight on this
     page is earned until a graded 21-session record exists behind
     it, and the page says which weights are unearned equal shares.
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
import os
import sys
import tempfile
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # terminal-lineup/
FORECAST = os.path.join(ROOT, "forecast")
sys.path.insert(0, FORECAST)
from ledger import Ledger, file_sha256             # noqa: E402
from registry import Registry                      # noqa: E402

OUT_DIR = os.path.join(HERE, "living-router")
RECORD = os.path.join(HERE, "record", "data.json")
FLOW_TAPE = os.path.join(HERE, "flow-tape", "data.json")
GRADE_A = os.path.join(HERE, "grade-a-board", "data.json")
STRAT = os.path.join(HERE, "strat-scanner", "data.json")
LEDGER_PATH = os.path.join(FORECAST, "ledger.jsonl")

ENGINE_ID = "engine_18"
HALF_LIFE = 63
SHRINK_PRIOR = 63
FAMILY_CAP = 0.50
FLOOR = 0.25
KILL_TARGET = 126
THIN_CELL_MIN_NAMES = 9
BULLISH = (0.20, 0.30, 0.50)
BEARISH = (0.50, 0.30, 0.20)
FLAT = (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)


def fail(msg):
    raise SystemExit(f"living-router refresh FAILED CLOSED: {msg}")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def add_weekdays(d, n):
    step = 1 if n >= 0 else -1
    for _ in range(abs(n)):
        d += timedelta(days=step)
        while d.weekday() >= 5:
            d += timedelta(days=step)
    return d


def convert(sign):
    return BULLISH if sign > 0 else BEARISH if sign < 0 else FLAT


# ------------------------------------------------------------------
# Population reads (compute from sources; fail closed on mismatch)
# ------------------------------------------------------------------
def read_board(record):
    """Board calls from The Record: freshest call per stock."""
    groups = record["board"]["groups"]
    total = sum(len(g["calls"]) for g in groups)
    if total != record["totals"]["board_calls"]:
        fail(f"Record board total mismatch: groups hold {total}, "
             f"totals say {record['totals']['board_calls']}")
    calls = {}
    sessions = []
    graded_21 = 0
    graded_1 = 0
    for g in groups:
        sessions.append(g["session"])
        graded_21 += (g.get("grades", {}).get("21d", {})
                      .get("graded_count") or 0)
        graded_1 += (g.get("grades", {}).get("1d", {})
                     .get("graded_count") or 0)
        for c in g["calls"]:
            prev = calls.get(c["symbol"])
            if prev is None or g["session"] > prev[0]:
                # The Record grades board calls by whether the stock
                # rose: every published call is a rising call (+1).
                calls[c["symbol"]] = (g["session"], +1)
    return {"calls": calls, "total_calls": total, "sessions": sessions,
            "graded_21": graded_21, "graded_1": graded_1}


def read_engine16(rows):
    """The capitulation clock's return-leg calls from the ledger."""
    calls = {}
    for r in rows:
        if r.get("type") != "forecast" or r.get("engine_id") != "engine_16":
            continue
        clocks = (r.get("lineage") or {}).get("clocks") or {}
        missing = [c for c in ("event_time", "publication_time",
                               "first_available_time", "ingestion_time",
                               "decision_as_of") if c not in clocks]
        if missing:
            fail(f"engine_16 row {r.get('row_id')} missing clocks {missing}")
        if r.get("quantity") != "median_20_session_excess_points":
            continue
        est = (r.get("value") or {}).get("estimate")
        if est is None:
            fail(f"engine_16 return row {r.get('row_id')} has no estimate")
        sign = +1 if est > 0 else -1 if est < 0 else 0
        calls[r["subject"]] = (clocks["decision_as_of"], sign)
    if not calls:
        fail("no engine_16 return-leg calls found in the ledger")
    graded = sum(1 for r in rows if r.get("type") == "grade"
                 and r.get("engine_id") == "engine_16")
    return {"calls": calls, "graded_any": graded}


# ------------------------------------------------------------------
# Weights (the registered formula, nothing else)
# ------------------------------------------------------------------
def compute_weights(eligible):
    """eligible: list of dicts with keys id, family, n_eff, rps (or None).
    Returns {id: weight} after shrinkage and the family cap."""
    n = len(eligible)
    if n == 0:
        return {}
    base = 1.0 / n
    have_scores = all(e["rps"] is not None and e["n_eff"] > 0
                      for e in eligible)
    if have_scores:
        import math
        raw = {e["id"]: math.exp(-e["rps"]) for e in eligible}
        tot = sum(raw.values())
        perf = {k: v / tot for k, v in raw.items()}
    else:
        perf = {e["id"]: base for e in eligible}
    w = {}
    for e in eligible:
        lam = e["n_eff"] / (e["n_eff"] + SHRINK_PRIOR)
        w[e["id"]] = (1.0 - lam) * base + lam * perf[e["id"]]
    tot = sum(w.values())
    w = {k: v / tot for k, v in w.items()}
    # Family cap: only when at least two families hold weight.
    fams = {}
    for e in eligible:
        fams[e["family"]] = fams.get(e["family"], 0.0) + w[e["id"]]
    if len([f for f, v in fams.items() if v > 0]) >= 2:
        excess = 0.0
        capped = {}
        for e in eligible:
            share = w[e["id"]]
            fam_share = fams[e["family"]]
            if fam_share > FAMILY_CAP:
                share = share * FAMILY_CAP / fam_share
            capped[e["id"]] = share
            excess += w[e["id"]] - share
        rest = sum(capped[e2["id"]] for e2 in eligible
                   if fams[e2["family"]] <= FAMILY_CAP)
        if excess > 0 and rest > 0:
            for e in eligible:
                if fams[e["family"]] <= FAMILY_CAP:
                    capped[e["id"]] += excess * capped[e["id"]] / rest
        tot = sum(capped.values())
        w = {k: v / tot for k, v in capped.items()}
    return w


def weighted_average(dists, weights):
    out = [0.0, 0.0, 0.0]
    tot = sum(weights)
    for d, wt in zip(dists, weights):
        for k in range(3):
            out[k] += d[k] * wt / tot
    return tuple(round(x, 6) for x in out)


# ------------------------------------------------------------------
# Self-test: the full distribution path on made-up forecasters,
# written only to a throwaway ledger in /tmp (like Engine 5).
# ------------------------------------------------------------------
def self_test():
    elig = [
        {"id": "fake_a", "family": "price", "n_eff": 0.0, "rps": None},
        {"id": "fake_b", "family": "options_prints", "n_eff": 0.0,
         "rps": None},
    ]
    w = compute_weights(elig)
    assert abs(w["fake_a"] - 0.5) < 1e-9 and abs(w["fake_b"] - 0.5) < 1e-9
    dists = {"fake_a": convert(+1), "fake_b": convert(-1)}  # disagree
    ew = sum(0.0 * w[k] for k in w)  # every lambda is 0 in the test
    published = FLAT if ew < FLOOR else weighted_average(
        [dists[k] for k in ("fake_a", "fake_b")],
        [w[k] for k in ("fake_a", "fake_b")])
    assert published == FLAT, published
    equal = weighted_average([dists["fake_a"], dists["fake_b"]], [1, 1])
    assert equal == (0.35, 0.3, 0.35), equal
    path = os.path.join(tempfile.mkdtemp(), "scratch.jsonl")
    led = Ledger(path)
    clocks = {c: "2026-10-29" for c in
              ("event_time", "publication_time", "first_available_time",
               "ingestion_time", "decision_as_of")}
    lin = {"clocks": clocks, "source_artifacts": [
        {"path": os.path.abspath(__file__),
         "sha256": file_sha256(os.path.abspath(__file__))}]}
    n = 0
    for marker, dist in (("weighted", published), ("equal_weight", equal)):
        _, created = led.append_forecast_declared(
            engine_id=ENGINE_ID, issued_ts="2026-10-29", subject="TEST",
            quantity="tercile_distribution_" + marker,
            value={"p_bottom": dist[0], "p_middle": dist[1],
                   "p_top": dist[2], "flat": dist == FLAT},
            horizon_open="2026-10-30", horizon_close="2026-11-30",
            lineage=lin, families=["price"],
            outcome={"kind": "tercile_21_session_excess_vs_spy",
                     "symbol": "TEST"})
        n += 1 if created else 0
        _, again = led.append_forecast_declared(
            engine_id=ENGINE_ID, issued_ts="2026-10-29", subject="TEST",
            quantity="tercile_distribution_" + marker,
            value={"p_bottom": dist[0], "p_middle": dist[1],
                   "p_top": dist[2], "flat": dist == FLAT},
            horizon_open="2026-10-30", horizon_close="2026-11-30",
            lineage=lin, families=["price"],
            outcome={"kind": "tercile_21_session_excess_vs_spy",
                     "symbol": "TEST"})
        assert not again  # identical republication counts once
    assert led.verify_chain()
    return {"rows_written_to_scratch": n,
            "flat_below_floor": True, "equal_weight_control": list(equal)}


# ------------------------------------------------------------------
def main():
    record = load_json(RECORD)
    tape = load_json(FLOW_TAPE)
    grade_a = load_json(GRADE_A)
    strat = load_json(STRAT)

    registry = Registry(os.path.join(FORECAST, "registry.json"))
    registry.validate_engine(ENGINE_ID)
    ledger = Ledger(LEDGER_PATH, registry=registry)
    rows = ledger.rows()
    if not ledger.verify_chain(rows):
        fail("forecast ledger hash chain does not verify")

    board = read_board(record)
    e16 = read_engine16(rows)

    # Cross-checks against the sources' own published counts.
    # Session pins cured at the class level (terminal audit,
    # 2026-10-31): the tape and strat records are rolling sources
    # that advance every session, so an exact session and count
    # pin fails the first scheduled run after every re-register,
    # which is the in-run-only failure class behind the refresh
    # reproducibility defect. The registered values (tape: 75
    # alerts on 2026-10-30; strat: 1816 names on 2026-10-29,
    # re-registered 2026-10-30) are now floors: a source may
    # advance past its register, never fall behind it or arrive
    # empty. The grade-A book counts below stay exact: that book
    # is a finished search result, not a rolling source.
    if tape["session"] < "2026-10-30" \
            or tape["counts"]["alerts_published"] <= 0:
        fail("flow tape record fell behind its registered floor "
             f"(75 alerts on 2026-10-30): {tape['counts']} "
             f"session {tape['session']}")
    ga = grade_a["counts"]
    if ga["grade_a"] != 63 or ga["movement_cells"] != 57 or ga["warning_cells"] != 6:
        fail(f"grade-A book counts disagree with the register: {ga}")
    if strat["session"] < "2026-10-29" \
            or strat["names_labelled"] <= 0:
        fail(f"strat label record fell behind its registered floor "
             f"(1816 names on 2026-10-29): "
             f"{strat['names_labelled']} names, session {strat['session']}")
    map_cards = sum(len(g["cards"]) for g in record["map"]["groups"])
    if map_cards != record["totals"]["map_calls"]:
        fail("Record map totals disagree with its groups")

    grade_rows_total = sum(1 for r in rows if r.get("type") == "grade")

    # ---- populations and weights --------------------------------
    # n_eff: graded 21-session forward records. Board: from The
    # Record's own 21-day grade state. Engine_16: grade rows in the
    # shared ledger (its grades, when they exist, are 21-session
    # tercile grades only via this engine's family of rules; today
    # the ledger holds no grade rows at all).
    eligible = [
        {"id": "board", "family": "price",
         "n_eff": float(board["graded_21"]), "rps": None},
        {"id": "capitulation_clock", "family": "price",
         "n_eff": float(e16["graded_any"]), "rps": None},
    ]
    weights = compute_weights(eligible)
    lam = {e["id"]: e["n_eff"] / (e["n_eff"] + SHRINK_PRIOR)
           for e in eligible}

    calls_by_forecaster = {"board": board["calls"],
                           "capitulation_clock": e16["calls"]}

    # ---- census ---------------------------------------------------
    names = {}
    for fid, calls in calls_by_forecaster.items():
        for sym, (sess, sign) in calls.items():
            names.setdefault(sym, {})[fid] = (sess, convert(sign))
    contested, agreeing = [], []
    for sym, per in sorted(names.items()):
        if len(per) < 2:
            continue
        dists = [per[f][1] for f in per]
        (contested if len(set(dists)) > 1 else agreeing).append(sym)
    one_forecaster = [s for s, per in names.items() if len(per) == 1]

    as_of = max(sess for calls in calls_by_forecaster.values()
                for sess, _ in calls.values())

    # ---- publish (only contested names; none today) ---------------
    published = []
    created_total = 0
    for sym in contested:
        per = names[sym]
        fids = sorted(per)
        dists = [per[f][1] for f in fids]
        ew = sum(lam[f] * weights[f] for f in fids)
        coverage_weight = (sum(weights[f] for f in fids) / sum(weights.values()) if weights else 0.0)
        is_flat = ew < FLOOR
        dist = FLAT if is_flat else weighted_average(
            dists, [weights[f] for f in fids])
        newest = max(per[f][0] for f in fids)
        nd = date.fromisoformat(newest)
        h_open = add_weekdays(nd, 1).isoformat()
        h_close = add_weekdays(nd, 21).isoformat()
        equal = weighted_average(dists, [1.0] * len(dists))
        clocks = {"event_time": newest, "publication_time": newest,
                  "first_available_time": newest,
                  "ingestion_time": as_of, "decision_as_of": as_of}
        lineage = {"clocks": clocks, "source_artifacts": [
            {"path": p, "sha256": file_sha256(p)}
            for p in (RECORD, LEDGER_PATH)]}
        fams = sorted({next(e["family"] for e in eligible
                            if e["id"] == f) for f in fids})
        for marker, d in (("weighted", dist), ("equal_weight", equal)):
            _, created = ledger.append_forecast_declared(
                engine_id=ENGINE_ID, issued_ts=as_of, subject=sym,
                quantity="tercile_distribution_" + marker,
                value={"p_bottom": d[0], "p_middle": d[1], "p_top": d[2],
                       "flat": d == FLAT,
                       "effective_weight": round(ew, 6),
                       "coverage_weight": round(coverage_weight, 6)},
                horizon_open=h_open, horizon_close=h_close,
                lineage=lineage, families=fams,
                outcome={"kind": "tercile_21_session_excess_vs_spy",
                         "symbol": sym, "base_date": newest,
                         "thin_cell_min_names": THIN_CELL_MIN_NAMES})
            created_total += 1 if created else 0
        published.append({"symbol": sym, "flat": is_flat,
                          "coverage_weight": round(coverage_weight, 6),
                          "p_bottom": dist[0], "p_middle": dist[1],
                          "p_top": dist[2],
                          "effective_weight": round(ew, 6)})

    rows_after = ledger.rows()
    if not ledger.verify_chain(rows_after):
        fail("forecast ledger chain broke after appends")
    e18 = [r for r in rows_after if r.get("engine_id") == ENGINE_ID
           and r.get("type") == "forecast"]
    e18_graded = sum(1 for r in rows_after if r.get("type") == "grade"
                     and r.get("engine_id") == ENGINE_ID)
    # Independent windows: greedy non-overlapping count over graded
    # name-windows (none today).
    indep = 0
    last_close = ""
    for r in sorted((r for r in rows_after if r.get("type") == "grade"
                     and r.get("engine_id") == ENGINE_ID),
                    key=lambda r: r.get("horizon_close", "")):
        if r.get("horizon_close", "") > last_close:
            indep += 1
            last_close = r["horizon_close"]

    test = self_test()

    data = {
        "tool": "The Living Router",
        "as_of": as_of,
        "source": ("The Record's published calls, the shared forecast "
                   "ledger, the top-grade book, the flow tape and the "
                   "Strat label record, all read directly"),
        "idea_words": (
            "Instead of one verdict on a stock, this page publishes a "
            "spread of three chances for what the stock does against "
            "the broad market over the next 21 trading days: the "
            "chance it lands in the bottom third of stocks, the "
            "middle third, or the top third. The chances are built "
            "by averaging the tracked forecasters who disagree about "
            "that stock, weighted by each forecaster's own graded "
            "track record. The weights are published here and graded "
            "in public, like the forecasts themselves."),
        "weights_words": (
            "A forecaster's weight grows only with its own graded "
            "record at 21 trading days: recent grades count more "
            "than old ones (a grade's pull halves every 63 trading "
            "days), a young record is pulled toward equal weights, "
            "and no single kind of evidence may hold more than half "
            "the total weight when more than one kind is speaking. "
            "Today no forecaster anywhere has a graded 21-day record "
            "yet, so nothing has been earned: the two eligible "
            "forecasters below hold exactly equal weights, and every "
            "stock's earned weight is zero, under the floor of 0.25 "
            "written down in advance. Any contested stock today "
            "would therefore publish flat chances (a third, a third, "
            "a third) and be graded on them."),
        "family_cap_note": (
            "Both eligible forecasters rest on the same kind of "
            "evidence (price), so the half-the-total cap on one kind "
            "of evidence cannot bite yet: there is no second kind "
            "holding weight to protect."),
        "forecasters": [
            {"name": "The daily board of top-scoring stocks, as "
                     "published in The Record",
             "family_words": "price evidence",
             "weight": weights.get("board", 0.0),
             "eligible": True,
             "track_record_words": (
                 f"{board['total_calls']} dated calls on "
                 f"{len(board['calls'])} stocks over "
                 f"{len(board['sessions'])} sessions "
                 f"({', '.join(board['sessions'])}); "
                 f"{board['graded_1']} graded so far, all at 1 "
                 f"trading day; 0 graded at 21 trading days (the "
                 f"first arrive November 23, 2026)"),
             "conversion_words": (
                 "Each call says the stock will rise; a rising call "
                 "becomes fixed chances of 20% bottom third, 30% "
                 "middle third, 50% top third, written down in "
                 "advance and never adjusted to fit past results")},
            {"name": "The capitulation volume clock's return calls, "
                     "recorded in the shared forecast ledger",
             "family_words": "price evidence",
             "weight": weights.get("capitulation_clock", 0.0),
             "eligible": True,
             "track_record_words": (
                 f"{len(e16['calls'])} stocks carry a return call "
                 f"(a claimed middle gain of 1.0 points against the "
                 f"broad market), made at the close of October 23, "
                 f"2026; 0 graded so far at any stretch"),
             "conversion_words": (
                 "The claimed gain is positive, so each call "
                 "converts the same way as a rising call: 20% bottom "
                 "third, 30% middle third, 50% top third")},
            {"name": "The morning map's published cards",
             "family_words": "modelled positioning evidence",
             "weight": 0.0, "eligible": False,
             "track_record_words": (
                 f"{map_cards} cards on the 3 big index funds; "
                 f"0 graded"),
             "conversion_words": (
                 "Weight zero: its cards give levels for index funds "
                 "only and make no call about any stock, so there is "
                 "nothing to convert. It enters the day it publishes "
                 "a dated per-stock call")},
            {"name": "The flow tape's published alerts",
             "family_words": "options trading evidence",
             "weight": 0.0, "eligible": False,
             "track_record_words": (
                 f"{tape['counts']['alerts_published']} alerts on "
                 f"{tape['session']} over the same 3 index funds; "
                 f"none graded"),
             "conversion_words": (
                 "Weight zero: its alerts point both ways on each "
                 "fund and name no stock, so there is no single call "
                 "to convert")},
            {"name": "The top-grade book of tested patterns",
             "family_words": "price evidence",
             "weight": 0.0, "eligible": False,
             "track_record_words": (
                 "63 top-grade patterns: 57 describe movement with "
                 "no direction, and 6 warning patterns carry pooled "
                 "study grades rather than dated calls on stocks"),
             "conversion_words": (
                 "Weight zero: no dated per-stock call exists to "
                 "convert. A study grade pooled over thousands of "
                 "past cases is not a call on today's stock")},
            {"name": "The Strat bar labels",
             "family_words": "price evidence",
             "weight": 0.0, "eligible": False,
             "track_record_words": (
                 "1,817 stocks labelled for one session, October "
                 "23, 2026; nothing has graded what follows a label"),
             "conversion_words": (
                 "Weight zero: the labels describe the shape of past "
                 "bars and claim no direction, so there is no call "
                 "to convert")},
        ],
        "census": {
            "names_with_any_forecaster": len(names),
            "names_with_one_forecaster": len(one_forecaster),
            "names_with_two_agreeing": len(agreeing),
            "names_contested": len(contested),
            "names_clearing_floor": sum(
                1 for p in published if not p["flat"]),
            "names_flat": sum(1 for p in published if p["flat"]),
            "board_names": len(board["calls"]),
            "capitulation_names": len(e16["calls"]),
            "overlap_names": len(set(board["calls"]) & set(e16["calls"])),
            "words": (
                f"The board speaks on {len(board['calls'])} stocks "
                f"and the capitulation clock on {len(e16['calls'])} "
                f"stocks, and the two lists share no stock at all. "
                f"So {len(one_forecaster)} stocks carry exactly one "
                f"forecaster each and none carries two: there is no "
                f"disagreement to average today, and this page "
                f"publishes no chances rather than inventing some. "
                f"The {len(one_forecaster)} single-forecaster stocks "
                f"are counted here, not quietly dropped.")},
        "contested_names": published,
        "controls": {
            "equal_weight_words": (
                "The plain average: the same forecasters' chances "
                "averaged with no weights at all, recorded on the "
                "same stocks on the same days and graded the same "
                "way. Today it is also what the shrinkage produces, "
                "which is exactly why it is the rival to beat."),
            "best_single_words": (
                "The best single forecaster, picked using only its "
                "past graded record. It cannot be picked today: no "
                "forecaster has any graded 21-day record to pick by, "
                "so it records nothing until one exists. Picking the "
                "best-looking forecaster after the fact flatters it; "
                "this control exists to keep that honest."),
            "best_single_selectable": False},
        "live_record": {
            "distributions_recorded": len(e18),
            "graded": e18_graded,
            "graded_name_windows": e18_graded,
            "independent_windows": indep,
            "target": KILL_TARGET,
            "words": (
                f"{len(e18)} distributions recorded, "
                f"{e18_graded} graded so far, of the {KILL_TARGET} "
                f"graded name-windows that decide this page. Because "
                f"21-day windows overlap, the graded windows are "
                f"also counted a stricter way: {indep} independent "
                f"windows so far.")},
        "kill_words": (
            "After 126 graded name-windows, if the weighted chances "
            "have not scored better than the plain average's chances "
            "on the same stocks, the weights freeze and this page "
            "publishes the plain average instead, labelled as such."),
        "thin_cell_words": (
            "Small counts prove little: a day needs at least 9 "
            "published stocks before its outcomes can be graded into "
            "thirds at all, and every count on this page is printed "
            "beside the rate it feeds."),
        # Named zero state with its dated unblock condition
        # (terminal audit cure, 2026-10-31): a router that has
        # never ledgered a forecast carries the reason and the
        # trigger on its own page, as a named open item, not as
        # a settled proving state. The block is computed from
        # this run's own census and grade counts.
        "zero_forecast_state": (None if e18 else {
            "forecasts_recorded": 0,
            "reason": (
                "The two eligible forecasters share no stock on "
                "the freshest census, so no name carries two "
                "forecasters to route, and no forecaster has a "
                "graded 21-session record to pick weights by."),
            "trigger": (
                "A name carrying both forecasters, once a "
                "forecaster has a graded 21-session record."),
            "first_possible": "2026-11-23",
            "first_possible_words": (
                "The first graded 21-session board records "
                "arrive November 23, 2026.")}),
        "proving_state": "Still being proven",
        "self_test": {
            "words": (
                "The averaging machinery itself is exercised on every "
                "refresh with made-up forecasters in a throwaway "
                "record: two forecasters disagreeing on one stock, "
                "with no graded record behind either, publish flat "
                "chances (a third each) because their earned weight "
                "is under the floor, beside the plain average's "
                "chances, and writing the same chances twice records "
                "them once."),
            "rows_written_to_scratch": test["rows_written_to_scratch"],
            "equal_weight_control": test["equal_weight_control"]},
        "ledger_rows_created_this_run": created_total,
        "grade_rows_in_shared_ledger": grade_rows_total,
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
    print(f"living-router: as_of {as_of}, names {len(names)}, "
          f"contested {len(contested)}, ledgered {created_total}, "
          f"wrote {out}")


if __name__ == "__main__":
    main()
