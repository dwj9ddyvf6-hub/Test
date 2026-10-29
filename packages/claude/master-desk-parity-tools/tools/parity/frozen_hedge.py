"""frozen_hedge (free_opt_pair's input): the SOURCE desk's option_inputs._hedge() (Agentic-Trading-Desk
aurelia-paper-desk @1720157f768e, run in its own tree: AURELIA_SRC; desk.bar_receipts.history stubbed to serve the
case's SIP rows) vs desk/feedlib/aurelia_options.frozen_hedge on the same closes. Randomized SPY / QQQ histories:
correlated walks of 40-120 sessions (fewer than 62 common sessions: no hedge), sessions missing from one side,
flat series (no variance), shocks that push the latest residual past |z| = 2. Every field compared exactly."""
import os
import random
from datetime import date, timedelta

from desk import calendar as cal
from desk.feedlib import aurelia_options as AO

from . import old_run, write_receipt

N = 1200

SRC = r'''
import json
import desk.bar_receipts as BR
import desk.option_inputs as OI
CASE = {}
BR.history = lambda symbol, **kw: CASE[symbol]
out = []
for case in PAYLOAD["cases"]:
    CASE.clear()
    CASE.update(case)
    out.append(OI._hedge())
print(json.dumps(out))
'''


def _sessions(rnd, n):
    d, out = date(2025, 1, 2) + timedelta(days=rnd.randint(0, 500)), []
    while len(out) < n:
        if cal.is_trading_day(d):
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def _case(rnd):
    n = rnd.choice((rnd.randint(40, 61), rnd.randint(62, 120), rnd.randint(62, 120)))
    ses = _sessions(rnd, n)
    beta, s, q = rnd.uniform(0.6, 1.6), rnd.uniform(400, 700), rnd.uniform(300, 650)
    spy, qqq = {}, {}
    flat = rnd.random() < 0.03
    for i, d in enumerate(ses):
        rs = 0.0 if flat else rnd.gauss(0.0004, 0.011)
        rq = beta * rs + rnd.gauss(0, 0.004)
        if i == len(ses) - 1 and rnd.random() < 0.35:
            rq += rnd.choice((-1, 1)) * rnd.uniform(0.005, 0.03)
        s, q = s * (1 + rs), q * (1 + rq)
        spy[d], qqq[d] = round(s, 2), round(q, 2)
    for side in (spy, qqq):
        if rnd.random() < 0.15:
            for d in rnd.sample(ses, rnd.randint(1, 5)):
                side.pop(d, None)
    return {"SPY": [{"session": d, "c": c} for d, c in spy.items()],
            "QQQ": [{"session": d, "c": c} for d, c in qqq.items()]}


def run():
    rnd = random.Random(20261016)
    cases = [_case(rnd) for _ in range(N)]
    src = old_run(SRC, {"cases": cases}, timeout=1800, tree=os.environ.get("AURELIA_SRC"))
    diffs, stats = [], {"frozen": 0, "signal": 0, "empty": 0}
    for case, o in zip(cases, src):
        p = AO.frozen_hedge({r["session"]: r["c"] for r in case["SPY"]}, {r["session"]: r["c"] for r in case["QQQ"]})
        if p != o:
            diffs.append({"case_sizes": [len(case["SPY"]), len(case["QQQ"])], "source": o, "port": p})
        stats["empty"] += not o
        stats["frozen"] += bool(o)
        stats["signal"] += bool(o and o.get("signal"))
    res = {"sleeve": "frozen_hedge", "sleeves": ["femto_free_opt_pair"], "cases": len(cases),
           "identical": len(cases) - len(diffs), "diffs": diffs[:10], "n_diffs": len(diffs), "stats": stats,
           "method": "source option_inputs._hedge() over stubbed bar_receipts.history vs "
                     "feedlib.aurelia_options.frozen_hedge"}
    write_receipt("frozen_hedge", res)
    return res
