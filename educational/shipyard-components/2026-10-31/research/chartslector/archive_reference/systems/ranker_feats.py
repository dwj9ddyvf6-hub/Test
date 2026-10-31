"""Archival opportunity-ranker feature kernels on S x T panels; fitted component coefficients are caller-supplied and are not included here.
u_<f> = universe percentile (share of universe names strictly below, x100); l_<f> = percentile rank inside the day's list (x100)."""
import numpy as np, pandas as pd, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "archive_source" / "lib"))
import ind as I
def raw(O, H, L, C, V, need=None):
    f = {}; tr = I.tr(H, L, C); a14 = I.rma(tr, 14); want = (lambda k: need is None or k in need)
    lc = np.log(C); dl = lc - I.lag(lc)
    for n in [5, 10, 20, 21, 50, 63, 126, 252]:
        if want(f"dhi{n}") or want(f"dhiA{n}") or want(f"pos{n}"):
            hh = I.rmax(H, n); ll = I.rmin(L, n)
            if want(f"dhi{n}"): f[f"dhi{n}"] = C / hh - 1
            if want(f"dhiA{n}"): f[f"dhiA{n}"] = (C - hh) / a14
            if want(f"pos{n}"): f[f"pos{n}"] = (C - ll) / (hh - ll)
        if want(f"ret{n}"): f[f"ret{n}"] = C / I.lag(C, n) - 1
    for n in [10, 20, 50, 100, 150, 200]:
        if want(f"xs{n}") or want(f"slope{n}"):
            m = I.sma(C, n)
            if want(f"xs{n}"): f[f"xs{n}"] = (C - m) / a14
            if want(f"slope{n}"): f[f"slope{n}"] = m / I.lag(m, 5) - 1
        if want(f"xe{n}"): f[f"xe{n}"] = (C - I.ema(C, n)) / a14
    if want("pctB") or want("bbw"):
        m20 = I.sma(C, 20); s20 = I.rstd(C, 20) * np.sqrt(20 / 19)   # pandas std ddof=1 as in feats.py
        f["pctB"] = (C - (m20 - 2 * s20)) / (4 * s20); f["bbw"] = 4 * s20 / m20
    if want("rvol50"): f["rvol50"] = V / I.sma(V, 50)
    if want("rvol20_50"): f["rvol20_50"] = I.sma(V, 20) / I.sma(V, 50)
    if want("atrp"): f["atrp"] = a14 / C
    if want("atr5_20"): f["atr5_20"] = I.sma(tr, 5) / I.sma(tr, 20)
    if want("atr14_50"): f["atr14_50"] = a14 / I.rma(tr, 50)
    if want("vol20"): f["vol20"] = I.rstd(dl, 20)
    if want("upfrac20"): f["upfrac20"] = I.sma((C > I.lag(C)).astype(np.float32), 20)
    if want("ema10_20"): f["ema10_20"] = (I.ema(C, 10) - I.ema(C, 20)) / a14
    ad = np.abs(C - I.lag(C))
    if want("er20"): f["er20"] = np.abs(C - I.lag(C, 20)) / I.rsum(ad, 20)
    if want("er63"): f["er63"] = np.abs(C - I.lag(C, 63)) / I.rsum(ad, 63)
    if want("sharpe63"): f["sharpe63"] = I.sma(dl, 63) / (I.rstd(dl, 63) * np.sqrt(63 / 62))
    if want("sharpe126"): f["sharpe126"] = I.sma(dl, 126) / (I.rstd(dl, 126) * np.sqrt(126 / 125))
    f["e50ATR"] = (C - I.sma(C, 50)) / a14
    for k, v in list(f.items()): f[k] = np.where(np.isfinite(v), v, np.nan).astype(np.float32)
    return f
def upct(x, umask):
    """share of universe names strictly below x (x100), per day; x evaluated for every row."""
    out = np.full(x.shape, np.nan, np.float32)
    for t in range(x.shape[1]):
        u = x[umask[:, t], t]; u = np.sort(u[np.isfinite(u)])
        if len(u) < 20: continue
        col = x[:, t]; ok = np.isfinite(col)
        out[ok, t] = np.searchsorted(u, col[ok], side="left") / len(u) * 100
    return out
def lpct(x, lmask):
    y = np.where(lmask, x, np.nan); return (pd.DataFrame(y).rank(axis=0, pct=True).values * 100).astype(np.float32)
# Static output-mixture weights are preserved as source; the fitted component-coefficient mapping required by score() is not included or calibrated here.
WEIGHTS = {"S10": (0.50, 0.20, 0.30), "S20": (0.45, 0.30, 0.25), "S42": (0.35, 0.40, 0.25), "S63": (0.30, 0.50, 0.20)}   # (Breakout, Expansion, Risk), exact fit
def term(F, name):
    """evaluate a model term name against feature dict F (u_/l_ prefixed or nonlinear e50 terms)."""
    e = F["e50ATR"]
    if name.startswith("ext_abs"): return np.abs(e - float(name[7:]))
    if name.startswith("ext_under"): return np.maximum(float(name[9:]) - e, 0)
    if name.startswith("ext_over"): return np.maximum(e - float(name[8:]), 0)
    return F[name]
def score(F, coefs):
    out = {}
    for comp in ("Breakout", "Expansion", "Risk"):
        c = coefs[comp]; v = np.full(F["e50ATR"].shape, c["const"], np.float32)
        for k, w in c["terms"].items(): v = v + w * term(F, k)
        out[comp] = np.clip(v, 0, 100)
    for k, (b, e, r) in WEIGHTS.items(): out[k] = b * out["Breakout"] + e * out["Expansion"] + r * out["Risk"]
    out["Opp"] = (out["S10"] + out["S20"] + out["S42"] + out["S63"]) / 4
    return out
