"""CRD-05 research kernels: no feed access, strategy activation or order routing.

This implements specified mathematical/accounting components. It is NOT a
canonical CRD backtest. Choice-dependent conventions are recorded in ASSUMPTIONS
and missing economic-exit labels fail closed rather than becoming cash.
"""
from __future__ import annotations

from dataclasses import dataclass,field
import math
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Sequence

import numpy as np
from scipy.optimize import minimize

EXIT = 10
STATES = 11
ASSUMPTIONS = {
    "ridge": "sum squared errors + .01*sum squared standardized slopes; intercept unpenalized",
    "ridge_standardization": "population predictor SD, sample residual SD",
    "residual_rank": "sum(e[t-9:t+1])/sigma[t-10], without sqrt(10); midpoint empirical ranks",
    "MAD": "unscaled median absolute deviation",
    "correlation_missing": "whole sector unavailable if any required 63-session residual is missing or constant",
    "percentile": "(# strictly lower + .5*# tied)/252",
    "effective_origins": "Kish ESS of per-origin state probability masses, distinct dates also reported",
    "pool_unobserved_transition": "identity fallback with zero reward; cannot qualify an unsupported state",
    "maturity": "exclude entire sector-origin cohort until every stock outcome is known; never renormalize survivors",
    "calibration_ridge": "required explicit research parameter; sealed design does not supply magnitude",
    "uncertainty": "calendar-month paired origin resampling with fixed seed; forecast bias magnitude floor",
    "scenario_dependence": "supplied synchronized terminal scenarios; path/exit sampler is not specified here",
    "ambiguity": "rectangular residual-mean intervals; all lower endpoints are worst case for long-only payoffs",
    "optimizer": "SLSQP multistart research solver; feasibility checked independently, global optimality not promised",
    "rounding": "floor purchases, round sell reductions up; greedily reduce until caps feasible; preserve failed candidate",
    "cash_clock": "explicit supplied per-session net cash gross multipliers, not inferred calendar-day accrual",
    "execution": "midpoint ledger with quoted spread plus impact/commission, .0005 side minimum; no queue claim",
    "partial_fills": "ledger checks cash/short feasibility; explicit risk_context enforces caps; emergency reductions may improve already violated caps without creating/worsening another breach",
}


class DataGap(ValueError):
    pass


def finite_array(value, ndim=None):
    a = np.asarray(value, dtype=float)
    if (ndim is not None and a.ndim != ndim) or not np.all(np.isfinite(a)):
        raise ValueError("Wrong dimensions or nonfinite input")
    return a


def transition(matrix, *, require_crd=True):
    a = finite_array(matrix, 2)
    if a.shape[0] != a.shape[1] or not len(a) or np.any(a < 0):
        raise ValueError("Transition matrix must be nonnegative and square")
    if not np.allclose(a.sum(axis=1), 1.0, atol=1e-10, rtol=0):
        raise ValueError("Transition rows must sum to one")
    if require_crd:
        if a.shape != (STATES, STATES) or not np.allclose(a[EXIT], np.eye(STATES)[EXIT], atol=1e-10, rtol=0):
            raise ValueError("CRD requires 11 states and absorbing EXIT")
    return a


def integer(value, minimum=0):
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < minimum:
        raise ValueError("Expected integer in allowed range")
    return int(value)


def state(release, rank):
    if type(release) is not bool or not math.isfinite(rank) or not 0 <= rank <= 1:
        raise ValueError("Invalid release/rank state")
    return 5 * int(release) + min(4, int(math.floor(5 * rank)))


def expected_reward(matrix, rewards, initial_state, steps=4):
    a = transition(matrix)
    b = finite_array(rewards, 1)
    initial_state, steps = integer(initial_state), integer(steps, 1)
    if len(b) != STATES or initial_state >= STATES or b[EXIT] != 0:
        raise ValueError("Invalid CRD reward/state or nonzero EXIT reward")
    value = np.zeros(STATES)
    for _ in range(steps):
        value = b + a @ value
    return float(value[initial_state])


def state_distribution(matrix, initial_state, steps=4):
    a = transition(matrix)
    initial_state, steps = integer(initial_state), integer(steps)
    if initial_state >= STATES:
        raise ValueError("State outside model")
    p = np.eye(STATES)[initial_state]
    for _ in range(steps):
        p = p @ a
    return p


def expected_held_sessions(matrix, initial_state, held_per_block, steps=4):
    """Economic occupancy when EXIT is completed within its transition block.

    Delayed liquidation cannot be represented by silently setting held time to
    zero. Such cases require an explicit label/path interpretation or new state.
    """
    a, h = transition(matrix), finite_array(held_per_block, 1)
    if len(h) != STATES or np.any(h < 0) or np.any(h > 5) or h[EXIT] != 0:
        raise DataGap("Held-time vector incompatible with 5-session absorbing economic EXIT")
    return expected_reward(a, h, initial_state, steps)


@dataclass(frozen=True)
class OriginOutcome:
    sector: str
    origin: int
    month: str
    issuer: str
    eligible_count: int
    source_state: int
    destination: int
    reward_simple_residual: float
    transition_end: int
    known_session: int
    economic_exit_session: int | None = None
    administrative_exit_session: int | None = None
    resolved: bool = True


def admitted_cohorts(records, cutoff, first_origin):
    """Retain cohort weights; reject missing members, defer unresolved cohorts."""
    cutoff, first_origin = integer(cutoff), integer(first_origin)
    groups = {}
    for r in records:
        if first_origin <= r.origin < cutoff:
            groups.setdefault((r.sector, r.origin), []).append(r)
    admitted, deferred = [], []
    for key, cohort in groups.items():
        n = {r.eligible_count for r in cohort}
        if len(n) != 1 or min(n) < 1 or len(cohort) != next(iter(n)) or len({r.issuer for r in cohort}) != len(cohort):
            raise DataGap("Origin cohort incomplete or duplicate issuer; survivors cannot be renormalized")
        if any(r.transition_end != r.origin + 5 or r.known_session < r.transition_end
               or (r.economic_exit_session is not None and r.known_session < r.economic_exit_session)
               for r in cohort):
            raise DataGap("Transition outcome receipt precedes its actual outcome")
        if any(not r.resolved or r.known_session >= cutoff or r.transition_end >= cutoff for r in cohort):
            deferred.append(key)
            continue
        for r in cohort:
            if r.transition_end != r.origin + 5 or r.source_state not in range(EXIT) or r.destination not in range(STATES):
                raise ValueError("Invalid 5-session transition label")
            if not math.isfinite(r.reward_simple_residual):
                raise ValueError("Nonfinite residual reward")
            if (r.destination == EXIT and r.economic_exit_session is not None
                    and not r.origin <= r.economic_exit_session <= r.transition_end):
                raise DataGap("EXIT outside economic transition block: sealed state/path interpretation unresolved")
            if r.destination == EXIT and r.economic_exit_session is None:
                raise DataGap("EXIT label lacks executable liquidation/legal-recovery timing")
        admitted += cohort
    return admitted, {"cohorts_admitted": len(groups) - len(deferred), "cohorts_deferred": len(deferred)}


def fit_markov(records, sector, cutoff, first_origin, shrink=50.0):
    if not math.isfinite(shrink) or shrink < 0:
        raise ValueError("Invalid shrinkage")
    admitted, receipt = admitted_cohorts(records, cutoff, first_origin)
    pooled, counts = np.zeros((STATES, STATES)), np.zeros((STATES, STATES))
    reward_sums, mass = np.zeros(STATES), np.zeros(STATES)
    rank_sums, rank_mass = np.zeros(5), np.zeros(5)
    by_date = {s: {} for s in range(EXIT)}
    for r in admitted:
        weight = 1.0 / r.eligible_count
        pooled[r.source_state, r.destination] += weight
        rank_sums[r.source_state % 5] += weight * r.reward_simple_residual
        rank_mass[r.source_state % 5] += weight
        if r.sector == sector:
            counts[r.source_state, r.destination] += weight
            reward_sums[r.source_state] += weight * r.reward_simple_residual
            mass[r.source_state] += weight
            d = by_date[r.source_state]
            d[r.origin] = d.get(r.origin, 0) + weight
    prior = np.eye(STATES)
    for s in range(EXIT):
        if pooled[s].sum() > 0:
            prior[s] = pooled[s] / pooled[s].sum()
    matrix, rewards = np.eye(STATES), np.zeros(STATES)
    origins = []
    for s in range(EXIT):
        denominator = mass[s] + shrink
        if denominator > 0:
            matrix[s] = (counts[s] + shrink * prior[s]) / denominator
            rank_prior = rank_sums[s % 5] / rank_mass[s % 5] if rank_mass[s % 5] else 0
            rewards[s] = (reward_sums[s] + shrink * rank_prior) / denominator
        weights = np.array(list(by_date[s].values()))
        ess = float(weights.sum() ** 2 / (weights @ weights)) if len(weights) else 0.0
        origins.append({"state": s, "weighted_origin_mass": float(mass[s]),
                        "distinct_origin_dates": len(weights), "kish_origin_ess": ess,
                        "entry_supported": ess >= 30})
    transition(matrix)
    return {"matrix": matrix, "rewards": rewards, "state_origins": origins,
            "receipt": receipt, "admitted_rows": len(admitted)}


def bootstrap_forecast(records, sector, cutoff, first_origin, source_state, *, seed, draws=500, bias=0.0):
    draws = integer(draws, 2)
    if not math.isfinite(bias):
        raise ValueError("Nonfinite historical OOF bias")
    admitted, _ = admitted_cohorts(records, cutoff, first_origin)
    months = sorted({r.month for r in admitted})
    if len(months) < 2:
        raise DataGap("At least two complete calendar-month blocks required")
    rng = np.random.default_rng(integer(seed))
    by_month = {m: [r for r in admitted if r.month == m] for m in months}
    # Repeated calendar blocks retain their whole original cohort, but receive
    # fresh episode origin numbers solely for estimator bookkeeping.
    forecasts = []
    for _ in range(draws):
        sampled = []
        for block, m in enumerate(rng.choice(months, size=len(months), replace=True)):
            rows = by_month[m]
            dates = {o: j for j, o in enumerate(sorted({r.origin for r in rows}))}
            for r in rows:
                o = block * 10000 + dates[r.origin] * 5
                sampled.append(OriginOutcome(r.sector, o, m, r.issuer, r.eligible_count,
                    r.source_state, r.destination, r.reward_simple_residual, o + 5, o + 5,
                    o + (r.economic_exit_session - r.origin) if r.economic_exit_session is not None else None,
                    o + (r.administrative_exit_session - r.origin) if r.administrative_exit_session is not None else None))
        fit = fit_markov(sampled, sector, len(months) * 10000 + 1000, 0)
        forecasts.append(expected_reward(fit["matrix"], fit["rewards"], source_state))
    se = float(np.std(forecasts, ddof=1))
    return {"draws": draws, "seed": seed, "bootstrap_se": se,
            "se_with_bias_floor": max(se, abs(bias)), "forecasts": np.array(forecasts)}


def calibrate(raw, outcomes, origins, label_ends, trained_through, cutoff, *, ridge, min_dates=100):
    x, y = finite_array(raw, 1), finite_array(outcomes, 1)
    if len(x) != len(y) or len(x) != len(origins) or len(x) != len(label_ends) or len(x) != len(trained_through):
        raise ValueError("Calibration dimensions mismatch")
    if len(set(origins)) < min_dates:
        raise DataGap("Insufficient distinct OOF calibration origin dates")
    if any(isinstance(v,bool) or not isinstance(v,(int,np.integer)) for values in (origins,label_ends,trained_through) for v in values):
        raise ValueError("Calibration clocks must be integer session indices")
    if any(o < 0 or o >= cutoff or e != o+20 for o,e in zip(origins,label_ends)):
        raise DataGap("Calibration label must span the actual next20-session horizon")
    # trained_through denotes the latest training LABEL END, not merely the
    # training sample's origin. Its20-session gap enforces embargo after purge.
    if any(t > o-20 for t, o in zip(trained_through, origins)) or any(e >= cutoff for e in label_ends):
        raise DataGap("Calibration prediction/model or label leaks beyond historical cutoff")
    if not math.isfinite(ridge) or ridge < 0:
        raise ValueError("Calibration ridge must be explicit and nonnegative")
    z = np.column_stack((np.ones(len(x)), x))
    target = np.array([0.0, 1.0])
    system = z.T @ z + ridge * np.eye(2)
    rhs = z.T @ y + ridge * target
    coefficients = np.linalg.lstsq(system, rhs, rcond=None)[0]
    residual = y - z @ coefficients
    return {"intercept": float(coefficients[0]), "slope": float(coefficients[1]),
            "ridge": ridge, "oof_bias": float(np.mean(residual)), "origin_dates": len(set(origins))}


def midpoint_percentiles(values):
    x = finite_array(values, 1)
    return np.array([(np.count_nonzero(x < v) + 0.5 * np.count_nonzero(x == v)) / len(x) for v in x])


def historical_percentile(history, present, length=252):
    h = finite_array(history, 1)
    if len(h) < length or not math.isfinite(present):
        raise DataGap("Historical percentile window unavailable")
    h = h[-length:]
    return float((np.count_nonzero(h < present) + 0.5 * np.count_nonzero(h == present)) / length)


def residual_for_next(stock_history, factor_history, next_stock, next_factors, penalty=.01):
    y, x = finite_array(stock_history, 1), finite_array(factor_history, 2)
    next_x = finite_array(next_factors, 1)
    if len(y) != len(x) or x.shape[1] != 2 or len(next_x) != 2 or len(y) < 200 or len(y) > 252:
        raise DataGap("Residual regression requires 200-252 prior observations and two factors")
    if not math.isfinite(next_stock) or penalty < 0 or not math.isfinite(penalty):
        raise ValueError("Invalid regression inputs")
    mean, sd = x.mean(axis=0), x.std(axis=0, ddof=0)
    if np.any(sd <= 0):
        raise DataGap("Constant market/sector factor history")
    z = (x - mean) / sd
    design = np.column_stack((np.ones(len(z)), z))
    ridge = np.diag([0.0, penalty, penalty])
    coef = np.linalg.solve(design.T @ design + ridge, design.T @ y)
    beta = coef[1:] / sd
    intercept = coef[0] - beta @ mean
    return {"residual": float(next_stock - beta @ next_x),
            "betas": beta, "intercept_fitted_not_subtracted": float(intercept)}


def residual_rank_at(residuals, t):
    e = finite_array(residuals, 2)  # time x stock; no zero imputation
    t = integer(t)
    if t < 72 or t >= len(e):
        raise DataGap("Rank denominator needs 63 observations before the 10-session signal")
    sd = np.maximum(e[t-72:t-9].std(axis=0, ddof=1), .0025)
    sums = e[t-9:t+1].sum(axis=0)
    return {"ranks": midpoint_percentiles(sums / sd), "sums": sums, "denominator": sd}


def sector_dispersion(residuals, t):
    e = finite_array(residuals, 2)
    if e.shape[1] < 30 or t < 67 or t >= len(e):
        raise DataGap("Dispersion needs 30 names and prior residual volatility")
    daily = []
    for u in range(t-4, t+1):
        sd = np.maximum(e[u-63:u].std(axis=0, ddof=1), .0025)
        z = e[u] / sd
        daily.append(float(np.median(np.abs(z - np.median(z)))))
    return float(np.mean(daily))


def synchronization(residuals):
    e = finite_array(residuals, 2)
    if e.shape[0] != 63 or e.shape[1] < 30 or np.any(e.std(axis=0) == 0):
        raise DataGap("Synchronization needs 63 complete observations, 30 nonconstant names")
    corr = np.corrcoef(e, rowvar=False)
    shrunk = .5 * corr + .5 * np.eye(e.shape[1])
    return float(np.linalg.eigvalsh(shrunk)[-1] / e.shape[1])


def release_flags(d_percentiles, k_percentiles):
    d, k = finite_array(d_percentiles, 1), finite_array(k_percentiles, 1)
    if len(d) != len(k) or np.any(d < 0) or np.any(d > 1) or np.any(k < 0) or np.any(k > 1):
        raise ValueError("Invalid dimensionless percentile series")
    flags, first = np.zeros(len(d), dtype=bool), None
    events = []
    for t in range(20, len(d)):
        active = first is not None and t - first < 10
        compression = np.count_nonzero((d[t-20:t] <= .2) & (k[t-20:t] >= .8)) >= 3
        trigger = compression and d[t] >= .6 and k[t-10] - k[t] >= .2 - 1e-14
        if trigger and not active:
            first = t
            active = True
            events.append(t)
        flags[t] = active
    return flags, events


def simple_to_log(returns):
    r = finite_array(returns)
    if np.any(r <= -1):
        raise DataGap("Zero recovery is an outcome, not a finite living log-return feature")
    return np.log1p(r)


def compound_cash(net_daily_yields):
    r = finite_array(net_daily_yields, 1)
    if np.any(r <= -1):
        raise ValueError("Invalid cash yields")
    return float(np.expm1(np.log1p(r).sum()))


def market_log_mean(trailing_log_returns, annual_simple_prior=.06):
    r = finite_array(trailing_log_returns, 1)
    if len(r) != 252 or annual_simple_prior <= -1:
        raise ValueError("Invalid market mean/prior inputs")
    return float(.25 * r.mean() + .75 * math.log1p(annual_simple_prior) / 252)


def match_simple_means(gross_scenarios, target_simple_means):
    gross, means = finite_array(gross_scenarios, 2), finite_array(target_simple_means, 1)
    if gross.shape[1] != len(means) or np.any(gross < 0) or np.any(means < -1):
        raise ValueError("Impossible gross scenarios or target mean")
    output = gross.copy()
    for i in range(len(means)):
        target, base = 1 + means[i], gross[:, i].mean()
        if base == 0:
            if target != 0:
                raise DataGap("Cannot restore positive mean from all zero-recovery scenarios")
        elif target == 0:
            raise DataGap("Positive scaling cannot force living scenarios to zero gross mean")
        else:
            output[:, i] *= target / base
    return output


def cvar_loss(terminal_wealth, tail=.05):
    w = finite_array(terminal_wealth, 1)
    if not len(w) or not 0 < tail <= 1:
        raise ValueError("Invalid CVaR sample/tail")
    losses = np.sort(1 - w)[::-1]
    mass = tail * len(losses)
    count = int(math.floor(mass))
    numerator = float(losses[:count].sum())
    if count < len(losses):
        numerator += (mass - count) * losses[count]
    return numerator / mass


def funded_target(current, target, side_cost=.0005):
    before, x = finite_array(current, 1), finite_array(target, 1)
    if len(before) != len(x) or np.any(before < 0) or np.any(x < 0) or before.sum() > 1 + 1e-12:
        raise ValueError("Invalid unlevered stock weights")
    if not math.isfinite(side_cost) or side_cost < 0:
        raise ValueError("Invalid side cost")
    cost = side_cost * float(np.abs(x - before).sum())
    cash = 1 - float(x.sum()) - cost
    if cost >= 1 or cash < -1e-12:
        raise ValueError("Unfunded target")
    return {"stocks": x, "cash": max(0.0, cash), "cost": cost,
            "post_stock_weights": x / (1-cost), "post_cash_weight": max(0.0, cash)/(1-cost)}


def terminal_objective(plan, stock_gross, cash_gross, sell_cost=.0005, penalty=.10, terminal_held=None):
    stocks=finite_array(plan["stocks"],1)
    if np.any(stocks<0) or not math.isfinite(plan["cash"]) or plan["cash"]<0 or not 0<=plan["cost"]<1 or not math.isclose(float(stocks.sum())+plan["cash"]+plan["cost"],1,abs_tol=1e-10):
        raise ValueError("Terminal objective requires a funded unlevered plan")
    gross, cash = finite_array(stock_gross, 2), finite_array(cash_gross, 1)
    if not len(gross) or gross.shape[1] != len(plan["stocks"]) or len(gross) != len(cash) or np.any(gross < 0) or np.any(cash < 0):
        raise ValueError("Invalid terminal scenarios")
    if not 0 <= sell_cost < 1 or not math.isfinite(penalty) or penalty < 0:
        raise ValueError("Invalid objective costs/penalty")
    # An already-liquidated episode's cash gross includes its actual exit cost;
    # reserve only positions still held at H. Missing mask means ALL held and
    # is legitimate only for that explicitly restricted research scenario.
    held = np.ones_like(gross,dtype=bool) if terminal_held is None else np.asarray(terminal_held)
    if held.shape != gross.shape or held.dtype != np.bool_:
        raise ValueError("Terminal economically-held mask must be boolean and scenario-shaped")
    net_gross = gross * (1-sell_cost*held)
    wealth = net_gross @ plan["stocks"] + plan["cash"] * cash
    if np.any(wealth <= 0):
        return {"objective": -math.inf, "mean_logwealth": -math.inf,
                "cvar_loss": cvar_loss(wealth), "terminal_wealth": wealth}
    mean_log = float(np.log(wealth).mean())
    risk = cvar_loss(wealth)
    return {"objective": mean_log - penalty * risk, "mean_logwealth": mean_log,
            "cvar_loss": risk, "terminal_wealth": wealth}


def connected_clusters(correlation, threshold=.7):
    corr = finite_array(correlation, 2)
    if corr.shape[0] != corr.shape[1] or not np.allclose(corr, corr.T) or not math.isfinite(threshold) or not -1<=threshold<=1:
        raise ValueError('Invalid correlation or threshold')
    if len(corr) and (not np.allclose(np.diag(corr),1,atol=1e-12) or np.any(np.abs(corr)>1+1e-12) or np.linalg.eigvalsh(corr)[0]<-1e-12):
        raise ValueError("Invalid symmetric correlation matrix")
    seen, groups = set(), []
    for i in range(len(corr)):
        if i in seen:
            continue
        stack, members = [i], []
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node); members.append(node)
            stack += [j for j in range(len(corr)) if j not in seen and j != node and corr[node,j] >= threshold]
        groups.append(members)
    return groups


def validate_partition(clusters,n):
    if not isinstance(clusters,(list,tuple)):raise ValueError('cluster partition required')
    flat=[]
    for group in clusters:
        if not isinstance(group,(list,tuple,np.ndarray)) or not len(group):raise ValueError('nonempty cluster groups required')
        flat.extend(integer(i) for i in group)
    if sorted(flat)!=list(range(n)):raise ValueError('clusters must partition every stock exactly once')
    return clusters


def constraint_slacks(plan, current, covariance20, sectors, clusters, *, emergency=False):
    x,y=finite_array(plan["stocks"],1),finite_array(plan["post_stock_weights"],1)
    current=finite_array(current,1)
    if type(emergency) is not bool:raise ValueError('explicit boolean emergency authorization required')
    if any(not isinstance(g,str) or not g for g in sectors):raise ValueError('then-known nonempty sector identities required')
    if x.shape!=y.shape or current.shape!=x.shape or np.any(current<0) or current.sum()>1+1e-12:
        raise ValueError('current and planned stock domains invalid')
    cost,cash=float(plan['cost']),float(plan['cash'])
    if not math.isfinite(cost) or not 0<=cost<1 or not math.isfinite(cash) or cash<0 or np.any(x<0) or not math.isclose(x.sum()+cash+cost,1,abs_tol=1e-10):
        raise ValueError('plan must conserve funded equity')
    if not np.allclose(y,x/(1-cost),rtol=0,atol=1e-12) or not math.isclose(float(plan['post_cash_weight']),cash/(1-cost),abs_tol=1e-12):
        raise ValueError('post-cost weights must use remaining equity')
    validate_partition(clusters,len(x))
    covariance = finite_array(covariance20, 2)
    if covariance.shape != (len(x), len(x)) or not np.allclose(covariance,covariance.T,atol=1e-12):
        raise ValueError("Invalid 20-session covariance")
    if (len(x) and np.linalg.eigvalsh(covariance)[0] < -1e-12) or len(sectors) != len(x):
        raise ValueError("Covariance not PSD or sectors mismatch")
    variance = max(0.0, float(y @ covariance @ y))
    slacks = {"cash_min": plan["post_cash_weight"] - .05,
              "cash_max": 1 - plan["post_cash_weight"], "gross_max": .95 - y.sum(),
              "stock_max": .05 - (max(y) if len(y) else 0),
              "sector_max": .25 - max((sum(y[i] for i,s in enumerate(sectors) if s==g) for g in set(sectors)),default=0),
              "cluster_max": .20 - max((sum(y[i] for i in cluster) for cluster in clusters),default=0),
              "vol_max": .20 - math.sqrt(variance * 252/20),
              "position_count": 30 - np.count_nonzero(x > 1e-12),
              "turnover": .30 - float(np.abs(x - np.asarray(current)).sum())}
    if emergency:
        if np.any(x > np.asarray(current) + 1e-12):
            raise ValueError("Emergency exemption only covers reductions")
        slacks.pop("turnover")
    return {k: float(v) for k,v in slacks.items()}


def feasible(slacks, tolerance=1e-10):
    return all(math.isfinite(v) and v >= -tolerance for v in slacks.values())


def optimize_target(current, lower_mean_gross, cash_gross, covariance20, sectors, clusters, side_cost=.0005):
    """Numerical proposal, not a global-optimum certificate or canonical solver."""
    w=finite_array(current,1)
    covariance20=finite_array(covariance20,2)
    if covariance20.shape!=(len(w),len(w)) or len(sectors)!=len(w):raise ValueError('risk context dimensions mismatch, including all cash')
    validate_partition(clusters,len(w))
    if not np.allclose(covariance20,covariance20.T,atol=1e-12) or (len(w) and np.linalg.eigvalsh(covariance20)[0]<-1e-12):raise ValueError('risk covariance must be PSD')
    if len(w) > 30:
        raise DataGap("Candidate selection beyond 30 names is unspecified; no hidden optimizer selection")
    gross = finite_array(lower_mean_gross, 2)
    if gross.shape[1] != len(w):
        raise ValueError("Scenario/current dimensions differ")
    if len(w)==0:
        held=funded_target([],[],side_cost)
        terminal_objective(held,gross,cash_gross,sell_cost=side_cost)
        if not feasible(constraint_slacks(held,[],np.zeros((0,0)),[],[])):
            raise ValueError("All-cash account unexpectedly infeasible")
        return {"plan":held,"proposal":held,"objective_improvement":0.0,"mean_logwealth_improvement":0.0,"trade":False,
                "held_legal":True,"solver_success":True,"solver_message":"No stock candidates; exact all-cash solution",
                "global_optimality_verified":True}
    def plan(x): return funded_target(w,x,side_cost)
    def slacks(x):
        try:return np.array(list(constraint_slacks(plan(x),w,covariance20,sectors,clusters).values()))
        except ValueError:return np.full(9,-1000.0)
    def objective(x):
        try:return -terminal_objective(plan(x),gross,cash_gross,sell_cost=side_cost)["objective"]
        except ValueError:return 1000.0
    starts = [np.zeros(len(w)), np.minimum(w,.045), np.full(len(w),min(.04,.25/max(len(w),1)))]
    candidates = []
    for start in starts:
        result = minimize(objective,start,method="SLSQP",bounds=[(0,.05)]*len(w),
                          constraints=[{"type":"ineq","fun":slacks}],options={"maxiter":1000,"ftol":1e-12})
        if result.success and feasible(dict(enumerate(slacks(result.x)))):
            candidates.append((objective(result.x), result))
    if not candidates:
        raise DataGap("Solver found no independently feasible proposal")
    _, best = min(candidates,key=lambda v:v[0])
    proposed = plan(best.x)
    held = plan(w)
    proposed_evaluation=terminal_objective(proposed,gross,cash_gross,sell_cost=side_cost)
    held_evaluation=terminal_objective(held,gross,cash_gross,sell_cost=side_cost)
    gain = proposed_evaluation["objective"]-held_evaluation["objective"]
    log_gain = proposed_evaluation["mean_logwealth"]-held_evaluation["mean_logwealth"]
    hold_legal = feasible(constraint_slacks(held,w,covariance20,sectors,clusters))
    trade = (log_gain > math.log1p(.0002) and gain > 0) or not hold_legal
    return {"plan": proposed if trade else held, "proposal": proposed,
            "objective_improvement": gain, "mean_logwealth_improvement":log_gain,
            "trade": trade, "held_legal": hold_legal,
            "solver_success": bool(best.success), "solver_message": str(best.message),
            "global_optimality_verified": False}


def round_target(current_shares, proposed_stock_fractions, prices, cash_usd, side_cost=.0005,
                 sectors=None, clusters=None, covariance20=None, emergency=False):
    if sectors is None or clusters is None or covariance20 is None:raise DataGap('whole-share rounding requires the actual complete risk context')
    if not math.isfinite(cash_usd) or not math.isfinite(side_cost) or side_cost<0:raise ValueError('finite nonnegative cash and fee model required')
    shares, p, target = finite_array(current_shares,1), finite_array(prices,1), finite_array(proposed_stock_fractions,1)
    if len(shares)!=len(p) or len(p)!=len(target) or np.any(p<=0) or np.any(shares<0) or np.any(shares!=np.floor(shares)) or cash_usd<0:
        raise ValueError("Invalid whole-share account")
    equity=float(shares@p+cash_usd)
    if equity<=0:raise ValueError("Insolvent account")
    desired=np.floor(target*equity/p+1e-12).astype(int)
    before=shares*p/equity
    sectors=list(sectors);validate_partition(clusters,len(p))
    iterations=0
    while True:
        try:
            plan=funded_target(before,desired*p/equity,side_cost)
            slacks=constraint_slacks(plan,before,covariance20,sectors,clusters,emergency=emergency)
        except ValueError:
            plan=None;slacks={"funding":-1.0}
        if plan is not None and feasible(slacks):
            return {"shares":desired,"cash_usd":plan["cash"]*equity,"cost_usd":plan["cost"]*equity,
                    "plan":plan,"slacks":slacks,"rounding_reductions":iterations}
        if not np.any(desired>0) or iterations>int(desired.sum())+len(p)+1:
            raise DataGap("Whole-share rounding cannot produce feasible ordinary target")
        # First remove purchase increments. If holding itself violates hard caps,
        # a separately authorized emergency reduction is required.
        available=np.where(desired>shares)[0]
        if not len(available):
            if not emergency:raise DataGap("Required cap repair exceeds ordinary rounding policy")
            available=np.where(desired>0)[0]
        j=max(available,key=lambda i:desired[i]*p[i])
        desired[j]-=1;iterations+=1


@dataclass
class Ledger:
    cash: float
    shares: np.ndarray
    participation_by_interval: dict = field(default_factory=dict)
    participation_by_session: dict = field(default_factory=dict)
    execution_receipts: dict = field(default_factory=dict)
    action_receipts: dict = field(default_factory=dict)

    def __post_init__(self):
        self.shares=finite_array(self.shares,1).copy()
        if not math.isfinite(self.cash) or self.cash<0 or np.any(self.shares<0) or np.any(self.shares!=np.floor(self.shares)):
            raise ValueError("Invalid initial account")

    def equity(self, prices):
        p=finite_array(prices,1)
        if len(p)!=len(self.shares) or np.any(p<0):raise ValueError("Invalid valuation prices")
        return float(self.cash+self.shares@p)

    def execute_slice(self, stock, delta, bid, ask, *, adv_shares, interval_volume,
                      observed_session, frozen_decision_session, quote_stale=False,
                      impact_rate=0, commission_rate=0, risk_context=None, emergency=False,
                      execution_interval_id=None, receipt_id=None, decision_at=None, quote_event_at=None, quote_received_at=None, processed_at=None):
        i=integer(stock)
        for t in (decision_at,quote_event_at,quote_received_at,processed_at):
            if not isinstance(t,datetime) or t.tzinfo is None or t.utcoffset() is None:raise ValueError('aware execution decision/event/receipt/processing clocks required')
        if not decision_at<quote_event_at<=quote_received_at<=processed_at or (processed_at-quote_event_at).total_seconds()>2:
            raise ValueError('execution chronology or two-second quote freshness violated')
        local=processed_at.astimezone(ZoneInfo('America/New_York'))
        if not (local.hour==9 and local.minute>=35 or local.hour==10 and local.minute<5):raise ValueError('execution outside frozen 09:35-10:05 New York window')
        observed_session,frozen_decision_session=integer(observed_session),integer(frozen_decision_session)
        if risk_context is None:raise ValueError('actual held risk context mandatory for every native slice')
        if not isinstance(receipt_id,str) or not receipt_id:raise ValueError('immutable execution receipt identity required')
        required={'prices','covariance20','sectors','clusters'}
        if not isinstance(risk_context,dict) or not required.issubset(risk_context):raise ValueError('complete risk context required')
        risk_binding=(tuple(finite_array(risk_context['prices'],1)),tuple(map(tuple,finite_array(risk_context['covariance20'],2))),tuple(risk_context['sectors']),tuple(map(tuple,risk_context['clusters'])))
        receipt=(risk_binding,i,delta,bid,ask,adv_shares,interval_volume,observed_session,frozen_decision_session,quote_stale,impact_rate,commission_rate,emergency,execution_interval_id,decision_at.isoformat(),quote_event_at.isoformat(),quote_received_at.isoformat(),processed_at.isoformat())
        if receipt_id in self.execution_receipts:
            prior=self.execution_receipts[receipt_id]
            if prior['receipt']!=receipt:raise ValueError('immutable execution receipt revised')
            return dict(prior['result'],duplicate=True)
        def record_result(result):
            self.execution_receipts[receipt_id]={'receipt':receipt,'result':dict(result)}
            return dict(result)
        if isinstance(delta,bool) or not isinstance(delta,(int,np.integer)):
            raise ValueError("Whole-share delta required")
        if any(not math.isfinite(v) or v<0 for v in (adv_shares,interval_volume,impact_rate,commission_rate)):
            raise ValueError("Invalid observed volume/fee evidence")
        if i>=len(self.shares) or delta==0:return record_result({"filled":0,"cost":0.0})
        if quote_stale or not (math.isfinite(bid) and math.isfinite(ask) and 0<bid<=ask) or observed_session<=frozen_decision_session:
            return record_result({"filled":0,"cost":0.0,"reason":"missing/stale quote or signal timing"})
        # Volume is cumulative observed volume in the named interval. Budgets
        # count buys PLUS sells and are shared by every slice/order that day.
        session_key=(observed_session,i)
        interval_key=(observed_session,execution_interval_id or '09:35-10:05',i)
        interval_used=self.participation_by_interval.get(interval_key,0)
        daily_used=self.participation_by_session.get(session_key,0)
        limit=math.floor(min(.005*adv_shares-daily_used,.05*interval_volume-interval_used))
        quantity=min(abs(delta),max(0,limit))
        if delta<0:quantity=min(quantity,int(self.shares[i]))
        mid=(bid+ask)/2
        prices=None
        if risk_context is not None:
            required={"prices","covariance20","sectors","clusters"}
            if not required.issubset(risk_context):raise ValueError("Incomplete slice risk context")
            prices=finite_array(risk_context["prices"],1)
            if len(prices)!=len(self.shares) or np.any(prices<0) or not math.isclose(prices[i],mid,rel_tol=1e-12):
                raise ValueError("Risk valuation must use current execution midpoint")
        rate=max(.0005,(ask-bid)/(2*mid)+impact_rate+commission_rate)
        if rate<0 or not math.isfinite(rate):raise ValueError("Invalid execution costs")
        if delta>0:quantity=min(quantity,max(0,math.floor(self.cash/(mid*(1+rate)))))
        signed=quantity if delta>0 else -quantity
        notional=quantity*mid;cost=rate*notional
        before=self.cash;before_shares=self.shares.copy()
        self.cash-=signed*mid+cost
        self.shares[i]+=signed
        if self.cash<-1e-8 or self.shares[i]<0:
            self.cash=before;self.shares[i]-=signed;raise ValueError("Execution violated self financing")
        if risk_context is not None:
            pre_equity=float(before+before_shares@prices)
            old_weights=before_shares*prices/pre_equity
            actual={"stocks":self.shares*prices/pre_equity,"cash":self.cash/pre_equity,"cost":cost/pre_equity,
                    "post_stock_weights":self.shares*prices/(pre_equity-cost),
                    "post_cash_weight":self.cash/(pre_equity-cost)}
            try:
                after_slacks=constraint_slacks(actual,old_weights,risk_context["covariance20"],
                    risk_context["sectors"],risk_context["clusters"],emergency=emergency)
                legal=feasible(after_slacks)
                if emergency and signed<0 and not legal:
                    initial=funded_target(old_weights,old_weights)
                    before_slacks=constraint_slacks(initial,old_weights,risk_context["covariance20"],
                        risk_context["sectors"],risk_context["clusters"],emergency=True)
                    legal=all(after_slacks[k]>=min(0,before_slacks[k])-1e-10 for k in after_slacks)
            except ValueError:
                legal=False
            if not legal:
                self.cash=before;self.shares=before_shares
                return record_result({"filled":0,"cost":0.0,"reason":"post-slice hard cap breach"})
        self.participation_by_interval[interval_key]=interval_used+quantity
        self.participation_by_session[session_key]=daily_used+quantity
        result={"filled":signed,"cost":cost,"mid_notional":notional,"side_rate":rate}
        return record_result(result)

    def _action(self,action_id,payload,effective_at,known_at,applied_at):
        if not isinstance(action_id,str) or not action_id:raise ValueError('corporate action immutable identity required')
        for t in (effective_at,known_at,applied_at):
            if not isinstance(t,datetime) or t.tzinfo is None or t.utcoffset() is None:raise ValueError('aware corporate-action clocks required')
        if max(effective_at,known_at)>applied_at:raise ValueError('corporate action applied before effect or receipt')
        record=(payload,effective_at.isoformat(),known_at.isoformat())
        if action_id in self.action_receipts:
            if self.action_receipts[action_id]!=record:raise ValueError('corporate action receipt revised')
            return None
        return record
    def distribution(self,stock,per_share,*,action_id,effective_at,known_at,applied_at,entitlement_shares):
        stock=integer(stock)
        if stock>=len(self.shares) or not math.isfinite(per_share) or per_share<0:raise ValueError('Invalid distribution')
        entitlement_shares=integer(entitlement_shares)
        record=self._action(action_id,('DIVIDEND',stock,float(per_share),entitlement_shares),effective_at,known_at,applied_at)
        if record is None:return False
        self.cash+=entitlement_shares*per_share;self.action_receipts[action_id]=record;return True
    def split(self,stock,ratio,*,action_id,effective_at,known_at,applied_at):
        stock=integer(stock)
        if stock>=len(self.shares) or not math.isfinite(ratio) or ratio<=0:raise ValueError('Invalid split')
        record=self._action(action_id,('SPLIT',stock,float(ratio)),effective_at,known_at,applied_at)
        if record is None:return False
        qty=self.shares[stock]*ratio
        if not math.isclose(qty,round(qty),abs_tol=1e-12,rel_tol=0):raise DataGap('explicit fractional cash-in-lieu resolution required')
        self.shares[stock]=round(qty);self.action_receipts[action_id]=record;return True
    def actual_cap_report(self,prices,covariance20,sectors,clusters):
        p=finite_array(prices,1);equity=self.equity(p)
        if equity<=0:raise DataGap('positive marked equity required')
        actual=self.shares*p/equity
        plan=funded_target(actual,actual)
        slacks=constraint_slacks(plan,actual,covariance20,sectors,clusters,emergency=True)
        breaches={k:v for k,v in slacks.items() if v< -1e-10}
        return {'actual_weights':actual,'slacks':slacks,'breaches':breaches,'risk_reduction_required':bool(breaches),'reductions_are_requests_not_fills':True,'block_new_purchases':bool(breaches)}

    def resolve(self, stock, recovery_per_share, *, tradable):
        if not tradable:return {"resolved":False,"remaining_shares":float(self.shares[stock])}
        if not math.isfinite(recovery_per_share) or recovery_per_share<0:raise ValueError("Invalid legal recovery")
        proceeds=float(self.shares[stock]*recovery_per_share)
        self.cash+=proceeds;self.shares[stock]=0
        return {"resolved":True,"proceeds":proceeds}


def entry_allowed(rank, rank_then, residual_sum, release, calibrated, rank_only, se,
                  incremental_se, effective_origins, calibration_dates, round_trip_cost):
    numbers=[rank,rank_then,residual_sum,calibrated,rank_only,se,incremental_se,effective_origins,round_trip_cost]
    if any(not math.isfinite(v) for v in numbers) or min(se,incremental_se,round_trip_cost)<0:
        raise ValueError("Invalid entry evidence")
    return (release is True and .6<=rank<=.95 and rank-rank_then>=.2-1e-14
            and residual_sum>0 and effective_origins>=30 and calibration_dates>=100
            and calibrated-rank_only-1.645*incremental_se>0
            and calibrated-1.645*se>round_trip_cost+.002)


def exit_decision(*, rank, conservative_forecast, fundamental_eligible, hard_cap_breach,
                  entry_drawdown, account_drawdown, release_expired=False):
    values=[rank,conservative_forecast,entry_drawdown,account_drawdown]
    if any(not math.isfinite(v) for v in values) or not 0<=rank<=1 or min(entry_drawdown,account_drawdown)<0:
        raise ValueError("Invalid close monitoring evidence")
    reasons=[]
    if rank<.4:reasons.append("rank")
    if conservative_forecast<=0:reasons.append("residual forecast")
    if not fundamental_eligible:reasons.append("fundamental eligibility")
    if hard_cap_breach:reasons.append("hard cap")
    if entry_drawdown>=.08:reasons.append("position drawdown")
    if account_drawdown>=.20:reasons.append("account drawdown")
    return {"queue_next_session":bool(reasons),"liquidate_all":account_drawdown>=.20,
            "reasons":reasons,"cooldown_sessions":5 if entry_drawdown>=.08 or account_drawdown>=.20 else 0,
            "release_expiry_alone_is_exit":False}


def joint_growth(strategy_returns, qqq_returns, spy_returns, cash_returns):
    arrays=[finite_array(a,1) for a in (strategy_returns,qqq_returns,spy_returns,cash_returns)]
    if not arrays[0].size or len({len(a) for a in arrays})!=1 or any(np.any(a<-1) for a in arrays):
        raise ValueError("Misaligned or invalid funded return series")
    def growth(r):return -math.inf if np.any(r==-1) else float(np.log1p(r).mean()*252)
    gs,gq,gp,gc=map(growth,arrays)
    j=min(gs-gq,gs-gp)
    return {"g_strategy":gs,"g_QQQ":gq,"g_SPY":gp,"g_cash":gc,"J":j,
            "joint_pass":j>0 and gs>max(gc,0)}

R10_VERSION="r10-crd-necessary-repairs-v1"
CANONICAL_FINANCIAL_QUALIFICATION=False
DEPLOYMENT_APPROVED=False
