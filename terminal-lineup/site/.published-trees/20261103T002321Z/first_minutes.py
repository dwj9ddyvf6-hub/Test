#!/usr/bin/env python3
"""First minutes acceptance record (publication cure B2 / R-31,
2026-10-30).

Engine 28's failed gap sub claim reads acceptance from a daily
proxy (the closing location inside the day's range) because the
first minutes acceptance reading its design names was not on any
record. This lane builds that record for the panel's latest
session: for every name that gapped that session (the refresher's
own live set floor, absolute gap at or above 0.5 percent), Alpaca
SIP 5 minute bars for the first 30 minutes after the open are
fetched in multi symbol calls (start always passed; the API
returns the earliest bars from start, so the window end bounds
the slice), and per name the record stores:

- the first 15 minute range (first three 5 minute bars),
- the close location inside that range read in the gap direction
  (the acceptance statistic, same form as the daily proxy),
- whether price held beyond the opening print at minute 15.

Sessions before this record starts keep the daily proxy, labelled
as such by the consumer; no backfill is claimed beyond what SIP
actually returns, and names SIP does not serve are named in the
record's missing list.

Store: site/gap-destiny/first_minutes/<session>.json plus
site/gap-destiny/first_minutes/record.json (freshest pointer).

Usage: python3 first_minutes.py [--session YYYY-MM-DD]
"""

import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(os.path.dirname(HERE))
PANEL = os.path.join(WORKSPACE, "morgue", "data_cache",
                     "board_bt_bars.json")
OUT_DIR = os.path.join(HERE, "gap-destiny", "first_minutes")
DATA_URL = "https://data.alpaca.markets"
GAP_FLOOR = 0.005


def acceptance(first_bars, gap_up):
    """Close location inside the first 15 minute range, read in
    the gap direction. first_bars: [(o,h,l,c)] in time order."""
    if len(first_bars) < 3:
        return None
    hi = max(b[1] for b in first_bars[:3])
    lo = min(b[2] for b in first_bars[:3])
    close = first_bars[2][3]
    if hi <= lo:
        return None
    loc = (close - lo) / (hi - lo)
    return loc if gap_up else 1.0 - loc


def main(argv):
    sys.path.insert(0, os.path.expanduser(
        "~/workspace/custom-skills/local-alpaca-paper/bin"))
    from alpaca_lib import api_request
    with open(PANEL, encoding="utf-8") as fh:
        panel = json.load(fh)
    session = panel["SPY"][-1][0]
    if "--session" in argv:
        session = argv[argv.index("--session") + 1]
    gap_names = []
    for sym, rows in panel.items():
        for i in range(1, len(rows)):
            if rows[i][0] == session:
                pc, o = float(rows[i - 1][4]), float(rows[i][1])
                if pc > 0 and o > 0 and abs(o / pc - 1.0) >= GAP_FLOOR:
                    gap_names.append((sym, o > pc))
                break
    start = f"{session}T13:30:00Z"
    end = f"{session}T14:00:00Z"
    bars = {}
    token = None
    while True:
        params = {"symbols": ",".join(s for s, _ in gap_names),
                  "timeframe": "5Min", "start": start, "end": end,
                  "feed": "sip", "limit": 10000}
        if token:
            params["page_token"] = token
        resp = api_request("GET", f"{DATA_URL}/v2/stocks/bars",
                           params=params)
        for sym, rows in (resp.get("bars") or {}).items():
            bars.setdefault(sym, []).extend(
                (r["o"], r["h"], r["l"], r["c"]) for r in rows)
        token = resp.get("next_page_token")
        if not token:
            break
    names, missing = {}, []
    for sym, up in gap_names:
        rows = sorted(bars.get(sym, []))
        acc = acceptance(rows, up)
        if acc is None:
            missing.append(sym)
            continue
        names[sym] = {
            "gap_up": up,
            "acceptance_first15": round(acc, 4),
            "held_beyond_open_at_15": bool(
                (rows[2][3] > rows[0][0]) if up
                else (rows[2][3] < rows[0][0])),
            "bars_on_record": len(rows),
        }
    record = {
        "updated_ts": datetime.now(timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session": session,
        "source": ("Alpaca SIP 5 minute bars, first 30 minutes "
                   "after the open, via first_minutes.py"),
        "bar_size": "5Min",
        "gap_names": len(gap_names),
        "names_recorded": len(names),
        "missing": missing,
        "names_detail": names,
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    for path in (os.path.join(OUT_DIR, session + ".json"),
                 os.path.join(OUT_DIR, "record.json")):
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(record, indent=1, sort_keys=True)
                     + "\n")
        os.replace(tmp, path)
    print(f"first_minutes: session {session}, "
          f"{len(names)} of {len(gap_names)} gap names recorded, "
          f"{len(missing)} missing")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
