"""APEX-NDX v1.0 (desk/strategies.py): ApexParams, the signals, apex_target, run, the core variants and the
extensions E1-E7, APEX-50F and v1.1.

Source: cursor2 main @ca8ac1f650670e1d1a8344d21cff8dd9f0ba4448. Each block after a `# >>> excerpt` marker is the exact text of that
source line range (the marker carries its sha256; tests/test_apex.py re-hashes every block)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..aurelia import features as F
from .engine import FUTURES_COSTS, LETF_COSTS, CostModel, buy_and_hold, simulate
from .backtest_options import tail_hedge_overlay
from .series import Market


# >>> excerpt desk/strategies.py lines 16-161 blob ab1a0058691d77e14ffebe7293e9cd73fd74f3ee sha256 b67cb41dbb3f753ec1d36f67c7b1c948505e6a0eba59ce6590c3f509c823ad1f
@dataclass(frozen=True)
class ApexParams:
    sigma_target: float = 0.30
    l_max: float = 3.0
    vol_power: float = 1.0
    band: float = 0.20
    lag: int = 1
    costs: CostModel = LETF_COSTS


FLAGSHIP = ApexParams()


@dataclass
class Signals:
    level: pd.Series
    trend: pd.Series
    vol: pd.Series
    sma200: pd.Series


def compute_signals(m: Market) -> Signals:
    level = m.level
    return Signals(level=level, trend=F.trend_score(level), vol=F.har_vol_forecast(m.r), sma200=F.sma_signal(level, 200))


def apex_target(sig: Signals, p: ApexParams = FLAGSHIP) -> pd.Series:
    scale = np.minimum(p.l_max, (p.sigma_target / sig.vol) ** p.vol_power)
    return (sig.trend * scale).rename("target")


def run(target: pd.Series, m: Market, p: ApexParams = FLAGSHIP, **kw) -> pd.DataFrame:
    return simulate(target, m.r, m.rf, costs=p.costs, lag=p.lag, band=p.band, **kw)


def core_variants(m: Market, sig: Signals) -> dict[str, pd.DataFrame]:
    """Every pre-registered core variant, trimmed to a common start once all signals are warm."""
    out: dict[str, pd.DataFrame] = {
        "QQQ": buy_and_hold(m.r, m.rf, 1.0),
        "BH2": buy_and_hold(m.r, m.rf, 2.0),
        "BH3": buy_and_hold(m.r, m.rf, 3.0),
        "SMA200-1x": run(sig.sma200 * 1.0, m),
        "SMA200-3x": run(sig.sma200 * 3.0, m),
        "TREND-1x": run(sig.trend * 1.0, m),
        "TREND-3x": run(sig.trend * 3.0, m),
        "VOL-3x": run(np.minimum(3.0, 0.30 / sig.vol).where(sig.trend.notna()), m),
        "APEX-20": run(apex_target(sig, ApexParams(sigma_target=0.20, l_max=2.0)), m),
        "APEX-25": run(apex_target(sig, ApexParams(sigma_target=0.25, l_max=2.5)), m),
        "APEX-30": run(apex_target(sig, FLAGSHIP), m),
        "APEX-40": run(apex_target(sig, ApexParams(sigma_target=0.40, l_max=3.0)), m),
        "APEX-50F": run(apex_target(sig, ApexParams(sigma_target=0.50, l_max=4.0, costs=FUTURES_COSTS)), m,
                        ApexParams(sigma_target=0.50, l_max=4.0, costs=FUTURES_COSTS)),
        "APEX-K": run(apex_target(sig, ApexParams(sigma_target=0.25, l_max=3.0, vol_power=2.0)), m),
    }
    start = max(df.index[0] for df in out.values())
    return {k: v[v.index >= start] for k, v in out.items()}


# ---------------------------------------------------------------- extensions (E1-E7)

def e1_vix_term_structure(m: Market, sig: Signals, vix: pd.Series, vix3m: pd.Series) -> pd.DataFrame:
    ratio = (vix / vix3m).reindex(m.index)
    mult = pd.Series(1.0, index=m.index).where(~(ratio > 1.0), 0.5)
    return run(apex_target(sig) * mult, m)


def e2_dip_overlay(m: Market, sig: Signals) -> pd.DataFrame:
    gate = sig.trend >= 0.5
    dip = F.double7_state(sig.level, gate)
    tgt = np.minimum(FLAGSHIP.l_max, apex_target(sig) + 0.5 * dip)
    return run(tgt.where(sig.trend.notna()), m)


def bond_trend(bond_r: pd.Series, index: pd.DatetimeIndex) -> pd.Series:
    """1.0 when the 7-10y Treasury total-return level is above its 200-day average."""
    bond_level = (1.0 + bond_r.reindex(index).fillna(0.0)).cumprod()
    return (bond_level > bond_level.rolling(200).mean()).astype(float).rename("bond_trend")


def e3_defensive_bonds(m: Market, sig: Signals, bond_r: pd.Series, p: ApexParams = FLAGSHIP) -> pd.DataFrame:
    on_held = bond_trend(bond_r, m.index).shift(p.lag + 1).fillna(0.0)
    rf_cash = m.rf.shift(1).bfill() - p.costs.cash_spread / 252
    cash_ret = on_held * bond_r.reindex(m.index).fillna(0.0) + (1 - on_held) * rf_cash
    base = run(apex_target(sig, p), m, p)
    idle = (1.0 - base["exposure"]).clip(lower=0.0)
    switch_cost = p.costs.trade_bps / 1e4 * idle * on_held.diff().abs().reindex(base.index).fillna(0.0)
    return run(apex_target(sig, p), m, p, cash_ret=cash_ret, extra_cost=switch_cost)


APEX_50F = ApexParams(sigma_target=0.50, l_max=4.0, costs=FUTURES_COSTS)
APEX_V11 = ApexParams(sigma_target=0.50, l_max=4.0, costs=FUTURES_COSTS, band=0.50)


def apex_v11(m: Market, sig: Signals, bond_r: pd.Series) -> pd.DataFrame:
    """v1.1 candidate: APEX-50F + defensive Treasuries (E3) + 0.50 rebalance band."""
    return e3_defensive_bonds(m, sig, bond_r, APEX_V11)


def e4_tail_hedge(m: Market, sig: Signals, iv_atm: pd.Series, spread: float = 0.05) -> pd.DataFrame:
    base = run(apex_target(sig), m)
    rf_annual = (m.rf * 252).reindex(base.index)
    hedged = tail_hedge_overlay(base["ret"], base["position"], sig.level.reindex(base.index), iv_atm, rf_annual,
                                spread=spread)
    out = base.copy()
    out["ret"] = hedged["ret"]
    out["hedge_pnl"] = hedged["hedge_pnl"]
    out["premium"] = hedged["premium"]
    return out


def e5_semis_tilt(m: Market, sig: Signals, smh_r: pd.Series) -> pd.DataFrame:
    smh_r = smh_r.reindex(m.index)
    smh_level = (1.0 + smh_r.fillna(0.0)).cumprod().where(smh_r.notna().cummax())
    rel = (smh_level / smh_level.shift(126)) > (sig.level / sig.level.shift(126))
    up = smh_level > smh_level.rolling(200).mean()
    flag = (rel & up).astype(float).where(smh_level.shift(200).notna(), 0.0)
    share = (flag / 3.0).shift(FLAGSHIP.lag + 1).fillna(0.0)
    blended = (1 - share) * m.r + share * smh_r.fillna(m.r)
    base = run(apex_target(sig), Market(r=blended, rf=m.rf, name="NDX+SMH"))
    switch_cost = FLAGSHIP.costs.trade_bps / 1e4 * base["exposure"] * share.diff().abs().reindex(base.index).fillna(0.0)
    out = base.copy()
    out["ret"] = base["ret"] - switch_cost
    out["semis_share"] = share.reindex(base.index)
    return out


def e6_overnight_boost(m: Market, sig: Signals, qqq_oc: pd.DataFrame, bps_per_side: float = 3.0) -> pd.DataFrame:
    base = run(apex_target(sig), m)
    oc = qqq_oc.reindex(base.index)
    r_on = (oc["open"] / oc["close"].shift(1) - 1.0).fillna(0.0)
    boost = (sig.trend.shift(FLAGSHIP.lag + 1) >= 0.5).astype(float).reindex(base.index).fillna(0.0)
    boost = boost.where(oc["open"].notna() & oc["close"].shift(1).notna(), 0.0)
    fin = (m.rf.shift(1).bfill().reindex(base.index) + FLAGSHIP.costs.fin_spread / 252)
    extra = boost * (r_on - fin - 2 * bps_per_side / 1e4)
    out = base.copy()
    out["ret"] = base["ret"] + extra
    out["boost"] = boost
    return out


def e7_turn_of_month(m: Market, sig: Signals) -> pd.DataFrame:
    tom = F.turn_of_month_window(m.index)
    ahead = tom.shift(-(FLAGSHIP.lag + 1)).fillna(0.0)
    boost = 0.5 * ahead * (sig.trend >= 0.5).astype(float)
    tgt = np.minimum(FLAGSHIP.l_max, apex_target(sig) + boost)
    return run(tgt.where(sig.trend.notna()), m)
