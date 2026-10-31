#!/usr/bin/env python3
"""Refresh the Idiosyncratic-or-Liquidity Splitter (Forecast Engine 13).

=====================================================================
CANDIDATE-REGISTER TRIPLE (written before any computation, per the
lineup's adopted standards)

1. EVIDENCE CLASS
   Two graded findings from the corpus's evidence record, joined
   into one conditional forecast:
   - Company-specific declines do worse (study row F4, filed as
     avoid A15, grade B): rank correlation -0.012 and -0.022 at 60
     sessions in 2023 onward across two eras; the idiosyncratic
     share's top tenth was a veto (top tenth -3.5%, strength -2.6;
     next slice -2.1%, strength -2.5 in study row AD-67).
   - Reversal in stress (study row T2, grade A): last-day return
     rank correlation -0.058 and -0.028 in the deepest market
     drawdown third; 393 stress-reversal confirmations against a
     null of 17; one-week peer-gap reversal +0.017, strength 4.4.
   One dataset family (daily prices) sits behind both parents,
   and the discovery ran on a roster of stocks that still trade
   (the D3 caveat carried by Engine 4). This engine's own live
   record: none yet; it starts here.

2. RECONSTRUCTION CHOICES (every constant, named before computing)
   - No coded definition from either parent study is readable on
     this disk (the study files exist only as summary rows), so
     the construction below is a registered RECONSTRUCTION, named
     as such, following this programme's own conventions wherever
     they exist.
   - Residual: a name's close-to-close return minus SPY's
     close-to-close return on the same session (beta 1, the
     programme's own "excess against SPY" convention everywhere:
     the grading runner and Engines 3 and 4 all use the simple
     difference of returns; no beta is estimated anywhere on this
     programme). The part of a move that is the name's own, after
     the market's move that day is taken out.
   - Residual share: |residual| / (|residual| + |SPY return|),
     between 0 and 1 by construction (matching the parent
     record's share capped at 1, with a mass at 1 when SPY is
     flat or moves against the name). "The name's own move
     dominates" = share above 0.5.
   - Own residual-vol: the sample standard deviation (ddof 1) of
     the name's residuals over the trailing 126 sessions ending
     yesterday, every one of the 126 residuals present on the
     SPY session calendar or the name is not judged that day.
     The window's own mean is trailing and leaves today out, so
     every own mean used satisfies the leave-out centring law
     (study row D2): today is never centred by a mean containing
     today, and the trigger uses the raw residual.
   - Trigger: today's residual at or below -2 times that own
     residual-vol (a drop of at least 2 of the name's own units).
     A fixed percent threshold is never used.
   - Legs (a trigger is assigned to exactly one):
     PERSIST: SPY flat or up today (return >= 0) and share > 0.5.
       Forecast: the leg's middle (median) 20-session excess
       return against SPY is at most -0.5 points.
     REVERSE: a fear day, SPY down at least 1 percent today (the
       house fear-day definition already in use on this
       programme). Forecast: the leg's median 20-session excess
       is at least +0.5 points.
     NEITHER: any other trigger (SPY down between 0 and -1
       percent, or share at most 0.5 on a flat/up day). Counted
       and named, never assigned to a leg.
     The two legs are graded separately and never netted.
   - Grading, exact: per case, the 20-session excess in points =
     100 x [(name close 20 sessions later / name close today - 1)
     - (SPY close 20 sessions later / SPY close today - 1)], the
     later session counted on the SPY calendar. Both closes
     required or the case stays ungraded and is counted missing.
     Leg statistic = the median of its graded excesses. A leg is
     falsified only if its median lands on the wrong side of
     zero; landing between zero and the claim means the claim is
     not met, not falsified.
   - Confidence range for a median: NO method is named in any
     record, so this is a registered RECONSTRUCTION: a
     distribution-free 95 percent range from order statistics
     with exact binomial ranks (the rank whose Bin(n, 0.5)
     cumulative probability first exceeds 0.025 on each side).
   - Episodes: every qualifying name-day counts; the design
     names no lockout, so overlapping 20-session windows count
     as separate cases.
   - Data reality: the design's route names the long daily
     history (2016-2026), which is not on this disk. The history
     below runs on the history that exists: the shipped daily
     panel (1,833 names including SPY, 399 SPY sessions,
     2025-03-25 to 2026-10-23). Warm-up at the 126-session
     window: the first judgeable session is 2025-09-25, leaving
     272 judgeable sessions; a name's first judgeable session is
     later where its own window has gaps. The claim runs on
     this history, stated as such.
   - Ledger shape: one forecast per qualifying name per leg per
     issue day, value {"estimate": -0.5} for the persist leg and
     {"estimate": +0.5} for the reverse leg (the leg's claimed
     median, in points). The outcome spec is the name's own
     20-session excess against SPY: new rows carry kind
     "excess_return_points" with benchmark SPY (RC-19 cure,
     2026-10-30), and rows issued before that date under kind
     "return" resolve through the registered legacy map in
     forecast/registry.json, so the grading pass resolves both
     legs from the same price source and grades the estimate,
     in points, against the excess in points. The registered
     grading rule is the point-error rule. Nothing from the history computation is ever written
     to the live ledger; only live forecasts are, through the
     machinery's own append call, never backfilled.
   - Thin-cell rule: below 30 graded cases in a leg, counts
     only: no median and no range is published for that leg.
   - Kill criterion: a leg retires on its own if, after 150 of
     its graded cases, its median's confidence range still
     includes zero.

3. NON-CLAIMS
   - The history medians are this construction's past, computed
     on a roster of stocks that still trade; they are not the
     parent studies' figures and not a live record.
   - Neither leg's claim is a result until this engine's own
     ledgered cases mature; the engine ships in proving state.
   - The two legs are opposite-signed by design; no combined
     or net figure across legs is ever published.

=====================================================================
Behaviour: validate the shipped panel (fails closed on any
disagreement), recompute the full history per leg, compute
today's qualifying names per leg, ledger any live forecasts
through forecast/ledger.py append_forecast (never hand-edited),
then write data.json from the panel plus figures recomputed from
the ledger alone. Idempotent: rerunning with the same panel
appends nothing and rewrites the same data.json. Timestamps come
from the sources, never the clock.
"""

import json
import math
import os
import sys
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(HERE)
PANEL_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")
OUT_PATH = os.path.join(HERE, "idio-liquidity", "data.json")
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

ENGINE_ID = "engine_13"
WINDOW = 126              # trailing residual sessions ending yesterday
TRIGGER_UNITS = 2.0       # residual <= -2 x own residual-vol
HORIZON = 20              # sessions
FEAR_DROP = -0.01         # SPY one-session return at or below this
SHARE_MIN = 0.5           # residual share must exceed this (persist leg)
CLAIM_PERSIST = -0.5      # points, median excess at most this
CLAIM_REVERSE = 0.5       # points, median excess at least this
THIN = 30                 # graded cases below this: counts only
KILL_EPISODES = 150       # graded cases per leg for the kill test


def fail(msg):
    print(f"Idio-Liquidity refresh: {msg}", file=sys.stderr)
    return 1


def median_of(sorted_vals):
    n = len(sorted_vals)
    if n == 0:
        return None
    mid = n // 2
    if n % 2:
        return sorted_vals[mid]
    return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0


def median_ci_ranks(n):
    """(lower_rank, upper_rank), 1-based order-statistic ranks for a
    distribution-free 95% range for the median: the largest k with
    P(Bin(n, 0.5) <= k-1) <= 0.025; upper rank is n-k+1."""
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


def leg_stats(excesses):
    """excesses: graded 20-session excess returns in points."""
    s = sorted(excesses)
    out = {"graded": len(s)}
    if len(s) >= THIN:
        med = median_of(s)
        ranks = median_ci_ranks(len(s))
        out["median_points"] = round(med, 3)
        if ranks:
            lo, hi = ranks
            out["median_ci95_points"] = [round(s[lo - 1], 3),
                                         round(s[hi - 1], 3)]
    return out


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
    spy_close = [float(r[4]) for r in spy_rows]
    spy_ret = [None] + [spy_close[i] / spy_close[i - 1] - 1.0
                        for i in range(1, n_sessions)]
    as_of = dates[-1]
    date_index = {d: i for i, d in enumerate(dates)}
    fear_days = sum(1 for i in range(1, n_sessions)
                    if spy_ret[i] <= FEAR_DROP)
    fear_days_evaluable = sum(1 for i in range(WINDOW + 1, n_sessions)
                              if spy_ret[i] <= FEAR_DROP)

    # ---- Full history: every name, per leg, never netted ----
    legs = {"persist": {"excesses": [], "episodes": 0, "days": set(),
                        "with_forward_session": 0, "missing_closes": 0},
            "reverse": {"excesses": [], "episodes": 0, "days": set(),
                        "with_forward_session": 0, "missing_closes": 0}}
    triggers_total = 0
    neither_episodes = 0
    today = {"persist": [], "reverse": [], "neither": []}
    names_checked = 0
    names_evaluable_today = 0
    names_excluded_today = 0

    for sym in sorted(panel):
        if sym == "SPY":
            continue
        names_checked += 1
        rows = sorted(panel[sym], key=lambda r: r[0])
        closes = {r[0]: float(r[4]) for r in rows}
        resid = [None] * n_sessions
        for i in range(1, n_sessions):
            d, dp = dates[i], dates[i - 1]
            if d in closes and dp in closes:
                resid[i] = closes[d] / closes[dp] - 1.0 - spy_ret[i]
        # prefix sums over residuals (missing counts tracked apart)
        cnt = [0] * (n_sessions + 1)
        s1 = [0.0] * (n_sessions + 1)
        s2 = [0.0] * (n_sessions + 1)
        for i in range(n_sessions):
            v = resid[i]
            cnt[i + 1] = cnt[i] + (1 if v is not None else 0)
            s1[i + 1] = s1[i] + (v if v is not None else 0.0)
            s2[i + 1] = s2[i] + (v * v if v is not None else 0.0)
        evaluable_today = False
        for i in range(WINDOW + 1, n_sessions):
            if resid[i] is None:
                continue
            lo = i - WINDOW
            if cnt[i] - cnt[lo] != WINDOW:
                continue
            mean = (s1[i] - s1[lo]) / WINDOW
            var = ((s2[i] - s2[lo]) - WINDOW * mean * mean) / (WINDOW - 1)
            if var <= 0:
                continue
            sd = math.sqrt(var)
            if i == n_sessions - 1:
                evaluable_today = True
            r = resid[i]
            if r > -TRIGGER_UNITS * sd:
                continue
            triggers_total += 1
            sr = spy_ret[i]
            denom = abs(r) + abs(sr)
            share = abs(r) / denom if denom > 0 else 1.0
            if sr >= 0 and share > SHARE_MIN:
                leg = "persist"
            elif sr <= FEAR_DROP:
                leg = "reverse"
            else:
                leg = "neither"
            z = r / sd
            if i == n_sessions - 1:
                today[leg].append({
                    "symbol": sym,
                    "drop_own_units": round(-z, 2),
                    "own_move_pct": round(r * 100.0, 2),
                    "share_pct": round(share * 100.0, 1)})
            if leg == "neither":
                neither_episodes += 1
                continue
            L = legs[leg]
            L["episodes"] += 1
            L["days"].add(dates[i])
            if i + HORIZON < n_sessions:
                L["with_forward_session"] += 1
                fwd = dates[i + HORIZON]
                if fwd in closes:
                    exc = ((closes[fwd] / closes[dates[i]] - 1.0)
                           - (spy_close[i + HORIZON] / spy_close[i] - 1.0))
                    L["excesses"].append(exc * 100.0)
                else:
                    L["missing_closes"] += 1
        if evaluable_today:
            names_evaluable_today += 1
        else:
            names_excluded_today += 1

    if names_evaluable_today + names_excluded_today != names_checked:
        return fail("today's name counts do not add up")
    hist = {}
    for leg, claim in (("persist", CLAIM_PERSIST), ("reverse", CLAIM_REVERSE)):
        L = legs[leg]
        st = leg_stats(L["excesses"])
        entry = {"episodes": L["episodes"], "days": len(L["days"]),
                 "with_forward_session": L["with_forward_session"],
                 "missing_closes": L["missing_closes"]}
        entry.update(st)
        if st["graded"] >= THIN and "median_points" in st:
            med = st["median_points"]
            entry["claim_points"] = claim
            entry["claim_met"] = (med <= claim) if leg == "persist" \
                else (med >= claim)
            entry["falsified"] = (med > 0) if leg == "persist" \
                else (med < 0)
        hist[leg] = entry

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
    live_names = {"persist": today["persist"], "reverse": today["reverse"]}
    if live_names["persist"] or live_names["reverse"]:
        fut = next_sessions(as_of, HORIZON)
        lineage = {
            "source_artifacts": [
                {"path": PANEL_PATH, "sha256": panel_sha}],
            "clocks": {
                "event_time": as_of,
                "publication_time": fut[0],
                "first_available_time": as_of,
                "ingestion_time": as_of,
                "decision_as_of": as_of},
            "note": ("Two-leg splitter forecasts from the close of "
                     "the as-of session. The value is the leg's "
                     "claimed middle 20-session excess return "
                     "against SPY, in points; the outcome spec "
                     "carries the name's own 20-session return and "
                     "SPY's leg is resolved at grading time.")}
        for leg, estimate in (("persist", CLAIM_PERSIST),
                              ("reverse", CLAIM_REVERSE)):
            for item in live_names[leg]:
                _row, was = led.append_forecast_declared(
                    engine_id=ENGINE_ID, issued_ts=fut[0],
                    subject=item["symbol"],
                    quantity=f"{leg}_median_20_session_excess_points",
                    value={"estimate": estimate},
                    horizon_open=fut[0], horizon_close=fut[-1],
                    lineage=lineage, families=["price"],
                    outcome={"symbol": item["symbol"],
                             "kind": "excess_return_points",
                             "benchmark": "SPY",
                             "base_date": as_of, "at_date": fut[-1]})
                created += 1 if was else 0
    rows_after = led.rows()
    if not led.verify_chain(rows_after):
        return fail("the forecast record failed verification after "
                    "writing; not publishing figures from it")
    figures = ledger_mod.recompute_figures(rows_after)
    mine = figures.get(ENGINE_ID, {"forecasts": 0, "graded": 0})
    if mine["forecasts"] != recorded_before + created:
        return fail("ledger figures do not match the live rows expected")

    spy_today_pct = round(spy_ret[-1] * 100.0, 2)
    if spy_ret[-1] >= 0:
        spy_today_kind = "flat or up"
    elif spy_ret[-1] <= FEAR_DROP:
        spy_today_kind = "a fear day (down at least 1 percent)"
    else:
        spy_today_kind = "down, but not a fear day"
    for leg in today:
        today[leg].sort(key=lambda x: x["symbol"])

    data = {
        "tool": "Idiosyncratic-or-Liquidity Splitter",
        "state": "proving",
        "as_of_session": as_of,
        "source": (f"The daily price history on record ({names_checked:,} "
                   f"stocks plus the broad market fund they are measured "
                   f"against, {dates[0]} to {as_of}, {n_sessions} trading "
                   f"days), checked for this page. The longer daily "
                   f"history the design names (2016 to 2026) is not on "
                   f"this computer, so the history below runs on the "
                   f"history that exists."),
        "market_today": {
            "return_pct": spy_today_pct,
            "kind": spy_today_kind,
            "note": ("Neither forecast fires on a day like this: the "
                     "keep-falling forecast needs the market flat or "
                     "up, and the bounce-back forecast needs a fear "
                     "day (the market down at least 1 percent)."),
        },
        "claims": {
            "persist": ("When a stock drops hard on its own while the "
                        "market is flat or up, the drop tends to "
                        "stick: the middle such stock is at least 0.5 "
                        "points behind the market 20 trading days "
                        "later."),
            "reverse": ("When the same size of drop lands on a fear "
                        "day, with the market falling hard around it, "
                        "the drop tends to unwind: the middle such "
                        "stock is at least 0.5 points ahead of the "
                        "market 20 trading days later."),
            "falsified_words": ("Either forecast is proven wrong if "
                                "its middle outcome lands on the "
                                "other side of zero."),
        },
        "how_the_split_works": (
            "Each stock's drop is first stripped of the market's "
            "move that day; what is left is the stock's own move. "
            "The drop counts only if it is at least twice the size "
            "of that stock's own usual daily move, measured over "
            "its past 126 trading days. No fixed percent drop is "
            "used anywhere: a quiet stock and a jumpy stock are "
            "each judged against themselves."),
        "today": {
            "names_checked": names_checked,
            "names_judged": names_evaluable_today,
            "names_set_aside_short_history": names_excluded_today,
            "hard_drops": len(today["persist"]) + len(today["reverse"])
            + len(today["neither"]),
            "persist": today["persist"],
            "reverse": today["reverse"],
            "neither": today["neither"],
            "neither_note": ("These stocks dropped hard enough "
                             "today, but the market's in-between "
                             "day (down, not a fear day) puts them "
                             "in neither group. They are counted "
                             "and named, and no forecast is made "
                             "about them."),
        },
        "history": {
            "label": "History, not live forecasts",
            "span": f"{dates[WINDOW + 1]} to {as_of}",
            "warmup_note": (f"Judging a drop against a stock's own "
                            f"usual move needs 126 of its past "
                            f"trading days first, so the first "
                            f"judgeable day in this history is "
                            f"{dates[WINDOW + 1]} and {n_sessions - WINDOW - 1} "
                            f"trading days are judged. Every stock "
                            f"that still trades is in this history; "
                            f"stocks that stopped trading are not, "
                            f"which can flatter the numbers."),
            "hard_drops_total": triggers_total,
            "neither_cases": neither_episodes,
            "fear_days_judged": fear_days_evaluable,
            "fear_days_total_in_history": fear_days,
            "persist": hist["persist"],
            "reverse": hist["reverse"],
            "legs_never_combined": ("The two groups are always "
                                    "shown separately. Their "
                                    "numbers are never added "
                                    "together or averaged into one "
                                    "figure."),
        },
        "live": {
            "forecasts_recorded": mine["forecasts"],
            "forecasts_graded": mine["graded"],
            "target_graded_per_leg": KILL_EPISODES,
            "note": ("The live record starts empty. Forecasts are "
                     "written down before the 20 trading days they "
                     "describe, and the first grades land only "
                     "after those days have passed."),
        },
        "kill_criterion": ("Either forecast retires on its own if, "
                           "after 150 of its cases have been "
                           "graded, the middle outcome could still "
                           "plausibly be zero."),
        "thin_cell_rule": ("Any group with fewer than 30 graded "
                           "cases shows its count only, with no "
                           "middle figure."),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH}: as of {as_of}, SPY {spy_today_pct:+.2f}% "
          f"({spy_today_kind}); history triggers {triggers_total}, "
          f"persist {hist['persist']['episodes']} episodes / "
          f"{hist['persist']['graded']} graded / median "
          f"{hist['persist'].get('median_points')}, reverse "
          f"{hist['reverse']['episodes']} episodes / "
          f"{hist['reverse']['graded']} graded / median "
          f"{hist['reverse'].get('median_points')}, neither "
          f"{neither_episodes}; today persist "
          f"{len(today['persist'])}, reverse {len(today['reverse'])}, "
          f"neither {len(today['neither'])}; ledger forecasts "
          f"{mine['forecasts']} ({created} new), graded {mine['graded']}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
