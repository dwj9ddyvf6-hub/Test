#!/usr/bin/env python3
"""Refresh the Router data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: the Router's own recorded state, read exactly as it
stands in the records this site has already published. The
Replication Wire carries the Router's own claim and its record so
far (7 sessions, none graded, cannot be tested on the records on
hand, as re-read October 30, 2026). The Grade-A
Board carries the top-grade forecasters the Router may route among
(63 in total: 57 that forecast how much prices move and 6 warning
flags), counted from its own published groups. The Proving Ground
carries the proving-state words this page uses. The one recorded
routing day (October 16, 2026: 700 names checked, 4 told to avoid,
696 with no call) and the Router's routing rule, in plain words,
are the recorded rule and day carried in this script, taken from
the Router's own program record as inspected before this build;
the refresh checks every number it can against the published
records above and publishes nothing if any of them disagree.

Reconstruction choices, stated as ours: (1) Today's standing
answer is no call, because no live routed state for the latest
session exists on any record found: the Router's default is no
call, and this page publishes that default rather than inventing
a routing decision for today. (2) The session record shows the
one routing day that exists on record, with its counts and its
four avoid names exactly as recorded, and states plainly that
the 7-session forward record the design cites is not on record:
no session list and no grades were found for it, so none are
shown. The record's youth is stated in words, never as a grade.
(3) The routing rule is stated in plain words from the recorded
rule: what it watches, every condition that must hold before it
may name a forecaster, the verdict words it can give for names
you do not own and names you do, and why it usually says no call.
(4) No time on this page comes from the clock: every date comes
from the records read, so running this script twice produces the
same file.

Non-claims: this page does not route anything today, does not
re-derive a routing decision, does not grade the Router, does
not reconstruct the missing session list, and does not publish
any number beyond what the records above carry.

Fail-closed rules: if the Wire's record is missing or not
published, if the Router's entry on the Wire is missing or its
words differ from the recorded ones (its claim, its 7-session
sample, its cannot-be-tested result, its cannot-be-tested
verdict), if the Wire's own counts disagree with its entries, if
the Grade-A Board is missing or its published counts (63 top
grade, 57 movement, 6 warning flags) disagree with a recount of
its own groups, if the Proving Ground's proving-state words are
missing, if the recorded routing day's counts do not add up
(4 avoid plus 696 no call equals 700 checked), or if any words
assembled here carry an internal file name or desk wording, the
refresh stops and publishes nothing.

Usage: python3 refresh_router.py
"""

import json
import os

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    from verdict_vocabulary import VERDICT_WORDS
except ImportError:  # refresh stays runnable standalone
    VERDICT_WORDS = {
        "held": "Held up",
        "partly": "Partly held up",
        "did_not": "Did not hold up",
        "not_yet": "Not yet tested",
        "untestable": "Cannot be tested on the records on hand",
    }

HERE = os.path.dirname(os.path.abspath(__file__))
WIRE_PATH = os.path.join(HERE, "replication-wire", "data.json")
BOARD_PATH = os.path.join(HERE, "grade-a-board", "data.json")
PROVING_PATH = os.path.join(HERE, "proving-ground", "data.json")
OUT_PATH = os.path.join(HERE, "router", "data.json")

SOURCE_WORDS = ("Our own forecast program's records: the Router's own published "
                "record on the research wire, and the board of forecast recipes "
                "that earned the top grade")

FORBIDDEN = (".json", ".md", ".py", ".jsonl", "morgue", "Femto", "Midna",
             "Codex", "ledger", "router.py", "promoted-book", "ABSTAIN",
             "Newey", "quintile", "dv20", "fid:")

ROUTER_CLAIM = ("The forecast program's one-verdict-per-stock router "
                "(Buy, Wait, Avoid, or Sit Out) has a track record.")
ROUTER_RESULT = ("Cannot be tested on the records on hand: its record is "
                 "7 sessions and provisional, and the program's own plan "
                 "requires its card to say exactly that, in words, until "
                 "the record grows up. The missing record is a graded "
                 "track record for this router: sessions of its verdicts "
                 "with their outcomes graded against what the stocks did "
                 "next, in the number its own maturity bar requires. No "
                 "graded record for it exists on hand.")
ROUTER_SAMPLE = "7 trading sessions of record, none of them graded"
ROUTER_WHEN = "Record as of October 2026; re-read October 30, 2026"

# The one routing day that exists on record, exactly as recorded.
ROUTING_DAY = {
    "date": "October 16, 2026",
    "checked": 700,
    "avoid": 4,
    "no_call": 696,
    "what": ("700 names were drawn at random from the research records and "
             "checked; none of them was recorded as owned. 4 names were "
             "told to avoid and the other 696 got no call, every one for "
             "the same recorded reason: no top-grade forecaster in the "
             "book matched that name that day."),
    "avoid_names": [
        {"name": "HODO", "why": "Flagged by the big opening gap warning, "
                                "in its 20-session form, for names in the "
                                "second fifth of trading activity."},
        {"name": "JYD", "why": "Flagged by the sudden pump warning, in "
                               "its form counted across every stock and "
                               "every day."},
        {"name": "SEED", "why": "Flagged by the sudden pump warning, in "
                                "its form counted across every stock and "
                                "every day."},
        {"name": "OXBR", "why": "Flagged by the big opening gap warning, "
                                "in its 5-session form for fear days when "
                                "the market sat above a rising 200-day "
                                "average."},
    ],
    "grades": ("No outcomes or grades are recorded for that day. The same "
               "four flagged names, if they had been held, would have got "
               "no call that day: at their own trading costs, the careful "
               "lower bound for selling them was at or below zero."),
}


def fail(msg):
    raise SystemExit("refresh_router: FAIL: " + msg)


def build():
    for path, label in ((WIRE_PATH, "the research wire's published record"),
                        (BOARD_PATH, "the top-grade board's published record"),
                        (PROVING_PATH, "the proving ground's published record")):
        if not os.path.exists(path):
            fail(label + " is missing")
    with open(WIRE_PATH, encoding="utf-8") as f:
        wire = json.load(f)
    with open(BOARD_PATH, encoding="utf-8") as f:
        board = json.load(f)
    with open(PROVING_PATH, encoding="utf-8") as f:
        proving = json.load(f)

    if wire.get("state") != "published":
        fail("the research wire's record is not in the published state")
    claims = wire.get("claims") or []
    recomputed = {"total": len(claims)}
    for verdict in VERDICT_WORDS:
        recomputed[verdict] = 0
    router_entry = None
    for c in claims:
        v = c.get("verdict")
        if v not in recomputed:
            fail(f"a claim on the wire carries an unknown verdict: {v!r}")
        recomputed[v] += 1
        if c.get("claim") == ROUTER_CLAIM:
            router_entry = c
    for key, value in recomputed.items():
        if (wire.get("counts") or {}).get(key) != value:
            fail(f"the wire's published count for {key!r} disagrees with "
                 f"its own entries ({value})")
    if router_entry is None:
        fail("the Router's own entry is missing from the wire's record")
    if router_entry.get("result") != ROUTER_RESULT:
        fail("the Router's recorded result on the wire has changed")
    if router_entry.get("sample") != ROUTER_SAMPLE:
        fail("the Router's recorded session count on the wire has changed: "
             f"{router_entry.get('sample')!r}")
    if router_entry.get("when") != ROUTER_WHEN:
        fail("the Router's recorded date on the wire has changed")
    if router_entry.get("verdict") != "untestable" or \
            router_entry.get("verdict_words") != \
            "Cannot be tested on the records on hand":
        fail("the Router's verdict on the wire is not 'cannot be tested "
             "on the records on hand'")

    if board.get("state") != "published":
        fail("the top-grade board's record is not in the published state")
    bcounts = board.get("counts") or {}
    groups = board.get("groups") or []
    warn_groups = [g for g in groups
                   if str(g.get("kind", "")).startswith("A warning flag")]
    move_groups = [g for g in groups if g not in warn_groups]
    warn_cells = sum(g.get("count", 0) for g in warn_groups)
    move_cells = sum(g.get("count", 0) for g in move_groups)
    total_cells = sum(g.get("count", 0) for g in groups)
    if bcounts.get("grade_a") != 63 or total_cells != 63:
        fail("the board's top-grade count disagrees with its own groups")
    if bcounts.get("warning_cells") != 6 or warn_cells != 6:
        fail("the board's warning-flag count disagrees with its own groups")
    if bcounts.get("movement_cells") != 57 or move_cells != 57:
        fail("the board's movement count disagrees with its own groups")
    warn_titles = sorted(g["title"] for g in warn_groups)
    expected_warn = sorted([
        "Beaten-down stocks that bounce: a warning flag, next 20 trading days",
        "Sudden pumps on heavy volume: a warning flag, next 20 trading days",
        "Big opening gaps up: a warning flag, next 20 trading days",
        "Big opening gaps up: a warning flag, next 5 trading days",
    ])
    if warn_titles != expected_warn:
        fail("the board's warning-flag groups have changed")

    proving_state = None
    for s in proving.get("states") or []:
        if s.get("key") == "proving":
            proving_state = s
    if not proving_state or proving_state.get("words") != "Still being proven":
        fail("the proving ground's proving-state words are missing")

    day = ROUTING_DAY
    if day["avoid"] + day["no_call"] != day["checked"]:
        fail("the recorded routing day's counts do not add up")
    if len(day["avoid_names"]) != day["avoid"]:
        fail("the recorded routing day's avoid names do not match its count")

    out = {
        "tool": "The Router",
        "source": SOURCE_WORDS,
        "state": "published",
        "proving_state": proving_state["words"],
        "proving_words": proving_state["definition"],
        "standing_answer": "No call",
        "standing_reason": ("No live routed state for the latest session is "
                            "on record, and no call is this tool's default "
                            "answer. It names a forecaster to follow only "
                            "when every condition in its rule below is met, "
                            "and nothing on record says that has happened "
                            "for today."),
        "youth_words": ("Its record is 7 sessions and early: too young to "
                        "grade. The record stays stated in words like that, "
                        "with no grade, until the record grows up."),
        "counts": {
            "book_entries": 388,
            "top_grade": 63,
            "on_probation": 325,
            "direction_top_grade": 6,
            "movement_top_grade": 57,
            "sessions_cited": 7,
            "routing_days_on_record": 1,
        },
        "rule": {
            "watches": ("For each name, each day, it watches: whether the "
                        "day's trading is finished (only a closed day "
                        "counts); whether you own the name, do not own it, "
                        "or that is not known (not known means no call); "
                        "the day's setting (a fear day or a calm day, "
                        "whether the market sits above its 200-day average "
                        "and whether that average is rising, the fear "
                        "gauge's reading, how actively the name trades "
                        "compared with other names, the name's age and its "
                        "trend state; any part of the setting that is not "
                        "known never matches); each forecaster's reading "
                        "for the name (a warning flag counts as on only "
                        "when its reading is clearly on, and a score counts "
                        "only when it sits in the top fifth or the bottom "
                        "fifth of all scores that day, matching the "
                        "direction the forecaster was graded on); what it "
                        "costs to trade this name, measured for this name; "
                        "how much money usually trades in the name; and "
                        "any plan already recorded for the name."),
            "names_a_forecaster_when": [
                "A forecaster in the book that earned the top grade matches the name on every part of the setting it was graded under, and that forecaster has a reading for the name today.",
                "The day's trading is finished, the name's own trading cost is measured, and how much money trades in the name is measured and inside the range the forecaster was graded on.",
                "The forecaster was scored on at least 30 dates in every stretch of time it was graded over.",
                "After subtracting trading costs (both sides of a buy, one side of a sale, none for avoid or hold), the careful lower end of what following it would have gained per day, over doing the best other thing including doing nothing, is still above zero. The careful lower end allows for the fact that its graded days overlap, uses the 95% careful level, and takes the weakest of its graded stretches, so one good stretch cannot carry it.",
            ],
            "one_name_one_call": ("One name gets one call: the passing "
                                  "forecaster with the strongest careful "
                                  "lower end speaks, and any others that "
                                  "pass are listed as support, never added "
                                  "together. If passing forecasters point "
                                  "both ways, that is a conflict and the "
                                  "answer is no call."),
            "labels": ("For a name you do not own, the call can be Buy, "
                       "Wait, or Avoid. For a name you own, it can be Hold, "
                       "Trim, or Sell: Sell needs the careful lower end to "
                       "stay above zero at the stricter 99% careful level "
                       "too, otherwise the strongest exit call is Trim. "
                       "Wait means the evidence supports a buy, or an exit, "
                       "but a check against the plan already recorded for "
                       "the name, or a stop switch, is holding it back."),
            "never_routes": ("Forecasters that only say how much a price "
                             "may move never set a call; they are shown as "
                             "a warning about risk only. Forecasters on "
                             "probation, the second grade down, and any "
                             "that were marked down are shown but never "
                             "routed. Anything that fails, is missing, or "
                             "cannot be checked means no call, with the "
                             "reason recorded."),
            "why_usually_no_call": ("That is why it usually says no call: "
                                    "every condition has to hold at once, "
                                    "most names match no top-grade "
                                    "forecaster on a given day, and on the "
                                    "book as recorded no buy-side "
                                    "forecaster reached the top grade at "
                                    "all, so a Buy call cannot be given "
                                    "from evidence yet. Avoid can be given, "
                                    "and Trim or Sell on a name you own."),
        },
        "forecasters": [
            {"name": "Beaten-down stocks that bounce (warning flag)",
             "what": "Flags a stock whose price is at or below 60% of its "
                     "highest price of the last 60 trading days and that "
                     "has still bounced at least 15% in the last 5 trading "
                     "days. It expects flagged stocks to do worse over the "
                     "next 20 trading days.",
             "standing": "Earned the top grade. 1 top-grade form, counted "
                         "across every stock and every day.",
             "can_route": "Yes: it can set an Avoid call."},
            {"name": "Sudden pumps on heavy volume (warning flag)",
             "what": "Flags a stock that is up at least 30% in the last 5 "
                     "trading days on at least 3 times its usual trading "
                     "volume. It expects flagged stocks to do worse over "
                     "the next 20 trading days.",
             "standing": "Earned the top grade. 2 top-grade forms: one "
                         "counted across every stock and every day, and "
                         "one for calm days and names in the third fifth "
                         "of trading activity.",
             "can_route": "Yes: it can set an Avoid call."},
            {"name": "Big opening gaps up (warning flag)",
             "what": "Flags a stock that opened at least 10% above its "
                     "previous day's closing price. Its forms expect "
                     "flagged stocks to do worse over the next 20 trading "
                     "days, or the next 5, depending on the form.",
             "standing": "Earned the top grade. 3 top-grade forms: one "
                         "for names in the second fifth of trading "
                         "activity over 20 days, one for calm days in that "
                         "same fifth over 5 days, and one for fear days "
                         "when the market sat above a rising 200-day "
                         "average over 5 days.",
             "can_route": "Yes: it can set an Avoid call."},
            {"name": "How-much-prices-move forecasters",
             "what": "57 forecasters that say how much a price is likely "
                     "to move, not which way: 48 built from past movement "
                     "patterns, 7 from a share of trading measure, and 2 "
                     "from options positioning.",
             "standing": "Earned the top grade in the study, as movement "
                         "forecasts.",
             "can_route": "No: they never set a call. They are shown as a "
                          "warning about risk only."},
            {"name": "Buy-side forecasters",
             "what": "Forecasters that point up, toward buying.",
             "standing": "None reached the top grade in the book as "
                         "recorded. The book holds 388 entries in total: "
                         "63 at the top grade and 325 one grade down, on "
                         "probation.",
             "can_route": "No: with no top-grade buy-side forecaster on "
                          "the book, a Buy call, or a Hold call from "
                          "evidence, cannot be given yet."},
            {"name": "Forecasters on probation",
             "what": "325 entries in the book that earned the second "
                     "grade. They are kept in the book and shown when "
                     "they match a name.",
             "standing": "On probation: shown, never routed.",
             "can_route": "No: a forecaster on probation is never the "
                          "reason for a call."},
        ],
        "session_record": [day],
        "forward_record": {
            "cited_sessions": 7,
            "on_record": False,
            "words": ("The record this tool's design points to is 7 "
                      "sessions long, and its youth is stated above in "
                      "words. But the list of those sessions is not on "
                      "record: no session dates, no per-session calls and "
                      "no grades for them were found in any record this "
                      "site can read, and the program's own report from "
                      "October 27, 2026 says no forward row exists yet and "
                      "no row has been graded, because the record starts "
                      "with the first hosted run. So this page shows the "
                      "one routing day that is on record, above, and does "
                      "not invent the other sessions."),
        },
        "wire": {
            "result": router_entry["result"],
            "verdict_words": router_entry["verdict_words"],
            "when": router_entry["when"],
            "grading_run_at": wire.get("grading_run_at"),
        },
    }

    blob = json.dumps(out, ensure_ascii=False)
    for bad in FORBIDDEN:
        if bad in blob:
            fail(f"assembled output carries forbidden wording: {bad!r}")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        out = _tc.stamp_for_script(out, __file__) if _tc is not None else out
        json.dump(out, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, OUT_PATH)
    print(f"refresh_router: wrote {OUT_PATH} (standing answer: no call; "
          f"book 388, top grade 63, direction 6, movement 57; "
          f"1 routing day on record; 7-session list not on record)")


if __name__ == "__main__":
    build()
