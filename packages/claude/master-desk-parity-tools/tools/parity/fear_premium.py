"""fear_premium: old fear_premium_sleeve.py scan_pass() vs the restored port's decide() on the same case.

The OLD module runs its real scan_pass(): rank_universe (the weekly beta cache or a fresh ranking of the basket),
manage_positions (exit_due on the conservative close cost, the 8-day clock, the 21-DTE floor; close_spread at each
leg's mid), then the entry loop (slots = positions + closing + awaiting fills + pending; maybe_enter: detect_red_day,
its real earnings_ok over desk/earnings.py fed the case's calendar, select_spread_legs, validate_spread_quotes,
size_contracts, both legs submitted). Stubbed: the clock, equity, the daily bars, the basket file, the chain / quote /
order CLIs (the case's), and the gates the cutover removed (risk gate, Decision #75 pre_buy -> proceed, desk cap).

Compared: the spreads opened (symbol, short, long, contracts, credit) and closed (symbol, short, long, contracts,
reason, net mid within a cent: the old priced each leg at its own %.2f mid, the port the package mid)."""
import random
from datetime import date, datetime, timedelta, timezone

from desk import calendar as cal
from desk.sleeves.femto import compat as fc
from desk.util import ET

from . import femto_module, old_run, write_receipt

F = femto_module("fear_premium")
N_CASES = 1500
NAMES = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG", "HHH", "III", "JJJ", "KKK", "LLL", "MMM", "NNN", "SOXL"]

OLD = r'''
import sys, types
from datetime import datetime as _dt, timezone
import fear_premium_sleeve as O
import desk.earnings as E
EV = []
O.log = lambda e: EV.append(dict(e))
O.save_state = lambda s: None
O.DRY_RUN = False
O._HAS_RISK_GATE = True
O._risk_gate = types.SimpleNamespace(evaluate_entry=lambda s, u: (True, []), blocked_reasons=lambda r: r)
O.check_kill_switch = lambda sym: True
O.cross_sleeve_ok = lambda sym: True
O._cap_gate_entry = lambda sym, n, e: True
O.replay_chart_gate_releases = lambda st, now, equity=None: None
O.promote_fills = lambda st, now: None
d75 = types.ModuleType("desk.decision75")
d75.pre_buy = lambda *a, **k: "proceed"
sys.modules["desk.decision75"] = d75
O._USE_CACHE = False
class FakeDT(_dt):
    NOW = None
    @classmethod
    def now(cls, tz=None):
        return cls.NOW.astimezone(tz) if tz else cls.NOW
O.datetime = FakeDT
E.datetime = FakeDT
O._HAS_EARN = True
O._earn = E
out = []
for case in PAYLOAD["cases"]:
    FakeDT.NOW = _dt.fromtimestamp(case["now"], tz=timezone.utc)
    st = O.fresh_state()
    st.update(json.loads(json.dumps(case["state"])))
    O.load_state = lambda st=st: st
    O.get_equity = lambda e=case["equity"]: e
    O.load_basket_symbols = lambda b=case["basket"]: list(b)
    O.fetch_daily_bars = lambda sym, limit=90, B=case["bars"]: (B[sym][-limit:] if sym in B else (_ for _ in ()).throw(RuntimeError("no bars")))
    E.load_earnings = lambda c=case["calendar"]: dict(c)
    E.calendar_status = lambda f=case["cal_ts"]: (f, 10)
    def chain(sym, dte_min=25, dte_max=35, C=case["chains"]):
        today = FakeDT.now(O.ET).date()
        lo = (today + O.timedelta(days=dte_min)).isoformat()
        hi = (today + O.timedelta(days=dte_max)).isoformat()
        return [r for r in C.get(sym, []) if lo <= r["expiration"] <= hi]
    O.option_chain_puts = chain
    O.option_quotes = lambda occs, q=case["quotes"]: {o: q[o] for o in occs if o in q}
    O._get_order = lambda oid: None
    ORD = []
    def sub(occ, side, qty, limit_price, intent, cid, ORD=ORD):
        ORD.append([occ, side, int(qty), float("%.2f" % limit_price), intent])
        return {"id": "o%d" % len(ORD), "status": "accepted"}
    O.submit_option = sub
    EV.clear()
    O.scan_pass(FakeDT.NOW)
    exits = {e["symbol"]: e["reason"] for e in EV if e.get("event") == "exit_signal"}
    out.append({"orders": ORD, "exits": exits})
print(json.dumps(out))
'''


def _bars(rnd, end, n=90, px=None):
    days, d = [], end
    while len(days) < n:
        if cal.is_trading_day(d):
            days.append(d)
        d -= timedelta(days=1)
    px = px or rnd.uniform(15, 300)
    out = []
    drift = rnd.uniform(-0.004, 0.003)
    for dd in reversed(days):
        r = rnd.gauss(drift, 0.025)
        c = max(1.0, px * (1 + r))
        out.append({"t": datetime(dd.year, dd.month, dd.day, 4, tzinfo=timezone.utc).timestamp(), "o": px,
                    "h": max(px, c) * 1.01, "l": min(px, c) * 0.99, "c": round(c, 2), "v": 1e6})
        px = c
    if rnd.random() < 0.5:                                    # a red day on the last completed session
        out[-1]["c"] = round(out[-2]["c"] * rnd.uniform(0.85, 0.955), 2)
    return out


def _occ(sym, exp, k):
    return "%s%s%s%sP%08d" % (sym, exp[2:4], exp[5:7], exp[8:10], int(round(k * 1000)))


def _chain(rnd, sym, ref, today):
    grid = rnd.choice((0.5, 1.0, 2.5, 5.0)) if ref > 20 else rnd.choice((0.5, 1.0))
    rows, quotes = [], {}
    for dte in sorted(rnd.sample(range(20, 42), rnd.randint(1, 4))):
        exp = (today + timedelta(days=dte)).isoformat()
        k = round(ref * 0.6 / grid) * grid
        while k <= ref * 1.02:
            occ = _occ(sym, exp, k)
            rows.append({"symbol": occ, "strike": k, "expiration": exp})
            otm = max(0.0, (ref - k) / ref)
            fair = max(0.05, ref * 0.06 * (1 - otm * 4)) if otm < 0.25 else 0.05
            bid = round(fair * rnd.uniform(0.9, 1.0), 2)
            ask = round(bid * rnd.uniform(1.01, 1.18) + 0.01, 2)
            if rnd.random() < 0.04:
                bid = 0.0
            quotes[occ] = {"bid": bid, "ask": ask}
            k = round(k + grid, 4)
    return rows, quotes


def _case(rnd):
    today = date(2026, 1, 12) + timedelta(days=rnd.randint(0, 250))
    while not cal.is_trading_day(today):
        today += timedelta(days=1)
    now = datetime(today.year, today.month, today.day, rnd.randint(9, 15), 55, tzinfo=ET).timestamp()
    prev = cal.prev_trading_day(today)
    names = rnd.sample(NAMES, rnd.randint(6, len(NAMES)))
    bars = {s: _bars(rnd, prev) for s in names + ["QQQ", "TQQQ"]}
    if "SOXL" not in bars:
        bars["SOXL"] = _bars(rnd, prev)
    basket = [s for s in NAMES if s in bars]
    chains, quotes = {}, {}
    for s, bl in bars.items():
        if rnd.random() < 0.9:
            rows, q = _chain(rnd, s, float(bl[-1]["c"]), today)
            chains[s] = rows
            quotes.update(q)
    calendar = {}
    for s in names:
        u = rnd.random()
        if u < 0.1:
            continue                                         # unknown
        calendar[s] = None if u < 0.15 else (today + timedelta(days=rnd.randint(-5, 40))).isoformat()
    fresh = rnd.random() < 0.9
    cal_ts = (datetime.fromtimestamp(now, tz=timezone.utc) - timedelta(days=2 if fresh else 9)).isoformat()
    state, ss, meta = {"positions": {}, "awaiting_fills": {}}, {}, {}
    if rnd.random() < 0.6:                                   # a cached ranking
        age = rnd.choice((1, 3, 6, 7, 9))
        ranked = ["SOXL", "TQQQ"] + rnd.sample(names, min(len(names), rnd.randint(3, 10)))
        ranked = list(dict.fromkeys(ranked))
        as_of = now - age * 86400 - rnd.randint(0, 3000)
        state["universe"] = {"ranked": ranked, "as_of": datetime.fromtimestamp(as_of, tz=timezone.utc).isoformat()}
        meta["universe"] = {"ranked": ranked, "as_of": as_of}
    for s in rnd.sample(names, rnd.randint(0, 4)):           # held spreads / in-flight entries
        bl = bars[s]
        ref = float(bl[-1]["c"])
        if rnd.random() < 0.2:
            state["awaiting_fills"][s] = {"symbol": s}
            ss[s] = {"position": None, "pending_entry": {"qty": 1}}
            continue
        exp = (today + timedelta(days=rnd.randint(15, 40))).isoformat()
        ks, kl = round(ref * 0.93, 0), round(ref * 0.83, 0)
        so, lo = _occ(s, exp, ks), _occ(s, exp, kl)
        credit = round(rnd.uniform(0.2, 2.0), 2)
        sb = round(credit * rnd.choice((0.2, 0.4, 0.5, 0.7, 1.0, 1.5)), 2)
        quotes[so] = {"bid": sb, "ask": round(sb + rnd.choice((0.01, 0.05, 0.1)), 2)}
        lb = round(sb * rnd.uniform(0.1, 0.6), 2)
        quotes[lo] = {"bid": lb, "ask": round(lb + rnd.choice((0.01, 0.05)), 2)}
        if rnd.random() < 0.05:
            quotes.pop(so)
            quotes.pop(lo)
        n = rnd.randint(1, 6)
        opened = now - rnd.randint(0, 12) * 86400 - rnd.randint(0, 80000)
        state["positions"][s] = {"spread": {"short_occ": so, "long_occ": lo, "expiry": exp}, "contracts": n,
                                 "entry_credit": credit, "long_filled": True,
                                 "entry_ts": datetime.fromtimestamp(opened, tz=timezone.utc).isoformat()}
        ss[s] = {"position": {"qty": n, "net_entry": -credit, "opened_at": opened, "legs": {so: -n, lo: n},
                              "expiry": exp}}
    equity = rnd.choice((rnd.uniform(5_000, 50_000), rnd.uniform(50_000, 2_000_000)))
    return {"now": now, "session": today.isoformat(), "bars": bars, "basket": basket, "chains": chains,
            "quotes": quotes, "calendar": calendar, "cal_ts": cal_ts, "fresh": fresh, "state": state, "ss": ss,
            "meta": meta, "equity": equity}


def _port(c):
    today = date.fromisoformat(c["session"])
    lo, hi = (today + timedelta(days=25)).isoformat(), (today + timedelta(days=35)).isoformat()
    chains = {s: [dict(r, type="put", **c["quotes"].get(r["symbol"], {})) for r in rows if lo <= r["expiration"] <= hi]
              for s, rows in c["chains"].items()}
    held = {o for st in c["ss"].values() for o in ((st.get("position") or {}).get("legs") or {})}
    extra = {"meta": c["meta"], "chains": chains, "option_quotes": {o: c["quotes"][o] for o in held if o in c["quotes"]},
             "earnings": c["calendar"], "earnings_fresh": c["fresh"], "basket": c["basket"], "sleeve_state": c["ss"]}
    ctx = fc.Context(now=c["now"], session=c["session"], equity=c["equity"], extra=extra)
    intents, _rank = F.decide(c["bars"], ctx)
    opened, closed = [], []
    for i in intents:
        if i.kind == "enter":
            opened.append([i.symbol, i.legs[0]["symbol"], i.legs[1]["symbol"], int(i.qty_hint), round(-i.net_price, 2)])
        else:
            pos = c["ss"][i.symbol]["position"]
            so = [o for o, q in pos["legs"].items() if q < 0][0]
            lo_ = [o for o, q in pos["legs"].items() if q > 0][0]
            closed.append([i.symbol, so, lo_, int(i.qty_hint), i.reason.split(": ", 1)[1].split(" ")[0], i.net_price])
    return opened, closed


def _old_view(c, o):
    opened, closed = [], []
    ords = o["orders"]
    by_sym = {}
    for occ, side, qty, px, intent in ords:
        sym = occ[:-15]
        by_sym.setdefault(sym, []).append((occ, side, qty, px, intent))
    for sym, legs in by_sym.items():
        so = [x for x in legs if x[4] == "sell_to_open"]
        lo = [x for x in legs if x[4] == "buy_to_open"]
        if so and lo:
            opened.append([sym, so[0][0], lo[0][0], so[0][2], round(so[0][3] - lo[0][3], 2)])
        sc = [x for x in legs if x[4] == "buy_to_close"]
        lc = [x for x in legs if x[4] == "sell_to_close"]
        if sc and lc:
            closed.append([sym, sc[0][0], lc[0][0], sc[0][2], o["exits"].get(sym), round(sc[0][3] - lc[0][3], 2)])
    return opened, closed


def run():
    rnd = random.Random(1016)
    cases = [_case(rnd) for _ in range(N_CASES)]
    old = old_run(OLD, {"cases": [{k: v for k, v in c.items() if k not in ("ss", "meta", "session", "fresh")}
                                  for c in cases]})
    diffs, stats = [], {"opened": 0, "closed": {}}
    for c, o in zip(cases, old):
        po, pc = _port(c)
        oo, oc = _old_view(c, o)
        same_open = sorted(po) == sorted(oo)
        same_close = len(pc) == len(oc) and all(
            a[:5] == b[:5] and abs(a[5] - b[5]) <= 0.011 + 1e-9 for a, b in zip(sorted(pc), sorted(oc)))
        if not (same_open and same_close):
            diffs.append({"session": c["session"], "old": [oo, oc], "port": [po, pc]})
        stats["opened"] += len(oo)
        for x in oc:
            stats["closed"][x[4]] = stats["closed"].get(x[4], 0) + 1
    res = {"sleeve": "fear_premium", "cases": len(cases), "identical": len(cases) - len(diffs), "diffs": diffs[:10],
           "n_diffs": len(diffs), "stats": stats,
           "method": "old scan_pass (clock, equity, bars, basket, chain/quote/order CLIs and removed gates stubbed; "
                     "its real earnings_ok over desk/earnings.py) vs port decide()"}
    write_receipt("fear_premium", res)
    return res
