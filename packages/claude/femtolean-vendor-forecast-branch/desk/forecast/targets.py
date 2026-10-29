"""Target labels on a closed-bar path (FACTORY.md §3): pure functions of one name's arrays. A decision at the close of
bar i is filled at the open of i+1, so every label reads bars i+1 onward only and is NaN when the path is short.

  fwd_return    close[i+h] / open[i+1] - 1
  excess        a label minus the same-day mean of its group (the state group, or the whole day)
  p_drawdown    1{min low[i+1..i+h] / open[i+1] - 1 <= -X}
  no_move       1{|r_h| < k sigma sqrt(h)}, sigma = the per-day volatility forecast known at i (FB2's HAR sigma_mean)
  big_move      1{|r_h| >= max(X, k sigma sqrt(h))}
  realized_vol  log of the realized daily volatility over i+1..i+h (0.5 log of the sample variance of the h daily log
                returns from close i to close i+h), FB2's lrv20 convention; scored by QLIKE
  path          +t1 first vs -out first in ATRs from the fill: desk/terminal/odds.simulate's bar rules, unchanged
                (a close at or under the out line sells at the next open; the target is an intraday high; the fill bar
                checks the out line only; the out line first on a bar that does both; time stop ts)
  time_to_move  sessions until the high or the low is `move` away from the fill (censored at h: NaN, `censored`)
"""
import numpy as np

from ..terminal import odds as O
from . import Target

UP20 = Target("up_excess_20", "up_excess", 20, benchmark="same_day_state_mean", loss="rank_ic")
UP60 = Target("up_excess_60", "up_excess", 60, benchmark="same_day_state_mean", loss="rank_ic")
DOWN20 = Target("down_excess_20", "down_excess", 20, benchmark="same_day_state_mean", loss="rank_ic")
PATH20 = Target("path_t1_stop_20", "path", 20, params={"rules": "odds.simulate"}, benchmark="random_same_name",
                loss="mean_r")
RV20 = Target("realized_vol_20", "realized_vol", 20, benchmark="none", loss="qlike")
TARGETS = {t.id: t for t in (UP20, UP60, DOWN20, PATH20, RV20)}


def _shift(x, k):
    """x[i + k] at i (NaN past the end)"""
    x = np.asarray(x, float)
    out = np.full(len(x), np.nan)
    if k < len(x):
        out[:len(x) - k] = x[k:]
    return out


def fwd_return(a, h):
    return _shift(a["c"], h) / _shift(a["o"], 1) - 1


def excess(values, dates, groups=None):
    """values minus the mean of the finite values sharing (date, group)"""
    import pandas as pd
    df = pd.DataFrame({"y": np.asarray(values, float), "d": np.asarray(dates)})
    keys = ["d"]
    if groups is not None:
        df["g"] = np.asarray(groups)
        keys.append("g")
    return (df["y"] - df.groupby(keys)["y"].transform("mean")).to_numpy()


def _fwd_window(x, h):
    """(n, h) matrix of x[i+1 .. i+h]; NaN past the end"""
    x = np.asarray(x, float)
    n = len(x)
    m = np.full((n, h), np.nan)
    for j in range(1, h + 1):
        m[:, j - 1] = _shift(x, j)
    return m


def p_drawdown(a, h, X):
    lows = _fwd_window(a["l"], h)
    e = _shift(a["o"], 1)
    full = np.isfinite(lows).all(axis=1) & np.isfinite(e)
    out = np.full(len(e), np.nan)
    with np.errstate(invalid="ignore"):
        out[full] = (lows[full].min(axis=1) / e[full] - 1 <= -X).astype(float)
    return out


def no_move(a, h, k, sigma):
    r = fwd_return(a, h)
    band = k * np.asarray(sigma, float) * np.sqrt(h)
    out = np.where(np.isfinite(r) & np.isfinite(band), (np.abs(r) < band).astype(float), np.nan)
    return out


def big_move(a, h, X, k, sigma):
    r = fwd_return(a, h)
    band = np.maximum(X, k * np.asarray(sigma, float) * np.sqrt(h))
    return np.where(np.isfinite(r) & np.isfinite(band), (np.abs(r) >= band).astype(float), np.nan)


def realized_vol(a, h):
    """log realized daily volatility over i+1..i+h (h log returns from close i)"""
    c = np.asarray(a["c"], float)
    lr = np.full(len(c), np.nan)
    lr[1:] = np.log(c[1:] / c[:-1])
    w = _fwd_window(lr, h)
    out = np.full(len(c), np.nan)
    ok = np.isfinite(w).all(axis=1)
    if ok.any():
        v = w[ok].var(axis=1, ddof=1)
        out[ok] = 0.5 * np.log(np.maximum(v, 1e-8))
    return out


def qlike(log_rv, log_sigma):
    """QLIKE of a volatility forecast: RV^2/s^2 - ln(RV^2/s^2) - 1 (0 at a perfect forecast, >= 0)"""
    x = np.exp(2 * (np.asarray(log_rv, float) - np.asarray(log_sigma, float)))
    return x - np.log(x) - 1


def path(a, i, out, t1, t2=None, ts=20, risk=None):
    """the path label at bar i for a plan (distances in ATRs from the fill): odds.simulate's dict for that one case,
    or None when bar i has no next bar. `a` needs the odds engine's atr (O.indicators)"""
    p = O.path(a, i)
    if p is None:
        return None
    s = O.simulate(p[None], out, t1, t2, ts, risk)
    return {k: (v[0].item() if hasattr(v[0], "item") else v[0]) for k, v in s.items()}


def time_to_move(a, h, move):
    """(sessions to a high or low `move` (fraction) from the fill, censored flag); sessions count from the fill bar 1"""
    e = _shift(a["o"], 1)
    hi, lo = _fwd_window(a["h"], h), _fwd_window(a["l"], h)
    n = len(e)
    days = np.full(n, np.nan)
    cens = np.zeros(n, bool)
    with np.errstate(invalid="ignore"):
        hit = (hi / e[:, None] - 1 >= move) | (1 - lo / e[:, None] >= move)
    full = np.isfinite(hi).all(axis=1) & np.isfinite(lo).all(axis=1) & np.isfinite(e)
    any_ = hit.any(axis=1)
    days[full & any_] = np.argmax(hit[full & any_], axis=1) + 1
    cens[full & ~any_] = True
    return days, cens
