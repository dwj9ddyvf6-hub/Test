"""own_iv_forecast (free_opt_own_iv's input): the SOURCE desk's own causal realized-volatility forecaster —
desk/features.py har_vol_forecast (Agentic-Trading-Desk aurelia-paper-desk @1720157f768e, run in its own tree:
AURELIA_SRC) — vs desk/feedlib/free_options_inputs.forecast on the same closes and horizon. Cases: windows of the
recorded SPY / QQQ daily closes (tests/fixtures/free_options; 30-700 sessions: before and after the first HAR fit at
504 observations) and synthetic walks with volatility regimes and jumps (some below the 10% / above the 150% clip),
horizons 1-45 sessions. The forecast (the last value of the source's series, annualized) is compared exactly."""
import gzip
import json
import math
import os
import random

from desk.feedlib import free_options_inputs as FI

from . import old_run, write_receipt

N = 600
HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SRC = r'''
import json
import pandas as pd
from desk.features import har_vol_forecast
out = []
for case in PAYLOAD["cases"]:
    r = pd.Series(case["closes"]).pct_change().dropna().reset_index(drop=True)
    out.append(float(har_vol_forecast(r, horizon=case["horizon"]).iloc[-1]))
print(json.dumps(out))
'''


def _cases(rnd):
    rec = json.load(gzip.open(os.path.join(HERE, "tests", "fixtures", "free_options", "daily_closes_spy_qqq.json.gz"),
                              "rt"))
    out = []
    for i in range(N):
        h = rnd.randint(1, 45)
        if i % 2 == 0:
            series = [c for _, c in rec[rnd.choice(("SPY", "QQQ"))]]
            n = rnd.choice((rnd.randint(30, 200), rnd.randint(480, len(series))))
            start = rnd.randint(0, len(series) - n)
            closes = series[start:start + n]
        else:
            n, px, vol, closes = rnd.randint(30, 700), rnd.uniform(50, 800), rnd.uniform(0.002, 0.05), []
            for _ in range(n):
                if rnd.random() < 0.01:
                    vol = rnd.uniform(0.002, 0.08)
                px *= math.exp(rnd.gauss(0, vol) + (rnd.choice((-1, 1)) * rnd.uniform(0.05, 0.15)
                                                    if rnd.random() < 0.005 else 0))
                closes.append(round(px, 4))
        out.append({"closes": closes, "horizon": h})
    return out


def run():
    rnd = random.Random(20261016)
    cases = _cases(rnd)
    src = old_run(SRC, {"cases": cases}, timeout=3600, tree=os.environ.get("AURELIA_SRC"))
    diffs, stats = [], {"fit": 0, "ewma": 0, "clipped": 0}
    for case, s in zip(cases, src):
        FI._MEMO.clear()
        p = FI.forecast(case["closes"], case["horizon"])
        if p != s:
            diffs.append({"n": len(case["closes"]), "horizon": case["horizon"], "source": s, "port": p})
        stats["fit" if len(case["closes"]) - 1 > 504 else "ewma"] += 1
        stats["clipped"] += s in (0.10, 1.50) or abs(s - 0.10) < 1e-12 or abs(s - 1.50) < 1e-12
    res = {"sleeve": "own_iv_forecast", "sleeves": ["femto_free_opt_own_iv"], "cases": len(cases),
           "identical": len(cases) - len(diffs), "diffs": diffs[:10], "n_diffs": len(diffs), "stats": stats,
           "method": "source desk/features.py har_vol_forecast (its own tree) vs "
                     "desk/feedlib/free_options_inputs.forecast on the same closes and horizon"}
    write_receipt("own_iv_forecast", res)
    return res
