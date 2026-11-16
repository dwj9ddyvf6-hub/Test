"""risk_lots — the ADAPTED half of Sol's portfolio.py (PORT-SPEC
section 4): RiskConfig values verbatim, lot/scale/stop math
re-expressed as pure functions over desk fill truth (Ink ledger
rows + broker position). No SQLite, no reservation database, no
broker access. Every equity-relative quantity is re-based on
the sleeve's virtual slice equity — the single sanctioned
adaptation; the fractions, caps and R arithmetic are his.

Sizing law (spec sections 4-5):
  session R        = risk_fraction x session-start slice equity E0
  per-entry budget = risk_fraction x min(E, E0) x risk_multiplier
  unit risk        = |entry - stop| + 2 x fee_per_unit (fee 0.0)
  quantity         = floor(budget / unit risk), clipped by ALL
                     caps; quantity < 1 is a REJECTION recorded
                     by the caller — there is no forced 1-share
                     floor (the desk OBS-1 ruling agrees).
Caps: session loss 2R, entries/session 3, aggregate open risk
2R, correlation-group risk 1R (SPY sits in his U.S. large-cap
index group), aggregate notional 1.0 x equity, group notional
1.0 x equity. Add-ons disabled.
Lot law: each fill is its own lot; first scale sells 50% of the
initial lot quantity, later scales 25%; after a profitable
partial, the stop may tighten to fee-aware breakeven; after a
completed target stage the runner trails at 1.0 ATR. Stops
never loosen.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class RiskConfig:
    """Verbatim values from saty_system/portfolio.py RiskConfig
    (pinned config risk.* section)."""
    risk_fraction: float = 0.0025
    max_session_loss_r: float = 2.0
    max_entries_per_session: int = 3
    max_total_risk_r: float = 2.0
    max_correlation_risk_r: float = 1.0
    max_notional_fraction: float = 1.0
    max_correlation_notional_fraction: float = 1.0
    fee_per_unit: float = 0.0
    option_fee_per_contract: float = 0.65
    max_quote_age_seconds: float = 5.0
    order_lifetime_seconds: float = 30.0
    partial_fraction: float = 0.5
    second_partial_fraction: float = 0.25
    runner_atr_multiple: float = 1.0
    option_notional_basis: str = "gross"


RISK = RiskConfig()
CORRELATION_GROUP = "us_large_cap_index"  # SPY/SPX/SPXW/ES/MES (spec section 5)


def session_r(e0: float, cfg: RiskConfig = RISK) -> float:
    """The session's frozen R from session-start slice equity."""
    return cfg.risk_fraction * float(e0 or 0.0)


def unit_risk(entry: float, stop: float, cfg: RiskConfig = RISK) -> float:
    return abs(float(entry) - float(stop)) + 2.0 * cfg.fee_per_unit


def compute_qty(equity: float, e0: float, entry: float, stop: float,
                risk_multiplier: float = 1.0,
                open_risk_r: float = 0.0,
                open_notional: float = 0.0,
                entries_taken: int = 0,
                session_pnl_r: float = 0.0,
                cfg: RiskConfig = RISK):
    """(qty, reason). qty is an int share count; reason is None
    when qty >= 1, else the named refusal (the caller journals
    it — a zero is never silent). Caps are checked in source
    order: session loss, entry cap, then quantity caps."""
    e = float(equity or 0.0)
    base = float(e0 or 0.0)
    r_unit = session_r(base, cfg)
    if r_unit <= 0 or e <= 0:
        return 0, "risk_cap_r: no slice equity basis"
    if session_pnl_r <= -cfg.max_session_loss_r:
        return 0, "session_loss_halt"
    if entries_taken >= cfg.max_entries_per_session:
        return 0, "entry_cap_reached"
    ur = unit_risk(entry, stop, cfg)
    if ur <= 0:
        return 0, "risk_cap_r: zero unit risk"
    budget = cfg.risk_fraction * min(e, base) * float(risk_multiplier or 0.0)
    qty = math.floor(budget / ur)
    # aggregate open-risk cap (2R) and correlation-group cap (1R —
    # this sleeve's only group, so it binds first in effect)
    for cap_r, name in ((cfg.max_correlation_risk_r, "correlation"),
                        (cfg.max_total_risk_r, "aggregate")):
        room_r = cap_r - float(open_risk_r or 0.0)
        if room_r <= 0:
            return 0, f"risk_cap_r: {name} risk cap spent"
        qty = min(qty, math.floor(room_r * r_unit / ur))
    # notional caps (aggregate and group are both 1.0 x equity)
    for frac in (cfg.max_notional_fraction,
                 cfg.max_correlation_notional_fraction):
        room = frac * e - float(open_notional or 0.0)
        if room <= 0:
            return 0, "risk_cap_r: notional cap spent"
        qty = min(qty, math.floor(room / float(entry)))
    if qty < 1:
        return 0, "risk_cap_r: quantity rounds to zero"
    return int(qty), None


def admission_recheck(direction: int, entry_ref: float, stop: float,
                      targets, quote_price: float, atr: float,
                      cfg: RiskConfig = RISK,
                      max_chase_atr: float = 0.4,
                      max_adverse_gap_atr: float = 0.15,
                      minimum_net_reward_risk: float = 1.5,
                      round_trip_cost: float = 0.02):
    """Quote-admission recheck (spec section 2): at the actual
    executable price, the adverse gap and the chase must stay
    inside their ATR allowances, the stop must still be on the
    correct side, and net R to the NEAREST target after the
    round-trip cost must still clear the pinned floor.
    Returns (ok, reason)."""
    d = 1 if direction > 0 else -1
    if atr is None or atr <= 0 or quote_price <= 0:
        return False, "entry_window_closed: no valid quote price"
    adverse = d * (entry_ref - quote_price)  # >0 when price ran away
    if adverse > max_adverse_gap_atr * atr:
        return False, "entry_window_closed: adverse gap beyond 0.15 ATR"
    if abs(quote_price - entry_ref) > max_chase_atr * atr:
        return False, "entry_window_closed: chase beyond 0.40 ATR"
    if d * (quote_price - stop) <= 0:
        return False, "entry_window_closed: stop no longer valid at quote"
    if not targets:
        return False, "entry_window_closed: no target"
    nearest = min(targets, key=lambda t: abs(t - quote_price))
    reward = d * (nearest - quote_price) - round_trip_cost
    risk = abs(quote_price - stop)
    if risk <= 0 or reward / risk < minimum_net_reward_risk:
        return False, "entry_window_closed: net R below 1.5 at quote"
    return True, None


def scale_quantity(initial_qty: int, stage: int,
                   cfg: RiskConfig = RISK) -> int:
    """Shares to sell at a target stage: stage 1 sells
    partial_fraction (50%) of the INITIAL lot quantity, later
    stages sell second_partial_fraction (25%); a 1-share lot may
    close completely; never more than the initial quantity."""
    q = int(initial_qty or 0)
    if q <= 0:
        return 0
    if q == 1:
        return 1
    frac = cfg.partial_fraction if stage <= 1 \
        else cfg.second_partial_fraction
    return max(0, min(q, math.floor(q * frac)))


def breakeven_stop(fill_price: float, direction: int,
                   cfg: RiskConfig = RISK) -> float:
    """Fee-aware breakeven (fees are 0.0 in the pinned config, so
    this is the fill price, computed by formula, not hard-coded)."""
    d = 1 if direction > 0 else -1
    return float(fill_price) + d * 2.0 * cfg.fee_per_unit


def trailed_stop(current_stop: float, direction: int,
                 favorable_extreme: float, atr: float,
                 cfg: RiskConfig = RISK) -> float:
    """The runner's 1-ATR trail from the favorable extreme.
    Stops never loosen: the result never moves against the
    position relative to current_stop."""
    d = 1 if direction > 0 else -1
    cand = float(favorable_extreme) - d * cfg.runner_atr_multiple * float(atr)
    if d > 0:
        return max(float(current_stop), cand)
    return min(float(current_stop), cand)
