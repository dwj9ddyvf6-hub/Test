"""Shared NYSE early-close calendar (13:00 ET sessions).

One source of truth for the sleeves that derive session clocks
from the actual close (saty_day, saty_sol, po10_qqq, spx_premium).
Before the 2026-10-22 cure each sleeve carried its own copy of a
finite table and the copies were missing known early closes
(2027-07-02, 2027-12-23) and every session from 2029 onward
(defect D-B3). Fully closed days are the calendar's business
(core.data.is_trading_day); this table holds only early closes.
Named, dated maintenance: extend yearly against the NYSE list.
"""
from datetime import date, datetime, time as dtime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

EARLY_CLOSES = {
    "2026-11-27": dtime(13, 0),   # day after Thanksgiving
    "2026-12-24": dtime(13, 0),   # Christmas Eve
    "2027-07-02": dtime(13, 0),   # Independence Day observed (Fri)
    "2027-11-26": dtime(13, 0),   # day after Thanksgiving
    "2027-12-23": dtime(13, 0),   # Christmas observed eve (Thu)
    "2028-07-03": dtime(13, 0),   # Independence Day observed eve
    "2028-11-24": dtime(13, 0),   # day after Thanksgiving
    "2029-07-03": dtime(13, 0),   # day before Independence Day (Wed)
    "2029-11-23": dtime(13, 0),   # day after Thanksgiving
    "2029-12-24": dtime(13, 0),   # Christmas Eve (Mon)
    "2030-07-03": dtime(13, 0),   # day before Independence Day (Wed)
    "2030-11-29": dtime(13, 0),   # day after Thanksgiving
    "2030-12-24": dtime(13, 0),   # Christmas Eve (Tue)
}


def session_close_dt(session_iso):
    """The session's actual close: 16:00 ET, or the named early
    close for that date."""
    d = date.fromisoformat(str(session_iso)[:10])
    t = EARLY_CLOSES.get(d.isoformat(), dtime(16, 0))
    return datetime.combine(d, t, tzinfo=ET)


def is_early_close(session_iso):
    return str(session_iso)[:10] in EARLY_CLOSES
