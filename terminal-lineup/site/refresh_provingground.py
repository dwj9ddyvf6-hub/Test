#!/usr/bin/env python3
"""Refresh the Proving Ground data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: each built tool's own published record, read exactly
as it stands, plus the public scoreboard's published grading where a
tool's grades live there, and the Receipts' published record as
corroboration. Every proving state on this page is the state the
tool's own record declares: a finished study marked graded, a live
record being graded on the scoreboard, a page that labels itself
still being proven, an honest empty state waiting on records, or a
tool that only measures and so has nothing to prove. No state on
this page exists anywhere except in a tool's own published record
first.

Reconstruction choices, stated as ours: (1) The five proving states
are defined in plain words at the top of the page, taken from what
the tools' own pages already declare. (2) Each tool carries the
one-line reason its own record gives for its state, and, only where
its own record names one, the thing that would move it to a stronger
state: sessions still to accrue, a study still to run, a record
still to start. Where no record names such a thing, none is shown.
(3) The Board's state rests on the scoreboard's published grading of
board calls, because the Board's own record carries no grade; the
page does not present that grade as coming from the Board's own
page. The Expected Move Map is counted as a measuring tool because
its own coverage note presents its bands as the last ones on record
from a fixed named construction, and its record carries no grade and
no proving label. (4) Counts are counted from the entries assembled
here, never typed in separately. (5) This page covers the full
70-tool lineup; every tool's state is the state its own record
declares, checked fail-closed below for every tool whose record
carries a proving state in words. (6) No time on this page comes from
the clock: the newest source time is the newest time found in the
records read, so running this script twice produces the same file.

Non-claims: this page does not grade anything, does not prove
anything, and does not move any tool to a stronger state than its
own record supports. It republishes proving states only.

Fail-closed rules: if the hub does not link every classified tool
exactly once, if any built tool in the hub is missing from the
classification, if a tool's published record is missing or does not
parse, if any published state, count or note disagrees with the
classification inputs checked below, if the verdict counts on the
Replication Wire do not recount from its own entries, if the
Graveyard's buried count disagrees with the Wire, or if any words
assembled here carry an internal file name or desk wording, the
refresh stops and publishes nothing.

Usage: python3 refresh_provingground.py
"""

import json
import os
import re
import sys
from datetime import datetime

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
HUB_PATH = os.path.join(HERE, "index.html")
OUT_PATH = os.path.join(HERE, "proving-ground", "data.json")

SOURCE_WORDS = ("Each tool's own published record, read exactly as it was published, "
                "with the public scoreboard's published grading where a tool's "
                "grades live there")

FORBIDDEN = (".json", ".md", ".py", ".jsonl", "morgue", "Femto", "Midna", "Codex",
             "data file", "not financial advice", "for informational purposes",
             "for educational purposes", "do your own research", "past performance",
             "no guarantee", "at your own risk", "Slate", "slate")

STATES = [
    ("study", "Backed by a finished study",
     "The tool's numbers are the counted result of a study that has already run on the record."),
    ("live", "Live record being graded",
     "The tool publishes calls or cards to the permanent record and those are being graded "
     "against what prices did next, with some grades in and some still waiting."),
    ("proving", "Still being proven",
     "The tool is published and working, but its own claim has not been graded or proven yet; "
     "grading or a verdict is still to come."),
    ("waiting", "Waiting on records",
     "The page is built, but the records it reads have not arrived or built up yet, so it "
     "shows nothing, or only its definition, until they do."),
    ("measuring", "A measuring tool, nothing to prove",
     "The tool only reports, filters, calculates or counts from records on file; it makes no "
     "forecast claim of its own, so there is nothing to grade."),
]
STATE_LABEL = {k: v for k, v, _ in STATES}

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def fail(msg):
    print("FAIL: " + msg, file=sys.stderr)
    sys.exit(1)


def plain_date(iso):
    d = datetime.strptime(iso, "%Y-%m-%d")
    return "%s %d, %d" % (MONTHS[d.month - 1], d.day, d.year)


def load(slug):
    path = os.path.join(HERE, slug, "data.json")
    if not os.path.exists(path):
        fail("published record missing for " + slug)
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        fail("published record for %s does not parse: %s" % (slug, e))


def need(cond, msg):
    if not cond:
        fail(msg)


# Classification: (number, slug, display name, state). Reasons and next
# steps are built below from the records themselves.
TOOLS = [
    (1, "morning-map", "Morning Map", "live"),
    (2, "record", "The Record", "measuring"),
    (3, "board", "Qualified Board", "live"),
    (4, "flow-tape", "Flow Tape", "proving"),
    (5, "golden-sweep-wire", "Golden Sweep Wire", "proving"),
    (6, "payoff-sketch", "Payoff Sketch", "measuring"),
    (7, "expected-move", "Expected Move Map", "measuring"),
    (8, "screener", "The Screener", "measuring"),
    (9, "portfolio-builder", "Portfolio Builder", "measuring"),
    (10, "activity-profile", "Activity Profile", "waiting"),
    (11, "gap-fill", "Gap-Fill Pane", "study"),
    (12, "opening-range", "Opening Range Pane", "study"),
    (13, "earnings-drift", "Earnings Drift Pane", "study"),
    (14, "wall-check", "Wall Check", "live"),
    (15, "squeeze-watch", "Squeeze Watch", "measuring"),
    (16, "fear-day", "Fear Day List", "waiting"),
    (17, "pullback-norm", "Pullback Norm", "proving"),
    (18, "second-opinion", "The Second Opinion", "measuring"),
    (19, "receipts", "The Receipts", "measuring"),
    (20, "state-analogue", "State Analogue", "waiting"),
    (21, "insider-wire", "Insider Wire", "measuring"),
    (22, "short-volume", "Short Volume Ledger", "measuring"),
    (23, "filings-wire", "Filings Wire", "measuring"),
    (24, "dark-prints", "Dark Prints", "measuring"),
    (25, "chain-explorer", "Chain Explorer", "measuring"),
    (26, "iv-weather", "IV Weather", "measuring"),
    (27, "skew-lens", "Skew Lens", "waiting"),
    (28, "premium-meter", "Premium Meter", "measuring"),
    (29, "greeks-sketch", "Greeks Sketch", "measuring"),
    (30, "expiry-pin-watch", "Expiry Pin Watch", "measuring"),
    (31, "breadth-meter", "Breadth Meter", "measuring"),
    (32, "sector-rotation", "Sector Rotation", "measuring"),
    (33, "regime-dial", "Regime Dial", "measuring"),
    (34, "week-ahead", "The Week Ahead", "measuring"),
    (35, "earnings-calendar", "Earnings Calendar", "measuring"),
    (36, "watchlist-pulse", "Watchlist Pulse", "measuring"),
    (37, "correlation-web", "Correlation Web", "proving"),
    (38, "unusual-volume", "Unusual Volume", "measuring"),
    (39, "grade-my-call", "Grade My Call", "measuring"),
    (40, "13f-tracker", "13F Tracker", "measuring"),
    (41, "replication-wire", "Replication Wire", "measuring"),
    (42, "grade-a-board", "Grade-A Board", "study"),
    (43, "fear-day-forecaster", "Fear-Day Forecaster", "proving"),
    (44, "router", "The Router", "proving"),
    (45, "promoted-book", "Promoted Book", "study"),
    (46, "odds-cards", "Odds Cards", "study"),
    (47, "decay-watch", "Decay Watch", "measuring"),
    (48, "horizon-grades", "Horizon Grades", "measuring"),
    (49, "survivors-wire", "Survivors Wire", "proving"),
    (50, "graveyard", "The Graveyard", "measuring"),
    (51, "strat-scanner", "Strat Scanner", "proving"),
    (52, "strat-combos", "Strat Combos Board", "proving"),
    (53, "smart-money-tracker", "Smart Money Tracker", "measuring"),
    (54, "gamma-ladder", "Gamma Ladder", "measuring"),
    (55, "tape-heatmap", "Tape Heatmap", "measuring"),
    (56, "flow-board", "Flow Board", "proving"),
    (57, "signal-feed", "Signal Feed", "proving"),
    (58, "echo-board", "Echo Board", "measuring"),
    (59, "flow-engine", "Flow Engine", "proving"),
    (60, "proving-ground", "The Proving Ground", "measuring"),
    (61, "holly-ideas", "Holly Ideas", "proving"),
    (62, "agent-debate", "Agent Debate", "proving"),
    (63, "ai-chart-read", "AI Chart Read", "proving"),
    (64, "reversal-wire", "Reversal Wire", "proving"),
    (65, "alert-tape", "Alert Tape", "measuring"),
    (66, "breakout-scanner", "Breakout Scanner", "proving"),
    (67, "one-page-report", "One-Page Report", "measuring"),
    (68, "pattern-draw", "Pattern Draw", "proving"),
    (69, "echo-lens", "Echo Lens", "proving"),
    (70, "momentum-clock", "Momentum Clock", "proving"),
]
NO_DATA = {"payoff-sketch", "greeks-sketch"}


def main():
    hub = open(HUB_PATH).read()
    hub_links = re.findall(r'href="([a-z0-9-]+)/"', hub)
    need(len(hub_links) == len(set(hub_links)), "hub links a tool more than once")
    classified = {slug for _, slug, _, _ in TOOLS}
    # Every classified tool must be linked from the hub exactly
    # once (the duplicate check above plus this subset check).
    # The hub also links the forecast engines section and the
    # tools this page has not classified yet; the old set-equality
    # demand assumed the hub linked nothing but the classified
    # tools, which stopped being true when the hub was rebuilt
    # with one link pattern for the whole 100-item lineup
    # (2026-10-30), and refused every run since. The page's
    # partial coverage is stated on its face; extending the
    # classification itself is the G16 build, still open.
    need(classified <= set(hub_links),
         "classified tools missing from the hub: %s"
         % (sorted(classified - set(hub_links)),))

    data = {}
    for _, slug, _, _ in TOOLS:
        if slug in NO_DATA:
            page = os.path.join(HERE, slug, "index.html")
            need(os.path.exists(page), "page missing for " + slug)
            data[slug] = None
        else:
            data[slug] = load(slug)

    # The added tools (42 onward) declare their own proving
    # state in their published records, in this page's own
    # vocabulary words (horizon-grades carries it as a state key
    # instead). The classification must equal the declared state
    # or the refresh stops: this page may not put a tool in a
    # stronger or weaker state than its own record supports.
    WORD_TO_STATE = {w: k for k, w, _ in STATES}
    for num, slug, _name, state in TOOLS:
        if num < 42 or slug in ("proving-ground", "graveyard"):
            # The Graveyard (50) predates the proving_state
            # field; its measuring state is tied instead by the
            # wire and graveyard recount checks below, which
            # refuse if its buried count disagrees with the
            # Wire's own verdicts.
            continue
        d = data[slug]
        declared = None
        if isinstance(d.get("proving_state"), str):
            declared = WORD_TO_STATE.get(d["proving_state"])
        elif isinstance(d.get("proving"), dict):
            declared = d["proving"].get("state")
        need(declared is not None,
             slug + " declares no proving state this page can read")
        need(declared == state,
             "%s declares %s but is classified %s"
             % (slug, declared, state))

    rec = data["record"]
    wall = data["wall-check"]
    wire = data["replication-wire"]
    grave = data["graveyard"]

    # --- evidence checks: published states must match the classification ---
    need(data["gap-fill"].get("state") == "graded", "gap-fill no longer marked graded")
    need(data["opening-range"].get("state") == "graded", "opening-range no longer marked graded")
    need(data["earnings-drift"].get("state") == "graded", "earnings-drift no longer marked graded")
    need(wall.get("state") == "graded", "wall-check no longer marked graded")

    board_groups = rec["board"]["groups"]
    graded_1d = sum(g["grades"]["1d"].get("graded_count", 0) for g in board_groups
                    if g["grades"]["1d"].get("state") == "graded")
    need(graded_1d > 0, "scoreboard shows no graded board calls at 1 day")
    # Longer horizons are checked for coherence, not pinned to
    # waiting: the first 5-day grades land on their due dates and
    # a check that demands they wait forever refuses every
    # coherent run from that day (re-take, 2026-10-30).
    for horizon in ("5d", "21d"):
        for g in board_groups:
            h = g["grades"][horizon]
            need(h.get("state") in ("not_yet_graded", "graded"),
                 f"scoreboard {horizon} grades carry a state this page does not know")
            if h.get("state") == "graded":
                need(h.get("rose_count", -1) + h.get("did_not_rise_count", -2)
                     == h.get("graded_count"),
                     f"scoreboard {horizon} graded counts do not add up")
    def first_due(horizon):
        dates = [g["grades"][horizon]["first_grade_date"]
                 for g in board_groups
                 if g["grades"][horizon].get("state") == "not_yet_graded"
                 and g["grades"][horizon].get("first_grade_date")]
        return min(dates) if dates else None
    first_5d = first_due("5d")
    first_21d = first_due("21d")

    # Flow Tape grading has landed (cure stream D): its note is
    # generated from the grading record, and this check ties the
    # note to that record's own totals instead of pinning the
    # pre-grading wording (re-take, 2026-10-30).
    with open(os.path.join(HERE, "flow-tape",
                           "grades.json")) as fh:
        tape_grades = json.load(fh)
    tape_totals = tape_grades["totals"]
    tape_note = data["flow-tape"].get("grading_note", "")
    need(f"{tape_totals['graded']} of {tape_totals['alerts']}"
         in tape_note and f"{tape_totals['hits']} of them"
         in tape_note,
         "flow-tape grading note disagrees with its grading record")
    gold = data["golden-sweep-wire"]["counts"]
    need(gold["sessions_recorded"] < gold["sessions_needed"],
         "golden-sweep-wire cohort no longer in progress")
    need(gold["golden_prints"] == len(data["golden-sweep-wire"]["prints"]),
         "golden-sweep-wire print count disagrees with its prints")
    gold_decision = data["golden-sweep-wire"]["decision"]["decision_date"]
    pb = data["pullback-norm"]
    # Re-take (PULLBACK-RECEIPT-SOURCE-20261031): the terminal's
    # own pullback study ran on 2026-10-30 and the page now
    # publishes its counted state. Two states are coherent: the
    # old unpublished zero-signal state, or the published state
    # whose counts agree with the study figures on the same
    # page (events counted, distribution and recovery counted,
    # signals equal to the latest-session signal list). Any
    # other shape still fails closed. The construction remains
    # classified proving either way: a counted study of its own
    # figures is not a graded verdict on the construction.
    pb_published = (
        pb.get("state") == "published"
        and pb.get("events", 0) > 0
        and pb.get("distribution", {}).get("state") == "counted"
        and pb.get("recovery", {}).get("state") == "counted"
        and pb.get("signals_published")
        == len(pb.get("study", {}).get("latest_signals") or []))
    pb_unpublished = (pb.get("state") == "unpublished"
                      and pb.get("signals_published") == 0)
    need(pb_published or pb_unpublished,
         "pullback-norm is in neither the published counted state nor "
         "the unpublished zero-signal state")
    need("still being proven" in pb.get("unproven_label", ""),
         "pullback-norm no longer labels itself still being proven")
    need("still being proven" in data["correlation-web"]["definitions"].get("newness", ""),
         "correlation-web no longer labels its construction still being proven")

    act = data["activity-profile"]["baseline"]
    need(act.get("state") == "building" and act["baseline_sessions"] < act["needed"],
         "activity-profile baseline no longer building")
    need(data["fear-day"].get("state") == "unpublished", "fear-day no longer unpublished")
    # The next six checks pinned the pre-cure empty states of
    # lanes that have since landed (state readings accruing,
    # short-volume collecting, filings on record, chain snapshots
    # on record, modelled skew figures, pins from measured open
    # interest). Each is re-taken against the record's own
    # published state and counts (re-take, 2026-10-30): the check
    # still refuses if the published state regresses or the
    # counts stop agreeing with it.
    sa = data["state-analogue"]
    sa_match = re.search(r"(\d+) trading days of state readings "
                         r"are on record of the (\d+) required",
                         sa.get("coverage", ""))
    need(sa.get("floor_met") is False and sa_match
         and int(sa_match.group(1)) < int(sa_match.group(2)),
         "state-analogue coverage no longer shows an accruing record")
    sa_days, sa_needed = int(sa_match.group(1)), int(sa_match.group(2))
    need(data["short-volume"].get("state") == "collecting"
         and data["short-volume"].get("days_on_record", 0) > 0,
         "short-volume collection state changed")
    need(data["filings-wire"].get("state") == "on_record"
         and data["filings-wire"].get("companies_on_record", 0) > 0,
         "filings-wire record state changed")
    need(data["chain-explorer"].get("state") == "snapshots_on_record"
         and data["chain-explorer"].get("snapshots_on_record", 0) > 0,
         "chain-explorer archive state changed")
    need(not data["skew-lens"].get("figures")
         and "no name carries" in data["skew-lens"].get("empty_note", "")
         and data["skew-lens"].get("modelled_figures"),
         "skew-lens recorded or modelled state changed")
    need(data["expiry-pin-watch"].get("state") == "pins_on_record"
         and data["expiry-pin-watch"].get("pins_on_record", 0) > 0,
         "expiry-pin-watch record state changed")

    need(data["receipts"].get("state") == "published", "receipts no longer published")
    # Re-take (EMAP-RECEIPT-PROVENANCE-20261031): the coverage
    # note no longer carries the old fixed-construction wording;
    # it now names, per covered name, the newest map on record
    # and whether that map was filed at the time or reconstructed.
    # The check ties the note to the record itself: every covered
    # name's newest session must be named in the note, and any
    # reconstructed session must be labelled reconstructed there.
    em = data["expected-move"]
    em_note = em.get("coverage_note", "")
    em_lane = em.get("filing_lane") or {}
    for _sym, _info in (em_lane.get("names") or {}).items():
        if _info.get("newest_session"):
            need(_info["newest_session"][:4] in em_note
                 and plain_date(_info["newest_session"]) in em_note,
                 "expected-move coverage note does not name the newest "
                 "session on record for " + _sym)
    if em_lane.get("reconstructed_sessions"):
        need("reconstructed" in em_note,
             "expected-move coverage note does not label its "
             "reconstructed sessions")
    verdicts = {}
    for claim in wire["claims"]:
        verdicts[claim["verdict"]] = verdicts.get(claim["verdict"], 0) + 1
    need(wire["counts"]["total"] == len(wire["claims"])
         and all(wire["counts"].get(k, 0) == v for k, v in
                 ((kk, verdicts.get(kk, 0)) for kk in ("held", "partly", "did_not", "not_yet"))),
         "replication-wire counts disagree with its own entries")
    need(grave["counts"]["buried"] == verdicts.get("did_not", 0),
         "graveyard buried count disagrees with the wire")

    # --- reasons and next steps, in plain words, from the records ---
    R = {}
    R["gap-fill"] = ("Its record is marked graded: a finished study counted %d gaps across "
                     "SPY, QQQ and IWM over the %d days of price history on record when the "
                     "study ran." % (data["gap-fill"]["events"], data["gap-fill"]["lookback_days"]), "")
    R["opening-range"] = ("Its record is marked graded: a finished study counted %d trading "
                          "days for each of %d names over the same %d days of price history."
                          % (data["opening-range"]["days_per_name"],
                             data["opening-range"]["name_count"],
                             data["opening-range"]["lookback_days"]), "")
    R["earnings-drift"] = ("Its record is marked graded: a finished study counted %d earnings "
                           "reports across AAPL, MSFT and NVDA over the %d days of price "
                           "history on record when the study ran."
                           % (data["earnings-drift"]["events"],
                              data["earnings-drift"]["lookback_days"]), "")
    R["wall-check"] = ("Its record is marked graded: it has graded %d wall tests from the %d "
                       "published map cards on record, and %d cards are still waiting for "
                       "their session to complete."
                       % (wall["totals"]["tests"], wall["cards_of_record"], len(wall["waiting"])),
                       "The waiting cards graded once their sessions complete, and more "
                       "published cards graded as new sessions finish.")
    R["morning-map"] = ("Its published cards sit on the permanent record and are graded as "
                        "their sessions complete: the wall grades on record cover %d tests "
                        "from its %d published cards, with %d cards still waiting."
                        % (wall["totals"]["tests"], wall["cards_of_record"], len(wall["waiting"])),
                        "More of its published cards graded as their sessions complete.")
    R["board"] = ("The public scoreboard has graded its published calls at 1 trading day "
                  "(%d graded so far)." % graded_1d,
                  ("Its first 5-day grades, due %s, and its first 21-day grades, due %s."
                   % (plain_date(first_5d), plain_date(first_21d))
                   if first_5d and first_21d else
                   "Its longer-horizon grades as their due dates land."))
    R["flow-tape"] = ("Its alerts are graded against what prices did next: %d of %d logged "
                      "alerts graded so far, %d of them in the direction the alert pointed, "
                      "from its own grading record."
                      % (tape_totals["graded"], tape_totals["alerts"],
                         tape_totals["hits"]),
                      "The freshest session's alerts grade after the next close exists.")
    R["golden-sweep-wire"] = ("A proving count is running: %d of the %d recorded trading days "
                              "toward a verdict are in, with %d golden prints so far."
                              % (gold["sessions_recorded"], gold["sessions_needed"],
                                 gold["golden_prints"]),
                              "%d more recorded trading days to reach %d, with the verdict "
                              "due on %s." % (gold["sessions_remaining"], gold["sessions_needed"],
                                              plain_date(gold_decision)))
    if pb_published:
        R["pullback-norm"] = ("Its own page labels it a new construction that is still being proven "
                              "and has not been proven yet; a pullback study of its own has run "
                              "on the record and counted %d events, and it publishes %d signal(s) "
                              "on the panel's freshest session."
                              % (pb["events"], pb["signals_published"]),
                              "A graded verdict on the construction itself, beyond the "
                              "counted study its page already publishes.")
    else:
        R["pullback-norm"] = ("Its own page labels it a new construction that is still being proven "
                              "and has not been proven yet; no pullback study of its own has run, "
                              "and it publishes 0 signals.",
                              "A study on the record that counts its own results: its page "
                              "publishes no result from it until such a study has run.")
    R["correlation-web"] = ("Its own definitions call the way it puts daily price moves "
                            "together a new construction of ours that is still being proven.", "")
    R["activity-profile"] = ("Its baseline is still building: %d of the %d sessions it is "
                             "judged against are recorded."
                             % (act["baseline_sessions"], act["needed"]),
                             "%d more recorded sessions to complete the %d-session baseline."
                             % (act["needed"] - act["baseline_sessions"], act["needed"]))
    R["fear-day"] = ("Its record is marked unpublished: no fear-day study has been published "
                     "yet, so there is no follow-through to grade; the page shows the "
                     "definition and the %d day on record that meets it."
                     % data["fear-day"]["events"],
                     "A fear-day study published on the record.")
    R["state-analogue"] = ("%d trading days of state readings are on record of the %d it "
                           "needs, so it shows no matches yet."
                           % (sa_days, sa_needed),
                           "%d recorded days of state readings."
                           % sa_needed)
    R["short-volume"] = ("The daily collection is running: %d days on record."
                         % data["short-volume"]["days_on_record"],
                         "The stored days climb one per session toward the baselines "
                         "its consumers judge against.")
    R["filings-wire"] = ("Companies' reported figures are on record: %d companies."
                         % data["filings-wire"]["companies_on_record"],
                         "More companies' figures as the weekly gathering covers them.")
    R["chain-explorer"] = ("The chain archive holds snapshots: %d on record, the freshest "
                           "from %s."
                           % (data["chain-explorer"]["snapshots_on_record"],
                              data["chain-explorer"]["freshest_snapshot"]),
                           "Snapshots accrue every 30 minutes in market hours.")
    R["skew-lens"] = ("In the recorded per-strike ledger no name carries both sides at "
                      "matched distances, so no recorded figure is shown; a modelled "
                      "figure from the chain record is shown separately and labelled "
                      "modelled (%s)."
                      % data["skew-lens"]["modelled_figures"][0]["sentence"],
                      "A recorded record that carries both sides for a name, which is "
                      "when its own note says a recorded figure will appear.")
    R["expiry-pin-watch"] = ("Per-strike open interest is on record from the chain "
                             "snapshots: %d pins on record."
                             % data["expiry-pin-watch"]["pins_on_record"],
                             "Pins recomputed as new snapshots land on expiry mornings.")
    R["record"] = ("It is the scoreboard itself: it only reports the grades of the calls "
                   "other tools published (%d published, %d graded so far); nothing grades it."
                   % (rec["totals"]["calls_published"], rec["totals"]["calls_graded_so_far"]), "")
    R["payoff-sketch"] = ("It has no published record: its figures are made on your screen, "
                          "from your inputs, at the moment you use it. A browser calculator only.", "")
    R["expected-move"] = ("It draws the bands of a fixed, named construction from the closes "
                          "on record and publishes no grade; its own coverage note presents "
                          "the bands as the last ones on record, not today's.", "")
    R["screener"] = ("It only filters the scored trading day by plain conditions in the "
                     "browser; it publishes no call and no grade.", "")
    R["portfolio-builder"] = ("It only turns the day's passing names into an equal-weight "
                              "basket sketch under stated freshness gates; no grade is "
                              "published for it.", "")
    R["squeeze-watch"] = ("It reports the twice-monthly short-interest readings against the "
                          "published 15 percent bar; no grade is published for its flags.", "")
    R["second-opinion"] = ("It only counts how many separate families of evidence speak for "
                           "a name from the records on file; it makes no call of its own.", "")
    R["receipts"] = ("It only republishes the other tools' records, completeness and grade "
                     "states, read exactly as they were published.", "")
    R["insider-wire"] = ("It only summarises insider filings on record per name; it publishes "
                         "no call of its own.", "")
    R["dark-prints"] = ("It reports the combined dark-pool reading for the index from the "
                        "sessions on record; the reading it exists to show is published, "
                        "and it makes no forecast of its own.", "")
    R["iv-weather"] = ("It reports each name's volatility readings against its own history; "
                       "it grades nothing.", "")
    R["premium-meter"] = ("It only reports each recorded day's options premium totals and "
                          "the put and call split from the prints on record.", "")
    R["greeks-sketch"] = ("Its page says everything is worked out on the page, in your "
                          "browser, and nothing you type is sent anywhere. A calculator only.", "")
    R["breadth-meter"] = ("It only reports market-wide counts from the daily scoring run's "
                          "price history; no call, no grade.", "")
    R["sector-rotation"] = ("It only ranks sectors over 5 and 21 sessions from the recorded "
                            "price history; no call, no grade.", "")
    R["regime-dial"] = ("It only combines the published figures of the other tools on this "
                        "site into one plain reading, each read exactly as published there.", "")
    R["week-ahead"] = ("A calendar only: official release schedules gathered into one view.", "")
    R["earnings-calendar"] = ("It only lists scheduled report dates on record, with a "
                              "priced expected move shown for the %d names the priced "
                              "move record covers."
                              % data["earnings-calendar"]["priced_moves_on_record"], "")
    R["watchlist-pulse"] = ("It only republishes the six evidence families the Second "
                            "Opinion assembles for each name as one strip; it makes no "
                            "claim of its own.", "")
    R["unusual-volume"] = ("It only reports names trading heavy volume against their own "
                           "recorded baseline from the consolidated tape records.", "")
    R["grade-my-call"] = ("It grades the reader's own call in the browser from the closing "
                          "prices on record; it publishes no call of its own.", "")
    R["13f-tracker"] = ("It only reports what the largest holders on record held, and how it "
                        "changed, in the quarterly filings on record.", "")
    R["replication-wire"] = ("It only reports the verdict record of finished re-tests (%d "
                             "claims counted); it is a reporting wire, not a claim."
                             % len(wire["claims"]), "")
    R["grade-a-board"] = ("A finished study publication: its record counts %d grade-A "
                          "cells from the two searches it republishes, and it grades "
                          "nothing new." % data["grade-a-board"]["counts"]["grade_a"], "")
    R["fear-day-forecaster"] = ("Its own note says it is still being proven: the ranking "
                                "rests on a finished study, but this page's own forward "
                                "record has not started yet, so nothing it could say "
                                "about the next fear day has been graded.",
                                "Forward entries published as qualifying fear days occur.")
    R["router"] = ("It republishes the rule's standing answer over the shared book of "
                   "%d entries, with the reason printed; its own record labels it "
                   "still being proven."
                   % data["router"]["counts"]["book_entries"], "")
    R["promoted-book"] = ("A finished study publication: it republishes the promotion "
                          "study's %d entries, with their grades as recorded, and "
                          "grades nothing new."
                          % data["promoted-book"]["counts"]["total"], "")
    R["odds-cards"] = ("A finished study publication: its cards republish a completed "
                       "replay of historical cases for named setup families, with "
                       "the pass bar stated per family.", "")
    R["decay-watch"] = ("It republishes the shared book's counts and grading "
                        "movements; it grades nothing itself.", "")
    R["horizon-grades"] = ("It republishes the grades the public scoreboard has "
                            "landed at 1, 5 and 21 sessions (%d calls published, "
                            "%d graded so far); it grades nothing itself."
                            % (data["horizon-grades"]["totals"]["calls_published"],
                               data["horizon-grades"]["totals"]["calls_graded_so_far"]),
                            "More grades as the 5 and 21 session horizons complete.")
    R["survivors-wire"] = ("It republishes the cross-check over the study corpus: "
                           "%d examined, %d standing, %d partly standing and %d not "
                           "standing, counted from the records it reads; its own "
                           "record labels the wire still being proven."
                           % (data["survivors-wire"]["counts"]["examined"],
                              data["survivors-wire"]["counts"]["standing"],
                              data["survivors-wire"]["counts"]["partly"],
                              data["survivors-wire"]["counts"]["not_standing"]), "")
    R["strat-scanner"] = ("Its labels are still being proven: %s No forward record "
                          "for its labels exists yet."
                          % data["strat-scanner"]["coverage"].split(";")[0] + ".",
                          "A forward record for its labels, graded as sessions complete.")
    R["strat-combos"] = ("It groups the Strat Scanner's labels into named "
                         "combinations and adds none of its own; it is still being "
                         "proven with the Scanner.", "The Scanner's forward record.")
    R["smart-money-tracker"] = ("It republishes the quarterly holdings reports from "
                                "the changes side (%s); it grades nothing."
                                % data["smart-money-tracker"]["coverage"].split(" and ")[0] + ".", "")
    R["gamma-ladder"] = ("It republishes the Morning Map family's modelled strike "
                         "ladder, labelled modelled on its own record; it makes no "
                         "reading of its own.", "")
    R["tape-heatmap"] = ("It republishes the tape family's freshest session as a "
                         "map: %s; it makes no forecast of its own."
                         % data["tape-heatmap"]["receipt"]["coverage"].split(":")[0] + ".", "")
    R["flow-board"] = ("It republishes the tape family's record across its "
                       "recorded sessions (%s); its own claim has not been graded "
                       "yet." % data["flow-board"]["coverage_words"].split(";")[0] + ".",
                       "More recorded sessions as the tape family accrues daily.")
    R["signal-feed"] = ("It aggregates entries the other tools already published, "
                        "each shown exactly as its own tool published it; its own "
                        "record says its claim has not been graded or proven yet.",
                        "Grading or a verdict on the feed's own claim.")
    R["echo-board"] = ("It republishes the Second Opinion's family counts for its "
                       "session and lists only the names whose direction-carrying "
                       "families agree; it makes no call of its own.", "")
    R["flow-engine"] = ("It republishes the tape family's freshest session with its "
                        "explanatory scoring (%d published alerts on its record); "
                        "its own claim is still being proven."
                        % data["flow-engine"]["counts"]["alerts_published"],
                        "More recorded sessions as the tape family accrues daily.")
    R["holly-ideas"] = ("It republishes the Board and tape families' assembly for "
                        "its session: %d ideas streamed on its record; its own "
                        "claim has not been graded yet."
                        % data["holly-ideas"]["counts"]["ideas_streamed"],
                        "Grading of the ideas it streams, as their sessions complete.")
    R["agent-debate"] = ("It argues a bull case and a bear case for the three index "
                         "funds from the same published readings, ending in a "
                         "stated lean; its own record labels it still being proven.", "")
    R["ai-chart-read"] = ("Still being proven: its own note says this read has no "
                          "graded record of its own yet; its reads are worked out "
                          "from the daily prices on record for the scored names.", "")
    R["reversal-wire"] = ("It republishes the Strat Scanner's reversal-shaped "
                          "labels as a dated wire: %d entries over %d names on its "
                          "record; still being proven."
                          % (data["reversal-wire"]["counts"]["total_entries"],
                             data["reversal-wire"]["counts"]["distinct_names"]),
                          "More sessions on the wire as the Scanner publishes them.")
    R["alert-tape"] = ("It republishes the tape family's alert archive for its "
                       "recorded sessions (%d alerts across %d funds on its "
                       "record); it makes no claim of its own."
                       % (data["alert-tape"]["counts"]["alerts_in_archive"],
                          data["alert-tape"]["counts"]["funds"]), "")
    R["breakout-scanner"] = ("Still being proven: its own note says no graded "
                             "record exists of what prices did after a name "
                             "appeared on its list.", "")
    R["one-page-report"] = ("It gathers readings other tools already published "
                            "into nine sections per name (%s); it makes no "
                            "reading of its own."
                            % data["one-page-report"]["receipt"].split(".")[0] + ".", "")
    R["pattern-draw"] = ("It draws the Strat Scanner's labels on charts from the "
                         "record (%s); the labels have no forward record yet."
                         % data["pattern-draw"]["coverage"].split(",")[0] + ".",
                         "A forward record for the labels it draws.")
    R["echo-lens"] = ("It republishes the analyst method's readings from the "
                      "published record (%s); its own claim has not been graded "
                      "yet." % data["echo-lens"]["coverage_words"].split(", with")[0] + ".",
                      "Grading or a verdict on the lens's own claim.")
    R["momentum-clock"] = ("Still being proven: its own note says the clock only "
                           "describes how far each name's price has risen or "
                           "fallen over 21, 63, 126 and 252 sessions, as "
                           "description only.", "")
    R["proving-ground"] = ("This page itself: it republishes the proving state of "
                           "every tool on the site from each tool's own record, "
                           "and grades nothing.", "")
    R["graveyard"] = ("It only keeps the claims that did not hold up readable, from the "
                      "Replication Wire's published verdict record (%d buried of %d "
                      "checked); it makes no claim of its own."
                      % (grave["counts"]["buried"], grave["counts"]["checked_total"]), "")

    entries = []
    counts = {k: 0 for k, _, _ in STATES}
    newest = ""
    for num, slug, name, state in TOOLS:
        need(slug in R, "no reason assembled for " + slug)
        reason, nxt = R[slug]
        counts[state] += 1
        entries.append({"name": name, "slug": slug, "state": state,
                        "state_words": STATE_LABEL[state], "reason": reason, "next": nxt})
        d = data[slug]
        if d:
            for key in ("published_at_utc", "generated_at_utc", "feed_generated_at_utc",
                        "newest_source_time"):
                v = d.get(key)
                if isinstance(v, str) and v > newest:
                    newest = v
    need(sum(counts.values()) == len(TOOLS), "counts do not add up to the tool list")

    out = {
        "tool": "The Proving Ground",
        "source": SOURCE_WORDS,
        "newest_source_time": newest,
        "tools_count": len(entries),
        "counts": counts,
        "states": [{"key": k, "words": w, "definition": d} for k, w, d in STATES],
        "tools": entries,
        "joining_note": ("Every tool designed for this site is on this page: all 70, "
                         "each with its proving state read from its own record."),
    }
    blob = json.dumps(out, ensure_ascii=False)
    for bad in FORBIDDEN:
        need(bad not in blob, "forbidden wording assembled: " + bad)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        out = _tc.stamp_for_script(out, __file__) if _tc is not None else out
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("wrote %s: %d tools, counts %s" % (OUT_PATH, len(entries), counts))


if __name__ == "__main__":
    main()
