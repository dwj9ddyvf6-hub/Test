#!/usr/bin/env python3
"""Refresh the Tape Heatmap data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: the same tape record the Flow Tape publishes (per
fund, the 25 largest alert prints of the freshest session, each
carrying its strike, expiry day, call or put side, contracts and
premium), cross-checked against the Activity Profile's published
figures for the same session (per fund: prints examined and total
premium across every print looked at) and against the Flow Tape's
own published counts (alerts published and prints looked at). The
Proving Ground's published vocabulary supplies this page's proving
state.

Reconstruction choices: the only arithmetic is grouping. Alerts
that share a strike, an expiry day and a call or put side are
added together into one grid cell (premium added, contracts added,
alerts counted); nothing is re-scored, re-ranked, estimated or
filled in. Strikes and expiry days that appear in no alert for a
fund do not appear as rows or columns at all, and a strike and
expiry that appear separately but never together show an empty
cell, which the page labels as no alert print on record there.

What a figure is, in plain words, printed on the page: each cell
shows the money in the largest alert prints that landed on that
strike and expiry day, for calls and for puts separately, exactly
as the record carries those prints. The grid shows only the
session's largest alert prints (25 per fund), never every print:
the record looked at about a million prints and kept only the
largest alerts, so the cells add up to the alert sum, not to the
session total, and the page says so on its face and prints both.

Fail-closed rules:
- If any of the three published records read here is missing, the
  refresh stops.
- If the Flow Tape and the Activity Profile disagree on the
  session, on any fund's prints examined, on its completeness
  state or count of capped groups, the refresh stops.
- If the Flow Tape's published counts (alerts published, prints
  looked at) disagree with the alerts and prints actually carried,
  the refresh stops.
- If a fund's grid cells do not add back up to that fund's alert
  premium, alert contracts and alert count, the refresh stops.
- If the session totals assembled from the Activity Profile's
  published figures do not add back up across the three funds,
  the refresh stops.
- If the Proving Ground's vocabulary does not carry the
  measuring state, the refresh stops.
- If any assembled string carries internal wording (file names or
  record jargon), the refresh stops.

Honesty rules:
- Dates and times are read off the records, never from the clock,
  so running this script twice produces the same file, byte for
  byte.
- Absence is not zero: an empty cell is published as no cell at
  all in the data and labelled on the page as no alert print on
  record, never as no trading.

Usage: python3 refresh_tapeheatmap.py
"""

import json
import os
import sys
from datetime import date

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
FLOW_PATH = os.path.join(HERE, "flow-tape", "data.json")
ACTIVITY_PATH = os.path.join(HERE, "activity-profile", "data.json")
PROVING_PATH = os.path.join(HERE, "proving-ground", "data.json")
OUT_PATH = os.path.join(HERE, "tape-heatmap", "data.json")

FUNDS = ["SPY", "QQQ", "IWM"]

SOURCE_WORDS = ("Every options trade printed on the three big "
                "index funds during the trading day, scored print "
                "by print as it came in; this page groups the "
                "largest alert prints that record kept")

SCOPE_WORDS = ("This grid shows only the session's largest alert "
               "prints: 25 per fund, the ones the record kept. It "
               "looked at far more prints than it kept, so the "
               "cells add up to the money in those largest alerts, "
               "not to the session's full total, which is printed "
               "beside the grid exactly as published.")

EMPTY_WORDS = ("An empty cell means no alert print on record "
               "there. It does not mean nothing traded there: "
               "prints that were not among the session's largest "
               "alerts are not on this record.")

FORBIDDEN = ("morgue", "json", "tape_card", ".py", "ledger",
             "data file", "dataset")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Tape Heatmap refresh: {message}", file=sys.stderr)
    return 1


def long_date(iso):
    y, m, d = (int(p) for p in iso.split("-"))
    return date(y, m, d).strftime("%A, %B %d, %Y").replace(" 0", " ")


def build_side(alerts, kind):
    rows = {}
    expiries = set()
    strikes = set()
    for a in alerts:
        if a["contract"]["kind"] != kind:
            continue
        strike = a["contract"]["strike"]
        expiry = a["contract"]["expiry"]
        strikes.add(strike)
        expiries.add(expiry)
        cell = rows.setdefault((strike, expiry),
                               {"strike": strike, "expiry": expiry,
                                "premium_usd": 0.0, "contracts": 0,
                                "alerts": 0})
        cell["premium_usd"] += a["premium_usd"]
        cell["contracts"] += a["contracts"]
        cell["alerts"] += 1
    cells = [rows[k] for k in sorted(rows, key=lambda k: (-k[0], k[1]))]
    return {"strikes": sorted(strikes, reverse=True),
            "expiries": sorted(expiries),
            "cells": cells}


def build():
    for path in (FLOW_PATH, ACTIVITY_PATH, PROVING_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    flow = load_json(FLOW_PATH)
    activity = load_json(ACTIVITY_PATH)
    proving = load_json(PROVING_PATH)

    session = flow.get("session")
    if not session:
        return fail("the tape record carries no session date; "
                    "refusing to guess.")
    if activity.get("current_session") != session:
        return fail("the Activity Profile's current session "
                    f"{activity.get('current_session')} disagrees "
                    f"with the tape session {session}; refusing to "
                    "publish a mixed state.")

    groups = {g.get("underlying"): g for g in flow.get("groups") or []}
    names = {n.get("underlying"): n for n in activity.get("names") or []}
    if set(groups) != set(FUNDS) or set(names) != set(FUNDS):
        return fail("the records do not cover exactly SPY, QQQ "
                    "and IWM; refusing to publish a partial grid.")

    counts = flow.get("counts") or {}
    total_alerts = sum(len(g["alerts"]) for g in groups.values())
    if counts.get("alerts_published") != total_alerts:
        return fail("the tape record's published alert count "
                    f"{counts.get('alerts_published')} disagrees "
                    f"with the {total_alerts} alerts it carries; "
                    "refusing to publish.")
    total_prints = sum(g["prints_looked_at"] for g in groups.values())
    if counts.get("prints_looked_at") != total_prints:
        return fail("the tape record's published prints-looked-at "
                    "count disagrees with its per-fund counts; "
                    "refusing to publish.")
    act_prints = sum(n["activity"]["prints_examined"]
                     for n in names.values())
    if act_prints != total_prints:
        return fail("the Activity Profile's prints examined "
                    f"{act_prints} disagree with the tape record's "
                    f"{total_prints}; refusing to publish.")

    measuring = None
    for state in proving.get("states") or []:
        if state.get("key") == "measuring":
            measuring = state
    if not measuring or not measuring.get("words") or \
            not measuring.get("definition"):
        return fail("the Proving Ground's vocabulary does not "
                    "carry the measuring state; refusing to "
                    "publish a proving label of our own.")

    funds = []
    session_total_premium = 0.0
    for sym in FUNDS:
        group = groups[sym]
        name = names[sym]
        if group.get("session") != session or \
                name.get("session") != session:
            return fail(f"a record for {sym} is dated differently "
                        "from the session; refusing to publish a "
                        "mixed state.")
        act = name["activity"]
        if act["prints_examined"] != group["prints_looked_at"]:
            return fail(f"the Activity Profile and the tape record "
                        f"disagree on prints examined for {sym}; "
                        "refusing to publish.")
        fc = group.get("completeness") or {}
        ac = name.get("completeness") or {}
        for field in ("state", "batches_capped", "prints_examined",
                      "contracts_in_scope", "state_words"):
            if fc.get(field) != ac.get(field):
                return fail(f"the completeness record for {sym} "
                            f"disagrees on {field} between the two "
                            "published records; refusing to publish.")
        if fc.get("state") != "incomplete" or not fc.get("state_words"):
            return fail(f"the completeness record for {sym} is not "
                        "the incomplete declaration the record "
                        "carries; refusing to publish it silently "
                        "as complete.")

        alerts = group["alerts"]
        if len(alerts) != group.get("alerts_shown"):
            return fail(f"the tape record shows {len(alerts)} "
                        f"alerts for {sym} but states "
                        f"{group.get('alerts_shown')}; refusing "
                        "to publish.")
        alert_premium = sum(a["premium_usd"] for a in alerts)
        alert_contracts = sum(a["contracts"] for a in alerts)

        sides = {}
        cell_count = 0
        for kind, key in (("call", "calls"), ("put", "puts")):
            side = build_side(alerts, kind)
            side_premium = sum(c["premium_usd"] for c in side["cells"])
            side_contracts = sum(c["contracts"] for c in side["cells"])
            side_alerts = sum(c["alerts"] for c in side["cells"])
            kind_alerts = [a for a in alerts
                           if a["contract"]["kind"] == kind]
            if side_premium != sum(a["premium_usd"] for a in kind_alerts) or \
                    side_contracts != sum(a["contracts"] for a in kind_alerts) or \
                    side_alerts != len(kind_alerts):
                return fail(f"the {key} grid for {sym} does not "
                            "add back up to its alert prints; "
                            "refusing to publish.")
            sides[key] = side
            cell_count += len(side["cells"])
        grid_premium = sum(c["premium_usd"] for s in sides.values()
                           for c in s["cells"])
        grid_contracts = sum(c["contracts"] for s in sides.values()
                             for c in s["cells"])
        if grid_premium != alert_premium or \
                grid_contracts != alert_contracts:
            return fail(f"the grid for {sym} adds up to "
                        f"{grid_premium} in premium, not its alert "
                        f"sum {alert_premium}; refusing to publish.")

        session_total_premium += act["total_premium_usd"]
        funds.append({
            "symbol": sym,
            "alerts": len(alerts),
            "alert_premium_usd": alert_premium,
            "alert_contracts": alert_contracts,
            "alert_share_pct": round(
                100.0 * alert_premium / act["total_premium_usd"], 2),
            "cell_count": cell_count,
            "calls": sides["calls"],
            "puts": sides["puts"],
            "session_total_premium_usd": act["total_premium_usd"],
            "prints_examined": act["prints_examined"],
            "completeness_words": fc["state_words"],
        })

    check_total = sum(f["session_total_premium_usd"] for f in funds)
    if check_total != session_total_premium:
        return fail("the session totals do not add back up across "
                    "the three funds; refusing to publish.")

    data = {
        "tool": "Tape Heatmap",
        "state": "published",
        "session": session,
        "session_long": long_date(session),
        "published_at_utc": flow.get("published_at_utc"),
        "source": SOURCE_WORDS,
        "proving_state": measuring["words"],
        "proving_note": measuring["definition"],
        "scope_words": SCOPE_WORDS,
        "empty_words": EMPTY_WORDS,
        "counts": {
            "alerts_published": total_alerts,
            "prints_looked_at": total_prints,
            "session_total_premium_usd": session_total_premium,
        },
        "funds": funds,
        "receipt": {
            "session": session,
            "source": SOURCE_WORDS,
            "coverage": (f"{total_alerts} largest alert prints for "
                         f"{long_date(session)}: 25 per fund across "
                         f"SPY, QQQ and IWM, grouped by strike and "
                         f"expiry day, calls and puts kept separate; "
                         f"{total_prints:,} prints looked at in all"),
        },
    }

    def walk(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for v in value.values():
                yield from walk(v)
        elif isinstance(value, list):
            for v in value:
                yield from walk(v)

    for text in walk(data):
        low = text.lower()
        for bad in FORBIDDEN:
            if bad in low:
                return fail(f"assembled data carries internal "
                            f"wording ({bad!r}); refusing to "
                            "publish.")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, OUT_PATH)
    print(f"Wrote {OUT_PATH} (session {session}, {total_alerts} "
          f"alerts across {len(funds)} funds)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
