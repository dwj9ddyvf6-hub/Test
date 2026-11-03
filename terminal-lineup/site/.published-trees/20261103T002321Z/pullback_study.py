#!/usr/bin/env python3
"""Pullback Norm study on the DEEP panel (RC-25 cure, 2026-10-30).

The Pullback Norm page shipped unpublished because no pullback
study had ever run on a record this terminal holds. The DEEP
panel (15,815 names, 22,346,713 rows) landed 2026-10-30, so the
study now runs here, through the panel's own reader, and writes
site/pullback-norm/study_record.json. refresh_pullback.py
publishes the counted state from that record.

Frozen definitions (labelled ours where a choice was ours):

- Universe: panel names with at least 900 sessions on record,
  excluding the index funds SPY, QQQ and IWM (counted as
  excluded). Every other name is counted as too short.
- True range and depth follow the depth family's narrowing as
  coded in refresh_feardaytriangulation.py: depth on session j
  is (the highest close of the last 63 sessions including j,
  minus the close on j) divided by the middle true range over
  the trailing 126 sessions ending the session before j. The
  own-norm rank is that depth's percentile against all of the
  same stock's earlier computable depths, leaving today out;
  at least 126 earlier depths are required.
- The original form from the earlier study (typical range over
  750 sessions, at least 750 earlier depths) is computed beside
  the narrowed form wherever the panel is long enough, so the
  narrowing is measured, not assumed.
- A depth whose middle true range is zero is not computable,
  exactly as the depth family's own depth reading treats it in
  refresh_feardaytriangulation.py (a median at or below zero
  returns no depth): the division yields no finite figure, so
  the depth is NaN, it is never ranked, and it can never
  publish as inf (cure 2026-10-30: XBPEW's freshest session
  depth divided by a zero median true range and published as
  Infinity).
- Rising trend is the picker replay's fixed reading, as coded
  for Engine 24: close above both the 21 and 50 session mean
  closes (today included) and the 50 session mean higher than
  it was 5 sessions earlier.
- An event is the first session of a dip: trend passes, the
  own-norm rank is at or above 80 out of 100, and the previous
  session's rank was below 80 or not computable.
- Forward readings are close to close at 20 and 60 sessions,
  minus SPY's forward reading over the same sessions, and are
  counted only where the full window exists on the panel.
- Recovery is the first session within 60 on which the close
  regains the 63 session high close that defined the dip;
  events that never regain it inside 60 are censored, counted,
  never dropped.
- Latest session signals: events whose session is the panel's
  freshest session, named in full up to 50.

Engine legs computed from the same event machinery:

- Engine 24 depth leg: fear days on the panel era the fear
  gauge record covers (its daily readings from 2024-10-30),
  using the Fear Day List's own definition. The cohort is
  rising trend names in the deepest fifth that day; the
  control is every rising trend name that day. Readings are
  20 session forward returns in units of the name's own
  typical range percent (middle true range over 14 sessions
  divided by the close), the R unit stated on the record.
- Engine 29 depth leg: the same fear day deepest fifth events
  run as first passage races: one expected move is the name's
  typical range percent times the square root of 20; the race
  settles on the first close at or beyond one expected move up
  or down within 60 sessions, or stays unsettled at 60.

Performance note (efficiency cure, same day): the first run of
this study spent its wall time converting every panel row's
date through Python and building a date dict per name. This
version works on the binary store's ordinal arrays, converts
only event dates, and takes rolling medians from the compiled
rolling implementation; the measured full run is recorded in
the terminal BUGLOG.

No number is published from a partial window, and no session
after the panel's freshest is invented.

Usage: python3 pullback_study.py
"""

import bisect
import json
import math
import os
import statistics
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(os.path.dirname(HERE))
PANEL_PATH = os.path.join(WORKSPACE, "morgue", "data_cache",
                          "deep_bars.json")
VIX_PATH = os.path.expanduser(
    "~/workspace/opt/rea-teardowns/azrael-1587/source/"
    "yahoo-vix-daily.json")
OUT_PATH = os.path.join(HERE, "pullback-norm", "study_record.json")

MIN_SESSIONS = 900
INDEX_FUNDS = ("SPY", "QQQ", "IWM")
HIGH_SESSIONS = 63
TR_WINDOW = 126
TR_WINDOW_ORIG = 750
MIN_PRIOR = 126
MIN_PRIOR_ORIG = 750
DEEP_RANK = 80.0
FWD_SHORT = 20
FWD_LONG = 60


def rolling_median(x, w):
    """Median of the trailing w values ending at each index;
    NaN where the window is short. Compiled rolling median."""
    return pd.Series(x).rolling(w, min_periods=w).median().to_numpy()


def rolling_max(x, w):
    n = len(x)
    out = np.full(n, np.nan)
    if n >= w:
        win = np.lib.stride_tricks.sliding_window_view(x, w)
        out[w - 1:] = win.max(axis=1)
    return out


def sma(x, w):
    n = len(x)
    out = np.full(n, np.nan)
    if n >= w:
        cs = np.concatenate(([0.0], np.cumsum(x)))
        out[w - 1:] = (cs[w:] - cs[:-w]) / w
    return out


def depth_ranks(closes, trs, tr_window, min_prior):
    """(depths list, ranks list) of Python floats; rank is the
    percentile of today's depth against all earlier computable
    depths, or NaN."""
    n = len(closes)
    med = rolling_median(trs, tr_window)
    med_prev = np.full(n, np.nan)
    med_prev[1:] = med[:-1]
    high = rolling_max(closes, HIGH_SESSIONS)
    with np.errstate(invalid="ignore", divide="ignore"):
        depths = (high - closes) / med_prev
    # Bound at the source (cure 2026-10-30): a zero median true
    # range makes the depth not computable, the depth family's
    # own convention, so every non-finite depth (inf from a zero
    # denominator, NaN from a short window) is NaN here and can
    # never be ranked, counted as an event, or published.
    depths = np.where(np.isfinite(depths), depths, np.nan)
    depths = depths.tolist()
    ranks = [math.nan] * n
    sorted_prior = []
    for j in range(n):
        d = depths[j]
        if d != d:  # NaN
            continue
        if len(sorted_prior) >= min_prior:
            ranks[j] = 100.0 * bisect.bisect_left(
                sorted_prior, d) / len(sorted_prior)
        bisect.insort(sorted_prior, d)
    return depths, ranks


def load_vix():
    with open(VIX_PATH, encoding="utf-8") as fh:
        doc = json.load(fh)
    result = doc["chart"]["result"][0]
    out = {}
    for ts, close in zip(result["timestamp"],
                         result["indicators"]["quote"][0]["close"]):
        if close is None:
            continue
        day = datetime.fromtimestamp(ts, tz=timezone.utc).date()
        out[day.toordinal()] = float(close)
    return out


def main():
    sys.path.insert(0, HERE)
    from deep_panel_reader import DeepPanelReader
    from datetime import date
    reader = DeepPanelReader(PANEL_PATH)
    fingerprint = reader.fingerprint
    lengths = reader.lengths()
    if reader.strategy.get("mode") != "binary_memmap":
        print("pullback_study: binary store unavailable, "
              "refusing the slow path", file=sys.stderr)
        return 1

    def arrays(sym):
        start, count = reader._index[sym]
        ohlc = reader._ohlc[start:start + count]
        ordd = reader._ord[start:start + count]
        return (np.asarray(ordd, dtype=np.int64),
                np.asarray(ohlc[:, 3], dtype=np.float64),
                np.asarray(ohlc[:, 1], dtype=np.float64),
                np.asarray(ohlc[:, 2], dtype=np.float64))

    spy_ord, spy_closes, _sh, _sl = arrays("SPY")
    qqq_ord, qqq_closes, _qh, _ql = arrays("QQQ")
    spy_idx = {int(o): i for i, o in enumerate(spy_ord)}
    qqq_close_by_ord = {int(o): float(c)
                        for o, c in zip(qqq_ord, qqq_closes)}
    last_ord = int(spy_ord[-1])
    last_session = date.fromordinal(last_ord).isoformat()

    def spy_fwd(ordinal, horizon):
        i = spy_idx.get(ordinal)
        if i is None or i + horizon >= len(spy_closes):
            return None
        return float(spy_closes[i + horizon] / spy_closes[i] - 1.0)

    vix = load_vix()
    vix_ords = sorted(vix)
    fear_ords = set()
    for k in range(1, len(vix_ords)):
        o, prev = vix_ords[k], vix_ords[k - 1]
        i = spy_idx.get(o)
        if i is None or i == 0:
            continue
        spy_chg = float(spy_closes[i] / spy_closes[i - 1] - 1.0)
        q = qqq_close_by_ord.get(o)
        q_prev = qqq_close_by_ord.get(int(spy_ord[i - 1]))
        qqq_chg = (q / q_prev - 1.0) if q and q_prev else 0.0
        vix_chg = vix[o] / vix[prev] - 1.0
        if (spy_chg < -0.015 or vix_chg > 0.15 or vix[o] >= 25.0
                or (vix[o] >= 20.0 and (spy_chg < 0 or qqq_chg < 0))):
            fear_ords.add(o)

    universe = [s for s in sorted(lengths)
                if lengths[s] >= MIN_SESSIONS and s not in INDEX_FUNDS]
    too_short = sum(1 for s in lengths
                    if lengths[s] < MIN_SESSIONS and s not in INDEX_FUNDS)

    events = []
    fear_events = []
    fear_control = []
    race_rows = []
    orig_computable_events = 0
    orig_also_deepest = 0
    latest_signals = []

    for sym in universe:
        ords, closes, highs, lows = arrays(sym)
        n = len(closes)
        pc = np.empty(n)
        pc[0] = closes[0]
        pc[1:] = closes[:-1]
        trs = np.maximum(highs - lows,
                         np.maximum(np.abs(highs - pc),
                                    np.abs(pc - lows)))
        depths, ranks = depth_ranks(closes, trs, TR_WINDOW, MIN_PRIOR)
        _d750, ranks750 = depth_ranks(closes, trs, TR_WINDOW_ORIG,
                                      MIN_PRIOR_ORIG)
        s21 = sma(closes, 21)
        s50 = sma(closes, 50)
        trend = (closes > s21) & (closes > s50)
        trend[5:] &= s50[5:] > s50[:-5]
        trend[:54] = False
        atr14 = rolling_median(trs, 14)
        is_fear = np.isin(ords, list(fear_ords)) if fear_ords \
            else np.zeros(n, dtype=bool)

        prev_rank = math.nan
        for j in range(n):
            r = ranks[j]
            if r == r and trend[j]:
                is_event = (r >= DEEP_RANK
                            and not (prev_rank == prev_rank
                                     and prev_rank >= DEEP_RANK))
            else:
                is_event = False
            if r == r:
                prev_rank = r
            elif not trend[j]:
                prev_rank = math.nan
            if is_event:
                o = int(ords[j])
                d = date.fromordinal(o).isoformat()
                ev = {"symbol": sym, "date": d,
                      "rank": round(float(r), 2),
                      "depth": round(float(depths[j]), 4)}
                r750 = ranks750[j]
                if r750 == r750:
                    orig_computable_events += 1
                    ev["rank_original_form"] = round(float(r750), 2)
                    if r750 >= DEEP_RANK:
                        orig_also_deepest += 1
                sf = spy_fwd(o, FWD_SHORT)
                if j + FWD_SHORT < n and sf is not None:
                    ev["fwd20_rel"] = float(
                        closes[j + FWD_SHORT] / closes[j] - 1.0 - sf)
                sf60 = spy_fwd(o, FWD_LONG)
                if j + FWD_LONG < n and sf60 is not None:
                    ev["fwd60_rel"] = float(
                        closes[j + FWD_LONG] / closes[j] - 1.0 - sf60)
                high_close = float(np.max(
                    closes[j - HIGH_SESSIONS + 1:j + 1]))
                rec = None
                for k in range(1, FWD_LONG + 1):
                    if j + k < n and closes[j + k] >= high_close:
                        rec = k
                        break
                ev["recovery_sessions"] = rec
                events.append(ev)
                if o == last_ord:
                    latest_signals.append(
                        {"symbol": sym, "rank": ev["rank"],
                         "depth": ev["depth"]})
                if is_fear[j] and atr14[j] == atr14[j] and atr14[j] > 0:
                    atr_pct = float(atr14[j] / closes[j])
                    if j + FWD_SHORT < n:
                        fear_events.append(
                            (d, sym, float(
                                closes[j + FWD_SHORT] / closes[j]
                                - 1.0) / atr_pct))
                    barrier = atr_pct * math.sqrt(20.0)
                    up = closes[j] * (1.0 + barrier)
                    dn = closes[j] * (1.0 - barrier)
                    settle = None
                    side = None
                    for k in range(1, FWD_LONG + 1):
                        if j + k >= n:
                            break
                        if closes[j + k] >= up:
                            settle, side = k, "up"
                            break
                        if closes[j + k] <= dn:
                            settle, side = k, "down"
                            break
                    race_rows.append({"date": d, "symbol": sym,
                                      "settle_session": settle,
                                      "side": side})
            # fear day control: every rising trend name that day
            if is_fear[j] and trend[j] and atr14[j] == atr14[j] \
                    and atr14[j] > 0 and j + FWD_SHORT < n:
                atr_pct = float(atr14[j] / closes[j])
                fear_control.append(
                    (date.fromordinal(int(ords[j])).isoformat(),
                     float(closes[j + FWD_SHORT] / closes[j]
                           - 1.0) / atr_pct))

    def bucket_stats(rows):
        f20 = [r["fwd20_rel"] for r in rows if "fwd20_rel" in r]
        f60 = [r["fwd60_rel"] for r in rows if "fwd60_rel" in r]
        recs = [r["recovery_sessions"] for r in rows
                if r["recovery_sessions"] is not None]
        return {
            "events": len(rows),
            "fwd20_counted": len(f20),
            "fwd20_mean_rel_pct": (round(statistics.fmean(f20) * 100, 3)
                                   if f20 else None),
            "fwd20_median_rel_pct": (round(statistics.median(f20) * 100, 3)
                                     if f20 else None),
            "fwd60_counted": len(f60),
            "fwd60_mean_rel_pct": (round(statistics.fmean(f60) * 100, 3)
                                   if f60 else None),
            "recovered_within_60": len(recs),
            "censored_at_60": len(rows) - len(recs),
            "recovery_median_sessions": (statistics.median(recs)
                                         if recs else None),
        }

    buckets = {}
    for lo, hi, label in ((80, 90, "rank_80_to_90"),
                          (90, 95, "rank_90_to_95"),
                          (95, 100.01, "rank_95_to_100")):
        buckets[label] = bucket_stats(
            [e for e in events if lo <= e["rank"] < hi])
    all_stats = bucket_stats(events)
    depth_vals = sorted(e["depth"] for e in events)
    deciles = ([round(depth_vals[int(q * (len(depth_vals) - 1))], 3)
                for q in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)]
               if depth_vals else [])

    fear_dates_used = sorted({d for d, _s, _r in fear_events})
    cohort_r = [r for _d, _s, r in fear_events]
    control_r = [r for _d, r in fear_control]
    e24_leg = {
        "state": "recorded",
        "fear_days_in_gauge_era": len(fear_ords),
        "fear_days_with_cohort": len(fear_dates_used),
        "cohort_events": len(fear_events),
        "control_name_days": len(fear_control),
        "cohort_mean_fwd20_r": (round(statistics.fmean(cohort_r), 4)
                                if cohort_r else None),
        "control_mean_fwd20_r": (round(statistics.fmean(control_r), 4)
                                 if control_r else None),
        "difference_r": (round(statistics.fmean(cohort_r)
                               - statistics.fmean(control_r), 4)
                         if cohort_r and control_r else None),
        "bar_note": ("Engine 24's +0.10R claim bar is stated in "
                     "the picker replay's risk units, not in this "
                     "leg's typical range units, so no bar is "
                     "applied to these figures; the engine's own "
                     "live grading judges its claim in its own "
                     "units."),
        "original_form_computable_events": orig_computable_events,
        "note": ("Deepest fifth cohort against the same day rising "
                 "trend control on the DEEP panel, 20 session forward "
                 "returns in units of each name's own typical range "
                 "percent. Fear days use the Fear Day List's own "
                 "definition over the fear gauge record from "
                 "2024-10-30."),
    }

    race_out = {}
    for horizon in (5, 10, 21, 60):
        up = sum(1 for r in race_rows
                 if r["side"] == "up" and r["settle_session"] is not None
                 and r["settle_session"] <= horizon)
        dn = sum(1 for r in race_rows
                 if r["side"] == "down" and r["settle_session"] is not None
                 and r["settle_session"] <= horizon)
        total = len(race_rows)
        race_out[f"at_{horizon}"] = {
            "up_first_pct": round(100.0 * up / total, 2) if total else None,
            "down_first_pct": round(100.0 * dn / total, 2) if total else None,
            "neither_pct": (round(100.0 * (total - up - dn) / total, 2)
                            if total else None),
        }
    settled = [r["settle_session"] for r in race_rows
               if r["settle_session"] is not None]
    hazard = []
    for k in range(1, 22):
        at_risk = sum(1 for r in race_rows
                      if r["settle_session"] is None
                      or r["settle_session"] >= k)
        settled_k = sum(1 for r in race_rows if r["settle_session"] == k)
        hazard.append(round(100.0 * settled_k / at_risk, 2)
                      if at_risk else 0.0)
    e29_leg = {
        "state": "recorded",
        "cohort_events": len(race_rows),
        "race": race_out,
        "median_settle_sessions": (statistics.median(settled)
                                   if settled else None),
        "unsettled_at_60": sum(1 for r in race_rows
                               if r["settle_session"] is None),
        "hazard_pct_sessions_1_to_21": hazard,
        "note": ("First passage race for the fear day deepest fifth "
                 "cohort on the DEEP panel: one expected move is each "
                 "name's typical range percent times the square root "
                 "of 20, settled on closes within 60 sessions."),
    }

    record = {
        "study": "Pullback Norm study on the DEEP panel",
        "run_at_utc": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
        "panel_fingerprint": fingerprint,
        "panel_names": len(lengths),
        "panel_last_session": last_session,
        "universe_names": len(universe),
        "names_too_short": too_short,
        "index_funds_excluded": len(INDEX_FUNDS),
        "min_sessions": MIN_SESSIONS,
        "events": len(events),
        "events_by_bucket": buckets,
        "all_events": all_stats,
        "depth_deciles_at_events": deciles,
        "original_form": {
            "computable_events": orig_computable_events,
            "also_deepest_under_original": orig_also_deepest,
            "agreement_pct": (round(100.0 * orig_also_deepest
                                    / orig_computable_events, 2)
                              if orig_computable_events else None),
        },
        "latest_session": last_session,
        "latest_signals": latest_signals[:50],
        "signals_on_latest_session": len(latest_signals),
        "engine_24_depth_leg": e24_leg,
        "engine_29_depth_leg": e29_leg,
    }
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, OUT_PATH)
    print(f"pullback_study: {len(events)} events over "
          f"{len(universe)} names, panel to {last_session}; "
          f"E24 cohort {len(fear_events)}, E29 races {len(race_rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
