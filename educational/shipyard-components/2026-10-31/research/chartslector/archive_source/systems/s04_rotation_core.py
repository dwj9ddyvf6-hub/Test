"""Importable Pine translations used by s04_rotation.py: RS-table percentrank (S5) and Relative Robustness Rotation (S6)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "[LOCAL_PATH_NOT_INCLUDED]")
import ind as I
from numpy.lib.stride_tricks import sliding_window_view as swv
def prank(x, n):
    """ta.percentrank(x, n): % of the previous n values <= current value."""
    x = np.asarray(x, float); out = np.full(x.shape, np.nan); w = swv(x, n + 1, axis=1); cur = w[..., -1:]; prev = w[..., :-1]
    out[:, n:] = np.where(np.isfinite(prev).all(-1) & np.isfinite(cur[..., 0]), (prev <= cur).sum(-1) / n * 100, np.nan); return out
def _ema(a, n): return pd.DataFrame(np.asarray(a, float).T).ewm(span=n, adjust=False).mean().values.T
def rrr(c, ref, fastW=0.6):
    """RRR Blended (735b7ed): RS line 100*c/ref; ratio = 100*EMA(rs,s)/EMA(EMA(rs,s),n) blended fast(15,21)/slow(26,34) 60/40; momentum the same on the ratio
    with fast(8,15)/slow(15,26); + acceleration 0.10*tanh(z) where z = (1-bar change - 5-bar avg change)/stdev(1-bar change, 20)."""
    rs = 100 * np.asarray(c, float) / np.asarray(ref, float)[None, :]
    def ratio(x, s, nn): sm = _ema(x, s); b = _ema(sm, nn); return 100 * sm / b
    R = fastW * ratio(rs, 15, 21) + (1 - fastW) * ratio(rs, 26, 34)
    M = fastW * ratio(R, 8, 15) + (1 - fastW) * ratio(R, 15, 26)
    ch1 = np.c_[np.full((R.shape[0], 1), np.nan), np.diff(R, axis=1)]; chl = np.c_[np.full((R.shape[0], 5), np.nan), (R[:, 5:] - R[:, :-5]) / 5]
    vol = pd.DataFrame(ch1.T).rolling(20, min_periods=20).std(ddof=0).values.T
    with np.errstate(invalid="ignore", divide="ignore"):
        z = np.where(vol > 1e-12, (ch1 - chl) / (vol + 1e-12), np.nan)
    adj = np.nan_to_num(0.10 * np.tanh(np.clip(z, -20, 20)))
    return R, M + adj
