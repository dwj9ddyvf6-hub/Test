#!/usr/bin/env python3
"""Refresh the Silent Accumulation engine (Forecast Engine 26).

=====================================================================
CANDIDATE-REGISTER TRIPLE (written before any computation, per the
lineup's adopted standards)

1. EVIDENCE CLASS
   None of the three parents carries a forward grade as a
   forecaster anywhere in the record. The combined off-exchange
   reading has been graded as a measurement (it matched the
   source file at 0.4365 across 501 of 503 index stocks on its
   recorded day), never as a predictor of what a stock does
   next. Insider summaries and quarterly holder changes are
   both listed in the record as untested. So the honest prior
   is weak, stated in advance: this engine survives on the
   novelty of requiring three independent kinds of evidence
   to agree, one of them an absence, and on the sharpness of
   its test, not on any parent's track record. This engine's
   own live record: none. It ships with zero groups, because
   one of its three legs has no stored record at all today
   (see the dark leg below), and it says so rather than
   substituting a different reading.

2. RECONSTRUCTION CHOICES (every constant, named before computing)
   - Universe: the 50 tracked names of the insider record. It
     is the only universe where the insider leg exists, so it
     is the only universe this engine can ever form a group in
     until that record grows. Nothing is extrapolated to other
     names.
   - The dark leg (off-exchange pressure): the reading the
     design names is a per-stock one: the share of a stock's
     off-exchange trading that was sold short, from the daily
     off-exchange file, ranked across stocks. THE NAMED GAP:
     that per-stock record does not exist as stored data
     today. The combined index reading is built each day from
     per-stock values worked out for the day and then not
     kept, and the per-stock collection has never started: the
     published dark record states 0 stocks and 0 sessions on
     record, in those words. The combined index reading and
     the three index funds' own ratios are different measures
     and are NEVER substituted for a per-stock reading. So
     today the top-fifth cut below is undefined (not zero, not
     failed by any name), no dark group can form, and the
     three-way group cannot form. The machinery below is
     complete: the first day the dark record stores per-stock
     readings, the same code takes the cut from them.
   - The dark cut, when readings exist: among the tracked
     names carrying a stored reading for the same session,
     rank the short share; the top fifth is the first
     ceil(count / 5) names. The session used is the freshest
     session in the dark record.
   - The insider leg (the absence): a name passes when its
     insider summary on record shows zero open-market sells.
     The window is the record's own: filings filed in the six
     months before the gathering date (2026-04-26 to
     2026-10-26), up to the 20 most recent filings per name.
     The summaries carry counts and dollar totals only, never
     who traded or on which day. A name with NO summary (7 of
     the 50 could not be matched to a company record) is never
     read as zero sells: no record is not the absence signal.
     Plain-words narrowing, printed on the page: of the 7
     names passing today, 6 also show zero open-market buys,
     so for them the reading is complete open-market silence,
     not buying; only one name pairs zero sells with an actual
     buy.
   - The big-holder leg: between the two quarters on record
     (periods ended 2026-03-31, 8,871 holders filed, and
     2026-06-30, 8,857 filed), a name passes when its holder
     count rose OR its aggregate reported shares rose. The
     reading is recomputed here from the two stored filing
     sets with the desk's own aggregation code (share rows
     only; a name resolving to more than one share-class
     identifier is dropped entirely, never guessed; holder
     count = the number of distinct filings naming the stock;
     aggregate position = the summed reported shares). The
     name matching is the recorded route: company names from
     the sector record and the regulator's company list,
     normalised the desk's own way. A name must resolve in
     BOTH quarters to be judged at all: resolving in only one,
     or in neither, is a matching failure, never a zero and
     never a fall. Exactly one observation per name exists
     today, because exactly two quarters are on record; the
     engine sharpens only as quarters accrue.
   - Group cadence: a group forms at each quarterly holdings
     publication plus the weekly dark refresh. In this code
     that means: a group can be recorded only on a run where
     the dark record carries stored per-stock readings for a
     session on or after this page's ship date, all three legs
     can be read, and that session has not already been
     recorded. A dark session that passes unrecorded is
     counted as missed and is NEVER backfilled.
   - Counting toward the verdict: the kill threshold counts
     group names as recorded, so a name recorded in two
     separate groups counts twice, because each recording is
     a separate 21-trading-day forecast. This is fixed here,
     before any group exists, not decided at grading time.
   - Ledger shape: per group day, FIVE records written the
     same day through the shared record's own append call:
     the three-way group, and each single condition alone
     (dark only, insider only, big holders only), each with
     quantity cohort_21_session_spy_excess_distribution and
     the same stated claim (middle gain over the market above
     zero; share reaching the top quarter at least 30 percent
     against the 25 percent plain rate), so all grade on one
     scale. The all-names comparison is not a record: it is
     the grading yardstick, computed at grading time from the
     same day's full price record. Horizon: opens the session
     after the group day, closes the 21st session after it,
     counted on SPY's session calendar. Families: the dark leg
     is options prints family as registered; the insider and
     big-holder legs are both company filings, one family
     counted once between them in any combined use.
   - Grading: when the price history covers a recorded
     group's full 21 sessions, each name's gain over the
     market is 100 times its 21-session return minus SPY's
     over the same sessions (close at the group day to the
     close 21 of its own sessions later; SPY on its own
     calendar). The group's middle and its top-quarter share
     (the share of its names reaching at least the 75th
     percentile of that same day's all-names gains, the
     all-names group being every price-record name except SPY
     with a computable 21-session gain that day, its count
     stated) are graded against the stated claim through the
     shared record's own grade call. The shared grading runner
     cannot yet resolve this kind of outcome (a group
     distribution), so grades are appended by this engine
     through the machinery's grade call, never by forking the
     runner. Names whose 21 sessions are not in the record
     are counted ungradeable, never dropped silently.
   - Thin-cell rule: any group with fewer than 30 graded
     names shows its count only, no middle and no share
     headline, on the page and in the verdict alike.
   - Kill criterion, in plain words, printed in advance:
     after 100 group names have been recorded and graded, if
     the three-way group adds less than 2 points (of
     top-quarter share) over the best single condition alone,
     this engine retires.
   - Ship date: this engine first published on 2026-10-29.
     Anything before that date is history, never recorded.

3. NON-CLAIMS
   - The combined off-exchange reading and the index funds'
     own ratios published on the dark page are shown here only
     as context for what the dark record holds; they are not
     this engine's reading for any stock, and no stock is ever
     assigned one of them.
   - The two names that pass both the insider leg and the
     big-holder leg today are candidates waiting on the dark
     leg, not a group, not a forecast, and they are never
     recorded until a stored per-stock dark reading exists.
   - Nothing from any history computation or self-test is
     ever written to the live record. Only a real group,
     formed on a stored dark session on or after the ship
     date with all three legs readable, is recorded there,
     through the machinery's own append call.

=====================================================================
Behaviour: read the price history, the insider record, the dark
record, the published big-holder tracker record and the two
stored filing sets (fails closed on any disagreement between
them, or with the shared record), run the self-test, recompute
the three legs and every group they form today, record a group
only when a stored per-stock dark session on or after the ship
date makes one possible, grade any matured recorded group, then
write data.json with the live figures recomputed from the shared
record alone. Idempotent: rerunning with the same sources
records nothing new and rewrites the same data.json.
Timestamps come from the sources, never the clock.
"""

import datetime
import io
import json
import math
import os
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(HERE)
PANEL_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")
INSIDER_PATH = os.path.join(HERE, "insider-wire", "data.json")
DARK_PATH = os.path.join(HERE, "dark-prints", "data.json")
TRACKER_PATH = os.path.join(HERE, "13f-tracker", "data.json")
F13_DIR = os.path.expanduser("~/workspace/morgue/data_cache/13f")
GICS_PATH = os.path.expanduser(
    "~/workspace/femto-lean/config/gics_sectors.json")
TICKERS_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/edgar/company_tickers.json")
MORGUE = os.path.expanduser("~/workspace/morgue")
OUT_PATH = os.path.join(HERE, "silent-accumulation", "data.json")
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
sys.path.insert(0, MORGUE)
from forecast import ledger as ledger_mod  # noqa: E402
from forecast import registry as registry_mod  # noqa: E402
import inst_13f  # noqa: E402  (the desk's own 13F aggregation code)
import inst_edgar  # noqa: E402

ENGINE_ID = "engine_26"
SHIP_DATE = "2026-10-29"
THIN = 30
PROVING_NAMES = 100
KILL_MARGIN_POINTS = 2.0
TOP_QUARTER_CLAIM_PCT = 30.0
BASELINE_TOP_QUARTER_PCT = 25.0


def fail(msg):
    print(f"Silent Accumulation refresh: {msg}", file=sys.stderr)
    return 1


# ---- the three legs -----------------------------------------------------------
def dark_top_fifth(readings):
    """readings: {symbol: short share} for one session. Returns
    (cut size, top-fifth symbols)."""
    ranked = sorted(readings, key=lambda s: (-readings[s], s))
    k = math.ceil(len(ranked) / 5) if ranked else 0
    return k, ranked[:k]


def zero_sell_names(insider_names):
    """Names whose insider summary shows zero open-market sells.
    A name with no summary never passes."""
    out = []
    for n in insider_names:
        s = n.get("summary")
        if s and s["sells"]["count"] == 0:
            out.append(n["symbol"])
    return sorted(out)


def rise_reading(cur, pri):
    """cur/pri: {symbol: {shares, filer_count}} for the newer and
    older quarters. A name is judged only when it resolves in
    both. Returns {symbol: {count_rose, shares_rose, rose}}."""
    out = {}
    for sym in sorted(set(cur) & set(pri)):
        c, p = cur[sym], pri[sym]
        out[sym] = {
            "holders_current": c["filer_count"],
            "holders_prior": p["filer_count"],
            "shares_current": c["shares"],
            "shares_prior": p["shares"],
            "count_rose": c["filer_count"] > p["filer_count"],
            "shares_rose": c["shares"] > p["shares"],
            "rose": (c["filer_count"] > p["filer_count"]
                     or c["shares"] > p["shares"]),
        }
    return out


def form_groups(dark_set, insider_set, rise_set):
    """Every group the three legs form, from plain sets."""
    dark_set, insider_set, rise_set = (set(dark_set), set(insider_set),
                                       set(rise_set))
    return {
        "interaction": sorted(dark_set & insider_set & rise_set),
        "dark_only": sorted(dark_set),
        "insider_only": sorted(insider_set),
        "filings_only": sorted(rise_set),
        "insider_and_filings": sorted(insider_set & rise_set),
    }


# ---- distribution grading -------------------------------------------------------
def excess_21(panel, spy, members, day):
    """Per-name 21-session gain over SPY in points, for the
    members with a computable figure. Returns (values dict,
    ungradeable count)."""
    spy_dates = [r[0] for r in spy]
    if day not in spy_dates:
        return {}, len(members)
    si = spy_dates.index(day)
    if si + 21 >= len(spy_dates):
        return {}, len(members)
    spy_ret = float(spy[si + 21][4]) / float(spy[si][4]) - 1.0
    vals, ungr = {}, 0
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
        if j + 21 >= len(rows):
            ungr += 1
            continue
        vals[sym] = 100.0 * ((float(rows[j + 21][4]) / float(rows[j][4])
                              - 1.0) - spy_ret)
    return vals, ungr


def percentile(sorted_vals, q):
    if not sorted_vals:
        return None
    pos = q * (len(sorted_vals) - 1)
    base = int(pos)
    frac = pos - base
    if base + 1 >= len(sorted_vals):
        return sorted_vals[-1]
    return sorted_vals[base] + frac * (sorted_vals[base + 1]
                                       - sorted_vals[base])


def distribution_figures(panel, spy, members, day):
    """The group's middle and top-quarter share against the same
    day's all-names yardstick."""
    all_members = [s for s in panel if s != "SPY"]
    all_vals, _ = excess_21(panel, spy, all_members, day)
    vals, ungr = excess_21(panel, spy, members, day)
    if not vals or not all_vals:
        return {"graded_names": len(vals), "ungradeable": ungr,
                "all_names_count": len(all_vals), "median": None,
                "top_quartile_share_pct": None}
    yard = sorted(all_vals.values())
    cut = percentile(yard, 0.75)
    got = sorted(vals.values())
    median = percentile(got, 0.5)
    share = 100.0 * sum(1 for v in got if v >= cut) / len(got)
    return {"graded_names": len(vals), "ungradeable": ungr,
            "all_names_count": len(all_vals),
            "median": round(median, 4),
            "top_quartile_share_pct": round(share, 4),
            "all_names_median": round(percentile(yard, 0.5), 4)}


# ---- 13F recompute ---------------------------------------------------------------
def load_filings(tracked):
    """Recompute per-name aggregate shares and holder counts for
    the two quarters on record, over the tracked names only,
    through the desk's own aggregation code and its recorded
    name-matching route. Also count the filers per period from
    the filing sets' submission files, the newest filing per
    manager winning, for the cross-check against the tracker."""
    gics = json.load(open(GICS_PATH, encoding="utf-8"))["symbols"]
    cik_map = inst_edgar.ticker_map(
        json.load(open(TICKERS_PATH, encoding="utf-8")))
    wanted = {}
    for sym in tracked:
        g = gics.get(sym) or {}
        if g.get("security"):
            wanted.setdefault(
                inst_13f.normalize_name(g["security"]), sym)
        hit = cik_map.get(sym)
        if hit and hit[1]:
            wanted.setdefault(inst_13f.normalize_name(hit[1]), sym)
    wanted = {k: v for k, v in wanted.items() if v in tracked}
    zips = sorted(n for n in os.listdir(F13_DIR)
                  if n.endswith("_form13f.zip"))
    if len(zips) != 2:
        raise RuntimeError(f"expected exactly two filing sets on "
                           f"record, found {len(zips)}")
    by_period = {}
    filers = {}
    best_all = {}
    for name in zips:
        path = os.path.join(F13_DIR, name)
        cmap, agg = inst_13f.aggregate_13f_zip(path, wanted)
        by_period[name] = {cmap[c]: a for c, a in agg.items()}
        best = {}
        with zipfile.ZipFile(path) as zf:
            member = next((n for n in zf.namelist()
                           if n.upper().endswith("SUBMISSION.TSV")),
                          None)
            with zf.open(member) as fh:
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
                    period = datetime.datetime.strptime(
                        p[col["PERIODOFREPORT"]].strip(),
                        "%d-%b-%Y").date().isoformat()
                    filed = datetime.datetime.strptime(
                        p[col["FILING_DATE"]].strip(),
                        "%d-%b-%Y").date().isoformat()
                    key = (p[col["CIK"]], period)
                    rank = (filed, 1 if p[col["SUBMISSIONTYPE"]]
                            .endswith("/A") else 0)
                    if key not in best or rank > best[key][0]:
                        best[key] = (rank, period)
                    if key not in best_all or rank > best_all[key][0]:
                        best_all[key] = (rank, period)
        counts = {}
        for _key, (_rank, period) in best.items():
            counts[period] = counts.get(period, 0) + 1
        filers[name] = counts
    combined = {}
    for _key, (_rank, period) in best_all.items():
        combined[period] = combined.get(period, 0) + 1
    filers["combined"] = combined
    return by_period, filers, zips


# ---- self-test ---------------------------------------------------------------------
def self_test(panel):
    """Prove the three legs, the group formation, the
    distribution grading and the five-record group recording on
    hand-built cases with known answers and a throwaway copy of
    the record. Raises on any disagreement."""
    # Dark cut on known readings: 10 names, top fifth = 2.
    readings = {f"N{k}": 0.10 * k for k in range(10)}
    k, top = dark_top_fifth(readings)
    if k != 2 or top != ["N9", "N8"]:
        raise RuntimeError(f"dark cut gave {(k, top)}, expected "
                           f"(2, ['N9', 'N8'])")
    if dark_top_fifth({}) != (0, []):
        raise RuntimeError("an empty dark record formed a cut")
    # Insider leg: zero sells passes, sells fail, and a name with
    # no summary never passes.
    fake = [{"symbol": "AAA", "summary": {"sells": {"count": 0}}},
            {"symbol": "BBB", "summary": {"sells": {"count": 3}}},
            {"symbol": "CCC", "summary": None},
            {"symbol": "DDD"}]
    if zero_sell_names(fake) != ["AAA"]:
        raise RuntimeError("the zero-sell reading is wrong on the "
                           "known summaries")
    # Big-holder leg: count-only rise and shares-only rise pass;
    # both falling fails; one-quarter resolution is unjudged.
    cur = {"AAA": {"shares": 100.0, "filer_count": 5},
           "BBB": {"shares": 90.0, "filer_count": 7},
           "CCC": {"shares": 80.0, "filer_count": 3},
           "DDD": {"shares": 50.0, "filer_count": 2}}
    pri = {"AAA": {"shares": 90.0, "filer_count": 5},
           "BBB": {"shares": 100.0, "filer_count": 6},
           "CCC": {"shares": 100.0, "filer_count": 4}}
    rise = rise_reading(cur, pri)
    if set(rise) != {"AAA", "BBB", "CCC"}:
        raise RuntimeError("a one-quarter name was judged")
    if not (rise["AAA"]["rose"] and rise["AAA"]["shares_rose"]
            and not rise["AAA"]["count_rose"]):
        raise RuntimeError("the shares-only rise was misread")
    if not (rise["BBB"]["rose"] and rise["BBB"]["count_rose"]
            and not rise["BBB"]["shares_rose"]):
        raise RuntimeError("the count-only rise was misread")
    if rise["CCC"]["rose"]:
        raise RuntimeError("a name falling on both readings passed")
    # Group formation on known sets.
    groups = form_groups({"A", "B", "C"}, {"B", "C", "D"},
                         {"C", "D", "E"})
    if groups["interaction"] != ["C"] \
            or groups["insider_and_filings"] != ["C", "D"]:
        raise RuntimeError(f"group formation gave {groups}")
    # Distribution grading on known prices: the member doubles
    # SPY's move; the yardstick's top-quarter cut is known.
    def rows(base, step, n=30):
        return [[f"2026-02-{k + 1:02d}", base + step * k,
                 base + step * k, base + step * k, base + step * k,
                 1.0] for k in range(n)]
    fake_panel = {"SPY": rows(100.0, 1.0)}
    for k in range(4):
        fake_panel[f"M{k}"] = rows(100.0, 1.0 + k)
    figs = distribution_figures(fake_panel, fake_panel["SPY"],
                                ["M3"], "2026-02-01")
    want_median = 100.0 * ((184.0 / 100.0 - 1.0)
                           - (121.0 / 100.0 - 1.0))
    if figs["graded_names"] != 1 or figs["all_names_count"] != 4 \
            or abs(figs["median"] - round(want_median, 4)) > 1e-9 \
            or figs["top_quartile_share_pct"] != 100.0:
        raise RuntimeError(f"distribution grading gave {figs}, "
                           f"expected median {want_median} and a "
                           f"100 percent top-quarter share")
    # Five-record group recording on a throwaway copy.
    reg = registry_mod.load()
    with tempfile.TemporaryDirectory() as td:
        scratch = ledger_mod.Ledger(os.path.join(td, "ledger.jsonl"),
                                    registry=reg)
        scratch.append_genesis("silent accumulation self-test")
        lineage = {"source_artifacts": [
                       {"path": "synthetic (self-test, not a record)",
                        "sha256": ledger_mod.file_sha256(PANEL_PATH)}],
                   "clocks": {c: "2026-10-29"
                              for c in ledger_mod.CLOCK_FIELDS},
                   "note": "Self-test only; never the live record."}
        made = 0
        for arm, fams in (
                ("interaction", ["options_prints",
                                 "filings_positioning"]),
                ("dark_only", ["options_prints"]),
                ("insider_only", ["filings_positioning"]),
                ("filings_only", ["filings_positioning"])):
            _row, created = scratch.append_forecast_declared(
                engine_id=ENGINE_ID, issued_ts="2026-10-29",
                subject="2026-10-29 dark session cohort: " + arm,
                quantity="cohort_21_session_spy_excess_distribution",
                value={"median_claim": "above_zero",
                       "median_boundary_points": 0.0,
                       "top_quartile_share_claim_pct":
                           TOP_QUARTER_CLAIM_PCT,
                       "baseline_top_quartile_share_pct":
                           BASELINE_TOP_QUARTER_PCT,
                       "members": ["AAA"]},
                horizon_open="2026-10-30",
                horizon_close="2026-11-27",
                lineage=lineage, families=fams,
                outcome={"kind":
                         "cohort_distribution_spy_excess_21_sessions",
                         "arm": arm, "members": ["AAA"],
                         "cohort_date": "2026-10-29"})
            made += 1 if created else 0
        figs2 = ledger_mod.recompute_figures(scratch.rows())
        if not scratch.verify_chain() or made != 4 \
                or figs2[ENGINE_ID]["forecasts"] != 4:
            raise RuntimeError("throwaway group recording failed")
    return {"state": "passed", "feature_cases_checked": 6,
            "ledger_arms_checked": 4}


# ---- live ledgering ------------------------------------------------------------------
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


def ledger_cohort(led, panel, cohort_date, groups, lineage_files,
                  clocks_day):
    spy_dates = [r[0] for r in panel["SPY"]]
    horizon_open = session_after(spy_dates, cohort_date, 1)
    horizon_close = session_after(spy_dates, cohort_date, 21)
    arms = (
        ("interaction", groups["interaction"],
         ["options_prints", "filings_positioning"]),
        ("dark_only", groups["dark_only"], ["options_prints"]),
        ("insider_only", groups["insider_only"],
         ["filings_positioning"]),
        ("filings_only", groups["filings_only"],
         ["filings_positioning"]),
    )
    created = 0
    for arm, members, fams in arms:
        lineage = {
            "source_artifacts": [
                {"path": p, "sha256": ledger_mod.file_sha256(p)}
                for p in lineage_files],
            "clocks": {c: clocks_day for c in ledger_mod.CLOCK_FIELDS},
            "cohort": {
                "cohort_date": cohort_date, "arm": arm,
                "members": list(members),
                "note": ("Group recorded on its day, before the 21 "
                         "trading days begin; graded as a "
                         "distribution against the same day's "
                         "all-names yardstick and against each "
                         "single condition alone.")},
        }
        _row, was = led.append_forecast_declared(
            engine_id=ENGINE_ID, issued_ts=cohort_date,
            subject=f"{cohort_date} dark session cohort: {arm}",
            quantity="cohort_21_session_spy_excess_distribution",
            value={"median_claim": "above_zero",
                   "median_boundary_points": 0.0,
                   "top_quartile_share_claim_pct":
                       TOP_QUARTER_CLAIM_PCT,
                   "baseline_top_quartile_share_pct":
                       BASELINE_TOP_QUARTER_PCT,
                   "members": list(members)},
            horizon_open=horizon_open, horizon_close=horizon_close,
            lineage=lineage, families=fams,
            outcome={"kind":
                     "cohort_distribution_spy_excess_21_sessions",
                     "arm": arm, "members": list(members),
                     "cohort_date": cohort_date})
        created += 1 if was else 0
    return created


# ---- build -----------------------------------------------------------------------------
def build():
    for path, label in ((PANEL_PATH, "price history"),
                        (INSIDER_PATH, "insider record"),
                        (DARK_PATH, "dark record"),
                        (TRACKER_PATH, "tracker record"),
                        (GICS_PATH, "sector record"),
                        (TICKERS_PATH, "company list")):
        if not os.path.exists(path):
            return fail(f"{label} not found: {path}")
    with open(PANEL_PATH, "r", encoding="utf-8") as fh:
        panel_raw = json.load(fh)
    panel = {sym: sorted(rows, key=lambda r: r[0])
             for sym, rows in panel_raw.items()}
    if "SPY" not in panel:
        return fail("the price history carries no SPY")
    with open(INSIDER_PATH, "r", encoding="utf-8") as fh:
        insider = json.load(fh)
    with open(DARK_PATH, "r", encoding="utf-8") as fh:
        dark = json.load(fh)
    with open(TRACKER_PATH, "r", encoding="utf-8") as fh:
        tracker = json.load(fh)
    spy = panel["SPY"]
    spy_dates = [r[0] for r in spy]
    panel_as_of = spy_dates[-1]

    # ---- Insider record, cross-checked against its own totals ----
    names = insider.get("names") or []
    tracked = [n["symbol"] for n in names]
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
    no_summary = sorted(n["symbol"] for n in names
                        if not n.get("summary"))
    zero_sell = zero_sell_names(names)
    zero_sell_detail = []
    for sym in zero_sell:
        n = next(x for x in names if x["symbol"] == sym)
        zero_sell_detail.append({
            "symbol": sym,
            "buys": n["summary"]["buys"]["count"],
            "buy_value_usd": n["summary"]["buys"]["value_usd"],
            "entries": n["summary"]["all_entries"],
            "open_transactions": n["summary"]["open_transactions"]})
    silent_all = [d["symbol"] for d in zero_sell_detail
                  if d["buys"] == 0]

    # ---- Dark record: per-stock state read exactly as published ----
    per_name = dark.get("per_name") or {}
    dark_names_on_record = per_name.get("names_on_record")
    dark_sessions_on_record = per_name.get("sessions_on_record")
    if dark_names_on_record is None or dark_sessions_on_record is None:
        return fail("the dark record does not state its per-stock "
                    "coverage; refusing to guess at it")
    dark_readings = {}
    dark_session = None
    readings_list = per_name.get("readings") or []
    for r in readings_list:
        if r.get("session") and (dark_session is None
                                 or r["session"] > dark_session):
            dark_session = r["session"]
    for r in readings_list:
        if r.get("session") == dark_session and r.get("symbol") \
                and isinstance(r.get("pct"), (int, float)):
            dark_readings[r["symbol"]] = float(r["pct"]) / 100.0
    dark_gap = not dark_readings
    if dark_gap and dark_names_on_record != 0:
        return fail("the dark record claims per-stock readings but "
                    "carries none this code can read; refusing to "
                    "publish rather than guess at their shape")
    tracked_dark = {s: v for s, v in dark_readings.items()
                    if s in tracked}
    dark_cut_size, dark_top = (dark_top_fifth(tracked_dark)
                               if tracked_dark else (0, []))

    # ---- Big-holder leg, recomputed and cross-checked ----
    periods = [tracker.get("current_period"), tracker.get("prior_period")]
    if not all(periods):
        return fail("the tracker record does not name its two periods")
    try:
        by_zip, filers_by_zip, zip_names = load_filings(tracked)
    except Exception as exc:
        return fail(f"the filing sets could not be read: {exc}")
    # Cross-check: filer counts combined across both filing sets
    # (the newer set also carries late filings for the older
    # period) must match the tracker record exactly. Each set is
    # assigned to the period most of its own filings cover.
    combined = filers_by_zip.get("combined") or {}
    if combined.get(periods[0]) != tracker.get("holders_on_record") \
            or combined.get(periods[1]) != tracker.get(
                "prior_holders_on_record"):
        return fail("the recomputed filer counts disagree with the "
                    "published tracker record; refusing to publish")
    cur_zip = pri_zip = None
    for name in zip_names:
        counts = filers_by_zip[name]
        main_period = max(counts, key=lambda p: counts[p]) \
            if counts else None
        if main_period == periods[0]:
            cur_zip = name
        elif main_period == periods[1]:
            pri_zip = name
    if cur_zip is None or pri_zip is None or cur_zip == pri_zip:
        return fail("the filing sets cannot be assigned to the "
                    "tracker's two periods; refusing to publish")
    cur_by_sym = by_zip[cur_zip]
    pri_by_sym = by_zip[pri_zip]
    rise = rise_reading(cur_by_sym, pri_by_sym)
    rise_names = sorted(s for s, v in rise.items() if v["rose"])
    rise_table = []
    for sym in sorted(rise):
        v = rise[sym]
        rise_table.append({
            "symbol": sym,
            "holders_current": v["holders_current"],
            "holders_prior": v["holders_prior"],
            "shares_current": round(v["shares_current"], 1),
            "shares_prior": round(v["shares_prior"], 1),
            "shares_change_pct": (
                round(100.0 * (v["shares_current"] / v["shares_prior"]
                               - 1.0), 1)
                if v["shares_prior"] else None),
            "count_rose": v["count_rose"],
            "shares_rose": v["shares_rose"], "rose": v["rose"]})

    # ---- Groups the legs form today ----
    groups_today = form_groups(dark_top, zero_sell, rise_names)

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

    # ---- Live: a group forms only on a stored dark session ----
    created = 0
    missed_sessions = []
    recorded_days = {(r.get("lineage") or {}).get("cohort", {})
                     .get("cohort_date")
                     for r in led.rows()
                     if r.get("type") == "forecast"
                     and r.get("engine_id") == ENGINE_ID
                     and (r.get("lineage") or {}).get("cohort")}
    if dark_session and dark_session >= SHIP_DATE and tracked_dark:
        if dark_session not in recorded_days:
            if groups_today["interaction"]:
                created = ledger_cohort(
                    led, panel, dark_session, groups_today,
                    [PANEL_PATH, INSIDER_PATH, DARK_PATH,
                     TRACKER_PATH], dark_session)
                recorded_days.add(dark_session)
            # an empty three-way group starts no records at all;
            # the day is a no-fire day, stated on the page
    elif dark_session and dark_session >= SHIP_DATE:
        missed_sessions.append(dark_session)

    # ---- Grade any recorded group whose 21 sessions have passed ----
    rows = led.rows()
    graded_now = 0
    for row in list(rows):
        if row.get("type") != "forecast" or row.get("engine_id") != ENGINE_ID:
            continue
        if any(g.get("type") == "grade"
               and g.get("forecast_row_id") == row["row_id"] for g in rows):
            continue
        outcome = row.get("outcome") or {}
        day = outcome.get("cohort_date")
        if not day or day not in spy_dates:
            continue
        if spy_dates.index(day) + 21 >= len(spy_dates):
            continue
        figs = distribution_figures(panel, spy,
                                    outcome.get("members") or [], day)
        if figs["graded_names"] == 0:
            continue
        median = figs["median"]
        led.append_grade(forecast_row=row, grade={
            "scores": {"pinball": round(0.5 * abs(median - 0.0), 4)},
            "median_excess_points": median,
            "top_quartile_share_pct": figs["top_quartile_share_pct"],
            "all_names_count": figs["all_names_count"],
            "all_names_median_excess_points": figs["all_names_median"],
            "graded_names": figs["graded_names"],
            "ungradeable_names": figs["ungradeable"],
            "thin": figs["graded_names"] < THIN,
            "claim_median_met": bool(median is not None
                                     and median > 0),
            "claim_share_met": bool(
                figs["top_quartile_share_pct"] is not None
                and figs["top_quartile_share_pct"]
                >= TOP_QUARTER_CLAIM_PCT),
            "rule": ("middle and top-quarter share of the group's "
                     "21-session gains over SPY, against the same "
                     "day's all-names yardstick")},
            **(ledger_mod.frozen_label_identity(row) or {}))
        graded_now += 1
        rows = led.rows()

    rows = led.rows()
    if not led.verify_chain(rows):
        return fail("the forecast record failed verification after "
                    "writing; not publishing figures from it")
    figures = ledger_mod.recompute_figures(rows)
    mine = figures.get(ENGINE_ID, {"forecasts": 0, "graded": 0})
    cohort_days = sorted({(r.get("lineage") or {}).get("cohort", {})
                          .get("cohort_date")
                          for r in rows
                          if r.get("type") == "forecast"
                          and r.get("engine_id") == ENGINE_ID
                          and (r.get("lineage") or {}).get("cohort")})
    interaction_names_recorded = sum(
        len((r.get("outcome") or {}).get("members") or [])
        for r in rows
        if r.get("type") == "forecast" and r.get("engine_id") == ENGINE_ID
        and (r.get("outcome") or {}).get("arm") == "interaction")
    interaction_names_graded = sum(
        (r.get("grade") or {}).get("graded_names", 0)
        for r in rows
        if r.get("type") == "grade" and r.get("engine_id") == ENGINE_ID
        and ": interaction" in (r.get("subject") or ""))
    # Verdict arithmetic, pooled over graded groups, thin rule on.
    arm_figs = {}
    for r in rows:
        if r.get("type") == "grade" and r.get("engine_id") == ENGINE_ID:
            arm = (r.get("subject") or "").rsplit(": ", 1)[-1]
            g = r["grade"]
            a = arm_figs.setdefault(arm, {"names": 0, "hits": 0,
                                          "medians": []})
            a["names"] += g.get("graded_names", 0)
            a["hits"] += round(
                g.get("top_quartile_share_pct", 0.0)
                * g.get("graded_names", 0) / 100.0)
            a["medians"].append(g.get("median_excess_points"))
    pooled = {}
    for arm, a in arm_figs.items():
        pooled[arm] = {
            "graded_names": a["names"],
            "top_quartile_share_pct": (
                round(100.0 * a["hits"] / a["names"], 2)
                if a["names"] >= THIN else None),
            "thin": a["names"] < THIN}
    retired = False
    kill_margin = None
    if interaction_names_graded >= PROVING_NAMES:
        singles = [pooled[a]["top_quartile_share_pct"]
                   for a in ("dark_only", "insider_only",
                             "filings_only")
                   if pooled.get(a, {}).get("top_quartile_share_pct")
                   is not None]
        inter = pooled.get("interaction", {}).get(
            "top_quartile_share_pct")
        if singles and inter is not None:
            kill_margin = round(inter - max(singles), 2)
            retired = kill_margin < KILL_MARGIN_POINTS

    idx = dark.get("index_reading") or {}
    data = {
        "tool": "Silent Accumulation",
        "state": "proving",
        "retired": retired,
        "as_of": panel_as_of,
        "price_history": {"from": spy_dates[0], "to": panel_as_of,
                          "sessions": len(spy_dates),
                          "names": len(panel)},
        "source": ("The insider record gathered "
                   f"{insider.get('as_of')} (filings filed "
                   f"{insider.get('window_start')} to "
                   f"{insider.get('as_of')}), the published dark "
                   "record, the quarterly holdings filings for the "
                   f"periods ended {periods[1]} and {periods[0]}, "
                   "and the daily price history on record "
                   f"({spy_dates[0]} to {panel_as_of}), which is "
                   "used only to grade, never as an input."),
        "idea": ("Some stocks are being quietly built up in ways "
                 "that leave no mark on the price chart. Trading "
                 "moves off the public exchanges. The people who "
                 "run the company stop selling their own shares. "
                 "And between one quarterly holdings report and "
                 "the next, more big holders own the stock, or "
                 "the ones who own it own more of it. Any one of "
                 "those can happen by accident. This page tests "
                 "what happens when all three point the same way "
                 "at once, and it is graded against each one on "
                 "its own, so the combination has to earn its "
                 "place. One of the three readings is an absence: "
                 "insiders not selling is treated as a reading in "
                 "its own right."),
        "claim": {
            "words": ("When a stock's off-exchange reading is in "
                      "the top fifth, its insiders show no sales "
                      "at all in the record window, and its big "
                      "holders grew between the two quarters on "
                      "record, then over the next 21 trading days "
                      "the middle stock in that group will beat "
                      "the broad market, and the share of the "
                      "group reaching the top quarter of all "
                      "stocks will be at least 30 percent, against "
                      "the 25 percent that happens by construction "
                      "across all stocks."),
            "top_quartile_claim_pct": TOP_QUARTER_CLAIM_PCT,
            "baseline_pct": BASELINE_TOP_QUARTER_PCT,
            "points_explained": ("Beating the market is measured "
                                 "in points: a stock up 5 percent "
                                 "while the market is up 2 percent "
                                 "scores +3 points over 21 trading "
                                 "days.")},
        "readings": {
            "dark": {
                "name": "Off-exchange pressure, per stock",
                "state": "not_on_record" if dark_gap else "on_record",
                "names_on_record": dark_names_on_record,
                "sessions_on_record": dark_sessions_on_record,
                "session": dark_session,
                "top_fifth": dark_top,
                "top_fifth_count": len(dark_top),
                "gap_words": (per_name.get("coverage") if dark_gap
                              else None),
                "combined_context": {
                    "name": idx.get("name"),
                    "pct": idx.get("pct"),
                    "session": idx.get("session"),
                    "stocks_used": idx.get("stocks_used"),
                    "stocks_total": idx.get("stocks_total"),
                    "funds": dark.get("funds") or [],
                    "history": dark.get("history") or [],
                    "words": ("For context only: the dark record "
                              "does hold a combined reading for "
                              "the whole index and the three index "
                              "funds' own ratios, shown here "
                              "exactly as published. Neither is a "
                              "reading for any single stock, and "
                              "neither is ever used in this "
                              "engine's test.")}},
            "insider": {
                "name": "Insiders not selling",
                "gathered": insider.get("as_of"),
                "window_start": insider.get("window_start"),
                "window": insider.get("window"),
                "names_covered": len(names),
                "names_with_summary": len(with_summary),
                "no_summary_names": no_summary,
                "open_buys": buys, "open_sells": sells,
                "zero_sell_names": zero_sell,
                "zero_sell_detail": zero_sell_detail,
                "silent_on_all_open_trades": silent_all,
                "words": ("A name passes when its summary shows "
                          "zero open-market sells in the window. "
                          "The 7 names with no summary at all are "
                          "never counted as passing: having no "
                          "record is not the same as insiders not "
                          "selling.")},
            "filings": {
                "name": "Big holders building",
                "periods": periods,
                "filers_current": tracker.get("holders_on_record"),
                "filers_prior": tracker.get(
                    "prior_holders_on_record"),
                "resolved_current": len(cur_by_sym),
                "resolved_prior": len(pri_by_sym),
                "resolved_both": len(rise),
                "tracked_names": len(tracked),
                "rise_names": rise_names,
                "rise_by_count": sorted(
                    s for s, v in rise.items() if v["count_rose"]),
                "table": rise_table,
                "words": ("A name passes when its holder count "
                          "rose or its total reported shares rose "
                          "between the two quarters. A name is "
                          "judged only when it can be matched in "
                          "both quarters: matching is by company "
                          "name, and large widely held names often "
                          "fail the strict match, so most tracked "
                          "names carry no judgement at all. An "
                          "unmatched name is never read as a fall.")}},
        "groups_today": {
            "dark_only": (None if dark_gap else groups_today["dark_only"]),
            "dark_only_state": ("cannot be formed: no per-stock "
                                "dark readings are stored"
                                if dark_gap else "formed"),
            "insider_only": groups_today["insider_only"],
            "filings_only": groups_today["filings_only"],
            "insider_and_filings": groups_today["insider_and_filings"],
            "interaction": groups_today["interaction"],
            "interaction_state": (
                "cannot form today: the dark leg has no stored "
                "per-stock readings, so no name can pass or fail "
                "it; the names passing the other two legs are "
                "listed as waiting, not recorded"
                if dark_gap else
                ("formed" if groups_today["interaction"]
                 else "no name passes all three today"))},
        "live": {
            "cohort_days": cohort_days,
            "records_written": mine["forecasts"],
            "records_graded": mine["graded"],
            "cohort_names_recorded": interaction_names_recorded,
            "cohort_names_graded": interaction_names_graded,
            "proving_target_names": PROVING_NAMES,
            "missed_sessions": missed_sessions,
            "pooled": pooled,
            "kill_margin_points": kill_margin,
            "created_this_run": created,
            "graded_this_run": graded_now,
            "wait": (("No group has been recorded yet, and none "
                     "can be until the per-stock dark record "
                     "exists: the readings for individual stocks "
                     "are worked out each day to build the "
                     "combined figure and then not kept, and the "
                     "per-stock collection has not started. The "
                     "day that record holds its first session of "
                     "per-stock readings, this page takes its top "
                     "fifth, meets it against the other two legs "
                     "exactly as shown above, and writes every "
                     "group to the public record before the 21 "
                     "trading days begin.")
                     if dark_gap else
                     ("No group has been recorded yet. The "
                     "per-stock dark record is on record "
                     "(%d names over %d sessions, freshest %s), "
                     "so the dark leg can be judged; today no "
                     "name passes all three legs at once "
                     "(%s)."
                     % (dark_names_on_record,
                        dark_sessions_on_record, dark_session,
                        "formed" if groups_today["interaction"]
                        else "no name passes all three today")))
                     + (" Groups then form at "
                     "each quarterly holdings publication and at "
                     "the weekly dark refresh. The verdict needs "
                     "100 recorded group names, and the other two "
                     "legs are narrow today (%d names pass the "
                     "insider and filings legs together), so this "
                     "record will build slowly and only widens as "
                     "the records behind it grow."
                     % len(groups_today["insider_and_filings"]))},
        "self_test": test,
        "kill_criterion": ("After 100 group names have been "
                           "recorded and graded, if the three-way "
                           "group's share reaching the top quarter "
                           "adds less than 2 points over the best "
                           "single condition on its own, this tool "
                           "retires. Beating the plain all-stocks "
                           "rate is not enough: the combination "
                           "must beat its own best part."),
        "thin_cell_rule": ("Any group with fewer than 30 graded "
                           "stocks shows its count only, with no "
                           "middle and no share headline."),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _ab.attach(data, ENGINE_ID) if _ab is not None else data
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH}: dark per-stock on record "
          f"{dark_names_on_record} names / {dark_sessions_on_record} "
          f"sessions, zero-sell {len(zero_sell)}, big-holder rise "
          f"{len(rise_names)} of {len(rise)} judged, waiting "
          f"{groups_today['insider_and_filings']}, live records "
          f"{mine['forecasts']} ({created} new), graded "
          f"{mine['graded']} ({graded_now} new), self-test "
          f"{test['state']}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
