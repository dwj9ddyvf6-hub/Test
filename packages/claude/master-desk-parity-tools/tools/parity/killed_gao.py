"""killed_intraday_momentum_gao: the study's own functions (vendored intraday_momentum_2026_10_02.py: load-style
session map, eligible_days, day_returns, test2) vs the sleeve deciding at 15:30 on the same 5-minute bars.

Per case: one session (a random real trading day, half-days included) of 5-minute bars 09:30-15:55 for SPY and QQQ,
with randomly dropped bars, zero-volume windows and flat first windows. Source: eligible_days({day: map}) then
test2([r_first], [map]) -> the trade's n and gross. Sleeve: signal() at 15:30:35 on the bars completed by then ->
the tranche's direction; its gross is direction x (c[15:55] / o[15:30] - 1) on the same bars. Exact on n, direction
and gross. A day the source drops for a last-window reason (missing 15:30-15:55 bar, zero last-window volume) is
counted as the named divergence (unknowable at 15:30), not as a diff; half-days are skipped by both."""
import json
import random
import sys
from datetime import date, datetime, timedelta

from desk import calendar as cal
from desk.contract import View
from desk.sleeves.killed import intraday as IN
from desk.util import ET

from . import write_receipt

N_CASES = 2000


def gen_day(rnd):
    d0 = date(2024, 1, 2) + timedelta(days=rnd.randint(0, 900))
    while not cal.is_trading_day(d0):
        d0 += timedelta(days=1)
    if rnd.random() < 0.05:
        d0 = rnd.choice([date(2024, 11, 29), date(2025, 7, 3), date(2025, 11, 28), date(2024, 12, 24),
                         date(2025, 12, 24)])
    return d0.isoformat()


def gen_bars(rnd, day):
    close_m = cal.close_minutes(day)
    out, px = [], rnd.uniform(50, 500)
    t0 = datetime.fromisoformat(day).replace(hour=9, minute=30, tzinfo=ET).timestamp()
    flat = rnd.random() < 0.05
    zero_first, zero_last = rnd.random() < 0.03, rnd.random() < 0.03
    for k in range((close_m - 570) // 5):
        hm = 570 + 5 * k
        if rnd.random() < 0.01:
            continue                                            # a missing bar
        o = px
        c = o if (flat and hm < 600) else o * (1 + rnd.gauss(0, 0.0015))
        v = 0 if ((zero_first and hm < 600) or (zero_last and hm >= 930)) else rnd.randint(100, 5000)
        out.append({"t": t0 + 300 * k, "o": round(o, 4), "h": round(max(o, c) * 1.0005, 4),
                    "l": round(min(o, c) * 0.9995, 4), "c": round(c, 4), "v": v})
        px = c
    return out


def source_trade(G, m):
    ok, reasons = G.eligible_days({"d": m})
    if not ok:
        return None, reasons
    rf, _ = G.day_returns(m)
    s = G.test2([rf], [m])
    return {"n": s["n_trades"], "gross": s["mean_gross_per_trade"] if s["n_trades"] else None, "rf": rf}, reasons


def run(n=N_CASES, seed=20261016):
    from desk.vendor.midna_research import intraday_momentum_2026_10_02 as G
    rnd = random.Random(seed)
    diffs, stats = [], {"trades": 0, "half_days": 0, "last_window_divergence": 0, "first_window_skips": 0,
                        "flat_skips": 0}
    for case in range(n):
        day = gen_day(rnd)
        bars = {s: gen_bars(rnd, day) for s in ("SPY", "QQQ")}
        sl = IN.IntradayMomentumGao()
        now = datetime.fromisoformat(day).replace(hour=15, minute=30, second=35, tzinfo=ET).timestamp()
        if cal.close_minutes(day) != 960:
            now = datetime.fromisoformat(day).replace(hour=12, minute=31, tzinfo=ET).timestamp()
        view = View(now=now, session=day, quotes={s: {"last": 100.0, "t": now} for s in bars},
                    bars={"5m": {s: [b for b in bl if b["t"] + 300 <= now] for s, bl in bars.items()}},
                    extra={"pending_orders": [], "closed_trades": []})
        sl.signal(view)
        side = {t["sym"]: t["side"] for t in (sl._st or {}).get("tranches", [])}
        for sym, bl in bars.items():
            m = IN.day_map(bl, day)
            src, reasons = source_trade(G, m)
            mine_n = 1 if sym in side else 0
            bad = None
            if cal.close_minutes(day) != 960:
                stats["half_days"] += 1
                if mine_n:
                    bad = "traded a half-day"
                elif src is not None:
                    bad = "source traded a half-day"
                if bad:
                    diffs.append({"case": case, "day": day, "sym": sym, "bad": bad})
                continue
            if src is None:
                first_ok = IN.r_first(m) is not None
                if first_ok and (reasons["missing_bars"] or reasons["zero_volume"]):
                    stats["last_window_divergence"] += mine_n      # named: the last window is unknowable at 15:30
                    if mine_n == 0 and IN.r_first(m) != 0:
                        bad = "skipped a first-window-eligible day"
                elif mine_n:
                    bad = "traded a day the first window excludes"
                else:
                    stats["first_window_skips"] += 1
            else:
                if src["n"] != mine_n:
                    bad = f"n source {src['n']} sleeve {mine_n}"
                elif mine_n:
                    gross = side[sym] * (m["15:55"]["c"] / m["15:30"]["o"] - 1.0)
                    if gross != src["gross"]:
                        bad = f"gross source {src['gross']} sleeve {gross}"
                    stats["trades"] += 1
                else:
                    stats["flat_skips"] += 1
            if bad:
                diffs.append({"case": case, "day": day, "sym": sym, "bad": bad})
        if (case + 1) % 500 == 0:
            print(f"case {case + 1}/{n} diffs={len(diffs)}", file=sys.stderr, flush=True)
    res = {"cases": n, "identical": n - len({d["case"] for d in diffs}), "diffs": diffs[:10], "n_diffs": len(diffs),
           "stats": stats, "sleeves": ["killed_intraday_momentum_gao"],
           "explained_diffs": {"last_window_divergence": stats["last_window_divergence"]},
           "method": "vendored intraday_momentum_2026_10_02 eligible_days/day_returns/test2 vs the sleeve's 15:30 "
                     "decision on the same 5m bars (SPY + QQQ per case); n, direction and gross exact; last-window "
                     "exclusions (unknowable at 15:30) counted as the named divergence"}
    write_receipt("killed_intraday_momentum", res)
    return res


if __name__ == "__main__":
    r = run(int(sys.argv[1]) if len(sys.argv) > 1 else N_CASES)
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
