#!/usr/bin/env python3
"""Refresh the Fear-Day Forecaster data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: three records already on file, read exactly as
published. (1) The Fear Day List's published data (tool 16): the
fear-day definition in its published words, the local history on
file (its coverage figures, the fear-gauge readings and the index
sessions, imported from the list's own record at runtime, never
pinned here), exactly 1 qualifying day (October 16, 2026), and
a follow-through state of not counted.
(2) The Pullback Norm's published research record (tool 17), which
carries the deep-history study behind this ranking: deep daily
price history, 2016 to 2026, 6,385 names including delisted ones;
rising-trend names on fear days, each name's move measured against
the same day's average move; rank links +0.026 (strength 4.3) over
20 sessions in 2016 to 2022, +0.031 (strength 4.3) over 20 sessions
in 2023 onward, +0.062 (strength 9.8) over 60 sessions in 2023
onward. (3) The forecast-search record of October 27, 2026: its
evidence summary carries the same study's 2023-onward spread of
+0.81 points per 20 sessions between its top and bottom fifths,
and its result table carries the re-test of this same ranking on
fear days with a high fear-gauge reading (earlier part +0.039,
held-back part +0.061, buying the top fifth netted -0.027 per
chance after costs, marked cost-failed), and its own notes carry
that search's fear-day meaning (SPY down at least 1% in a day, or
SPY's close under its average of the last 50 sessions).

Reconstruction choices, stated as ours: (1) The fear-day
definition at the top of the page is the Fear Day List's published
definition, imported word for word from its data file, never
forked; if that file's wording ever changes, this refresh stops.
(2) The deep-history study's numbers are published as that study's
result, in its own terms: the page states the study's own fear-day
meaning next to them and never implies they were counted under
the published definition at the top. The study's number of fear
days is not on record, so no event count, rate or win rate is
shown for it. (3) The re-test ships whole: the ranking showing up
again and the top fifth losing money after costs are both on the
page, or neither is. (4) The local record is a thin cell (1 event,
under the 30-event line): counts only, no percentage, no average,
and no forecast is drawn from one event. (5) The forward record
starts empty: fear days from the studies record date onward will
be recorded and graded at 1, 5 and 21 sessions; none has been
recorded yet, and the page says exactly that.

Non-claims: this page makes no forecast, names no stocks, and
shows no expected move, win rate or average outcome. It does not
claim the one local fear day led to anything (its follow-through
was never counted), and it does not present the deep study's
ranking numbers as belonging to fear days in general or to any
other method.

Fail-closed rules: if the Fear Day List's published definition,
qualifying days or follow-through state disagree with the
figures this page uses, or if its coverage record does not hold
together (this page takes its coverage figures from that record
at runtime, so a malformed or self-contradictory one stops the
refresh), if the Pullback Norm's research
record disagrees with the study figures on any row, if the
evidence summary's study row disagrees on any figure or on the
+0.81 spread, if the re-test row in the search results disagrees
on its earlier part, held-back part, net per chance or cost
verdict, or if the search's own fear-day meaning is no longer on
its record, the refresh stops and publishes nothing. All
timestamps come from the sources, never the clock, so running
this script twice produces the same file.

Usage: python3 refresh_feardayforecaster.py
"""

import json
import os
import sys

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
FEARDAY_PATH = os.path.join(HERE, "fear-day", "data.json")
PULLBACK_PATH = os.path.join(HERE, "pullback-norm", "data.json")
RECORDS_DIR = os.path.expanduser(
    "~/workspace/terminal-lineup/records/forecast-search-2026-10-27")
EVIDENCE_PATH = os.path.join(RECORDS_DIR, "EVIDENCE.md")
SEARCH_PATH = os.path.join(
    RECORDS_DIR, "forecast-search-2026-10-27.json")
CONTEXTS_PATH = os.path.join(RECORDS_DIR, "contexts.py")
OUT_PATH = os.path.join(HERE, "fear-day-forecaster", "data.json")

MIN_EVENTS_FOR_PERCENT = 30

SOURCE_WORDS = ("The published studies record, the daily market "
                "history on file, and the deep-history study and "
                "re-test records on file")

PROVING_STATE = "Still being proven"
PROVING_NOTE = ("Still being proven: the ranking below rests on a "
                "finished study, but this page's own forward "
                "record has not started yet, so nothing it could "
                "say about the next fear day has been graded.")

STUDY_RESULTS = [
    {"window_sessions": 20, "era": "2016 to 2022",
     "rank_correlation": 0.026, "strength": 4.3},
    {"window_sessions": 20, "era": "2023 onward",
     "rank_correlation": 0.031, "strength": 4.3},
    {"window_sessions": 60, "era": "2023 onward",
     "rank_correlation": 0.062, "strength": 9.8},
]
STUDY_DATASET = ("Deep daily price history, 2016 to 2026, 6,385 "
                 "names including delisted ones")
STUDY_SETTING = ("Rising-trend names on fear days, each name's move "
                 "measured against the same day's average move")
STUDY_SPREAD_PTS = 0.81
STUDY_FEAR_MEANING = ("In that study, a fear day meant SPY fell at "
                      "least 1% in a day, or SPY closed below its "
                      "average of the last 50 sessions. That is "
                      "not the same as the definition at the top "
                      "of this page.")

RETEST = {"earlier_link": 0.039, "held_back_link": 0.061,
          "net_per_chance": -0.027}


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Fear-Day Forecaster refresh: {message}", file=sys.stderr)
    return 1


def find_row(rows, forecaster, target, cell):
    cols = rows["columns"]
    for raw in rows["data"]:
        row = dict(zip(cols, raw))
        if (row.get("forecaster") == forecaster
                and row.get("target") == target
                and row.get("cell") == cell):
            return row
    return None


def derive_coverage(fearday):
    """This page's coverage figures, taken from the Fear Day
    List's own published record at runtime, never pinned here.
    (Cured 2026-10-30: this refresh used to demand the pre-cure
    figures, 23 readings from September 21 to October 21, 2026,
    so once the VIX capture cure advanced the list's record to
    504 readings it refused a healthy record forever.) Returns
    None when the record does not hold together: every figure
    present, the gauge window in order, and the checked-session
    count equal to the index sessions less the first one, which
    is the list's own counting rule (the first session on file
    has no session before it to compare against)."""
    hist = fearday.get("history", {})
    try:
        readings = int(hist["fear_gauge_readings"])
        checked = int(hist["sessions_checked"])
        index_sessions = int(hist["index_sessions"])
        gauge_from = str(hist["fear_gauge_from"])
        gauge_to = str(hist["fear_gauge_to"])
    except (KeyError, TypeError, ValueError):
        return None
    if readings < 1 or index_sessions < 1:
        return None
    if gauge_from > gauge_to:
        return None
    if checked != index_sessions - 1:
        return None
    return {
        "sessions_checked": checked,
        "fear_gauge_readings": readings,
        "fear_gauge_from": gauge_from,
        "fear_gauge_to": gauge_to,
    }


def build():
    for path in (FEARDAY_PATH, PULLBACK_PATH, EVIDENCE_PATH,
                 SEARCH_PATH, CONTEXTS_PATH):
        if not os.path.exists(path):
            return fail(f"source record missing: {path}")

    fearday = load_json(FEARDAY_PATH)
    pullback = load_json(PULLBACK_PATH)
    search = load_json(SEARCH_PATH)
    with open(EVIDENCE_PATH, "r", encoding="utf-8") as fh:
        evidence = fh.read()
    with open(CONTEXTS_PATH, "r", encoding="utf-8") as fh:
        contexts = fh.read()

    # --- Tool 16's published data: definition + local record ---
    definition = fearday.get("definition", "")
    if "fell more than 1.5%" not in definition \
            or "rose more than 15%" not in definition \
            or "25 or higher" not in definition \
            or "20 or higher" not in definition:
        return fail("the Fear Day List's published definition no "
                    "longer matches the wording this page imports")
    if fearday.get("follow_through", {}).get("state") != "not_counted":
        return fail("the Fear Day List's follow-through state is no "
                    "longer 'not counted'")
    days = fearday.get("qualifying_days", [])
    if fearday.get("events") != 1 or len(days) != 1:
        return fail("the Fear Day List's qualifying-day count no "
                    "longer recomputes to exactly 1")
    day = days[0]
    expected_day = {"date": "2026-10-16", "fear_gauge_change_pct": 21.4,
                    "fear_gauge_close": 19.99, "spy_change_pct": -1.1,
                    "qqq_change_pct": -2.5}
    for key, value in expected_day.items():
        if day.get(key) != value:
            return fail(f"the Fear Day List's qualifying day disagrees "
                        f"on {key}: {day.get(key)!r} != {value!r}")
    coverage = derive_coverage(fearday)
    if coverage is None:
        return fail("the Fear Day List's coverage record does not "
                    "hold together, so this page cannot state its "
                    "coverage")

    # --- Tool 17's research record: the deep-history study ---
    research = pullback.get("research_record", {})
    if research.get("dataset") != STUDY_DATASET:
        return fail("the Pullback Norm's research record dataset "
                    "disagrees with the study dataset on this page")
    if research.get("setting") != STUDY_SETTING:
        return fail("the Pullback Norm's research record setting "
                    "disagrees with the study setting on this page")
    if research.get("results") != STUDY_RESULTS:
        return fail("the Pullback Norm's research record results "
                    "disagree with the study figures on this page")

    # --- Evidence summary: same study, spread + grade ---
    s1_lines = [ln for ln in evidence.splitlines()
                if ln.startswith("| S1 |")]
    if len(s1_lines) != 1:
        return fail("the evidence record's study row for this "
                    "ranking was not found exactly once")
    s1 = s1_lines[0]
    for token in ("+0.026", "+0.031", "+0.062", "+0.81"):
        if token not in s1:
            return fail(f"the evidence record's study row no longer "
                        f"carries {token}")

    # --- The re-test row in the search results ---
    row = find_row(search["rows"], "feat.F3", "up_excess_20",
                   "fear=fear|vix=hi")
    if row is None:
        return fail("the re-test row for this ranking was not found "
                    "in the search results on record")
    if row.get("verdict") != "cost-failed":
        return fail("the re-test row's verdict is no longer "
                    "cost-failed")
    if round(float(row["disc_mean"]), 3) != RETEST["earlier_link"]:
        return fail("the re-test row's earlier-part figure disagrees "
                    "with the figure this page uses")
    if round(float(row["hold_signed"]), 3) != RETEST["held_back_link"]:
        return fail("the re-test row's held-back figure disagrees "
                    "with the figure this page uses")
    if round(float(row["execution_net"]), 3) != RETEST["net_per_chance"]:
        return fail("the re-test row's net per chance disagrees "
                    "with the figure this page uses")

    # --- The search's own fear-day meaning ---
    if "<= -0.01" not in contexts or "50-session" not in contexts:
        return fail("the search record no longer carries its own "
                    "fear-day meaning")

    published = fearday.get("published_at_utc")
    studies_as_of = fearday.get("studies_as_of")

    data = {
        "tool": "Fear-Day Forecaster",
        "state": "unpublished",
        "proving_state": PROVING_STATE,
        "proving_note": PROVING_NOTE,
        "definition": definition,
        "source": SOURCE_WORDS,
        "studies_as_of": studies_as_of,
        "published_at_utc": published,
        "thin_threshold": MIN_EVENTS_FOR_PERCENT,
        "local_record": {
            "events": 1,
            "sessions_checked": coverage["sessions_checked"],
            "fear_gauge_readings": coverage["fear_gauge_readings"],
            "fear_gauge_from": coverage["fear_gauge_from"],
            "fear_gauge_to": coverage["fear_gauge_to"],
            "qualifying_days": days,
            "follow_through": {"state": "not_counted"},
            "thin": True,
        },
        "study": {
            "dataset": STUDY_DATASET,
            "setting": STUDY_SETTING,
            "mechanism": ("On fear days, rising-trend stocks are "
                          "ranked by how deep their dip is compared "
                          "with that same stock's own past dips."),
            "results": STUDY_RESULTS,
            "spread_pts_per_20_sessions": STUDY_SPREAD_PTS,
            "spread_words": ("top fifth against bottom fifth, "
                             "2023 onward"),
            "fear_day_meaning": STUDY_FEAR_MEANING,
            "event_count": {"state": "not_on_record"},
        },
        "retest": {
            "setting": ("Fear days with a high fear-gauge reading, "
                        "in a full re-test run on October 27, 2026"),
            "earlier_link": RETEST["earlier_link"],
            "held_back_link": RETEST["held_back_link"],
            "net_per_chance": RETEST["net_per_chance"],
            "outcome": "did not pass as something to trade",
        },
        "forward_record": {
            "state": "empty",
            "recorded": 0,
            "grade_sessions": [1, 5, 21],
        },
        "receipt": {
            "source": SOURCE_WORDS,
            "published_at_utc": published,
            "coverage": (f"Local record: 1 qualifying day among "
                         f"the {coverage['sessions_checked']} "
                         f"comparable sessions in the history on "
                         f"file, {coverage['fear_gauge_readings']} "
                         f"fear-gauge readings from "
                         f"{coverage['fear_gauge_from']} to "
                         f"{coverage['fear_gauge_to']}, "
                         f"follow-through not counted. Study "
                         f"record: deep daily price history, 2016 "
                         f"to 2026, 6,385 names including delisted "
                         f"ones; its number of fear days is not on "
                         f"record."),
        },
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, OUT_PATH)
    print(f"Fear-Day Forecaster refresh: wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
