#!/usr/bin/env python3
"""Freshest completed NYSE session (terminal audit cure, 2026-10-31).

Root cause of the one-session lag defect: the panel advance lanes
defaulted their through date to "yesterday" in America/New_York.
An evening post-close run therefore advanced the panels only
through the prior session, and every engine whose decision date
derives from the panel end published one session behind the
engines that derive from the ledger or the calendar. The lag was
structural: it healed one day late and reappeared every day.

The completed session is a market fact, not a wall-clock offset:
today's session is completed once the regular close has passed
(16:10 ET, which also covers 13:00 early closes), and on a
non-session day the freshest completed session is the last
session before today. Session membership comes from the program's
own verified calendar, forecast/session_calendar.py; dates past
that calendar's edge fall back to weekday membership so the
helper never raises inside a refresh lane.
"""
import os
import sys
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CLOSE_DONE = time(16, 10)  # ET; regular close 16:00, early close 13:00


def _sessions():
    try:
        from forecast.session_calendar import load_calendar
        return load_calendar()
    except Exception:
        return None


def _is_session(day_iso, sessions):
    if sessions is not None and day_iso <= sessions[-1]:
        return day_iso in set(sessions)
    from datetime import date
    return date.fromisoformat(day_iso).weekday() < 5


def freshest_completed_session(now=None):
    """ISO date of the freshest completed NYSE session at ``now``
    (an aware datetime; default: now in America/New_York)."""
    if now is None:
        now = datetime.now(ZoneInfo("America/New_York"))
    now_et = now.astimezone(ZoneInfo("America/New_York"))
    sessions = _sessions()
    day = now_et.date()
    if _is_session(day.isoformat(), sessions) \
            and now_et.time() >= CLOSE_DONE:
        return day.isoformat()
    day -= timedelta(days=1)
    while not _is_session(day.isoformat(), sessions):
        day -= timedelta(days=1)
    return day.isoformat()


if __name__ == "__main__":
    print(freshest_completed_session())
