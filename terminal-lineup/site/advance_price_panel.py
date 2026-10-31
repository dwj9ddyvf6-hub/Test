#!/usr/bin/env python3
"""Daily price-panel advance lane (cure G1/G2, 2026-10-29).

Root cause of the freeze: board_bt_bars.json was built once as a
backtest file ending 2026-10-23 and no lane ever advanced it, so the
grading price source (forecast/grading.py PriceSource) could never
mature a forecast past that date and zero grades landed.

This lane appends every completed session after the panel's last
date, per symbol, from Alpaca SIP daily bars (feed=sip, explicit
start always passed, multi-symbol endpoint, paginated). Stored bars
were verified byte-equal to Alpaca SIP raw bars for 2026-10-22/23
(SPY), so new rows use the same raw adjustment. Symbols with no new
bars (halted/delisted) are named in the report, never silently
filled. The result must pass grading.validate_bars_payload before
it is written, atomically, or nothing is written.

Usage: python3 advance_price_panel.py [--through YYYY-MM-DD]
Default through: the freshest completed session (see
completed_session.py; terminal audit cure, 2026-10-31). The old
default, yesterday in America/New_York, made every post-close run
advance only through the prior session, so panel-fed engines
published one session behind the rest of the terminal every day.
"""
import json
import os
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.expanduser(
    "~/workspace/custom-skills/local-alpaca-paper/bin"))
sys.path.insert(0, os.path.expanduser("~/workspace/terminal-lineup"))

PANEL_PATH = os.path.expanduser("~/workspace/morgue/data_cache/board_bt_bars.json")
DATA = "https://data.alpaca.markets"


def fetch_bars(symbols, start_iso, end_iso):
    """{symbol: {date: [date,o,h,l,c,v]}} from Alpaca SIP daily bars."""
    from alpaca_lib import api_request
    out = {}
    batch = 200
    for i in range(0, len(symbols), batch):
        chunk = symbols[i:i + batch]
        token = None
        while True:
            params = {"symbols": ",".join(chunk), "timeframe": "1Day",
                      "start": f"{start_iso}T00:00:00Z",
                      "end": f"{end_iso}T00:00:00Z",
                      "feed": "sip", "limit": 10000}
            if token:
                params["page_token"] = token
            resp = api_request("GET", f"{DATA}/v2/stocks/bars", params=params)
            for sym, bars in (resp.get("bars") or {}).items():
                for b in bars or []:
                    day = b["t"][:10]
                    out.setdefault(sym, {})[day] = [
                        day, b["o"], b["h"], b["l"], b["c"], b["v"]]
            token = resp.get("next_page_token")
            if not token:
                break
    return out


def advance(panel, fetched):
    """Append fetched sessions strictly after each symbol's last
    stored date. Returns (appended_per_symbol, missing_symbols)."""
    appended = {}
    missing = []
    for sym, rows in panel.items():
        last = rows[-1][0] if rows else None
        new = [fetched[sym][d] for d in sorted(fetched.get(sym, {}))
               if last is None or d > last]
        if new:
            rows.extend(new)
            appended[sym] = [r[0] for r in new]
        else:
            missing.append(sym)
    return appended, missing


def main():
    through = None
    if "--through" in sys.argv:
        through = sys.argv[sys.argv.index("--through") + 1]
    if through is None:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from completed_session import freshest_completed_session
        through = freshest_completed_session()
    with open(PANEL_PATH, encoding="utf-8") as fh:
        panel = json.load(fh)
    last_dates = sorted({rows[-1][0] for rows in panel.values() if rows})
    panel_last = last_dates[-1]
    if panel_last >= through:
        print(f"panel already at {panel_last}; nothing to advance")
        return 0
    start = (date.fromisoformat(panel_last) + timedelta(days=1)).isoformat()
    end = (date.fromisoformat(through) + timedelta(days=1)).isoformat()
    fetched = fetch_bars(sorted(panel), start, end)
    appended, missing = advance(panel, fetched)
    if not appended:
        print(f"FAIL: no new bars fetched for {start}..{through}; "
              f"panel left at {panel_last}", file=sys.stderr)
        return 1
    from forecast.grading import validate_bars_payload
    problems = validate_bars_payload(panel)
    if problems:
        print(f"FAIL: advanced panel fails integrity gate: "
              f"{'; '.join(problems[:5])}; nothing written",
              file=sys.stderr)
        return 1
    tmp = PANEL_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(panel, fh)
    os.replace(tmp, PANEL_PATH)
    new_last = sorted({rows[-1][0] for rows in panel.values() if rows})[-1]
    total_new = sum(len(v) for v in appended.values())
    print(f"panel advanced {panel_last} -> {new_last}: "
          f"{total_new} new bars across {len(appended)} symbols; "
          f"{len(missing)} symbols with no new bars"
          + (f" ({', '.join(missing[:20])})" if missing else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
