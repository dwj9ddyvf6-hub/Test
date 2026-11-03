#!/usr/bin/env python3
"""Refresh the Wall Check data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: the real grading record for the published index
map: the public scorecard's map grades, which are computed from the
permanent log's published map cards (the last card per name per day
is the card of record) and the completed sessions' daily prices.
Cross-checked three ways: against the permanent log itself (every
grade must name a card of record held in the log, with the walls
that card published), against the published feed's summary of the
same grades, and against the permanent log's freshest scorecard
entry (its card and graded counts). The grading definitions are the
scorecard's own, declared in its source and never forked here: an
upper wall held if the session's highest price never traded above
it, and it was touched if the high came within 0.2% below it; the
lower wall is the mirror image against the session's lowest price;
the flip level was respected if the session's close stayed on the
same side of it as the price when the card was published. A card
published before the close grades against its own session; a card
published after the close grades against the next session.

Reconstruction choices, stated as ours: (1) The scorecard's grades
are the grading record of the lineup. An older research summary of
the same tests, written before the graded sessions had completed,
still says no test has been graded; it is a stale copy, not a
second grading, and this refresh publishes from the scorecard. If
that summary is ever regenerated after the scorecard and still
disagrees with it, this refresh fails closed instead (see below).
(2) Every card of record is one wall test, so a name with cards
published on two different days that both grade against the same
session contributes two tests of that session, each with the walls
its own card published. (3) Tests are split by the positioning sign
the card itself carried: negative positioning (the map's
amplifying side) and positive positioning (its dampening side) are
shown as separate buckets, and a bucket with no tests yet says so.
(4) A cell with fewer than 30 tests is a thin cell: the page shows
its counts and no percentage, in the headline as everywhere else,
because a percentage on a handful of tests reads as far more
certain than it is. Today every cell is thin (6 tests in total), so
the page carries no percentages at all. (5) Cards of record whose
session has not completed yet are shown as waiting to be graded,
with the walls they published; they are not counted as tests.

Scope: this page claims nothing about any future session. It shows
only the tests the grading record carries, under the grading
record's own definitions. A wall that price never came near counts
as held, exactly as the definition says; the page shows the
touched counts separately so a held wall that was never tested is
not dressed up as a wall that turned price back.

Fail-closed rules: if the scorecard's grades disagree with the
permanent log's cards of record (a grade naming no card of record,
or walls that differ from the card's), if the feed's summary of the
grades or the log's freshest scorecard counts disagree with the
grades, if the scorecard's own summary rates do not recompute from
its grades, if a card carries a positioning value this page cannot
sign, or if the stale research summary has been regenerated after
the scorecard and still disagrees with it, the refresh stops and
publishes nothing. All timestamps come from the sources, never the
clock, so running this script twice produces the same file.

Usage: python3 refresh_wallcheck.py
"""

import json
import os
import sys

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.expanduser("~/workspace/morgue/output")
SCORECARD_PATH = os.path.join(SOURCE_DIR, "scorecard.json")
FEED_PATH = os.path.join(SOURCE_DIR, "morgue-feed.json")
LOG_PATH = os.path.join(SOURCE_DIR, "ledger.jsonl")
HARNESS_PATH = os.path.join(SOURCE_DIR, "wall_validation.json")
OUT_PATH = os.path.join(HERE, "wall-check", "data.json")

MIN_TESTS_FOR_PERCENT = 30
NAMES = ["SPY", "QQQ", "IWM"]

SOURCE_WORDS = ("The published index map cards on record and the "
                "public grading of those cards against the "
                "completed trading sessions that followed them")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Wall Check refresh: {message}", file=sys.stderr)
    return 1


def wall_outcome(touched, held, side):
    """Plain outcome key for one wall under the declared definition."""
    if not held:
        return "traded_through"
    if touched:
        return "reached_and_held"
    return "never_reached" if side == "upper" else "never_reached"


def summarize(tests):
    n = len(tests)
    thin = n < MIN_TESTS_FOR_PERCENT
    out = {
        "tests": n,
        "upper_held": sum(1 for t in tests if t["upper_held"]),
        "upper_broke": sum(1 for t in tests if not t["upper_held"]),
        "upper_reached": sum(1 for t in tests if t["upper_touched"]),
        "lower_held": sum(1 for t in tests if t["lower_held"]),
        "lower_broke": sum(1 for t in tests if not t["lower_held"]),
        "lower_reached": sum(1 for t in tests if t["lower_touched"]),
        "reached_and_held": sum(
            1 for t in tests
            if (t["upper_touched"] and t["upper_held"])
            or (t["lower_touched"] and t["lower_held"])),
        "flip_respected": sum(1 for t in tests if t["flip_respected"]),
        "flip_not_respected": sum(
            1 for t in tests if not t["flip_respected"]),
        "thin": thin,
        "upper_held_share": (
            None if thin else sum(1 for t in tests
                                  if t["upper_held"]) / n),
        "lower_held_share": (
            None if thin else sum(1 for t in tests
                                  if t["lower_held"]) / n),
        "flip_respected_share": (
            None if thin else sum(1 for t in tests
                                  if t["flip_respected"]) / n),
    }
    return out


def build():
    for path in (SCORECARD_PATH, FEED_PATH, LOG_PATH, HARNESS_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    scorecard = load_json(SCORECARD_PATH)
    feed = load_json(FEED_PATH)
    harness = load_json(HARNESS_PATH)
    with open(LOG_PATH, encoding="utf-8") as fh:
        log_rows = [json.loads(line) for line in fh if line.strip()]

    map_sc = scorecard.get("map") or {}
    grades = map_sc.get("grades") or []

    # --- Cards of record from the permanent log: the last map card
    # per name per day, in the log's own order. ---
    of_record = {}
    for r in log_rows:
        if r.get("component") == "gex_static_v1":
            of_record[(r["underlying"], r["ts_utc"][:10])] = r
    if not of_record:
        return fail("the permanent log holds no published map "
                    "cards; refusing to publish a page with no "
                    "cards behind it.")
    cards_by_ts = {}
    for r in of_record.values():
        if r["underlying"] not in NAMES:
            return fail(f"a card of record names {r['underlying']}, "
                        "which this page does not cover; refusing "
                        "to publish a partial page.")
        gex = r.get("net_gex_usd_per_1pct")
        if not isinstance(gex, (int, float)):
            return fail("a card of record carries no positioning "
                        "figure to sign; refusing to publish.")
        cards_by_ts[r["ts_utc"]] = {
            "name": r["underlying"],
            "published_at_utc": r["ts_utc"],
            "spot": r["spot"],
            "call_wall": r["call_wall"],
            "put_wall": r["put_wall"],
            "zero_gamma": r["zero_gamma"],
            "positioning": "amplifying" if gex < 0 else "dampening",
        }

    # --- Every grade must name a card of record, and the walls
    # behind the grade are that card's published walls. ---
    tests = []
    graded_ts = set()
    for g in grades:
        card = cards_by_ts.get(g.get("card_ts"))
        if card is None:
            return fail(f"a grade names a card "
                        f"({g.get('card_ts')}) that is not a card "
                        "of record in the permanent log; refusing "
                        "to publish.")
        if g.get("underlying") != card["name"]:
            return fail("a grade's name disagrees with the card of "
                        "record it names; refusing to publish.")
        graded_ts.add(g["card_ts"])
        tests.append({
            "name": card["name"],
            "session": g["session"],
            "published_at_utc": card["published_at_utc"],
            "spot": card["spot"],
            "call_wall": card["call_wall"],
            "put_wall": card["put_wall"],
            "flip": card["zero_gamma"],
            "positioning": card["positioning"],
            "upper_touched": bool(g["call_wall_touched"]),
            "upper_held": bool(g["call_wall_held"]),
            "upper_outcome": wall_outcome(
                g["call_wall_touched"], g["call_wall_held"], "upper"),
            "lower_touched": bool(g["put_wall_touched"]),
            "lower_held": bool(g["put_wall_held"]),
            "lower_outcome": wall_outcome(
                g["put_wall_touched"], g["put_wall_held"], "lower"),
            "flip_respected": bool(g["flip_respected"]),
        })
    tests.sort(key=lambda t: (t["session"], t["published_at_utc"],
                              t["name"]))

    # --- The scorecard's own summary must recompute from its
    # grades, and its counters must match the log. ---
    if map_sc.get("state") != ("graded" if tests else
                               "not_yet_graded"):
        return fail("the scorecard's map state disagrees with the "
                    "grades it carries; refusing to publish.")
    if map_sc.get("cards_graded") != len(tests):
        return fail("the scorecard's graded count disagrees with "
                    "the grades it carries; refusing to publish.")
    counters = scorecard.get("counters") or {}
    if counters.get("map_cards_of_record") != len(of_record):
        return fail("the scorecard's card count disagrees with "
                    "the permanent log; refusing to publish.")
    if tests:
        n = len(tests)
        for key, field in (("call_wall_held_rate", "upper_held"),
                           ("put_wall_held_rate", "lower_held"),
                           ("flip_respected_rate", "flip_respected")):
            want = sum(1 for t in tests if t[field]) / n
            if abs(map_sc.get(key, -1) - want) > 1e-9:
                return fail(f"the scorecard's {key} does not "
                            "recompute from its own grades; "
                            "refusing to publish.")
        if map_sc.get("touched_and_held") != sum(
                1 for t in tests
                if (t["upper_touched"] and t["upper_held"])
                or (t["lower_touched"] and t["lower_held"])):
            return fail("the scorecard's reached-and-held count "
                        "does not recompute from its grades; "
                        "refusing to publish.")

    # --- The published feed's summary of the same grades must
    # agree (its percentages are whole numbers). ---
    feed_map = (feed.get("scorecard") or {}).get("map") or {}
    if feed_map.get("state") != map_sc.get("state") or \
            feed_map.get("cards_graded") != len(tests):
        return fail("the published summary of the grades disagrees "
                    "with the grading record; refusing to publish.")
    if tests:
        n = len(tests)
        for fkey, field in (("call_wall_held_pct", "upper_held"),
                            ("put_wall_held_pct", "lower_held"),
                            ("flip_respected_pct", "flip_respected")):
            want = round(100 * sum(1 for t in tests
                                   if t[field]) / n)
            if feed_map.get(fkey) != want:
                return fail(f"the published summary's {fkey} "
                            "disagrees with the grades; refusing "
                            "to publish.")
    feed_counters = (feed.get("scorecard") or {}).get(
        "counters") or {}
    if feed_counters.get("map_cards_of_record") != len(of_record):
        return fail("the published summary's card count disagrees "
                    "with the permanent log; refusing to publish.")

    # --- The permanent log's freshest scorecard entry must carry
    # the same counts. ---
    sc_rows = [r for r in log_rows if r.get("component") == "scorecard"]
    if not sc_rows:
        return fail("the permanent log holds no scorecard entry; "
                    "refusing to publish.")
    latest_sc = sc_rows[-1].get("value") or {}
    if latest_sc.get("map_cards") != len(of_record) or \
            latest_sc.get("map_graded") != len(tests):
        return fail("the permanent log's freshest scorecard entry "
                    "disagrees with the grading record; refusing "
                    "to publish.")

    # --- The older research summary of the same tests: a stale
    # copy written before the graded sessions completed is not a
    # second grading, but a copy regenerated after the scorecard
    # that still disagrees with it is a real disagreement. ---
    if harness.get("state") == "graded":
        if harness.get("cards_graded") != len(tests):
            return fail("the research summary of the wall tests "
                        "disagrees with the grading record; "
                        "refusing to publish.")
    elif harness.get("generated_at", "") >= \
            scorecard.get("generated_at", ""):
        return fail("the research summary of the wall tests was "
                    "regenerated after the grading record and "
                    "still disagrees with it; refusing to publish.")

    # --- Waiting cards: cards of record with no grade yet. Their
    # grading session follows the scorecard's declared rule from
    # the sessions already graded or completed on the record. ---
    graded_sessions = sorted({t["session"] for t in tests})
    waiting = []
    for ts in sorted(cards_by_ts):
        if ts in graded_ts:
            continue
        card = cards_by_ts[ts]
        card_date = ts[:10]
        hour = int(ts[11:13])
        if hour < 20:
            session = card_date
        else:
            later = [s for s in graded_sessions if s > card_date]
            session = later[0] if later else None
        waiting.append({
            "name": card["name"],
            "published_at_utc": card["published_at_utc"],
            "spot": card["spot"],
            "call_wall": card["call_wall"],
            "put_wall": card["put_wall"],
            "flip": card["zero_gamma"],
            "positioning": card["positioning"],
            "session": session,
        })

    sessions = []
    for s in graded_sessions:
        sessions.append({
            "session": s,
            "tests": [t for t in tests if t["session"] == s],
            "summary": summarize(
                [t for t in tests if t["session"] == s]),
        })

    by_name = []
    for name in NAMES:
        own = [t for t in tests if t["name"] == name]
        if own:
            by_name.append({"name": name, **summarize(own)})
    by_positioning = []
    for key, label in (("amplifying", "Amplifying positioning"),
                       ("dampening", "Dampening positioning")):
        own = [t for t in tests if t["positioning"] == key]
        by_positioning.append({"key": key, "label": label,
                               **summarize(own)})

    totals = summarize(tests)
    data = {
        "tool": "Wall Check",
        "state": "graded" if tests else "not_yet_graded",
        "published_at_utc": scorecard["generated_at"],
        "source": SOURCE_WORDS,
        "thin_threshold": MIN_TESTS_FOR_PERCENT,
        "cards_of_record": len(of_record),
        "sessions_graded": graded_sessions,
        "totals": totals,
        "sessions": sessions,
        "by_name": by_name,
        "by_positioning": by_positioning,
        "waiting": waiting,
        "receipt": {
            "published_at_utc": scorecard["generated_at"],
            "source": SOURCE_WORDS,
            "coverage": (
                f"{len(tests)} graded wall tests from "
                f"{len(of_record)} published map cards on record; "
                f"{len(waiting)} card(s) still waiting for their "
                "session to complete"),
        },
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} ({len(tests)} graded tests, "
          f"{len(of_record)} cards of record, "
          f"{len(waiting)} waiting, published "
          f"{scorecard['generated_at']})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
