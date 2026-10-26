"""The APEX canonical daily series (desk/data/series.py): the Nasdaq-100 total return, the T-bill rate,
aligned closes, the 7-10y Treasury return, adjusted open/close, Market.

Source: cursor2 main @ca8ac1f650670e1d1a8344d21cff8dd9f0ba4448. Each block after a `# >>> excerpt` marker is the exact text of that
source line range (the marker carries its sha256; tests/test_apex.py re-hashes every block)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

yahoo = None  # bound by the caller (desk/feedlib/apex.py): get_daily(symbol) -> the source's daily frame


# >>> excerpt desk/data/series.py lines 12-94 blob 278b0eea97df5b2ca6ccb18931a2b6af66f0c221 sha256 4da902e338a9aec20dbfadc39f387a39f5360e0af46bf2f1ff53a77d434a91bc
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


def risk_free_daily(index: pd.DatetimeIndex, refresh: bool = False) -> pd.Series:
    """13-week T-bill yield converted to a daily simple return, aligned to `index`."""
    irx = yahoo.get_daily("^IRX", refresh=refresh)["close"] / 100.0
    rf = irx.reindex(index.union(irx.index)).ffill().reindex(index)
    rf = rf.fillna(irx.iloc[0])
    return (rf / 252.0).rename("rf")


def aligned_close(symbol: str, index: pd.DatetimeIndex, field: str = "close", refresh: bool = False) -> pd.Series:
    s = yahoo.get_daily(symbol, refresh=refresh)[field]
    return s.reindex(index.union(s.index)).ffill().reindex(index).rename(symbol)


def treasury_7_10y_returns(index: pd.DatetimeIndex, refresh: bool = False) -> pd.Series:
    """IEF total return; before IEF existed, a duration model on the 10y yield (^TNX)."""
    ief = yahoo.get_daily("IEF", refresh=refresh)["adj_close"].pct_change()
    tnx = yahoo.get_daily("^TNX", refresh=refresh)["close"] / 100.0
    tnx = tnx.reindex(index.union(tnx.index)).ffill()
    dy = tnx.diff()
    duration, convexity = 7.5, 70.0
    synth = tnx.shift(1) / 252 - duration * dy + 0.5 * convexity * dy**2
    synth = synth.reindex(index)
    ief = ief.reindex(index)
    first_ief = ief.first_valid_index()
    out = synth.copy()
    if first_ief is not None:
        out[out.index >= first_ief] = ief[ief.index >= first_ief]
    return out.fillna(0.0).rename("bond_7_10y")


def adjusted_open_close(symbol: str, refresh: bool = False) -> pd.DataFrame:
    """Dividend/split-adjusted open and close so overnight and intraday returns can be separated."""
    df = yahoo.get_daily(symbol, refresh=refresh)
    factor = df["adj_close"] / df["close"]
    return pd.DataFrame({"open": df["open"] * factor, "close": df["adj_close"]})


@dataclass
class Market:
    """Everything the strategies need, aligned on the trading calendar of the underlying."""

    r: pd.Series  # underlying daily simple return
    rf: pd.Series  # daily risk-free simple return
    name: str = "NDX"

    @property
    def index(self) -> pd.DatetimeIndex:
        return self.r.index

    @property
    def level(self) -> pd.Series:
        return (1.0 + self.r).cumprod()


def ndx_market(refresh: bool = False) -> Market:
    r = ndx_total_return(refresh=refresh)
    return Market(r=r, rf=risk_free_daily(r.index, refresh=refresh), name="NDX")


def index_market(symbol: str, start: str | None = None, zero_rf: bool = True, refresh: bool = False) -> Market:
    px = yahoo.get_daily(symbol, refresh=refresh)["close"]
    if start:
        px = px[px.index >= pd.Timestamp(start) - pd.Timedelta(days=400)]
    r = px.pct_change().dropna()
    r = r.replace([np.inf, -np.inf], np.nan).dropna()
    rf = pd.Series(0.0, index=r.index) if zero_rf else risk_free_daily(r.index, refresh=refresh)
    return Market(r=r.rename(symbol), rf=rf.rename("rf"), name=symbol)
