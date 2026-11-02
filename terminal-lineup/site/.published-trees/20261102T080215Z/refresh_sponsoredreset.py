#!/usr/bin/env python3
"""Refresh the Sponsored Reset engine (Forecast Engine 25).

=====================================================================
CANDIDATE-REGISTER TRIPLE (written before any computation, per the
lineup's adopted standards)

1. EVIDENCE CLASS
   The parent is a genuine survivor. The RESET study on record
   (the study record's rows for the pullback studies and the
   reset-universe study) measured a combined score built from two
   parts, laggard relative strength and down-volume capitulation,
   on washed-out names on fear days: a link to the next 20
   sessions of +0.053 in its discovery years and +0.028 in its
   holdout years, holdout confirmed, grade B. Its rising-trend
   version faded in holdout and is not used. The market gate
   beside it is grade B too: leader setups made +0.1 to +0.2
   percent over 20 sessions in up markets against -1.2 to -1.3
   percent otherwise. The filings condition this engine adds
   (big holders not leaving, or an insider buy on record) has
   never been graded as a forecaster anywhere in the record:
   that untested increment, worth at least half a point or the
   engine retires, is the whole test. This engine's own live
   record: none. It ships with zero cohorts, waiting on the
   next fear day.

2. RECONSTRUCTION CHOICES (every constant, named before computing)
   - Fear day: the Fear Day List's settled definition, reused
     verbatim through the Fear-Day Triangulation engine's
     published record (four arms: SPY fell more than 1.5 percent
     in a day, or the fear gauge rose more than 15 percent in a
     day, closed at 25 or higher, or closed at 20 or higher on a
     day SPY or QQQ fell). The qualifying days in the shipped
     price history (65 on the settled record as recounted
     2026-10-30, when the fear gauge record was cured; the
     earlier count of 22 was measured on the truncated gauge
     record) are taken from that settled record and
     cross-checked against the price history here; the
     definition is never re-derived or forked. All of them are
     history and are never recorded.
   - The deep panel the study ran on (2016 to 2026, thousands
     of names including ones that later closed) is NOT on this
     disk. Everything below is built from the shipped daily
     history only (1,833 names, at most 399 sessions each,
     2025-03-25 to 2026-10-23, a survivors-only list), and that
     narrowing is printed on the page.
   - Washed-out state, the study code's own definition, found
     on this disk in a cached copy of the study code and read
     in full during this engine's inspection: the close is at
     or below 65 percent of the highest high of the last 252
     sessions (today included), AND at or below 110 percent of
     the lowest low of the last 252 sessions. NAMED DIFFERENCE
     from this engine's written design, which says 35 to 80
     percent off the high: the code carries no 80 percent
     floor, so a name more than 80 percent off its high still
     counts when it sits near its low. The build follows the
     parent code exactly and names the difference on the page;
     it does not silently add a floor.
   - Liquid filter, exact from the same code: the close is
     above 5 and the 20-session mean of close times share
     volume is above 5 million dollars. Narrowing, stated: the
     shipped history carries one close series per name, so that
     series serves as both the adjusted close the code reads
     and the raw close its filter reads.
   - Universe keep, exact: a name needs at least 320 bars in
     total, and a day counts only from the name's own session
     number 260 onward (counting from 0), with the state and
     the liquid filter both required. Consequence on the
     shipped history, stated on the page: no fear day before
     2026-06-05 can form a pool at all.
   - The combined score, exact from the same code: two parts
     per name per day. Part one (laggard strength, sign -1):
     the name's 10-session close return minus SPY's 10-session
     close return the same day. Part two (down-volume
     capitulation, sign +1): share volume on days the close
     fell, summed over the last 10 sessions, divided by the
     per-10-session average of the same sum over the 30
     sessions before those (the sum taken after shifting 10
     sessions, divided by 3); a reading above 1 means down
     volume is running hot. The score is the mean of the two
     signed ranks: each part is ranked across that day's
     washed-out names as a share of the count (average ranks
     for ties), the laggard part's rank is subtracted, the
     capitulation part's rank is added, and the two are
     averaged. Matching the score on a day = its top fifth:
     the day's scores are ranked in the order they were built
     (the code's own first-come ranking for ties), split into
     five equal groups, and the top group is taken; days with
     fewer than 10 scored names form no matching group.
   - The study's own fear cut (SPY down at least 1 percent, or
     SPY under its 50-session average) and its own forward
     measure (next session's open to the close 20 sessions
     ahead, measured against the same day's same-state average)
     are the study's grading machinery, NOT this engine's: this
     engine keeps the settled fear-day definition above and
     grades mean SPY excess per its design and registry. The
     study's figures therefore never transfer to this engine.
   - Market gate, exact test: SPY's close on the fear day is
     above its 200-session mean close (that day and the 199
     before it) AND that mean is above its value 20 sessions
     earlier. The gate is undefined until 220 SPY sessions
     exist, which covers the first 12 fear days on the shipped
     history. On the days it is defined: it passes 2026-02-12,
     2026-03-12, 2026-06-05, 2026-06-10, 2026-07-29 and
     2026-10-16, and fails 2026-03-20, 2026-03-26, 2026-03-27.
   - Sponsorship, two legs, either one enough. Leg one (big
     holders): the count of distinct filing managers holding
     the name in the newer of the two quarters on record is at
     least the count in the older quarter (not falling). The
     counts are recomputed here from the two stored filing
     sets on record (periods ended 2026-03-31, 8,871 filers,
     and 2026-06-30, 8,857 filers; the newer filing for each
     manager and period wins, plain shares only, no option
     rows), and the recomputed filer counts must match the
     published tracker record or nothing is published. The
     name-to-identifier map on record resolves 2,526
     identifiers; only 346 of the 1,833 names in the price
     history resolve AND carry a holder record in either
     quarter, and that coverage is the binding limit of this
     leg: a name with no map entry can never pass or fail it.
     The reading is one current snapshot, never point-in-time
     for a past fear day; a live group reads the newest two
     quarters on record at its date and prints their dates.
     Leg two (insider buy): the name's insider summary on
     record shows at least one open-market buy. The summaries
     were gathered 2026-10-26 from filings filed 2026-04-26 to
     2026-10-26, up to the 20 most recent per name, covering 50
     tracked names, 43 with a summary, 18 buys against 326
     sells in total; the buy flag holds for exactly five names
     (CCI, GO, OXY, UFCS, USO). Summaries carry counts and
     dollar totals only, never who traded or on which day, so
     several insiders buying close together cannot be
     identified from them, and the page says so. A name with
     no record on either leg never counts as sponsored.
   - Ledger shape: per fear-day group, at the fear day's
     close, THREE records written the same day through the
     shared record's own append call, one per arm (sponsored;
     the combined score alone; the combined score plus the
     market gate), each with quantity
     mean_20_session_spy_excess_points and a stated figure of
     2.0 points, so all three grade on one scale; the verdict
     below is computed from the arms' realised averages, not
     from the grades. Each record's lineage carries its arm's
     full member list, the price-history hash, the two filing
     periods, the insider gathering date and the gate reading.
     Horizon: opens the session after the fear day, closes the
     20th session after it, counted on SPY's session calendar.
     Families: the sponsored arm is price plus company
     filings; the two baselines are price only. A group forms
     only when the gate passes AND the sponsored arm is not
     empty: when the gate fails the forecast does not fire at
     all, and an empty sponsored arm starts no group (the
     settled precedent of the engine before this one). Only
     the freshest session in the price history can start a
     group: a post-ship fear day that is no longer freshest
     and was never recorded is counted as missed and is NEVER
     backfilled.
   - Grading: when the price history covers a recorded group's
     full 20 sessions, each arm's average is computed as the
     mean over its graded names of 100 times the name's
     20-session return minus SPY's over the same sessions
     (close at the fear day to the close 20 of the name's own
     sessions later; SPY on its own calendar), and graded
     against the stated 2.0 through the shared record's own
     grade call, with the count of graded names beside it. The
     shared grading runner cannot yet resolve this kind of
     outcome (a group average), so grades are appended by this
     engine through the machinery's grade call, never by
     forking the runner. Names whose 20 sessions are not in
     the record are counted ungradeable, never dropped
     silently.
   - Thin-cell rule: any arm or group with fewer than 30
     graded names shows its count only, no average headline.
     Every sponsored arm in the history below holds at most 4
     names, so history is published as counts only.
   - Kill criterion, in plain words, printed in advance:
     after 3 fear-day groups have matured, if the filings
     condition adds less than half a point of average excess
     over the gated baseline (the combined score plus the
     market gate, without the filings condition), this engine
     retires.
   - Ship date: this engine first published on 2026-10-29.
     Fear days on or before that date are history, never
     recorded; the first group can only start on a fear day
     after it.

3. NON-CLAIMS
   - The study's figures (+0.053 and +0.028 on its own fear
     cut and its own forward measure) are its own record,
     shown labelled as the parent's record. They are not this
     engine's results, and they do not transfer to the shipped
     history, the settled fear-day definition, or this
     engine's grading.
   - The history below applies today's filings snapshot to
     past fear days; it is labelled not point-in-time, and
     every sponsored arm in it is far under the thin-cell
     line, so it carries counts only and no verdict.
   - Nothing from any history computation or self-test is
     ever written to the live record. Only a real fear-day
     group, formed on the freshest session after the ship
     date with the gate passing and a non-empty sponsored
     arm, is recorded there, through the machinery's own
     append call.

=====================================================================
Behaviour: read the price history, the settled fear-day record,
the two filing sets and their identifier map, the published
tracker record and the insider record (fails closed on any
disagreement between them, or with the shared record), run the
self-test, work the labelled history through the full pipeline
without recording it, form a group only if the freshest session
is a post-ship fear day with the gate passing and a non-empty
sponsored arm, grade any matured recorded group, then write
data.json with the live figures recomputed from the shared
record alone. Idempotent: rerunning with the same sources
records nothing new and rewrites the same data.json.
Timestamps come from the sources, never the clock.
"""

import bisect
import datetime
import io
import json
import os
import sys
import tempfile
import zipfile
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(HERE)
PANEL_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")
FEARDAY_PATH = os.path.join(HERE, "fear-day-triangulation", "data.json")
INSIDER_PATH = os.path.join(HERE, "insider-wire", "data.json")
TRACKER_PATH = os.path.join(HERE, "13f-tracker", "data.json")
F13_DIR = os.path.expanduser("~/workspace/morgue/data_cache/13f")
CUSIP_MAP_PATH = os.path.join(F13_DIR, "cusip_map.json")
OUT_PATH = os.path.join(HERE, "sponsored-reset", "data.json")
try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import attestation_block as _ab
except ImportError:  # refresh stays runnable standalone
    _ab = None

try:
    import session_history as _sh
except ImportError:  # refresh stays runnable standalone
    _sh = None
LEDGER_PATH = os.path.join(LINEUP, "forecast", "ledger.jsonl")
HISTORY_PATH = os.path.join(HERE, "sponsored-reset",
                            "session-history.json")

sys.path.insert(0, LINEUP)
from forecast import ledger as ledger_mod  # noqa: E402
from forecast import registry as registry_mod  # noqa: E402

ENGINE_ID = "engine_25"
SHIP_DATE = "2026-10-29"
THIN = 30
PROVING_COHORTS = 3
STATED_POINTS = 2.0
KILL_MARGIN_POINTS = 0.5
MIN_BARS = 320
FIRST_INDEX = 260
STATE_WINDOW = 252
LIQ_WINDOW = 20


def fail(msg):
    print(f"Sponsored Reset refresh: {msg}", file=sys.stderr)
    return 1


# ---- price features (the study code's definitions) -------------------------
def down_volumes(closes, vols):
    out = [0.0]
    for j in range(1, len(closes)):
        out.append(vols[j] if closes[j] < closes[j - 1] else 0.0)
    return out


def name_features(closes, highs, lows, vols, i, spy_r10):
    """The washed-out state, the liquid filter and the two score
    parts for one name at its own session i. Returns a dict, or
    None when the day does not count for this name."""
    if i < FIRST_INDEX or i < STATE_WINDOW - 1 or i < 39 or i < 10:
        return None
    close = closes[i]
    hi = max(highs[i - STATE_WINDOW + 1:i + 1])
    lo = min(lows[i - STATE_WINDOW + 1:i + 1])
    if not (close <= 0.65 * hi and close <= 1.10 * lo):
        return None
    dv20 = sum(closes[j] * vols[j]
               for j in range(i - LIQ_WINDOW + 1, i + 1)) / LIQ_WINDOW
    if not (close > 5.0 and dv20 > 5_000_000.0):
        return None
    dv = down_volumes(closes, vols)
    recent = sum(dv[i - 9:i + 1])
    prior = sum(dv[i - 39:i - 9]) / 3.0
    if prior <= 0:
        return None
    f6 = recent / prior
    if spy_r10 is None:
        return None
    f7 = closes[i] / closes[i - 10] - 1.0 - spy_r10
    return {"f6": f6, "f7": f7, "off_high_pct": (close / hi - 1.0) * 100.0}


def composite_top_fifth(scored):
    """scored: [(symbol, f7, f6)] in build order. Returns the top
    fifth's symbols under the study code's own grouping (signed
    average ranks for the score; first-come ranks split into five
    equal groups for the top group), or [] under 10 scored."""
    n = len(scored)
    if n < 10:
        return []
    def pct_ranks(vals):
        order = sorted(range(n), key=lambda k: vals[k])
        ranks = [0.0] * n
        k = 0
        while k < n:
            j = k
            while j + 1 < n and vals[order[j + 1]] == vals[order[k]]:
                j += 1
            avg = (k + j) / 2.0 + 1.0          # average rank, 1-based
            for t in range(k, j + 1):
                ranks[order[t]] = avg / n
            k = j + 1
        return ranks
    r7 = pct_ranks([s[1] for s in scored])
    r6 = pct_ranks([s[2] for s in scored])
    scores = [(-r7[k] + r6[k]) / 2.0 for k in range(n)]
    # first-come ranks of the scores (ties keep build order)
    order = sorted(range(n), key=lambda k: (scores[k], k))
    first_rank = [0] * n
    for pos, k in enumerate(order):
        first_rank[k] = pos + 1
    # five equal groups over the first-come ranks, as the code's
    # quantile split does (linear-interpolated edges, right-closed)
    vals = sorted(first_rank)
    def quantile(q):
        pos = q * (n - 1)
        base = int(pos)
        frac = pos - base
        if base + 1 >= n:
            return float(vals[-1])
        return vals[base] + frac * (vals[base + 1] - vals[base])
    edges = [quantile(q / 5.0) for q in range(1, 5)]
    top = []
    for k in range(n):
        group = bisect.bisect_left(edges, first_rank[k])
        if group == 4:
            top.append(scored[k][0])
    return top


def gate_reading(spy_closes, i):
    """SPY above its rising 200-session average. None when the
    average cannot be read yet (fewer than 220 sessions)."""
    if i < 219:
        return None
    mean = sum(spy_closes[i - 199:i + 1]) / 200.0
    mean_prev = sum(spy_closes[i - 219:i - 19]) / 200.0
    return {"pass": bool(spy_closes[i] > mean and mean > mean_prev),
            "close": round(spy_closes[i], 2),
            "mean_200": round(mean, 2),
            "rising": bool(mean > mean_prev)}


def mean_excess(panel, spy, members, day):
    """Mean 20-session SPY excess in points over the gradeable
    members. Returns (graded_count, mean or None, ungradeable)."""
    spy_dates = [r[0] for r in spy]
    if day not in spy_dates:
        return 0, None, len(members)
    si = spy_dates.index(day)
    if si + 20 >= len(spy_dates):
        return 0, None, len(members)
    spy_ret = float(spy[si + 20][4]) / float(spy[si][4]) - 1.0
    vals = []
    ungr = 0
    for sym in members:
        rows = panel.get(sym)
        if not rows:
            ungr += 1
            continue
        dates = [r[0] for r in rows]
        if day not in dates:
            ungr += 1
            continue
        j = dates.index(day)
        if j + 20 >= len(rows):
            ungr += 1
            continue
        vals.append(100.0 * ((float(rows[j + 20][4]) / float(rows[j][4])
                              - 1.0) - spy_ret))
    if not vals:
        return 0, None, ungr
    return len(vals), sum(vals) / len(vals), ungr


def form_cohort(panel, spy_maps, sponsorship, day):
    """The full pipeline for one fear day: washed-out liquid pool,
    the combined score's top fifth, the gate, and the sponsored
    arm. Pure computation: records nothing."""
    spy_dates, spy_closes, spy_r10_by_date = spy_maps
    if day not in spy_dates:
        return None
    si = spy_dates.index(day)
    scored = []
    for sym in sorted(panel):
        if sym == "SPY":
            continue
        rows = panel[sym]
        if len(rows) < MIN_BARS:
            continue
        dates = [r[0] for r in rows]
        if day not in dates:
            continue
        i = dates.index(day)
        closes = [float(r[4]) for r in rows]
        highs = [float(r[2]) for r in rows]
        lows = [float(r[3]) for r in rows]
        vols = [float(r[5]) for r in rows]
        feat = name_features(closes, highs, lows, vols, i,
                             spy_r10_by_date.get(day))
        if feat is None:
            continue
        scored.append((sym, feat["f7"], feat["f6"]))
    comp = composite_top_fifth(scored)
    sponsored = [s for s in comp if sponsorship.get(s)]
    return {"date": day, "pool": [s[0] for s in scored],
            "pool_count": len(scored), "composite": comp,
            "sponsored": sponsored, "gate": gate_reading(spy_closes, si)}


# ---- 13F holder counts -------------------------------------------------------
def load_holder_counts(periods):
    """Recompute holder counts per mapped identifier for the two
    periods, from the stored filing sets, exactly as inspected:
    the newest filing per manager and period wins (later filing
    date, then amended over original); plain shares only."""
    with open(CUSIP_MAP_PATH, "r", encoding="utf-8") as fh:
        cmap = json.load(fh)["cusip_map"]
    wanted = set(cmap)
    zips = sorted(os.path.join(F13_DIR, n) for n in os.listdir(F13_DIR)
                  if n.endswith("_form13f.zip"))
    if not zips:
        raise RuntimeError("no filing sets on record")
    best = {}
    for path in zips:
        with zipfile.ZipFile(path) as zf:
            subs = {}
            with zf.open("SUBMISSION.tsv") as fh:
                text = io.TextIOWrapper(fh, encoding="utf-8",
                                        errors="replace")
                header = text.readline().rstrip("\n").split("\t")
                col = {n: k for k, n in enumerate(header)}
                for line in text:
                    p = line.rstrip("\n").split("\t")
                    if len(p) < len(header):
                        continue
                    if p[col["SUBMISSIONTYPE"]] not in ("13F-HR",
                                                        "13F-HR/A"):
                        continue
                    filed = datetime.datetime.strptime(
                        p[col["FILING_DATE"]].strip(),
                        "%d-%b-%Y").date().isoformat()
                    period = datetime.datetime.strptime(
                        p[col["PERIODOFREPORT"]].strip(),
                        "%d-%b-%Y").date().isoformat()
                    subs[p[col["ACCESSION_NUMBER"]]] = {
                        "accession": p[col["ACCESSION_NUMBER"]],
                        "cik": p[col["CIK"]], "period": period,
                        "filed": filed,
                        "amended": p[col["SUBMISSIONTYPE"]].endswith("/A")}
            for sub in subs.values():
                key = (sub["cik"], sub["period"])
                cur = best.get(key)
                rank = (sub["filed"], 1 if sub["amended"] else 0)
                if cur is None or rank > (cur["filed"],
                                          1 if cur["amended"] else 0):
                    best[key] = sub
    filers = Counter(per for (_cik, per) in best)
    acc_period = {}
    for (cik, per), f in best.items():
        if per in periods:
            acc_period[f["accession"]] = (per, cik)
    holders = {per: {} for per in periods}
    for path in zips:
        with zipfile.ZipFile(path) as zf:
            with zf.open("INFOTABLE.tsv") as fh:
                text = io.TextIOWrapper(fh, encoding="utf-8",
                                        errors="replace")
                header = text.readline().rstrip("\n").split("\t")
                col = {n: k for k, n in enumerate(header)}
                for line in text:
                    p = line.rstrip("\n").split("\t")
                    if len(p) < len(header):
                        continue
                    meta = acc_period.get(p[col["ACCESSION_NUMBER"]])
                    if meta is None:
                        continue
                    cu = p[col["CUSIP"]]
                    if cu not in wanted:
                        continue
                    if p[col["SSHPRNAMTTYPE"]] != "SH":
                        continue
                    if p[col["PUTCALL"]].strip():
                        continue
                    per, cik = meta
                    holders[per].setdefault(cu, set()).add(cik)
    cur_per, pri_per = periods[0], periods[1]
    out = {}
    for cu, ticker in cmap.items():
        cur = len(holders[cur_per].get(cu, ()))
        pri = len(holders[pri_per].get(cu, ()))
        out[ticker] = {"cusip": cu, "current": cur, "prior": pri,
                       "has_record": bool(cur or pri),
                       "not_falling": bool((cur or pri) and cur >= pri)}
    return out, filers


# ---- self-test -----------------------------------------------------------------
def self_test(panel):
    """Prove the feature maths on hand-built series with known
    answers, the score's top fifth on a known pool, the gate on a
    known series, the group grading on known prices, and the
    three-arm recording on a throwaway copy of the record.
    Raises on any disagreement."""
    # A steady decline: every close falls, so all volume is down
    # volume and the capitulation part is exactly 1.0; the close
    # sits at its own low and far under 65 percent of the
    # 252-session high, so the washed-out state holds; the
    # dollar volume is far above the filter.
    closes = [100.0 * (0.995 ** k) for k in range(330)]
    highs = [c * 1.001 for c in closes]
    lows = [c * 0.999 for c in closes]
    vols = [2_000_000.0] * 330
    feat = name_features(closes, highs, lows, vols, 319, 0.0)
    if feat is None:
        raise RuntimeError("the steady-decline series is not in the "
                           "washed-out liquid state")
    if abs(feat["f6"] - 1.0) > 1e-9:
        raise RuntimeError(f"capitulation part on all-down volume is "
                           f"{feat['f6']}, expected 1.0")
    want_f7 = 0.995 ** 10 - 1.0
    if abs(feat["f7"] - want_f7) > 1e-9:
        raise RuntimeError(f"laggard part is {feat['f7']}, expected "
                           f"{want_f7}")
    rising = [100.0 + 0.5 * k for k in range(330)]
    if name_features(rising, [c * 1.001 for c in rising],
                     [c * 0.999 for c in rising], vols, 319, 0.0) \
            is not None:
        raise RuntimeError("a steadily rising series passed the "
                           "washed-out state")
    # Top fifth on a known pool of 10: names built so the score
    # order is known (laggard part most negative and capitulation
    # highest for the first names).
    pool = [(f"N{k}", -0.10 + 0.01 * k, 2.0 - 0.1 * k)
            for k in range(10)]
    top = composite_top_fifth(pool)
    if sorted(top) != ["N0", "N1"]:
        raise RuntimeError(f"top fifth on the known pool is {top}, "
                           f"expected N0 and N1")
    if composite_top_fifth(pool[:9]) != []:
        raise RuntimeError("a pool of 9 formed a matching group")
    # Gate on known series: flat then rising means pass at the end;
    # a falling series fails.
    up = [100.0] * 200 + [100.0 + k for k in range(1, 41)]
    g = gate_reading(up, len(up) - 1)
    if not g or not g["pass"]:
        raise RuntimeError("the rising series does not pass the gate")
    down = [300.0 - k for k in range(240)]
    g2 = gate_reading(down, len(down) - 1)
    if not g2 or g2["pass"]:
        raise RuntimeError("the falling series passes the gate")
    if gate_reading(up, 100) is not None:
        raise RuntimeError("the gate read a series too short to judge")
    # Group grading on known prices: the member doubles SPY's move.
    def rows(base, step, n=30):
        return [[f"2026-02-{k + 1:02d}", base + step * k, base + step * k,
                 base + step * k, base + step * k, 1.0] for k in range(n)]
    fake = {"SPY": rows(100.0, 1.0), "AAA": rows(100.0, 2.0)}
    n, mean, ungr = mean_excess(fake, fake["SPY"], ["AAA"], "2026-02-01")
    want = 100.0 * ((140.0 / 100.0 - 1.0) - (120.0 / 100.0 - 1.0))
    if n != 1 or ungr != 0 or abs(mean - want) > 1e-9:
        raise RuntimeError(f"group grading gave {(n, mean, ungr)}, "
                           f"expected (1, {want}, 0)")
    # Three-arm recording on a throwaway copy.
    reg = registry_mod.load()
    with tempfile.TemporaryDirectory() as td:
        scratch = ledger_mod.Ledger(os.path.join(td, "ledger.jsonl"),
                                    registry=reg)
        scratch.append_genesis("sponsored reset self-test")
        lineage = {"source_artifacts": [
                       {"path": "synthetic (self-test, not a record)",
                        "sha256": ledger_mod.file_sha256(PANEL_PATH)}],
                   "clocks": {c: "2026-10-16"
                              for c in ledger_mod.CLOCK_FIELDS},
                   "note": "Self-test only; never the live record."}
        made = 0
        for arm, fams in (
                ("sponsored", ["price", "filings_positioning"]),
                ("composite_alone", ["price"]),
                ("composite_plus_gate", ["price"])):
            _row, created = scratch.append_forecast_declared(
                engine_id=ENGINE_ID, issued_ts="2026-10-16",
                subject="2026-10-16 fear-day cohort: " + arm,
                quantity="mean_20_session_spy_excess_points",
                value={"estimate": STATED_POINTS},
                horizon_open="2026-10-19", horizon_close="2026-11-13",
                lineage=lineage, families=fams,
                outcome={"kind": "cohort_mean_spy_excess_20_sessions",
                         "arm": arm, "members": ["AAA"],
                         "fear_day": "2026-10-16"})
            made += 1 if created else 0
        figs = ledger_mod.recompute_figures(scratch.rows())
        if not scratch.verify_chain() or made != 3 \
                or figs[ENGINE_ID]["forecasts"] != 3:
            raise RuntimeError("throwaway three-arm recording failed")
    return {"state": "passed", "feature_cases_checked": 5,
            "ledger_arms_checked": 3}


# ---- live ledgering --------------------------------------------------------------
def session_after(spy_dates, day, n):
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


def ledger_cohort(led, panel, filings, insider, cohort):
    spy_dates = [r[0] for r in panel["SPY"]]
    day = cohort["date"]
    horizon_open = session_after(spy_dates, day, 1)
    horizon_close = session_after(spy_dates, day, 20)
    panel_hash = ledger_mod.file_sha256(PANEL_PATH)
    arms = (
        ("sponsored", cohort["sponsored"],
         ["price", "filings_positioning"]),
        ("composite_alone", cohort["composite"], ["price"]),
        ("composite_plus_gate", cohort["composite"], ["price"]),
    )
    created = 0
    for arm, members, fams in arms:
        lineage = {
            "source_artifacts": [
                {"path": PANEL_PATH, "sha256": panel_hash},
                {"path": INSIDER_PATH,
                 "sha256": ledger_mod.file_sha256(INSIDER_PATH)},
                {"path": CUSIP_MAP_PATH,
                 "sha256": ledger_mod.file_sha256(CUSIP_MAP_PATH)}],
            "clocks": {c: day for c in ledger_mod.CLOCK_FIELDS},
            "cohort": {
                "fear_day": day, "arm": arm, "members": list(members),
                "pool_count": cohort["pool_count"],
                "gate": cohort["gate"],
                "filings_periods": filings["periods"],
                "insider_gathered": insider["as_of"],
                "note": ("Fear-day group recorded at the fear day's "
                         "close; graded at 20 sessions as the arm's "
                         "average gain over SPY.")},
        }
        _row, was = led.append_forecast_declared(
            engine_id=ENGINE_ID, issued_ts=day,
            subject=f"{day} fear-day cohort: {arm}",
            quantity="mean_20_session_spy_excess_points",
            value={"estimate": STATED_POINTS},
            horizon_open=horizon_open, horizon_close=horizon_close,
            lineage=lineage, families=fams,
            outcome={"kind": "cohort_mean_spy_excess_20_sessions",
                     "arm": arm, "members": list(members),
                     "fear_day": day})
        created += 1 if was else 0
    return created


# ---- build -------------------------------------------------------------------------
def build():
    for path, label in ((PANEL_PATH, "price history"),
                        (FEARDAY_PATH, "settled fear-day record"),
                        (INSIDER_PATH, "insider record"),
                        (TRACKER_PATH, "tracker record"),
                        (CUSIP_MAP_PATH, "identifier map")):
        if not os.path.exists(path):
            return fail(f"{label} not found: {path}")
    with open(PANEL_PATH, "r", encoding="utf-8") as fh:
        panel_raw = json.load(fh)
    panel = {sym: sorted(rows, key=lambda r: r[0])
             for sym, rows in panel_raw.items()}
    if "SPY" not in panel:
        return fail("the price history carries no SPY")
    with open(FEARDAY_PATH, "r", encoding="utf-8") as fh:
        fearday = json.load(fh)
    with open(INSIDER_PATH, "r", encoding="utf-8") as fh:
        insider = json.load(fh)
    with open(TRACKER_PATH, "r", encoding="utf-8") as fh:
        tracker = json.load(fh)
    spy = panel["SPY"]
    spy_dates = [r[0] for r in spy]
    spy_closes = [float(r[4]) for r in spy]
    panel_as_of = spy_dates[-1]
    spy_r10_by_date = {}
    for k in range(10, len(spy)):
        spy_r10_by_date[spy_dates[k]] = spy_closes[k] / spy_closes[k - 10] - 1.0
    spy_maps = (spy_dates, spy_closes, spy_r10_by_date)

    # ---- Settled fear days, cross-checked, never re-derived ----
    # Count re-registered 2026-10-30 (engine refresh cure): the
    # settled register was recounted at 65 days when the fear
    # gauge record was cured (the earlier count of 22 was
    # measured on the truncated 23-close gauge record). The
    # check is that every settled day stands inside the price
    # history, never a pinned count: the record's own days are
    # the construction.
    fear_entries = (fearday.get("fear_days_in_record") or {}).get("days") \
        or []
    fear_days = [e["date"] for e in fear_entries]
    if not fear_days or any(d not in spy_dates for d in fear_days):
        return fail("the settled fear-day record does not hold "
                    "its days inside the price history; "
                    "refusing to publish")

    # ---- Insider record, cross-checked against its own totals ----
    names = insider.get("names") or []
    with_summary = [n for n in names if n.get("summary")]
    totals = insider.get("totals") or {}
    buys = sum(n["summary"]["buys"]["count"] for n in with_summary)
    sells = sum(n["summary"]["sells"]["count"] for n in with_summary)
    if buys != totals.get("open_buys") or sells != totals.get("open_sells") \
            or len(with_summary) != totals.get("names_with_summary") \
            or len(names) != totals.get("names_covered"):
        return fail("the insider record's per-name summaries do not "
                    "add up to its published totals; refusing to "
                    "publish from a record that disagrees with itself")
    any_buy = sorted(n["symbol"] for n in with_summary
                     if n["summary"]["buys"]["count"] >= 1)

    # ---- Filing holder counts, cross-checked against the tracker ----
    periods = [tracker.get("current_period"), tracker.get("prior_period")]
    if not all(periods):
        return fail("the tracker record does not name its two periods")
    try:
        holders, filers = load_holder_counts(periods)
    except Exception as exc:
        return fail(f"the filing sets could not be read: {exc}")
    if filers.get(periods[0]) != tracker.get("holders_on_record") \
            or filers.get(periods[1]) != tracker.get("prior_holders_on_record"):
        return fail("the recomputed filer counts disagree with the "
                    "published tracker record; refusing to publish")
    panel_covered = [s for s in panel if s != "SPY"
                     and holders.get(s, {}).get("has_record")]
    sponsorship = {}
    for sym in panel:
        h = holders.get(sym)
        sponsorship[sym] = bool(
            (h and h["not_falling"]) or sym in any_buy)
    filings = {"periods": periods,
               "filers_current": filers.get(periods[0]),
               "filers_prior": filers.get(periods[1]),
               "mapped_identifiers": len(holders),
               "panel_names_with_holder_record": len(panel_covered),
               "not_falling_among_mapped": sum(
                   1 for h in holders.values() if h["not_falling"])}

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

    # ---- Labelled history: every settled fear day, never recorded ----
    history = []
    for entry in fear_entries:
        day = entry["date"]
        cohort = form_cohort(panel, spy_maps, sponsorship, day)
        n, mean, ungr = mean_excess(panel, spy, cohort["composite"], day)
        history.append({
            "date": day,
            "qualified_by": entry["qualified_by"],
            "spy_change_pct": entry["spy_change_pct"],
            "gate": (None if cohort["gate"] is None
                     else cohort["gate"]["pass"]),
            "gate_close": (None if cohort["gate"] is None
                           else cohort["gate"]["close"]),
            "gate_mean_200": (None if cohort["gate"] is None
                              else cohort["gate"]["mean_200"]),
            "pool_count": cohort["pool_count"],
            "composite_count": len(cohort["composite"]),
            "composite_names": cohort["composite"],
            "sponsored_count": len(cohort["sponsored"]),
            "sponsored_names": cohort["sponsored"],
            "composite_graded_names": n,
            "composite_mean_excess_points": (
                round(mean, 2) if (mean is not None and n >= THIN)
                else None),
            "ungradeable": (n == 0 and len(cohort["composite"]) > 0),
        })
    hist_totals = {
        "pool_name_days": sum(h["pool_count"] for h in history),
        "composite_name_days": sum(h["composite_count"] for h in history),
        "days_with_pool": sum(1 for h in history if h["pool_count"] > 0),
        "max_sponsored_names": max(h["sponsored_count"] for h in history),
    }

    # ---- Live: only the freshest session can start a group ----
    freshest = panel_as_of
    created = 0
    freshest_note = None
    if freshest in fear_days and freshest >= SHIP_DATE:
        cohort = form_cohort(panel, spy_maps, sponsorship, freshest)
        if cohort["gate"] is not None and cohort["gate"]["pass"] \
                and cohort["sponsored"]:
            created = ledger_cohort(led, panel, filings, insider, cohort)
        elif cohort["gate"] is None or not cohort["gate"]["pass"]:
            freshest_note = ("The freshest session was a fear day, "
                             "but the market gate did not pass, so "
                             "the forecast did not fire and nothing "
                             "was recorded.")
        else:
            freshest_note = ("The freshest session was a fear day and "
                             "the market gate passed, but no washed-out "
                             "name showed backing on record, so no "
                             "group started and nothing was recorded.")
    missed = [d for d in fear_days if SHIP_DATE <= d < freshest]
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
        if spy_dates.index(day) + 20 >= len(spy_dates):
            continue
        n, mean, ungr = mean_excess(panel, spy,
                                    outcome.get("members") or [], day)
        if n == 0:
            continue
        estimate = (row.get("value") or {}).get("estimate")
        led.append_grade(forecast_row=row, grade={
            "scores": {"abs_error": round(abs(estimate - mean), 4)},
            "mean_excess_points": round(mean, 4), "graded_names": n,
            "ungradeable_names": ungr, "thin": n < THIN,
            "rule": ("average gain over SPY across the arm's graded "
                     "names over the 20 sessions after the fear day")},
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
    # Wait text (cure SPONSORED-WAIT-STATE-20261031): the pre-fire
    # template may render only while no cohort has formed. Once a
    # cohort forms the same field names the formed cohort instead,
    # so the wait text and the live counts can never claim
    # opposite states on the same page.
    formed_cohorts = {}
    for r in rows:
        if r.get("type") == "forecast" \
                and r.get("engine_id") == ENGINE_ID:
            cohort = (r.get("lineage") or {}).get("cohort") or {}
            day = cohort.get("fear_day")
            if day and cohort.get("arm") == "sponsored":
                formed_cohorts[day] = list(cohort.get("members")
                                            or [])
    if cohorts_formed and formed_cohorts:
        first_day = sorted(formed_cohorts)[0]
        first_names = ", ".join(formed_cohorts[first_day])
        wait_text = (
            f"The first group started on {first_day}: the backed "
            f"group holds {first_names}, written to the public "
            "record at that close, before its 20 trading days "
            "began. Later fear days on which the market gate "
            "passes and at least one washed-out top scorer shows "
            "backing on record add further groups the same way. "
            "Fear days are rare, so this record builds slowly, in "
            "quarters rather than weeks. It also needs the price "
            "record and the fear-gauge readings to keep accruing "
            f"past their current ends ({panel_as_of} for prices).")
    elif cohorts_formed:
        wait_text = (
            f"{cohorts_formed} group has started. Later fear days "
            "on which the market gate passes and at least one "
            "washed-out top scorer shows backing on record add "
            "further groups, written to the public record at the "
            "close, before the 20 trading days begin.")
    else:
        wait_text = (
            "No group has started yet. The live record "
            "begins with the first fear day after "
            f"{SHIP_DATE} on which the market gate passes "
            "and at least one washed-out top scorer shows "
            "backing on record: that day, all three groups "
            "are written to the public record at the close, "
            "before the 20 trading days begin. Fear days "
            "are rare, so this record builds slowly, in "
            "quarters rather than weeks. It also needs the "
            "price record and the fear-gauge readings to "
            "keep accruing past their current ends "
            f"({panel_as_of} for prices).")
    retired = False
    kill_margin = None
    if cohorts_matured >= PROVING_COHORTS and "sponsored" in arm_means \
            and "composite_plus_gate" in arm_means:
        s_mean = sum(g["mean_excess_points"] for g in arm_means["sponsored"]
                     ) / len(arm_means["sponsored"])
        g_mean = sum(g["mean_excess_points"]
                     for g in arm_means["composite_plus_gate"]
                     ) / len(arm_means["composite_plus_gate"])
        kill_margin = round(s_mean - g_mean, 4)
        retired = kill_margin < KILL_MARGIN_POINTS

    data = {
        "tool": "Sponsored Reset",
        "state": "proving",
        "retired": retired,
        "as_of": panel_as_of,
        "price_history": {"from": spy_dates[0], "to": panel_as_of,
                          "sessions": len(spy_dates),
                          "names": len(panel)},
        "source": ("The daily price history on record (1,833 names, "
                   f"{spy_dates[0]} to {panel_as_of}), the settled "
                   "fear-day record, the big-holder filings for the "
                   f"periods ended {periods[1]} and {periods[0]}, and "
                   f"the insider record gathered {insider.get('as_of')}."),
        "idea": ("Some washed-out stocks are being held through the "
                 "washout by the big holders and insiders who know "
                 "them best. Others have been abandoned by those same "
                 "people, and their falls tend to continue. From the "
                 "outside the two look identical: both are far below "
                 "their highs, sitting near their lows, after a fear "
                 "day. This page tests whether the public filings "
                 "tell the held ones from the abandoned ones before "
                 "the next 20 trading days, not after."),
        "claim": {
            "words": ("On a fear day when the wider market is above "
                      "its rising 200-day average, washed-out stocks "
                      "that score at the top of the combined score "
                      "and show backing on record will beat the "
                      "market by at least +2.0 points on average over "
                      "the next 20 trading days."),
            "stated_points": STATED_POINTS,
            "points_explained": ("Points are percentage points of "
                                 "gain over the market: a stock up 5 "
                                 "percent while the market is up 2 "
                                 "percent scores +3 points."),
        },
        "arms": [
            {"name": "Backed",
             "words": ("The full test: washed-out, top of the "
                       "combined score, the market gate passing, and "
                       "backing on record (big holders not leaving, "
                       "or an insider buy). This arm must average at "
                       "least +2.0 points over the market.")},
            {"name": "Score alone",
             "words": ("The same washed-out top scorers with no "
                       "other condition. This is the parent survivor "
                       "on its own, recorded so the two added "
                       "conditions can be priced separately.")},
            {"name": "Score plus the market gate",
             "words": ("The same top scorers, only on fear days when "
                       "the market gate passes, with no filings "
                       "condition. The verdict compares the backed "
                       "arm against this one: whatever the backed arm "
                       "adds over it is what the filings are worth.")},
        ],
        "parent_record": {
            "label": "The parent survivor's own record",
            "words": ("The combined score comes from a study of "
                      "washed-out stocks on fear days. On its own "
                      "fear cut (days the market fell at least 1 "
                      "percent, or sat under its 50-day average) and "
                      "its own way of measuring what came next, it "
                      "showed a link of +0.053 in its discovery years "
                      "and +0.028 in its holdout years, and the "
                      "holdout confirmed it: the strongest grade this "
                      "record gives a directional finding of its "
                      "kind, one step below the top grade. Its "
                      "rising-trend version faded in the holdout and "
                      "is not used here. Those figures belong to the "
                      "study, on its own definitions: they are the "
                      "reason this test exists, never figures this "
                      "page claims."),
            "discovery": 0.053, "holdout": 0.028,
        },
        "definitions": {
            "fear_day": ("A day when SPY fell more than 1.5 percent, "
                         "or the fear gauge rose more than 15 "
                         "percent in a day, closed at 25 or higher, "
                         "or closed at 20 or higher on a day when SPY "
                         "or QQQ fell. This is the Fear Day List's own "
                         "settled definition, reused exactly; run "
                         "over the price history here it finds 22 "
                         "days, all before this page existed."),
            "washed_out": ("The close is at or below 65 percent of "
                           "the highest high of the last 252 trading "
                           "days, and at or below 110 percent of the "
                           "lowest low of the same stretch: at least "
                           "35 percent off the high and sitting near "
                           "the low. One honest difference from this "
                           "page's original written design, which "
                           "said 35 to 80 percent off the high: the "
                           "study's own coded rule carries no 80 "
                           "percent floor, so a stock more than 80 "
                           "percent off its high still counts when "
                           "it sits near its low. This page follows "
                           "the parent code exactly and prints the "
                           "difference rather than quietly adding a "
                           "floor. The stock must also be liquid: "
                           "closing above 5 dollars with more than 5 "
                           "million dollars a day changing hands over "
                           "the last 20 days, and it needs a long "
                           "enough record (at least 320 days on file, "
                           "and only its days from number 260 onward "
                           "count). The deep history the study ran "
                           "on, thousands of names including ones "
                           "that later closed, is not on record here: "
                           "the price history here holds 1,833 names "
                           "still trading, at most 399 days each, so "
                           "no fear day before June 5, 2026 can form "
                           "a pool at all. That is a limit of the "
                           "record, stated, not a market fact."),
            "combined_score": ("Two readings per stock per day, "
                               "combined the study's own coded way. "
                               "Laggard strength: how far the stock's "
                               "last 10 days trail the market's 10 "
                               "days (trailing more scores higher). "
                               "Down-volume capitulation: the share "
                               "volume on falling days over the last "
                               "10 days against its own recent "
                               "per-10-day average (running hot "
                               "scores higher). Each reading is "
                               "ranked across that day's washed-out "
                               "stocks, the two signed ranks are "
                               "averaged, and the top fifth of the "
                               "day matches. Days with fewer than 10 "
                               "scored stocks form no matching group."),
            "gate": ("The market gate: SPY's close is above its "
                     "200-day average close, and that average is "
                     "higher than it was 20 days earlier. It cannot "
                     "be read at all until 220 days of market "
                     "history exist, which covers the first 12 fear "
                     "days on record here."),
            "sponsorship": {
                "words": ("Backing on record, either leg enough. "
                          "Big holders: the number of filing "
                          "managers holding the stock in the newer "
                          "quarter is at least the number in the "
                          "older quarter. Insider buy: the stock's "
                          "insider summary shows at least one "
                          "open-market buy. A stock with no record "
                          "on either leg never counts as backed."),
                "periods": periods,
                "filers_current": filings["filers_current"],
                "filers_prior": filings["filers_prior"],
                "panel_names_with_holder_record":
                    filings["panel_names_with_holder_record"],
                "panel_names_total": len(panel) - 1,
                "any_buy_names": any_buy,
                "insider_gathered": insider.get("as_of"),
                "insider_window_start": insider.get("window_start"),
                "limits": ("The big-holder reading covers only "
                           f"{filings['panel_names_with_holder_record']} "
                           f"of the {len(panel) - 1:,} stocks in the price "
                           "history: the rest have no identifier "
                           "match on record, so they can only be "
                           "backed through the insider leg, which "
                           "itself covers 50 tracked names. The "
                           "filings are one snapshot of two quarters "
                           "(periods ended March 31 and June 30, "
                           "2026, filed weeks later), so applied to "
                           "a past fear day they are not what was "
                           "known that day, and the history below "
                           "says so. Insider summaries carry counts "
                           "and dollar totals only, never who "
                           "traded or on which day, so several "
                           "insiders buying close together (what "
                           "traders call cluster buying) cannot "
                           "be identified from them: this page uses "
                           "the simple any-buy reading and claims "
                           "nothing finer.")},
        },
        "history": {
            "label": "History, worked in full, never recorded",
            "words": ("Every fear day on record, worked through "
                      "the full pipeline with today's filings "
                      "snapshot. Because the price history here is "
                      "shorter than the study's, no fear day before "
                      "June 5, 2026 forms a pool. Every backed group "
                      "in this history holds at most 4 stocks, far "
                      "under the 30 needed before an average means "
                      "anything, so history is published as counts "
                      "only: it shows the shape of the wait, not a "
                      "verdict. None of it is in the live record "
                      "and none ever will be backfilled."),
            "days": history,
            "totals": hist_totals,
        },
        "live": {
            "cohorts_formed": cohorts_formed,
            "cohorts_matured": cohorts_matured,
            "records_written": mine["forecasts"],
            "records_graded": mine["graded"],
            "proving_target_cohorts": PROVING_COHORTS,
            "missed_fear_days": missed,
            "freshest_session": freshest,
            "freshest_note": freshest_note,
            "arm_means": {arm: [{"mean_excess_points":
                                 g["mean_excess_points"],
                                 "graded_names": g["graded_names"],
                                 "thin": g["thin"]} for g in gs]
                          for arm, gs in arm_means.items()},
            "kill_margin_points": kill_margin,
            "wait": wait_text},
        "self_test": test,
        "kill_criterion": ("After 3 fear-day groups have matured, "
                           "if the filings condition adds less than "
                           "half a point of average gain over the "
                           "market, compared with the same top "
                           "scorers under the market gate alone, "
                           "this tool retires. The filings are the "
                           "only new idea here; if they do not earn "
                           "their place, the page goes."),
        "thin_cell_rule": ("Any group with fewer than 30 graded "
                           "stocks shows its count only, with no "
                           "average headline."),
    }
    # Session keeping (2026-10-31, Wave 3 Item F): from this run
    # forward, each refresh appends a dated snapshot of the
    # charted subject values (the qualifying days on record and
    # SPY's move on each) to the page's session-history store and
    # carries the kept list on the page data, so the record's
    # accrual is provable run by run. The history record itself
    # is unchanged; nothing is backfilled.
    if _sh is not None:
        data["session_history"] = _sh.append_session(
            HISTORY_PATH, freshest,
            {"days": [{"date": day["date"],
                        "spy_change_pct": day["spy_change_pct"]}
                       for day in history]})

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH}: fear days {len(fear_days)}, history "
          f"pool name-days {hist_totals['pool_name_days']}, live "
          f"cohorts {cohorts_formed}, records {mine['forecasts']} "
          f"({created} new), graded {mine['graded']} "
          f"({graded_now} new), self-test {test['state']}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
