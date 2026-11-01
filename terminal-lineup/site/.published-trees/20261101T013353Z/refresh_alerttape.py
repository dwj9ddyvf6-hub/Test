#!/usr/bin/env python3
"""Refresh the Alert Tape data file.

Reads the tape records this site already publishes: the Flow Tape's
published alerts for its session, and the Golden Sweep Wire's
published session coverage (which sessions were recorded and how
many prints were looked at in each), and writes
site/alert-tape/data.json in the shape the Alert Tape page renders.

What the sources carry (and what this script therefore shows):
- The Flow Tape keeps, for its one session on record, the 25
  largest alerts for each of the three index funds: 75 alerts.
  The full prints were not retained, so the archive is those kept
  alerts only, never every alert that fired.
- The Wire's coverage names every recorded session and how many
  prints were looked at in each. A recorded session whose alert
  list the published tape does not keep is carried as coverage
  with no alerts kept for it, in plain words; it is never filled
  in and never read as a session with no alerts.
- What happened after each alert is limited to what the record
  carries: the Flow Tape's own grading state, that the alerts are
  not yet graded. No outcome is attached to any alert.

Fails closed:
- If the archive built here disagrees with the Flow Tape's
  published alert count, or any fund's alert count disagrees with
  the count its published group declares, the refresh stops.
- If the session coverage built here disagrees with the Wire's
  published coverage (its sessions, the prints looked at in each,
  or its freshest session), the refresh stops.
- If the Flow Tape's session is not one of the Wire's recorded
  sessions, or the prints looked at for that session disagree
  between the two records, the refresh stops.

Honesty rules:
- Sessions and times are read off the sources, never from the
  clock, so running this script twice produces the same file.
- Every figure on an alert is carried exactly as published.

Usage: python3 refresh_alerttape.py
"""

import json
import os
import sys

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
FLOW_PATH = os.path.join(HERE, "flow-tape", "data.json")
WIRE_PATH = os.path.join(HERE, "golden-sweep-wire", "data.json")
OUT_PATH = os.path.join(HERE, "alert-tape", "data.json")

UNDERLYINGS = ["SPY", "QQQ", "IWM"]

SOURCE_WORDS = ("Every options trade printed on the three big "
                "index funds during the trading day, scored "
                "print by print as it came in; this page keeps "
                "the largest alerts that record published")

PROVING_STATE = "A measuring tool, nothing to prove"
PROVING_NOTE = ("The tool only reports, filters, calculates or "
                "counts from records on file; it makes no "
                "forecast claim of its own, so there is nothing "
                "to grade.")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Alert Tape refresh: {message}", file=sys.stderr)
    return 1


def build():
    for path in (FLOW_PATH, WIRE_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    flow = load_json(FLOW_PATH)
    wire = load_json(WIRE_PATH)

    flow_session = flow.get("session")
    groups = flow.get("groups") or []
    if sorted(g.get("underlying") for g in groups) != sorted(UNDERLYINGS):
        return fail("the published tape does not cover the three "
                    "index funds; refusing to publish a partial "
                    "archive.")
    if any(g.get("session") != flow_session for g in groups):
        return fail("a published tape group names a different "
                    "session than the tape itself; refusing to "
                    "publish a mismatched archive.")

    # --- Flatten the archive, exactly as published. ---
    alerts = []
    per_fund_completeness = []
    for g in groups:
        if g.get("alerts_shown") != len(g.get("alerts") or []):
            return fail(f"the published tape says it shows "
                        f"{g.get('alerts_shown')} {g['underlying']} "
                        f"alerts but lists "
                        f"{len(g.get('alerts') or [])}; refusing to "
                        "publish a mismatched archive.")
        per_fund_completeness.append({
            "underlying": g["underlying"],
            "alerts_kept": len(g["alerts"]),
            "prints_looked_at": g["prints_looked_at"],
            "completeness": g.get("completeness"),
            "coverage": (g.get("receipt") or {}).get("coverage"),
        })
        for a in g["alerts"]:
            alerts.append({
                "session": flow_session,
                "underlying": g["underlying"],
                "time_utc": a["time_utc"],
                "contract_code": a["contract_code"],
                "contract": a["contract"],
                "price_per_contract": a["price_per_contract"],
                "contracts": a["contracts"],
                "premium_usd": a["premium_usd"],
                "heat_score": a["heat_score"],
                "band": a["band"],
                "golden_sweep": a["golden_sweep"],
                "unusual": a["unusual"],
                "side_words": a["side_words"],
                "direction": a["direction"],
                "direction_words": a["direction_words"],
                "grading_words": "Not yet graded",
            })
    published_count = (flow.get("counts") or {}).get("alerts_published")
    if len(alerts) != published_count:
        return fail(f"the archive holds {len(alerts)} alerts but "
                    f"the published tape's count is "
                    f"{published_count}; refusing to publish a "
                    "mismatched archive.")
    if sum(g["prints_looked_at"] for g in groups) != \
            (flow.get("counts") or {}).get("prints_looked_at"):
        return fail("the published tape's per-fund prints do not "
                    "add up to its published total; refusing to "
                    "publish a mismatched archive.")

    # --- Session coverage, exactly as the Wire publishes it. ---
    wire_sessions = wire.get("sessions") or []
    coverage = []
    for s in wire_sessions:
        kept = len(alerts) if s["session"] == flow_session else 0
        coverage.append({
            "session": s["session"],
            "published_at_utc": s["published_at_utc"],
            "prints_looked_at": s["prints_looked_at"],
            "alerts_kept": kept,
            "alert_list_kept": s["session"] == flow_session,
            "completeness": s.get("completeness"),
            "coverage": (s.get("receipt") or {}).get("coverage"),
        })
    coverage.sort(key=lambda s: s["session"])
    if (wire.get("counts") or {}).get("sessions_recorded") != len(coverage):
        return fail("the Wire's published session count disagrees "
                    "with the sessions it lists; refusing to "
                    "publish mismatched coverage.")
    if wire.get("freshest_session") != flow_session:
        return fail(f"the Wire's freshest recorded session is "
                    f"{wire.get('freshest_session')} but the "
                    f"published tape's session is {flow_session}; "
                    "refusing to publish a mismatched archive.")
    match = [s for s in coverage if s["session"] == flow_session]
    if len(match) != 1:
        return fail("the published tape's session is not one of "
                    "the sessions the Wire's coverage names; "
                    "refusing to publish a mismatched archive.")
    if match[0]["prints_looked_at"] != \
            (flow.get("counts") or {}).get("prints_looked_at"):
        return fail("the Wire says "
                    f"{match[0]['prints_looked_at']:,} prints were "
                    f"looked at in the tape's session but the tape "
                    f"says {(flow.get('counts') or {}).get('prints_looked_at'):,}; "
                    "refusing to publish a mismatched archive.")

    alerts.sort(key=lambda a: (a["session"], a["underlying"],
                               -a["premium_usd"]))

    scope_words = (
        f"Alert records are kept for 1 session: the session of "
        f"{flow_session}. This archive holds {len(alerts)} alerts: "
        f"the 25 largest alerts for each of SPY, QQQ and IWM for "
        f"that session. The full prints were not retained, so this "
        f"is the kept alerts only, not every alert that fired. The "
        f"tape record names {len(coverage)} recorded sessions in "
        f"all; for the other recorded session it keeps how many "
        f"prints were looked at, but no alert list. Earlier "
        f"sessions and sessions that were not recorded are not in "
        f"this archive.")

    data = {
        "tool": "Alert Tape",
        "freshest_session": flow_session,
        "published_at_utc": flow.get("published_at_utc"),
        "source": SOURCE_WORDS,
        "proving_state": PROVING_STATE,
        "proving_note": PROVING_NOTE,
        "grading_note": flow.get("grading_note"),
        "scope_words": scope_words,
        "counts": {
            "alerts_in_archive": len(alerts),
            "sessions_with_alert_records": 1,
            "alert_session": flow_session,
            "sessions_recorded": len(coverage),
            "alerts_per_fund": 25,
            "funds": len(groups),
        },
        "coverage": coverage,
        "per_fund": per_fund_completeness,
        "alerts": alerts,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} ({len(alerts)} alerts kept for "
          f"session {flow_session}, {len(coverage)} recorded "
          f"sessions in coverage, published "
          f"{flow.get('published_at_utc')})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
