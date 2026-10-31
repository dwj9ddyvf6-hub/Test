"""S10: his single-chart Pine tools, translated to panel form (S x T float32). Faithful to the published scripts; quirks kept with a flag.
rs1m        1-Month RS (close/SPY ratio, rank of today's ratio in the last 26 bars = indexof(sorted) = count strictly lower, /(N-1)*100), alerts: >50 streak>=15, >=12 of prior 15 bars >50
stage       Candle Stage Analysis (11 stages, ATR-percent-normalised xATR default)
gaps        Unfilled Close-Adjusted Gaps: new gap up (low>prev close) / down; removal when a later close crosses the far edge; active count
crsi        Calibrated RSI Position Zones: logit-RSI z vs fast centre, tail-confirmed re-entries, strong continuation
emgmr       EM Gaussian Mixture Regime oscillator (3 comps, online EM with memory 100); as_written keeps the init batch sums un-reset across EM iterations, corrected resets
lod         LoD Intraday Entry eligibility (close <= LoD + 65% ATR and stop distance < 1 ATR; stop = LoD - 0.1 ATR) + RPRP sizing (as_written /2 vs corrected)"""
import numpy as np, pandas as pd, numba as nb, sys
sys.path.insert(0, "[LOCAL_PATH_NOT_INCLUDED]")
import ind as I
from numpy.lib.stride_tricks import sliding_window_view as swv
def rs1m(C, spy, N=26, alert_len=15, least=12):
    r = (C / spy[None, :]).astype(np.float64); S, T = r.shape; pct = np.full((S, T), np.nan, np.float32)
    w = swv(r, N, axis=1)                      # S x (T-N+1) x N, last element = current
    cur = w[..., -1]; ok = np.isfinite(w).all(-1)
    rank = (w < cur[..., None]).sum(-1)        # array.indexof(sorted, current) = number of strictly smaller values
    pct[:, N - 1:] = np.where(ok, rank / (N - 1) * 100, np.nan)
    a50 = np.nan_to_num(pct, nan=0) > 50
    streak = I.consec(a50); cnt = I.rsum(I.lag(a50.astype(np.float32), 1), 15, mp=15)
    return pct, streak >= alert_len, cnt >= least
def stage(O, H, L, C, mode="pctnorm"):
    e5 = I.ema(C, 5); e10 = I.ema(C, 10); e20 = I.ema(C, 20); s50 = I.sma(C, 50); atr = I.atr(H, L, C, 14)
    atrx = ((C - s50) / s50) / (atr / C) if mode == "pctnorm" else (C - s50) / atr     # note: pct-normalised == raw*(C/s50)
    spread = np.fmax(np.fmax(e10, e20), s50) - np.fmin(np.fmin(e10, e20), s50)
    e10up = e10 >= I.lag(e10)
    up = (C >= e10) & (e10 >= e20) & (e20 >= s50); dn = (C < e20) & (e10 < e20) & (e20 < s50)
    bo = C >= I.lag(I.rmax(H, 20)); bd = C < I.lag(I.rmin(L, 20))
    basing = (np.abs(C - s50) < atr) & (spread < 1.5 * atr); bb50 = (C > e20) & (C < s50) & (e20 > e10) & (e20 < s50)
    extB = up & (atrx >= 7) & (atrx < 11); exhB = up & (atrx >= 11); extBear = dn & (atrx < -7)
    fadeA = (C >= s50) & (e10 >= e20) & ((C < e10) | ~e10up); fadeB = ~extBear & (C >= s50) & (e10 < e20)
    mr = ~up & ~dn & ~(basing | bb50) & (C > e20) & (e10 >= e20)
    st = np.select([exhB, extB, extBear, fadeA, fadeB, up & bo, up, dn & bd, dn, basing | bb50, mr],
                   [6, 5, 11, 7, 8, 4, 3, 10, 9, 1, 2], 12).astype(np.int8)
    st[~np.isfinite(s50) | ~np.isfinite(atr)] = 0
    return st          # 1 1A,2 1B,3 2A,4 2B,5 2C,6 2D,7 3A,8 3B,9 4A,10 4B,11 4C,12 NA
STAGE_NAMES = {1: "1A", 2: "1B", 3: "2A", 4: "2B", 5: "2C", 6: "2D", 7: "3A", 8: "3B", 9: "4A", 10: "4B", 11: "4C", 12: "NA"}
@nb.njit(cache=True)
def _gaps(H, L, C, lookback, maxg):
    S, T = C.shape; nup = np.zeros((S, T), np.int16); ndn = np.zeros((S, T), np.int16); fill_up = np.zeros((S, T), np.bool_); fill_dn = np.zeros((S, T), np.bool_)
    for s in range(S):
        lo = np.empty(maxg + 2); hi = np.empty(maxg + 2); st = np.empty(maxg + 2, np.int64); dr = np.empty(maxg + 2, np.int64); n = 0
        for t in range(1, T):
            pc = C[s, t - 1]; c = C[s, t]
            if not (np.isfinite(pc) and np.isfinite(c)): continue
            if L[s, t] > pc: lo[n] = pc; hi[n] = L[s, t]; st[n] = t; dr[n] = 1; n += 1          # Pine: always push, trim oldest after the loop
            if H[s, t] < pc: lo[n] = H[s, t]; hi[n] = pc; st[n] = t; dr[n] = -1; n += 1
            i = n - 1
            while i >= 0:
                fut = t > st[i]; old = t - st[i] > lookback
                rem_u = dr[i] == 1 and fut and c < lo[i]; rem_d = dr[i] == -1 and fut and c > hi[i]
                if old or rem_u or rem_d:
                    if rem_u: fill_up[s, t] = True
                    if rem_d: fill_dn[s, t] = True
                    for j in range(i, n - 1): lo[j] = lo[j + 1]; hi[j] = hi[j + 1]; st[j] = st[j + 1]; dr[j] = dr[j + 1]
                    n -= 1
                i -= 1
            while n > maxg:                                   # Pine: while array.size > maxGaps -> f_delete_gap(0)
                for j in range(n - 1): lo[j] = lo[j + 1]; hi[j] = hi[j + 1]; st[j] = st[j + 1]; dr[j] = dr[j + 1]
                n -= 1
            cu = 0; cd = 0
            for j in range(n):
                if dr[j] == 1: cu += 1
                else: cd += 1
            nup[s, t] = cu; ndn[s, t] = cd
    return nup, ndn, fill_up, fill_dn
def gaps(H, L, C, lookback=80, maxg=100):
    pc = I.lag(C); gu = L > pc; gd = H < pc
    nup, ndn, fu, fd = _gaps(H.astype(np.float64), L.astype(np.float64), C.astype(np.float64), lookback, maxg)
    return dict(gap_up=gu, gap_dn=gd, n_up=nup, n_dn=ndn, upgap_closed=fu, dngap_closed=fd)
def _rsi(C, n=14):
    d = np.diff(C, axis=1, prepend=np.nan); up = I.rma(np.where(d > 0, d, 0).astype(np.float32) * np.where(np.isfinite(d), 1, np.nan), n)
    dn = I.rma(np.where(d < 0, -d, 0).astype(np.float32) * np.where(np.isfinite(d), 1, np.nan), n)
    return np.where(dn == 0, 100, np.where(up == 0, 0, 100 - 100 / (1 + up / dn))).astype(np.float32)
def _prank(x, n):
    """ta.percentrank: % of the previous n values <= current."""
    S, T = x.shape; out = np.full((S, T), np.nan, np.float32); w = swv(x, n + 1, axis=1); cur = w[..., -1:]; prev = w[..., :-1]
    out[:, n:] = np.where(np.isfinite(prev).all(-1) & np.isfinite(cur[..., 0]), (prev <= cur).sum(-1) / n * 100, np.nan); return out
def _linreg_slope(x, n):
    k = np.arange(n) - (n - 1) / 2; w = swv(x, n, axis=1); out = np.full(x.shape, np.nan, np.float32); out[:, n - 1:] = (w * k).sum(-1) / (k * k).sum(); return out
def crsi(H, L, C):
    r = _rsi(C, 14); p = np.clip(r / 100, .001, .999); lg = I.ema(np.log(p / (1 - p)).astype(np.float32), 3)
    muF = I.ema(lg, 42); muS = I.ema(lg, 126); fr = lg - muF; sF = np.sqrt(np.fmax(I.ema(fr * fr, 63), 1e-6)); z = fr / sF
    zs = I.ema(z, 3); zr = _prank(z, 126); sr = lg - muS; sS = np.sqrt(np.fmax(I.ema(sr * sr, 126), 1e-6)); regZ = (muF - muS) / sS
    cs = I.ema(_linreg_slope(muF, 10) * 9 / sS, 3)
    te = I.ema(C, 200); ts = te - I.lag(te, 10); trend = np.where((C > te) & (ts > 0), 1, np.where((C < te) & (ts < 0), -1, 0))
    zl = I.lag(z); lre = (z > -2) & (zl <= -2) & (I.lag(zr) <= 10) & (zs > I.lag(zs)); sre = (z < 2) & (zl >= 2) & (I.lag(zr) >= 90) & (zs < I.lag(zs))
    return dict(z=z, long_re=lre, short_re=sre, strong_long=lre & (trend == 1) & (regZ > .1) & (cs > .05), strong_short=sre & (trend == -1) & (regZ < -.1) & (cs < -.05),
                oversold=z < -2, overbought=z > 2)
@nb.njit(cache=True)
def _logdens(x, w, m, v, k):
    md = 0.0; ld = 0.0
    for d in range(3): vv = max(v[k, d], 0.05); md += (x[d] - m[k, d]) ** 2 / vv; ld += np.log(vv)
    return np.log(max(w[k], 1e-10)) - 0.5 * (3 * np.log(2 * np.pi) + ld + md)
@nb.njit(cache=True)
def _resp(x, w, m, v, K, out):
    lp = np.empty(K); mx = -1e30
    for k in range(K): lp[k] = _logdens(x, w, m, v, k); mx = max(mx, lp[k])
    s = 0.0
    for k in range(K): out[k] = np.exp(lp[k] - mx); s += out[k]
    s = max(s, 1e-10)
    for k in range(K): out[k] /= s
    return mx + np.log(s)
@nb.njit(cache=True)
def _emgmr_one(F, ready, K, mem, initN, iters, tol, vfloor, minw, reset):
    T = F.shape[0]; score = np.full(T, np.nan); seed = np.empty((T, 3)); ns = 0; init = False
    w = np.full(K, 1.0 / K); m = np.zeros((K, 3)); v = np.ones((K, 3)); cnt = np.zeros(K); sm = np.zeros((K, 3)); sq = np.zeros((K, 3)); r = np.zeros(K)
    for t in range(T):
        if not ready[t]: continue
        just = False
        if not init:
            seed[ns] = F[t]; ns += 1
            if ns >= initN:
                g = np.zeros(3); gv = np.zeros(3)
                for i in range(ns): g += seed[i]
                g /= ns
                for i in range(ns): gv += (seed[i] - g) ** 2
                for d in range(3): gv[d] = max(gv[d] / ns, vfloor)
                order = np.argsort(seed[:ns, 0], kind="mergesort")
                for k in range(K):
                    pos = int(np.round((k + 0.5) / K * (ns - 1))); pos = max(0, min(ns - 1, pos)); m[k] = seed[order[pos]]; v[k] = gv; w[k] = 1.0 / K
                bc = np.zeros(K); bs = np.zeros((K, 3)); bq = np.zeros((K, 3)); prev = np.nan; rr = np.zeros(K)
                for it in range(iters):
                    if reset: bc[:] = 0; bs[:] = 0; bq[:] = 0
                    tot = 0.0
                    for i in range(ns):
                        tot += _resp(seed[i], w, m, v, K, rr)
                        for k in range(K): bc[k] += rr[k]; bs[k] += rr[k] * seed[i]; bq[k] += rr[k] * seed[i] ** 2
                    ws = 0.0
                    for k in range(K):
                        if bc[k] > 1e-10:
                            mu = bs[k] / bc[k]; m[k] = mu
                            for d in range(3): v[k, d] = max(bq[k, d] / bc[k] - mu[d] ** 2, vfloor)
                        else:
                            pos = int(np.round((k + 0.5) / K * (ns - 1))); m[k] = seed[order[pos]]; v[k] = gv
                        w[k] = max(bc[k] / ns, minw); ws += w[k]
                    w /= max(ws, 1e-10)
                    if np.isfinite(prev) and abs(tot - prev) / (1 + abs(prev)) <= tol: break
                    prev = tot
                for k in range(K):
                    pc = max(w[k] * mem, 1e-10); cnt[k] = pc; sm[k] = pc * m[k]; sq[k] = pc * (v[k] + m[k] ** 2)
                init = True; just = True
        if init:
            _resp(F[t], w, m, v, K, r)
            if not just:
                dec = np.exp(-1.0 / mem)
                for k in range(K): cnt[k] = dec * cnt[k] + r[k]; sm[k] = dec * sm[k] + r[k] * F[t]; sq[k] = dec * sq[k] + r[k] * F[t] ** 2
                te = cnt.sum(); ws = 0.0
                for k in range(K):
                    c = max(cnt[k], 1e-10); mu = sm[k] / c; m[k] = mu
                    for d in range(3): v[k, d] = max(sq[k, d] / c - mu[d] ** 2, vfloor)
                    w[k] = max(c / max(te, 1e-10), minw); ws += w[k]
                w /= max(ws, 1e-10); _resp(F[t], w, m, v, K, r)
            eo = 0.0
            for k in range(K):
                rank = 0
                for o in range(K):
                    if m[o, 0] < m[k, 0] or (m[o, 0] == m[k, 0] and o < k): rank += 1
                eo += r[k] * (2.0 * rank / max(K - 1, 1) - 1.0)
            score[t] = eo * 100
    return score
def emgmr(C, V, variant="as_written", K=3, mem=100):
    C64 = C.astype(np.float64); lr = np.log(C64 / I.lag(C64)); mom = np.log(C64 / I.lag(C64, 14))
    sv = pd.DataFrame(lr.T).rolling(20, min_periods=20).std().values.T; lv = pd.DataFrame(lr.T).rolling(mem, min_periods=mem).std().values.T   # ta.stdev = population sd
    sv = pd.DataFrame(lr.T).rolling(20, min_periods=20).std(ddof=0).values.T; lv = pd.DataFrame(lr.T).rolling(mem, min_periods=mem).std(ddof=0).values.T
    den = np.fmax(np.nan_to_num(lv), 1e-10); f1 = np.clip(mom / (den * np.sqrt(14)), -6, 6); f2 = np.clip(np.log(np.fmax(np.nan_to_num(sv), 1e-10) / den), -6, 6)
    va = pd.DataFrame(V.T.astype(np.float64)).rolling(50, min_periods=50).mean().values.T
    f3 = np.where(~np.isfinite(V) | ~np.isfinite(va) | (va <= 0), 0.0, np.log(np.fmax(np.nan_to_num(V), 1e-10) / np.where(va > 0, va, 1)))
    f3 = np.clip(f3, -6, 6); ready = np.isfinite(f1) & np.isfinite(f2) & np.isfinite(lv) & (lv > 1e-10)
    S, T = C.shape; out = np.full((S, T), np.nan, np.float32)
    for s in range(S):
        F = np.stack([f1[s], f2[s], f3[s]], 1)
        if ready[s].sum() > 80: out[s] = _emgmr_one(np.nan_to_num(F), ready[s], K, mem, max(75, K * 10), 15, 1e-4, 0.05, 0.01, variant == "corrected")
    return I.ema(np.where(np.isfinite(out), out, np.nan).astype(np.float32), 3)  # note: ta.ema over na-gaps differs slightly; warm-up only
def lod_daily(H, L, C, atr_prev, pct=0.65):
    """daily-bar approximation: buying at the close is eligible when close <= low + pct*ATR(prev day) and close - (low - 0.1 ATR) < ATR."""
    return (C <= L + pct * atr_prev) & ((C - (L - 0.1 * atr_prev)) < atr_prev)
def rprp_shares(price, stop, beta, atrpct, capital=1e5, risk_pct=0.25, base_alloc=15.0, variant="as_written"):
    rvf = 0.5 * beta + 0.5 * atrpct; don = np.where(rvf > 0, base_alloc / rvf, np.nan) / 100 * capital / price
    tharp = capital * risk_pct / 100 / np.abs(price - stop); mx = np.fmax(don, tharp); mn = np.fmin(don, tharp)
    s = 0.35 * mx + 0.65 * mn; return s / 2 if variant == "as_written" else s
