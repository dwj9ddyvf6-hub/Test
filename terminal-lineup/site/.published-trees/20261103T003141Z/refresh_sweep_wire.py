#!/usr/bin/env python3
"""Refresh the Golden Sweep Wire data file.

Reads the real published tape (the daily card that scores every
options print on SPY, QQQ and IWM), cross-checked against the
published feed's tape figures and against the permanent log, which
recorded every tape run and every alert before the cards were
written, and writes site/golden-sweep-wire/data.json in the shape
the Golden Sweep Wire page renders.

What the sources carry (and what this script therefore shows):
- Every tape run in the log names its trading day. The distinct
  trading days are the recorded sessions of the wire's proving
  cohort: the wire needs 30 recorded sessions before it earns a
  verdict, and the decision is scheduled for 2026-12-08. Each
  session may have been run more than once in a day; the freshest
  run of the session is the session's record.
- Each run counts every golden sweep in its whole tape (a sweep
  whose size is at least the contract's whole open interest and
  whose premium is at least $1 million) and lists its largest
  alerts, golden sweeps among them. The golden prints on the wire
  are the golden alerts of each session's freshest run.
- If the card, the feed and the log disagree on any of this, the
  refresh fails instead of publishing a mismatched page. A run
  that counted more golden sweeps than its alert list carries
  also fails the refresh: the wire promises every golden print,
  so a count it cannot list in full is not published.

Completeness discipline (adopted from Codex's Bullflow activity
profile, evaluation 05 section 2 item 2): every session receipt in
data.json carries an explicit completeness declaration computed
from that session's own cards: prints examined, contracts in scope,
batches capped as a named incomplete state, an overall state of
complete, incomplete (with the reason named), or undeclared when a
card does not carry the fields, plus the same declaration per
index. A session whose reading was capped says so in its receipt
coverage as well as in the declaration; no session is ever
silently complete.

Honesty rules:
- Sessions and times are read off the sources, never from the
  clock. All timestamps come from the sources, so running this
  script twice produces the same file.
- The contract description on the page (call or put, strike,
  expiry) is read straight out of the contract code the source
  carries; a code that does not parse stops the refresh.
- Zero golden sweeps is a real state, not an error: golden sweeps
  are rare, and most sessions have none. The data file carries the
  true count, and the page says so in plain words.

Usage: python3 refresh_sweep_wire.py
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
OUT_PATH = os.path.join(HERE, "golden-sweep-wire", "data.json")

UNDERLYINGS = ["SPY", "QQQ", "IWM"]
SESSIONS_NEEDED = 30  # the recorded proving cohort for this wire
DECISION_DATE = "2026-12-08"  # the recorded decision date

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

SOURCE_WORDS = ("Every options trade printed on the three big "
                "index funds during the trading day, scored "
                "print by print as it came in")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_log(path):
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def fail(message):
    print(f"Golden Sweep Wire refresh: {message}", file=sys.stderr)
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
    """Explicit completeness declaration from a card's own fields.

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


def session_completeness(run_cards):
    """Session declaration: per-index declarations plus the whole.

    The session is complete only when every index is complete; any
    capped or undeclared index names the session's state.
    """
    by_index = []
    for u in UNDERLYINGS:
        card = run_cards[u]
        decl = completeness_declaration(
            card.get("prints"), card.get("contracts_in_scope"),
            card.get("batches_capped"))
        by_index.append({"underlying": u, **decl})

    def total(field):
        values = [d[field] for d in by_index]
        return None if any(v is None for v in values) else sum(values)

    overall = completeness_declaration(
        total("prints_examined"), total("contracts_in_scope"),
        total("batches_capped"))
    if any(d["state"] == "undeclared" for d in by_index):
        overall["state"] = "undeclared"
        overall["reason"] = ("at least one index card does not "
                             "declare its completeness fields, so "
                             "session completeness is not claimed")
        overall["state_words"] = ("Not declared: at least one index "
                                  "does not say how complete its "
                                  "reading is, so no completeness "
                                  "is claimed for the session")
    overall["by_index"] = by_index
    return overall


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
                    "publish a partial wire.")

    # --- The published card's session, from its own window. ---
    card_sessions = {c["window"].split(" -> ")[0][:10]
                     for c in cards.values()}
    if len(card_sessions) != 1:
        return fail(f"the three index cards name different sessions "
                    f"{sorted(card_sessions)}; refusing to publish "
                    "a mismatched page.")
    card_session = card_sessions.pop()
    if published_at[:10] != card_session:
        return fail(f"the tape was published on {published_at[:10]} "
                    f"but its window is the session of "
                    f"{card_session}; refusing to publish a "
                    "mismatched page.")

    # --- Cross-check the feed's tape figures against the card. ---
    feed_tape = {t["symbol"]: t for t in feed.get("tape", [])}
    if sorted(feed_tape) != sorted(UNDERLYINGS):
        return fail("the published feed's tape figures do not cover "
                    "the same three indexes as the card; refusing to "
                    "publish a mismatched page.")
    for u in UNDERLYINGS:
        c, t = cards[u], feed_tape[u]
        for label, got, want in [
                ("prints", t["prints"], c["prints"]),
                ("golden sweeps", t["golden_sweeps"],
                 c["golden_sweeps"])]:
            if got != want:
                return fail(f"the feed says {u} {label} is {got} "
                            f"but the card says {want}; refusing to "
                            "publish a mismatched page.")

    # --- The log's tape runs: group the aggregate rows into runs,
    # one run per recorded moment, three indexes per run. ---
    aggregates = [r for r in log_rows
                  if r.get("component") == "tape-aggregate"]
    if not aggregates:
        return fail("the permanent log holds no tape run at all; "
                    "refusing to show a wire that is not on the "
                    "record.")
    runs = {}
    for r in aggregates:
        runs.setdefault(r["ts_utc"][:16], []).append(r)
    run_list = []
    for minute in sorted(runs):
        rows = runs[minute]
        by_name = {r["name"]: r for r in rows}
        if sorted(by_name) != sorted(UNDERLYINGS):
            return fail(f"the tape run recorded at {minute} does "
                        "not cover the same three indexes as the "
                        "card; refusing to publish a mismatched page.")
        sessions = {r["value"]["window"].split(" -> ")[0][:10]
                    for r in rows}
        if len(sessions) != 1:
            return fail(f"the tape run recorded at {minute} mixes "
                        f"sessions {sorted(sessions)}; refusing to "
                        "publish a mismatched page.")
        run_list.append({
            "start": min(r["ts_utc"] for r in rows),
            "end": max(r["ts_utc"] for r in rows),
            "session": sessions.pop(),
            "cards": {u: by_name[u]["value"] for u in UNDERLYINGS},
        })
    run_list.sort(key=lambda run: run["start"])

    # --- Cross-check every run's logged alerts against its own
    # recorded cards, alert for alert. ---
    alert_rows = [r for r in log_rows
                  if r.get("component") == "tape-alert"]
    for i, run in enumerate(run_list):
        next_start = (run_list[i + 1]["start"]
                      if i + 1 < len(run_list) else None)
        in_run = [r for r in alert_rows
                  if r["ts_utc"] >= run["start"]
                  and (next_start is None or r["ts_utc"] < next_start)]
        for u in UNDERLYINGS:
            logged = Counter(json.dumps(r["value"], sort_keys=True)
                             for r in in_run if r["name"] == u)
            on_card = Counter(json.dumps(a, sort_keys=True)
                              for a in run["cards"][u]["alerts"])
            if logged != on_card:
                return fail(f"the log holds "
                            f"{sum(logged.values())} {u} alerts for "
                            f"the run of {run['session']} recorded at "
                            f"{run['start']} but its recorded card "
                            f"lists {sum(on_card.values())}, and they "
                            "do not match alert for alert; refusing "
                            "to publish a mismatched page.")

    # --- The freshest run overall must hold the published card. ---
    freshest_run = run_list[-1]
    if freshest_run["session"] != card_session:
        return fail(f"the freshest tape run in the log is the "
                    f"session of {freshest_run['session']} but the "
                    f"published card is the session of "
                    f"{card_session}; refusing to publish a "
                    "mismatched page.")
    for u in UNDERLYINGS:
        if freshest_run["cards"][u] != cards[u]:
            return fail(f"the log's recorded {u} card for the "
                        "freshest run differs from the published "
                        "card; refusing to publish a mismatched page.")

    # --- One record per session: its freshest run. ---
    sessions = {}
    for run in run_list:
        sessions[run["session"]] = run  # later runs overwrite
    session_names = sorted(sessions)

    prints_out = []
    session_entries = []
    total_golden = 0
    for session in session_names:
        run = sessions[session]
        session_published = (published_at if session == card_session
                             else run["end"])
        prints_looked_at = sum(run["cards"][u]["prints"]
                               for u in UNDERLYINGS)
        golden_count = sum(run["cards"][u]["golden_sweeps"]
                           for u in UNDERLYINGS)
        golden_alerts = []
        for u in UNDERLYINGS:
            card = run["cards"][u]
            listed = [a for a in card["alerts"] if a["golden_sweep"]]
            if len(listed) != card["golden_sweeps"]:
                return fail(f"the {u} run of {session} counted "
                            f"{card['golden_sweeps']} golden sweeps "
                            f"in its whole tape but its alert list "
                            f"carries {len(listed)}; the wire "
                            "promises every golden print, so a count "
                            "it cannot list in full is not published.")
            golden_alerts.extend((u, a) for a in listed)
        completeness = session_completeness(run["cards"])
        coverage = (f"{prints_looked_at:,} prints looked at across "
                    f"the three indexes; {golden_count} golden "
                    f"sweeps found")
        if completeness["batches_capped"]:
            coverage += (f"; {completeness['state_words']}")
        elif completeness["state"] == "undeclared":
            coverage += f"; {completeness['state_words']}"
        receipt = {
            "session": session,
            "published_at_utc": session_published,
            "source": SOURCE_WORDS,
            "coverage": coverage,
            "completeness": completeness,
        }
        for u, a in golden_alerts:
            if a["ts"][:10] != session:
                return fail(f"a golden alert on {u} printed on "
                            f"{a['ts'][:10]}, outside the session "
                            f"{session}; refusing to publish a "
                            "mismatched page.")
            if a["side"] not in SIDE_WORDS:
                return fail(f"a golden alert on {u} carries a side "
                            f"this page cannot say plainly: "
                            f"{a['side']!r}; refusing to guess.")
            if a["sentiment"] not in DIRECTION_WORDS:
                return fail(f"a golden alert on {u} carries a "
                            f"direction this page cannot say plainly: "
                            f"{a['sentiment']!r}; refusing to guess.")
            contract = describe_contract(a["symbol"], u)
            if contract is None:
                return fail(f"the contract code {a['symbol']!r} on "
                            f"{u} does not read as one of its own "
                            "contracts; refusing to guess at it.")
            prints_out.append({
                "session": session,
                "underlying": u,
                "time_utc": a["ts"],
                "contract_code": a["symbol"],
                "contract": contract,
                "price_per_contract": a["price"],
                "contracts": a["size"],
                "premium_usd": a["premium"],
                "heat_score": a["heat"],
                "side_words": SIDE_WORDS[a["side"]],
                "direction": a["sentiment"],
                "direction_words": DIRECTION_WORDS[a["sentiment"]],
                "receipt": receipt,
            })
        session_entries.append({
            "session": session,
            "published_at_utc": session_published,
            "prints_looked_at": prints_looked_at,
            "golden_prints": golden_count,
            "completeness": completeness,
            "receipt": receipt,
        })
        total_golden += golden_count

    prints_out.sort(key=lambda p: (p["session"], -p["premium_usd"]))

    data = {
        "tool": "Golden Sweep Wire",
        "freshest_session": session_names[-1],
        "published_at_utc": published_at,
        "source": SOURCE_WORDS,
        "decision": {
            "sessions_needed": SESSIONS_NEEDED,
            "decision_date": DECISION_DATE,
        },
        "counts": {
            "sessions_recorded": len(session_names),
            "sessions_needed": SESSIONS_NEEDED,
            "sessions_remaining": SESSIONS_NEEDED - len(session_names),
            "golden_prints": total_golden,
        },
        "sessions": session_entries,
        "prints": prints_out,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} ({len(session_names)} sessions on "
          f"record of {SESSIONS_NEEDED} needed, {total_golden} "
          f"golden prints, freshest session {session_names[-1]}, "
          f"published {published_at})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
