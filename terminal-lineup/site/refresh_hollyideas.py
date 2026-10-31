#!/usr/bin/env python3
"""Refresh the Holly Ideas data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: the Qualified Board's published record for its
freshest session (the 50 published names, each with its closing
price, its combined score, the state of each of its eight checks
and whether it passed every check) and The Record's published
grading of the board's passed-every-check calls as one group (its
strongest block: how many such calls there are across the sessions
on record, and at 1, 5 and 21 trading days how many are graded, how
many rose, and the average and middle moves, or the date the first
grades are due). The Proving Ground's published vocabulary supplies
this page's proving state label.

Reconstruction choices: the stream is exactly the board's
passed-every-check names among its 50 published names for the
session, in the board's own score order, and nothing else: no
other record on file publishes dated, named stock ideas, so no
other names are streamed. Each idea's trigger is its own eight
checks exactly as the board recorded them (which checks were in
favor, which in between, which had not enough data), in plain
words. Grading is attached as the group's only, worded from The
Record's strongest block exactly as published: no grade exists for
any single idea, so none is shown or invented, and no idea is
called a recommendation or given a confidence of its own.

What a figure is, in plain words, printed on the page: an idea is
a stock name the board's eight checks all passed for that trading
day; its trigger is the checks themselves, and its grading state
is the graded record of all such passed names together.

Fail-closed rules:
- If any published record read here is missing, the refresh stops.
- If the number of passed-every-check names carried disagrees
  with the board's own published passed count for the session,
  the refresh stops.
- If a streamed name's passed flag disagrees with its own missed
  list, or a check carries a state the board does not use, the
  refresh stops.
- If The Record carries no board sessions at all, the refresh
  stops. A board session The Record does not carry yet is stated
  as a lag in the grading words, not a stop: the board is a
  morning product and The Record an evening one.
- If The Record's strongest block cannot be matched to its own
  session groups (the passed calls in its groups must add up to
  the strongest block's call count, and its 1-day figures must be
  complete), the refresh stops rather than publishing grading
  words that do not trace to the record.
- If the Proving Ground's vocabulary does not carry the proving
  state, the refresh stops.
- If any assembled string carries internal wording (file names or
  record jargon), the refresh stops.

Honesty rules:
- Dates and times are read off the records, never from the clock,
  so running this script twice produces the same file, byte for
  byte.
- The stream never calls an idea a recommendation and never
  attaches a confidence the record does not carry.

Usage: python3 refresh_hollyideas.py
"""

import json
import os
import sys
from datetime import date

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD_PATH = os.path.join(HERE, "board", "data.json")
RECORD_PATH = os.path.join(HERE, "record", "data.json")
PROVING_PATH = os.path.join(HERE, "proving-ground", "data.json")
OUT_PATH = os.path.join(HERE, "holly-ideas", "data.json")

CHECK_STATES = {
    "in_favor": "in favor",
    "in_between": "in between",
    "against": "against",
    "no_data": "not enough data to judge",
}

FORBIDDEN = ("morgue", ".json", ".py", "ledger", "data file",
             "dataset", "nbbo", "sleeve", "scorecard")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Holly Ideas refresh: {message}", file=sys.stderr)
    return 1


def long_date(iso):
    y, m, d = (int(p) for p in iso.split("-"))
    return date(y, m, d).strftime("%A, %B %d, %Y").replace(" 0", " ")


def pct(v):
    return f"{v:+.2f}%"


def build():
    for path in (BOARD_PATH, RECORD_PATH, PROVING_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    board = load_json(BOARD_PATH)
    record = load_json(RECORD_PATH)
    proving = load_json(PROVING_PATH)

    session = board.get("session")
    if not session:
        return fail("the board record carries no session date; "
                    "refusing to guess.")
    groups = board.get("groups") or []
    if len(groups) != 1 or groups[0].get("session") != session:
        return fail("the board record does not carry exactly one "
                    "group for its session; refusing to publish.")
    names = groups[0].get("names") or []
    counts = board.get("counts") or {}
    if len(names) != counts.get("names_published"):
        return fail("the board record's published name count "
                    "disagrees with the names it carries; refusing "
                    "to publish.")

    passed = [n for n in names if n.get("passed_every_check")]
    if len(passed) != counts.get("passed_every_check_published"):
        return fail("the passed-every-check names carried "
                    f"({len(passed)}) disagree with the board's "
                    "published passed count for the session "
                    f"({counts.get('passed_every_check_published')}); "
                    "refusing to publish.")

    proving_state = None
    for state in proving.get("states") or []:
        if state.get("key") == "proving":
            proving_state = state
    if not proving_state or not proving_state.get("words") or \
            not proving_state.get("definition"):
        return fail("the Proving Ground's vocabulary does not "
                    "carry the proving state; refusing to publish "
                    "a proving label of our own.")

    # The Record's strongest block must add up from its own
    # session groups. The board session itself joins The Record
    # when the engine job next refreshes it (the board is a
    # morning product, The Record an evening one), so a board
    # session the Record does not carry yet is a stated lag in
    # the grading words below, never a refusal: the ideas are
    # the board's, dated to its session, and the grading words
    # describe the record exactly as it stands (joined-consumer
    # semantics, hookup cure 2026-10-30; the old demand refused
    # every run between the board advancing and the Record
    # refreshing).
    rec_board = record.get("board") or {}
    rec_groups = rec_board.get("groups") or []
    rec_sessions = [g.get("session") for g in rec_groups]
    if not rec_groups:
        return fail("The Record carries no board sessions; "
                    "refusing to publish ideas whose grading "
                    "record cannot be stated.")
    board_session_in_record = session in rec_sessions
    passed_in_record = sum(
        1 for g in rec_groups for c in g.get("calls") or []
        if c.get("passed_every_check"))
    strongest = rec_board.get("strongest") or {}
    if strongest.get("calls") != passed_in_record:
        return fail("The Record's strongest block "
                    f"({strongest.get('calls')} calls) does not "
                    "match the passed calls in its own session "
                    f"groups ({passed_in_record}); refusing to "
                    "publish grading words that do not trace.")
    horizons = strongest.get("horizons") or {}
    h1 = horizons.get("1d") or {}
    if h1.get("state") != "graded" or \
            h1.get("rose_count", -1) + h1.get("did_not_rise_count", -2) \
            != h1.get("graded_count"):
        return fail("The Record's 1-day grading of the passed "
                    "calls is incomplete or does not add up; "
                    "refusing to publish it.")
    # TRADING-PATH-HOLLY-20261031: every horizon is stated from
    # its own state, graded or not yet graded. Before this cure
    # the 5-day and 21-day horizons were demanded to be
    # not_yet_graded, so the first time the 5-day horizon matured
    # (the Record rebuild that carried the 2026-10-30 board
    # session) this refresh failed closed and Holly stayed one
    # session behind its board permanently.
    def horizon_words(label, h):
        if h.get("state") == "graded":
            if h.get("rose_count", -1) + \
                    h.get("did_not_rise_count", -2) != \
                    h.get("graded_count"):
                return None
            return (f"At {label}, {h['graded_count']} are graded "
                    f"so far: {h['rose_count']} rose and "
                    f"{h['did_not_rise_count']} did not rise, "
                    f"average {pct(h['average_pct'])}, middle "
                    f"{pct(h['middle_pct'])}.")
        if h.get("state") == "not_yet_graded" and \
                h.get("first_grade_date"):
            return (f"At {label}, not yet graded: the first "
                    f"grades are due after the close on "
                    f"{long_date(h['first_grade_date'])}.")
        return None

    h5_words = horizon_words("5 days", horizons.get("5d") or {})
    h21_words = horizon_words("21 days", horizons.get("21d") or {})
    if h5_words is None or h21_words is None:
        return fail("The Record's 5-day or 21-day grading state "
                    "for the passed calls cannot be stated "
                    "plainly; refusing to publish.")

    grading_words = (
        f"Graded as one group, exactly as the public record "
        f"carries them: {strongest['calls']} calls that passed "
        f"every check across the {len(rec_groups)} board sessions "
        f"on record. At the 1-day mark, {h1['graded_count']} are "
        f"graded so far: {h1['rose_count']} rose and "
        f"{h1['did_not_rise_count']} did not rise, average "
        f"{pct(h1['average_pct'])}, middle {pct(h1['middle_pct'])}. "
        f"{h5_words} "
        f"{h21_words} "
        "No single idea carries a grade of its own; the grade "
        "belongs to the group."
        + ("" if board_session_in_record else
           f" The board session this page's ideas come from, "
           f"{long_date(session)}, is not in The Record yet; "
           f"it joins the graded record when The Record next "
           f"refreshes."))

    ideas = []
    for n in passed:
        if n.get("missed"):
            return fail(f"{n.get('symbol')} is flagged as passing "
                        "every check but carries a missed list; "
                        "refusing to publish.")
        checks = []
        for c in n.get("checks") or []:
            if c.get("state") not in CHECK_STATES:
                return fail(f"{n.get('symbol')} carries a check "
                            "state the board does not use; "
                            "refusing to publish.")
            checks.append({
                "name": c["name"],
                "state": c["state"],
                "state_words": CHECK_STATES[c["state"]],
                "score": c.get("score"),
            })
        if len(checks) != n.get("checks_total", 8):
            return fail(f"{n.get('symbol')} does not carry its "
                        "full set of checks; refusing to publish "
                        "a partial trigger.")
        favor = [c["name"] for c in checks
                 if c["state"] == "in_favor"]
        between = [c["name"] for c in checks
                   if c["state"] == "in_between"]
        against = [c["name"] for c in checks
                     if c["state"] == "against"]
        nodata = [c["name"] for c in checks
                  if c["state"] == "no_data"]
        if len(favor) != n.get("checks_in_favor"):
            return fail(f"{n.get('symbol')}'s checks in favor do "
                        "not add up from its own check list; "
                        "refusing to publish.")
        trigger = (f"Passed every check on the board for this "
                   f"day: {len(favor)} of its {len(checks)} checks "
                   f"in favor ({'; '.join(favor)})")
        if between:
            trigger += f"; in between ({'; '.join(between)})"
        if against:
            trigger += f"; against ({'; '.join(against)})"
        if nodata:
            trigger += (f"; not enough data to judge "
                        f"({'; '.join(nodata)})")
        trigger += "; and it missed none of the board's set bars."
        ideas.append({
            "symbol": n["symbol"],
            "sector": n.get("sector"),
            "close": n.get("close"),
            "score": n.get("score"),
            "checks_in_favor": n.get("checks_in_favor"),
            "checks_total": n.get("checks_total"),
            "data_behind_score_pct": n.get("data_behind_score_pct"),
            "checks": checks,
            "trigger": trigger,
        })

    data = {
        "tool": "Holly Ideas",
        "state": "published",
        "session": session,
        "session_long": long_date(session),
        "published_at_utc": board.get("published_at_utc"),
        "source": board.get("source"),
        "proving_state": proving_state["words"],
        "proving_note": proving_state["definition"],
        "record_sessions": rec_sessions,
        "board_session_in_record": board_session_in_record,
        "grading_words": grading_words,
        "ideas": ideas,
        "counts": {
            "ideas_streamed": len(ideas),
            "names_checked": counts.get("names_checked"),
            "names_published": counts.get("names_published"),
            "passed_every_check_published":
                counts.get("passed_every_check_published"),
            "passed_every_check_all":
                counts.get("passed_every_check_all"),
        },
        "receipt": {
            "session": session,
            "source": board.get("source"),
            "coverage": (f"{len(ideas)} ideas for "
                         f"{long_date(session)}: the names that "
                         f"passed every check among the "
                         f"{counts.get('names_published')} the "
                         f"board published that day, out of "
                         f"{counts.get('names_checked'):,} names "
                         "checked in all"),
        },
    }

    def walk(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for v in value.values():
                yield from walk(v)
        elif isinstance(value, list):
            for v in value:
                yield from walk(v)

    for text in walk(data):
        low = text.lower()
        for bad in FORBIDDEN:
            if bad in low:
                return fail(f"assembled data carries internal "
                            f"wording ({bad!r}); refusing to "
                            "publish.")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, OUT_PATH)
    print(f"Wrote {OUT_PATH} (session {session}, "
          f"{len(ideas)} ideas)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
