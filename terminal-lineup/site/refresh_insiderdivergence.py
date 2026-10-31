#!/usr/bin/env python3
"""Refresh the Insider-Flow Divergence forecaster (Forecast Engine 10).

=====================================================================
REGISTER TRIPLE (written before any computation)

1. EVIDENCE CLASS
   - Insider summaries: the Insider Wire page's record, gathered
     2026-10-26 from company ownership filings (the reports company
     officers and directors file when their holdings change),
     covering filings filed 2026-04-26 to 2026-10-26, up to the 20
     most recent filings per name, open-market buys and sells only.
     The grain is SUMMARY grain: per name, counts and dollar values
     of buys and sells and the latest filing date. There are no
     trader names and no per-trade dates, so every test below is
     measured at summary grain, across the whole record, exactly as
     the design states. Across the record: 18 buys against 326
     sells; that lopsided base rate is what any forecast here must
     beat, and it is printed on the page.
   - Options Heat: the heat score computed by the options-print
     tape machinery, per print, from 8 live parts (trade size,
     days to expiry, sweep, size against open interest and against
     the usual size, how far out of the money, and open interest
     against its usual level; a ninth vendor part is hard-coded to
     zero in the machinery and is not used). The score itself is
     NEVER redefined here. What this engine reads is only what the
     tape machinery stores per name per session: the sum of heat
     over the session's prints, the average heat, the print count,
     and the count of prints at or above the High Heat line.
   - The two families are independent by construction: company
     filings (one family) and options prints (another). This
     engine prices their DISAGREEMENT, and counts agreement only
     as the control group it is graded against.
   - This engine's own live record: none before today.

2. RECONSTRUCTION CHOICES (every constant named before computing)
   - The High Heat line: 15, the per-print line the tape machinery
     itself uses to band a print as high heat (the only top-band
     boundary anywhere in the record; no per-name bucket table
     exists). From the stored per-session counts alone, a name's
     Heat state for a session is registered as:
       TOP:    its tape card for that session counts at least one
               print at or above the High Heat line.
       COLD:   a tape card exists for that name and session AND it
               counts zero prints at or above the line.
       UNMEASURED: no tape card exists for that name and session.
     A name with no tape card is unmeasured, never cold: "Heat
     absent" means a real reading of zero hot prints, not a
     missing reading. Nothing is imputed: an index fund's Heat is
     never handed to a stock, and no Heat value is ever built from
     another family's data.
   - Insider legs, from a name's summary alone:
       HEAVY SELLING: sells count at least 1 AND sells count at
               least 10 times the buys count. (With zero buys, any
               positive sells count passes; the at-least-1 rule is
               what keeps the six names with no buys and no sells
               out of this leg, and it is coded explicitly.)
       BUY PRESENT: buys count at least 1.
       NEITHER: anything else, including no buys and no sells.
   - THE FORECASTS, per name carrying BOTH readings (an insider
     summary AND a tape card) for the same session window, graded
     at exactly 21 trading days after the fire session, the name's
     gain over those days measured against SPY's:
       ARM A (selling into heat): heavy selling AND Heat TOP ->
               the arm's average gain against SPY will be at most
               -1.5 points. Recorded estimate: -1.5.
       ARM B (quiet buying): buy present AND Heat COLD -> the
               arm's average gain against SPY will be at least
               +1.0 point. Recorded estimate: +1.0.
       CONTROL (agreement): both readings exist AND the pair is
               not a divergence: heavy selling with Heat COLD, or
               buy present with Heat TOP, or the insider leg is
               NEITHER (whatever the Heat state). Control cases are
               recorded the same way, with estimate 0.0, and graded
               identically; each arm is judged against the control.
   - Session pairing: the insider record is a single snapshot
     (gathered 2026-10-26); there is no per-session insider series.
     A session's arm tests pair that session's tape cards with the
     insider snapshot on record, and both dates are printed
     wherever the pairing is shown. A future fire pairs a later
     tape session with the snapshot then on record; the snapshot
     will need re-gathering as time passes, and its date rides on
     every recorded forecast's lineage.
   - Tape sessions: per session, the LAST tape summary run in the
     permanent log is the record (an early partial run on
     2026-10-26 is superseded by that evening's full run), the
     same rule the Intake-Bias engine uses.
   - History: every session on record is run through the same arm
     tests and shown labelled as history; history records nothing
     in advance (a forecast written after its window opened would
     break the record-before-display rule) and no history outcome
     is graded.
   - Grading note, stated like the earlier engines stated theirs:
     the shared grading runner cannot yet resolve a per-arm
     average 21-session gain-against-SPY outcome measured against
     a control group, and the price history on record ends
     2026-10-23, before every tape session, so no fire could grade
     until the price history extends 21 sessions past it.
   - Thin-cell rule: below 30 graded in any arm or the control,
     counts only, no average and no score is published from the
     record.
   - Kill criterion, from the design: after 60 fires in an arm,
     if that arm's average gain against SPY points the wrong way
     (Arm A not negative, Arm B not positive), that arm is
     retired.

   - FE23 adoption (DEEP-PASS 3.2 item 7, 2026-10-29): plan
     adjusted insider flow enters through a Form 4 footnote
     plan status classifier (site/engine_adaptations.py):
     discretionary flow discounted by the single non 10b5-1
     confidence multiplier, recency, and a positive only
     illiquidity damper. Its precision is tracked against a
     labelled footnote set under a registered kill floor
     (0.90 on at least 20 labelled footnotes). The insider
     record here is summary grain with no footnotes, so today
     nothing is classified and no leg is adjusted; the page
     data states that in its plan_adjustment block.

3. NON-CLAIMS
   - No name is ever given a Heat reading it does not have. The
     three index funds are the only names with tape cards today,
     and none of them is among the 50 names with insider records,
     so today the two families overlap on zero names. That empty
     overlap is the finding, printed with both coverages counted.
   - Insider buying is untested as a forecaster and Heat has never
     been graded as one; neither parent's reputation is borrowed.
   - Summary grain means this engine cannot see who traded or
     when inside the window; it claims nothing at finer grain.

=====================================================================
Behaviour: cross-checks the insider record's own totals against a
recount, the tape card file against the permanent log's freshest
run (heat sums, averages, hot-print counts, print counts), and the
forecast ledger's chain, failing closed on any disagreement; runs
the history check over every session on record; runs today's arm
tests over the real overlap and appends any genuine fires (both
arms and the control) through the forecast machinery API only;
exercises the arm tests on made-up records in memory on every run
so the tests are proven even while the real overlap is empty;
writes data.json. All timestamps come from the sources, never the
clock, so reruns are idempotent.

Usage: python3 refresh_insiderdivergence.py
"""

import json
import os
import sys
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
MORGUE = os.path.expanduser("~/workspace/morgue")
LOG_PATH = os.path.join(MORGUE, "output", "ledger.jsonl")
TAPE_CARD_PATH = os.path.join(MORGUE, "output", "tape_card.json")
# Hookup 2026-10-30: the per-name tape store is the second heat
# source. The tape family now cards heat for every tracked name, not
# only the three index funds, and this engine's tests pair those
# readings with the same insider snapshot. The two aggregations are
# NOT merged: the index cards and the per-name store count prints
# differently (checked 2026-10-30: SPY 455,245 card prints against
# 380,438 store prints for the same session), so each source keeps
# its own session row and its own lineage, and an index fund's card
# reading is never substituted for its store reading.
PERNAME_TAPE_DIR = os.path.join(MORGUE, "state", "morgue",
                                "pername_tape")
INSIDER_PATH = os.path.join(HERE, "insider-wire", "data.json")
PANEL_PATH = os.path.join(MORGUE, "data_cache", "board_bt_bars.json")
FORECAST_DIR = os.path.expanduser("~/workspace/terminal-lineup/forecast")
OUT_PATH = os.path.join(HERE, "insider-divergence", "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import attestation_block as _ab
except ImportError:  # refresh stays runnable standalone
    _ab = None

import importlib.util  # noqa: E402


def _load(mod_name, path):
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_adapt = _load("engine_adaptations_mod10",
               os.path.join(HERE, "engine_adaptations.py"))
_forecast_ledger = _load("forecast_ledger_mod",
                         os.path.join(FORECAST_DIR, "ledger.py"))
_forecast_registry = _load("forecast_registry_mod",
                           os.path.join(FORECAST_DIR, "registry.py"))
Ledger = _forecast_ledger.Ledger
file_sha256 = _forecast_ledger.file_sha256
Registry = _forecast_registry.Registry

ENGINE_ID = "engine_10"
TAPE_NAMES = ["SPY", "QQQ", "IWM"]
HIGH_HEAT_LINE = 15
ARM_A_ESTIMATE = -1.5
ARM_B_ESTIMATE = 1.0
CONTROL_ESTIMATE = 0.0
HORIZON = 21
THIN = 30
KILL_FIRES = 60

SOURCE_WORDS = ("Company ownership filings gathered on October 26, "
                "2026, and the daily options-print tape summaries")


def fail(message):
    print(f"Insider-Divergence refresh: {message}", file=sys.stderr)
    return 1


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def weekdays_after(start_iso, count):
    d = date.fromisoformat(start_iso) + timedelta(days=1)
    out = []
    while len(out) < count:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def insider_leg(summary):
    """summary: {'buys': n, 'sells': n} or None."""
    if summary is None:
        return "no_summary"
    buys, sells = summary["buys"], summary["sells"]
    if sells >= 1 and sells >= 10 * buys:
        return "heavy_selling"
    if buys >= 1:
        return "buy_present"
    return "neither"


def heat_state(tape_row):
    """tape_row: the stored per-session aggregates or None."""
    if tape_row is None:
        return "unmeasured"
    return "top" if tape_row["high_heat"] >= 1 else "cold"


def classify(summary, tape_row):
    """The registered arm tests. Returns 'arm_a', 'arm_b',
    'control', or None when the pair cannot be tested at all."""
    if summary is None or tape_row is None:
        return None
    leg = insider_leg(summary)
    heat = heat_state(tape_row)
    if leg == "heavy_selling" and heat == "top":
        return "arm_a"
    if leg == "buy_present" and heat == "cold":
        return "arm_b"
    return "control"


FOOTNOTE_RECORD_PATH = os.path.join(
    HERE, "insider-divergence", "footnotes", "record.json")


def _footnote_record():
    try:
        with open(FOOTNOTE_RECORD_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def plan_adjustment_block(summaries):
    """FE23 plan adjusted insider flow (DEEP-PASS 3.2 item 7).
    Publication cure 2026-10-30: the Form 4 footnote record now
    exists (form4_footnotes.py, EDGAR ownership XML for the
    tracked universe). When it is on disk, sales are classified
    from the footnote texts their own transactions reference, a
    filing with no footnotes stays unknown, and precision is
    measured against the record's labelled set (labels read off
    the raw filing text by an independent rule) under the
    registered kill floor. Without the record, the honest
    not_recorded block below stands."""
    rec = _footnote_record()
    if rec.get("filings"):
        _a = _adapt
        classified = {}
        for filing in rec["filings"]:
            for txn in filing.get("transactions", []):
                for text in txn.get("footnote_texts", []):
                    got = _a.classify_plan_status(text)
                    if got["label"] != "unknown":
                        classified.setdefault(
                            filing["symbol"], []).append(
                            got["label"])
        labelled = [tuple(x) for x in rec.get("labelled", [])]
        precision = _a.classifier_precision(labelled)
        state = _a.classifier_kill_state(precision)
        return {
            "state": "recorded" if state == "standing"
                     else state,
            "classifier": "form4_footnote_plan_status_v1",
            "precision": precision,
            "precision_kill_floor":
                _a.PLAN_CLASSIFIER_PRECISION_FLOOR,
            "classifier_state": state,
            "names_with_summaries": len(summaries),
            "names_classified": len(classified),
            "classified": {k: {"plan_10b5_1": v.count(
                                   "plan_10b5_1"),
                               "discretionary": v.count(
                                   "discretionary")}
                           for k, v in sorted(
                               classified.items())},
            "footnote_record": {
                "filings_on_record": rec.get(
                    "filings_on_record"),
                "window_since": rec.get("window_since"),
                "updated_ts": rec.get("updated_ts")},
            "detail": ("Plan status is now read from Form 4 "
                       "footnote text on record "
                       "(form4_footnotes.py, EDGAR ownership "
                       "XML): each classified name's sales were "
                       "matched to the footnotes their own "
                       "transactions reference, and a filing "
                       "with no footnotes stays unknown, never "
                       "discretionary by default. Precision is "
                       "measured against the record's labelled "
                       "footnotes, labelled off the raw filing "
                       "text by an independent literal rule, "
                       "under the registered 0.90 floor on at "
                       "least 20 labelled footnotes.")}
    precision = _adapt.classifier_precision([])
    return {
        "state": "not_recorded",
        "classifier": "form4_footnote_plan_status_v1",
        "precision": precision,
        "precision_kill_floor":
            _adapt.PLAN_CLASSIFIER_PRECISION_FLOOR,
        "classifier_state": _adapt.classifier_kill_state(
            precision),
        "names_with_summaries": len(summaries),
        "names_classified": 0,
        "detail": ("Insider flow here is raw: the record "
                   "carries counts and dollar values only, "
                   "with no Form 4 footnote text on disk yet, "
                   "and whether a sale ran under a 10b5-1 plan "
                   "is stated only in those footnotes. Until "
                   "the footnote record lands, no name is "
                   "classified and no arm leg is changed by "
                   "plan status.")}


def self_test():
    """Exercise the arm tests on made-up records, in memory only.
    Proves each branch of the registered tests fires as written,
    including the two ways a pair must NOT fire."""
    cases = [
        ({"buys": 0, "sells": 9}, {"high_heat": 3}, "arm_a"),
        ({"buys": 1, "sells": 12}, {"high_heat": 1}, "arm_a"),
        ({"buys": 4, "sells": 1}, {"high_heat": 0}, "arm_b"),
        ({"buys": 1, "sells": 0}, {"high_heat": 0}, "arm_b"),
        ({"buys": 0, "sells": 9}, {"high_heat": 0}, "control"),
        ({"buys": 4, "sells": 1}, {"high_heat": 5}, "control"),
        ({"buys": 0, "sells": 0}, {"high_heat": 5}, "control"),
        ({"buys": 0, "sells": 0}, {"high_heat": 0}, "control"),
        ({"buys": 11, "sells": 10}, {"high_heat": 0}, "arm_b"),
        ({"buys": 0, "sells": 9}, None, None),
        (None, {"high_heat": 3}, None),
        ({"buys": 2, "sells": 19}, {"high_heat": 2}, "control"),
    ]
    passed = 0
    for summary, tape_row, want in cases:
        if classify(summary, tape_row) == want:
            passed += 1
    return {"cases": len(cases), "passed": passed,
            "ok": passed == len(cases)}


def load_pername_session():
    """The freshest per-name tape store, cross-checked against its
    own records. Returns (session, generated_at_utc, path,
    {symbol: {heat_sum, mean_heat, high_heat, prints, run_ts}}), or
    None when no store is on record. Raises ValueError when a store
    is present but disagrees with itself."""
    if not os.path.isdir(PERNAME_TAPE_DIR):
        return None
    files = sorted(f for f in os.listdir(PERNAME_TAPE_DIR)
                   if f.endswith(".json"))
    if not files:
        return None
    path = os.path.join(PERNAME_TAPE_DIR, files[-1])
    with open(path, "r", encoding="utf-8") as fh:
        store = json.load(fh)
    session = store["session"]
    if os.path.basename(path) != session + ".json":
        raise ValueError("the per-name tape store's file name "
                         "disagrees with the session inside it")
    if store.get("direction_basis") != \
            "unjudged_no_print_time_quote":
        raise ValueError("the per-name tape store does not carry "
                         "its expected unjudged direction basis")
    tape = {}
    for sym, e in sorted(store["names"].items()):
        # The store carries aggregates, not prints, so the checks
        # are its own consistency fields: a name whose fetch was
        # capped is marked incomplete by the store itself and is
        # unmeasured here, never read from partial prints; a
        # complete name's mean heat must reconcile with its heat
        # sum over its print count.
        if e.get("completeness") != "complete":
            continue
        if e["prints"] > 0 and abs(
                e["mean_heat"] - e["heat_sum"] / e["prints"]) > 0.011:
            raise ValueError(f"the per-name tape store's {sym} "
                             "mean heat disagrees with its own "
                             "heat sum and print count")
        if e["prints"] == 0 and e["heat_sum"] != 0:
            raise ValueError(f"the per-name tape store's {sym} "
                             "carries heat with no prints")
        tape[sym] = {"heat_sum": e["heat_sum"],
                     "mean_heat": e["mean_heat"],
                     "high_heat": e["high_heat"],
                     "prints": e["prints"],
                     "run_ts": store["generated_at_utc"]}
    return session, store["generated_at_utc"], path, tape


def build():
    for path in (LOG_PATH, TAPE_CARD_PATH, INSIDER_PATH, PANEL_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    with open(LOG_PATH, encoding="utf-8") as fh:
        log_rows = [json.loads(line) for line in fh if line.strip()]
    tape_card = load_json(TAPE_CARD_PATH)
    insider = load_json(INSIDER_PATH)
    panel = load_json(PANEL_PATH)
    panel_last = panel["SPY"][-1][0]

    # ---- Insider record: recount must agree with its own totals
    summaries = {}
    not_on_record = []
    for entry in insider["names"]:
        if entry.get("state") == "summary" and entry.get("summary"):
            s = entry["summary"]
            summaries[entry["symbol"]] = {
                "buys": s["buys"]["count"], "sells": s["sells"]["count"],
                "buys_value": s["buys"]["value_usd"],
                "sells_value": s["sells"]["value_usd"],
                "latest_filing_date": s["latest_filing_date"]}
        else:
            not_on_record.append(entry["symbol"])
    totals = insider["totals"]
    recount_buys = sum(v["buys"] for v in summaries.values())
    recount_sells = sum(v["sells"] for v in summaries.values())
    if recount_buys != totals["open_buys"] or \
            recount_sells != totals["open_sells"] or \
            len(summaries) != totals["names_with_summary"] or \
            len(insider["names"]) != totals["names_covered"] or \
            len(not_on_record) != totals["names_not_on_record"]:
        return fail("the insider record's totals disagree with a "
                    "recount of its own names")
    insider_as_of = insider["as_of"]

    legs = {}
    for sym, s in summaries.items():
        legs[sym] = insider_leg(s)
    arm_a_eligible = sorted(s for s in summaries
                            if legs[s] == "heavy_selling")
    arm_b_eligible = sorted(s for s in summaries
                            if legs[s] == "buy_present")
    neither = sorted(s for s in summaries if legs[s] == "neither")

    # ---- Tape sessions: last summary run per session is the record
    runs = {}
    for r in log_rows:
        if r.get("component") == "tape-aggregate":
            v = r["value"]
            runs.setdefault(r["ts_utc"][:10], {})[v["underlying"]] = (
                r["ts_utc"], v)
    sessions = {}
    for day, per_name in runs.items():
        if set(per_name) != set(TAPE_NAMES):
            return fail(f"tape session {day} does not carry exactly "
                        "the three index funds")
        sessions[day] = {}
        for sym, (ts, v) in per_name.items():
            sessions[day][sym] = {
                "heat_sum": v["heat_sum"], "mean_heat": v["mean_heat"],
                "high_heat": v["high_heat"], "prints": v["prints"],
                "run_ts": ts}
    if not sessions:
        return fail("the permanent log holds no tape summary runs")
    freshest_day = max(sessions)

    # ---- The tape card file must agree with the freshest run
    card_by_sym = {c["underlying"]: c for c in tape_card["cards"]}
    if set(card_by_sym) != set(TAPE_NAMES):
        return fail("the tape card file does not carry exactly the "
                    "three index funds")
    for sym in TAPE_NAMES:
        c, s = card_by_sym[sym], sessions[freshest_day][sym]
        if c["heat_sum"] != s["heat_sum"] or \
                c["high_heat"] != s["high_heat"] or \
                c["prints"] != s["prints"] or \
                abs(c["mean_heat"] - s["mean_heat"]) > 0.011:
            return fail(f"the tape card file's {sym} heat readings "
                        "disagree with the permanent log's freshest "
                        "run")

    # ---- The per-name tape store: a second heat source, kept apart
    try:
        pername = load_pername_session()
    except (ValueError, KeyError) as exc:
        return fail(str(exc))
    pername_day = pername_tape = pername_path = None
    pername_generated = None
    if pername is not None:
        (pername_day, pername_generated, pername_path,
         pername_tape) = pername

    # ---- Arm tests over every session on record (history + today)
    def run_session(day, tape_map=None):
        tape = sessions[day] if tape_map is None else tape_map
        overlap = sorted(set(summaries) & set(tape))
        out = {"session": day, "overlap": overlap,
               "arm_a": [], "arm_b": [], "control": []}
        for sym in overlap:
            cell = classify(summaries[sym], tape[sym])
            if cell:
                out[cell].append(sym)
        return out

    session_rows = [run_session(day) for day in sorted(sessions)]
    history_rows = session_rows[:-1]
    today = session_rows[-1]
    pername_row = None
    if pername_tape is not None:
        pername_row = run_session(pername_day, pername_tape)
        pername_row["source"] = "per-name tape store"
    if today["session"] != freshest_day:
        return fail("internal ordering error on sessions")
    heat_names = sorted({sym for day in sessions
                         for sym in sessions[day]})

    test = self_test()
    if not test["ok"]:
        return fail("the arm tests failed their own exercise: "
                    f"{test['passed']} of {test['cases']}")

    # ---- Record any genuine fires, machinery API only
    registry = Registry()
    ledger = Ledger(os.path.join(FORECAST_DIR, "ledger.jsonl"),
                    registry=registry)
    if not ledger.verify_chain():
        return fail("the forecast ledger's chain does not verify")
    lineage = {
        "source_artifacts": [
            {"path": p, "sha256": file_sha256(p)}
            for p in (INSIDER_PATH, LOG_PATH, TAPE_CARD_PATH,
                      PANEL_PATH)],
        "note": ("Freshest tape session's arm tests over the names "
                 "carrying both an insider summary and a tape card; "
                 f"insider snapshot gathered {insider_as_of}."),
        "clocks": {
            "event_time": sessions[freshest_day]["SPY"]["run_ts"],
            "publication_time": tape_card["generated_at_utc"],
            "first_available_time":
                sessions[freshest_day]["SPY"]["run_ts"],
            "ingestion_time": tape_card["generated_at_utc"],
            "decision_as_of": freshest_day,
        },
    }
    horizon = weekdays_after(freshest_day, HORIZON)
    cell_specs = [
        ("arm_a", ARM_A_ESTIMATE,
         "Arm A (insiders selling heavily while options heat is at "
         "its top): 21-session gain against SPY, in points"),
        ("arm_b", ARM_B_ESTIMATE,
         "Arm B (an insider buy while options heat is cold): "
         "21-session gain against SPY, in points"),
        ("control", CONTROL_ESTIMATE,
         "Control (both readings present, no disagreement): "
         "21-session gain against SPY, in points"),
    ]
    def record_cells(day, tape_map, row_result, issued_ts, lin,
                     heat_source):
        hz = weekdays_after(day, HORIZON)
        made = 0
        for cell, estimate, quantity in cell_specs:
            for sym in row_result[cell]:
                _row, created = ledger.append_forecast_declared(
                    engine_id=ENGINE_ID, issued_ts=issued_ts,
                    subject=sym, quantity=quantity,
                    value={"estimate": estimate, "cell": cell,
                           "insider_buys": summaries[sym]["buys"],
                           "insider_sells": summaries[sym]["sells"],
                           "heat_state": heat_state(tape_map[sym]),
                           "high_heat_prints":
                               tape_map[sym]["high_heat"],
                           "heat_source": heat_source,
                           "insider_as_of": insider_as_of},
                    horizon_open=hz[0], horizon_close=hz[-1],
                    lineage=lin,
                    families=["filings_positioning",
                              "options_prints"],
                    outcome={"symbol": sym, "kind": "excess_21s",
                             "benchmark": "SPY", "base_date": day,
                             "at_date": hz[-1], "cell": cell})
                made += int(created)
        return made

    created_total = record_cells(
        freshest_day, sessions[freshest_day], today,
        sessions[freshest_day]["SPY"]["run_ts"], lineage,
        "index tape cards")
    if pername_row is not None:
        pn_lineage = {
            "source_artifacts": [
                {"path": p, "sha256": file_sha256(p)}
                for p in (INSIDER_PATH, pername_path, PANEL_PATH)],
            "note": ("Per-name tape store session's arm tests over "
                     "the names carrying both an insider summary "
                     "and a per-name heat reading; insider snapshot "
                     f"gathered {insider_as_of}."),
            "clocks": {
                "event_time": pername_generated,
                "publication_time": pername_generated,
                "first_available_time": pername_generated,
                "ingestion_time": pername_generated,
                "decision_as_of": pername_day},
        }
        created_total += record_cells(
            pername_day, pername_tape, pername_row,
            pername_generated, pn_lineage, "per-name tape store")
    if not ledger.verify_chain():
        return fail("the forecast ledger's chain broke during append")

    recorded = graded = 0
    fires = {"arm_a": 0, "arm_b": 0, "control": 0}
    for row in ledger.rows():
        if row.get("engine_id") != ENGINE_ID:
            continue
        if row.get("type") == "forecast":
            recorded += 1
            cell = (row.get("value") or {}).get("cell")
            if cell in fires:
                fires[cell] += 1
        if row.get("type") == "grade":
            graded += 1

    heat_sessions = [{
        "session": day,
        "names": [{"symbol": sym,
                   "mean_heat": sessions[day][sym]["mean_heat"],
                   "high_heat_prints": sessions[day][sym]["high_heat"],
                   "prints": sessions[day][sym]["prints"],
                   "heat_state": heat_state(sessions[day][sym])}
                  for sym in TAPE_NAMES]}
        for day in sorted(sessions)]

    data = {
        "tool": "Insider-Flow Divergence",
        "state": "proving",
        "waiting": True,
        "source": SOURCE_WORDS,
        "published_at_utc": tape_card["generated_at_utc"],
        "panel_last_session": panel_last,
        "coverage": {
            "insider": {
                "tracked": len(insider["names"]),
                "with_summary": len(summaries),
                "not_on_record": not_on_record,
                "as_of": insider_as_of,
                "window": insider["window"],
                "total_buys": recount_buys,
                "total_sells": recount_sells,
                "note": ("Each summary holds counts and dollar "
                         "amounts of company insiders' open-market "
                         "buys and sells over the window. It does "
                         "not say who traded or on which day, so "
                         "the tests here work at that whole-record "
                         "grain, exactly as designed.")},
            "heat": {
                "names": heat_names,
                "sessions_on_record": len(sessions),
                "sessions": heat_sessions,
                "pername_session": pername_day,
                "pername_names": (sorted(pername_tape)
                                  if pername_tape else []),
                "pername_names_count": (len(pername_tape)
                                        if pername_tape else 0),
                "note": ("Options heat is carded for the three "
                         "index funds on every session on record. "
                         + (f"The per-name tape store also cards "
                            f"heat for {len(pername_tape)} names "
                            f"for {pername_day}, each name's own "
                            "reading from its own prints. The two "
                            "aggregations count prints differently "
                            "and are kept apart; an index fund's "
                            "card reading is never handed to a "
                            "stock, and no reading is ever "
                            "substituted for another."
                            if pername_tape else
                            "No per-name tape store is on record "
                            "yet, so no stock carries a heat "
                            "reading."))},
            "both": len(today["overlap"]),
            "both_pername": (len(pername_row["overlap"])
                             if pername_row else 0),
            "both_note": (
                (f"On the index cards, no name carries both "
                 f"readings: the three funds with card readings are "
                 f"not among the names with insider records. On "
                 f"the per-name store for {pername_day}, "
                 f"{len(pername_row['overlap'])} names carry both "
                 f"readings, and those are the names the arm tests "
                 f"below ran on.")
                if pername_row and pername_row["overlap"] else
                ("No name carries both readings on either heat "
                 "source. The three funds with card readings are "
                 "not among the names with insider records, and "
                 "the per-name store's names do not overlap the "
                 "insider record either."
                 if pername_row else
                 "No name carries both readings, today or on any "
                 "session on record. The three funds with heat "
                 "readings are not among the names with insider "
                 "records at all."))},
        "plan_adjustment": plan_adjustment_block(summaries),
        "insider_legs": {
            "arm_a_eligible": arm_a_eligible,
            "arm_a_count": len(arm_a_eligible),
            "arm_b_eligible": [
                {"symbol": s, "buys": summaries[s]["buys"],
                 "sells": summaries[s]["sells"]}
                for s in arm_b_eligible],
            "arm_b_count": len(arm_b_eligible),
            "neither_count": len(neither),
            "neither_note": ("The remaining names with summaries "
                             "show no buys and no sells at all, so "
                             "neither side of the test can start "
                             "from them.")},
        "forecast": {
            "arm_a": ("Arm A: in a name where insiders have sold "
                      "heavily (at least 10 sales for every buy "
                      "across the record) while options trading is "
                      "at its hottest, the name will trail SPY by "
                      "an average of at least 1.5 points over the "
                      "next 21 trading days."),
            "arm_b": ("Arm B: in a name where an insider buy is on "
                      "record while options trading is cold, the "
                      "name will beat SPY by an average of at "
                      "least 1.0 point over the next 21 trading "
                      "days."),
            "control": ("Names carrying both readings where the "
                        "two agree, or where neither side of the "
                        "insider test is triggered, are recorded "
                        "as the comparison group and graded the "
                        "same way. Each arm has to beat that group, "
                        "not just the market."),
            "heat_states": ("A name's heat for a session is at its "
                            "top when at least one of its options "
                            "trades that session scored at or above "
                            "the tape's own High Heat line of 15. "
                            "It is cold only when the name was "
                            "actually measured that session and no "
                            "trade reached the line. A name that was "
                            "not measured is unmeasured, never "
                            "cold.")},
        "today": {
            "session": freshest_day,
            "insider_as_of": insider_as_of,
            "overlap": today["overlap"],
            "arm_a": today["arm_a"], "arm_b": today["arm_b"],
            "control": today["control"],
            "fires": len(today["arm_a"]) + len(today["arm_b"]) +
                     len(today["control"]),
            "reason": ("No name carries both readings, so no test "
                       "could run on any name and nothing was "
                       "recorded. Zero is the count, not a gap in "
                       "the page.")},
        "pername_today": (None if pername_row is None else {
            "session": pername_day,
            "insider_as_of": insider_as_of,
            "overlap": pername_row["overlap"],
            "arm_a": pername_row["arm_a"],
            "arm_b": pername_row["arm_b"],
            "control": pername_row["control"],
            "fires": (len(pername_row["arm_a"]) +
                      len(pername_row["arm_b"]) +
                      len(pername_row["control"])),
            "reason": (
                (f"{len(pername_row['overlap'])} names carry both "
                 f"an insider summary and a per-name heat reading "
                 f"for {pername_day}. Every one of them was "
                 f"tested and recorded in the forecast ledger "
                 f"under its own arm, graded 21 sessions out "
                 f"against SPY.")
                if pername_row["overlap"] else
                ("The per-name store's names do not overlap the "
                 "insider record, so no test could run from this "
                 "source either."))}),
        "history": {
            "label": "History: the sessions on record, worked out "
                     "after the fact and recorded nowhere in "
                     "advance",
            "sessions": (history_rows + [today] +
                         ([pername_row] if pername_row else [])),
            "would_have": {
                "arm_a": sum(len(s["arm_a"]) for s in
                             session_rows + ([pername_row]
                                             if pername_row
                                             else [])),
                "arm_b": sum(len(s["arm_b"]) for s in
                             session_rows + ([pername_row]
                                             if pername_row
                                             else [])),
                "control": sum(len(s["control"]) for s in
                               session_rows + ([pername_row]
                                               if pername_row
                                               else [])),
                "sessions_on_record": (len(session_rows) +
                                       (1 if pername_row else 0))},
            "note": ("On every index-card session on record the "
                     "overlap was empty, so no card session would "
                     "have fired. The insider side alone was ready: "
                     f"{len(arm_a_eligible)} names met Arm A's "
                     "selling test and "
                     f"{len(arm_b_eligible)} met Arm B's buying "
                     "test. "
                     + (f"The per-name store session "
                        f"{pername_day} is the first session where "
                        f"the second reading exists for those same "
                        f"names: {len(pername_row['overlap'])} "
                        f"names carried both readings and were "
                        f"tested for real, and their forecasts are "
                        f"in the ledger, not in this after-the-fact "
                        f"table."
                        if pername_row and pername_row["overlap"]
                        else
                        "Only the missing second reading, a heat "
                        "reading for those same names, kept every "
                        "one of them from being tested."))},
        "self_test": {
            "cases": test["cases"], "passed": test["passed"],
            "note": ("On every run, the two tests and the "
                     "comparison-group rule are also exercised on "
                     "made-up records in memory, covering each way "
                     "a name can land and the two ways it must not "
                     "fire (no insider record, or no heat reading). "
                     "All cases passed on this run. Made-up records "
                     "are never written to the record of real "
                     "forecasts.")},
        "live": {"forecasts_recorded": recorded,
                 "forecasts_graded": graded,
                 "arm_a_fires": fires["arm_a"],
                 "arm_b_fires": fires["arm_b"],
                 "control_recorded": fires["control"],
                 "target_per_arm": KILL_FIRES},
        "kill_criterion": (
            "After 60 fires in either arm, that arm is retired if "
            "its average gain against SPY points the wrong way: "
            "Arm A must average below SPY, Arm B must average above "
            "it. An arm that points the wrong way at 60 fires is "
            "finished, with its record left standing."),
        "thin_rule": ("Below 30 graded in any group, counts only: "
                      "no average and no score is drawn from a "
                      "handful of tests."),
        "grading_note": ("Grading waits on the calendar, stated "
                         "plainly: the shared grading machinery "
                         "scores this kind of 21-day gain against "
                         "SPY directly (the excess_21s resolver, "
                         "wired 2026-10-30), each arm is judged "
                         "against the comparison group once 30 in "
                         "a group have graded, and the price "
                         "history on record ends "
                         f"{panel_last}, before every "
                         "tape session on record, so no 21-day "
                         "window after a fire exists yet either."),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    pn_fires = (len(pername_row["arm_a"]) + len(pername_row["arm_b"])
                + len(pername_row["control"])) if pername_row else 0
    print(f"Wrote {OUT_PATH} (insider {len(summaries)} of "
          f"{len(insider['names'])} as of {insider_as_of}; heat "
          f"{len(heat_names)} names x {len(sessions)} sessions; "
          f"overlap {len(today['overlap'])}; today "
          f"{freshest_day}: 0 fires; per-name {pername_day}: "
          f"{pn_fires} fires; {created_total} new forecasts, "
          f"{recorded} recorded in total)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
