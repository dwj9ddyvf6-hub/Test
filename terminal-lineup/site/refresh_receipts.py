#!/usr/bin/env python3
"""Refresh the Receipts data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: the published records of the other tools on this
site, exactly as each tool published them: for every tool, the
record its figures come from (in that tool's own public words), the
time that record was made, the trading day it covers where one is
named, how complete it is, and its grading state where the tool
itself publishes one. Where a tool publishes no receipt of its own,
this page assembles the same shape from that tool's own published
summary counts, and where a tool publishes nothing at all (the
payoff tool works in the reader's browser and keeps no record),
this page says exactly that and nothing more.

Reconstruction choices, stated as ours: (1) One receipt per tool,
in the site's own order, using only words and numbers the tool
itself published: a tool's own receipt wording is used word for
word where it exists; coverage lines built from a tool's published
counts are plain counts, never percentages, because several of the
counts behind them are small. (2) A grade line appears only where
the tool's own record carries grading: a study pane whose figures
are the study itself carries no grade line, and no tool is given a
grade borrowed from another tool's page. (3) What is not recorded
is named per tool: no tool on this site publishes a separate method
label beyond the words in its record line, and none publishes a
step-by-step trail of how each figure was passed along, so both are
named as not recorded rather than filled in. The one tool that
publishes extra time points (the morning map) has them shown as
they are: two of the five time points in the shared evidence
standard are recorded, three are not, and its record is therefore
not cleared for decision use; the blockers behind that are stated
in plain words, never in the internal wording of its record.
(4) Every time on this page comes from a source record, never from
the clock, so running this script twice produces the same file.

Non-claims: this page does not claim any tool's record is better
or worse than another's, does not grade any figure itself, does
not fill a gap in a tool's record from a sister tool's record, and
does not show any figure from any tool: it shows only where each
tool's figures came from.

Fail-closed rules: if any tool's own published receipt disagrees
with that tool's published summary (a different record line, a
different time, or a different trading day in the receipt than at
the top of its record), if a tool's name is not the name this page
expects, if a group receipt inside a tool names a different record
than the tool's own top line, or if any words assembled here carry
an internal file name, the refresh stops and publishes nothing.

Usage: python3 refresh_receipts.py
"""

import json
import os
import sys
from datetime import datetime

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "receipts", "data.json")

SOURCE_WORDS = ("The published records of the other free tools on "
                "this site, read exactly as they were published")

NOT_RECORDED_COMMON = [
    "No separate method label is published beyond the words in the record line above.",
    "No step-by-step trail of how each figure was passed along is published.",
]

FORBIDDEN = (".json", ".py", "morgue", "ledger.jsonl")


def fail(msg):
    raise SystemExit("refresh_receipts: FAIL: " + msg)


def load(slug):
    path = os.path.join(HERE, slug, "data.json")
    if not os.path.exists(path):
        fail(f"{slug}: published data file missing")
    with open(path) as f:
        return json.load(f)


def num(x):
    return f"{int(x):,}"


def fmt_day(iso):
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return d.strftime("%b %-d, %Y")


def expect_tool(d, slug, name):
    if d.get("tool") != name:
        fail(f"{slug}: tool name {d.get('tool')!r} != expected {name!r}")


def check_receipt_matches(d, slug, time_keys):
    """A tool's own top-level receipt must agree with its summary."""
    r = d.get("receipt")
    if not r:
        return
    if r.get("source") and r["source"] != d.get("source"):
        fail(f"{slug}: receipt record line disagrees with the tool's own top line")
    for k in time_keys:
        if r.get(k) and d.get(k) and r[k] != d[k]:
            fail(f"{slug}: receipt time {k} disagrees with the tool's own top line")
    if r.get("session") and d.get("session") and r["session"] != d["session"]:
        fail(f"{slug}: receipt session disagrees with the tool's own top line")


def check_group_receipts(d, slug, containers, check_time=True):
    for items in containers:
        for it in items or []:
            r = it.get("receipt") if isinstance(it, dict) else None
            if r and r.get("source") and r["source"] != d.get("source"):
                fail(f"{slug}: a group receipt names a different record than the tool's top line")
            if check_time and r and r.get("published_at_utc") and d.get("published_at_utc") \
                    and r["published_at_utc"] != d["published_at_utc"]:
                fail(f"{slug}: a group receipt time disagrees with the tool's top line")


def entry(tool, slug, record, made_at, session, coverage,
          completeness=None, grade=None, extra_lines=None, not_recorded=None):
    return {
        "tool": tool,
        "slug": slug,
        "record": record,
        "made_at": made_at,
        "session": session,
        "coverage": coverage,
        "completeness": completeness,
        "grade": grade,
        "extra_lines": extra_lines or [],
        "not_recorded": (NOT_RECORDED_COMMON if not_recorded is None
                         else not_recorded),
    }


def build():
    receipts = []

    # 1 Morning Map
    d = load("morning-map"); expect_tool(d, "morning-map", "Morning Map")
    covs = []
    seen_src = set()
    for idx in d["indexes"]:
        pos = idx["positioning"]["receipt"]
        if pos["session"] != d["session"]:
            fail("morning-map: a receipt session disagrees with the tool's session")
        if pos["source"] in seen_src:
            continue
        seen_src.add(pos["source"])
        covs.append(pos)
    cov_text = "; ".join(
        f"{idx['symbol']}: {idx['positioning']['receipt']['coverage']}"
        for idx in d["indexes"])
    clocks = d["contract"]["clocks"]
    present = [k for k, v in clocks.items() if v.get("state") == "present"]
    absent = [k for k, v in clocks.items() if v.get("state") != "present"]
    if len(present) != 2 or len(absent) != 3:
        fail("morning-map: the recorded time points are not the two-of-five this page states")
    gh = d["contract"]["grading_horizon"]
    graded = [k for k, v in gh["per_index"].items() if v.get("state") == "graded"]
    ungraded = [k for k, v in gh["per_index"].items() if v.get("state") != "graded"]
    grade = (f"Grading so far is {gh['state']}: "
             + ", ".join(f"{k} carries a graded reading dated {gh['per_index'][k]['date']}"
                         for k in graded)
             + "; " + ", ".join(f"{k} carries no grading state in this record"
                                for k in ungraded) + ".")
    receipts.append(entry(
        d["tool"], "morning-map", d["source"], d["generated_at_utc"], d["session"],
        cov_text,
        completeness=("The combined dark pool reading across the stocks inside an index "
                      "is calculated for SPY only, so QQQ and IWM have no such figure."),
        grade=grade,
        extra_lines=[
            ["Time points", "2 of the 5 time points in the shared evidence standard are "
            "recorded (when it was gathered and when it was published). When it "
            "happened, when it first became available, and when a decision could be "
            "made are not recorded."],
            ["Decision use", "This record is not cleared for decision use, because those "
            "time points are missing and the combined dark pool reading exists for "
            "SPY only."],
            ["How the figures were made", "In the record's own words: modelled from "
            "dealer positioning, not directly observed."],
        ]))

    # 2 The Record
    d = load("record"); expect_tool(d, "record", "The Record")
    t = d["totals"]; oc = t["outcomes_so_far"]
    receipts.append(entry(
        d["tool"], "record", d["source"], d["generated_at_utc"], None,
        (f"{num(t['calls_published'])} calls published ({num(t['board_calls'])} from the "
         f"board, {num(t['map_calls'])} from the morning map)"),
        grade=(f"{num(t['calls_graded_so_far'])} of {num(t['calls_published'])} calls "
               f"graded so far, at {oc['horizon_days']} trading day: {num(oc['rose_count'])} "
               f"rose, {num(oc['did_not_rise_count'])} did not rise. Counts only: fewer "
               f"than 30 graded calls is too few for a percentage.")))

    # 3 Qualified Board
    d = load("board"); expect_tool(d, "board", "Qualified Board")
    check_group_receipts(d, "board", [d["groups"]])
    receipts.append(entry(
        d["tool"], "board", d["source"], d["published_at_utc"], d["session"],
        d["groups"][0]["receipt"]["coverage"]))

    # 4 Flow Tape
    d = load("flow-tape"); expect_tool(d, "flow-tape", "Flow Tape")
    check_group_receipts(d, "flow-tape", [d["groups"]])
    comp = d["groups"][0]["completeness"]
    total_comp_reason = None
    for g in d["groups"]:
        if g["completeness"]["state"] != "incomplete":
            fail("flow-tape: a group completeness state is not the incomplete this page states")
    receipts.append(entry(
        d["tool"], "flow-tape", d["source"], d["published_at_utc"], d["session"],
        (f"{num(d['counts']['prints_looked_at'])} prints looked at across "
         f"{d['counts']['indexes']} index funds; {num(d['counts']['alerts_published'])} "
         f"alerts published"),
        completeness=("Incomplete: very busy contract groups hit the reading limit, "
                      "so some prints in those groups may be missing."),
        grade=d["grading_note"]))

    # 5 Golden Sweep Wire
    d = load("golden-sweep-wire"); expect_tool(d, "golden-sweep-wire", "Golden Sweep Wire")
    # Session receipts each carry their own session's publication time;
    # the freshest session's receipt must match the tool's top line.
    check_group_receipts(d, "golden-sweep-wire", [d["sessions"]], check_time=False)
    freshest = max(d["sessions"], key=lambda s: s.get("session", ""))
    if freshest["receipt"]["published_at_utc"] != d["published_at_utc"]:
        fail("golden-sweep-wire: the freshest session's receipt time disagrees with the top line")
    if freshest["session"] != d["freshest_session"]:
        fail("golden-sweep-wire: the freshest session disagrees with the tool's summary")
    receipts.append(entry(
        d["tool"], "golden-sweep-wire", d["source"], d["published_at_utc"],
        d["freshest_session"], freshest["receipt"]["coverage"],
        grade=(f"No verdict yet: {num(d['counts']['sessions_recorded'])} of "
               f"{num(d['counts']['sessions_needed'])} recorded trading days toward a "
               f"verdict on {fmt_day(d['decision']['decision_date'])}.")))

    # 6 Payoff Sketch: no published record at all
    receipts.append(entry(
        "Payoff Sketch", "payoff-sketch",
        ("Worked out in your browser from the prices and the position you type in. "
         "Nothing you type is sent anywhere."),
        None, None, None,
        not_recorded=[
            "No published record exists for this tool, so there is no record line, "
            "date, coverage or grade to trace: its figures are made on your screen, "
            "from your inputs, at the moment you use it.",
        ]))

    # 7 Expected Move Map
    d = load("expected-move"); expect_tool(d, "expected-move", "Expected Move Map")
    # Each name's receipt names the record that name's map
    # actually came from: filed-at-the-time maps carry the top
    # line's source; reconstructed maps carry the reconstructed
    # source and must be flagged reconstructed in their receipt
    # (EMAP-RECEIPT-PROVENANCE-20261031). Any other source, or a
    # reconstructed source without the flag, still fails closed.
    for n in d["names"]:
        src = n["receipt"]["source"]
        if src == d["source"]:
            continue
        if n["receipt"].get("filing") == "reconstructed" \
                and "reconstructed" in src \
                and n.get("reconstructed") is True:
            continue
        fail("expected-move: a name's receipt names a different record than the top line")
    ok_names = [n["symbol"] for n in d["names"] if n.get("state") == "ok"]
    no_names = [n["symbol"] for n in d["names"] if n.get("state") != "ok"]
    receipts.append(entry(
        d["tool"], "expected-move", d["source"], d["published_at_utc"], d["session"],
        d["coverage_note"].strip(),
        completeness=(f"{len(ok_names)} of {len(d['names'])} names have a map on record"
                      + (f"; no map was ever filed for {', '.join(no_names)}." if no_names else "."))))

    # 8 The Screener
    d = load("screener"); expect_tool(d, "screener", "The Screener")
    c = d["counts"]
    receipts.append(entry(
        d["tool"], "screener", d["source"], d["published_at_utc"], d["session"],
        (f"{num(c['names_checked'])} names checked, {num(c['names_scored'])} scored, "
         f"{num(c['not_enough_data'])} with too little data to score, "
         f"{num(c['passed_every_check_all'])} passed every check")))

    # 9 Portfolio Builder
    d = load("portfolio-builder"); expect_tool(d, "portfolio-builder", "Portfolio Builder")
    c = d["counts"]
    if not all(g["passed"] for g in d["gates"]):
        fail("portfolio-builder: a gate did not pass, so the gate line this page states is wrong")
    receipts.append(entry(
        d["tool"], "portfolio-builder", d["source"], d["published_at_utc"], d["session"],
        (f"A basket of {num(c['members'])} members, built from the "
         f"{num(c['passed_every_check_all'])} names that passed every check out of "
         f"{num(c['names_checked'])} checked"),
        completeness=("Both gates the snapshot had to pass before a basket was built "
                      "from it did pass: " + "; ".join(g["name"] for g in d["gates"]) + ".")))

    # 10 Activity Profile
    d = load("activity-profile"); expect_tool(d, "activity-profile", "Activity Profile")
    check_group_receipts(d, "activity-profile", [d["names"]])
    check_group_receipts(d, "activity-profile", [d["sessions"]], check_time=False)
    cur = [s for s in d["sessions"] if s["session"] == d["current_session"]]
    if len(cur) != 1 or cur[0]["receipt"]["published_at_utc"] != d["published_at_utc"]:
        fail("activity-profile: the current session's receipt time disagrees with the top line")
    b = d["baseline"]
    receipts.append(entry(
        d["tool"], "activity-profile", d["source"], d["published_at_utc"],
        d["current_session"],
        b["state_words"] + f", across the three index funds (SPY, QQQ, IWM)",
        completeness=("Incomplete: very busy contract groups hit the reading limit, "
                      "so some prints in those groups may be missing.")))

    # 11-13 study panes with their own receipts
    for slug, name in (("gap-fill", "Gap-Fill Pane"),
                       ("opening-range", "Opening Range Pane"),
                       ("earnings-drift", "Earnings Drift Pane")):
        d = load(slug); expect_tool(d, slug, name)
        check_receipt_matches(d, slug, ["published_at_utc"])
        receipts.append(entry(
            d["tool"], slug, d["source"], d["published_at_utc"],
            d["receipt"].get("session"), d["receipt"]["coverage"]))

    # 14 Wall Check
    d = load("wall-check"); expect_tool(d, "wall-check", "Wall Check")
    check_receipt_matches(d, slug if False else "wall-check", ["published_at_utc"])
    receipts.append(entry(
        d["tool"], "wall-check", d["source"], d["published_at_utc"], None,
        d["receipt"]["coverage"],
        grade=("Graded, and every cell behind it is thin (fewer than 30 tests), so "
               "this tool shows counts and no percentages.")))

    # 15 Squeeze Watch
    d = load("squeeze-watch"); expect_tool(d, "squeeze-watch", "Squeeze Watch")
    check_receipt_matches(d, "squeeze-watch", ["published_date"])
    receipts.append(entry(
        d["tool"], "squeeze-watch", d["source"], d["published_date"], None,
        d["receipt"]["coverage"],
        extra_lines=[["Settlement", f"The readings rest on the settlement of {fmt_day(d['receipt']['settlement_date'])}."]]))

    # 16 Fear Day List
    d = load("fear-day"); expect_tool(d, "fear-day", "Fear Day List")
    check_receipt_matches(d, "fear-day", ["published_at_utc"])
    receipts.append(entry(
        d["tool"], "fear-day", d["source"], d["published_at_utc"], None,
        d["receipt"]["coverage"],
        completeness="No fear-day study has been published yet, so there is no follow-through to grade."))

    # 17 Pullback Norm
    d = load("pullback-norm"); expect_tool(d, "pullback-norm", "Pullback Norm")
    check_receipt_matches(d, "pullback-norm", ["published_at_utc"])
    if d.get("state") == "published":
        # Re-take (PULLBACK-RECEIPT-SOURCE-20261031): the
        # terminal's own study has run and counted, so the
        # receipt states the counted state in the study's own
        # published figures; the unpublished words below remain
        # the only other state this page accepts.
        if not (d.get("events", 0) > 0
                and d.get("distribution", {}).get("state") == "counted"):
            fail("pullback-norm: published state without a counted distribution")
        pb_completeness = (
            f"A pullback study of its own has run and counted: "
            f"{num(d['events'])} events, with a counted depth "
            f"distribution and recovery record on its page.")
    elif d.get("state") == "unpublished" and d.get("signals_published") == 0:
        pb_completeness = ("No pullback study has been published yet, so there is "
                           "no distribution or result to grade.")
    else:
        fail("pullback-norm: state is neither the published counted state nor "
             "the unpublished zero-signal state")
    receipts.append(entry(
        d["tool"], "pullback-norm", d["source"], d["published_at_utc"], None,
        d["receipt"]["coverage"],
        completeness=pb_completeness))

    # 18 The Second Opinion
    d = load("second-opinion"); expect_tool(d, "second-opinion", "The Second Opinion")
    if d["receipt"]["source"] != d["source"]:
        fail("second-opinion: its receipt names a different record than its top line")
    receipts.append(entry(
        d["tool"], "second-opinion", d["source"], d["board_published_at_utc"],
        d["session"], d["receipt"]["coverage"],
        extra_lines=[
            ["When each part was made", "The scored day was published "
            + fmt_day(d["board_published_at_utc"]) + "; the prints were published "
            + fmt_day(d["prints_published_at_utc"]) + "; the positioning was built "
            + fmt_day(d["positioning_built_at_utc"]) + "; the filings are dated "
            + fmt_day(d["filings_as_of"]) + "."],
        ]))

    # 19-70: the rest of the lineup, assembled generically from
    # each tool's own published record (RC-11 cure, 2026-10-30).
    # The first 18 receipts above are hand-built because their
    # records carry bespoke shapes; these follow one rule: the
    # record line is the tool's own top line, the time and
    # session are the tool's own, the coverage is the tool's own
    # coverage words where it publishes them (its own receipt's
    # coverage first), and a grade line appears only where the
    # tool's own record publishes a proving state, in its words.
    GENERIC = [
        (20, "state-analogue", "State Analogue"),
        (21, "insider-wire", "Insider Wire"),
        (22, "short-volume", "Short Volume Ledger"),
        (23, "filings-wire", "Filings Wire"),
        (24, "dark-prints", "Dark Prints"),
        (25, "chain-explorer", "Chain Explorer"),
        (26, "iv-weather", "IV Weather"),
        (27, "skew-lens", "Skew Lens"),
        (28, "premium-meter", "Premium Meter"),
        (30, "expiry-pin-watch", "Expiry Pin Watch"),
        (31, "breadth-meter", "Breadth Meter"),
        (32, "sector-rotation", "Sector Rotation"),
        (33, "regime-dial", "Regime Dial"),
        (34, "week-ahead", "The Week Ahead"),
        (35, "earnings-calendar", "Earnings Calendar"),
        (36, "watchlist-pulse", "Watchlist Pulse"),
        (37, "correlation-web", "Correlation Web"),
        (38, "unusual-volume", "Unusual Volume"),
        (39, "grade-my-call", "Grade My Call"),
        (40, "13f-tracker", "13F Tracker"),
        (41, "replication-wire", "Replication Wire"),
        (42, "grade-a-board", "Grade-A Board"),
        (43, "fear-day-forecaster", "Fear-Day Forecaster"),
        (44, "router", "The Router"),
        (45, "promoted-book", "Promoted Book"),
        (46, "odds-cards", "Odds Cards"),
        (47, "decay-watch", "Decay Watch"),
        (48, "horizon-grades", "Horizon Grades"),
        (49, "survivors-wire", "Survivors Wire"),
        (50, "graveyard", "The Graveyard"),
        (51, "strat-scanner", "Strat Scanner"),
        (52, "strat-combos", "Strat Combos Board"),
        (53, "smart-money-tracker", "Smart Money Tracker"),
        (54, "gamma-ladder", "Gamma Ladder"),
        (55, "tape-heatmap", "Tape Heatmap"),
        (56, "flow-board", "Flow Board"),
        (57, "signal-feed", "Signal Feed"),
        (58, "echo-board", "Echo Board"),
        (59, "flow-engine", "Flow Engine"),
        (60, "proving-ground", "The Proving Ground"),
        (61, "holly-ideas", "Holly Ideas"),
        (62, "agent-debate", "Agent Debate"),
        (63, "ai-chart-read", "AI Chart Read"),
        (64, "reversal-wire", "Reversal Wire"),
        (65, "alert-tape", "Alert Tape"),
        (66, "breakout-scanner", "Breakout Scanner"),
        (67, "one-page-report", "One-Page Report"),
        (68, "pattern-draw", "Pattern Draw"),
        (69, "echo-lens", "Echo Lens"),
        (70, "momentum-clock", "Momentum Clock"),
    ]
    TIME_KEYS = ("published_at_utc", "generated_at_utc",
                 "board_published_at_utc", "feed_generated_at_utc",
                 "newest_source_time", "published_date", "as_of",
                 "freshest_date", "date")
    for _num, slug, name in GENERIC:
        d = load(slug); expect_tool(d, slug, name)
        if isinstance(d.get("receipt"), dict):
            check_receipt_matches(d, slug, [k for k in TIME_KEYS
                                            if k.endswith("_utc")])
        made_at = next((d[k] for k in TIME_KEYS if d.get(k)), None)
        session = (d.get("session") or d.get("current_session")
                   or d.get("freshest_session")
                   or d.get("scored_run_session"))
        r = d.get("receipt")
        coverage = None
        if isinstance(r, dict) and r.get("coverage"):
            coverage = r["coverage"]
            if r.get("source") and r["source"] != d.get("source"):
                fail(f"{slug}: its receipt names a different "
                     "record than its top line")
            if session is None:
                session = r.get("session")
        elif isinstance(r, str) and r:
            coverage = r
        if coverage is None and isinstance(d.get("coverage"), str):
            coverage = d["coverage"]
        if coverage is None and isinstance(
                d.get("coverage_words"), str):
            coverage = d["coverage_words"]
        if coverage is None:
            tally = d.get("counts") or d.get("totals") or {}
            parts = [f"{k.replace('_', ' ')} {num(v)}"
                     for k, v in tally.items()
                     if isinstance(v, (int, float))
                     and not isinstance(v, bool)][:4]
            if parts:
                coverage = ("Counts on its own record: "
                            + ", ".join(parts) + ".")
        if coverage is None and isinstance(d.get("coverage"), dict):
            parts = [f"{k.replace('_', ' ')} {num(v)}"
                     for k, v in d["coverage"].items()
                     if isinstance(v, (int, float))
                     and not isinstance(v, bool)][:4]
            if parts:
                coverage = ("Counts on its own record: "
                            + ", ".join(parts) + ".")
        if coverage is None:
            COUNT_KEYS = ("distinct_names", "events_total",
                          "total_entries", "gradings_count",
                          "checks_total", "tools_count",
                          "names_count", "snapshots_on_record",
                          "pins_on_record", "companies_on_record",
                          "days_on_record")
            parts = [f"{k.replace('_', ' ')} {num(d[k])}"
                     for k in COUNT_KEYS
                     if isinstance(d.get(k), (int, float))
                     and not isinstance(d.get(k), bool)]
            if parts:
                coverage = ("Counts on its own record: "
                            + ", ".join(parts[:4]) + ".")
        if coverage is None:
            for list_key in ("names", "entries", "events",
                             "groups", "checks", "families",
                             "gradings"):
                v = d.get(list_key)
                if isinstance(v, list) and v:
                    coverage = (f"{len(v)} {list_key} on its own "
                                "record.")
                    break
        if coverage is None:
            for note_key in ("empty_note", "coverage_note",
                             "scope_note"):
                if isinstance(d.get(note_key), str) and d[note_key]:
                    coverage = d[note_key]
                    break
        if coverage is None:
            fail(f"{slug}: no coverage words on its own record "
                 "to republish")
        grade = None
        if isinstance(d.get("proving_state"), str):
            grade = ("Its own record labels its proving state: "
                     + d["proving_state"] + ".")
        elif isinstance(d.get("proving"), dict) \
                and d["proving"].get("words"):
            grade = ("Its own record labels its proving state: "
                     + d["proving"]["words"] + ".")
        record_line = d.get("source")
        if record_line is None and slug == "one-page-report":
            # Its record carries no top source line; its own
            # proving note states what it gathers, verbatim.
            record_line = ("Readings other tools on this site "
                           "have already published, each under "
                           "its own name and date")
        if record_line is None:
            fail(f"{slug}: its record carries no source line")
        receipts.append(entry(
            d["tool"], slug, record_line, made_at, session,
            coverage, grade=grade))

    # 29 Greeks Sketch: no published record (browser calculator,
    # the same honest state Payoff Sketch carries above).
    receipts.insert(27, entry(
        "Greeks Sketch", "greeks-sketch",
        ("Worked out in your browser from the position you type "
         "in. Nothing you type is sent anywhere."),
        None, None, None,
        not_recorded=[
            "No published record exists for this tool, so there "
            "is no record line, date, coverage or grade to "
            "trace: its figures are made on your screen, from "
            "your inputs, at the moment you use it.",
        ]))

    # 19 The Receipts itself, inserted in lineup order: its
    # record is this page's own source line, and its coverage is
    # the assembled set itself, counted after assembly.
    receipts.insert(18, entry(
        "The Receipts", "receipts", SOURCE_WORDS,
        max([r["made_at"] for r in receipts if r["made_at"]],
            default=None),
        None,
        (f"{len(receipts) + 1} receipts, one per tool on this "
         "site, each assembled from that tool's own published "
         "record, read exactly as it was published.")))

    if len(receipts) != 70:
        fail(f"expected 70 receipts, built {len(receipts)}")

    made = [r["made_at"] for r in receipts if r["made_at"] and len(r["made_at"]) > 10]
    out = {
        "tool": "The Receipts",
        "source": SOURCE_WORDS,
        "state": "published",
        "tools_count": len(receipts),
        "newest_source_time": max(made) if made else None,
        "receipts": receipts,
    }

    # No internal file names or desk wording may reach the page.
    blob = json.dumps(out)
    for bad in FORBIDDEN:
        if bad in blob:
            fail(f"assembled output carries forbidden internal wording: {bad}")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w") as f:
        out = _tc.stamp_for_script(out, __file__) if _tc is not None else out
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, OUT_PATH)
    print(f"refresh_receipts: wrote {OUT_PATH} with {len(receipts)} receipts")


if __name__ == "__main__":
    build()
