"""Daily exposure simulator with leverage financing, leveraged-ETF fees, trading costs, delay and bands."""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

TRADING_DAYS = 252


@dataclass(frozen=True)
class CostModel:
    trade_bps: float = 5.0  # per 1.0 of exposure changed
    fin_spread: float = 0.0040  # annual spread over T-bill on borrowed exposure (L - 1)
    letf_fee: float = 0.0095  # annual fee on the leveraged-ETF sleeve
    letf_multiple: float = 3.0  # sleeve weight = (L - 1) / (multiple - 1)
    cash_spread: float = 0.0010  # annual haircut on idle cash vs T-bill

    def with_(self, **kw) -> "CostModel":
        return replace(self, **kw)


LETF_COSTS = CostModel()
FUTURES_COSTS = CostModel(trade_bps=3.0, fin_spread=0.0030, letf_fee=0.0)


def simulate(
    target: pd.Series,
    r: pd.Series,
    rf: pd.Series,
    costs: CostModel = LETF_COSTS,
    lag: int = 1,
    band: float = 0.20,
    cash_ret: pd.Series | None = None,
    extra_cost: pd.Series | None = None,
    trim: bool = True,
) -> pd.DataFrame:
    """Simulate a strategy whose desired exposure, decided at each close, is `target`.

    The decision made at the close of day t is executed at the close of day t + lag and is held
    over the next day's return. Execution only happens when the desired exposure differs from the
    current position by at least `band` (or the desire is to go flat).
    """
    idx = r.index
    d = target.reindex(idx).to_numpy(dtype=float)
    rr = r.to_numpy(dtype=float)
    rfa = rf.reindex(idx).shift(1).bfill().to_numpy(dtype=float)
    cash = (rfa - costs.cash_spread / TRADING_DAYS) if cash_ret is None else cash_ret.reindex(idx).fillna(0.0).to_numpy(dtype=float)
    xc = np.zeros(len(idx)) if extra_cost is None else extra_cost.reindex(idx).fillna(0.0).to_numpy(dtype=float)

    n = len(idx)
    pos = np.zeros(n)  # position after the close of day t
    cur = 0.0
    for t in range(n):
        j = t - lag
        want = d[j] if j >= 0 and np.isfinite(d[j]) else 0.0
        want = max(want, 0.0)
        if (want == 0.0 and cur != 0.0) or abs(want - cur) >= band - 1e-12:
            cur = want
        pos[t] = cur

    held = np.concatenate([[0.0], pos[:-1]])  # exposure during day t's return
    turnover = np.abs(np.diff(np.concatenate([[0.0], pos])))
    gross = held * rr
    levered = np.maximum(held - 1.0, 0.0)
    unlevered_cash = np.maximum(1.0 - held, 0.0)
    financing = -levered * (rfa + costs.fin_spread / TRADING_DAYS)
    cash_income = unlevered_cash * cash
    sleeve = levered / max(costs.letf_multiple - 1.0, 1e-9) if costs.letf_fee > 0 else 0.0 * levered
    fee = -costs.letf_fee / TRADING_DAYS * sleeve
    tcost = -costs.trade_bps / 1e4 * turnover
    ret = gross + financing + cash_income + fee + tcost - xc

    out = pd.DataFrame(
        {
            "ret": ret,
            "gross": gross,
            "exposure": held,
            "position": pos,
            "turnover": turnover,
            "financing": financing,
            "cash_income": cash_income,
            "fee": fee,
            "tcost": tcost,
        },
        index=idx,
    )
    if trim:
        first = target.first_valid_index()
        if first is not None:
            start = idx.searchsorted(first) + lag + 1
            out = out.iloc[min(start, n - 1):]
    return out


def buy_and_hold(r: pd.Series, rf: pd.Series, multiple: float = 1.0, costs: CostModel = LETF_COSTS) -> pd.DataFrame:
    """Constant exposure, rebalanced daily (multiple > 1 behaves like a daily-reset leveraged ETF)."""
    tgt = pd.Series(multiple, index=r.index)
    out = simulate(tgt, r, rf, costs=costs, lag=0, band=0.0, trim=False)
    return out.iloc[1:]


def equity(ret: pd.Series, start: float = 1.0) -> pd.Series:
    return start * (1.0 + ret).cumprod()
