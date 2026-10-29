"""leaps_momentum: old leaps_momentum.py mirror_pass() + pmcc_pass() vs the restored port's decide() on the same case.

The OLD module runs its real passes in the old cron's order: mirror_pass (read_momentum_book over a momentum state
file -- its staleness rule --, manage_leaps: leaps_exit_due, close_leaps with the covered calls first; then the
entry loop in the book's order: _slot_count, maybe_enter_leaps, find_leaps_contract, size_leaps_contracts, the buy
at the ask), then pmcc_pass (manage_pmcc_shorts: the 21-DTE / tested roll at the mid; ensure_pmcc_shorts:
select_pmcc_short over the realized vol, sold at the bid). Stubbed: the clock, equity, the spot, the daily bars,
the chain / quote / order CLIs (the case's), state load/save, and the gates the cutover removed (kill switch,
earnings blackout, cross-sleeve check, Decision #75 pre_buy -> proceed, desk cap); fills are not promoted (state
as given, shared by the two passes as the old's save/load would).

Compared: every order (contract, side, contracts, limit price, intent) -- the port's package close expanded into
its legs at the old's leg prices, its net checked against them -- and every exit's and roll's reason. Named
divergences counted, not failed, each verified: the slots (the old also counted in-flight covered-call orders: the
port's decision under the old count is the baseline), an exit-due LEAPS without a bid (the old could also sell a
fresh call or buy a call back twice) and an exit-due LEAPS whose call is already being bought back (the port waits;
the old re-sent the buy-back, sold the LEAPS and bought the name again): on such a name the port's orders must be among the old's and the
old's extra orders only of the kinds named."""
import math
import random
from datetime import date, datetime, timedelta, timezone

from desk import calendar as cal
from desk.sleeves.femto import compat as fc
from desk.util import ET

from . import femto_module, old_run, write_receipt

F = femto_module("leaps_momentum")
N_CASES = 1500
NAMES = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG", "HHH", "III", "JJJ", "KKK", "LLL"]

OLD = r'''
import os, sys, tempfile, types
from datetime import datetime as _dt, timezone
import leaps_momentum as O
import desk as _D
EV = []
O.log = lambda e: EV.append(dict(e))
O.save_state = lambda s: None
O.DRY_RUN = False
O.earnings_ok = lambda sym: True
O.cross_sleeve_ok = lambda sym: True
O.check_kill_switch = lambda sym: True
O._cap_gate_entry = lambda sym, n, e: True
O.replay_chart_gate_releases = lambda st, now: None
O.promote_fills = lambda st, now: None
O._get_order = lambda oid: None
d75 = types.ModuleType("desk.decision75")
d75.pre_buy = lambda *a, **k: "proceed"
sys.modules["desk.decision75"] = d75
_D.decision75 = d75
class FakeDT(_dt):
    NOW = None
    @classmethod
    def now(cls, tz=None):
        return cls.NOW.astimezone(tz) if tz else cls.NOW
O.datetime = FakeDT
TMP = tempfile.mkdtemp()
out = []
for idx, case in enumerate(PAYLOAD["cases"]):
    FakeDT.NOW = _dt.fromtimestamp(case["now"], tz=timezone.utc)
    st = O.fresh_state()
    st.update(json.loads(json.dumps(case["state"])))
    O.load_state = lambda st=st: st
    O.get_equity = lambda e=case["equity"]: e
    path = os.path.join(TMP, "mom%d.json" % idx)
    if case["mom_file"] is not None:
        with open(path, "w") as fh:
            json.dump(case["mom_file"], fh)
    O.MOMENTUM_STATE_PATH = path
    O._get_stock_price = lambda t, S=case["spot"]: S.get(t)
    def chain(ticker, expiry_gte=None, expiry_lte=None, option_type="call", C=case["chains"]):
        return [dict(r) for r in C.get(ticker, []) if (expiry_gte is None or r["expiration"] >= expiry_gte)
                and (expiry_lte is None or r["expiration"] <= expiry_lte)]
    O.get_option_chain = chain
    O.get_option_quote = lambda occ, Q=case["quotes"]: (dict(Q[occ]) if occ in Q else None)
    def bars(sym, limit=60, B=case["bars"]):
        if sym not in B or len(B[sym]) < 2:
            raise RuntimeError("no daily bars for %s" % sym)
        return B[sym][-limit:]
    O.fetch_daily_bars = bars
    ORD = []
    def sub(occ, side, qty, limit_price, intent, cid, ORD=ORD):
        ORD.append([occ, side, int(qty), round(float(limit_price), 6), intent])
        return {"id": "o%d" % len(ORD), "status": "accepted"}
    O.submit_leg = sub
    EV.clear()
    O.mirror_pass(FakeDT.NOW)
    O.pmcc_pass(FakeDT.NOW)
    exits = {e["symbol"]: e["reason"] for e in EV if e.get("event") == "exit_signal"}
    rolls = {e["occ"]: e["reason"] for e in EV if e.get("event") == "pmcc_roll_signal"}
    out.append({"orders": ORD, "exits": exits, "rolls": rolls})
print(json.dumps(out))
'''


def _occ(sym, exp, k):
    return "%s%s%s%sC%08d" % (sym, exp[2:4], exp[5:7], exp[8:10], int(round(k * 1000)))


def _bs_call(S, K, T, sigma, r=0.04):
    if T <= 0:
        return max(0.0, S - K)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    n = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
    return S * n(d1) - K * math.exp(-r * T) * n(d2)


def _quote(rnd, fair, wide=0.0):
    if rnd.random() < 0.03:
        return {"bid": 0.0, "ask": round(max(0.05, fair), 2)}
    h = rnd.choice((0.004, 0.008, 0.012, 0.02, 0.03)) + wide
    bid = round(max(0.01, fair * (1 - h)), 2)
    ask = round(max(bid + 0.01, fair * (1 + h)), 2)
    if rnd.random() < 0.01:
        bid, ask = ask, bid                                  # a crossed quote
    return {"bid": bid, "ask": ask}


def _chain(rnd, sym, S, iv, today, quotes):
    grid = 1.0 if S < 40 else (2.5 if S < 150 else 5.0)
    rows = []
    wide = rnd.choice((0.0, 0.0, 0.0, 0.03))
    dtes = sorted(set(rnd.sample(range(330, 800), rnd.randint(1, 3)) + rnd.sample(range(18, 46), rnd.randint(1, 3))))
    for dte in dtes:
        exp = (today + timedelta(days=dte)).isoformat()
        k = max(grid, math.floor(S * 0.5 / grid) * grid)
        while k <= S * 1.6:
            occ = _occ(sym, exp, k)
            rows.append({"symbol": occ, "strike": k, "expiration": exp, "type": "call"})
            if rnd.random() < 0.97:
                quotes[occ] = _quote(rnd, _bs_call(S, k, dte / 365.0, iv), wide)
            k = round(k + grid, 4)
    return rows


def _bars(rnd, end, S, n):
    days, d = [], end
    while len(days) < n:
        if cal.is_trading_day(d):
            days.append(d)
        d -= timedelta(days=1)
    vol = rnd.uniform(0.01, 0.05)
    out, px = [], S
    closes = [S]
    for _ in range(n - 1):
        px = px / (1 + rnd.gauss(0, vol))
        closes.append(px)
    closes.reverse()
    for dd, c in zip(reversed(days), closes):
        out.append({"t": datetime(dd.year, dd.month, dd.day, 4, tzinfo=timezone.utc).timestamp(), "o": c,
                    "h": c * 1.01, "l": c * 0.99, "c": round(c, 4), "v": 1e6})
    out[-1]["c"] = S
    return out


def _case(rnd):
    today = date(2026, 1, 5) + timedelta(days=rnd.randint(0, 260))
    while not cal.is_trading_day(today):
        today += timedelta(days=1)
    now = datetime(today.year, today.month, today.day, rnd.randint(10, 15), 37, tzinfo=ET).timestamp()
    spot, bars, chains, quotes = {}, {}, {}, {}
    for sym in NAMES:
        S = round(rnd.uniform(15, 400), 2)
        if rnd.random() < 0.05:
            continue                                         # no price, no bars
        spot[sym] = S
        bars[sym] = _bars(rnd, today, S, rnd.choice((35, 35, 35, 15)))
        if rnd.random() < 0.93:
            chains[sym] = _chain(rnd, sym, S, rnd.uniform(0.2, 0.8), today, quotes)
    state = {"positions": {}, "closing": {}, "awaiting_fills": {}, "pending": {}}
    legs, pending = {}, []
    held = rnd.sample(NAMES, rnd.randint(0, 7))
    for sym in held:
        S = spot.get(sym) or rnd.uniform(20, 300)
        exp = (today + timedelta(days=rnd.choice((rnd.randint(30, 70), rnd.randint(200, 700))))).isoformat()
        K = round(S * rnd.uniform(0.6, 0.95), 0)
        n = rnd.randint(1, 5)
        prem = round(max(0.5, (S - K) * rnd.uniform(0.9, 1.6)), 2)
        occ = _occ(sym, exp, K)
        mid = prem * rnd.choice((1.0, rnd.uniform(0.5, 0.9), rnd.uniform(0.9, 1.4)))
        if rnd.random() < 0.95:
            quotes[occ] = _quote(rnd, mid)
            if rnd.random() < 0.04:
                quotes[occ]["bid"] = 0.0                     # an exit-due LEAPS without a bid
        pos = {"symbol": sym, "occ": occ, "contracts": n, "shares_equiv": n * 100, "entry_premium": prem,
               "leaps_strike": K, "expiry": exp, "entry_ts": "x", "pmcc_shorts": []}
        legs[occ] = {"qty": float(n), "avg": prem, "opened_at": now - 86400 * 30,
                     "meta": {"role": "leaps", "sym": sym, "strike": K, "expiry": exp}}
        u = rnd.random()
        if u < 0.55:                                         # a covered call on
            sexp = (today + timedelta(days=rnd.randint(5, 38))).isoformat()
            SK = round(S * rnd.uniform(0.95, 1.2), 0)
            socc = _occ(sym, sexp, SK)
            if socc == occ:
                SK += 1
                socc = _occ(sym, sexp, SK)
            sc = n if rnd.random() < 0.92 else max(1, n - 1)
            if rnd.random() < 0.95:
                quotes[socc] = _quote(rnd, max(0.05, _bs_call(S, SK, max(1, (date.fromisoformat(sexp) - today).days)
                                                              / 365.0, 0.4)))
            sh = {"occ": socc, "contracts": sc, "entry_credit": 1.0, "strike": SK, "expiry": sexp, "entry_ts": "x"}
            legs[socc] = {"qty": -float(sc), "avg": 1.0, "opened_at": now - 86400 * 5,
                          "meta": {"role": "pmcc", "sym": sym, "strike": SK, "expiry": sexp}}
            if rnd.random() < 0.08:                          # a roll's buy-back already working
                sh["closing"] = True
                state["awaiting_fills"]["rollclose:%s:%s" % (sym, socc)] = {"kind": "pmcc_roll_close", "symbol": sym,
                                                                             "occ": socc, "contracts": sc}
                pending.append({"action": "exit", "occ": socc, "key": "%s:x:pmcc-roll" % sym})
            pos["pmcc_shorts"].append(sh)
        elif u < 0.62:
            state["awaiting_fills"]["pmcc:%s:X" % sym] = {"kind": "pmcc_short", "symbol": sym, "occ": "X",
                                                          "contracts": n}
            pending.append({"action": "enter", "occ": "X", "key": "pmcc:%s:X:d" % sym})
        if rnd.random() < 0.1:                               # its close already working
            state["closing"][sym] = pos
            pending.append({"action": "exit", "occ": occ, "key": "%s:x:leaps-exit" % sym})
            pending += [{"action": "exit", "occ": s["occ"], "key": "%s:x:leaps-exit" % sym} for s in pos["pmcc_shorts"]
                        if not s.get("closing")]
        else:
            state["positions"][sym] = pos
    for sym in rnd.sample([s for s in NAMES if s not in held], rnd.randint(0, 2)):
        state["awaiting_fills"]["leaps:%s" % sym] = {"kind": "leaps", "symbol": sym, "occ": "Y", "contracts": 1}
        pending.append({"action": "enter", "occ": "Y", "key": "leaps:%s:Y:d" % sym})
    # the momentum book: names in fill order; fresh, stale, undated, empty or missing
    book = {}
    for sym in rnd.sample(NAMES, rnd.randint(0, 10)):
        book[sym] = {"qty": rnd.choice((0, 30, 100, 150, 420, 1000)), "entry_px": 1.0, "entry_date": "x"}
    u = rnd.random()
    ran = None
    if u < 0.75:
        age = rnd.choice((0, 1, 3, 7, 8))
        rd = today - timedelta(days=age)
        ran = datetime(rd.year, rd.month, rd.day, 16, 5, tzinfo=ET).timestamp()
        mom_file = {"book": book, "last_rank_date": rd.isoformat()}
    elif u < 0.82:
        mom_file = {"book": book}                            # undated
    elif u < 0.9:
        mom_file = {"book": {}, "last_rank_date": today.isoformat()}
        book = {}
    else:
        mom_file, book = None, {}
    port_mom = None if mom_file is None else {"book": {s: {"qty": r["qty"]} for s, r in book.items()}, "ran_at": ran}
    equity = rnd.choice((rnd.uniform(20_000, 150_000), rnd.uniform(150_000, 2_000_000)))
    return {"now": now, "session": today.isoformat(), "spot": spot, "bars": bars, "chains": chains, "quotes": quotes,
            "state": state, "mom_file": mom_file, "equity": equity, "legs": legs, "pending": pending,
            "port_mom": port_mom}


def _port(c, extra_slots=0):
    today = date.fromisoformat(c["session"])
    lo = (today + timedelta(days=365)).isoformat()
    plo, phi = (today + timedelta(days=25)).isoformat(), (today + timedelta(days=38)).isoformat()
    q = c["quotes"]
    leaps = {s: [dict(r, **q.get(r["symbol"], {})) for r in rows if r["expiration"] >= lo] for s, rows in
             c["chains"].items()}
    pmcc = {s: [dict(r, **q.get(r["symbol"], {})) for r in rows if plo <= r["expiration"] <= phi] for s, rows in
            c["chains"].items()}
    extra = {"momentum": c["port_mom"], "legs": c["legs"], "pending": c["pending"], "leaps_chains": leaps,
             "pmcc_chains": pmcc, "option_quotes": {o: q[o] for o in c["legs"] if o in q},
             "quotes": {s: {"last": px} for s, px in c["spot"].items()}}
    ctx = fc.Context(now=c["now"], session=c["session"], equity=c["equity"], extra=extra)
    orig = F.slots_used
    if extra_slots:
        F.slots_used = lambda *a: orig(*a) + extra_slots
    try:
        intents = F.decide({s: bl[-35:] for s, bl in c["bars"].items()}, ctx)
    finally:
        F.slots_used = orig
    return intents


def _orders(c, intents):
    """the port's intents as the old's single-leg orders (a package expanded at the old's leg prices)."""
    oq = c["quotes"]
    out, bad, reasons = [], [], {}
    for i in intents:
        if i.kind == "enter":
            l = i.legs[0]
            out.append([l["symbol"], l["side"], int(i.qty_hint), round(float(i.order["limit_price"]), 6),
                        l["position_intent"]])
            continue
        tag, why = i.reason.split(": ", 1)[0], i.reason.split(": ", 1)[1].split(" ")[0]
        if len(i.legs) == 1:
            occ = i.legs[0]["symbol"]
            short = c["legs"][occ]["qty"] < 0
            out.append([occ, "buy" if short else "sell", int(i.qty_hint), round(float(i.order["limit_price"]), 6),
                        "buy_to_close" if short else "sell_to_close"])
        else:
            net = 0.0
            for l in i.legs:
                occ = l["symbol"]
                qq = oq.get(occ) or {}
                if c["legs"][occ]["qty"] < 0:
                    px = (float(qq.get("bid") or 0) + float(qq.get("ask") or 0)) / 2
                    out.append([occ, "buy", int(i.qty_hint), round(px, 6), "buy_to_close"])
                    net += px
                else:
                    b, a = float(qq.get("bid") or 0), float(qq.get("ask") or 0)
                    px = b if why == "stop_minus30pct" else (b + a) / 2
                    out.append([occ, "sell", int(i.qty_hint), round(px, 6), "sell_to_close"])
                    net -= px
            if abs(net - float(i.net_price)) > 1e-9:
                bad.append("package net")
        reasons.setdefault(tag, {})[i.symbol if tag.endswith("exit") else i.legs[0]["symbol"]] = why
    return out, bad, reasons


def run():
    rnd = random.Random(1016)
    cases = [_case(rnd) for _ in range(N_CASES)]
    old = old_run(OLD, {"cases": [{k: c[k] for k in ("now", "state", "equity", "mom_file", "spot", "chains", "quotes",
                                                     "bars")} for c in cases]})
    diffs = []
    stats = {"entries": 0, "pmcc_sales": 0, "exits": {}, "rolls": {}, "slots_old_count": 0, "exit_due_no_bid": 0,
             "call_rebuy_waits": 0}
    for c, o in zip(cases, old):
        po, bad, reasons = _orders(c, _port(c))
        oo = sorted(list(x) for x in o["orders"])
        # the slots: the port's decision under the old's count (in-flight covered-call orders included)
        extra = sum(1 for k in c["state"]["awaiting_fills"] if not k.startswith("leaps:"))
        po_r = sorted(_orders(c, _port(c, extra))[0]) if extra else sorted(po)
        if po_r != sorted(po):
            stats["slots_old_count"] += 1
        # an exit-due LEAPS without a bid, or with a call already being bought back: the port's orders on such a
        # name must be among the old's, and the old's extra orders only the ones named
        nobid, rebuy = set(), set()
        for sym, pos in c["state"]["positions"].items():
            if sym not in o["exits"]:
                continue
            if any(sh.get("closing") for sh in pos["pmcc_shorts"]):
                rebuy.add(sym)
            elif float((c["quotes"].get(pos["occ"]) or {}).get("bid") or 0) <= 0:
                nobid.add(sym)
        special = nobid | rebuy
        rest_o = [x for x in oo if x[0][:3] not in special]
        rest_p = [x for x in po_r if x[0][:3] not in special]
        sp_o = [x for x in oo if x[0][:3] in special]
        sp_p = [x for x in po_r if x[0][:3] in special]
        ok_special = all(x in sp_o for x in sp_p) and all(
            x in sp_p or (x[0][:3] in nobid and x[4] in ("sell_to_open", "buy_to_close"))
            or (x[0][:3] in rebuy and x[4] in ("buy_to_close", "sell_to_close", "buy_to_open")) for x in sp_o)
        if rest_o != rest_p or not ok_special:
            bad.append("orders")
        else:
            stats["exit_due_no_bid"] += len({x[0][:3] for x in sp_o if x[0][:3] in nobid and x not in sp_p})
            stats["call_rebuy_waits"] += len({x[0][:3] for x in sp_o if x[0][:3] in rebuy and x not in sp_p})
        for sym, why in (reasons.get("leaps_momentum exit") or {}).items():
            if o["exits"].get(sym) != why:
                bad.append("exit reason %s" % sym)
        for occ, why in (reasons.get("leaps_momentum pmcc_roll") or {}).items():
            if o["rolls"].get(occ) != why:
                bad.append("roll reason %s" % occ)
        if bad:
            diffs.append({"session": c["session"], "what": bad, "old": oo, "port": sorted(po)})
        for x in oo:
            if x[4] == "buy_to_open":
                stats["entries"] += 1
            elif x[4] == "sell_to_open":
                stats["pmcc_sales"] += 1
        for r in o["exits"].values():
            stats["exits"][r] = stats["exits"].get(r, 0) + 1
        for r in o["rolls"].values():
            stats["rolls"][r] = stats["rolls"].get(r, 0) + 1
    res = {"sleeve": "leaps_momentum", "cases": len(cases), "identical": len(cases) - len(diffs),
           "diffs": diffs[:10], "n_diffs": len(diffs), "stats": stats,
           "method": "old mirror_pass + pmcc_pass (clock, equity, spot, bars, chain/quote/order CLIs, state and "
                     "removed gates stubbed; its real read_momentum_book over a state file) vs port decide()"}
    write_receipt("leaps_momentum", res)
    return res
