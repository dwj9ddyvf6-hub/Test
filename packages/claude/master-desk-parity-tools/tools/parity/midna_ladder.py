"""midna_qqq_csp_ladder: the original qqq-ladder.ts applyQqqLadder (entire 43f08f96) under Node vs
desk/sleeves/midna/ladder.py apply_ladder on randomized ladder books, QQQ chains, quotes and clocks.

The source's halt is off (state.halted false, no ledger break: the removed entriesHeld) and its yield day is the
clock's day (the unpaid cash yield, a named divergence, accrues nothing in the compared pass). Cases: a book (cash
$0..$1,000,000, 0..7 open short-put layers in different expirations, some rolled, with sale spots and credits), a QQQ
chain (Black-Scholes-shaped bids / asks around a random vol with a skew, strikes every $1 or $5, expirations 0..70
days out, missing / crossed / zero-bid / wide contracts; spot near or beyond 2% of the quote; today's or yesterday's;
built within or beyond 20 minutes), QQQ and VIX quotes (up / down / flat days, missing previous closes) and clocks
(regular hours before / after 10:00, after hours, expiration days, 7 / 21-DTE boundaries). Compared exactly: the
cash, the open layers in order (id, qty, entry credit x 100, expiration, strike, OCC, sale spot, credit, rolled),
the closed layers (exit price, reason), the week stamp and the told map."""
import json
import math
import random
from datetime import date, datetime, timezone

from desk.sleeves.midna import common as M
from desk.sleeves.midna import ladder as L

from . import write_receipt
from .midna_common import build, calendar_js, run_js, same, sessions_ending

N_CASES = 1500
FILES = ["src/lib/equity/qqq-ladder.ts", "src/lib/equity/option-books.ts", "src/lib/equity/options-surface.ts",
         "src/lib/equity/rules.ts", "src/lib/equity/green.ts", "src/lib/equity/kronos.ts", "src/lib/equity/types.ts"]

JS = r'''
const lad = require('./src/lib/equity/qqq-ladder.js')
const out = []
for (const c of PAYLOAD.cases) {
  const acc = lad.blankLadder('2026-01-02')
  acc.cash = c.cash
  acc.addedWeek = c.addedWeek
  acc.yieldDay = c.today
  acc.told = Object.assign({}, c.told)
  for (const p of c.positions) {
    acc.positions[p.id] = { sym: 'QQQ ' + p.strike + ' put', qty: p.qty, entryAvg: p.entryAvg, mark: p.entryAvg,
      markAt: '2026-01-02T15:00:00.000Z', entryDay: p.entryDay, openedAt: '2026-01-02T15:00:00.000Z', expiration: p.expiration,
      strike: p.strike, occ: p.occ, entrySpot: p.entrySpot, credit: p.credit, rolledUp: p.rolledUp, status: 'open' }
  }
  const state = { halted: false, ledgerBreak: null, shadow: { ladder: acc } }
  lad.applyQqqLadder(state, new Date(c.now * 1000), c.quotes, c.marks)
  const all = Object.entries(acc.positions)
  out.push({ cash: acc.cash, addedWeek: acc.addedWeek, told: acc.told || {},
    open: all.filter(([k, p]) => p.status === 'open').map(([k, p]) => [p.qty, p.entryAvg, p.expiration, p.strike, p.occ,
      p.entrySpot, p.credit, p.rolledUp]),
    closed: all.filter(([k, p]) => p.status === 'closed').map(([k, p]) => [k, p.exit.price, p.exit.reason]) })
}
console.log(JSON.stringify(out))
'''


def _iso(t):
    return datetime.fromtimestamp(t, tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _nc(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _put(spot, k, t, vol):
    d1 = (math.log(spot / k) + (0.04 + vol * vol / 2) * t) / (vol * math.sqrt(t))
    d2 = d1 - vol * math.sqrt(t)
    return k * math.exp(-0.04 * t) * _nc(-d2) - spot * _nc(-d1)


def gen_chain(rnd, spot, today, extra_exps):
    exps = set(extra_exps)
    for _ in range(rnd.randint(2, 6)):
        exps.add(M.add_days(today, rnd.randint(0, 70)))
    for d in (38, 45, 52, rnd.randint(38, 52)):
        if rnd.random() < 0.6:
            exps.add(M.add_days(today, d))
    out = {}
    step = rnd.choice([1.0, 5.0, 1.0])
    for e in sorted(exps):
        days = max(0, (date.fromisoformat(e) - date.fromisoformat(today)).days)
        t = max(days, 0.5) / 365
        base_vol = rnd.uniform(0.14, 0.35)
        strikes = sorted({round(spot * f / step) * step for f in [0.7 + 0.01 * i for i in range(36)]})
        contracts = {}
        for k in strikes:
            if rnd.random() < 0.03:
                continue
            vol = base_vol * (1 + 0.8 * max(0.0, (spot - k) / spot) * 4)
            px = max(0.0, _put(spot, k, t, vol))
            sp = max(0.01, px * rnd.choice([0.03, 0.08, 0.2, 0.6, 1.5]))
            bid, ask = round(max(0.0, px - sp / 2), 2), round(px + sp / 2, 2)
            r = rnd.random()
            if r < 0.02:
                bid, ask = ask, bid
            elif r < 0.04:
                bid = 0.0
            contracts[L.contract_key("P", k)] = {"bid": bid, "ask": ask}
        out[e] = {"strikes": strikes, "contracts": contracts}
    return out


def gen_case(rnd):
    today = rnd.choice(sessions_ending("2026-12-28", 230))
    r = rnd.random()
    mins = rnd.randint(600, M.session_close_minutes(today) - 1) if r < 0.8 else \
        (rnd.randint(570, 599) if r < 0.9 else rnd.randint(M.session_close_minutes(today), 1200))
    now = M.et_to_epoch(today, mins // 60, mins % 60, rnd.randint(0, 59))
    spot = round(rnd.uniform(380, 620), 2)
    positions, exps = [], []
    for i in range(rnd.choice([0, 1, 2, 3, 4, 5, 7])):
        e = M.add_days(today, rnd.choice([rnd.randint(-1, 60), 7, 8, 21, 22, 0]))
        if e in exps:
            continue
        exps.append(e)
        k = round(spot * rnd.uniform(0.78, 1.02))
        credit = round(rnd.uniform(0.3, 4.0), 2)
        positions.append({"id": f"qqq-ladder:{e}:{k}:2026-01-0{i + 1}T15:00:00.000Z", "qty": -3,
                          "entryAvg": M.round2(credit * 100), "entryDay": M.add_days(today, -rnd.randint(1, 40)),
                          "expiration": e, "strike": float(k), "occ": L.occ_symbol("QQQ", e, "P", k),
                          "entrySpot": round(spot * rnd.uniform(0.92, 1.05), 2), "credit": credit,
                          "rolledUp": rnd.random() < 0.2})
    calm = rnd.random() < 0.45                            # a day the ladder can act on: fresh chain, QQQ up, VIX down
    chain_spot = spot if calm else round(spot * (1 + rnd.choice([0, 0, 0, 0.001, -0.005, 0.019, -0.03])), 2)
    built = now - (rnd.choice([0, 60, 600]) if calm else rnd.choice([0, 60, 600, 1199, 1201, 2400, -30, -90]))
    name = {"spot": chain_spot, "day": today if calm or rnd.random() > 0.05 else M.add_days(today, -1), "error": None,
            "expirations": gen_chain(rnd, chain_spot, today, exps)}
    if calm:                                               # layers sold lower and richer: roll-up candidates
        for p in positions:
            if rnd.random() < 0.6:
                p["strike"] = float(round(spot * rnd.uniform(0.8, 0.93)))
                p["occ"] = L.occ_symbol("QQQ", p["expiration"], "P", p["strike"])
                p["entrySpot"] = round(spot * rnd.uniform(0.9, 0.99), 2)
                p["credit"] = round(rnd.uniform(1.0, 6.0), 2)
                p["entryAvg"] = M.round2(p["credit"] * 100)
    if rnd.random() < 0.03:
        name = {"spot": 0, "day": "", "error": "Cboe had no option chain", "expirations": {}}
    marks = {"builtAt": _iso(built), "signalAsOf": None, "names": {"QQQ": name}} if rnd.random() > 0.03 else None
    qprev = round(spot * (rnd.choice([0.99, 1.0]) if calm else rnd.choice([0.99, 1.0, 1.01, 0.995, 1.005])), 2)
    vlast = round(rnd.uniform(12, 30), 2)
    quotes = {"QQQ": {"last": spot, "previousClose": qprev if calm or rnd.random() > 0.03 else 0, "timeMs": now * 1000},
              "^VIX": {"last": vlast, "previousClose": round(vlast * (rnd.choice([1.0, 1.03]) if calm else
                                                                       rnd.choice([0.97, 1.0, 1.03])), 2),
                       "timeMs": now * 1000}}
    if not calm and rnd.random() < 0.03:
        quotes.pop("QQQ")
    cash = round(rnd.choice([1_000_000.0, rnd.uniform(0, 1_000_000), rnd.uniform(0, 200_000)]), 2)
    week = M.iso_week(today)
    return {"now": now, "today": today, "cash": cash, "positions": positions, "marks": marks, "quotes": quotes,
            "addedWeek": rnd.choice([None, week, M.iso_week(M.add_days(today, -7))]),
            "told": {"down": today} if rnd.random() < 0.1 else {}}


def port(c):
    quotes = {s: M.mq({"last": q["last"], "prev_close": q["previousClose"], "t": q["timeMs"] / 1000})
              for s, q in c["quotes"].items()}
    quotes = {s: q for s, q in quotes.items() if q}
    marks = None
    if c["marks"]:
        marks = dict(c["marks"], builtAt=datetime.fromisoformat(c["marks"]["builtAt"].replace("Z", "+00:00")).timestamp())
    acc = L.Ladder(c["cash"], [dict(p) for p in c["positions"]], c["addedWeek"], c["told"])
    L.apply_ladder(acc, c["now"], quotes, marks)
    opens = [[p["qty"], p["entryAvg"], p["expiration"], p["strike"], p["occ"], p["entrySpot"], p["credit"], p["rolledUp"]]
             for p in acc.positions]
    # listed in the book's insertion order (the source's Object.entries), not in the order they closed
    rank = {p["id"]: i for i, p in enumerate(c["positions"])}
    for o in acc.orders:
        if o["action"] == "sell_open":
            rank.setdefault(o["pos"]["id"], len(rank))
    closed = sorted([[o["id"], M.round2(o["price"] * 100), o["reason"]] for o in acc.orders
                     if o["action"] in ("buy_close", "settle")], key=lambda x: rank.get(x[0], 1e9))
    return {"cash": acc.cash, "addedWeek": acc.added_week, "told": acc.told, "open": opens, "closed": closed}


def run(n=N_CASES, seed=20261016):
    rnd = random.Random(seed)
    work = build("entire", FILES)
    diffs, stats = [], {"sold": 0, "closed": 0, "rolls": 0}
    done = 0
    while done < n:
        cases = [gen_case(rnd) for _ in range(min(150, n - done))]
        old = run_js(work, calendar_js() + JS, {"cases": cases})
        for c, o in zip(cases, old):
            p = port(c)
            stats["closed"] += len(o["closed"])
            stats["sold"] += len(o["open"]) - (len(c["positions"]) - len(o["closed"]))
            stats["rolls"] += sum(1 for x in o["closed"] if x[2].startswith("Roll"))
            if not same(p, o):
                diffs.append({"case": done, "port": p, "source": o})
            done += 1
    res = {"cases": n, "identical": n - len(diffs), "diffs": diffs[:6], "n_diffs": len(diffs), "stats": stats,
           "sleeves": ["midna_qqq_csp_ladder"],
           "method": "qqq-ladder.ts applyQqqLadder under Node (halt off; yield day = today; the source holiday table "
                     "extended with the desk calendar outside 2026) vs ladder.apply_ladder; exact"}
    write_receipt("midna_ladder", res)
    return dict(res, sleeve="midna_ladder")


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
