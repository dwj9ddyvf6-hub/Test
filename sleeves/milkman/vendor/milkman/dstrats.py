"""Daily strategy definitions (Milkman v2). Each returns dict(ent, xi, ep, xp, side, gate, rsim) where rsim(rand_idx[k, r]) -> (ep, xp)
of the SAME exit engine run from random entry bars with the trade's own parameters (risk-matched random baseline)."""
import numpy as np, pandas as pd
from dlib import *
def _cache(d):
    if "_c" not in d:
        o, h, l, c = d["o"], d["h"], d["l"], d["c"]; a = atr(h, l, c, 14)
        d["_c"] = dict(a=a, e8=ema(c, 8), e13=ema(c, 13), e20=ema(c, 20), e21=ema(c, 21), e48=ema(c, 48), e50=ema(c, 50), s100=sma(c, 100), s200=sma(c, 200),
                       po=po(c, h, l), comp=compression(c, h, l), liq=liq_gate(d), dates=pd.DatetimeIndex(d["date"]))
    return d["_c"]
def _pack(ent, xi, ep, xp, side, gate, rsim):
    return dict(ent=np.asarray(ent, np.int64), xi=np.asarray(xi, np.int64), ep=np.asarray(ep, float), xp=np.asarray(xp, float), side=side, gate=np.asarray(gate, np.int64), rsim=rsim)
# ---------------------------------------------------------------- 1. Connors Double 7
def double7(d, side=1, N=7, ma=200, cap=60):
    C = _cache(d); c = d["c"]; n = len(c); s = C["s200"] if ma == 200 else C["s100"]
    rmin = pd.Series(c).rolling(N, min_periods=N).min().values; rmax = pd.Series(c).rolling(N, min_periods=N).max().values
    trend = (c > s) if side > 0 else (c < s)
    sig = trend & ((c <= rmin) if side > 0 else (c >= rmax)) & C["liq"]; sig[:max(ma, N)] = False
    ent = np.flatnonzero(sig); xi, xp = eng_d7(c, ent, N, side, cap); keep = nonoverlap(ent, xi); ent, xi, xp = ent[keep], xi[keep], xp[keep]
    gate = np.flatnonzero(trend & C["liq"] & (np.arange(n) >= max(ma, N)))
    def rsim(R):
        f = R.ravel(); x2, p2 = eng_d7(c, f, N, side, cap); return c[f].reshape(R.shape), p2.reshape(R.shape)
    return _pack(ent, xi, c[ent], xp, side, gate, rsim)
# ---------------------------------------------------------------- 2. Legend's Buy Day (overnight after k lower closes)
def buyday(d, side=1, k=3, exact=True):
    C = _cache(d); o, c = d["o"], d["c"]; n = len(c)
    dn = np.r_[False, c[1:] < c[:-1]] if side > 0 else np.r_[False, c[1:] > c[:-1]]
    run = np.zeros(n, int)
    for i in range(1, n): run[i] = run[i - 1] + 1 if dn[i] else 0
    sig = ((run == k) if exact else (run >= k)) & C["liq"]; sig[-1] = False
    ent = np.flatnonzero(sig); ep, xp, xi = eng_hold(o, c, ent, 0, 2)
    gate = np.flatnonzero(C["liq"][:-1])
    def rsim(R):
        f = R.ravel(); e2, p2, _ = eng_hold(o, c, f, 0, 2); return e2.reshape(R.shape), p2.reshape(R.shape)
    return _pack(ent, xi, ep, xp, side, gate, rsim)
# ---------------------------------------------------------------- 3. Day-of-week open->close (ES Monday)
def weekday(d, side=1, dow=0):
    C = _cache(d); o, c = d["o"], d["c"]; wd = C["dates"].weekday.values
    sig = (wd == dow) & C["liq"]; ent = np.flatnonzero(sig); ep, xp, xi = eng_hold(o, c, ent, 0, 3)
    gate = np.flatnonzero(C["liq"])
    def rsim(R):
        f = R.ravel(); e2, p2, _ = eng_hold(o, c, f, 0, 3); return e2.reshape(R.shape), p2.reshape(R.shape)
    return _pack(ent, xi, ep, xp, side, gate, rsim)
# ---------------------------------------------------------------- 4. Daily Bilbo Box
def bilbo_daily(d, side=1, boxlen=5, window=20, exitm="ema50", cap=250):
    C = _cache(d); o, h, l, c = d["o"], d["h"], d["l"], d["c"]; n = len(c); comp = C["comp"]; e21 = C["e21"]
    trail_arr = C["e50"] if exitm in ("ema50", "scr3") else (C["e20"] if exitm == "ema20" else C["e50"])
    trail = {"ema50": 0, "ema20": 0, "scr3": 1, "h20": 2, "h60": 2}[exitm]; capx = {"h20": 20, "h60": 60}.get(exitm, cap)
    ents, eps, stops, edges = [], [], [], []
    i = 1
    while i < n:
        if comp[i] == 1 and comp[i - 1] == 0:
            j = i; bh_, bl_ = h[i], l[i]; cnt = 1
            while j + 1 < n and comp[j + 1] == 1 and cnt < boxlen: j += 1; cnt += 1; bh_ = max(bh_, h[j]); bl_ = min(bl_, l[j])
            lock = j   # box locks at close of bar j (5th compression bar or end of squeeze)
            for t in range(lock + 1, min(n, lock + 1 + window)):
                if side > 0:
                    if o[t] <= bl_ or (l[t] <= bl_ and not (o[t] >= bh_)): break   # box low touched first -> void (conservative)
                    if c[t - 1] > e21[t - 1] and h[t] >= bh_ and C["liq"][t - 1]:
                        ents.append(t); eps.append(max(o[t], bh_)); stops.append(bl_); edges.append(bh_); break
                else:
                    if o[t] >= bh_ or (h[t] >= bh_ and not (o[t] <= bl_)): break
                    if c[t - 1] < e21[t - 1] and l[t] <= bl_ and C["liq"][t - 1]:
                        ents.append(t); eps.append(min(o[t], bl_)); stops.append(bh_); edges.append(bl_); break
            # next squeeze episode only after this one ends
            while i < n and comp[i] == 1: i += 1
        i += 1
    ent = np.array(ents, np.int64); ep = np.array(eps); st = np.array(stops); ed = np.array(edges)
    xi, xp = eng_trail(o, h, l, c, trail_arr, ent, ep, st, side, trail, ed, capx); keep = nonoverlap(ent, xi)
    ent, xi, xp, ep, st, ed = ent[keep], xi[keep], xp[keep], ep[keep], st[keep], ed[keep]
    gm = np.r_[False, (c[:-1] > e21[:-1]) if side > 0 else (c[:-1] < e21[:-1])] & np.r_[False, C["liq"][:-1]]; gate = np.flatnonzero(gm)
    risk = np.abs(ep - st) / ep
    def rsim(R):
        f = R.ravel(); rk = np.repeat(risk, R.shape[1]); e2 = o[f]; s2 = e2 * (1 - side * rk)
        x2, p2 = eng_trail(o, h, l, c, trail_arr, f, e2, s2, side, 2 if trail == 2 else 0, e2, capx); return e2.reshape(R.shape), p2.reshape(R.shape)
    return _pack(ent, xi, ep, xp, side, gate, rsim)
# ---------------------------------------------------------------- helpers: higher-timeframe ATR levels on daily bars
def htf_levels(d, freq):
    """prior completed period close (PC) and prior period Wilder ATR14 of that timeframe, mapped onto each daily bar; plus last bar index of the period."""
    C = _cache(d); dt = C["dates"]; df = pd.DataFrame(dict(o=d["o"], h=d["h"], l=d["l"], c=d["c"]), index=dt)
    per = dt.to_period(freq); g = df.groupby(per).agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"))
    A = atr(g.h.values, g.l.values, g.c.values, 14)
    pc = pd.Series(np.r_[np.nan, g.c.values[:-1]], index=g.index); pa = pd.Series(np.r_[np.nan, A[:-1]], index=g.index)
    PC = pc.reindex(per).values; PA = pa.reindex(per).values
    pid = pd.Series(np.arange(len(dt)), index=dt).groupby(per.values).transform("max").values; first = pd.Series(np.arange(len(dt)), index=dt).groupby(per.values).transform("min").values
    return PC, PA, pid.astype(np.int64), first.astype(np.int64)
# ---------------------------------------------------------------- 5. Swing GG (monthly ATR) / 6. Multiday GG (weekly ATR)
def gg_trade(d, side=-1, freq="M", gate_lvl=0.382, entry_lvl=0.618, tgt_lvl=1.0, stop="pivot", ema_gate="with", po_filter=False, min_left=5):
    """side -1 = downside gate short (his Swing-GG short); +1 = upside gate long. ema_gate: 'with' = his rule (prior close above EMA21 for the short,
    mirrored below EMA21 for the long), 'trend' = long only when prior close above EMA21 (short below), 'off'. stop: 'pivot' (PC) or 'trigger' (0.236)."""
    C = _cache(d); o, h, l, c = d["o"], d["h"], d["l"], d["c"]; n = len(c); e21 = C["e21"]
    PC, PA, last, first = htf_levels(d, freq)
    lev = lambda x: PC + side * x * PA
    Lg, Le, Lt = lev(gate_lvl), lev(entry_lvl), lev(tgt_lvl); Ls = PC if stop == "pivot" else lev(0.236)
    pos_in = np.arange(n) - first; left = last - np.arange(n)
    ents, eps, tg, sp, ls = [], [], [], [], []
    done_period = -1
    for t in range(1, n):
        if not np.isfinite(PA[t]) or last[t] == done_period: continue
        hit_gate = (l[t] <= Lg[t]) if side < 0 else (h[t] >= Lg[t])
        if not hit_gate: continue
        done_period = last[t]   # first gate open of the period decides
        if left[t] < min_left - 1: continue
        if ema_gate == "with" and not ((c[t - 1] > e21[t - 1]) if side < 0 else (c[t - 1] < e21[t - 1])): continue
        if ema_gate == "trend" and not ((c[t - 1] > e21[t - 1]) if side > 0 else (c[t - 1] < e21[t - 1])): continue
        if po_filter and not ((C["po"][t - 1] < -61.8) if side < 0 else (C["po"][t - 1] > 61.8)): continue
        if not C["liq"][t - 1]: continue
        for u in range(t, last[t] + 1):     # resting stop at entry level from the gate-open bar to period end
            if (side < 0 and l[u] <= Le[t]) or (side > 0 and h[u] >= Le[t]):
                px = min(o[u], Le[t]) if side < 0 else max(o[u], Le[t])   # gap through the level fills at the open
                ents.append(u); eps.append(px); tg.append(Lt[t]); sp.append(Ls[t]); ls.append(last[t]); break
    ent = np.array(ents, np.int64); ep = np.array(eps); T = np.array(tg); S = np.array(sp); LS = np.array(ls, np.int64)
    xi, xp = eng_bracket(o, h, l, c, ent, ep, T, S, LS, side, 1)
    if ema_gate == "with": gm = np.r_[False, (c[:-1] > e21[:-1]) if side < 0 else (c[:-1] < e21[:-1])]
    elif ema_gate == "trend": gm = np.r_[False, (c[:-1] > e21[:-1]) if side > 0 else (c[:-1] < e21[:-1])]
    else: gm = np.ones(n, bool)
    gm &= np.r_[False, C["liq"][:-1]] & np.isfinite(PA); gate = np.flatnonzero(gm)
    dT = (T - ep) / ep; dS = (S - ep) / ep; nleft = LS - ent
    def rsim(R):
        f = R.ravel(); r_ = R.shape[1]; e2 = o[f]; T2 = e2 * (1 + np.repeat(dT, r_)); S2 = e2 * (1 + np.repeat(dS, r_))
        L2 = np.minimum(f + np.repeat(nleft, r_), n - 1).astype(np.int64)
        x2, p2 = eng_bracket(o, h, l, c, f, e2, T2, S2, L2, side, 0); return e2.reshape(R.shape), p2.reshape(R.shape)
    return _pack(ent, xi, ep, xp, side, gate, rsim)
# ---------------------------------------------------------------- 7. Daily EMA21 deviation reversion
def ema21rev(d, side=-1, k=3.0, H=28):
    """side -1: close >= EMA21 + k*ATR -> short at close, cover on touch of EMA21 (prior-bar value) or after H; +1 mirror below."""
    C = _cache(d); o, h, l, c = d["o"], d["h"], d["l"], d["c"]; n = len(c); e21 = C["e21"]; a = C["a"]
    dev = (c - e21) / a; x = (dev >= k) if side < 0 else (dev <= -k)
    sig = x & ~np.r_[False, x[:-1]] & C["liq"]; sig[:30] = False
    ent = np.flatnonzero(sig); xi, xp = eng_touch(o, h, l, c, e21, ent, side, H)
    # note: a long (side +1) bought below EMA21 exits when high touches EMA21; a short exits when low touches EMA21
    keep = nonoverlap(ent, xi); ent, xi, xp = ent[keep], xi[keep], xp[keep]
    gate = np.flatnonzero(C["liq"] & (np.arange(n) >= 30) & ((c < e21) if side > 0 else (c > e21)))
    def rsim(R):
        f = R.ravel(); x2, p2 = eng_touch(o, h, l, c, e21, f, side, H); return c[f].reshape(R.shape), p2.reshape(R.shape)
    return _pack(ent, xi, c[ent], xp, side, gate, rsim)
# ---------------------------------------------------------------- 8. Phase Oscillator zone exits (doctrine signals)
def po_signal(d, side=1, kind="accum", H=10):
    C = _cache(d); o, c = d["o"], d["c"]; n = len(c); p = C["po"]; pp = np.r_[np.nan, p[:-1]]
    if kind == "accum": sig = (pp <= -61.8) & (p > -61.8) if side > 0 else (pp >= 61.8) & (p < 61.8)
    else: sig = (pp <= -100) & (p > -100) if side > 0 else (pp >= 100) & (p < 100)
    sig &= C["liq"]; sig[:30] = False
    ent = np.flatnonzero(sig); ep, xp, xi = eng_hold(o, c, ent, H, 0)
    gate = np.flatnonzero(C["liq"] & (np.arange(n) >= 30))
    def rsim(R):
        f = R.ravel(); e2, p2, _ = eng_hold(o, c, f, H, 0); return e2.reshape(R.shape), p2.reshape(R.shape)
    return _pack(ent, xi, ep, xp, side, gate, rsim)
# ---------------------------------------------------------------- 9. Pivot Ribbon conviction arrow (13/48 cross)
def ribbon(d, side=1, exitm="opposite", cap=120):
    C = _cache(d); o, c = d["o"], d["c"]; n = len(c); up = C["e13"] > C["e48"]
    cross = (up & ~np.r_[False, up[:-1]]) if side > 0 else (~up & np.r_[False, up[:-1]])
    cross &= C["liq"]; cross[:60] = False
    if exitm == "opposite": ex = (~up & np.r_[False, up[:-1]]) if side > 0 else (up & ~np.r_[False, up[:-1]])
    else: f8 = C["e8"] > C["e21"]; ex = ~f8 if side > 0 else f8
    ent = np.flatnonzero(cross)
    if exitm.startswith("h"):
        H = int(exitm[1:]); ep, xp, xi = eng_hold(o, c, ent, H, 0)
        def rsim(R):
            f = R.ravel(); e2, p2, _ = eng_hold(o, c, f, H, 0); return e2.reshape(R.shape), p2.reshape(R.shape)
    else:
        xi, xp = eng_signal_exit(c, ent, ex, cap); ep = c[ent]
        def rsim(R):
            f = R.ravel(); x2, p2 = eng_signal_exit(c, f, ex, cap); return c[f].reshape(R.shape), p2.reshape(R.shape)
    gate = np.flatnonzero(C["liq"] & (np.arange(n) >= 60))
    return _pack(ent, xi, ep, xp, side, gate, rsim)
# ---------------------------------------------------------------- 10. Compression -> expansion in the EMA21/48 direction
def comp_expansion(d, side=1, minbars=5, H=10):
    C = _cache(d); o, c = d["o"], d["c"]; n = len(c); comp = C["comp"]
    run = np.zeros(n, int)
    for i in range(1, n): run[i] = run[i - 1] + 1 if comp[i] else 0
    rel = (comp == 0) & (np.r_[0, run[:-1]] >= minbars)
    tr = (C["e21"] > C["e48"]) if side > 0 else (C["e21"] < C["e48"])
    sig = rel & tr & C["liq"]; sig[:60] = False
    ent = np.flatnonzero(sig); ep, xp, xi = eng_hold(o, c, ent, H, 1)
    gate = np.flatnonzero(C["liq"] & (np.arange(n) >= 60) & tr)
    def rsim(R):
        f = R.ravel(); e2, p2, _ = eng_hold(o, c, f, H, 1); return e2.reshape(R.shape), p2.reshape(R.shape)
    return _pack(ent, xi, ep, xp, side, gate, rsim)
# ---------------------------------------------------------------- 11. Big down day (SPX -2% day) -> next H sessions
def bigday(d, side=1, thr=-2.0, H=10):
    C = _cache(d); o, c = d["o"], d["c"]; n = len(c); r = np.r_[np.nan, c[1:] / c[:-1] - 1] * 100
    sig = (r <= thr) & C["liq"]; ent = np.flatnonzero(sig); ep, xp, xi = eng_hold(o, c, ent, H, 0)
    gate = np.flatnonzero(C["liq"])
    def rsim(R):
        f = R.ravel(); e2, p2, _ = eng_hold(o, c, f, H, 0); return e2.reshape(R.shape), p2.reshape(R.shape)
    return _pack(ent, xi, ep, xp, side, gate, rsim)
# ---------------------------------------------------------------- 12. O'Neil follow-through day (symmetric race to the correction low)
def ftd(d, side=1, corr=10.0, gain=1.25, lb=63):
    C = _cache(d); o, h, l, c, v = d["o"], d["h"], d["l"], d["c"], d["v"]; n = len(c)
    hh = pd.Series(c).rolling(lb, min_periods=20).max().values
    ents, tg, sp = [], [], []
    i = lb; state = 0; low = np.nan; d1 = -1; d1low = np.nan
    while i < n:
        dd = c[i] / hh[i] - 1
        if state == 0 and dd <= -corr / 100: state = 1; low = l[i]
        if state >= 1:
            low = min(low, l[i]) if state == 1 else low
            if state == 1 and c[i] > c[i - 1]: state = 2; d1 = i; d1low = l[i]; low = min(low, l[i])
            elif state == 2:
                if l[i] < d1low: state = 1; low = min(low, l[i])
                elif i - d1 >= 3 and (c[i] / c[i - 1] - 1) * 100 >= gain and (v[i] > v[i - 1] or d["kind"] == "fut" and False):
                    X = c[i] - low
                    if X > 0: ents.append(i); tg.append(c[i] + X if side > 0 else c[i] - X); sp.append(low if side > 0 else c[i] + X)
                    state = 0
            if c[i] >= hh[i] * 0.999: state = 0
        i += 1
    ent = np.array(ents, np.int64); T = np.array(tg); S = np.array(sp); LS = np.minimum(ent + 120, n - 1).astype(np.int64)
    xi, xp = eng_bracket(o, h, l, c, ent, c[ent] if len(ent) else np.array([]), T, S, LS, side, 2) if len(ent) else (np.array([], np.int64), np.array([]))
    gate = np.flatnonzero(np.arange(n) >= lb); ep = c[ent] if len(ent) else np.array([])
    dT = (T - ep) / ep if len(ent) else np.array([]); dS = (S - ep) / ep if len(ent) else np.array([])
    def rsim(R):
        f = R.ravel(); r_ = R.shape[1]; e2 = c[f]; L2 = np.minimum(f + 120, n - 1).astype(np.int64)
        x2, p2 = eng_bracket(o, h, l, c, f, e2, e2 * (1 + np.repeat(dT, r_)), e2 * (1 + np.repeat(dS, r_)), L2, side, 2); return e2.reshape(R.shape), p2.reshape(R.shape)
    return _pack(ent, xi, ep, xp, side, gate, rsim)
