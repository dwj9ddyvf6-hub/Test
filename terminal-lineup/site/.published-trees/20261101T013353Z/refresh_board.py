#!/usr/bin/env python3
"""Refresh the Qualified Board data file.

Reads the real published board (the daily card that ranks the highest
scoring names, cross-checked against the full ranked list and the
permanent log that records when each day's board was published) and
writes site/board/data.json in the shape the Qualified Board page
renders.

What the sources carry (and what this script therefore shows):
- The board card publishes the 50 highest-scoring names for its
  session, in score order. Each name carries its closing price, its
  combined score out of 100, how many of the eight checks lined up in
  its favor, the state of each of the eight checks, how much of the
  data behind the score was present, whether it passed every check,
  and, when it did not, the list of requirements it missed, including
  the detail behind a missed basic bar.
- The full ranked list covers every name that was scored, so the
  card's figures (how many names were checked, scored, short on data,
  and how many passed every check in total) are recomputed from it
  and must agree with the card's own summary.
- The card's own date field is the start of its price history window,
  not a publication time, so the moment this board was published is
  taken from the permanent log entry for the same session.

Honesty rules:
- Every requirement a name missed is translated into plain words from
  the exact list the source carries. An unknown entry stops the
  refresh instead of being guessed at or dropped.
- All timestamps and figures come from the source files, never from
  the clock, so running this script twice produces the same file.
- If the card, the full list and the log disagree, the script fails
  instead of publishing a mismatched page.

Usage: python3 refresh_board.py
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
CARD_PATH = os.path.join(SOURCE_DIR, "board_card.json")
FULL_PATH = os.path.join(SOURCE_DIR, "board_full.json")
LOG_PATH = os.path.join(SOURCE_DIR, "ledger.jsonl")
OUT_PATH = os.path.join(HERE, "board", "data.json")

# The eight checks, in the order the board itself lists them, named
# the way a reader would say them.
CHECK_NAMES = [
    ("relativeStrength", "Strength against the market"),
    ("priceAction", "Recent price action"),
    ("volumeParticipation", "Trading volume behind the move"),
    ("trendAlignment", "Trend direction"),
    ("supportResistance", "Support and resistance levels"),
    ("sectorLeadership", "Strength of its sector"),
    ("institutionalPositioning", "Big investors' reported positions"),
    ("marketContext", "The overall market backdrop"),
]

CHECK_STATES = {
    "confirming": "in_favor",
    "neutral": "in_between",
    "conflicting": "against",
    "no-data": "no_data",
}

# The basic bars a name can miss, in plain words. These wordings state
# the published bars themselves: more than 500,000 shares and more
# than $5 million traded a day on average, a typical daily move of at
# least 2%, price not more than 2% below its 50-day or 200-day
# average, and a trend in stage 1 or 2.
BASIC_BAR_WORDS = {
    "adv<=500k": "It trades too few shares a day: 500,000 or fewer "
                 "on average, and the bar is more than that.",
    "dollar-adv<=$5M": "Too little money changes hands in it each "
                       "day: $5 million or less on average.",
    "atr<2%": "Its typical daily move is too small: under 2%.",
    "below-50ema": "Its price sits more than 2% below its 50-day "
                   "average line.",
    "below-200ema": "Its price sits more than 2% below its 200-day "
                    "average line.",
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_log(path):
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def fail(message):
    print(f"Qualified Board refresh: {message}", file=sys.stderr)
    return None


def missed_words(row):
    """Translate the source's missed-requirement lists into plain words.

    Returns None (and the refresh fails) on anything the source
    carries that this script does not know how to say plainly.
    """
    words = []
    for token in row.get("gate_fails", []):
        if token == "not-qualified":
            detail = row.get("qualify_fails", [])
            if not detail:
                return fail(f"{row['symbol']}: the board says a basic "
                            "bar was missed but carries no detail "
                            "saying which one; refusing to guess.")
            for item in detail:
                if item in BASIC_BAR_WORDS:
                    words.append(BASIC_BAR_WORDS[item])
                elif re.fullmatch(r"stage-\d+", item):
                    words.append(
                        f"Its trend is in stage {item.split('-')[1]}, "
                        "and this board only takes the early stages, "
                        "1 and 2.")
                else:
                    return fail(f"{row['symbol']}: unknown basic bar "
                                f"missed: {item!r}; refusing to guess.")
        elif token == "count":
            words.append(
                "Too few of the eight checks lined up in its favor: "
                f"{row['confirming']} of 8, and the bar is at least 5.")
        elif token == "conviction":
            words.append(
                "Its combined score did not reach the bar of 65.")
        elif token == "data-confidence":
            words.append(
                "Too much of the data behind its score was missing: "
                f"only {row['dc']:.0f}% of the measures behind the "
                "score had data, and the bar is 70%.")
        else:
            return fail(f"{row['symbol']}: unknown missed requirement: "
                        f"{token!r}; refusing to guess.")
    return words


def build():
    for path in (CARD_PATH, FULL_PATH, LOG_PATH):
        if not os.path.exists(path):
            print(f"Qualified Board refresh: source not found: {path}",
                  file=sys.stderr)
            return 1

    card = load_json(CARD_PATH)
    full = load_json(FULL_PATH)
    log_rows = load_log(LOG_PATH)

    summary = card["summary"]
    session = summary["as_of_session"]
    published_rows = card["board"]

    # --- Cross-check the card against the full ranked list. ---
    if full.get("as_of_session") != session:
        print(f"Qualified Board refresh: the full list is for "
              f"{full.get('as_of_session')} but the board card is for "
              f"{session}; refusing to publish a mismatched page.",
              file=sys.stderr)
        return 1
    full_rows = full["rows"]
    scored = [r for r in full_rows if not r.get("insufficient_data")]
    short = [r for r in full_rows if r.get("insufficient_data")]
    recomputed = {
        "universe": len(full_rows),
        "scored": len(scored),
        "insufficient_data": len(short),
        "qualified": sum(1 for r in scored if r["qualified"]),
    }
    for key, value in recomputed.items():
        if summary.get(key) != value:
            print(f"Qualified Board refresh: the card summary says "
                  f"{key}={summary.get(key)} but the full list holds "
                  f"{value}; refusing to publish a mismatched page.",
                  file=sys.stderr)
            return 1
    top = scored[:len(published_rows)]
    for got, want in zip(published_rows, top):
        if (got["symbol"], got["score"], got["qualified"]) != \
                (want["symbol"], want["score"], want["qualified"]):
            print(f"Qualified Board refresh: the card's published "
                  f"names do not match the top of the full list at "
                  f"{got['symbol']}; refusing to publish a mismatched "
                  "page.", file=sys.stderr)
            return 1

    # --- When was this session's board published? From the log. ---
    published_at = None
    for r in log_rows:
        if r.get("component") == "board-summary" and \
                r.get("value", {}).get("as_of_session") == session:
            if published_at is None or r["ts_utc"] > published_at:
                published_at = r["ts_utc"]
    if published_at is None:
        print(f"Qualified Board refresh: the log holds no board "
              f"publication for session {session}; refusing to show "
              "names without a publication time.", file=sys.stderr)
        return 1

    receipt = {
        "session": session,
        "published_at_utc": published_at,
        "source": "Daily price and trading history for each stock, "
                  "plus public filings on the positions big investors "
                  "report, combined into the same eight checks for "
                  "every name",
        "coverage": (f"{summary['universe']:,} names checked, "
                     f"{summary['scored']:,} scored, "
                     f"{summary['insufficient_data']} with too little "
                     f"data to score, top {len(published_rows)} "
                     "published here"),
    }

    names = []
    for rank, row in enumerate(published_rows, start=1):
        checks = []
        for key, plain in CHECK_NAMES:
            cat = row["categories"].get(key)
            if cat is None or cat.get("state") not in CHECK_STATES:
                print(f"Qualified Board refresh: {row['symbol']} is "
                      f"missing a readable result for the check "
                      f"{plain!r}; refusing to publish a partial row.",
                      file=sys.stderr)
                return 1
            checks.append({
                "name": plain,
                "state": CHECK_STATES[cat["state"]],
                "score": cat.get("score"),
            })
        in_favor = sum(1 for c in checks if c["state"] == "in_favor")
        if in_favor != row["confirming"]:
            print(f"Qualified Board refresh: {row['symbol']} says "
                  f"{row['confirming']} checks lined up but its own "
                  f"check list shows {in_favor}; refusing to publish "
                  "a mismatched page.", file=sys.stderr)
            return 1
        passed = bool(row["qualified"])
        if passed != (not row.get("gate_fails")):
            print(f"Qualified Board refresh: {row['symbol']} has a "
                  "passed flag that disagrees with its missed list; "
                  "refusing to publish a mismatched page.",
                  file=sys.stderr)
            return 1
        missed = missed_words(row)
        if missed is None:
            return 1
        if passed and missed:
            print(f"Qualified Board refresh: {row['symbol']} passed "
                  "every check but carries a missed list; refusing "
                  "to publish a mismatched page.", file=sys.stderr)
            return 1
        names.append({
            "rank_by_score": rank,
            "symbol": row["symbol"],
            "sector": row.get("sector"),
            "close": row.get("close"),
            "score": row.get("score"),
            "passed_every_check": passed,
            "checks_in_favor": in_favor,
            "checks_total": len(CHECK_NAMES),
            "data_behind_score_pct": row.get("dc"),
            "coverage_pct": row.get("dc"),
            "coverage_floor_pct": 70,
            "passes_coverage_floor": (row.get("dc") >= 70 if row.get("dc") is not None else None),
            "checks": checks,
            "missed": missed,
        })

    n_passed = sum(1 for n in names if n["passed_every_check"])
    data = {
        "tool": "Qualified Board",
        "session": session,
        "published_at_utc": published_at,
        "source": receipt["source"],
        "counts": {
            "names_checked": summary["universe"],
            "names_scored": summary["scored"],
            "not_enough_data": summary["insufficient_data"],
            "passed_every_check_all": summary["qualified"],
            "names_published": len(names),
            "passed_every_check_published": n_passed,
        },
        "groups": [{
            "session": session,
            "receipt": receipt,
            "names": names,
        }],
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (session {session}, {len(names)} names "
          f"published, {n_passed} passed every check, published "
          f"{published_at})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
