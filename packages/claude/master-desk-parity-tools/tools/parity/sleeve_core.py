"""sleeve_core: the old sleeve_core.Sleeve.run_fill vs the restored fill law (desk/sleeves/femto/sleeve_core.py).

The OLD run_fill runs in its own process on an in-memory state with its broker/desk calls stubbed (no open
orders, submits captured, desk-wide gates proceed: risk gate, circuit breaker, context gate, drawdown brake,
red/green-day gates, Decision #75 buy-delay and chart gate, the 150% cap). Its OWN quote freshness runs on
stubbed latest quotes. Compared per case: the sells submitted (symbol, qty), the buys submitted (symbol,
qty, exit due date) and the pending buys/sells left after the pass. Random books, working entries, staged
buys/sells/targets/exit-date overrides, equities, costs, quote ages and clocks."""
import os
import random
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from . import old_run, trading_dates, write_receipt
from desk.sleeves.femto import sleeve_core as C

ET = ZoneInfo("America/New_York")
N_CASES = 3000

OLD = r'''
import sys, types
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import scan_and_trade as SAT
import sleeve_core as core
import desk as _pkg
ET = ZoneInfo("America/New_York")
SAT.CHART_GATE_ENABLED = False
SAT.RED_DAY_GATE_ENABLED = False
def mod(name, **fns):
    m = types.ModuleType("desk." + name)
    for k, v in fns.items():
        setattr(m, k, v)
    sys.modules["desk." + name] = m
    setattr(_pkg, name, m)
mod("circuit_breaker", check_circuit_breaker=lambda: ("ok", ""), record_closed_trade=lambda *a, **k: True)
mod("context_gate", entries_allowed=lambda sleeve=None: (True, ""), log_block=lambda *a, **k: None)
mod("drawdown_brake", check_drawdown=lambda: ("ok", ""), log_activation=lambda *a, **k: None)
mod("red_day_gate", check=lambda sym, now: (True, ""), green_day_block=lambda sym, now: (False, ""),
    market_green_day=lambda now: (False, ""))
mod("decision75", buy_delay_ok=lambda *a, **k: (True, ""))
mod("risk_verdict", build_verdict=lambda *a, **k: None, cap_check=lambda *a, **k: None,
    protection_check=lambda *a, **k: None)
mod("chart_gate", sweep_queue=lambda sleeve=None: ([], []))
core._desk_exposure = types.SimpleNamespace(
    read_exposure=lambda: {}, holders_of=lambda *a, **k: [], check_cap=lambda equity, add, data=None: (True, 0.0, 0.0),
    clamp_exit_qty=lambda sym, q, sleeve=None: (q, ""), self_heal_sleeve=lambda *a, **k: [],
    add_position=lambda *a, **k: None, remove_position=lambda *a, **k: None)
core._HAS_DESK_EXPOSURE = True
core._risk_gate = types.SimpleNamespace(evaluate_entry=lambda *a, **k: (True, []), blocked_reasons=lambda r: r)
core._HAS_RISK_GATE = True
core.fetch_vix = lambda: (18.0, 17.0, "2026-01-01", "stub")
core.fetch_daily_bars = lambda sym, days=60, attempts=3: []
NOW = [None]
core.et_now = lambda: NOW[0]
core.desk.run_cli = lambda script, args, timeout=None: []
out = []
for c in PAYLOAD["cases"]:
    NOW[0] = datetime.fromtimestamp(c["now"], tz=ET)
    SL = core.Sleeve("parity", "femto-px-", c["cost"])
    STATE = {"sleeve": "parity", "book": c["book"], "pending": c["pending"], "pending_entry": c["pending_entry"],
             "pending_exit": c["pending_exit"], "stats": {}}
    SUB = []
    SL.load_state = lambda dry_run=False: STATE
    SL.save_state = lambda s: None
    SL.reconcile_pending = lambda st, today: ([], [])
    SL.log = lambda e: None
    SL._tca_record = lambda *a, **k: None
    SL._cancel_disaster_stop = lambda *a, **k: True
    SL.get_account = lambda: {"equity": c["equity"]}
    QT = c["quotes"]
    def _lq(sym, QT=QT):
        q = QT.get(sym)
        if q is None:
            raise RuntimeError("no quote")
        return float(q[0]), float(q[1]), datetime.fromtimestamp(q[2], tz=ET)
    SL.latest_quote = _lq
    def _sub(args, timeout=120, SUB=SUB):
        a = dict(zip(args[0::2], args[1::2]))
        SUB.append([a["--side"], a["--symbol"], float(a["--qty"])])
        return {"id": "o%d" % len(SUB), "status": "accepted"}
    SL.submit = _sub
    SL.run_fill(c["today"])
    pe = STATE.get("pending_entry") or {}
    out.append({"sells": [[s, q] for side, s, q in SUB if side == "sell"],
                "buys": [[s, q, (pe.get(s) or {}).get("exit_due_date")] for side, s, q in SUB if side == "buy"],
                "left_buys": list(STATE["pending"].get("buys") or []),
                "left_sells": list(STATE["pending"].get("sells") or [])})
print(json.dumps(out))
'''


def _case(rnd, days):
    today = rnd.choice(days)
    hh, mm = rnd.choice(((10, 5), (10, 35), (11, 2), (13, 30), (15, 40), (9, 45)))
    now = datetime.fromisoformat(today).replace(hour=hh, minute=mm, tzinfo=ET).timestamp()
    syms = ["S%02d" % i for i in range(30)]
    rnd.shuffle(syms)
    book, pe, pex = {}, {}, {}
    for s in syms[:rnd.randint(0, 12)]:
        due = (date.fromisoformat(today) + timedelta(days=rnd.randint(-5, 60))).isoformat()
        book[s] = {"qty": float(rnd.choice((1, 3, 17, 40, 120.5))), "entry_px": round(rnd.uniform(2, 300), 2),
                   "entry_date": today, "exit_due_date": due if rnd.random() < 0.9 else None}
    rest = [s for s in syms if s not in book]
    for s in rest[:rnd.randint(0, 3)]:
        pe[s] = {"qty": float(rnd.randint(1, 50)), "ref_px": round(rnd.uniform(2, 300), 2), "order_id": "x"}
    for s in rnd.sample(list(book), min(len(book), rnd.randint(0, 2))):
        pex[s] = {"order_id": "y", "qty": book[s]["qty"]}
    pool = syms[:]
    buys = rnd.sample(pool, rnd.randint(0, 14))
    sells = rnd.sample(pool, rnd.randint(0, 3))
    exit_dates = {}
    for s in rnd.sample(buys, min(len(buys), rnd.randint(0, 4))):
        k = rnd.random()
        if k < 0.3:
            exit_dates[s] = {"anchor": "fill+91"}
        elif k < 0.5:
            exit_dates[s] = {"date": (date.fromisoformat(today) + timedelta(days=10)).isoformat()}
        elif k < 0.75:
            exit_dates[s] = (date.fromisoformat(today) + timedelta(days=rnd.choice((4, 32, 88, 91, 93)))).isoformat()
        else:
            exit_dates[s] = (date.fromisoformat(today) + timedelta(days=120)).isoformat()
    pending = {"buys": buys, "sells": sells, "exit_dates": exit_dates}
    if rnd.random() < 0.3:
        pending["target"] = buys + rnd.sample(pool, rnd.randint(0, 6))
    quotes = {}
    for s in syms:
        r = rnd.random()
        if r < 0.06:
            continue
        mid = round(rnd.uniform(2, 300), 2)
        age = rnd.choice((5, 30, 600, 899, 950, 3600)) if r < 0.85 else 20
        qt = now - age
        if rnd.random() < 0.04:
            quotes[s] = [0.0, mid, qt]
        else:
            quotes[s] = [round(mid - 0.01, 2), round(mid + 0.01, 2), qt]
    return {"today": today, "now": now, "book": book, "pending_entry": pe, "pending_exit": pex, "pending": pending,
            "equity": rnd.choice((25_000.0, 100_000.0, 250_000.0)), "cost": rnd.choice((0.0005, 0.001, 0.00255, 0.015)),
            "quotes": quotes}


def run():
    rnd = random.Random(83)
    days = trading_dates("2026-01-05", 180)
    cases = [_case(rnd, days) for _ in range(N_CASES)]
    old = old_run(OLD, {"cases": cases}, timeout=3000)
    n = same = 0
    diffs = []
    counts = {"sells": 0, "buys": 0, "left_buys": 0}

    def cmp(kind, ref, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "ref": ref, "old": a, "new": b})

    for ci, (c, o) in enumerate(zip(cases, old)):
        state = {}
        for s, p in c["book"].items():
            state[s] = {"position": dict(p, exit_submitted=True if s in c["pending_exit"] else None)}
        for s, w in c["pending_entry"].items():
            state.setdefault(s, {})["pending_entry"] = {"qty": w["qty"], "ref_px": w["ref_px"]}
        quotes = {s: {"bid": q[0], "ask": q[1], "t": q[2]} for s, q in c["quotes"].items()}
        sells, buys, left = C.fill(state, c["pending"], c["equity"], quotes, c["cost"], c["today"], c["now"])
        cmp("sells", ci, o["sells"], [[s, q] for s, q, _m, _w in sells])
        cmp("buys", ci, o["buys"], [[s, float(q), due] for s, q, _m, due in buys])
        cmp("left", ci, [o["left_buys"], o["left_sells"]], [left["buys"], left["sells"]])
        counts["sells"] += len(o["sells"])
        counts["buys"] += len(o["buys"])
        counts["left_buys"] += len(o["left_buys"])
    res = {"sleeve": "sleeve_core", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:30],
           "exercised": counts}
    write_receipt("sleeve_core", res)
    return res
