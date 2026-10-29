"""The fear-day survivors as ranking forecasters, with the exact formulas of scratchpad xcheck/novel.py and
xcheck/new10/new10.py (per name, pandas rolling windows on closed bars; SPY on its own calendar, mapped by session):

  r = c.pct_change(); sp = SPY's daily return on the session; beta = 60-session cov(r, sp) / var(sp)
  F3  pb_z           pb = (20d high - c) / ATR14 (simple mean true range); (pb - its 252d median) / its 252d std
  F4  idio_share     |r5 - beta * SPY r5| / |r5|  (an input of N1)
  N1  bystander      F3 * (1 - clip(F4, 0, 1))
  N7  gap absorbed   count over 10 sessions of (open < previous low and close > open)
  F6  downvol decay  down-day volume of the last 10 sessions / (down-day volume of the 30 before / 3)
  F7  sector turn    c.pct_change(10) - SPY's 10-session return            (forecaster feat.F7neg = -F7)
  N5  first responder  on the 2nd session after a fear day: c.pct_change(2) - beta[t-2] * SPY's 2-session return,
                     NaN otherwise (it abstains)                           (forecaster feat.N5neg = -N5)
States and the fear day (contexts here, never filters): UP = c > 200d mean and 50d > 200d and 50d > its value 10
sessions ago; RESET = c <= 0.65 x 252d high and c <= 1.10 x 252d low; fear = SPY <= -1% on the day or SPY under its
50-day mean. A zero denominator is NaN (as the sources' replace(0, nan)); an infinite value (a zero std) is NaN.
Survivor roster (FACTORY.md P1, new10/RESULTS.md): UP F3, N1, N7; RESET -F7, F6, -N5."""
import numpy as np
import pandas as pd

from .. import Forecaster, Laws
from .. import data as D

FEATS = ("F3", "N1", "N7", "F6", "F7neg", "N5neg")
STATE = {"F3": "UP", "N1": "UP", "N7": "UP", "F6": "RESET", "F7neg": "RESET", "N5neg": "RESET"}
WARMUP = {"F3": 272, "N1": 272, "N7": 11, "F6": 41, "F7neg": 11, "N5neg": 0}
BOUND = {"N7": (0.0, 10.0), "F6": (0.0, float("inf"))}
SRC = {"F3": "xcheck/novel.py", "F6": "xcheck/novel.py", "F7neg": "xcheck/novel.py", "N1": "xcheck/new10/new10.py",
       "N7": "xcheck/new10/new10.py", "N5neg": "xcheck/new10/new10.py"}

FORECASTERS = tuple(
    Forecaster(id=f"feat.{k}", version="xcheck-2026-10-27", kind="score", owner_module="desk.forecast.adapters.features",
               family="fearday." + STATE[k], targets=("up_excess_20", "up_excess_60"),
               laws=Laws(bounded=BOUND.get(k, (float("-inf"), float("inf"))), warmup=WARMUP[k],
                         abstains=(k == "N5neg"), costed="own_name_half_spread"),
               contexts_declared=(f"state={STATE[k]}", f"state={STATE[k]}|fear=1"), inputs=("daily bars", "SPY"),
               grade="B", evidence=(SRC[k], "xcheck/new10/RESULTS.md"), sign=1)
    for k in FEATS)


def spy_series(spy):
    """SPY close as a Series on its own sessions (usable bars only)"""
    ok = D.guard(spy)
    return pd.Series(np.asarray(spy["c"], float)[ok], index=np.asarray(spy["d"])[ok])


def market(mkt):
    s = mkt["spy"] if isinstance(mkt["spy"], pd.Series) else spy_series(mkt["spy"])
    spyr = s.pct_change()
    fear = (spyr <= -0.01) | (s < s.rolling(50).mean())
    return {"s": s, "spyr": spyr, "s5": s.pct_change(5), "s10": s.pct_change(10), "s2": s.pct_change(2),
            "fear": fear}


def frame(d, o, h, l, c, v, m):
    """the sources' per-name computation on one name's (usable) bars -> DataFrame of features, states and fear"""
    c, h, l, o, v = (pd.Series(np.asarray(x, float)) for x in (c, h, l, o, v))
    dd = pd.Series(np.asarray(d))
    r = c.pct_change()
    sp = dd.map(m["spyr"]).astype(float)
    fd = dd.map(m["fear"]).fillna(False).astype(bool)
    cov = (r * sp).rolling(60).mean() - r.rolling(60).mean() * sp.rolling(60).mean()
    beta = cov / sp.rolling(60).var()
    m50, m200 = c.rolling(50).mean(), c.rolling(200).mean()
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    up = (c > m200) & (m50 > m200) & (m50 > m50.shift(10))
    hi252, lo252 = h.rolling(252).max(), l.rolling(252).min()
    reset = (c <= hi252 * 0.65) & (c <= lo252 * 1.10)
    f = pd.DataFrame({"d": dd, "state": np.where(up, "UP", np.where(reset, "RESET", "")), "fear": fd,
                      "fear2": fd.shift(2).fillna(False).astype(bool)})
    pb = (h.rolling(20).max() - c) / atr
    f["F3"] = (pb - pb.rolling(252).median()) / pb.rolling(252).std()
    sp5 = dd.map(m["s5"]).astype(float)
    r5 = c.pct_change(5)
    F4 = (r5 - beta * sp5).abs() / r5.abs().replace(0, np.nan)
    f["N1"] = f["F3"] * (1 - F4.clip(0, 1))
    dvol = v.where(r < 0, 0.0)
    f["F6"] = dvol.rolling(10).sum() / (dvol.shift(10).rolling(30).sum() / 3).replace(0, np.nan)
    f["F7"] = c.pct_change(10) - dd.map(m["s10"]).astype(float)
    sp2 = dd.map(m["s2"]).astype(float)
    f["N5"] = (c.pct_change(2) - beta.shift(2) * sp2).where(f["fear2"])
    f["N7"] = ((o < l.shift()) & (c > o)).astype(float).rolling(10).sum()
    f["F7neg"], f["N5neg"] = -f["F7"], -f["N5"]
    for k in FEATS + ("F7", "N5"):
        x = f[k].to_numpy(float)
        f[k] = np.where(np.isfinite(x), x, np.nan)
    return f


def compute(a, mkt, m=None):
    n = len(a["c"])
    out = {f.id: np.full(n, np.nan) for f in FORECASTERS}
    ok = D.guard(a)
    idx = np.where(ok)[0]
    if len(idx) < 2:
        return out
    b = D.masked(a, ok)
    f = frame(b["d"], b["o"], b["h"], b["l"], b["c"], b["v"], m or market(mkt))
    for k in FEATS:
        out["feat." + k][idx] = f[k].to_numpy(float)
    return out
