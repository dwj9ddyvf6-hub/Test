#!/usr/bin/env python3
"""Refresh the State Analogue data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: the state section of the daily studies record,
cross-checked three ways: the studies card itself, the published
feed's summary of that same card, and every state entry in the
permanent log (each written before the card was displayed). The
matching rule and the 126-session floor are read from the matching
code itself, not restated from memory: the refresh opens the code
and stops if the floor it finds there is not the floor this page
publishes.

Reconstruction choices: the five readings are named in plain words
from the coded definitions (the price move over the last 21 trading
days; how much daily moves varied over those 21 days; how much of
the options market's sensitivity sits in calls rather than puts; the
share of trading done away from the public exchanges, averaged over
5 days and lagged a day; the move size options prices imply). The
matching method is stated in one plain sentence that follows the
code: every reading is scaled against the days before it, the
recorded days whose five scaled readings sit closest to today's are
the matches (the closest one sixth of recorded days), and what
followed a match is the market's move over the 21 trading days after
it, averaged across the matches. No part of a day's readings, a
match, or a follow-through figure is computed here: this script
publishes only what the records carry.

Non-claims: this tool makes no claim about what the market will do.
Until 126 trading days of readings are on record it shows no matches
and no follow-through at all, only the count of days on record; a
day's readings are shown only when that day's readings are actually
on record, and their absence is stated, never filled in.

What the sources carry: the studies card's state section is read
back from the daily state readings store (one stored reading per
completed session, written by the morgue's state writer since the
2026-10-29 cure of gap G12). The count stands at the store's real
day count of the 126 days required; until the floor is met there
are no matches, and the freshest stored day's five readings are
shown as today's. The page is the honest counter pane the design
specifies for exactly this state.

Fail-closed rules: if the card and the feed summary disagree with
each other on the state section; if the freshest state entry in
the permanent log disagrees with the card, or any earlier log
entry carries an accrued count above the card's (the count only
ever grows); if the feed was generated before the card it
summarises (the card is stamped with the calendar day the study
ran while the feed names the board's last completed session, so
the binding is generation order plus exact agreement of the state
section, never equality of those two different date kinds); if
the matching code's floor is not the published floor; or if the
state ever reports itself graded while the records carry no day's
readings and no matches to publish, the refresh stops and
publishes nothing.

Honesty rules:
- Sessions and times are read off the sources, never from the
  clock. All timestamps come from the sources, so running this
  script twice produces the same file.
- Zero days on record is a real state, not an error: the history
  accrues one trading day at a time, and the counter says exactly
  where it stands.

Usage: python3 refresh_analogue.py
"""

import json
import os
import re
import sys

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.expanduser("~/workspace/morgue/output")
ENGINE_PATH = os.path.expanduser("~/workspace/morgue/studies.py")
CARD_PATH = os.path.join(SOURCE_DIR, "studies_card.json")
FEED_PATH = os.path.join(SOURCE_DIR, "morgue-feed.json")
LOG_PATH = os.path.join(SOURCE_DIR, "ledger.jsonl")
OUT_PATH = os.path.join(HERE, "state-analogue", "data.json")

SESSIONS_NEEDED = 126  # the floor coded in the matching engine

SOURCE_WORDS = ("The daily studies record: the market's state "
                "readings, written into the permanent record before "
                "anything is shown from them")

METHOD_WORDS = ("Each recorded day is scored by how close its five "
                "readings sit to today's, with every reading first "
                "scaled against the days that came before it, and "
                "the closest one sixth of recorded days count as "
                "matches, whose average move over the following 21 "
                "trading days is what this page reports.")

READINGS = [
    {"name": "Price move over the last month",
     "meaning": "How far the market's price travelled over the "
                "last 21 trading days, up or down."},
    {"name": "How jumpy prices have been",
     "meaning": "How much the daily moves varied over the last 21 "
                "trading days: steady days or swinging days."},
    {"name": "Calls' share of the options market's sensitivity",
     "meaning": "How much of the options market's sensitivity to "
                "price sits in call options rather than put options."},
    {"name": "Share of trading away from the public exchanges",
     "meaning": "The share of trading done in dark pools instead of "
                "on the public exchanges, averaged over 5 trading "
                "days and counted a day late, the way it is "
                "reported."},
    {"name": "The move size options prices imply",
     "meaning": "How large a move options prices are set for, read "
                "from the options market itself."},
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_log(path):
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def fail(message):
    print(f"State Analogue refresh: {message}", file=sys.stderr)
    return 1


def build():
    for path in (CARD_PATH, FEED_PATH, LOG_PATH, ENGINE_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    # --- The floor, read from the matching code itself. ---
    with open(ENGINE_PATH, "r", encoding="utf-8") as fh:
        engine = fh.read()
    if "len(finite) < 126" not in engine or "accrued < 126" not in engine \
            or ">=126 accrued state sessions" not in engine:
        return fail("the matching code no longer carries the "
                    "126-session floor this page publishes; refusing "
                    "to publish a floor the code does not hold.")

    card = load_json(CARD_PATH)
    feed = load_json(FEED_PATH)
    log_rows = load_log(LOG_PATH)

    card_state = card.get("state_vectors")
    if not isinstance(card_state, dict) or "state" not in card_state \
            or "history_sessions_accrued" not in card_state:
        return fail("the studies card carries no usable state "
                    "section; refusing to guess at the count.")
    feed_state = (feed.get("studies") or {}).get("state_vectors")
    if not isinstance(feed_state, dict):
        return fail("the published feed carries no state summary; "
                    "refusing to publish a count only one record "
                    "supports.")
    if feed_state != card_state:
        return fail(f"the feed's state summary {feed_state} does not "
                    f"match the studies card's state section "
                    f"{card_state}; refusing to publish a mismatched "
                    "page.")

    # --- The permanent log: the freshest state entry must equal
    # the card; earlier entries are the count's history and may
    # only sit at or below the card's count (it grows one session
    # at a time and never shrinks). ---
    state_rows = [r for r in log_rows
                  if r.get("component") == "state-vectors"]
    if not state_rows:
        return fail("the permanent log holds no state entry at all; "
                    "refusing to show a count that is not on the "
                    "record.")
    freshest = max(state_rows, key=lambda r: r.get("ts_utc") or "")
    if freshest.get("value") != card_state:
        return fail(f"the freshest state entry recorded at "
                    f"{freshest.get('ts_utc')} says "
                    f"{freshest.get('value')} but the studies card "
                    f"says {card_state}; refusing to publish a "
                    "mismatched page.")
    for r in state_rows:
        n = (r.get("value") or {}).get("history_sessions_accrued")
        if not isinstance(n, int) \
                or n > card_state["history_sessions_accrued"]:
            return fail(f"the state entry recorded at "
                        f"{r.get('ts_utc')} carries an accrued "
                        f"count of {n!r}, above the card's "
                        f"{card_state['history_sessions_accrued']}; "
                        "the count never shrinks, so the records "
                        "disagree; refusing to publish.")

    # --- The feed must have been generated at or after the card
    # it summarises (the two carry different date kinds: the card
    # is stamped with the study's run day, the feed names the
    # board's last completed session). ---
    as_of = card.get("as_of")
    card_gen = card.get("generated_at")
    feed_gen = feed.get("generated_at_utc")
    if not as_of or not card_gen or not feed_gen \
            or feed_gen < card_gen:
        return fail(f"the published feed (generated {feed_gen}) "
                    f"does not postdate the studies card "
                    f"(generated {card_gen}); refusing to publish "
                    "a summary older than the card it summarises.")

    accrued = card_state["history_sessions_accrued"]
    if not isinstance(accrued, int) or accrued < 0 \
            or accrued > SESSIONS_NEEDED and card_state["state"] \
            == "insufficient_history":
        return fail(f"the accrued count {accrued!r} does not sit "
                    "with the recorded state; refusing to publish.")
    if card_state["state"] == "graded" or accrued >= SESSIONS_NEEDED:
        return fail("the records say the history floor is met, but "
                    "this page does not yet carry the matched days "
                    "the graded state would publish; refusing to "
                    "invent them. The refresh must be extended to "
                    "publish the matches before this state can be "
                    "shown.")
    if card_state["state"] != "insufficient_history":
        return fail(f"the state section carries a state this page "
                    f"cannot say plainly: {card_state['state']!r}; "
                    "refusing to guess.")

    latest = card_state.get("latest")
    today = None
    if accrued > 0:
        if not isinstance(latest, dict) \
                or not latest.get("date") \
                or not isinstance(latest.get("vector"), list) \
                or len(latest["vector"]) != 5:
            return fail("the card counts stored state readings "
                        "but carries no freshest day's readings to "
                        "show; refusing to publish a count with no "
                        "reading behind it.")
        today = {"date": latest["date"],
                 "values": [None if v is None else round(v, 4)
                            for v in latest["vector"]]}

    first_recorded = min(r["ts_utc"] for r in state_rows)
    last_recorded = max(r["ts_utc"] for r in state_rows)
    coverage = (f"{accrued} trading days of state readings are on "
                f"record of the {SESSIONS_NEEDED} required; the "
                f"state record has been written "
                f"{len(state_rows)} times, first on "
                f"{first_recorded[:10]} and most recently on "
                f"{last_recorded[:10]}, and the freshest writing "
                f"agrees with the card; earlier writings carry "
                f"the counts of their own day")

    data = {
        "tool": "State Analogue",
        "floor_met": False,
        "counts": {
            "sessions_recorded": accrued,
            "sessions_needed": SESSIONS_NEEDED,
            "sessions_remaining": SESSIONS_NEEDED - accrued,
        },
        "as_of_session": today["date"] if today else as_of,
        "published_at_utc": card.get("generated_at"),
        "feed_published_at_utc": feed.get("generated_at_utc"),
        "source": SOURCE_WORDS,
        "coverage": coverage,
        "method": METHOD_WORDS,
        "readings": READINGS,
        "today": today,
        "matches": [],
        "receipt": {
            "session": as_of,
            "published_at_utc": card.get("generated_at"),
            "source": SOURCE_WORDS,
            "coverage": coverage,
        },
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} ({accrued} sessions on record of "
          f"{SESSIONS_NEEDED} needed, floor not met, no matches, "
          f"record dated {as_of}, published "
          f"{card.get('generated_at')})")
    # Record-surface cure (2026-10-31): surface this page's full
    # record in its own data.json, from numbers already on file.
    try:
        import record_surface as _rs
        _rs.enrich_slug("state-analogue")
    except Exception as _exc:
        print(f"record-surface enrich failed: {_exc}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
