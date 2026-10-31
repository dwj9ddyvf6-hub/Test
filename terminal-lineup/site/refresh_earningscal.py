#!/usr/bin/env python3
"""Refresh the Earnings Calendar data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: two committed records of scheduled earnings report
dates, both stamped as recorded at the same moment
(2026-10-12T21:57:32Z). The dates in them were gathered from the
published earnings calendar and then checked name by name against
several earnings trackers and company announcements, with the
checked result kept wherever the sources disagreed. The two records
cover overlapping sets of names; every name carried by both must
carry the identical date in both, or this refresh stops and
publishes nothing. A future earnings date is a scheduled fact and
is published only from these records, which actually carry
scheduled dates. Past report dates from company filings are a
different record entirely (they live on the Earnings Drift Pane)
and are never used here.

Reconstruction choices (stated as this build's own choices):
  - The published list is the union of the two records' dated
    names. A name recorded with no date (a confirmed "no date
    scheduled" entry) is not a scheduled report and is left out,
    and counted in the receipt.
  - This file carries every dated name on record, past ones
    included, and the reader's screen shows only the names dated
    today or later in New York, in date order. That keeps this
    refresh identical whenever it is run on the same records:
    dates here come from the records, never from the clock. The
    only timestamps published are the records' own recorded time.
  - Freshness is judged on the screen against the records' own
    rule: a list more than 8 days old is out of date, and the page
    says so in a banner naming the day the list was recorded.
  - Expected moves: the priced move record
    (earnings-record/priced_moves.json, built by priced_moves.py
    from stored at the money straddle quotes) is the only source.
    A name is published with a move only when that record carries
    the name with the same report date as the calendar record;
    every other name is published with its expected move marked
    not on record, and the page says that plainly for each name.
    No move is estimated from anything else. (Before 2026-10-30
    no such record existed and every name published null.)

Non-claims: this build does not claim the list covers every
company that will report, only the names the two records carry.
It does not present any past report date as an upcoming one, and
it adds no date that is not in the records on file.

Fail-closed rules: either record missing or unreadable; either
record not a plain name-to-date list; the two records stamped
with different recorded times, or a recorded time that cannot be
read; a value that is neither empty nor a readable date; or any
name carried by both records with two different dates. Any of
these stops the refresh and publishes nothing.

Usage: python3 refresh_earningscal.py
"""

import json
import os
import sys
from datetime import date

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(os.path.dirname(HERE))
RECORD_PATHS = [
    os.path.join(WORKSPACE, "alpaca-swing-desk", "desk",
                 "earnings.json"),
    os.path.join(WORKSPACE, "alpaca-swing-desk", "desk",
                 "phase_earnings.json"),
]
OUT_PATH = os.path.join(HERE, "earnings-calendar", "data.json")
FRESH_RECORD_PATH = os.path.join(HERE, "earnings-calendar", "record.json")
FRESH_SOURCE_WORDS = ("Scheduled report dates re-checked against "
                      "the Nasdaq public earnings calendar, one "
                      "published file per day, for every name the "
                      "earlier records carried")

SOURCE_WORDS = ("Scheduled report dates gathered from the published "
                "earnings calendar and checked name by name against "
                "several earnings trackers and company announcements")

MOVE_NOTE = ("No priced expected move is on record for any of these "
             "names, so none is shown. A move is only ever shown "
             "here when a record carries one, priced by the options "
             "market.")
MOVE_NOTE_PRICED = ("A priced expected move is shown for every name "
                    "the priced move record covers, priced from "
                    "stored at the money straddle quotes. Names the "
                    "record does not cover are marked not on record.")
PRICED_MOVES_PATH = os.path.join(HERE, "earnings-record",
                                 "priced_moves.json")
REALISED_PATH = os.path.join(HERE, "earnings-calendar",
                             "realised_moves.json")
EARNINGS_RECORD_PATH = os.path.join(HERE, "earnings-record",
                                    "record.json")
PANEL_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/deep_bars.json")
REALISED_SOURCE_WORDS = (
    "Realised moves computed from the price history on record in "
    "this lane (the DEEP panel): the close of the first session on "
    "or after the report date against the close just before it. "
    "A name enters this record only when a calendar record this "
    "lane holds carries its report date in the past, and, for the "
    "seeded rows, the lane's earnings record confirms the report "
    "with a reported figure on the same date. An expected move is "
    "carried only where the priced move record priced that name "
    "before it reported; otherwise none is shown.")


def _realised_move(closes, day):
    dates = sorted(closes)
    sess = [d for d in dates if d >= day]
    prior = [d for d in dates if d < day]
    if not sess or not prior or not closes[prior[-1]]:
        return None
    return {"realised_move_pct": round(
                (closes[sess[0]] / closes[prior[-1]] - 1) * 100, 4),
            "session_date": sess[0]}


def build_realised(names, recorded_on, priced):
    """The realised record (cure 2026-10-31), kept in an accrual
    store so a name's expected move, priced before it reported,
    survives the calendar rotating forward. Rows are append-only:
    a row once computed is never recomputed or overwritten.
    Returns the full row list for the page, or None via fail()."""
    candidates = {}
    for n in names or []:
        if n["date"] < recorded_on and n.get("expected_move"):
            try:
                exp = float(str(n["expected_move"]).rstrip("%"))
            except ValueError:
                exp = None
            candidates[(n["symbol"], n["date"])] = exp
    for sym, entry in (priced or {}).items():
        day = entry.get("report_date")
        pct = entry.get("priced_move_pct")
        if isinstance(day, str) and day < recorded_on and \
                isinstance(pct, (int, float)) and \
                not isinstance(pct, bool):
            candidates.setdefault((sym, day), float(pct))
    # Seeded past reports: the lane's earnings record confirms the
    # report (a reported figure on that date) and a legacy calendar
    # record this producer already reads carries the same date.
    try:
        legacy = {}
        for path in RECORD_PATHS:
            doc, err = load_record(path)
            if err:
                raise ValueError(err)
            for name, value in doc.items():
                if name != "updated_ts" and value:
                    legacy.setdefault(name, set()).add(value)
        erec = load_json(EARNINGS_RECORD_PATH)
        for sym, entry in (erec.get("names") or {}).items():
            for rep in entry.get("reports") or []:
                day = rep.get("report_date")
                if isinstance(day, str) and day < recorded_on and \
                        rep.get("eps_actual") is not None and \
                        day in legacy.get(sym, set()):
                    candidates.setdefault((sym, day), None)
    except (OSError, ValueError) as exc:
        return fail(f"the realised record's seed records could "
                    f"not be read: {exc}")
    store = {"source": REALISED_SOURCE_WORDS, "rows": []}
    if os.path.exists(REALISED_PATH):
        try:
            store = load_json(REALISED_PATH)
        except (OSError, ValueError) as exc:
            return fail(f"the realised move record could not be "
                        f"read: {exc}")
    have = {(r["symbol"], r["report_date"]) for r in store["rows"]}
    missing = [k for k in sorted(candidates) if k not in have]
    if missing:
        sys.path.insert(0, HERE)
        from deep_panel_reader import DeepPanelReader
        reader = DeepPanelReader(PANEL_PATH, log=False)
        cache = {}
        for sym, day in missing:
            if sym not in cache:
                cache[sym] = ({row[0]: row[4] for row in reader[sym]}
                              if sym in reader else {})
            got = _realised_move(cache[sym], day)
            if got is None:
                continue
            store["rows"].append({
                "symbol": sym, "report_date": day,
                "expected_move_pct": candidates[(sym, day)],
                **got})
    store["rows"].sort(key=lambda r: (r["report_date"], r["symbol"]))
    tmp = REALISED_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(store, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, REALISED_PATH)
    return store["rows"]


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_priced_moves():
    """The priced move record (priced_moves.py). Returns a dict of
    symbol to its record entry. A missing record is the pre-lane
    state and yields an empty dict; an unreadable or malformed
    record fails closed, like every other record here."""
    if not os.path.exists(PRICED_MOVES_PATH):
        return {}, None
    try:
        with open(PRICED_MOVES_PATH, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        return None, f"the priced move record could not be read: {exc}"
    names = doc.get("names") if isinstance(doc, dict) else None
    if not isinstance(names, dict):
        return None, "the priced move record carries no name list"
    return names, None


def priced_move_for(priced, symbol, report_date):
    """The published expected move string for one dated name, or
    None. A move is published only when the priced record carries
    the same name with the same report date and a numeric priced
    move; any disagreement publishes nothing for that name."""
    entry = priced.get(symbol)
    if not isinstance(entry, dict):
        return None
    if entry.get("report_date") != report_date:
        return None
    pct = entry.get("priced_move_pct")
    if not isinstance(pct, (int, float)) or isinstance(pct, bool):
        return None
    return f"{pct:.1f}%"


def fail(message):
    print(f"Earnings Calendar refresh: {message}", file=sys.stderr)
    return None


def load_record(path):
    if not os.path.exists(path):
        return None, f"a record of scheduled dates was not found: {path}"
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        return None, f"a record of scheduled dates could not be read: {exc}"
    if not isinstance(doc, dict):
        return None, "a record of scheduled dates is not a name list"
    return doc, None


def build_fresh():
    """The re-checked record written by fetch_earnings_calendar.py
    (2026-10-29 cure): one dated record, restamped on every fetch.
    Returns the published doc, or None via fail() when the record
    is malformed. A name recorded null has no date scheduled
    inside the checked window and is counted, not dated."""
    try:
        with open(FRESH_RECORD_PATH, encoding="utf-8") as fh:
            rec = json.load(fh)
    except (OSError, ValueError) as exc:
        return fail(f"the re-checked earnings record could not be "
                    f"read: {exc}")
    stamp = rec.get("updated_ts")
    if not isinstance(stamp, str) or not stamp.endswith("Z") \
            or "T" not in stamp:
        return fail("the re-checked record carries no readable "
                    "recorded time")
    try:
        date.fromisoformat(stamp[:10])
    except ValueError:
        return fail("the re-checked record carries an unreadable "
                    "recorded time")
    entries = rec.get("entries")
    if not isinstance(entries, dict) or not entries:
        return fail("the re-checked record carries no name list")
    priced, perr = load_priced_moves()
    if perr:
        return fail(perr)
    names, no_date = [], 0
    for name, value in sorted(entries.items()):
        if value is None:
            no_date += 1
            continue
        if not isinstance(value, str):
            return fail(f"the re-checked record for {name} is "
                        "neither empty nor a date")
        try:
            date.fromisoformat(value)
        except ValueError:
            return fail(f"the re-checked record for {name} carries "
                        f"an unreadable date: {value!r}")
        names.append({"symbol": name, "date": value,
                      "expected_move": priced_move_for(
                          priced, name, value)})
    names.sort(key=lambda n: (n["date"], n["symbol"]))
    if not names:
        return fail("the re-checked record carries no dated names "
                    "in its window")
    priced_count = sum(1 for n in names
                       if n["expected_move"] is not None)
    realised = build_realised(names, stamp[:10], priced)
    if realised is None:
        return None
    return {
        "tool": "Earnings Calendar",
        "realised_moves": realised,
        "realised_count": len(realised),
        "source": FRESH_SOURCE_WORDS,
        "recorded_at": stamp,
        "recorded_on": stamp[:10],
        "names_on_record": len(entries),
        "dated_names": len(names),
        "names_with_no_date": no_date,
        "shared_names_checked": 0,
        "window_start": rec.get("window_start"),
        "window_days": rec.get("window_days"),
        "move_note": MOVE_NOTE_PRICED if priced_count else MOVE_NOTE,
        "priced_moves_on_record": priced_count,
        "names": names,
    }


def build():
    if os.path.exists(FRESH_RECORD_PATH):
        return build_fresh()
    priced, perr = load_priced_moves()
    if perr:
        return fail(perr)
    records = []
    stamps = []
    for path in RECORD_PATHS:
        doc, err = load_record(path)
        if err:
            return fail(err)
        stamp = doc.get("updated_ts")
        if not isinstance(stamp, str) or not stamp.endswith("Z") \
                or "T" not in stamp:
            return fail("a record carries no readable recorded time")
        try:
            date.fromisoformat(stamp[:10])
        except ValueError:
            return fail("a record carries an unreadable recorded time")
        stamps.append(stamp)
        entries = {}
        for name, value in doc.items():
            if name == "updated_ts":
                continue
            if value is not None:
                if not isinstance(value, str):
                    return fail(f"the record for {name} is neither "
                                f"empty nor a date")
                try:
                    date.fromisoformat(value)
                except ValueError:
                    return fail(f"the record for {name} carries an "
                                f"unreadable date: {value!r}")
            entries[name] = value
        records.append(entries)
    if len(set(stamps)) != 1:
        return fail("the two records were not recorded at the same "
                    "time, so they cannot be checked against each "
                    "other")
    recorded_at = stamps[0]

    merged = {}
    shared = 0
    for entries in records:
        for name, value in entries.items():
            if name in merged:
                shared += 1
                if merged[name] != value:
                    return fail(f"the two records disagree on {name}: "
                                f"{merged[name]!r} vs {value!r}")
            else:
                merged[name] = value

    names = []
    no_date = 0
    for name, value in sorted(merged.items()):
        if value is None:
            no_date += 1
            continue
        names.append({
            "symbol": name,
            "date": value,
            "expected_move": priced_move_for(priced, name, value),
        })
    names.sort(key=lambda n: (n["date"], n["symbol"]))
    if not names:
        return fail("the records carry no dated names at all")
    priced_count = sum(1 for n in names
                       if n["expected_move"] is not None)
    realised = build_realised(names, recorded_at[:10], priced)
    if realised is None:
        return None

    return {
        "tool": "Earnings Calendar",
        "realised_moves": realised,
        "realised_count": len(realised),
        "source": SOURCE_WORDS,
        "recorded_at": recorded_at,
        "recorded_on": recorded_at[:10],
        "names_on_record": len(merged),
        "dated_names": len(names),
        "names_with_no_date": no_date,
        "shared_names_checked": shared,
        "move_note": MOVE_NOTE_PRICED if priced_count else MOVE_NOTE,
        "priced_moves_on_record": priced_count,
        "names": names,
    }


def main():
    doc = build()
    if doc is None:
        return 1
    doc = _tc.stamp_for_script(doc, __file__) if _tc is not None else doc
    text = json.dumps(doc, indent=2, sort_keys=True) + "\n"
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, OUT_PATH)
    print(f"Earnings Calendar refresh: wrote {OUT_PATH} "
          f"({doc['dated_names']} dated names, "
          f"{doc['names_with_no_date']} with no date scheduled, "
          f"{doc['shared_names_checked']} names checked in both "
          f"records, {doc.get('priced_moves_on_record', 0)} priced "
          f"moves published, recorded {doc['recorded_at']})")
    # Self-enrich tail (cure 2026-10-31, same pattern as the tails in
    # refresh_regime.py and refresh_flowengine.py, in enrich_all.py's
    # order: record surface first, explanation second, because the
    # explanation body reads the record surface). This page has a
    # standalone recheck path that runs this refresher bare, with no
    # lane close after it; without this tail a bare run strips both
    # blocks and the page publishes with no explanation. A failure is
    # printed and named, never silent.
    try:
        import explanation as _ex
        import record_surface as _rs
        _rs.enrich_slug("earnings-calendar")
        _ex.enrich_slug("earnings-calendar")
    except Exception as _exc:
        print(f"self-enrich failed: {_exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
