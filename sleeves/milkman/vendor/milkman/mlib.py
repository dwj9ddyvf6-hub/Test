"""Shared library for the Milkman v2 study: Saty indicators (ported from his public scripts/indicators.py), trade stats,
month-block bootstrap, permutation p, BH. Everything at bar t uses bars <= t."""
import numpy as np, pandas as pd
CA = "<workspace>/milkman-study/v2/cache"; OUT = "<workspace>/milkman-study/v2/out"
SPLITS_U = (pd.Timestamp("2017-06-01"), pd.Timestamp("2022-07-01"), pd.Timestamp("2025-01-01"))   # universe: train | holdout | fresh
SPLITS_X = (pd.Timestamp("1993-01-01"), pd.Timestamp("2013-01-01"), pd.Timestamp("2021-01-01"))   # long index history
SPLITS_I = (pd.Timestamp("2000-01-01"), pd.Timestamp("2013-01-01"), pd.Timestamp("2021-01-01"))   # SPY intraday vault (fresh = 2021..2026-04)
def seg(dt, S):
    dt = pd.to_datetime(np.asarray(dt))
    return np.where(dt < S[0], "pre", np.where(dt < S[1], "train", np.where(dt < S[2], "holdout", "fresh")))
def ema(x, n): return pd.Series(x).ewm(span=n, adjust=False).mean().values
def rma(x, n): return pd.Series(x).ewm(alpha=1.0 / n, adjust=False).mean().values
def sma(x, n): return pd.Series(x).rolling(n, min_periods=n).mean().values
def atr(h, l, c, n=14):
    pc = np.r_[np.nan, c[:-1]]; tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0); return rma(tr, n)
def po(c, h, l):
    """Saty Phase Oscillator: EMA3(((close-EMA21)/(3*ATR14))*100)."""
    a = atr(h, l, c, 14); return ema((c - ema(c, 21)) / (3 * a) * 100, 3)
def compression(c, h, l):
    """Saty compression flag, exact port of his public indicators.py (po_compression / compression)."""
    a = atr(h, l, c, 14); piv = ema(c, 21); sd = pd.Series(c).rolling(21, min_periods=1).std().values
    above = c >= piv
    comp = np.where(above, (piv + 2 * sd) - (piv + 2 * a), (piv - 2 * a) - (piv - 2 * sd))
    inexp = np.where(above, (piv + 2 * sd) - (piv + 1.854 * a), (piv - 1.854 * a) - (piv - 2 * sd))
    expansion = np.r_[False, comp[:-1] <= comp[1:]]
    out = ((comp <= 0) & ~(expansion & (inexp > 0))).astype(np.int8); out[0] = 0   # faithful: non-stateful, as in his indicators.py
    return out
def stats(r):
    r = np.asarray(r, float); r = r[np.isfinite(r)]; n = len(r)
    if n == 0: return dict(n=0, mean=np.nan, med=np.nan, win=np.nan, pf=np.nan, t=np.nan)
    g = r[r > 0].sum(); L = -r[r < 0].sum()
    return dict(n=n, mean=r.mean(), med=np.median(r), win=(r > 0).mean() * 100, pf=g / L if L > 0 else np.inf, t=r.mean() / (r.std(ddof=1) / np.sqrt(n)) if n > 2 and r.std() > 0 else np.nan)
def month_boot(r, month, nb=2000, seed=11):
    """mean and 95% CI by month-block bootstrap; two-sided p vs 0."""
    r = np.asarray(r, float); ok = np.isfinite(r); r = r[ok]; m = np.asarray(month)[ok]
    if len(r) < 5: return (r.mean() if len(r) else np.nan, np.nan, np.nan, np.nan)
    um, inv = np.unique(m, return_inverse=True); K = len(um); S = np.bincount(inv, weights=r, minlength=K); N = np.bincount(inv, minlength=K).astype(float)
    W = np.random.default_rng(seed).multinomial(K, np.ones(K) / K, size=nb); bs = (W @ S) / np.maximum(W @ N, 1e-9); bs = bs[(W @ N) > 0]
    p = max(2 * min((bs <= 0).mean(), (bs >= 0).mean()), 1 / len(bs)); lo, hi = np.percentile(bs, [2.5, 97.5]); return r.mean(), lo, hi, p
def bh(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p); q = np.empty(n); prev = 1.0
    for r_, i in enumerate(o[::-1]):
        k = n - r_; prev = min(prev, p[i] * n / k); q[i] = prev
    return q
def holm(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p); q = np.empty(n); run = 0
    for r_, i in enumerate(o):
        run = max(run, min(1, p[i] * (n - r_))); q[i] = run
    return q
def cost_side(px):
    """research cost per side in % (same convention as deep_reset): 0.05 + spread bucket."""
    px = np.asarray(px, float); return 0.05 + np.where(px < 5, 0.25, np.where(px < 20, 0.10, 0.05))
