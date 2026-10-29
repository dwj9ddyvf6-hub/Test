"""midna_turtle_s1 / midna_macd_cci / midna_ema4_vwap: the original board.ts (entire 43f08f96) under Node vs
desk/sleeves/midna/board.py on the same randomized books, signals, quotes and clocks.

The source runs its real applyBoard(state, now, quotes, signals) on the three accounts (green.ts buyBlockReason
stubbed to "no block" — the removed desk gate; halted / ledgerBreak off — the removed kill switches); the port runs
board.step on the same accounts. Compared: every open position (symbol, shares, units, entry average, last add, stop,
peak, N, ATR14, mark), the cash, and the Turtle skip bookkeeping (skip20, skippedFor, wonOn) after the pass."""
import json
import random

from desk.feedlib.midna_panel import swing_universe
from desk.sleeves.midna import board as P
from desk.sleeves.midna import common as M

from . import write_receipt
from .midna_common import build, run_js, same, sessions_ending

N_CASES = 2000
FILES = ["src/lib/equity/board.ts", "src/lib/equity/kronos.ts", "src/lib/equity/rules.ts", "src/lib/equity/green.ts",
         "src/lib/equity/types.ts"]
SIDES = ("turtle", "macd", "vwap")
FIELDS = ("sym", "qty", "units", "entryAvg", "lastAdd", "stop", "peak", "n", "atr14", "mark")

JS = r'''
const board = require('./src/lib/equity/board.js')
const green = require('./src/lib/equity/green.js')
green.buyBlockReason = () => null
const FIELDS = ['sym', 'qty', 'units', 'entryAvg', 'lastAdd', 'stop', 'peak', 'n', 'atr14', 'mark']
const out = []
for (const c of PAYLOAD.cases) {
  const books = board.blankBoard(c.born)
  for (const side of ['turtle', 'macd', 'vwap']) {
    const a = books[side], b = c.books[side]
    a.cash = b.cash
    a.skip20 = Object.assign({}, b.skip20)
    a.skippedFor = Object.assign({}, b.skippedFor)
    a.wonOn = Object.assign({}, b.wonOn)
    b.positions.forEach((p, k) => {
      a.positions[side + ':' + p.sym + ':' + k] = Object.assign({ entryDay: '2026-01-02', openedAt: '2026-01-02T15:00:00.000Z',
        markAt: '2026-01-02T15:00:00.000Z', status: 'open' }, p)
    })
  }
  const state = { halted: false, ledgerBreak: null, shadow: { board: books } }
  board.applyBoard(state, new Date(c.now * 1000), c.quotes, c.signals)
  const res = {}
  for (const side of ['turtle', 'macd', 'vwap']) {
    const a = books[side]
    res[side] = { cash: a.cash, skip20: a.skip20, skippedFor: a.skippedFor || {}, wonOn: a.wonOn || {},
      open: Object.values(a.positions).filter((p) => p.status === 'open').map((p) => FIELDS.map((f) => p[f])) }
  }
  out.push(res)
}
console.log(JSON.stringify(out))
'''

BASKET = swing_universe()


def _bar(rnd, sym):
    pick = lambda p: rnd.random() < p  # noqa: E731
    e20 = pick(0.25)
    return {"sym": sym, "close": round(rnd.uniform(5, 200), 2), "atr20": rnd.choice([0.0, round(rnd.uniform(0.2, 9), 4)]),
            "atr14": rnd.choice([0.0, round(rnd.uniform(0.2, 9), 4), round(rnd.uniform(0.2, 9), 4)]),
            "enter20": e20, "enter55": e20 and pick(0.3) or pick(0.03), "exit10": pick(0.2), "macdUp": pick(0.3),
            "macdDown": pick(0.2), "cci": round(rnd.uniform(-250, 300), 4), "vwapUp": pick(0.3), "vwapDown": pick(0.2),
            "vwapRising": pick(0.5)}


def _quote(rnd, now, base):
    last = round(base * rnd.uniform(0.9, 1.1), 2)
    age = rnd.choice([0, 30, 300, 840, 1000, -30, -100]) if rnd.random() < 0.25 else rnd.choice([0, 60, 400])
    q = {"last": last, "previousClose": round(base, 2), "timeMs": (now - age) * 1000}
    r = rnd.random()
    if r < 0.5:
        s = rnd.uniform(0.0002, 0.01)
        q["bid"], q["ask"] = round(last * (1 - s), 2), round(last * (1 + s), 2)
    elif r < 0.55:
        q["bid"], q["ask"] = round(last * 1.01, 2), round(last * 0.99, 2)
    return q


def gen_case(rnd):
    as_of = rnd.choice(sessions_ending("2026-12-15", 230))
    roll = rnd.random()
    day = M.next_trading_day(as_of) if roll < 0.75 else (as_of if roll < 0.87 else M.next_trading_day(M.next_trading_day(as_of)))
    mins = rnd.choice([rnd.randint(600, 959), rnd.randint(600, 959), rnd.randint(570, 599), rnd.randint(960, 1100),
                       rnd.randint(200, 560)])
    now = M.et_to_epoch(day, mins // 60, mins % 60, rnd.randint(0, 59))
    syms = rnd.sample(BASKET, rnd.randint(4, 30))
    signals = {"asOf": as_of, "bars": [_bar(rnd, s) for s in syms]} if rnd.random() < 0.93 else \
        rnd.choice([None, {"asOf": as_of, "bars": []}])
    born = rnd.choice([as_of, "2026-01-01", M.next_trading_day(as_of)])
    base = {s: rnd.uniform(5, 200) for s in BASKET}
    books = {}
    for side in SIDES:
        src = syms if rnd.random() < 0.7 else BASKET
        held = rnd.sample(src, min(len(src), rnd.randint(0, 5)))
        pos = []
        for s in held:
            n = round(rnd.uniform(0.3, 8), 4)
            avg = round(base[s] * rnd.uniform(0.85, 1.15), 2)
            pos.append({"sym": s, "qty": rnd.randint(1, 900), "units": rnd.randint(1, 4), "entryAvg": avg,
                        "lastAdd": round(avg * rnd.uniform(0.95, 1.1), 2),
                        "stop": round(avg - 2 * n, 4) if side == "turtle" else 0, "peak": round(avg * rnd.uniform(1, 1.3), 2),
                        "n": n, "atr14": rnd.choice([0.0, round(rnd.uniform(0.2, 8), 4)]), "mark": round(base[s], 2)})
        flags = {s: rnd.random() < 0.5 for s in rnd.sample(syms, min(len(syms), rnd.randint(0, 4)))}
        books[side] = {"cash": round(rnd.choice([rnd.uniform(0, 5000), rnd.uniform(0, 100000), 100000.0]), 2),
                       "positions": pos, "skip20": flags,
                       "skippedFor": {s: rnd.choice([as_of, "2026-01-05"]) for s in rnd.sample(syms, min(len(syms), rnd.randint(0, 3)))},
                       "wonOn": {s: rnd.choice([as_of, "2026-01-05", M.next_trading_day(as_of)]) for s in flags if flags[s]}}
    quotes = {s: _quote(rnd, now, base[s]) for s in set(syms) | {p["sym"] for b in books.values() for p in b["positions"]}
              if rnd.random() < 0.95}
    return {"now": now, "born": born, "signals": signals, "quotes": quotes, "books": books}


def port(c):
    out = {}
    quotes = {s: M.mq({"last": q["last"], "bid": q.get("bid"), "ask": q.get("ask"), "prev_close": q.get("previousClose"),
                       "t": q["timeMs"] / 1000.0}) for s, q in c["quotes"].items()}
    quotes = {s: q for s, q in quotes.items() if q}
    for side in SIDES:
        b = c["books"][side]
        acc = P.Account(side, b["cash"], [dict(p) for p in b["positions"]], b["skip20"], b["skippedFor"], b["wonOn"])
        P.step(acc, c["now"], quotes, c["signals"], c["born"])
        out[side] = {"cash": acc.cash, "skip20": acc.skip20, "skippedFor": acc.skipped_for, "wonOn": acc.won_on,
                     "open": [[p[f] for f in FIELDS] for p in acc.positions]}
    return out


def run(n=N_CASES, seed=20261018):
    rnd = random.Random(seed)
    work = build("entire", FILES)
    diffs, stats = [], {"cases_with_orders": 0}
    done = 0
    while done < n:
        cases = [gen_case(rnd) for _ in range(min(250, n - done))]
        old = run_js(work, JS, {"cases": cases})
        for c, o in zip(cases, old):
            p = port(c)
            before = {side: [[x[f] for f in FIELDS] for x in c["books"][side]["positions"]] for side in SIDES}
            stats["cases_with_orders"] += any(not same(p[s]["open"], before[s]) for s in SIDES)
            if not same(p, o):
                diffs.append({"case": done, "port": p, "source": o})
            done += 1
    res = {"cases": n, "identical": n - len(diffs), "diffs": diffs[:10], "n_diffs": len(diffs), "stats": stats,
           "sleeves": ["midna_turtle_s1", "midna_macd_cci", "midna_ema4_vwap"],
           "method": "board.ts applyBoard under Node (buyBlockReason stubbed, halt off) vs board.py step"}
    write_receipt("midna_board", res)
    return dict(res, sleeve="midna_board")


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
