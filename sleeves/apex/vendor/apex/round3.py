"""Round 3 C1-C7 (desk/round3.py): the lagged multi-asset book, Follow-through, Slingshot, Broken Hedge,
Sector Kings, REFLEX, the gold sleeve, Variance Value on cash, AURELIA.

Source: cursor2 main @ca8ac1f650670e1d1a8344d21cff8dd9f0ba4448. Each block after a `# >>> excerpt` marker is the exact text of that
source line range (the marker carries its sha256; tests/test_apex.py re-hashes every block)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..aurelia import features as F
from . import inventions as N
from . import strategies as S
from .engine import FUTURES_COSTS, simulate
from .series import Market
from . import opt_strategies as O
from .sim import Book, OptionCosts
from .surface import Surface, SurfaceParams

yahoo = None  # bound by the caller (desk/feedlib/apex.py): get_daily(symbol) -> the source's daily frame


# >>> excerpt desk/round3.py lines 18-230 blob 18292d0e9521701363f9f434d472ea12291b9967 sha256 6dd8712584f7b9cfa53cd651da215c0d2b9c6471bcb0a2e99e28bddf24ff2101
SECTORS = ["XLK", "XLF", "XLE", "XLV", "XLP", "XLI", "XLB", "XLU", "XLY"]
TRADING_DAYS = 252


def _lagged_book(decision: np.ndarray, rets: np.ndarray, rf: np.ndarray, bps: float, fin_spread: float = 0.003,
                 lag: int = 1, band: float = 0.20) -> pd.Series:
    """`decision[t]` is the desired weight vector at the close of t. Timing matches `simulate`."""
    n, k = decision.shape
    pos = np.zeros((n, k))
    cur = np.zeros(k)
    for t in range(n):
        j = t - lag
        want = decision[j] if j >= 0 else np.zeros(k)
        want = np.where(np.isfinite(want), want, cur)
        for a in range(k):
            if (want[a] == 0.0 and cur[a] != 0.0) or abs(want[a] - cur[a]) >= band - 1e-12:
                cur[a] = want[a]
        pos[t] = cur
    held = np.vstack([np.zeros(k), pos[:-1]])
    turnover = np.abs(np.diff(np.vstack([np.zeros(k), pos]), axis=0)).sum(axis=1)
    gross = held.sum(axis=1)
    ret = (held * rets).sum(axis=1)
    ret -= np.maximum(gross - 1.0, 0.0) * (rf + fin_spread / TRADING_DAYS)
    ret += np.maximum(1.0 - gross, 0.0) * rf
    ret -= turnover * bps / 1e4
    return ret


def follow_through_mask(level: pd.Series, arm: float = -0.10, jump: float = 0.0125, hold: int = 20) -> pd.Series:
    """True on the sessions whose target is boosted. One follow-through per correction."""
    lvl = level.to_numpy(dtype=float)
    hi63 = level.rolling(63, min_periods=63).max().to_numpy()
    hi10 = level.rolling(10, min_periods=10).max().to_numpy()
    ret = level.pct_change().to_numpy()
    boosted = np.zeros(len(lvl), dtype=bool)
    armed = used = False
    left = 0
    for t in range(len(lvl)):
        if left > 0:
            boosted[t] = True
            left -= 1
        if not np.isfinite(hi63[t]):
            continue
        if lvl[t] >= hi63[t] * (1 - 1e-12):
            armed = False
        elif not armed and lvl[t] <= hi63[t] * (1 + arm):
            armed = True
            used = False
        if armed and not used and np.isfinite(ret[t]) and ret[t] >= jump and np.isfinite(hi10[t]) and lvl[t] >= hi10[t]:
            used = True
            left = hold
            boosted[t] = True
            left -= 1
    return pd.Series(boosted, index=level.index, name="ftd")


def c3_follow_through(m: Market, sig: S.Signals, arm: float = -0.10, hold: int = 20, p: S.ApexParams = S.APEX_50F) -> pd.DataFrame:
    base = S.apex_target(sig, p)
    boosted = follow_through_mask(sig.level, arm=arm, hold=hold)
    tgt = pd.Series(np.maximum(base, np.where(boosted, 2.0, 0.0)), index=m.index).where(base.notna())
    return S.run(tgt, m, p)


def c6_slingshot(m: Market, sig: S.Signals, tnx: pd.Series, threshold: float = 0.50, dip: float = -0.05,
                 hold: int = 10, p: S.ApexParams = S.APEX_50F) -> pd.DataFrame:
    y = tnx.reindex(m.index.union(tnx.index)).ffill().reindex(m.index)
    rise = (y - y.shift(63)).to_numpy()
    ret10 = (sig.level / sig.level.shift(10) - 1).to_numpy()
    trend = sig.trend.to_numpy()
    on = np.zeros(len(m.index), dtype=bool)
    left = 0
    for t in range(len(on)):
        if left > 0:
            on[t] = True
            left -= 1
            continue
        if np.isfinite(rise[t]) and np.isfinite(ret10[t]) and np.isfinite(trend[t]) and trend[t] >= 4 / 6 - 1e-9 \
                and rise[t] > threshold and ret10[t] <= dip:
            on[t] = True
            left = hold - 1
    base = S.apex_target(sig, p)
    tgt = pd.Series(np.maximum(base, np.where(on, 3.0, 0.0)), index=m.index).where(base.notna())
    return S.run(tgt, m, p)


def c4_broken_hedge(m: Market, sig: S.Signals, tsy: pd.Series, gold: pd.Series, dxy: pd.Series, gate: float = 0.20,
                    corr_cut: float = -0.10, p: S.ApexParams = S.APEX_50F, switch_bps: float = 3.0) -> pd.DataFrame:
    idx = m.index
    rn = m.r
    ct = rn.rolling(63).corr(tsy.reindex(idx))
    cg = rn.rolling(63).corr(gold.reindex(idx))
    cd = rn.rolling(63).corr(dxy.reindex(idx))
    mult = pd.Series(np.where((ct > gate) & (cg > gate), 0.5, 1.0), index=idx)
    mult[ct.isna() | cg.isna()] = np.nan
    corrs = pd.concat([ct.rename("TSY"), cg.rename("GOLD"), cd.rename("DXY")], axis=1)
    best = corrs.min(axis=1)
    valid = corrs.notna().any(axis=1)
    choice = pd.Series("CASH", index=corrs.index)
    choice.loc[valid] = corrs.loc[valid].idxmin(axis=1)
    choice = choice.where(best < corr_cut, "CASH")
    # Held during day t is the decision from t-2 when lag is 1, so the diversifier has to be shifted the same way.
    chosen = choice.shift(2)
    cash_spread = m.rf - p.costs.cash_spread / TRADING_DAYS
    div_ret = pd.Series(np.where(chosen == "TSY", tsy.reindex(idx), np.where(chosen == "GOLD", gold.reindex(idx),
                         np.where(chosen == "DXY", dxy.reindex(idx), cash_spread))), index=idx).fillna(0.0)
    switches = (choice != choice.shift(1)).astype(float).shift(2).fillna(0.0)
    out = S.run(S.apex_target(sig, p) * mult, m, p, cash_ret=div_ret)
    idle = (1.0 - out["exposure"]).clip(lower=0.0)
    extra = switches.reindex(out.index).fillna(0.0) * idle * switch_bps / 1e4
    out = out.copy()
    out["ret"] = out["ret"] - extra
    out["hedge_off"] = ((ct > gate) & (cg > gate)).reindex(out.index)
    return out


def c2_sector_kings(index: pd.DatetimeIndex, rf: pd.Series, lookback: int = 126, vol_target: float = 0.25, cap: float = 2.0,
                    bps: float = 5.0, fin_spread: float = 0.003) -> pd.DataFrame:
    px = pd.DataFrame({s: yahoo.get_daily(s)["adj_close"] for s in SECTORS})
    px = px.reindex(index.union(px.index)).ffill().reindex(index)
    r = px.pct_change().fillna(0.0)
    ready = px.notna().all(axis=1) & px.shift(max(lookback, 200)).notna().all(axis=1)
    mom = px / px.shift(lookback) - 1
    above = px > px.rolling(200).mean()
    month_start = pd.Series(index.month, index=index).ne(pd.Series(index.month, index=index).shift(1)).to_numpy()
    raw = np.zeros((len(index), len(SECTORS)))
    cur = np.zeros(len(SECTORS))
    mom_v, above_v, ready_v = mom.to_numpy(), above.fillna(False).to_numpy(), ready.to_numpy()
    for t in range(len(index)):
        if month_start[t] and ready_v[t]:
            scores = np.where(above_v[t] & np.isfinite(mom_v[t]), mom_v[t], -np.inf)
            order = np.argsort(-scores)
            picks = [i for i in order if np.isfinite(scores[i])][:2]
            cur = np.zeros(len(SECTORS))
            for i in picks:
                cur[i] = 1.0 / len(picks)
        raw[t] = cur
    held = np.vstack([np.zeros(len(SECTORS)), raw[:-1]])
    basket = pd.Series((held * r.to_numpy()).sum(axis=1), index=index)
    live = pd.Series(raw.sum(axis=1), index=index).cumsum() > 0
    vol = F.har_vol_forecast(basket.where(live, 0.0))
    scale = np.minimum(cap, vol_target / vol).where(live)
    decision = raw * scale.to_numpy()[:, None]
    ret = _lagged_book(decision, r.to_numpy(), rf.reindex(index).to_numpy(), bps=bps, fin_spread=fin_spread)
    out = pd.DataFrame({"ret": ret}, index=index)
    out = out[live.shift(2).fillna(False)]
    out["gross"] = pd.Series(decision.sum(axis=1), index=index).shift(2).reindex(out.index)
    return out


def c5_reflex(m: Market, sig: S.Signals, sox_r: pd.Series, recent: int = 1260, start: str = "2001-01-02",
              costs=FUTURES_COSTS) -> tuple[pd.DataFrame, pd.Series]:
    X, fwd = N.gestalt_inputs(m, sig, sox_r)
    idx = X.index
    Xv = X.to_numpy(dtype=float)
    y = fwd.to_numpy(dtype=float)
    ok = np.isfinite(Xv).all(axis=1)
    vol = sig.vol
    lev = np.full(len(idx), np.nan)
    first = idx.searchsorted(pd.Timestamp(start))
    last = np.nan
    k, horizon, shrink = 150, 21, 0.5
    for t in range(first, len(idx)):
        if (t - first) % 5 == 0 and ok[t]:
            cand = np.arange(0, t - horizon)
            cand = cand[ok[cand] & np.isfinite(y[cand])]
            if len(cand) > k * 2:
                hist = Xv[: t + 1][ok[: t + 1]]
                mu, sd = hist.mean(axis=0), hist.std(axis=0)
                sd[sd == 0] = 1.0
                d = np.sqrt((((Xv[cand] - mu) / sd - (Xv[t] - mu) / sd) ** 2).sum(axis=1))
                nn = cand[np.argpartition(d, k)[:k]]
                mu_s = (1 - shrink) * y[nn].mean() + shrink * y[cand].mean()
                base = float(np.clip(0.5 * (mu_s * TRADING_DAYS / horizon) / max(vol.iloc[t], 0.05) ** 2, 0.0, 4.0))
                recent_nn = nn[nn >= t - recent]
                m_all = y[nn].mean() * TRADING_DAYS / horizon
                if len(recent_nn) >= 15:
                    m_recent = y[recent_nn].mean() * TRADING_DAYS / horizon
                    if m_recent < 0 and m_all > 0:
                        base *= 0.25
                    elif m_recent > m_all + 0.10:
                        base = min(4.0, base * 1.25)
                last = base
        lev[t] = last
    L = pd.Series(lev, index=idx, name="reflex_L")
    p = S.ApexParams(sigma_target=0.5, l_max=4.0, costs=costs)
    return S.run(L, m, p), L


def gold_sleeve(index: pd.DatetimeIndex, rf: pd.Series, gold: pd.Series, bps: float = 3.0, fin_spread: float = 0.003) -> pd.Series:
    r = gold.reindex(index)
    valid = r.notna()
    rv = r[valid].fillna(0.0)
    mk = Market(r=rv, rf=rf.reindex(rv.index).fillna(0.0), name="GOLD")
    sig = S.compute_signals(mk)
    L = (sig.trend * np.minimum(2.0, 0.20 / sig.vol)).reindex(index)
    out = simulate(L, r.fillna(0.0), rf.reindex(index).fillna(0.0), costs=FUTURES_COSTS.with_(trade_bps=bps, fin_spread=fin_spread),
                   lag=1, band=0.20)
    return out["ret"]


def variance_value_cash(m: Market, price: pd.Series, vol_symbol: str, div: float, cost_mult: float = 1.0,
                        start: str = "2002-01-25") -> pd.Series:
    surf = Surface(m.index, vol_symbol, SurfaceParams.load())
    x = O.build_inputs(m, price, surf, div)
    book = Book(x.dates, x.S, x.r, surf, x.rf_daily, x.div, OptionCosts(mult=cost_mult))
    t0 = int(m.index.searchsorted(pd.Timestamp(start)))
    return book.run(lambda b, t: O._variance_value(b, x, t), t0)["ret"]


def c1_aurelia(equity_r: pd.Series, gold_r: pd.Series, rf: pd.Series, cost_mult: float = 1.0) -> pd.DataFrame:
    both = pd.concat([equity_r.rename("E"), gold_r.rename("G")], axis=1).dropna()
    mk = Market(r=both["E"], rf=rf.reindex(both.index).fillna(0.0), name="EQ")
    return N.prism({"NDX": both["E"], "GOLD": both["G"].reindex(both.index)}, mk, cost_mult=cost_mult)
