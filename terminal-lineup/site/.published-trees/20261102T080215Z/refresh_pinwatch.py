#!/usr/bin/env python3
"""Refresh the Expiry Pin Watch data file.

Rebuilt 2026-10-29 in the same pass as the chain content cure
(G5): the old page fail-closed forever once the chain store began
accruing, because its honest state was "no per-strike open
interest exists anywhere". That state ended when the collector
started storing MEASURED per-strike open interest (Alpaca
contracts API, dated by the snapshot's oi_date) beside the
TastyTrade strike layout.

What this page now publishes, per underlying, from the freshest
manifest-verified chain snapshot:

- for each expiry carrying measured open interest, the strike
  where the most contracts are still open (calls + puts), with
  its call and put open interest counted separately;
- the pin for the nearest such expiry: that heaviest strike,
  named as the level open interest can pull price toward into
  the expiry. A pin is a statement about where contracts sit,
  never a forecast that price will go there.

Fail-closed rules: a stored snapshot day with no matching ok
manifest line, or whose bytes do not hash to the manifest's
sha256, stops the refresh; a snapshot whose rows carry no
measured open interest at all publishes the honest
no_open_interest_picture_yet state for that name, never a pin
built from anything else. Open interest is a stock (contracts
still open), not a flow: print sizes, volume and gamma pull are
never presented as open interest here.

Dates are read off the store, never the clock, so running this
script twice on the same store produces the same file.

Usage: python3 refresh_pinwatch.py
"""

import gzip
import hashlib
import json
import os
import sys
from datetime import date

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None
try:
    import chain_content as _ccx
except ImportError:
    _ccx = None

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(os.path.dirname(HERE))
CHAINS_DIR = os.path.join(WORKSPACE, "morgue", "state", "morgue", "chains")
OUT_PATH = os.path.join(HERE, "expiry-pin-watch", "data.json")
UNDERLYINGS = ["SPY", "QQQ", "IWM"]

SOURCE_WORDS = ("Per-strike open interest measured by the Alpaca "
                "contracts record and kept in the daily chain "
                "snapshots, beside the strike layout kept from the "
                "nested chain record")


def fail(message):
    print(f"Expiry Pin Watch refresh: {message}", file=sys.stderr)
    return 1


def long_date(iso):
    y, m, d = (int(p) for p in iso.split("-"))
    return date(y, m, d).strftime("%A, %B %d, %Y").replace(" 0", " ")


def stored_days(underlying):
    d = os.path.join(CHAINS_DIR, underlying)
    try:
        names = os.listdir(d)
    except OSError:
        return []
    return sorted(n[:-8] for n in names if n.endswith(".json.gz"))


def manifest_ok_hashes():
    """{(symbol, day): sha256} from the collector manifest's ok
    lines; the latest ok line for a file wins."""
    out = {}
    path = os.path.join(CHAINS_DIR, "manifest.jsonl")
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("status") != "ok" or not row.get("sha256"):
                continue
            p = row.get("path") or ""
            day = os.path.basename(p)[:-8] if p.endswith(".json.gz") else None
            if day and row.get("symbol"):
                out[(row["symbol"], day)] = row["sha256"]
    return out


def read_snapshot(underlying, day, expected_sha):
    path = os.path.join(CHAINS_DIR, underlying, f"{day}.json.gz")
    raw = open(path, "rb").read()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        return None, (f"the stored snapshot for {underlying} on {day} "
                      "does not hash to its manifest record; refusing "
                      "to publish from unverified bytes")
    try:
        doc = json.loads(gzip.decompress(raw))
    except (ValueError, OSError) as exc:
        return None, f"the stored snapshot for {underlying} on {day} cannot be read: {exc}"
    return doc, None


def build():
    if _ccx is None:
        return fail("chain_content module unavailable; refusing to guess pins")
    hashes = manifest_ok_hashes()
    names = []
    checked_days = []
    total_pins = 0
    for und in UNDERLYINGS:
        days = stored_days(und)
        if not days:
            names.append({"symbol": und, "state": "no_snapshot_on_record",
                          "pin": None, "expiries": []})
            continue
        day = days[-1]
        sha = hashes.get((und, day))
        if sha is None:
            return fail(f"no ok manifest line verifies the stored "
                        f"snapshot for {und} on {day}; refusing to "
                        "publish from an unverified store")
        doc, err = read_snapshot(und, day, sha)
        if err:
            return fail(err)
        checked_days.append(day)
        rows = doc.get("rows") or []
        heaviest = _ccx.heaviest_strikes_by_expiry(rows)
        cov = doc.get("field_coverage") or {}
        if not heaviest:
            names.append({
                "symbol": und, "state": "no_open_interest_picture_yet",
                "snapshot_day": day, "oi_date": doc.get("oi_date"),
                "spot": doc.get("spot"), "pin": None, "expiries": [],
                "contracts_with_oi": cov.get("with_oi", 0)})
            continue
        expiries = []
        for expiry in sorted(heaviest):
            h = heaviest[expiry]
            expiries.append({"expiry": expiry,
                             "heaviest_strike": h["strike"],
                             "total_oi": h["total_oi"],
                             "call_oi": h["call_oi"],
                             "put_oi": h["put_oi"]})
        nearest = expiries[0]
        pin = {"expiry": nearest["expiry"],
               "strike": nearest["heaviest_strike"],
               "total_oi": nearest["total_oi"],
               "call_oi": nearest["call_oi"],
               "put_oi": nearest["put_oi"]}
        total_pins += 1
        names.append({
            "symbol": und, "state": "pin_on_record",
            "snapshot_day": day, "oi_date": doc.get("oi_date"),
            "spot": doc.get("spot"), "pin": pin,
            "expiries": expiries[:12],
            "expiry_count_with_oi": len(expiries),
            "contracts_with_oi": cov.get("with_oi", 0),
            "contracts": cov.get("contracts", len(rows))})
    checked = max(checked_days) if checked_days else None
    state = ("pins_on_record" if total_pins
             else "no_open_interest_picture_yet")
    coverage = (
        f"Checked against the chain snapshots on record"
        + (f", freshest {long_date(checked)}" if checked else "")
        + f": {total_pins} of {len(UNDERLYINGS)} names carry measured "
          "per-strike open interest for named expiries.")
    data = {
        "tool": "Expiry Pin Watch",
        "state": state,
        "checked": checked,
        "source": SOURCE_WORDS,
        "coverage": coverage,
        "pins_on_record": total_pins,
        "names": names,
        "what_the_job_needs": (
            "A pin watch is made from open interest: for one name "
            "and one expiry day, the strikes where the most "
            "contracts are still open. Those are the levels price "
            "can get pulled toward as the expiry nears."),
        "receipt": {"checked": checked, "coverage": coverage,
                    "source": SOURCE_WORDS},
    }
    if not total_pins:
        data["empty_reason"] = (
            "No snapshot on record carries measured per-strike open "
            "interest for a named expiry, so no pin is shown.")
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        fh.write(json.dumps(data, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, OUT_PATH)
    print(f"Wrote {OUT_PATH} (state {data['state']}, checked "
          f"{checked}, pins {total_pins})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
