#!/usr/bin/env python3
"""Refresh the Unusual Volume data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: the real daily share-volume history behind the
daily scoring run: one daily bar per stock per session, each bar
carrying that session's share volume, 399 sessions from March 25,
2025 to October 23, 2026 for the 1,833 scored stocks. The bars on
record are the consolidated-tape (SIP) daily bars the scoring
run's own bar fetch pulls (daily bars, split-adjusted, completed
sessions only); that fetch is the only route by which this history
was written, and this refresh re-checks the fetch's declared feed
before trusting a single volume (see the provenance gate below).
The history is cross-checked against the scored run's two
published carriers (its summary card and its full scored list),
which must agree with each other and with the history's name set.

Reconstruction choices (the exact construction):
- The session measured is the freshest session in the volume
  history on record (October 23, 2026 on the current history).
- A name's usual level is the average of its share volume over
  its own previous 20 trading days (the 20 bars before the
  measured session in that name's own record), rounded to the
  nearest whole share. The baseline window is 20 sessions long;
  on the history's calendar those 20 sessions run September 25,
  2026 to October 22, 2026 for a name that traded every day.
- The multiple (the ratio printed for a name) is the measured
  session's share volume divided by that rounded usual level,
  shown to two decimal places, so every printed multiple can be
  recomputed exactly from the two printed volumes beside it.
- The floor for publishing a name: its unrounded ratio reaches
  2.00, twice its own usual level (a name at 1.997 does not pass
  merely because its printed multiple would round to 2.00).
  Every name at or above the floor is
  published, ranked by the multiple, highest first; ties break
  by the measured volume, then by the ticker letters.
- Thin-cell rule: this page prints no percentage anywhere. Its
  counts (names measured, names published) are printed as counts
  with their denominators, and each name's figures are its own
  measurements, not shares of a small cell.

Non-claims: this tool does not use any hourly volume and does not
use any daily volume whose source is not the consolidated tape;
a name whose only volume on record came from another source would
show no figure here. It says nothing about why a name's volume
ran high, and nothing about what its price did. The options
prints kept elsewhere on this site are not share volume and are
never used here.

Fail-closed rules:
- Provenance gate: the bar fetch that wrote this history must
  still declare the consolidated tape feed for daily bars in its
  own code, and the history's loader must still route through
  that fetch. If either check fails, the volumes' provenance is
  not proven and the refresh stops, publishing nothing.
- If the scored run's summary card and its full list disagree
  with each other (checked, scored, too little data, passed
  every check, or the session), or the history's name set differs
  from the scored set in either direction, the refresh stops.
- If any bar carries a volume that is missing, not a number, or
  negative; if a name's sessions repeat or run out of order; if
  a name measured on the freshest session has fewer than 20
  earlier bars or a usual level of zero, the refresh stops
  rather than publish a figure it cannot stand behind. (A name
  that simply did not trade on the measured session is not an
  error: it is counted as not measured and shows nothing.)

Honesty rules:
- Dates are read off the sources, never from the clock: the
  measured session and the history's span come from the bars
  themselves, so running this script twice produces the same
  file, byte for byte.
- Absence is not zero: a name that did not trade on the measured
  session, or that falls under the floor, shows no figure.

Usage: python3 refresh_unusualvolume.py
"""

import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MORGUE = os.path.expanduser("~/workspace/morgue")
CARD_PATH = os.path.join(MORGUE, "output", "board_card.json")
FULL_PATH = os.path.join(MORGUE, "output", "board_full.json")
BARS_PATH = os.path.join(MORGUE, "data_cache", "board_bt_bars.json")
FETCH_PATH = os.path.join(MORGUE, "board_card.py")
LOADER_PATH = os.path.join(MORGUE, "board_backtest.py")
OUT_PATH = os.path.join(HERE, "unusual-volume", "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

BASELINE_SESSIONS = 20
FLOOR_MULTIPLE = 2.0

SOURCE_WORDS = ("Daily share volume from the consolidated tape "
                "records (the official record of trades on every "
                "exchange) for the stocks in the daily scoring run")

DEFINITIONS = {
    "construction": (
        "For the measured session, each name's share volume is "
        "compared with that same name's own usual level: the "
        "average of its share volume over its previous 20 "
        "trading days. The multiple printed beside a name is its "
        "volume for the measured session divided by that usual "
        "level."),
    "floor": (
        "A name is listed only when its volume for the measured "
        "session reached at least twice its own usual level "
        "(a multiple of 2.00 or more). Every name that reaches "
        "the floor is listed, ranked by the multiple, highest "
        "first."),
    "universe": (
        "The names measured are the stocks in the daily scoring "
        "run, which are stocks listed today, so stocks that "
        "stopped trading earlier are not in it. A name that did "
        "not trade on the measured session is not measured and "
        "shows nothing."),
    "volume_source": (
        "Every volume on this page comes from the consolidated "
        "tape records. No other volume source is used, and a "
        "name with no consolidated-tape volume on record would "
        "show no figure."),
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Unusual Volume refresh: {message}", file=sys.stderr)
    return 1


def build():
    for path in (CARD_PATH, FULL_PATH, BARS_PATH, FETCH_PATH,
                 LOADER_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    # --- Provenance gate: the volumes in this history were
    # written by one route only: the history's loader calls the
    # scoring run's own bar fetch, and that fetch declares the
    # consolidated tape (SIP) feed for daily bars. If either
    # link in that chain no longer reads that way, the volumes'
    # provenance is unproven and nothing is published. ---
    with open(FETCH_PATH, "r", encoding="utf-8") as fh:
        fetch_src = fh.read()
    with open(LOADER_PATH, "r", encoding="utf-8") as fh:
        loader_src = fh.read()
    if '"feed": "sip"' not in fetch_src \
            or '"timeframe": "1Day"' not in fetch_src:
        return fail("the bar fetch behind this volume history no "
                    "longer declares the consolidated tape feed "
                    "for daily bars; the volumes' provenance is "
                    "not proven, refusing to publish.")
    if "bc.fetch_bars" not in loader_src:
        return fail("the volume history's loader no longer "
                    "routes through the scoring run's bar fetch; "
                    "the volumes' provenance is not proven, "
                    "refusing to publish.")

    card = load_json(CARD_PATH)
    full = load_json(FULL_PATH)
    bars = load_json(BARS_PATH)

    # --- The scored run's two carriers must agree with each
    # other, and the history must hold exactly the scored names.
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
    bar_names = set(bars)
    if bar_names != scored_names:
        return fail(f"the volume history holds {len(bar_names)} "
                    f"stocks but the scored run scored "
                    f"{len(scored_names)}; the names differ "
                    f"(history only: "
                    f"{sorted(bar_names - scored_names)[:5]}, "
                    f"run only: "
                    f"{sorted(scored_names - bar_names)[:5]}); "
                    "refusing to publish a mismatched page.")
    if not bars:
        return fail("the volume history is empty; refusing to "
                    "publish.")

    # --- Per-name volume series, dates strictly increasing,
    # every volume a non-negative number. ---
    series = {}
    calendar = set()
    for symbol, stock_rows in bars.items():
        dates = []
        volumes = []
        prev = None
        for row in stock_rows:
            if len(row) != 6:
                return fail(f"{symbol} has a bar that is not a "
                            "dated open, high, low, close and "
                            "volume; refusing to publish.")
            date, volume = row[0], row[5]
            if prev is not None and date <= prev:
                return fail(f"{symbol} has a repeated or "
                            f"out-of-order session {date}; "
                            "refusing to publish.")
            if not isinstance(volume, (int, float)) \
                    or isinstance(volume, bool):
                return fail(f"{symbol} has a share volume that "
                            f"is not a number on {date}; refusing "
                            "to publish.")
            if volume < 0:
                return fail(f"{symbol} has a negative share "
                            f"volume on {date}; refusing to "
                            "publish.")
            prev = date
            dates.append(date)
            volumes.append(volume)
            calendar.add(date)
        series[symbol] = (dates, volumes)
    if not calendar:
        return fail("the volume history holds no dated bars; "
                    "refusing to publish.")
    calendar = sorted(calendar)
    measured = calendar[-1]
    if len(calendar) <= BASELINE_SESSIONS:
        return fail("the volume history holds no more sessions "
                    "than the baseline window; refusing to "
                    "publish.")
    baseline_calendar = calendar[-BASELINE_SESSIONS - 1:-1]

    # --- Measure every name that traded on the measured
    # session against its own previous 20 trading days. ---
    names = []
    measured_count = 0
    not_traded = 0
    for symbol in sorted(series):
        dates, volumes = series[symbol]
        if dates[-1] != measured:
            not_traded += 1
            continue
        measured_count += 1
        if len(volumes) < BASELINE_SESSIONS + 1:
            return fail(f"{symbol} traded on {measured} but has "
                        f"only {len(volumes) - 1} earlier bars, "
                        f"fewer than the {BASELINE_SESSIONS} the "
                        "baseline needs; refusing to publish.")
        usual = round(statistics.mean(volumes[-BASELINE_SESSIONS - 1:-1]))
        if usual <= 0:
            return fail(f"{symbol} has a usual level of zero "
                        f"over its previous {BASELINE_SESSIONS} "
                        "trading days; refusing to publish a "
                        "multiple against zero.")
        ratio = volumes[-1] / usual
        if ratio >= FLOOR_MULTIPLE:
            names.append({
                "symbol": symbol,
                "volume": volumes[-1],
                "usual_volume": usual,
                "multiple": round(ratio, 2),
                "baseline_sessions": BASELINE_SESSIONS,
            })
    names.sort(key=lambda n: (-n["multiple"], -n["volume"],
                              n["symbol"]))
    if measured_count == 0:
        return fail(f"no name traded on the freshest session "
                    f"{measured}; refusing to publish an empty "
                    "measurement.")

    coverage = (
        f"{measured_count:,} of the {len(scored_names):,} stocks "
        f"in the daily scoring run traded on {measured} and were "
        f"measured against their own previous "
        f"{BASELINE_SESSIONS} trading days; {not_traded} did not "
        f"trade that day and show nothing; {len(names)} reached "
        f"at least twice their own usual level")

    data = {
        "tool": "Unusual Volume",
        "state": "published",
        "session": measured,
        "scored_run_session": run_session,
        "source": SOURCE_WORDS,
        "history_sessions_on_record": len(calendar),
        "history_from": calendar[0],
        "history_to": measured,
        "baseline_sessions": BASELINE_SESSIONS,
        "baseline_from": baseline_calendar[0],
        "baseline_to": baseline_calendar[-1],
        "floor_multiple": FLOOR_MULTIPLE,
        "names": names,
        "definitions": DEFINITIONS,
        "coverage": coverage,
        "receipt": {
            "session": measured,
            "source": SOURCE_WORDS,
            "coverage": coverage,
        },
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (session {measured}, "
          f"{len(names)} names at or above "
          f"{FLOOR_MULTIPLE:.2f}x of {measured_count:,} measured)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
