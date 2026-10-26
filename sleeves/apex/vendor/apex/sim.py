"""The daily options book simulator (desk/options/sim.py): Leg, OptionCosts, monthly expiries, Book.

Source: cursor2 main @ca8ac1f650670e1d1a8344d21cff8dd9f0ba4448. Each block after a `# >>> excerpt` marker is the exact text of that
source line range (the marker carries its sha256; tests/test_apex.py re-hashes every block)."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import bs
from .surface import Surface


# >>> excerpt desk/options/sim.py lines 14-192 blob 43288f98876061726ee509b553f33481d360f8d5 sha256 45af960d2e527c7df702539e74049c7787816b37457346e8a6fe98afef2eb224
@dataclass
class Leg:
    is_call: bool
    K: float
    exp_i: int
    units: float  # >0 long, <0 short, in units of the underlying
    px: float
    tag: str


@dataclass
class OptionCosts:
    fee_per_unit: float = 0.0002  # ~$0.02 per 100-share contract
    min_pct: float = 0.0075
    mult: float = 1.0

    def spread_vp(self, date: pd.Timestamp, abs_delta: float) -> float:
        base = 1.0 if date.year <= 2007 else 0.5 if date.year <= 2015 else 0.3
        return base * (2.0 if abs_delta < 0.15 else 1.0) * self.mult


def monthly_expiries(dates: pd.DatetimeIndex) -> np.ndarray:
    """Trading-day index of each month's third Friday (previous trading day if it was a holiday)."""
    out = []
    months = pd.period_range(dates[0], dates[-1] + pd.offsets.MonthEnd(15), freq="M")
    for p in months:
        first = pd.Timestamp(p.start_time)
        tf = first + pd.Timedelta(days=(4 - first.weekday()) % 7 + 14)
        out.append(tf)
    out = pd.DatetimeIndex(out)
    return out


@dataclass
class Book:
    dates: pd.DatetimeIndex
    S: np.ndarray
    r: np.ndarray
    surface: Surface
    core_ret: np.ndarray
    div: float = 0.0055
    costs: OptionCosts = field(default_factory=OptionCosts)

    def __post_init__(self):
        self.legs: list[Leg] = []
        self.core = 1.0
        self.nav_prev = 1.0
        self.expiry_dates = monthly_expiries(self.dates)
        self.cost_paid = 0.0
        self.premium_net = 0.0
        self._t = 0

    # ---------------------------------------------------------------- pricing helpers
    def T_years(self, t: int, exp_date: pd.Timestamp) -> float:
        return max((exp_date - self.dates[t]).days + 0.25, 0.0) / 365.0

    def exp_date(self, exp_i: int) -> pd.Timestamp:
        return self.expiry_dates[exp_i]

    def forward(self, t: int, T: float) -> float:
        return self.S[t] * np.exp((self.r[t] - self.div) * T)

    def quote(self, t: int, is_call: bool, K: float, exp_i: int) -> tuple[float, float, float, float]:
        """(price, delta, vega_per_vol_point, iv) for one contract-unit."""
        T = self.T_years(t, self.exp_date(exp_i))
        if T <= 0:
            intrinsic = max(self.S[t] - K, 0.0) if is_call else max(K - self.S[t], 0.0)
            return intrinsic, 0.0, 0.0, 0.0
        F = self.forward(t, T)
        iv = float(self.surface.iv(t, np.array([K]), np.array([F]), np.array([T]))[0])
        px = float(bs.price(self.S[t], K, T, self.r[t], self.div, iv, is_call))
        d = float(bs.delta(self.S[t], K, T, self.r[t], self.div, iv, is_call))
        v = float(bs.vega(self.S[t], K, T, self.r[t], self.div, iv)) / 100.0
        return px, d, v, iv

    def atm_iv(self, t: int, exp_i: int) -> float:
        T = self.T_years(t, self.exp_date(exp_i))
        F = self.forward(t, T)
        return float(self.surface.iv(t, np.array([F]), np.array([F]), np.array([T]))[0])

    def expiry_near(self, t: int, days: int, min_days: int = 0) -> int:
        """Index into expiry_dates of the monthly expiry closest to `days` calendar days ahead (and >= min_days)."""
        d0 = self.dates[t]
        gaps = np.array([(e - d0).days for e in self.expiry_dates])
        ok = np.where(gaps >= max(min_days, 1))[0]
        return int(ok[np.argmin(np.abs(gaps[ok] - days))])

    def next_expiry(self, t: int, min_days: int = 15) -> int:
        d0 = self.dates[t]
        gaps = np.array([(e - d0).days for e in self.expiry_dates])
        return int(np.where(gaps >= min_days)[0][0])

    def strike_for_delta(self, t: int, exp_i: int, target: float, is_call: bool) -> float:
        T = self.T_years(t, self.exp_date(exp_i))
        sig = self.atm_iv(t, exp_i)
        K = bs.strike_for_delta(target, self.S[t], T, self.r[t], self.div, sig, is_call)
        for _ in range(3):
            F = self.forward(t, T)
            sig = float(self.surface.iv(t, np.array([K]), np.array([F]), np.array([T]))[0])
            K = bs.strike_for_delta(target, self.S[t], T, self.r[t], self.div, sig, is_call)
        return K

    # ---------------------------------------------------------------- trading
    def _cost(self, t: int, px: float, d: float, v: float, units: float) -> float:
        half = max(self.costs.spread_vp(self.dates[t], abs(d)) * v, self.costs.min_pct * px)
        return abs(units) * (half + self.costs.fee_per_unit)

    def open(self, t: int, is_call: bool, K: float, exp_i: int, units: float, tag: str) -> Leg | None:
        if units == 0 or not np.isfinite(units):
            return None
        px, d, v, _ = self.quote(t, is_call, K, exp_i)
        c = self._cost(t, px, d, v, units)
        self.core -= units * px + c
        self.cost_paid += c
        self.premium_net -= units * px
        leg = Leg(is_call, K, exp_i, units, px, tag)
        self.legs.append(leg)
        return leg

    def close(self, t: int, leg: Leg) -> None:
        px, d, v, _ = self.quote(t, leg.is_call, leg.K, leg.exp_i)
        c = self._cost(t, px, d, v, leg.units)
        self.core += leg.units * px - c
        self.cost_paid += c
        self.legs.remove(leg)

    def adjust(self, t: int, leg: Leg, delta_units: float) -> None:
        """Trade only `delta_units` of an existing contract (no re-strike)."""
        if delta_units == 0 or not np.isfinite(delta_units):
            return
        px, d, v, _ = self.quote(t, leg.is_call, leg.K, leg.exp_i)
        c = self._cost(t, px, d, v, delta_units)
        self.core -= delta_units * px + c
        self.cost_paid += c
        leg.units += delta_units
        leg.px = px
        if abs(leg.units) < 1e-12:
            self.legs.remove(leg)

    def close_tag(self, t: int, tag: str) -> None:
        for leg in [l for l in self.legs if l.tag == tag]:
            self.close(t, leg)

    def legs_with(self, tag: str) -> list[Leg]:
        return [l for l in self.legs if l.tag == tag]

    def delta_exposure(self, t: int, tag: str) -> float:
        tot = 0.0
        for l in self.legs_with(tag):
            _, d, _, _ = self.quote(t, l.is_call, l.K, l.exp_i)
            tot += l.units * d * self.S[t]
        return tot

    def nav(self) -> float:
        return self.core + sum(l.units * l.px for l in self.legs)

    # ---------------------------------------------------------------- daily loop
    def run(self, decide, start: int) -> pd.DataFrame:
        n = len(self.dates)
        rows = np.zeros((n, 4))
        for t in range(start, n):
            self._t = t
            self.core *= 1.0 + self.core_ret[t]
            today = self.dates[t]
            for leg in list(self.legs):
                exp_day = self.exp_date(leg.exp_i)
                if exp_day <= today:
                    intrinsic = max(self.S[t] - leg.K, 0.0) if leg.is_call else max(leg.K - self.S[t], 0.0)
                    self.core += leg.units * intrinsic
                    self.legs.remove(leg)
                else:
                    leg.px = self.quote(t, leg.is_call, leg.K, leg.exp_i)[0]
            decide(self, t)
            nav = self.nav()
            rows[t] = (nav, nav / self.nav_prev - 1.0, sum(l.units * l.px for l in self.legs) / nav if nav else 0.0, len(self.legs))
            self.nav_prev = nav
        df = pd.DataFrame(rows, index=self.dates, columns=["nav", "ret", "opt_weight", "n_legs"]).iloc[start:]
        df.attrs["cost_paid"] = self.cost_paid
        return df
