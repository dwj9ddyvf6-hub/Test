#!/usr/bin/env python3
"""Refresh the Strat Scanner data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: the real daily price history behind the daily
scoring run (1,833 scored names, 399 sessions, March 25, 2025 to
October 23, 2026), labelled by our own working copy of the
published TheStrat bar-pattern rules. That copy passes its own
21 known-answer tests against the publisher's own published
examples; this refresh re-runs that whole test suite in this
environment first and publishes nothing if any test fails.

Reconstruction choices (the exact construction):
- The session scanned is the freshest session in the daily price
  history (October 23, 2026 on the current history). A name is
  labelled for that session only when it has a bar that day and
  at least 3 bars on record; names with no bar that day are
  counted as not labelled and show nothing.
- Groups are the four daily bar labels the rule copy assigns,
  in the publisher's published terms: 1 (inside bar), 2-up,
  2-down, and 3 (outside bar). Every labelled name sits in
  exactly one group: the label of its freshest bar. A plain-words
  meaning for each label is printed once, with its group.
- Each name also carries: the closing colour of its freshest bar
  (closed above, below, or at its open, in the copy's own words
  green / red / flat), its shape tag where the copy gives one
  (hammer or shooter), its failed-2 flag where the copy gives one
  (kept in the copy's exact words), the multi-bar patterns the
  copy itself names as completed on the freshest bar, and its
  label sequence for the last 5 sessions.
- Nothing from the rule copy that points anywhere is published:
  no direction word, no trigger, target, or level from its
  setup records is read into this page at all. Labels only.

Non-claims: this page names the pattern each name's bars showed;
it claims no edge, makes no forecast, and gives no direction or
suggestion. The scanner's output has no forward record yet: it
publishes in the proving state the site's proving page defines
("Still being proven"), stated on the page in those words.

Fail-closed rules:
- If the rule copy's own test suite does not pass in this
  environment (21 tests, all passing), the refresh stops.
- If the scored run's summary card and its full scored list
  disagree with each other (checked, scored, too little data,
  passed every check, or the session), or the price history's
  name set differs from the scored run's scored names in either
  direction, the refresh stops.
- If any bar is malformed, out of order, or carries a
  non-numeric price; if a labelled name's freshest label is
  missing; if the four group counts do not add up to the
  labelled count; or if any published string carries a direction
  word from the rule copy's setup records, the refresh stops.

Honesty rules:
- Dates are read off the sources, never from the clock: the
  session and the history's span come from the bars themselves,
  so running this script twice produces the same file, byte for
  byte.
- Absence is not zero: a name with no bar on the scanned session
  is counted as not labelled and shows nothing.

Usage: python3 refresh_stratscanner.py
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MORGUE = os.path.expanduser("~/workspace/morgue")
REPLICA_DIR = os.path.expanduser(
    "~/workspace/opt/rea-teardowns/thestrat/replica")
CARD_PATH = os.path.join(MORGUE, "output", "board_card.json")
FULL_PATH = os.path.join(MORGUE, "output", "board_full.json")
BARS_PATH = os.path.join(MORGUE, "data_cache", "board_bt_bars.json")
OUT_PATH = os.path.join(HERE, "strat-scanner", "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

sys.path.insert(0, REPLICA_DIR)
import strat_replica as replica  # noqa: E402

try:
    import aperture_policy as _ap
except ImportError:  # policy ledger is part of this surface
    _ap = None

SEQUENCE_SESSIONS = 5

SOURCE_WORDS = ("Daily closing prices from the consolidated tape "
                "records for the stocks in the daily scoring run, "
                "labelled by a working copy of the published "
                "TheStrat bar-pattern rules that passes all 21 of "
                "its known-answer tests against the publisher's "
                "own published examples")

PROVING_WORDS = "Still being proven"
PROVING_NOTE = ("Still being proven: this scanner's labels have no "
                "forward record yet. The labels below name the "
                "pattern each name's bars showed on the day; "
                "nothing has graded what happened after them, and "
                "the page makes no claim about what follows a label.")

GROUPS = [
    {
        "key": "1",
        "label": "1",
        "name": "Inside bar",
        "meaning": ("The day's bar stayed inside the day before: "
                    "its highest price did not pass the day "
                    "before's highest, and its lowest price did "
                    "not pass the day before's lowest."),
    },
    {
        "key": "2u",
        "label": "2-up",
        "name": "Took the high side only",
        "meaning": ("The day's bar passed the day before's highest "
                    "price, but did not pass its lowest price."),
    },
    {
        "key": "2d",
        "label": "2-down",
        "name": "Took the low side only",
        "meaning": ("The day's bar passed the day before's lowest "
                    "price, but did not pass its highest price."),
    },
    {
        "key": "3",
        "label": "3",
        "name": "Outside bar",
        "meaning": ("The day's bar passed both sides of the day "
                    "before: its highest price passed the day "
                    "before's highest, and its lowest price passed "
                    "the day before's lowest. Daily prices alone "
                    "cannot say which side was passed first, so "
                    "the label is the plain 3."),
    },
]

WORDS = {
    "colour": ("Closed above its open (shown as green), below its "
               "open (red), or exactly at its open (flat)."),
    "hammer": ("Hammer shape: the whole body of the day's bar, "
               "from its open to its close, sits in the top third "
               "of the day's range."),
    "shooter": ("Shooter shape: the whole body of the day's bar, "
                "from its open to its close, sits in the bottom "
                "third of the day's range."),
    "failed_2u": ("Failed 2-up: the bar took the day before's high "
                  "but closed below where it opened."),
    "failed_2d": ("Failed 2-down: the bar took the day before's low "
                  "but closed above where it opened."),
    "completed": ("Completed patterns name a run of labels over "
                  "the last few days that the rules count as a "
                  "finished pattern on the scanned day, such as a "
                  "2-2 reversal: two 2 bars in a row pointing "
                  "opposite ways in their labels."),
    "sequence": ("Each name shows its labels for the last "
                 f"{SEQUENCE_SESSIONS} sessions, oldest first, so "
                 "the pattern sits in its recent run."),
}

FORBIDDEN = ("bullish", "bearish", "trigger", "level_of_reclaim",
             "failure_level")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Strat Scanner refresh: {message}", file=sys.stderr)
    return 1


def build():
    for path in (CARD_PATH, FULL_PATH, BARS_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")
    if not os.path.isdir(REPLICA_DIR):
        return fail("the bar-pattern rule copy was not found; "
                    "refusing to publish.")

    # --- Gate 1: the rule copy's own test suite must pass here.
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s",
         "tests"],
        cwd=REPLICA_DIR, capture_output=True, text=True)
    tail = (proc.stderr or "") + (proc.stdout or "")
    if proc.returncode != 0 or "Ran 21 tests" not in tail \
            or not tail.rstrip().endswith("OK"):
        return fail("the bar-pattern rule copy's own test suite "
                    "did not pass in this environment (21 tests "
                    "expected, all passing); refusing to publish. "
                    f"Test output tail: {tail.strip()[-300:]}")

    card = load_json(CARD_PATH)
    full = load_json(FULL_PATH)
    bars_hist = load_json(BARS_PATH)

    # --- Gate 2: the scored run's published counts must agree
    # with its full list, and the history must hold exactly its
    # scored names.
    summary = card["summary"]
    run_session = summary["as_of_session"]
    if full.get("as_of_session") != run_session:
        return fail(f"the full scored list is for "
                    f"{full.get('as_of_session')} but the scored "
                    f"run's card is for {run_session}; refusing "
                    "to publish a mismatched page.")
    rows = full["rows"]
    scored = [r for r in rows if not r.get("insufficient_data")]
    short = [r for r in rows if r.get("insufficient_data")]
    recomputed = {
        "universe": len(rows),
        "scored": len(scored),
        "insufficient_data": len(short),
        "qualified": sum(1 for r in scored if r["qualified"]),
    }
    for key, value in recomputed.items():
        if summary.get(key) != value:
            return fail(f"the scored run's card says {key}="
                        f"{summary.get(key)} but its full list "
                        f"holds {value}; refusing to publish a "
                        "mismatched page.")
    scored_names = {r["symbol"] for r in scored}
    if set(bars_hist) != scored_names:
        return fail(f"the price history holds "
                    f"{len(bars_hist)} names but the scored run "
                    f"scored {len(scored_names)}; the names differ "
                    f"(history only: "
                    f"{sorted(set(bars_hist) - scored_names)[:5]}, "
                    f"run only: "
                    f"{sorted(scored_names - set(bars_hist))[:5]}); "
                    "refusing to publish a mismatched page.")
    if not bars_hist:
        return fail("the price history is empty; refusing to "
                    "publish.")

    # --- Validate every bar and find the freshest session.
    calendar = set()
    for symbol, stock_rows in bars_hist.items():
        prev = None
        for row in stock_rows:
            if len(row) != 6:
                return fail(f"{symbol} has a bar that is not a "
                            "dated open, high, low, close and "
                            "volume; refusing to publish.")
            date = row[0]
            if prev is not None and date <= prev:
                return fail(f"{symbol} has a repeated or "
                            f"out-of-order session {date}; "
                            "refusing to publish.")
            for value in row[1:5]:
                if not isinstance(value, (int, float)) \
                        or isinstance(value, bool):
                    return fail(f"{symbol} has a price that is "
                                f"not a number on {date}; refusing "
                                "to publish.")
            prev = date
            calendar.add(date)
    calendar = sorted(calendar)
    if not calendar:
        return fail("the price history holds no dated bars; "
                    "refusing to publish.")
    session = calendar[-1]

    # --- Run the real rule copy over the real history.
    groups = {g["key"]: [] for g in GROUPS}
    labelled = 0
    not_labelled = 0
    exclusions = []
    shape_counts = {"hammer": 0, "shooter": 0}
    failed_count = 0
    completed_count = 0
    for symbol in sorted(bars_hist):
        stock_rows = bars_hist[symbol]
        if stock_rows[-1][0] != session or len(stock_rows) < 3:
            not_labelled += 1
            # APERTURE-POLICY-20261029 (DEEP-PASS 3.2 item 1):
            # an unlabelled name is ledgered per name with its
            # reasons, never only counted in aggregate.
            if _ap is None:
                return fail("the candidate policy module was "
                            "not found; refusing to publish "
                            "exclusions without their ledger.")
            _why = []
            if stock_rows[-1][0] != session:
                _why.append("no_bar_on_scanned_session")
            if len(stock_rows) < 3:
                _why.append("fewer_than_3_bars")
            exclusions.append(_ap.exclusion_record(symbol, _why))
            continue
        bars = [{"t": r[0], "o": r[1], "h": r[2], "l": r[3],
                 "c": r[4], "v": r[5]} for r in stock_rows]
        classified = replica.classify_bars(bars)
        today = classified[-1]
        if today["scenario"] not in groups:
            return fail(f"{symbol} has no label for {session}; "
                        "refusing to publish.")
        completed = [label for idx, label in
                     replica.completed_sequences(bars)
                     if idx == len(bars) - 1]
        if today["shape"] in shape_counts:
            shape_counts[today["shape"]] += 1
        if today["failed_2"]:
            failed_count += 1
        completed_count += len(completed)
        sequence = [{"date": c["t"], "label": c["scenario"]}
                    for c in classified[-SEQUENCE_SESSIONS:]]
        groups[today["scenario"]].append({
            "symbol": symbol,
            "label": today["scenario"],
            "colour": today["color"],
            "shape": today["shape"],
            "failed_2": today["failed_2"],
            "completed": completed,
            "sequence": sequence,
        })
        labelled += 1

    if labelled == 0:
        return fail(f"no name could be labelled for {session}; "
                    "refusing to publish an empty scan.")
    if sum(len(v) for v in groups.values()) != labelled:
        return fail("the group counts do not add up to the "
                    "labelled count; refusing to publish.")
    if labelled + not_labelled != len(scored_names):
        return fail("the labelled and not-labelled counts do not "
                    "add up to the scored names; refusing to "
                    "publish.")

    coverage = (
        f"{labelled:,} of the {len(scored_names):,} names in the "
        f"daily scoring run were labelled for {session}; "
        f"{not_labelled} had no bar that day and show nothing; "
        f"the price history on record holds "
        f"{len(calendar)} sessions, from {calendar[0]} to "
        f"{session}")

    data = {
        "tool": "Strat Scanner",
        "state": "published",
        "session": session,
        "scored_run_session": run_session,
        "source": SOURCE_WORDS,
        "proving_state": PROVING_WORDS,
        "proving_note": PROVING_NOTE,
        "history_sessions_on_record": len(calendar),
        "history_from": calendar[0],
        "history_to": session,
        "names_on_record": len(scored_names),
        "names_labelled": labelled,
        "names_not_labelled": not_labelled,
        "exclusions": exclusions,
        "shape_counts": shape_counts,
        "failed_2_count": failed_count,
        "completed_patterns_count": completed_count,
        "sequence_sessions": SEQUENCE_SESSIONS,
        "words": WORDS,
        "groups": [
            {
                "key": g["key"],
                "label": g["label"],
                "name": g["name"],
                "meaning": g["meaning"],
                "count": len(groups[g["key"]]),
                "names": groups[g["key"]],
            } for g in GROUPS
        ],
        "coverage": coverage,
        "receipt": {
            "session": session,
            "source": SOURCE_WORDS,
            "coverage": coverage,
        },
    }

    data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
    blob = json.dumps(data, indent=2, sort_keys=True)
    for word in FORBIDDEN:
        if word in blob:
            return fail(f"a direction or setup word ({word}) "
                        "reached the output; refusing to publish "
                        "anything but labels.")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(blob)
        fh.write("\n")
    counts = ", ".join(f"{g['label']} "
                       f"{len(groups[g['key']])}" for g in GROUPS)
    print(f"Wrote {OUT_PATH} (session {session}, {labelled:,} "
          f"labelled of {len(scored_names):,}; {counts})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
