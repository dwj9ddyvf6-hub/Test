"""qr_news121: News-conditioned 12-1 leadership's monthly snapshot vs its specification.

SOURCE: quant-research-critical@0be4c575 research/2026-10-08-agentic-top-five/branches/news.md (blob e06be765), a
design document without code ("Causal ranking and the extraction contract"): the universe filters (>= 253 completed
observations so d-252 is observable, last close >= $10, trailing 20-session average dollar volume >= $25M), M_i =
TR[d-21]/TR[d-252] - 1, the positive-momentum top-20% pool, R_i the momentum percentile in the universe with the
permanent-ID tie break, S_i = .65 R_i + .35 (1 + C_i N_i)/2 with C = N = 0 (no extractor: NO_SEMANTIC_EDGE), the
ranking by S, then R, then the ID, and the top 50.
SPEC CONFORMANCE (no source code exists): the formulas transcribed independently below in pandas, on randomized
universes (sizes, price levels, volumes, history lengths, flat and trending names, ties), vs news121.snapshot()."""
import json
import math

import numpy as np
import pandas as pd

from . import write_receipt

N_CASES = 1000


def spec(frames, d):
    rows = []
    for s, f in frames.items():
        f = f.loc[:d]
        if len(f) < 253 or f.index[-1] != pd.Timestamp(d):
            continue
        c = f["c"]
        if c.iloc[-1] < 10 or (c * f["v"]).iloc[-20:].mean() < 25e6:
            continue
        rows.append({"symbol": s, "M": c.iloc[-22] / c.iloc[-253] - 1})
    t = pd.DataFrame(rows, columns=["symbol", "M"])
    if not len(t):
        return [], []
    t = t.sort_values(["M", "symbol"]).reset_index(drop=True)
    t["R"] = (t.index + 1) / len(t)
    k = math.ceil(0.2 * len(t))
    pool = t.iloc[len(t) - k:]
    pool = pool[pool.M > 0].copy()
    pool["S"] = 0.65 * pool.R + 0.35 * (1 + 0.0 * 0.0) / 2
    pool = pool.sort_values(["S", "R", "symbol"], ascending=[False, False, True])
    return list(pool.symbol), sorted(t.symbol)


def case(rng, days):
    n = int(rng.integers(5, 120))
    frames = {}
    for j in range(n):
        length = int(rng.choice([300, 300, 300, 260, 253, 252, 120]))
        px = float(rng.choice([3.0, 12.0, 50.0, 400.0]))
        vol = float(rng.choice([1e4, 1e5, 1e6, 5e6]))
        drift = rng.normal(0, 0.001)
        r = rng.normal(drift, rng.uniform(0.0, 0.03), length)
        if rng.random() < 0.05:
            r[:] = 0.0                                      # flat: zero momentum ties
        c = px * np.exp(np.cumsum(r))
        idx = pd.DatetimeIndex(days[-length:])
        frames[f"X{j:03d}"] = pd.DataFrame({"o": c, "h": c, "l": c, "c": c, "v": np.full(length, vol)}, index=idx)
    return frames


def run():
    from desk.sleeves.quant_research import common as C
    from desk.sleeves.quant_research import news121 as N
    rng = np.random.default_rng(1212)
    days = C.sessions_between("2025-06-01", "2027-02-26")[-300:]
    d = days[-1]
    st = {"cases": 0, "identical": 0, "pools": 0, "nonempty": 0}
    diffs = []
    for i in range(N_CASES):
        frames = case(rng, days)
        doc = N.snapshot(frames, list(frames), d)
        want, elig = spec(frames, d)
        got = [r["symbol"] for r in doc["ranked"]]
        ok = got == want and doc["eligible"] == elig and doc["top"] == want[:50] and \
            all(abs(r["S"] - (0.65 * r["R"] + 0.175)) < 1e-12 for r in doc["ranked"])
        st["cases"] += 1
        st["identical"] += ok
        st["pools"] += len(want)
        st["nonempty"] += bool(want)
        if not ok:
            diffs.append({"case": i, "port": got[:10], "spec": want[:10]})
    out = {"family": "quant_research", "sleeves": [N.SID], "cases": st["cases"], "identical": st["identical"],
           "n_diffs": len(diffs), "detail": st, "diffs": diffs[:20],
           "source": N.SOURCE, "method": "spec conformance: news.md's ranking transcribed independently (pandas) vs "
                                         "news121.snapshot() on randomized universes",
           "not_in_this_comparison": ["the Tensor verdict (the desk's own engine and flagship law, used as is)",
                                      "membership source (divergence 2)", "total-return source (3)"]}
    write_receipt("qr_news121", out)
    return out


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs")}), json.dumps(r["detail"]))
