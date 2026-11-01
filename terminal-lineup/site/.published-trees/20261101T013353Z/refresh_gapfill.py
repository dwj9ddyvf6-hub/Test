#!/usr/bin/env python3
"""Refresh the Gap-Fill Pane data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: the real output of the gap-fill study that is on
record: the published studies card for the freshest study run,
cross-checked against the published feed's copy of the same study
(the summary) and against the permanent log, whose freshest graded
gap-fill entry must match the card exactly. The study was computed
from five-minute prices for SPY, QQQ and IWM over the 90 days of
price history on record when it ran, completed trading days only.

Reconstruction choices, stated as ours: (1) The freshest study run
on record is the one published; older runs (which counted different
fills) stay in the log and are not mixed in. (2) The study's three
size bands are always all shown, in order (under 1%, 1% to 2%, 2%
or more); a band the study found no gaps in shows a count of 0.
(3) A breakdown cell with fewer than 30 events is a thin cell: the
page shows its event count and its fill count and no percentage,
because a percentage on a handful of events reads as far more
certain than it is. (4) Sessions per name is shown only when the
event total divides evenly across the names and every weekday
cell does too, which is the shape the study's own counting
produces (each name counted once per gapped day); otherwise that
figure is left off rather than guessed. (5) The study measures
fills only within the same trading day, so the page states that
timing plainly instead of inventing a typical number of days.

Non-claims: this page claims nothing about any future gap. The
study carries no split of gaps into up gaps and down gaps and no
measure of how many days a fill took beyond the same day, so
neither is shown and neither is invented. A gap that did not fill
on its own day is counted as not filled, however it moved later.

Fail-closed rules: if the studies card, the published feed's
summary of the same study, and the permanent log's freshest graded
gap-fill entry disagree on any figure this page carries, or if the
study's own breakdowns do not add up to its totals, or if any
printed frequency does not recompute from its own counts, the
refresh stops and publishes nothing. All timestamps come from the
sources, never the clock, so running this script twice produces
the same file.

Usage: python3 refresh_gapfill.py
"""

import json
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
OUT_PATH = os.path.join(HERE, "gap-fill", "data.json")

MIN_EVENTS_FOR_PERCENT = 30
BANDS = ["<1%", "1-2%", ">=2%"]
BAND_WORDS = {
    "<1%": "Under 1%",
    "1-2%": "1% to 2%",
    ">=2%": "2% or more",
}
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
WEEKDAY_WORDS = {
    "Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday",
    "Thu": "Thursday", "Fri": "Friday",
}

SOURCE_WORDS = ("Five-minute prices for SPY, QQQ and IWM over the "
                "90 days of price history on record when the study "
                "ran, completed trading days only")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Gap-Fill refresh: {message}", file=sys.stderr)
    return 1


def cell_out(key, words, cell):
    n = cell["n"]
    fills = cell["fills"]
    thin = n < MIN_EVENTS_FOR_PERCENT
    return {
        "key": key,
        "label": words,
        "n": n,
        "fills": fills,
        "frequency": (None if thin else round(fills / n, 4)),
        "thin": thin,
    }


def build():
    for path in (CARD_PATH, FEED_PATH, LOG_PATH, ENGINE_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    card = load_json(CARD_PATH)
    feed = load_json(FEED_PATH)
    gap = card.get("gap_fill") or {}

    # --- The study's universe and history depth, from the engine
    # that ran it (its declared names and lookback). ---
    engine_src = open(ENGINE_PATH, encoding="utf-8").read()
    m = re.search(r'INTRADAY_SYMBOLS\s*=\s*\(([^)]*)\)', engine_src)
    names = re.findall(r'"([A-Z]+)"', m.group(1)) if m else []
    m2 = re.search(r'INTRADAY_LOOKBACK_DAYS\s*=\s*(\d+)', engine_src)
    lookback_days = int(m2.group(1)) if m2 else None
    if not names or not lookback_days:
        return fail("the study engine does not declare its names "
                    "and history depth; refusing to publish a page "
                    "whose coverage is undeclared.")

    if gap.get("state") != "graded":
        return fail(f"the freshest study on record is not a "
                    f"completed count (state "
                    f"{gap.get('state')!r}); refusing to publish "
                    "figures that were not counted.")
    if gap.get("fill_pct") != 1.0:
        return fail(f"the study counted fills at "
                    f"{gap.get('fill_pct')} of the gap, not the "
                    "full gap this page describes; refusing to "
                    "publish a mismatched page.")

    # --- The summary (the published feed's copy) must agree. ---
    feed_gap = (feed.get("studies") or {}).get("gap_fill")
    if feed_gap != gap:
        return fail("the published summary of the study disagrees "
                    "with the study card; refusing to publish a "
                    "mismatched page.")
    # --- The summary must be a copy of this card, not of an older
    # run: the feed's generation time must not precede the card's.
    # (The feed's as_of_session is the board's session date, a
    # different date kind from the study card's run date; comparing
    # them refused every coherent cycle. Cured 2026-10-30 in the
    # pattern of refresh_earningsdrift.py: exact figure agreement
    # above, plus generation order here.) ---
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

    # --- The permanent log's freshest graded gap-fill entry must
    # match the card exactly. ---
    with open(LOG_PATH, encoding="utf-8") as fh:
        log_rows = [json.loads(line) for line in fh if line.strip()]
    graded = [r for r in log_rows
              if r.get("component") == "study-gap-fill"
              and (r.get("value") or {}).get("state") == "graded"]
    if not graded:
        return fail("the permanent log holds no completed gap-fill "
                    "study; refusing to show a study that is not "
                    "on the record.")
    if graded[-1].get("value") != gap:
        return fail("the permanent log's freshest completed "
                    "gap-fill study differs from the study card; "
                    "refusing to publish a mismatched page.")

    # --- The study's own arithmetic must hold together. ---
    n = gap["n"]
    fills = gap["fills"]
    if n <= 0 or not (0 <= fills <= n):
        return fail(f"the study's totals do not hold together "
                    f"({fills} fills of {n} gaps); refusing to "
                    "publish.")
    if abs(gap["frequency"] - fills / n) > 1e-9:
        return fail("the study's overall share filled does not "
                    "recompute from its own counts; refusing to "
                    "publish.")
    parts = gap.get("partitions") or {}
    by_band_src = parts.get("by_band") or {}
    by_weekday_src = parts.get("by_weekday") or {}
    for label, part in (("size band", by_band_src),
                        ("weekday", by_weekday_src)):
        if sum(c["n"] for c in part.values()) != n or \
                sum(c["fills"] for c in part.values()) != fills:
            return fail(f"the study's by-{label} counts do not "
                        f"add up to its totals ({n} gaps, {fills} "
                        "fills); refusing to publish.")
        for key, c in part.items():
            if c["n"] and abs(c["frequency"] - c["fills"] / c["n"]) > 1e-9:
                return fail(f"the study's {label} cell {key} has a "
                            "share that does not recompute from its "
                            "own counts; refusing to publish.")
    unknown_bands = sorted(set(by_band_src) - set(BANDS))
    if unknown_bands:
        return fail(f"the study carries size bands this page does "
                    f"not know: {unknown_bands}; refusing to "
                    "publish a partial breakdown.")

    # --- Sessions per name, only in the shape the counting
    # itself guarantees (see the register triple). ---
    sessions_per_name = None
    if n % len(names) == 0 and all(
            c["n"] % len(names) == 0 for c in by_weekday_src.values()):
        sessions_per_name = n // len(names)

    by_band = [cell_out(b, BAND_WORDS[b],
                        by_band_src.get(b, {"n": 0, "fills": 0}))
               for b in BANDS]
    by_weekday = [cell_out(d, WEEKDAY_WORDS[d], by_weekday_src[d])
                  for d in WEEKDAYS if d in by_weekday_src]

    data = {
        "tool": "Gap-Fill Pane",
        "state": "graded",
        "as_of": card["as_of"],
        "published_at_utc": card["generated_at"],
        "source": SOURCE_WORDS,
        "names": names,
        "name_count": len(names),
        "lookback_days": lookback_days,
        "sessions_per_name": sessions_per_name,
        "events": n,
        "fills": fills,
        "frequency": round(fills / n, 4),
        "thin_threshold": MIN_EVENTS_FOR_PERCENT,
        "by_band": by_band,
        "by_weekday": by_weekday,
        "receipt": {
            "session": card["as_of"],
            "published_at_utc": card["generated_at"],
            "source": SOURCE_WORDS,
            "coverage": (f"{n} gap events counted across "
                         f"{len(names)} names "
                         f"({', '.join(names)}), from the "
                         f"{lookback_days} days of price history "
                         "on record when the study ran"),
        },
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} ({n} gaps, {fills} filled, "
          f"{len(names)} names, as of {card['as_of']}, "
          f"published {card['generated_at']})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
