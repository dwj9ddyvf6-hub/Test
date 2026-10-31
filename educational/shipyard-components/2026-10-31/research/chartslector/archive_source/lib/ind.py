"""Panel indicators (S x T float32 arrays, NaN-aware), Pine-faithful where it matters:
ta.rma/ta.atr = Wilder (alpha 1/n), ta.ema = EMA alpha 2/(n+1), ta.sma = simple mean over n non-NaN bars (min_periods = n)."""
import numpy as np, pandas as pd
def _df(a): return pd.DataFrame(a.T)
def sma(a, n, mp=None): return _df(a).rolling(n, min_periods=mp or n).mean().values.T.astype(np.float32)
def rstd(a, n, mp=None): return _df(a).rolling(n, min_periods=mp or n).std(ddof=0).values.T.astype(np.float32)
def rmax(a, n, mp=None): return _df(a).rolling(n, min_periods=mp or n).max().values.T.astype(np.float32)
def rmin(a, n, mp=None): return _df(a).rolling(n, min_periods=mp or n).min().values.T.astype(np.float32)
def rsum(a, n, mp=None): return _df(a).rolling(n, min_periods=mp or n).sum().values.T.astype(np.float32)
def ema(a, n): return _df(a).ewm(span=n, adjust=False, min_periods=n).mean().values.T.astype(np.float32)
import numba as _nb
@_nb.njit(cache=True)
def _rma(a, n):
    S, T = a.shape; out = np.full((S, T), np.nan, np.float32); al = 1.0 / n
    for s in range(S):
        prev = np.nan; run = 0; acc = 0.0
        for t in range(T):
            x = a[s, t]
            if np.isnan(x):
                prev = np.nan; run = 0; acc = 0.0; continue
            if np.isnan(prev):
                run += 1; acc += x
                if run > n: acc -= a[s, t - n]
                if run >= n: prev = acc / n; out[s, t] = prev
            else:
                prev = al * x + (1 - al) * prev; out[s, t] = prev
    return out
def rma(a, n):
    """Pine ta.rma: seeded with ta.sma(src, n) on the first n consecutive valid bars, then alpha 1/n; a na source breaks the chain and re-seeds."""
    return _rma(np.ascontiguousarray(a, dtype=np.float64), n)
def lag(a, k=1):
    out = np.full_like(a, np.nan)
    if k > 0: out[:, k:] = a[:, :-k]
    elif k < 0: out[:, :k] = a[:, -k:]
    else: out = a.copy()
    return out
def ffill(a, limit=None): return _df(a).ffill(limit=limit).values.T.astype(np.float32)
def tr(H, L, C):
    pc = lag(C); return np.fmax(H - L, np.fmax(np.abs(H - pc), np.abs(L - pc))).astype(np.float32)
def atr(H, L, C, n=14): return rma(tr(H, L, C), n)
def xrank(a, mask=None):
    """cross-sectional percentile 0-100 per day (column), among finite (and mask) entries."""
    x = a.astype(np.float64).copy()
    if mask is not None: x[~mask] = np.nan
    r = pd.DataFrame(x).rank(axis=0, pct=True).values
    return (r * 100).astype(np.float32)
def rising(a, k=1): return a > lag(a, k)
def consec(b):
    """count of consecutive True up to and including t (per row)."""
    out = np.zeros(b.shape, np.int16); run = np.zeros(b.shape[0], np.int16)
    for t in range(b.shape[1]):
        run = np.where(b[:, t], run + 1, 0); out[:, t] = run
    return out
def to_weekly(P, keys=("O", "H", "L", "C", "V")):
    """resample daily panel to weekly (W-FRI) bars: O first, H max, L min, C last, V sum. Returns dict + week-end dates + last-daily-index per week."""
    days = P["days"]; wk = days.to_period("W-FRI"); g = pd.Series(np.arange(len(days)), index=days).groupby(wk)
    last = g.max().values; first = g.min().values; W = {}
    for k in keys:
        a = P[k]
        if k == "O":
            W[k] = np.stack([pd.DataFrame(a[:, f:l + 1].T).bfill().iloc[0].values if True else None for f, l in zip(first, last)], 1).astype(np.float32)
        elif k == "H": W[k] = np.stack([np.nanmax(a[:, f:l + 1], 1) for f, l in zip(first, last)], 1).astype(np.float32)
        elif k == "L": W[k] = np.stack([np.nanmin(a[:, f:l + 1], 1) for f, l in zip(first, last)], 1).astype(np.float32)
        elif k == "C": W[k] = np.stack([pd.DataFrame(a[:, f:l + 1].T).ffill().iloc[-1].values for f, l in zip(first, last)], 1).astype(np.float32)
        elif k == "V": W[k] = np.stack([np.nansum(a[:, f:l + 1], 1) for f, l in zip(first, last)], 1).astype(np.float32)
    return W, days[last], last, first
