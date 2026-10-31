"""cl_core.py - self-contained ChartsLector signal math for the paper_sleeve CL lanes (no import of the research tree).
Copied (logic-identical) from CHARTSLECTOR/lib/ind.py (sma/ema/Pine rma/atr) + systems/screens.py (qullamaggie_nofloat) + systems/map_vmr_ram.py (VMR sub-scores).
Parity with the research code is asserted by CHARTSLECTOR/ship/sleeve_cl/tests/test_cl_sleeve.py."""
import numpy as np, pandas as pd
def _df(a): return pd.DataFrame(a.T)
def sma(a, n): return _df(a).rolling(n, min_periods=n).mean().values.T.astype(np.float32)
def ema(a, n): return _df(a).ewm(span=n, adjust=False, min_periods=n).mean().values.T.astype(np.float32)
def lag(a, k=1):
    out = np.full(a.shape, np.nan, np.float32); out[:, k:] = a[:, :-k]; return out
def rma(a, n):
    """Pine ta.rma: SMA seed over the first n consecutive valid bars, then alpha 1/n; a NaN breaks the chain and re-seeds."""
    S, T = a.shape; out = np.full((S, T), np.nan, np.float32); al = 1.0 / n
    prev = np.full(S, np.nan); run = np.zeros(S, int); acc = np.zeros(S)
    for t in range(T):
        x = a[:, t].astype(np.float64); bad = np.isnan(x)
        seeding = np.isnan(prev) & ~bad
        run = np.where(bad, 0, np.where(seeding, run + 1, run)); acc = np.where(bad, 0.0, np.where(seeding, acc + np.nan_to_num(x), acc))
        if t >= n:
            old = a[:, t - n].astype(np.float64); acc = np.where(seeding & (run > n), acc - np.nan_to_num(old), acc)
        newseed = seeding & (run >= n); ema_ = ~np.isnan(prev) & ~bad
        nxt = np.where(newseed, acc / n, np.where(ema_, al * np.nan_to_num(x) + (1 - al) * prev, np.nan))
        nxt = np.where(bad, np.nan, nxt); prev = nxt; out[:, t] = nxt
    return out
def atr(H, L, C, n=14):
    pc = lag(C); tr = np.fmax(H - L, np.fmax(np.abs(H - pc), np.abs(L - pc))).astype(np.float32); return rma(tr, n)
def qullamaggie_nofloat(H, L, C, V):
    """his Qullamaggie TradingView screen without the float filter, conventional stage-2 order (SMA50 >= SMA150)."""
    sma50 = sma(C, 50); sma150 = sma(C, 150); e10 = ema(C, 10); e20 = ema(C, 20); av60 = sma(V, 60); adr14 = (sma(H / L, 14) - 1) * 100
    with np.errstate(invalid="ignore"):
        return (adr14 >= 4) & (e10 >= e20) & (e20 >= sma50) & (av60 > 3e5) & (C >= e20) & (C >= 1) & (sma50 >= sma150)
def newin(b): return b & ~np.concatenate([np.zeros((b.shape[0], 1), bool), b[:, :-1]], axis=1)
def score_vix(x):
    s = np.select([x < 13, x < 17, x < 20, x < 25, x < 32], [100.0, 100 - (x - 13) * 15 / 4, 85 - (x - 17) * 15 / 3, 70 - (x - 20) * 10 / 5, 60 - (x - 25) * 40 / 7],
                  20 - np.minimum(20, (x - 32) * 2.5)); return np.where(np.isnan(x), np.nan, np.clip(s, 0, 100))
def score_term(r):
    s = np.select([r < 0.85, r < 0.95, r < 1.0], [80 + np.minimum(20, (0.85 - r) * 100), 80 - (r - 0.85) * 22 / 0.10, 58 - (r - 0.95) * 28 / 0.05], 30 - np.minimum(30, (r - 1) * 300))
    return np.where(np.isnan(r), np.nan, np.clip(s, 0, 100))
def score_vvix(x):
    s = np.select([x < 85, x < 100, x < 115, x < 130], [100.0, 90 - (x - 85) * 20 / 15, 70 - (x - 100) * 15 / 15, 55 - (x - 115) * 20 / 15], 35 - np.minimum(35, (x - 130) * 2))
    return np.where(np.isnan(x), np.nan, np.clip(s, 0, 100))
def score_skew(x):
    s = np.select([x < 115, x < 130, x < 145], [100.0, 82 - (x - 115) * 16 / 15, 66 - (x - 130) * 25 / 15], 41 - np.minimum(41, (x - 145) * 2))
    return np.where(np.isnan(x), np.nan, np.clip(s, 0, 100))
def vmr_composite(vix, vix3m, vvix, skew):
    """his VIX Mood Ring composite (Market Action Pulse & VIX Mood Ring @196f302): 0.35 VIX + 0.25 term + 0.25 SKEW + 0.15 VVIX."""
    vix, vix3m, vvix, skew = (np.asarray(v, float) for v in (vix, vix3m, vvix, skew))
    return 0.35 * score_vix(vix) + 0.25 * score_term(vix / vix3m) + 0.25 * score_skew(skew) + 0.15 * score_vvix(vvix)
