#!/usr/bin/env python3
"""Per name priced expected move record (publication cure B4 /
R-15, 2026-10-30).

Engine 11 has never published a row and Engine 12's bigger than
priced leg and FE17 centre have never had an input, because no
record carried a priced expected move for an individual name: the
chain store is index only. This lane extends the proven Alpaca
options route (contracts with dated open interest, indicative
snapshots carrying bid and ask) from the three index names to
upcoming reporters only, the bounded universe dated in the
earnings calendar record's next 14 days.

For each such name, on the session of the run: the nearest expiry
on or after the report date is read from the contracts API, the
at the money call and put nearest spot are snapshot on feed
indicative, and the record stores the raw inputs (spot from the
panel's last close, strikes, expiry, bid, ask, quote basis) plus
two move figures that must agree or be flagged:

- straddle move: (call mid + put mid) / spot, the classic priced
  move, needing no vol model;
- modelled IV move: spot times the ATM modelled IV (Black-Scholes
  inversion of the same midpoints, chain_content) times sqrt(T),
  the chain store's existing expected move form.

A disagreement above 20 percent flags the name in the record
instead of silently choosing. A name whose chain cannot be read
is named in the record's missing list with its error, never given
an estimated move.

Store: site/earnings-record/priced_moves.json (the earnings
record lane's folder, one earnings fact set, one home).

Usage: python3 priced_moves.py [--days 14]
"""

import json
import math
import os
import sys
from datetime import date, datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(os.path.dirname(HERE))
PANEL = os.path.join(WORKSPACE, "morgue", "data_cache",
                     "board_bt_bars.json")
CAL_RECORD = os.path.join(HERE, "earnings-calendar", "record.json")
OUT_PATH = os.path.join(HERE, "earnings-record",
                        "priced_moves.json")
PAPER_URL = "https://paper-api.alpaca.markets"
DATA_URL = "https://data.alpaca.markets"
FLAG_PCT = 20.0

sys.path.insert(0, HERE)
import chain_content as cc  # noqa: E402


def _recompute(row, spot, captured):
    """The producer's own figures for one name at a given spot,
    from the quote mids on record. Shared by the panel resync."""
    mids = {occ: q["mid"] for occ, q in row["quotes"].items()}
    if len(mids) != 2:
        return None
    straddle_pct = round(sum(mids.values()) / spot * 100.0, 4)
    t = cc.t_years(row["expiry"], captured)
    ivs = []
    for occ, is_call in ((row["call"], True), (row["put"], False)):
        p = cc.parse_occ(occ)
        iv = cc.implied_vol(mids[occ], spot, p["strike"], t,
                            is_call, 0.0)
        if iv is not None:
            ivs.append(iv)
    iv_move_pct = (round(spot * (sum(ivs) / len(ivs))
                         * math.sqrt(t) / spot * 100.0, 4)
                   if ivs else None)
    flag = None
    if iv_move_pct:
        diff = abs(straddle_pct - iv_move_pct) / iv_move_pct * 100.0
        if diff > FLAG_PCT:
            flag = (f"straddle and modelled IV moves "
                    f"disagree by {diff:.1f} percent")
    return straddle_pct, iv_move_pct, flag


def resync_panel():
    """Panel resync (PANEL-RESYNC-20261031): re-derive spot and
    spot_session from the price panel's last row per name and
    recompute the straddle and modelled IV figures from the
    record's own stored quote mids, without fetching new quotes.
    Fail closed: the recompute must first reproduce every stored
    figure exactly at the stored spot, or nothing is written.
    This is the fallback when a live refetch cannot complete;
    the full run above remains the primary lane."""
    with open(OUT_PATH, encoding="utf-8") as fh:
        record = json.load(fh)
    with open(PANEL, encoding="utf-8") as fh:
        panel = json.load(fh)
    captured = datetime.strptime(
        record["updated_ts"], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc)
    for sym, row in record["names"].items():
        got = _recompute(row, row["spot"], captured)
        if got is None or got != (row["straddle_move_pct"],
                                  row["modelled_iv_move_pct"],
                                  row["cross_check_flag"]):
            print(f"priced_moves resync: control failed for {sym}; "
                  "nothing written", file=sys.stderr)
            return 1
    changed = 0
    for sym, row in record["names"].items():
        last = panel[sym][-1]
        if row["spot_session"] == last[0] and \
                row["spot"] == float(last[4]):
            continue
        row["spot"] = float(last[4])
        row["spot_session"] = last[0]
        s, iv, flag = _recompute(row, row["spot"], captured)
        row["straddle_move_pct"] = s
        row["modelled_iv_move_pct"] = iv
        row["priced_move_pct"] = s
        row["cross_check_flag"] = flag
        changed += 1
    record["panel_resynced_ts"] = datetime.now(
        timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record["panel_resync_note"] = (
        "Spot and spot_session re-derived from the price panel "
        "(board_bt_bars.json) after the panel advanced past the "
        "session this record's quotes were captured in; straddle "
        "and modelled IV figures recomputed from the record's own "
        "stored quote mids with the producer's formulas, verified "
        "to reproduce the stored figures exactly at the old spot "
        "before the new spot was applied. No new quotes fetched.")
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(record, indent=1, sort_keys=True) + "\n")
    os.replace(tmp, OUT_PATH)
    print(f"priced_moves resync: {changed} names re-derived from "
          f"the panel, {len(record['names'])} on record")
    return 0


def main(argv):
    if "--resync-panel" in argv:
        return resync_panel()
    days = 14
    if "--days" in argv:
        days = int(argv[argv.index("--days") + 1])
    sys.path.insert(0, os.path.expanduser(
        "~/workspace/custom-skills/local-alpaca-paper/bin"))
    from alpaca_lib import api_request
    with open(CAL_RECORD, encoding="utf-8") as fh:
        cal = json.load(fh)
    with open(PANEL, encoding="utf-8") as fh:
        panel = json.load(fh)
    today = datetime.now(timezone.utc).date()
    upcoming = {}
    for sym, d in cal["entries"].items():
        if not d:
            continue
        rd = date.fromisoformat(d)
        if 0 <= (rd - today).days <= days and sym in panel:
            upcoming[sym] = d
    captured = datetime.now(timezone.utc)
    names, missing = {}, []
    for sym, report_date in sorted(upcoming.items()):
        try:
            spot = float(panel[sym][-1][4])
            spot_session = panel[sym][-1][0]
            resp = api_request(
                "GET", f"{PAPER_URL}/v2/options/contracts",
                params={"underlying_symbols": sym, "status": "active",
                        "limit": 1000,
                        "expiration_date_gte": report_date,
                        "expiration_date_lte": date.fromordinal(
                            date.fromisoformat(report_date)
                            .toordinal() + 21).isoformat()})
            contracts = resp.get("option_contracts") or []
            if not contracts:
                missing.append({"symbol": sym,
                                "error": "no_contracts_after_report"})
                continue
            expiries = sorted({c["expiration_date"]
                               for c in contracts})
            expiry = expiries[0]
            live = [c for c in contracts
                    if c["expiration_date"] == expiry]
            def dist(c):
                return abs(float(c["strike_price"]) - spot)
            calls = sorted([c for c in live if c["type"] == "call"],
                           key=dist)
            puts = sorted([c for c in live if c["type"] == "put"],
                          key=dist)
            if not calls or not puts:
                missing.append({"symbol": sym,
                                "error": "no_atm_call_or_put"})
                continue
            occs = [calls[0]["symbol"], puts[0]["symbol"]]
            snap = api_request(
                "GET", f"{DATA_URL}/v1beta1/options/snapshots",
                params={"symbols": ",".join(occs),
                        "feed": "indicative"})
            snaps = snap.get("snapshots") or {}
            mids, quotes = {}, {}
            for occ in occs:
                q = (snaps.get(occ) or {}).get("latestQuote") or {}
                mid = cc.quote_mid(q.get("bp"), q.get("ap"))
                if mid is None:
                    continue
                mids[occ] = mid
                quotes[occ] = {"bid": q.get("bp"), "ask": q.get("ap"),
                               "mid": round(mid, 4)}
            if len(mids) != 2:
                missing.append({"symbol": sym,
                                "error": "no_indicative_quote_mid"})
                continue
            straddle_pct = round(
                sum(mids.values()) / spot * 100.0, 4)
            t = cc.t_years(expiry, captured)
            ivs = []
            for occ, is_call in ((occs[0], True), (occs[1], False)):
                p = cc.parse_occ(occ)
                iv = cc.implied_vol(mids[occ], spot, p["strike"], t,
                                    is_call, 0.0)
                if iv is not None:
                    ivs.append(iv)
            iv_move_pct = (round(spot * (sum(ivs) / len(ivs))
                                 * math.sqrt(t) / spot * 100.0, 4)
                           if ivs else None)
            flag = None
            if iv_move_pct:
                diff = abs(straddle_pct - iv_move_pct) \
                    / iv_move_pct * 100.0
                if diff > FLAG_PCT:
                    flag = (f"straddle and modelled IV moves "
                            f"disagree by {diff:.1f} percent")
            names[sym] = {
                "report_date": report_date, "spot": spot,
                "spot_session": spot_session, "expiry": expiry,
                "call": occs[0], "put": occs[1], "quotes": quotes,
                "straddle_move_pct": straddle_pct,
                "modelled_iv_move_pct": iv_move_pct,
                "priced_move_pct": straddle_pct,
                "cross_check_flag": flag,
            }
        except Exception as exc:  # noqa: BLE001 - named per name
            missing.append({"symbol": sym, "error": str(exc)[:160]})
    record = {
        "updated_ts": captured.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": ("Alpaca options contracts and indicative "
                   "snapshots via priced_moves.py; priced move is "
                   "the at the money straddle over spot, cross "
                   "checked against the modelled IV move"),
        "window_days": days,
        "names_dated_in_window": len(upcoming),
        "priced_moves_on_record": len(names),
        "missing": missing,
        "names": names,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(record, indent=1, sort_keys=True) + "\n")
    os.replace(tmp, OUT_PATH)
    print(f"priced_moves: {len(names)} of {len(upcoming)} upcoming "
          f"reporters priced, {len(missing)} missing")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
