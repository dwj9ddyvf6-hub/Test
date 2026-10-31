#!/usr/bin/env python3
"""Refresh the Chain Explorer data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: the archived options chain itself: one stored file
per trading day and index fund (SPY, QQQ, IWM), each holding every
contract read that day with its open interest, its trading volume,
its implied volatility and the fund's price level when the chain
was read. The store now accrues under the chain snapshot collector
(site/collect_chains.py, TastyTrade nested chains), whose manifest
(one line per fund per run, with the stored file's sha256) is the
store's own record: every stored day must match the manifest's
latest ok line for that file, hash for hash, or the refresh stops.
Three further records (the gathering record, the published card
and the published daily summary) stamp the older Map archive's
state; they must still agree with each other, and while the store
holds no snapshot they are the record the empty state is checked
against, but their no-data stamp speaks for the Map reads only and
is not evidence about the collector's store.

Reconstruction choices: a contract's place in the chain (its expiry
day, whether it is a call or a put, and its strike) is read off the
contract's own code, the standard options code every exchange uses.
The archived record carries no price for an individual contract and
no greeks, so none is published as a recorded figure: the page
computes the greeks itself, in the reader's browser, from the
recorded price level and implied volatility, using the same model
conventions as the Payoff Sketch on this site (the standard
textbook pricing formula, a 4.5% interest rate, no dividends, time
to expiry counted from the end of the snapshot day), and labels
them computed. A contract whose implied volatility is not on record
carries no computed greeks. Nothing is carried over from any other
day or any other source.

Non-claims: nothing on this page is live, and no figure is an
exchange figure. Open interest is the count recorded when the chain
was read, which reflects the prior close. The page makes no claim
about what any contract is worth today, and it publishes nothing
for a snapshot that is not stored.

Fail-closed rules: if any two state stamps disagree with each
other; if the store is empty but a stamp does not say the archive
is empty; if a stored day has no matching manifest line, or the
manifest's latest hash for it differs from the bytes on disk; if
a stored day's own date or fund does not match the day and fund
it is filed under; if a stored day has no price level, a contract
code that does not parse as its own fund's contract, a duplicate
contract, or an open interest figure that is present but not a
number at or above zero, the refresh stops and publishes nothing.
The collector's snapshots carry no open interest figure (the
nested chain has none to record), so open interest may be absent,
exactly as volume and implied volatility may; absent stays absent
in the published file, never a fabricated zero.

Honesty rules:
- Dates are read off the sources, never from the clock. The
  checked date comes from the state stamps while the store is
  empty, and from the freshest manifest-verified snapshot day once
  snapshots are stored, and every snapshot day shown comes from a
  stored file, so running this script twice produces the same
  file.
- Absence is not zero: zero stored snapshots is published as the
  plain not-yet-archived state, naming what the archive holds.

Usage: python3 refresh_chain.py
"""

import gzip
import hashlib
import json
import os
import re
import sys

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None
try:
    import options_gate as _og
except ImportError:  # gate unavailable: snapshots carry no gate block
    _og = None

HERE = os.path.dirname(os.path.abspath(__file__))
MORGUE = os.path.expanduser("~/workspace/morgue")
CHAINS_DIR = os.path.join(MORGUE, "state", "morgue", "chains")
EXT_PATH = os.path.join(MORGUE, "state", "morgue", "ext.json")
CARD_PATH = os.path.join(MORGUE, "output", "ext_card.json")
FEED_PATH = os.path.join(MORGUE, "output", "morgue-feed.json")
OUT_PATH = os.path.join(HERE, "chain-explorer", "data.json")

UNDERLYINGS = ["SPY", "QQQ", "IWM"]
OCC_RE = re.compile(r"^([A-Z]+)(\d{6})([CP])(\d{8})$")

SOURCE_WORDS = ("The options chains read for SPY, QQQ and IWM and "
                "kept on file, one snapshot per trading day: every "
                "contract in the chain as read, with its open "
                "interest, its trading volume and the volatility "
                "the market was pricing into it where the snapshot "
                "carries those figures, and the fund's price level "
                "when the chain was read")
DELAY_WORDS = ("Each snapshot is as it stood when the chain was "
               "read that day; a figure the snapshot does not "
               "carry is shown as not on record, never filled in "
               "from another day or another source. Nothing here "
               "is live")
GREEKS_WORDS = ("The greeks on this page are computed by this page, "
                "in your browser, from the recorded price level and "
                "the recorded implied volatility, using the same "
                "pricing model as the Payoff Sketch on this site "
                "(the standard textbook formula, a 4.5% interest "
                "rate, no dividends, time to expiry counted from "
                "the end of the snapshot day). They are labelled "
                "computed because the recorded chain carries no "
                "greeks of its own")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Chain Explorer refresh: {message}", file=sys.stderr)
    return 1


def chain_stamps(doc):
    """The per-fund chain state stamps in one carrier document."""
    chain = doc.get("chain") or {}
    return chain.get("cards") or {}


def lane_stamp(doc):
    lanes = (doc.get("lanes") or {}).get("lanes") or {}
    return lanes.get("chain_archive")


def stored_days(underlying):
    d = os.path.join(CHAINS_DIR, underlying)
    try:
        names = os.listdir(d)
    except OSError:
        return []
    return sorted(n[:-8] for n in names if n.endswith(".json.gz"))


def manifest_check(days_by_und):
    """Verify every stored day against the collector manifest, the
    store's own record: the manifest's latest ok line for a stored
    file must carry the sha256 of the bytes on disk. Returns None
    when the store and its record agree, else an error message."""
    path = os.path.join(CHAINS_DIR, "manifest.jsonl")
    try:
        with open(path, encoding="utf-8") as fh:
            lines = [json.loads(line) for line in fh if line.strip()]
    except (OSError, ValueError):
        return ("snapshot day(s) are stored, but the collector "
                "manifest that records the store cannot be read; "
                "refusing to publish a store its own record does "
                "not cover.")
    latest = {}
    for line in lines:
        if line.get("status") != "ok":
            continue
        key = (line.get("symbol"),
               os.path.basename(line.get("path") or ""))
        latest[key] = line
    for und, days in days_by_und.items():
        for day in days:
            line = latest.get((und, f"{day}.json.gz"))
            if line is None:
                return (f"the stored chain for {und} on {day} has "
                        "no ok line in the collector manifest; "
                        "refusing to publish a day the store's "
                        "own record does not cover.")
            fpath = os.path.join(CHAINS_DIR, und, f"{day}.json.gz")
            with open(fpath, "rb") as fh:
                digest = hashlib.sha256(fh.read()).hexdigest()
            if line.get("sha256") != digest:
                return (f"the stored chain for {und} on {day} does "
                        "not match the collector manifest's hash "
                        "for it; refusing to publish a store its "
                        "own record disagrees with.")
    return None


def parse_occ(code, underlying):
    m = OCC_RE.match(code or "")
    if not m:
        return None
    root, ymd, kind, strike8 = m.groups()
    if root != underlying:
        return None
    expiry = f"20{ymd[0:2]}-{ymd[2:4]}-{ymd[4:6]}"
    return expiry, kind == "C", int(strike8) / 1000.0


def read_snapshot(underlying, day):
    """One stored snapshot, validated; returns (snapshot, None) or
    (None, error message)."""
    path = os.path.join(CHAINS_DIR, underlying, f"{day}.json.gz")
    try:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError, EOFError):
        return None, (f"the stored chain for {underlying} on {day} "
                      "cannot be read; refusing to publish a "
                      "partial chain.")
    if doc.get("underlying") != underlying or doc.get("day") != day:
        return None, (f"the stored chain filed as {underlying} "
                      f"{day} calls itself {doc.get('underlying')} "
                      f"{doc.get('day')}; refusing to publish a "
                      "mismatched snapshot.")
    spot = doc.get("spot")
    if not isinstance(spot, (int, float)) or isinstance(spot, bool) \
            or spot <= 0:
        return None, (f"the stored chain for {underlying} on {day} "
                      "carries no usable price level; refusing to "
                      "publish a chain with nothing to measure "
                      "it against.")
    cols = doc.get("columns") or []
    if cols[:1] != ["occ"] or \
            not {"oi", "volume", "iv"} <= set(cols[1:]):
        return None, (f"the stored chain for {underlying} on {day} "
                      "does not carry the recorded fields this "
                      "page reads; refusing to guess its layout.")
    idx = {name: cols.index(name) for name in cols}
    rows = doc.get("rows") or []
    if not rows:
        return None, (f"the stored chain for {underlying} on {day} "
                      "carries no contracts; a stored snapshot "
                      "with nothing in it is a broken record, not "
                      "an empty chain.")
    seen = set()
    by_expiry = {}
    candidates = []
    greek_idx = idx.get("greek_ts", idx.get("greeks_ts"))
    for row in rows:
        if not isinstance(row, list) or len(row) != len(cols):
            return None, (f"a contract row in the {underlying} "
                          f"chain for {day} does not match the "
                          "record's own layout; refusing to "
                          "publish.")
        code = row[idx["occ"]]
        if code in seen:
            return None, (f"the contract {code} appears twice in "
                          f"the {underlying} chain for {day}; "
                          "refusing to publish a doubled chain.")
        seen.add(code)
        parsed = parse_occ(code, underlying)
        if parsed is None:
            return None, (f"the contract code {code} in the "
                          f"{underlying} chain for {day} does not "
                          "parse as one of its own contracts; "
                          "refusing to publish.")
        expiry, is_call, strike = parsed
        oi = row[idx["oi"]]
        if oi is not None and (not isinstance(oi, (int, float))
                               or isinstance(oi, bool) or oi < 0):
            return None, (f"{code} on {day}: the recorded open "
                          "interest is not a number at or above "
                          "zero; refusing to publish.")
        volume = row[idx["volume"]]
        if volume is not None and (not isinstance(volume,
                                                  (int, float))
                                   or isinstance(volume, bool)
                                   or volume < 0):
            return None, (f"{code} on {day}: the recorded volume "
                          "is not a number at or above zero; "
                          "refusing to publish.")
        iv = row[idx["iv"]]
        if iv is not None and (not isinstance(iv, (int, float))
                               or isinstance(iv, bool) or iv <= 0):
            return None, (f"{code} on {day}: the recorded implied "
                          "volatility is not a positive number; "
                          "refusing to publish.")
        candidates.append({
            "iv": iv,
            "greek_ts": (row[greek_idx] if greek_idx is not None
                         else None)})
        slot = by_expiry.setdefault(expiry, {}).setdefault(
            strike, {"call": None, "put": None})
        slot["call" if is_call else "put"] = {
            "oi": oi, "volume": volume, "iv": iv}
    expiries = []
    for expiry in sorted(by_expiry):
        strikes = []
        for strike in sorted(by_expiry[expiry]):
            pair = by_expiry[expiry][strike]
            strikes.append({"strike": strike,
                            "call": pair["call"],
                            "put": pair["put"]})
        expiries.append({"expiry": expiry, "strikes": strikes})
    gate = None
    if _og is not None:
        gate = _og.gate_summary(candidates, doc.get("captured_at_utc"))
        gate["note"] = (
            "Candidate gate (75 minute Greek freshness where a "
            "Greek timestamp exists, undated labelling where none "
            "does, IV ceiling 500 percent). This snapshot's source "
            "supplies no Greek timestamps, so its contracts are "
            "undated, stated rather than silently trusted.")
    return {
        "underlying": underlying,
        "snapshot_day": day,
        "spot": spot,
        "open_interest_dated": doc.get("oi_date"),
        "contracts": len(rows),
        "options_gate": gate,
        "expiries": expiries,
    }, None


def build():
    for path in (EXT_PATH, CARD_PATH, FEED_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    carriers = {}
    for name, path in (("gathering record", EXT_PATH),
                       ("published card", CARD_PATH),
                       ("published daily summary", FEED_PATH)):
        doc = load_json(path)
        carriers[name] = (chain_stamps(doc), lane_stamp(doc))

    # Every carrier's per-fund chain stamps must agree exactly.
    reference = None
    for name, (cards, _lane) in carriers.items():
        if set(cards) != set(UNDERLYINGS):
            return fail(f"the {name} does not stamp the chain "
                        "state for exactly SPY, QQQ and IWM; "
                        "refusing to guess the archive's state.")
        if reference is None:
            reference = cards
        elif cards != reference:
            return fail("the records stamp the chain archive "
                        "differently from each other; refusing "
                        "to publish until they agree.")
    stamps = reference

    # Every carrier's archive stamp must agree exactly too.
    lane_reference = None
    for name, (_cards, lane) in carriers.items():
        if not lane:
            return fail(f"the {name} carries no chain archive "
                        "state stamp; refusing to guess the "
                        "archive's state.")
        if lane_reference is None:
            lane_reference = lane
        elif lane != lane_reference:
            return fail("the records stamp the chain archive's "
                        "collection state differently; refusing "
                        "to publish until they agree.")
    lane = lane_reference

    as_of = stamps[UNDERLYINGS[0]].get("as_of")
    if not as_of:
        return fail("the chain state stamps carry no date; "
                    "refusing to guess.")
    for und in UNDERLYINGS:
        if stamps[und].get("as_of") != as_of:
            return fail("the chain state stamps carry different "
                        "dates for different funds; refusing to "
                        "publish a mixed state.")
    # The lane stamp's as_of is the day the morgue built the
    # section (a run date); the archive's data date is its
    # last_date, and that is what must agree with the per-fund
    # chain stamps. Demanding the run date equal the data date
    # refused every coherent cycle once the section was rebuilt
    # on a later day than the archived session (hookup cure,
    # 2026-10-29; same defect class as the tape family cure).
    if lane.get("last_date") != as_of:
        return fail("the archive collection stamp's last data "
                    "date carries a different date from the "
                    "chain stamps; refusing to publish a mixed "
                    "state.")

    days_by_und = {und: stored_days(und) for und in UNDERLYINGS}
    total_days = sum(len(v) for v in days_by_und.values())

    if total_days == 0:
        for und in UNDERLYINGS:
            st = stamps[und]
            if st.get("status") != "no_data" or \
                    "no archived chain yet" not in \
                    (st.get("reason") or ""):
                return fail(f"no chain is stored for {und}, but "
                            "its state stamp does not say the "
                            "archive is empty; refusing to publish "
                            "a state the records do not agree on.")
        if lane.get("status") != "no_data" or \
                lane.get("reason") != "no chain archived yet":
            return fail("no chain is stored, but the archive "
                        "collection stamp does not say the archive "
                        "is empty; refusing to publish a state "
                        "the records do not agree on.")
        coverage = ("The options chain archive this page reads "
                    "holds no snapshot yet: 0 snapshots on record "
                    "for SPY, QQQ and IWM, no expiry on record, "
                    "and no most recent snapshot day. The archive "
                    "starts with the first chain read and kept")
        data = {
            "tool": "Chain Explorer",
            "state": "no_snapshot_yet",
            "checked": as_of,
            "snapshots_on_record": 0,
            "freshest_snapshot": None,
            "underlyings": [],
            "source": SOURCE_WORDS,
            "delay": DELAY_WORDS,
            "greeks_note": GREEKS_WORDS,
            "coverage": coverage,
            "receipt": {
                "checked": as_of,
                "source": SOURCE_WORDS,
                "coverage": coverage,
            },
        }
    else:
        # The store accrues under the collector, so the agreement
        # that binds it is the collector manifest, not the Map
        # stamps: those stamps record the Map reads (their source
        # is the Map's own Alpaca reads) and their no-data state
        # predates the collector's first stored day.
        err = manifest_check(days_by_und)
        if err:
            return fail(err)
        underlyings = []
        for und in UNDERLYINGS:
            snapshots = []
            for day in days_by_und[und]:
                snap, err = read_snapshot(und, day)
                if err:
                    return fail(err)
                snapshots.append(snap)
            underlyings.append({"underlying": und,
                                "snapshots": snapshots})
        freshest = max(d for v in days_by_und.values() for d in v)
        as_of = freshest
        coverage = (f"{total_days} snapshot day(s) on record "
                    f"across SPY, QQQ and IWM; the most recent "
                    f"snapshot day is {freshest}. Each snapshot "
                    "shows the contracts on record for that day "
                    "only; a contract missing from a snapshot is "
                    "not shown, never filled in from another day")
        data = {
            "tool": "Chain Explorer",
            "state": "snapshots_on_record",
            "checked": as_of,
            "snapshots_on_record": total_days,
            "freshest_snapshot": freshest,
            "underlyings": underlyings,
            "source": SOURCE_WORDS,
            "delay": DELAY_WORDS,
            "greeks_note": GREEKS_WORDS,
            "coverage": coverage,
            "receipt": {
                "checked": as_of,
                "source": SOURCE_WORDS,
                "coverage": coverage,
            },
        }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (state {data['state']}, "
          f"{data['snapshots_on_record']} snapshot(s) on record, "
          f"checked {as_of})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
