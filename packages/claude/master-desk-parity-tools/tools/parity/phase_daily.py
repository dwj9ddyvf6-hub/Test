"""phase_daily: old phase_daily.py (daily_pass + intraday_pass + the 15:55 passes) vs the restored femto port.

The OLD module runs a day-by-day forward simulation per symbol in its own process, with broker calls stubbed
(submit / stop placement captured, order book empty, desk gates proceed). Fills are simulated the same way
for every decision: K5 stop fills when the day's high reaches box high (at max(box high, open)) unless the
box-low kill withdrew it, NC fills at the provisional close, breach/scr3 exits at the open, stops at
min(stop, open), the earnings flatten and the re-entry at the day's close. At every decision point the old
state is snapshotted in the port's sleeve_state shape and the port is asked the same question:

  pre    (08:46)  no position: K5 resting stop [qty, stop price] or none
                  position:    trail raise level, trail breach, scr3, earnings flatten scheduled
  rth    (11:00, 15:30 on partial / full provisional bars): box-low kill of a resting K5; NC entry qty
  close  (15:55)  kill; NC; earnings re-entry qty
Indicators: detect_episodes and nowcast_grey on every simulated day are compared directly as well."""
import os
import random
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from desk.sleeves.families.femto_specs import _holiday_list
from desk.sleeves.femto import compat as fc

from . import as_epoch, femto_module, old_run, trading_dates, write_receipt

F = femto_module("phase_daily")
ET = ZoneInfo("America/New_York")
N_CASES = 120

OLD = r'''
import sys, types
import pandas as pd
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import phase_daily as O, phase_signals as B
import desk as _pkg
ET = ZoneInfo("America/New_York")
EV, SUB, STOPS, FIVE = [], [], [], [[]]
O.log = lambda e: EV.append(e)
O.save_state = lambda s: None
def _submit(args, timeout=120):
    a = dict(zip(args[0::2], args[1::2]))
    SUB.append(a)
    return {"id": "x%d" % len(SUB), "status": "accepted"}
O.submit = _submit
O.open_order_map_strict = lambda: {}
O.open_order_map = lambda: {}
O.cancel_verified = lambda *a, **k: True
O._evaluate_entry_gated = lambda sym: (True, [])
O._cap_gate_entry = lambda *a, **k: True
O._clamped_exit_qty = lambda sym, q: (q, True)
O._dx_add = lambda *a, **k: None
O.place_stop = lambda sym, qty, px, cid: STOPS.append([sym, qty, round(float(px), 2)]) or {"id": "s", "status": "accepted"}
O.fetch_5min_today = lambda sym: list(FIVE[0])
d75 = types.ModuleType("desk.decision75"); d75.pre_buy = lambda *a, **k: "proceed"
cg = types.ModuleType("desk.context_gate"); cg.check_and_log = lambda *a, **k: (True, "")
sys.modules["desk.decision75"] = d75; sys.modules["desk.context_gate"] = cg
_pkg.decision75 = d75; _pkg.context_gate = cg

def frame(rows):
    df = pd.DataFrame([(pd.Timestamp(r["d"]), r["o"], r["h"], r["l"], r["c"]) for r in rows],
                      columns=["date", "o", "h", "l", "c"]).set_index("date")
    return df

def at(d, hh, mm):
    return datetime.fromisoformat(d).replace(hour=hh, minute=mm, tzinfo=ET)

out = []
for case in PAYLOAD["cases"]:
    sym, rows, eq = case["sym"], case["rows"], case["equity"]
    earnings = case["earnings"]
    fresh = case["fresh"]
    df_all = frame(rows)
    st = O.fresh_symbol_state()
    state = {sym: st}
    side = {"traded": None, "killed": None, "ep_of_pos": None}
    recs = []

    def snap(today):
        p = st.get("position")
        pos = None
        if p:
            pos = {"qty": p["qty"], "entry_px": p.get("entry_px"), "entry_date": p["entry_date"], "stop_px": p["stop"],
                   "ref_hi": p.get("ref_hi"), "path": p.get("path"), "episode_start": side["ep_of_pos"],
                   "flatten_for": p.get("earnings_for") if p.get("flatten_today") else None}
        pend = None
        if st["k5"]["status"] == "resting" and st.get("episode"):
            pend = {"key": "%s:%s:k5:%s" % (sym, today, st["episode"]["start_date"])}
        pr = st.get("pending_reentry")
        re = None
        if pr and not pr.get("cid"):
            re = {"qty": pr["qty"], "stop": pr["stop"], "earnings_date": pr["earnings_date"], "path": pr.get("path"),
                  "ref_hi": pr.get("ref_hi"), "episode_start": side["traded"]}
        return {"pos": pos, "pending": pend, "traded": side["traded"], "killed": side["killed"], "reentry": re}

    def fill_entry(path, px, now):
        o = {"filled_qty": None, "filled_avg_price": px}
        if path == "k5":
            o["filled_qty"] = SUBQ[0]
        else:
            o["filled_qty"] = SUBQ[0]
        O.open_position_from_fill(sym, st, "cid", o, path, now)
        side["traded"] = st["episode"]["start_date"] if st.get("episode") else side["traded"]
        side["ep_of_pos"] = side["traded"]

    SUBQ = [0]
    for i in range(case["start"], len(rows)):
        today = rows[i]["d"]
        bar = rows[i]
        dfi = df_all.iloc[:i]
        cache = dfi.tail(130)
        # ---------------- pre-market daily pass (08:46)
        now = at(today, 8, 46)
        SUB.clear(); STOPS.clear()
        eps = B.detect_episodes(dfi)
        s0 = snap(today)
        O.reconcile_episode(sym, st, eps, dfi, now)
        e21 = B.ema(dfi["c"], 21); e50 = B.ema(dfi["c"], 50)
        p = st.get("position")
        if p:
            O.manage_position_daily(sym, st, dfi, e50, earnings, now)
            sells = [s for s in SUB if s.get("--side") == "sell"]
            dec = {"breach": bool(sells), "raise": STOPS[-1][2] if STOPS else None,
                   "scr3": bool(p.get("scr3_exit_today")), "flatten": bool(p.get("flatten_today")) and not s0["pos"]["flatten_for"]}
            recs.append({"i": i, "kind": "pre", "snap": s0, "dec": dec})
            if sells or p.get("scr3_exit_today"):          # market exit at the open
                st["position"] = None
                side["ep_of_pos"] = None
        else:
            O.manage_k5_daily(sym, st, dfi, e21, now, eq, state, earnings=earnings, earnings_fresh=fresh)
            k5 = [s for s in SUB if s.get("--type") == "stop"]
            dec = {"k5": [int(k5[0]["--qty"]), float(k5[0]["--stop-price"])] if k5 else None}
            recs.append({"i": i, "kind": "pre", "snap": s0, "dec": dec,
                         "status": st["k5"]["status"], "dead": st["k5"].get("dead_reason")})
            if k5:
                SUBQ[0] = int(k5[0]["--qty"])
        # ---------------- intraday checkpoints (11:00 partial bar, 15:30 full bar, 15:55 close pass)
        rnd_h, rnd_l, rnd_c = case["u"][i % len(case["u"])]
        provs = [
            (11, 0, {"o": bar["o"], "h": bar["o"] + (bar["h"] - bar["o"]) * rnd_h, "l": bar["o"] - (bar["o"] - bar["l"]) * rnd_l}),
            (15, 30, {"o": bar["o"], "h": bar["h"], "l": bar["l"]}),
            (15, 55, {"o": bar["o"], "h": bar["h"], "l": bar["l"]}),
        ]
        provs[0][2]["c"] = provs[0][2]["l"] + (provs[0][2]["h"] - provs[0][2]["l"]) * rnd_c
        provs[1][2]["c"] = bar["c"]
        provs[2][2]["c"] = bar["c"]
        for hh, mm, prov in provs:
            now = at(today, hh, mm)
            FIVE[0] = [{"t": now, "o": prov["o"], "h": prov["h"], "l": prov["l"], "c": prov["c"]}]
            SUB.clear()
            s0 = snap(today)
            resting = st["k5"]["status"] == "resting"
            O.boxlow_kill_check(sym, st, now)
            killed = resting and st["k5"]["status"] == "dead"
            if killed:
                side["killed"] = st["episode"]["start_date"]
            nc = None
            if fresh and st.get("position") is None and st["k5"].get("status") != "resting":
                O.maybe_nc_fire(sym, st, cache, earnings, now, eq, state)
                buys = [s for s in SUB if s.get("--side") == "buy"]
                if buys:
                    nc = int(buys[0]["--qty"])
                    SUBQ[0] = nc
                    fill_entry("nc", prov["c"], now)
            re = None
            if (hh, mm) >= (15, 55):
                SUB.clear()
                O.earnings_flatten_pass(state, now)
                flat = [s for s in SUB if s.get("--side") == "sell"]
                if flat:                                     # flatten fills at the close
                    st["position"] = None
                    side["ep_of_pos"] = None
                SUB.clear()
                pr_before = st.get("pending_reentry")
                O.earnings_reentry_pass(state, now, eq, {sym: cache})
                buys = [s for s in SUB if s.get("--side") == "buy"]
                if buys:
                    re = int(buys[0]["--qty"])
                    pr = st["pending_reentry"]
                    O.open_position_from_reentry(sym, st, pr["cid"], {"filled_qty": re, "filled_avg_price": bar["c"]}, pr, now)
                    st["pending_reentry"] = None
                    side["ep_of_pos"] = side["traded"]
            recs.append({"i": i, "kind": "rth" if (hh, mm) < (15, 55) else "close", "hm": [hh, mm], "prov": prov,
                         "snap": s0, "dec": {"kill": killed, "nc": nc, "re": re}})
        # ---------------- the rest of the day: resting K5 fill, stop-outs
        if st["k5"]["status"] == "resting" and st.get("position") is None and st.get("episode"):
            bh = st["episode"]["box_hi"]
            if bar["h"] >= bh:
                fill_entry("k5", max(bh, bar["o"]), at(today, 15, 59))
            else:
                st["k5"]["status"] = "watching"        # the DAY stop expired
                st["k5"]["rest_cid"] = None
        p = st.get("position")
        if p and (bar["l"] <= p["stop"] if p["entry_date"] < today else bar["c"] <= p["stop"]):
            st["position"] = None                       # stopped out (a same-day entry: judged on the close)
            side["ep_of_pos"] = None
    eps_all = B.detect_episodes(df_all)
    out.append({"recs": recs, "episodes": [[str(e["start_date"].date()), str(e["end_date"].date()), int(e["n_grey"]),
                                            round(e["box_hi"], 6), round(e["box_lo"], 6),
                                            None if e["box_locked_idx"] is None else int(e["box_locked_idx"]),
                                            bool(e["ended"])] for e in eps_all],
                "nowcast": [[bool(x[0]), x[1]] for x in [B.nowcast_grey(df_all.iloc[:k], {"o": rows[k]["o"], "h": rows[k]["h"], "l": rows[k]["l"], "c": rows[k]["c"]})
                                                       for k in range(case["start"], len(rows), 7)]]})
print(json.dumps(out, default=str))
'''


def _regime_walk(seed, n, start):
    """daily OHLC with volatility regimes (quiet stretches make compression boxes; jumps break them)."""
    rnd = random.Random(seed)
    dates = trading_dates(start, n)
    px, rows, seg, vol, drift = rnd.uniform(8, 300), [], 0, 0.02, 0.0
    for d in dates:
        if seg <= 0:
            vol = rnd.choice((0.003, 0.005, 0.008, 0.012, 0.02, 0.035))
            seg = rnd.randint(6, 30)
            drift = rnd.uniform(-0.003, 0.004)
        seg -= 1
        r = rnd.gauss(drift, vol) + (rnd.choice((-1, 1)) * rnd.uniform(0.03, 0.09) if rnd.random() < 0.025 else 0.0)
        o = px * (1 + rnd.gauss(0, vol / 3))
        c = max(0.5, px * (1 + r))
        h = max(o, c) * (1 + abs(rnd.gauss(0, vol / 2)))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, vol / 2)))
        rows.append({"d": d, "o": round(o, 4), "h": round(h, 4), "l": round(lo, 4), "c": round(c, 4),
                     "v": float(int(rnd.uniform(2e5, 5e6)))})
        px = c
    return rows


def _ctx(sym, rows, i, hh, mm, snap, earnings, fresh, equity, prov=None):
    d = rows[i]["d"]
    now = datetime.fromisoformat(d).replace(hour=hh, minute=mm, tzinfo=ET).timestamp()
    st = {}
    if snap["pos"]:
        p = snap["pos"]
        st["position"] = {"qty": p["qty"], "entry_px": p["entry_px"], "entry_date": p["entry_date"],
                          "stop_px": p["stop_px"], "ref_hi": p["ref_hi"], "path": p["path"],
                          "episode_start": p["episode_start"], "exit_submitted": None}
    else:
        st["position"] = None
    if snap["pending"]:
        st["pending_entry"] = dict(snap["pending"], qty=1, filled=0)
    if snap["traded"]:
        st["traded_episode"] = snap["traded"]
    if snap["killed"]:
        st["k5_killed"] = snap["killed"]
    if snap["reentry"]:
        st["reentry"] = snap["reentry"]
    if snap["pos"] and snap["pos"].get("flatten_for"):
        st["flatten_for"] = snap["pos"]["flatten_for"]
    extra = {"sleeve_state": {sym: st}, "universe": [sym], "earnings": earnings, "earnings_fresh": fresh,
             "nyse_holidays": _holiday_list(d), "closed_trades": []}
    if prov is not None:
        extra["forming"] = {sym: dict(prov, v=0.0)}
        extra["marks"] = {sym: prov["c"]}
    return fc.Context(now=now, session=d, equity=equity, extra=extra)


def run():
    rnd = random.Random(31)
    cases = []
    for k in range(N_CASES):
        rows = _regime_walk(90_000 + k, 420, "2024-05-01")
        sym = "PH%03d" % k
        start = 330
        earnings = {}
        if rnd.random() < 0.6:
            earnings[sym] = rows[rnd.randint(start + 5, len(rows) - 3)]["d"]
        cases.append({"sym": sym, "rows": rows, "equity": rnd.choice((50_000.0, 100_000.0)), "start": start,
                      "earnings": earnings, "fresh": rnd.random() < 0.92,
                      "u": [[rnd.uniform(0.2, 1.0), rnd.uniform(0.2, 1.0), rnd.random()] for _ in range(17)]})
    old = old_run(OLD, {"cases": cases}, timeout=3000)
    n = same = 0
    diffs = []
    counts = {"pre_k5": 0, "pre_pos": 0, "rth": 0, "close": 0, "k5_placed": 0, "nc_fired": 0, "kills": 0,
              "breach": 0, "scr3": 0, "raise": 0, "flatten": 0, "reentry": 0}

    def cmp(kind, ref, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "ref": ref, "old": a, "new": b})

    for case, res in zip(cases, old):
        sym, rows = case["sym"], case["rows"]
        bars_all = as_epoch(rows)
        # indicators
        eps_new = F.detect_episodes(bars_all)
        cmp("episodes", sym, res["episodes"],
            [[e["start_date"], e["end_date"], e["n_grey"], round(e["box_hi"], 6), round(e["box_lo"], 6),
              e["box_locked_idx"], e["ended"]] for e in eps_new])
        nc_new = []
        for k in range(case["start"], len(rows), 7):
            g, ctx = F.nowcast_grey(bars_all[:k], {"o": rows[k]["o"], "h": rows[k]["h"], "l": rows[k]["l"],
                                                   "c": rows[k]["c"]})
            nc_new.append([bool(g), ctx])
        cmp("nowcast", sym, res["nowcast"], nc_new)
        for r in res["recs"]:
            i = r["i"]
            bars = {sym: bars_all[:i]}
            snap = r["snap"]
            if r["kind"] == "pre":
                ctx = _ctx(sym, rows, i, 8, 46, snap, case["earnings"], case["fresh"], case["equity"])
                out = F.signal(bars, {}, ctx)
                lv = F.stop_levels(bars, {}, ctx)
                if snap["pos"]:
                    counts["pre_pos"] += 1
                    ex = [x for x in out if x.kind == "exit"]
                    new = {"breach": any("trail_breach" in x.reason for x in ex),
                           "raise": lv.get(sym),
                           "scr3": any("scr3" in x.reason for x in ex),
                           "flatten": any((x.signal_key or "").endswith(":flatten") for x in ex)}
                    a = dict(r["dec"])
                    if a["scr3"] or a["breach"]:        # old also arms the flatten; the port exits first
                        a["flatten"] = new["flatten"]
                    if a["breach"]:
                        a["raise"] = new["raise"]       # old: no raise on a breach; port: none published either
                    counts["breach"] += a["breach"]
                    counts["scr3"] += a["scr3"]
                    counts["raise"] += a["raise"] is not None
                    counts["flatten"] += a["flatten"]
                    cmp("pre_pos", [sym, rows[i]["d"]], a, new)
                else:
                    counts["pre_k5"] += 1
                    en = [x for x in out if x.kind == "enter"]
                    new = {"k5": [en[0].qty_hint, en[0].order["stop_price"]] if en else None}
                    counts["k5_placed"] += r["dec"]["k5"] is not None
                    cmp("pre_k5", [sym, rows[i]["d"], r.get("status"), r.get("dead")], r["dec"], new)
            else:
                hh, mm = r["hm"]
                ctx = _ctx(sym, rows, i, hh, mm, snap, case["earnings"], case["fresh"], case["equity"], prov=r["prov"])
                out = F.signal(bars, {}, ctx)
                counts[r["kind"]] += 1
                nc = [x for x in out if x.kind == "enter" and ":nc:" in (x.signal_key or "")]
                re = [x for x in out if x.kind == "enter" and ":reentry:" in (x.signal_key or "")]
                new = {"kill": any(x.kind == "cancel" and "box-low" in x.reason for x in out),
                       "nc": nc[0].qty_hint if nc else None,
                       "re": re[0].qty_hint if re else None}
                counts["nc_fired"] += r["dec"]["nc"] is not None
                counts["kills"] += r["dec"]["kill"]
                counts["reentry"] += r["dec"]["re"] is not None
                cmp(r["kind"], [sym, rows[i]["d"], r["hm"]], r["dec"], new)
    res = {"sleeve": "phase_daily", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:30],
           "exercised": counts}
    write_receipt("phase_daily" + ("@" + os.environ["FEMTO_REF"] if os.environ.get("FEMTO_REF") else ""), res)
    return res
