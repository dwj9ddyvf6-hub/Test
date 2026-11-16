"""risk_lots — the ADAPTED half of Sol's saty_system/portfolio.py
(PORT-SPEC section 3.6): RiskConfig values verbatim, the
reservation/lot MATH re-expressed as pure functions over desk
fill truth (Ink ledger rows + broker position). No SQLite, no
reservation tables, no broker access. Every equity-relative
quantity is re-based on the sleeve's virtual slice equity —
the single sanctioned adaptation; the fractions, caps and R
arithmetic are his (portfolio.py line ranges named in
ports/saty_gpt_v02.md).

Sizing law (portfolio.py reserve_entry, lines ~271-378):
  session R        = risk_fraction x session-start slice equity E0
  per-entry budget = min(E, E0) x risk_fraction x risk_multiplier,
                     R x max_total_risk_r      - open risk,
                     R x max_correlation_risk_r - group risk,
                     R x max_session_loss_r + min(0, session P&L)
                       - open risk
  unit risk        = |entry - stop| x multiplier(1) + 2 x fee
  quantity         = floor of the minimum over ALL caps (budget,
                     quoted depth when a real size exists,
                     aggregate + group notional at 1.0 x equity;
                     the buy cash cap coincides with the notional
                     cap at fraction 1.0 on a share slice).
                     quantity < 1 is a REJECTION recorded by the
                     caller — there is no forced 1-share floor
                     (the desk OBS-1 ruling agrees).
Caps: session loss 2R, entries/session 3, aggregate open risk
2R, correlation-group risk 1R (SPY's underlying forces his
US_LARGE_CAP_INDEX group, portfolio.py _group). Add-ons off.
Lot law (portfolio.py on_fill / exit_intents): each fill is its
own lot; a target stage's cumulative goal is max(1, floor(
initial x fraction)) — 50% at the first stage, 25% at later
stages — capped at remaining - 1 when remaining > 1 so a runner
is retained where feasible; a one-unit lot may close fully.
After a profitable partial fill the stop tightens to fee-aware
breakeven; after a completed target stage the runner trails at
1.0 ATR from the high-water price. Stops never loosen
(portfolio.py _tighten checks direction x (new - old) > 0).
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
CORRELATION_GROUP = "US_LARGE_CAP_INDEX"  # portfolio.py _group:
# SPY/SPX/SPXW/ES/MES underlyings are forced into this group.


def session_r(e0: float, cfg: RiskConfig = RISK) -> float:
    """The session's frozen R from session-start slice equity
    (portfolio.py _r)."""
    return cfg.risk_fraction * float(e0 or 0.0)


def unit_risk(entry: float, stop: float, cfg: RiskConfig = RISK) -> float:
    """Linear unit risk (portfolio.py reserve_entry):
    |price - stop| x multiplier(1) + 2 x fee_per_unit."""
    return abs(float(entry) - float(stop)) + 2.0 * cfg.fee_per_unit


def compute_qty(equity: float, e0: float, entry: float, stop: float,
                risk_multiplier: float = 1.0,
                open_risk_r: float = 0.0,
                open_notional: float = 0.0,
                entries_taken: int = 0,
                session_pnl_r: float = 0.0,
                depth: int | None = None,
                cfg: RiskConfig = RISK):
    """(qty, reason). qty is an int share count; reason is None
    when qty >= 1, else the named refusal (the caller journals
    it — a zero is never silent). `equity` is his _equity basis:
    current realized slice equity (initial + realized net P&L,
    no unrealized mark). `depth` is the displayed size for the
    side in use, or None when the door carries no real size
    (0/0 is unknown, never zero liquidity — PORT-SPEC 11.2)."""
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
    open_risk = float(open_risk_r or 0.0) * r_unit
    pnl = float(session_pnl_r or 0.0) * r_unit
    budget = min(
        min(e, base) * cfg.risk_fraction * float(risk_multiplier or 0.0),
        r_unit * cfg.max_total_risk_r - open_risk,
        r_unit * cfg.max_correlation_risk_r - open_risk,
        r_unit * cfg.max_session_loss_r + min(0.0, pnl) - open_risk)
    qty = math.floor((budget + 1e-9) / ur)
    if depth is not None and int(depth) > 0:
        qty = min(qty, int(depth))
    for frac in (cfg.max_notional_fraction,
                 cfg.max_correlation_notional_fraction):
        room = frac * e - float(open_notional or 0.0)
        if room <= 0:
            return 0, "risk_cap_r: notional cap spent"
        qty = min(qty, math.floor((room + 1e-9) / float(entry)))
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
    """Quote-admission recheck (portfolio.py reserve_entry quote
    checks + the pinned DeskConfig geometry, PORT-SPEC 6.4): at
    the actual executable price the stop must still be valid,
    EVERY target must still be ahead, the adverse gap must stay
    within 0.15 ATR, the chase within 0.40 ATR, and net room to
    the NEAREST target after the 0.02 round-trip cost must still
    clear 1.5 x net risk. Returns (ok, reason)."""
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
    if any(d * (t - quote_price) <= 0 for t in targets):
        return False, "entry_window_closed: target already reached at quote"
    nearest = min(targets, key=lambda t: abs(t - quote_price))
    reward = d * (nearest - quote_price) - round_trip_cost
    risk = abs(quote_price - stop)
    if risk <= 0 or reward / risk < minimum_net_reward_risk:
        return False, "entry_window_closed: net R below 1.5 at quote"
    return True, None


def stage_goal(initial_qty: int, remaining_qty: int, stage: int,
               cfg: RiskConfig = RISK) -> int:
    """The CUMULATIVE quantity a target stage aims to have sold
    (portfolio.py exit_intents): max(1, floor(initial x
    fraction)) — partial_fraction at stage 1 (index 0 in his
    code), second_partial_fraction later — capped at
    remaining - 1 when remaining > 1 so a runner is retained
    where feasible; a one-unit lot may close completely."""
    q = int(initial_qty or 0)
    rem = int(remaining_qty or 0)
    if q <= 0 or rem <= 0:
        return 0
    frac = cfg.partial_fraction if stage <= 1 \
        else cfg.second_partial_fraction
    goal = max(1, math.floor(q * frac))
    if rem > 1:
        goal = min(goal, rem - 1)
    return min(goal, rem)


def scale_quantity(initial_qty: int, stage: int,
                   filled_for_stage: int = 0,
                   remaining_qty: int | None = None,
                   cfg: RiskConfig = RISK) -> int:
    """Shares still due at a target stage: the stage goal minus
    what that stage has already filled (a canceled/reissued
    target order can never re-sell the same scale)."""
    rem = int(initial_qty or 0) if remaining_qty is None \
        else int(remaining_qty)
    goal = stage_goal(initial_qty, rem, stage, cfg)
    return max(0, goal - int(filled_for_stage or 0))


def breakeven_stop(entry_px: float, direction: int,
                   entry_fees_remaining: float = 0.0,
                   remaining_qty: float = 1.0,
                   cfg: RiskConfig = RISK) -> float:
    """Fee-aware breakeven (portfolio.py on_fill): entry +
    direction x (entry_fees_remaining / remaining_qty +
    fee_per_unit) / multiplier(1). With fee_per_unit 0.0 and no
    unallocated entry fees this is the entry price itself,
    computed by formula, never hard-coded."""
    d = 1 if direction > 0 else -1
    rem = float(remaining_qty or 0.0)
    per_unit = (float(entry_fees_remaining or 0.0) / rem
                if rem > 0 else 0.0) + cfg.fee_per_unit
    return float(entry_px) + d * per_unit


def trailed_stop(current_stop: float, direction: int,
                 favorable_extreme: float, atr: float,
                 cfg: RiskConfig = RISK) -> float:
    """The runner's 1-ATR trail from the high-water underlying
    price (portfolio.py exit_intents). Stops never loosen: the
    result never moves against the position."""
    d = 1 if direction > 0 else -1
    cand = float(favorable_extreme) - d * cfg.runner_atr_multiple * float(atr)
    if d > 0:
        return max(float(current_stop), cand)
    return min(float(current_stop), cand)


def tightened(old_stop: float, new_stop: float, direction: int) -> float:
    """Tighten-only application (portfolio.py _tighten): the new
    stop applies only when direction x (new - old) > 0."""
    d = 1 if direction > 0 else -1
    if d * (float(new_stop) - float(old_stop)) > 0:
        return float(new_stop)
    return float(old_stop)
