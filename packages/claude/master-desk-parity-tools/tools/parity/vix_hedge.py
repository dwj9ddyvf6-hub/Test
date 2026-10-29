"""vix_hedge: old vix_hedge_sleeve.py scan_pass() vs the restored port's signal() on the same case.

The OLD module runs its real scan_pass(): vix_complacent on the case's ^VIX series, manage_positions (exit_due on
the held call's mid, the VIX, the days to expiry; close_hedge at the mid), then maybe_enter (pick_hedge_call over
the chain and the candidates' quotes, size_contracts, buy to open at the ask). Stubbed: the clock, the VIX fetch,
equity, the VXX daily bar (the spot), the chain / quote / order CLIs (the case's), and the gates the cutover
removed (risk gate, Decision #75 pre_buy -> proceed, desk cap); fills are not promoted (state as given).

Compared: every order (side, OCC, contracts, limit) and the exit reason."""
import random
from datetime import date, datetime, timedelta, timezone

from desk.sleeves.femto import compat as fc
from desk.util import ET

from . import femto_module, old_run, write_receipt

F = femto_module("vix_hedge")
N_CASES = 3000

OLD = r'''
import sys, types
from datetime import datetime as _dt, timezone
import vix_hedge_sleeve as O
EV = []
O.log = lambda e: EV.append(dict(e))
O.save_state = lambda s: None
O.DRY_RUN = False
O._HAS_RISK_GATE = True
O._risk_gate = types.SimpleNamespace(evaluate_entry=lambda s, u: (True, []), blocked_reasons=lambda r: r)
O.cross_sleeve_ok = lambda sym: True
O._cap_gate_entry = lambda sym, n, e: True
O.replay_chart_gate_releases = lambda st, now, equity=None: None
O.promote_fills = lambda st, now: None
d75 = types.ModuleType("desk.decision75")
d75.pre_buy = lambda *a, **k: "proceed"
sys.modules["desk.decision75"] = d75
class FakeDT(_dt):
    NOW = None
    @classmethod
    def now(cls, tz=None):
        return cls.NOW.astimezone(tz) if tz else cls.NOW
O.datetime = FakeDT
out = []
for case in PAYLOAD["cases"]:
    FakeDT.NOW = _dt.fromtimestamp(case["now"], tz=timezone.utc)
    st = O.fresh_state()
    st.update(json.loads(json.dumps(case["state"])))
    O.load_state = lambda st=st: st
    O.fetch_vix_daily = lambda c=case["vix"]: (list(c) if len(c) >= 35 else None)
    O.get_equity = lambda e=case["equity"]: e
    O.fetch_daily_bars = lambda sym, limit=30, px=case["spot"]: [{"c": px - 1}, {"c": px}]
    O.option_chain_calls = lambda sym, dte_min=60, dte_max=110, ch=case["chain"]: list(ch)
    O.option_quotes = lambda occs, q=case["quotes"]: {o: q[o] for o in occs if o in q}
    ORD = []
    def sub(occ, side, qty, limit_price, intent, cid, ORD=ORD):
        ORD.append([side, occ, int(qty), float("%.2f" % limit_price)])     # what the CLI sent: --limit-price %.2f
        return {"id": "o%d" % len(ORD), "status": "accepted"}
    O.submit_option = sub
    EV.clear()
    O.scan_pass(FakeDT.NOW)
    why = [e.get("reason") for e in EV if e.get("event") == "exit_signal"] if any(o[0] == "sell" for o in ORD) else []
    out.append({"orders": ORD, "exit": why[:1]})
print(json.dumps(out))
'''


def _occ(exp, k):
    return "VXX%s%s%sC%08d" % (exp[2:4], exp[5:7], exp[8:10], int(round(k * 1000)))


def _case(rnd):
    today = date(2026, 1, 5) + timedelta(days=rnd.randint(0, 270))
    while today.weekday() > 4:
        today += timedelta(days=1)
    now = datetime(today.year, today.month, today.day, rnd.randint(9, 15), 49, tzinfo=ET).timestamp()
    base = rnd.uniform(12, 32)
    n = rnd.choice((20, 40, 126, 126, 126))
    vix = [round(max(9.0, base + rnd.gauss(0, 3)), 2) for _ in range(n)]
    if rnd.random() < 0.3:
        vix[-1] = round(rnd.uniform(10, 15.9), 2)
    spot = round(rnd.uniform(12, 60), 2)
    chain, quotes = [], {}
    for _ in range(rnd.randint(0, 6)):
        dte = rnd.randint(40, 130)
        exp = (today + timedelta(days=dte)).isoformat()
        for k in sorted({round(spot * f, 0) for f in (0.9, 1.0, 1.1, 1.15, 1.2, 1.25, 1.3, 1.4)}):
            occ = _occ(exp, k)
            chain.append({"symbol": occ, "strike": k, "expiration": exp})
            u = rnd.random()
            if u < 0.1:
                continue                                     # no quote
            bid = round(max(0.0, rnd.uniform(-0.1, 3.0)), 2)
            quotes[occ] = {"bid": bid, "ask": round(bid + rnd.choice((0.01, 0.05, 0.1, 0.3, 0.8)), 2)}
    state, st = {}, {}
    v = rnd.random()
    if v < 0.35:                                             # a held hedge
        dte = rnd.randint(5, 100)
        exp = (today + timedelta(days=dte)).isoformat()
        occ = _occ(exp, round(spot * 1.2, 0))
        ask = round(rnd.uniform(0.3, 3.0), 2)
        cn = rnd.randint(1, 12)
        bid = round(ask * rnd.choice((0.5, 1.0, 1.9, 2.0, 2.1, 3.0)), 2)
        quotes[occ] = {"bid": bid, "ask": round(bid + rnd.choice((0.01, 0.05, 0.2)), 2)}
        if rnd.random() < 0.05:
            quotes.pop(occ)
        state["positions"] = {occ: {"occ": occ, "underlying": "VXX", "contracts": cn, "entry_debit": ask * cn * 100,
                                    "expiry": exp}}
        st = {"position": {"qty": cn, "entry_px": ask, "occ": occ, "expiry": exp}}
    equity = rnd.choice((rnd.uniform(5_000, 40_000), rnd.uniform(40_000, 400_000)))
    return {"now": now, "session": today.isoformat(), "vix": vix, "spot": spot, "chain": chain, "quotes": quotes,
            "state": state, "st": st, "equity": equity}


def _port(c):
    chain = [dict(r, type="call", **c["quotes"].get(r["symbol"], {})) for r in c["chain"]]
    held = (c["st"].get("position") or {}).get("occ")
    extra = {"vix_closes": c["vix"], "chain": {"VXX": chain},
             "option_quotes": {held: c["quotes"][held]} if held and held in c["quotes"] else {},
             "quotes": {"VXX": {"bid": None, "ask": None, "last": c["spot"]}},
             "sleeve_state": {"VXX": c["st"]} if c["st"] else {}}
    ctx = fc.Context(now=c["now"], session=c["session"], equity=c["equity"], extra=extra)
    out = F.signal({}, {}, ctx)
    orders, why = [], []
    for i in out:
        if i.kind == "enter":
            orders.append(["buy", i.legs[0]["symbol"], int(i.qty_hint), round(float(i.order["limit_price"]), 4)])
        else:
            orders.append(["sell", held, int(i.qty_hint), round(float(i.order["limit_price"]), 4)])
            why.append(i.reason.split(": ", 1)[1].split(" ")[0])
    return {"orders": orders, "exit": why}


def run():
    rnd = random.Random(1018)
    cases = [_case(rnd) for _ in range(N_CASES)]
    old = old_run(OLD, {"cases": [{k: v for k, v in c.items() if k not in ("st", "session")} for c in cases]})
    diffs, stats = [], {"entries": 0, "exits": {}}
    for c, o in zip(cases, old):
        p = _port(c)
        if p != o:
            diffs.append({"session": c["session"], "old": o, "port": p})
        stats["entries"] += sum(1 for x in o["orders"] if x[0] == "buy")
        for w in o["exit"]:
            stats["exits"][w] = stats["exits"].get(w, 0) + 1
    res = {"sleeve": "vix_hedge", "cases": len(cases), "identical": len(cases) - len(diffs), "diffs": diffs[:10],
           "n_diffs": len(diffs), "stats": stats,
           "method": "old scan_pass (clock, VIX, equity, spot, chain/quote/order CLIs and removed gates stubbed) vs "
                     "port signal() on the same case"}
    write_receipt("vix_hedge", res)
    return res
