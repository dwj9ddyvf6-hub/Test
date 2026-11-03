#!/usr/bin/env python3
"""Refresh the Stress-Reversal Staging tool (Forecast Engine 4).

=====================================================================
CANDIDATE-REGISTER TRIPLE (written before any computation, per the
lineup's adopted standards)

1. EVIDENCE CLASS
   The corpus's only grade A directional effect: row T2 of
   terminal-lineup/records/forecast-search-2026-10-27/EVIDENCE.md.
   In the deepest SPY-drawdown tercile, last-day return rank
   correlation was -0.058 in the discovery years (2017-2021) and
   -0.028 in the confirmation years (2022-2026): yesterday's losers
   beat yesterday's winners. Short-term reversal was stronger in
   stress: 393 confirmed against a null of 17. The one-week
   peer-gap reversal rank correlation was +0.017 (strength 4.4).
   Supporting rows: F5/F7 RESET laggard relative strength (row S2,
   grade B, consistent with T2). This engine stages that one
   blended effect into three separately graded stage forecasts
   per name, per the Engine 4 design in FORECAST-ENGINES-30.md.
   This engine's own live record: none before today; it starts
   here, in the state computed below.

2. RECONSTRUCTION CHOICES (every definition the study did not
   write down, named before computing, with its reason)
   The study's own record (EVIDENCE row T2 and its restatements)
   states only: the condition label "deepest SPY-drawdown
   tercile", the factor "last-day return", the claim direction,
   "1-week peer-gap reversal", the periods 2017-2021 / 2022-2026,
   and the survivors roster. The study's source files are not on
   this disk. Everything below that the study did not state is a
   RECONSTRUCTION, chosen here and frozen:
   - Drawdown (RECONSTRUCTED): on each session, SPY's close
     divided by the highest SPY close up to and including that
     session, minus 1, computed within the shipped daily history
     only (2025-03-25 onward). The shipped window starts after
     SPY's February 2025 high, so early-window drawdowns are
     understated against any long-history measure; stated, never
     hidden. Reason: the running peak is the plain meaning of
     drawdown, and the shipped history is the only SPY panel on
     this disk (the 2010-2026 panel the design names is
     summary-only here, as Engines 1 and 3 also found).
   - Deepest third (RECONSTRUCTED): a session is a stress session
     when its drawdown is at or below the one-third quantile
     (linear interpolation) of all drawdown readings on earlier
     sessions in the shipped window. Point-in-time: no reading is
     judged against its own future. At least 60 earlier readings
     are required before any session can be a stress session,
     because a third computed from a handful of readings is too
     jumpy to mean anything. Consequence, stated plainly: a third
     of a mostly calm 399-session window is shallow; on this
     window the deepest third begins at about 1.57 percent below
     the peak, far shallower than the falls the original study
     spanned. The threshold is printed on the page and in
     data.json so anyone can check the reading against it.
   - Episode (RECONSTRUCTED): a run of consecutive stress
     sessions is one episode. Rates are always printed beside the
     number of episodes they rest on, because overlapping days
     inside one episode are not independent evidence (the
     small-episode trap named in the design).
   - Yesterday's loser group (RECONSTRUCTED): on a stress
     session (day 0), the group is the bottom third of names by
     their return on the session before day 0, among names with
     closes 5 sessions before day 0, 2 sessions before, the
     session before, and day 0 itself (the 5-session close is
     needed for the peer-gap measure below). The study graded a
     continuous rank correlation and named no cut; a third
     matches the condition's own third and keeps the group
     large enough to grade. SPY itself is never in the group.
   - Stage 1, reversal begins by +1 (RECONSTRUCTED event): the
     name's return from day 0's close to the next session's close
     beats SPY's return over the same two closes. The study's
     claim is relative (losers beat winners), so the event is
     relative to the market, not a bare rise.
   - Peer gap and stage 2 (RECONSTRUCTED): peers are all names
     in the shipped list with the needed closes (no sector list
     exists on this disk). A name's gap at day 0 is the middle
     (median) trailing 5-session return of all peers minus the
     name's own trailing 5-session return ("1-week" read as 5
     sessions, the study's only peer-gap horizon word). The gap
     closes by +3 when the name's cumulative return over the 3
     sessions after day 0, minus the peers' middle cumulative
     return over the same 3 sessions, reaches at least the
     day-0 gap. Full close only; a partial catch-up does not
     count.
   - Stage 3 (design's own words, not the study's): the middle
     (median) cumulative return of the group at +1, +3 and +5
     sessions, carried as one stage forecast with three numbers.
   - Denominators: every day-0 group name stays in every stage's
     denominator. In the history run, a name whose later close is
     missing counts as not begun (stage 1) and not closed
     (stage 2), and is counted in the missing tally for stage
     3's middles (a middle cannot be taken over a missing
     price). History events are graded only when their whole
     +5 window has closed inside the panel.
   - Forecast values (RECONSTRUCTED): the live stage forecasts
     for every group name are the history run's pooled rates and
     middles over all graded history events (the script's own
     measured behaviour on the only history on record), the
     same for every name, because the study's effect is a
     group-level effect and no per-name conditioner is in the
     design. They are rounded to 4 decimals (rates) and 3
     decimals (return points) in the ledger values.
   - Stage 1 bar (RECONSTRUCTED, pre-registered here before the
     first live episode): over the first 3 live episodes pooled,
     at least half of all flagged names must have begun their
     reversal by +1. Below half, stage 1 has failed its bar and
     the whole script retires. 50 percent is the plain reading
     of "the reversal begins": more names turning than not.
   - Ledger shape: three rows per group name, through the
     machinery's append call only. Stage 1 value
     {"resolved_by": {"1": rate}} and stage 2 value
     {"resolved_by": {"3": rate}} follow the registered
     timing form; stage 3 value {"medians_pct": {"plus_1": m1,
     "plus_3": m3, "plus_5": m5}}. Known grading note, stated
     like Engines 2 and 3 stated theirs: the shared grading
     runner's current outcome resolver cannot express
     "beats SPY over the same window" (stage 1), a peer-median
     comparison (stage 2), or a three-horizon median (stage 3);
     the outcome specs below carry the plain event each row
     states (stage 1: close above day-0 close at +1, the
     absolute half of its event; stage 3: the name's own +5
     return), and the rows must be graded by the stated events
     when the runner is next extended. No live row can mature
     until the price source passes its horizon close in any
     case. The shared ledger's dedupe key omits the quantity,
     so each stage's value also carries its stage name
     ("stage": ...) to keep the three distinct rows distinct
     even if two values ever rounded alike.
   - Thin-cell rule: any stage with fewer than 30 graded cases
     shows its count only, no rate and no score.
   - Panel: the only daily history on record on this box is
     ~/workspace/morgue/data_cache/board_bt_bars.json (1,833
     names including SPY, 399 sessions, 2025-03-25 to
     2026-10-23). Nothing is claimed beyond that span, and
     nothing from the history run is ever written to the live
     ledger.

3. NON-CLAIMS
   - The earlier study's figures (rank correlations -0.058 and
     -0.028, 393 confirmations against a null of 17, peer-gap
     +0.017 at strength 4.4) are that study's record, shown
     labelled as the study's; they are not this engine's
     results, and this engine's history run on a short, mostly
     calm window does not reproduce or confirm them.
   - The stress condition used here is a stated reconstruction
     on a truncated window, not the study's exact coded
     condition, which is not written down anywhere on this disk.
   - No name is claimed more likely to reverse than another
     name in the group; the forecast is the group's script,
     applied name by name so every name is graded.
   - Nothing from any history computation is ever written to
     the live ledger. Only today's live group forecasts are
     ledgered, through the machinery's own append call, and
     only when today's session is a stress session.

=====================================================================
Behaviour: stage the history run over the shipped panel (ledgers
nothing), evaluate the freshest session's stress condition, and
if it holds, ledger today's group forecasts through
forecast/ledger.py append_forecast (never hand-edited), then
write data.json from the panel plus figures recomputed from the
ledger alone. Idempotent: rerunning with the same panel appends
nothing and rewrites the same data.json. Fails closed on any
disagreement with the bar source or the ledger (broken chain,
missing SPY, too-short panel, ledger figures that do not match
the live rows this run expects). Timestamps come from the
sources, never the clock.
"""

import json
import math
import os
import sys
from datetime import date, timedelta
from statistics import median

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(HERE)
PANEL_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")
EVIDENCE_PATH = os.path.join(
    LINEUP, "records", "forecast-search-2026-10-27", "EVIDENCE.md")
OUT_PATH = os.path.join(HERE, "stress-reversal", "data.json")
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

ENGINE_ID = "engine_04"
WARMUP = 60               # earlier drawdown readings required
THIN = 30
BAR_STAGE1 = 0.5          # pre-registered stage 1 bar (pooled)
PROVING_EPISODES = 3      # first 3 forward episodes decide


def fail(msg):
    print(f"Stress-Reversal refresh: {msg}", file=sys.stderr)
    return 1


def quantile(vals, q):
    s = sorted(vals)
    pos = q * (len(s) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return s[lo]
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def next_sessions(after_iso, count):
    d = date.fromisoformat(after_iso)
    out = []
    while len(out) < count:
        d += timedelta(days=1)
        if d.weekday() < 5:
            out.append(d.isoformat())
    return out


def load_panel():
    with open(PANEL_PATH, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if "SPY" not in raw:
        raise ValueError("panel has no SPY bars")
    spy_rows = sorted(raw["SPY"], key=lambda r: r[0])
    dates = [r[0] for r in spy_rows]
    if dates != sorted(set(dates)):
        raise ValueError("SPY session dates are not unique and sorted")
    closes = {}
    for sym, rows in raw.items():
        closes[sym] = {r[0]: float(r[4]) for r in rows}
    return raw, dates, closes, [float(r[4]) for r in spy_rows]


def drawdown_series(spy_closes):
    peak = -1.0
    out = []
    for c in spy_closes:
        peak = max(peak, c)
        out.append(c / peak - 1.0)
    return out


def stress_flags(dd):
    """Point-in-time deepest-third flags + threshold per session."""
    flags, thresholds = [], []
    for t in range(len(dd)):
        if t < WARMUP:
            flags.append(False)
            thresholds.append(None)
            continue
        th = quantile(dd[:t], 1.0 / 3.0)
        thresholds.append(th)
        flags.append(dd[t] <= th)
    return flags, thresholds


def episode_ids(flags):
    """Contiguous-run episode index per session (None if not stress)."""
    out = [None] * len(flags)
    cur = -1
    inside = False
    for t, f in enumerate(flags):
        if f and not inside:
            cur += 1
            inside = True
        elif not f:
            inside = False
        if f:
            out[t] = cur
    return out, cur + 1


def cohort_at(t, dates, closes, symbols):
    """Bottom third by return on session t-1, with all needed closes.
    Returns (cohort list of (symbol, yesterday_return), peer_r5 dict)."""
    d5, d2, d1, d0 = dates[t - 5], dates[t - 2], dates[t - 1], dates[t]
    cand = []
    peer_r5 = {}
    for sym in symbols:
        table = closes[sym]
        c5, c0 = table.get(d5), table.get(d0)
        if c5 is not None and c0 is not None:
            peer_r5[sym] = c0 / c5 - 1.0
        c2, c1 = table.get(d2), table.get(d1)
        if c2 is not None and c1 is not None and c0 is not None \
                and c5 is not None:
            cand.append((c1 / c2 - 1.0, sym))
    cand.sort()
    k = max(1, len(cand) // 3)
    return cand[:k], peer_r5


def stage_history(dates, closes, spy_closes, flags, epids):
    """Stage every stress session whose +5 window closed in-panel."""
    symbols = [s for s in closes if s != "SPY"]
    n = len(dates)
    s1_hit = s2_hit = denom = 0
    missing = {1: 0, 3: 0, 5: 0}
    cum = {1: [], 3: [], 5: []}
    events = 0
    eps = set()
    for t in range(n):
        if not flags[t] or t < 6 or t + 5 >= n:
            continue
        cohort, peer_r5 = cohort_at(t, dates, closes, symbols)
        if not cohort or not peer_r5:
            continue
        med5 = median(peer_r5.values())
        d0, d1, d3, d5 = dates[t], dates[t + 1], dates[t + 3], dates[t + 5]
        pc3 = []
        for sym, _r5 in ((s, None) for s in peer_r5):
            c0 = closes[sym].get(d0)
            c3 = closes[sym].get(d3)
            if c0 is not None and c3 is not None:
                pc3.append(c3 / c0 - 1.0)
        medc3 = median(pc3) if pc3 else 0.0
        spy1 = spy_closes[t + 1] / spy_closes[t] - 1.0
        events += 1
        eps.add(epids[t])
        for _r, sym in cohort:
            denom += 1
            table = closes[sym]
            c0 = table[d0]
            r1 = table.get(d1)
            r1 = None if r1 is None else r1 / c0 - 1.0
            if r1 is None:
                missing[1] += 1
            else:
                cum[1].append(r1)
                if r1 - spy1 > 0:
                    s1_hit += 1
            r3 = table.get(d3)
            r3 = None if r3 is None else r3 / c0 - 1.0
            if r3 is None:
                missing[3] += 1
            else:
                cum[3].append(r3)
                gap = med5 - peer_r5[sym]
                if (r3 - medc3) >= gap:
                    s2_hit += 1
            r5 = table.get(d5)
            r5 = None if r5 is None else r5 / c0 - 1.0
            if r5 is None:
                missing[5] += 1
            else:
                cum[5].append(r5)
    return {
        "events": events,
        "episodes": len(eps),
        "denominator": denom,
        "stage1": {"hits": s1_hit, "rate": (s1_hit / denom) if denom else None},
        "stage2": {"hits": s2_hit, "rate": (s2_hit / denom) if denom else None},
        "stage3_medians_pct": {
            f"plus_{h}": (round(median(cum[h]) * 100.0, 3) if cum[h] else None)
            for h in (1, 3, 5)},
        "stage3_counts": {f"plus_{h}": len(cum[h]) for h in (1, 3, 5)},
        "missing_future_close": {f"plus_{h}": missing[h] for h in (1, 3, 5)},
    }


def main():
    try:
        _raw, dates, closes, spy_closes = load_panel()
    except (OSError, ValueError, KeyError) as exc:
        return fail(f"bar source disagrees with what this tool needs: {exc}")
    if len(dates) <= WARMUP + 10:
        return fail("panel too short to judge a deepest third")
    panel_sha = ledger_mod.file_sha256(PANEL_PATH)
    evidence_sha = ledger_mod.file_sha256(EVIDENCE_PATH)

    dd = drawdown_series(spy_closes)
    flags, thresholds = stress_flags(dd)
    epids, n_episodes = episode_ids(flags)
    hist = stage_history(dates, closes, spy_closes, flags, epids)

    t_last = len(dates) - 1
    as_of = dates[t_last]
    today_stress = bool(flags[t_last])
    threshold = thresholds[t_last]
    symbols = [s for s in closes if s != "SPY"]

    # ---- ledger: verify before touching -----------------------------
    registry = registry_mod.load()
    ledger = ledger_mod.Ledger(
        os.path.join(LINEUP, "forecast", "ledger.jsonl"), registry=registry)
    try:
        rows_before = ledger.rows()
        if not ledger.verify_chain(rows_before):
            return fail("ledger hash chain does not verify; refusing to run")
    except ledger_mod.LedgerError as exc:
        return fail(f"ledger disagrees: {exc}")
    figures_before = ledger_mod.recompute_figures(rows_before)
    recorded_before = figures_before.get(ENGINE_ID, {}).get("forecasts", 0)

    live_rows = []
    created = 0
    if today_stress:
        cohort, _peer = cohort_at(t_last, dates, closes, symbols)
        if not cohort:
            return fail("stress session but no group could be formed")
        p1 = round(hist["stage1"]["rate"], 4)
        p2 = round(hist["stage2"]["rate"], 4)
        meds = hist["stage3_medians_pct"]
        fut = next_sessions(as_of, 5)
        lineage = {
            "source_artifacts": [
                {"path": PANEL_PATH, "sha256": panel_sha},
                {"path": EVIDENCE_PATH, "sha256": evidence_sha},
            ],
            "clocks": {
                "event_time": as_of,
                "publication_time": fut[0],
                "first_available_time": as_of,
                "ingestion_time": as_of,
                "decision_as_of": as_of,
            },
            "note": "Stage forecasts from the close of the as-of "
                    "session, for the sessions starting on the "
                    "horizon open date. Values are the history "
                    "run's pooled stage rates and middles, the "
                    "same for every group name.",
        }
        specs = [
            ("stage_1_reversal_begins_by_plus_1",
             {"resolved_by": {"1": p1}, "stage": "stage_1"},
             fut[0], fut[0],
             {"symbol": None, "kind": "close_above", "at_date": fut[0],
              "threshold": None}),
            ("stage_2_peer_gap_closes_by_plus_3",
             {"resolved_by": {"3": p2}, "stage": "stage_2"},
             fut[0], fut[2],
             {"symbol": None, "kind": "return", "base_date": as_of,
              "at_date": fut[2]}),
            ("stage_3_median_cumulative_return",
             {"medians_pct": meds, "stage": "stage_3"},
             fut[0], fut[4],
             {"symbol": None, "kind": "return", "base_date": as_of,
              "at_date": fut[4]}),
        ]
        try:
            for yret, sym in cohort:
                c0 = closes[sym][as_of]
                for quantity, value, h_open, h_close, outcome in specs:
                    oc = dict(outcome)
                    oc["symbol"] = sym
                    if "threshold" in oc:
                        oc["threshold"] = c0
                    row, was = ledger.append_forecast_declared(
                        engine_id=ENGINE_ID, issued_ts=fut[0], subject=sym,
                        quantity=quantity, value=value,
                        horizon_open=h_open, horizon_close=h_close,
                        lineage=lineage, families=["price"], outcome=oc)
                    created += 1 if was else 0
                    live_rows.append({
                        "symbol": sym, "yesterday_return_pct":
                            round(yret * 100.0, 3)})
                # one live_rows entry per name (appended inside loop
                # per stage would triple it; keep the first stage's)
                # -- handled by slicing below
        except ledger_mod.LedgerError as exc:
            return fail(f"ledger refused a live forecast: {exc}")
        # cohort list: one entry per name, in group order
        live_rows = [{"symbol": sym,
                      "yesterday_return_pct": round(yret * 100.0, 3)}
                     for yret, sym in cohort]

    rows_after = ledger.rows()
    if not ledger.verify_chain(rows_after):
        return fail("ledger hash chain broke after appends; not publishing")
    figures = ledger_mod.recompute_figures(rows_after)
    mine = figures.get(ENGINE_ID, {"forecasts": 0, "graded": 0})
    expected = recorded_before + created
    if mine["forecasts"] != expected:
        return fail("ledger figures do not match the live rows expected")
    if not today_stress and created != 0:
        return fail("forecasts were created on a non-stress session")

    ep_today = epids[t_last] + 1 if today_stress else None
    data = {
        "tool": "Stress-Reversal Staging",
        "state": "proving",
        "as_of_session": as_of,
        "source": "The daily price history on record (1,833 names "
                  "including the broad market fund, March 25, 2025 "
                  "to October 23, 2026, 399 trading days), checked "
                  "for this page.",
        "claim": "The claim under test: when the broad market is in "
                 "the deepest third of its fall, yesterday's biggest "
                 "losers start to turn in an order: first they beat "
                 "the market by the next trading day, then they make "
                 "up their past week's lag behind the typical stock "
                 "within 3 trading days, with the middle total gain "
                 "or loss landing where stage 3 states at 1, 3 and "
                 "5 trading days.",
        "condition": {
            "drawdown_pct": round(dd[t_last] * 100.0, 2),
            "threshold_pct": round(threshold * 100.0, 2),
            "stress_today": today_stress,
            "episode_number_overall": ep_today,
            "episodes_in_history": n_episodes,
            "stress_sessions_in_history": int(sum(flags)),
            "note": "The fall is measured from the broad market "
                    "fund's highest close in the record on hand. "
                    "The deepest third is judged only against "
                    "readings from earlier days, and only once 60 "
                    "earlier readings exist.",
        },
        "live": {
            "state": "firing" if today_stress else "waiting",
            "forecasts": live_rows if today_stress else [],
            "stage_forecast": {
                "stage_1_pct": round(hist["stage1"]["rate"] * 100.0, 1),
                "stage_2_pct": round(hist["stage2"]["rate"] * 100.0, 1),
                "stage_3_medians_pct": hist["stage3_medians_pct"],
            } if today_stress else None,
            "forecasts_recorded": mine["forecasts"],
            "forecasts_graded": mine["graded"],
            "forward_episodes_so_far": 1 if today_stress else 0,
            "proving_episodes": PROVING_EPISODES,
        },
        "history": {
            "label": "History, not live forecasts",
            "graded_day0_events": hist["events"],
            "episodes": hist["episodes"],
            "cohort_name_events": hist["denominator"],
            "stage_1": {
                "rate_pct": round(hist["stage1"]["rate"] * 100.0, 1),
                "hits": hist["stage1"]["hits"],
                "denominator": hist["denominator"],
                "episodes": hist["episodes"],
            },
            "stage_2": {
                "rate_pct": round(hist["stage2"]["rate"] * 100.0, 1),
                "hits": hist["stage2"]["hits"],
                "denominator": hist["denominator"],
                "episodes": hist["episodes"],
            },
            "stage_3_medians_pct": hist["stage3_medians_pct"],
            "stage_3_counts": hist["stage3_counts"],
            "missing_future_close": hist["missing_future_close"],
            "study_record": {
                "source_name": "The earlier study this engine is "
                               "built from, on daily prices 2017 to "
                               "2026, a list of companies that "
                               "survived to the end of the study.",
                "rows": [
                    {"era": "2017 to 2021", "measure":
                     "How strongly yesterday's losers ranked ahead "
                     "of yesterday's winners in the deepest third "
                     "of the market's fall", "value": -0.058},
                    {"era": "2022 to 2026", "measure":
                     "Same reading, later years", "value": -0.028},
                    {"era": "2017 to 2026", "measure":
                     "One-week lag behind other stocks closing: "
                     "the strength reading", "value": 0.017,
                     "strength": 4.4},
                ],
                "confirmations": 393,
                "null_confirmations": 17,
                "note": "In that study, the reversal pattern showed "
                        "up 393 times against 17 expected by chance. "
                        "Those are the study's figures, from its own "
                        "years. They are the reason this engine "
                        "exists; they are not this engine's results, "
                        "and the short, mostly calm record on hand "
                        "here does not reproduce them.",
            },
        },
        "caveats": [
            "The study that found this pattern only looked at "
            "companies that survived to the end of its years. "
            "Companies that disappeared along the way are missing "
            "from it, and that can make the pattern look stronger "
            "than it was.",
            "This tool only speaks when the market is in the "
            "deepest third of its fall. Those stretches arrive on "
            "the market's schedule, not on a calendar, so its "
            "proving may rest on few stretches spread over a long "
            "time.",
        ],
        "reconstruction_note": "The original study did not write "
            "down exactly how it measured the market's fall, which "
            "losers counted, or what counted as the lag behind other "
            "stocks closing. This tool fills those gaps with stated "
            "stand-ins, fixed in advance: the fall is measured from "
            "the highest close in the record on hand; the deepest "
            "third is judged against earlier days only; the group is "
            "the bottom third of yesterday's returns; other stocks "
            "means the typical (middle) stock in the same list; and "
            "the lag is over the past 5 trading days. On this short, "
            "mostly calm record, the deepest third begins at about "
            "1.57 percent below the highest close, much shallower "
            "than a real market fall.",
        "stage_1_bar_pct": 50,
        "kill_criterion": "This tool is retired as a whole if, over "
            "its first 3 live stress stretches pooled together, "
            "fewer than half of the stocks it flagged had begun to "
            "turn by the next trading day. The later stages do not "
            "rescue it: if the first step fails, the whole sequence "
            "is retired with its record kept.",
        "thin_cell_rule": "Any stage with fewer than 30 graded "
            "forecasts shows its count only, with no percentage "
            "headline.",
    }
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"stress-reversal: as_of={as_of} stress={today_stress} "
          f"dd={dd[t_last]*100:.2f}% thr={threshold*100:.2f}% "
          f"history_events={hist['events']} episodes={hist['episodes']} "
          f"created={created} recorded={mine['forecasts']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
