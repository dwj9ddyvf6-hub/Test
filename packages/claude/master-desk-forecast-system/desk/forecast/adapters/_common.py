"""Shared closed-bar helpers for the P2 adapters: every function reads bars 0..t for its value at t (pandas rolling
windows with full min_periods, recursive filters started at bar 0), so a value never depends on a later bar.

wrap(fn, ids) turns a per-name function of the guarded bars into a law-checkable compute group: data.guard masks the
unusable bars, fn runs on the usable bars only, and its outputs are scattered back (NaN on unusable bars), the P1
adapters' rule. An infinite intermediate is NaN, never a value."""
import numpy as np
import pandas as pd
from scipy.signal import lfilter

from .. import data as D


def roll(x, w, f, minp=None):
    return np.array(getattr(pd.Series(np.asarray(x, float)).rolling(w, min_periods=minp or w), f)().to_numpy())


def lag(x, k=1):
    x = np.asarray(x, float)
    out = np.full(len(x), np.nan)
    if 0 < k < len(x):
        out[k:] = x[:-k]
    return out


def ret(c, k=1):
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.asarray(c, float) / lag(c, k) - 1


def ema(x, span):
    """the recursive EMA from bar 0 (alpha = 2 / (span + 1)), NaN-free input assumed; NaN before `span` bars"""
    x = np.asarray(x, float)
    a = 2.0 / (span + 1)
    if not len(x):
        return x
    y = lfilter([a], [1, -(1 - a)], x, zi=[(1 - a) * x[0]])[0]
    y[:span - 1] = np.nan
    return y


def wilder(x, n):
    """Wilder's smoothing (alpha = 1/n) from bar 0"""
    x = np.asarray(x, float)
    a = 1.0 / n
    if not len(x):
        return x
    return lfilter([a], [1, -(1 - a)], x, zi=[(1 - a) * x[0]])[0]


def rsi(c, n=14):
    c = np.asarray(c, float)
    d = np.r_[0.0, np.diff(c)]
    up, dn = wilder(np.maximum(d, 0), n), wilder(np.maximum(-d, 0), n)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = 100 - 100 / (1 + up / dn)
    out = np.where(dn == 0, np.where(up > 0, 100.0, 50.0), out)
    out[:n] = np.nan
    return out


def true_range(h, l, c):
    pc = lag(c)
    tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
    return tr


def atr(h, l, c, n=14):
    return roll(true_range(h, l, c), n, "mean")


def finite(x):
    x = np.asarray(x, float)
    return np.where(np.isfinite(x), x, np.nan)


def market_series(mkt, key):
    """a market input as a Series indexed by session: SPY's guarded closes, or a {session: value} dict"""
    x = mkt[key]
    if isinstance(x, pd.Series):
        return x
    if key == "spy":
        ok = D.guard(x)
        return pd.Series(np.asarray(x["c"], float)[ok], index=np.asarray(x["d"])[ok])
    s = pd.Series(x, dtype=float).sort_index()
    return s[np.isfinite(s.to_numpy())]


def on(dates, series):
    """series values on the given sessions (NaN where missing)"""
    return pd.Series(np.asarray(dates)).map(series).to_numpy(float)


def wrap(fn, ids, prefix=""):
    def compute(a, mkt, m=None):
        n = len(a["c"])
        out = {i: np.full(n, np.nan) for i in ids}
        ok = D.guard(a)
        idx = np.where(ok)[0]
        if len(idx) < 2:
            return out
        b = D.masked(a, ok)
        v = np.asarray(b["v"], float)
        b["v"] = np.where(np.isfinite(v), v, np.nan)
        res = fn(b, m if m is not None else market(mkt))
        for k, x in res.items():
            out[prefix + k][idx] = finite(x)
        return out
    return compute


def market(mkt):
    """the market inputs every P2 adapter reads, computed once per run (pass as m=)"""
    s = market_series(mkt, "spy")
    out = {"spy": s, "spyr": s.pct_change(), "spy126": s.pct_change(126)}
    for k in ("vix", "vix3m", "skew", "gex", "dix"):
        if k in mkt:
            out[k] = market_series(mkt, k)
    return out
