"""qr_finrlx: the six-strategy reconstruction's FinRL-X driver vs desk/sleeves/quant_research/finrlx.py.

SOURCE side: finrlx/finrlx_reconstruction.py + finrlx/load_arrays.py + the upstream engine (finrlx/vendor/src, the 17
files the port vendors) from quant-research-critical@0be4c575 research/2026-10-08-six-strategy-reconstruction/
source.zip.parts (members sha256-pinned below; SIXAI_X names the extracted package), copied to a temporary tree with
a synthetic data/vix.csv and run with `python3 -I` in its own process: generate_signals(panel, start, end) over a
synthetic panel.npz (split-adjusted close / open arrays, as the reconstruction's Alpaca panel) -> the native_cash
stream (the principal allocation) at every Friday.
PORT side: finrlx.native_weights(closes, friday) at each of those Fridays from the same daily closes.
Compared exactly, symbol by symbol (|diff| <= 1e-12). pandas_market_calendars is absent on both sides: the source
side gets tools/parity/stubs/pandas_market_calendars.py, which raises if called (the weekly path never calls it).
Panels: 2014-2019 sessions, 27 assets on a regime-switching market factor with group factors, crashes and recoveries,
a VIX that spikes with drawdowns; decisions on every Friday 2017-2019."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from datetime import date, timedelta

import numpy as np
import pandas as pd

from . import write_receipt

SIXAI_X = os.environ.get("SIXAI_X", "/tmp/claude-0/-home-user/68100f50-a551-5c19-83c9-96beaaccdaac/scratchpad/dl/"
                                    "sixai/x")
PINS = {"finrlx/finrlx_reconstruction.py": "b1bfe514f002bc3a6876f166092f8213f30f742b5af003e73979e94683051242",
        "finrlx/load_arrays.py": "0f81a02e796c791766f739ad972acf8fb0f0ddf50ac089b205af3b0e08e95844"}
STUBS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stubs")
N_SEEDS = int(os.environ.get("FINRLX_PARITY_SEEDS", 7))


def sessions(a, b):
    from desk import calendar as cal
    d, out = date.fromisoformat(a), []
    while d <= date.fromisoformat(b):
        if cal.is_trading_day(d):
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def gen_panel(seed):
    from desk.sleeves.quant_research import finrlx as F
    rng = np.random.default_rng(seed)
    days = sessions("2014-01-02", "2019-12-31")
    n = len(days)
    syms = list(F.TRADABLES)
    # market regimes: bull drift, chop, crashes with recoveries
    mkt = np.zeros(n)
    k = 0
    while k < n:
        L = int(rng.integers(20, 160))
        kind = rng.choice(["bull", "chop", "bear"], p=[0.5, 0.3, 0.2])
        mu, sd = {"bull": (0.0008, 0.008), "chop": (0.0, 0.011), "bear": (-0.0018, 0.022)}[kind]
        mkt[k:k + L] = rng.normal(mu, sd, min(L, n - k))
        k += L
    grp = {g: rng.normal(0, 0.006, n) + np.repeat(rng.normal(0, 0.0015, n // 40 + 1), 40)[:n] for g in F.GROUPS}
    close = np.zeros((n, len(syms)))
    for j, s in enumerate(syms):
        beta = {"SHY": 0.02, "IEF": -0.1, "TLT": -0.25, "UUP": -0.1, "GLD": 0.05, "IAU": 0.05,
                "SLV": 0.3}.get(s, rng.uniform(0.6, 1.5))
        g = next((g for g, m in F.GROUPS.items() if s in m), None)
        r = beta * mkt + (grp[g] if g else 0.0) + rng.normal(rng.uniform(-0.0002, 0.0006), rng.uniform(0.004, 0.02), n)
        if s in ("SPY", "QQQ"):
            r = mkt * (1.0 if s == "SPY" else 1.25) + rng.normal(0, 0.002, n)
        jumps = rng.random(n) < 0.004
        r = r + jumps * rng.normal(0, 0.08, n)
        close[:, j] = np.round(rng.uniform(20, 300) * np.exp(np.cumsum(r)), 4)
    if rng.random() < 0.5:                              # a late listing (NaN history) for one growth name
        j = syms.index(str(rng.choice(F.GROUPS["group_a_growth_tech"])))
        close[: int(rng.integers(100, 500)), j] = np.nan
    opn = np.round(np.r_[close[:1], close[:-1]] * np.exp(rng.normal(0, 0.003, close.shape)), 4)
    spy = close[:, syms.index("SPY")]
    dd = 1 - spy / np.fmax.accumulate(spy)
    vix = np.clip(12 + 120 * dd + 40 * np.abs(mkt) * 10 + rng.normal(0, 1.2, n), 9, 90)
    vix = pd.Series(vix).ewm(span=3).mean().round(2).values
    return days, syms, close, opn, vix


SRC_SCRIPT = r'''
import json, sys
TREE, STUBS = sys.argv[1], sys.argv[2]
sys.path[:0] = [TREE, STUBS]
import numpy as np, pandas as pd
import finrlx_reconstruction as F
out = []
for case in json.load(sys.stdin)["cases"]:
    pd.DataFrame({"DATE": case["vix_dates"], "OPEN": case["vix"], "HIGH": case["vix"], "LOW": case["vix"],
                  "CLOSE": case["vix"]}).to_csv(TREE + "/data/vix.csv", index=False)
    streams, audits, risk_rows, config, tradables = F.generate_signals(case["panel"], case["start"], case["end"])
    nat = streams["native_cash"]
    out.append({"rows": nat.values.tolist(), "regimes": [a["portfolio"]["regime_state"] for a in audits]})
print(json.dumps(out))
'''


def source_tree():
    tmp = tempfile.mkdtemp(prefix="finrlx_src_")
    base = os.path.join(SIXAI_X, "finrlx")
    for rel, pin in PINS.items():
        b = open(os.path.join(SIXAI_X, rel), "rb").read()
        assert hashlib.sha256(b).hexdigest() == pin, f"{rel} differs from the pinned member"
        shutil.copyfile(os.path.join(SIXAI_X, rel), os.path.join(tmp, os.path.basename(rel)))
    shutil.copytree(os.path.join(base, "vendor"), os.path.join(tmp, "vendor"))
    lock = json.load(open(os.path.join(base, "upstream-used-source-lock.json")))
    for f in lock["files"]:
        p = os.path.join(tmp, "vendor", f["path"])
        b = open(p, "rb").read()
        assert hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest() == f["git_blob_sha1"], p
    os.makedirs(os.path.join(tmp, "data"))
    return tmp


def run_case(seed):
    from desk.sleeves.quant_research import finrlx as F
    days, syms, close, opn, vix = gen_panel(seed)
    tmp = source_tree()
    try:
        panel = os.path.join(tmp, "panel.npz")
        np.savez(panel, dates=np.array(days), symbols=np.array(syms), close=close, open=opn)
        vd = [pd.Timestamp(d).strftime("%m/%d/%Y") for d in days]
        payload = {"cases": [{"panel": panel, "start": "2017-01-01", "end": "2019-12-31", "vix_dates": vd,
                              "vix": [float(x) for x in vix]}]}
        r = subprocess.run([sys.executable, "-I", "-c", SRC_SCRIPT, tmp, STUBS], input=json.dumps(payload),
                           capture_output=True, text=True, timeout=3600, cwd=tmp)
        if r.returncode:
            raise RuntimeError(r.stderr[-3000:])
        src = json.loads(r.stdout.strip().splitlines()[-1])[0]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    idx = pd.DatetimeIndex(days)
    closes = {s: pd.Series(close[:, j], index=idx).dropna() for j, s in enumerate(syms)}
    closes["^VIX"] = pd.Series(vix, index=idx)
    want = {}
    for d, s, w in src["rows"]:
        want.setdefault(d, {})[s] = float(w)
    bad, n, invested = [], 0, 0
    for d in sorted(want):
        got, _ = F.native_weights(closes, d)
        n += 1
        invested += int(sum(got.values()) > 0)
        diff = {s: (want[d].get(s, 0.0), got.get(s, 0.0)) for s in set(want[d]) | set(got)
                if abs(want[d].get(s, 0.0) - got.get(s, 0.0)) > 1e-12}
        if diff:
            bad.append({"friday": d, "diff": diff})
    from collections import Counter
    return {"seed": seed, "n": n, "nbad": len(bad), "bad": bad[:3], "invested": invested,
            "regimes": dict(Counter(src["regimes"]))}


def run():
    seeds = [7100 + k for k in range(N_SEEDS)]
    W = max(1, int(os.environ.get("PARITY_WORKERS", 1)))      # one heavy process at a time unless asked otherwise
    if W == 1:
        res = [run_case(s) for s in seeds]
    else:
        with ProcessPoolExecutor(min(W, len(seeds))) as ex:
            res = list(ex.map(run_case, seeds))
    cases = sum(r["n"] for r in res)
    nbad = sum(r["nbad"] for r in res)
    from collections import Counter
    reg = Counter()
    for r in res:
        reg.update(r["regimes"])
    out = {"family": "quant_research", "sleeves": ["qr_finrlxreleasedadaptiverotationrecons"], "cases": cases,
           "identical": cases - nbad, "n_diffs": nbad, "diffs": [d for r in res for d in r["bad"]][:10],
           "per_seed": [{k: r[k] for k in ("seed", "n", "nbad", "invested")} for r in res],
           "regimes": dict(reg),
           "source": {"archive": "quant-research-critical@0be4c57569e363d052bd23564cf0664697439927 research/"
                                 "2026-10-08-six-strategy-reconstruction/source.zip.parts",
                      "members_sha256": PINS, "upstream_lock": "finrlx/upstream-used-source-lock.json (blob-checked)"},
           "method": "generate_signals native_cash stream (source, own process, python -I) vs finrlx.native_weights "
                     "on the same synthetic panels; every Friday 2017-2019",
           "not_in_this_comparison": ["execution (named divergence 2)", "the data provider (divergence 1)"]}
    write_receipt("qr_finrlx", out)
    return out


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs")}), json.dumps(r["per_seed"]),
          json.dumps(r["regimes"]))
    for d in r["diffs"][:3]:
        print(json.dumps(d)[:1500])
