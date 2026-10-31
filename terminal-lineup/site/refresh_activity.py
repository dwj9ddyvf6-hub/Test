#!/usr/bin/env python3
"""Refresh the Activity Profile data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: the published daily tape records for the three big
index funds (SPY, QQQ and IWM): the published card for the freshest
recorded trading day, cross-checked against the published feed's
tape figures for the same day and against the permanent log, which
recorded every tape run (its whole-day totals and every alert)
before the cards were written. A trading day counts as a recorded
(covered) session only because a tape run for that day stands in
the permanent log; a day with no run is not covered, and its
activity is unknown, never zero. The construction this tool follows
(the published activity-profile construction adopted for this
lineup) declares covered sessions explicitly in exactly this way:
an uncovered date is unavailable, a covered date with no prints is
a known zero, and cancelled prints never count.

Reconstruction choices, stated as ours: (1) A session may have been
run more than once in a day; the freshest run of the session is the
session's record (the same choice the Golden Sweep Wire makes).
(2) The baseline for the current day is the strictly prior recorded
sessions only, up to the 20 the construction wants; the current day
never counts toward its own baseline, and no later day can leak
into it. (3) The records on disk are whole-day totals (prints
examined and premium traded), not readings taken at the same clock
time each day, so when a comparison is shown it compares whole
recorded days, and it is labelled that way; the construction's
same-clock intraday comparison is not claimed, because these
records cannot carry it. (4) Activity is measured in the two whole-
day figures the records actually carry for every name: prints
examined and total premium traded. Contract volume by call and put
is not in these records, so it is not shown and not invented.
(5) Completeness is declared per name and per session from the
card's own fields (prints examined, contracts in scope, batches
that hit the reading limit): capped batches are a named incomplete
state, missing fields are a named undeclared state, and neither is
ever shown as a complete reading or as a zero.

Non-claims: this page claims nothing about what any name will do
next. No hidden score is reproduced: the
vendor's own alert score is sealed and is not claimed here. While
fewer than 20 prior sessions are on record, no "times its usual
level" figure is shown for any name, because the baseline it would
rest on does not exist yet; the page shows the count of sessions
recorded and only the current day's own recorded figures.

What the sources carry today (and what this script therefore
shows): two recorded sessions (2026-10-26 and 2026-10-27) for the
three index funds. The current day is 2026-10-27; its strictly
prior baseline is 1 session of the 20 needed, so every name shows
the named not-enough-history state instead of a ratio, alongside
its own current-day figures and its completeness declaration.

Fail-closed rules: if the published card, the feed and the log
disagree on any figure this page carries (prints, total premium,
net premium, golden sweeps, or any run's alerts against its own
recorded card), the refresh stops and publishes nothing. All
timestamps come from the sources, never the clock, so running this
script twice produces the same file.

Usage: python3 refresh_activity.py
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
OUT_PATH = os.path.join(HERE, "activity-profile", "data.json")

UNDERLYINGS = ["SPY", "QQQ", "IWM"]
BASELINE_NEEDED = 20  # the construction's strictly-prior baseline

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
    print(f"Activity Profile refresh: {message}", file=sys.stderr)
    return 1


def completeness_declaration(prints, contracts_in_scope,
                             batches_capped):
    """Explicit completeness declaration from a card's own fields.

    Adopted discipline: capped batches are a named incomplete
    state, never a silent shortfall, and missing source fields are
    an undeclared state, never an assumed complete and never a zero.
    """
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
        overall["reason"] = ("at least one index record does not "
                             "declare its completeness fields, so "
                             "session completeness is not claimed")
        overall["state_words"] = ("Completeness unknown: at least one "
                                  "index does not say how complete "
                                  "its reading is, so no completeness "
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
                    "publish a partial profile.")

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

    # --- The log's tape runs: group the aggregate rows into runs,
    # one run per recorded moment, three indexes per run. ---
    aggregates = [r for r in log_rows
                  if r.get("component") == "tape-aggregate"]
    if not aggregates:
        return fail("the permanent log holds no tape run at all; "
                    "refusing to show a profile that is not on the "
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

    # --- One record per session: its freshest run. Covered
    # sessions are exactly the sessions with a run on record. ---
    sessions = {}
    for run in run_list:
        sessions[run["session"]] = run  # later runs overwrite
    session_names = sorted(sessions)
    current_session = session_names[-1]
    if current_session != card_session:
        return fail(f"the freshest recorded session is "
                    f"{current_session} but the published card is "
                    f"the session of {card_session}; refusing to "
                    "publish a mismatched page.")

    # --- The baseline: strictly prior recorded sessions only. ---
    prior_sessions = [s for s in session_names if s < current_session]
    baseline_sessions = prior_sessions[-BASELINE_NEEDED:]
    baseline_count = len(baseline_sessions)
    baseline_ready = baseline_count >= BASELINE_NEEDED

    session_entries = []
    for session in session_names:
        run = sessions[session]
        session_published = (published_at if session == card_session
                             else run["end"])
        completeness = session_completeness(run["cards"])
        prints_looked_at = sum(run["cards"][u]["prints"]
                               for u in UNDERLYINGS)
        premium_traded = sum(run["cards"][u]["total_premium"]
                             for u in UNDERLYINGS)
        coverage = (f"{prints_looked_at:,} prints looked at across "
                    f"the three indexes; {completeness['state_words']}")
        session_entries.append({
            "session": session,
            "published_at_utc": session_published,
            "prints_looked_at": prints_looked_at,
            "total_premium_usd": premium_traded,
            "completeness": completeness,
            "receipt": {
                "session": session,
                "published_at_utc": session_published,
                "source": SOURCE_WORDS,
                "coverage": coverage,
                "completeness": completeness,
            },
        })

    def baseline_mean(u, field):
        if not baseline_ready:
            return None
        vals = [sessions[s]["cards"][u][field]
                for s in baseline_sessions]
        return sum(vals) / len(vals)

    names_out = []
    for u in UNDERLYINGS:
        c = cards[u]
        completeness = completeness_declaration(
            c.get("prints"), c.get("contracts_in_scope"),
            c.get("batches_capped"))
        coverage = (f"{c['prints']:,} prints looked at on {u}; "
                    f"{completeness['state_words']}")
        receipt = {
            "session": current_session,
            "published_at_utc": published_at,
            "source": SOURCE_WORDS,
            "coverage": coverage,
            "completeness": completeness,
        }
        prem_mean = baseline_mean(u, "total_premium")
        prints_mean = baseline_mean(u, "prints")
        premium_ratio = (round(c["total_premium"] / prem_mean, 2)
                         if prem_mean else None)
        prints_ratio = (round(c["prints"] / prints_mean, 2)
                        if prints_mean else None)
        if baseline_ready and premium_ratio is not None:
            ratio_state = "shown"
            ratio_state_words = (
                "Compared with its own usual level: the average of "
                f"its {BASELINE_NEEDED} prior recorded days")
        elif baseline_ready:
            ratio_state = "no_baseline_level"
            ratio_state_words = (
                "No usual level to compare with: its prior recorded "
                "days average to nothing to divide by, so no "
                "comparison is shown")
        else:
            ratio_state = "not_enough_history"
            ratio_state_words = (
                "Not enough history yet: a comparison with this "
                f"name's usual level needs {BASELINE_NEEDED} prior "
                f"recorded days and {baseline_count} "
                f"{'is' if baseline_count == 1 else 'are'} on "
                "record, so no comparison is shown")
        names_out.append({
            "underlying": u,
            "session": current_session,
            "baseline_sessions": baseline_count,
            "baseline_needed": BASELINE_NEEDED,
            "baseline_session_dates": baseline_sessions,
            "activity": {
                "prints_examined": c["prints"],
                "total_premium_usd": c["total_premium"],
                "call_net_premium_usd": c["call_net_premium"],
                "put_net_premium_usd": c["put_net_premium"],
                "multileg_prints": c["multileg_prints"],
                "cancelled_prints_excluded": c["cancelled_excluded"],
                "contracts_in_scope": c["contracts_in_scope"],
            },
            "comparison": {
                "state": ratio_state,
                "state_words": ratio_state_words,
                "premium_times_usual": premium_ratio,
                "prints_times_usual": prints_ratio,
                "baseline_total_premium_usd": (
                    round(prem_mean, 2) if prem_mean else None),
                "baseline_prints": (
                    round(prints_mean, 2) if prints_mean else None),
            },
            "completeness": completeness,
            "receipt": receipt,
        })

    data = {
        "tool": "Activity Profile",
        "current_session": current_session,
        "published_at_utc": published_at,
        "source": SOURCE_WORDS,
        "baseline": {
            "needed": BASELINE_NEEDED,
            "baseline_sessions": baseline_count,
            "sessions_recorded": len(session_names),
            "prior_session_dates": baseline_sessions,
            "state": "ready" if baseline_ready else "building",
            "state_words": (
                f"Baseline ready: {BASELINE_NEEDED} prior recorded "
                "days stand behind each comparison"
                if baseline_ready else
                f"Baseline still building: {baseline_count} of "
                f"{BASELINE_NEEDED} sessions recorded"),
        },
        "names": names_out,
        "sessions": session_entries,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (current session {current_session}, "
          f"baseline {baseline_count} of {BASELINE_NEEDED} prior "
          f"sessions, {len(session_names)} sessions on record, "
          f"published {published_at})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
