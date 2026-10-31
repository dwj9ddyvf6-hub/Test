#!/usr/bin/env python3
"""Refresh the Earnings Drift Pane data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: the real output of the earnings study that is on
record: the published studies card for the freshest study run,
cross-checked against the published feed's copy of the same study
(the summary) and against the permanent log, whose freshest graded
earnings entry must match the card exactly. The study counted
earnings events for AAPL, MSFT and NVDA from the companies' public
filings, and measured each event with daily closing prices over the
1,095 days of price history on record when it ran, completed
trading days only.

Reconstruction choices, stated as ours: (1) The freshest study run
on record is the one published; older runs (including the earlier
runs that found no events on the data then owned) stay in the log
and are not mixed in. (2) The count of reports that ended higher is
derived from the study's stored share of positive moves, and the
refresh publishes it only when that share reproduces a whole count
exactly; the rest of the events are counted as not ending higher.
(3) The study carries one pooled count across the three names and
no breakdown of any kind, so the page shows the pooled count only:
no per-name split, no split by year, and no 5-day or 21-day move
after a report is shown, because the study never measured one; the
page states that plainly instead of inventing those windows.
(4) A count with fewer than 30 events is a thin count: the page
shows its event counts and no percentage of any kind, headline
included, because a percentage on a handful of events reads as far
more certain than it is. (5) The measured move is stated as what it
is: the report day's own close-to-close move (the close of the
first trading day on or after the filing, against the close just
before it), not a multi-day drift window.

Scope: this page states what the counted stocks did on their
report days in the history on record. The individual report dates
and the individual moves are not in the record the study left
behind (only its pooled summary is), so neither is shown and
neither is invented. Tonight's and last night's reporting names are
not in the record either, so no such list is shown.

Fail-closed rules: if the studies card, the published feed's
summary of the same study, and the permanent log's freshest graded
earnings entry disagree on any figure this page carries, or if the
study's own figures do not recompute from each other (the share of
positive moves from its counts, the steadiness score from its
average and spread), or if the counted events exceed what the
engine's own per-name cap allows, the refresh stops and publishes
nothing. The feed's summary is bound to the card it copies by that
exact figure agreement plus generation order: the feed must carry
a generation time at or after the card's, or the summary on record
predates the study it claims to copy and the refresh stops. The
feed's own session date is not compared to the card's date: the
session date is the board's last completed session (the feed
takes it from the board summary), while the card's date is the
calendar day the study ran, and the daily rhythm runs the board
before the open on the prior session and the studies after the
close today, so the two dates differ on every coherent cycle.
All timestamps come from the sources, never the clock, so
running this script twice produces the same file.

Usage: python3 refresh_earningsdrift.py
"""

import json
import math
import os
import re
import sys
from datetime import datetime

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.expanduser("~/workspace/morgue/output")
CARD_PATH = os.path.join(SOURCE_DIR, "studies_card.json")
FEED_PATH = os.path.join(SOURCE_DIR, "morgue-feed.json")
LOG_PATH = os.path.join(SOURCE_DIR, "ledger.jsonl")
ENGINE_PATH = os.path.expanduser("~/workspace/morgue/studies_card.py")
STUDY_PATH = os.path.expanduser("~/workspace/morgue/studies.py")
OUT_PATH = os.path.join(HERE, "earnings-drift", "data.json")

MIN_EVENTS_FOR_PERCENT = 30

SOURCE_WORDS = ("Report dates from the three companies' public "
                "filings, and daily closing prices over the "
                "1,095 days of price history on record when the "
                "study ran, completed trading days only")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Earnings Drift refresh: {message}", file=sys.stderr)
    return 1


def build():
    for path in (CARD_PATH, FEED_PATH, LOG_PATH, ENGINE_PATH,
                 STUDY_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    card = load_json(CARD_PATH)
    feed = load_json(FEED_PATH)
    earn = card.get("earnings_dist") or {}

    # --- The study's universe, history depth and per-name cap,
    # from the engine that ran it (its declared names, lookback
    # and event cap). ---
    engine_src = open(ENGINE_PATH, encoding="utf-8").read()
    m = re.search(r'EARNINGS_SYMBOLS\s*=\s*\(([^)]*)\)', engine_src)
    names = re.findall(r'"([A-Z]+)"', m.group(1)) if m else []
    m2 = re.search(r'EARNINGS_LOOKBACK_DAYS\s*=\s*(\d+)', engine_src)
    lookback_days = int(m2.group(1)) if m2 else None
    study_src = open(STUDY_PATH, encoding="utf-8").read()
    m3 = re.search(r'def earnings_moves\([^)]*cap:\s*int\s*=\s*(\d+)',
                   study_src)
    cap = int(m3.group(1)) if m3 else None
    if not names or not lookback_days or not cap:
        return fail("the study engine does not declare its names, "
                    "history depth and per-name event cap; "
                    "refusing to publish a page whose coverage is "
                    "undeclared.")
    if earn.get("symbols") != names:
        return fail(f"the study counted {earn.get('symbols')} but "
                    f"the engine declares {names}; refusing to "
                    "publish a mismatched page.")

    if earn.get("state") != "graded":
        return fail(f"the freshest study on record is not a "
                    f"completed count (state "
                    f"{earn.get('state')!r}); refusing to publish "
                    "figures that were not counted.")

    # --- The summary (the published feed's copy) must agree. ---
    feed_earn = (feed.get("studies") or {}).get("earnings_dist")
    if feed_earn != earn:
        return fail("the published summary of the study disagrees "
                    "with the study card; refusing to publish a "
                    "mismatched page.")
    # --- The summary must be a copy of this card, not of an older
    # run: the feed's generation time must not precede the card's.
    # (The feed's as_of_session is the board's session date, a
    # different date from the study's run date by construction;
    # comparing them refused every coherent cycle.) ---
    try:
        card_ts = datetime.fromisoformat(card["generated_at"])
        feed_ts = datetime.fromisoformat(feed["generated_at_utc"])
        stale = feed_ts < card_ts
    except (KeyError, TypeError, ValueError):
        return fail("the study card and the published summary do "
                    "not both carry a generation time; refusing "
                    "to publish a summary whose run cannot be "
                    "bound to the card.")
    if stale:
        return fail("the published summary was generated "
                    f"{feed.get('generated_at_utc')} before the "
                    f"study card it copies "
                    f"({card.get('generated_at')}); refusing to "
                    "publish a stale summary.")

    # --- The permanent log's freshest graded earnings entry must
    # match the card exactly. ---
    with open(LOG_PATH, encoding="utf-8") as fh:
        log_rows = [json.loads(line) for line in fh if line.strip()]
    graded = [r for r in log_rows
              if r.get("component") == "study-earnings-dist"
              and (r.get("value") or {}).get("state") == "graded"]
    if not graded:
        return fail("the permanent log holds no completed earnings "
                    "study; refusing to show a study that is not "
                    "on the record.")
    if graded[-1].get("value") != earn:
        return fail("the permanent log's freshest completed "
                    "earnings study differs from the study card; "
                    "refusing to publish a mismatched page.")

    # --- The study's own arithmetic must hold together. ---
    n = earn["n"]
    if n < 3:
        return fail(f"the study counted only {n} events, below "
                    "the 3 its own counting requires; refusing to "
                    "publish.")
    if n > len(names) * cap:
        return fail(f"the study counted {n} events, more than its "
                    f"own cap allows ({cap} per name across "
                    f"{len(names)} names); refusing to publish.")
    for key in ("mean", "median", "std", "share_positive",
                "sharpe"):
        if not isinstance(earn.get(key), (int, float)) or \
                not math.isfinite(earn[key]):
            return fail(f"the study's {key} is not a finite "
                        "number; refusing to publish.")
    positive = round(earn["share_positive"] * n)
    if abs(earn["share_positive"] - positive / n) > 1e-9:
        return fail("the study's share of moves that ended higher "
                    "does not reproduce a whole count of events; "
                    "refusing to publish.")
    if earn["std"] <= 0:
        return fail("the study's spread of moves is not positive; "
                    "refusing to publish.")
    if abs(earn["sharpe"] - earn["mean"] / earn["std"]) > 1e-9:
        return fail("the study's steadiness score does not "
                    "recompute from its own average and spread; "
                    "refusing to publish.")

    thin = n < MIN_EVENTS_FOR_PERCENT
    data = {
        "tool": "Earnings Drift Pane",
        "state": "graded",
        "as_of": card["as_of"],
        "published_at_utc": card["generated_at"],
        "source": SOURCE_WORDS,
        "names": names,
        "name_count": len(names),
        "lookback_days": lookback_days,
        "max_events_per_name": cap,
        "max_events": len(names) * cap,
        "events": n,
        "positive": positive,
        "not_positive": n - positive,
        "thin": thin,
        "thin_threshold": MIN_EVENTS_FOR_PERCENT,
        "share_positive": (None if thin
                           else earn["share_positive"]),
        "mean": (None if thin else earn["mean"]),
        "median": (None if thin else earn["median"]),
        "std": (None if thin else earn["std"]),
        "sharpe": (None if thin else earn["sharpe"]),
        "receipt": {
            "session": card["as_of"],
            "published_at_utc": card["generated_at"],
            "source": SOURCE_WORDS,
            "coverage": (f"{n} earnings reports counted across "
                         f"{len(names)} names "
                         f"({', '.join(names)}), up to the {cap} "
                         "most recent reports per name, from the "
                         f"{lookback_days} days of price history "
                         "on record when the study ran"),
        },
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} ({n} earnings reports, {positive} "
          f"ended higher, {len(names)} names, as of "
          f"{card['as_of']}, published {card['generated_at']})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
