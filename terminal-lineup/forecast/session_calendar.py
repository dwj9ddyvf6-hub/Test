"""Forward session calendar for the Forecast Engines 30 program.

Built 2026-10-30 (RC-04 cure): Engine 3's live branch fail-closed
because no session calendar beyond the shipped price history's last
session existed on record, so a qualifying live name could never be
issued a horizon. This module is that calendar: the NYSE session
list generated from the exchange's own published holiday rules
(weekends plus the rule-based holidays below), persisted beside it
as session_calendar.json so the calendar is a record on disk, not a
guess made inside a refresher. The generator and the persisted file
must agree; build_calendar_file refuses to write a file whose
sessions differ from a fresh generation, and load_calendar verifies
the file against the rules on every load.

Holidays, rule form (observed dates follow the NYSE convention:
a Saturday holiday is observed the Friday before, a Sunday holiday
the Monday after):
- New Year's Day (Jan 1)
- Martin Luther King Jr. Day (third Monday of January)
- Washington's Birthday (third Monday of February)
- Good Friday (the Friday before Easter Sunday, computus below)
- Memorial Day (last Monday of May)
- Juneteenth National Independence Day (Jun 19)
- Independence Day (Jul 4)
- Labor Day (first Monday of September)
- Thanksgiving Day (fourth Thursday of November)
- Christmas Day (Dec 25)

Early closes are not modelled: a session is a session for horizon
dating, which is all the ledger's horizon_open and horizon_close
fields carry.
"""
import json
import os
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
CALENDAR_PATH = os.path.join(HERE, "session_calendar.json")
FIRST_YEAR = 2026
LAST_YEAR = 2028


class CalendarError(Exception):
    pass


def _observed(d):
    if d.weekday() == 5:
        return d - timedelta(days=1)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


def _nth_weekday(year, month, weekday, n):
    d = date(year, month, 1)
    offset = (weekday - d.weekday()) % 7
    return d + timedelta(days=offset + 7 * (n - 1))


def _last_weekday(year, month, weekday):
    if month == 12:
        d = date(year, 12, 31)
    else:
        d = date(year, month + 1, 1) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - weekday) % 7)


def _easter(year):
    """Gregorian computus for Easter Sunday."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    ell = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * ell) // 451
    month, day = divmod(h + ell - 7 * m + 114, 31)
    return date(year, month, day + 1)


def holidays(year):
    """{date: name} of NYSE full-day closures for one year."""
    out = {}

    def add(d, name):
        out[d] = name

    add(_observed(date(year, 1, 1)), "New Year's Day")
    add(_nth_weekday(year, 1, 0, 3), "Martin Luther King Jr. Day")
    add(_nth_weekday(year, 2, 0, 3), "Washington's Birthday")
    add(_easter(year) - timedelta(days=2), "Good Friday")
    add(_last_weekday(year, 5, 0), "Memorial Day")
    add(_observed(date(year, 6, 19)), "Juneteenth")
    add(_observed(date(year, 7, 4)), "Independence Day")
    add(_nth_weekday(year, 9, 0, 1), "Labor Day")
    add(_nth_weekday(year, 11, 3, 4), "Thanksgiving Day")
    add(_observed(date(year, 12, 25)), "Christmas Day")
    # A New Year falling on Saturday is observed on Dec 31 of the
    # prior year; that closure belongs to the prior year's list.
    nxt = date(year + 1, 1, 1)
    if nxt.weekday() == 5:
        add(date(year, 12, 31), "New Year's Day (observed)")
    return out


def sessions(first_year=FIRST_YEAR, last_year=LAST_YEAR):
    """Sorted ISO session dates from Jan 1 of first_year through
    Dec 31 of last_year."""
    out = []
    d = date(first_year, 1, 1)
    end = date(last_year, 12, 31)
    closed = set()
    for y in range(first_year, last_year + 2):
        closed.update(holidays(y))
    while d <= end:
        if d.weekday() < 5 and d not in closed:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def build_calendar_file(path=CALENDAR_PATH):
    days = sessions()
    doc = {
        "calendar": "NYSE sessions, rule generated",
        "generated_on": "2026-10-30",
        "generator": "forecast/session_calendar.py",
        "first_session": days[0],
        "last_session": days[-1],
        "sessions": days,
        "holidays": {y: {d.isoformat(): n
                         for d, n in sorted(holidays(y).items())}
                     for y in range(FIRST_YEAR, LAST_YEAR + 1)},
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    return doc


def load_calendar(path=CALENDAR_PATH):
    """The persisted session list, verified against the rules on
    every load: a file that disagrees with a fresh generation is
    refused, never trusted."""
    if not os.path.exists(path):
        raise CalendarError(
            f"session calendar is not on record: {path} does not "
            f"exist; build it with forecast.session_calendar")
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    days = doc.get("sessions") or []
    if days != sessions():
        raise CalendarError(
            "session calendar on record disagrees with the NYSE "
            "holiday rules in forecast/session_calendar.py; "
            "refusing to date horizons from it")
    return days


def is_session(day, days=None):
    return day in set(days if days is not None else load_calendar())


def next_sessions(after, count, days=None):
    """The first `count` sessions strictly after `after`. Raises
    CalendarError when the calendar on record ends first, so a
    horizon is never guessed past the calendar's edge."""
    days = days if days is not None else load_calendar()
    out = [d for d in days if d > after][:count]
    if len(out) < count:
        raise CalendarError(
            f"session calendar ends {days[-1] if days else 'empty'}; "
            f"only {len(out)} of {count} sessions after {after} are "
            f"on record")
    return out


def sessions_between(first, last, days=None):
    days = days if days is not None else load_calendar()
    return [d for d in days if first <= d <= last]
