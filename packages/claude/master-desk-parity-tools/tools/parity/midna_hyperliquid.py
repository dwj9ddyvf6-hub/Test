"""midna_hyperliquid_momentum_floor: the original floor (src/lib/desk.ts handleAction with decide.ts, market.ts,
store.ts — entire 43f08f96) driven under Node through a watch tick and an immediate approve vs
desk/sleeves/midna/hyperliquid.py step, on randomized Hyperliquid books, candles and floor states.

Each case: a floor state (watch armed, cash, 0..3 open positions with stops / targets around the marks, a last scan
0..30 minutes ago or none, the day-start equity set so the removed daily loss halt never trips) and a public book
(18..30 perps: day moves around +/-1%, funding around the crowded thresholds, day notionals around $25M, the majors
present or not, delisted rows, missing marks) with hourly candles per coin (3..9 bars, or a failure). The source runs
handleAction({action: "tick"}) (exits on the marks, then the watch scan writing a pending ticket), then, if a ticket is
pending, handleAction({action: "decide", decision: "approve"}) (the door checks and the paper fill) — fetch and the
clock stubbed, its store file in a scratch cwd. Compared exactly: the open positions (coin, side, entry, stop,
target, notional, qty), the closed ones (exit price, reason), the cash and the last scan time."""
import atexit
import json
import math
import os
import random
import shutil
import tempfile

from desk.feedlib import midna_hyperliquid as F
from desk.sleeves.midna import hyperliquid as H

from . import write_receipt
from .midna_common import build, run_js, same

N_CASES = 1200
FILES = ["src/lib/desk.ts", "src/lib/decide.ts", "src/lib/format.ts", "src/lib/market.ts", "src/lib/store.ts",
         "src/lib/types.ts"]
COINS = ["BTC", "ETH", "SOL", "XRP", "DOGE", "AVAX", "LINK", "ARB", "OP", "SUI", "APT", "INJ", "TIA", "SEI", "WIF",
         "kPEPE", "HYPE", "ENA", "NEAR", "LTC", "BCH", "ADA", "DOT", "TRX", "AAVE", "UNI", "FET", "RNDR", "JUP", "ONDO"]

JS = r'''
const fs = require('fs')
const path = require('path')
const RealDate = Date
let FAKE = 0
class FakeDate extends RealDate {
  constructor(...a) { if (a.length === 0) super(FAKE); else super(...a) }
  static now() { return FAKE }
}
globalThis.Date = FakeDate
let CASE = null
globalThis.fetch = async (url, opts) => {
  const body = JSON.parse(opts.body)
  if (body.type === 'metaAndAssetCtxs') return { ok: true, status: 200, json: async () => CASE.payload }
  const c = CASE.candles[body.req.coin]
  if (c === undefined || c === null) return { ok: false, status: 500, json: async () => ({}) }
  return { ok: true, status: 200, json: async () => c }
}
const desk = require('./src/lib/desk.js')
;(async () => {
  const out = []
  const root = process.cwd()        // store.ts keeps its file under the cwd's data/desk.json
  for (const c of PAYLOAD.cases) {
    CASE = c
    FAKE = c.now * 1000
    fs.mkdirSync(path.join(root, 'data'), { recursive: true })
    fs.writeFileSync(path.join(root, 'data', 'desk.json'), JSON.stringify(c.state))
    await desk.handleAction({ action: 'tick' })
    let st = JSON.parse(fs.readFileSync(path.join(root, 'data', 'desk.json'), 'utf8'))
    const pending = st.proposals.filter((p) => p.status === 'pending')
    for (const p of pending) await desk.handleAction({ action: 'decide', proposalId: p.id, decision: 'approve' })
    st = JSON.parse(fs.readFileSync(path.join(root, 'data', 'desk.json'), 'utf8'))
    out.push({ cash: st.cashUsd, lastScanAt: st.lastScanAt ? Date.parse(st.lastScanAt) / 1000 : null,
      open: st.positions.filter((p) => p.status === 'open').map((p) => [p.coin, p.side, p.entry, p.stop, p.target, p.notionalUsd, p.qty]),
      closed: st.positions.filter((p) => p.status === 'closed').map((p) => [p.coin, p.exit, p.closeReason]) })
  }
  console.log(JSON.stringify(out))
})()
'''


def _iso(t):
    from datetime import datetime, timezone
    return datetime.fromtimestamp(t, tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def gen_case(rnd, now):
    coins = rnd.sample(COINS, rnd.randint(18, 30))
    if rnd.random() < 0.5:
        coins = [c for c in coins if c not in ("BTC", "ETH", "SOL")] or coins
    universe, ctxs, book = [], [], {}
    for c in coins:
        mark = rnd.choice([rnd.uniform(0.01, 5), rnd.uniform(5, 500), rnd.uniform(500, 100000)])
        ch = rnd.choice([rnd.uniform(-0.06, 0.06), 0.01, -0.01, rnd.uniform(-0.012, 0.012)])
        prev = mark / (1 + ch)
        f = rnd.choice([rnd.uniform(-0.00005, 0.00008), 0.00004, -0.00001, 0.0])
        dn = rnd.choice([rnd.uniform(1e6, 2e7), rnd.uniform(2.5e7, 2e9), 25_000_000.0])
        universe.append({"name": c, "maxLeverage": rnd.choice([3, 5, 10, 20, 50]),
                         **({"isDelisted": True} if rnd.random() < 0.03 else {})})
        ctxs.append({"funding": repr(f), "openInterest": repr(rnd.uniform(1e3, 1e8)),
                     "prevDayPx": repr(prev) if rnd.random() > 0.02 else "0", "dayNtlVlm": repr(dn),
                     "markPx": repr(mark)})
        book[c] = mark
    payload = [{"universe": universe}, ctxs]
    candles = {}
    for c in coins:
        if rnd.random() < 0.08:
            candles[c] = None
            continue
        rows = []
        for _ in range(rnd.randint(0, 9)):
            cc = book[c] * rnd.uniform(0.98, 1.02)
            rows.append({"t": 0, "h": repr(cc * rnd.uniform(1.0, 1.02)), "l": repr(cc * rnd.uniform(0.98, 1.0)),
                         "c": repr(cc)})
        candles[c] = rows
    positions = []
    for c in rnd.sample(coins, rnd.choice([0, 0, 1, 2, 3])):
        side = rnd.choice(["long", "short"])
        m = book[c]
        entry = m * rnd.uniform(0.97, 1.03)
        sp = rnd.uniform(0.006, 0.05)
        stop, target = H.levels(entry, side, sp)
        notional = float(rnd.randint(500, 20000))
        positions.append({"id": f"P-{c}", "coin": c, "side": side, "qty": notional / entry, "notionalUsd": notional,
                          "entry": entry, "stop": stop, "target": target, "riskUsd": notional * sp, "thesis": "t",
                          "openedAt": _iso(now - 3600), "status": "open"})
    last = rnd.choice([None, now - rnd.randint(0, 599), now - rnd.randint(600, 1800), now - 600])
    from datetime import datetime, timezone
    state = {"cashUsd": round(rnd.uniform(90000, 110000), 2),
             "dayKey": datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%d"), "dayStartEquity": 1.0,
             "halted": False, "watch": True, "lastScanAt": _iso(last) if last is not None else None,
             "lastQuietAt": None, "cooldowns": [],
             "limits": {"riskPerTradePct": 0.5, "maxOpenPositions": 3, "dailyLossHaltPct": 3, "maxGrossNotionalPct": 60,
                        "singleNameNotionalPct": 20},
             "messages": [], "proposals": [], "positions": positions,
             "seats": {s: {"phase": "idle", "note": ""} for s in ("lead", "market", "research", "strategist", "risk",
                                                                   "execution", "reviewer")}}
    return {"now": now, "payload": payload, "candles": candles, "state": state}


def port(c):
    quotes = F.parse_quotes(c["payload"])
    ranges = {}
    for coin, rows in c["candles"].items():
        if rows is None:
            ranges[coin] = None
            continue
        ranges[coin] = F.average_range_pct([{"h": F._num(r["h"]), "l": F._num(r["l"]), "c": F._num(r["c"])}
                                            for r in rows])
    st = c["state"]
    from datetime import datetime
    last = st["lastScanAt"]
    book = {"positions": {p["coin"]: {"side": p["side"], "entry": p["entry"], "stop": p["stop"], "target": p["target"],
                                      "notional": p["notionalUsd"], "qty": p["qty"]} for p in st["positions"]},
            "lastScanAt": datetime.fromisoformat(last.replace("Z", "+00:00")).timestamp() if last else None,
            "cooldowns": []}
    marks = {q["coin"]: q["mark"] for q in quotes}
    cash = st["cashUsd"]
    # the source's equity: cash + the open book at the live marks (its valuedMark), after the exits of the tick
    b2 = {"positions": dict(book["positions"]), "lastScanAt": book["lastScanAt"], "cooldowns": []}
    exits = []
    for coin, p in list(b2["positions"].items()):
        m = marks.get(coin)
        if not (m and m > 0):
            continue
        sig = H.exit_signal(p["side"], m, p["stop"], p["target"])
        if sig:
            px = H.fill_price(p["side"], m, "exit")
            cash += (px - p["entry"]) * p["qty"] if p["side"] == "long" else (p["entry"] - px) * p["qty"]
            exits.append([coin, px, sig])
    equity = cash
    for coin, p in b2["positions"].items():
        if any(e[0] == coin for e in exits):
            continue
        m = marks.get(coin)
        if m and m > 0:
            equity += (m - p["entry"]) * p["qty"] if p["side"] == "long" else (p["entry"] - m) * p["qty"]
    orders = H.step(b2, c["now"], {"quotes": quotes, "ranges": ranges, "stale": False}, equity)
    return {"cash": cash, "lastScanAt": b2["lastScanAt"],
            "open": [[k, p["side"], p["entry"], p["stop"], p["target"], p["notional"], p["qty"]]
                     for k, p in b2["positions"].items()],
            "closed": [[o["coin"], o["price"], o["reason"]] for o in orders if o["action"] == "exit"]}


def run(n=N_CASES, seed=20261016):
    rnd = random.Random(seed)
    work = build("entire", FILES)
    root = tempfile.mkdtemp(prefix="midna_hl_")
    atexit.register(shutil.rmtree, root, True)
    diffs, stats = [], {"entries": 0, "exits": 0, "scans": 0}
    done, t = 0, 1_790_000_000
    while done < n:
        cases = []
        for _ in range(min(150, n - done)):
            t += rnd.randint(4000, 90000)
            cases.append(gen_case(rnd, t))
        old = run_js(work, JS, {"cases": cases, "root": root})
        for c, o in zip(cases, old):
            p = port(c)
            stats["exits"] += len(o["closed"])
            stats["entries"] += len(o["open"]) - (len(c["state"]["positions"]) - len(o["closed"]))
            stats["scans"] += o["lastScanAt"] is not None and o["lastScanAt"] == c["now"]
            # the source keeps closed positions in its list (the order of opening); the port lists the closes
            o["closed"] = sorted(o["closed"])
            p["closed"] = sorted(p["closed"])
            if not same(p, o):
                diffs.append({"case": done, "port": p, "source": o})
            done += 1
    shutil.rmtree(root, ignore_errors=True)
    res = {"cases": n, "identical": n - len(diffs), "diffs": diffs[:6], "n_diffs": len(diffs), "stats": stats,
           "sleeves": ["midna_hyperliquid_momentum_floor"],
           "method": "desk.ts handleAction tick + approve under Node (fetch / clock stubbed; daily halt kept off) vs "
                     "hyperliquid.step; exact"}
    write_receipt("midna_hyperliquid", res)
    return dict(res, sleeve="midna_hyperliquid")


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
