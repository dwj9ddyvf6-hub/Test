"""r17_etf: the source run_ladder.run_account vs the R17 port, on randomized 14-fund ETF panels.

SOURCE side: the source file itself runs in its own process (quant-research-backup@d170596b
research-archives/2026-10-09-third-pass-edge-r17/inventions/run_ladder.py, read from the local clone and checked
against blob 0392bb5d). It runs from a scratch tree beside the vendored EXPERIMENT_PROTOCOL.json (blob e0c26c42).
run_account(..., save=True) writes each account (targets, fills, NAV) into the scratch tree's accounts/; that is the
only I/O involved.
PORT side: R17Etf is driven through signal()/update_state() on desk-shaped views by a minimal desk loop. The views
carry the completed daily bars (last 300, as the hub serves them), the dollar-volume bars, quotes carrying the
session open, and the sleeve's positions and cash. Each session has an open pass (09:31 ET) and a post-close pass
(16:30 ET). Target intents fill at the open with cost_bps. On margin cells the engine's debit carry applies before
the open.
Each case: a random panel on real trading days spanning the T+3 / T+2 / T+1 settlement eras, with 276-320 history
sessions and a 25-90 session account window. Rule, gross target {0.98, 1.5} and cost {5, 15, 30} bp are random.
Funds can list late (XLC / XLRE NaN prefix). The panel has isolated missing bars, missing session opens, and dollar
volume low enough for the 0.1% capacity cap to bind.
Every executed decision (signal date, execution date, weights), every fill (date, fund, side, units, price) and
every session NAV is compared, floats at a relative 1e-9.
Excluded by construction (named divergence 3 of the module): a missing bar AT a month-end signal close for a fund
with history. The port waits for it, whereas the research read NaN as "not listed". QQQ never has a missing bar,
because it is the session axis."""
import bisect
import gzip
import hashlib
import json
import os
import random
import shutil
import tempfile
from concurrent.futures import ProcessPoolExecutor
from datetime import date, datetime, time as dtime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np

from desk import calendar as cal

from . import ROOT, old_run, write_receipt

ET = ZoneInfo("America/New_York")
SRC = ("/home/user/quant-research-backup/research-archives/2026-10-09-third-pass-edge-r17/inventions/run_ladder.py")
PROTOCOL = os.path.join(ROOT, "desk", "vendor", "quant_r17", "EXPERIMENT_PROTOCOL.json")
RULES = ("ACCEL3", "ESCAPE1", "LEADER3", "RELATIVE3", "REPAIR3", "VOLADJ3")
N_PER_RULE = int(os.environ.get("R17_CASES_PER_RULE", 1000))
REL = 1e-9

OLD = r'''
import gzip, json
import numpy as np
import run_ladder as L
out = []
for case in PAYLOAD["cases"]:
    v = {k: np.array(case[k], dtype=float) for k in ("open", "close", "dollar_volume")}
    res = L.run_account(case["dates"], v, "ALPACA", case["start"], case["end"], case["rule"], case["gross"], case["bps"], save=True)
    name = f'ALPACA_{case["start"]}_{case["end"]}_{case["rule"]}_G{case["gross"]}_C{case["bps"]}'
    with gzip.open(L.ROOT / "accounts" / f"{name}.json.gz", "rt") as f:
        doc = json.load(f)
    out.append({"targets": [[t["decision_date"], t["execution_start"], t["reason"], {k: w for k, w in t["weights"].items() if w}]
                            for t in doc["targets"]],
                "fills": [[x["date"], x["symbol"], x["side"], x["units"], x["price"]] for x in doc["fills"]],
                "nav": [[n["date"], n["nav"]] for n in doc["nav"]],
                "bankrupt": res["bankrupt"], "capacity_hits": res["capacity_hits"],
                "settlement_block_days": res["settlement_block_days"], "maintenance_events": res["maintenance_events"]})
print(json.dumps(out))
'''


def _blob(b):
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def trading_days_from(d0, n):
    out, d = [], d0
    while len(out) < n:
        if cal.is_trading_day(d):
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def make_case(seed, rule):
    rnd = random.Random(seed)
    nprng = np.random.default_rng(seed)
    gross = rnd.choice((0.98, 0.98, 1.5))
    bps = rnd.choice((5, 15, 30))
    n_hist, n_win = rnd.randint(276, 320), rnd.randint(25, 90)
    d0 = date(2015, 3, 1) + timedelta(days=rnd.randint(0, (date(2025, 9, 1) - date(2015, 3, 1)).days))
    dates = trading_days_from(d0, n_hist + n_win)
    n, m = len(dates), 14
    mu = nprng.uniform(-0.0012, 0.0022, m)
    sig = nprng.uniform(0.004, 0.028 if gross < 1 else 0.02, m)
    r = nprng.normal(mu, sig, (n, m))
    if rnd.random() < 0.5:                              # a common shock: drawdowns / repairs across funds
        k = rnd.randrange(n)
        r[k:k + 8] -= nprng.uniform(0.004, 0.012)
    if gross > 1 and rnd.random() < 0.4:                # a crash inside the window: margin maintenance (gross/NAV > 2)
        k, L = rnd.randrange(n_hist + 2, n - 3), rnd.randint(3, 10)
        r[k:k + L] += np.log(1 - nprng.uniform(0.30, 0.50)) / L          # a 30-50% drop over L sessions
    close = np.exp(np.cumsum(r, axis=0)) * nprng.uniform(20, 400, m)
    gap = nprng.normal(0, 1, (n, m)) * sig / 3
    opn = np.vstack([close[:1], close[:-1]]) * np.exp(gap)
    base = 10 ** nprng.uniform(6.3, 9.3, m)               # 0.1% of dollar volume ~ $2k .. $2M
    dv = base * np.exp(nprng.normal(0, 0.4, (n, m)))
    month_end = {k for k in range(n - 1) if dates[k][:7] != dates[k + 1][:7]}
    for j in (4, 10):                                    # XLC / XLRE may list late
        if rnd.random() < 0.3:
            cut = rnd.randint(1, n_hist + n_win // 2)
            close[:cut, j] = np.nan
            opn[:cut, j] = np.nan
    for k in range(n):
        for j in range(1, m):                            # QQQ (j=0) is the session axis: never missing
            if k in month_end or not np.isfinite(close[k, j]):
                continue
            if rnd.random() < 0.003:                     # a missing bar (no open, no close, no volume)
                close[k, j] = opn[k, j] = np.nan
            elif rnd.random() < 0.003:                   # a missing session open (quote outage)
                opn[k, j] = np.nan
    dv = np.where(np.isfinite(close), dv, np.nan)       # no bar, no volume
    tolist = lambda a: [[None if not np.isfinite(x) else float(x) for x in row] for row in a]
    return {"seed": seed, "rule": rule, "gross": gross, "bps": bps, "dates": dates, "start": dates[n_hist],
            "end": dates[-1], "open": tolist(opn), "close": tolist(close), "dollar_volume": tolist(dv)}


def _nan(a):
    return np.array([[np.nan if x is None else x for x in row] for row in a], dtype=float)


def _et(d, hh, mm):
    return datetime.combine(date.fromisoformat(d), dtime(hh, mm), ET).timestamp()


def port_case(case):
    from desk.contract import View
    from desk.sleeves.families import r17_etf as R
    sl = R.R17Etf(case["rule"], gross=case["gross"], cost_bps=case["bps"])
    S, dates = sl.syms, case["dates"]
    op, cl, dv = _nan(case["open"]), _nan(case["close"]), _nan(case["dollar_volume"])
    n = len(dates)
    T = [datetime.fromisoformat(d).replace(hour=4, tzinfo=timezone.utc).timestamp() for d in dates]
    rows = {s: [] for s in S}
    bars = {s: [] for s in S}
    dvb = {s: [] for s in S}
    for k in range(n):
        for j, s in enumerate(S):
            if np.isfinite(cl[k, j]):
                rows[s].append(k)
                bars[s].append({"t": T[k], "o": cl[k, j], "h": cl[k, j], "l": cl[k, j], "c": cl[k, j], "v": 1.0})
                dvb[s].append({"t": T[k], "c": dv[k, j], "v": 1.0})

    def upto(k):                                         # bars with row < k (the hub's last 300 completed bars)
        out_b, out_d = {}, {}
        for s in S:
            i = bisect.bisect_left(rows[s], k)
            out_b[s] = bars[s][max(0, i - 300):i]
            out_d[s] = dvb[s][max(0, i - 5):i]
        return out_b, out_d

    cost = case["bps"] / 1e4
    cash = 100000.0
    units = np.zeros(len(S))
    state = {}
    fills, navs = [], []
    a = dates.index(case["start"])
    lastclose = cl[a - 1].copy()
    for k in range(a, n):
        d = dates[k]
        if case["gross"] > 1 and cash < 0:               # the engine's carry on the debit (once per session)
            days = (date.fromisoformat(d) - date.fromisoformat(dates[k - 1])).days
            cash -= -cash * 0.10 * days / 365
        b, dvx = upto(k)
        pos = {"EQ:" + s: {"qty": float(units[j]), "avg": 0.0, "opened_at": None, "meta": {}, "mark": None}
               for j, s in enumerate(S) if units[j] != 0}
        quotes = {s: {"day_open": float(op[k, j]), "day_date": d} for j, s in enumerate(S)
                  if np.isfinite(op[k, j]) and op[k, j] > 0}
        v = View(now=_et(d, 9, 31), session=d, bars={"1d": b}, quotes=quotes, positions=pos, cash=cash,
                 state=state, extra={"bars_dv": dvx, "pending_orders": [], "closed_trades": []})
        intents = sl.signal(v)
        state = sl.update_state(v, intents) or state
        for it in intents:
            if it.kind != "target":
                continue
            j = S.index(it.symbol)
            delta = it.qty - units[j]
            px = op[k, j]
            fee = abs(delta) * px * cost
            cash -= delta * px + fee
            units[j] = it.qty
            fills.append([d, it.symbol, "buy" if delta > 0 else "sell", abs(delta), float(px)])
        lastclose = np.where(np.isfinite(cl[k]) & (cl[k] > 0), cl[k], lastclose)
        active = units > 1e-12
        navs.append([d, cash + float(units[active] @ lastclose[active])])
        b, dvx = upto(k + 1)
        pos = {"EQ:" + s: {"qty": float(units[j]), "avg": 0.0, "opened_at": None, "meta": {}, "mark": None}
               for j, s in enumerate(S) if units[j] != 0}
        v = View(now=_et(d, 16, 30), session=d, bars={"1d": b}, quotes={}, positions=pos, cash=cash, state=state,
                 extra={"bars_dv": dvx, "pending_orders": [], "closed_trades": []})
        intents = sl.signal(v)
        state = sl.update_state(v, intents) or state
    dec = [[x["signal"], x["executed"], x["reason"], x["weights"]] for x in state.get("decisions") or []]
    return {"targets": dec, "fills": fills, "nav": navs}


def _close(x, y):
    return abs(x - y) <= REL * max(1.0, abs(x), abs(y))


def compare(o, p):
    out = []
    if len(o["targets"]) != len(p["targets"]):
        out.append({"what": "decision count", "old": o["targets"], "port": p["targets"]})
    for x, y in zip(o["targets"], p["targets"]):
        reason = lambda r: "month_end" if r in ("month_end", "initial") else r
        if x[0] != y[0] or x[1] != y[1] or reason(x[2]) != reason(y[2]) or set(x[3]) != set(y[3]) or \
                any(not _close(x[3][k], y[3][k]) for k in x[3]):
            out.append({"what": "decision", "old": x, "port": y})
    of = sorted(o["fills"], key=lambda f: (f[0], f[1], f[2]))
    pf = sorted(p["fills"], key=lambda f: (f[0], f[1], f[2]))
    if [f[:3] for f in of] != [f[:3] for f in pf]:
        out.append({"what": "fill set", "old": [f[:3] for f in of][:20], "port": [f[:3] for f in pf][:20]})
    else:
        for x, y in zip(of, pf):
            if not _close(x[3], y[3]) or x[4] != y[4]:
                out.append({"what": "fill", "old": x, "port": y})
    on = o["nav"]
    pn = p["nav"][:len(on)] if o["bankrupt"] else p["nav"]
    if [x[0] for x in on] != [x[0] for x in pn]:
        out.append({"what": "nav dates", "old": len(on), "port": len(pn)})
    else:
        for x, y in zip(on, pn):
            if not _close(x[1], y[1]):
                out.append({"what": "nav", "old": x, "port": y})
                break
    return out


def _port_seeds(items):
    return [port_case(make_case(seed, rule)) for seed, rule in items]


def run():
    data = open(SRC, "rb").read()
    from desk.sleeves.families import r17_etf as R
    assert _blob(data) == R.SOURCE["blob"], "source file differs from the pinned blob"
    assert _blob(open(PROTOCOL, "rb").read()) == R.SOURCE["protocol_blob"]
    seeds = [(1000 * (RULES.index(rule) + 1) + i, rule) for rule in RULES for i in range(N_PER_RULE)]
    diffs, identical = [], 0
    stats = {"decisions": 0, "fills": 0, "navs": 0, "capacity_hits": 0, "settlement_block_days": 0,
             "maintenance_events": 0, "bankrupt": 0, "by_rule": {r: 0 for r in RULES},
             "cells": {}, "eras": {"T+3": 0, "T+2": 0, "T+1": 0}}
    tree = tempfile.mkdtemp(prefix="r17_src_")
    try:
        shutil.copyfile(SRC, os.path.join(tree, "run_ladder.py"))
        shutil.copyfile(PROTOCOL, os.path.join(tree, "EXPERIMENT_PROTOCOL.json"))
        os.makedirs(os.path.join(tree, "accounts"))
        with ProcessPoolExecutor(4) as ex:
            for b in range(0, len(seeds), 200):              # stream: 200 cases at a time, nothing kept but results
                batch = seeds[b:b + 200]
                cases = [make_case(s, r) for s, r in batch]
                old = old_run(OLD, {"cases": cases}, timeout=3600, tree=tree)
                for f in os.listdir(os.path.join(tree, "accounts")):
                    os.remove(os.path.join(tree, "accounts", f))
                parts = list(ex.map(_port_seeds, [batch[i::4] for i in range(4)]))
                port = [None] * len(batch)
                for i in range(4):
                    for k, r in zip(range(i, len(batch), 4), parts[i]):
                        port[k] = r
                _tally(cases, old, port, diffs, stats)
                identical = sum(stats["by_rule"].values())
                del cases, old, port, parts
    finally:
        shutil.rmtree(tree, ignore_errors=True)
    return _finish(seeds, identical, diffs, stats, R)


def _tally(cases, old, port, diffs, stats):
    for c, o, p in zip(cases, old, port):
        d = compare(o, p)
        if d:
            diffs.append({"seed": c["seed"], "rule": c["rule"], "gross": c["gross"], "bps": c["bps"], "diffs": d[:3]})
        else:
            stats["by_rule"][c["rule"]] += 1
        stats["decisions"] += len(o["targets"])
        stats["fills"] += len(o["fills"])
        stats["navs"] += len(o["nav"])
        for k in ("capacity_hits", "settlement_block_days", "maintenance_events"):
            stats[k] += o[k]
        stats["bankrupt"] += bool(o["bankrupt"])
        key = f"G{c['gross']}_C{c['bps']}"
        stats["cells"][key] = stats["cells"].get(key, 0) + 1
        era = "T+3" if c["start"] < "2017-09-05" else "T+2" if c["start"] < "2024-05-28" else "T+1"
        stats["eras"][era] += 1


def _finish(seeds, identical, diffs, stats, R):
    res = {"sleeve": "r17_etf", "family": "r17_etf", "sleeves": ["r17_" + r.lower() for r in RULES],
           "cases": len(seeds), "identical": identical, "diffs": diffs[:10], "n_diffs": len(diffs), "stats": stats,
           "source": {"repo": "quant-research-backup", "commit": R.SOURCE["commit"], "path": R.SOURCE["path"],
                      "blob": R.SOURCE["blob"], "protocol_blob": R.SOURCE["protocol_blob"], "local_file": SRC},
           "method": "the source run_account (own process, scratch tree, save=True) vs R17Etf through "
                     "signal()/update_state() on desk views; decisions, fills and session NAVs compared at a "
                     "relative 1e-9",
           "divergences": {"excluded_by_construction": [
               "a missing bar at a month-end signal close for a fund with history (the port waits: divergence 3)",
               "missing QQQ bars (QQQ is the session axis)"],
               "not_in_this_comparison": [
               "live fill prices (the harness fills at the open, as the research did: divergence 1)",
               "the engine's $1 minimum rebalance (divergence 5)", "dividends (divergence 6)"]}}
    write_receipt("r17_etf", res)
    return res


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs")}), json.dumps(r["stats"])[:1500])
    for d in r["diffs"][:3]:
        print(json.dumps(d, default=str)[:3000])
