"""The options strategies O1-O12 (desk/options/strategies.py): Inputs, build_inputs, the strategies, the
overlays and their decision rules.

Source: cursor2 main @ca8ac1f650670e1d1a8344d21cff8dd9f0ba4448. Each block after a `# >>> excerpt` marker is the exact text of that
source line range (the marker carries its sha256; tests/test_apex.py re-hashes every block)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import strategies as S
from .engine import LETF_COSTS, simulate
from .series import Market
from .sim import Book, OptionCosts
from .surface import Surface


# >>> excerpt desk/options/strategies.py lines 17-361 blob 5764b8b82e5b3729525ca49f973dc3813f421fa5 sha256 797e0244c7fba2986eb52a9bbc2eb29ab3f54919a4fedea92157d215bdaefe19
@dataclass
class Inputs:
    """Signals and series aligned on the option calendar; every array is read at t-1 by the strategies."""

    dates: pd.DatetimeIndex
    S: np.ndarray  # option underlying price
    r: np.ndarray  # annual risk-free rate
    rf_daily: np.ndarray
    tr: np.ndarray  # underlying total-return daily return
    trend: np.ndarray
    vol: np.ndarray
    L: np.ndarray  # APEX-50F target exposure
    dd252: np.ndarray
    vol30: np.ndarray
    vol30_p80: np.ndarray
    hi10_prior: np.ndarray
    level: np.ndarray
    apex_ret: np.ndarray
    month_start: np.ndarray
    div: float


def build_inputs(m: Market, price: pd.Series, surface: Surface, div: float) -> Inputs:
    sig = S.compute_signals(m)
    idx = m.index
    L = S.apex_target(sig, S.APEX_50F)
    apex = S.run(L, m, S.APEX_50F)["ret"].reindex(idx).fillna(0.0)
    level = sig.level
    dd = level / level.rolling(252, min_periods=252).max() - 1.0
    v30 = surface.vol30.reindex(idx)
    p80 = v30.rolling(252, min_periods=252).quantile(0.80)
    hi10 = level.shift(1).rolling(10, min_periods=10).max()
    ms = pd.Series(idx.month, index=idx)
    month_start = (ms != ms.shift(1)).to_numpy()
    rf_annual = (m.rf * 252).to_numpy()
    return Inputs(dates=idx, S=price.reindex(idx).ffill().to_numpy(), r=rf_annual, rf_daily=m.rf.to_numpy(), tr=m.r.to_numpy(),
                  trend=sig.trend.to_numpy(), vol=sig.vol.to_numpy(), L=L.to_numpy(), dd252=dd.to_numpy(),
                  vol30=v30.to_numpy(), vol30_p80=p80.to_numpy(), hi10_prior=hi10.to_numpy(), level=level.to_numpy(),
                  apex_ret=apex.to_numpy(), month_start=month_start, div=div)


def _nav0(book: Book) -> float:
    return book.nav()


# ---------------------------------------------------------------- O1 CONVEX
def o1_convex(x: Inputs, m: Market, surface: Surface, costs: OptionCosts, start: int) -> pd.DataFrame:
    core_tgt = pd.Series(np.minimum(x.L, 1.0), index=x.dates)
    core = simulate(core_tgt, m.r, m.rf, costs=LETF_COSTS, lag=1, band=0.2, trim=False)["ret"].to_numpy()
    book = Book(x.dates, x.S, x.r, surface, core, x.div, costs)

    def decide(b: Book, t: int) -> None:
        Lp = x.L[t - 1]
        if not np.isfinite(Lp):
            return
        nav = b.nav()
        want = max(Lp - 1.0, 0.0)
        have = b.delta_exposure(t, "call") / nav if b.legs else 0.0
        if x.month_start[t] or abs(want - have) >= 0.5:
            b.close_tag(t, "call")
            if want > 0:
                e = b.expiry_near(t, 91, 45)
                K = b.S[t]
                _, d, _, _ = b.quote(t, True, K, e)
                if d > 0.05:
                    b.open(t, True, K, e, want * b.nav() / (d * b.S[t]), "call")

    return book.run(decide, start)


# ---------------------------------------------------------------- O2 LEAPS-APEX
def o2_leaps(x: Inputs, surface: Surface, costs: OptionCosts, start: int) -> pd.DataFrame:
    book = Book(x.dates, x.S, x.r, surface, x.rf_daily, x.div, costs)

    def decide(b: Book, t: int) -> None:
        Lp = x.L[t - 1]
        if not np.isfinite(Lp):
            return
        nav = b.nav()
        legs = b.legs_with("leap")
        have = b.delta_exposure(t, "leap") / nav if legs else 0.0
        days_left = min((b.exp_date(l.exp_i) - b.dates[t]).days for l in legs) if legs else 9999
        roll = legs and days_left < 183
        if Lp <= 0:
            b.close_tag(t, "leap")
            return
        if not legs or roll or abs(Lp - have) >= 0.5:
            b.close_tag(t, "leap")
            e = b.expiry_near(t, 365, 300)
            K = b.strike_for_delta(t, e, 0.80, True)
            _, d, _, _ = b.quote(t, True, K, e)
            b.open(t, True, K, e, Lp * b.nav() / (max(d, 0.5) * b.S[t]), "leap")

    return book.run(decide, start)


# ---------------------------------------------------------------- O3 REGIME PUT-WRITE
def o3_putwrite(x: Inputs, surface: Surface, costs: OptionCosts, start: int) -> pd.DataFrame:
    book = Book(x.dates, x.S, x.r, surface, x.rf_daily, x.div, costs)

    def decide(b: Book, t: int) -> None:
        Lp = x.L[t - 1]
        if not np.isfinite(Lp):
            return
        if Lp <= 0:
            b.close_tag(t, "put")
            return
        if x.month_start[t] and not b.legs_with("put"):
            e = b.next_expiry(t, 15)
            T = b.T_years(t, b.exp_date(e))
            sig = b.atm_iv(t, e)
            K = b.S[t] * np.exp(-0.5 * sig * np.sqrt(T))
            b.open(t, False, K, e, -min(Lp, 3.0) * b.nav() / b.S[t], "put")

    return book.run(decide, start)


# ---------------------------------------------------------------- overlays on APEX-50F
def _phoenix(b: Book, x: Inputs, t: int) -> None:
    legs = b.legs_with("phx")
    if legs:
        if (b.exp_date(legs[0].exp_i) - b.dates[t]).days <= 30:  # ~21 trading days
            b.close_tag(t, "phx")
        return
    p = t - 1
    if not (np.isfinite(x.dd252[p]) and np.isfinite(x.vol30_p80[p]) and np.isfinite(x.hi10_prior[p])):
        return
    if x.dd252[p] <= -0.15 and x.vol30[p] >= x.vol30_p80[p] and x.level[p] >= x.hi10_prior[p]:
        e = b.expiry_near(t, 91, 60)
        K = b.S[t]
        px, _, _, _ = b.quote(t, True, K, e)
        if px > 0:
            b.open(t, True, K, e, 0.05 * b.nav() / px, "phx")


def _chop(b: Book, x: Inputs, t: int) -> None:
    if not x.month_start[t] or b.legs_with("chop"):
        return
    T6 = round(x.trend[t - 1] * 6) if np.isfinite(x.trend[t - 1]) else -1
    if T6 not in (2, 3, 4):
        return
    e = b.next_expiry(t, 15)
    T = b.T_years(t, b.exp_date(e))
    sig = b.atm_iv(t, e)
    s, units = b.S[t], b.nav() / b.S[t]
    w = sig * np.sqrt(T)
    b.open(t, True, s * np.exp(1.0 * w), e, -units, "chop")
    b.open(t, False, s * np.exp(-1.0 * w), e, -units, "chop")
    b.open(t, True, s * np.exp(2.0 * w), e, units, "chop")
    b.open(t, False, s * np.exp(-2.0 * w), e, units, "chop")


def _fear(b: Book, x: Inputs, t: int) -> None:
    if not x.month_start[t] or b.legs_with("fear"):
        return
    p = t - 1
    if not (np.isfinite(x.vol30_p80[p]) and np.isfinite(x.trend[p])):
        return
    if x.vol30[p] >= x.vol30_p80[p] and round(x.trend[p] * 6) <= 2:
        e = b.expiry_near(t, 61, 45)
        units = b.nav() / b.S[t]
        b.open(t, False, 0.90 * b.S[t], e, -units, "fear")
        b.open(t, False, 0.80 * b.S[t], e, units, "fear")


def overlay(x: Inputs, surface: Surface, costs: OptionCosts, start: int, sleeves: tuple[str, ...]) -> pd.DataFrame:
    book = Book(x.dates, x.S, x.r, surface, x.apex_ret, x.div, costs)
    fns = {"phoenix": _phoenix, "chop": _chop, "fear": _fear, "vv": _variance_value}

    def decide(b: Book, t: int) -> None:
        for s in sleeves:
            fns[s](b, x, t)

    return book.run(decide, start)


# ---------------------------------------------------------------- overlays on a QQQ core
def _variance_value(b: Book, x: Inputs, t: int) -> None:
    if not x.month_start[t] or b.legs_with("vv") or not np.isfinite(x.vol[t - 1]):
        return
    e = b.next_expiry(t, 15)
    T = b.T_years(t, b.exp_date(e))
    sig = b.atm_iv(t, e)
    ratio = sig / x.vol[t - 1]
    s = b.S[t]
    if ratio >= 1.25:
        units = b.nav() / s
        w = 1.5 * sig * np.sqrt(T)
        b.open(t, True, s, e, -units, "vv")
        b.open(t, False, s, e, -units, "vv")
        b.open(t, True, s * np.exp(w), e, units, "vv")
        b.open(t, False, s * np.exp(-w), e, units, "vv")
    elif ratio <= 0.95:
        c, _, _, _ = b.quote(t, True, s, e)
        p, _, _, _ = b.quote(t, False, s, e)
        units = 0.02 * b.nav() / (c + p)
        b.open(t, True, s, e, units, "vv")
        b.open(t, False, s, e, units, "vv")


def o6_variance_value(x: Inputs, surface: Surface, costs: OptionCosts, start: int) -> pd.DataFrame:
    book = Book(x.dates, x.S, x.r, surface, x.tr, x.div, costs)
    return book.run(lambda b, t: _variance_value(b, x, t), start)


# ---------------------------------------------------------------- v2: incremental execution
def _leaps_book(b: Book, x: Inputs, t: int, tag: str = "leap") -> None:
    Lp = x.L[t - 1]
    if not np.isfinite(Lp):
        return
    legs = b.legs_with(tag)
    if Lp <= 0:
        b.close_tag(t, tag)
        return
    nav = b.nav()
    s = b.S[t]
    if legs:
        leg = legs[0]
        _, d, _, _ = b.quote(t, True, leg.K, leg.exp_i)
        if (b.exp_date(leg.exp_i) - b.dates[t]).days < 183 or not (0.60 <= d <= 0.95):
            b.close_tag(t, tag)
            legs = []
    if not legs:
        e = b.expiry_near(t, 365, 300)
        K = b.strike_for_delta(t, e, 0.80, True)
        px, d, _, _ = b.quote(t, True, K, e)
        nav = b.nav()
        units = min(Lp * nav / (d * s), 0.995 * nav / px)
        b.open(t, True, K, e, units, tag)
        return
    leg = legs[0]
    px, d, _, _ = b.quote(t, True, leg.K, leg.exp_i)
    have = leg.units * d * s / nav
    if abs(Lp - have) >= 0.5:
        target = min(Lp * nav / (d * s), 0.995 * nav / px)
        b.adjust(t, leg, target - leg.units)


def o2b_leaps(x: Inputs, surface: Surface, costs: OptionCosts, start: int, with_variance_value: bool = False) -> pd.DataFrame:
    book = Book(x.dates, x.S, x.r, surface, x.rf_daily, x.div, costs)

    def decide(b: Book, t: int) -> None:
        _leaps_book(b, x, t)
        if with_variance_value:
            _variance_value(b, x, t)

    return book.run(decide, start)


def o1b_convex(x: Inputs, m: Market, surface: Surface, costs: OptionCosts, start: int) -> pd.DataFrame:
    core_tgt = pd.Series(np.minimum(x.L, 1.0), index=x.dates)
    core = simulate(core_tgt, m.r, m.rf, costs=LETF_COSTS, lag=1, band=0.2, trim=False)["ret"].to_numpy()
    book = Book(x.dates, x.S, x.r, surface, core, x.div, costs)

    def decide(b: Book, t: int) -> None:
        Lp = x.L[t - 1]
        if not np.isfinite(Lp):
            return
        want = max(Lp - 1.0, 0.0)
        legs = b.legs_with("call")
        s = b.S[t]
        if legs:
            leg = legs[0]
            _, d, _, _ = b.quote(t, True, leg.K, leg.exp_i)
            if (b.exp_date(leg.exp_i) - b.dates[t]).days < 45 or not (0.30 <= d <= 0.85):
                b.close_tag(t, "call")
                legs = []
        nav = b.nav()
        if not legs:
            if want >= 0.5:
                e = b.expiry_near(t, 91, 60)
                px, d, _, _ = b.quote(t, True, s, e)
                b.open(t, True, s, e, min(want * nav / (d * s), 0.995 * nav / px), "call")
            return
        leg = legs[0]
        px, d, _, _ = b.quote(t, True, leg.K, leg.exp_i)
        have = leg.units * d * s / nav
        if abs(want - have) >= 0.5:
            target = min(want * nav / (d * s), 0.995 * nav / px) if want > 0 else 0.0
            b.adjust(t, leg, target - leg.units)

    return book.run(decide, start)


def o7_skew_rr(x: Inputs, surface: Surface, costs: OptionCosts, start: int) -> pd.DataFrame:
    book = Book(x.dates, x.S, x.r, surface, x.tr, x.div, costs)

    def decide(b: Book, t: int) -> None:
        p = t - 1
        if not np.isfinite(x.trend[p]):
            return
        if b.legs_with("rr") and x.trend[p] < 4 / 6 - 1e-9:
            b.close_tag(t, "rr")
            return
        if x.month_start[t] and not b.legs_with("rr") and x.trend[p] >= 5 / 6 - 1e-9 and x.vol[p] < 0.25:
            e = b.next_expiry(t, 15)
            units = 2.0 * b.nav() / b.S[t]
            Kp = b.strike_for_delta(t, e, -0.25, False)
            Kc = b.strike_for_delta(t, e, 0.25, True)
            b.open(t, False, Kp, e, -units, "rr")
            b.open(t, True, Kc, e, units, "rr")

    return book.run(decide, start)


# ---------------------------------------------------------------- v3: convex base + futures trim
def o12_hybrid(x: Inputs, surface: Surface, costs: OptionCosts, start: int, fut_bps: float = 3.0,
               fin_spread: float = 0.003, band: float = 0.2, base_share: float = 0.75) -> pd.DataFrame:
    book = Book(x.dates, x.S, x.r, surface, x.rf_daily, x.div, costs)
    state = {"fut": 0.0, "wait_month": False}

    def decide(b: Book, t: int) -> None:
        fe = state["fut"]
        if fe != 0.0:
            b.core += fe * b.nav_prev * (x.tr[t] - x.rf_daily[t]) - max(fe, 0.0) * b.nav_prev * fin_spread / 252
        Lp = x.L[t - 1]
        if not np.isfinite(Lp):
            return
        s = b.S[t]
        legs = b.legs_with("base")
        if legs:
            leg = legs[0]
            _, d, _, _ = b.quote(t, True, leg.K, leg.exp_i)
            if Lp <= 0:
                b.close_tag(t, "base")
                state["wait_month"] = True
                legs = []
            elif (b.exp_date(leg.exp_i) - b.dates[t]).days < 183 or not (0.60 <= d <= 0.95):
                b.close_tag(t, "base")
                legs = []
        if not legs and Lp > 0 and (not state["wait_month"] or x.month_start[t]):
            e = b.expiry_near(t, 365, 300)
            K = b.strike_for_delta(t, e, 0.80, True)
            px, d, _, _ = b.quote(t, True, K, e)
            nav = b.nav()
            b.open(t, True, K, e, min(base_share * Lp * nav / (d * s), 0.995 * nav / px), "base")
            state["wait_month"] = False
        nav = b.nav()
        opt_exp = b.delta_exposure(t, "base") / nav if b.legs_with("base") else 0.0
        want = (Lp - opt_exp) if Lp > 0 else 0.0
        if abs(want - fe) >= band - 1e-12 or (want == 0.0 and fe != 0.0):
            b.core -= fut_bps / 1e4 * abs(want - fe) * nav
            state["fut"] = want

    return book.run(decide, start)
