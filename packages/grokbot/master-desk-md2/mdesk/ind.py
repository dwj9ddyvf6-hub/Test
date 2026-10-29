"""Indicators on numpy arrays. Each returns an array aligned to input (nan where undefined)."""
import numpy as np
nan = np.nan
def sma(x, n):
    x = np.asarray(x, float); out = np.full(len(x), nan)
    if len(x) >= n: c = np.cumsum(np.insert(x, 0, 0.0)); out[n - 1:] = (c[n:] - c[:-n]) / n
    return out
def ema(x, n):   # recursive EMA seeded with first value (current-inclusive)
    x = np.asarray(x, float); out = np.empty(len(x)); a = 2.0 / (n + 1)
    if not len(x): return out
    out[0] = x[0]
    for i in range(1, len(x)): out[i] = out[i - 1] + a * (x[i] - out[i - 1])
    return out
def wilder_rsi(c, n=2):
    c = np.asarray(c, float); out = np.full(len(c), nan)
    if len(c) <= n: return out
    d = np.diff(c); g = np.maximum(d, 0); l = np.maximum(-d, 0)
    ag = g[:n].mean(); al = l[:n].mean()
    def v(ag, al): return 100.0 if al == 0 and ag > 0 else (50.0 if al == 0 else 100 - 100 / (1 + ag / al))
    out[n] = v(ag, al)
    for i in range(n, len(d)):
        ag = (ag * (n - 1) + g[i]) / n; al = (al * (n - 1) + l[i]) / n; out[i + 1] = v(ag, al)
    return out
def atr(h, l, c, n=14):
    h, l, c = (np.asarray(x, float) for x in (h, l, c)); tr = np.empty(len(c)); tr[0] = h[0] - l[0]
    tr[1:] = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    out = np.full(len(c), nan)
    if len(c) >= n:
        out[n - 1] = tr[:n].mean()
        for i in range(n, len(c)): out[i] = (out[i - 1] * (n - 1) + tr[i]) / n
    return out
from numpy.lib.stride_tricks import sliding_window_view as _sw
def _roll(x, n, f):
    x = np.asarray(x, float); out = np.full(len(x), nan)
    if len(x) >= n: out[n - 1:] = f(_sw(x, n), axis=1)
    return out
def rolling_max(x, n): return _roll(x, n, np.max)
def rolling_min(x, n): return _roll(x, n, np.min)
def stdev(x, n): return _roll(x, n, np.std)
def linreg_last(y):
    """value of the least-squares line at the last point (Pine linreg(y, n, 0))."""
    n = len(y); xs = np.arange(n); A = np.vstack([xs, np.ones(n)]).T; m, b = np.linalg.lstsq(A, y, rcond=None)[0]; return m * (n - 1) + b
def squeeze(h, l, c, n=20, bbm=2.0, kcm=1.5):
    """LazyBear squeeze: inside = BB within KC; momentum = linreg(close - avg(avg(hh,ll), sma), n)."""
    basis = sma(c, n); dev = bbm * stdev(c, n); rng = sma(np.asarray(h) - np.asarray(l), n)
    inside = (basis - dev > basis - kcm * rng) & (basis + dev < basis + kcm * rng)
    hh, ll = rolling_max(h, n), rolling_min(l, n); mid = ((hh + ll) / 2 + basis) / 2; src = np.asarray(c) - mid
    mom = np.full(len(c), nan)   # vectorised linreg end-point: a + b*(n-1) over every window (same math as linreg_last)
    if len(c) >= 2 * n - 1:
        W = _sw(src[n - 1:], n); xs = np.arange(n); xm = xs.mean(); ym = W.mean(axis=1)
        b = ((xs - xm) * (W - ym[:, None])).sum(axis=1) / ((xs - xm) ** 2).sum(); mom[2 * n - 2:] = ym + b * (n - 1 - xm)
    return inside, mom
