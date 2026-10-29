"""tensor_red_dip: old tensor_red_dip_sleeve.py vs the restored port (desk/sleeves/femto/tensor_red_dip.py).

The OLD module runs its real manage_exits(state, now) then entry_pass(state, False, now, equity) — the main pass
order — over today's journal written to a scratch JOURNAL_DIR (read_fresh_signals parses the flagship's
"SYM DEC conf=N PHENO" strings: the latest entry with fresh_signals wins, conf >= 7, first per symbol wins).
Stubbed: the market data (red_day_gate.day_return / is_red_day and latest_price return the case's prices: the
day return is the same float the port computes, price / prior close - 1), the broker and order book (positions
held, working entries and working exits), and the gates the cutover removed (kill switch, earnings blackout,
Decision #75 pre_buy, the 150% desk cap). The port runs signal() on the same case: the flagship's structured
signals of the latest non-empty row, quotes stamped in the session, the prior session's daily bar.

Compared: every exit submitted (symbol, qty, reason, reference price) and every entry submitted (symbol, qty,
reference price), in order."""
import random
from datetime import datetime, timedelta

from desk import calendar as cal
from desk.sleeves.femto import compat as fc
from desk.util import ET

from . import femto_module, old_run, write_receipt

F = femto_module("tensor_red_dip")
N_CASES = 3000
POOL = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG", "HHH", "III", "JJJ", "BRK.B", "KK-W"]
PHENOS = ["BREAKOUT", "RECLAIM", "REVERSAL", "TRANSITION"]

OLD = r'''
import os, tempfile
from datetime import datetime
from zoneinfo import ZoneInfo
import tensor_red_dip_sleeve as O
ET = ZoneInfo("America/New_York")
EV = []
O.log = lambda e: EV.append(dict(e))
O.kill_tripped = lambda equity, today: False
O._desk_earnings.is_blackout = lambda sym, d: False
O._desk_earnings.has_entry = lambda sym: True
O._d75.pre_buy = lambda *a, **k: "proceed"
O._cap_gate_entry = lambda sym, notional, equity: True
O._clamped_exit_qty = lambda sym, qty: (qty, True)
O.submit_market = lambda sym, side, qty, cid: {"id": "x", "status": "accepted"}
root = tempfile.mkdtemp()
out = []
for i, case in enumerate(PAYLOAD["cases"]):
    now = datetime.fromtimestamp(case["now"], tz=ET)
    jd = os.path.join(root, str(i))
    os.makedirs(jd)
    O.JOURNAL_DIR = jd
    with open(os.path.join(jd, now.strftime("%Y-%m-%d") + ".jsonl"), "w") as fh:
        for row in case["journal"]:
            fh.write(json.dumps(row) + "\n")
    rets, px = case["rets"], case["px"]
    O._day_return = lambda sym, rets=rets: (rets.get(sym), "stub")
    O._rdg.is_red_day = lambda sym, asof=None, rets=rets: ((rets.get(sym) is not None and rets[sym] < 0.0), "stub")
    O.latest_price = lambda sym, px=px: px.get(sym)
    pos = json.loads(json.dumps(case["positions"]))
    O.broker_positions = lambda pos=pos: {s: {"qty": p["qty"]} for s, p in pos.items() if p.get("entry_px")}
    omap = {}
    for s, p in case["positions"].items():
        if p.get("entry_px") is None:
            omap[(s, "femto-trd-%s-20260101T000000-000000-entry" % s)] = {"qty": p["qty"]}
    for s in case["exiting"]:
        omap[(s, "femto-trd-%s-20260101T000000-000000-exit" % s)] = {"qty": 1}
    O.open_order_cids = lambda omap=omap: dict(omap)
    state = {"positions": pos, "meta": {}}
    EV.clear()
    O.manage_exits(state, now)
    O.entry_pass(state, False, now, case["equity"])
    ex = [[e["symbol"], e["qty"], e["reason"], e["ref_px"]] for e in EV if e.get("event") == "exit_submitted"]
    en = [[e["symbol"], e["qty"], e["ref_px"]] for e in EV if e.get("event") == "entry_submitted"]
    out.append({"exits": ex, "entries": en})
print(json.dumps(out))
'''


def _sessions(rnd, n):
    out, d = [], datetime(2026, 1, 2).date()
    days = []
    while d <= datetime(2027, 12, 31).date():
        if cal.is_trading_day(d):
            days.append(d)
        d += timedelta(days=1)
    for _ in range(n):
        out.append(rnd.choice(days[10:]))
    return out


def _ret(rnd):
    r = rnd.random()
    if r < 0.05:
        return 0.0
    return rnd.uniform(-0.06, 0.04)


def _signals(rnd):
    k = rnd.randint(1, 8)
    out = []
    for _ in range(k):
        conf = None if rnd.random() < 0.03 else rnd.randint(3, 11)
        out.append({"symbol": rnd.choice(POOL), "decision": rnd.choice(("TRADE", "WATCH")), "confidence": conf,
                    "phenotype": rnd.choice(PHENOS)})
    return out


def _case(rnd, session):
    prev = cal.prev_trading_day(session)
    t = datetime(session.year, session.month, session.day, 9, 35, tzinfo=ET).timestamp() + rnd.randint(0, 370) * 60
    s_iso = session.isoformat()
    # the flagship's passes today: rows with / without / with empty fresh_signals; the latest non-empty wins
    rows, latest = [], None
    for j in range(rnd.randint(0, 4)):
        u = rnd.random()
        if u < 0.6:
            sig = _signals(rnd)
            rows.append({"ts_utc": "r%d" % j, "fresh_signals": ["%s %s conf=%s %s" % (
                s["symbol"], s["decision"], s["confidence"], s["phenotype"]) for s in sig]})
            latest = sig
        elif u < 0.8:
            rows.append({"ts_utc": "r%d" % j, "fresh_signals": []})
        else:
            rows.append({"ts_utc": "r%d" % j})
    # QQQ and the names: prior close, today's price (or unknown), the day return the port will compute
    pcs, pxs, rets, no_prior = {}, {}, {}, set()
    q = rnd.random()
    qpc = rnd.uniform(380, 520)
    qr = (rnd.uniform(-0.04, -0.0145) if q < 0.6 else rnd.uniform(-0.016, 0.02))
    names = ["QQQ"] + POOL
    for s in names:
        pc = qpc if s == "QQQ" else round(rnd.uniform(5, 1200), 2)
        r = qr if s == "QQQ" else _ret(rnd)
        u = rnd.random()
        if s == "QQQ" and q > 0.97:
            u = 0.0
        if u < 0.05:
            px = None                                    # no price today yet
        else:
            px = round(pc * (1 + r), 2)
        if 0.05 <= u < 0.09:
            no_prior.add(s)                              # the prior session missing from the series
        pcs[s], pxs[s] = pc, px
        rets[s] = None if (px is None or s in no_prior) else px / pc - 1.0
    # the book: held positions (some exiting), working entries
    positions, exiting = {}, []
    for s in rnd.sample(POOL, rnd.randint(0, 6)):
        if rnd.random() < 0.2:
            positions[s] = {"qty": rnd.randint(1, 400), "entry_px": None, "entry_date": s_iso, "entry_cid": "w",
                            "staged": False}
            continue
        k = rnd.randint(0, 5)
        ed = session
        for _ in range(k):
            ed = cal.prev_trading_day(ed)
        if rnd.random() < 0.1:
            ed = ed - timedelta(days=rnd.randint(0, 3))  # a calendar date, not always a session
        entry = round(rnd.uniform(5, 1200), 2)
        positions[s] = {"qty": rnd.randint(1, 400), "entry_px": entry, "entry_date": ed.isoformat(),
                        "entry_cid": "e", "staged": False}
        u = rnd.random()
        if pxs[s] is not None:                           # the held name's price relative to its entry
            if u < 0.25:
                pxs[s] = round(entry * rnd.uniform(1.025, 1.06), 2)
            elif u < 0.45:
                pxs[s] = round(entry * rnd.uniform(0.88, 0.93), 2)
            else:
                pxs[s] = round(entry * rnd.uniform(0.93, 1.03), 2)
            rets[s] = None if s in no_prior else pxs[s] / pcs[s] - 1.0
        if rnd.random() < 0.1:
            exiting.append(s)
    return {"now": t, "session": s_iso, "prev": prev.isoformat(), "journal": rows, "latest": latest,
            "pcs": pcs, "px": pxs, "rets": rets, "no_prior": sorted(no_prior), "positions": positions,
            "exiting": exiting, "equity": round(rnd.choice((rnd.uniform(15_000, 60_000), rnd.uniform(60_000, 800_000))), 2)}


def _port(case):
    s_iso, prev = case["session"], case["prev"]
    p_day = datetime.fromisoformat(prev).replace(hour=4, tzinfo=ET)
    bars = {}
    for s, pc in case["pcs"].items():
        d = p_day - timedelta(days=7) if s in case["no_prior"] else p_day
        bars[s] = [{"t": d.timestamp() - 86400 * 3, "o": pc, "h": pc, "l": pc, "c": pc * 1.01, "v": 1e6},
                   {"t": d.timestamp(), "o": pc, "h": pc, "l": pc, "c": pc, "v": 1e6}]
    quotes = {s: {"bid": None, "ask": None, "last": px, "t": case["now"] - 5}
              for s, px in case["px"].items() if px is not None}
    ss = {}
    for s, p in case["positions"].items():
        if p["entry_px"] is None:
            ss[s] = {"position": None, "pending_entry": {"qty": p["qty"], "filled": 0.0, "key": "k", "ref_px": None}}
        else:
            ss[s] = {"position": {"qty": p["qty"], "entry_px": p["entry_px"], "entry_date": p["entry_date"],
                                  "opened_at": case["now"] - 3600, "exit_submitted": (s in case["exiting"]) or None}}
    fresh = {"session": s_iso, "at": case["now"] - 60, "signals": case["latest"]} if case["latest"] else None
    hol = sorted(d.isoformat() for y in range(int(s_iso[:4]) - 1, int(s_iso[:4]) + 2) for d in cal.holidays(y))
    extra = {"sleeve_state": ss, "quotes": quotes, "prev_session": prev, "nyse_holidays": hol, "closed_trades": []}
    if fresh:
        extra["fresh"] = fresh
    ctx = fc.Context(now=case["now"], session=s_iso, equity=case["equity"], extra=extra)
    out = F.signal(bars, {}, ctx)
    ex = [[i.symbol, i.qty_hint, i.reason.split(": ", 1)[1], i.price_hint] for i in out if i.kind == "exit"]
    en = [[i.symbol, i.qty_hint, i.price_hint] for i in out if i.kind == "enter"]
    return {"exits": ex, "entries": en}


def run():
    rnd = random.Random(20261016)
    cases = [_case(rnd, d) for d in _sessions(rnd, N_CASES)]
    old = old_run(OLD, {"cases": cases})
    diffs, stats = [], {"entries": 0, "exits": {}, "fear_days": 0, "fear_days_with_signals": 0,
                        "at_max_positions": 0, "qqq_unknown": 0}
    for c, o in zip(cases, old):
        p = _port(c)
        if p != o:
            diffs.append({"session": c["session"], "old": o, "port": p})
        stats["entries"] += len(o["entries"])
        for e in o["exits"]:
            stats["exits"][e[2]] = stats["exits"].get(e[2], 0) + 1
        qr = c["rets"].get("QQQ")
        stats["qqq_unknown"] += qr is None
        if qr is not None and qr * 100.0 <= -1.5:
            stats["fear_days"] += 1
            if c["latest"]:
                stats["fear_days_with_signals"] += 1
                stats["at_max_positions"] += len(c["positions"]) + len(o["entries"]) >= 5
    res = {"sleeve": "tensor_red_dip", "cases": len(cases), "identical": len(cases) - len(diffs), "diffs": diffs[:20],
           "n_diffs": len(diffs), "stats": stats,
           "method": "old manage_exits + entry_pass (real journal parse; market data, broker and removed gates "
                     "stubbed) vs port signal() on the same case"}
    write_receipt("tensor_red_dip", res)
    return res
