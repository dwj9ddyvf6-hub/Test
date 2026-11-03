#!/usr/bin/env python3
"""Refresh the Premium Meter data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: the published daily tape records for the three big
index funds (SPY, QQQ and IWM): the published card for the freshest
recorded trading day, cross-checked against the published feed's
tape figures for the same day and against the permanent log, which
recorded every tape run (its whole-day totals and every alert)
before the cards were written. A trading day counts as a recorded
session only because a tape run for that day stands in the
permanent log; a day with no run is not covered, and its premium
is unknown, never zero. A name with no tape coverage shows no
meter, never a zero.

Reconstruction choices, stated as ours: (1) A session may have been
run more than once in a day; the freshest run of the session is the
session's record (the same choice the Activity Profile and the
Golden Sweep Wire make). (2) The records carry, per name per
session, the total premium traded across every print examined and
the net premium in calls and in puts (money taken in on prints
judged bought minus money paid out on prints judged sold, per
side; multi-part prints count in the total but not in the net
figures, per the tape's own published rule, which the page states).
No record carries the total premium split into a call total and a
put total, so that split is not shown and not invented; the split
shown is the net premium per side, which is what the records
carry. (3) The meter is the put share: the put side's share of the
two sides' combined net premium, measured on the size of each
side's net figure (a net figure can be negative, so the share is
taken on magnitudes). A share is shown only where both sides are
on record for that session and their combined size is not zero.
(4) Movement across the recorded sessions is stated as counts of
steps (with only two sessions on record there is one step per
name), never as a trend claim. (5) Completeness is declared per
name and per session from the card's own fields (prints examined,
contracts in scope, batches that hit the reading limit): capped
batches are a named incomplete state, missing fields are a named
undeclared state, and the prints-examined count travels beside
every total this page shows.

Scope: this page shows the premium the tape records carry and how
it split between calls and puts, session by session. It shows no
figure for any name or session the tape does not cover.

What the sources carry today (and what this script therefore
shows): two recorded sessions (2026-10-26 and 2026-10-27) for the
three index funds, each with prints examined, total premium, and
net premium in calls and in puts, so a put share is shown for
every name in both sessions and each name's movement is the one
step between them.

Fail-closed rules: if the published card, the feed and the log
disagree on any figure this page carries (prints, total premium,
net premium, golden sweeps, or any run's alerts against its own
recorded card), the refresh stops and publishes nothing. All
timestamps come from the sources, never the clock, so running
this script twice produces the same file.

Usage: python3 refresh_premiummeter.py
"""

import json
import os
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
OUT_PATH = os.path.join(HERE, "premium-meter", "data.json")

UNDERLYINGS = ["SPY", "QQQ", "IWM"]

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
    print(f"Premium Meter refresh: {message}", file=sys.stderr)
    return 1


def completeness_declaration(prints, contracts_in_scope,
                             batches_capped):
    """Explicit completeness declaration from a card's own fields."""
    if prints is None or contracts_in_scope is None \
            or batches_capped is None:
        return {
            "prints_examined": prints,
            "contracts_in_scope": contracts_in_scope,
            "batches_capped": batches_capped,
            "state": "undeclared",
            "reason": ("the record does not declare prints examined, "
                       "contracts in scope and batches capped, so "
                       "completeness is not claimed"),
            "state_words": ("Completeness unknown: this reading does "
                            "not declare how complete it is, so no "
                            "completeness is claimed for it"),
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


def put_share(call_net, put_net):
    """The put share of the two sides' combined net premium.

    Shown only where both sides are on record and their combined
    size is not zero; otherwise None (no meter, never a zero).
    """
    if call_net is None or put_net is None:
        return None
    combined = abs(call_net) + abs(put_net)
    if combined == 0:
        return None
    return round(100.0 * abs(put_net) / combined, 1)


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
                    "publish a partial meter.")

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
    # The feed's as_of_session is the BOARD's last completed session
    # (publish_feed takes it from the board summary), a different date
    # kind from the tape card's session: the board runs pre-open on the
    # prior session while the tape runs post-close, so equality refused
    # every coherent cycle (BUGLOG 2026-10-29, tape family). The binding
    # that ties the feed to THIS card is exact tape-figure agreement
    # (checked below) plus generation order: the feed must have been
    # generated at or after the card it copies.
    try:
        from datetime import datetime as _dt
        _feed_ts = _dt.fromisoformat(feed["generated_at_utc"])
        _card_ts = _dt.fromisoformat(published_at)
        _stale = _feed_ts < _card_ts
    except (KeyError, TypeError, ValueError):
        return fail("the tape card and the published feed do not both "
                    "carry a generation time; refusing to publish a "
                    "page whose feed cannot be bound to the card.")
    if _stale:
        return fail(f"the published feed was generated "
                    f"{feed.get('generated_at_utc')} before the tape "
                    f"card it copies ({published_at}); refusing to "
                    "publish a stale feed copy.")

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
                 c["golden_sweeps"]),
                ("total premium (millions)",
                 t["total_premium_m"],
                 round(c["total_premium"] / 1e6, 1)),
                ("net premium (millions)",
                 t["net_premium_m"],
                 round(c["net_premium"] / 1e6, 1))]:
            if got != want:
                return fail(f"the feed says {u} {label} is {got} "
                            f"but the card says {want}; refusing to "
                            "publish a mismatched page.")

    aggregates = [r for r in log_rows
                  if r.get("component") == "tape-aggregate"]
    if not aggregates:
        return fail("the permanent log holds no tape run at all; "
                    "refusing to show a meter that is not on the "
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

    sessions = {}
    for run in run_list:
        sessions[run["session"]] = run  # later runs overwrite
    session_names = sorted(sessions)
    freshest_session = session_names[-1]
    if freshest_session != card_session:
        return fail(f"the freshest recorded session is "
                    f"{freshest_session} but the published card is "
                    f"the session of {card_session}; refusing to "
                    "publish a mismatched page.")

    names_out = []
    for u in UNDERLYINGS:
        entries = []
        for session in session_names:
            run = sessions[session]
            c = run["cards"][u]
            session_published = (published_at
                                 if session == card_session
                                 else run["end"])
            completeness = completeness_declaration(
                c.get("prints"), c.get("contracts_in_scope"),
                c.get("batches_capped"))
            share = put_share(c.get("call_net_premium"),
                              c.get("put_net_premium"))
            coverage = (f"{c['prints']:,} prints examined on {u}; "
                        f"{completeness['state_words']}")
            entries.append({
                "session": session,
                "published_at_utc": session_published,
                "prints_examined": c["prints"],
                "total_premium_usd": c["total_premium"],
                "call_net_premium_usd": c.get("call_net_premium"),
                "put_net_premium_usd": c.get("put_net_premium"),
                "put_share_percent": share,
                "completeness": completeness,
                "receipt": {
                    "session": session,
                    "published_at_utc": session_published,
                    "source": SOURCE_WORDS,
                    "coverage": coverage,
                    "completeness": completeness,
                },
            })
        shares = [(e["session"], e["put_share_percent"])
                  for e in entries
                  if e["put_share_percent"] is not None]
        steps = rose = fell = flat = 0
        for (_, prev), (_, cur) in zip(shares, shares[1:]):
            steps += 1
            if cur > prev:
                rose += 1
            elif cur < prev:
                fell += 1
            else:
                flat += 1
        if not shares:
            movement_words = ("No put share is on record for this "
                              "name in any recorded session, so no "
                              "movement is shown")
        elif steps == 0:
            movement_words = ("Only one recorded session carries a "
                              "put share for this name, so there is "
                              "no step to measure yet")
        else:
            step_word = "step" if steps == 1 else "steps"
            parts = []
            if rose:
                parts.append(f"rose at {rose} of the {steps} "
                             f"{step_word}")
            if fell:
                parts.append(f"fell at {fell} of the {steps} "
                             f"{step_word}")
            if flat:
                parts.append(f"stayed level at {flat} of the "
                             f"{steps} {step_word}")
            movement_words = (
                f"Across the {len(shares)} recorded sessions with a "
                f"put share on record, the put share "
                + " and ".join(parts)
                + f": {shares[0][1]:.1f}% in the first, "
                f"{shares[-1][1]:.1f}% in the latest")
        names_out.append({
            "underlying": u,
            "sessions": entries,
            "movement": {
                "sessions_with_share": len(shares),
                "steps": steps,
                "rose": rose,
                "fell": fell,
                "flat": flat,
                "first_share_percent": (shares[0][1] if shares
                                        else None),
                "latest_share_percent": (shares[-1][1] if shares
                                         else None),
                "words": movement_words,
            },
        })

    session_entries = []
    for session in session_names:
        run = sessions[session]
        session_published = (published_at if session == card_session
                             else run["end"])
        prints_total = sum(run["cards"][u]["prints"]
                           for u in UNDERLYINGS)
        premium_total = sum(run["cards"][u]["total_premium"]
                            for u in UNDERLYINGS)
        session_entries.append({
            "session": session,
            "published_at_utc": session_published,
            "prints_examined": prints_total,
            "total_premium_usd": premium_total,
        })

    data = {
        "tool": "Premium Meter",
        "freshest_session": freshest_session,
        "published_at_utc": published_at,
        "source": SOURCE_WORDS,
        "sessions_recorded": len(session_names),
        "session_dates": session_names,
        "names": names_out,
        "sessions": session_entries,
        "how": ("The total is every dollar of premium across the "
                "prints examined that day. The split is the net "
                "premium in calls and in puts: money taken in on "
                "prints judged bought minus money paid out on "
                "prints judged sold, per side; prints that are part "
                "of a multi-part trade count in the total but not "
                "in the net figures. The meter is the put share: "
                "the put side's share of the two sides' combined "
                "net premium, measured on the size of each side's "
                "net figure. A share is shown only where both "
                "sides are on record for that session."),
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (freshest session {freshest_session}, "
          f"{len(session_names)} sessions on record, published "
          f"{published_at})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
