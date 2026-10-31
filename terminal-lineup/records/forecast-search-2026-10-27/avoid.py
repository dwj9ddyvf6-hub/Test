"""The avoid arm as DOWN forecasters: the per-name rules of scratchpad xcheck/avoid/build.py, formulas unchanged, on
the bad-print-guarded bars (data.guard is build.py's own guard plus missing / non-positive prices and high < low).
Its two discovery thresholds (DEEP 2016-22) are loaded through the sha256 pin (freeze.load("avoid-deep-1")).

  r = c / c[-1] - 1; r5 = c / c[-5] - 1; r20 = c / c[-20] - 1; m50 = 50-bar mean; vm1 = the 60-bar median volume of
  the bars before; beta = 60-bar cov(r, SPY r) / var(SPY r)
  avoid.jump25    any r >= +25% in the last 20 bars
  avoid.deadcat   c / 60-bar high <= 0.6 and r5 >= +15%
  avoid.surge2    >= 2 bars in 20 with |r| >= 10% on volume >= 3 vm1
  avoid.pump      r5 >= +30% on volume >= 3 vm1          (build.py's A_pump_nano is this in the nano tier: tier is a
                                                          context cell, never a filter here)
  avoid.mfi75     the 14-bar money-flow index >= 75       (A_mfi_nano likewise)
  avoid.stretch   c / m50 - 1 >= stretch_q95 (frozen)
  avoid.x1p6      c / m50 - 1 >= 0.6
  avoid.idio      r5 <= -5% and |r5 - beta SPY r5| / |r5| >= idio_q80_r5neg (frozen)
  avoid.newlist   fewer than 252 bars of the name's history
  avoid.r20       r20 itself (A_loser is its bottom decile within the small tiers of the day: a cross-sectional cut
                  the scorer applies by cell; a higher r20 forecasts a better excess, sign +1)
Every flag is 1.0 or 0.0 (0.0 while its window is short, as build.py's fillna(False)); NaN on unusable bars. A flag
forecasts a lower 20-session excess (sign -1 on up_excess_20)."""
import numpy as np
import pandas as pd

from .. import Forecaster, Laws
from .. import data as D
from .. import freeze as FR

FLAGS = ("jump25", "deadcat", "surge2", "pump", "mfi75", "stretch", "x1p6", "idio", "newlist")
EVID = ("FACTORY.md §2 avoid arm", "xcheck/avoid/build.py", "xcheck/avoid/run.log")


def _fc(k, sign, bounds, warm=0):
    return Forecaster(id=f"avoid.{k}", version="avoid-deep-1", kind="rule", owner_module="desk.forecast.adapters.avoid",
                      family="avoid", targets=("up_excess_20", "up_excess_60"),
                      laws=Laws(bounded=bounds, warmup=warm, costed="own_name_half_spread"),
                      inputs=("daily bars", "SPY"), frozen_sha=FR.PINS["avoid-deep-1"], grade="B", sign=sign,
                      evidence=EVID)


FORECASTERS = tuple(_fc(k, -1, (0.0, 1.0)) for k in FLAGS) + (_fc("r20", 1, (-1.0, float("inf")), warm=20),)


def _roll(x, w, f):
    return getattr(pd.Series(x).rolling(w, min_periods=w), f)().to_numpy()


def flags(d, h, l, c, v, spyr, thr):
    n = len(c)
    r = np.r_[np.nan, c[1:] / c[:-1] - 1]
    r5 = np.r_[np.full(min(5, n), np.nan), c[5:] / c[:-5] - 1] if n > 5 else np.full(n, np.nan)
    r20 = np.r_[np.full(20, np.nan), c[20:] / c[:-20] - 1] if n > 20 else np.full(n, np.nan)
    m50 = _roll(c, 50, "mean")
    stretch = c / m50 - 1
    sp = pd.Series(d).map(spyr["r1"]).to_numpy(float)
    sp5 = pd.Series(d).map(spyr["r5"]).to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        cov = _roll(r * sp, 60, "mean") - _roll(r, 60, "mean") * _roll(sp, 60, "mean")
        bet = cov / _roll(sp, 60, "var")
        idio = np.abs(r5 - bet * sp5) / np.where(np.abs(r5) > 0, np.abs(r5), np.nan)
        hi60 = _roll(h, 60, "max")
        vmed = _roll(v, 60, "median")
        vm1 = np.r_[np.nan, vmed[:-1]]
        tp = (h + l + c) / 3
        mf = tp * v
        dtp = np.r_[0, np.diff(tp)]
        pos = _roll(np.where(dtp > 0, mf, 0), 14, "sum")
        neg = _roll(np.where(dtp < 0, mf, 0), 14, "sum")
        mfi = 100 - 100 / (1 + pos / np.where(neg > 0, neg, np.nan))
        out = {"jump25": _roll((r >= 0.25).astype(float), 20, "max") == 1,
               "deadcat": (c / hi60 <= 0.6) & (r5 >= 0.15),
               "surge2": _roll(((np.abs(r) >= 0.10) & (v >= 3 * vm1)).astype(float), 20, "sum") >= 2,
               "pump": (r5 >= 0.30) & (v >= 3 * vm1),
               "mfi75": mfi >= 75,
               "stretch": stretch >= thr["stretch_q95"],
               "x1p6": stretch >= 0.6,
               "idio": (r5 <= -0.05) & (idio >= thr["idio_q80_r5neg"]),
               "newlist": np.arange(n) < 252}
    res = {k: v_.astype(float) for k, v_ in out.items()}
    res["r20"] = np.where(np.isfinite(r20), r20, np.nan)
    return res


def spy_returns(mkt):
    from .features import spy_series
    s = mkt["spy"] if isinstance(mkt["spy"], pd.Series) else spy_series(mkt["spy"])
    return {"r1": s.pct_change(), "r5": s.pct_change(5)}


def compute(a, mkt, spyr=None, thr=None):
    n = len(a["c"])
    out = {f.id: np.full(n, np.nan) for f in FORECASTERS}
    ok = D.guard(a)
    idx = np.where(ok)[0]
    if not len(idx):
        return out
    b = D.masked(a, ok)
    v = np.where(np.isfinite(b["v"]), b["v"], np.nan)
    f = flags(np.asarray(b["d"]), b["h"], b["l"], b["c"], v, spyr or spy_returns(mkt), thr or FR.load("avoid-deep-1"))
    for k, x in f.items():
        out["avoid." + k][idx] = x
    return out
