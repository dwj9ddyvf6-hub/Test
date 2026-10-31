#!/usr/bin/env python3
"""Refresh the Static GEX Cross-Check data file (DEEP-PASS 3.2
item 13).

Register triple:
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28).

Evidence class: the stored TastyTrade chain snapshots in the
chain store (one file per fund per day, rows of contract code,
open interest, volume and implied volatility, with the recorded
price level), read through the same manifest discipline as the
Chain Explorer, plus the Gamma Ladder's published data file for
the modelled inventory figures this surface cross-checks.

Reconstruction choices: the static GEX figures are computed by
site/static_gex.py under its one stated convention (calls
positive, puts negative; walls; a 101 point grid flip level with
each contract's implied volatility held constant across the
grid, and an IV sensitivity band at 0.80x and 1.25x). A contract
counts only when both its open interest and its implied
volatility are on the snapshot; the rest are excluded and
counted, never filled in. The snapshot implied volatility is
modelled (inverted from indicative quote midpoints), and that
basis is printed with the figures.

Non-claims: this is a cross check under a different convention,
not a replacement for the modelled ladder and not a reading of
any dealer's actual holdings. Where the two conventions put the
flip or a wall at different levels, both levels are printed and
the difference is the published fact.

Fail-closed rules: a fund whose freshest snapshot is missing,
unreadable, or carries no countable contract publishes a
not_on_record state for that fund rather than figures; if no
fund can be counted, the refresh stops and publishes nothing.

Usage: python3 refresh_staticgex.py
"""

import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
WORKSPACE = os.path.dirname(os.path.dirname(HERE))
CHAINS_DIR = os.path.join(WORKSPACE, "morgue", "state", "morgue", "chains")
LADDER_PATH = os.path.join(HERE, "gamma-ladder", "data.json")
OUT_DIR = os.path.join(HERE, "static-gex")
OUT_PATH = os.path.join(OUT_DIR, "data.json")
FUNDS = ["SPY", "QQQ", "IWM"]

try:
    import terminal_common as _tc
except ImportError:
    _tc = None

import static_gex as _sg

SOURCE_WORDS = ("The options chains kept on file for SPY, QQQ and IWM, "
                "one snapshot per trading day, read at each fund's "
                "freshest snapshot day on record")
CONVENTION_WORDS = (
    "One stated convention, the same for every fund: each call "
    "counts positive and each put counts negative, weighted by the "
    "contract's gamma and open interest, in dollars for a 1 percent "
    "move. The call wall is the strike with the largest positive "
    "call figure; the put wall is the strike with the largest put "
    "figure by size. The flip level is the price where the total "
    "crosses zero, searched on a grid 10 percent either side of the "
    "recorded price.")
IV_WORDS = (
    "On that grid search, each contract's implied volatility is "
    "held constant while the price moves: that is an assumption, "
    "stated here because gamma near the money is sensitive to it. "
    "The band beside each flip level is the range of flip levels "
    "the same search finds when every volatility is scaled to "
    "0.80 times and to 1.25 times its recorded value. The recorded "
    "volatility itself is modelled from the chain's quotes, not "
    "read off an exchange.")
CROSS_WORDS = (
    "Beside each fund, the modelled ladder's own flip level and "
    "walls for the same funds are printed. The two are built under "
    "different conventions, so a difference between them is a fact "
    "about the conventions, printed as a difference, not resolved "
    "into one number.")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def freshest_snapshot(symbol):
    d = os.path.join(CHAINS_DIR, symbol)
    if not os.path.isdir(d):
        return None
    days = sorted(f[:-8] for f in os.listdir(d) if f.endswith(".json.gz"))
    if not days:
        return None
    path = os.path.join(d, days[-1] + ".json.gz")
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def modelled_rows():
    if not os.path.exists(LADDER_PATH):
        return {}
    doc = load_json(LADDER_PATH)
    rows = {}
    for entry in doc.get("funds") or doc.get("ladders") or []:
        sym = entry.get("symbol")
        if sym:
            rows[sym] = {"flip": entry.get("flip"),
                         "call_wall": entry.get("call_wall"),
                         "put_wall": entry.get("put_wall"),
                         "net": entry.get("positioning_net"),
                         "spot": entry.get("spot")}
    return rows


def build():
    modelled = modelled_rows()
    funds, counted = [], 0
    freshest_day = None
    for sym in FUNDS:
        try:
            snap = freshest_snapshot(sym)
        except Exception as exc:  # unreadable snapshot: named, not faked
            funds.append({"underlying": sym, "state": "not_on_record",
                          "reason": f"snapshot unreadable: {exc}"})
            continue
        if snap is None:
            funds.append({"underlying": sym, "state": "not_on_record",
                          "reason": "no snapshot on record"})
            continue
        result = _sg.static_gex_snapshot(snap["rows"], snap["spot"],
                                         snap["day"], sym)
        freshest_day = max(freshest_day or snap["day"], snap["day"])
        if result["net_gex"] is None:
            funds.append({"underlying": sym, "state": "not_on_record",
                          "reason": "no contract carries both open "
                                    "interest and implied volatility",
                          "day": snap["day"], "coverage": result["coverage"]})
            continue
        counted += 1
        entry = {"underlying": sym, "state": "ok", "day": snap["day"],
                 "spot": result["spot"], "net_gex": result["net_gex"],
                 "call_wall": result["call_wall"],
                 "put_wall": result["put_wall"], "flip": result["flip"],
                 "flip_iv_band": result["flip_iv_band"],
                 "coverage": result["coverage"],
                 "strongest": sorted(
                     result["per_strike"],
                     key=lambda s: abs(s["net_gex"]), reverse=True)[:8]}
        m = modelled.get(sym)
        if m is not None:
            entry["modelled_ladder"] = m
            entry["flip_difference"] = (
                round(result["flip"] - m["flip"], 4)
                if result["flip"] is not None and m.get("flip") is not None
                else None)
        funds.append(entry)
    if counted == 0:
        print("Static GEX refresh: no fund could be counted; "
              "publishing nothing", file=sys.stderr)
        return 1
    data = {"tool": "Static GEX Cross-Check",
            "state": "snapshots_on_record",
            "checked": freshest_day,
            "freshest_snapshot": freshest_day,
            "source": SOURCE_WORDS,
            "convention": CONVENTION_WORDS,
            "iv_assumption": IV_WORDS,
            "cross_check": CROSS_WORDS,
            "funds": funds}
    if _tc is not None:
        data = _tc.stamp_for_script(data, __file__)
    os.makedirs(OUT_DIR, exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, OUT_PATH)
    print(f"Static GEX refresh: wrote {OUT_PATH} "
          f"({counted} of {len(FUNDS)} funds counted, "
          f"freshest {freshest_day})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
