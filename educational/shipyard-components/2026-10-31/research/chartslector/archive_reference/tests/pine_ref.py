"""Literal bar-by-bar transliterations of his Pine scripts (one series at a time, Pine semantics: na handling, var state, history refs).
Used only as an independent reference to check the vectorised panel versions in systems/."""
import math, numpy as np
nan = float("nan")
def isna(x): return x is None or (isinstance(x, float) and math.isnan(x))
def ta_ema(src, n):
    a = 2 / (n + 1); out = []; s = nan
    for x in src:
        s = x if isna(s) else a * x + (1 - a) * s; out.append(s)
    return np.array(out)
def ta_sma(src, n):
    out = []
    for i in range(len(src)):
        w = src[max(0, i - n + 1):i + 1]; out.append(nan if i < n - 1 or any(isna(v) for v in w) else sum(w) / n)
    return np.array(out)
def ta_rma(src, n):
    a = 1 / n; out = []; s = nan; sm = ta_sma(src, n)
    for i, x in enumerate(src):
        s = sm[i] if isna(s) else a * x + (1 - a) * s; out.append(s)
    return np.array(out)
def ta_tr(h, l, c):
    return np.array([h[i] - l[i] if i == 0 else max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])) for i in range(len(c))])
def ta_atr(h, l, c, n=14): return ta_rma(ta_tr(h, l, c), n)
def rs1m(close, ref, lookback=26):
    arr = []; out = []
    for c, r in zip(close, ref):
        arr.append(c / r)
        if len(arr) > lookback: arr.pop(0)
        if len(arr) == lookback:
            srt = sorted(arr); rank = srt.index(arr[-1]); out.append(rank / (lookback - 1) * 100)
        else: out.append(nan)
    return np.array(out)
def stage(o, h, l, c):
    n = len(c); e10 = ta_ema(c, 10); e20 = ta_ema(c, 20); s50 = ta_sma(c, 50); atr = ta_atr(h, l, c, 14); out = []
    for i in range(n):
        if i < 50 or isna(s50[i]) or isna(atr[i]): out.append(0); continue
        atrx = ((c[i] - s50[i]) / s50[i]) / (atr[i] / c[i])
        spread = max(e10[i], e20[i], s50[i]) - min(e10[i], e20[i], s50[i])
        e10up = e10[i] >= e10[i - 1]
        up = c[i] >= e10[i] >= e20[i] >= s50[i]
        dn = c[i] < e20[i] and e10[i] < e20[i] and e20[i] < s50[i]
        bo = c[i] >= max(h[i - 20:i]); bd = c[i] < min(l[i - 20:i])
        basing = abs(c[i] - s50[i]) < atr[i] and spread < 1.5 * atr[i]
        bb50 = c[i] > e20[i] and c[i] < s50[i] and e20[i] > e10[i] and e20[i] < s50[i]
        extB = up and 7 <= atrx < 11; exhB = up and atrx >= 11; extBear = dn and atrx < -7
        fadeA = c[i] >= s50[i] and e10[i] >= e20[i] and (c[i] < e10[i] or not e10up)
        fadeB = (not extBear) and c[i] >= s50[i] and e10[i] < e20[i]
        mr = (not up) and (not dn) and not (basing or bb50) and c[i] > e20[i] and e10[i] >= e20[i]
        if exhB: st = 6
        elif extB: st = 5
        elif extBear: st = 11
        elif fadeA: st = 7
        elif fadeB: st = 8
        elif up: st = 4 if bo else 3
        elif dn: st = 10 if bd else 9
        elif basing or bb50: st = 1
        elif mr: st = 2
        else: st = 12
        out.append(st)
    return np.array(out)
def percentrank(src, n):
    out = []
    for i in range(len(src)):
        if i < n or any(isna(v) for v in src[i - n:i + 1]): out.append(nan); continue
        out.append(sum(1 for v in src[i - n:i] if v <= src[i]) / n * 100)
    return np.array(out)
def crsi_z(c):
    d = np.r_[nan, np.diff(c)]; up = ta_rma(np.where(d > 0, d, 0.0) * np.where(np.isnan(d), nan, 1), 14); dn = ta_rma(np.where(d < 0, -d, 0.0) * np.where(np.isnan(d), nan, 1), 14)
    rsi = np.array([100 if b == 0 else (0 if a == 0 else 100 - 100 / (1 + a / b)) if not (isna(a) or isna(b)) else nan for a, b in zip(up, dn)])
    p = np.clip(rsi / 100, .001, .999); lg = np.log(p / (1 - p))
    first = np.where(np.isfinite(lg))[0][0]; sm = np.full(len(c), nan); sm[first:] = ta_ema(lg[first:], 3)
    mu = np.full(len(c), nan); mu[first:] = ta_ema(sm[first:], 42); fr = sm - mu
    var = np.full(len(c), nan); var[first:] = ta_ema(fr[first:] ** 2, 63)
    return fr / np.sqrt(np.maximum(var, 1e-6))
def rrr(c, ref):
    rs = 100 * c / ref
    def ratio(x, s, n): sm = ta_ema(x, s); b = ta_ema(sm, n); return 100 * sm / b
    R = 0.6 * ratio(rs, 15, 21) + 0.4 * ratio(rs, 26, 34); M = 0.6 * ratio(R, 8, 15) + 0.4 * ratio(R, 15, 26)
    ch1 = np.r_[nan, np.diff(R)]; chl = np.r_[[nan] * 5, (R[5:] - R[:-5]) / 5]
    vol = np.array([nan if i < 20 or np.isnan(ch1[i - 19:i + 1]).any() else np.std(ch1[i - 19:i + 1]) for i in range(len(R))])
    z = np.where(vol > 1e-12, (ch1 - chl) / (vol + 1e-12), nan)
    adj = np.where(np.isnan(z), 0.0, 0.10 * (2 / (1 + np.exp(-2 * np.clip(z, -20, 20))) - 1))
    return R, M + adj
def lod_entry(close, lod, atr, pct=0.65, frac=0.1):
    """his LoD script, reference_point = Low: threshold = LoD + pct*ATR; stop = LoD - frac*ATR; eligible = close <= threshold and 0 < close-stop < ATR."""
    thr = lod + pct * atr; stop = lod - frac * atr; risk = close - stop
    return (close <= thr) and (risk > 0) and (risk < atr), stop
def rprp(price, stop, beta, atrpct, capital=100000.0, risk_pct=0.25, base=15.0, sleeve=100.0, halve=True):
    rvf = (50 * beta + 50 * atrpct) / 100; don_pct = base / rvf; don_sh = capital * sleeve / 100 * don_pct / 100 / price
    tharp = capital * risk_pct / 100 / abs(price - stop); s = 0.35 * max(don_sh, tharp) + 0.65 * min(don_sh, tharp)
    return s / 2 if halve else s
def gaps_counts(H, L, C, lookback=80, maxg=100):
    """literal port of 'Unfilled Close-Adjusted Gaps' array logic (boxes/lines dropped): active gap-up / gap-down counts per bar."""
    gl, gu, gs, gd = [], [], [], []; nu = []; nd = []
    for b in range(len(C)):
        pc = C[b - 1] if b > 0 else float("nan")
        if b > 0 and pc == pc and L[b] > pc: gl.append(pc); gu.append(L[b]); gs.append(b); gd.append(1)
        if b > 0 and pc == pc and H[b] < pc: gl.append(H[b]); gu.append(pc); gs.append(b); gd.append(-1)
        i = len(gl) - 1
        while i >= 0:
            fut = b > gs[i]; old = b - gs[i] > lookback
            if old or (gd[i] == 1 and fut and C[b] < gl[i]) or (gd[i] == -1 and fut and C[b] > gu[i]):
                for a in (gl, gu, gs, gd): a.pop(i)
            i -= 1
        while len(gl) > maxg:
            for a in (gl, gu, gs, gd): a.pop(0)
        nu.append(sum(1 for d in gd if d == 1)); nd.append(sum(1 for d in gd if d == -1))
    return nu, nd
