"""midna_hourly_playbook: the original rules.ts evaluatePass (lector-desk fd0e0a07) under Node, its fires parsed by
fires.ts parseInboxFire, vs desk/sleeves/midna/hourly.py parse_inbox_fire + step on randomized books, inbox fires,
dv20 maps, quotes and clocks.

Cases: a book (cash, 0..22 open positions on the three lanes with stop / no-stop plans and time exits around the
clock, a seen map, setup episodes, capacity waits) and 0..14 inbox fires (1H basket fires at hour-bar starts around
the clock, 1D / 1W calibrated fires, tags that hit or miss the killed list, missing / false gap20 and
first-of-setup flags, non-Yahoo bar sources, untradeable fires, duplicated episodes), dv20 values on both sides of
$1,000,000 and of the $500,000 that caps the slot, quotes (bid-ask, schedule, stale, ahead of the clock, crossed,
beyond the limit band) and clocks (regular hours, pre-open, after hours, weekends and holidays). state.halted is
false (the removed kill switch). Compared after the pass: the cash, the open positions in order (id, symbol, lane,
unit, qty, entry price, entry fill kind, entry bar start, time exit, plan), the closed positions with their exit
price, the seen map (action and reason per key), the episodes and the capacity waits — exact."""
import json
import random

from desk.sleeves.midna import common as M
from desk.sleeves.midna import hourly as H

from . import write_receipt
from .midna_common import build, calendar_js, run_js, same, sessions_ending

N_CASES = 1500
FILES = ["src/lib/equity/rules.ts", "src/lib/equity/fires.ts", "src/lib/equity/types.ts"]
BASKET = json.load(open("desk/vendor/universes/old_desk/universe_swing_basket_v1.json"))["symbols"]

JS = r'''
const rules = require('./src/lib/equity/rules.js')
const fires = require('./src/lib/equity/fires.js')
const out = []
for (const c of PAYLOAD.cases) {
  const positions = {}
  for (const p of c.positions) {
    positions[p.id] = { id: p.id, sym: p.sym, lane: p.lane, unit: p.unit, qty: p.qty, entryAvg: p.entryAvg,
      entryFill: p.entryFill, openedAt: '2026-01-02T15:00:00.000Z', fireClose: p.fireClose, fireBar: p.fireBar,
      entryBarStart: new Date(p.entryBarStart * 1000).toISOString(), timeExitAt: new Date(p.timeExitAt * 1000).toISOString(),
      plan: p.plan, status: 'open', mark: null, markAt: null, mfe: 0, mae: 0 }
  }
  const state = { version: 'equity-paper 1.0.0', playbook: '1.0.0', desk: 'paper-desk 1.5.0', cash: c.cash, halted: false,
    positions, seen: Object.fromEntries(Object.entries(c.seen).map(([k, v]) => [k, { action: v, at: '2026-01-02T15:00:00.000Z' }])),
    capacityWait: Object.assign({}, c.capacityWait), episodes: Object.assign({}, c.episodes), beliefs: rules.blankBeliefs(),
    lines: [], passes: 0, lastPassAt: null, dayAnchor: null,
    checkpoint: { pdfEquity: 0, reconstructed: 1, note: '' }, ledgerHead: '0', ledgerSeq: 0, lastQuoteError: null,
    trackerAsOf: null }
  const fs = c.inbox.map((raw) => fires.parseInboxFire(raw)).filter(Boolean)
  const res = rules.evaluatePass(state, { now: new Date(c.now * 1000), quotes: c.quotes, fires: fs, dv20: c.dv20,
    quoteError: null, trackerAsOf: null })
  const s = res.state
  const all = Object.values(s.positions)
  out.push({ cash: s.cash,
    open: all.filter((p) => p.status === 'open').map((p) => [p.id, p.sym, p.lane, p.unit, p.qty, p.entryAvg, p.entryFill || null,
      Date.parse(p.entryBarStart) / 1000, Date.parse(p.timeExitAt) / 1000, p.plan]),
    closed: all.filter((p) => p.status === 'closed').map((p) => [p.id, p.exit.price, p.exit.reason]),
    seen: Object.fromEntries(Object.entries(s.seen).map(([k, v]) => [k, [v.action, v.reason ?? null]])),
    episodes: s.episodes, capacityWait: s.capacityWait })
}
console.log(JSON.stringify(out))
'''


def _iso_utc(t):
    from datetime import datetime, timezone
    return datetime.fromtimestamp(int(t), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _clock(rnd):
    day = rnd.choice(sessions_ending("2026-12-29", 240))
    r = rnd.random()
    if r < 0.75:
        mins = rnd.randint(570, M.session_close_minutes(day) - 1)
    elif r < 0.85:
        mins = rnd.randint(555, 569)
    elif r < 0.95:
        mins = rnd.randint(M.session_close_minutes(day), 1250)
    else:
        day = M.add_days(day, rnd.choice([1, 2, -1]))
        mins = rnd.randint(540, 1000)
    return M.et_to_epoch(day, mins // 60, mins % 60, rnd.randint(0, 59)), day


def _bar_start(rnd, now):
    """an hourly bar start (09:30 .. 15:30 ET) of a session within a few days before the clock (or just after)."""
    d = M.et_ymd(now)
    back = rnd.choice([0, 0, 0, 1, 1, 2, 3])
    for _ in range(back):
        d = M.add_days(d, -1)
        while not M.is_trading_day(d):
            d = M.add_days(d, -1)
    if not M.is_trading_day(d):
        d = M.add_days(d, -1)
        while not M.is_trading_day(d):
            d = M.add_days(d, -1)
    close = M.session_close_minutes(d)
    starts = list(range(570, close, 60))
    m = rnd.choice(starts)
    return M.et_to_epoch(d, m // 60, m % 60)


def _quote(rnd, now, base):
    last = round(base * rnd.uniform(0.97, 1.06), 2)
    age = rnd.choice([0, 30, 200, 899, 901, 1000, -30, -61]) if rnd.random() < 0.2 else rnd.choice([0, 60, 400])
    q = {"last": last, "previousClose": round(base, 2), "timeMs": (now - age) * 1000}
    r = rnd.random()
    if r < 0.55:
        s = rnd.uniform(0.0002, 0.01)
        q["bid"], q["ask"] = round(last * (1 - s), 2), round(last * (1 + s), 2)
    elif r < 0.6:
        q["bid"], q["ask"] = round(last * 1.01, 2), round(last * 0.99, 2)
    return q


KILLED_TAGS = ["rsi-obv", "raschke", "midna-20d", "in:1h-basket", "sector:tech", "red-day-policy", "x", "alt-exit"]


def gen_case(rnd):
    now, day = _clock(rnd)
    anchor = None
    if rnd.random() < 0.6:                               # a clock inside the entry window of an hour bar's fires
        d = rnd.choice(sessions_ending("2026-12-29", 240))
        m = rnd.choice(list(range(570, M.session_close_minutes(d) - 60, 60)))
        anchor = M.et_to_epoch(d, m // 60, m % 60)
        now = anchor + 3600 + rnd.randint(0, 1860)
    pool = rnd.sample(BASKET, 30)
    base = {s: rnd.choice([rnd.uniform(1, 5), rnd.uniform(5, 20), rnd.uniform(20, 300)]) for s in pool}
    positions = []
    for s in rnd.sample(pool, rnd.choice([0, 1, 3, 5, 8, 12, 22])):
        lane = rnd.choice(["1h", "1h", "1d", "1w"])
        stop = rnd.choice([None, 15, 10.5, 99, 120]) if rnd.random() < 0.7 else None
        mb = 60 if lane == "1h" else rnd.choice([40, 52, 20])
        plan = {"scheme": "p", "stopPct": stop, "maxBars": mb, "source": rnd.choice(["playbook-1.0.0", "calibrated"])}
        ebs = now - rnd.randint(0, 40 * 86400)
        te = now + rnd.choice([-1, 1]) * rnd.randint(0, 10 * 86400) if rnd.random() < 0.7 else now - rnd.randint(0, 900)
        positions.append({"id": f"{s}:{lane}:k{rnd.randint(1, 99999)}", "sym": s, "lane": lane, "unit": "1h-basket",
                          "qty": rnd.randint(1, 900), "entryAvg": round(base[s] * rnd.uniform(0.7, 1.3), 2),
                          "entryFill": rnd.choice(["bid-ask", "schedule"]), "fireClose": round(base[s], 2),
                          "fireBar": "2026-01-02T15:30:00.000Z", "entryBarStart": ebs, "timeExitAt": te, "plan": plan})
    inbox, seen, episodes, cap = [], {}, {}, {}
    for _ in range(rnd.randint(0, 14)):
        s = rnd.choice(pool + [p["sym"] for p in positions][:3])
        lane = rnd.choice(["1h", "1h", "1h", "1d", "1w"])
        fb = _bar_start(rnd, now) if lane == "1h" else M.et_to_epoch(M.et_ymd(now - rnd.randint(0, 3) * 86400), 9, 30)
        if lane == "1h" and anchor is not None and rnd.random() < 0.7:
            fb = anchor
        unit = "1h-basket" if lane == "1h" and rnd.random() < 0.85 else rnd.choice(["1h-E22", "1d-G4", "1w-C-PX15"])
        key = f"{s}:{lane}:swing:{int(fb)}:confirmed:{rnd.randint(0, 9)}"
        raw = {"key": key, "sym": s, "lane": lane, "unit": unit, "fireBar": _iso_utc(fb),
               "fireClose": round(base[s] * rnd.uniform(0.98, 1.05), 2), "detectedAt": _iso_utc(now),
               "tradeable": rnd.random() < 0.92, "barSource": rnd.choice(["yahoo:canonical"] * 9 + ["alpaca:iex"]),
               "tags": rnd.sample(KILLED_TAGS, rnd.choice([0, 1, 1, 2])), "maxBars": 60}
        r = rnd.random()
        if r < 0.85:
            raw["gap20"], raw["firstOfSetup"] = True, True
        elif r < 0.92:
            raw["gap20"], raw["firstOfSetup"] = rnd.choice([(True, False), (False, True)])
        if lane != "1h":
            raw["stopPct"] = rnd.choice([None, 12, 15.5])
            raw["maxBars"] = rnd.choice([None, 40, 52, 8])
        if rnd.random() < 0.2:
            raw["metaDecile"] = rnd.randint(1, 10)
            raw["score"] = round(rnd.uniform(0, 5), 3)
        if rnd.random() < 0.05:
            raw.pop("unit")
        if rnd.random() < 0.1:
            seen[key] = "skip"
        if rnd.random() < 0.05:
            episodes[f"{s}:{lane}:{unit}:{_iso_utc(fb)}"] = "other"
        if rnd.random() < 0.1:
            cap[key] = rnd.randint(1, 4)
        inbox.append(raw)
    dv20 = {}
    for s in pool:
        r = rnd.random()
        dv20[s] = None if r < 0.08 else rnd.choice([rnd.uniform(1e5, 9.9e5), rnd.uniform(1e6, 5e5 * 4),
                                                     rnd.uniform(5e5, 1e9), 1_000_000.0])
    quotes = {}
    for s in pool:
        if rnd.random() < 0.93:
            quotes[s] = _quote(rnd, now, base[s])
    cash = round(rnd.choice([rnd.uniform(0, 5000), rnd.uniform(0, 100000), 100000.0, rnd.uniform(4400, 4600)]), 2)
    return {"now": now, "cash": cash, "positions": positions, "inbox": inbox, "seen": seen, "episodes": episodes,
            "capacityWait": cap, "dv20": dv20, "quotes": quotes}


def port(c):
    quotes = {}
    for s, q in c["quotes"].items():
        m = M.mq({"last": q["last"], "bid": q.get("bid"), "ask": q.get("ask"), "prev_close": q.get("previousClose"),
                  "t": q["timeMs"] / 1000.0})
        if m:
            quotes[s] = m
    book = {"cash": c["cash"], "positions": [dict(p) for p in c["positions"]],
            "seen": {k: {"action": v} for k, v in c["seen"].items()}, "episodes": dict(c["episodes"]),
            "capacityWait": dict(c["capacityWait"])}
    fires = [f for f in (H.parse_inbox_fire(r) for r in c["inbox"]) if f]
    orders = H.step(book, c["now"], quotes, fires, c["dv20"])
    return {"cash": book["cash"],
            "open": [[p["id"], p["sym"], p["lane"], p["unit"], p["qty"], p["entryAvg"], p.get("entryFill"),
                      p["entryBarStart"], p["timeExitAt"], p["plan"]] for p in book["positions"]],
            "closed": [[o["id"], o["px"], o["reason"]] for o in orders if o["side"] == "sell"],
            "seen": {k: [v["action"], v.get("reason")] for k, v in book["seen"].items()},
            "episodes": book["episodes"], "capacityWait": book["capacityWait"]}


def run(n=N_CASES, seed=20261016):
    rnd = random.Random(seed)
    work = build("lector", FILES)
    diffs, stats = [], {"entries": 0, "exits": 0, "skips": 0, "waits": 0, "fires": 0}
    done = 0
    while done < n:
        cases = [gen_case(rnd) for _ in range(min(300, n - done))]
        old = run_js(work, calendar_js() + JS, {"cases": cases})
        for c, o in zip(cases, old):
            p = port(c)
            stats["fires"] += len(c["inbox"])
            stats["entries"] += sum(1 for k, v in p["seen"].items() if v[0] == "enter" and k not in c["seen"])
            stats["skips"] += sum(1 for k, v in p["seen"].items() if v[0] == "skip" and k not in c["seen"])
            stats["exits"] += len(p["closed"])
            stats["waits"] += sum(1 for k in p["capacityWait"] if p["capacityWait"][k] != c["capacityWait"].get(k))
            if not same(p, o):
                diffs.append({"case": done, "port": p, "source": o})
            done += 1
    res = {"cases": n, "identical": n - len(diffs), "diffs": diffs[:8], "n_diffs": len(diffs), "stats": stats,
           "sleeves": ["midna_hourly_playbook"],
           "method": "rules.ts evaluatePass + fires.ts parseInboxFire under Node (state.halted false; the source holiday "
                     "table extended with the desk calendar outside 2026) vs hourly.parse_inbox_fire + hourly.step; exact"}
    write_receipt("midna_hourly", res)
    return dict(res, sleeve="midna_hourly")


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
