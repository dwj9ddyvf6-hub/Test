"""Author_screens: the Author daily screens and printers vs their TypeScript sources under Node 22 (unmodified,
types erased by the TypeScript compiler; the source's clock — Date.now(), read by tape-levels' completedDailyBars —
is set per case to the case's `now`, the only stub).

  levels  Author-desk @652db7af admit-ticker.ts admitTicker (the next-support plan v1.1), washout.ts readWashout /
          readCoil / washoutBuy, tape-levels.ts fibLevels / nextLowerShelf — vs desk/sleeves/Author/levels.py
  komar   Author-desk @a4fc436c komar/screen.ts inspectName / classifyTier, proxies.ts colorHistory, size.ts
          planTicket — vs desk/sleeves/Author/komar.py
  anna    Author-desk @7683c7dd tensor/anna-replica.ts buildAnnaReplica (every replica bar: EMAs, bands, votes,
          regime, markers, printer location, signal state, glyphs) — vs desk/sleeves/Author/anna.py
Cases are deterministic random daily tapes (trends, washouts under the 50-day, coils, rips, gaps, volume
climaxes), lasts on and off the levels, clocks inside and after the session. Compared exactly (JSON null =
undefined).

    Author_DESK=<Author-desk @652db7af> PARITY_BLOBS=<blobs incl. @a4fc436c / @7683c7dd files>
        python3 -m tools.parity.run Author_screens"""
import math
import random
from datetime import datetime, timezone

from desk.sleeves.Author import anna as A
from desk.sleeves.Author import komar as K
from desk.sleeves.Author import levels as L

from . import write_receipt
from .Author_src import ANNA_COMMIT, ANNA_TS, BOOK_DATA, BOOK_TS, COMMIT, DAY_MS, KOMAR_COMMIT, KOMAR_TS, daily_bars
from .node_pinned import cleanup, run as node_run, same, stage, transpile_ts

N_LEVELS = 3000
N_KOMAR = 2000
N_ANNA = 1000
BATCH = 100

DRIVER_LEVELS = r"""
const { readFileSync } = require("node:fs");
const AT = require("./src/lib/workdesk/admit-ticker.js");
const WA = require("./src/lib/workdesk/washout.js");
const TL = require("./src/lib/workdesk/tape-levels.js");
const P = JSON.parse(readFileSync(0, "utf8"));
const out = P.cases.map((c) => {
  Date.now = () => c.now;
  const b = c.bars;
  return { admit: AT.admitTicker(c.symbol, b, c.last), wash: WA.readWashout(b, c.last), coil: WA.readCoil(b, c.last),
           buy: WA.washoutBuy(b, c.last), shelf: TL.nextLowerShelf(b, c.last), fibs: TL.fibLevels(b) };
});
console.log(JSON.stringify(out));
"""
DRIVER_KOMAR = r"""
const { readFileSync } = require("node:fs");
const S = require("./src/lib/komar/screen.js");
const X = require("./src/lib/komar/proxies.js");
const Z = require("./src/lib/komar/size.js");
const P = JSON.parse(readFileSync(0, "utf8"));
const out = P.cases.map((c) => {
  const cand = S.inspectName({ symbol: c.symbol, bars: c.bars, qqqReturn20: c.qqq });
  const tiers = c.colors.map((e) => S.classifyTier({ candidate: cand, effectiveB: e }));
  const hist = c.index ? X.colorHistory(c.index) : null;
  const plan = Z.planTicket(c.plan);
  return { cand, tiers, hist, plan };
});
console.log(JSON.stringify(out));
"""
DRIVER_ANNA = r"""
const { readFileSync } = require("node:fs");
const R = require("./src/lib/tensor/anna-replica.js");
const P = JSON.parse(readFileSync(0, "utf8"));
const out = P.cases.map((c) => R.buildAnnaReplica(c.bars).map((r) => { const o = { ...r }; delete o.bar; return o; }));
console.log(JSON.stringify(out));
"""


def _clean(x):
    if isinstance(x, float) and not math.isfinite(x):
        return None
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    return x


# -- cases -------------------------------------------------------------------------------------------------------------
def _coil_case(rnd, k):
    """search random coil-shaped tapes for one the port reads as a PPC coil (the path random walks rarely reach);
    the comparison against the source is unchanged."""
    for _ in range(400):
        bars = daily_bars(rnd, rnd.choice([80, 120, 160]), regime=rnd.choice(["coil", "chop", "drop"]))
        now = bars[-1]["t"] + 20 * 3600_000
        fibs = [f for f in L.fib_levels(bars, now) if f["r"] in (0.5, 0.618)]
        if not fibs:
            continue
        last = round(rnd.choice(fibs)["px"] * rnd.uniform(0.99, 1.01), 2)
        if L.read_coil(bars, last, now)["ok"]:
            return {"symbol": "COIL%d" % k, "bars": bars, "last": last, "now": now}
    return None


def levels_case(rnd, k):
    if rnd.random() < 0.06:
        c = _coil_case(rnd, k)
        if c:
            return c
    n = rnd.choice([0, 5, 12, 20, 25, 49, 50, 59, 60, 61, 80, 120, 200, 260, 400])
    bars = daily_bars(rnd, n, regime=rnd.choice([None, None, "drop", "coil"]))
    lastc = bars[-1]["c"] if bars else rnd.uniform(5, 50)
    now = (bars[-1]["t"] if bars else 1_790_000_000_000) + rnd.choice(
        [0, 3600_000, 5 * 3600_000, 8 * 3600_000, 12 * 3600_000, 20 * 3600_000, 3 * DAY_MS])
    x = rnd.random()
    if x < 0.05:
        last = rnd.choice([0, None, -1])
    elif x < 0.35 and bars:
        fibs = L.fib_levels(bars, now)
        pick = rnd.choice(fibs) if fibs else None
        last = round(pick["px"] * rnd.uniform(0.985, 1.015), 2) if pick else lastc
    elif x < 0.5 and len(bars) >= 21:
        e21 = L.last_ema([b["c"] for b in bars], 21)
        last = round(e21 * rnd.uniform(0.985, 1.02), 2) if e21 else lastc
    else:
        last = rnd.choice([lastc, round(lastc * rnd.uniform(0.95, 1.05), 2)])
    return {"symbol": rnd.choice(["aapl", "NVDA", "", "brk.b", "SOFI"]) + str(k % 3), "bars": bars, "last": last,
            "now": now}


def komar_case(rnd, k):
    n = rnd.choice([10, 79, 80, 120, 252, 300, 504])
    bars = daily_bars(rnd, n, regime=rnd.choice([None, "trend", "rip", "coil"]),
                      px=rnd.choice([rnd.uniform(2, 6), rnd.uniform(10, 300)]))
    if rnd.random() < 0.7:                      # liquid names (the $20M dollar-volume gate)
        for b in bars:
            b["v"] = float(int(b["v"] * rnd.uniform(5, 40)))
    for b in bars:
        b["date"] = datetime.fromtimestamp(b["t"] / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    index = None
    if rnd.random() < 0.6:
        index = daily_bars(rnd, rnd.choice([5, 25, 80, 300]), regime=rnd.choice([None, "trend", "drop", "chop"]),
                           px=rnd.uniform(10000, 20000))
        for b in index:
            b["date"] = datetime.fromtimestamp(b["t"] / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    plan = {"symbol": "X", "tier": rnd.choice(["A", "B", "reject"]), "price": rnd.choice([rnd.uniform(5, 500), 0.5]),
            "stopPct": rnd.choice([None, 0, rnd.uniform(0.01, 0.12)]),
            "deskEquity": rnd.choice([98461, 100_000.0, rnd.uniform(1e4, 1e6)]), "deployed": rnd.random() < 0.3}
    return {"symbol": "K%d" % k, "bars": bars, "qqq": rnd.choice([None, rnd.uniform(-0.15, 0.2)]),
            "colors": ["green", "yellow", "red", None], "index": index, "plan": plan}


def anna_case(rnd, k):
    if rnd.random() < 0.15:                     # several bars a session: the session VWAP resets on the ET day
        bars = daily_bars(rnd, rnd.choice([40, 120, 250]))
        out, t = [], bars[0]["t"]
        for i, b in enumerate(bars):
            out.append(dict(b, t=t))
            t += rnd.choice([3600_000, 3600_000, 20 * 3600_000])
        return {"bars": out}
    return {"bars": daily_bars(rnd, rnd.choice([0, 20, 34, 35, 36, 60, 120, 199, 200, 260, 400]),
                               regime=rnd.choice([None, None, "drop", "rip", "chop"]))}


# -- the port's side ---------------------------------------------------------------------------------------------------
def port_levels(c):
    b, last, now = c["bars"], c["last"], c["now"]
    return {"admit": L.admit_ticker(c["symbol"], b, last, now), "wash": L.read_washout(b, last, now),
            "coil": L.read_coil(b, last, now), "buy": L.washout_buy(b, last, now),
            "shelf": L.next_lower_shelf(b, last, now), "fibs": L.fib_levels(b, now)}


def port_komar(c):
    cand = K.inspect_name(c["symbol"], c["bars"], c["qqq"])
    tiers = [K.classify_tier(cand, e) for e in c["colors"]]
    strip = lambda d: {k: v for k, v in d.items() if k not in K.PORT_ONLY}
    p = c["plan"]
    return {"cand": strip(cand), "tiers": [strip(t) for t in tiers],
            "hist": K.color_history(c["index"]) if c["index"] else None,
            "plan": K.plan_ticket(p["symbol"], p["tier"], p["price"], p["stopPct"], p["deskEquity"], p["deployed"])}


def port_anna(c):
    out = []
    for r in A.build_anna_replica(c["bars"]):
        o = dict(r)
        o.pop("bar")
        out.append(o)
    return out


def _run_part(tree, driver, cases, port, diffs, label):
    ident = 0
    for i in range(0, len(cases), BATCH):
        chunk = cases[i:i + BATCH]
        theirs = node_run(tree, driver, {"cases": chunk}, name="__driver.cjs")
        for j, (c, t) in enumerate(zip(chunk, theirs)):
            d = same(_clean(port(c)), t)
            if d:
                diffs.append({"part": label, "case": i + j, "diff": [list(map(str, x)) for x in d[:5]]})
            else:
                ident += 1
    return ident


def run():
    rnd = random.Random(20261016)
    lv = [levels_case(rnd, k) for k in range(N_LEVELS)]
    km = [komar_case(rnd, k) for k in range(N_KOMAR)]
    an = [anna_case(rnd, k) for k in range(N_ANNA)]
    diffs, stats = [], {}
    trees = []
    try:
        t1 = stage("Author_DESK", "/home/user/Author-desk", dict(BOOK_TS, **BOOK_DATA))
        trees.append(t1)
        transpile_ts(t1, list(BOOK_TS))
        s1 = _run_part(t1, DRIVER_LEVELS, lv, port_levels, diffs, "levels")
        t2 = stage("Author_DESK", "/home/user/Author-desk", KOMAR_TS)
        trees.append(t2)
        transpile_ts(t2, list(KOMAR_TS))
        s2 = _run_part(t2, DRIVER_KOMAR, km, port_komar, diffs, "komar")
        t3 = stage("Author_DESK", "/home/user/Author-desk", ANNA_TS)
        trees.append(t3)
        transpile_ts(t3, list(ANNA_TS))
        s3 = _run_part(t3, DRIVER_ANNA, an, port_anna, diffs, "anna")
    finally:
        for t in trees:
            cleanup(t)
    for c in lv:
        a = port_levels(c)
        stats.setdefault("admit_tags", {}).setdefault(a["admit"]["tag"], 0)
        stats["admit_tags"][a["admit"]["tag"]] += 1
        stats.setdefault("washout_ok", 0)
        stats["washout_ok"] += int(a["wash"]["ok"])
        stats.setdefault("coil_ok", 0)
        stats["coil_ok"] += int(a["coil"]["ok"])
    for c in km:
        cand = K.inspect_name(c["symbol"], c["bars"], c["qqq"])
        for e in c["colors"]:
            tier = K.classify_tier(cand, e)["tier"]
            stats.setdefault("komar_tiers", {}).setdefault(tier, 0)
            stats["komar_tiers"][tier] += 1
    for c in an:
        for r in A.build_anna_replica(c["bars"]):
            if r["marker"]:
                stats.setdefault("anna_markers", {}).setdefault(r["marker"], 0)
                stats["anna_markers"][r["marker"]] += 1
    n = len(lv) + len(km) + len(an)
    res = {"sleeve": "Author_screens", "cases": n, "identical": s1 + s2 + s3, "diffs": diffs[:40],
           "n_diffs": len(diffs),
           "stats": dict(stats, levels_cases=len(lv), levels_identical=s1, komar_cases=len(km), komar_identical=s2,
                         anna_cases=len(an), anna_identical=s3),
           "source": {"repo": "Author-desk", "levels": {"commit": COMMIT, "files": dict(BOOK_TS, **BOOK_DATA)},
                      "komar": {"commit": KOMAR_COMMIT, "files": KOMAR_TS},
                      "anna": {"commit": ANNA_COMMIT, "files": ANNA_TS}},
           "method": "source TypeScript under Node 22 vs desk/sleeves/Author/{levels,komar,anna}.py, exact JSON "
                     "equality (Date.now set to each case's clock)",
           "sleeves": ["Author_next_support_plan", "Author_washout_ppc_coil", "Author_komar_momentum",
                       "Author_anna_seven_vote_printer"]}
    write_receipt("Author_screens", res)
    return res
