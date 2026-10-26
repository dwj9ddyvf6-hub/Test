"""Signal library. Every value at date t uses data up to and including the close of t."""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def trend_votes(level: pd.Series, sma_windows=(50, 100, 200), mom_windows=(63, 126, 252)) -> pd.DataFrame:
    votes = {}
    for w in sma_windows:
        votes[f"above_sma{w}"] = (level > level.rolling(w, min_periods=w).mean()).astype(float)
    for w in mom_windows:
        votes[f"mom{w}"] = (level / level.shift(w) - 1.0 > 0).astype(float)
    df = pd.DataFrame(votes, index=level.index)
    warm = max(max(sma_windows), max(mom_windows))
    df.iloc[:warm] = np.nan
    return df


def trend_score(level: pd.Series) -> pd.Series:
    """Share of six bullish trend votes (0..1). NaN during warm-up."""
    return trend_votes(level).mean(axis=1, skipna=False).rename("trend")


def sma_signal(level: pd.Series, window: int = 200) -> pd.Series:
    s = (level > level.rolling(window, min_periods=window).mean()).astype(float)
    s.iloc[:window] = np.nan
    return s.rename(f"sma{window}")


def ewma_vol(r: pd.Series, lam: float = 0.94) -> pd.Series:
    lr2 = np.log1p(r) ** 2
    var = lr2.ewm(alpha=1 - lam, adjust=False).mean()
    return np.sqrt(var * TRADING_DAYS).rename("ewma_vol")


def har_vol_forecast(
    r: pd.Series,
    horizon: int = 5,
    refit_every: int = 21,
    min_obs: int = 504,
    lo: float = 0.10,
    hi: float = 1.50,
) -> pd.Series:
    """Walk-forward HAR-RV forecast of annualised volatility over the next `horizon` days.

    At each refit date t the OLS uses only rows whose forward target window ends on or before t.
    Before the first fit the forecast is an EWMA(0.94).
    """
    lr = np.log1p(r.to_numpy(dtype=float))
    v = lr**2
    n = len(v)
    s = pd.Series(v)
    vd = v
    vw = s.rolling(5, min_periods=5).mean().to_numpy()
    vm = s.rolling(22, min_periods=22).mean().to_numpy()
    fwd = s[::-1].rolling(horizon, min_periods=horizon).mean()[::-1].shift(-1).to_numpy()  # mean of v[t+1..t+h]

    X = np.column_stack([np.ones(n), vd, vw, vm])
    ewma = ewma_vol(r).to_numpy() ** 2 / TRADING_DAYS
    out = np.full(n, np.nan)
    beta = None
    var_lo, var_hi = lo**2 / TRADING_DAYS, hi**2 / TRADING_DAYS
    for t in range(n):
        if t >= min_obs and (beta is None or (t - min_obs) % refit_every == 0):
            last_row = t - horizon  # target of row last_row covers v[last_row+1 .. t]
            rows = np.arange(22, last_row + 1)
            Xi, yi = X[rows], fwd[rows]
            ok = np.isfinite(yi) & np.isfinite(Xi).all(axis=1)
            if ok.sum() > 100:
                beta, *_ = np.linalg.lstsq(Xi[ok], yi[ok], rcond=None)
        if beta is not None and np.isfinite(X[t]).all():
            f = float(X[t] @ beta)
        else:
            f = ewma[t]
        out[t] = min(max(f, var_lo), var_hi)
    return pd.Series(np.sqrt(out * TRADING_DAYS), index=r.index, name="har_vol")


def realized_vol(r: pd.Series, window: int = 21) -> pd.Series:
    return (np.log1p(r).rolling(window).std() * np.sqrt(TRADING_DAYS)).rename(f"rv{window}")


def double7_state(level: pd.Series, gate: pd.Series) -> pd.Series:
    """Double 7: enter on a 7-day closing low while `gate` is true, exit on a 7-day closing high."""
    lo7 = level.rolling(7, min_periods=7).min()
    hi7 = level.rolling(7, min_periods=7).max()
    lvl, lo, hi, g = level.to_numpy(), lo7.to_numpy(), hi7.to_numpy(), gate.fillna(False).to_numpy()
    state = np.zeros(len(lvl))
    on = False
    for t in range(len(lvl)):
        if not on and g[t] and np.isfinite(lo[t]) and lvl[t] <= lo[t]:
            on = True
        elif on and np.isfinite(hi[t]) and lvl[t] >= hi[t]:
            on = False
        state[t] = 1.0 if on else 0.0
    return pd.Series(state, index=level.index, name="double7")


def turn_of_month_window(index: pd.DatetimeIndex) -> pd.Series:
    """1.0 on the last trading day of each month and the first three trading days of the next."""
    s = pd.Series(1, index=index)
    ym = index.year * 12 + index.month
    pos = s.groupby(ym).cumcount().to_numpy() + 1
    size = s.groupby(ym).transform("size").to_numpy()
    flag = (pos <= 3) | (pos == size)
    return pd.Series(flag.astype(float), index=index, name="tom")


def qlike(sigma_forecast: pd.Series, r: pd.Series, horizon: int = 5) -> float:
    """QLIKE loss of an annualised vol forecast against realised next-`horizon`-day variance."""
    v = np.log1p(r) ** 2
    realized = v[::-1].rolling(horizon).mean()[::-1].shift(-1)
    f = (sigma_forecast**2) / TRADING_DAYS
    df = pd.concat([realized, f], axis=1).dropna()
    df = df[df.iloc[:, 0] > 0]
    ratio = df.iloc[:, 0] / df.iloc[:, 1]
    return float((ratio - np.log(ratio) - 1).mean())
