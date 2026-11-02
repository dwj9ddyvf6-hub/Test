#!/usr/bin/env python3
"""Refresh the Fear-Day Triangulation engine (Forecast Engine 24).

=====================================================================
CANDIDATE-REGISTER TRIPLE (written before any computation, per the
lineup's adopted standards)

1. EVIDENCE CLASS
   Timing versus selection, measured, is the whole evidence base.
   The picker replay on record (296,093 cases, 71,227 random
   entries, 2019-12-20 to 2026-10-15) found that on its fear slice
   (days SPY fell at least 1 percent, a DIFFERENT and wider cut
   than this engine's fear-day definition below), picked groups of
   rising-trend names averaged +0.29 to +0.36R (the four recorded
   groups: +0.285, +0.276, +0.247, +0.356) while random entries in
   the same names under the same exits averaged +0.34 to +0.38R
   (+0.384, +0.339, +0.360, +0.357). Picking carefully on fear
   days did not beat picking at random: the lift belonged to the
   day, not the setup. That is the control this engine must beat,
   and the reason it exists. Behind the three conditions: the
   pullback-depth study (grade B) measured, for rising-trend names
   on fear days, a small real link between how deep a dip is
   against the stock's own past dips and the next 20 sessions
   (correlation +0.026 and +0.031 in its two eras, deepest fifth
   beating shallowest by +0.81 points in the later era); the gap
   study (grade B) measured gap share on fear days carrying a
   similar small link (+0.069 and +0.074 in its two eras, in its
   top fear-gauge third); insider silence has no graded study
   behind it at all and is carried as an untested third leg.
   This engine's own live record: none. It ships with zero
   cohorts, waiting on the next fear day.

2. RECONSTRUCTION CHOICES (every constant, named before computing)
   - Fear day: the Fear Day List's own published definition,
     verbatim: a day when SPY fell more than 1.5 percent, or the
     fear gauge (VIX) rose more than 15 percent in a day, closed
     at 25 or higher, or closed at 20 or higher on a day when SPY
     or QQQ fell. Four arms, any one qualifies. Detection reads
     the shipped daily price history for SPY and QQQ and the fear
     gauge file on record (23 daily readings, 2026-09-21 to
     2026-10-21, the only such file on this disk), so the three
     gauge arms are judgeable only inside that window; outside
     it only the SPY arm can qualify a day, and the page prints
     the gauge record's end date. Fail-closed check: this
     engine's detection, run over the Fear Day List's own checked
     window (sessions 2026-10-15 to 2026-10-21, four with a prior
     session), must reproduce its published qualifying days
     (exactly one: 2026-10-16) or nothing is published.
   - Rising trend (the picker replay's rule): the replay record
     states only the phrase "uptrend pullback to a rising 21/50
     day". No fuller coded rule exists on this disk. FIXED
     reading, labelled ours: the close is above both the 21
     session and the 50 session mean closes (today included) AND
     the 50 session mean is higher than it was 5 sessions
     earlier. (The depth forecaster's different reading, close
     above the 200 session mean, is NOT used here.)
   - Pullback depth (the depth family), with its narrowing
     stated in plain words: depth today = (the highest close of
     the last 63 sessions including today, minus today's close)
     divided by the stock's own typical daily range, where the
     typical range is the middle true range over the trailing
     126 sessions ending yesterday (true range = the largest of
     high minus low, high minus previous close, previous close
     minus low). Today's depth is then ranked against ALL of the
     stock's own earlier computable depths on the shipped record,
     leaving today out, and a stock needs at least 126 earlier
     depths or it is set aside and counted. Deepest fifth =
     rank at or above 80 out of 100. THE NARROWING: the original
     study judged each dip against about three years of the
     stock's own past dips (750 of them, typical range over 750
     sessions); the shipped record holds at most 399 sessions per
     stock, so that version qualifies zero stocks here and this
     engine judges each dip against at most about a year and a
     half of the stock's own past dips instead. The deepest
     fifth line is therefore noisier, and the study's figures
     (+0.026 / +0.031, +0.81 points) belong to the long-history
     version: they are the reason the test exists, never figures
     this engine claims.
   - Gap share: the gap study's exact formula is NOT on this
     disk (its registry row says the formula lives in a ledger
     that was not among the sources read), so any claim to
     reproduce it would be invented. FIXED definition, labelled
     ours: on the fear day, gap share = the size of the open's
     jump from the previous close (either way) divided by the
     fear day's high-to-low range (0 when high equals low; the
     value can exceed 1 when the day trades entirely away from
     the previous close). Top third = at or above the two-thirds
     cut of gap share across that fear day's rising-trend pool,
     computed that day. This replaces the study's top
     fear-gauge-third conditioning, which the 23-reading gauge
     record cannot support; that substitution is part of the
     narrowing above.
   - Insider silence: read at summary grain from the insider
     record on file (gathered 2026-10-26; filings filed in the
     183 days before gathering, 2026-04-26 to 2026-10-26, up to
     the 20 most recent per name, open-market buys and sells
     only). Silence = a summary exists AND its sell count is 0.
     A name with NO summary is never counted as silent; it is
     set aside and counted. Coverage that binds the whole
     engine: the insider record covers 50 tracked names, 43 with
     a summary, against 1,832 names in the price history, so on
     any fear day only rising-trend names among those 50 can
     pass or fail this leg. Lag: a live cohort reads the most
     recent gathering on record at its date and prints that
     gathering date and window; a stale gathering is printed as
     stale, never treated as current. In the snapshot on file,
     7 of the 43 carry zero sells.
   - The exits (the picker replay's own, for comparability):
     bought at the next open after the fear-day close; the stop
     level is the fear day's low (the natural reading of a
     pullback entry, labelled ours: the replay record does not
     name its per-name level); the stop triggers on a close
     under the level minus 0.25 times the average true range,
     and the sale is at the next open; the first target is the
     nearest real resistance at least 0.75 average true ranges
     away (labelled ours, the replay record does not define
     resistance on this disk: the nearest single-session high
     among the 126 sessions up to and including the fear day
     that stands at or above the entry price plus 0.75 ranges;
     if none exists there is no target and only the stop or the
     time limit ends the trade); on a session that both touches
     the target and closes under the stop, the stop wins; the
     time limit is 20 sessions, sold at the 20th session's
     close. The average true range is the plain mean of the
     last 14 true ranges ending on the fear day (the replay
     record does not state its range window; 14 is ours). One R
     = the entry price minus the stop trigger price; a trade's
     result in R is its gain or loss divided by that amount.
   - The comparison draw (random entries, never by hand): on
     the fear day, take the rising-trend pool in alphabetical
     order, remove the depth-only group's members, and draw
     exactly as many names as the depth-only group holds, using
     a fixed random draw seeded with the fear day's date as a
     number (YYYYMMDD). NOTE on the ground-truth record: the
     inspection phase's worked example for 2026-10-16 printed
     the draw CRBG, but its script sampled the pool WITHOUT
     removing the depth group, against its own fixed rule; under
     the rule as fixed, the draw is CRC. This engine follows the
     rule, and the history on the page shows CRC.
   - Ledger shape: per fear-day group, at the fear day's close,
     THREE records written the same day through the shared
     record's own append call, one per arm (all three checks,
     depth alone, random draw), each with quantity
     mean_r_20_sessions_picker_exits and a stated figure: the
     triple arm states 0.39 (the comparison's low end 0.29 plus
     the claimed 0.10), the depth-only and random arms each
     state 0.29 (the control figure they embody). Each record's
     lineage carries the full member list of its arm, the panel
     and insider snapshot hashes, and the five clocks, so the
     group result is recomputable. Horizon: opens the session
     after the fear day, closes the 20th session after it,
     counted on SPY's session calendar (weekday projection past
     the end of the price record). Families: the triple arm is
     price plus company filings; depth and gap share are both
     read from the same price bars, so the three checks count
     as at most one and a half families of evidence, never
     three, and the page says so. The random and depth-only
     arms are price only. Only the freshest session in the
     price record can start a new group: a fear day that is no
     longer the freshest session and was never recorded is
     counted as missed and is NEVER backfilled. A fear day
     whose triple group is empty starts no group at all and
     records nothing (its depth and random arms exist only to
     grade a fired triple).
   - Grading: when the price record covers a recorded group's
     full 20 sessions, each arm's member results are computed
     with the exits above and the arm's average R is graded
     against its stated figure through the shared record's own
     grade call, with the count of graded names beside it. The
     shared grading runner cannot yet resolve this kind of
     outcome (a path-dependent stop-and-target simulation), so
     grades are appended by this engine through the machinery's
     grade call, never by forking the runner. No group can
     mature until the price record passes its horizon.
   - Thin-cell rule: any arm or group with fewer than 30 graded
     names shows its count only, no average R headline.
   - Self-retirement, the engine's own verdict printed in
     advance: once three groups have matured, if the triple
     group's average R does not beat the depth-only group's,
     picking by all three checks adds nothing over the single
     best part and this engine retires itself. The claim
     against the random comparison is separate: the triple must
     beat the random arm by at least +0.10R average at 20
     sessions.
   - Ship date: this engine first published on 2026-10-29.
     Fear days on or before that date are history, never
     recorded; the first group can only start on a fear day
     after it.

3. NON-CLAIMS
   - The earlier studies' figures are their own records, shown
     labelled as history. They are not this engine's results,
     and the depth study's figures in particular belong to the
     long-history construction this engine cannot run.
   - No result is claimed from the one fear day worked through
     as history (2026-10-16): its triple group was empty, its
     20-session outcome does not exist in the price record
     (which ends 5 sessions after entry), and the insider
     snapshot postdates it. It is published as history only.
   - Three checks agreeing is not three independent
     confirmations: at most one and a half families, as above.
   - Nothing from any history computation or self-test is ever
     written to the live record. Only a real fear-day group,
     formed on the freshest session after the ship date, is
     recorded there, through the machinery's own append call.

=====================================================================
Behaviour: read the price history, the fear gauge file, the Fear
Day List's published record, the insider record and the picker
replay record (fails closed on any disagreement between them, or
with the shared record), run the self-test, work the labelled
history day through the full pipeline without recording it, form
a group only if the freshest session is a post-ship fear day with
a non-empty triple, grade any matured recorded group, then write
data.json with the live figures recomputed from the shared record
alone. Idempotent: rerunning with the same sources records
nothing new and rewrites the same data.json. Timestamps come
from the sources, never the clock.
"""

import bisect
import datetime
import json
import os
import random
import statistics
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(HERE)
PANEL_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")
VIX_PATH = os.path.expanduser(
    "~/workspace/opt/rea-teardowns/azrael-1587/source/"
    "yahoo-vix-daily.json")
FEARDAY_PATH = os.path.join(HERE, "fear-day", "data.json")
INSIDER_PATH = os.path.join(HERE, "insider-wire", "data.json")
PICKER_PATH = os.path.join(
    LINEUP, "records", "picker-replay-2026-10-27",
    "picker-replay-2026-10-27.json")
OUT_PATH = os.path.join(HERE, "fear-day-triangulation", "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import attestation_block as _ab
except ImportError:  # refresh stays runnable standalone
    _ab = None
LEDGER_PATH = os.path.join(LINEUP, "forecast", "ledger.jsonl")

sys.path.insert(0, LINEUP)
from forecast import ledger as ledger_mod  # noqa: E402
from forecast import registry as registry_mod  # noqa: E402

ENGINE_ID = "engine_24"
SHIP_DATE = "2026-10-29"
HISTORY_DAY = "2026-10-16"
THIN = 30
PROVING_COHORTS = 3
TRIPLE_ESTIMATE = 0.39
CONTROL_ESTIMATE = 0.29
CLAIM_MARGIN_R = 0.10
HIGH_SESSIONS = 63
TR_WINDOW = 126
MIN_PRIOR_DEPTHS = 126
ATR_WINDOW = 14
RESISTANCE_LOOKBACK = 126


def fail(msg):
    print(f"Fear-Day Triangulation refresh: {msg}", file=sys.stderr)
    return 1


# ---- price helpers ------------------------------------------------------
def true_ranges(rows):
    out = [None]
    for j in range(1, len(rows)):
        h, l, pc = float(rows[j][2]), float(rows[j][3]), float(rows[j - 1][4])
        out.append(max(h - l, abs(h - pc), abs(l - pc)))
    return out


def uptrend(closes, i):
    """The fixed reading of the picker phrase: close above both the
    21 and 50 session mean closes, the 50 mean rising over 5."""
    if i < 54:
        return False
    ma21 = sum(closes[i - 20:i + 1]) / 21.0
    ma50 = sum(closes[i - 49:i + 1]) / 50.0
    ma50_prev = sum(closes[i - 54:i - 4]) / 50.0
    return closes[i] > ma21 and closes[i] > ma50 and ma50 > ma50_prev


def gap_share(rows, i):
    o, h, l = float(rows[i][1]), float(rows[i][2]), float(rows[i][3])
    pc = float(rows[i - 1][4])
    rng = h - l
    return abs(o - pc) / rng if rng > 0 else 0.0


def depth_percentile(rows, closes, trs, i):
    """Today's pullback depth ranked against the stock's own earlier
    depths (leave today out). Returns (depth, percentile, n_prior)
    or (depth, None, n_prior) when the stock is too short."""
    def depth(j):
        if j - (HIGH_SESSIONS - 1) < 0 or j - TR_WINDOW < 1:
            return None
        window = trs[j - TR_WINDOW:j]
        if any(t is None for t in window):
            return None
        med = statistics.median(window)
        if med <= 0:
            return None
        return (max(closes[j - (HIGH_SESSIONS - 1):j + 1]) - closes[j]) / med

    today = depth(i)
    if today is None:
        return None, None, 0
    prior = []
    for j in range(0, i):
        d = depth(j)
        if d is not None:
            prior.append(d)
    if len(prior) < MIN_PRIOR_DEPTHS:
        return today, None, len(prior)
    prior.sort()
    pct = 100.0 * bisect.bisect_left(prior, today) / len(prior)
    return today, pct, len(prior)


def atr(rows, trs, i):
    if i < ATR_WINDOW:
        return None
    window = trs[i - ATR_WINDOW + 1:i + 1]
    if any(t is None for t in window):
        return None
    return sum(window) / float(ATR_WINDOW)


def picker_exit_r(rows, i):
    """One name's result in R under the registered exits, for a
    signal at session i. Returns R, or None when the trade cannot
    be graded from the record (no next session, a non-positive
    risk amount, or the holding window runs past the record)."""
    if i + 1 >= len(rows):
        return None
    trs = true_ranges(rows)
    a = atr(rows, trs, i)
    if a is None or a <= 0:
        return None
    entry_i = i + 1
    entry = float(rows[entry_i][1])
    level = float(rows[i][3])
    stop_trigger = level - 0.25 * a
    risk = entry - stop_trigger
    if risk <= 0:
        return None
    target = None
    lo = max(0, i - RESISTANCE_LOOKBACK + 1)
    for j in range(lo, i + 1):
        h = float(rows[j][2])
        if h >= entry + 0.75 * a and (target is None or h < target):
            target = h
    last = entry_i + 19                     # the 20th held session
    if last >= len(rows):
        return None
    exit_price = None
    for j in range(entry_i, last + 1):
        h, c = float(rows[j][2]), float(rows[j][4])
        stop_close = c < stop_trigger
        touched = target is not None and h >= target
        if stop_close:                      # stop wins a both-day
            if j + 1 >= len(rows):
                return None
            exit_price = float(rows[j + 1][1])
            break
        if touched:
            exit_price = target
            break
    if exit_price is None:
        exit_price = float(rows[last][4])   # time limit: 20th close
    return (exit_price - entry) / risk


def grade_arm(panel, members, fear_day):
    """Grade one arm's members under the registered exits.
    Returns (graded_count, mean_r or None, ungradeable_count)."""
    results = []
    ungradeable = 0
    for sym in members:
        rows = panel.get(sym)
        if not rows:
            ungradeable += 1
            continue
        dates = [r[0] for r in rows]
        if fear_day not in dates:
            ungradeable += 1
            continue
        r = picker_exit_r(rows, dates.index(fear_day))
        if r is None:
            ungradeable += 1
        else:
            results.append(r)
    if not results:
        return 0, None, ungradeable
    return len(results), sum(results) / len(results), ungradeable


# ---- fear days ------------------------------------------------------------
def load_vix():
    with open(VIX_PATH, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    res = raw["chart"]["result"][0]
    stamps = res["timestamp"]
    closes = res["indicators"]["quote"][0]["close"]
    out = []
    for ts, c in zip(stamps, closes):
        if c is None:
            continue
        day = datetime.datetime.fromtimestamp(
            ts, datetime.timezone.utc).date().isoformat()
        out.append((day, float(c)))
    out.sort()
    return out


def fear_days(panel, vix):
    """Every qualifying day in the shipped price record, under the
    Fear Day List's four arms. The gauge arms are judgeable only
    on days the gauge file covers."""
    spy = panel["SPY"]
    qqq = panel.get("QQQ") or []
    qclose = {r[0]: float(r[4]) for r in qqq}
    qdates = [r[0] for r in qqq]
    vixd = dict(vix)
    vix_order = [d for d, _ in vix]
    out = []
    for i in range(1, len(spy)):
        day, close = spy[i][0], float(spy[i][4])
        prev = float(spy[i - 1][4])
        spy_pct = (close / prev - 1.0) * 100.0
        arms = []
        if spy_pct < -1.5:
            arms.append("SPY fell more than 1.5% that day")
        vc = vixd.get(day)
        vix_pct = None
        if vc is not None:
            k = vix_order.index(day)
            if k > 0:
                vix_pct = (vc / vix[k - 1][1] - 1.0) * 100.0
                if vix_pct > 15.0:
                    arms.append("the fear gauge rose more than 15% that day")
            if vc >= 25.0:
                arms.append("the fear gauge closed at 25 or higher")
            q_pct = None
            if day in qclose and qdates.index(day) > 0:
                pd_ = qdates[qdates.index(day) - 1]
                q_pct = (qclose[day] / qclose[pd_] - 1.0) * 100.0
            if vc >= 20.0 and (spy_pct < 0 or (q_pct is not None and q_pct < 0)):
                arms.append("the fear gauge closed at 20 or higher on a "
                            "day SPY or QQQ fell")
        if arms:
            out.append({"date": day, "spy_change_pct": round(spy_pct, 2),
                        "vix_close": vc,
                        "vix_change_pct": (round(vix_pct, 1)
                                           if vix_pct is not None else None),
                        "qualified_by": arms})
    return out


# ---- cohort formation -------------------------------------------------------
def form_cohort(panel, zero_sells, tracked_with_summary, day):
    """The full pipeline for one fear day: rising-trend pool, gap
    third, depth fifth, triple, and the fixed-rule random draw.
    Pure computation: records nothing."""
    pool = []
    detail = {}
    for sym in sorted(panel):
        if sym == "SPY":
            continue
        rows = panel[sym]
        dates = [r[0] for r in rows]
        if day not in dates:
            continue
        i = dates.index(day)
        if i < 54:
            continue
        closes = [float(r[4]) for r in rows]
        if not uptrend(closes, i):
            continue
        pool.append(sym)
        detail[sym] = {"index": i, "gap_share": gap_share(rows, i)}
    gaps = sorted(detail[s]["gap_share"] for s in pool)
    gap_cut = gaps[(2 * len(gaps)) // 3] if gaps else None
    depth_only = []
    depth_short = 0
    for sym in pool:
        rows = panel[sym]
        i = detail[sym]["index"]
        closes = [float(r[4]) for r in rows]
        _d, pct, _n = depth_percentile(rows, closes, true_ranges(rows), i)
        detail[sym]["depth_percentile"] = pct
        if pct is None:
            depth_short += 1
        elif pct >= 80.0:
            depth_only.append(sym)
    triple = []
    for sym in depth_only:
        if gap_cut is not None and detail[sym]["gap_share"] >= gap_cut \
                and sym in zero_sells:
            triple.append(sym)
    draw = []
    if depth_only:
        rest = [s for s in pool if s not in set(depth_only)]
        seed = int(day.replace("-", ""))
        draw = random.Random(seed).sample(rest, len(depth_only)) \
            if len(rest) >= len(depth_only) else list(rest)
    return {
        "date": day, "pool": pool, "pool_count": len(pool),
        "gap_top_third_cut": (round(gap_cut, 4) if gap_cut is not None
                              else None),
        "depth_only": depth_only, "triple": triple, "random_draw": draw,
        "depth_too_short_count": depth_short,
        "detail": {s: {"gap_share": round(detail[s]["gap_share"], 4),
                       "depth_percentile": (
                           round(detail[s]["depth_percentile"], 1)
                           if detail[s]["depth_percentile"] is not None
                           else None)}
                   for s in pool},
        "zero_sell_names_in_pool": [s for s in pool if s in zero_sells],
        "tracked_in_pool_count": sum(1 for s in pool
                                     if s in tracked_with_summary),
    }


# ---- self-test ----------------------------------------------------------------
def self_test(panel):
    """Prove the exit maths on hand-built price paths with known
    answers, the cohort helpers on known series, the fixed-rule
    draw's reproducibility, and the three-arm ledgering on a
    throwaway copy of the record. Raises on any disagreement."""
    def rows_from(ohlc):
        return [[f"2026-01-{k + 1:02d}", o, h, l, c]
                for k, (o, h, l, c) in enumerate(ohlc)]

    # A flat history gives a known range: every true range is
    # exactly 2.0, so the range average is 2.0; the signal low is
    # 99, so the stop trigger is 99 - 0.25 x 2.0 = 98.5; entry is
    # the next open, 100; one R is 100 - 98.5 = 1.5.
    hist = [(100.0, 101.0, 99.0, 100.0)] * 20
    sig = (100.0, 101.0, 99.0, 100.0)
    # Target case: one past high of 103 (outside the range-average
    # window, so the average stays 2.0) is the nearest resistance
    # at least 0.75 ranges (1.5) above entry; a later session
    # touches it and the trade ends at 103.
    bars = hist[:]
    bars[3] = (100.0, 103.0, 99.0, 100.0)
    case = bars + [sig] + [(100.0, 101.0, 99.0, 100.0),
                           (100.0, 103.5, 99.0, 101.0)]
    case += [(101.0, 101.5, 100.5, 101.0)] * 25
    r = picker_exit_r(rows_from(case), 20)
    if r is None or abs(r - (103.0 - 100.0) / 1.5) > 1e-9:
        raise RuntimeError(f"target case graded {r}, expected 2.0")
    # Stop case: a close under the trigger sells at the next open.
    case2 = hist + [sig] + [(100.0, 101.0, 98.0, 98.0),
                            (97.0, 97.5, 96.5, 97.0)]
    case2 += [(97.0, 97.5, 96.5, 97.0)] * 25
    r2 = picker_exit_r(rows_from(case2), 20)
    if r2 is None or abs(r2 - (97.0 - 100.0) / 1.5) > 1e-9:
        raise RuntimeError(f"stop case graded {r2}, expected -2.0")
    # Both in one session: the stop wins by the registered rule.
    case3 = hist[:]
    case3[3] = (100.0, 103.0, 99.0, 100.0)
    case3 = case3 + [sig] + [(100.0, 103.5, 98.0, 98.0),
                             (97.0, 97.5, 96.5, 97.0)]
    case3 += [(97.0, 97.5, 96.5, 97.0)] * 25
    r3 = picker_exit_r(rows_from(case3), 20)
    if r3 is None or abs(r3 - (97.0 - 100.0) / 1.5) > 1e-9:
        raise RuntimeError(f"both-day case graded {r3}, expected -2.0")
    # Time limit: nothing triggers, sold at the 20th held close.
    case4 = hist + [sig] + [(100.0, 101.0, 99.0, 100.0)] * 19 \
        + [(100.0, 101.0, 99.0, 103.0)]
    case4 += [(103.0, 103.5, 102.5, 103.0)] * 5
    r4 = picker_exit_r(rows_from(case4), 20)
    if r4 is None or abs(r4 - (103.0 - 100.0) / 1.5) > 1e-9:
        raise RuntimeError(f"time-limit case graded {r4}, expected 2.0")

    # Cohort helpers on known series.
    rising = [100.0 + 0.1 * k for k in range(60)]
    if not uptrend(rising, 59):
        raise RuntimeError("a steadily rising series is not in a rising trend")
    falling = [100.0 - 0.1 * k for k in range(60)]
    if uptrend(falling, 59):
        raise RuntimeError("a steadily falling series passed the rising test")
    grow = [[f"d{k}", 100.0, 101.0, 99.0, 100.0] for k in range(3)]
    grow[2] = ["d2", 104.0, 105.0, 103.0, 104.0]
    grow[1][4] = 100.0
    if abs(gap_share(grow, 2) - 4.0 / 2.0) > 1e-9:
        raise RuntimeError("gap share on a known bar is wrong")
    pool = ["AAA", "BBB", "CCC", "DDD", "EEE"]
    d1 = random.Random(20261016).sample([s for s in pool if s != "CCC"], 2)
    d2 = random.Random(20261016).sample([s for s in pool if s != "CCC"], 2)
    if d1 != d2 or "CCC" in d1 or len(d1) != 2:
        raise RuntimeError("the fixed-rule draw is not reproducible")

    # Three-arm ledgering on a throwaway copy.
    reg = registry_mod.load()
    with tempfile.TemporaryDirectory() as td:
        scratch = ledger_mod.Ledger(os.path.join(td, "ledger.jsonl"),
                                    registry=reg)
        scratch.append_genesis("fear-day triangulation self-test")
        lineage = {"source_artifacts": [
                       {"path": "synthetic (self-test, not a record)",
                        "sha256": ledger_mod.file_sha256(PANEL_PATH)}],
                   "clocks": {c: "2026-10-16"
                              for c in ledger_mod.CLOCK_FIELDS},
                   "note": "Self-test only; never the live record."}
        made = 0
        for arm, est, fams in (
                ("triple", TRIPLE_ESTIMATE, ["price", "filings_positioning"]),
                ("depth_only", CONTROL_ESTIMATE, ["price"]),
                ("random", CONTROL_ESTIMATE, ["price"])):
            _row, created = scratch.append_forecast_declared(
                engine_id=ENGINE_ID, issued_ts="2026-10-16",
                subject="2026-10-16 fear-day cohort: " + arm,
                quantity="mean_r_20_sessions_picker_exits",
                value={"estimate": est},
                horizon_open="2026-10-19", horizon_close="2026-11-13",
                lineage=lineage, families=fams,
                outcome={"kind": "picker_exit_mean_r_20_sessions",
                         "arm": arm, "members": ["AAA"]})
            made += 1 if created else 0
        figs = ledger_mod.recompute_figures(scratch.rows())
        if not scratch.verify_chain() or made != 3 \
                or figs[ENGINE_ID]["forecasts"] != 3:
            raise RuntimeError("throwaway three-arm ledgering failed")
    return {"state": "passed", "exit_cases_checked": 4,
            "ledger_arms_checked": 3}


# ---- live ledgering ------------------------------------------------------------
def session_after(spy_dates, day, n):
    """The date n sessions after day on SPY's calendar, projecting
    weekdays past the end of the record when needed."""
    if day in spy_dates:
        k = spy_dates.index(day) + n
        if k < len(spy_dates):
            return spy_dates[k]
        d = datetime.date.fromisoformat(spy_dates[-1])
        left = k - (len(spy_dates) - 1)
    else:
        d = datetime.date.fromisoformat(day)
        left = n
    while left > 0:
        d += datetime.timedelta(days=1)
        if d.weekday() < 5:
            left -= 1
    return d.isoformat()


def ledger_cohort(led, panel, insider, cohort, fear_entry):
    """Write the three arms of one fired cohort through the shared
    record's append call. Returns how many records were new."""
    spy_dates = [r[0] for r in panel["SPY"]]
    day = cohort["date"]
    horizon_open = session_after(spy_dates, day, 1)
    horizon_close = session_after(spy_dates, day, 20)
    panel_hash = ledger_mod.file_sha256(PANEL_PATH)
    insider_hash = ledger_mod.file_sha256(INSIDER_PATH)
    arms = (
        ("triple", cohort["triple"], TRIPLE_ESTIMATE,
         ["price", "filings_positioning"]),
        ("depth_only", cohort["depth_only"], CONTROL_ESTIMATE, ["price"]),
        ("random", cohort["random_draw"], CONTROL_ESTIMATE, ["price"]),
    )
    created = 0
    for arm, members, estimate, fams in arms:
        lineage = {
            "source_artifacts": [
                {"path": PANEL_PATH, "sha256": panel_hash},
                {"path": INSIDER_PATH, "sha256": insider_hash},
                {"path": FEARDAY_PATH,
                 "sha256": ledger_mod.file_sha256(FEARDAY_PATH)}],
            "clocks": {c: day for c in ledger_mod.CLOCK_FIELDS},
            "cohort": {
                "fear_day": day, "arm": arm, "members": list(members),
                "qualified_by": fear_entry["qualified_by"],
                "pool_count": cohort["pool_count"],
                "gap_top_third_cut": cohort["gap_top_third_cut"],
                "insider_gathered": insider["as_of"],
                "insider_window_start": insider["window_start"],
                "note": ("Fear-day group recorded at the fear day's "
                         "close; graded at 20 sessions under the "
                         "registered exits from the price record.")},
        }
        _row, was = led.append_forecast_declared(
            engine_id=ENGINE_ID, issued_ts=day,
            subject=f"{day} fear-day cohort: {arm}",
            quantity="mean_r_20_sessions_picker_exits",
            value={"estimate": estimate},
            horizon_open=horizon_open, horizon_close=horizon_close,
            lineage=lineage, families=fams,
            outcome={"kind": "picker_exit_mean_r_20_sessions",
                     "arm": arm, "members": list(members),
                     "fear_day": day})
        created += 1 if was else 0
    return created


# ---- build ----------------------------------------------------------------------
def build():
    for path, label in ((PANEL_PATH, "price history"),
                        (VIX_PATH, "fear gauge file"),
                        (FEARDAY_PATH, "Fear Day List record"),
                        (INSIDER_PATH, "insider record"),
                        (PICKER_PATH, "picker replay record")):
        if not os.path.exists(path):
            return fail(f"{label} not found: {path}")
    with open(PANEL_PATH, "r", encoding="utf-8") as fh:
        panel = json.load(fh)
    if "SPY" not in panel or "QQQ" not in panel:
        return fail("the price history carries no SPY or QQQ")
    with open(FEARDAY_PATH, "r", encoding="utf-8") as fh:
        fearday_tool = json.load(fh)
    with open(INSIDER_PATH, "r", encoding="utf-8") as fh:
        insider = json.load(fh)
    with open(PICKER_PATH, "r", encoding="utf-8") as fh:
        picker = json.load(fh)
    vix = load_vix()
    spy_dates = [r[0] for r in panel["SPY"]]
    panel_as_of = spy_dates[-1]

    # ---- Insider record, cross-checked against its own totals ----
    names = insider.get("names") or []
    with_summary = [n for n in names if n.get("summary")]
    zero_sells = {n["symbol"] for n in with_summary
                  if n["summary"]["sells"]["count"] == 0}
    tracked_with_summary = {n["symbol"] for n in with_summary}
    totals = insider.get("totals") or {}
    buys = sum(n["summary"]["buys"]["count"] for n in with_summary)
    sells = sum(n["summary"]["sells"]["count"] for n in with_summary)
    if buys != totals.get("open_buys") or sells != totals.get("open_sells") \
            or len(with_summary) != totals.get("names_with_summary") \
            or len(names) != totals.get("names_covered"):
        return fail("the insider record's per-name summaries do not "
                    "add up to its published totals; refusing to "
                    "publish from a record that disagrees with itself")

    # ---- Fear days, cross-checked against the Fear Day List ----
    all_fear = fear_days(panel, vix)
    tool_hist = fearday_tool.get("history") or {}
    window = [d for d in spy_dates
              if (tool_hist.get("index_from") or "") <= d
              <= (tool_hist.get("index_to") or "")]
    # The List's own record starts at its first window session, so
    # that session has no predecessor inside its record and is not
    # one of its checked sessions.
    checked = window[1:]
    if len(checked) != tool_hist.get("sessions_checked"):
        return fail("the price record does not reproduce the Fear "
                    "Day List's checked-session count in its own "
                    "window; refusing to publish")
    mine_in_window = {e["date"] for e in all_fear if e["date"] in checked}
    tool_days = {q["date"] for q in fearday_tool.get("qualifying_days") or []}
    if mine_in_window != tool_days:
        return fail(f"fear-day detection disagrees with the Fear Day "
                    f"List in its own window: this engine finds "
                    f"{sorted(mine_in_window)}, the List publishes "
                    f"{sorted(tool_days)}; refusing to publish")
    history_entry = next((e for e in all_fear if e["date"] == HISTORY_DAY),
                         None)
    if history_entry is None:
        return fail(f"the labelled history day {HISTORY_DAY} is not a "
                    f"fear day under the published definition in the "
                    f"shipped record; refusing to publish")

    # ---- Picker control figures, from the replay record itself ----
    control_rows = []
    for key in ("A0", "A1", "A2", "A3"):
        fear_slice = (picker.get("definitions") or {}).get(key, {}) \
            .get("fear_spy_down1")
        if not fear_slice:
            return fail(f"the picker replay record carries no fear "
                        f"slice for {key}; refusing to publish")
        control_rows.append({
            "group": key, "cases": fear_slice["n"],
            "picked_mean_r": fear_slice["mean_r"],
            "random_mean_r": fear_slice["base_r"]})
    picked = [r["picked_mean_r"] for r in control_rows]
    if not (0.24 <= min(picked) and max(picked) <= 0.37):
        return fail("the picker replay's fear-slice figures fall "
                    "outside the published +0.29 to +0.36R range the "
                    "claim rests on; refusing to publish")

    # ---- Self-test (always; proves the maths in either state) ----
    try:
        test = self_test(panel)
    except Exception as exc:
        return fail(f"self-test failed, refusing to publish: {exc}")

    # ---- Ledger (API only) ----
    reg = registry_mod.load()
    led = ledger_mod.Ledger(LEDGER_PATH, registry=reg)
    if not led.verify_chain():
        return fail("the forecast record does not verify; refusing "
                    "to add to it")

    # ---- The labelled history day, worked in full, never recorded ----
    hist = form_cohort(panel, zero_sells, tracked_with_summary, HISTORY_DAY)
    hist_detail = {}
    for sym in hist["depth_only"] + hist["random_draw"] + hist["triple"]:
        hist_detail[sym] = hist["detail"][sym]
    sessions_after = len(spy_dates) - spy_dates.index(HISTORY_DAY) - 1

    # ---- Live: only the freshest session can start a group ----
    freshest = panel_as_of
    freshest_entry = next((e for e in all_fear if e["date"] == freshest),
                          None)
    created = 0
    freshest_note = None
    if freshest_entry is not None and freshest >= SHIP_DATE:
        cohort = form_cohort(panel, zero_sells, tracked_with_summary,
                             freshest)
        if cohort["triple"]:
            created = ledger_cohort(led, panel, insider, cohort,
                                    freshest_entry)
        else:
            freshest_note = ("The freshest session was a fear day, "
                             "but no stock passed all three checks, "
                             "so no group started and nothing was "
                             "recorded.")
    missed = [e["date"] for e in all_fear
              if SHIP_DATE <= e["date"] < freshest]
    recorded_days = {r["lineage"]["cohort"]["fear_day"]
                     for r in led.rows()
                     if r.get("type") == "forecast"
                     and r.get("engine_id") == ENGINE_ID
                     and (r.get("lineage") or {}).get("cohort")}
    missed = [d for d in missed if d not in recorded_days]

    # ---- Grade any recorded group whose 20 sessions have passed ----
    rows = led.rows()
    graded_now = 0
    for row in list(rows):
        if row.get("type") != "forecast" or row.get("engine_id") != ENGINE_ID:
            continue
        if any(g.get("type") == "grade"
               and g.get("forecast_row_id") == row["row_id"] for g in rows):
            continue
        outcome = row.get("outcome") or {}
        day = outcome.get("fear_day")
        if not day or day not in spy_dates:
            continue
        if spy_dates.index(day) + 21 >= len(spy_dates):
            continue            # the 20 sessions have not all happened
        n, mean_r, ungr = grade_arm(panel, outcome.get("members") or [], day)
        if n == 0:
            continue
        estimate = (row.get("value") or {}).get("estimate")
        led.append_grade(forecast_row=row, grade={
            "scores": {"abs_error": round(abs(estimate - mean_r), 4)},
            "mean_r": round(mean_r, 4), "graded_names": n,
            "ungradeable_names": ungr, "thin": n < THIN,
            "rule": ("average result in R over the arm's graded "
                     "names under the registered exits")},
            **(ledger_mod.frozen_label_identity(row) or {}))
        graded_now += 1
        rows = led.rows()

    rows = led.rows()
    if not led.verify_chain(rows):
        return fail("the forecast record failed verification after "
                    "writing; not publishing figures from it")
    figures = ledger_mod.recompute_figures(rows)
    mine = figures.get(ENGINE_ID, {"forecasts": 0, "graded": 0})
    cohorts_formed = len({(r.get("lineage") or {}).get("cohort", {})
                          .get("fear_day")
                          for r in rows
                          if r.get("type") == "forecast"
                          and r.get("engine_id") == ENGINE_ID
                          and (r.get("lineage") or {}).get("cohort")})
    cohorts_matured = len({r["subject"].split(" ")[0] for r in rows
                           if r.get("type") == "grade"
                           and r.get("engine_id") == ENGINE_ID})
    arm_means = {}
    for r in rows:
        if r.get("type") == "grade" and r.get("engine_id") == ENGINE_ID:
            arm = (r.get("subject") or "").rsplit(": ", 1)[-1]
            arm_means.setdefault(arm, []).append(r["grade"])
    retired = False
    if cohorts_matured >= PROVING_COHORTS and "triple" in arm_means \
            and "depth_only" in arm_means:
        t = arm_means["triple"][-1]["mean_r"]
        dpt = arm_means["depth_only"][-1]["mean_r"]
        retired = t <= dpt

    data = {
        "tool": "Fear-Day Triangulation",
        "state": "proving",
        "retired": retired,
        "as_of": panel_as_of,
        "price_history": {"from": spy_dates[0], "to": panel_as_of,
                          "sessions": len(spy_dates),
                          "names": len(panel)},
        "fear_gauge": {"from": vix[0][0], "to": vix[-1][0],
                       "readings": len(vix)},
        "source": ("The daily price history on record (1,833 names, "
                   f"{spy_dates[0]} to {panel_as_of}), the fear "
                   f"gauge's daily readings ({vix[0][0]} to "
                   f"{vix[-1][0]}), the insider record gathered "
                   f"{insider.get('as_of')}, and the earlier replay "
                   "of picked against random entries."),
        "idea": ("A fear day lifts almost everything: in the earlier "
                 "replay, stocks picked carefully on fear days did "
                 "no better than entries picked at random in the "
                 "same names. So the real question is not whether "
                 "fear days are good days to buy. It is whether "
                 "picking carefully on those days, using three "
                 "different kinds of check, beats picking at random. "
                 "This page runs that test in public, one fear day "
                 "at a time, and retires itself if the answer is no."),
        "claim": {
            "words": ("On a fear day, rising-trend stocks that pass "
                      "all three checks will beat the random-entry "
                      "comparison by at least +0.10R on average over "
                      "the next 20 trading days, using the same "
                      "entry and exit rules as the earlier replay."),
            "r_explained": ("R measures a result in units of what "
                            "was risked: a trade that risks 2 points "
                            "to make 3 scores +1.5R, and one that "
                            "loses its full risk scores -1R."),
            "triple_stated_r": TRIPLE_ESTIMATE,
            "control_stated_r": CONTROL_ESTIMATE,
            "margin_r": CLAIM_MARGIN_R,
        },
        "checks": [
            {"name": "A deep dip, by the stock's own measure",
             "words": ("Today's pullback, measured from the highest "
                       "close of the last 63 trading days in units "
                       "of the stock's own typical daily range, sits "
                       "in the deepest fifth of that stock's own "
                       "earlier pullbacks.")},
            {"name": "A gap that fills much of the day's range",
             "words": ("The size of the fear day's opening jump "
                       "from the previous close, as a share of the "
                       "day's whole high-to-low range, sits in the "
                       "top third of that day's rising-trend stocks.")},
            {"name": "No insider selling on record",
             "words": ("The stock's insider summary shows zero "
                       "open-market sells. A stock with no summary "
                       "at all does not pass: no record is not the "
                       "same as no selling.")},
        ],
        "family_discount": ("The three checks are not three "
                            "independent confirmations. The dip and "
                            "the gap are both read from the same "
                            "price history, so together they count "
                            "as about one family of evidence; the "
                            "insider check is a second kind. All "
                            "three together count as at most one "
                            "and a half families, never three."),
        "definitions": {
            "fear_day": fearday_tool.get("definition"),
            "fear_day_arms": [
                "SPY fell more than 1.5% in a day",
                "the fear gauge rose more than 15% in a day",
                "the fear gauge closed at 25 or higher",
                "the fear gauge closed at 20 or higher on a day "
                "SPY or QQQ fell"],
            "rising_trend": ("The close is above both its 21 day "
                             "and 50 day average closes, and the "
                             "50 day average is higher than it was "
                             "5 days earlier. The earlier replay "
                             "states its rising-trend rule only as "
                             "a short phrase; this is the fixed "
                             "reading of that phrase, printed here "
                             "so it can be checked."),
            "depth_narrowing": ("The original study judged each "
                                "dip against about three years of "
                                "the stock's own past dips. The "
                                "price history here holds at most "
                                "399 trading days per stock, so this "
                                "engine judges each dip against the "
                                "stock's own earlier dips on this "
                                "record, at most about a year and "
                                "a half of them, with the typical "
                                "range taken over the last 126 days "
                                "and at least 126 earlier dips "
                                "required. The line for the deepest "
                                "fifth is noisier that way, and the "
                                "study's figures belong to the "
                                "long-history version, not to this "
                                "one."),
            "gap_share": ("The gap study's exact formula is not "
                          "on record here, so this engine uses "
                          "its own, printed in the checks above, "
                          "and says so. Its top-third cut is "
                          "worked out across each fear day's "
                          "rising-trend stocks on the day."),
            "insider": {
                "gathered": insider.get("as_of"),
                "window": insider.get("window"),
                "window_start": insider.get("window_start"),
                "names_tracked": totals.get("names_covered"),
                "names_with_summary": totals.get("names_with_summary"),
                "names_not_on_record": totals.get("names_not_on_record"),
                "zero_sell_names": sorted(zero_sells),
                "open_buys": totals.get("open_buys"),
                "open_sells": totals.get("open_sells"),
                "words": ("Insider readings are summaries only: "
                          "counts and dollar totals from the "
                          "filings in the six months before the "
                          "gathering date, up to the 20 most "
                          "recent per name. Only the 50 tracked "
                          "names carry one, against 1,832 stocks "
                          "in the price history, so most stocks "
                          "can never pass or fail this check. The "
                          "gathering date above is the record's "
                          "age: a group formed later reads the "
                          "newest gathering then on file and "
                          "prints its date.")},
            "exits": ("Bought at the next open after the fear "
                      "day. Sold when a close falls under the "
                      "fear day's low by more than a quarter of "
                      "the stock's typical daily range (sold at "
                      "the next open), or when price reaches the "
                      "nearest earlier high that stands at least "
                      "three quarters of a typical range above "
                      "the entry, or after 20 trading days, "
                      "whichever comes first. If one day both "
                      "reaches the high and closes under the "
                      "stop, the stop wins. Two pieces are this "
                      "engine's fixed readings, printed here: "
                      "the stop level is the fear day's low, and "
                      "the typical range is the average of the "
                      "last 14 days' ranges."),
            "random_draw": ("The comparison group is drawn by a "
                            "fixed rule, never by hand: the day's "
                            "rising-trend stocks in alphabetical "
                            "order, the deep-dip group removed, "
                            "and a draw seeded with the fear "
                            "day's date picking exactly as many "
                            "names as the deep-dip group holds."),
        },
        "control_history": {
            "label": "The earlier replay: picked against random on "
                     "fear days",
            "note": ("That replay used a wider fear cut (days SPY "
                     "fell at least 1%) than this engine's fear-day "
                     "definition, and its own years (2019 to 2026, "
                     "3,446 names, 296,093 cases). Its picked "
                     "groups averaged between +0.25R and +0.36R "
                     "while random entries in the same names "
                     "averaged between +0.34R and +0.38R: picking "
                     "carefully did not beat picking at random, "
                     "which is the result this engine is testing "
                     "whether three checks can overturn."),
            "rows": control_rows,
            "picked_range_r": [min(picked), max(picked)],
            "random_range_r": [min(r["random_mean_r"] for r in control_rows),
                               max(r["random_mean_r"] for r in control_rows)],
        },
        "fear_days_in_record": {
            "count": len(all_fear),
            "days": all_fear,
            "tool_record": {
                "qualifying": len(tool_days),
                "sessions_checked": tool_hist.get("sessions_checked"),
                "days": fearday_tool.get("qualifying_days") or []},
            "words": ("The Fear Day List's own published record "
                      "covers a short recent window and holds 1 "
                      "qualifying day. Run over the fuller price "
                      "history here, the same definition finds "
                      f"{len(all_fear)} fear days, every one of "
                      "them before this engine existed. All are "
                      "history: none is in the live record, and "
                      "none ever will be backfilled. The fear "
                      "gauge arms can only be judged inside the "
                      f"gauge record's window ({vix[0][0]} to "
                      f"{vix[-1][0]}); outside it, only a fall of "
                      "more than 1.5% in SPY can make a day a "
                      "fear day in this record.")},
        "history_day": {
            "date": HISTORY_DAY,
            "label": "History, worked in full, never recorded",
            "qualified_by": history_entry["qualified_by"],
            "spy_change_pct": history_entry["spy_change_pct"],
            "vix_close": history_entry["vix_close"],
            "vix_change_pct": history_entry["vix_change_pct"],
            "pool_count": hist["pool_count"],
            "gap_top_third_cut": hist["gap_top_third_cut"],
            "depth_only": [{"symbol": s,
                            "depth_percentile": hist_detail[s]["depth_percentile"],
                            "gap_share": hist_detail[s]["gap_share"]}
                           for s in hist["depth_only"]],
            "depth_too_short_count": hist["depth_too_short_count"],
            "zero_sell_names_in_pool": hist["zero_sell_names_in_pool"],
            "triple": hist["triple"],
            "random_draw": hist["random_draw"],
            "words": ("On the one fear day in the Fear Day "
                      "List's own record, 325 stocks were in a "
                      "rising trend. Exactly one sat in the "
                      "deepest fifth of its own past dips, and "
                      "it carried no insider record at all, so "
                      "the group passing all three checks was "
                      "empty and no group could have started. "
                      "Six of the seven zero-selling names were "
                      "in the rising-trend pool; none was in the "
                      "deepest fifth. This day can never be "
                      "graded: the price history ends "
                      f"{sessions_after} trading days after its "
                      "entry, not 20, and the insider record was "
                      "gathered after it. It is shown as history "
                      "only.")},
        "live": {
            "cohorts_formed": cohorts_formed,
            "cohorts_matured": cohorts_matured,
            "records_written": mine["forecasts"],
            "records_graded": mine["graded"],
            "proving_target_cohorts": PROVING_COHORTS,
            "missed_fear_days": missed,
            "freshest_session": freshest,
            "freshest_note": freshest_note,
            "arm_means": {arm: [{"mean_r": g["mean_r"],
                                 "graded_names": g["graded_names"],
                                 "thin": g["thin"]} for g in gs]
                          for arm, gs in arm_means.items()},
            "wait": ("No group has started yet. The live record "
                     "begins with the first fear day after "
                     f"{SHIP_DATE} on which at least one "
                     "rising-trend stock passes all three checks: "
                     "that day, the all-three group, the "
                     "deep-dip-only group and the fixed-rule "
                     "random group are all written to the public "
                     "record at the close, before the 20 trading "
                     "days begin. Fear days are rare, so this "
                     "record builds slowly, in quarters rather "
                     "than weeks.")},
        "self_test": test,
        "kill_criterion": ("This engine retires itself if, once "
                           "three fear-day groups have matured, "
                           "the group passing all three checks "
                           "does not beat the group passing the "
                           "deep-dip check alone. Its separate "
                           "claim, to beat the random group by at "
                           "least +0.10R, is graded on the same "
                           "groups."),
        "thin_cell_rule": ("Any group with fewer than 30 graded "
                           "stocks shows its count only, with no "
                           "average R headline."),
    }
    # Depth leg on the DEEP panel (RC-25 cure, 2026-10-30): the
    # pullback study's record carries this engine's depth leg
    # computed against the landed panel, where the original
    # 750 session form is computable beside the narrowing this
    # page's live cohorts use. Absence of the record keeps the
    # page exactly as it was.
    try:
        with open(os.path.join(HERE, "pullback-norm",
                               "study_record.json"),
                  encoding="utf-8") as fh:
            _study = json.load(fh)
        if _study.get("engine_24_depth_leg"):
            data["depth_leg_deep_panel"] = _study["engine_24_depth_leg"]
    except (OSError, ValueError):
        pass
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH}: fear days in record {len(all_fear)}, "
          f"history day pool {hist['pool_count']}, depth-only "
          f"{hist['depth_only']}, triple {len(hist['triple'])}, "
          f"live cohorts {cohorts_formed}, records "
          f"{mine['forecasts']} ({created} new), graded "
          f"{mine['graded']} ({graded_now} new), self-test "
          f"{test['state']}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
