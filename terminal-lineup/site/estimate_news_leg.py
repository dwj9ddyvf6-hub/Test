#!/usr/bin/env python3
"""FE04 news leg estimation (RC-09, 2026-10-30).

The fair gap model's news leg had no registered coefficient
because the news store carried no signed per article
direction. From 2026-10-30 the news lane stores a direction
per article (morgue/news_direction.py, frozen headline
lexicon). This estimator is the registered estimation route:

- for each session from 2026-10-30 forward, it pairs every
  directed article published inside the session's overnight
  window (20:00 UTC the prior day to 13:30 UTC, the fair gap
  record's own window) with its name's market and sector
  residual gap from gap-destiny/fair_gap_record.json;
- the per name news variable is the mean direction of its
  overnight articles; the coefficient is the pooled
  regression slope of residual gap on that variable across
  all paired names and sessions, with its standard error;
- a coefficient is registered only when the pooled sample
  reaches MIN_PAIRS paired names and the slope's absolute
  t statistic reaches MIN_T; otherwise the record states
  the sample on hand and the first date the thresholds
  could be met is named by the accrual itself.

Lookahead boundary: the gap is the estimation outcome only.
Live use of a registered coefficient, in fair_gap_model.py,
may only use articles published before the session open.
No coefficient is written by this script until the
thresholds are met; it writes only the estimation record at
site/gap-destiny/news_leg_estimation.json.

Usage: python3 estimate_news_leg.py
"""

import json
import math
import os
import statistics
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
NEWS_DIR = os.path.join(WS, "morgue", "state", "morgue", "news")
FAIR_GAP = os.path.join(HERE, "gap-destiny", "fair_gap_record.json")
OUT_PATH = os.path.join(HERE, "gap-destiny",
                        "news_leg_estimation.json")
START_DATE = "2026-10-30"
MIN_PAIRS = 100
MIN_T = 2.0


def overnight_pairs(news_days, fair_gap):
    """Pair directed overnight articles with residual gaps.
    news_days: {date: news store doc}; fair_gap: the fair gap
    record for one session. Returns per name mean direction
    and residual for names present in both."""
    session = fair_gap.get("session")
    if not session:
        return {}
    day = datetime.strptime(session, "%Y-%m-%d").replace(
        tzinfo=timezone.utc)
    lo = (day - timedelta(days=1)).strftime("%Y-%m-%dT20:00:00Z")
    hi = day.strftime("%Y-%m-%dT13:30:00Z")
    per_name = {}
    for doc in news_days.values():
        for sym, arts in (doc.get("symbols") or {}).items():
            for a in arts:
                if "direction" not in a:
                    continue
                ts = a.get("created_at") or ""
                if not (lo <= ts <= hi):
                    continue
                per_name.setdefault(sym, []).append(a["direction"])
    names = fair_gap.get("names") or {}
    pairs = {}
    for sym, dirs in per_name.items():
        row = names.get(sym)
        if not row or row.get("residual_gap_pct") is None:
            continue
        pairs[sym] = {"news_direction_mean": round(
                          statistics.fmean(dirs), 4),
                      "articles": len(dirs),
                      "residual_gap_pct": row["residual_gap_pct"]}
    return pairs


def pooled_slope(pairs_by_session):
    xs, ys = [], []
    for pairs in pairs_by_session.values():
        for row in pairs.values():
            xs.append(row["news_direction_mean"])
            ys.append(row["residual_gap_pct"])
    n = len(xs)
    if n < 3:
        return {"pairs": n, "slope": None, "t": None}
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return {"pairs": n, "slope": None, "t": None}
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    resid = [y - (my + slope * (x - mx)) for x, y in zip(xs, ys)]
    s2 = sum(r * r for r in resid) / (n - 2)
    se = math.sqrt(s2 / sxx) if sxx > 0 else None
    t = (slope / se) if se else None
    return {"pairs": n, "slope": round(slope, 4),
            "t": round(t, 3) if t is not None else None}


def main():
    news_days = {}
    if os.path.isdir(NEWS_DIR):
        for name in sorted(os.listdir(NEWS_DIR)):
            if name.endswith(".json") and name[:10] >= START_DATE:
                with open(os.path.join(NEWS_DIR, name),
                          encoding="utf-8") as fh:
                    news_days[name[:10]] = json.load(fh)
    pairs_by_session = {}
    if os.path.exists(FAIR_GAP):
        with open(FAIR_GAP, encoding="utf-8") as fh:
            fair_gap = json.load(fh)
        if (fair_gap.get("session") or "") >= START_DATE:
            pairs_by_session[fair_gap["session"]] = \
                overnight_pairs(news_days, fair_gap)
    est = pooled_slope(pairs_by_session)
    registrable = (est["pairs"] >= MIN_PAIRS and est["t"] is not None
                   and abs(est["t"]) >= MIN_T)
    record = {
        "record": "FE04 news leg estimation, directed news record",
        "method": ("per article direction from the frozen "
                   "headline lexicon (morgue/news_direction.py); "
                   "per name variable is the mean direction of "
                   "its overnight articles; coefficient is the "
                   "pooled slope of the fair gap market and "
                   "sector residual on that variable"),
        "lookahead_boundary": ("direction uses headline text and "
                               "publication time only; the gap is "
                               "the estimation outcome, never an "
                               "input; live use may only use "
                               "articles published before the "
                               "session open"),
        "start_date": START_DATE,
        "thresholds": {"min_pairs": MIN_PAIRS, "min_abs_t": MIN_T},
        "sessions_on_record": sorted(pairs_by_session),
        "pairs_by_session": {s: len(p)
                             for s, p in pairs_by_session.items()},
        "estimate": est,
        "coefficient_registered": registrable,
        "coefficient": est["slope"] if registrable else None,
        "state": ("registered" if registrable else
                  "accruing: the directed record starts "
                  "2026-10-30 and the fair gap record for a "
                  "directed session is not on hand yet, so no "
                  "pair can be formed; the first estimation "
                  "runs on the first fair gap session at or "
                  "after 2026-10-30 whose overnight window "
                  "holds directed articles"),
    }
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, OUT_PATH)
    print(f"news leg estimation: pairs {est['pairs']}, "
          f"registered {registrable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
