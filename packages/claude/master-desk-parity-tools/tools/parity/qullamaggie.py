"""qullamaggie: the old qullamaggie_sleeve (select_leaders, mode_enter, mode_manage and its pure research
functions) vs the restored port's screen / entries / manage, on the same synthetic genome, 5-min tapes and books.

Per case: a genome of 260 random walks (some volatile enough to lead) plus 8-14 names built to carry (or
narrowly miss) the breakout setup — a 30-120% impulse into a 10-session base; today's 5-min RTH tape for every
built name (triggers forced on most, some next bars opening under the level, some grids gapped); a scan clock
on a 5-min bar close + 40 s between 10:30 and 15:55 (triggers fresh and stale); a book of 0-9 held names with
entry dates 0-12 calendar days back (scaled / unscaled, stops above and below the close) and 0-2 entries in
flight. The OLD functions run in their own process on the old desk tree with every broker / gate call stubbed
(the risk gate, Decision #75 and the 150% cap approve — the cutover doctrine removes them); their submitted
orders are captured. The port runs without quotes (its live-price path only replaces an open the old could not
read yet). Compared: the pure functions on every built name's bars, the leader list, every leader's setup,
the staged entries (qty, entry reference, stop) and the manage orders (side / qty / reason) — a scale and a
stop/trail exit due on the same close are expected as the one exit (named divergence), counted as collapsed."""
import random
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from . import femto_module, old_run, trading_dates, write_receipt

F = femto_module("qullamaggie")
ET = ZoneInfo("America/New_York")
N_CASES = 40

OLD = r'''
import sys, types
from datetime import datetime as _DT
import numpy as np
import pandas as pd
sys.argv = ["x"]
import qullamaggie_sleeve as O


class FakeDT(_DT):
    NOW = None

    @classmethod
    def now(cls, tz=None):
        return cls.NOW.astimezone(tz) if tz is not None else cls.NOW


O.datetime = FakeDT
CUR = {}
d75 = types.ModuleType("desk.decision75")
d75.pre_buy = lambda *a, **k: "proceed"
d75.sweep_releases = lambda *a, **k: []
dx = types.ModuleType("desk.desk_exposure")
dx.clamp_exit_qty = lambda symbol, qty, side="long", sleeve="": (float(qty), "ok")
dx.add_position = lambda *a, **k: None
dx.remove_position = lambda *a, **k: None
dx.assert_cap_or_block = lambda *a, **k: (True, 0.0, 0.0, "")
fl = types.ModuleType("desk.fetch_layer")
fl.get_daily_cached = lambda symbol, limit=200: [dict(b) for b in CUR["genome"].get(symbol, [])][-limit:]
fl.fetch_daily_batched = lambda *a, **k: None
import desk
for m in (d75, dx, fl):
    sys.modules[m.__name__] = m
    setattr(desk, m.__name__.split(".")[1], m)
O._USE_CACHE = True
O._risk_gate_ok = lambda sym, today: True
O._cap_gate_entry = lambda sym, notional, equity: True
O._consume_releases = lambda *a, **k: None
O.save_state = lambda s: None
O.log_ledger = lambda e: CUR["events"].append(e)
O.load_genome_universe = lambda: list(CUR["universe"])


def cached(symbol, tf):
    if tf == "daily":
        return [{"t": b["d"], "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"]}
                for b in CUR["genome"].get(symbol, [])]
    if tf == "5min":
        return [dict(b) for b in CUR["m5"].get(symbol, [])]
    return []


O.cached_get_bars = cached


def cli(*args):
    name = args[0]
    kv = {args[i]: args[i + 1] for i in range(1, len(args) - 1) if str(args[i]).startswith("--")}
    if name == "alpaca_get_account.py":
        return {"equity": str(CUR["equity"])}
    if name == "alpaca_list_positions.py":
        return [{"symbol": s, "qty": str(p["qty"])} for s, p in CUR["state"]["positions"].items()]
    if name == "alpaca_get_order.py":
        return {"status": "new", "filled_qty": "0"}
    if name == "alpaca_list_orders.py":
        return []
    if name == "alpaca_cancel_order.py":
        return {}
    if name == "alpaca_get_bars_5min.py" or name == "alpaca_get_bars_1h.py":
        return []
    if name == "alpaca_submit_order.py":
        CUR["orders"].append({"symbol": kv["--symbol"], "side": kv["--side"], "qty": kv["--qty"],
                              "type": kv["--type"], "tag": kv["--client-order-id"].rsplit("-", 1)[-1]})
        return {"id": "o%d" % len(CUR["orders"]), "status": "accepted"}
    raise RuntimeError("unstubbed CLI " + name)


O._run_cli = cli


def frame(rows):
    return pd.DataFrame({"open": [r["o"] for r in rows], "high": [r["h"] for r in rows],
                         "low": [r["l"] for r in rows], "close": [r["c"] for r in rows],
                         "volume": [r["v"] for r in rows]})


def jf(x):
    if isinstance(x, dict):
        return {k: jf(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jf(v) for v in x]
    if isinstance(x, (np.floating, np.integer)):
        return x.item()
    return x


out = []
for c in PAYLOAD["cases"]:
    FakeDT.NOW = _DT.fromisoformat(c["now"])
    CUR.update(genome=c["genome"], universe=c["universe"], m5=c["m5"], equity=c["equity"], events=[], orders=[])
    pure = {}
    for s in c["built"]:
        rows = c["genome"][s]
        df = frame(rows[-150:])
        tr = O.trailing_returns([r["c"] for r in rows[-130:]])
        pure[s] = {"features": O.compute_features(df), "atr": O.atr20(df), "gap": O.gap_buffer_pct(df),
                   "trail": list(O.trail_target(df)), "ret": None if tr is None else [float(x) for x in tr],
                   "trigger": None, "size": O.size_position(c["equity"], 50.0, 47.5, O.gap_buffer_pct(df),
                                                            c["adv_probe"])}
        bars = O.get_intraday_bars(s, c["today"])
        if bars is not None and len(bars) and pure[s]["features"]:
            t = O.find_trigger(bars, pure[s]["features"]["pivot"])
            pure[s]["trigger"] = None if t is None else list(t)
    state = {"positions": {}, "pending_entry": dict(c["pending"])}
    if c.get("pinned") is not None:
        state["sizing_equity"] = {"date": c["today"], "equity": c["pinned"]}
    leaders = O.select_leaders(state, c["today"])
    setups = {s: O.compute_features(O.get_daily_bars(s)) for s in leaders}
    state["positions"] = {s: dict(p) for s, p in c["book_enter"].items()}
    CUR["state"] = state
    O.mode_enter(state, leaders, c["today"])
    staged = {s: {"qty": r["qty"], "entry_price": r["entry_price"], "stop": r["stop"]}
              for s, r in state["pending_entry"].items() if s not in c["pending"]}
    enter_events = [e for e in CUR["events"] if e.get("type") == "enter_skipped"]
    CUR["orders"] = []
    state2 = {"positions": {s: dict(p) for s, p in c["book_manage"].items()}, "pending_entry": {}}
    CUR["state"] = state2
    O.mode_manage(state2, c["today"])
    out.append(jf({"pure": pure, "leaders": leaders, "setups": setups, "staged": staged,
                   "manage": CUR["orders"], "enter_events": enter_events}))
print(json.dumps(out))
'''


def _walk(rnd, days, px, drift, vol):
    rows = []
    for d in days:
        o = px * (1 + rnd.gauss(0, vol / 3))
        c = max(0.5, px * (1 + rnd.gauss(drift, vol)))
        rows.append({"d": d, "o": round(o, 4), "h": round(max(o, c) * (1 + abs(rnd.gauss(0, vol / 2))), 4),
                     "l": round(min(o, c) * (1 - abs(rnd.gauss(0, vol / 2))), 4), "c": round(c, 4),
                     "v": float(int(rnd.uniform(5e4, 2e6)))})
        px = c
    return rows


def _built(rnd, days):
    """a path into a breakout setup: drift, a 30-120% impulse over ~53 sessions, a 10-session base (tight or
    loose, lows rising or falling) — most pass the converged spec, some miss one filter."""
    n = len(days)
    px = rnd.uniform(8, 150)
    rows = _walk(rnd, days[:n - 63], px, 0.0005, 0.018)
    px = rows[-1]["c"]
    gain = rnd.uniform(0.25, 1.2)
    step = (1 + gain) ** (1 / 53) - 1
    for d in days[n - 63:n - 10]:
        o = px * (1 + rnd.gauss(0, 0.004))
        c = px * (1 + step + rnd.gauss(0, 0.012))
        rows.append({"d": d, "o": round(o, 4), "h": round(max(o, c) * (1 + abs(rnd.gauss(0, 0.006))), 4),
                     "l": round(min(o, c) * (1 - abs(rnd.gauss(0, 0.006))), 4), "c": round(c, 4),
                     "v": float(int(rnd.uniform(1e5, 3e6)))})
        px = c
    top = px
    g = rnd.choice((0.003, 0.002, 0.001, -0.002))
    w = rnd.choice((0.008, 0.012, 0.02, 0.03, 0.06))
    vmul = rnd.choice((1, 1, 1, 1, 0.02))
    for i, d in enumerate(days[n - 10:]):
        tight = 1.0 if i < 5 else rnd.choice((0.5, 0.7, 1.3))
        c = top * (1 + g * (i + 1)) * (1 + rnd.gauss(0, w * tight / 2))
        o = c * (1 + rnd.gauss(0, w * tight / 3))
        h = max(o, c) * (1 + abs(rnd.gauss(0, w * tight / 2)))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, w * tight / 2)))
        rows.append({"d": d, "o": round(o, 4), "h": round(h, 4), "l": round(lo, 4), "c": round(c, 4),
                     "v": float(int(rnd.uniform(1e5, 2e6) * vmul))})
    return rows


def _m5(rnd, today, prev_close, pivot, now):
    """today's completed 5-min RTH tape; a crossing of max(OR high, pivot) forced on most."""
    tight = rnd.random() < 0.5                         # a tape that coils just under the pivot (stop within 1 ATR)
    o0 = pivot * (1 - rnd.uniform(0.002, 0.012)) if tight else prev_close * (1 + rnd.gauss(0, 0.01))
    vol = 0.0012 if tight else 0.004
    start = datetime.fromisoformat(today).replace(hour=9, minute=30, tzinfo=ET)
    n = int((now - start.timestamp()) // 300)
    px, rows = o0, []
    for k in range(n):
        o = px * (1 + rnd.gauss(0, vol / 4))
        c = px * (1 + rnd.gauss(0.0002, vol))
        rows.append([o, max(o, c) * (1 + abs(rnd.gauss(0, vol / 2))), min(o, c) * (1 - abs(rnd.gauss(0, vol / 2))), c])
        px = c
    if n >= 13 and rnd.random() < 0.75:
        level = max(rows[0][1], pivot)
        k = rnd.randint(max(1, n - 8), n - 1) if rnd.random() < 0.7 else rnd.randint(1, n - 1)
        for j in range(1, k):                          # stay under the level before the trigger bar
            rows[j] = [min(x, level * 0.997) for x in rows[j]]
        rows[k][1] = max(rows[k][1], level * (1 + rnd.uniform(0.0005, 0.01)))
        nxt = level * (1 + rnd.choice((-0.004, 0.001, 0.003, 0.006)))
        for j in range(k + 1, n):
            rows[j] = [x / rows[k + 1][0] * nxt for x in rows[j]] if j == k + 1 else rows[j]
    out = []
    for k, (o, h, l, c) in enumerate(rows):
        t = start + timedelta(minutes=5 * k)
        out.append({"t": t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "o": round(o, 4),
                    "h": round(max(o, h, c), 4), "l": round(min(o, l, c), 4), "c": round(c, 4),
                    "v": float(int(rnd.uniform(1e4, 2e5)))})
    if out and rnd.random() < 0.08:                    # a gapped grid: fail closed
        del out[rnd.randint(0, len(out) - 1)]
    return out


def _case(rnd, k):
    days = trading_dates("2025-11-03", 175)
    last, today = days[-2], days[-1]
    hist = days[:-1]
    genome, universe, built = {}, [], []
    for j in range(260):
        s = "R%03d" % j
        genome[s] = _walk(rnd, hist, rnd.uniform(5, 300), rnd.uniform(-0.001, 0.003),
                          rnd.choice((0.01, 0.02, 0.03, 0.045)))
        universe.append(s)
    for j in range(rnd.randint(12, 20)):
        s = "B%02d" % j
        genome[s] = _built(rnd, hist)
        universe.insert(rnd.randint(0, len(universe)), s)
        built.append(s)
    slot = rnd.randint(12, 77)                         # 10:30 .. 15:55 bar closes
    nowdt = datetime.fromisoformat(today).replace(hour=9, minute=30, tzinfo=ET) + timedelta(minutes=5 * slot, seconds=40)
    now = nowdt.timestamp()
    m5 = {}
    sc = F.screen({s: _epoch_daily(r) for s, r in genome.items()}, last)       # tapes for every setup leader too
    for s in dict.fromkeys(built + list(sc["setups"])):
        rows = genome[s]
        pivot = max(r["h"] for r in rows[-10:])
        m5[s] = _m5(rnd, today, rows[-1]["c"], pivot, now)
    held = rnd.sample(universe, rnd.randint(0, 9))
    book_enter = {s: {"qty": 10, "entry_date": last, "entry_price": 20.0, "stop_level": 18.0,
                      "stop_order_id": "s-" + s, "scaled_third": False} for s in held}
    pend = {s: {"order_id": "p-" + s, "qty": 5, "entry_price": 10.0, "stop": 9.0, "date": today}
            for s in rnd.sample([u for u in universe if u not in held], rnd.randint(0, 2))}
    book_manage = {}
    for s in rnd.sample(universe, rnd.randint(0, 9)):
        c_last = genome[s][-1]["c"]
        entry = round(c_last * rnd.uniform(0.85, 1.15), 2)
        scaled = rnd.random() < 0.3
        stop = round(entry * rnd.uniform(0.85, 0.99), 4)
        if rnd.random() < 0.15:
            stop = round(c_last * rnd.uniform(1.0, 1.05), 4)            # close under the stop
        ed = (date.fromisoformat(today) - timedelta(days=rnd.randint(0, 12))).isoformat()
        book_manage[s] = {"qty": rnd.choice((1, 2, 3, 5, 9, 10, 37, 100)), "entry_date": ed, "entry_price": entry,
                          "stop_level": round(max(stop, entry), 2) if scaled else stop,
                          "stop_order_id": "s-" + s, "scaled_third": scaled}
    return {"today": today, "last": last, "now": nowdt.isoformat(), "genome": genome, "universe": universe,
            "built": built, "m5": m5, "equity": round(rnd.uniform(5e4, 2e5), 2),
            "pinned": rnd.choice((None, None, round(rnd.uniform(5e4, 2e5), 2))), "adv_probe": rnd.choice((0, 300, 1e6)),
            "book_enter": book_enter, "pending": pend, "book_manage": book_manage}


def _epoch_daily(rows):
    return [{"t": datetime.fromisoformat(r["d"]).replace(hour=4, tzinfo=timezone.utc).timestamp(), "o": r["o"],
             "h": r["h"], "l": r["l"], "c": r["c"], "v": r["v"]} for r in rows]


def _epoch_m5(rows):
    return [dict(r, t=datetime.fromisoformat(r["t"].replace("Z", "+00:00")).timestamp()) for r in rows]


def run():
    rnd = random.Random(53)
    cases = [_case(rnd, k) for k in range(N_CASES)]
    old = old_run(OLD, {"cases": cases}, timeout=3000)
    n = same = 0
    diffs = []
    counts = {"setups": 0, "leaders": 0, "triggers": 0, "staged": 0, "no_chase": 0, "stop_too_wide": 0,
              "trigger_stale": 0, "max_positions": 0, "manage_orders": 0, "scale": 0, "stop": 0, "trail": 0,
              "collapsed": 0}

    def cmp(kind, ref, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "ref": ref, "old": str(a)[:400], "new": str(b)[:400]})

    for ci, (c, o) in enumerate(zip(cases, old)):
        genome = {s: _epoch_daily(rows) for s, rows in c["genome"].items()}
        now = datetime.fromisoformat(c["now"]).timestamp()
        for s in c["built"]:
            daily = genome[s][-150:]
            tr = F.trailing_returns([b["c"] for b in genome[s][-130:]])
            feat = F.compute_features(daily)
            new = {"features": feat, "atr": F.atr20(daily), "gap": F.gap_buffer_pct(daily),
                   "trail": list(F.trail_target(daily)), "ret": None if tr is None else [float(x) for x in tr],
                   "trigger": None,
                   "size": F.size_position(c["equity"], 50.0, 47.5, F.gap_buffer_pct(daily), c["adv_probe"])}
            rows = F.intraday_rows(_epoch_m5(c["m5"][s]), c["today"])
            if rows is not None and feat:
                t = F.find_trigger(rows, feat["pivot"])
                new["trigger"] = None if t is None else list(t)
                counts["triggers"] += t is not None
            cmp("pure", [ci, s], o["pure"][s], new)
        sc = F.screen(genome, c["last"])
        cmp("leaders", ci, o["leaders"], sc["leaders"])
        counts["leaders"] += len(sc["leaders"])
        counts["setups"] += len(sc["setups"])
        cmp("setups", ci, {s: f for s, f in o["setups"].items() if f},
            {s: {k: v for k, v in f.items() if k not in ("atr", "gap", "score")} for s, f in sc["setups"].items()})
        state = {s: {"position": {"qty": p["qty"], "entry_px": p["entry_price"], "entry_date": p["entry_date"],
                                  "stop_px": p["stop_level"], "stop_level": p["stop_level"]}}
                 for s, p in c["book_enter"].items()}
        for s, r in c["pending"].items():
            state[s] = {"position": None, "pending_entry": {"qty": r["qty"]}}
        equity = c["pinned"] if c["pinned"] is not None else c["equity"]
        sc_today = dict(sc, date=c["today"])
        ents, decided = F.entries(sc_today, {s: _epoch_m5(b) for s, b in c["m5"].items()}, {}, state, {}, equity,
                                  now, c["today"])
        staged = {i.symbol: {"qty": i.qty_hint, "entry_price": i.position_meta["entry_ref"],
                             "stop": i.position_meta["stop_level"]} for i in ents}
        cmp("staged", ci, o["staged"], staged)
        counts["staged"] += len(staged)
        for e in o["enter_events"]:
            r = e.get("reason")
            key = "max_positions" if str(r).startswith("max_positions") else r
            if key in counts:
                counts[key] += 1
        mstate = {}
        for s, p in c["book_manage"].items():
            pos = {"qty": p["qty"], "entry_px": p["entry_price"], "entry_date": p["entry_date"],
                   "stop_px": round(p["stop_level"], 2), "stop_level": p["stop_level"],
                   "scaled_third": p["scaled_third"] or None}
            mstate[s] = {"position": pos}
        bars = {s: genome[s] for s in c["book_manage"]}
        mi = F.manage(bars, mstate, c["last"], c["today"])
        new_orders = sorted((i.symbol, i.signal_key.rsplit(":", 1)[-1], int(i.qty_hint)) for i in mi)
        by = {}
        for od in o["manage"]:
            by.setdefault(od["symbol"], []).append((od["tag"], int(od["qty"])))
        want = []
        for s, lst in by.items():
            tags = [t for t, _ in lst]
            if "scale" in tags and len(lst) > 1:      # the old's scale + stop/trail on one close -> one exit
                t, q = next((t, q) for t, q in lst if t != "scale")
                want.append((s, t, q))
                counts["collapsed"] += 1
            else:
                want += [(s, t, q) for t, q in lst]
        for _s, t, _q in want:
            counts[t] = counts.get(t, 0) + 1
        counts["manage_orders"] += len(o["manage"])
        cmp("manage", ci, sorted(want), new_orders)
    res = {"sleeve": "qullamaggie", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:20],
           "exercised": counts}
    write_receipt("qullamaggie", res)
    return res
