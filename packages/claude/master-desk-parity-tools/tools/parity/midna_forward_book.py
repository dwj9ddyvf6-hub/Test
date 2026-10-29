"""The forward lab accounts: the original forward.ts advanceForward (paper-desk 68315288) under Node vs
desk/sleeves/midna/forward.py step on randomized books, hits, quotes, panels and clocks.

The source runs its real advanceForward(state, now, quotes, panel, hits) over the six accounts; green.ts
buyBlockReason is stubbed to "no block" and the inputs stay off the removed gates the port drops (a flat VIX quote at
18: no VIX freeze, no jump, no rising VIX; clocks off Friday afternoons, the year-end window and FOMC days; marks
within 30% of entry so the 40% breaker never trips; no halted account). Entry days reach back into 2025, so the
source's 2026 holiday table is extended with the desk calendar's closes of the other years (calendar_js — the
calendar is common.py's named divergence). Compared per account after the pass: the open
positions (symbol, shares, entry day, hold), the cash, the staged rows (symbol, signal day, score, flag) and the
scanned session."""
import json
import random

from desk.sleeves.midna import common as M
from desk.sleeves.midna import forward as P
from desk.sleeves.midna.forward_scan import FORWARD_SPECS

from . import write_receipt
from .midna_common import build, calendar_js, run_js, same, sessions_ending

N_CASES = 1500
FILES = ["src/lib/equity/forward.ts", "src/lib/equity/context.ts", "src/lib/equity/rules.ts", "src/lib/equity/green.ts",
         "src/lib/equity/types.ts"]
BASKET = json.load(open("desk/vendor/universes/old_desk/universe_swing_basket_v1.json"))["symbols"]
FOMC = {"2026-01-27", "2026-01-28", "2026-03-17", "2026-03-18", "2026-04-28", "2026-04-29", "2026-06-16", "2026-06-17",
        "2026-07-28", "2026-07-29", "2026-09-15", "2026-09-16", "2026-10-27", "2026-10-28", "2026-12-08", "2026-12-09"}

JS = r'''
const fwd = require('./src/lib/equity/forward.js')
const green = require('./src/lib/equity/green.js')
green.buyBlockReason = () => null
const out = []
for (const c of PAYLOAD.cases) {
  const state = { halted: false }
  const book = fwd.ensureForward(state, '2026-01-02T15:00:00.000Z')
  book.scannedAsOf = c.scanned
  for (const spec of fwd.FORWARD_SPECS) {
    const a = book.accounts[spec.id], b = c.accounts[spec.id]
    a.cash = b.cash
    a.staged = b.staged.map((r) => Object.assign({}, r))
    b.positions.forEach((p, k) => {
      const id = spec.id + ':' + p.sym
      a.positions[id] = { id, sym: p.sym, qty: p.qty, entryAvg: p.entryAvg, openedAt: '2026-01-02T15:00:00.000Z',
        signalDay: p.signalDay, entryDay: p.entryDay, holdSessions: p.holdSessions, score: p.score, flag: p.flag,
        status: 'open', mark: p.entryAvg, entrySchedule: true, markAt: '2026-01-02T15:00:00.000Z' }
    })
  }
  fwd.advanceForward(state, new Date(c.now * 1000), c.quotes, c.panel, c.hits)
  const res = { scanned: book.scannedAsOf }
  for (const spec of fwd.FORWARD_SPECS) {
    const a = book.accounts[spec.id]
    res[spec.id] = { cash: a.cash, staged: a.staged.map((r) => [r.sym, r.signalDay, r.score, r.flag]),
      open: Object.values(a.positions).filter((p) => p.status === 'open').map((p) => [p.sym, p.qty, p.entryDay, p.holdSessions]) }
  }
  out.push(res)
}
console.log(JSON.stringify(out))
'''


def _quote(rnd, now, base):
    last = round(base * rnd.uniform(0.97, 1.03), 2)
    age = rnd.choice([0, 30, 200, 899, 1000, -30, -90]) if rnd.random() < 0.2 else rnd.choice([0, 60, 400])
    q = {"last": last, "previousClose": round(base, 2), "timeMs": (now - age) * 1000}
    r = rnd.random()
    if r < 0.5:
        s = rnd.uniform(0.0002, 0.01)
        q["bid"], q["ask"] = round(last * (1 - s), 2), round(last * (1 + s), 2)
    elif r < 0.55:
        q["bid"], q["ask"] = round(last * 1.01, 2), round(last * 0.99, 2)
    return q


def gen_case(rnd):
    as_of = rnd.choice(sessions_ending("2026-12-10", 200))
    roll = rnd.random()
    day = M.next_trading_day(as_of) if roll < 0.8 else (as_of if roll < 0.9 else M.next_trading_day(M.next_trading_day(as_of)))
    for _ in range(50):
        if day not in FOMC and not (day[5:7] == "12" and day[8:] >= "22") and \
                M.next_trading_day(day) not in FOMC:
            break
        as_of = rnd.choice(sessions_ending("2026-11-20", 200))
        day = M.next_trading_day(as_of)
    mins = rnd.choice([rnd.randint(600, 959), rnd.randint(600, 959), rnd.randint(600, 959), rnd.randint(570, 599),
                       rnd.randint(960, 1150), rnd.randint(300, 560)])
    if M.et_parts(M.et_to_epoch(day, 12, 0))["weekday"] == 5 and mins >= 840:
        mins = rnd.randint(600, 839)                        # off the removed Friday-afternoon entry block
    now = M.et_to_epoch(day, mins // 60, mins % 60, rnd.randint(0, 59))
    clock = sessions_ending(as_of, 40)
    panel = {"asOf": as_of, "clock": clock if rnd.random() > 0.05 else clock[:-1],
             "series": {"SPY": [{"close": 100.0, "adj": 100.0, "high": 101.0, "volume": 1e6}] * 40},
             "vixLast": 18.0, "vixPrev": 18.0, "universe": []}
    if rnd.random() < 0.1:
        panel = None
    pool = rnd.sample(BASKET, 30)
    base = {s: rnd.uniform(4, 150) for s in pool}
    hits = None
    if rnd.random() < 0.5:
        hits = []
        for spec in FORWARD_SPECS:
            for s in rnd.sample(pool, rnd.randint(0, 8)):
                score = round(rnd.uniform(0.004, 0.03), 6) if spec["id"] == "gbm-1d-cyan" else None
                hits.append({"accountId": spec["id"], "sym": s, "score": score, "flag": f"{spec['ruleId']}. x {s}"})
    accounts = {}
    prev_days = sessions_ending(as_of, 300)
    for spec in FORWARD_SPECS:
        pos = []
        for s in rnd.sample(pool, rnd.randint(0, 6)):
            pos.append({"sym": s, "qty": rnd.randint(1, 600), "entryAvg": round(base[s] * rnd.uniform(0.8, 1.3), 2),
                        "entryDay": rnd.choice(prev_days), "holdSessions": spec["holdSessions"],
                        "signalDay": rnd.choice(prev_days), "score": None, "flag": "f"})
        staged = []
        for s in rnd.sample(pool, rnd.randint(0, 6)):
            staged.append({"sym": s, "signalDay": rnd.choice([as_of, as_of, prev_days[-2], prev_days[-3], day]),
                           "score": round(rnd.uniform(0, 0.03), 6) if rnd.random() < 0.5 else None, "flag": "g " + s})
        accounts[spec["id"]] = {"cash": round(rnd.choice([rnd.uniform(0, 4000), rnd.uniform(0, 20000), 20000.0]), 2),
                                "positions": pos, "staged": staged}
    quotes = {"^VIX": {"last": 18.0, "previousClose": 18.0, "timeMs": now * 1000}}
    for s in pool:
        if rnd.random() < 0.95:
            quotes[s] = _quote(rnd, now, base[s])
    # marks within 30% of entry: the removed 40% breaker never trips on the source
    for a in accounts.values():
        for p in a["positions"]:
            if p["sym"] in quotes:
                p["entryAvg"] = round(quotes[p["sym"]]["last"] * rnd.uniform(0.8, 1.3), 2)
    return {"now": now, "panel": panel, "hits": hits, "accounts": accounts, "quotes": quotes,
            "scanned": rnd.choice([None, as_of, prev_days[-2]])}


def port(c):
    res = {}
    scanned = c["scanned"]
    quotes = {}
    for s, q in c["quotes"].items():
        m = M.mq({"last": q["last"], "bid": q.get("bid"), "ask": q.get("ask"), "prev_close": q.get("previousClose"),
                  "t": q["timeMs"] / 1000.0})
        if m:
            quotes[s] = m
    for spec in FORWARD_SPECS:
        a = c["accounts"][spec["id"]]
        acc = {"cash": a["cash"], "positions": [dict(p) for p in a["positions"]], "staged": [dict(r) for r in a["staged"]],
               "scanned": scanned}
        P.step(spec, acc, c["now"], quotes, c["panel"], c["hits"])
        res[spec["id"]] = {"cash": acc["cash"], "staged": [[r["sym"], r["signalDay"], r["score"], r["flag"]] for r in acc["staged"]],
                           "open": [[p["sym"], p["qty"], p["entryDay"], p["holdSessions"]] for p in acc["positions"]]}
        res["scanned"] = acc["scanned"]
    return res


def run(n=N_CASES, seed=20261020):
    rnd = random.Random(seed)
    work = build("paper", FILES)
    diffs, stats = [], {"changed": 0}
    done = 0
    while done < n:
        cases = [gen_case(rnd) for _ in range(min(250, n - done))]
        old = run_js(work, calendar_js() + JS, {"cases": cases})
        for c, o in zip(cases, old):
            p = port(c)
            stats["changed"] += any(len(p[s["id"]]["open"]) != len(c["accounts"][s["id"]]["positions"]) for s in FORWARD_SPECS)
            if not same(p, o):
                diffs.append({"case": done, "port": p, "source": o})
            done += 1
    res = {"cases": n, "identical": n - len(diffs), "diffs": diffs[:10], "n_diffs": len(diffs), "stats": stats,
           "sleeves": [P.IDS[s["id"]] for s in FORWARD_SPECS],
           "method": "forward.ts advanceForward under Node (buyBlockReason stubbed; inputs off the removed entryBlock "
                     "and breaker; the source holiday table extended with the desk calendar outside 2026) vs forward.py step"}
    write_receipt("midna_forward_book", res)
    return dict(res, sleeve="midna_forward_book")


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
