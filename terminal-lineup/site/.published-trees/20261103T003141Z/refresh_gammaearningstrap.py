#!/usr/bin/env python3
"""Refresh the Gamma-Pressure Earnings Trap forecaster (Engine 11).

=====================================================================
REGISTER TRIPLE (written before any computation)

1. EVIDENCE CLASS
   - Earnings calendar: the Earnings Calendar page's record (the
     union of the two desk earnings files, checked name by name on
     the 18 names they share), gathered 2026-10-12: 77 names, 73
     with a report date, 4 with no date scheduled. Per name it
     carries ONLY a symbol, a report date, and a priced-move field
     that is empty for every dated name. There is NO report timing
     (before or after the open) anywhere in the record.
   - Index positioning: the morning map's modelled dealer
     positioning for the whole index (a modelled inventory under a
     stated sign convention, never an observed holding), stored per
     index fund (SPY, QQQ, IWM) in the permanent map record and in
     the freshest map card. Index level is the ONLY level that
     exists today: per-name positioning would need stored per-name
     option chains, and the chain archive holds 0 snapshots.
   - Priced expected move: ABSENT everywhere on record. The
     calendar's priced-move field is empty for all 73 dated names;
     the chain archive holds 0 snapshots, so no per-name straddle
     or chain price exists to read one from; the Expected Move Map
     page is index-only and is not a per-name earnings priced move;
     the per-name volatility record carries a volatility level, not
     a priced earnings move, and a volatility level is never
     converted into a priced move and called priced. This absence
     is the engine's blocking input and is named as such.
   - Past earnings moves: the Earnings Drift record is POOLED
     ONLY: 35 reports across AAPL, MSFT and NVDA summarised as a
     mean, a middle and a spread, gathered 2026-10-27. Individual
     report dates and individual moves are not stored anywhere,
     it carries no priced move for any event, and index
     positioning signs exist only for October 2026 sessions, long
     after those reports. Events carrying all four inputs (report
     date, actual move, priced move, that day's positioning sign):
     0. History therefore grades nothing, in either arm.
   - This engine's own live record: none before today.

2. RECONSTRUCTION CHOICES (every constant named before computing)
   - THE FORECAST, for a stock in the index reporting earnings
     within the next 5 trading days while the index-wide dealer
     positioning reading is negative: the size of its earnings-day
     move, either way, will be bigger than its priced expected
     move in at least 55 percent of cases, and the middle ratio of
     actual move to priced move will be at least 1.10. Horizon:
     the earnings session. SIZE ONLY: this engine never forecasts
     which way a stock will move, and no forecast it records
     carries a direction.
   - Governing index rule: a name that is on the S&P 500 list on
     record is governed by SPY (its own index, the only membership
     that can be shown: the record carries an S&P list of 1,503
     tagged names, 503 of them S&P 500; no Nasdaq-100 or
     Russell 2000 membership record exists on disk, and membership
     in the smaller S&P lists is never substituted for either).
     Every other calendar name is governed by SPY as the stated
     fallback. The governing index and the positioning LEVEL used
     (index-wide, always, today) are stated on every forecast.
   - Earnings session: the report date on the calendar IS the
     earnings session for grading, because the record carries no
     report timing. This is a named gap, not a silent assumption:
     a report released after the close arguably belongs to the
     next session, and the record cannot say which reports those
     are. The first record that carries timing replaces this rule
     openly, never quietly.
   - Ratio and exceedance: ratio = the size of the earnings-day
     move (the absolute close-to-close percent move into the
     earnings session's close) divided by the priced expected
     move in percent. An event exceeds when its ratio is above
     1.0. Both arms are graded identically: the same ratio, the
     same exceedance count, the same middle ratio.
   - CONTROL ARM: every earnings event whose governing index's
     positioning reading is POSITIVE at the time is recorded at
     the same time, in the same form, as the comparison group.
     The main claim has to beat that group, not just a coin flip.
     On the record today every positioning session is negative
     for all three index funds, so the comparison group has
     0 possible events so far and cannot fire until a positive
     session is recorded.
   - The next-5 window: the 5 trading days after the freshest
     completed map session on record (weekends skipped; the
     calendar record itself carries no holiday list, so a market
     holiday inside a future window would be named when the map
     record shows it).
   - Worked example: because no past event carries a priced move,
     the computation is proven on MADE-UP numbers in memory on
     every run (the Engine 5 and Engine 10 pattern): invented
     priced and actual moves run through the exact ratio,
     exceedance and middle-ratio code the live path uses, and a
     worked set of four invented events is checked against
     hand-computed answers. Made-up numbers are never written to
     the record of real forecasts and are labelled made-up
     wherever they appear.
   - Grading note, stated like the earlier engines stated theirs:
     the shared grading runner cannot yet resolve a realised-to-
     priced ratio or a group exceedance / middle-ratio outcome,
     and the price history on record ends 2026-10-23, before every
     report date in the window; grading follows when the runner
     is next extended.
   - Thin-cell rule: below 30 graded events in either group,
     counts only, no share and no middle ratio is published from
     the record.
   - Kill criterion, from the design: after 60 events, if the
     exceedance share's confidence range includes 50 percent, or
     the middle ratio is below 1.0, the engine is retired.

3. NON-CLAIMS
   - No direction, ever: nothing here says or implies which way
     any stock will move on its report.
   - No priced move is invented: not from past movement, not from
     a volatility level, not from an index band. Where no record
     carries a priced move, the field stays empty and the engine
     waits.
   - No per-name positioning is claimed: the positioning level
     used is index-wide on every forecast, stated each time.
     Per-name positioning waits on the chain archive and is never
     substituted silently.
   - Membership is claimed only where a record shows it: S&P 500
     membership from the list on record; nothing about the other
     two indexes is inferred.

=====================================================================
Behaviour: cross-checks the calendar's own counts against a
recount, the freshest map card against the permanent map record's
newest positioning rows (value for value, per index fund), the
S&P list's own counts against a recount, and the forecast
ledger's chain, failing closed on any disagreement; lists the
reports inside the next 5 trading days with their membership,
positioning state and priced move or its named absence; runs the
history test (events carrying all four inputs: 0); exercises the
ratio computation on made-up numbers in memory; appends any
genuine forecast (main arm and comparison group alike) through
the forecast machinery API only, which today is none, because
the priced move is absent for every name in the window; writes
data.json. All timestamps come from the sources, never the
clock, so reruns are idempotent.

Usage: python3 refresh_gammaearningstrap.py
"""

import json
import os
import statistics
import sys
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
MORGUE = os.path.expanduser("~/workspace/morgue")
MAP_LOG_PATH = os.path.join(MORGUE, "output", "ledger.jsonl")
MAP_CARD_PATH = os.path.join(MORGUE, "output", "map_card.json")
CALENDAR_PATH = os.path.join(HERE, "earnings-calendar", "data.json")
DRIFT_PATH = os.path.join(HERE, "earnings-drift", "data.json")
GICS_PATH = os.path.expanduser(
    "~/workspace/femto-lean/config/gics_sectors.json")
PANEL_PATH = os.path.join(MORGUE, "data_cache", "board_bt_bars.json")
CHAINS_DIR = os.path.join(MORGUE, "state", "morgue", "chains")
FORECAST_DIR = os.path.expanduser("~/workspace/terminal-lineup/forecast")
OUT_PATH = os.path.join(HERE, "gamma-earnings-trap", "data.json")
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

ENGINE_ID = "engine_11"
INDEX_FUNDS = ["SPY", "QQQ", "IWM"]
WINDOW_SESSIONS = 5
THIN = 30
KILL_EVENTS = 60
CLAIM_SHARE = 0.55
CLAIM_MEDIAN = 1.10

SOURCE_WORDS = ("The scheduled earnings calendar gathered on "
                "October 12, 2026, and the morning market map's "
                "index-wide positioning record")


def fail(message):
    print(f"Gamma-Earnings-Trap refresh: {message}", file=sys.stderr)
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


def move_ratio(prev_close, earnings_close, priced_move_pct):
    """The one ratio computation, used by the live path, the
    history path and the made-up worked example alike."""
    actual_pct = abs(earnings_close - prev_close) / prev_close * 100.0
    return actual_pct / priced_move_pct, actual_pct


def summarise(ratios):
    """Exceedance share and middle ratio for a group of events,
    graded identically in both arms."""
    if not ratios:
        return {"events": 0, "exceedances": 0, "share": None,
                "median_ratio": None}
    exc = sum(1 for r in ratios if r > 1.0)
    return {"events": len(ratios), "exceedances": exc,
            "share": round(exc / len(ratios), 4),
            "median_ratio": round(statistics.median(ratios), 4)}


def self_test():
    """Exercise the ratio computation on made-up numbers, in
    memory only, against hand-computed answers."""
    cases = [
        # (prev close, earnings close, priced %, want ratio, exceed)
        (200.0, 210.0, 4.0, 1.25, True),
        (100.0, 96.0, 5.0, 0.80, False),
        (50.0, 51.8, 3.0, 1.20, True),
        (80.0, 85.28, 6.0, 1.10, True),
    ]
    passed = 0
    ratios = []
    for prev, close, priced, want_ratio, want_exc in cases:
        ratio, _actual = move_ratio(prev, close, priced)
        ratios.append(ratio)
        if abs(ratio - want_ratio) < 1e-9 and (ratio > 1.0) == want_exc:
            passed += 1
    summary = summarise(ratios)
    worked_ok = (summary["events"] == 4 and summary["exceedances"] == 3
                 and abs(summary["share"] - 0.75) < 1e-9
                 and abs(summary["median_ratio"] - 1.15) < 1e-9)
    return {"cases": len(cases), "passed": passed,
            "worked_events": [
                {"prev_close": c[0], "earnings_close": c[1],
                 "priced_move_pct": c[2],
                 "actual_move_pct": round(move_ratio(c[0], c[1], c[2])[1], 4),
                 "ratio": round(move_ratio(c[0], c[1], c[2])[0], 4),
                 "exceeded": move_ratio(c[0], c[1], c[2])[0] > 1.0}
                for c in cases],
            "worked_summary": summary, "worked_ok": worked_ok,
            "ok": passed == len(cases) and worked_ok}


def chain_gate_summary():
    """The options candidate gate over the stored chain snapshots
    (options_gate.py, DEEP-PASS 3.1 item 3): the candidate surface
    this engine's per name work will rank from, gated before any
    ranking exists. Returns a summary dict, or None when the gate
    module cannot be loaded. Snapshots whose source supplies no
    Greek timestamp count as undated, in the open."""
    import gzip
    try:
        og = _load("options_gate_mod",
                   os.path.join(HERE, "options_gate.py"))
    except Exception:
        return None
    merged = og.gate_summary([], None)
    snapshots = 0
    if os.path.isdir(CHAINS_DIR):
        for sym in INDEX_FUNDS:
            d = os.path.join(CHAINS_DIR, sym)
            if not os.path.isdir(d):
                continue
            for name in sorted(os.listdir(d)):
                if not name.endswith(".json.gz"):
                    continue
                try:
                    with gzip.open(os.path.join(d, name), "rt",
                                   encoding="utf-8") as fh:
                        doc = json.load(fh)
                except (OSError, ValueError, EOFError):
                    continue
                snapshots += 1
                cols = doc.get("columns") or []
                idx = {c: cols.index(c) for c in cols}
                gi = (idx.get("greek_ts") if "greek_ts" in idx
                      else idx.get("greeks_ts"))
                snap_candidates = []
                for row in doc.get("rows") or []:
                    if not isinstance(row, list) \
                            or len(row) != len(cols):
                        continue
                    snap_candidates.append({
                        "iv": row[idx["iv"]] if "iv" in idx else None,
                        "greek_ts": (row[gi] if gi is not None
                                     else None)})
                # Freshness is judged at each snapshot's own
                # capture, so no contract is ever judged against
                # another day's clock; counts are then merged.
                snap_summary = og.gate_summary(
                    snap_candidates, doc.get("captured_at_utc"))
                merged["total"] += snap_summary["total"]
                merged["admitted"] += snap_summary["admitted"]
                merged["refused"] += snap_summary["refused"]
                for k, v in snap_summary["greek_states"].items():
                    merged["greek_states"][k] = \
                        merged["greek_states"].get(k, 0) + v
                for k, v in snap_summary["iv_states"].items():
                    merged["iv_states"][k] = \
                        merged["iv_states"].get(k, 0) + v
    merged["snapshots_scanned"] = snapshots
    merged["greek_max_age_seconds"] = og.GREEK_MAX_AGE_SECONDS
    merged["iv_ceiling"] = og.IV_CEILING
    merged["note"] = (
        "Candidate gate over the stored chain snapshots: Greeks "
        "older than 75 minutes, future dated Greeks and IV at or "
        "over 500 percent refuse a candidate; contracts whose "
        "source supplies no Greek timestamp are labelled undated, "
        "not silently trusted. The current store's source supplies "
        "no Greek timestamps and no IV, so its contracts count as "
        "undated with IV absent.")
    return merged


def build():
    for path in (MAP_LOG_PATH, MAP_CARD_PATH, CALENDAR_PATH,
                 DRIFT_PATH, GICS_PATH, PANEL_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    with open(MAP_LOG_PATH, encoding="utf-8") as fh:
        log_rows = [json.loads(line) for line in fh if line.strip()]
    map_card = load_json(MAP_CARD_PATH)
    calendar = load_json(CALENDAR_PATH)
    drift = load_json(DRIFT_PATH)
    gics = load_json(GICS_PATH)
    panel = load_json(PANEL_PATH)
    panel_last = panel["SPY"][-1][0]

    # ---- Calendar: recount must agree with its own counts
    names = calendar["names"]
    dated = [n for n in names if n.get("date")]
    if len(dated) != calendar["dated_names"] or \
            len(dated) + calendar["names_with_no_date"] != \
            calendar["names_on_record"] or \
            len(names) != len(dated):
        return fail("the earnings calendar's counts disagree with "
                    "a recount of its own names")
    priced_present = [n["symbol"] for n in dated
                      if n.get("expected_move") is not None]
    recorded_on = calendar["recorded_on"]

    # ---- Membership: the S&P list on record, recounted
    symbols = gics["symbols"]
    sp500 = {s for s, v in symbols.items() if v.get("index") == "sp500"}
    counts = {}
    for v in symbols.values():
        counts[v.get("index")] = counts.get(v.get("index"), 0) + 1
    if len(sp500) != counts.get("sp500"):
        return fail("internal membership recount error")

    # ---- Positioning sessions: last map run per session date,
    # keyed by the session the reading belongs to
    gex_rows = [r for r in log_rows
                if r.get("component") == "gex_static_v1"]
    by_session = {}
    for r in gex_rows:
        sess = r.get("dix_date") or r["ts_utc"][:10]
        cur = by_session.setdefault(sess, {})
        if r["underlying"] not in cur or \
                r["ts_utc"] > cur[r["underlying"]]["ts_utc"]:
            cur[r["underlying"]] = r
    sessions = []
    for sess in sorted(by_session):
        per = by_session[sess]
        if set(per) != set(INDEX_FUNDS):
            return fail(f"the map session {sess} does not carry "
                        "exactly the three index funds")
        sessions.append({
            "session": sess,
            "funds": {sym: {
                "value_usd_per_1pct": per[sym]["net_gex_usd_per_1pct"],
                "sign": ("negative" if per[sym]["net_gex_usd_per_1pct"] < 0
                         else "positive" if
                         per[sym]["net_gex_usd_per_1pct"] > 0 else "zero"),
                "run_ts": per[sym]["ts_utc"]}
                for sym in INDEX_FUNDS}})
    if not sessions:
        return fail("the map record holds no positioning sessions")
    freshest = sessions[-1]
    freshest_session = freshest["session"]
    positive_sessions = [s for s in sessions
                         if any(f["sign"] == "positive"
                                for f in s["funds"].values())]

    # ---- The freshest map card must agree with the record
    card_by_sym = {c["underlying"]: c for c in map_card["cards"]}
    if set(card_by_sym) != set(INDEX_FUNDS):
        return fail("the map card file does not carry exactly the "
                    "three index funds")
    for sym in INDEX_FUNDS:
        want = freshest["funds"][sym]["value_usd_per_1pct"]
        if abs(card_by_sym[sym]["net_gex_usd_per_1pct"] - want) > 1.0:
            return fail(f"the map card's {sym} positioning reading "
                        "disagrees with the permanent map record's "
                        "newest row")

    # ---- The window: next 5 trading days after the freshest
    # completed map session
    window_days = weekdays_after(freshest_session, WINDOW_SESSIONS)
    spy_sign = freshest["funds"]["SPY"]["sign"]
    window_events = []
    for n in sorted(dated, key=lambda x: (x["date"], x["symbol"])):
        if n["date"] not in window_days:
            continue
        in_sp500 = n["symbol"] in sp500
        window_events.append({
            "symbol": n["symbol"], "date": n["date"],
            "in_sp500": in_sp500,
            "membership": ("S&P 500 constituent on the list on "
                           "record" if in_sp500 else
                           "not on the S&P 500 list on record; "
                           "carried under the SPY fallback"),
            "governing_index": "SPY",
            "governing_basis": ("its own index" if in_sp500
                                else "the stated fallback"),
            "positioning_level": "index-wide",
            "positioning_sign": spy_sign,
            "positioning_value_usd_per_1pct":
                freshest["funds"]["SPY"]["value_usd_per_1pct"],
            "positioning_session": freshest_session,
            "priced_move_pct": n.get("expected_move"),
            "priced_move_state": ("on record" if
                                  n.get("expected_move") is not None
                                  else "absent: no record carries "
                                       "one for this name")})
    window_sp500 = sum(1 for e in window_events if e["in_sp500"])

    chain_snapshots = 0
    if os.path.isdir(CHAINS_DIR):
        chain_snapshots = sum(len(files) for _r, _d, files
                              in os.walk(CHAINS_DIR))
    chain_gate = chain_gate_summary()

    test = self_test()
    if not test["ok"]:
        return fail("the ratio computation failed its own worked "
                    f"example: {test['passed']} of {test['cases']}")

    # ---- Record any genuine forecasts, machinery API only.
    # A forecast needs every input: a dated report inside the
    # window, a priced move on record, and a positioning sign.
    # The main arm and the comparison group go through the same
    # code path; the arm is decided by the sign alone.
    registry = Registry()
    ledger = Ledger(os.path.join(FORECAST_DIR, "ledger.jsonl"),
                    registry=registry)
    if not ledger.verify_chain():
        return fail("the forecast ledger's chain does not verify")
    lineage = {
        "source_artifacts": [
            {"path": p, "sha256": file_sha256(p)}
            for p in (CALENDAR_PATH, MAP_LOG_PATH, MAP_CARD_PATH,
                      GICS_PATH, PANEL_PATH)],
        "note": ("Earnings events inside the 5 trading days after "
                 f"the freshest map session ({freshest_session}); "
                 "positioning level index-wide (SPY), stated per "
                 "forecast; earnings session = the calendar's "
                 "report date, the record carrying no timing."),
        "clocks": {
            "event_time": freshest["funds"]["SPY"]["run_ts"],
            "publication_time": map_card["built_utc"],
            "first_available_time": freshest["funds"]["SPY"]["run_ts"],
            "ingestion_time": map_card["built_utc"],
            "decision_as_of": freshest_session,
        },
    }
    created_total = 0
    for e in window_events:
        if e["priced_move_pct"] is None:
            continue
        arm = "main_negative_positioning" if \
            e["positioning_sign"] == "negative" else \
            "control_positive_positioning"
        _row, created = ledger.append_forecast_declared(
            engine_id=ENGINE_ID,
            issued_ts=freshest["funds"]["SPY"]["run_ts"],
            subject=e["symbol"],
            quantity=("Size of the earnings-day move against its "
                      "priced expected move (ratio, size only)"),
            value={"arm": arm,
                   "priced_move_pct": e["priced_move_pct"],
                   "claim_share_at_least": CLAIM_SHARE,
                   "claim_median_ratio_at_least": CLAIM_MEDIAN,
                   "positioning_level": "index",
                   "governing_index": e["governing_index"],
                   "positioning_sign": e["positioning_sign"],
                   "positioning_value_usd_per_1pct":
                       e["positioning_value_usd_per_1pct"],
                   "positioning_session": freshest_session},
            horizon_open=e["date"], horizon_close=e["date"],
            lineage=lineage,
            families=["modelled_inventory", "events_calendar"],
            outcome={"symbol": e["symbol"], "kind": "earnings_ratio",
                     "report_date": e["date"],
                     "priced_move_pct": e["priced_move_pct"],
                     "arm": arm})
        created_total += int(created)
    if not ledger.verify_chain():
        return fail("the forecast ledger's chain broke during append")

    recorded = graded = 0
    arms = {"main_negative_positioning": 0,
            "control_positive_positioning": 0}
    for row in ledger.rows():
        if row.get("engine_id") != ENGINE_ID:
            continue
        if row.get("type") == "forecast":
            recorded += 1
            arm = (row.get("value") or {}).get("arm")
            if arm in arms:
                arms[arm] += 1
        if row.get("type") == "grade":
            graded += 1

    data = {
        "tool": "Gamma-Pressure Earnings Trap",
        "state": "proving",
        "waiting": True,
        "source": SOURCE_WORDS,
        "published_at_utc": map_card["built_utc"],
        "panel_last_session": panel_last,
        "forecast": {
            "claim": ("For a stock in the index that reports "
                      "earnings within the next 5 trading days "
                      "while dealer positioning for the whole "
                      "index is negative, the size of its "
                      "earnings-day move, whichever way it goes, "
                      "will be bigger than the move the options "
                      "market priced in for at least 55 out of "
                      "every 100 such reports, and the middle "
                      "report's actual move will be at least "
                      "1.10 times its priced move."),
            "size_only": ("This forecast is about the SIZE of the "
                          "move only. It never says, and nothing "
                          "on this page says, which way any stock "
                          "will move."),
            "control": ("The comparison group: the same "
                        "measurement for earnings reports that "
                        "land while index-wide positioning is "
                        "positive, recorded at the same time and "
                        "graded in exactly the same way. The claim "
                        "above has to beat this group, not just a "
                        "coin flip."),
            "positioning_level": ("Every forecast states the "
                                  "positioning level it used. "
                                  "Today only the index-wide level "
                                  "exists. A per-stock positioning "
                                  "reading would need stored "
                                  "per-stock option chains, and "
                                  "the chain store holds "
                                  f"{chain_snapshots} snapshots, "
                                  "so no per-stock reading is used "
                                  "or implied.")},
        "missing_input": {
            "name": "the priced expected move for each report",
            "state": "absent",
            "detail": ("The calendar's priced-move field is empty "
                       f"for all {len(dated)} dated names. The "
                       "chain store that could carry a per-stock "
                       f"priced move holds {chain_snapshots} "
                       "snapshots. The expected-move page covers "
                       "the index funds only and is not a "
                       "per-stock earnings price. The per-stock "
                       "volatility record holds a volatility level, "
                       "not a priced move, and a level is never "
                       "turned into a priced move here. The first "
                       "record that carries a real priced move for "
                       "a coming report, for example the first "
                       "stored per-stock option chain, lets this "
                       "engine record forecasts unchanged.")},
        "calendar": {
            "recorded_on": recorded_on,
            "names_on_record": calendar["names_on_record"],
            "dated": len(dated),
            "no_date": calendar["names_with_no_date"],
            "priced_moves_on_record": len(priced_present),
            "stale_note": ("The calendar was gathered on "
                           "October 12, 2026, more than a week "
                           "before the newest map session, so by "
                           "its own page's rule it is old. Its "
                           "dates are shown as recorded, and any "
                           "date that has slipped will be caught "
                           "when the calendar is next gathered."),
            "timing_note": ("The calendar carries no report "
                            "timing, nothing about whether a "
                            "report lands before the open or after "
                            "the close. Until a record carries "
                            "timing, the report date itself is "
                            "counted as the earnings day. That is "
                            "a named gap in the record, not a "
                            "fact about the companies.")},
        "positioning": {
            "level": "index-wide",
            "freshest_session": freshest_session,
            "sessions_on_record": len(sessions),
            "sessions": sessions,
            "positive_sessions": len(positive_sessions),
            "note": ("On every session on record, the positioning "
                     "reading for each of SPY, QQQ and IWM is "
                     "negative. No positive session exists yet, "
                     "so the comparison group has no possible "
                     "events so far.")},
        "membership": {
            "sp500_on_record": len(sp500),
            "tagged_names_on_record": len(symbols),
            "note": ("The only index membership list on record is "
                     "the S&P list: 503 S&P 500 names among 1,503 "
                     "tagged names. No membership list for the "
                     "Nasdaq-100 or the Russell 2000 exists on "
                     "record, so membership is claimed for the "
                     "S&P 500 only. A name on the list is governed "
                     "by SPY as its own index; every other "
                     "calendar name is carried under SPY as the "
                     "stated fallback, and each report below "
                     "says which.")},
        "window": {
            "after_session": freshest_session,
            "sessions": window_days,
            "events": window_events,
            "count": len(window_events),
            "sp500_count": window_sp500,
            "forecasts_recorded_today": created_total,
            "reason_none": ("Every report in the window has its "
                            "date, its membership and its "
                            "positioning state on record. What "
                            "none of them has is a priced expected "
                            "move, so no forecast could be "
                            "recorded for any of them. Zero is "
                            "the count, not a gap in the page.")},
        "history": {
            "label": ("History: past reports carrying every input "
                      "the grading needs"),
            "qualifying_events": 0,
            "main_arm_graded": 0,
            "control_arm_graded": 0,
            "detail": ("No past report qualifies, in either "
                       "group. The past-earnings record holds a "
                       f"pooled summary only: {drift['events']} "
                       f"reports across {drift['name_count']} "
                       "names (AAPL, MSFT, NVDA), a pooled average "
                       "move of "
                       f"{drift['mean'] * 100:.2f} percent and a "
                       f"pooled middle of {drift['median'] * 100:.2f} "
                       "percent, gathered "
                       f"{drift['as_of']}. Individual report dates "
                       "and individual moves are not stored, no "
                       "priced move exists for any of those "
                       "reports, and positioning readings exist "
                       "only for October 2026 sessions, long after "
                       "them. With any one of the four inputs "
                       "missing, an event is not graded, so the "
                       "count is 0, stated plainly.")},
        "worked_example": {
            "label": ("A worked example on made-up numbers, "
                      "proving the arithmetic end to end"),
            "events": test["worked_events"],
            "summary": {
                "events": test["worked_summary"]["events"],
                "exceedances": test["worked_summary"]["exceedances"],
                "share": test["worked_summary"]["share"],
                "median_ratio": test["worked_summary"]["median_ratio"]},
            "note": ("These four reports are invented, in memory, "
                     "on every run: a priced move and a pair of "
                     "closing prices are made up, and the exact "
                     "code the live engine uses turns them into "
                     "ratios (actual move divided by priced move), "
                     "counts how many beat their priced move "
                     "(3 of 4, a 75 percent share) and takes the "
                     "middle ratio (1.15). The answers are checked "
                     "against hand-computed values. Invented "
                     "numbers are never written into the record "
                     "of real forecasts, and no real past report "
                     "is dressed up as an example, because no real "
                     "past report carries a priced move.")},
        "self_test": {"cases": test["cases"],
                      "passed": test["passed"]},
        "options_gate": chain_gate,
        "live": {"forecasts_recorded": recorded,
                 "forecasts_graded": graded,
                 "main_recorded": arms["main_negative_positioning"],
                 "control_recorded":
                     arms["control_positive_positioning"],
                 "target_events": KILL_EVENTS},
        "kill_criterion": (
            "After 60 graded events, this engine is retired if "
            "the share of reports beating their priced move could "
            "still plausibly be 50 percent (its confidence range "
            "includes 50 percent), or if the middle report's "
            "actual move is smaller than its priced move (a "
            "middle ratio below 1.0)."),
        "thin_rule": ("Below 30 graded events in either group, "
                      "counts only: no share and no middle ratio "
                      "is drawn from a handful of reports."),
        "grading_note": ("Grading waits on two things, both "
                         "stated plainly: the shared grading "
                         "machinery cannot yet score this kind of "
                         "actual-against-priced size result for a "
                         "group of reports, and the price history "
                         f"on record ends {panel_last}, before "
                         "every report date in the window."),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} (calendar {len(dated)} dated, "
          f"priced moves {len(priced_present)}; positioning "
          f"{len(sessions)} sessions, freshest {freshest_session} "
          f"SPY {spy_sign}; window {window_days[0]} to "
          f"{window_days[-1]}: {len(window_events)} reports, "
          f"{window_sp500} S&P 500; qualifying history 0; "
          f"{created_total} new forecasts, {recorded} recorded "
          "in total)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
