"""V-tradingkit-1 - the stationary circular bootstrap uncertainty fan of the closed calls' R, and the losing-streak
simulation.

Stationary bootstrap (Politis and Romano): each simulated path of length n draws its first index at random and then
either steps to the next index (wrapping around the series, so it is circular) or, with probability 1/L, jumps to a
fresh random index; L = round(sqrt(n)) is the mean block length. 1000 paths; at each step the p05, p25, p50, p75, p95 of
cumulative R across paths, plus the same quantiles at the end and the p95 of the longest losing streak (a loss is R
below -even). Seeded, so the same record always draws the same fan. Under MIN_N closed calls: no_data."""
import math

import numpy as np

from .stats import no_data

MIN_N = 10
PATHS = 1000
SEED = 1587
EVEN_R = 0.05
QS = (5, 25, 50, 75, 95)
POINTS = 24


def _paths(r, paths, rng, block):
    n = len(r)
    idx = np.empty((paths, n), dtype=np.int64)
    idx[:, 0] = rng.integers(0, n, paths)
    jump = rng.random((paths, n)) < (1.0 / block)
    fresh = rng.integers(0, n, (paths, n))
    for t in range(1, n):
        idx[:, t] = np.where(jump[:, t], fresh[:, t], (idx[:, t - 1] + 1) % n)
    return r[idx]


def longest_losing_streak(r, even=EVEN_R):
    best = cur = 0
    for v in r:
        cur = cur + 1 if v < -even else 0
        best = max(best, cur)
    return best


def fan_of(r_values, paths=PATHS, seed=SEED, even=EVEN_R, points=POINTS):
    r = np.asarray([v for v in r_values if v is not None and math.isfinite(v)], float)
    n = len(r)
    if n < MIN_N:
        return no_data(f"{n} closed calls; need {MIN_N}", n=n)
    block = max(1, round(math.sqrt(n)))
    rng = np.random.default_rng(seed)
    P = _paths(r, int(paths), rng, block)
    cum = np.cumsum(P, axis=1)
    ks = sorted({int(round(k)) for k in np.linspace(1, n, min(points, n))})
    q = lambda a: [round(float(v), 2) for v in np.percentile(a, QS)]          # noqa: E731
    fan = [dict(zip(("k", "p05", "p25", "p50", "p75", "p95"), [k] + q(cum[:, k - 1]))) for k in ks]
    streaks = np.array([longest_losing_streak(p, even) for p in P])
    return {"status": "ok", "n": n, "paths": int(paths), "block": int(block), "seed": seed, "fan": fan,
            "final": dict(zip(("p05", "p25", "p50", "p75", "p95"), q(cum[:, -1]))),
            "actual_total_r": round(float(r.sum()), 2),
            "streak": {"observed": longest_losing_streak(r, even), "p95": int(np.percentile(streaks, 95))}}


def record_fan(rows, **kw):
    """rows = the record's rows (closed ones with an R), oldest first by close date"""
    closed = [x for x in rows if x.get("status") == "closed" and x.get("r") is not None]
    closed.sort(key=lambda x: (x.get("closed") or "", x.get("id") or ""))
    return fan_of([x["r"] for x in closed], **kw)
