#!/usr/bin/env python3
"""Refresh the Breakout Scanner data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: the same shipped daily price history the AI Chart
Read carries (daily bars with open, high, low and close for every
scored stock, 399 trading sessions from March 25, 2025 to October
23, 2026), cross-checked bar for bar against the AI Chart Read's
own published data file, and against the scored run's published
counts (the board card's summary and the full scored list: 1,838
stocks checked, 1,833 scored, 5 with too little data to score).
The page ships that history's closing prices only, trimmed to what
its three measures need, and every figure on the page is worked
out in the reader's own browser from those closes; nothing the
reader picks is sent anywhere.

Reconstruction choices (the exact constructions, frozen here and
printed on the page in plain words):
- Distance from the high: a name's high is the highest closing
  price over its most recent 252 sessions, ending on its own last
  session on record. The distance is how far the last close sits
  below that high, as a percent of the high. A name with fewer
  than 252 sessions on record has no 252-session high: its high is
  taken over the sessions it does have, the row names that real
  window, and the page counts how many names are in that position.
- Tightness: over the name's last 10 sessions, the highest close
  minus the lowest close, as a percent of the last close. A
  smaller number means the closes sat in a narrower band.
- Rise over 21 sessions: the last close compared with the close
  21 sessions before it (so the measure spans 21 steps and needs
  22 closes), as a percent.
- Freshness is per name: 16 names on record stopped trading
  before the history's last session, and each such name's figures
  are dated to its own last session on the page, never presented
  as a reading for the history's last session.
- The list shows the names whose distance is at or under the
  reader's chosen percent (within 2, 5 or 10 percent), tightest
  first (smallest tightness first; ties broken by name).

Scope: the names on record are the stocks in the daily scoring
run, stated as such on the page. The page describes past prices
only: it carries no statement about what any name did after it
appeared on the list, and no graded record of that exists.

Honesty rules:
- If the card, the full list, the price history and the AI Chart
  Read's published file disagree with each other in any check
  (the card's counts against its own list, the history holding
  exactly the scored names, every shipped close matching the AI
  Chart Read's closes for the same name and session, each name's
  sessions a continuous run of the shared calendar, or the
  counted window support disagreeing with the counts this script
  publishes), the script fails instead of publishing a mismatched
  page.
- Running this script twice on the same sources produces the
  same file, byte for byte. All dates come from the sources,
  never from the clock.

Usage: python3 refresh_breakoutscanner.py
"""

import json
import os
import sys

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import aperture_policy as _ap
except ImportError:  # policy ledger is part of this surface
    _ap = None

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.expanduser("~/workspace/morgue/output")
CARD_PATH = os.path.join(SOURCE_DIR, "board_card.json")
FULL_PATH = os.path.join(SOURCE_DIR, "board_full.json")
BARS_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")
CHART_PATH = os.path.join(HERE, "ai-chart-read", "data.json")
OUT_PATH = os.path.join(HERE, "breakout-scanner", "data.json")

SOURCE_WORDS = ("Daily closing prices from the consolidated tape "
                "records for the stocks in the daily scoring "
                "run, over the price history on record")

PROVING_STATE = "Still being proven"
PROVING_NOTE = ("Still being proven: no graded record exists of "
                "what prices did after a name appeared on this "
                "list, so the page describes past prices only "
                "and makes no claim about what follows a name "
                "appearing here.")

HIGH_WINDOW = 252
TIGHT_WINDOW = 10
RISE_STEPS = 21


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Breakout Scanner refresh: {message}", file=sys.stderr)
    return 1


def build():
    for path in (CARD_PATH, FULL_PATH, BARS_PATH, CHART_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    card = load_json(CARD_PATH)
    full = load_json(FULL_PATH)
    bars = load_json(BARS_PATH)
    chart = load_json(CHART_PATH)

    summary = card["summary"]
    run_session = summary["as_of_session"]
    if full.get("as_of_session") != run_session:
        return fail(f"the full scored list is for "
                    f"{full.get('as_of_session')} but the board "
                    f"card is for {run_session}; refusing to "
                    "publish a mismatched page.")

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
            return fail(f"the card summary says {key}="
                        f"{summary.get(key)} but the full list "
                        f"holds {value}; refusing to publish a "
                        "mismatched page.")

    scored_names = {r["symbol"] for r in scored}
    short_names = {r["symbol"] for r in short}
    bar_names = set(bars)
    if bar_names != scored_names:
        return fail(f"the price history holds {len(bar_names)} "
                    f"stocks but the scored run scored "
                    f"{len(scored_names)}; refusing to publish "
                    "a mismatched page.")
    if bar_names & short_names:
        return fail("the price history holds stocks the scored "
                    "run set aside for too little data; refusing "
                    "to publish.")
    if not bars:
        return fail("the price history is empty; refusing to "
                    "publish.")

    calendar = sorted({row[0] for stock_rows in bars.values()
                       for row in stock_rows})
    if not calendar:
        return fail("the price history holds no dated bars; "
                    "refusing to publish.")
    cal_pos = {d: i for i, d in enumerate(calendar)}

    # The AI Chart Read's published file must describe the same
    # history: same calendar, same names, same closes.
    if chart.get("dates") != calendar:
        return fail("the AI Chart Read's published calendar "
                    "disagrees with the price history; refusing "
                    "to publish a mismatched page.")
    chart_bars = chart.get("bars") or {}
    if set(chart_bars) != bar_names:
        return fail("the AI Chart Read's published names "
                    "disagree with the price history; refusing "
                    "to publish a mismatched page.")

    shipped = {}
    for symbol in sorted(bars):
        dates = []
        closes = []
        prev = None
        for row in bars[symbol]:
            date = row[0]
            high, low, close = row[2], row[3], row[4]
            if prev is not None and date <= prev:
                return fail(f"{symbol} has a repeated or "
                            f"out-of-order session {date}; "
                            "refusing to publish.")
            for value in (high, low, close):
                if not isinstance(value, (int, float)):
                    return fail(f"{symbol} has a price that is "
                                f"not a number on {date}; "
                                "refusing to publish.")
            if high < low:
                return fail(f"{symbol} has a high below its "
                            f"low on {date}; refusing to publish.")
            prev = date
            dates.append(date)
            closes.append(float(close))
        idx = [cal_pos[d] for d in dates]
        if idx != list(range(idx[0], idx[0] + len(idx))):
            return fail(f"{symbol}'s sessions are not a "
                        "continuous run of the shared calendar; "
                        "refusing to publish.")
        entry = chart_bars[symbol]
        if entry[0] != idx[0] or \
                [float(c) for c in entry[1]] != closes:
            return fail(f"{symbol}'s closes disagree with the "
                        "AI Chart Read's published closes; "
                        "refusing to publish a mismatched page.")
        shipped[symbol] = [idx[0], closes]

    full_high = sum(1 for s in shipped.values()
                    if len(s[1]) >= HIGH_WINDOW)
    short_high = len(shipped) - full_high
    tight_ok = sum(1 for s in shipped.values()
                   if len(s[1]) >= TIGHT_WINDOW)
    rise_ok = sum(1 for s in shipped.values()
                  if len(s[1]) >= RISE_STEPS + 1)
    ended_early = sum(
        1 for s in shipped.values()
        if s[0] + len(s[1]) - 1 != len(calendar) - 1)
    if tight_ok != len(shipped) or rise_ok != len(shipped):
        return fail("the counted window support for the "
                    "tightness or rise measure disagrees with "
                    "the published counts; refusing to publish.")

    # APERTURE-POLICY-20261029 (DEEP-PASS 3.2 item 1): names the
    # scored run set aside for too little data are ledgered per
    # name with their exclusion reason, never only counted.
    if _ap is None:
        return fail("the candidate policy module was not found; "
                    "refusing to publish exclusions without "
                    "their ledger.")
    exclusions = [_ap.exclusion_record(r["symbol"],
                                       ["insufficient_data"])
                  for r in sorted(short, key=lambda r: r["symbol"])]

    data = {
        "tool": "Breakout Scanner",
        "exclusions": exclusions,
        "state": "published",
        "proving_state": PROVING_STATE,
        "proving_note": PROVING_NOTE,
        "source": SOURCE_WORDS,
        "session": calendar[-1],
        "history_from": calendar[0],
        "history_to": calendar[-1],
        "history_sessions": len(calendar),
        "names_on_record": len(shipped),
        "scored_run_session": run_session,
        "high_window": HIGH_WINDOW,
        "tight_window": TIGHT_WINDOW,
        "rise_steps": RISE_STEPS,
        "names_full_high_window": full_high,
        "names_short_high_window": short_high,
        "names_ended_early": ended_early,
        "coverage": (
            f"Worked out in your browser from the daily closing "
            f"prices on record for the {len(shipped):,} stocks "
            f"in the daily scoring run, {len(calendar)} trading "
            f"days from {calendar[0]} to {calendar[-1]}. "
            f"{full_high:,} names carry the full "
            f"{HIGH_WINDOW} sessions behind the high; "
            f"{short_high} names have fewer sessions on record, "
            f"so their high is taken over the sessions they do "
            f"have and their row names that window. "
            f"{ended_early} names stopped trading before "
            f"{calendar[-1]}; their figures are dated to their "
            f"own last session."),
        "dates": calendar,
        "bars": shipped,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, separators=(",", ":"), sort_keys=True)
        fh.write("\n")
    size = os.path.getsize(OUT_PATH)
    print(f"Wrote {OUT_PATH} ({size:,} bytes, "
          f"{len(shipped):,} names, {len(calendar)} sessions "
          f"{calendar[0]} to {calendar[-1]}, {full_high:,} with "
          f"the full {HIGH_WINDOW}-session window, "
          f"{short_high} with a shorter one, {ended_early} "
          f"ended early)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
