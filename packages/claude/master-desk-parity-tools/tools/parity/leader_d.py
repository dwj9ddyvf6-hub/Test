"""leader_d: old leader_d_sleeve.py (latest_event_date + mode_rank) vs the restored port + the leader feed.

A synthetic genome (random walks with trend bursts so the leader score/gate fires; SPY in up and down 60-day
regimes) of up to 600 daily bars. Compared per case: every name's latest-bar event (the vendored research
frame through the feed vs the old sleeve's own call), and the staged pending (buys with the capacity
rule and the surviving buys, sells at >= 19 bars after entry, the today + 32 exit backstop) plus the
refreshed last_event dedupe — given random books, entry dates, prior events and surviving buys."""
import os
import random
from datetime import date, datetime, timedelta, timezone

from desk.feedlib import leader
from desk.sleeves.femto import compat as fc

from . import as_epoch, femto_module, old_run, trading_dates, write_receipt

F = femto_module("leader_d")
N_CASES = 40

OLD = r'''
from datetime import datetime
from zoneinfo import ZoneInfo
import sleeve_core as core
import leader_d_sleeve as O
ET = ZoneInfo("America/New_York")
out = []
for c in PAYLOAD["cases"]:
    bars = {s: [list(r) for r in rows] for s, rows in c["bars"].items()}
    now = datetime.fromisoformat(c["today"]).replace(hour=16, minute=45, tzinfo=ET)
    core.et_now = lambda now=now: now
    O.core.et_now = core.et_now
    ev = {s: O.latest_event_date([b for b in bl if b[0] <= c["today"]], today=c["today"], now_et=now)
          for s, bl in bars.items()}
    core.load_cache = lambda path, bars=bars: {"bars": bars}
    O.core.load_cache = core.load_cache
    STATE = {"book": c["book"], "pending": c["pending"], "last_event": c["last_event"], "stats": {}}
    O.SL.load_state = lambda dry_run=False, STATE=STATE: STATE
    O.SL.save_state = lambda s: None
    O.SL.log = lambda e: None
    res = O.mode_rank(c["today"], dry_run=False, no_fetch=True)
    out.append({"events": ev, "pending": STATE["pending"], "last_event": STATE["last_event"],
                "down": res["spy_down"]})
print(json.dumps(out))
'''


def _path(rnd, dates, px, regime):
    rows = []
    burst = set()
    for _ in range(rnd.randint(2, 6)):
        k = rnd.randint(260, len(dates) - 2)
        burst.update(range(k - rnd.randint(3, 8), k + 1))
    if rnd.random() < 0.6:                       # a breakout into the last bar: the rank day's event
        burst.update(range(len(dates) - rnd.randint(2, 7), len(dates)))
    for i, d in enumerate(dates):
        drift = 0.012 if i in burst else regime
        vol = 0.03 if i in burst else 0.015
        o = px * (1 + rnd.gauss(0, vol / 3))
        c = max(0.5, px * (1 + rnd.gauss(drift, vol)))
        h = max(o, c) * (1 + abs(rnd.gauss(0, vol / 2)))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, vol / 2)))
        v = float(int(rnd.uniform(2e5, 2e6) * (2.5 if i in burst else 1)))
        rows.append([d, round(o, 4), round(h, 4), round(lo, 4), round(c, 4), v])
        px = c
    return rows


def run():
    rnd = random.Random(41)
    cases = []
    for k in range(N_CASES):
        n = rnd.randint(380, 600)
        dates = trading_dates("2024-01-02", n)
        today = dates[-1]
        spy_trend = rnd.choice((-0.0015, -0.0006, 0.0008))
        bars = {"SPY": _path(rnd, dates, 450.0, spy_trend)}
        for j in range(rnd.randint(25, 45)):
            nb = rnd.choice((n, n, n - 200, 230))
            bars["L%02d" % j] = _path(rnd, dates, rnd.uniform(5, 300), rnd.uniform(-0.001, 0.0015))[-nb:]
        names = [s for s in bars if s != "SPY"]
        book = {}
        for s in rnd.sample(names, rnd.randint(0, 6)):
            book[s] = {"qty": 10.0, "entry_px": 50.0, "entry_date": dates[-rnd.randint(2, 30)], "exit_due_date": "2099-01-01"}
        last_event = {s: today for s in rnd.sample(names, rnd.randint(0, 4))}
        pending = {"buys": rnd.sample(names, rnd.randint(0, 3)), "sells": [], "exit_dates": {}}
        cases.append({"bars": bars, "today": today, "book": book, "last_event": last_event, "pending": pending})
    old = old_run(OLD, {"cases": cases}, timeout=3000)
    n = same = 0
    diffs = []
    counts = {"events": 0, "down_cases": 0, "staged_buys": 0, "staged_sells": 0}

    def cmp(kind, ref, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "ref": ref, "old": a, "new": b})

    for ci, (c, o) in enumerate(zip(cases, old)):
        ebars = {s: as_epoch([dict(d=r[0], o=r[1], h=r[2], l=r[3], c=r[4], v=r[5]) for r in rows])
                 for s, rows in c["bars"].items()}
        rows = {}
        for s, bl in ebars.items():
            r = leader.latest(bl)
            if r:
                rows[s] = r
        new_ev = {s: (rows[s][0] if s in rows and leader.is_event(rows[s]) else None) for s in c["bars"]}
        cmp("events", ci, o["events"], new_ev)
        counts["events"] += sum(1 for v in o["events"].values() if v)
        state = {s: {"position": dict(p)} for s, p in c["book"].items()}
        now = datetime.fromisoformat(c["today"]).replace(hour=21, minute=45, tzinfo=timezone.utc).timestamp()
        ctx = fc.Context(now=now, session=c["today"], equity=100_000.0, extra={"sleeve_state": state})
        pending, last_ev, down, _sig = F.rank(ebars, ctx, {"pending": c["pending"], "last_event": c["last_event"]}, rows)
        cmp("pending", ci, {k: o["pending"].get(k) for k in ("buys", "sells", "exit_dates")}, pending)
        cmp("last_event", ci, o["last_event"], last_ev)
        cmp("down", ci, o["down"], down)
        counts["down_cases"] += bool(o["down"])
        counts["staged_buys"] += len(o["pending"].get("buys") or [])
        counts["staged_sells"] += len(o["pending"].get("sells") or [])
    res = {"sleeve": "leader_d", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:20],
           "exercised": counts}
    write_receipt("leader_d" + ("@" + os.environ["FEMTO_REF"] if os.environ.get("FEMTO_REF") else ""), res)
    return res
