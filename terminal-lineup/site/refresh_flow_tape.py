#!/usr/bin/env python3
"""Refresh the Flow Tape data file.

Reads the real published tape (the daily card that scores every
options print on SPY, QQQ and IWM and lists its largest alerts),
cross-checked against the published feed's tape figures and against
the permanent log, which recorded the same card and the same alerts
before the card was written, and writes site/flow-tape/data.json in
the shape the Flow Tape page renders.

What the sources carry (and what this script therefore shows):
- For each of the three indexes, the card lists the 25 largest
  alerts of the session: prints whose heat score reached the high
  heat band, plus any golden sweeps. Each alert carries the moment
  it printed, the contract, the price per contract, how many
  contracts changed hands, the total premium, its heat score, which
  side of the market it hit, the direction that read implies, and
  whether it was a golden sweep or carried the unusual tag.
- The card also states its own coverage: how many prints it looked
  at, how many contracts were in scope, and how many busy contract
  groups hit the reading limit, which can leave some prints in
  those groups unread. That limit is carried onto the page, never
  hidden.
- Completeness discipline (adopted from Codex's Bullflow activity
  profile, evaluation 05 section 2 item 2): every index group in
  data.json carries an explicit per-index completeness declaration
  computed from the card's own fields: prints examined, contracts
  in scope, batches capped as a named incomplete state, and an
  overall state of complete, incomplete (with the reason named),
  or undeclared when the card does not carry the fields. No group
  is ever silently complete. The page receipt already states the
  capped batches in plain words, so the declaration lives in
  data.json (on the group and inside its receipt) and the page
  text is left unchanged.
- The feed repeats the card's headline figures per index (prints,
  total and net premium, golden sweeps, high heat count, average
  heat, and the three largest alerts). The log holds the identical
  card and the identical alert list from the same run. If the card,
  the feed and the log disagree on any of these, the refresh fails
  instead of publishing a mismatched page.

Honesty rules:
- The session is read off the card's own window and the alert
  times, never from the clock. All timestamps come from the
  sources, so running this script twice produces the same file.
- The contract description on the page (call or put, strike,
  expiry) is read straight out of the contract code the source
  carries; a code that does not parse stops the refresh.
- Tape alerts are not graded by the scorecard yet. The data file
  says so in plain words, and the page prints that line where a
  track record would otherwise be implied.

Usage: python3 refresh_flow_tape.py
"""

import json
import os
import re
import sys
from collections import Counter

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.expanduser("~/workspace/morgue/output")
CARD_PATH = os.path.join(SOURCE_DIR, "tape_card.json")
FEED_PATH = os.path.join(SOURCE_DIR, "morgue-feed.json")
LOG_PATH = os.path.join(SOURCE_DIR, "ledger.jsonl")
OUT_PATH = os.path.join(HERE, "flow-tape", "data.json")

UNDERLYINGS = ["SPY", "QQQ", "IWM"]
HIGH_HEAT = 15  # the published high heat band: a print alerts at this score

SIDE_WORDS = {
    "ask": "Bought at the asking price",
    "above_ask": "Bought above the asking price",
    "bid": "Sold at the bidding price",
    "below_bid": "Sold below the bidding price",
    "mid": "Traded between the bid and the ask",
    "unknown": "Side not clear from the latest quote",
}

DIRECTION_WORDS = {
    "bullish": "points up",
    "bearish": "points down",
    "neutral": "no clear direction",
}

OCC_RE = re.compile(r"^([A-Z]+)(\d{2})(\d{2})(\d{2})([CP])(\d{8})$")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_log(path):
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def fail(message):
    print(f"Flow Tape refresh: {message}", file=sys.stderr)
    return 1


def describe_contract(symbol, underlying):
    """Read call/put, strike and expiry out of the contract code.

    Returns None when the code does not parse as this underlying's
    contract, so the refresh can stop instead of guessing.
    """
    m = OCC_RE.match(symbol or "")
    if not m or m.group(1) != underlying:
        return None
    yy, mm, dd = int(m.group(2)), int(m.group(3)), int(m.group(4))
    strike = int(m.group(6)) / 1000.0
    return {
        "kind": "call" if m.group(5) == "C" else "put",
        "strike": strike,
        "expiry": f"20{yy:02d}-{mm:02d}-{dd:02d}",
    }


def completeness_declaration(prints, contracts_in_scope,
                             batches_capped):
    """Explicit completeness declaration from the card's own fields.

    Adopted Bullflow discipline: capped batches are a named
    incomplete state, never a silent shortfall, and missing source
    fields are an undeclared state, never an assumed complete.
    """
    if prints is None or contracts_in_scope is None \
            or batches_capped is None:
        return {
            "prints_examined": prints,
            "contracts_in_scope": contracts_in_scope,
            "batches_capped": batches_capped,
            "state": "undeclared",
            "reason": ("the card does not declare prints examined, "
                       "contracts in scope and batches capped, so "
                       "completeness is not claimed"),
            "state_words": ("Not declared: the card does not say "
                            "how complete this reading is, so no "
                            "completeness is claimed"),
        }
    if batches_capped:
        reason = (f"{batches_capped} very busy contract groups hit "
                  "the reading limit, so some prints in those "
                  "groups may be missing")
        return {
            "prints_examined": prints,
            "contracts_in_scope": contracts_in_scope,
            "batches_capped": batches_capped,
            "state": "incomplete",
            "reason": reason,
            "state_words": f"Incomplete: {reason}",
        }
    return {
        "prints_examined": prints,
        "contracts_in_scope": contracts_in_scope,
        "batches_capped": batches_capped,
        "state": "complete",
        "reason": None,
        "state_words": ("Complete: every print in scope was "
                        "examined; no contract group hit the "
                        "reading limit"),
    }


GRADES_PATH = os.path.join(HERE, "flow-tape", "grades.json")


def grading_note_text():
    """The alerts' grading state, from the grading pass's own
    record (grade_tape_alerts.py) when it exists. The static
    not-graded text was true only until the first grading pass
    landed (cure stream D); stating it after that mislabelled
    the page (hookup cure, 2026-10-29)."""
    try:
        with open(GRADES_PATH, encoding="utf-8") as fh:
            grades = json.load(fh)
        sessions = grades.get("sessions") or {}
        graded = sum(s.get("graded", 0) for s in sessions.values())
        total = sum(s.get("alerts", 0) for s in sessions.values())
        hits = sum(s.get("hits", 0) for s in sessions.values())
    except (OSError, ValueError):
        graded = 0
    if not graded:
        return ("These alerts are published by the rule "
                "above and every one of them is kept on the "
                "public record, but they have not been "
                "graded yet: nothing has checked what "
                "happened after each alert. Grading is to "
                "follow.")
    return (f"These alerts are published by the rule above and "
            f"every one of them is kept on the public record. "
            f"Grading has landed for the sessions whose next "
            f"close exists: {graded} of {total} logged alerts "
            f"graded so far, {hits} of them in the direction "
            f"the alert pointed. The freshest session's alerts "
            f"grade after the next close.")


def build():
    for path in (CARD_PATH, FEED_PATH, LOG_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    card_doc = load_json(CARD_PATH)
    feed = load_json(FEED_PATH)
    log_rows = load_log(LOG_PATH)

    published_at = card_doc["generated_at_utc"]
    cards = {c["underlying"]: c for c in card_doc["cards"]}
    if sorted(cards) != sorted(UNDERLYINGS):
        return fail(f"the tape card covers {sorted(cards)}, not the "
                    f"three indexes {UNDERLYINGS}; refusing to "
                    "publish a partial tape.")

    # --- The session, from the card's own window. ---
    sessions = set()
    for c in cards.values():
        window_start = c["window"].split(" -> ")[0]
        sessions.add(window_start[:10])
    if len(sessions) != 1:
        return fail(f"the three index cards name different sessions "
                    f"{sorted(sessions)}; refusing to publish a "
                    "mismatched page.")
    session = sessions.pop()
    if published_at[:10] != session:
        return fail(f"the tape was published on {published_at[:10]} "
                    f"but its window is the session of {session}; "
                    "refusing to publish a mismatched page.")
    for c in cards.values():
        for a in c["alerts"]:
            if a["ts"][:10] != session:
                return fail(f"an alert on {c['underlying']} printed "
                            f"on {a['ts'][:10]}, outside the session "
                            f"{session}; refusing to publish a "
                            "mismatched page.")

    # --- Cross-check the feed's tape figures against the card. ---
    feed_tape = {t["symbol"]: t for t in feed.get("tape", [])}
    if sorted(feed_tape) != sorted(UNDERLYINGS):
        return fail("the published feed's tape figures do not cover "
                    "the same three indexes as the card; refusing to "
                    "publish a mismatched page.")
    for u in UNDERLYINGS:
        c, t = cards[u], feed_tape[u]
        checks = [
            ("prints", t["prints"], c["prints"]),
            ("golden sweeps", t["golden_sweeps"], c["golden_sweeps"]),
            ("high heat prints", t["high_heat"], c["high_heat"]),
            ("average heat", t["mean_heat"], c["mean_heat"]),
            ("total premium (millions)",
             t["total_premium_m"], round(c["total_premium"] / 1e6, 1)),
            ("net premium (millions)",
             t["net_premium_m"], round(c["net_premium"] / 1e6, 1)),
        ]
        for label, got, want in checks:
            if got != want:
                return fail(f"the feed says {u} {label} is {got} but "
                            f"the card says {want}; refusing to "
                            "publish a mismatched page.")
        feed_top = [(a["contract"], a["premium"], a["heat"],
                     a["sentiment"], a["golden"])
                    for a in t["top_alerts"]]
        card_top = [(a["symbol"], a["premium"], a["heat"],
                     a["sentiment"], a["golden_sweep"])
                    for a in c["alerts"][:len(feed_top)]]
        if feed_top != card_top:
            return fail(f"the feed's largest {u} alerts do not match "
                        "the top of the card's alert list; refusing "
                        "to publish a mismatched page.")

    # --- Cross-check the log: the freshest tape run must hold the
    # identical card and the identical alerts. ---
    aggregates = [r for r in log_rows
                  if r.get("component") == "tape-aggregate"]
    if not aggregates:
        return fail("the permanent log holds no tape run at all; "
                    "refusing to show alerts that are not on the "
                    "record.")
    freshest = max(r["ts_utc"] for r in aggregates)
    run_start = min(r["ts_utc"] for r in aggregates
                    if r["ts_utc"][:16] == freshest[:16])
    run_cards = {r["name"]: r["value"] for r in aggregates
                 if r["ts_utc"] >= run_start}
    if sorted(run_cards) != sorted(UNDERLYINGS):
        return fail("the freshest tape run in the log does not cover "
                    "the same three indexes as the card; refusing to "
                    "publish a mismatched page.")
    for u in UNDERLYINGS:
        if run_cards[u] != cards[u]:
            return fail(f"the log's recorded {u} card differs from "
                        "the published card; refusing to publish a "
                        "mismatched page.")
    logged_alerts = [r for r in log_rows
                     if r.get("component") == "tape-alert"
                     and r["ts_utc"] >= run_start]
    for u in UNDERLYINGS:
        logged = Counter(json.dumps(r["value"], sort_keys=True)
                         for r in logged_alerts if r["name"] == u)
        on_card = Counter(json.dumps(a, sort_keys=True)
                          for a in cards[u]["alerts"])
        if logged != on_card:
            return fail(f"the log holds {sum(logged.values())} {u} "
                        f"alerts for this run but the card lists "
                        f"{sum(on_card.values())}, and they do not "
                        "match alert for alert; refusing to publish "
                        "a mismatched page.")

    # --- Build the page data, translating each alert plainly. ---
    source_words = ("Every options trade printed on the three big "
                    "index funds during the trading day, scored "
                    "print by print as it came in")
    groups = []
    total_alerts = 0
    total_prints = 0
    for u in UNDERLYINGS:
        c = cards[u]
        alerts = []
        for a in c["alerts"]:
            if a["side"] not in SIDE_WORDS:
                return fail(f"an alert on {u} carries a side this "
                            f"page cannot say plainly: {a['side']!r}; "
                            "refusing to guess.")
            if a["sentiment"] not in DIRECTION_WORDS:
                return fail(f"an alert on {u} carries a direction "
                            f"this page cannot say plainly: "
                            f"{a['sentiment']!r}; refusing to guess.")
            if not (a["golden_sweep"] or a["heat"] >= HIGH_HEAT):
                return fail(f"an alert on {u} reached neither the "
                            "high heat band nor the golden sweep "
                            "rule; refusing to publish an alert the "
                            "rule does not explain.")
            contract = describe_contract(a["symbol"], u)
            if contract is None:
                return fail(f"the contract code {a['symbol']!r} on "
                            f"{u} does not read as one of its own "
                            "contracts; refusing to guess at it.")
            alerts.append({
                "time_utc": a["ts"],
                "contract_code": a["symbol"],
                "contract": contract,
                "price_per_contract": a["price"],
                "contracts": a["size"],
                "premium_usd": a["premium"],
                "heat_score": a["heat"],
                "band": ("Golden sweep" if a["golden_sweep"]
                         else "High heat"),
                "golden_sweep": bool(a["golden_sweep"]),
                "unusual": bool(a["unusual"]),
                "side_words": SIDE_WORDS[a["side"]],
                "direction": a["sentiment"],
                "direction_words": DIRECTION_WORDS[a["sentiment"]],
            })
        coverage = (f"{c['prints']:,} prints looked at across "
                    f"{c['contracts_in_scope']:,} contracts; the "
                    f"{len(alerts)} largest alerts shown")
        if c["batches_capped"]:
            coverage += (f"; {c['batches_capped']} very busy "
                         "contract groups hit the reading limit, so "
                         "some prints in those groups may be missing")
        completeness = completeness_declaration(
            c.get("prints"), c.get("contracts_in_scope"),
            c.get("batches_capped"))
        groups.append({
            "underlying": u,
            "session": session,
            "receipt": {
                "session": session,
                "published_at_utc": published_at,
                "source": source_words,
                "coverage": coverage,
                "completeness": completeness,
            },
            "completeness": completeness,
            "prints_looked_at": c["prints"],
            "alerts_shown": len(alerts),
            "alerts": alerts,
        })
        total_alerts += len(alerts)
        total_prints += c["prints"]

    data = {
        "tool": "Flow Tape",
        "session": session,
        # Self-stamp (G7 residual cure, 2026-10-30): Flow Tape is the
        # tape source itself, so its tape_freshness is current by
        # construction. Writing it here, not only in
        # tape_family_run.py, means a standalone refresh of this
        # script can never silently strip the shared freshness stamp
        # the consumers are checked against.
        "tape_freshness": {
            "tape_session": session,
            "consumer_session": session,
            "state": "current",
            "note": "Flow Tape is the tape source itself; built "
                    "from the freshest tape session",
        },
        "published_at_utc": published_at,
        "source": source_words,
        "grading_note": grading_note_text(),
        "counts": {
            "alerts_published": total_alerts,
            "prints_looked_at": total_prints,
            "indexes": len(groups),
        },
        "groups": groups,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (session {session}, {total_alerts} "
          f"alerts across {len(groups)} indexes, {total_prints:,} "
          f"prints looked at, published {published_at})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
