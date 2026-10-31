#!/usr/bin/env python3
"""Fetch a fresh earnings calendar record from a public source.

Cure for the stale half of G10 (2026-10-29): the Earnings Calendar
tool consumed two records stamped 2026-10-12 and nothing ever
re-checked them. This lane re-checks scheduled report dates
against the Nasdaq public earnings calendar API (no credentials,
one public file per day) for the checked universe (the legacy
records' names union the daily scoring run's full board list;
TRADING-PATH-EARNINGS-20261031 widened it from 77 names after the
lane could not answer for the book's own carded names), over a
forward window, and writes ONE dated record the tool consumes:

  site/earnings-calendar/record.json
    {"updated_ts": "<UTC ISO Z>", "source": "nasdaq public
     earnings calendar api (api.nasdaq.com/api/calendar/earnings)",
     "window_days": N, "entries": {"SYM": "YYYY-MM-DD" or null}}

A name with no row in the window is recorded null (no date
scheduled inside the window), never given a guessed date. A day
whose fetch fails stops the lane and writes nothing: a partial
calendar dressed as a full re-check is worse than a stale one
whose date is printed on its face.

Route history, kept honest: Yahoo quoteSummary calendarEvents
was tried first (Yahoo is the spot/VIX source already in use)
and refused with "Invalid Crumb" (crumb-gated); the Nasdaq
public calendar is the route that answers.

Usage: python3 fetch_earnings_calendar.py [--days 60]
"""

import json
import os
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(os.path.dirname(HERE))
LEGACY_PATHS = [
    os.path.join(WORKSPACE, "alpaca-swing-desk", "desk", "earnings.json"),
    os.path.join(WORKSPACE, "alpaca-swing-desk", "desk",
                 "phase_earnings.json"),
]
OUT_PATH = os.path.join(HERE, "earnings-calendar", "record.json")
API = "https://api.nasdaq.com/api/calendar/earnings?date={day}"


BOARD_FULL_PATH = os.path.expanduser(
    "~/workspace/morgue/output/board_full.json")


def legacy_symbols():
    syms = set()
    for path in LEGACY_PATHS:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        syms.update(k for k in doc if k != "updated_ts")
    return sorted(syms)


def universe_symbols():
    """TRADING-PATH-EARNINGS-20261031: the checked universe is the
    legacy watchlist UNION the daily scoring run's full list
    (morgue/output/board_full.json) and the Breakout Scanner's
    names on record. Before this cure the lane checked only the
    77 legacy names, so it could not answer the earnings rule for
    the book's own carded names (KDP, the book's first candidate
    for 2026-11-02, was absent, as were CVX, ABBV, REGN, CL and
    CBOE). The board list is the terminal's widest dated universe
    and already contains every Board, Scanner and carded name the
    audit named. If the board list cannot be read, the lane fails
    closed: a silently shrunk universe is the defect itself."""
    syms = set(legacy_symbols())
    with open(BOARD_FULL_PATH, encoding="utf-8") as fh:
        full = json.load(fh)
    rows = full.get("rows") if isinstance(full, dict) else None
    if not isinstance(rows, list) or not rows:
        raise RuntimeError(
            f"board full list at {BOARD_FULL_PATH} carries no rows; "
            "refusing to re-check a shrunk earnings universe")
    syms.update((r.get("symbol") or "").strip().upper()
                for r in rows if isinstance(r, dict))
    syms.discard("")
    return sorted(syms)


def parse_day_payload(doc, wanted):
    """{symbol: date} for wanted symbols in one day's Nasdaq
    payload. Pure: the day itself is stamped by the caller from
    the request, and a row's own date is the request day by the
    API's contract (one file per day)."""
    rows = ((doc or {}).get("data") or {}).get("rows") or []
    out = {}
    for row in rows:
        sym = (row.get("symbol") or "").strip().upper()
        if sym in wanted:
            out[sym] = True
    return out


def fetch_day(day_iso):
    out = subprocess.run(
        ["curl", "-sS", "--fail", "-m", "30", "-A", "Mozilla/5.0",
         "-H", "Accept: application/json", API.format(day=day_iso)],
        capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"nasdaq calendar fetch failed for "
                           f"{day_iso}: {out.stderr.strip()[:160]}")
    return json.loads(out.stdout)


def main(argv):
    days = 60
    if "--days" in argv:
        days = int(argv[argv.index("--days") + 1])
    today = datetime.now(timezone.utc).date()
    wanted = set(universe_symbols())
    found = {}
    for i in range(days):
        day = today + timedelta(days=i)
        doc = fetch_day(day.isoformat())
        for sym in parse_day_payload(doc, wanted):
            found.setdefault(sym, day.isoformat())
    entries = {sym: found.get(sym) for sym in sorted(wanted)}
    record = {
        "updated_ts": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
        "source": ("nasdaq public earnings calendar api "
                   "(api.nasdaq.com/api/calendar/earnings)"),
        "window_start": today.isoformat(),
        "window_days": days,
        "names_checked": len(entries),
        "names_dated": sum(1 for v in entries.values() if v),
        "entries": entries,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, OUT_PATH)
    print(f"fetch_earnings_calendar: wrote {OUT_PATH} "
          f"({record['names_dated']} of {record['names_checked']} "
          f"names dated in {days} days from {today})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
