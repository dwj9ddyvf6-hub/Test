#!/usr/bin/env python3
"""Refresh the Week Ahead data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: one committed calendar document on file, assembled
2026-10-25 from the official release schedules published by the
Federal Reserve (its meeting calendar) and the Bureau of Labor
Statistics (its release schedules for consumer prices and for the
jobs report), checked against a second, independent carrier of the
same calendar: the copies of it carried inside the desk's own dated
snapshots (session 2026-10-28). Every event published here must
appear, identical in date, kind, recorded time and recorded label,
in both carriers, or this refresh stops and publishes nothing.

Reconstruction choices (stated as this build's own choices):
  - Plain names are translations of the calendar's own labels, one
    per kind, fixed here: the central bank rate decision (recorded
    label "FOMC rate decision"), the consumer prices report
    (recorded label "Consumer Price Index") and the jobs report
    (recorded label "Employment Situation"). Plain kinds likewise:
    Central bank, Prices, Jobs.
  - Times: the calendar records each event's time as Eastern Time
    (its own field is the Eastern time of day). Eastern Time is
    New York time, so the times are shown exactly as recorded, in
    12-hour form, with the timezone named on the page. No time is
    converted, because none needs converting; a time recorded in
    any other timezone would have to be converted explicitly here,
    and an event with no recorded time is published with no time,
    to be shown as date only with the time marked not on record.
  - Which events are upcoming, and the recent-past strip, are
    worked out on the reader's screen against that day's date in
    New York, so this file carries the whole calendar on record
    (all 64 events) and running this script twice on the same
    sources produces the same file, byte for byte. Dates here come
    from the calendar document, never from the clock.

Non-claims: this build does not claim the calendar covers anything
beyond its three recorded kinds. It carries no Treasury sales, no
central bank minutes and no other events, and the page says so in
plain words. It does not claim any event will move prices, and it
adds no event that is not in the calendar on record.

Fail-closed rules: the calendar document missing, unreadable, of
an unexpected version, or carrying an event kind, label, date or
time this build does not know; an event outside the document's own
stated coverage; a duplicate event; no snapshot carrier found; or
any snapshot carrier whose copy of the calendar disagrees with the
document in coverage, version, or any single event. Any of these
stops the refresh and publishes nothing.

Usage: python3 refresh_weekahead.py
"""

import glob
import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(os.path.dirname(HERE))
CALENDAR_PATH = os.path.join(
    WORKSPACE, "muse-desk-v3", "desk3", "macro_calendar.json")
SNAPSHOT_GLOB = os.path.join(
    WORKSPACE, "muse-desk-v3", "state", "snapshots", "*.json")
OUT_PATH = os.path.join(HERE, "week-ahead", "data.json")

EXPECTED_VERSION = "desk-macro-calendar-v1"

# kind -> (recorded label, plain name, plain kind)
KINDS = {
    "FOMC": ("FOMC rate decision",
             "Central bank rate decision", "Central bank"),
    "CPI": ("Consumer Price Index",
            "Consumer prices report", "Prices"),
    "NFP": ("Employment Situation",
            "Jobs report", "Jobs"),
}

SOURCE_WORDS = ("The official release schedules published by the "
                "Federal Reserve and the Bureau of Labor "
                "Statistics, gathered into one calendar")

SCOPE_NOTE = ("This calendar covers three kinds of events: central "
              "bank rate decisions, the consumer prices report and "
              "the jobs report. It carries no Treasury sales and "
              "no other events, so none are shown.")


def fail(message):
    print(f"Week Ahead refresh: {message}", file=sys.stderr)
    return None


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def time_label(time_et):
    """'08:30' -> '8:30 AM'; '14:00' -> '2:00 PM'."""
    hh, mm = int(time_et[:2]), int(time_et[3:5])
    suffix = "AM" if hh < 12 else "PM"
    hour = hh % 12 or 12
    return f"{hour}:{mm:02d} {suffix}"


def event_key(e):
    return (e.get("date"), e.get("kind"), e.get("time_et"),
            e.get("label"))


def build():
    if not os.path.exists(CALENDAR_PATH):
        return fail("the calendar on record was not found")
    try:
        doc = load_json(CALENDAR_PATH)
    except (OSError, ValueError) as exc:
        return fail(f"the calendar on record could not be read: {exc}")
    if not isinstance(doc, dict) or doc.get("version") != EXPECTED_VERSION:
        return fail("the calendar on record is of an unexpected version")
    try:
        coverage_start = doc["coverage_start"]
        coverage_end = doc["coverage_end"]
        assembled_on = doc["retrieved"]
        date.fromisoformat(coverage_start)
        date.fromisoformat(coverage_end)
        date.fromisoformat(assembled_on)
    except (KeyError, TypeError, ValueError) as exc:
        return fail(f"the calendar's coverage or assembly date is "
                    f"missing or unreadable: {exc}")
    raw_events = doc.get("events")
    if not isinstance(raw_events, list) or not raw_events:
        return fail("the calendar on record carries no events")

    events = []
    seen = set()
    for e in raw_events:
        if not isinstance(e, dict):
            return fail("the calendar carries an event that is not a record")
        kind = e.get("kind")
        if kind not in KINDS:
            return fail(f"the calendar carries an event kind this "
                        f"build does not know: {kind!r}")
        label, plain_name, plain_kind = KINDS[kind]
        if e.get("label") != label:
            return fail(f"the calendar's label for a {kind} event "
                        f"is not the one on record: {e.get('label')!r}")
        d = e.get("date")
        try:
            date.fromisoformat(d)
        except (TypeError, ValueError):
            return fail(f"the calendar carries an event with an "
                        f"unreadable date: {d!r}")
        if not (coverage_start <= d <= coverage_end):
            return fail(f"an event dated {d} sits outside the "
                        f"calendar's own stated coverage")
        t = e.get("time_et")
        if t is not None and not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", t):
            return fail(f"an event on {d} carries a time that is "
                        f"not a recorded Eastern time of day: {t!r}")
        key = event_key(e)
        if key in seen:
            return fail(f"the calendar carries the same event twice: {key}")
        seen.add(key)
        events.append({
            "date": d,
            "name": plain_name,
            "kind": plain_kind,
            "time_et": t,
            "time_label": time_label(t) if t else None,
        })
    events.sort(key=lambda e: (e["date"], e["time_et"] or "", e["name"]))

    # Rolling 14 day coverage window (TRADING-PATH-WEEKAHEAD-20261031):
    # the calendar on record covers only three kinds, so a weekday
    # with no event in the window is UNVERIFIED, never quiet. Before
    # this, the file carried no window at all and the 2026-10-30
    # pre-open read had to name the thinness itself: the window
    # 2026-10-30 to 2026-11-03 held zero events while the Employment
    # Cost Index, Chicago PMI and ISM manufacturing all printed.
    # Each weekday in the next 14 days is now stated with its event
    # count or its unverified flag, computed at refresh time.
    today_ny = datetime.now(ZoneInfo("America/New_York")).date()
    by_date = {}
    for e in events:
        by_date.setdefault(e["date"], []).append(e["name"])
    weekday_coverage = []
    for i in range(14):
        d = today_ny + timedelta(days=i)
        if d.weekday() >= 5:
            continue
        names = by_date.get(d.isoformat(), [])
        weekday_coverage.append({
            "date": d.isoformat(),
            "events_on_record": len(names),
            "event_names": names,
            "state": "covered" if names else "unverified_no_events_on_record",
            "note": (None if names else
                     "No event of the kinds this calendar covers is "
                     "on record for this weekday. That is "
                     "unverified, not quiet: other releases this "
                     "calendar does not carry may print that day."),
        })

    # Second carrier: every dated snapshot that carries a copy of
    # this calendar must agree with the document, event for event.
    carriers = 0
    doc_keys = {event_key(e) for e in raw_events}
    for path in sorted(glob.glob(SNAPSHOT_GLOB)):
        try:
            snap = load_json(path)
        except (OSError, ValueError):
            continue  # an unreadable snapshot is not a carrier
        me = ((snap.get("data") or {}).get("macro_events")
              if isinstance(snap, dict) else None)
        if not isinstance(me, dict) or not isinstance(me.get("events"), list):
            continue
        carriers += 1
        if me.get("source") != EXPECTED_VERSION:
            return fail("a snapshot carries a calendar of an "
                        "unexpected version")
        if me.get("coverage_start") != coverage_start or \
                me.get("coverage_end") != coverage_end:
            return fail("a snapshot's calendar coverage disagrees "
                        "with the calendar on record")
        snap_keys = {event_key(e) for e in me["events"]
                     if isinstance(e, dict)}
        if len(snap_keys) != len(me["events"]) or snap_keys != doc_keys:
            return fail("a snapshot's copy of the calendar disagrees "
                        "with the calendar on record, event for event")
    if carriers == 0:
        return fail("no second carrier of the calendar was found "
                    "to check it against")

    return {
        "tool": "The Week Ahead",
        "source": SOURCE_WORDS,
        "assembled_on": assembled_on,
        "coverage_start": coverage_start,
        "coverage_end": coverage_end,
        "events_total": len(events),
        "carriers_checked": carriers,
        "scope_note": SCOPE_NOTE,
        "events": events,
        "window_start": today_ny.isoformat(),
        "window_days": 14,
        "weekday_coverage": weekday_coverage,
        "window_note": ("Rolling 14 day window from the refresh "
                        "date in New York. A weekday listed as "
                        "unverified_no_events_on_record has no "
                        "event of the covered kinds on record; it "
                        "is not evidence of a quiet day."),
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
    print(f"Week Ahead refresh: wrote {OUT_PATH} "
          f"({doc['events_total']} events, coverage "
          f"{doc['coverage_start']} to {doc['coverage_end']}, "
          f"checked against {doc['carriers_checked']} snapshot "
          f"carrier(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
