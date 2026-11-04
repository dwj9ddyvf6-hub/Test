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

Cure PANEL-LAGGARD-GAP-20261104: the fetch window used to start the
day after the panel's NEWEST symbol date, so a symbol whose newest
bar lagged the panel (SUPN, halted with zero trades on 2026-11-02,
whose zero bar Alpaca published late) never had its missing session
fetched once the panel moved past it, and the hole then blocked
every continuity-gated consumer (Momentum Clock refused to publish).
The window now starts after the OLDEST symbol date, bounded to 21
days before the through date so a long-dead symbol cannot widen it
without limit, and fetched rows merge in date order, inserting any
session the symbol is missing inside the window (a halted session's
zero bar is a real bar: flat OHLC at the prior close, volume 0).
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


def _capped_end(end_iso):
    """The request end for a through date, capped out of the recent
    SIP window. Cure PANEL-END-RECENT-SIP-20261102: the subscription
    refuses (403) any SIP query whose end sits inside its recent
    window, and end = through + 1 day at 00:00Z is always hours in
    the future for the scheduled 17:46 run, so the advance could
    only ever pass on late-night catch-up runs. Daily bars for a
    completed session are stamped 04:00Z, so capping the end at
    now minus 20 minutes never drops a completed bar in a
    post-close run; an early run simply finds no new bars and the
    lane fails loudly, as designed."""
    from datetime import timezone
    requested = datetime.fromisoformat(f"{end_iso}T00:00:00+00:00")
    cap = datetime.now(timezone.utc) - timedelta(minutes=20)
    if requested <= cap:
        return f"{end_iso}T00:00:00Z"
    return cap.strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_bars(symbols, start_iso, end_iso):
    """{symbol: {date: [date,o,h,l,c,v]}} from Alpaca SIP daily bars."""
    from alpaca_lib import api_request
    end_param = _capped_end(end_iso)
    out = {}
    batch = 200
    for i in range(0, len(symbols), batch):
        chunk = symbols[i:i + batch]
        token = None
        while True:
            params = {"symbols": ",".join(chunk), "timeframe": "1Day",
                      "start": f"{start_iso}T00:00:00Z",
                      "end": end_param,
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
    """Merge fetched sessions the symbol does not already hold, in
    date order: sessions after its last stored date append, and a
    missing interior session (a halted day whose bar was published
    late) is inserted where it belongs. Returns
    (appended_per_symbol, missing_symbols)."""
    appended = {}
    missing = []
    for sym, rows in panel.items():
        have = {r[0] for r in rows}
        new = [fetched[sym][d] for d in sorted(fetched.get(sym, {}))
               if d not in have]
        if new:
            rows.extend(new)
            rows.sort(key=lambda r: r[0])
            appended[sym] = [r[0] for r in new]
        else:
            missing.append(sym)
    return appended, missing


def classify_advance(appended, fetched):
    """Decide the lane's verdict after a merge attempt
    (PANEL-LAGGARD-DEADNAMES-20261104). "advanced": at least one held
    gap was filled. "noop": the source served bars in the window but
    none were new; every still-lagging symbol is one the source
    itself serves no newer bar for (a name that stopped trading
    keeps its last date forever, and that must not fail the lane).
    "fail": the fetch returned nothing at all, which is the broken
    fetch the original guard existed to catch."""
    if appended:
        return "advanced"
    if sum(len(v) for v in fetched.values()) == 0:
        return "fail"
    return "noop"


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
    panel_first_lag = last_dates[0]
    if panel_first_lag >= through:
        print(f"panel already at {panel_last}; nothing to advance")
        return 0
    # PANEL-LAGGARD-GAP-20261104: start after the OLDEST symbol's
    # last date so lagging symbols are re-fetched, bounded to 21
    # days before the through date.
    start_floor = (date.fromisoformat(through) - timedelta(days=21)).isoformat()
    start = max((date.fromisoformat(panel_first_lag) + timedelta(days=1)).isoformat(),
                start_floor)
    end = (date.fromisoformat(through) + timedelta(days=1)).isoformat()
    fetched = fetch_bars(sorted(panel), start, end)
    appended, missing = advance(panel, fetched)
    verdict = classify_advance(appended, fetched)
    if verdict == "fail":
        print(f"FAIL: no new bars fetched for {start}..{through}; "
              f"panel left at {panel_last}", file=sys.stderr)
        return 1
    if verdict == "noop":
        lagging = sorted((rows[-1][0], sym) for sym, rows in panel.items()
                         if rows and rows[-1][0] < through)
        print(f"panel already current through {through} for every "
              f"symbol the source serves; {len(lagging)} symbols hold "
              f"no bar after their last date and none was served: "
              + ", ".join(f"{sym} {d}" for d, sym in lagging))
        return 0
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
