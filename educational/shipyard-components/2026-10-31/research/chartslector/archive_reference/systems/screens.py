"""S2 TradingView screeners, exact filters as posted (SPECS 2). Volumes in shares (TV 'Average Volume 60D'). Float is unknown -> proxy shares outstanding
(MC/close) <= 300M (flagged). 'Primary listing' / 'Sector != biotech' cannot be applied on our panel (all names are US primary listings; no full sector map)."""
import numpy as np, pandas as pd, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "archive_source" / "lib"))
import ind as I
def weekly_to_daily(Wa, P_days, last):
    """value of the last COMPLETED week, for each daily session (no look-ahead)."""
    T = len(P_days); out = np.full((Wa.shape[0], T), np.nan, np.float32); wi = np.searchsorted(last, np.arange(T), side="right") - 1   # week whose last day <= t
    ok = wi >= 0; out[:, ok] = Wa[:, wi[ok]]; return out
def build(L, MC=None, weekly=None):
    O, H, Lo, C, V = L.O, L.H, L.L, L.C, L.V
    atrp = L.atrp * 100; sma50 = I.sma(C, 50); sma150 = I.sma(C, 150); e10 = I.ema(C, 10); e20 = I.ema(C, 20)
    av60 = I.sma(V, 60); adr14 = (I.sma(H / Lo, 14) - 1) * 100; chg = (C / I.lag(C) - 1) * 100; relvol = V / I.sma(I.lag(V), 10)
    perf3m = (C / I.lag(C, 63) - 1) * 100; shares = MC / C if MC is not None else np.full(C.shape, np.nan, np.float32)
    flt = shares <= 3e8
    sc = {}
    sc["breadth_screener"] = (C > sma50) & (atrp > 3) & (av60 > 5e5) & (C > 1) & (e20 > sma50)
    sc["base_screen"] = (C > sma50) & (atrp > 3) & (av60 > 3e5) & (C > 1)
    q_core = (adr14 >= 4) & (e10 >= e20) & (e20 >= sma50) & (av60 > 3e5) & (C >= e20) & (C >= 1)
    sc["qullamaggie_as_posted"] = q_core & flt & (sma150 >= sma50)            # as shown in his image (SMA150 >= SMA50)
    sc["qullamaggie_corrected"] = q_core & flt & (sma50 >= sma150)            # conventional stage-2 order
    sc["qullamaggie_nofloat"] = q_core & (sma50 >= sma150)
    if weekly is not None:
        W, last = weekly
        mfv = np.where(W["H"] > W["L"], ((W["C"] - W["L"]) - (W["H"] - W["C"])) / (W["H"] - W["L"]), 0) * W["V"]
        cmf = I.rsum(mfv.astype(np.float32), 20) / I.rsum(W["V"], 20)
        tp = (W["H"] + W["L"] + W["C"]) / 3; rmf = tp * W["V"]; up = tp > I.lag(tp); dn = tp < I.lag(tp)
        pmf = I.rsum(np.where(up, rmf, 0).astype(np.float32), 14); nmf = I.rsum(np.where(dn, rmf, 0).astype(np.float32), 14)
        mfi = 100 - 100 / (1 + pmf / np.where(nmf > 0, nmf, np.nan))
        cmf_d = weekly_to_daily(cmf, L.dates, last); mfi_d = weekly_to_daily(mfi.astype(np.float32), L.dates, last)
        hot = (MC > 1.5e8) & (atrp > 4) & (perf3m > 25) & flt & (cmf_d > 0)
        sc["hot_stocks"] = hot & (av60 > 1e6) & (mfi_d <= 70)
        sc["hot_stocks_v2"] = hot & (mfi_d < 80) & (I.sma(C * V, 20) > 5e7)
    hvc_base = (C >= 1) & (av60 > 5e5) & (atrp > 3)
    upper = (C - Lo) >= 0.5 * (H - Lo)                                          # daily proxy for 'Change 30m > 0' (strong into the close)
    sc["hvc_daily_proxy"] = hvc_base & (chg > 3) & (relvol > 1.4) & upper
    sc["hvc_jul_tweak_proxy"] = hvc_base & (relvol > 0.7) & (C > O) & upper & (chg > 0)
    return sc
