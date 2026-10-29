"""iron_condor: old iron_condor_sleeve.py scan_pass() vs the restored port's decide() on the same case.

The OLD module runs its real scan_pass(): manage_positions (exit_due on the conservative close cost, the 7-DTE and
21-day clocks; short_leg_deep_itm, the early-assignment guard; the post-entry earnings check; close_condor at each
leg's natural), then the entry loop (live = positions + closing + pending + awaiting fills, at most 3; maybe_enter:
the VIX filter, get_iv_rank over its real IV store file -- the ATM call's Black-Scholes IV recorded once per day and
ranked against its own history, the cold start -- its real earnings_status over desk/earnings.py fed the case's
calendar, the $10 floor, build_condor, size_contracts, the four legs submitted). Stubbed: the clock, equity, the VIX
fetch, the daily bars, the chain / quote / order CLIs (the case's), and the gates the cutover removed (kill switch,
drawdown brake, circuit breaker, context gate, desk cap); fills are not promoted (state as given).

Compared: the condors opened (symbol, four legs, contracts, credit), the condors closed (symbol, contracts, reason)
and the IV observations recorded. Named divergences counted, not failed: the port records every watchlist name's IV
at the session's first pass (the old recorded only the names its entry loop evaluated); the port closes a condor
whose leg has no quote on its closing side (the old's close_condor could not); a wing quoted without a bid counts at
zero in the port's close cost (the old read it as unquoted) -- each such decision is checked against the port's own
decision under the old rule."""
import math
import random
from datetime import date, datetime, timedelta, timezone

from desk import calendar as cal
from desk.sleeves.femto import compat as fc
from desk.util import ET

from . import femto_module, old_run, write_receipt

F = femto_module("iron_condor")
N_CASES = 1200
NAMES = list(F.WATCHLIST)

OLD = r'''
import os, sys, tempfile, types
from datetime import datetime as _dt, timezone
import iron_condor_sleeve as O
import desk.earnings as E
import desk as _D
EV = []
O.log = lambda e: EV.append(dict(e))
O.save_state = lambda s: None
O.DRY_RUN = False
O.check_kill_switch = lambda sym: True
O.drawdown_allows = lambda sym: (True, 1)
O._cap_gate_entry = lambda sym, n, e: True
O.replay_chart_gate_releases = lambda st, now, equity=None: None
O.promote_fills = lambda st, now: None
O.process_flatten_queue = lambda st, now: None
O._get_order = lambda oid: None
cb = types.ModuleType("desk.circuit_breaker")
cb.check_circuit_breaker = lambda: ("ok", "")
cg = types.ModuleType("desk.context_gate")
cg.entries_allowed = lambda sleeve=None: (True, "")
sys.modules["desk.circuit_breaker"], sys.modules["desk.context_gate"] = cb, cg
_D.circuit_breaker, _D.context_gate = cb, cg
class FakeDT(_dt):
    NOW = None
    @classmethod
    def now(cls, tz=None):
        return cls.NOW.astimezone(tz) if tz else cls.NOW
O.datetime = FakeDT
E.datetime = FakeDT
O._HAS_EARN = True
O._earn = E
TMP = tempfile.mkdtemp()
def _arg(args, flag):
    return args[args.index(flag) + 1] if flag in args else None
out = []
for idx, case in enumerate(PAYLOAD["cases"]):
    FakeDT.NOW = _dt.fromtimestamp(case["now"], tz=timezone.utc)
    st = O.fresh_state()
    st.update(json.loads(json.dumps(case["state"])))
    O.load_state = lambda st=st: st
    O.get_equity = lambda e=case["equity"]: e
    O.vix_close = lambda v=case["vix"]: v
    def bars(sym, limit=300, B=case["bars"]):
        if sym not in B or len(B[sym]) < 2:
            raise RuntimeError("no daily bars for %s" % sym)
        return B[sym][-limit:]
    O.fetch_daily_bars = bars
    path = os.path.join(TMP, "iv%d.jsonl" % idx)
    with open(path, "w") as fh:
        for sym, obs in case["iv"].items():
            for d, iv in obs:
                fh.write(json.dumps({"date": d, "symbol": sym, "iv": iv}) + "\n")
    O.IV_HISTORY_PATH = path
    E.load_earnings = lambda c=case["calendar"]: dict(c)
    E.calendar_status = lambda f=case["cal_ts"]: (f, 10)
    def run_cli(script, args, timeout=90, C=case["chains"], Q=case["quotes"]):
        args = [str(a) for a in args]
        if script == "alpaca_option_chain.py":
            u, typ = _arg(args, "--underlying"), _arg(args, "--type")
            lo, hi = _arg(args, "--expiry-gte"), _arg(args, "--expiry-lte")
            if u not in C:
                raise RuntimeError("chain failed")
            return [r for r in C[u] if r["type"] == typ and lo <= r["expiration"] <= hi]
        if script == "alpaca_option_quotes.py":
            return {o: Q[o] for o in _arg(args, "--symbols").split(",") if o in Q}
        raise RuntimeError("unexpected CLI " + script)
    O.desk.run_cli = run_cli
    ORD = []
    def sub(occ, side, qty, limit, intent, cid, ORD=ORD):
        ORD.append([occ, side, int(qty), float("%.2f" % limit), intent])     # what the CLI sent: --limit-price %.2f
        return {"id": "o%d" % len(ORD), "status": "accepted"}
    O.submit_leg = sub
    EV.clear()
    O.scan_pass(FakeDT.NOW)
    today = FakeDT.NOW.astimezone(O.ET).date().isoformat()
    before = {(s, d) for s, obs in case["iv"].items() for d, _ in obs}
    rec = {}
    with open(path) as fh:
        for line in fh:
            row = json.loads(line)
            if row["date"] == today and (row["symbol"], today) not in before:
                rec[row["symbol"]] = row["iv"]
    exits = {e["symbol"]: e["reason"] for e in EV if e.get("event") == "exit_signal" and e.get("reason")}
    out.append({"orders": ORD, "exits": exits, "recorded": rec})
print(json.dumps(out))
'''


def _occ(sym, exp, kind, k):
    return "%s%s%s%s%s%08d" % (sym, exp[2:4], exp[5:7], exp[8:10], "P" if kind == "put" else "C", int(round(k * 1000)))


def _quote(rnd, fair, wide=0.0):
    """a two-sided quote around a model price: mostly inside the 10% gate, some wide, a few one-sided."""
    if fair < 0.02:
        return {"bid": 0.0, "ask": 0.05}
    h = rnd.choice((0.005, 0.01, 0.02, 0.03, 0.04, 0.06)) + wide
    bid = round(max(0.01, fair * (1 - h)), 2)
    ask = round(max(bid + 0.01, fair * (1 + h)), 2)
    if rnd.random() < 0.02:
        bid = 0.0
    return {"bid": bid, "ask": ask}


def _chain(rnd, sym, S, iv, today):
    grid = 0.5 if S < 15 else (1.0 if S < 40 else (2.5 if S < 120 else 5.0))
    rows, quotes = [], {}
    wide = rnd.choice((0.0, 0.0, 0.0, 0.04))
    for dte in sorted(rnd.sample(range(24, 56), rnd.randint(1, 4))):
        exp = (today + timedelta(days=dte)).isoformat()
        T = dte / 365.0
        k = max(grid, math.floor(S * 0.4 / grid) * grid)
        while k <= S * 1.8:
            for kind in ("put", "call"):
                occ = _occ(sym, exp, kind, k)
                rows.append({"symbol": occ, "strike": k, "expiration": exp, "type": kind})
                if rnd.random() < 0.97:
                    quotes[occ] = _quote(rnd, F.bs_price(S, k, T, F.RISK_FREE, iv * rnd.uniform(0.97, 1.03), kind)
                                         or 0.0, wide)
            k = round(k + grid, 4)
    return rows, quotes


def _bars(rnd, end, S):
    days, d = [], end
    while len(days) < 30:
        if cal.is_trading_day(d):
            days.append(d)
        d -= timedelta(days=1)
    out, px = [], S * rnd.uniform(0.8, 1.2)
    for i, dd in enumerate(reversed(days)):
        px = S if i == len(days) - 1 else px * (1 + rnd.gauss(0, 0.03))
        out.append({"t": datetime(dd.year, dd.month, dd.day, 4, tzinfo=timezone.utc).timestamp(), "o": px,
                    "h": px * 1.02, "l": px * 0.98, "c": round(px, 2), "v": 1e6})
    return out


def _history(rnd, sym, today, iv_now):
    n = rnd.choice((0, 20, 59, 60, 61, 90, 180, 252, 300))
    base_lo = iv_now * rnd.uniform(0.5, 1.1)
    base_hi = base_lo * rnd.uniform(1.05, 2.0)
    obs, d = [], cal.prev_trading_day(today)
    for _ in range(n):
        obs.append([d.isoformat(), round(rnd.uniform(base_lo, base_hi), 6)])
        d = cal.prev_trading_day(d)
    obs.reverse()
    if n and rnd.random() < 0.1:                             # a later pass of a session already observed
        obs.append([today.isoformat(), round(iv_now * rnd.uniform(0.95, 1.05), 6)])
    return obs


def _held(rnd, sym, S0, today, now, quotes):
    """a held condor (or one closing): legs on a 16 / 5-delta-like grid, the underlying moved since entry."""
    dte = rnd.randint(3, 44)
    exp = (today + timedelta(days=dte)).isoformat()
    grid = 0.5 if S0 < 15 else (1.0 if S0 < 40 else 2.5)
    ps = round(S0 * 0.85 / grid) * grid
    pl = ps - grid * rnd.randint(1, 4)
    cs = round(S0 * 1.15 / grid) * grid
    cl = cs + grid * rnd.randint(1, 4)
    occs = {"put_short": _occ(sym, exp, "put", ps), "put_long": _occ(sym, exp, "put", pl),
            "call_short": _occ(sym, exp, "call", cs), "call_long": _occ(sym, exp, "call", cl)}
    S = S0 * rnd.choice((1.0, rnd.uniform(0.7, 1.3), rnd.uniform(0.95, 1.05)))
    iv, T = rnd.uniform(0.3, 1.2), max(dte, 1) / 365.0
    for leg, occ in occs.items():
        kind = "put" if leg.startswith("put") else "call"
        K = {"put_short": ps, "put_long": pl, "call_short": cs, "call_long": cl}[leg]
        if rnd.random() < 0.95:
            quotes[occ] = _quote(rnd, F.bs_price(S, K, T, F.RISK_FREE, iv, kind) or 0.0)
    fair = sum((F.bs_price(S0, K, T + 0.05, F.RISK_FREE, iv, kd) or 0.0) * sg for K, kd, sg in
               ((ps, "put", 1), (pl, "put", -1), (cs, "call", 1), (cl, "call", -1)))
    credit = round(max(0.05, fair * rnd.uniform(0.5, 1.5)), 2)
    condor = {"put_short_occ": occs["put_short"], "put_long_occ": occs["put_long"],
              "call_short_occ": occs["call_short"], "call_long_occ": occs["call_long"],
              "put_short_strike": ps, "put_long_strike": pl, "call_short_strike": cs, "call_long_strike": cl,
              "expiry": exp, "dte": dte, "credit": credit, "width": max(ps - pl, cl - cs),
              "max_loss": round((max(ps - pl, cl - cs) - credit) * 100, 2)}
    n = rnd.randint(1, 8)
    opened = now - rnd.randint(0, 25) * 86400 - rnd.randint(0, 80000)
    return S, condor, n, credit, opened


def _case(rnd):
    today = date(2026, 1, 5) + timedelta(days=rnd.randint(0, 260))
    while not cal.is_trading_day(today):
        today += timedelta(days=1)
    now = datetime(today.year, today.month, today.day, rnd.randint(10, 15), 31, tzinfo=ET).timestamp()
    bars, chains, quotes, ivs = {}, {}, {}, {}
    state = {"positions": {}, "awaiting_fills": {}, "closing": {}, "pending": {}}
    ss = {}
    for sym in NAMES:
        S = rnd.choice((rnd.uniform(4, 12), rnd.uniform(10, 60), rnd.uniform(30, 160)))
        iv = rnd.uniform(0.35, 1.3)
        u = rnd.random()
        if u < 0.08:
            continue                                             # no bars, no chain
        if u < 0.2:                                              # held / in flight
            if rnd.random() < 0.25:
                state["awaiting_fills"][sym] = {"ticker": sym}
                ss[sym] = {"position": None, "pending_entry": {"qty": 1}}
            else:
                S, condor, n, credit, opened = _held(rnd, sym, S, today, now, quotes)
                legs = {condor["put_short_occ"]: -n, condor["put_long_occ"]: n, condor["call_short_occ"]: -n,
                        condor["call_long_occ"]: n}
                pos = {"ticker": sym, "condor": condor, "contracts": n, "entry_credit": credit,
                       "entry_ts": datetime.fromtimestamp(opened, tz=timezone.utc).isoformat()}
                port = {"qty": n, "net_entry": -credit, "opened_at": opened, "legs": legs, "condor": condor}
                if rnd.random() < 0.15:
                    state["closing"][sym] = pos
                    port["exit_submitted"] = True
                else:
                    state["positions"][sym] = pos
                ss[sym] = {"position": port}
        bars[sym] = _bars(rnd, today, round(S, 2))
        S = bars[sym][-1]["c"]
        if rnd.random() < 0.92:
            rows, q = _chain(rnd, sym, S, iv, today)
            chains[sym] = rows
            quotes.update(q)
        ivs[sym] = _history(rnd, sym, today, iv)
    calendar = {}
    for sym in NAMES:
        u = rnd.random()
        if u < 0.08:
            continue                                             # absent: unknown
        calendar[sym] = None if u < 0.3 else (today + timedelta(days=rnd.randint(-5, 90))).isoformat()
    fresh = rnd.random() < 0.92
    cal_ts = (datetime.fromtimestamp(now, tz=timezone.utc) - timedelta(days=2 if fresh else 9)).isoformat()
    vix = None if rnd.random() < 0.05 else round(rnd.choice((rnd.uniform(12, 30), rnd.uniform(30, 45))), 2)
    equity = rnd.choice((rnd.uniform(20_000, 100_000), rnd.uniform(100_000, 3_000_000)))
    return {"now": now, "session": today.isoformat(), "bars": bars, "chains": chains, "quotes": quotes, "iv": ivs,
            "calendar": calendar, "cal_ts": cal_ts, "fresh": fresh, "vix": vix, "state": state, "ss": ss,
            "equity": equity}


def _port(c):
    today = date.fromisoformat(c["session"])
    lo, hi = (today + timedelta(days=30)).isoformat(), (today + timedelta(days=45)).isoformat()
    chains = {s: [dict(r, **c["quotes"].get(r["symbol"], {})) for r in rows if lo <= r["expiration"] <= hi]
              for s, rows in c["chains"].items()}
    held = {o for st in c["ss"].values() for o in ((st.get("position") or {}).get("legs") or {})}
    extra = {"meta": {"iv": c["iv"]}, "chains": chains,
             "option_quotes": {o: c["quotes"][o] for o in held if o in c["quotes"]}, "quotes": {},
             "earnings": c["calendar"], "earnings_fresh": c["fresh"], "vix": c["vix"], "sleeve_state": c["ss"]}
    ctx = fc.Context(now=c["now"], session=c["session"], equity=c["equity"], extra=extra)
    intents, updates = F.decide(c["bars"], ctx)
    opened, closed = [], []
    for i in intents:
        if i.kind == "enter":
            opened.append([i.symbol] + [l["symbol"] for l in i.legs] + [int(i.qty_hint), round(-i.net_price, 2)])
        else:
            closed.append([i.symbol, int(i.qty_hint), i.reason.split(": ", 1)[1].split(" ")[0]])
    rec = {s: obs[-1][1] for s, obs in updates.items() if obs and obs[-1][0] == c["session"]}
    return opened, closed, rec


def _old_rule_reason(c, sym):
    """the port's exit decision on this condor with the old close-cost rule (a wing without a bid = unquoted)."""
    cd = F.held_condor(c["ss"][sym]["position"])
    lqs = F.leg_quotes(cd, c["quotes"])
    cost = None if any(lqs[w]["bid"] <= 0 for w in ("put_long", "call_long")) else F.close_cost_of(lqs)
    why = F.exit_due(cd, c["now"], c["session"], cost)
    if why is None and F.short_leg_deep_itm(cd, lqs, F.spot_of(sym, {}, c["bars"]), c["session"])[0]:
        why = "assignment_guard_deep_itm"
    if why is None and F.earnings_status(sym, c["calendar"], c["fresh"], c["session"]) == "blocked":
        why = "earnings_entered_window"
    return why


def _old_view(c, o):
    opened, closed = [], []
    by_sym = {}
    for occ, side, qty, px, intent in o["orders"]:
        by_sym.setdefault(occ[:-15], []).append((occ, side, qty, px, intent))
    for sym, legs in by_sym.items():
        op = {x[4]: [] for x in legs}
        for x in legs:
            op[x[4]].append(x)
        if "sell_to_open" in op:
            (ps, cs), (pl, cl) = op["sell_to_open"][:2], op["buy_to_open"][:2]
            opened.append([sym, ps[0], cs[0], pl[0], cl[0], ps[2], round(ps[3] + cs[3] - pl[3] - cl[3], 2)])
        if "buy_to_close" in op:
            closed.append([sym, op["buy_to_close"][0][2], o["exits"].get(sym)])
    return opened, closed


def run():
    rnd = random.Random(1016)
    cases = [_case(rnd) for _ in range(N_CASES)]
    old = old_run(OLD, {"cases": [{k: v for k, v in c.items() if k not in ("ss", "session", "fresh")}
                                  for c in cases]})
    diffs, stats = [], {"opened": 0, "closed": {}, "recorded": 0, "port_only_records": 0,
                        "old_close_blocked_one_sided": 0, "wing_bid_zero_decisions": 0}
    for c, o in zip(cases, old):
        po, pc, prec = _port(c)
        oo, oc = _old_view(c, o)
        pex, oex = {x[0]: x[2] for x in pc}, dict(o["exits"])
        # a wing quoted without a bid counts at zero in the port's close cost (named): the decisions that differ
        # only by it must be the port's own decision under the old rule
        wing0 = {s for s in set(pex) | set(oex) if pex.get(s) != oex.get(s) and _old_rule_reason(c, s) == oex.get(s)}
        # the old could not close a condor with a leg unquoted on its closing side: the exit fired, no orders
        blocked = [x for x in pc if x[0] in oex and x[0] not in wing0 and x[0] not in {y[0] for y in oc}]
        bad = []
        if sorted(po) != sorted(oo):
            bad.append("opened")
        if sorted(x for x in pc if x not in blocked and x[0] not in wing0) != sorted(oc) or \
                any(pex.get(s) != oex.get(s) for s in set(pex) | set(oex) if s not in wing0):
            bad.append("closed")
        orec = o["recorded"]
        if any(s not in prec or abs(prec[s] - v) > 1e-9 for s, v in orec.items()):
            bad.append("recorded")
        if bad:
            diffs.append({"session": c["session"], "what": bad, "old": [oo, oc, orec], "port": [po, pc, prec]})
        stats["opened"] += len(oo)
        stats["recorded"] += len(orec)
        stats["port_only_records"] += len(set(prec) - set(orec))
        stats["old_close_blocked_one_sided"] += len(blocked)
        stats["wing_bid_zero_decisions"] += len(wing0)
        for x in oc:
            stats["closed"][x[2]] = stats["closed"].get(x[2], 0) + 1
    res = {"sleeve": "iron_condor", "cases": len(cases), "identical": len(cases) - len(diffs), "diffs": diffs[:10],
           "n_diffs": len(diffs), "stats": stats,
           "method": "old scan_pass (clock, equity, VIX, bars, chain/quote/order CLIs and removed gates stubbed; its "
                     "real IV store file, get_iv_rank and earnings_status over desk/earnings.py) vs port decide()"}
    write_receipt("iron_condor", res)
    return res
