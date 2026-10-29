"""Parity: desk.feedlib.r19_source.DeskXNYS (the desk's NYSE rules + the exchange's ad-hoc closures) against the
calendar the R19 source read — exchange_calendars' XNYS built as backend/providers._nyse() built it
(get_calendar("XNYS", start="2000-01-01", end="2040-12-31")) — on every call r19_data / r19_intraday_data /
r19_timing / r19_tensor make: is_session, date_to_session (previous / next), session_open, session_close,
previous_session, next_session over every calendar day from its first to its last session, and sessions_in_range
over randomized ranges.

exchange_calendars is not a desk dependency: point XCALS_SITE at a directory holding it (pip install --target),
it is imported only in the source subprocess (python -I).

    XCALS_SITE=/path/to/site python3 -m tools.parity.run r19_calendar"""
import json
import os
import random
import subprocess
import sys
from datetime import date, timedelta

from tools.parity import write_receipt

START, END = date(2000, 1, 1), date(2040, 12, 31)
N_RANGES = int(os.environ.get("R19_CALENDAR_RANGES", "2000"))

SOURCE = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
import exchange_calendars as xc
from datetime import date, timedelta
P = json.load(sys.stdin)
cal = xc.get_calendar("XNYS", start="2000-01-01", end="2040-12-31")
first, last = cal.first_session.date(), cal.last_session.date()
d, days = first, {}
while d <= last:
    k = d.isoformat()
    s = bool(cal.is_session(k))
    row = {"s": s, "prev": str(cal.date_to_session(k, direction="previous").date()),
           "next": str(cal.date_to_session(k, direction="next").date())}
    if s:
        row["open"] = cal.session_open(k).timestamp()
        row["close"] = cal.session_close(k).timestamp()
        row["ps"] = str(cal.previous_session(k).date()) if d > first else None
        row["ns"] = str(cal.next_session(k).date()) if d < last else None
    days[k] = row
    d += timedelta(days=1)
ranges = [[str(x.date()) for x in cal.sessions_in_range(a, b)] for a, b in P["ranges"]]
print(json.dumps({"days": days, "ranges": ranges, "version": xc.__version__, "first": str(first), "last": str(last)}))
'''


def port_side(first, last, ranges):
    from desk.feedlib.r19_source import DeskXNYS
    cal = DeskXNYS()
    d, days = first, {}
    while d <= last:
        k = d.isoformat()
        s = bool(cal.is_session(k))
        row = {"s": s, "prev": str(cal.date_to_session(k, direction="previous").date()),
               "next": str(cal.date_to_session(k, direction="next").date())}
        if s:
            row["open"] = cal.session_open(k).timestamp()
            row["close"] = cal.session_close(k).timestamp()
            row["ps"] = str(cal.previous_session(k).date()) if d > first else None
            row["ns"] = str(cal.next_session(k).date()) if d < last else None
        days[k] = row
        d += timedelta(days=1)
    return {"days": days, "ranges": [[str(x.date()) for x in cal.sessions_in_range(a, b)] for a, b in ranges]}


def run():
    site = os.environ.get("XCALS_SITE")
    if not site or not os.path.isdir(site):
        raise SystemExit("set XCALS_SITE to a directory holding exchange_calendars")
    rnd = random.Random(19)
    span = (END - START).days
    ranges = []
    for _ in range(N_RANGES):
        a = START + timedelta(days=2 + rnd.randrange(span - 400))
        b = min(END - timedelta(days=7), a + timedelta(days=rnd.choice((0, 1, 3, 7, 30, 390, 1700, 2100))))
        ranges.append([a.isoformat(), b.isoformat()])
    payload = {"start": START.isoformat(), "end": END.isoformat(), "ranges": ranges}
    r = subprocess.run([sys.executable, "-I", "-c", SOURCE, os.path.abspath(site)], input=json.dumps(payload),
                       capture_output=True, text=True, timeout=1800, cwd=os.path.dirname(os.path.abspath(__file__)))
    if r.returncode:
        raise RuntimeError(r.stderr[-2000:])
    src = json.loads(r.stdout.strip().splitlines()[-1])
    port = port_side(date.fromisoformat(src["first"]), date.fromisoformat(src["last"]), ranges)
    diffs = []
    for k, row in src["days"].items():
        if port["days"].get(k) != row:
            diffs.append({"day": k, "source": row, "port": port["days"].get(k)})
    for i, (a, b) in enumerate(ranges):
        if src["ranges"][i] != port["ranges"][i]:
            diffs.append({"range": [a, b], "source_n": len(src["ranges"][i]), "port_n": len(port["ranges"][i])})
    cases = len(src["days"]) + len(ranges)
    stats = {"days": len(src["days"]), "sessions": sum(1 for r in src["days"].values() if r["s"]),
             "early_closes": sum(1 for r in src["days"].values() if r["s"] and r["close"] - r["open"] < 6.5 * 3600),
             "ranges": len(ranges), "exchange_calendars": src["version"]}
    res = {"cases": cases, "identical": cases - len(diffs), "diffs": diffs[:30], "n_diffs": len(diffs),
           "stats": stats, "source": "exchange_calendars XNYS (backend/providers._nyse, 2000-01-01..2040-12-31)",
           "port": "desk/feedlib/r19_source.py DeskXNYS"}
    from tools.parity.r19_ledger import r19_sleeve_ids
    res["sleeves"] = r19_sleeve_ids()
    write_receipt("r19_calendar", res)
    return dict(res, sleeve="r19_calendar")
