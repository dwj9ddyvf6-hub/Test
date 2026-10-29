"""spx_premium: old spx_premium.py run_entry() vs the restored port's decide() on the same case.

The OLD module runs its real run_entry(): entry_day_ok on the dates its SPY frame carries, the cooldown, the
once-a-week and open-position rails, the equity gate, prior_week_level on its own W-FRI resample, the ATR strike
rule, this week's latest put expiry, the contracts, the natural credit, and the mleg submit at -credit. Stubbed:
the clock (datetime.now -> the case), its SPY 1H frame (one bar per session carrying the level series the port
reads: S&P 500 / 10), the broker (flat), its chain / quote CLIs (the case's), equity, and the gates the cutover
removed (risk gate, drawdown brake, circuit breaker, context gate, desk cap).

Compared: the submitted spread (short, long, qty, credit) or the first skip reason."""
import random
from datetime import date, datetime, timedelta, timezone

from desk import calendar as cal
from desk.sleeves.femto import compat as fc
from desk.util import ET

from . import femto_module, old_run, write_receipt

F = femto_module("spx_premium")
N_CASES = 2500

OLD = r'''
import sys, types
from datetime import datetime as _dt, timezone
from zoneinfo import ZoneInfo
import pandas as pd
ET = ZoneInfo("America/New_York")
for name, attrs in (("desk.drawdown_brake", {"check_drawdown": lambda: ("ok", ""), "log_activation": lambda *a: None}),
                    ("desk.circuit_breaker", {"check_circuit_breaker": lambda: ("ok", "")}),
                    ("desk.context_gate", {"entries_allowed": lambda sleeve=None: (True, "")})):
    m = types.ModuleType(name); m.__dict__.update(attrs); sys.modules[name] = m
import spx_premium as O
EV = []
O.log = lambda e: EV.append(dict(e))
O._maybe_run_broker_sync = lambda st: None
O._replay_chart_gate_releases = lambda st: None
O._HAS_RISK_GATE = True
O._risk_gate = types.SimpleNamespace(evaluate_entry=lambda s, u: (True, []), blocked_reasons=lambda r: r)
O._cap_gate_entry = lambda sym, n, e: True
O.save_state = lambda s: None
O.DRY_RUN = False
class FakeDT(_dt):
    NOW = None
    @classmethod
    def now(cls, tz=None):
        return cls.NOW.astimezone(tz) if tz else cls.NOW
O.datetime = FakeDT
out = []
for case in PAYLOAD["cases"]:
    FakeDT.NOW = _dt.fromtimestamp(case["now"], tz=timezone.utc)
    st = O._blank_state()
    st.update(case["state"])
    O.load_state = lambda st=st: st
    rows = case["bars"]
    df = pd.DataFrame([{"o": r[1], "h": r[2], "l": r[3], "c": r[4]} for r in rows],
                      index=pd.to_datetime([r[0] for r in rows], unit="s", utc=True).tz_convert(ET))
    O.fetch_spy_1h = lambda limit=1500, df=df: df
    O._run_cli = lambda name, *a: []
    O.get_equity = lambda eq=case["equity"]: eq
    O.option_chain_puts = lambda gte, lte, ch=case["chain"]: [c for c in ch if gte <= c["expiration"] <= lte]
    O.option_quotes = lambda syms, q=case["quotes"]: {s: q[s] for s in syms if s in q}
    SUB = []
    def sub(short_occ, long_occ, qty, credit, cid, SUB=SUB):
        SUB.append([short_occ, long_occ, int(qty), round(float(credit), 2)])
        return {"id": "x"}
    O.submit_spread_mleg = sub
    O.get_order = lambda oid: {"filled_qty": 1, "filled_avg_price": None}
    EV.clear()
    O.run_entry()
    skip = [e.get("reason") for e in EV if e.get("event") == "entry_skipped"]
    out.append({"submit": SUB, "skip": skip[:1]})
print(json.dumps(out))
'''


def _sessions(start, end):
    d, out = start, []
    while d <= end:
        if cal.is_trading_day(d):
            out.append(d)
        d += timedelta(days=1)
    return out


def _occ(exp, k):
    return "XSP%s%s%sP%08d" % (exp[2:4], exp[5:7], exp[8:10], int(round(k * 1000)))


def _case(rnd, days, idx):
    today = days[idx]
    # the clock: mostly the week's first session from 10:00, sometimes before 10:00 or another weekday
    u = rnd.random()
    hh, mm = (10, rnd.randint(0, 59)) if u < 0.75 else ((9, rnd.randint(30, 59)) if u < 0.85 else
                                                         (rnd.randint(11, 15), rnd.randint(0, 59)))
    now = datetime(today.year, today.month, today.day, hh, mm, tzinfo=ET).timestamp()
    hist = days[max(0, idx - rnd.choice((60, 90, 300, 480))):idx + 1]
    px, spx = rnd.uniform(5000, 8000), []                    # the S&P 500 level; the old reads it / 10
    for d in hist:
        o = px * (1 + rnd.gauss(0, 0.003))
        c = o * (1 + rnd.gauss(0, 0.009))
        h, l = max(o, c) * (1 + abs(rnd.gauss(0, 0.004))), min(o, c) * (1 - abs(rnd.gauss(0, 0.004)))
        spx.append({"t": datetime(d.year, d.month, d.day, 15, 0, tzinfo=ET).timestamp(), "o": round(o, 2),
                    "h": round(h, 2), "l": round(l, 2), "c": round(c, 2)})
        px = c
    bars = [[b["t"]] + [b[k] / F.INDEX_DIV for k in ("o", "h", "l", "c")] for b in spx]
    # the port's ATR strikes, to place the chain around them (old and port compute their own)
    weekly = F.weekly_bars(spx)
    wk = F.iso_week_tuple(today)
    pc, atr = F.prior_week_level(weekly, wk)
    monday = today - timedelta(days=today.weekday())
    chain, quotes = [], {}
    if pc is not None:
        ks, kl = F.atr_level_strikes(pc, atr)
        exps = [(monday + timedelta(days=i)).isoformat() for i in range(5)
                if cal.is_trading_day(monday + timedelta(days=i)) and rnd.random() < 0.8]
        for e in exps:
            for k in range(kl - 3, ks + 4):
                if rnd.random() < 0.06 and k in (ks, kl):
                    continue                                  # a missing contract
                occ = _occ(e, k)
                chain.append({"symbol": occ, "strike": float(k), "expiration": e})
                bid = round(max(0.0, rnd.uniform(-0.05, 1.5) * (k - kl + 1) / 6), 2)
                quotes[occ] = {"bid": bid, "ask": round(bid + rnd.choice((0.01, 0.02, 0.05, 0.2)), 2)}
    state, meta, st = {}, {}, {}
    v = rnd.random()
    if v < 0.08:
        state["cooldown_until"] = meta["cooldown_until"] = F.iso_week_tuple(today + timedelta(weeks=rnd.randint(-2, 3)))
    elif v < 0.14:
        state["last_entry_week"] = meta["last_entry_week"] = wk
    elif v < 0.18:
        state["positions"] = {"2026-01-01": {"status": "open"}}
        st = {"position": {"qty": 1, "legs": {}}}
    equity = rnd.choice((rnd.uniform(30_000, 37_000), rnd.uniform(37_000, 300_000), 37_000.0))
    return {"now": now, "session": today.isoformat(), "bars": bars, "spx": spx, "chain": chain, "quotes": quotes,
            "state": state,
            "meta": meta, "st": st, "equity": equity,
            "traded": [d.isoformat() for d in hist if d >= monday] + [d.isoformat() for d in _sessions(today, monday + timedelta(days=4)) if d > today]}


def _port(c):
    chain = [dict(r, type="put", **c["quotes"].get(r["symbol"], {})) for r in c["chain"]]
    extra = {"meta": c["meta"], "spx": {"^GSPC": c["spx"]},
             "chain": {"XSP": chain}, "traded_dates": c["traded"], "sleeve_state": {"XSP": c["st"]} if c["st"] else {}}
    ctx = fc.Context(now=c["now"], session=c["session"], equity=c["equity"], extra=extra)
    intent, why, _decided = F.decide(ctx)
    if intent is None:
        return {"submit": [], "skip": [why]}
    return {"submit": [[intent.legs[0]["symbol"], intent.legs[1]["symbol"], int(intent.qty_hint),
                        round(-intent.net_price, 2)]], "skip": []}


def run():
    rnd = random.Random(20261015)
    days = _sessions(date(2024, 1, 2), date(2026, 10, 9))
    firsts = [i for i, d in enumerate(days) if i > 120 and (d.weekday() == 0 or (d.weekday() == 1 and
                                                                                 days[i - 1].weekday() == 4))]
    others = [i for i in range(121, len(days)) if i not in firsts]
    cases = [_case(rnd, days, rnd.choice(firsts) if rnd.random() < 0.8 else rnd.choice(others)) for _ in range(N_CASES)]
    old = old_run(OLD, {"cases": [{k: v for k, v in c.items() if k not in ("meta", "st", "traded", "session", "spx")}
                                  for c in cases]})
    diffs, stats = [], {"entries": 0, "skips": {}}
    for c, o in zip(cases, old):
        # the port scales the S&P 500 by 1/10 on its own; the old reads the level directly: same weekly bars
        p = _port(c)
        o = {"submit": o["submit"], "skip": [s for s in o["skip"] if s][:1]}
        if p != o:
            diffs.append({"session": c["session"], "now": c["now"], "old": o, "port": p})
        stats["entries"] += bool(o["submit"])
        for s in o["skip"]:
            stats["skips"][s] = stats["skips"].get(s, 0) + 1
    res = {"sleeve": "spx_premium", "cases": len(cases), "identical": len(cases) - len(diffs), "diffs": diffs[:10],
           "n_diffs": len(diffs), "stats": stats,
           "method": "old run_entry (clock, SPY frame, broker, chain/quote CLIs and removed gates stubbed) vs "
                     "port decide() on the same levels, chain and quotes"}
    write_receipt("spx_premium", res)
    return res
