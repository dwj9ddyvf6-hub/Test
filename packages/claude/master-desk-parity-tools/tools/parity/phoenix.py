"""phoenix: old phoenix_sleeve.py (the 15:55 daily pass) vs the femto port with its restored state hooks.

The OLD module runs a day-by-day forward simulation over the frozen 19-name universe (synthetic bars, SPY
regimes that flip the 60-day return through zero) in its own process: broker calls stubbed (MOC submits
captured, flat broker book, desk gates proceed — risk gate, context gate, drawdown brake, Decision #75,
the Decision #8 earnings blackout and the 150% cap are out of scope by the cutover doctrine), fills
simulated alike for every decision — entries and d+20 exits at the 15:55 read, the -25% disaster stop at
min(stop, open) on the first day the low reaches it (before that day's pass, as the old detect_fills saw
it). At every pass the old state is snapshotted in
the port's sleeve_state shape and the port is asked the same day:

  entries   {symbol: qty}             old maybe_enter submits  vs  port enter intents
  exits     [symbol]                  old maybe_exit submits   vs  port exit intents
  signals   pending_signals per name  old state after the pass and its fills  vs  port next_symbol_state
  pause     Decision #49 latch        old meta flag            vs  port latch (next_meta) at the pass"""
import os
import random
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from desk.sleeves.femto import compat as fc

from . import as_epoch, femto_module, old_run, trading_dates, write_receipt

F = femto_module("phoenix")
ET = ZoneInfo("America/New_York")
N_CASES = 24

OLD = r'''
import sys, types, copy
import pandas as pd
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import phoenix_sleeve as O
import desk as _pkg
ET = ZoneInfo("America/New_York")
EV, MOC, FORM, HELD = [], [], {}, {}
O.log = lambda e: EV.append(e)
O.save_state = lambda s: None
O.DRY_RUN = True
O.fetch_forming_bar = lambda sym: FORM.get(sym)
O.earnings_entry_veto = lambda *a, **k: None          # Decision #8 blackout: a desk-wide rail, gone (cutover)
O._broker_qty = lambda sym: HELD.get(sym, 0)
O.submit_moc = lambda sym, side, qty, cid, action: MOC.append([sym, side, qty, cid, action]) or {"id": "m", "status": "accepted"}
O.place_disaster_stop = lambda sym, qty, px, cid: {"id": "s", "status": "accepted"}
O.open_order_map_strict = lambda: {}
O.cancel_verified = lambda *a, **k: True
O._phoenix_pre_buy = lambda *a, **k: "proceed"
O._cap_gate_entry = lambda *a, **k: True
O.ensure_disaster_stop = lambda *a, **k: None
O.tensor_open_position = lambda sym: None
O._risk_gate = types.SimpleNamespace(evaluate_entry=lambda sleeve, sym: (True, []), blocked_reasons=lambda r: r)
O._HAS_RISK_GATE = True
cg = types.ModuleType("desk.context_gate"); cg.check_and_log = lambda *a, **k: (True, "")
dd = types.ModuleType("desk.drawdown_brake"); dd.check_drawdown = lambda: ("ok", ""); dd.log_activation = lambda *a, **k: None
dx = types.ModuleType("desk.desk_exposure"); dx.holders_of = lambda *a, **k: []
dx.clamp_exit_qty = lambda sym, q, sleeve=None: (q, ""); dx.add_position = lambda *a, **k: None
dx.remove_position = lambda *a, **k: None
for _n, _m in (("context_gate", cg), ("drawdown_brake", dd), ("desk_exposure", dx)):
    sys.modules["desk." + _n] = _m
    setattr(_pkg, _n, _m)

def frame(rows):
    return pd.DataFrame([(pd.Timestamp(r["d"]), r["o"], r["h"], r["l"], r["c"], r["v"]) for r in rows],
                        columns=["date", "o", "h", "l", "c", "v"]).set_index("date")

def at(d, hh, mm):
    return datetime.fromisoformat(d).replace(hour=hh, minute=mm, tzinfo=ET)

def snap_state(state):
    out = {}
    for sym, st in state.items():
        if sym.startswith("__"):
            continue
        p = st.get("position")
        out[sym] = {"pending_signals": copy.deepcopy(st.get("pending_signals") or []),
                    "last_exit_date": st.get("last_exit_date"),
                    "position": None if not p else {"qty": p["qty"], "entry_px": p["entry_px"],
                                                     "entry_date": p["entry_date"], "stop_px": p["stop_px"]}}
    return out

out = []
for case in PAYLOAD["cases"]:
    U = case["universe"]
    rows = case["rows"]
    frames = {s: frame(rows[s]) for s in U}
    eq = case["equity"]
    earnings, fresh = case["earnings"], case["fresh"]
    state = {}
    O.get_meta(state)
    HELD.clear()
    recs = []
    n = len(rows["SPY"])
    for i in range(case["start"], n):
        today = rows["SPY"][i]["d"]
        now = at(today, 15, 55)
        # GTC disaster stops that hit today before the pass (old detect_fills at the pass start)
        for sym in U:
            st = state.get(sym)
            p = (st or {}).get("position")
            if p and p["entry_date"] < today and rows[sym][i]["l"] <= p["stop_px"]:
                xp = min(p["stop_px"], rows[sym][i]["o"])
                O._on_stop_fill(sym, st, "stop", {"filled_avg_price": xp, "filled_at": today + "T15:00:00Z"}, now, state)
                HELD[sym] = 0
        FORM.clear()
        for sym in U:
            r = rows[sym][i]
            FORM[sym] = {"o": r["o"], "c": r["c"], "v": r["v"]}
        snap = snap_state(state)
        meta = O.get_meta(state)
        paused = bool(meta["entries_paused_by_disaster_rule"])
        closed = [dict(t) for t in meta["closed_trades"]]
        MOC.clear()
        bars_map = {s: frames[s].iloc[:i] for s in U}
        spy = bars_map["SPY"]
        for sym in U:
            st = state.setdefault(sym, O.fresh_symbol_state())
            bars = bars_map[sym]
            if len(bars) < O.WARMUP_BARS + 1:
                continue
            O.record_signals(sym, st, bars, spy, today)
            p = st.get("position")
            if p and not p.get("exit_due_date") and p.get("entry_date"):
                due = O.exit_due_date(bars, p["entry_date"])
                if due:
                    p["exit_due_date"] = due
                else:
                    _eloc = O._bar_loc(bars, p["entry_date"])
                    if _eloc is not None and (len(bars) - 1) - _eloc == O.HOLD_DAYS - 1:
                        p["exit_due_date"] = today
                    elif bars.index[-1].date() > date.fromisoformat(p["entry_date"]) + timedelta(days=25):
                        p["exit_due_date"] = today
            O.maybe_exit(sym, st, bars, now, state)
            O.maybe_enter(sym, st, bars, now, eq, earnings, fresh, state)
        entries = {m[0]: m[2] for m in MOC if m[1] == "buy"}
        exits = sorted(m[0] for m in MOC if m[1] == "sell")
        # fills at the 15:55 read
        for sym, q in entries.items():
            st = state[sym]
            O._on_entry_fill(sym, st, "e", {"filled_qty": q, "filled_avg_price": FORM[sym]["c"],
                                            "filled_at": today + "T19:56:00Z"}, now)
            HELD[sym] = q
        for sym in exits:
            st = state[sym]
            O._close_position(sym, st, {"filled_at": today + "T19:56:00Z"}, "time_stop", now, FORM[sym]["c"], state)
            HELD[sym] = 0
        after = {s: copy.deepcopy(state[s].get("pending_signals") or []) for s in U if s in state}
        recs.append({"i": i, "snap": snap, "paused": paused, "closed": closed, "entries": entries, "exits": exits,
                     "signals": after})
    out.append(recs)
print(json.dumps(out, default=str))
'''


def _walk(rnd, dates, px, vol, drift_fn, jump=0.02):
    rows = []
    for k, d in enumerate(dates):
        r = rnd.gauss(drift_fn(k), vol) + (rnd.choice((-1, 1)) * rnd.uniform(0.05, 0.3) if rnd.random() < jump else 0)
        o = px * (1 + rnd.gauss(0, vol / 2))
        c = max(0.5, px * (1 + r))
        h = max(o, c) * (1 + abs(rnd.gauss(0, vol / 2)))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, vol / 2)))
        v = 0.0 if rnd.random() < 0.01 else float(int(rnd.uniform(2e5, 5e6)))
        rows.append({"d": d, "o": round(o, 4), "h": round(h, 4), "l": round(lo, 4), "c": round(c, 4), "v": v})
        px = c
    return rows


def _case(seed):
    rnd = random.Random(seed)
    dates = trading_dates("2025-01-02", 300)
    period = rnd.randint(40, 90)
    spy = _walk(rnd, dates, 500.0, 0.009, lambda k: 0.004 if (k // period) % 2 == 0 else -0.004, jump=0.0)
    rows = {"SPY": spy}
    for sym in F.CONFIG.universe:
        if sym == "SPY":
            continue
        vol = rnd.choice((0.02, 0.035, 0.05, 0.08))
        rows[sym] = _walk(rnd, dates, rnd.uniform(5, 300), vol, lambda k, d=rnd.uniform(-0.002, 0.004): d)
    earnings = {}
    for sym in F.CONFIG.universe:
        u = rnd.random()
        if u < 0.1:
            continue                                   # unknown -> fail-closed veto
        earnings[sym] = None if u < 0.25 else dates[rnd.randint(200, 299)]
    return {"universe": list(F.CONFIG.universe), "rows": rows, "equity": rnd.choice((50_000.0, 100_000.0)),
            "start": 200, "earnings": earnings, "fresh": rnd.random() < 0.9}


def _norm(rows):
    out = []
    for ps in rows or []:
        out.append({k: (round(v, 6) if isinstance(v, float) else v) for k, v in sorted(ps.items())})
    return sorted(out, key=lambda r: r.get("signal_date") or "")


def run():
    cases = [_case(70_100 + k) for k in range(int(os.environ.get("PARITY_N", N_CASES)))]
    old = old_run(OLD, {"cases": cases}, timeout=3000)
    n = same = 0
    diffs = []
    counts = {"passes": 0, "entries": 0, "exits": 0, "paused_passes": 0, "signals_rows": 0, "stops": 0}

    def cmp(kind, ref, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "ref": ref, "old": a, "new": b})

    for ci, (case, recs) in enumerate(zip(cases, old)):
        bars_all = {s: as_epoch(r) for s, r in case["rows"].items()}
        for r in recs:
            i = r["i"]
            today = case["rows"]["SPY"][i]["d"]
            bars = {s: bl[:i] for s, bl in bars_all.items()}
            ss = {}
            for sym, st in r["snap"].items():
                ss[sym] = {"pending_signals": st["pending_signals"], "last_exit_date": st["last_exit_date"],
                           "position": None if not st["position"] else dict(st["position"], exit_submitted=None)}
            held = {s: (st["position"]["qty"] if st["position"] else 0) for s, st in r["snap"].items()}
            closed = []
            for k, t in enumerate(r["closed"]):
                closed.append({"symbol": t["symbol"], "reason": t["reason"], "closed_at": float(k + 1)})
            forming = {s: {"o": case["rows"][s][i]["o"], "c": case["rows"][s][i]["c"], "v": case["rows"][s][i]["v"]}
                       for s in case["universe"]}
            now = datetime.fromisoformat(today).replace(hour=15, minute=55, tzinfo=ET).timestamp()
            extra = {"sleeve_state": ss, "meta": {"closes_checked_to": 0.0}, "closed_trades": closed,
                     "forming": forming, "earnings": case["earnings"], "earnings_fresh": case["fresh"],
                     "broker_qty": {s: held.get(s, 0) for s in case["universe"]}, "foreign_holders": {}}
            ctx = fc.Context(now=now, session=today, equity=case["equity"], extra=extra)
            out = F.signal(bars, {}, ctx)
            nss = F.next_symbol_state(bars, {}, ctx, out)
            meta = F.next_meta(bars, {}, ctx)
            counts["passes"] += 1
            counts["entries"] += len(r["entries"])
            counts["exits"] += len(r["exits"])
            counts["paused_passes"] += r["paused"]
            cmp("entries", [ci, today], r["entries"],
                {x.symbol: x.qty_hint for x in out if x.kind == "enter"})
            cmp("exits", [ci, today], r["exits"], sorted(x.symbol for x in out if x.kind == "exit"))
            cmp("pause", [ci, today], r["paused"], bool(meta.get("entries_paused_by_disaster_rule")))
            for sym, rows in r["signals"].items():
                if sym not in nss:
                    continue                                       # warmup: the port records nothing either
                counts["signals_rows"] += len(rows)
                cmp("signals", [ci, sym, today], _norm(rows), _norm(nss[sym]["pending_signals"]))
        if recs:
            counts["stops"] += sum(1 for t in recs[-1]["closed"] if t["reason"] == "disaster_stop")
    res = {"sleeve": "phoenix", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:30],
           "exercised": counts}
    write_receipt("phoenix" + ("@" + os.environ["FEMTO_REF"] if os.environ.get("FEMTO_REF") else ""), res)
    return res
