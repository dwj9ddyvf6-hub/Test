"""sable_runtime: the Sable unattended paper pass (autopilot-desk @48e8f90f src/lib/desk/unattended-core.mjs
runUnattendedPaperPass + ledger-core.mjs, the SOURCE modules run unmodified under Node 22, the simulator path) vs
the port (desk/sleeves/sable/runtime.py) on the same desk state, reads and clocks.

Each case: a random desk state — 0-7 long positions (fills, open times 0-30 days back, stops / targets around the
fill or missing), working / filled / cancelled orders, a history of BUY / SELL / EXIT / TRIM / ATTENTION events
(inside and outside the 8-hour round-trip window, colliding idempotency keys), quotes (price, daily ATR or none,
stock / ETF, location-first or desk-scanner stamps, earnings flags, hostile regime, RSI / extension / MACD), a
scanner bundle (SETUP / WATCH / PRESSURE candidates and hands, location-first or desk origin, anti-chase, thesis-
break reasons), Tensor reads (buy / sell / neutral), a mandate (cap 1-8, autonomy, earnings / extended-hours /
mega-cap switches), cash and broker equity, the market session, the run state and Edge flags; the pass clock and
the wall clock (Date.now) set separately.

Compared, exactly: the state after the pass — positions (ticker, qty, fill, open time, stop, target), orders
(ticker, side, qty, limit, status, reject reason, fill price / time), events (idempotency key, kind, ticker, title,
body, price, qty, created, flags), cash — ids aside (opaque uid()s); plus 4,000 direct calls of each ledger-core
helper (swingStopPrice / swingTargetPrice / swingSizeShares / swingTimeStopDue / swingTrailStop /
swingThesisBroken / deskDiscretionAllowsBuy / canEnterUnderMandate / mapTensorToDeskDecision) on edge inputs.

    AUTOPILOT_DESK=<autopilot-desk @48e8f90f> python3 -m tools.parity.run sable_runtime"""
import copy
import random

from desk.sleeves.sable import runtime as rt

from . import write_receipt
from .node_pinned import cleanup, run as node_run, same, stage

COMMIT = "48e8f90f5d9def28363eb4013dac4dd8d78f74bf"
FILES = {
    "src/lib/desk/unattended-core.mjs": "8fb33e5932fa2a015c7a660e61a671c2bed58926",
    "src/lib/desk/ledger-core.mjs": "6342ddc827978ceaecefa2c893bbc85e7d1361f8",
    "src/lib/desk/always-on-core.mjs": "0acb87a777d0997e659fc52be73fb9acea1c7a82",
    "src/lib/scanner/contract.mjs": "3777a9ce71bb1b4d697b0437e40ef2a8a06193ac",
    "src/lib/scanner/desk-core.mjs": "1b5f90418acae9d53d3bf25caa251f86843351b2",
    "src/lib/scanner/features.mjs": "843833d1f8fab0669912c6bf1cd3860a771f735e",
    "src/lib/broker/alpaca-core.mjs": "06c99170c3062b8b8413777ffbefe47f4bf33f20",
}
N_PASS = 3000
N_HELPER = 4000
POOL = ["AAPL", "MSFT", "NVDA", "IRDM", "OSCR", "PANW", "MU", "SMH", "QQQ", "AMD", "CRWD", "TSLA", "ONDS", "AMPX",
        "LLY"]
THESIS = ["50-day still falling. Not a leader rest.", "Too far from the 52-week high. Laggard.",
          "Not on a rising 50-day.", "near the 21-day average, still under the 50-day average.", ""]

DRIVER = r"""
import { readFileSync } from "node:fs";
import { runUnattendedPaperPass } from "./src/lib/desk/unattended-core.mjs";
import * as L from "./src/lib/desk/ledger-core.mjs";
const P = JSON.parse(readFileSync(0, "utf8"));
let CLOCK = 0, SEQ = 0;
Date.now = () => CLOCK;
Math.random = () => { SEQ += 1; return (SEQ % 9973) / 9973; };
const strip = (s) => ({
  positions: s.positions.map((p) => ({ ticker: p.ticker, qty: p.qty, avgPrice: p.avgPrice, openedAt: p.openedAt,
    stop: p.stop, target: p.target, side: p.side })),
  orders: s.orders.map((o) => ({ ticker: o.ticker, side: o.side, qty: o.qty, limit: o.limit, status: o.status,
    rejectReason: o.rejectReason, fillPrice: o.fillPrice, filledAt: o.filledAt, createdAt: o.createdAt, venue: o.venue })),
  events: s.events.map((e) => ({ key: e.idempotencyKey, kind: e.kind, ticker: e.ticker, title: e.title, body: e.body,
    price: e.price, qty: e.qty, createdAt: e.createdAt, requiresAction: e.requiresAction, resolved: e.resolved })),
  cash: s.cash });
const passes = P.passes.map((c) => { CLOCK = c.clock; const s = c.state; runUnattendedPaperPass(s, c.reads, c.now); return strip(s); });
const helpers = P.helpers.map((h) => {
  const a = h.args;
  switch (h.fn) {
    case "swingStopPrice": return L.swingStopPrice(...a);
    case "swingTargetPrice": return L.swingTargetPrice(...a);
    case "swingSizeShares": return L.swingSizeShares(a[0]);
    case "swingTimeStopDue": return L.swingTimeStopDue(...a);
    case "swingTrailStop": return L.swingTrailStop(...a);
    case "swingThesisBroken": return L.swingThesisBroken(a[0]);
    case "deskDiscretionAllowsBuy": return L.deskDiscretionAllowsBuy(a[0]);
    case "canEnterUnderMandate": return L.canEnterUnderMandate(...a);
    case "mapTensorToDeskDecision": return L.mapTensorToDeskDecision(a[0]);
  }
});
console.log(JSON.stringify({ passes, helpers }));
"""


def _maybe(rnd, p, v):
    return v if rnd.random() < p else None


def _quote(rnd, t, now):
    px = round(rnd.uniform(5, 400), 2)
    q = {"ticker": t, "price": px}
    if rnd.random() < 0.85:
        q["atr"] = round(px * rnd.uniform(0.005, 0.06), 3)
    q["kind"] = "etf" if (t in ("SMH", "QQQ") and rnd.random() < 0.8) else rnd.choice(["stock"] * 9 + ["etf"])
    r = rnd.random()
    if r < 0.6:
        q["locationFirstAt"] = now - rnd.randint(0, 3) * 86_400_000
        q["origin"] = "location-first"
    elif r < 0.85:
        q["completedBarAt"] = now - rnd.randint(1, 12) * 300_000
    if rnd.random() < 0.06:
        q["earningsImminent"] = True
    if rnd.random() < 0.04:
        q["regime"] = "hostile"
    if rnd.random() < 0.5:
        q["rsi"] = round(rnd.uniform(25, 80), 2)
    if rnd.random() < 0.5:
        q["extensionAtr"] = round(rnd.uniform(0, 2.5), 3)
    if rnd.random() < 0.4:
        q["macdHist"] = round(rnd.uniform(-0.4, 0.4), 3)
    if rnd.random() < 0.2:
        q["location"] = rnd.choice(["favorable", "extended", "compressed"])
    return q


def make_pass(i):
    rnd = random.Random(f"sable-rt-{i}")
    now = 1_790_000_000_000 + rnd.randint(0, 10**9) * 7
    clock = now + rnd.choice([0, 0, 0, rnd.randint(1, 60_000)])
    names = rnd.sample(POOL, rnd.randint(4, len(POOL)))
    quotes = {t: _quote(rnd, t, now) for t in names if rnd.random() < 0.95}
    positions = []
    for t in rnd.sample(names, rnd.randint(0, min(7, len(names)))):
        q = quotes.get(t) or {"price": rnd.uniform(5, 400)}
        avg = round(q["price"] * rnd.uniform(0.85, 1.15), 2)
        p = {"id": f"pos_{t}_{i}", "ticker": t, "side": "long", "qty": rnd.randint(1, 500), "avgPrice": avg,
             "openedAt": now - rnd.randint(0, 30 * 86_400_000)}
        if rnd.random() < 0.9:
            p["stop"] = round(avg * rnd.uniform(0.85, 1.02), 2)
        if rnd.random() < 0.9:
            p["target"] = round(avg * rnd.uniform(0.98, 1.3), 2)
        positions.append(p)
    orders = []
    for _ in range(rnd.randint(0, 4)):
        orders.append({"id": f"o{rnd.randint(0, 10**6)}", "ticker": rnd.choice(names), "side": rnd.choice(["buy", "sell"]),
                       "qty": rnd.randint(1, 100), "limit": round(rnd.uniform(5, 400), 2),
                       "status": rnd.choice(["accepted", "proposed", "filled", "cancelled"]),
                       "createdAt": now - rnd.randint(0, 10**7)})
    events = []
    for _ in range(rnd.randint(0, 12)):
        t = rnd.choice(names)
        kind = rnd.choice(["BUY", "SELL", "EXIT", "TRIM", "ATTENTION", "WAIT"])
        q = quotes.get(t) or {}
        bar = q.get("locationFirstAt") if q.get("locationFirstAt") is not None else q.get("completedBarAt")
        key = rnd.choice([f"buy:{t}:{rt.js_str(bar) if bar is not None else 'x'}", f"{kind.lower()}:{t}:{rnd.randint(0, 9)}",
                          f"attention:{t}:{rt.js_str(bar) if bar is not None else 'y'}"])
        e = {"id": f"e{rnd.randint(0, 10**6)}", "idempotencyKey": key, "kind": kind, "ticker": t,
             "createdAt": clock - rnd.choice([rnd.randint(0, 8 * 3600_000), rnd.randint(8 * 3600_000, 10**9)]),
             "resolved": rnd.random() < 0.8, "requiresAction": rnd.random() < 0.2}
        events.append(e)
    cands = []
    for t in names:
        if rnd.random() < 0.25:
            continue
        q = quotes.get(t) or {}
        lfo = rnd.random() < 0.6
        row = {"ticker": t, "action": rnd.choice(["SETUP", "SETUP", "WATCH", "PRESSURE"]),
               "tier": rnd.choice(["S", "A", "B", None]), "kind": q.get("kind", "stock"),
               "origin": "location-first" if lfo else "desk", "source": "desk",
               "antiChase": rnd.choice(["clear"] * 5 + ["blocked"]),
               "reason": rnd.choice(THESIS), "location": rnd.choice(["favorable", "extended", "compressed"])}
        if lfo and rnd.random() < 0.85:
            row["dailyBarAt"] = q.get("locationFirstAt", now - 86_400_000)
        if rnd.random() < 0.05:
            row["action"] = rnd.choice(["SKIP", "pass", "Leave"])
        cands.append(row)
    hands = [{"ticker": r["ticker"], "action": r["action"], "tier": r["tier"]} for r in cands
             if r["action"] == "SETUP" and r["kind"] != "etf" and rnd.random() < 0.8]
    if rnd.random() < 0.1:
        hands = []
    scanner = {"status": rnd.choice(["ready"] * 9 + ["unavailable"]), "candidates": cands, "hands": hands}
    mandate = dict(rt.DEFAULT_MANDATE, maxPositions=rnd.choice([1, 2, 3, 4, 5, 6, 6, 6, 7, 8]),
                   autonomy=rnd.choice(["autopilot"] * 8 + ["approve", "observe"]),
                   allowEarningsWindow=rnd.random() < 0.2, allowExtendedHours=rnd.random() < 0.2,
                   excludeMegaCaps=rnd.random() < 0.15)
    if rnd.random() < 0.05:
        mandate["tensorTiming"] = "required"
    reads = {}
    for t in names:
        if rnd.random() < 0.5:
            reads[t] = {"paperBuy": rnd.random() < 0.15, "paperSell": rnd.random() < 0.1,
                        "state": rnd.choice(["NEUTRAL", "VECTOR_BUY", "REVERSAL_WINDOW"])}
            if rnd.random() < 0.7:
                reads[t]["completedBarAt"] = now - rnd.randint(1, 6) * 300_000
    cash = round(rnd.uniform(-5000, 120_000), 2)
    state = {"positions": positions, "orders": orders, "events": events, "quotes": quotes, "scanner": scanner,
             "mandate": mandate, "runState": rnd.choice(["running"] * 9 + ["paused"]), "cash": cash,
             "broker": {"cash": cash if rnd.random() < 0.7 else 0, "equity": round(cash + rnd.uniform(0, 80_000), 2)},
             "market": {"session": rnd.choice(["regular"] * 6 + ["premarket", "afterhours", "closed", "paper"])},
             "freshness": {"lastCompletedBarAt": rnd.choice([None, now - 300_000, 1_790_000_000_000])}}
    if rnd.random() < 0.08:
        state["edge"] = {"blockNewEntries": rnd.random() < 0.5, "parked": rnd.sample(names, 1),
                         "sizeDown": rnd.random() < 0.5}
    return {"state": state, "reads": reads, "now": now, "clock": clock}


def make_helper(i):
    rnd = random.Random(f"sable-rt-h-{i}")
    fn = rnd.choice(["swingStopPrice", "swingTargetPrice", "swingSizeShares", "swingTimeStopDue", "swingTrailStop",
                     "swingThesisBroken", "deskDiscretionAllowsBuy", "canEnterUnderMandate", "mapTensorToDeskDecision"])
    px = rnd.choice([round(rnd.uniform(0.5, 500), 2), 0, -3, "12.5"])
    atr = rnd.choice([round(rnd.uniform(0, 20), 3), None, 0, "x"])
    if fn in ("swingStopPrice", "swingTargetPrice"):
        args = [px, atr]
    elif fn == "swingSizeShares":
        args = [{k: v for k, v in {"equity": rnd.choice([round(rnd.uniform(-10, 3e5), 2), None, 0]),
                                   "cash": rnd.choice([round(rnd.uniform(-10, 2e5), 2), None, 0]),
                                   "price": px, "atr": atr, "sizeDown": rnd.random() < 0.3}.items() if v is not None}]
    elif fn == "swingTimeStopDue":
        args = [rnd.choice([0, None, 1.79e12, 1.79e12 - rnd.randint(0, 40) * 86_400_000]), 1.79e12,
                rnd.choice([0, -5.5, 12.25, None])]
    elif fn == "swingTrailStop":
        args = [px, atr, rnd.choice([round(rnd.uniform(0, 600), 2), None]), rnd.choice([None, 0, round(rnd.uniform(0, 500), 2)])]
    elif fn == "swingThesisBroken":
        args = [rnd.choice([None, {"reason": rnd.choice(THESIS)}, {"publicReason": "Collapsing 50 here"},
                            {"action": rnd.choice(["skip", "PASS", "leave it", "Leave", "SETUP"])}, {}])]
    elif fn == "deskDiscretionAllowsBuy":
        q = _quote(rnd, rnd.choice(POOL), 1.79e12)
        hit = rnd.choice([None, {"action": rnd.choice(["SETUP", "WATCH"]), "origin": rnd.choice(["location-first", "desk"]),
                                 "antiChase": rnd.choice(["clear", "blocked"]), "tier": rnd.choice(["S", "A", None]),
                                 "reason": rnd.choice(THESIS), "dailyBarAt": rnd.choice([None, 0, 1.79e12]),
                                 "ticker": q["ticker"], "location": rnd.choice(["favorable", "extended"])}])
        args = [{k: v for k, v in {"quote": q, "scannerHit": hit, "paperSell": rnd.random() < 0.1,
                                   "paperBuy": rnd.random() < 0.2,
                                   "completedBarAt": rnd.choice([None, 0, 1.79e12]),
                                   "tensorState": rnd.choice([None, "NEUTRAL", "VECTOR_BUY"]),
                                   "mandate": {"tensorTiming": rnd.choice(["optional", "required"])}}.items() if v is not None}]
    elif fn == "canEnterUnderMandate":
        q = _quote(rnd, rnd.choice(POOL), 1.79e12)
        m = dict(rt.DEFAULT_MANDATE, allowStocks=rnd.choice([True, False]), excludeMegaCaps=rnd.random() < 0.3,
                 allowOvernight=rnd.random() < 0.7, allowExtendedHours=rnd.random() < 0.3,
                 allowEarningsWindow=rnd.random() < 0.3, allowStressBuys=rnd.random() < 0.5)
        args = [m, q, rnd.choice(["regular", "paper", "premarket", "afterhours", "closed"])]
    else:
        args = [{k: v for k, v in {"paperBuy": rnd.random() < 0.3, "paperSell": rnd.random() < 0.3,
                                   "hasPosition": rnd.random() < 0.3, "parked": rnd.random() < 0.1,
                                   "autonomy": rnd.choice(["approve", "observe", "autopilot"]),
                                   "scannerAvailable": rnd.random() < 0.5,
                                   "deskBuy": rnd.choice([None, True, False]),
                                   "deskBuyReason": rnd.choice(["", "because"])}.items() if v is not None}]
    return {"fn": fn, "args": args}


def port_helper(h):
    a = h["args"]
    fn = h["fn"]
    if fn == "swingStopPrice":
        return rt.swing_stop_price(*a)
    if fn == "swingTargetPrice":
        return rt.swing_target_price(*a)
    if fn == "swingSizeShares":
        x = a[0]
        return rt.swing_size_shares(x.get("equity"), x.get("cash"), x.get("price"), x.get("atr"), x.get("sizeDown", False))
    if fn == "swingTimeStopDue":
        return rt.swing_time_stop_due(*a)
    if fn == "swingTrailStop":
        return rt.swing_trail_stop(*a)
    if fn == "swingThesisBroken":
        return rt.swing_thesis_broken(a[0])
    if fn == "deskDiscretionAllowsBuy":
        x = a[0]
        return rt.desk_discretion_allows_buy(quote=x.get("quote"), scanner_hit=x.get("scannerHit"),
                                             paper_sell=x.get("paperSell", False), paper_buy=x.get("paperBuy", False),
                                             completed_bar_at=x.get("completedBarAt"),
                                             tensor_state=x.get("tensorState"), mandate=x.get("mandate"))
    if fn == "canEnterUnderMandate":
        return rt.can_enter_under_mandate(*a)
    x = a[0]
    return rt.map_tensor_to_desk_decision(paper_buy=x.get("paperBuy", False), paper_sell=x.get("paperSell", False),
                                          has_position=x.get("hasPosition", False), parked=x.get("parked", False),
                                          autonomy=x.get("autonomy", "approve"),
                                          scanner_available=x.get("scannerAvailable", False),
                                          desk_buy=x.get("deskBuy"), desk_buy_reason=x.get("deskBuyReason", ""))


def strip(s):
    return {"positions": [{k: p.get(k) for k in ("ticker", "qty", "avgPrice", "openedAt", "stop", "target", "side")}
                          for p in s["positions"]],
            "orders": [{k: o.get(k) for k in ("ticker", "side", "qty", "limit", "status", "rejectReason", "fillPrice",
                                              "filledAt", "createdAt", "venue")} for o in s["orders"]],
            "events": [{"key": e.get("idempotencyKey"), "kind": e.get("kind"), "ticker": e.get("ticker"),
                        "title": e.get("title"), "body": e.get("body"), "price": e.get("price"), "qty": e.get("qty"),
                        "createdAt": e.get("createdAt"), "requiresAction": e.get("requiresAction"),
                        "resolved": e.get("resolved")} for e in s["events"]],
            "cash": s["cash"]}


def run():
    passes = [make_pass(i) for i in range(N_PASS)]
    helpers = [make_helper(i) for i in range(N_HELPER)]
    ours, acts = [], {"buy": 0, "sell": 0, "cancel": 0}
    for c in passes:
        st = copy.deepcopy(c["state"])
        for a in rt.run_pass(st, copy.deepcopy(c["reads"]), c["now"], c["clock"]):
            acts[a[0]] += 1
        ours.append(strip(st))
    tree = stage("AUTOPILOT_DESK", "/home/user/autopilot-desk", FILES)
    try:
        theirs = node_run(tree, DRIVER, {"passes": passes, "helpers": helpers})
    finally:
        cleanup(tree)
    diffs, identical = [], 0
    for i, (o, t) in enumerate(zip(ours, theirs["passes"])):
        d = same(o, t)
        if d:
            diffs.append({"pass": i, "diff": d[:5]})
        else:
            identical += 1
    for i, (h, t) in enumerate(zip(helpers, theirs["helpers"])):
        d = same(port_helper(h), t)
        if d:
            diffs.append({"helper": i, "fn": h["fn"], "diff": d[:3]})
        else:
            identical += 1
    res = {"sleeve": "sable_runtime", "cases": N_PASS + N_HELPER, "identical": identical, "diffs": diffs[:50],
           "n_diffs": len(diffs), "stats": {"actions": acts, "passes": N_PASS, "helpers": N_HELPER},
           "method": "unattended-core.mjs runUnattendedPaperPass + ledger-core.mjs (autopilot-desk @48e8f90f, "
                     "blob-verified) under Node 22 (Date.now pinned per case) vs the Python port, same state",
           "source": {"repo": "autopilot-desk", "commit": COMMIT, "files": FILES},
           "sleeves": ["sable_location_first_repair_v210", "sable_support_scanner"]}
    write_receipt("sable_runtime", res)
    return res
