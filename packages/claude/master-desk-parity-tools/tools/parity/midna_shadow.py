"""Midna's shadow books (midna_qqq_flip5_tza, midna_w_cyan_moonshot): the original shadow.ts (lector-desk fd0e0a07)
advanceShadows under Node vs desk/sleeves/midna/shadow.py hedge_session / moonshot_step on randomized inputs.

  hedge     a random starting hedge (pending BUY / SELL / none, a TZA position of 0..25 sessions or none) driven
            through a sequence of 1..40 feed signals (new sessions, repeated sessions, a missing QQQ block, TZA opens
            or closes that are zero / missing); compared after every signal: lastSession, pending, the position
            (entry day, sessions held, qty, entry price) and signalOn
  moonshot  a random book (cash, 0..10 open names with exit times around the clock, a seen map) and a random fire list
            (fresh / seen / rejected by price or depth / held names), quotes (bid-ask, schedule, stale, crossed,
            missing) and clocks (regular hours, pre-open, after hours, weekends, holidays); compared after one step:
            the cash, the open positions (symbol, qty, time exit, key) in order, the closed names with their exit
            price, and the seen map
The exit times reach into 2027 / 2028: the source's 2026 holiday table is extended with the desk calendar's closes of
the other years (midna_common.calendar_js — the calendar is common.py's named divergence)."""
import json
import random

from desk.sleeves.midna import common as M
from desk.sleeves.midna import shadow as S

from . import write_receipt
from .midna_common import build, calendar_js, run_js, same, sessions_ending

N_HEDGE = 1000
N_MOON = 1500
FILES = ["src/lib/equity/shadow.ts", "src/lib/equity/rules.ts", "src/lib/equity/types.ts"]
BASKET = json.load(open("desk/vendor/universes/old_desk/universe_swing_basket_v1.json"))["symbols"]

JS = r'''
const shadow = require('./src/lib/equity/shadow.js')
const out = { hedge: [], moon: [] }
for (const c of PAYLOAD.hedge) {
  const state = { shadow: shadow.blankShadow([], 0) }
  const h = state.shadow.hedge
  h.lastSession = c.init.lastSession
  h.pending = c.init.pending
  if (c.init.pos) h.pos = { entryDay: c.init.pos.entryDay, entry: c.init.pos.entry, qty: c.init.pos.qty,
    notional: 30000, held: c.init.pos.held, lastMark: 30000 }
  const steps = []
  for (const sig of c.feeds) {
    shadow.advanceShadows(state, new Date(c.now * 1000), {}, { qqq: sig, moonshots: [] })
    steps.push([h.lastSession, h.pending, h.pos ? [h.pos.entryDay, h.pos.held, h.pos.qty, h.pos.entry] : null, h.signalOn])
  }
  out.hedge.push(steps)
}
for (const c of PAYLOAD.moon) {
  const state = { shadow: shadow.blankShadow([], 0) }
  const b = state.shadow.moonshot
  b.cash = c.cash
  b.seen = Object.assign({}, c.seen)
  for (const p of c.positions) {
    b.positions[p.key] = { id: p.key, sym: p.sym, lane: '1w', unit: 'moonshot', qty: p.qty, entryAvg: p.entryAvg,
      entryFill: 'bid-ask', openedAt: '2025-06-02T14:00:00.000Z', fireClose: 5, fireBar: '2025-05-26T04:00:00.000Z',
      entryBarStart: '2025-06-02T13:30:00.000Z', timeExitAt: new Date(p.timeExitAt * 1000).toISOString(),
      plan: { scheme: 'no stop / time exit 78 weeks', stopPct: null, maxBars: 78, source: 'playbook-1.0.0' },
      status: 'open', mark: p.entryAvg, markAt: '2025-06-02T14:00:00.000Z', mfe: 0, mae: 0 }
  }
  shadow.advanceShadows(state, new Date(c.now * 1000), c.quotes, { qqq: null, moonshots: c.moonshots })
  const all = Object.values(b.positions)
  out.moon.push({ cash: b.cash, seen: b.seen,
    open: all.filter((p) => p.status === 'open').map((p) => [p.sym, p.qty, Date.parse(p.timeExitAt) / 1000, p.id]),
    closed: all.filter((p) => p.status === 'closed').map((p) => [p.sym, p.exit.price]) })
}
console.log(JSON.stringify(out))
'''


def _clock(rnd, day=None):
    day = day or rnd.choice(sessions_ending("2026-12-30", 250))
    r = rnd.random()
    if r < 0.75:
        mins = rnd.randint(570, M.session_close_minutes(day) - 1)
    elif r < 0.85:
        mins = rnd.randint(560, 569)                       # pre-open
    elif r < 0.95:
        mins = rnd.randint(M.session_close_minutes(day), 1200)
    else:
        day = M.add_days(day, rnd.choice([1, 2, -1]))      # possibly a weekend / holiday
        mins = rnd.randint(540, 1000)
    return M.et_to_epoch(day, mins // 60, mins % 60, rnd.randint(0, 59))


def gen_hedge(rnd):
    days = sessions_ending("2026-12-30", 250)
    i = rnd.randrange(0, 180)
    init_pos = None
    if rnd.random() < 0.4:
        init_pos = {"entryDay": days[max(0, i - rnd.randint(0, 25))], "entry": round(rnd.uniform(5, 40), 2),
                    "qty": round(rnd.uniform(500, 6000), 6), "held": rnd.randint(0, 25)}
    init = {"lastSession": rnd.choice([None, days[i]]), "pending": rnd.choice([None, None, "BUY", "SELL"]),
            "pos": init_pos}
    feeds = []
    j = i
    for _ in range(rnd.randint(1, 40)):
        r = rnd.random()
        if r < 0.05:
            feeds.append(None)
            continue
        if r < 0.2 and feeds and feeds[-1]:
            feeds.append(dict(feeds[-1]))                  # the same session again
            continue
        j = min(len(days) - 1, j + rnd.choice([1, 1, 1, 2, 3]))
        o = round(rnd.uniform(5, 40), 2)
        sig = {"session": days[j], "slowBear": rnd.random() < 0.5, "flip5": rnd.random() < rnd.choice([0.2, 0.5, 0.9]),
               "tzaOpen": o, "tzaClose": round(o * rnd.uniform(0.95, 1.05), 2)}
        if rnd.random() < 0.04:
            sig[rnd.choice(["tzaOpen", "tzaClose"])] = rnd.choice([0, None])
        feeds.append(sig)
    return {"now": _clock(rnd), "init": init, "feeds": feeds}


def _quote(rnd, now, base):
    last = round(base * rnd.uniform(0.95, 1.05), 2)
    age = rnd.choice([0, 30, 200, 899, 901, 1000, -30, -61, -90]) if rnd.random() < 0.25 else rnd.choice([0, 60, 400])
    q = {"last": last, "previousClose": round(base, 2), "timeMs": (now - age) * 1000}
    r = rnd.random()
    if r < 0.55:
        s = rnd.uniform(0.0002, 0.02)
        q["bid"], q["ask"] = round(last * (1 - s), 2), round(last * (1 + s), 2)
    elif r < 0.6:
        q["bid"], q["ask"] = round(last * 1.01, 2), round(last * 0.99, 2)
    elif r < 0.63:
        q["last"] = 0.0
    return q


def gen_moon(rnd):
    now = _clock(rnd)
    pool = rnd.sample(BASKET, 24)
    base = {s: rnd.choice([rnd.uniform(0.5, 3), rnd.uniform(2, 15), rnd.uniform(10, 60)]) for s in pool}
    positions = []
    for s in rnd.sample(pool, rnd.randint(0, 10)):
        te = now + rnd.choice([-1, 1]) * rnd.randint(0, 40 * 86400) if rnd.random() < 0.6 else now - rnd.randint(0, 600)
        positions.append({"sym": s, "qty": rnd.randint(1, 900), "entryAvg": round(base[s] * rnd.uniform(0.5, 2), 2),
                          "timeExitAt": te, "key": f"{s}:1w:cyan:{1700000000 + rnd.randint(0, 90_000_000)}:moonshot"})
    moonshots, seen = [], {}
    for s in rnd.sample(pool, rnd.randint(0, 14)):
        key = f"{s}:1w:cyan:{1700000000 + rnd.randint(0, 90_000_000)}:moonshot"
        close = round(rnd.choice([rnd.uniform(0.3, 14.94), 14.94, 14.95, rnd.uniform(15, 30)]), 2)
        depth = rnd.choice([rnd.uniform(70.35, 99), 70.35, 70.34, rnd.uniform(20, 70)])
        moonshots.append({"key": key, "sym": s, "fireBar": "2026-05-04T04:00:00.000Z", "close": close, "depth60": depth})
        if rnd.random() < 0.15:
            seen[key] = rnd.choice(["enter", "rejected", "cash", "held"])
    for _ in range(rnd.randint(0, 5)):
        seen[f"X{rnd.randint(0, 999)}:1w:cyan:1:moonshot"] = "enter"
    quotes = {}
    for s in pool:
        if rnd.random() < 0.9:
            quotes[s] = _quote(rnd, now, base[s])
    cash = round(rnd.choice([rnd.uniform(0, 1500), rnd.uniform(0, 100000), 100000.0, rnd.uniform(0, 30)]), 2)
    return {"now": now, "cash": cash, "positions": positions, "moonshots": moonshots, "seen": seen, "quotes": quotes}


def port_hedge(c):
    init = c["init"]
    hedge = {"lastSession": init["lastSession"], "pending": init["pending"],
             "pos": dict(init["pos"]) if init["pos"] else None, "signalOn": False}
    steps = []
    for sig in c["feeds"]:
        S.hedge_session(hedge, sig)
        pos = hedge["pos"]
        steps.append([hedge["lastSession"], hedge["pending"],
                      [pos["entryDay"], pos["held"], pos["qty"], pos["entry"]] if pos else None, hedge["signalOn"]])
    return steps


def port_moon(c):
    quotes = {}
    for s, q in c["quotes"].items():
        m = M.mq({"last": q["last"], "bid": q.get("bid"), "ask": q.get("ask"), "prev_close": q.get("previousClose"),
                  "t": q["timeMs"] / 1000.0})
        if m:
            quotes[s] = m
    book = {"cash": c["cash"], "positions": [{"sym": p["sym"], "qty": p["qty"], "timeExitAt": p["timeExitAt"],
                                              "key": p["key"]} for p in c["positions"]], "seen": dict(c["seen"])}
    orders = S.moonshot_step(book, c["now"], quotes, c["moonshots"])
    return {"cash": book["cash"], "seen": book["seen"],
            "open": [[p["sym"], p["qty"], p["timeExitAt"], p["key"]] for p in book["positions"]],
            "closed": [[o["sym"], o["px"]] for o in orders if o["side"] == "sell"]}


def run(n_hedge=N_HEDGE, n_moon=N_MOON, seed=20261016):
    rnd = random.Random(seed)
    work = build("lector", FILES)
    hedge = [gen_hedge(rnd) for _ in range(n_hedge)]
    moon = [gen_moon(rnd) for _ in range(n_moon)]
    old = run_js(work, calendar_js() + JS, {"hedge": hedge, "moon": moon})
    diffs = []
    stats = {"hedge_steps": 0, "hedge_buys": 0, "hedge_sells": 0, "moon_entries": 0, "moon_exits": 0,
             "moon_rejected": 0, "moon_cash": 0}
    for k, (c, o) in enumerate(zip(hedge, old["hedge"])):
        p = port_hedge(c)
        stats["hedge_steps"] += len(p)
        prev = c["init"]["pos"] is not None
        for row in p:
            cur = row[2] is not None
            stats["hedge_buys"] += (cur and not prev) or (cur and prev and row[2][1] == 1)
            stats["hedge_sells"] += prev and not cur
            prev = cur
        if not same(p, o):
            diffs.append({"kind": "hedge", "case": k, "port": p, "source": o})
    for k, (c, o) in enumerate(zip(moon, old["moon"])):
        p = port_moon(c)
        new = {key: v for key, v in p["seen"].items() if key not in c["seen"]}
        stats["moon_entries"] += sum(v == "enter" for v in new.values())
        stats["moon_rejected"] += sum(v == "rejected" for v in new.values())
        stats["moon_cash"] += sum(v == "cash" for v in new.values())
        stats["moon_exits"] += len(p["closed"])
        if not same(p, o):
            diffs.append({"kind": "moon", "case": k, "port": p, "source": o})
    n = n_hedge + n_moon
    res = {"cases": n, "hedge_cases": n_hedge, "moonshot_cases": n_moon, "identical": n - len(diffs),
           "diffs": diffs[:10], "n_diffs": len(diffs), "stats": stats,
           "sleeves": ["midna_qqq_flip5_tza", "midna_w_cyan_moonshot"],
           "method": "shadow.ts advanceShadows under Node (the source holiday table extended with the desk calendar "
                     "outside 2026) vs shadow.hedge_session / shadow.moonshot_step; exact"}
    write_receipt("midna_shadow", res)
    return dict(res, sleeve="midna_shadow")


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
