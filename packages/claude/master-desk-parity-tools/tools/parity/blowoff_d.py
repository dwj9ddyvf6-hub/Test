"""blowoff_d: old blowoff_d_sleeve.py (latest_signal_date + mode_rank, entries enabled as in the forward test)
vs the port (the blowoff feed's last-close rows + rank) on a synthetic genome with rallies (RSI/OBV
exhaustion) and SPY regimes. Compared: every name's last-bar signal, the staged pending, last_signal."""
import os
import random
from datetime import datetime, timezone

from desk.feedlib import blowoff
from desk.sleeves.femto import compat as fc

from . import as_epoch, femto_module, old_run, trading_dates, write_receipt
from .leader_d import _path

F = femto_module("blowoff_d")
N_CASES = 40

OLD = r'''
import sleeve_core as core
import blowoff_d_sleeve as O
O.TRADING_ENABLED = True
out = []
for c in PAYLOAD["cases"]:
    bars = {s: [list(r) for r in rows] for s, rows in c["bars"].items()}
    sig = {s: O.latest_signal_date([b for b in bl if b[0] <= c["today"]]) for s, bl in bars.items()}
    core.load_cache = lambda path, bars=bars: {"bars": bars}
    O.core.load_cache = core.load_cache
    STATE = {"book": c["book"], "pending": c["pending"], "last_signal": c["last_signal"], "stats": {}}
    O.SL.load_state = lambda dry_run=False, STATE=STATE: STATE
    O.SL.save_state = lambda s: None
    O.SL.log = lambda e: None
    res = O.mode_rank(c["today"], dry_run=False, no_fetch=True)
    out.append({"sig": sig, "pending": STATE["pending"], "last_signal": STATE["last_signal"], "down": res["spy_down"]})
print(json.dumps(out))
'''


def run():
    rnd = random.Random(61)
    cases = []
    for k in range(N_CASES):
        n = rnd.randint(300, 600)
        dates = trading_dates("2024-01-02", n)
        today = dates[-1]
        bars = {"SPY": _path(rnd, dates, 450.0, rnd.choice((-0.0015, -0.0008, 0.0008)))}
        for j in range(rnd.randint(25, 50)):
            bars["X%02d" % j] = _path(rnd, dates, rnd.uniform(5, 300), rnd.uniform(-0.001, 0.002))
        names = [s for s in bars if s != "SPY"]
        book = {s: {"qty": 5.0, "entry_px": 20.0, "entry_date": dates[-rnd.randint(2, 30)], "exit_due_date": "2099-01-01"}
                for s in rnd.sample(names, rnd.randint(0, 5))}
        last_signal = {s: dates[-rnd.randint(1, 40)] for s in rnd.sample(names, rnd.randint(0, 8))}
        pending = {"buys": rnd.sample(names, rnd.randint(0, 2)), "sells": [], "exit_dates": {}}
        cases.append({"bars": bars, "today": today, "book": book, "last_signal": last_signal, "pending": pending})
    old = old_run(OLD, {"cases": cases}, timeout=3000)
    n = same = 0
    diffs = []
    counts = {"signals": 0, "down_cases": 0, "staged_buys": 0, "staged_sells": 0}

    def cmp(kind, ref, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "ref": ref, "old": a, "new": b})

    for ci, (c, o) in enumerate(zip(cases, old)):
        ebars = {s: as_epoch([dict(d=r[0], o=r[1], h=r[2], l=r[3], c=r[4], v=r[5]) for r in rows])
                 for s, rows in c["bars"].items()}
        sig = {s: blowoff.latest_daily_signal(bl) for s, bl in ebars.items()}
        cmp("signals", ci, o["sig"], sig)
        counts["signals"] += sum(1 for v in o["sig"].values() if v)
        rows = {s: [blowoff.bar_date(bl[-1]), sig[s]] for s, bl in ebars.items() if len(bl) >= 252}
        state = {s: {"position": dict(p)} for s, p in c["book"].items()}
        now = datetime.fromisoformat(c["today"]).replace(hour=21, minute=0, tzinfo=timezone.utc).timestamp()
        ctx = fc.Context(now=now, session=c["today"], equity=100_000.0, extra={"sleeve_state": state})
        pending, last_sig, down, _s = F.rank(ebars, ctx, {"pending": c["pending"], "last_signal": c["last_signal"]}, rows)
        cmp("pending", ci, {k: o["pending"].get(k) for k in ("buys", "sells", "exit_dates")}, pending)
        cmp("last_signal", ci, o["last_signal"], last_sig)
        cmp("down", ci, o["down"], down)
        counts["down_cases"] += bool(o["down"])
        counts["staged_buys"] += len(o["pending"].get("buys") or [])
        counts["staged_sells"] += len(o["pending"].get("sells") or [])
    res = {"sleeve": "blowoff_d", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:20],
           "exercised": counts}
    write_receipt("blowoff_d", res)
    return res
