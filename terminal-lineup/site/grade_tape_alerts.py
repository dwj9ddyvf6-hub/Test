#!/usr/bin/env python3
"""Grade the tape family's published alerts (G7 grading, 2026-10-29).

Every flow alert carried "not yet graded". This pass grades what
the machinery on hand can grade, with a stated rule, and names the
rest ungraded rather than grading it by a weaker rule:

- Cohort: every tape-alert row in the morgue permanent log
  (morgue/output/ledger.jsonl), grouped by session.
- Rule: an alert's direction is its published sentiment. The
  outcome is the underlying's close-to-close move from the alert
  session to the NEXT session (Alpaca SIP daily bars, start always
  passed): bullish grades a hit when the move is up, bearish when
  down, neutral never grades. A same-session or missing next bar
  leaves the alert ungraded with the reason counted.
- Output: site/flow-tape/grades.json (per session: alerts, graded,
  hits, hit share, ungraded by reason) plus the alert cohorts'
  mean next-session move for bullish vs bearish alerts. This is a
  one-horizon descriptive grade, not a proven edge: counts under
  30 graded print counts only, no rate claim (the terminal's
  thin-cell rule).

Usage: python3 grade_tape_alerts.py
"""

import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.expanduser("~/workspace/morgue/output/ledger.jsonl")
OUT_PATH = os.path.join(HERE, "flow-tape", "grades.json")
sys.path.insert(0, os.path.expanduser("~/workspace/morgue"))
sys.path.insert(0, os.path.expanduser(
    "~/workspace/custom-skills/local-alpaca-paper/bin"))
from alpaca_lib import api_request  # noqa: E402

DATA = "https://data.alpaca.markets"
UNDERLYINGS = ["SPY", "QQQ", "IWM"]


def grade_move(sentiment, move):
    """Pure grading rule: (sentiment, next-session move) -> hit/None."""
    if sentiment == "bullish":
        return move > 0
    if sentiment == "bearish":
        return move < 0
    return None


def daily_closes(symbol, start, end):
    # No explicit end: an end date at/after the current session
    # makes the SIP query "recent" and this subscription refuses it
    # (403, proven 2026-10-29); tape_card's fetch_52wk shape (start
    # only) is the proven route.
    resp = api_request("GET", f"{DATA}/v2/stocks/{symbol}/bars",
                       params={"timeframe": "1Day", "start": start,
                               "limit": 1000, "feed": "sip"})
    out = {}
    token = resp.get("next_page_token")
    bars = resp.get("bars") or []
    while token:
        resp = api_request("GET", f"{DATA}/v2/stocks/{symbol}/bars",
                           params={"timeframe": "1Day", "start": start,
                                   "limit": 1000, "feed": "sip",
                                   "page_token": token})
        bars += resp.get("bars") or []
        token = resp.get("next_page_token")
    for b in bars:
        out[b["t"][:10]] = b["c"]
    return out


def main():
    rows = [json.loads(l) for l in open(LOG_PATH) if l.strip()]
    alerts = [r for r in rows if r.get("component") == "tape-alert"]
    # Deduplicate repeated runs of the same session: the freshest
    # run per session wins (later log rows supersede earlier ones
    # for the same minute-run grouping used by the consumers).
    by_session = defaultdict(list)
    for r in alerts:
        by_session[r["value"]["ts"][:10]].append(r)
    sessions = sorted(by_session)
    closes = {}
    for u in UNDERLYINGS:
        # SIP refuses a window that is only recent data on this
        # subscription (403, proven 2026-10-29); the window starts
        # weeks back, the same shape tape_card's 52-week fetch uses.
        closes[u] = daily_closes(u, "2026-09-01", "2026-11-05")
    out_sessions = {}
    tot = Counter()
    dir_moves = defaultdict(list)
    for s in sessions:
        # one run per session: take alerts from the last run minute
        runs = defaultdict(list)
        for r in by_session[s]:
            runs[r["ts_utc"][:16]].append(r)
        run = runs[max(runs)]
        graded = hits = 0
        ungraded = Counter()
        for r in run:
            a = r["value"]
            u = r["name"]
            series = sorted(closes.get(u, {}).items())
            days = [d for d, _ in series]
            if s not in closes.get(u, {}):
                ungraded["no_close_for_alert_session"] += 1
                continue
            nxt = [d for d in days if d > s]
            if not nxt:
                ungraded["next_session_close_not_yet_available"] += 1
                continue
            move = closes[u][nxt[0]] / closes[u][s] - 1.0
            hit = grade_move(a["sentiment"], move)
            if hit is None:
                ungraded["neutral_direction_never_grades"] += 1
                continue
            graded += 1
            hits += 1 if hit else 0
            dir_moves[a["sentiment"]].append(move)
            tot["graded"] += 1
            tot["hits"] += 1 if hit else 0
        out_sessions[s] = {
            "alerts": len(run), "graded": graded, "hits": hits,
            "hit_share": (round(hits / graded, 3) if graded >= 30
                          else None),
            "hit_share_state": ("shown" if graded >= 30 else
                                "counts_only_under_30_graded"),
            "ungraded_by_reason": dict(ungraded),
        }
        tot["alerts"] += len(run)
    doc = {
        "tool": "Flow Tape alert grades",
        "rule": "alert sentiment vs the underlying's close-to-close "
                "move to the next session (Alpaca SIP daily bars)",
        "sessions": out_sessions,
        "totals": {"alerts": tot["alerts"], "graded": tot["graded"],
                   "hits": tot["hits"],
                   "hit_share": (round(tot["hits"] / tot["graded"], 3)
                                 if tot["graded"] >= 30 else None)},
        "mean_next_session_move": {
            k: round(sum(v) / len(v), 5) for k, v in dir_moves.items()
            if v},
        "note": "One-horizon descriptive grade of the published "
                "alert rule, not a proven edge. Sessions whose next "
                "close does not exist yet stay ungraded by name.",
    }
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH}: {tot['alerts']} alerts, "
          f"{tot['graded']} graded, {tot['hits']} hits")
    return 0


if __name__ == "__main__":
    sys.exit(main())
