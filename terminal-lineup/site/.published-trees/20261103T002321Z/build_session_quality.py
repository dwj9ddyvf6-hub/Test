#!/usr/bin/env python3
"""FE12 session quality record (RC-23 cure, 2026-10-30).

Corrected Band's session quality guard stood not_recorded with
all four inputs missing, because no intraday reading was on
record for any session. Two of the four inputs are computable
from intraday bars, and a live route for those bars exists on
this box (the first minutes lane proves Alpaca SIP 5 minute
bars daily). This builder is that route for the guard:

- realised vol per session: the square root of the sum of
  squared 5 minute log returns over the regular session, for
  SPY, QQQ and IWM, averaged;
- volume concentration per session: the share of the session's
  volume printed in its six most active 5 minute bars, same
  names, averaged (a share in [0, 1], the guard's own form);
- z readings for the freshest session against the earlier
  sessions in this record.

The other two inputs come from the live quote capture lane
(capture_session_quality_live.py, added 2026-10-30 for the
RC-23 residual): DXLink Quote in market hours records a per
session spread reading and a per session depth drop reading
for the tracked names, and this builder computes their z
readings against the capture record's earlier sessions with
the same three prior session rule used for realised vol.
Until three earlier live sessions exist, the record states
that accrual on its face so the guard publishes partial,
with the two inputs named by the guard itself.

Sessions are the board panel's own session dates; the record
keeps the trailing SESSIONS sessions and is rebuilt by this
script on the daily cadence before the engine refresh.

Store: site/corrected-band/session_quality_record.json

Usage: python3 build_session_quality.py
"""

import json
import math
import os
import statistics
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
PANEL_PATH = os.path.join(WS, "morgue", "data_cache",
                          "board_bt_bars.json")
OUT_PATH = os.path.join(HERE, "corrected-band",
                        "session_quality_record.json")
DATA_URL = "https://data.alpaca.markets"
SYMBOLS = ("SPY", "QQQ", "IWM")
SESSIONS = 65
TOP_BARS = 6


def session_readings(bars_by_sym):
    """(realised_vol, volume_concentration) averaged over the
    symbols present, or (None, None) when no symbol has bars."""
    rvs, concs = [], []
    for sym in SYMBOLS:
        rows = sorted(bars_by_sym.get(sym) or [])
        if len(rows) < 10:
            continue
        closes = [r[3] for r in rows]
        vols = [r[4] for r in rows]
        ss = 0.0
        for i in range(1, len(closes)):
            if closes[i] > 0 and closes[i - 1] > 0:
                lr = math.log(closes[i] / closes[i - 1])
                ss += lr * lr
        total_vol = sum(vols)
        if total_vol <= 0:
            continue
        rvs.append(math.sqrt(ss))
        concs.append(sum(sorted(vols, reverse=True)[:TOP_BARS])
                     / total_vol)
    if not rvs:
        return None, None
    return statistics.fmean(rvs), statistics.fmean(concs)


def main():
    sys.path.insert(0, os.path.expanduser(
        "~/workspace/custom-skills/local-alpaca-paper/bin"))
    from alpaca_lib import api_request
    with open(PANEL_PATH, encoding="utf-8") as fh:
        panel = json.load(fh)
    sessions = [r[0] for r in panel["SPY"]][-SESSIONS:]
    series = []
    for session in sessions:
        start = f"{session}T13:30:00Z"
        end = f"{session}T20:00:00Z"
        bars = {}
        token = None
        while True:
            params = {"symbols": ",".join(SYMBOLS),
                      "timeframe": "5Min", "start": start,
                      "end": end, "feed": "sip", "limit": 10000}
            if token:
                params["page_token"] = token
            resp = api_request("GET", f"{DATA_URL}/v2/stocks/bars",
                               params=params)
            for sym, rows in (resp.get("bars") or {}).items():
                bars.setdefault(sym, []).extend(
                    (r["t"], r["o"], r["h"], r["l"], r["c"], r["v"])
                    for r in rows)
            token = resp.get("next_page_token")
            if not token:
                break
        rv, conc = session_readings(
            {s: [(t, o, h, l, c, v) for (t, o, h, l, c, v) in rows]
             for s, rows in bars.items()})
        if rv is None:
            series.append({"session": session, "state": "no_bars"})
        else:
            series.append({"session": session, "state": "recorded",
                           "realised_vol": round(rv, 6),
                           "volume_concentration": round(conc, 4)})
    recorded = [s for s in series if s["state"] == "recorded"]
    freshest = recorded[-1] if recorded else None
    inputs = {"spread_z": None, "depth_drop_z": None,
              "volume_concentration": None, "realised_vol_z": None}
    # RC-23 residual (2026-10-30): the live quote capture
    # (capture_session_quality_live.py, DXLink Quote in market
    # hours) now records per session spread and depth drop
    # readings for the tracked names. When the freshest bar
    # session has a live capture and at least three earlier
    # live sessions exist, the two missing guard inputs are
    # computed as z readings against those earlier live
    # sessions, the same rule used for realised vol below.
    live = {"sessions_on_record": 0, "freshest_session": None,
            "state": "no_live_capture_on_record"}
    live_path = os.path.join(HERE, "corrected-band",
                             "live_quote_record.json")
    if os.path.exists(live_path):
        with open(live_path, encoding="utf-8") as fh:
            live_doc = json.load(fh)
        live_sessions = live_doc.get("sessions") or []
        live = {"sessions_on_record": len(live_sessions),
                "freshest_session": live_doc.get("freshest_session"),
                "state": "recorded"}
        if freshest:
            match = [s for s in live_sessions
                     if s.get("session") == freshest["session"]]
            priors = [s for s in live_sessions
                      if s.get("session") < freshest["session"]]
            if match and len(priors) >= 3:
                cur = match[-1]
                for key, field in (("spread_z", "spread_share_median"),
                                   ("depth_drop_z",
                                    "depth_drop_share_median")):
                    vals = [p[field] for p in priors
                            if p.get(field) is not None]
                    if len(vals) >= 3 and cur.get(field) is not None:
                        sd = statistics.pstdev(vals)
                        if sd > 0:
                            inputs[key] = round(
                                (cur[field] - statistics.fmean(vals))
                                / sd, 4)
            elif match:
                live["z_state"] = (
                    "baseline accruing: this session has a live "
                    "capture, and its z readings follow once "
                    "three earlier live sessions are on record")
    if freshest and len(recorded) >= 3:
        prior = recorded[:-1]
        mean = statistics.fmean(s["realised_vol"] for s in prior)
        sd = statistics.pstdev([s["realised_vol"] for s in prior])
        if sd > 0:
            inputs["realised_vol_z"] = round(
                (freshest["realised_vol"] - mean) / sd, 4)
        inputs["volume_concentration"] = \
            freshest["volume_concentration"]
    record = {
        "record": "FE12 session quality readings from intraday bars",
        "built_at_utc": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
        "source": ("Alpaca SIP 5 minute bars for SPY, QQQ and IWM, "
                   "regular session, via build_session_quality.py"),
        "sessions_on_record": len(recorded),
        "freshest_session": freshest["session"] if freshest else None,
        "freshest_inputs": inputs,
        "live_quote_capture": live,
        "absent_inputs": {
            "spread_z": ("no z reading until the live quote "
                         "capture record holds three earlier "
                         "sessions: capture_session_quality_live.py "
                         "records the per session spread reading "
                         "in market hours from 2026-10-30, and the "
                         "z follows from the fourth live session"),
            "depth_drop_z": ("no z reading until the live quote "
                             "capture record holds three earlier "
                             "sessions: the capture records the "
                             "per session depth drop reading in "
                             "market hours from 2026-10-30, and "
                             "the z follows from the fourth live "
                             "session"),
        },
        "series": series,
    }
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, OUT_PATH)
    print(f"session quality: {len(recorded)} sessions recorded, "
          f"freshest {record['freshest_session']}, "
          f"inputs {inputs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
