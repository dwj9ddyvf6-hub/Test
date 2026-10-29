"""midna_kronos_topk: the original kronos.ts applyKronos / kronosTargets / kronosForecastDue (paper-desk 68315288) under
Node vs desk/sleeves/midna/kronos.py apply / kronos_targets and desk/feedlib/midna_kronos.py forecast_due, on randomized
books, forecasts, quotes and clocks.

green.ts buyBlockReason is stubbed to "no block" and state.halted is false (the removed gates). Cases: a book (cash,
0..6 open names of the frozen universe with entry days 0..20 sessions back, marks, a born day, an applied signal with
its targets / pending or none), a forecast (ready / running / error, a signal day 0..12 sessions back or before the
book, 20..24 scored names with ties and a non-finite score, names outside the universe), quotes (present / missing /
zero) and clocks around the session. Compared exactly: the cash, the open names in order (symbol, qty, entry price,
entry day, mark), the closed names (exit price), targets, pending, signal and applied days; and kronosForecastDue."""
import json
import random

from desk.feedlib import midna_kronos as F
from desk.sleeves.midna import common as M
from desk.sleeves.midna import kronos as K

from . import write_receipt
from .midna_common import build, calendar_js, run_js, same, sessions_ending

N_CASES = 1500
FILES = ["src/lib/equity/kronos.ts", "src/lib/equity/green.ts", "src/lib/equity/rules.ts", "src/lib/equity/types.ts"]

JS = r'''
const kr = require('./src/lib/equity/kronos.js')
const green = require('./src/lib/equity/green.js')
green.buyBlockReason = () => null
const out = []
for (const c of PAYLOAD.cases) {
  const book = kr.blankKronos(c.born + 'T12:00:00.000Z')
  book.cash = c.cash
  book.bornDay = c.born
  book.signalDay = c.signalDay
  book.appliedDay = c.appliedDay
  if (c.targets) book.targets = c.targets.slice()
  book.pending = c.pending.slice()
  for (const p of c.positions) {
    book.positions['kronos:' + p.sym + ':' + p.entryDay] = { sym: p.sym, qty: p.qty, entryAvg: p.entryAvg, entryDay: p.entryDay,
      openedAt: p.entryDay + 'T15:00:00.000Z', mark: p.mark, markAt: '2026-01-02T15:00:00.000Z', status: 'open', entryCost: 0 }
  }
  const state = { halted: false, shadow: { kronos: book } }
  kr.applyKronos(state, new Date(c.now * 1000), c.quotes, c.forecast)
  const all = Object.values(book.positions)
  out.push({ cash: book.cash, targets: book.targets ?? null, pending: book.pending, signalDay: book.signalDay,
    appliedDay: book.appliedDay,
    open: all.filter((p) => p.status === 'open').map((p) => [p.sym, p.qty, p.entryAvg, p.entryDay, p.mark]),
    closed: all.filter((p) => p.status === 'closed').map((p) => [p.sym, p.exit.price]),
    due: kr.kronosForecastDue(c.forecast, c.born, c.asOf) })
}
console.log(JSON.stringify(out))
'''


def gen_case(rnd):
    day = rnd.choice(sessions_ending("2026-12-29", 220))
    r = rnd.random()
    mins = rnd.randint(600, M.session_close_minutes(day) - 1) if r < 0.75 else \
        (rnd.randint(570, 599) if r < 0.85 else rnd.randint(M.session_close_minutes(day), 1200))
    now = M.et_to_epoch(day, mins // 60, mins % 60, rnd.randint(0, 59))
    back = sessions_ending(day, 30)
    signal = rnd.choice([back[-2], back[-2], back[-3], back[-6], back[-11], back[-12], day])
    born = rnd.choice([back[0], back[-15], signal, M.add_days(signal, 1)])
    uni = list(K.UNIVERSE)
    scores = []
    for s in rnd.sample(uni + ["XYZ", "QQQX"], rnd.randint(20, 24)):
        sc = rnd.choice([round(rnd.uniform(-0.08, 0.08), 6), 0.01, 0.01])
        scores.append({"sym": s, "score": sc, "lastClose": 50.0, "forecastClose": 50.5})
    status = rnd.choice(["ready"] * 8 + ["running", "error"])
    forecast = {"status": status, "signalDay": signal if rnd.random() > 0.03 else None, "model": "m", "scores": scores,
                "error": None, "note": "n"} if rnd.random() > 0.05 else None
    positions = []
    for s in rnd.sample(uni, rnd.randint(0, 6)):
        positions.append({"sym": s, "qty": rnd.randint(1, 900), "entryAvg": round(rnd.uniform(20, 300), 2),
                          "entryDay": rnd.choice(back[-21:]), "mark": round(rnd.uniform(20, 300), 2)})
    quotes = {}
    for s in uni:
        if rnd.random() < 0.92:
            quotes[s] = {"last": round(rnd.uniform(15, 320), 2) if rnd.random() > 0.02 else 0,
                         "previousClose": 50.0, "timeMs": now * 1000}
    applied = rnd.choice([None, signal, back[-12]])
    targets = rnd.sample(uni, 4) if applied and rnd.random() < 0.7 else None
    return {"now": now, "born": born, "cash": round(rnd.choice([rnd.uniform(0, 100000), 100000.0, rnd.uniform(0, 500)]), 2),
            "signalDay": applied, "appliedDay": applied, "targets": targets,
            "pending": rnd.sample(uni, rnd.randint(0, 2)), "positions": positions, "quotes": quotes,
            "forecast": forecast, "asOf": M.last_completed_session(now)}


def port(c):
    quotes = {s: M.mq({"last": q["last"], "prev_close": q["previousClose"], "t": q["timeMs"] / 1000})
              for s, q in c["quotes"].items()}
    book = {"cash": c["cash"], "positions": [dict(p) for p in c["positions"]], "bornDay": c["born"],
            "signalDay": c["signalDay"], "appliedDay": c["appliedDay"],
            "targets": list(c["targets"]) if c["targets"] else None, "pending": list(c["pending"])}
    orders = K.apply(book, c["now"], {k: v for k, v in quotes.items() if v}, c["forecast"])
    return {"cash": book["cash"], "targets": book["targets"], "pending": book["pending"],
            "signalDay": book["signalDay"], "appliedDay": book["appliedDay"],
            "open": [[p["sym"], p["qty"], p["entryAvg"], p["entryDay"], p["mark"]] for p in book["positions"]],
            "closed": [[o["sym"], o["px"]] for o in orders if o["side"] == "sell"],
            "due": F.forecast_due(c["forecast"], c["born"], c["asOf"])}


def run(n=N_CASES, seed=20261016):
    rnd = random.Random(seed)
    work = build("paper", FILES)
    diffs, stats = [], {"buys": 0, "sells": 0, "due": 0}
    done = 0
    while done < n:
        cases = [gen_case(rnd) for _ in range(min(300, n - done))]
        old = run_js(work, calendar_js() + JS, {"cases": cases})
        for c, o in zip(cases, old):
            p = port(c)
            stats["sells"] += len(o["closed"])
            stats["buys"] += len(o["open"]) - (len(c["positions"]) - len(o["closed"]))
            stats["due"] += bool(o["due"])
            if not same(p, o):
                diffs.append({"case": done, "port": p, "source": o})
            done += 1
    res = {"cases": n, "identical": n - len(diffs), "diffs": diffs[:6], "n_diffs": len(diffs), "stats": stats,
           "sleeves": ["midna_kronos_topk"],
           "method": "kronos.ts applyKronos + kronosForecastDue under Node (buyBlockReason stubbed, halted false; the "
                     "source holiday table extended with the desk calendar outside 2026) vs kronos.apply / "
                     "midna_kronos.forecast_due; exact"}
    write_receipt("midna_kronos", res)
    return dict(res, sleeve="midna_kronos")


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
