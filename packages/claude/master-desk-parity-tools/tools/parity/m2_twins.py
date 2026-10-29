"""beatendown + confluence: old mode_rank (Friday) and mode_fill (Monday) vs the restored twins (m2_core).

Per case one synthetic week: qualifier rows (tools/parity/m2_features._case — mapped / unmapped symbols, ETF
series with holes, short daily histories), the weekly ETF closes and each name's daily bars. The OLD rank
computes its own features (its compute_features over the ETF series and its own daily window: beatendown
through the rank Friday, confluence before it), the port ranks the M2 job's precomputed feat_bd / feat_cf.
The OLD fill runs with the desk gates proceeding (risk gate, Decision #75 flags off, context gate, drawdown
brake, 150% cap; no working orders at the broker) on stubbed quotes (fresh / stale / pre-10:00 / one-sided),
VIX (fresh / stale / missing), FOMC and year-end Mondays and beatendown's fear gate. Compared: the staged
buys / sells / target and the selected rows (symbol, count, rules), then the sells (symbol, qty) and buys
(symbol, qty) submitted."""
import os
import random
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from desk.feedlib import m2
from desk.sleeves.femto import compat as fc

from . import femto_module, old_run, write_receipt
from .m2_features import _case

ET = ZoneInfo("America/New_York")
N_CASES = 24
TWINS = {"beatendown": ((16, 20), (10, 20)), "confluence": ((16, 5), (10, 0))}

OLD = r'''
import sys, types
from datetime import datetime
from zoneinfo import ZoneInfo
ET = ZoneInfo("America/New_York")
sys.argv = ["x"]
import desk as _pkg


def mod(name, **fns):
    m = types.ModuleType("desk." + name)
    for k, v in fns.items():
        setattr(m, k, v)
    sys.modules["desk." + name] = m
    setattr(_pkg, name, m)


FEAR = [True]
mod("decision75", _flags=lambda: (False, False), pre_buy=lambda *a, **k: "proceed", sweep_releases=lambda *a, **k: [])
mod("context_gate", entries_allowed=lambda sleeve=None: (True, ""))
mod("drawdown_brake", check_drawdown=lambda: ("ok", ""), log_activation=lambda *a, **k: None)
mod("desk_exposure", clamp_exit_qty=lambda sym, q, sleeve=None: (q, ""), read_exposure=lambda: {},
    check_cap=lambda equity, add, data=None: (True, 0.0, 0.0))
mod("sentiment", fear_gate_ok=lambda: (FEAR[0], "stub"))
mod("judgment_telemetry", screen_out=lambda *a, **k: None)
import importlib
out = []
for c in PAYLOAD["cases"]:
    O = importlib.import_module(c["module"])
    O._HAS_RISK_GATE = True
    O._risk_gate = types.SimpleNamespace(evaluate_entry=lambda *a, **k: (True, []), blocked_reasons=lambda r: r)
    O._HAS_DESK_EXPOSURE = True
    O._desk_exposure = sys.modules["desk.desk_exposure"]
    STATE = {"book": c["book"], "pending": {}, "pending_entry": c["pending_entry"], "pending_exit": {}, "stats": {}}
    O.load_state = lambda STATE=STATE: STATE
    O.save_state = lambda s: None
    O.log = lambda e: None
    O.universe_symbols = lambda: []
    O.run_qualifiers = lambda c=c: {"asof_monday": c["monday"], "qualifiers": c["quals"], "n_symbols": len(c["quals"])}
    O.fetch_weekly_etf = lambda sym, c=c: dict(c["etf_px"].get(sym) or {})
    O.fetch_daily = lambda sym, days=120, c=c: [dict(r) for r in (c["daily"].get(sym) or [])]
    O.reconcile_pending = lambda st, today: None
    O.get_account = lambda c=c: {"equity": c["equity"]}
    O.fetch_vix = lambda c=c: tuple(c["vix"]) if c["vix"] else (None, None, None, "unavailable")
    O.desk.run_cli = lambda *a, **k: []
    QT = c["quotes"]

    def lq(sym, QT=QT):
        q = QT.get(sym)
        if q is None:
            raise RuntimeError("no quote")
        return float(q[0]), float(q[1]), datetime.fromtimestamp(q[2], tz=ET)
    O.latest_quote = lq
    SUB = []

    def sub(args, timeout=120, SUB=SUB):
        a = dict(zip(args[0::2], args[1::2]))
        SUB.append([a["--side"], a["--symbol"], float(a["--qty"])])
        return {"id": "o%d" % len(SUB), "status": "accepted"}
    O.submit = sub
    FEAR[0] = c["fear_ok"]
    rank_t = datetime.fromtimestamp(c["rank_ts"], tz=ET)
    fill_t = datetime.fromtimestamp(c["fill_ts"], tz=ET)
    O.et_now = lambda rank_t=rank_t: rank_t
    O.mode_rank(types.SimpleNamespace(no_fetch=True, dry_run=False))
    pend = json.loads(json.dumps(STATE.get("pending") or {}))   # the fill's safety net appends to the same lists
    O.et_now = lambda fill_t=fill_t: fill_t
    O.mode_fill(types.SimpleNamespace(no_fetch=True, dry_run=False))
    out.append({"pending": {"buys": pend.get("buys"), "sells": pend.get("sells"), "target": pend.get("target"),
                            "selected": [[r["symbol"], r["count"], r["rules"]] for r in pend.get("selected_detail") or []]},
                "sells": [[s, q] for side, s, q in SUB if side == "sell"],
                "buys": [[s, q] for side, s, q in SUB if side == "buy"]})
print(json.dumps(out))
'''


def _fridays(n, rnd):
    out, d = [], date(2026, 1, 9)
    while len(out) < n:
        out.append(d)
        d += timedelta(weeks=rnd.randint(1, 3))
    return out


def run():
    rnd = random.Random(57)
    cases, metas = [], []
    special = [date(2026, 3, 13), date(2026, 4, 24), date(2026, 12, 25), date(2026, 12, 18)]   # FOMC / year end
    fridays = _fridays(N_CASES - len(special), rnd) + special
    for k, fri in enumerate(fridays):
        twin = ("beatendown", "confluence")[k % 2]
        monday = (fri - timedelta(days=4)).isoformat()
        c = _case(rnd, monday)
        seen, quals = set(), []
        for q in c["quals"]:
            if q["symbol"] not in seen:
                seen.add(q["symbol"])
                quals.append(q)
        friday = fri.isoformat()
        for q in quals:
            q["friday"] = friday
            if rnd.random() < 0.45:                      # beaten down: 20%+ under the trailing 52-week high
                hi = max(q["wcloses"][-52:])
                q["close"] = q["wcloses"][-1] = round(hi * rnd.uniform(0.4, 0.8), 4)
        daily_bd = c["daily"]
        daily_cf = {s: [r for r in rows if r["date"] < friday] for s, rows in daily_bd.items()}
        fill_mon = fri + timedelta(days=3)
        rank_hm, fill_hm = TWINS[twin]
        rank_ts = datetime(fri.year, fri.month, fri.day, *rank_hm, tzinfo=ET).timestamp()
        fill_ts = datetime(fill_mon.year, fill_mon.month, fill_mon.day, *fill_hm, tzinfo=ET).timestamp() + 30
        syms = [q["symbol"] for q in quals]
        book = {}
        for s in rnd.sample(syms + ["H%02d" % j for j in range(8)], rnd.randint(0, 9)):
            due = (fill_mon + timedelta(days=rnd.choice((-7, -3, 0, 0, 3, 40)))).isoformat()
            book[s] = {"qty": float(rnd.choice((3, 17, 40, 120))), "entry_px": round(rnd.uniform(5, 150), 2),
                       "entry_date": (fill_mon - timedelta(days=60)).isoformat(),
                       "exit_due_date": due if rnd.random() < 0.9 else None}
        pending_entry = {}
        if rnd.random() < 0.2:
            s = rnd.choice(syms)
            if s not in book:
                pending_entry[s] = {"qty": 10.0, "ref_px": 20.0, "cid": "x"}
        quotes = {}
        for s in set(syms) | set(book):
            r = rnd.random()
            mid = round(rnd.uniform(3, 150), 2)
            age = 20 if r < 0.8 else rnd.choice((1200, 3600))
            qt = fill_ts - age
            if r > 0.95:
                qt = datetime(fill_mon.year, fill_mon.month, fill_mon.day, 9, 45, tzinfo=ET).timestamp()
            quotes[s] = [0.0 if rnd.random() < 0.03 else round(mid - 0.02, 2), round(mid + 0.02, 2), qt]
        vr = rnd.random()
        vix = None if vr < 0.08 else [19.5, 18.0, (fill_mon - timedelta(days=6 if vr < 0.16 else 3)).isoformat(),
                                       "yahoo"]
        cases.append({"module": twin + "_sleeve", "twin": twin, "monday": monday, "quals": quals,
                      "etf_px": c["etf_px"], "daily": daily_bd if twin == "beatendown" else daily_cf, "book": book,
                      "pending_entry": pending_entry, "quotes": quotes, "vix": vix, "equity":
                      rnd.choice((100_000.0, 400_000.0)), "fear_ok": rnd.random() < 0.7,
                      "rank_ts": rank_ts, "fill_ts": fill_ts})
        metas.append({"daily_bd": daily_bd, "daily_cf": daily_cf})
    old = old_run(OLD, {"cases": cases}, timeout=3000)
    n = same = 0
    diffs = []
    counts = {"selected": 0, "staged_buys": 0, "staged_sells": 0, "sells": 0, "buys": 0, "gated_weeks": 0}

    def cmp(kind, ref, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "ref": ref, "old": a, "new": b})

    for ci, (c, mt, o) in enumerate(zip(cases, metas, old)):
        F = femto_module(c["twin"])
        bd = m2.compute_features(c["quals"], c["etf_px"], c["monday"], lambda s, d=mt["daily_bd"]: d.get(s) or [])
        cf = m2.compute_features(c["quals"], c["etf_px"], c["monday"], lambda s, d=mt["daily_cf"]: d.get(s) or [])
        rows = [dict(q, feat_bd=fb, feat_cf=fcf) for (q, fb), (_q, fcf) in zip(bd, cf)]
        friday = c["quals"][0]["friday"] if c["quals"] else None
        qfile = {"rank_date": datetime.fromtimestamp(c["rank_ts"], tz=ET).date().isoformat(),
                 "asof_monday": c["monday"], "qualifiers": rows}
        state = {s: {"position": dict(p, exit_submitted=None)} for s, p in c["book"].items()}
        for s, w in c["pending_entry"].items():
            state.setdefault(s, {})["pending_entry"] = {"qty": w["qty"], "ref_px": w["ref_px"]}
        rank_day = datetime.fromtimestamp(c["rank_ts"], tz=ET).date().isoformat()
        ctx = fc.Context(now=c["rank_ts"], session=rank_day, equity=c["equity"],
                         extra={"sleeve_state": state, "meta": {}, "m2": qfile})
        meta = F.next_meta({}, {}, ctx, [])
        p = meta.get("pending") or {}
        new_p = {"buys": p.get("buys"), "sells": p.get("sells"), "target": p.get("target"),
                 "selected": [[r["symbol"], r["count"], r["rules"]] for r in p.get("selected_detail") or []]}
        cmp("pending", [ci, c["twin"]], o["pending"], new_p)
        fill_day = datetime.fromtimestamp(c["fill_ts"], tz=ET).date().isoformat()
        quotes = {s: {"bid": q[0], "ask": q[1], "t": q[2]} for s, q in c["quotes"].items()}
        ctx2 = fc.Context(now=c["fill_ts"], session=fill_day, equity=c["equity"],
                          extra={"sleeve_state": state, "meta": meta, "quotes": quotes,
                                 "vix": tuple(c["vix"]) if c["vix"] else None, "fear_ok": c["fear_ok"]})
        out = F.signal({}, {}, ctx2)
        cmp("sells", [ci, c["twin"]], o["sells"], [[i.symbol, i.qty] for i in out if i.kind == "exit"])
        cmp("buys", [ci, c["twin"]], o["buys"], [[i.symbol, i.qty] for i in out if i.kind == "enter"])
        counts["selected"] += len(o["pending"]["selected"])
        counts["staged_buys"] += len(o["pending"]["buys"] or [])
        counts["staged_sells"] += len(o["pending"]["sells"] or [])
        counts["sells"] += len(o["sells"])
        counts["buys"] += len(o["buys"])
        counts["gated_weeks"] += bool(o["pending"]["buys"]) and not o["buys"]
    res = {"sleeve": "m2_twins", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:20],
           "exercised": counts}
    write_receipt("m2_twins", res)
    return res
