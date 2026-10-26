"""Black-Scholes put pricing and a rolling tail-hedge overlay."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.stats import norm


def bs_put(S: float, K: float, T: float, r: float, sigma: float) -> float:
    if T <= 0:
        return max(K - S, 0.0)
    sigma = max(sigma, 1e-4)
    srt = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / srt
    d2 = d1 - srt
    return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


def skewed_iv(iv_atm: float, S: float, K: float, skew_pts_per_pct: float) -> float:
    """ATM vol plus `skew_pts_per_pct` vol points for every 1% the strike sits below spot."""
    otm_pct = max(0.0, (1.0 - K / S) * 100.0)
    return iv_atm + skew_pts_per_pct / 100.0 * otm_pct


def tail_hedge_overlay(
    core_ret: pd.Series,
    exposure: pd.Series,
    spot: pd.Series,
    iv_atm: pd.Series,
    rf_annual: pd.Series,
    otm: float = 0.15,
    tenor_days: int = 63,
    trigger: float = 1.5,
    skew: float = 0.7,
    spread: float = 0.05,
) -> pd.DataFrame:
    """Each month, roll into puts struck `otm` below spot on (exposure x NAV) notional while exposure > trigger.

    `spread` is the fraction of option premium lost per side to bid/ask.
    """
    idx = core_ret.index
    S = spot.reindex(idx).ffill().to_numpy()
    iv = iv_atm.reindex(idx).ffill().bfill().to_numpy()
    rf = rf_annual.reindex(idx).ffill().bfill().to_numpy()
    cr = core_ret.to_numpy()
    ex = exposure.reindex(idx).fillna(0.0).to_numpy()
    month = idx.year * 12 + idx.month
    new_month = np.r_[True, month[1:] != month[:-1]]

    core = 1.0
    qty = 0.0
    K = 0.0
    expiry = -1
    put_px = 0.0
    nav_prev = 1.0
    out_ret = np.zeros(len(idx))
    hedge_pnl = np.zeros(len(idx))
    premium = np.zeros(len(idx))
    for t in range(len(idx)):
        core *= 1.0 + cr[t]
        if qty > 0:
            T = max(expiry - t, 0) / 252.0
            new_px = bs_put(S[t], K, T, rf[t], skewed_iv(iv[t], S[t], K, skew))
            hedge_pnl[t] = qty * (new_px - put_px)
            put_px = new_px
            if expiry - t <= 0:
                core += qty * put_px
                qty = 0.0
        if new_month[t]:
            if qty > 0:
                core += qty * put_px * (1.0 - spread)
                premium[t] -= qty * put_px * spread
                qty = 0.0
            if ex[t] > trigger:
                nav = core
                K = (1.0 - otm) * S[t]
                expiry = t + tenor_days
                put_px = bs_put(S[t], K, tenor_days / 252.0, rf[t], skewed_iv(iv[t], S[t], K, skew))
                qty = ex[t] * nav / S[t]
                cost = qty * put_px * (1.0 + spread)
                core -= cost
                premium[t] += cost
        nav = core + qty * put_px
        out_ret[t] = nav / nav_prev - 1.0
        nav_prev = nav
    return pd.DataFrame({"ret": out_ret, "hedge_pnl": hedge_pnl, "premium": premium}, index=idx)
