"""killed_rsiobv_daily / killed_rsiobv_intraday: the studies have no committed runner for the forward rules (the daily
reassessment's script and the intraday validation pass were never committed; the scanner rsiobv.py is vendored, blob
9421874c, and called unchanged), so this harness measures the sleeves' named divergence - the windowed, incremental
scan - against a full-history batch scan with the same scanner:

  daily     rsiobv_daily_signals on the last 520 closed bars vs on the whole series up to the same bar: the Study A
            (four buckets x direction, de-overlapped >= 20 bars) and Study C (breakout F0-F4) signals of the last bar
            exact; Study B (trendline breaks within 5 bars of a de-overlapped base divergence) exact
  intraday  the RsiObvIntraday sleeve stepped pass by pass on the last 600 5-minute bars vs one scan of the whole
            series: the kept BuR RSI STRONG/SUPERSTRONG signal times (24h de-overlap, earliest kept) exact, and every
            leg's exit at the close of bar ki+24 / +48 / +96 (rsiobv_backtest.fwd_ret's convention)"""
import json
import random
import sys

from desk.contract import View
from desk.sleeves.killed import daily as DL
from desk.sleeves.killed import intraday as IN

from . import write_receipt

N_DAILY = 1000
N_INTRADAY = 30


def walk(rnd, n, step):
    c, out, t = rnd.uniform(20, 200), [], 1_700_000_000
    drift = 0.0
    for i in range(n):
        if rnd.random() < 0.02:
            drift = rnd.choice([-0.004, 0.0, 0.002, 0.006])
        o = c
        c = max(1.0, c * (1 + rnd.gauss(drift, 0.02 if step == 86400 else 0.004)))
        out.append({"t": t + step * i, "o": o, "h": max(o, c) * (1 + abs(rnd.gauss(0, 0.004))),
                    "l": min(o, c) * (1 - abs(rnd.gauss(0, 0.004))), "c": c, "v": float(rnd.randint(10_000, 900_000))})
    return out


def daily_part(n, rnd):
    diffs, stats = [], {"signals": 0, "A": 0, "B": 0, "C": 0}
    for case in range(n):
        bars = walk(rnd, rnd.randint(700, 1000), 86400)
        end = rnd.randint(600, len(bars) - 1)
        full = sorted((a, d, h) for a, d, h, _ in DL.rsiobv_daily_signals(bars[:end + 1]))
        win = sorted((a, d, h) for a, d, h, _ in DL.rsiobv_daily_signals(bars[end + 1 - 520:end + 1]))
        if full != win:
            diffs.append({"case": case, "end": end, "full": full[:6], "window": win[:6]})
        stats["signals"] += len(full)
        for a, _, _ in full:
            stats[a[0]] += 1
    return diffs, stats


def intraday_part(n, rnd):
    from desk.vendor.old_desk_research import rsiobv as R
    diffs, stats = [], {"kept": 0, "legs_closed": 0, "passes": 0, "study_vs_causal_kept_diff": 0}
    for case in range(n):
        bars = walk(rnd, 1000, 300)
        sl = IN.RsiObvIntraday()
        sl.UNIVERSE = ("MU",)
        st, start = {}, 700
        opened = {}
        for k in range(start, len(bars)):
            now = bars[k]["t"] + 300                                 # bar k has just closed
            view = View(now=now, session="2026-03-11", state=st,
                        bars={"5m": {"MU": bars[max(0, k + 1 - 600):k + 1]}}, quotes={"MU": {"last": bars[k]["c"],
                                                                                               "t": now}},
                        extra={"pending_orders": [], "closed_trades": []})
            # the sleeve's clock gate: treat every pass as inside the session (the bar grid is synthetic)
            IN.K.in_rth = lambda t: True
            try:
                sl.plan(view, st, IN.K.TrancheBook(st, view, sl.SLEEVE_ID))
            finally:
                IN.K.in_rth = _REAL_IN_RTH
            for t in st.get("tranches", []):
                if t["status"] == "planned":
                    t["status"], t["units"] = "held", 1.0            # the book took it at this pass
                    opened[t["id"]] = (t["event"], int(t["arm"].split(":")[1]), k)
                elif t["status"] == "held" and t.get("exit_day") and t["id"] in opened and len(opened[t["id"]]) == 3:
                    ev, h, k0 = opened[t["id"]]
                    opened[t["id"]] = (ev, h, k0, k)                 # the pass that closed the leg
                    t["status"] = "closed"
            stats["passes"] += 1
        # causal batch: every candidate of the whole-series scan re-classified on the bars knowable at its own bar
        # (the 600-bar prefix ending there); the study's whole-series classification is counted against it
        divs = R.scan_divergences(bars, rsi_periods=(8, 13, 21), rsi_lookbacks=(8,))
        cands = sorted({d["knowable_index"] for d in divs if d["type"] == "BuR" and d["indicator"] in ("RSI", "RSI+OBV")
                        and d["knowable_index"] > start})
        causal = []
        for i in cands:
            pre = bars[max(0, i + 1 - 600):i + 1]
            got = IN.rsiobv_bucket(R.scan_divergences(pre, rsi_periods=(8, 13, 21), rsi_lookbacks=(8,)))
            if len(pre) - 1 in got:
                causal.append(bars[i]["t"])
        kept = IN.deoverlap_time(causal)
        study = IN.deoverlap_time([bars[i]["t"] for i in sorted(IN.rsiobv_bucket(divs)) if i > start])
        stats["study_vs_causal_kept_diff"] += len(set(study) ^ set(kept))
        mine = sorted({v[0] for v in opened.values()})
        if mine != kept:
            diffs.append({"case": case, "kept_causal": kept[:5], "kept_sleeve": mine[:5]})
        idx = {b["t"]: i for i, b in enumerate(bars)}
        for ev, h, k0, *rest in opened.values():
            if rest:
                if rest[0] != idx[ev] + h:                           # exits the pass after bar ki + h closed
                    diffs.append({"case": case, "exit": [ev, h, rest[0], idx[ev] + h]})
                stats["legs_closed"] += 1
        stats["kept"] += len(kept)
    return diffs, stats


_REAL_IN_RTH = IN.K.in_rth


def run(nd=N_DAILY, ni=N_INTRADAY, seed=20261016):
    rnd = random.Random(seed)
    d1, s1 = daily_part(nd, rnd)
    d2, s2 = intraday_part(ni, rnd)
    res = {"cases": nd + ni, "identical": nd + ni - len({("d", d["case"]) for d in d1} | {("i", d["case"]) for d in d2}),
           "n_diffs": len(d1) + len(d2), "diffs": (d1 + d2)[:8], "stats": {"daily": s1, "intraday": s2},
           "sleeves": ["killed_rsiobv_daily", "killed_rsiobv_intraday"],
           "method": "no committed forward runner exists for either study; the vendored scanner (rsiobv.py) drives "
                     "both sides: daily = the sleeve's 520-bar window vs the full history at the same bar (Study "
                     "A/B/C signals of the last bar exact); intraday = the sleeve stepped pass by pass on 600-bar "
                     "windows vs one full-series scan (kept signal times and ki+k exits exact)"}
    write_receipt("killed_rsiobv", res)
    return res


if __name__ == "__main__":
    a = sys.argv[1:]
    r = run(int(a[0]) if a else N_DAILY, int(a[1]) if len(a) > 1 else N_INTRADAY)
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
