#!/usr/bin/env python3
"""Refresh the Own Capitulation Volume Clock (Forecast Engine 16).

=====================================================================
CANDIDATE-REGISTER TRIPLE (written before any computation, per the
lineup's adopted standards)

1. EVIDENCE CLASS
   - Study row F6 (grade B, two eras, long daily history 2016-2026):
     "high recent down volume in resets is better": rank correlation
     +0.040 and +0.020 across the two eras; top-vs-bottom fifth
     spreads +0.95 and +1.28 points.
   - Study row new10 N6 (volume-confirmed capitulation): rank
     correlation +0.016 (strength 4.2) in the discovery sample and
     +0.015 (strength 3.9) in the holdout, on all days; about zero
     on fear days.
   - Study row A9 (grade B avoid) enters only as a structural gate:
     buying far above the day's low and surges in trading activity
     are a strong avoid in stretched names, so this engine fires
     only inside a drawdown, never on an up-move.
   - THE STANDING TENSION, named before computing: the reset
     study's f_voldie row passed with the opposite sign (negative)
     at both 20 and 60 sessions in both eras, over 32,460 reset
     rows; it defines the volume state differently (volume dying
     away, not volume surging on down days), and it points the
     other way. This engine follows F6's stated definition and
     direction (high down volume inside a fall is the better
     state) and prints the tension on its page in plain words.
   - Both parent studies ran on a long history of names including
     ones that later stopped trading; the history that exists on
     this disk is a roster of names that still trade, and that
     survivors-only caveat is carried on the page.
   - This engine's own live record: none yet; it starts here.

2. RECONSTRUCTION CHOICES (every constant, named before computing)
   - No coded formula from F6 or N6 is readable on this disk (the
     records state the words and the figures only), so every
     operational definition below is a registered RECONSTRUCTION,
     named as such; nothing on the page claims a coded parent
     definition was copied.
   - Data: the shipped daily panel only (date, open, high, low,
     close, share volume). Share volume is never called a trade
     count. No hourly volume of any kind is used: the standing
     desk law bars Yahoo hourly volume as corrupt, and no
     substitute is made. Subjects are every name except SPY;
     SPY is the yardstick only.
   - Drawdown gate (the A9 gate, structural): the name's close
     today is strictly below the mean of its prior 200 closes
     (its own sessions t-200 to t-1, today left out).
   - Down session: close below the previous close. A session's
     down-volume value is its share volume when it is a down
     session. The down-volume history at t is the share volumes
     of all prior down sessions (own sessions 1 to t-1), today
     left out; fewer than 30 prior down-volume readings and the
     name-session abstains and is counted.
   - Trigger, both halves required on the same session: the
     session is a down session whose share volume is strictly
     above the 95th percentile of its own down-volume history,
     AND its total share volume is strictly above the 90th
     percentile of all its prior sessions' total share volumes
     (today left out both times). The candidate's "trade/range
     activity" wording is not computable from this panel (no
     trade count exists); total share volume is the activity
     measure, and none other is substituted silently.
   - Percentiles: type-7 straight-line interpolation (the
     programme standard, Engines 13/14 precedent).
   - Warm-up: the 200 prior sessions for the gate bind. The
     first evaluable session is a name's own session index 200
     (for names on the full market calendar, 2026-01-09); names
     with 200 or fewer sessions on record never evaluate and are
     counted as abstentions.
   - Episodes: after an episode at t, raw triggers at t+1 to
     t+10 are suppressed and counted; the next eligible session
     is t+11.
   - RETURN half, graded exactly: 20-session excess in points =
     100 x [(name close on the market-calendar session 20 after
     the trigger / name close at trigger - 1) - (SPY close then
     / SPY close at trigger - 1)]. Both closes required or the
     episode stays ungraded and is counted pending/missing.
     Claim: the median graded excess is at least +1.0 point.
   - EXHAUSTION half, graded exactly: the name's own median
     total share volume is the type-7 median of all its prior
     sessions' total share volumes, FROZEN at trigger time.
     Success: some session in t+1 to t+10 (the name's own
     sessions) prints share volume strictly below that frozen
     median. Success can be settled early; failure only after
     all 10 sessions pass with no such print, else pending.
     Claim: the success share is at least 60 percent.
   - Confidence ranges: no method is named in any record, so
     these are registered RECONSTRUCTIONS (Engine 13 precedent):
     a distribution-free exact-binomial order-statistic 95
     percent range for the return median (its null is 0 points)
     and a Wilson 95 percent range for the exhaustion share
     (its null is 50 percent, plain chance).
   - Kill criterion, per half: after 200 graded episodes, a
     half retires if its confidence range still includes its
     null (0 points for the return half, 50 percent for the
     exhaustion half). Either half failing falsifies that half
     only; the halves are always graded and shown separately.
   - Ledger shape: one forecast per half per triggering name.
     Return half: quantity median_20_session_excess_points,
     value {"estimate": 1.0}. Exhaustion half: quantity
     chance_volume_below_own_median_within_10_sessions, value
     {"p": 0.6}, with the frozen own median carried in its
     outcome spec. The shared grading runner resolves the
     two-symbol 20-session excess through kind
     "excess_return_points" (new rows) and the registered
     legacy map for rows issued under kind "return" (RC-19
     cure, 2026-10-30), and the volume-below-frozen-median
     event through its own resolver; no live row can mature
     until the price source passes its horizon in any case. Nothing from the
     history computation is ever written to the live ledger;
     only live forecasts are, through the machinery's own
     append call, never backfilled.
   - Thin-cell rule: below 30 graded episodes in a half, counts
     only: no median, no share and no range is published.

3. NON-CLAIMS
   - The history figures are this construction's past on a
     roster of names that still trade; they are not the parent
     studies' figures and not a live record.
   - Neither half's claim is a result until this engine's own
     ledgered episodes mature; the engine ships proving.
   - Share volume says how many shares changed hands, never
     how many trades happened, and nothing here reads it as
     anything else.

=====================================================================
Behaviour: validate the shipped panel (fails closed on any
disagreement), recompute the full history with both halves
graded separately, compute today's triggers, ledger any live
forecasts through forecast/ledger.py append_forecast (never
hand-edited), then write data.json from the panel plus figures
recomputed from the ledger alone. Idempotent: rerunning with
the same panel appends nothing and rewrites the same data.json.
Timestamps come from the sources, never the clock.
"""

import bisect
import json
import math
import os
import sys
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(HERE)
PANEL_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")
OUT_PATH = os.path.join(HERE, "capitulation-clock", "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import attestation_block as _ab
except ImportError:  # refresh stays runnable standalone
    _ab = None

sys.path.insert(0, LINEUP)
from forecast import ledger as ledger_mod  # noqa: E402
from forecast import registry as registry_mod  # noqa: E402

ENGINE_ID = "engine_16"
WARMUP = 200               # prior sessions for the 200-session mean
DOWN_FLOOR = 30            # prior down-volume readings required
P_DOWN = 0.95              # down-volume percentile line
P_ACT = 0.90               # activity percentile line
LOCKOUT = 10               # sessions suppressed after an episode
RET_HORIZON = 20           # sessions, return half
EXH_HORIZON = 10           # sessions, exhaustion half
CLAIM_RETURN = 1.0         # points, median excess at least this
CLAIM_EXHAUST = 0.60       # success share at least this
THIN = 30                  # graded episodes below this: counts only
KILL_EPISODES = 200        # graded episodes per half for the kill test


def fail(msg):
    print(f"Capitulation Clock refresh: {msg}", file=sys.stderr)
    return 1


def pctile(sorted_vals, q):
    """Type-7 straight-line percentile of an ascending list."""
    n = len(sorted_vals)
    if n == 0:
        return None
    pos = q * (n - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return sorted_vals[lo]
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def median_ci_ranks(n):
    """(lower_rank, upper_rank), 1-based order-statistic ranks for a
    distribution-free 95% range for the median (Engine 13 form)."""
    if n < 2:
        return None
    log_half = math.log(0.5)
    cum = 0.0
    k_found = 1
    for j in range(0, n // 2 + 1):
        log_pmf = (math.lgamma(n + 1) - math.lgamma(j + 1)
                   - math.lgamma(n - j + 1) + n * log_half)
        cum += math.exp(log_pmf) if log_pmf > -745 else 0.0
        if cum <= 0.025:
            k_found = j + 1
        else:
            break
    return k_found, n - k_found + 1


def wilson(k, n):
    """Wilson 95 percent range for a share k/n."""
    if n == 0:
        return None
    z = 1.959963984540054
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [round(max(0.0, centre - half) * 100.0, 1),
            round(min(1.0, centre + half) * 100.0, 1)]


def next_sessions(after_iso, count):
    d = date.fromisoformat(after_iso)
    out = []
    while len(out) < count:
        d += timedelta(days=1)
        if d.weekday() < 5:
            out.append(d.isoformat())
    return out


def build():
    if not os.path.exists(PANEL_PATH):
        return fail(f"daily price history not found: {PANEL_PATH}")
    panel_sha = ledger_mod.file_sha256(PANEL_PATH)
    with open(PANEL_PATH, "r", encoding="utf-8") as fh:
        panel = json.load(fh)

    # ---- Validate the shipped daily history (fails closed) ----
    if "SPY" not in panel:
        return fail("the shipped daily history carries no SPY")
    spy_rows = sorted(panel["SPY"], key=lambda r: r[0])
    dates = [r[0] for r in spy_rows]
    if dates != sorted(set(dates)):
        return fail("SPY dates in the shipped history are not a clean "
                    "increasing session list")
    n_sessions = len(dates)
    date_index = {d: i for i, d in enumerate(dates)}
    spy_close = {r[0]: float(r[4]) for r in spy_rows}
    as_of = dates[-1]
    for sym, rows in panel.items():
        for r in rows:
            if len(r) != 6:
                return fail(f"{sym} carries a row that is not "
                            f"[date, open, high, low, close, volume]")

    # ---- Full history: every name, halves always separate ----
    raw_triggers = 0
    suppressed = 0
    episodes = []            # (symbol, date, own_index)
    floor_abstentions = 0    # name-sessions stopped by the 30 floor
    never_eval = []          # subjects with <= WARMUP sessions
    today_triggers = []      # post-lockout episodes on the as-of day
    today_suppressed = 0
    today_gate_blocked = []  # both extremes printed, not in a drawdown
    today_one_line = 0       # in a drawdown, exactly one line cleared
    names_checked = 0
    names_judged_today = 0
    ret_excesses = []
    ret_pending = 0
    exh_graded = 0
    exh_success = 0
    exh_pending = 0

    for sym in sorted(panel):
        if sym == "SPY":
            continue
        names_checked += 1
        rows = sorted(panel[sym], key=lambda r: r[0])
        ds = [r[0] for r in rows]
        cl = [float(r[4]) for r in rows]
        vo = [float(r[5]) for r in rows]
        n = len(rows)
        if n <= WARMUP:
            never_eval.append(sym)
        pref = [0.0]
        for c in cl:
            pref.append(pref[-1] + c)
        down_vols = []       # sorted share volumes of prior down sessions
        all_vols = []        # sorted share volumes of prior sessions
        last_ep = -10 ** 9
        judged_today = False
        for i in range(n):
            if i >= 1:
                j = i - 1
                bisect.insort(all_vols, vo[j])
                if j >= 1 and cl[j] < cl[j - 1]:
                    bisect.insort(down_vols, vo[j])
            if i < WARMUP:
                continue
            if ds[i] == as_of:
                judged_today = True
            if len(down_vols) < DOWN_FLOOR:
                floor_abstentions += 1
                continue
            in_dd = cl[i] < (pref[i] - pref[i - WARMUP]) / WARMUP
            is_down = cl[i] < cl[i - 1]
            p95 = pctile(down_vols, P_DOWN)
            p90 = pctile(all_vols, P_ACT)
            vol_extreme = is_down and vo[i] > p95
            act_extreme = vo[i] > p90
            is_today = ds[i] == as_of
            if vol_extreme and act_extreme:
                if not in_dd:
                    if is_today:
                        today_gate_blocked.append(sym)
                    continue
                raw_triggers += 1
                if i - last_ep <= LOCKOUT:
                    suppressed += 1
                    if is_today:
                        today_suppressed += 1
                    continue
                last_ep = i
                episodes.append((sym, ds[i]))
                if is_today:
                    today_triggers.append({
                        "symbol": sym,
                        "down_volume_times_line": round(vo[i] / p95, 2),
                        "activity_times_line": round(vo[i] / p90, 2),
                        "frozen_own_median_volume": pctile(all_vols, 0.5)})
                # RETURN half
                s = date_index[ds[i]]
                cd = {r[0]: float(r[4]) for r in rows}
                if s + RET_HORIZON < n_sessions \
                        and dates[s + RET_HORIZON] in cd:
                    fwd = dates[s + RET_HORIZON]
                    exc = ((cd[fwd] / cl[i] - 1.0)
                           - (spy_close[fwd] / spy_close[ds[i]] - 1.0))
                    ret_excesses.append(exc * 100.0)
                else:
                    ret_pending += 1
                # EXHAUSTION half (median frozen at trigger)
                med = pctile(all_vols, 0.5)
                succ = None
                seen = 0
                for k in range(i + 1, min(i + 1 + EXH_HORIZON, n)):
                    seen += 1
                    if vo[k] < med:
                        succ = True
                        break
                if succ is None and seen == EXH_HORIZON:
                    succ = False
                if succ is None:
                    exh_pending += 1
                else:
                    exh_graded += 1
                    exh_success += 1 if succ else 0
            elif is_today and in_dd and (vol_extreme != act_extreme):
                today_one_line += 1
        if judged_today:
            names_judged_today += 1

    if len(never_eval) + 0 > names_checked:
        return fail("abstention counts do not add up")

    ret_excesses.sort()
    ret = {"episodes": len(episodes), "graded": len(ret_excesses),
           "pending": ret_pending, "claim_points": CLAIM_RETURN}
    if len(ret_excesses) >= THIN:
        m = len(ret_excesses)
        med = ret_excesses[m // 2] if m % 2 else \
            (ret_excesses[m // 2 - 1] + ret_excesses[m // 2]) / 2.0
        ret["median_points"] = round(med, 2)
        ranks = median_ci_ranks(m)
        if ranks:
            lo, hi = ranks
            ret["median_ci95_points"] = [round(ret_excesses[lo - 1], 2),
                                         round(ret_excesses[hi - 1], 2)]
        ret["claim_met"] = med >= CLAIM_RETURN
        ret["falsified"] = med < 0
    exh = {"episodes": len(episodes), "graded": exh_graded,
           "pending": exh_pending, "successes": exh_success,
           "claim_pct": round(CLAIM_EXHAUST * 100)}
    if exh_graded >= THIN:
        share = exh_success / exh_graded
        exh["share_pct"] = round(share * 100.0, 1)
        exh["share_ci95_pct"] = wilson(exh_success, exh_graded)
        exh["claim_met"] = share >= CLAIM_EXHAUST
        exh["falsified"] = share < 0.5
    ep_dates = [d for _s, d in episodes]
    distinct_names = len({s for s, _d in episodes})

    # ---- Ledger (API only) ----
    reg = registry_mod.load()
    led = ledger_mod.Ledger(
        os.path.join(LINEUP, "forecast", "ledger.jsonl"), registry=reg)
    rows_before = led.rows()
    if not led.verify_chain(rows_before):
        return fail("the forecast record does not verify; refusing "
                    "to add to it")
    figures_before = ledger_mod.recompute_figures(rows_before)
    recorded_before = figures_before.get(ENGINE_ID, {}).get("forecasts", 0)

    created = 0
    if today_triggers:
        fut_ret = next_sessions(as_of, RET_HORIZON)
        fut_exh = next_sessions(as_of, EXH_HORIZON)
        lineage = {
            "source_artifacts": [
                {"path": PANEL_PATH, "sha256": panel_sha}],
            "clocks": {
                "event_time": as_of,
                "publication_time": fut_exh[0],
                "first_available_time": as_of,
                "ingestion_time": as_of,
                "decision_as_of": as_of},
            "note": ("Capitulation volume forecasts from the close "
                     "of the as-of session, one row per half per "
                     "name. The return value is the claimed middle "
                     "20-session gain against SPY, in points; the "
                     "exhaustion value is the claimed chance that "
                     "share volume falls below the name's own "
                     "typical day (frozen at the trigger) within "
                     "10 sessions.")}
        for item in today_triggers:
            sym = item["symbol"]
            _row, was = led.append_forecast_declared(
                engine_id=ENGINE_ID, issued_ts=fut_exh[0], subject=sym,
                quantity="median_20_session_excess_points",
                value={"estimate": CLAIM_RETURN},
                horizon_open=fut_ret[0], horizon_close=fut_ret[-1],
                lineage=lineage, families=["price"],
                outcome={"symbol": sym,
                         "kind": "excess_return_points",
                         "benchmark": "SPY",
                         "base_date": as_of, "at_date": fut_ret[-1]})
            created += 1 if was else 0
            _row, was = led.append_forecast_declared(
                engine_id=ENGINE_ID, issued_ts=fut_exh[0], subject=sym,
                quantity="chance_volume_below_own_median_within_10_sessions",
                value={"p": CLAIM_EXHAUST},
                horizon_open=fut_exh[0], horizon_close=fut_exh[-1],
                lineage=lineage, families=["price"],
                outcome={"symbol": sym,
                         "kind": "volume_below_frozen_median",
                         "frozen_median_volume":
                             item["frozen_own_median_volume"],
                         "base_date": as_of, "at_date": fut_exh[-1]})
            created += 1 if was else 0
    rows_after = led.rows()
    if not led.verify_chain(rows_after):
        return fail("the forecast record failed verification after "
                    "writing; not publishing figures from it")
    figures = ledger_mod.recompute_figures(rows_after)
    mine = figures.get(ENGINE_ID, {"forecasts": 0, "graded": 0})
    if mine["forecasts"] != recorded_before + created:
        return fail("ledger figures do not match the live rows expected")
    live_subjects = {r["subject"] for r in rows_after
                     if r.get("type") == "forecast"
                     and r.get("engine_id") == ENGINE_ID}
    graded_rows = [r for r in rows_after if r.get("type") == "grade"
                   and r.get("engine_id") == ENGINE_ID]
    graded_by_q = {}
    fc_by_id = {r["row_id"]: r for r in rows_after
                if r.get("type") == "forecast"}
    for r in graded_rows:
        q = fc_by_id.get(r["forecast_row_id"], {}).get("quantity", "?")
        graded_by_q[q] = graded_by_q.get(q, 0) + 1

    today_out = [{k: v for k, v in t.items()
                  if k != "frozen_own_median_volume"}
                 for t in today_triggers]
    today_out.sort(key=lambda x: x["symbol"])
    today_gate_blocked.sort()

    data = {
        "tool": "Own Capitulation Volume Clock",
        "state": "proving",
        "as_of_session": as_of,
        "source": (f"The daily price and share-volume history on "
                   f"record ({names_checked:,} stocks plus the broad "
                   f"market fund they are measured against, "
                   f"{dates[0]} to {as_of}, {n_sessions} trading "
                   f"days), checked for this page. The longer daily "
                   f"history the parent studies ran on (2016 to "
                   f"2026) is not on this computer, so the history "
                   f"below runs on the history that exists, which "
                   f"holds only stocks that still trade."),
        "trigger_words": (
            "A stock counts as printing capitulation volume on a "
            "day when three things line up. First, it is in a "
            "fall of its own: its price sits below its own average "
            "price of the past 200 trading days. Second, on a day "
            "it fell, the shares that changed hands were heavier "
            "than on 95 of every 100 of its own past falling days. "
            "Third, its total trading that day was heavier than "
            "on 90 of every 100 of its own past days. One name can "
            "start a new episode at most once every 11 trading "
            "days, so a long heavy spell counts once, not daily."),
        "claims": {
            "return_half": ("The middle stock that prints this "
                            "will beat the broad market by at "
                            "least 1.0 point over the next 20 "
                            "trading days."),
            "exhaustion_half": ("In at least 60 of every 100 "
                                "cases, the stock's daily trading "
                                "will fall back below its own "
                                "typical day within 10 trading "
                                "days: the heavy selling burns "
                                "itself out."),
            "separate_words": ("The two halves are graded "
                               "separately. Either half can fail "
                               "on its own, and a failed half is "
                               "retired on its own."),
        },
        "gate_words": (
            "The same heavy trading on a rising stock is treated "
            "by an older finding as a warning sign, not a buying "
            "sign. So this tool only ever fires on a stock that "
            "is already in a fall of its own, and never on a "
            "stock that is rising."),
        "tension_words": (
            "One earlier study points the other way. It measured "
            "a nearby but different thing, trading drying up "
            "after a fall rather than trading surging on falling "
            "days, and it found the drying-up version predicted "
            "worse, not better, days ahead, in both stretches of "
            "years it checked. This tool follows the surging "
            "version, the one two other studies found pointed "
            "up, and prints the disagreement here rather than "
            "hiding it. The live record below is what will "
            "settle which reading is right for this exact "
            "definition."),
        "today": {
            "names_checked": names_checked,
            "names_judged": names_judged_today,
            "names_set_aside": names_checked - names_judged_today,
            "triggers": today_out,
            "trigger_count": len(today_out),
            "suppressed_repeats_today": today_suppressed,
            "gate_blocked": today_gate_blocked,
            "gate_blocked_count": len(today_gate_blocked),
            "one_line_count": today_one_line,
            "notes": (
                "Names that printed both kinds of heavy trading "
                "today but are not in a fall of their own are "
                "listed as held back by the gate, and no forecast "
                "is made about them. Names in a fall that cleared "
                "only one of the two heavy-trading lines are "
                "counted too."),
        },
        "history": {
            "label": "History, not live forecasts",
            "span": f"{min(ep_dates)} to {max(ep_dates)}",
            "warmup_note": (
                f"Judging a day against a stock's own past needs "
                f"200 of its past trading days first, so the "
                f"first judgeable day is a stock's 201st trading "
                f"day on record (January 9, 2026 for stocks with "
                f"a full record) and {len(never_eval)} stocks "
                f"have too little history to be judged at all. "
                f"On {floor_abstentions} stock-days the falling-"
                f"day record was still too short (fewer than 30 "
                f"past falling days), so those days were set "
                f"aside and counted. Every stock in this history "
                f"still trades today; stocks that stopped trading "
                f"are not in it, which can flatter the numbers."),
            "raw_triggers": raw_triggers,
            "suppressed_repeats": suppressed,
            "episodes": len(episodes),
            "distinct_names": distinct_names,
            "return_half": ret,
            "exhaustion_half": exh,
        },
        "study_record": {
            "label": "The earlier studies this tool is built from",
            "f6": ("In the long study (2016 to 2026), heavy "
                   "trading on falling days inside a fall lined "
                   "up with better days ahead in both stretches "
                   "of years checked: the link measured +0.040 "
                   "and +0.020, and the heaviest fifth beat the "
                   "lightest fifth by 0.95 and 1.28 points."),
            "n6": ("A second study of volume-confirmed falls "
                   "found the same direction: the link measured "
                   "+0.016 and +0.015 in its two samples."),
        },
        "live": {
            "episodes_recorded": len(live_subjects),
            "forecasts_recorded": mine["forecasts"],
            "graded_return_half": graded_by_q.get(
                "median_20_session_excess_points", 0),
            "graded_exhaustion_half": graded_by_q.get(
                "chance_volume_below_own_median_within_10_sessions", 0),
            "target_episodes": KILL_EPISODES,
            "note": ("Episodes are written down at the close "
                     "that triggers them, before the days they "
                     "describe. The return half grades 20 trading "
                     "days later and the exhaustion half within "
                     "10, so the first grades land only after "
                     "those days pass."),
        },
        "kill_criterion": (
            "After 200 graded episodes, either half retires on "
            "its own if its figures could still plausibly be "
            "nothing: for the return half, if the middle gain "
            "could still be zero; for the exhaustion half, if "
            "the share settling down could still be a coin flip."),
        "thin_cell_rule": (
            "Any half with fewer than 30 graded episodes shows "
            "its count only, with no middle figure and no share."),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH}: as of {as_of}; history raw "
          f"{raw_triggers}, suppressed {suppressed}, episodes "
          f"{len(episodes)} on {distinct_names} names; return "
          f"graded {ret['graded']} median "
          f"{ret.get('median_points')}; exhaustion graded "
          f"{exh_graded} share {exh.get('share_pct')}%; today "
          f"{len(today_out)} triggers, {len(today_gate_blocked)} "
          f"gate-blocked, {today_one_line} one-line; ledger "
          f"forecasts {mine['forecasts']} ({created} new)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
