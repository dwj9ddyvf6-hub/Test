"""Daily-bar engines for the Milkman v2 study (numba). All signals at close t use bars <= t."""
import numpy as np, pandas as pd, numba as nb
from mlib import *
# ------------------------------------------------------------------ data sets
IDX_SYMS = ["SPY", "QQQ", "IWM", "DIA", "ES_F", "NQ_F", "RTY_F", "YM_F", "XLK", "XLF", "XLE", "SMH", "TLT", "GLD"]
def load_universe():
    U = pd.read_parquet(f"{CA}/univ_d.parquet"); out = {}
    for s, g in U.groupby("sym", sort=False):
        g = g.sort_values("date")
        if len(g) < 260: continue
        out[s] = dict(date=g.date.values, o=g.o.values.astype(float), h=g.h.values.astype(float), l=g.l.values.astype(float), c=g.c.values.astype(float), v=g.v.values.astype(float), kind="stock")
    return out
def load_index():
    out = {}
    for s in IDX_SYMS:
        g = pd.read_parquet(f"{CA}/y_{s}.parquet").dropna(subset=["o", "h", "l", "c"]); g = g[(g.o > 0) & (g.h >= g.l)].sort_values("date")
        out[s] = dict(date=g.date.values, o=g.o.values.astype(float), h=g.h.values.astype(float), l=g.l.values.astype(float), c=g.c.values.astype(float), v=g.v.values.astype(float), kind="fut" if s.endswith("_F") else "etf")
    return out
def cost_of(d, px):
    if d["kind"] == "fut": return np.full(len(px), 0.01)
    if d["kind"] == "etf": return np.full(len(px), 0.02)
    return cost_side(px)
def liq_gate(d):
    if d["kind"] != "stock": return np.ones(len(d["c"]), bool)
    dv = pd.Series(d["c"] * d["v"]).rolling(20, min_periods=20).mean().values
    return (dv >= 5e6) & (d["c"] >= 3)
# ------------------------------------------------------------------ engines
@nb.njit(cache=True)
def eng_d7(c, ent, N, side, cap):
    """enter at close ent; exit at first close that is the N-day closing high (long) / low (short). returns exit idx, exit px (nan if unclosed)."""
    n = len(c); m = len(ent); xi = np.full(m, -1); xp = np.full(m, np.nan)
    for k in range(m):
        i = ent[k]
        for j in range(i + 1, min(n, i + cap + 1)):
            lo = max(0, j - N + 1); ok = True
            for q in range(lo, j):
                if side > 0 and c[q] > c[j]: ok = False; break
                if side < 0 and c[q] < c[j]: ok = False; break
            if ok or j == i + cap: xi[k] = j; xp[k] = c[j]; break
    return xi, xp
@nb.njit(cache=True)
def eng_hold(o, c, ent, H, mode):
    """mode 0: close[i] -> close[i+H]; 1: open[i+1] -> close[i+H]; 2: close[i] -> open[i+1]; 3: open[i] -> close[i]."""
    n = len(c); m = len(ent); ep = np.full(m, np.nan); xp = np.full(m, np.nan); xi = np.full(m, -1)
    for k in range(m):
        i = ent[k]
        if mode == 0 and i + H < n: ep[k] = c[i]; xp[k] = c[i + H]; xi[k] = i + H
        elif mode == 1 and i + H < n and i + 1 < n: ep[k] = o[i + 1]; xp[k] = c[i + H]; xi[k] = i + H
        elif mode == 2 and i + 1 < n: ep[k] = c[i]; xp[k] = o[i + 1]; xi[k] = i + 1
        elif mode == 3: ep[k] = o[i]; xp[k] = c[i]; xi[k] = i
    return ep, xp, xi
@nb.njit(cache=True)
def eng_trail(o, h, l, c, e50, ent, ep, stop0, side, trail, boxedge, cap):
    """stop-entry trades filled on bar ent at price ep with initial stop stop0. trail: 0 = ratchet to prior-bar EMA (e50 array),
    1 = same + scratch if close back inside box (boxedge) within 3 bars, 2 = fixed time exit at cap (stop stays)."""
    n = len(c); m = len(ent); xp = np.full(m, np.nan); xi = np.full(m, -1)
    for k in range(m):
        i = ent[k]; st = stop0[k]
        # entry bar: stopped only if the close is through the stop (conservative intrabar order unknown)
        if (side > 0 and c[i] <= st) or (side < 0 and c[i] >= st): xp[k] = st if ((side > 0 and l[i] <= st) or (side < 0 and h[i] >= st)) else c[i]; xi[k] = i; continue
        for j in range(i + 1, min(n, i + cap + 1)):
            if trail != 2 and np.isfinite(e50[j - 1]):
                if side > 0 and e50[j - 1] > st: st = e50[j - 1]
                if side < 0 and e50[j - 1] < st: st = e50[j - 1]
            if side > 0 and l[j] <= st: xp[k] = min(o[j], st); xi[k] = j; break
            if side < 0 and h[j] >= st: xp[k] = max(o[j], st); xi[k] = j; break
            if trail == 1 and j - i <= 3 and ((side > 0 and c[j] < boxedge[k]) or (side < 0 and c[j] > boxedge[k])): xp[k] = c[j]; xi[k] = j; break
            if j == i + cap: xp[k] = c[j]; xi[k] = j; break
    return xi, xp
@nb.njit(cache=True)
def eng_bracket(o, h, l, c, ent, ep, tgt, stp, last, side, entry_day_mode):
    """bracket from entry bar ent at ep; exits at target/stop/close of bar last[k]. Same bar target & stop -> stop (conservative).
    entry bar: target counts if reached (move continued through the stop-entry); stop counts only if the close is through it."""
    m = len(ent); xp = np.full(m, np.nan); xi = np.full(m, -1)
    for k in range(m):
        i = ent[k]; T = tgt[k]; S = stp[k]
        if entry_day_mode == 1:
            if side > 0:
                if h[i] >= T: xp[k] = T; xi[k] = i; continue
                if c[i] <= S: xp[k] = c[i]; xi[k] = i; continue
            else:
                if l[i] <= T: xp[k] = T; xi[k] = i; continue
                if c[i] >= S: xp[k] = c[i]; xi[k] = i; continue
        start = i + 1 if entry_day_mode >= 1 else i
        for j in range(start, last[k] + 1):
            if side > 0:
                if l[j] <= S: xp[k] = min(o[j], S) if j > i else S; xi[k] = j; break
                if h[j] >= T: xp[k] = max(o[j], T) if j > i else T; xi[k] = j; break
            else:
                if h[j] >= S: xp[k] = max(o[j], S) if j > i else S; xi[k] = j; break
                if l[j] <= T: xp[k] = min(o[j], T) if j > i else T; xi[k] = j; break
            if j == last[k]: xp[k] = c[j]; xi[k] = j; break
    return xi, xp
@nb.njit(cache=True)
def eng_touch(o, h, l, c, lvl, ent, side, H):
    """enter at close ent; exit when price touches the prior-bar level lvl[j-1] (mean), else close at ent+H."""
    n = len(c); m = len(ent); xp = np.full(m, np.nan); xi = np.full(m, -1)
    for k in range(m):
        i = ent[k]
        for j in range(i + 1, min(n, i + H + 1)):
            L = lvl[j - 1]
            if side > 0 and h[j] >= L: xp[k] = max(o[j], L); xi[k] = j; break
            if side < 0 and l[j] <= L: xp[k] = min(o[j], L); xi[k] = j; break
            if j == i + H: xp[k] = c[j]; xi[k] = j; break
    return xi, xp
@nb.njit(cache=True)
def eng_signal_exit(c, ent, exitmask, cap):
    n = len(c); m = len(ent); xp = np.full(m, np.nan); xi = np.full(m, -1)
    for k in range(m):
        i = ent[k]
        for j in range(i + 1, min(n, i + cap + 1)):
            if exitmask[j] or j == i + cap: xp[k] = c[j]; xi[k] = j; break
    return xi, xp
def nonoverlap(ent, xi):
    keep = np.zeros(len(ent), bool); busy = -1
    for k in np.argsort(ent, kind="stable"):
        if ent[k] > busy and xi[k] >= 0: keep[k] = True; busy = xi[k]
    return keep
def rand_same_year(dates, gate_idx, ent, R, rng):
    """for each entry, R random indices from gate_idx in the same calendar year (fallback: any gated index)."""
    if len(gate_idx) == 0: return np.full((len(ent), R), -1)
    yr = pd.DatetimeIndex(dates).year.values; gy = yr[gate_idx]; out = np.empty((len(ent), R), np.int64)
    for k, i in enumerate(ent):
        pool = gate_idx[gy == yr[i]]
        if len(pool) < 5: pool = gate_idx
        out[k] = pool[rng.integers(0, len(pool), R)]
    return out
