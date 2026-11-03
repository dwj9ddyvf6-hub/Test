#!/usr/bin/env python3
"""Refresh the Signal Feed data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (2026-10-28): no disclaimer-style
copy on any reader surface of any tool, in pages or generated data,
ever.

Evidence class: a union view over records the terminal already
publishes, read exactly as published: The Record's published calls
(50 board calls in two session groups plus 6 index cards), the
Flow Tape's alerts for its freshest session (75), the Qualified
Board's passed-every-check names among its published names (19),
The Screener's passed-every-check names in its scored run (43),
and the Morning Map's cards (3). The Proving Ground's published
vocabulary supplies this page's proving state label.

Reconstruction choices: this feed adds no call, grade or figure of
its own. Every entry keeps the grading state its own source record
states, in that source's own terms: a board call in The Record's
one graded group carries that group's published grade (the record
grades the group, never a single call, so no single call is given
a win or a loss); calls and cards whose grade has not arrived are
waiting to be graded; Flow Tape alerts are not graded yet, exactly
as the tape's own note states; and entries whose own record states
no grade at all (the Board's, the Screener's and the Morning Map's
own entries) say exactly that, which is a different state from
waiting and is never merged with it. Entries are ordered newest
first by the time each source record itself carries: a per-entry
time where the record carries one, otherwise the published time
of the source's record for that session. Two entries about the
same index and session from different tools stay separate entries;
nothing is merged. No source is excluded: every source's entries
can be dated from its own record.

Fail-closed rules:
- If any of the six published records read here is missing, the
  refresh stops and publishes nothing.
- If a source's contributed count disagrees with that source's
  own published count (The Record's published total, the Flow
  Tape's published alert count, the Board's published
  passed-every-check count, the Screener's passed-every-check
  count, the Morning Map's card count), the refresh stops.
- If an entry's grading state cannot be matched to its source
  record (an unknown grade state in The Record, a Flow Tape note
  that no longer states the alerts are ungraded, or a grade field
  appearing in a record that states no grade), the refresh stops.
- If any entry cannot be dated from its own source record, the
  refresh stops rather than guessing a time for it.
- If the Proving Ground's vocabulary does not carry the proving
  state this page labels itself with, the refresh stops.
- If any assembled string carries internal wording (file names or
  record jargon), the refresh stops.

Honesty rules:
- Dates and times are read off the records, never from the clock,
  so running this script twice produces the same file, byte for
  byte.
- No entry is dropped for losing or for not being graded yet.

Usage: python3 refresh_signalfeed.py
"""

import json
import os
import sys
from datetime import date, datetime

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
RECORD_PATH = os.path.join(HERE, "record", "data.json")
FLOW_PATH = os.path.join(HERE, "flow-tape", "data.json")
BOARD_PATH = os.path.join(HERE, "board", "data.json")
SCREENER_PATH = os.path.join(HERE, "screener", "data.json")
MAP_PATH = os.path.join(HERE, "morning-map", "data.json")
PROVING_PATH = os.path.join(HERE, "proving-ground", "data.json")
OUT_PATH = os.path.join(HERE, "signal-feed", "data.json")

FORBIDDEN = ("morgue", ".json", ".py", ".jsonl", "ledger", "sleeve",
             "scorecard", "data file", "dataset", "alpaca", "finra",
             "gex", "nbbo")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Signal Feed refresh: {message}", file=sys.stderr)
    return 1


def long_date(iso):
    y, m, d = (int(p) for p in iso.split("-"))
    return date(y, m, d).strftime("%A, %B %d, %Y").replace(" 0", " ")


def parse_time(text):
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def money(value):
    if value is None:
        return "not on record"
    if value == int(value):
        return f"${int(value):,}"
    return f"${value:,.2f}"


def price(value):
    return f"${value:,.2f}"


def build():
    for path in (RECORD_PATH, FLOW_PATH, BOARD_PATH, SCREENER_PATH,
                 MAP_PATH, PROVING_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")
    record = load_json(RECORD_PATH)
    flow = load_json(FLOW_PATH)
    board = load_json(BOARD_PATH)
    screener = load_json(SCREENER_PATH)
    morning = load_json(MAP_PATH)
    proving = load_json(PROVING_PATH)

    proving_entry = None
    for state in proving.get("states") or []:
        if state.get("key") == "proving":
            proving_entry = state
    if proving_entry is None:
        return fail("the Proving Ground's vocabulary does not "
                    "carry the proving state; refusing to publish "
                    "a proving label of our own.")

    entries = []

    # ---- The Record: board calls --------------------------------
    totals = record.get("totals") or {}
    board_part = record.get("board") or {}
    record_board_count = 0
    for group in board_part.get("groups") or []:
        session = group.get("session")
        grades = group.get("grades") or {}
        one_day = grades.get("1d") or {}
        if one_day.get("state") == "graded":
            grading_state = "graded_with_its_group"
            grading_words = (
                f"Graded with its day's group at the 1-day mark: "
                f"{one_day['graded_count']} of "
                f"{one_day['graded_of_group']} of these calls "
                f"graded, {one_day['rose_count']} rose and "
                f"{one_day['did_not_rise_count']} did not "
                f"(average {one_day['average_pct']:+.2f}%, middle "
                f"{one_day['middle_pct']:+.2f}%). The grade belongs "
                f"to the group; no single call is given a win or "
                f"a loss of its own.")
        elif all((grades.get(h) or {}).get("state")
                 == "not_yet_graded" for h in ("1d", "5d", "21d")):
            first = one_day.get("first_grade_date")
            grading_state = "waiting_to_be_graded"
            grading_words = (
                "Waiting to be graded. Its first grade arrives "
                f"after the close on {long_date(first)}."
                if first else "Waiting to be graded.")
            if not first:
                return fail("a Record board group is waiting to be "
                            "graded but carries no first grade "
                            "date; refusing to publish.")
        else:
            return fail("a Record board group carries a grading "
                        "state this feed cannot match to the "
                        "record; refusing to publish.")
        for call in group.get("calls") or []:
            when = call.get("logged_at_utc")
            if parse_time(when) is None:
                return fail("a Record board call carries no time "
                            "in its own record; refusing to "
                            "publish an undated entry.")
            detail = (f"Closed at {price(call['close'])} on the "
                      f"day it was published, checklist score "
                      f"{call['score']:g} of 100.")
            if call.get("passed_every_check"):
                detail += " It passed every check."
            entries.append({
                "source_tool": "The Record",
                "kind_words": "Stock call",
                "name": call["symbol"],
                "detail": detail,
                "session": session,
                "session_long": long_date(session),
                "sort_time_utc": when,
                "grading_state": grading_state,
                "grading_words": grading_words,
            })
            record_board_count += 1

    # ---- The Record: Morning Map cards it keeps -----------------
    map_part = record.get("map") or {}
    # The Record's map cards are graded by the wall study once
    # a following session exists: the state is "graded" with a
    # graded and a waiting count, not the not-yet-graded pin
    # this feed was built against. A card is graded when its
    # grading session is older than the freshest grading
    # session on record (the waiting cards are exactly the
    # freshest group); the derived count must equal the
    # Record's own graded count or this feed refuses (hookup
    # cure, 2026-10-29).
    if map_part.get("state") not in ("not_yet_graded", "graded"):
        return fail("The Record's map cards carry a grading state "
                    "this feed cannot match; refusing to publish.")
    map_groups = map_part.get("groups") or []
    all_cards = [c for g in map_groups for c in g.get("cards") or []]
    grading_sessions = [c.get("grading_session") for c in all_cards
                        if c.get("grading_session")]
    freshest_grading = max(grading_sessions) if grading_sessions \
        else None

    def map_card_graded(card):
        gs = card.get("grading_session")
        return bool(gs and freshest_grading
                    and gs < freshest_grading)

    if sum(1 for c in all_cards if map_card_graded(c)) \
            != map_part.get("cards_graded"):
        return fail("The Record's map graded count disagrees "
                    "with the per-card grading sessions; refusing "
                    "to publish.")
    record_map_count = 0
    for group in map_part.get("groups") or []:
        session = group.get("session")
        for card in group.get("cards") or []:
            when = card.get("published_at_utc")
            if parse_time(when) is None:
                return fail("a Record map card carries no time in "
                            "its own record; refusing to publish "
                            "an undated entry.")
            grading_session = card.get("grading_session")
            graded = map_card_graded(card)
            entries.append({
                "source_tool": "The Record",
                "kind_words": "Index card",
                "name": card["index"],
                "detail": (
                    f"Price then {price(card['price_then'])}; "
                    f"call wall {money(card['call_wall'])} above, "
                    f"put wall {money(card['put_wall'])} below, "
                    f"flip level {price(card['flip_level'])}."),
                "session": session,
                "session_long": long_date(session),
                "sort_time_utc": when,
                "grading_state": ("graded" if graded else
                                  "waiting_to_be_graded"),
                "grading_words": (
                    "Graded on "
                    f"{long_date(grading_session)}: its walls "
                    "and flip level were tested against what "
                    "prices did in the session that followed."
                    if graded else
                    "Waiting to be graded on "
                    f"{long_date(grading_session)}."
                    if grading_session else
                    "Waiting to be graded."),
            })
            record_map_count += 1
    record_count = record_board_count + record_map_count
    if record_count != totals.get("calls_published") \
            or record_board_count != totals.get("board_calls") \
            or record_map_count != totals.get("map_calls"):
        return fail("the entries taken from The Record disagree "
                    "with The Record's own published counts; "
                    "refusing to publish.")

    # ---- Flow Tape alerts ---------------------------------------
    note = flow.get("grading_note") or ""
    # This feed's alert entries are the freshest session's
    # cohort, which is ungraded until the next close exists,
    # whichever of the Flow Tape's two truthful notes is
    # current: the waiting note (no grading pass yet) or the
    # landed note (earlier sessions graded, the freshest
    # session's alerts grade after the next close). Any other
    # wording is a grading state this feed has not matched
    # (hookup cure, 2026-10-29).
    if not (("have not been graded yet" in note
             and "Grading is to follow" in note)
            or ("Grading has landed" in note
                and "grade after the next close" in note)):
        return fail("the Flow Tape's note no longer states a "
                    "grading state this feed can match; refusing "
                    "to publish a grading state of our own.")
    flow_count = 0
    for group in flow.get("groups") or []:
        for alert in group.get("alerts") or []:
            when = alert.get("time_utc")
            if parse_time(when) is None:
                return fail("a Flow Tape alert carries no time in "
                            "its own record; refusing to publish "
                            "an undated entry.")
            contract = alert.get("contract") or {}
            kind = contract.get("kind")
            if kind not in ("call", "put") \
                    or contract.get("strike") is None \
                    or not contract.get("expiry"):
                return fail("a Flow Tape alert's contract cannot "
                            "be read from its own record; refusing "
                            "to publish.")
            tags = ""
            if alert.get("golden_sweep"):
                tags += " A golden sweep."
            if alert.get("unusual"):
                tags += " Tagged unusual."
            entries.append({
                "source_tool": "Flow Tape",
                "kind_words": "Options alert",
                "name": (f"{group['underlying']} "
                         f"{price(contract['strike'])} {kind}"),
                "detail": (
                    f"Expires {long_date(contract['expiry'])}. "
                    f"{alert['contracts']:,} contracts, "
                    f"{money(alert['premium_usd'])} in total, "
                    f"heat score {alert['heat_score']:g} "
                    f"({alert['band']}). "
                    f"{alert['side_words']}; it "
                    f"{alert['direction_words']}." + tags),
                "session": flow.get("session"),
                "session_long": long_date(flow["session"]),
                "sort_time_utc": when,
                "grading_state": "not_graded_yet",
                "grading_words": (
                    "Not graded yet: nothing has checked what "
                    "happened after this alert. Grading is to "
                    "follow."),
            })
            flow_count += 1
    flow_published = (flow.get("counts") or {}).get("alerts_published")
    if flow_count != flow_published:
        return fail("the alerts taken from the Flow Tape disagree "
                    "with the Flow Tape's own published count; "
                    "refusing to publish.")

    # ---- Qualified Board: passed-every-check names --------------
    for key in board:
        if "grad" in key.lower():
            return fail("the Qualified Board's record now carries "
                        "a grading field this feed has not "
                        "matched; refusing to publish.")
    board_count = 0
    board_published_at = board.get("published_at_utc")
    if parse_time(board_published_at) is None \
            or not board.get("session"):
        return fail("the Qualified Board's record cannot be "
                    "dated; refusing to publish.")
    for group in board.get("groups") or []:
        for name_row in group.get("names") or []:
            if any("grad" in k.lower() for k in name_row):
                return fail("a Qualified Board name now carries "
                            "a grading field this feed has not "
                            "matched; refusing to publish.")
            if not name_row.get("passed_every_check"):
                continue
            sector = name_row.get("sector")
            entries.append({
                "source_tool": "Qualified Board",
                "kind_words": "Passed every check",
                "name": name_row["symbol"],
                "detail": (
                    f"Score {name_row['score']:g} of 100, closed "
                    f"at {price(name_row['close'])}"
                    + (f", {sector}." if sector else ".")),
                "session": board["session"],
                "session_long": long_date(board["session"]),
                "sort_time_utc": board_published_at,
                "grading_state": "no_grade_stated",
                "grading_words": (
                    "Not graded: its own record states no grade "
                    "for this entry."),
            })
            board_count += 1
    board_published_count = (board.get("counts") or {}).get(
        "passed_every_check_published")
    if board_count != board_published_count:
        return fail("the passed names taken from the Qualified "
                    "Board disagree with the Board's own "
                    "published count; refusing to publish.")

    # ---- The Screener: passed-every-check names -----------------
    for key in screener:
        if "grad" in key.lower():
            return fail("The Screener's record now carries a "
                        "grading field this feed has not matched; "
                        "refusing to publish.")
    screener_count = 0
    screener_published_at = screener.get("published_at_utc")
    if parse_time(screener_published_at) is None \
            or not screener.get("session"):
        return fail("The Screener's record cannot be dated; "
                    "refusing to publish.")
    for name_row in screener.get("names") or []:
        if any("grad" in k.lower() for k in name_row):
            return fail("a Screener name now carries a grading "
                        "field this feed has not matched; refusing "
                        "to publish.")
        if not name_row.get("passed_every_check"):
            continue
        sector = name_row.get("sector")
        index = name_row.get("index")
        where = ", ".join(x for x in (sector, index) if x)
        entries.append({
            "source_tool": "The Screener",
            "kind_words": "Passed every check",
            "name": name_row["symbol"],
            "detail": (
                f"Score {name_row['score']:g} of 100, closed at "
                f"{price(name_row['close'])}"
                + (f", {where}." if where else ".")),
            "session": screener["session"],
            "session_long": long_date(screener["session"]),
            "sort_time_utc": screener_published_at,
            "grading_state": "no_grade_stated",
            "grading_words": (
                "Not graded: its own record states no grade for "
                "this entry."),
        })
        screener_count += 1
    screener_published_count = (screener.get("counts") or {}).get(
        "passed_every_check_all")
    if screener_count != screener_published_count:
        return fail("the passed names taken from The Screener "
                    "disagree with The Screener's own published "
                    "count; refusing to publish.")

    # ---- Morning Map cards --------------------------------------
    map_count = 0
    map_when = morning.get("generated_at_utc")
    map_session = morning.get("session")
    contract = morning.get("contract") or {}
    carried_session = (contract.get("source_session") or {}).get(
        "value")
    if parse_time(map_when) is None or not map_session \
            or carried_session != map_session:
        return fail("the Morning Map's record cannot be dated "
                    "from its own record; refusing to publish.")
    for index_row in morning.get("indexes") or []:
        if any("grad" in k.lower() for k in index_row):
            return fail("a Morning Map card now carries a "
                        "grading field this feed has not matched; "
                        "refusing to publish.")
        flip = (index_row.get("flip") or {}).get("value")
        spot = index_row.get("spot")
        call_wall = (index_row.get("call_wall") or {}).get("value")
        put_wall = (index_row.get("put_wall") or {}).get("value")
        if spot is None or call_wall is None or put_wall is None \
                or flip is None:
            return fail("a Morning Map card is missing a figure "
                        "its own record carries; refusing to "
                        "publish a card with a figure filled in.")
        entries.append({
            "source_tool": "Morning Map",
            "kind_words": "Morning map card",
            "name": index_row["symbol"],
            "detail": (
                f"Price {price(spot)}; call wall "
                f"{money(call_wall)} above, put wall "
                f"{money(put_wall)} below, flip level "
                f"{price(round(flip, 2))}."),
            "session": map_session,
            "session_long": long_date(map_session),
            "sort_time_utc": map_when,
            "grading_state": "no_grade_stated",
            "grading_words": (
                "Not graded: its own record states no grade for "
                "this card."),
        })
        map_count += 1
    if map_count != len(morning.get("indexes") or []):
        return fail("the cards taken from the Morning Map "
                    "disagree with the cards it carries; refusing "
                    "to publish.")

    # ---- Order newest first by the time each record carries -----
    entries.sort(
        key=lambda e: parse_time(e["sort_time_utc"]), reverse=True)

    sources = [
        {"tool": "The Record", "contributed": record_count,
         "published_words": (
             f"{totals.get('calls_published')} calls published: "
             f"{totals.get('board_calls')} stock calls and "
             f"{totals.get('map_calls')} index cards")},
        {"tool": "Flow Tape", "contributed": flow_count,
         "published_words": (
             f"{flow_published} alerts published for "
             f"{long_date(flow['session'])}")},
        {"tool": "Qualified Board", "contributed": board_count,
         "published_words": (
             f"{board_published_count} of its "
             f"{(board.get('counts') or {}).get('names_published')} "
             f"published names passed every check, for "
             f"{long_date(board['session'])}")},
        {"tool": "The Screener", "contributed": screener_count,
         "published_words": (
             f"{screener_published_count} names passed every "
             f"check in its scored run for "
             f"{long_date(screener['session'])}")},
        {"tool": "Morning Map", "contributed": map_count,
         "published_words": (
             f"{map_count} cards, one per index, for "
             f"{long_date(map_session)}")},
    ]
    freshest_session = max(e["session"] for e in entries)
    newest_time = max(e["sort_time_utc"] for e in entries
                      ) if entries else None
    # newest by parsed time, not string order
    newest_time = max(entries,
                      key=lambda e: parse_time(e["sort_time_utc"])
                      )["sort_time_utc"] if entries else None

    data = {
        "tool": "Signal Feed",
        "state": "published",
        "freshest_session": freshest_session,
        "freshest_session_long": long_date(freshest_session),
        "newest_entry_time_utc": newest_time,
        "total_entries": len(entries),
        "sources": sources,
        "excluded_sources": [],
        "entries": entries,
        "proving_state": proving_entry["words"],
        "proving_note": proving_entry["definition"],
        "source": ("The newest entries from the records this "
                   "site already publishes, each shown exactly "
                   "as its own tool published it"),
    }

    blob = json.dumps(data, sort_keys=True)
    for bad in FORBIDDEN:
        if bad in blob.lower():
            return fail(f"assembled data carries internal wording "
                        f"({bad}); refusing to publish.")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} ({len(entries)} entries: "
          f"Record {record_count}, Flow Tape {flow_count}, "
          f"Qualified Board {board_count}, Screener "
          f"{screener_count}, Morning Map {map_count}; freshest "
          f"session {freshest_session})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
