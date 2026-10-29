"""The law checker: every registered forecaster's declared laws, tested on seeded random price histories.

A forecaster group is a compute function `compute(a, mkt) -> {forecaster id: float array, one value per bar of a}`:
`a` is one name's bars as arrays (data.arrays), `mkt` the market's raw inputs {"spy": SPY's bars as arrays, "vix":
{session: close}}. The laws (desk.forecast.Laws):
  1. point_in_time  for each history, every bar after a seeded t (the name's and the market's) is replaced by other
                    random values: the output at bars 0..t is bit-identical (compared as uint64 views)
  2. deterministic  two runs on the same input are bit-identical (uint64 views, NaN payloads included)
  3. bounded        every value is NaN or finite and inside the declared [lo, hi]; on a history without defects a
                    forecaster that does not abstain is finite at every bar from its warmup on (NaN only where data is
                    missing)
Histories (HISTORIES = 200 by default): real NYSE sessions from a seeded start; prices a random walk at a random scale
(1e-4 to 1e6); about half carry defects: date gaps (more than 45 calendar days), price gaps, zero-volume runs, +0 and
-0 prices, NaN bars and single bad prints."""
from datetime import date, datetime, time as dtime, timedelta, timezone

import numpy as np

from .. import calendar as cal

HISTORIES = 200


def _sessions(start, n, gap_at=None, gap_days=0):
    out, d = [], start
    while len(out) < n:
        if cal.is_trading_day(d):
            out.append(d)
            if gap_at is not None and len(out) == gap_at:
                d = d + timedelta(days=gap_days)
        d = d + timedelta(days=1)
    return out


def _bars(rng, sess, scale, vol, defects):
    n = len(sess)
    r = rng.normal(0.0003, vol, n)
    c = scale * np.exp(np.cumsum(r))
    o = c * np.exp(rng.normal(0, vol / 3, n))
    h = np.maximum(o, c) * np.exp(np.abs(rng.normal(0, vol / 2, n)))
    l = np.minimum(o, c) * np.exp(-np.abs(rng.normal(0, vol / 2, n)))
    v = np.round(rng.lognormal(12, 1, n))
    if defects:
        for _ in range(rng.integers(1, 4)):
            k = int(rng.integers(0, 7))
            i = int(rng.integers(1, n))
            if k == 0:
                o[i] = c[i - 1] * float(rng.choice([0.5, 1.8]))         # a price gap
                h[i], l[i] = max(h[i], o[i]), min(l[i], o[i])
            elif k == 1:
                v[i:i + int(rng.integers(1, 15))] = 0.0                     # zero-volume run
            elif k == 2:
                c[i] = 0.0                                                   # +0 price
            elif k == 3:
                l[i] = -0.0                                                  # -0 price
            elif k == 4:
                o[i] = h[i] = l[i] = c[i] = np.nan                           # a NaN bar
            elif k == 5:
                c[i] = c[i] * 25                                             # a bad print
            else:
                v[i] = np.nan
    t = np.array([datetime.combine(s, dtime(5, 0), timezone.utc).timestamp() for s in sess])
    return {"t": t, "o": o, "h": h, "l": l, "c": c, "v": v, "d": np.array([s.isoformat() for s in sess])}


def history(seed, n=None):
    """(name arrays, market inputs, defects flag) for one seed"""
    rng = np.random.default_rng(seed)
    n = int(n or rng.integers(300, 420))
    defects = bool(rng.random() < 0.5)
    start = date(2005, 1, 3) + timedelta(days=int(rng.integers(0, 6000)))
    gap = int(rng.integers(50, n - 10)) if defects and rng.random() < 0.3 else None
    sess = _sessions(start, n, gap, int(rng.integers(46, 120)) if gap else 0)
    scale = float(10 ** rng.uniform(-4, 6))
    a = _bars(rng, sess, scale, float(rng.uniform(0.005, 0.06)), defects)
    spy = _bars(rng, sess, 300.0, 0.011, False)
    vix = {d: float(x) for d, x in zip(spy["d"], 12 + 30 * rng.random(n))}
    return a, dict({"spy": spy, "vix": vix}, **extra_market(seed, spy["d"], vix)), defects


EXTRA = ("vix3m", "skew", "gex", "dix")


def extra_market(seed, sessions, vix):
    """P2's further market inputs ({session: value}), from their own random stream so P1's histories are unchanged:
    VIX3M, SKEW, SqueezeMetrics-style GEX (sign changes included) and DIX; a few sessions are missing"""
    rng = np.random.default_rng(30_000 + seed)
    n = len(sessions)
    out = {"vix3m": {d: v * float(np.exp(rng.normal(0.05, 0.08))) for d, v in vix.items()},
           "skew": dict(zip(sessions, 110 + 40 * rng.random(n))),
           "gex": dict(zip(sessions, 1e9 * np.cumsum(rng.normal(0.02, 0.3, n)))),
           "dix": dict(zip(sessions, 0.35 + 0.15 * rng.random(n)))}
    for k in EXTRA:
        for d in list(rng.choice(np.asarray(sessions), size=int(rng.integers(0, 4)), replace=False)):
            out[k].pop(d, None)
    return out


def perturb(a, mkt, t, seed):
    """a copy with every bar after t (name and market) replaced by other random values"""
    rng = np.random.default_rng(10_000 + seed)
    b = {k: np.array(v, copy=True) for k, v in a.items()}
    n = len(b["c"])
    k = n - t - 1
    if k > 0:
        for key in ("o", "h", "l", "c"):
            b[key][t + 1:] = b[key][t + 1:] * np.exp(rng.normal(0, 0.2, k)) + rng.normal(0, 1e-3, k)
        b["v"][t + 1:] = rng.lognormal(10, 2, k)
        b["c"][t + 1 + int(rng.integers(0, k))] = np.nan
    s = {kk: np.array(v, copy=True) for kk, v in mkt["spy"].items()}
    if k > 0:
        for key in ("o", "h", "l", "c"):
            s[key][t + 1:] = s[key][t + 1:] * np.exp(rng.normal(0, 0.1, k))
    vix = dict(mkt["vix"])
    for d in list(a["d"][t + 1:]):
        vix[d] = float(10 + 70 * rng.random())
    out = {"spy": s, "vix": vix}
    for k in EXTRA:
        if k in mkt:
            x = dict(mkt[k])
            for d in list(a["d"][t + 1:]):
                x[d] = float(x.get(d, 1.0)) * float(np.exp(rng.normal(0, 0.5))) + float(rng.normal(0, 1))
            out[k] = x
    return b, out


def _u64(x):
    return np.ascontiguousarray(np.asarray(x, dtype=np.float64)).view(np.uint64)


def check(compute, forecasters, histories=HISTORIES, seed0=0, n=None):
    """{forecaster id: [failure strings]} for one compute group; an empty list for each id is a pass"""
    fails = {f.id: [] for f in forecasters}
    byid = {f.id: f for f in forecasters}
    for s in range(seed0, seed0 + histories):
        a, mkt, defects = history(s, n)
        nb = len(a["c"])
        out1 = compute(a, mkt)
        m2 = {k: dict(v) for k, v in mkt.items() if k != "spy"}
        m2["spy"] = {k: np.array(v, copy=True) for k, v in mkt["spy"].items()}
        out2 = compute({k: np.array(v, copy=True) for k, v in a.items()}, m2)
        rng = np.random.default_rng(20_000 + s)
        t = int(rng.integers(min(nb - 2, 200), nb - 1))
        pa, pm = perturb(a, mkt, t, s)
        out3 = compute(pa, pm)
        for fid, f in byid.items():
            if len(fails[fid]) >= 3:
                continue
            x1, x2, x3 = out1.get(fid), out2.get(fid), out3.get(fid)
            if x1 is None or x2 is None or x3 is None or len(x1) != nb:
                fails[fid].append(f"seed {s}: no output of length {nb}")
                continue
            if not np.array_equal(_u64(x1), _u64(x2)):
                fails[fid].append(f"seed {s}: not deterministic")
            if not np.array_equal(_u64(x1)[:t + 1], _u64(x3)[:t + 1]):
                j = int(np.argmax(_u64(x1)[:t + 1] != _u64(x3)[:t + 1]))
                fails[fid].append(f"seed {s}: look-ahead (bar {j} changed when bars after {t} changed)")
            lo, hi = f.laws.bounded
            x = np.asarray(x1, float)
            fin = np.isfinite(x)
            if np.isinf(x).any():
                fails[fid].append(f"seed {s}: infinite output")
            if (x[fin] < lo).any() or (x[fin] > hi).any():
                fails[fid].append(f"seed {s}: out of bounds [{lo}, {hi}]")
            if not defects and not f.laws.abstains:
                w = f.laws.warmup
                if w < nb and not fin[w:].all():
                    j = w + int(np.argmin(fin[w:]))
                    fails[fid].append(f"seed {s}: NaN at bar {j} on a clean history (warmup {w})")
    return fails
