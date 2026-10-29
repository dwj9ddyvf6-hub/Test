"""midna_opt_turtle_atm_call / midna_opt_reversal_call_spread / midna_opt_distance_pair: the original option-books.ts
applyOptionBooks (paper-desk 68315288) under Node vs desk/sleeves/midna/options.py step on randomized books, signals,
listed chains, quotes and clocks.

green.ts buyBlockReason is stubbed to "no block" and state.halted is false (the removed gates). Cases: three books
(cash, 0..6 open packages each — calls with stops, call spreads, call / put pairs — with marks, skip20 / skippedFor /
wonOn maps), board signals (20 / 55-day breakouts and 10-day exits of the listed surface names and others, ATR20
values), quantpedia signals (prior-month returns, pairs with |z| around 0.5 and 2), chains per name (spot near or
beyond 2% of the quote, today's or yesterday's, built within or beyond 20 minutes; expirations 5..75 days out, strike
grids of 1 / 2.5 / 5, two-sided / one-sided / crossed / wide / missing contracts) and clocks around the session.
Compared exactly per book after the pass: the cash, the open packages in order (key, root, pair, qty, entry, mark,
expiration, legs, stop), the closed ones (exit value, reason), skip20, skippedFor and wonOn."""
import json
import math
import random
from datetime import datetime, timezone

from desk.feedlib import midna_options as P
from desk.sleeves.midna import common as M
from desk.sleeves.midna import options as O

from . import write_receipt
from .midna_common import build, calendar_js, run_js, same, sessions_ending

N_CASES = 1200
FILES = ["src/lib/equity/option-books.ts", "src/lib/equity/options-surface.ts", "src/lib/equity/green.ts",
         "src/lib/equity/kronos.ts", "src/lib/equity/rules.ts", "src/lib/equity/types.ts", "src/lib/equity/board.ts",
         "src/lib/equity/quantpedia.ts", "src/lib/equity/context.ts"]
OTHERS = ["ABCD", "WXYZ", "PLUG", "SOFI", "RIVN", "HOOD", "DKNG", "ROKU"]

JS = r'''
const ob = require('./src/lib/equity/option-books.js')
const green = require('./src/lib/equity/green.js')
green.buyBlockReason = () => null
const out = []
for (const c of PAYLOAD.cases) {
  const books = ob.blankOptionBooks(c.born)
  for (const [id, a] of Object.entries(c.accounts)) {
    const acc = books[id]
    acc.cash = a.cash
    acc.skip20 = Object.assign({}, a.skip20)
    acc.skippedFor = Object.assign({}, a.skippedFor)
    acc.wonOn = Object.assign({}, a.wonOn)
    for (const p of a.positions) {
      acc.positions[p.key] = { sym: p.sym, root: p.root, pairKey: p.pairKey ?? undefined, qty: p.qty, entryAvg: p.entryAvg,
        mark: p.mark, markAt: '2026-01-02T15:00:00.000Z', entryDay: p.entryDay, openedAt: '2026-01-02T15:00:00.000Z',
        expiration: p.expiration, legs: p.legs, stop: p.stop, status: 'open' }
    }
  }
  const state = { halted: false, shadow: { listed: books } }
  ob.applyOptionBooks(state, new Date(c.now * 1000), c.quotes, c.board, c.qp, c.marks)
  const res = {}
  for (const id of ['turtle', 'reversal', 'pairs']) {
    const acc = books[id]
    const all = Object.entries(acc.positions)
    res[id] = { cash: acc.cash, skip20: acc.skip20, skippedFor: acc.skippedFor || {}, wonOn: acc.wonOn || {},
      open: all.filter(([k, p]) => p.status === 'open').map(([k, p]) => [k, p.root, p.pairKey ?? null, p.qty, p.entryAvg, p.mark,
        p.expiration, p.legs.map((l) => [l.occ, l.root, l.right, l.strike, l.side]), p.stop]),
      closed: all.filter(([k, p]) => p.status === 'closed').map(([k, p]) => [k, p.exit.price, p.exit.reason]) }
  }
  out.push(res)
}
console.log(JSON.stringify(out))
'''


def _iso(t):
    return datetime.fromtimestamp(t, tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _clock(rnd):
    day = rnd.choice(sessions_ending("2026-12-28", 220))
    r = rnd.random()
    mins = rnd.randint(600, M.session_close_minutes(day) - 1) if r < 0.75 else \
        (rnd.randint(570, 599) if r < 0.85 else rnd.randint(M.session_close_minutes(day), 1200))
    return M.et_to_epoch(day, mins // 60, mins % 60, rnd.randint(0, 59)), day


def _chain(rnd, spot, today):
    step = rnd.choice([1.0, 2.5, 5.0]) if spot > 40 else rnd.choice([0.5, 1.0])
    exps = sorted({M.add_days(today, rnd.randint(5, 75)) for _ in range(rnd.randint(1, 5))})
    out = {}
    for e in exps:
        t = max(1, (datetime.fromisoformat(e) - datetime.fromisoformat(today)).days) / 365
        vol = rnd.uniform(0.2, 0.9)
        base = round(spot / step) * step
        strikes = sorted({round(base + k * step, 2) for k in range(-12, 13) if base + k * step > 0})
        contracts = {}
        for k in strikes:
            for right in ("C", "P"):
                if rnd.random() < 0.04:
                    continue
                d1 = (math.log(spot / k) + 0.5 * vol * vol * t) / (vol * math.sqrt(t))
                d2 = d1 - vol * math.sqrt(t)
                nc = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
                px = spot * nc(d1) - k * nc(d2) if right == "C" else k * nc(-d2) - spot * nc(-d1)
                px = max(0.01, px)
                sp = px * rnd.choice([0.02, 0.05, 0.1, 0.3, 0.8])
                bid, ask = round(max(0.0, px - sp / 2), 2), round(px + sp / 2, 2)
                r = rnd.random()
                if r < 0.03:
                    bid, ask = ask, bid
                elif r < 0.06:
                    bid = 0
                contracts[O.contract_key(right, k)] = {"bid": bid, "ask": ask}
        out[e] = {"strikes": strikes, "contracts": contracts}
    return out


def gen_case(rnd):
    now, today = _clock(rnd)
    born = rnd.choice([today, M.add_days(today, -30)])
    as_of = M.prev_trading_day(today) if rnd.random() < 0.85 else rnd.choice([today, M.add_days(today, -5)])
    names = rnd.sample(list(P.SURFACE), 8) + rnd.sample(OTHERS, 2)
    spots = {s: round(rnd.uniform(20, 500), 2) for s in names}
    bars = []
    for s in names:
        bars.append({"sym": s, "enter20": rnd.random() < 0.4, "enter55": rnd.random() < 0.2, "exit10": rnd.random() < 0.15,
                     "atr20": round(spots[s] * rnd.uniform(0.01, 0.05), 4) if rnd.random() > 0.05 else 0})
    board = {"asOf": as_of, "bars": bars} if rnd.random() > 0.05 else None
    rev = [{"sym": s, "ret": round(rnd.uniform(-0.3, 0.2), 4)} for s in names]
    pairs = []
    for _ in range(rnd.randint(0, 5)):
        a, b = rnd.sample(names, 2)
        z = rnd.choice([round(rnd.uniform(-3.5, 3.5), 3), 2.0, -2.0, 0.5, -0.49])
        pairs.append({"a": a, "b": b, "z": z, "long": rnd.choice([a, b]) if abs(z) >= 2 else None})
    qp = {"asOf": as_of, "reversal": rev, "pairs": pairs} if rnd.random() > 0.05 else None
    built = now - rnd.choice([0, 60, 600, 1199, 1201, 3000, -30, -90])
    chains = {}
    for s in names:
        if rnd.random() < 0.07:
            chains[s] = {"spot": 0, "day": "", "error": "Cboe had no option chain", "expirations": {}}
            continue
        spot = spots[s] * (1 + rnd.choice([0, 0, 0.001, -0.004, 0.019, 0.03]))
        chains[s] = {"spot": round(spot, 2), "day": today if rnd.random() > 0.05 else M.add_days(today, -1),
                     "error": None, "expirations": _chain(rnd, spot, today)}
    marks = {"builtAt": _iso(built), "signalAsOf": as_of, "names": chains} if rnd.random() > 0.03 else None
    quotes = {}
    for s in names + ["QQQ", "^VIX"]:
        last = spots.get(s, 400.0)
        quotes[s] = {"last": last, "previousClose": round(last * rnd.uniform(0.97, 1.03), 2), "timeMs": now * 1000}
    accounts = {}
    for ident, key in (("turtle", "opt-turtle"), ("reversal", "opt-reversal"), ("pairs", "opt-pairs")):
        pos = []
        for s in rnd.sample(names, rnd.randint(0, 6)):
            ch = chains[s]
            exps = list(ch["expirations"]) or [M.add_days(today, 20)]
            e = rnd.choice(exps + [today, M.add_days(today, -1)])
            strikes = (ch["expirations"].get(e) or {}).get("strikes") or [round(spots[s])]
            k = rnd.choice(strikes)
            if ident == "turtle":
                legs = [{"occ": O.occ_symbol(s, e, "C", k), "root": s, "right": "C", "strike": k, "side": "long"}]
                stop = round(spots[s] * rnd.uniform(0.9, 1.05), 2)
                pk = None
            elif ident == "reversal":
                k2 = rnd.choice(strikes)
                legs = [{"occ": O.occ_symbol(s, e, "C", k), "root": s, "right": "C", "strike": k, "side": "long"},
                        {"occ": O.occ_symbol(s, e, "C", k2), "root": s, "right": "C", "strike": k2, "side": "short"}]
                stop, pk = None, None
            else:
                rich = rnd.choice([n for n in names if n != s])
                k2 = rnd.choice(((chains[rich]["expirations"].get(e) or {}).get("strikes")) or [round(spots[rich])])
                legs = [{"occ": O.occ_symbol(s, e, "C", k), "root": s, "right": "C", "strike": k, "side": "long"},
                        {"occ": O.occ_symbol(rich, e, "P", k2), "root": rich, "right": "P", "strike": k2, "side": "long"}]
                pk = O.pair_key(s, rich) if rnd.random() < 0.7 or not pairs else O.pair_key(pairs[0]["a"], pairs[0]["b"])
                stop = None
            k_ = f"{key}:{pk or s}:{M.add_days(today, -rnd.randint(1, 40))}"
            if any(q["key"] == k_ for q in pos):
                continue                                    # one package per key (the source's book is keyed)
            pos.append({"key": k_, "sym": s, "root": s,
                        "pairKey": pk, "qty": rnd.randint(1, 30), "entryAvg": round(rnd.uniform(50, 900), 2),
                        "mark": round(rnd.uniform(0, 900), 2), "entryDay": M.add_days(today, -3), "expiration": e,
                        "legs": legs, "stop": stop})
        accounts[ident] = {"cash": round(rnd.choice([rnd.uniform(0, 3000), rnd.uniform(0, 100000), 100000.0]), 2),
                           "positions": pos,
                           "skip20": {s: rnd.random() < 0.5 for s in rnd.sample(names, rnd.randint(0, 3))},
                           "skippedFor": {s: rnd.choice([as_of, "2026-01-05"]) for s in rnd.sample(names, rnd.randint(0, 2))},
                           "wonOn": {s: rnd.choice([as_of, "2026-01-05", ""]) for s in rnd.sample(names, rnd.randint(0, 2))}}
    return {"now": now, "born": born, "board": board, "qp": qp, "marks": marks, "quotes": quotes, "accounts": accounts}


def port(c):
    quotes = {s: M.mq({"last": q["last"], "prev_close": q["previousClose"], "t": q["timeMs"] / 1000})
              for s, q in c["quotes"].items()}
    marks = None
    if c["marks"]:
        marks = dict(c["marks"], builtAt=datetime.fromisoformat(c["marks"]["builtAt"].replace("Z", "+00:00")).timestamp())
    res = {}
    for ident, key in (("turtle", "opt-turtle"), ("reversal", "opt-reversal"), ("pairs", "opt-pairs")):
        a = c["accounts"][ident]
        acc = O.Account(key, a["cash"], [dict(p) for p in a["positions"]], c["born"], a["skip20"], a["skippedFor"],
                        a["wonOn"])
        O.step(acc, c["now"], quotes, c["board"], c["qp"], marks)
        res[ident] = {"cash": acc.cash, "skip20": acc.skip20, "skippedFor": acc.skipped_for, "wonOn": acc.won_on,
                      "open": [[p["key"], p["root"], p.get("pairKey"), p["qty"], p["entryAvg"], p["mark"], p["expiration"],
                                [[l["occ"], l["root"], l["right"], l["strike"], l["side"]] for l in p["legs"]], p["stop"]]
                               for p in acc.positions],
                      "closed": sorted([[o["pos"]["key"], o["value"], o["reason"]] for o in acc.orders
                                        if o["action"] == "close"], key=lambda x: _rank(a, acc, x[0]))}
    return res


def _rank(a, acc, key):
    """the source's Object.entries order: the case's packages, then the ones opened this pass."""
    keys = [p["key"] for p in a["positions"]] + [o["pos"]["key"] for o in acc.orders if o["action"] == "open"]
    return keys.index(key) if key in keys else len(keys)


def run(n=N_CASES, seed=20261016):
    rnd = random.Random(seed)
    work = build("paper", FILES)
    diffs, stats = [], {"opens": 0, "closes": 0}
    done = 0
    while done < n:
        cases = [gen_case(rnd) for _ in range(min(100, n - done))]
        old = run_js(work, calendar_js() + JS, {"cases": cases})
        for c, o in zip(cases, old):
            p = port(c)
            for ident in p:
                stats["closes"] += len(p[ident]["closed"])
                stats["opens"] += len([x for x in p[ident]["open"] if x[0] not in {q["key"] for q in c["accounts"][ident]["positions"]}])
            if not same(p, o):
                diffs.append({"case": done, "port": p, "source": o})
            done += 1
    res = {"cases": n, "identical": n - len(diffs), "diffs": diffs[:6], "n_diffs": len(diffs), "stats": stats,
           "sleeves": list(O.IDS.values()),
           "method": "option-books.ts applyOptionBooks under Node (buyBlockReason stubbed, halted false; the source "
                     "holiday table extended with the desk calendar outside 2026) vs options.step per book; exact"}
    write_receipt("midna_options", res)
    return dict(res, sleeve="midna_options")


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
