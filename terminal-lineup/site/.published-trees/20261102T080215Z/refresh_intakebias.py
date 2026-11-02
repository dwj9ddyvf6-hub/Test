#!/usr/bin/env python3
"""Refresh the Intake-Bias Reversal forecaster (Forecast Engine 9).

=====================================================================
REGISTER TRIPLE (written before any computation)

1. EVIDENCE CLASS
   - The dual-population flow score tallies, computed by the tape
     machinery exactly as extracted (tallies verbatim; the score is
     the sum of its tallies, which is the extraction's own
     inference; the vendor's sub-1 floor bug is NOT copied: no tally
     anywhere floors a ratio at 1, so a ratio of 0.05 scores 0.5).
     The score is computed twice per name: once over buys-only
     prints (the prints a buys-only intake keeps: at the ask or
     above it) and once over every non-cancelled print. Stored per
     run in the permanent log as tape summary rows and, for the
     freshest run only, in the tape card file. Side labels inherit
     the declared latest-quote limitation: a print's side is read
     against the latest quote, not a quote proven live at the
     print's own instant.
   - Short volume: the share of a day's total volume that was short
     sales, from the FINRA off-exchange (FNQC) daily file as
     republished in the morning map record (per-name short share
     with its file date). This is the exchange republication route.
     It is NOT the Short Volume Ledger page's own store, which has
     stored 0 days; it is NOT the long FINRA study history
     (2018-08 to 2026-10), which exists on this disk only as summary
     figures with no per-name file; and it is NOT short interest
     (shares on loan at a settlement date), a different measure
     that is never substituted. The raw short and total counts are
     read live by the map machinery and not kept per name; only the
     share is stored, and ranking by the share is the same ranking
     as ranking by short volume within a day's tercile cut only
     when totals are comparable, so this engine registers its cut
     as a cut on the SHARE, in plain words on the page.
   - Corpus avoid evidence behind the mechanism (each parent
     grade B in context): loud attention days fade; trade-count
     surges are a strong avoid; heavily shorted names lag in
     healthy markets. The interaction itself is untested.
   - This engine's own live record: none before today.

2. RECONSTRUCTION CHOICES (every constant named before computing)
   - Universe: exactly the names carrying both flow scores for a
     session. Today that is the three big index funds only (SPY,
     QQQ, IWM): the tape machinery cards those three and no stock
     carries a tape card. Nothing is extended to names without
     cards; the claim is narrowed to this universe and the page
     prints its size.
   - Session record: per session, the LAST tape summary run in the
     permanent log (an early partial run on 2026-10-26 is superseded
     by that evening's full run). Means are recomputed from the
     stored sums and counts, never taken from a rounded display.
   - Gap: the buys-only mean score minus the all-prints mean score,
     signed. Largest means most positive: the buys-only intake
     looking most bullish against the honest all-prints score.
     (An absolute-gap reading exists in one parent candidate; the
     signed reading is the one registered here, and on the freshest
     session the two readings pick different names, which the
     history table shows.)
   - Cohort sizes on a universe of n names: the gap cohort is the
     top fifth, max(1, ceil(n/5)) names; the short-share cohort is
     the top third, max(1, ceil(n/3)) names. On today's n = 3 both
     are 1 name. The interaction cohort is the overlap of the two;
     an empty overlap is a no-fire day, never backfilled.
   - Short share for a tape session D: the newest stored FNQC file
     date strictly before D (that file is published after D-1's
     close, so it is the latest short reading in hand when D's
     prints complete). Its date is printed beside every reading.
   - THE FORECAST, per firing session: the interaction cohort's
     mean 5-session gain against SPY (the big S&P 500 fund) will be
     at least 1.0 point negative, and its predicted middle
     (median) gain is stated as a number: -1.5 points, fixed here
     before any live outcome exists. No source on record supplies
     a median; -1.5 is this engine's own pre-registered point,
     set half a point beyond the mean floor so both halves of the
     claim can fail. With a one-name cohort the mean and the
     middle are the same number when graded.
   - Companion claim, same ledger: the top-gap fifth's 5-session
     middle gain against SPY is negative. On today's universe the
     top-gap fifth IS the bias-only rival cohort, so the companion
     claim rides on that cohort's row set as its own row.
   - Rival cohorts, ledgered on the same days with the same form
     and the same grading: the bias-only cohort (largest gap, no
     short condition) and the short-only cohort (top-third short
     share, no gap condition), each carrying the same -1.5 point
     predicted middle. The interaction must beat both or the kill
     rule fires. Note, stated plainly: when SPY itself is a cohort's
     only name, that cohort's gain against SPY is zero by
     construction, because SPY is the yardstick.
   - Grading: at exactly 5 sessions after the fire session, mean
     and middle both published, every cohort name in the count
     including a halted name at its last price. Known grading note,
     stated like the earlier engines stated theirs: the shared
     grading runner cannot yet resolve a cohort mean/middle excess
     outcome, and the price history on record ends 2026-10-23,
     before every tape session on record, so no cohort can grade
     until the price history extends 5 sessions past a fire.
   - History: the sessions on record where both inputs exist are
     replayed into the same three cohorts and shown labelled as
     history; history ledgers nothing (a forecast written after
     its window opened would break the ledger-before-display law),
     and no history outcome is graded because the price history
     ends before those sessions.
   - Thin-cell rule: below 30 graded, counts only, no percentage
     and no score is published from the record.

3. NON-CLAIMS
   - This is a cohort fade forecast, never a short book and never
     a list of names to short: shorting picked names was tested
     and killed after borrowing costs; the forecast is used, if at
     all, as a reason to avoid, not to borrow and sell.
   - No claim is made about any stock without a tape card.
   - The vendor score itself is not endorsed: the gap between its
     two populations is the measurement, not the score's level.

=====================================================================
Behaviour: cross-checks the tape card file against the permanent
log's freshest full run, the map card file against the log's short
shares, and the forecast ledger's chain, failing closed on any
disagreement; builds the three cohorts for every session on record
and for the freshest session; appends the freshest session's
cohort forecasts through the forecast machinery API only; writes
data.json. All timestamps come from the sources, never the clock,
so reruns are idempotent.

Usage: python3 refresh_intakebias.py
"""

import json
import math
import os
import sys
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
MORGUE = os.path.expanduser("~/workspace/morgue")
LOG_PATH = os.path.join(MORGUE, "output", "ledger.jsonl")
TAPE_CARD_PATH = os.path.join(MORGUE, "output", "tape_card.json")
MAP_CARD_PATH = os.path.join(MORGUE, "output", "map_card.json")
PANEL_PATH = os.path.join(MORGUE, "data_cache", "board_bt_bars.json")
FORECAST_DIR = os.path.expanduser("~/workspace/terminal-lineup/forecast")
OUT_PATH = os.path.join(HERE, "intake-bias", "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import attestation_block as _ab
except ImportError:  # refresh stays runnable standalone
    _ab = None

import importlib.util  # noqa: E402


def _load(mod_name, path):
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_forecast_ledger = _load("forecast_ledger_mod",
                         os.path.join(FORECAST_DIR, "ledger.py"))
_forecast_registry = _load("forecast_registry_mod",
                           os.path.join(FORECAST_DIR, "registry.py"))
Ledger = _forecast_ledger.Ledger
file_sha256 = _forecast_ledger.file_sha256
Registry = _forecast_registry.Registry

ENGINE_ID = "engine_09"
NAMES = ["SPY", "QQQ", "IWM"]
PLAIN_NAME = {"SPY": "SPY (the big S&P 500 fund)",
              "QQQ": "QQQ (the big Nasdaq-100 fund)",
              "IWM": "IWM (the big small-company fund)"}
PREDICTED_MEDIAN = -1.5
MEAN_CLAIM_FLOOR = -1.0
HORIZON = 5
THIN = 30
KILL_FIRES = 80

SOURCE_WORDS = ("The daily options-print tape summaries for the three "
                "big index funds, and the short-sale share of each "
                "day's volume from the FINRA off-exchange daily file "
                "as republished in the morning map record")


def fail(message):
    print(f"Intake-Bias refresh: {message}", file=sys.stderr)
    return 1


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def weekdays_after(start_iso, count):
    d = date.fromisoformat(start_iso) + timedelta(days=1)
    out = []
    while len(out) < count:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def cohorts_for(rows, short):
    """rows: {name: gap}; short: {name: share}. Returns the three
    cohorts under the registered cuts."""
    n = len(rows)
    k_gap = max(1, math.ceil(n / 5))
    k_short = max(1, math.ceil(n / 3))
    by_gap = sorted(rows, key=lambda s: (-rows[s], s))
    by_short = sorted(short, key=lambda s: (-short[s], s))
    bias = by_gap[:k_gap]
    short_only = by_short[:k_short]
    interaction = [s for s in bias if s in short_only]
    return bias, short_only, interaction


def build():
    for path in (LOG_PATH, TAPE_CARD_PATH, MAP_CARD_PATH, PANEL_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    with open(LOG_PATH, encoding="utf-8") as fh:
        log_rows = [json.loads(line) for line in fh if line.strip()]
    tape_card = load_json(TAPE_CARD_PATH)
    map_card = load_json(MAP_CARD_PATH)
    panel = load_json(PANEL_PATH)
    panel_last = panel["SPY"][-1][0]

    # ---- Tape sessions: last summary run per session is the record
    runs = {}
    for r in log_rows:
        if r.get("component") == "tape-aggregate":
            v = r["value"]
            runs.setdefault(r["ts_utc"][:10], {})[v["underlying"]] = (
                r["ts_utc"], v)
    sessions = {}
    for day, per_name in runs.items():
        if set(per_name) != set(NAMES):
            return fail(f"tape session {day} does not carry exactly "
                        "the three index funds")
        sess = {}
        for sym, (ts, v) in per_name.items():
            buys = v["algo_buys_only_sum"] / v["algo_buys_only_n"]
            allp = v["algo_all_sum"] / v["algo_all_n"]
            sess[sym] = {"buys_only": round(buys, 4),
                         "all_prints": round(allp, 4),
                         "gap": round(buys - allp, 4),
                         "prints": v["prints"], "run_ts": ts}
        sessions[day] = sess
    if not sessions:
        return fail("the permanent log holds no tape summary runs")
    freshest_day = max(sessions)

    # ---- The tape card file must agree with the freshest full run
    card_by_sym = {c["underlying"]: c for c in tape_card["cards"]}
    if set(card_by_sym) != set(NAMES):
        return fail("the tape card file does not carry exactly the "
                    "three index funds")
    for sym in NAMES:
        c = card_by_sym[sym]
        s = sessions[freshest_day][sym]
        if abs(c["mean_algo_buys_only"] - s["buys_only"]) > 0.011 or \
                abs(c["mean_algo_all"] - s["all_prints"]) > 0.011:
            return fail(f"the tape card file's {sym} scores disagree "
                        "with the permanent log's freshest run")

    # ---- Short shares: last map row per name per file date
    short_by_date = {}
    for r in log_rows:
        if r.get("component") == "gex_static_v1" and \
                r.get("dix_ratio") is not None:
            short_by_date.setdefault(r["dix_date"], {})[
                r["underlying"]] = float(r["dix_ratio"])
    for day, per_name in short_by_date.items():
        if set(per_name) != set(NAMES):
            return fail(f"short-share date {day} does not carry "
                        "exactly the three index funds")
    if not short_by_date:
        return fail("the map record holds no short shares")

    # ---- The map card file must agree with the log's newest shares
    newest_short_date = max(short_by_date)
    mc_by_sym = {c["underlying"]: c for c in map_card["cards"]}
    if map_card.get("dix_date") != newest_short_date:
        return fail("the map card file's short-share date disagrees "
                    "with the permanent log")
    for sym in NAMES:
        if abs(mc_by_sym[sym]["dix_ratio"] -
               short_by_date[newest_short_date][sym]) > 1e-9:
            return fail(f"the map card file's {sym} short share "
                        "disagrees with the permanent log")

    def short_for(session_day):
        prior = [d for d in short_by_date if d < session_day]
        if not prior:
            return None, None
        d = max(prior)
        return d, short_by_date[d]

    # ---- Cohorts for every session on record (history + freshest)
    session_rows = []
    for day in sorted(sessions):
        sdate, shares = short_for(day)
        if shares is None:
            return fail(f"no short-share file predates tape session "
                        f"{day}")
        gaps = {sym: sessions[day][sym]["gap"] for sym in NAMES}
        bias, short_only, interaction = cohorts_for(gaps, shares)
        session_rows.append({
            "session": day,
            "short_share_date": sdate,
            "names": [{"symbol": sym,
                       "name": PLAIN_NAME[sym],
                       "buys_only": sessions[day][sym]["buys_only"],
                       "all_prints": sessions[day][sym]["all_prints"],
                       "gap": gaps[sym],
                       "short_share": round(shares[sym], 4)}
                      for sym in NAMES],
            "bias_only": bias, "short_only": short_only,
            "interaction": interaction,
            "fired": bool(interaction),
        })
    history_rows = session_rows[:-1]
    today = session_rows[-1]
    if today["session"] != freshest_day:
        return fail("internal ordering error on sessions")

    # ---- Ledger the freshest session's cohorts, machinery API only
    registry = Registry()
    ledger = Ledger(os.path.join(FORECAST_DIR, "ledger.jsonl"),
                    registry=registry)
    if not ledger.verify_chain():
        return fail("the forecast ledger's chain does not verify")
    lineage = {
        "source_artifacts": [
            {"path": p, "sha256": file_sha256(p)}
            for p in (LOG_PATH, TAPE_CARD_PATH, MAP_CARD_PATH,
                      PANEL_PATH)],
        "note": ("Freshest tape session's three cohorts under the "
                 "registered cuts; short shares from the newest FNQC "
                 "file dated strictly before the session."),
        "clocks": {
            "event_time": sessions[freshest_day]["SPY"]["run_ts"],
            "publication_time": tape_card["generated_at_utc"],
            "first_available_time":
                sessions[freshest_day]["SPY"]["run_ts"],
            "ingestion_time": tape_card["generated_at_utc"],
            "decision_as_of": freshest_day,
        },
    }
    horizon = weekdays_after(freshest_day, HORIZON)
    created_total = 0
    ledgered = []
    cohort_specs = [
        ("interaction", today["interaction"],
         "Interaction cohort (largest score gap and top-third short "
         "share): mean 5-session gain against SPY, in points"),
        ("bias_only", today["bias_only"],
         "Bias-only rival cohort (largest score gap, no short "
         "condition): mean 5-session gain against SPY, in points"),
        ("short_only", today["short_only"],
         "Short-only rival cohort (top-third short share, no gap "
         "condition): mean 5-session gain against SPY, in points"),
    ]
    for cell, members, quantity in cohort_specs:
        if not members:
            continue
        subject = "cohort:" + "+".join(members)
        _row, created = ledger.append_forecast_declared(
            engine_id=ENGINE_ID,
            issued_ts=sessions[freshest_day]["SPY"]["run_ts"],
            subject=subject, quantity=quantity,
            value={"estimate": PREDICTED_MEDIAN, "cell": cell,
                   "members": members,
                   "mean_claim_floor": MEAN_CLAIM_FLOOR},
            horizon_open=horizon[0], horizon_close=horizon[-1],
            lineage=lineage,
            families=["options_prints", "filings_positioning"],
            outcome={"symbol": members[0], "kind": "cohort_excess_5s",
                     "members": members, "benchmark": "SPY",
                     "base_date": freshest_day,
                     "at_date": horizon[-1]})
        created_total += int(created)
        ledgered.append(cell)
    if today["bias_only"]:
        subject = "cohort:" + "+".join(today["bias_only"])
        _row, created = ledger.append_forecast_declared(
            engine_id=ENGINE_ID,
            issued_ts=sessions[freshest_day]["SPY"]["run_ts"],
            subject=subject,
            quantity=("Companion claim: top-gap fifth's 5-session "
                      "middle gain against SPY, in points (negative "
                      "is the claim)"),
            value={"estimate": PREDICTED_MEDIAN,
                   "cell": "companion_median",
                   "members": today["bias_only"],
                   "mean_claim_floor": MEAN_CLAIM_FLOOR},
            horizon_open=horizon[0], horizon_close=horizon[-1],
            lineage=lineage,
            families=["options_prints", "filings_positioning"],
            outcome={"symbol": today["bias_only"][0],
                     "kind": "cohort_excess_5s",
                     "members": today["bias_only"], "benchmark": "SPY",
                     "base_date": freshest_day,
                     "at_date": horizon[-1]})
        created_total += int(created)
        ledgered.append("companion_median")

    if not ledger.verify_chain():
        return fail("the forecast ledger's chain broke during append")
    recorded = graded = fires = 0
    fire_days = set()
    for row in ledger.rows():
        if row.get("engine_id") != ENGINE_ID:
            continue
        if row.get("type") == "forecast":
            recorded += 1
            if (row.get("value") or {}).get("cell") == "interaction":
                fires += 1
                fire_days.add(row["lineage"]["clocks"]
                              ["decision_as_of"])
        if row.get("type") == "grade":
            graded += 1

    data = {
        "tool": "Intake-Bias Reversal",
        "state": "proving",
        "source": SOURCE_WORDS,
        "published_at_utc": tape_card["generated_at_utc"],
        "panel_last_session": panel_last,
        "universe": {"size": len(NAMES),
                     "names": [PLAIN_NAME[s] for s in NAMES],
                     "note": ("Only these three names carry both "
                              "flow scores today. No stock has a "
                              "tape card, so no stock is in any "
                              "cohort and nothing is extended to "
                              "names without cards.")},
        "today": dict(today, horizon_open=horizon[0],
                      horizon_close=horizon[-1],
                      ledgered_cells=ledgered),
        "forecast": {
            "mean_claim": ("The interaction cohort's average gain "
                           "over the next 5 trading days, measured "
                           "against SPY, will be at least 1.0 point "
                           "worse than SPY."),
            "predicted_median": PREDICTED_MEDIAN,
            "predicted_median_words": ("The predicted middle gain "
                                       "for the cohort is -1.5 "
                                       "points against SPY."),
            "companion_claim": ("Companion claim, recorded the same "
                                "way: the middle gain of the "
                                "largest-gap group alone will be "
                                "below zero over the same 5 trading "
                                "days."),
            "never_a_short_book": ("This is a warning about a group "
                                   "of names, not a list to borrow "
                                   "and sell short. Shorting picked "
                                   "names was tested and dropped "
                                   "after borrowing costs ate the "
                                   "gain; a fade warning is a reason "
                                   "to stay away, not a short sale."),
        },
        "history": {
            "label": "History: the sessions on record, worked out "
                     "after the fact and recorded nowhere in advance",
            "sessions": history_rows,
            "outcomes_note": ("No history outcome is graded: the "
                              "price history on record ends "
                              f"{panel_last}, before every tape "
                              "session on record, so the 5 trading "
                              "days after these sessions are not on "
                              "record yet."),
            "would_have_fired": sum(1 for s in session_rows
                                    if s["fired"]),
            "sessions_on_record": len(session_rows),
        },
        "short_volume_route": {
            "used": ("The short figures come from the FINRA "
                     "off-exchange daily file, as republished in "
                     "the morning map record: for each fund, the "
                     "share of that day's total volume that was "
                     "short sales, with the file's own date printed "
                     "beside it. The file for a day is published "
                     "after that day's close, so each session uses "
                     "the newest file dated before it."),
            "not_used": [
                "The Short Volume Ledger page's own store: it has "
                "stored 0 days, so it supplies nothing.",
                "The long FINRA study history (August 2018 to "
                "October 2026): it exists here only as summary "
                "figures, with no per-name file to read.",
                "Short interest (shares out on loan on two "
                "settlement dates a month): a different measure, "
                "never substituted for short volume.",
            ],
        },
        "live": {"forecasts_recorded": recorded,
                 "forecasts_graded": graded,
                 "interaction_fires": len(fire_days),
                 "target_fires": KILL_FIRES},
        "kill_criterion": (
            "After 80 days on which the combined group actually "
            "forms, this tool is retired if that group's average "
            "gain is zero or better, or if it does no better than "
            "the short-volume-only group on its own."),
        "thin_rule": ("Below 30 graded, counts only: no percentage "
                      "and no score is drawn from a handful of "
                      "tests."),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} ({len(session_rows)} tape sessions, "
          f"freshest {freshest_day}: interaction "
          f"{today['interaction'] or 'empty, no fire'}, "
          f"{created_total} new forecasts, {recorded} recorded in "
          f"total, {len(fire_days)} interaction fire days)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
