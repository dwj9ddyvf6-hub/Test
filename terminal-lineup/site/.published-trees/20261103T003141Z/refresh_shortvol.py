#!/usr/bin/env python3
"""Refresh the Short Volume Ledger data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: the stored daily short-sale volume record itself:
one stored file per trading day, each holding, for every stock in
that day's published file, the shares sold short that day and the
day's total shares traded. Two further carriers stamp the same
collection's state (the gathering record and the published daily
summary); both stamps must agree with each other and with the days
actually stored, or the refresh stops.

Reconstruction choices: the only figure computed here is each day's
short share: the shares sold short that day divided by that day's
total shares traded, shown as a percentage of that day's own volume
next to the day it measures. It is a measurement of that day, not a
tally over days, so it is shown per day however few days are stored.
A stock missing from a day's file is carried as a missing day for
that stock, never as a zero. Ticker spelling follows the stored
record's own spelling. Page window (2026-10-29, when the store went
live with a multi-year backfill): each stock's published ledger
carries the freshest 20 stored days; the store itself keeps every
stored day, and the coverage line states both numbers, so the page
window is never mistaken for the store.

Non-claims: this tool does not publish short interest (the shares
still owed back from earlier short sales); that is a different
measure, counted twice a month, and nothing on this page is it. It
makes no claim about why any day's short share was what it was, and
it publishes nothing for a day that is not stored.

Fail-closed rules: if the two state stamps disagree with each
other; if either stamp's state disagrees with the days actually
stored (a no-data stamp while days are stored, or a live stamp
while none are); if a stored day's own date does not match the day
it is filed under; if a stored day carries a short count above its
total or a value that is not a number, the refresh stops and
publishes nothing. A row whose total is zero is a placeholder in
the published file, not a reading: that day is missing for that
name, exactly as if the name were absent from the file.

Honesty rules:
- Dates are read off the sources, never from the clock. The
  checked date comes from the state stamps, and every day shown
  comes from a stored file, so running this script twice produces
  the same file.
- Absence is not zero: zero stored days is published as the plain
  not-yet-collecting state, and a missing day inside a stored
  history stays missing.

Usage: python3 refresh_shortvol.py
"""

import gzip
import json
import os
import sys

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
MORGUE = os.path.expanduser("~/workspace/morgue")
SHORTVOL_DIR = os.path.join(MORGUE, "state", "morgue", "shortvol")
EXT_PATH = os.path.join(MORGUE, "state", "morgue", "ext.json")
FEED_PATH = os.path.join(MORGUE, "output", "morgue-feed.json")
OUT_PATH = os.path.join(HERE, "short-volume", "data.json")

PAGE_DAYS = 20  # page window per stock; the store keeps every day

SOURCE_WORDS = ("The daily short-sale volume files published for "
                "every stock after each trading day's close: one "
                "file per day, listing the shares sold short that "
                "day and the total shares traded that day")
DELAY_WORDS = ("Each day's file is published after that day's "
               "close, so a day appears here only once its file "
               "has been published and stored")
DISTINCTION_WORDS = ("Short volume counts the shares sold short "
                     "on that one day; short interest counts the "
                     "shares still owed back from all earlier "
                     "short sales that have not been covered yet.")
EMPTY_COVERAGE = ("The daily short-sale volume collection this "
                  "page reads has not started: 0 days on record, "
                  "no stock on record, and no most recent day. "
                  "Nothing is shown for any stock because there "
                  "is no stored day to show")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Short Volume Ledger refresh: {message}",
          file=sys.stderr)
    return 1


def lane_stamp(doc):
    lanes = (doc.get("lanes") or {}).get("lanes") or {}
    return lanes.get("short_volume")


def stored_days():
    try:
        names = os.listdir(SHORTVOL_DIR)
    except OSError:
        return []
    return sorted(n[:-8] for n in names if n.endswith(".json.gz"))


def build():
    for path in (EXT_PATH, FEED_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    ext_stamp = lane_stamp(load_json(EXT_PATH))
    feed_doc = load_json(FEED_PATH)
    feed_stamp = lane_stamp(feed_doc)
    if not ext_stamp or not feed_stamp:
        return fail("one of the records carries no short-sale "
                    "volume state stamp; refusing to guess the "
                    "collection's state.")
    if ext_stamp != feed_stamp:
        return fail("the two records stamp the short-sale volume "
                    "collection differently; refusing to publish "
                    "until they agree.")
    stamp = ext_stamp
    as_of = stamp.get("as_of")
    if not as_of:
        return fail("the state stamp carries no date; refusing "
                    "to guess.")

    days = stored_days()

    if not days:
        if stamp.get("status") != "no_data" \
                or stamp.get("reason") != "no FINRA day stored yet":
            return fail("no day is stored, but the state stamp "
                        "does not say the collection is empty; "
                        "refusing to publish a state the records "
                        "do not agree on.")
        data = {
            "tool": "Short Volume Ledger",
            "state": "not_yet_collecting",
            "checked": as_of,
            "days_on_record": 0,
            "freshest_day": None,
            "tickers": [],
            "source": SOURCE_WORDS,
            "delay": DELAY_WORDS,
            "distinction": DISTINCTION_WORDS,
            "coverage": EMPTY_COVERAGE,
            "receipt": {
                "checked": as_of,
                "source": SOURCE_WORDS,
                "coverage": EMPTY_COVERAGE,
            },
        }
    else:
        if stamp.get("status") == "no_data":
            return fail(f"{len(days)} day(s) are stored, but the "
                        "state stamp still says no day is stored; "
                        "refusing to publish until the records "
                        "agree.")
        per_ticker = {}
        for day in days:
            path = os.path.join(SHORTVOL_DIR, f"{day}.json.gz")
            try:
                with gzip.open(path, "rt", encoding="utf-8") as fh:
                    doc = json.load(fh)
            except (OSError, ValueError, EOFError):
                return fail(f"the stored day {day} cannot be "
                            "read; refusing to publish a partial "
                            "ledger.")
            if doc.get("date") != day:
                return fail(f"the stored day filed as {day} calls "
                            f"itself {doc.get('date')}; refusing "
                            "to publish a mismatched day.")
            names = doc.get("names") or {}
            if not names:
                return fail(f"the stored day {day} carries no "
                            "stocks; a stored day with nothing in "
                            "it is a broken record, not a zero day.")
            for sym, pair in names.items():
                if not isinstance(pair, (list, tuple)) \
                        or len(pair) != 2:
                    return fail(f"{sym} on {day}: the stored "
                                "record is not a short count and "
                                "a total; refusing to publish.")
                short, total = pair
                if not isinstance(short, (int, float)) \
                        or not isinstance(total, (int, float)) \
                        or isinstance(short, bool) \
                        or isinstance(total, bool):
                    return fail(f"{sym} on {day}: the stored "
                                "figures are not numbers; refusing "
                                "to publish.")
                if short < 0 or short > total:
                    return fail(f"{sym} on {day}: the stored "
                                f"figures (short {short}, total "
                                f"{total}) cannot describe a day; "
                                "refusing to publish.")
                if total <= 0:
                    # A zero-total row in the published file is
                    # a placeholder, not a reading: the name did
                    # not trade that day, so the day is missing
                    # for that name, never a zero reading (the
                    # same rule refresh_darkprints applies).
                    continue
                per_ticker.setdefault(sym, {})[day] = (short, total)
        page_days = days[-PAGE_DAYS:]
        tickers = []
        for sym in sorted(per_ticker):
            rows = []
            for day in page_days:
                got = per_ticker[sym].get(day)
                if got is None:
                    rows.append({"date": day, "state": "missing"})
                else:
                    short, total = got
                    rows.append({
                        "date": day, "state": "recorded",
                        "short_volume": short,
                        "total_volume": total,
                        "short_share_pct":
                            round(short / total * 100.0, 1),
                    })
            tickers.append({"symbol": sym, "days": rows})
        coverage = (f"{len(days)} day(s) on record in the store, "
                    f"from {days[0]} to {days[-1]}, covering "
                    f"{len(tickers)} stock(s). This page shows "
                    f"each stock's freshest {len(page_days)} "
                    f"stored day(s) ({page_days[0]} to "
                    f"{page_days[-1]}); the store keeps every day. "
                    "A day a stock is missing from is shown as "
                    "missing, never as zero")
        data = {
            "tool": "Short Volume Ledger",
            "state": "collecting",
            "checked": as_of,
            "days_on_record": len(days),
            "freshest_day": days[-1],
            "page_days_shown": len(page_days),
            "tickers": tickers,
            "source": SOURCE_WORDS,
            "delay": DELAY_WORDS,
            "distinction": DISTINCTION_WORDS,
            "coverage": coverage,
            "receipt": {
                "checked": as_of,
                "source": SOURCE_WORDS,
                "coverage": coverage,
            },
        }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (state {data['state']}, "
          f"{data['days_on_record']} days on record, checked "
          f"{as_of})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
