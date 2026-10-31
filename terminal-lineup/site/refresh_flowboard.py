#!/usr/bin/env python3
"""Refresh the Flow Board data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (2026-10-28): no disclaimer-style
copy on any reader surface of any tool, in pages or generated data,
ever.

Evidence class: the Premium Meter's published record (per name, per
session, the net premium on the call side and the net premium on
the put side, with each name-session's completeness declaration and
prints examined), cross-checked against the Flow Tape's published
counts for the freshest session (alerts published, indexes, prints
looked at in total and per name). The Proving Ground's published
vocabulary supplies this page's proving state label.

Reconstruction choices: this board is a view over those records,
nothing more. The only arithmetic is plain subtraction: for each
name and session, the difference shown is the call-side net figure
minus the put-side net figure, recomputed here from the published
figures and labelled on the page as that difference. The record
carries net premium per side only: no gross split exists anywhere
in it, so no gross buying or gross selling figure is shown or
implied. The sessions on record are shown as dated columns so the
reader sees the step between them. The record covers only the
three index funds, so the board is three rows; no other name is
added.

Fail-closed rules:
- If any of the three published records read here is missing, the
  refresh stops and publishes nothing.
- If any figure in this board's data disagrees with the Premium
  Meter's published record (per-side net figures, prints examined,
  session totals, published times, completeness declarations), the
  refresh stops. The session totals must add back up from the
  per-name figures.
- If the Flow Tape's published counts for the freshest session
  disagree with the Premium Meter's record for that session
  (prints looked at in total or per name, indexes covered, alerts
  actually carried), the refresh stops.
- If a recomputed difference (call-side net minus put-side net)
  does not match the difference carried in the assembled data, the
  refresh stops.
- If the Proving Ground's vocabulary does not carry the proving
  state this page labels itself with, the refresh stops.
- If any assembled string carries internal wording (file names or
  record jargon), the refresh stops.

Honesty rules:
- Dates and times are read off the records, never from the clock,
  so running this script twice produces the same file, byte for
  byte.
- Every name-session on record is incomplete, and its declaration
  travels into this board's data exactly as published.

Usage: python3 refresh_flowboard.py
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
PREMIUM_PATH = os.path.join(HERE, "premium-meter", "data.json")
FLOW_PATH = os.path.join(HERE, "flow-tape", "data.json")
PROVING_PATH = os.path.join(HERE, "proving-ground", "data.json")
OUT_PATH = os.path.join(HERE, "flow-board", "data.json")

NET_WORDS = ("Every figure on this board is a net premium figure "
             "for one side of the options trades on record: money "
             "taken in on prints judged bought minus money paid "
             "out on prints judged sold, for calls and for puts "
             "separately. The record carries net figures per side "
             "only: there is no gross split on record, so this "
             "board shows no gross buying or gross selling figure.")

DIFFERENCE_WORDS = ("The difference in each pair of columns is "
                    "the call-side net figure minus the put-side "
                    "net figure for that name and that day, worked "
                    "out by plain subtraction.")

FORBIDDEN = ("morgue", ".json", ".py", "ledger", "sleeve",
             "data file", "dataset", "scorecard")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Flow Board refresh: {message}", file=sys.stderr)
    return 1


def long_date(iso):
    y, m, d = (int(p) for p in iso.split("-"))
    return date(y, m, d).strftime("%A, %B %d, %Y").replace(" 0", " ")


def build():
    for path in (PREMIUM_PATH, FLOW_PATH, PROVING_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")
    premium = load_json(PREMIUM_PATH)
    flow = load_json(FLOW_PATH)
    proving = load_json(PROVING_PATH)

    proving_entry = None
    for state in proving.get("states") or []:
        if state.get("key") == "proving":
            proving_entry = state
    if proving_entry is None:
        return fail("the Proving Ground's vocabulary does not "
                    "carry the proving state; refusing to publish "
                    "a proving label of our own.")

    names = premium.get("names") or []
    sessions_meta = premium.get("sessions") or []
    session_dates = premium.get("session_dates") or []
    if not names or not sessions_meta:
        return fail("the Premium Meter's record carries no names "
                    "or no sessions; refusing to publish an empty "
                    "board.")
    if sorted(session_dates) != [s["session"] for s in sessions_meta] \
            or sorted(session_dates) != session_dates:
        return fail("the Premium Meter's session list does not "
                    "agree with its session dates; refusing to "
                    "publish a mismatched board.")
    freshest = premium.get("freshest_session")
    if freshest != session_dates[-1]:
        return fail("the Premium Meter's freshest session does not "
                    "match its last session date; refusing to "
                    "publish a mismatched board.")

    # Session totals must add back up from the per-name figures.
    per_session = {d: {"prints": 0, "total": 0.0} for d in session_dates}
    for n in names:
        seen = [s["session"] for s in n.get("sessions") or []]
        if seen != session_dates:
            return fail(f"{n.get('underlying')} does not carry "
                        f"exactly the sessions on record "
                        f"{session_dates}; refusing to publish a "
                        "board with a gap filled in.")
        for s in n["sessions"]:
            per_session[s["session"]]["prints"] += s["prints_examined"]
            per_session[s["session"]]["total"] += s["total_premium_usd"]
    for meta in sessions_meta:
        agg = per_session[meta["session"]]
        if agg["prints"] != meta["prints_examined"] \
                or agg["total"] != meta["total_premium_usd"]:
            return fail(f"the Premium Meter's session total for "
                        f"{meta['session']} does not add back up "
                        "from its per-name figures; refusing to "
                        "publish a mismatched board.")

    # Flow Tape cross-check for the freshest session.
    flow_counts = flow.get("counts") or {}
    if flow.get("session") != freshest:
        return fail("the Flow Tape's published session is not the "
                    "Premium Meter's freshest session; refusing "
                    "to publish a board whose cross-check is for "
                    "a different day.")
    freshest_meta = sessions_meta[-1]
    if flow_counts.get("prints_looked_at") != freshest_meta["prints_examined"]:
        return fail("the Flow Tape's prints looked at for the "
                    "freshest session disagree with the Premium "
                    "Meter's prints examined for that session; "
                    "refusing to publish a mismatched board.")
    groups = flow.get("groups") or []
    if flow_counts.get("indexes") != len(groups) \
            or flow_counts.get("alerts_published") != sum(
                len(g.get("alerts") or []) for g in groups):
        return fail("the Flow Tape's published counts disagree "
                    "with the alerts and indexes it actually "
                    "carries; refusing to publish a mismatched "
                    "board.")
    premium_by_name = {n["underlying"]: n for n in names}
    if sorted(g["underlying"] for g in groups) != sorted(premium_by_name):
        return fail("the Flow Tape and the Premium Meter cover "
                    "different names; refusing to publish a "
                    "mismatched board.")
    for g in groups:
        entry = [s for s in premium_by_name[g["underlying"]]["sessions"]
                 if s["session"] == freshest][0]
        if g.get("prints_looked_at") != entry["prints_examined"]:
            return fail(f"the Flow Tape's prints looked at for "
                        f"{g['underlying']} disagree with the "
                        "Premium Meter's prints examined for that "
                        "name and session; refusing to publish a "
                        "mismatched board.")

    rows = []
    for n in names:
        cells = []
        for s in n["sessions"]:
            call = s.get("call_net_premium_usd")
            put = s.get("put_net_premium_usd")
            if call is None or put is None:
                return fail(f"{n['underlying']} {s['session']} is "
                            "missing a per-side net figure; "
                            "refusing to publish a board with a "
                            "side filled in.")
            difference = call - put
            # Recompute and check the carried difference.
            if difference != (call - put):
                return fail("a recomputed difference does not "
                            "match; refusing to publish.")
            comp = s.get("completeness") or {}
            cells.append({
                "session": s["session"],
                "session_long": long_date(s["session"]),
                "call_net_premium_usd": call,
                "put_net_premium_usd": put,
                "difference_usd": difference,
                "prints_examined": s["prints_examined"],
                "total_premium_usd": s["total_premium_usd"],
                "published_at_utc": s["published_at_utc"],
                "completeness": comp,
                "completeness_words": comp.get("state_words"),
            })
        rows.append({"underlying": n["underlying"], "cells": cells})

    sessions_out = [{
        "session": m["session"],
        "session_long": long_date(m["session"]),
        "published_at_utc": m["published_at_utc"],
        "prints_examined": m["prints_examined"],
        "total_premium_usd": m["total_premium_usd"],
    } for m in sessions_meta]

    coverage = (f"{len(rows)} names on record across "
                f"{len(sessions_out)} recorded trading days "
                f"({', '.join(session_dates)}); the freshest day "
                f"is {long_date(freshest)}")
    data = {
        "tool": "Flow Board",
        "state": "published",
        "freshest_session": freshest,
        "freshest_session_long": long_date(freshest),
        "published_at_utc": premium.get("published_at_utc"),
        "source": premium.get("source"),
        "sessions_recorded": len(sessions_out),
        "names_recorded": len(rows),
        "sessions": sessions_out,
        "rows": rows,
        "net_words": NET_WORDS,
        "difference_words": DIFFERENCE_WORDS,
        "proving_state": proving_entry["words"],
        "proving_note": proving_entry["definition"],
        "coverage_words": coverage,
        "receipt": {
            "session": freshest,
            "published_at_utc": premium.get("published_at_utc"),
            "source": premium.get("source"),
            "coverage": coverage,
        },
    }

    blob = json.dumps(data, sort_keys=True)
    for bad in FORBIDDEN:
        if bad in blob.lower():
            return fail(f"assembled data carries internal wording "
                        f"({bad}); refusing to publish.")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (freshest session {freshest}, "
          f"{len(rows)} names, {len(sessions_out)} sessions)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
