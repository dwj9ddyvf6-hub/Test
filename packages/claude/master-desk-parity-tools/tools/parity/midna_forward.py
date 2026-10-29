"""midna forward lab (midna_d_cyan_gbm, midna_d_green_band, midna_w_cyan_quiet_tape, midna_w_cyan_mid_vix,
midna_w_green_calm_smh, midna_w_cyan_high_adx): the original forward-scan.ts / forward.ts / gbm.ts (paper-desk
68315288) under Node vs desk/sleeves/midna/forward_scan.py fed by desk/feedlib/midna_forward_runner.mjs, on randomized
panels.

The source runs its real scanForward(panel) (its own scripts/tensor/engine.mjs + engine-extra.mjs and the frozen
model at its own paths, pinned blobs). forward.ts hitsFor is wrapped (the module export scanForward calls) to record
every scored row — symbol, daily / weekly flags, the daily and weekly feature bags, the score — before the original
runs. Compared per row: the flags, the feature-bag keys, every GBM bin (gbm.ts binsFor on the source bag vs the port's
bins_for on its bag), the score, and the final capped hits (account, symbol, score, flag text) — all exact. Feature
values are compared exactly and, when they differ, counted by their relative distance: CPython (glibc) and V8 (fdlibm)
log / exp / pow differ in the last bit on a few percent of inputs (forward_scan.py's named divergence); a value
further than 1e-12 relative, or any decision difference, is a diff."""
import json
import math
import random

from desk.feedlib import midna_forward as RUN
from desk.sleeves.midna import common as M
from desk.sleeves.midna import forward_scan as F

from . import write_receipt
from .midna_common import build, gen_series, js_panel, run_js, sessions_ending

N_CASES = 240
FILES = ["src/lib/equity/forward-scan.ts", "src/lib/equity/forward.ts", "src/lib/equity/gbm.ts",
         "src/lib/equity/context.ts", "src/lib/equity/rules.ts", "src/lib/equity/green.ts", "src/lib/equity/types.ts",
         "scripts/tensor/engine.mjs", "scripts/tensor/engine-extra.mjs",
         "quant-research/strategies/tensor_gbm_v4_1D_cyan_full.json"]
BASKET = json.load(open("desk/vendor/universes/old_desk/universe_swing_basket_v1.json"))["symbols"]

JS = r'''
const fwd = require('./src/lib/equity/forward.js')
const gbm = require('./src/lib/equity/gbm.js')
const scan = require('./src/lib/equity/forward-scan.js')
const orig = fwd.hitsFor
let rows = []
fwd.hitsFor = (row, cut) => { rows.push({ sym: row.sym, dailyCyan: row.dailyCyan, dailyGreen: row.dailyGreen,
  weeklyCyan: row.weeklyCyan, weeklyGreen: row.weeklyGreen, daily: row.daily, weekly: row.weekly, score: row.score }); return orig(row, cut) }
;(async () => {
  const model = await gbm.loadCyanModel()
  const out = []
  for (const panel of PAYLOAD.panels) {
    rows = []
    const res = await scan.scanForward(panel)
    for (const r of rows) r.bins = Array.from(gbm.binsFor(model, r.daily))
    out.push({ blocked: res.blocked, cyan: res.cyan, green: res.green, hits: res.hits, rows })
  }
  console.log(JSON.stringify(out))
})()
'''


def trend_series(rnd, n, hole):
    """a regime-switching path (trend up / down / chop, gaps on volume) so the engine prints cyan and green fires and
    the rule thresholds (dollar volume, 126-session return, price band, gap age) are crossed."""
    px = rnd.choice([rnd.uniform(6, 25), rnd.uniform(9, 22), rnd.uniform(20, 120)])
    vscale = 10 ** rnd.uniform(4.3, 6.3)
    adjf = rnd.uniform(0.9, 1.0)
    out, drift, vol = [], 0.0, rnd.uniform(0.012, 0.04)
    for _ in range(n):
        if rnd.random() < 0.03:
            drift = rnd.choice([0.006, 0.004, -0.004, 0.0, 0.002, -0.002])
            vol = rnd.uniform(0.01, 0.05)
        o = px * (1 + rnd.gauss(0, vol / 2))
        if rnd.random() < 0.01:
            o = px * (1 + rnd.choice((-1, 1)) * rnd.uniform(0.04, 0.12))
        px = max(0.5, o * (1 + rnd.gauss(drift, vol)))
        h = max(o, px) * (1 + abs(rnd.gauss(0, vol / 2)))
        lo = min(o, px) * (1 - abs(rnd.gauss(0, vol / 2)))
        prev = (out[-1]["close"] or o) if out else o
        v = float(int(vscale * rnd.lognormvariate(0, 0.5) * (3.0 if abs(o / prev - 1) >= 0.04 else 1.0)))
        if rnd.random() < hole:
            out.append({"close": 0.0, "adj": 0.0, "high": 0.0, "volume": 0.0, "low": None, "open": None})
            continue
        out.append({"close": round(px, 4), "adj": round(px * adjf, 6), "high": round(h, 4), "low": round(lo, 4),
                    "open": round(o, 4), "volume": v})
    return out


def gen_panel(rnd):
    as_of = rnd.choice(sessions_ending("2026-12-10", 150))
    if rnd.random() < 0.6:                       # a week-closing session: the weekly specs are tested
        while not M.week_just_closed(as_of):
            as_of = M.next_trading_day(as_of)
    L = rnd.randint(150, 500)
    clock = sessions_ending(as_of, L)
    universe = rnd.sample(BASKET, rnd.randint(40, 60))
    series = {}
    for s in universe + F.MARKET + ["^VIX3M"]:
        hole = rnd.choice([0.0, 0.0, 0.003, 0.02])
        series[s] = trend_series(rnd, L, hole) if not s.startswith("^") else \
            gen_series(rnd, L, vol=0.03, hole=hole, zero_vol=1.0)
        if rnd.random() < 0.03:                  # a short history (listed late)
            k = rnd.randint(10, L - 1)
            series[s] = [{"close": 0.0, "adj": 0.0, "high": 0.0, "volume": 0.0, "low": None, "open": None}] * k + series[s][k:]
    vix = [round(max(9.0, 18 + 6 * math.sin(i / 17.0) + rnd.gauss(0, 2)), 2) if rnd.random() > 0.02 else 0.0
           for i in range(L)]
    return {"asOf": as_of, "clock": clock, "series": series, "vixLast": rnd.choice([vix[-1], round(rnd.uniform(11, 30), 2)]),
            "vixPrev": vix[-2], "vixCloses": vix, "universe": universe}


def _close(a, b):
    if a == b:
        return "same"
    if isinstance(a, float) and isinstance(b, (int, float)) and math.isfinite(a):
        rel = abs(a - b) / max(abs(a), abs(b), 1e-300)
        return "ulp" if rel <= 1e-12 else "far"
    return "far"


def run(n=N_CASES, seed=20261019, batch=8):
    rnd = random.Random(seed)
    work = build("paper", FILES)
    model = F.load_model()
    diffs, stats = [], {"rows": 0, "hits": 0, "cyan_rows": 0, "weekly_rows": 0, "values": 0, "ulp_values": 0,
                        "blocked": 0}
    done = 0
    while done < n:
        panels = [gen_panel(rnd) for _ in range(min(batch, n - done))]
        old = run_js(work, JS, {"panels": [js_panel(p) for p in panels]})
        for panel, o in zip(panels, old):
            eng = RUN.run_engine(F.runner_input(panel))
            p = F.scan_forward(panel, eng, model)
            bad = []
            if p["blocked"] != o["blocked"]:
                bad.append("blocked")
            stats["blocked"] += bool(o["blocked"])
            if not o["blocked"] and not p["blocked"]:
                if (p["cyan"], p["green"]) != (o["cyan"], o["green"]):
                    bad.append("counts")
                prow = {r["sym"]: r for r in p["rows"]}
                if [r["sym"] for r in p["rows"]] != [r["sym"] for r in o["rows"]]:
                    bad.append("row_syms")
                for orow in o["rows"]:
                    r = prow.get(orow["sym"])
                    if r is None:
                        continue
                    stats["rows"] += 1
                    stats["cyan_rows"] += bool(orow["dailyCyan"])
                    stats["weekly_rows"] += bool(orow["weekly"])
                    for k in ("dailyCyan", "dailyGreen", "weeklyCyan", "weeklyGreen"):
                        if r[k] != orow[k]:
                            bad.append(f"{orow['sym']}.{k}")
                    for bag in ("daily", "weekly"):
                        if set(r[bag]) != set(orow[bag]):
                            bad.append(f"{orow['sym']}.{bag}.keys:{sorted(set(r[bag]) ^ set(orow[bag]))[:6]}")
                            continue
                        for k, v in orow[bag].items():
                            stats["values"] += 1
                            c = _close(float(r[bag][k]), v)
                            if c == "ulp":
                                stats["ulp_values"] += 1
                            elif c == "far":
                                bad.append(f"{orow['sym']}.{bag}.{k}:{r[bag][k]}!={v}")
                    if F.bins_for(model, r["daily"]) != orow["bins"]:
                        bad.append(f"{orow['sym']}.bins")
                    if (r["score"] is None) != (orow["score"] is None) or (r["score"] is not None and r["score"] != orow["score"]):
                        bad.append(f"{orow['sym']}.score")
                ph = [[h["accountId"], h["sym"], h["score"], h["flag"]] for h in p["hits"]]
                oh = [[h["accountId"], h["sym"], h["score"], h["flag"]] for h in o["hits"]]
                stats["hits"] += len(oh)
                if ph != oh:
                    bad.append("hits")
            if bad:
                diffs.append({"case": done, "asOf": panel["asOf"], "bad": bad[:12]})
            done += 1
    res = {"cases": n, "identical": n - len(diffs), "diffs": diffs[:20], "n_diffs": len(diffs), "stats": stats,
           "sleeves": ["midna_d_cyan_gbm", "midna_d_green_band", "midna_w_cyan_quiet_tape", "midna_w_cyan_mid_vix",
                       "midna_w_green_calm_smh", "midna_w_cyan_high_adx"],
           "method": "forward-scan.ts scanForward under Node (hitsFor wrapped to record rows; its own engine and model) "
                     "vs forward_scan.scan_forward over midna_forward_runner.mjs; decisions exact, feature values exact or "
                     "within 1e-12 relative (counted: ulp_values)"}
    write_receipt("midna_forward_scan", res)
    return dict(res, sleeve="midna_forward_scan")


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
