"""The Aurelia signal stack: the Nasdaq-100 total return, aligned returns and the PRISM trend x volatility
targets. `yahoo` is the module the excerpts call (yahoo.get_daily(symbol) -> the source desk's daily frame):
desk/feedlib/aurelia.py binds it to its full-history loader.

Source: Agentic-Trading-Desk aurelia-paper-desk @1720157f768e63ebe76b148aa3d7d1a409ac9673. Each block after a `# >>> excerpt` marker is the
exact text of that source line range (the marker carries its sha256; tests/test_aurelia.py re-hashes every block)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import features as F

yahoo = None  # bound by the caller


# >>> excerpt desk/data/series.py lines 12-25 blob 278b0eea97df5b2ca6ccb18931a2b6af66f0c221 sha256 10d9768414abd2850f859c6a426b33b784037c04ecbcd93bfbd9cfd728221058
PRE_QQQ_DRIFT = 0.0030  # dividends minus ETF fee, added to ^NDX price returns before QQQ existed
QQQ_START = pd.Timestamp("1999-03-10")


def ndx_total_return(refresh: bool = False) -> pd.Series:
    """Daily simple returns of the investable Nasdaq-100: QQQ TR, spliced onto ^NDX before 1999-03-10."""
    ndx = yahoo.get_daily("^NDX", refresh=refresh)["close"]
    qqq = yahoo.get_daily("QQQ", refresh=refresh)["adj_close"]
    r_ndx = ndx.pct_change() + PRE_QQQ_DRIFT / 252
    r_qqq = qqq.pct_change()
    r = pd.concat([r_ndx[r_ndx.index <= QQQ_START], r_qqq[r_qqq.index > QQQ_START]])
    r = r[~r.index.duplicated(keep="last")].sort_index().dropna()
    r.name = "ndx_tr"
    return r


# >>> excerpt desk/inventions.py lines 14-26 blob 9c335dd226e928634e20ceba8d27bf6084aa2ee1 sha256 d8cd3b3d10ae1cff85e764856fbc9f0fcdb22558e160ba3c9f46324ed3b8580b
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


# >>> excerpt desk/inventions.py lines 130-165 blob 9c335dd226e928634e20ceba8d27bf6084aa2ee1 sha256 2c47fc53092e672b789cfb65cc5c0ce0ab2ceff57d15afd6d4fd115df0a92ddd
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
