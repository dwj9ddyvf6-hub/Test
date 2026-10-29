"""m2 features: the old beatendown_sleeve.compute_features (E/X/M/Q/P blocks — identical in confluence_sleeve)
vs the port in desk/feedlib/m2.py, on the same qualifier rows, weekly ETF closes and daily bars.

Rows: the live qualifier output of the vendored qualify_week.mjs over the vendored research bars (the
2026-09-28 week) plus synthetic rows covering every branch — desk-mapped and unmapped symbols (the
60-week sector-correlation fallback), wide / narrow weekly ranges, enrichment ids, fast state, the
calendar AVWAP above / far / missing, vote spreads, zero closes in the weekly window (the daily RQA
fallback), short daily histories (no M-block) and ETF series with holes (no X/P features). Compared: the
full feature dict of every row, the sector bucket included."""
import json
import os
import random
from datetime import date, datetime, timedelta, timezone

from desk.feedlib import m2

from . import old_run, trading_dates, write_receipt

N_WEEKS = 12

OLD = r'''
import sys
sys.argv = ["beatendown_sleeve.py"]
import beatendown_sleeve as O
out = []
for c in PAYLOAD["cases"]:
    daily = c["daily"]
    sc = O.compute_features(c["quals"], c["etf_px"], c["monday"], lambda s, daily=daily: daily.get(s) or [])
    out.append([f for _q, f in sc])
print(json.dumps(out))
'''

MAPPED = ["AEHR", "MU", "ARM", "TSEM", "ANF", "CVNA", "OKLO", "FCEL", "AG", "USAR", "KEEL", "WDC", "TEM", "VRT"]


def _walk(rnd, n, px, drift=0.0, vol=0.03):
    out = []
    for _ in range(n):
        px = max(0.5, px * (1 + rnd.gauss(drift, vol)))
        out.append(round(px, 4))
    return out


def _case(rnd, monday, real=None):
    md = date.fromisoformat(monday)
    mondays = [(md - timedelta(weeks=k)).isoformat() for k in range(89, -1, -1)]
    etf = {}
    for e in m2.ETF_WEEKLY:
        closes = _walk(rnd, len(mondays), rnd.uniform(20, 400), rnd.uniform(-0.004, 0.006))
        px = dict(zip(mondays, closes))
        if rnd.random() < 0.12 and e not in ("SPY", "UUP"):
            px.pop(rnd.choice(mondays[-61:]))               # a hole: that ETF's features drop out
        etf[e] = px
    quals, daily = [], {}
    friday = (md + timedelta(days=4)).isoformat()
    sessions = [d for d in trading_dates((md - timedelta(days=170)).isoformat(), 130) if d <= friday]
    rows = list(real or [])
    for j in range(rnd.randint(15, 35)):
        sym = rnd.choice(MAPPED) if rnd.random() < 0.3 else "Q%03d" % j
        wc = _walk(rnd, 61, rnd.uniform(3, 200), rnd.uniform(-0.01, 0.01), rnd.choice((0.02, 0.05, 0.09)))
        if rnd.random() < 0.08:
            wc[rnd.randrange(61)] = 0                        # a zero close: weekly Q-block -> daily fallback
        c = wc[-1]
        h = c * (1 + rnd.choice((0.01, 0.05, 0.12)))
        lo = c * (1 - rnd.choice((0.01, 0.04, 0.09)))
        cal = None if rnd.random() < 0.15 else round(c * rnd.uniform(0.85, 1.1), 4)
        bull = rnd.randint(2, 9)
        rows.append({"symbol": sym, "friday": friday, "monday": monday, "m2": ["GREEN"],
                     "enrich": rnd.sample(["consensus-buy", "extension-warning", "volume-thrust"], rnd.randint(1, 3)),
                     "fastState": rnd.choice(("bullish", "bearish", "mixed")), "calendarAvwap": cal, "close": c,
                     "bull": bull, "bear": rnd.randint(0, bull), "wcloses": wc,
                     "bar": {"o": c, "h": round(h, 4), "l": round(lo, 4), "c": c, "v": 1e6, "t": 0}})
    for q in rows:
        s = q["symbol"]
        if s in daily:
            continue
        n = rnd.choice((len(sessions), len(sessions), 50))
        closes = _walk(rnd, n, q["close"] or 20.0, 0.0, 0.025)
        daily[s] = [{"date": d, "o": c0, "h": round(c0 * 1.02, 4), "l": round(c0 * 0.98, 4), "c": c0, "v": 1e5}
                    for d, c0 in zip(sessions[-n:], closes)]
    for q in rows:
        quals.append(q)
    return {"monday": monday, "quals": quals, "etf_px": etf, "daily": daily}


def _real_rows():
    try:
        import tempfile
        root = tempfile.mkdtemp()
        q = m2.run_qualifiers(root)
        return q.get("asof_monday"), [r for r in q.get("qualifiers") or [] if m2._valid(r)]
    except Exception:
        return None, []


def run():
    rnd = random.Random(92)
    real_monday, real = _real_rows()
    cases = []
    if real_monday:
        cases.append(_case(rnd, real_monday, real))
    m0 = date(2026, 3, 2)
    for k in range(N_WEEKS):
        cases.append(_case(rnd, (m0 + timedelta(weeks=3 * k)).isoformat()))
    old = old_run(OLD, {"cases": cases}, timeout=3000)
    n = same = 0
    diffs = []
    counts = {"rows": 0, "real_rows": len(real), "fallback_buckets": 0, "q_lam": 0, "m_block": 0, "sect_lead": 0}

    def cmp(kind, ref, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "ref": ref, "old": a, "new": b})

    for ci, (c, o) in enumerate(zip(cases, old)):
        new = [f for _q, f in m2.compute_features(c["quals"], c["etf_px"], c["monday"],
                                                  lambda s, d=c["daily"]: d.get(s) or [])]
        for ri, (fo, fn) in enumerate(zip(o, new)):
            cmp("features", [ci, ri, c["quals"][ri]["symbol"]], fo, fn)
            counts["rows"] += 1
            counts["fallback_buckets"] += bool(fo.get("_bucket")) and c["quals"][ri]["symbol"] not in MAPPED
            counts["q_lam"] += "Q_LAM_HIGH" in fo
            counts["m_block"] += "M_DAILY_RANGE_HI" in fo
            counts["sect_lead"] += "X_SECT_LEAD" in fo
        cmp("n_rows", ci, len(o), len(new))
    res = {"sleeve": "m2_features", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:20],
           "exercised": counts, "real_monday": real_monday}
    write_receipt("m2_features", res)
    return res
