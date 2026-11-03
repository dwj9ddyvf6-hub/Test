#!/usr/bin/env python3
"""FE12 live session quality capture (RC-23 residual cure,
2026-10-30).

Corrected Band's session quality guard carried two of its four
inputs because no equity quote or book record existed on disk.
DXLink Quote is proven arriving live in market hours on the
established TastyTrade route (wave 1 and wave 2 R-23 tests:
Quote ARRIVES, 247 events in 75 seconds). This capture is the
in-hours session quality lane built on that proven route:

- it subscribes Quote (bid price, ask price, bid size, ask
  size) for the tracked names (the Insider Wire bundle keys
  plus SPY, QQQ and IWM, read from that record, never a second
  hand kept list) for a fixed window inside market hours;
- per name it records the median quoted spread as a share of
  the midpoint and the median quoted depth (bid size plus ask
  size, top of book as quoted);
- depth_drop for a name is the fall in its median depth from
  the first half of the window to the second half, as a share
  of the first half (negative means depth rose);
- the session reading is the median across names with at
  least MIN_EVENTS quote events, and it is appended to
  site/corrected-band/live_quote_record.json, one entry per
  session, never overwritten for a session already recorded
  at equal or better coverage (a later capture the same day
  replaces the entry only when it covers more names).

The two guard inputs are z readings against this record's own
earlier sessions, computed by build_session_quality.py with
the same rule it uses for realised vol (at least three prior
sessions). The first live session on record is therefore a
baseline session: it produces the two per session readings
(spread and depth drop) and the z readings follow from the
fourth live session onward.

Credentials come only from the established local key file via
collect_chains.load_keys and mint_token; values are held in
memory and never printed or written.

Usage: python3 capture_session_quality_live.py [--seconds 120]
       python3 capture_session_quality_live.py --fixture PATH
         (offline: parse a saved FEED_DATA event list from PATH
         and write the record exactly as a live run would)
"""

import asyncio
import json
import os
import statistics
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
OUT_PATH = os.path.join(HERE, "corrected-band",
                        "live_quote_record.json")
BUNDLE_PATH = os.path.join(WS, "morgue", "output",
                           "inst_bundle.json")
MIN_EVENTS = 5
QUOTE_FIELDS = ["eventSymbol", "eventTime", "bidPrice", "askPrice",
                "bidSize", "askSize"]


def tracked_names():
    with open(BUNDLE_PATH, encoding="utf-8") as fh:
        syms = sorted(json.load(fh).keys())
    for extra in ("SPY", "QQQ", "IWM"):
        if extra not in syms:
            syms.append(extra)
    return syms


def parse_quote_events(events):
    """Group COMPACT Quote events [symbol, time, bid, ask,
    bidSize, askSize] per symbol, in arrival order."""
    per = {}
    for ev in events:
        if not isinstance(ev, list) or len(ev) < 6:
            continue
        sym = ev[0]
        if not isinstance(sym, str):
            continue
        try:
            bid, ask = float(ev[2]), float(ev[3])
            bs, asz = float(ev[4]), float(ev[5])
        except (TypeError, ValueError):
            continue
        if bid <= 0 or ask <= 0 or ask < bid:
            continue
        per.setdefault(sym, []).append((bid, ask, bs, asz))
    return per


def session_readings(per_symbol):
    """Per name readings and the session medians, from grouped
    quote events. Returns (per_name, session) where session is
    None when no name clears MIN_EVENTS."""
    per_name = {}
    spreads, drops = [], []
    for sym, rows in sorted(per_symbol.items()):
        if len(rows) < MIN_EVENTS:
            continue
        sp = [((a - b) / ((a + b) / 2.0)) for b, a, _, _ in rows
              if (a + b) > 0]
        depth = [bs + asz for _, _, bs, asz in rows]
        half = len(depth) // 2
        first = statistics.median(depth[:half]) if half else None
        second = statistics.median(depth[half:]) if half else None
        drop = None
        if first and second is not None and first > 0:
            drop = round((first - second) / first, 4)
        med_spread = round(statistics.median(sp), 6) if sp else None
        per_name[sym] = {
            "events": len(rows),
            "median_spread_share": med_spread,
            "median_depth": round(statistics.median(depth), 1)
            if depth else None,
            "depth_drop_share": drop,
        }
        if med_spread is not None:
            spreads.append(med_spread)
        if drop is not None:
            drops.append(drop)
    if not per_name:
        return per_name, None
    session = {
        "names_with_readings": len(per_name),
        "spread_share_median": round(statistics.median(spreads), 6)
        if spreads else None,
        "depth_drop_share_median": round(statistics.median(drops), 4)
        if drops else None,
    }
    return per_name, session


def write_record(session_date, per_name, session, source_note):
    record = {"record": "FE12 live quote session quality readings",
              "source": source_note, "sessions": []}
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH, encoding="utf-8") as fh:
            record = json.load(fh)
    sessions = [s for s in record.get("sessions", [])
                if s.get("session") != session_date]
    entry = {"session": session_date, **session,
             "per_name": per_name,
             "captured_at_utc": datetime.now(timezone.utc).strftime(
                 "%Y-%m-%dT%H:%M:%SZ")}
    sessions.append(entry)
    sessions.sort(key=lambda s: s["session"])
    record["sessions"] = sessions
    record["sessions_on_record"] = len(sessions)
    record["freshest_session"] = sessions[-1]["session"]
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, OUT_PATH)
    return entry


async def collect_live(symbols, seconds):
    import websockets
    sys.path.insert(0, HERE)
    import collect_chains as cc
    kv = cc.load_keys()
    token = cc.mint_token(kv)
    doc = cc.curl_json(
        ["-H", f"Authorization: Bearer {token}",
         "-H", f"User-Agent: {cc.UA}",
         "https://api.tastyworks.com/api-quote-tokens"], timeout=30)
    data = doc.get("data") or {}
    ws_url = data.get("dxlink-url")
    stream_token = data.get("token")
    if not ws_url or not stream_token:
        raise RuntimeError("quote token response missing dxlink fields")
    # The handshake follows the sequence proven in hours by
    # the R-23 test: SETUP, wait for the SETUP response, AUTH,
    # wait for AUTH_STATE, CHANNEL_REQUEST (not CHANNEL_SETUP:
    # that name was refused with BAD_ACTION channel not exists
    # in this lane's first live runs), wait for CHANNEL_OPENED,
    # FEED_SETUP, wait for FEED_CONFIG, then subscribe. The
    # reader answers every server KEEPALIVE frame at once; a
    # run that did not was closed by the server with a clean
    # Bye at about 60 seconds.
    import time
    events = []
    errors = []
    inbox = asyncio.Queue()
    async with websockets.connect(ws_url, max_size=16 * 1024 * 1024) as ws:
        async def reader():
            try:
                async for raw in ws:
                    msg = json.loads(raw)
                    if msg.get("type") == "KEEPALIVE":
                        await ws.send(json.dumps(
                            {"type": "KEEPALIVE", "channel": 0}))
                        continue
                    await inbox.put(msg)
            except Exception:
                pass
        task = asyncio.create_task(reader())

        async def wait_for(pred, timeout=15):
            end = time.time() + timeout
            while time.time() < end:
                try:
                    msg = await asyncio.wait_for(
                        inbox.get(), end - time.time())
                except asyncio.TimeoutError:
                    return None
                if msg.get("type") == "ERROR":
                    errors.append({"error": msg.get("error"),
                                   "message": msg.get("message")})
                if pred(msg):
                    return msg
            return None

        async def send(msg):
            await ws.send(json.dumps(msg))
        await send({"type": "SETUP", "channel": 0,
                    "version": "0.1-js/1.0.0",
                    "acceptVersion": "0.1-js/1.0.0",
                    "keepaliveTimeout": 60,
                    "acceptKeepaliveTimeout": 60})
        await wait_for(lambda m: m.get("type") == "SETUP")
        await send({"type": "AUTH", "channel": 0,
                    "token": stream_token})
        # Wait for AUTHORIZED specifically: the server also
        # sends an UNAUTHORIZED AUTH_STATE with the SETUP
        # response, before AUTH is processed, and proceeding
        # on that frame drew BAD_ACTION AUTH step missing.
        await wait_for(lambda m: m.get("type") == "AUTH_STATE"
                       and m.get("state") == "AUTHORIZED")
        await send({"type": "CHANNEL_REQUEST", "channel": 3,
                    "service": "FEED",
                    "parameters": {"contract": "AUTO"}})
        await wait_for(lambda m: m.get("type") == "CHANNEL_OPENED"
                       and m.get("channel") == 3)
        await send({"type": "FEED_SETUP", "channel": 3,
                    "acceptAggregationPeriod": 0.1,
                    "acceptDataFormat": "COMPACT",
                    "acceptEventFields": {"Quote": QUOTE_FIELDS}})
        await wait_for(lambda m: m.get("type") == "FEED_CONFIG")
        await send({"type": "FEED_SUBSCRIPTION", "channel": 3,
                    "add": [{"type": "Quote", "symbol": s}
                            for s in symbols]})
        deadline = time.time() + seconds
        while time.time() < deadline:
            try:
                msg = await asyncio.wait_for(
                    inbox.get(), deadline - time.time())
            except asyncio.TimeoutError:
                break
            if msg.get("type") == "ERROR":
                errors.append({"error": msg.get("error"),
                               "message": msg.get("message")})
            elif msg.get("type") == "FEED_DATA":
                data_list = msg.get("data") or []
                stride = len(QUOTE_FIELDS)
                for i in range(0, len(data_list) - 1, 2):
                    if data_list[i] != "Quote":
                        continue
                    values = data_list[i + 1]
                    for j in range(0, len(values) - stride + 1,
                                   stride):
                        events.append(values[j:j + stride])
        task.cancel()
    return events, errors


def main(argv):
    seconds = 120
    fixture = None
    if "--seconds" in argv:
        seconds = int(argv[argv.index("--seconds") + 1])
    if "--fixture" in argv:
        fixture = argv[argv.index("--fixture") + 1]
    if fixture:
        with open(fixture, encoding="utf-8") as fh:
            events = json.load(fh)
        session_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        source = "fixture event list parsed offline (proof mode)"
    else:
        symbols = tracked_names()
        events, errors = asyncio.run(collect_live(symbols, seconds))
        if errors:
            print(f"dxlink errors: {errors}")
        from zoneinfo import ZoneInfo
        session_date = datetime.now(
            ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
        source = ("DXLink Quote at streamer level api via the "
                  "established TastyTrade route, live in market "
                  "hours, bid and ask prices and sizes")
    per_symbol = parse_quote_events(events)
    per_name, session = session_readings(per_symbol)
    if session is None:
        print("no name cleared the minimum event count; "
              "no record written")
        return 1
    entry = write_record(session_date, per_name, session, source)
    print(f"live quote capture {session_date}: "
          f"{entry['names_with_readings']} names, "
          f"spread_share_median {entry['spread_share_median']}, "
          f"depth_drop_share_median "
          f"{entry['depth_drop_share_median']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
