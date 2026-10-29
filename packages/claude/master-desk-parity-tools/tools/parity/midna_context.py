"""midna_liquid_126_momentum: the original context.ts (paper-desk 68315288) under Node vs the port
(desk/sleeves/midna/context.py) on the same randomized panel / book / quotes / clock.

The source runs its real advanceContext(state, now, quotes, panel) and rankContext(panel). Removed gates are
neutralised on the source side, never on the port's: green.ts buyBlockReason is stubbed to "no block" (the module
export the book calls), and the cases avoid the internal freezes the port drops (VIX quote flat at 18, so no shock
freeze; clocks off Friday afternoons, the year-end window and the FOMC sessions; marks within 30% of entry, so the
40% breaker never trips) — tests/test_midna.py proves the port never applies them.

Compared per case: rankContext (names, scores, flags, eligible, overlap, combo), the staging (target, set-on day,
applied flag) and, when the review runs, every open position's shares and the book's cash after the pass (the port's
review rows replayed at their own prices = setQty)."""
import json
import random

from desk.sleeves.midna import common as M
from desk.sleeves.midna import context as P

from . import write_receipt
from .midna_common import build, gen_series, js_panel, run_js, same, sessions_ending

N_CASES = 1500
FILES = ["src/lib/equity/context.ts", "src/lib/equity/rules.ts", "src/lib/equity/green.ts", "src/lib/equity/types.ts"]
BASKET = json.load(open("desk/vendor/universes/old_desk/universe_swing_basket_v1.json"))["symbols"]
FOMC = {"2026-01-27", "2026-01-28", "2026-03-17", "2026-03-18", "2026-04-28", "2026-04-29", "2026-06-16", "2026-06-17",
        "2026-07-28", "2026-07-29", "2026-09-15", "2026-09-16", "2026-10-27", "2026-10-28", "2026-12-08", "2026-12-09",
        "2026-01-26", "2026-03-16", "2026-04-27", "2026-06-15", "2026-07-27", "2026-09-14", "2026-10-26", "2026-12-07"}

JS = r'''
const ctx = require('./src/lib/equity/context.js')
const green = require('./src/lib/equity/green.js')
green.buyBlockReason = () => null
const out = []
for (const c of PAYLOAD.cases) {
  const rank = ctx.rankContext(c.panel)
  const book = ctx.blankContext('2026-01-01T00:00:00.000Z')
  book.cash = c.cash
  book.csmomSetOn = c.set_on
  book.csmomApplied = c.applied
  book.comboApplied = true
  book.carryApplied = true
  book.target = { csmom: c.target, combo: [] }
  for (const h of c.held) {
    book.positions['csmom:' + h.sym] = { id: 'csmom:' + h.sym, sym: h.sym, sleeve: 'csmom', qty: h.qty, entryAvg: h.avg,
      openedAt: '2026-01-02T15:00:00.000Z', mark: h.mark, markAt: '2026-01-02T15:00:00.000Z', status: 'open', flag: '',
      entryCost: 0 }
  }
  const state = { halted: false, context: book }
  ctx.advanceContext(state, new Date(c.now * 1000), c.quotes, c.panel)
  const pos = {}
  for (const p of Object.values(book.positions)) if (p.status === 'open') pos[p.sym] = p.qty
  out.push({ rank, cash: book.cash, set_on: book.csmomSetOn, applied: book.csmomApplied,
             target: book.target.csmom.map((r) => r.sym), pos })
}
console.log(JSON.stringify(out))
'''


def _clock_now(rnd, as_of):
    """a clock on the session after as_of (or later / earlier for stale and pre-10:00 cases), off the removed
    freeze windows."""
    for _ in range(100):
        roll = rnd.random()
        day = M.next_trading_day(as_of) if roll < 0.85 else M.next_trading_day(M.next_trading_day(as_of))
        mins = rnd.choice([rnd.randint(570, 599), rnd.randint(600, 959), rnd.randint(600, 959), rnd.randint(600, 959),
                           rnd.randint(960, 1200), rnd.randint(300, 569)])
        if day in FOMC or day[5:7] == "12" and day[8:] >= "22":
            continue
        dt = M.et_to_epoch(day, mins // 60, mins % 60, rnd.randint(0, 59))
        if M.et_parts(dt)["weekday"] == 5 and mins >= 840:
            continue
        return dt
    return M.et_to_epoch(M.next_trading_day(as_of), 11, 0)


def gen_case(rnd):
    as_of = rnd.choice(["2026-02-13", "2026-03-20", "2026-05-07", "2026-06-10", "2026-08-21", "2026-09-30",
                        "2026-10-09", "2026-11-05", "2026-07-15", "2026-04-22"])
    L = rnd.randint(150, 520)
    clock = sessions_ending(as_of, L)
    k = rnd.randint(5, 30)
    universe = rnd.sample(BASKET, k) + (["SOXL"] if rnd.random() < 0.3 else [])
    universe = list(dict.fromkeys(universe))
    series = {s: gen_series(rnd, L) for s in universe + ["SPY", "IWM", "GLD", "TLT", "BTC-USD"]}
    panel = {"asOf": as_of, "clock": clock, "series": series, "vixLast": 18.0, "vixPrev": 18.0,
             "vixCloses": [18.0] * L, "universe": universe}
    if rnd.random() < 0.05:                              # a panel whose clock ends before asOf: stale
        panel["clock"] = clock[:-1]
        panel["series"] = {s: p[:-1] for s, p in series.items()}
    now = _clock_now(rnd, as_of)
    ranked = P.rank_context(panel)
    pool = list(dict.fromkeys([r["sym"] for r in ranked["csmom"]] + universe))
    held_syms = rnd.sample(pool, min(len(pool), rnd.randint(0, 8)))
    if rnd.random() < 0.5:
        target = [dict(r) for r in ranked["csmom"]]
    else:
        target = [{"sym": s, "score": rnd.uniform(-0.5, 2), "flag": "126-day book."}
                  for s in rnd.sample(pool, min(len(pool), rnd.randint(0, 6)))]
    set_on = rnd.choice([None, clock[-1], clock[max(0, len(clock) - 1 - rnd.randint(1, 120))], "2025-01-02"])
    applied = rnd.random() < 0.25
    quotes = {"^VIX": {"last": 18.0, "previousClose": 18.0, "timeMs": now * 1000}}
    clean = rnd.random() < 0.65                          # every quote fresh: the review runs
    for s in sorted(set(held_syms) | {r["sym"] for r in target} | {r["sym"] for r in ranked["csmom"]}):
        pts = series.get(s) or [{"close": 50.0}]
        base = next((p["close"] for p in reversed(pts) if p["close"] > 0), 50.0)
        roll = 1.0 if clean else rnd.random()
        if roll < 0.04:
            continue
        last = round(base * rnd.uniform(0.95, 1.05), 2)
        age = rnd.choice([0, 30, 200, 600, 1300, -30, -90]) if roll < 0.2 else rnd.choice([0, 15, 120, 400])
        q = {"last": last, "timeMs": (now - age) * 1000, "previousClose": round(base, 2)}
        b = rnd.random()
        if b < 0.6:
            s_ = rnd.uniform(0.0002, 0.01)
            q["bid"], q["ask"] = round(last * (1 - s_), 2), round(last * (1 + s_), 2)
        elif b < 0.65:
            q["bid"], q["ask"] = round(last * 1.01, 2), round(last * 0.99, 2)
        elif b < 0.7:
            q["ask"] = round(last * 1.003, 2)
        elif b < 0.75:
            q["bid"] = round(last * 0.997, 2)
        quotes[s] = q
    held = []
    for s in held_syms:
        q = quotes.get(s)
        mark = q["last"] if q else round(rnd.uniform(5, 100), 2)
        held.append({"sym": s, "qty": rnd.randint(1, 600), "avg": round(mark * rnd.uniform(0.75, 1.4), 2),
                     "mark": round(mark * rnd.uniform(0.98, 1.02), 2)})
    cash = round(rnd.choice([rnd.uniform(0, 5000), rnd.uniform(0, 120000), 100000.0]), 2)
    return {"panel": panel, "now": now, "held": held, "cash": cash, "set_on": set_on, "applied": applied,
            "target": target, "quotes": quotes}


def port(c):
    panel, now = c["panel"], c["now"]
    ranked = P.rank_context(panel)
    st = {"target": c["target"], "set_on": c["set_on"], "applied": c["applied"]}
    target, set_on, applied = P.stage(st, panel, ranked, now)
    pos = {h["sym"]: h["qty"] for h in c["held"]}
    cash = c["cash"]
    if P.fill_ok(now) and not P.panel_stale(panel, now) and not applied:
        held = {}
        for h in c["held"]:
            q = c["quotes"].get(h["sym"])
            held[h["sym"]] = {"qty": h["qty"], "mark": q["last"] if q and q["last"] > 0 else h["mark"]}
        plan = P.plan_review(held, cash, target, c["quotes"], now)
        if not plan["incomplete"]:
            for r in plan["rows"]:
                pos[r["sym"]] = r["qty"]
            cash = plan["cash"]
            if not target or not plan["missed"]:
                applied = True
    return {"rank": ranked, "cash": cash, "set_on": set_on, "applied": applied,
            "target": [r["sym"] for r in target], "pos": {s: q for s, q in pos.items() if q}}


def _batches(rnd, n, size=40):
    done = 0
    while done < n:
        k = min(size, n - done)
        yield [gen_case(rnd) for _ in range(k)]
        done += k


def run(n=N_CASES, seed=20261016):
    rnd = random.Random(seed)
    work = build("paper", FILES)
    diffs, stats = [], {"review_ran": 0, "staged": 0, "applied": 0}
    i = -1
    for cases in _batches(rnd, n):
        old = run_js(work, JS, {"cases": [dict(c, panel=js_panel(c["panel"])) for c in cases]})
        for c, o in zip(cases, old):
            i += 1
            _compare(i, c, o, diffs, stats)
    res = {"cases": n, "identical": n - len(diffs), "diffs": diffs[:20], "n_diffs": len(diffs), "stats": stats,
           "sleeves": ["midna_liquid_126_momentum"], "family": None,
           "method": "context.ts advanceContext + rankContext under Node (green.ts buyBlockReason stubbed; inputs off "
                     "the removed freezes) vs desk/sleeves/midna/context.py stage + plan_review"}
    write_receipt("midna_context", res)
    return dict(res, sleeve="midna_context")


def _compare(i, c, o, diffs, stats):
    if True:
        p = port(c)
        bad = [k for k in ("rank", "set_on", "applied", "target", "pos", "cash") if not same(p[k], o[k])]
        stats["staged"] += p["set_on"] != c["set_on"]
        stats["applied"] += p["applied"] and not c["applied"]
        stats["review_ran"] += p["pos"] != {h["sym"]: h["qty"] for h in c["held"]}
        if bad:
            diffs.append({"case": i, "fields": bad, "port": {k: p[k] for k in bad if k != "rank"},
                          "source": {k: o[k] for k in bad if k != "rank"}})


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
