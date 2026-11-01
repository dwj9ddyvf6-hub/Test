#!/usr/bin/env python3
"""FE04 fair gap model (publication cure B3 / R-16, 2026-10-30).

Decomposes a session's overnight gap per name into:

- market leg: rolling overnight beta (the name's overnight returns
  regressed on SPY's, trailing 250 sessions, minimum 120, sessions
  strictly before the gap day) times SPY's overnight gap that
  session;
- sector leg: the median overnight gap of the name's sector
  constituents that session, times a sector beta estimated the
  same rolling way, orthogonalised by removing the market leg's
  share of the sector move so the legs never double count. Names
  with no sector on record fall back to a correlation cluster:
  the panel names whose overnight returns correlate most with the
  name (best correlation at or above the registered floor 0.30),
  labelled cluster_sector, never presented as a GICS sector.
  Below the floor the sector leg is not_recorded for that name;
- news leg: from the morgue news store, articles timestamped after
  the prior close and before the open for that name. The store
  covers only the tracked universe and only recent sessions; where
  it does not cover a name or session the leg is not_recorded and
  the residual is published as market_and_sector_residual, never
  as the full fair gap residual.

residual_gap = raw_gap - market_leg - sector_leg (news leg joins
the subtraction only on sessions and names where it is recorded,
with its registered form stated in the record).

The runner writes site/gap-destiny/fair_gap_record.json for the
panel's latest session: per gap name (absolute gap at or above
0.5 percent, the Engine 28 live set's own floor) the legs, the
residual, and coverage counts. refresh_earningsdistribution.py
publishes the remainder block from this record; Engine 28's raw
gap legs continue unchanged so the two can be graded against
each other.

Usage: python3 fair_gap_model.py
"""

import json
import os
import statistics
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(os.path.dirname(HERE))
PANEL = os.path.join(WORKSPACE, "morgue", "data_cache",
                     "board_bt_bars.json")
SECTOR_MAP = os.path.join(WORKSPACE, "femto-lean", "config",
                          "gics_sectors.json")
NEWS_DIR = os.path.join(WORKSPACE, "morgue", "state", "morgue",
                        "news")
OUT_PATH = os.path.join(HERE, "gap-destiny",
                        "fair_gap_record.json")
BETA_WINDOW = 250
BETA_MIN = 120
CLUSTER_FLOOR = 0.30
CLUSTER_SIZE = 12
GAP_FLOOR = 0.005


def overnight(rows):
    """[(date, open/prior_close - 1)] from panel rows
    [date, o, h, l, c, v]."""
    out = []
    for i in range(1, len(rows)):
        pc = float(rows[i - 1][4])
        o = float(rows[i][1])
        if pc > 0 and o > 0:
            out.append((rows[i][0], o / pc - 1.0))
    return out


def beta_and_corr(xs, ys):
    """OLS slope of ys on xs and their correlation, or
    (None, None) below the minimum or on a flat market leg."""
    if len(xs) < BETA_MIN:
        return None, None
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return None, None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    syy = sum((y - my) ** 2 for y in ys)
    corr = sxy / math.sqrt(sxx * syy) if syy > 0 else None
    return sxy / sxx, corr


import math  # noqa: E402


def main():
    with open(PANEL, encoding="utf-8") as fh:
        panel = json.load(fh)
    sector_of = {}
    if os.path.exists(SECTOR_MAP):
        with open(SECTOR_MAP, encoding="utf-8") as fh:
            raw = json.load(fh)
        # the map's shape is {"symbols": {symbol: {"sector":
        # ...}}}, the same map the rotation refresher proves
        # against; a flat {symbol: sector} shape is also read.
        symbols_map = raw.get("symbols", raw)
        for k, v in symbols_map.items():
            if isinstance(v, str):
                sector_of[k] = v
            elif isinstance(v, dict) and v.get("sector"):
                sector_of[k] = v["sector"]
    spy_ov = dict(overnight(panel["SPY"]))
    session = panel["SPY"][-1][0]
    prior = panel["SPY"][-2][0]
    spy_gap = spy_ov[session]
    # per name overnight series ending the session before `session`
    series = {}
    gap_today = {}
    for sym, rows in panel.items():
        ov = overnight(rows)
        series[sym] = ov
        d = dict(ov)
        if session in d and abs(d[session]) >= GAP_FLOOR:
            gap_today[sym] = d[session]
    # sector median gaps today
    by_sector = {}
    for sym, g in gap_today.items():
        s = sector_of.get(sym)
        if s:
            by_sector.setdefault(s, []).append(g)
    sector_median = {s: statistics.median(v)
                     for s, v in by_sector.items() if len(v) >= 3}
    # news coverage for the session window. The store's actual
    # shape is {symbols: {symbol: [articles]}} with a fetched
    # window per file; the earlier reader looked for a top level
    # articles list and a list valued symbols key, matched
    # neither, and so read the store as empty on every run
    # (RC-09 cure, 2026-10-30). Articles are now selected by
    # their own timestamps: the overnight window for the
    # session runs from the prior session's close (20:00 UTC)
    # to the session's open (13:30 UTC), whichever file holds
    # them.
    news_names = set()
    overnight_counts = {}
    news_fields = set()
    news_store_symbols = set()
    win_lo = prior + "T20:00:00Z"
    win_hi = session + "T13:30:00Z"
    if os.path.isdir(NEWS_DIR):
        for fname in sorted(os.listdir(NEWS_DIR)):
            if not fname.endswith(".json"):
                continue
            with open(os.path.join(NEWS_DIR, fname),
                      encoding="utf-8") as fh:
                doc = json.load(fh)
            by_sym = doc.get("symbols") or {}
            if isinstance(by_sym, dict):
                for key, arts in by_sym.items():
                    news_store_symbols.add(key)
                    for a in arts if isinstance(arts, list) else []:
                        if not isinstance(a, dict):
                            continue
                        news_fields.update(a.keys())
                        ts = a.get("created_at") or ""
                        syms = a.get("symbols") or [key]
                        if win_lo <= ts <= win_hi:
                            for s in syms:
                                overnight_counts[s] = \
                                    overnight_counts.get(s, 0) + 1
            for a in doc.get("articles") or doc.get("items") or []:
                if isinstance(a, dict) and a.get("symbol"):
                    news_fields.update(a.keys())
                    ts = a.get("created_at") or ""
                    if win_lo <= ts <= win_hi:
                        s = a["symbol"]
                        overnight_counts[s] = \
                            overnight_counts.get(s, 0) + 1
    news_names = set(overnight_counts)
    series_dict = {s: dict(v) for s, v in series.items()}
    # Cluster medians for gap names with no sector on record:
    # one matrix correlation pass (numpy) over the trailing
    # window aligned to SPY sessions. For each unmapped gap
    # name, the median today gap of its CLUSTER_SIZE most
    # correlated panel names whose correlation clears the floor.
    _cluster_medians = {}
    unmapped = [s_ for s_ in gap_today if s_ not in sector_of]
    if unmapped:
        import numpy as np
        spy_dates = [d for d, _v in series["SPY"] if d < session]
        window = spy_dates[-BETA_WINDOW:]
        widx = {d: i for i, d in enumerate(window)}
        all_syms = sorted(series)
        mat = np.full((len(all_syms), len(window)), np.nan)
        for ri, s_ in enumerate(all_syms):
            for d, v in series[s_]:
                j = widx.get(d)
                if j is not None:
                    mat[ri, j] = v
        today_gap = np.array([dict(series[s_]).get(session, np.nan)
                              for s_ in all_syms])
        sym_row = {s_: i for i, s_ in enumerate(all_syms)}
        for s_ in unmapped:
            own = mat[sym_row[s_]]
            ok = ~np.isnan(own)
            if ok.sum() < BETA_MIN:
                continue
            xo = own[ok]
            filled = np.where(np.isnan(mat[:, ok]), 0.0,
                              mat[:, ok])
            num = filled @ xo
            den_x = np.sqrt((filled ** 2).sum(axis=1))
            den_o = np.sqrt((xo ** 2).sum())
            with np.errstate(invalid="ignore", divide="ignore"):
                corr = num / (den_x * den_o)
            corr[sym_row[s_]] = -1.0
            order = np.argsort(-np.nan_to_num(corr))[:CLUSTER_SIZE]
            top = [all_syms[i] for i in order
                   if corr[i] >= CLUSTER_FLOOR
                   and not np.isnan(today_gap[i])]
            if top:
                _cluster_medians[s_] = statistics.median(
                    [dict(series[o])[session] for o in top])
    results = {}
    counts = {"gap_names": len(gap_today), "market_leg": 0,
              "sector_leg_gics": 0, "sector_leg_cluster": 0,
              "sector_leg_missing": 0, "news_leg": 0,
              "full_residual": 0, "market_sector_residual": 0}
    for sym, raw_gap in sorted(gap_today.items()):
        hist = [(d, v) for d, v in series[sym] if d < session]
        xs, ys = [], []
        spy_hist = spy_ov
        for d, v in hist[-BETA_WINDOW:]:
            if d in spy_hist:
                xs.append(spy_hist[d])
                ys.append(v)
        b, _c = beta_and_corr(xs, ys)
        market_leg = b * spy_gap if b is not None else None
        if market_leg is not None:
            counts["market_leg"] += 1
        sector = sector_of.get(sym)
        sector_leg, sector_kind = None, None
        if sector and sector in sector_median and b is not None:
            # sector beta: median constituent overnight series is
            # approximated by the sector median gap series leg
            # through the name's own beta orthogonalised: the
            # sector move beyond the market move, weighted by the
            # name's beta, so the legs sum without double counting.
            sector_leg = b * (sector_median[sector] - spy_gap)
            sector_kind = "gics"
            counts["sector_leg_gics"] += 1
        elif b is not None:
            # correlation cluster fallback, from the one
            # correlation pass over the aligned overnight matrix
            # (_cluster_medians, computed once for all unmapped
            # gap names, never per name pairwise loops).
            med = _cluster_medians.get(sym)
            if med is not None:
                sector_leg = b * (med - spy_gap)
                sector_kind = "cluster_sector"
                counts["sector_leg_cluster"] += 1
            else:
                counts["sector_leg_missing"] += 1
        if market_leg is None:
            continue
        residual = raw_gap - market_leg - (sector_leg or 0.0)
        kind = "market_and_sector_residual" \
            if sector_leg is not None else "market_residual_only"
        if sym in news_names:
            # On record is not a leg: with no registered
            # coefficient no news leg is computed for any name,
            # so counts["news_leg"] stays 0 and the coverage is
            # carried by counts["news_on_record"] and the
            # news_leg_evidence block (RC-09 cure, 2026-10-30).
            kind = kind + "_news_on_record_no_coefficient"
        if sector_leg is not None:
            counts["market_sector_residual"] += 1
        results[sym] = {
            "raw_gap_pct": round(raw_gap * 100, 4),
            "beta": round(b, 4) if b is not None else None,
            "market_leg_pct": round(market_leg * 100, 4),
            "sector_leg_pct": (round(sector_leg * 100, 4)
                               if sector_leg is not None else None),
            "sector_kind": sector_kind,
            "news_leg": ("on_record_no_registered_coefficient"
                         if sym in news_names else "not_recorded"),
            "residual_gap_pct": round(residual * 100, 4),
            "residual_kind": kind,
        }
    gap_with_news = [s for s in gap_today if s in overnight_counts]
    news_evidence = {
        "state": "not_estimable_on_records_on_hand",
        "window_utc": [win_lo, win_hi],
        "gap_names": len(gap_today),
        "gap_names_with_overnight_news": len(gap_with_news),
        "overnight_articles_on_gap_names": sum(
            overnight_counts[s] for s in gap_with_news),
        "news_store_symbols": len(news_store_symbols),
        "news_store_fields": sorted(news_fields),
        "signed_direction_field_present": False,
        "missing_inputs": [
            "a signed per article direction record (sentiment or "
            "event direction) in the news store: its articles carry "
            "only id, headline, source, created_at, url and symbols, "
            "so no signed news variable exists to estimate a "
            "coefficient against",
            "news coverage beyond the tracked universe: the store "
            f"covers {len(news_store_symbols)} symbols, and "
            f"{len(gap_today) - len(gap_with_news)} of the "
            f"{len(gap_today)} gap names have no overnight article "
            "on record for this session",
        ],
        "note": ("No news coefficient is registered, because the "
                 "records on hand cannot estimate one honestly: an "
                 "unsigned article count would enter an award "
                 "headline and a fraud headline with the same sign. "
                 "The news leg and the full residual stay at 0 "
                 "until a signed news record exists."),
    }
    counts["news_on_record"] = len(gap_with_news)
    record = {
        "updated_ts": datetime.now(timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session": session,
        "news_leg_evidence": news_evidence,
        "model": "fair_gap_model v1 (fair_gap_model.py): rolling "
                 "250 session overnight beta (min 120), sector "
                 "median gap orthogonalised against the market "
                 "leg, correlation cluster fallback labelled "
                 "cluster_sector at floor 0.30, news leg recorded "
                 "but carrying no registered coefficient yet",
        "spy_gap_pct": round(spy_gap * 100, 4),
        "counts": counts,
        "names": results,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(record, indent=1, sort_keys=True) + "\n")
    os.replace(tmp, OUT_PATH)
    print(f"fair_gap_model: session {session}, {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
