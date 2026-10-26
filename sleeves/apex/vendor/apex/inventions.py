"""The invention round N1-N7 (desk/inventions.py): aligned returns, the SOX total return, Duration Shield,
Silicon Switch, the multi-asset simulator and PRISM, GESTALT and GESTALT x APEX.

Source: cursor2 main @ca8ac1f650670e1d1a8344d21cff8dd9f0ba4448. Each block after a `# >>> excerpt` marker is the exact text of that
source line range (the marker carries its sha256; tests/test_apex.py re-hashes every block)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..aurelia import features as F
from . import strategies as S
from .engine import FUTURES_COSTS, simulate
from .series import Market, ndx_market, treasury_7_10y_returns

yahoo = None  # bound by the caller (desk/feedlib/apex.py): get_daily(symbol) -> the source's daily frame


# >>> excerpt desk/inventions.py lines 14-245 blob 9c335dd226e928634e20ceba8d27bf6084aa2ee1 sha256 3a38709a4c2f10d32077f0d4f812a03b60a5423a5727dcf2899f186edcbf6cf5
TRADING_DAYS = 252


# ---------------------------------------------------------------- data
def aligned_returns(symbol: str, index: pd.DatetimeIndex, field: str = "adj_close") -> pd.Series:
    """Daily returns of `symbol` measured between consecutive dates of `index` (handles 7-day crypto calendars)."""
    df = yahoo.get_daily(symbol)
    px = df[field].where(df[field].notna(), df["close"])
    px = px.reindex(index.union(px.index)).ffill().reindex(index)
    first = df.index[0]
    r = px.pct_change()
    r[index <= first] = np.nan
    return r.rename(symbol)


def sox_total_return(index: pd.DatetimeIndex) -> pd.Series:
    sox = aligned_returns("^SOX", index, field="close") + 0.01 / TRADING_DAYS
    smh = aligned_returns("SMH", index)
    first_smh = yahoo.get_daily("SMH").index[0]
    out = sox.where(index <= first_smh + pd.Timedelta(days=1), smh)
    out[index < yahoo.get_daily("^SOX").index[0] + pd.Timedelta(days=1)] = np.nan
    return out.rename("SOX")


def sleeve_returns(index: pd.DatetimeIndex, ndx_r: pd.Series) -> dict[str, pd.Series]:
    return {
        "NDX": ndx_r.reindex(index),
        "TSY": treasury_7_10y_returns(index),
        "GOLD": aligned_returns("GLD", index),
        "OIL": aligned_returns("USO", index),
        "USD": aligned_returns("UUP", index),
        "SOX": sox_total_return(index),
        "BTC": aligned_returns("BTC-USD", index, field="close"),
    }


# ---------------------------------------------------------------- N1 Duration Shield
def duration_gate(tnx: pd.Series, index: pd.DatetimeIndex, threshold: float = 0.50) -> pd.Series:
    y = tnx.reindex(index.union(tnx.index)).ffill().reindex(index)
    rise = y - y.shift(63)
    return pd.Series(np.where(rise > threshold, 0.5, 1.0), index=index).rename("duration_gate")


def n1_duration_shield(m: Market, sig: S.Signals, tnx: pd.Series, threshold: float = 0.50, p: S.ApexParams = S.APEX_50F) -> pd.DataFrame:
    tgt = S.apex_target(sig, p) * duration_gate(tnx, m.index, threshold)
    return S.run(tgt.where(sig.trend.notna()), m, p)


# ---------------------------------------------------------------- N2 Silicon Switch
def n2_silicon_switch(m: Market, sox_r: pd.Series, lookback: int = 126, hysteresis: float = 0.05,
                      p: S.ApexParams = S.APEX_50F) -> pd.DataFrame:
    idx = m.index
    rn, rs = m.r, sox_r.reindex(idx)
    valid = rs.notna()
    lvl_n = (1 + rn).cumprod()
    lvl_s = (1 + rs.fillna(0)).cumprod().where(valid.cummax())
    mom_n = lvl_n / lvl_n.shift(lookback) - 1
    mom_s = lvl_s / lvl_s.shift(lookback) - 1
    hold = np.zeros(len(idx), dtype=int)  # 0 = NDX, 1 = SOX
    cur = 0
    mn, ms = mom_n.to_numpy(), mom_s.to_numpy()
    for t in range(len(idx)):
        if np.isfinite(mn[t]) and np.isfinite(ms[t]):
            if cur == 0 and ms[t] - mn[t] > hysteresis:
                cur = 1
            elif cur == 1 and mn[t] - ms[t] > hysteresis:
                cur = 0
        hold[t] = cur
    hold = pd.Series(hold, index=idx)
    sig_n = S.compute_signals(m)
    rs_valid = rs[valid.cummax()].fillna(0.0)
    sig_s = S.compute_signals(Market(r=rs_valid, rf=m.rf.reindex(rs_valid.index), name="SOX"))
    L_s = S.apex_target(sig_s, p).reindex(idx)
    L = np.where(hold == 1, L_s, S.apex_target(sig_n, p))
    target = pd.Series(L, index=idx).where(sig_n.trend.notna())
    held_asset = hold.shift(p.lag + 1).fillna(0)
    r_blend = pd.Series(np.where(held_asset == 1, rs.fillna(rn), rn), index=idx)
    switched = hold.shift(p.lag).diff().abs().fillna(0)
    extra = switched * target.shift(p.lag).abs().fillna(0) * 2 * p.costs.trade_bps / 1e4
    out = simulate(target, r_blend, m.rf, costs=p.costs, lag=p.lag, band=p.band, extra_cost=extra)
    out["holding_sox"] = held_asset.reindex(out.index)
    return out


# ---------------------------------------------------------------- multi-asset simulator and PRISM
def simulate_multi(targets: pd.DataFrame, rets: pd.DataFrame, rf: pd.Series, bps: dict, carry: dict,
                   fin_spread: float = 0.003, lag: int = 1, band: float = 0.2) -> pd.DataFrame:
    idx = rets.index
    cols = list(targets.columns)
    Tg = targets.reindex(idx)[cols].to_numpy(dtype=float)
    R = rets.reindex(idx)[cols].fillna(0.0).to_numpy(dtype=float)
    rfa = rf.reindex(idx).shift(1).bfill().to_numpy(dtype=float)
    n, k = R.shape
    pos = np.zeros((n, k))
    cur = np.zeros(k)
    for t in range(n):
        j = t - lag
        want = np.where(np.isfinite(Tg[j]), np.maximum(Tg[j], 0.0), 0.0) if j >= 0 else np.zeros(k)
        for a in range(k):
            if (want[a] == 0.0 and cur[a] != 0.0) or abs(want[a] - cur[a]) >= band - 1e-12:
                cur[a] = want[a]
        pos[t] = cur
    held = np.vstack([np.zeros(k), pos[:-1]])
    turnover = np.abs(np.diff(np.vstack([np.zeros(k), pos]), axis=0))
    bps_v = np.array([bps.get(c, 3.0) for c in cols]) / 1e4
    carry_v = np.array([carry.get(c, 0.0) for c in cols])
    excess = (held * (R - rfa[:, None])).sum(axis=1)
    gross = held.sum(axis=1)
    ret = rfa + excess - np.maximum(gross - 1.0, 0.0) * fin_spread / TRADING_DAYS - (held * carry_v).sum(axis=1) / TRADING_DAYS \
        - (turnover * bps_v).sum(axis=1)
    out = pd.DataFrame({"ret": ret, "gross": gross}, index=idx)
    for i, c in enumerate(cols):
        out[f"w_{c}"] = held[:, i]
    return out


PRISM_CAPS = {"NDX": 4.0, "TSY": 5.0, "GOLD": 3.0, "OIL": 2.0, "USD": 4.0, "SOX": 3.0, "BTC": 1.0}
PRISM_BPS = {"NDX": 3.0, "TSY": 3.0, "GOLD": 3.0, "OIL": 5.0, "USD": 3.0, "SOX": 3.0, "BTC": 10.0}
PRISM_CARRY = {"BTC": 0.03}


def prism_targets(rets: dict[str, pd.Series], index: pd.DatetimeIndex, sigma_sleeve: float = 0.20, sigma_port: float = 0.35,
                  m_cap: float = 3.0, gross_cap: float = 6.0) -> tuple[pd.DataFrame, pd.DataFrame]:
    unit = {}
    for name, r in rets.items():
        r = r.reindex(index)
        valid = r.notna().cummax()
        if not valid.any():
            continue
        rv = r[valid].fillna(0.0)
        lvl = (1 + rv).cumprod()
        trend = F.trend_score(lvl)
        vol = F.har_vol_forecast(rv)
        e = (trend * np.minimum(PRISM_CAPS[name], sigma_sleeve / vol)).reindex(index)
        e[index < rv.index[0] + pd.Timedelta(days=380)] = np.nan
        unit[name] = e
    E = pd.DataFrame(unit, index=index)
    R = pd.DataFrame({k: v.reindex(index) for k, v in rets.items()})
    n_avail = E.notna().sum(axis=1).replace(0, np.nan)
    w_unit = E.div(n_avail, axis=0)
    u = (w_unit.shift(1) * R).sum(axis=1, min_count=1)
    live = u.notna() & (n_avail.shift(1) > 0)
    u_live = u[live.cummax()].fillna(0.0).clip(-0.5, 0.5)
    vol_u = F.har_vol_forecast(u_live).reindex(index)
    mult = np.minimum(m_cap, sigma_port / vol_u)
    final = w_unit.mul(mult, axis=0)
    for c in final.columns:
        final[c] = np.minimum(final[c], PRISM_CAPS[c])
    gross = final.sum(axis=1)
    scale = np.where(gross > gross_cap, gross_cap / gross, 1.0)
    final = final.mul(scale, axis=0)
    return final, R


def prism(rets: dict[str, pd.Series], m: Market, sigma_port: float = 0.35, cost_mult: float = 1.0) -> pd.DataFrame:
    tg, R = prism_targets(rets, m.index, sigma_port=sigma_port)
    bps = {k: v * cost_mult for k, v in PRISM_BPS.items()}
    out = simulate_multi(tg, R, m.rf, bps, PRISM_CARRY, fin_spread=0.003 * cost_mult)
    first = tg.dropna(how="all").index[0]
    return out[out.index > first]


# ---------------------------------------------------------------- N5 GESTALT analog engine
def gestalt_features(level: pd.Series, r: pd.Series, vol: pd.Series, trend: pd.Series, tnx: pd.Series, vix: pd.Series,
                     sox_r: pd.Series) -> pd.DataFrame:
    idx = level.index
    y = tnx.reindex(idx.union(tnx.index)).ffill().reindex(idx)
    v = vix.reindex(idx.union(vix.index)).ffill().reindex(idx)
    sox_lvl = (1 + sox_r.reindex(idx).fillna(0)).cumprod().where(sox_r.reindex(idx).notna().cummax())
    X = pd.DataFrame({
        "trend": trend,
        "log_vol": np.log(vol),
        "vol_change": np.log(vol) - np.log(vol.shift(21)),
        "drawdown": level / level.rolling(252).max() - 1,
        "ret21": level / level.shift(21) - 1,
        "yield_chg63": y - y.shift(63),
        "vix_rel": np.log(v / v.rolling(252).median()),
        "semis_rel63": (sox_lvl / sox_lvl.shift(63)) - (level / level.shift(63)),
    }, index=idx)
    return X


def gestalt_leverage(X: pd.DataFrame, fwd_excess: pd.Series, vol: pd.Series, start: pd.Timestamp, k: int = 150,
                     shrink: float = 0.5, kelly: float = 0.5, cap: float = 4.0, every: int = 5, horizon: int = 21) -> pd.Series:
    idx = X.index
    Xv = X.to_numpy(dtype=float)
    y = fwd_excess.to_numpy(dtype=float)
    ok_feat = np.isfinite(Xv).all(axis=1)
    lev = np.full(len(idx), np.nan)
    first_trade = idx.searchsorted(start)
    last_val = np.nan
    for t in range(first_trade, len(idx)):
        if (t - first_trade) % every == 0 and ok_feat[t]:
            cand = np.arange(0, t - horizon)
            cand = cand[ok_feat[cand] & np.isfinite(y[cand])]
            if len(cand) > k * 2:
                hist = Xv[: t + 1][ok_feat[: t + 1]]
                mu, sd = hist.mean(axis=0), hist.std(axis=0)
                sd[sd == 0] = 1.0
                Z = (Xv[cand] - mu) / sd
                z0 = (Xv[t] - mu) / sd
                d = np.sqrt(((Z - z0) ** 2).sum(axis=1))
                nn = cand[np.argpartition(d, k)[:k]]
                mu_hat = y[nn].mean() * TRADING_DAYS / horizon
                mu_bar = y[cand].mean() * TRADING_DAYS / horizon
                mu_s = (1 - shrink) * mu_hat + shrink * mu_bar
                last_val = float(np.clip(kelly * mu_s / max(vol.iloc[t], 0.05) ** 2, 0.0, cap))
        lev[t] = last_val
    return pd.Series(lev, index=idx, name="gestalt_L")


def gestalt_inputs(m: Market, sig: S.Signals, sox_r: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    tnx = yahoo.get_daily("^TNX")["close"]
    vix = yahoo.get_daily("^VIX")["close"]
    X = gestalt_features(sig.level, m.r, sig.vol, sig.trend, tnx, vix, sox_r)
    lr = np.log1p(m.r - m.rf)
    fwd = lr[::-1].rolling(21).sum()[::-1].shift(-1)
    return X, fwd


def n5_gestalt(m: Market, sig: S.Signals, sox_r: pd.Series, start: str = "2001-01-02", k: int = 150, shrink: float = 0.5,
               costs=FUTURES_COSTS) -> tuple[pd.DataFrame, pd.Series]:
    X, fwd = gestalt_inputs(m, sig, sox_r)
    L = gestalt_leverage(X, fwd, sig.vol, pd.Timestamp(start), k=k, shrink=shrink)
    p = S.ApexParams(sigma_target=0.5, l_max=4.0, costs=costs)
    return S.run(L, m, p), L


def n6_ensemble(m: Market, sig: S.Signals, L_gestalt: pd.Series, costs=FUTURES_COSTS) -> pd.DataFrame:
    p = S.ApexParams(sigma_target=0.5, l_max=4.0, costs=costs)
    tgt = 0.5 * (S.apex_target(sig, S.APEX_50F) + L_gestalt)
    return S.run(tgt, m, p)
