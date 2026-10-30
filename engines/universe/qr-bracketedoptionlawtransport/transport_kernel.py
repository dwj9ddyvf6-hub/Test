"""Exact finite-state martingale bounds for a stated hypothetical European payoff.

This reference kernel does NOT implement native CME fixing/delivery payoffs,
continuous tail certificates, physical return calibration, or a trading account.
"""
from dataclasses import dataclass
import math
import numpy as np
from scipy.optimize import linprog
from fractions import Fraction

VERSION = "r10-finite-dual-witness-v1"


@dataclass(frozen=True)
class Bounds:
    lower: float
    upper: float
    lower_coupling: np.ndarray
    upper_coupling: np.ndarray
    maximum_primal_residual: float
    scope: str = "HYPOTHETICAL_EXACT_FINITE_STATE_PAYOFF_ONLY"
    lower_certificate: dict | None = None
    upper_certificate: dict | None = None


def validate_certificate(c, aeq, beq, aub, bub, result, tolerance=1e-8):
    """Check a returned solve and build an EXACT dual outer witness.

    Fractions encode the actual binary-float LP coefficients exactly, not an
    imagined continuous/native contract. Inequality multipliers are clipped to
    their required nonpositive sign; the probability-normalization multiplier
    is reduced by the worst reduced-cost deficit. This creates an exactly
    feasible dual. Primal feasibility and the outer/approximate-primal gap are
    also checked; they are numerical checks, not a continuous-tail certificate.
    """
    c = np.asarray(c, dtype=float)
    try:
        x = np.asarray(result.x, dtype=float)
        ey = np.asarray(result.eqlin.marginals, dtype=float)
        iz = np.asarray(result.ineqlin.marginals, dtype=float) if aub is not None else np.zeros(0)
        if not result.success or x.shape != c.shape or ey.shape != beq.shape or (aub is not None and iz.shape != bub.shape):
            raise ValueError("certificate dimensions/status")
        if not all(np.all(np.isfinite(v)) for v in (x, ey, iz)) or not math.isfinite(float(result.fun)):
            raise ValueError("nonfinite certificate")
        primal = max(float(np.max(np.abs(aeq @ x - beq))), max(0., -float(np.min(x))))
        if aub is not None:
            primal = max(primal, max(0., float(np.max(aub @ x-bub))))
        if primal > tolerance or abs(float(c@x)-float(result.fun)) > tolerance:
            raise ValueError("primal/objective reconstruction")
        f = lambda v: Fraction.from_float(float(v))
        y = [f(v) for v in ey]
        z = [min(Fraction(), f(v)) for v in iz]
        rc = [f(c[j])-sum((f(aeq[k,j])*y[k] for k in range(len(y))), Fraction())
              - (sum((f(aub[k,j])*z[k] for k in range(len(z))), Fraction()) if aub is not None else Fraction())
              for j in range(len(c))]
        deficit = max(Fraction(), -min(rc))
        if not np.array_equal(aeq[0], np.ones(len(c))) or beq[0] != 1:
            raise ValueError("required probability normalization row")
        y[0] -= deficit
        exact_dual = sum((f(beq[k])*y[k] for k in range(len(y))), Fraction())
        if aub is not None:
            exact_dual += sum((f(bub[k])*z[k] for k in range(len(z))), Fraction())
        exact_primal_objective = sum((f(c[j])*f(x[j]) for j in range(len(c))), Fraction())
        gap = exact_primal_objective-exact_dual
        if abs(float(gap)) > tolerance:
            raise ValueError("primal/dual gap")
        # This outward conversion is weaker than the exact rational value.
        outer = math.nextafter(float(exact_dual), -math.inf)
        return outer, {"exact_dual_lower": str(exact_dual), "exact_dual_multipliers": [str(v) for v in y],
                       "exact_inequality_multipliers": [str(v) for v in z],
                       "exact_cash_correction": str(deficit), "maximum_primal_residual": primal,
                       "approximate_primal_dual_gap": float(gap),
                       "scope": "EXACT_DUAL_OUTER_BOUND_FOR_SUPPLIED_BINARY_FLOAT_FINITE_LP"}
    except (AttributeError, TypeError, IndexError) as exc:
        raise ValueError("BLOCKED: missing or malformed dual certificate") from exc


def _vector(name, values):
    raw = list(values)
    if any(isinstance(v, (bool, np.bool_)) for v in raw):
        raise ValueError(f"{name}: boolean is not a numeric observation")
    a = np.asarray(raw, dtype=float)
    if a.ndim != 1 or not np.all(np.isfinite(a)):
        raise ValueError(f"{name}: finite one-dimensional values required")
    return a


def quote_bounds(x, y, before_quotes, after_quotes, payoff, mean=1.0):
    """Bound E[payoff(X,Y)] over finite martingale laws and call quote boxes.

    Quotes are (strike, undiscounted_bid, undiscounted_ask), with all prices
    normalized to the SAME fixed futures-price unit. No early exercise or
    fixing average is present in this hypothetical contract definition.
    """
    x, y = _vector("x", x), _vector("y", y)
    if not len(x) or not len(y) or np.any(x <= 0) or np.any(y <= 0):
        raise ValueError("Strictly positive nonempty state grids required")
    if np.any(np.diff(x) <= 0) or np.any(np.diff(y) <= 0):
        raise ValueError("State grids must be strictly increasing")
    if isinstance(mean, (bool, np.bool_)) or not math.isfinite(mean) or mean <= 0:
        raise ValueError("Positive finite mean required")
    h = np.asarray(payoff, dtype=float)
    if h.shape != (len(x), len(y)) or not np.all(np.isfinite(h)):
        raise ValueError("Finite payoff matrix with the grid shape required")
    n = len(x) * len(y)
    eq = [np.ones(n), np.repeat(x, len(y))]
    rhs = [1.0, float(mean)]
    for i in range(len(x)):
        row = np.zeros((len(x), len(y)))
        row[i, :] = y - x[i]
        eq.append(row.ravel())
        rhs.append(0.0)
    ub, ub_rhs = [], []
    for axis, quotes in ((0, before_quotes), (1, after_quotes)):
        for quote in quotes:
            q = _vector("quote", quote)
            if len(q) != 3:
                raise ValueError("A quote must have exactly three fields")
            strike, bid, ask = q
            if strike < 0 or bid < 0 or bid > ask:
                raise ValueError("Nonnegative strike/bid and ordered bid/ask required")
            row = (np.repeat(np.maximum(x - strike, 0.0), len(y)) if axis == 0
                   else np.tile(np.maximum(y - strike, 0.0), len(x)))
            ub.extend((row, -row))
            ub_rhs.extend((ask, -bid))
    aeq, beq = np.asarray(eq), np.asarray(rhs)
    aub = np.asarray(ub) if ub else None
    bub = np.asarray(ub_rhs) if ub else None
    fits = [linprog(sign * h.ravel(), A_ub=aub, b_ub=bub,
                    A_eq=aeq, b_eq=beq, bounds=(0.0, None), method="highs")
            for sign in (1.0, -1.0)]
    if any(not r.success for r in fits):
        raise ValueError("BLOCKED: no feasible law or solver failure; quotes are not repaired")
    residuals = []
    for r in fits:
        residuals.append(float(np.max(np.abs(aeq @ r.x - beq))))
        residuals.append(max(0.0, -float(np.min(r.x))))
        if aub is not None:
            residuals.append(max(0.0, float(np.max(aub @ r.x - bub))))
    residual = max(residuals)
    if residual > 1e-8:
        raise ValueError("BLOCKED: unacceptable primal residual")
    low, low_cert = validate_certificate(h.ravel(), aeq, beq, aub, bub, fits[0])
    neg_high, high_cert = validate_certificate(-h.ravel(), aeq, beq, aub, bub, fits[1])
    high = math.nextafter(-neg_high, math.inf)
    if low > high + 1e-8:
        raise ValueError("BLOCKED: bounds reversed")
    return Bounds(low, high, fits[0].x.reshape(h.shape),
                  fits[1].x.reshape(h.shape), residual,
                  lower_certificate=low_cert, upper_certificate=high_cert)


def crossing_payoff(x, y, threshold):
    if isinstance(threshold, (bool, np.bool_)) or not math.isfinite(threshold) or threshold <= 0:
        raise ValueError("Positive finite threshold required")
    x, y = _vector("x", x), _vector("y", y)
    return (((x[:, None] <= 1.0) & (y[None, :] >= 1.0 + threshold)).astype(float)
            - ((x[:, None] >= 1.0) & (y[None, :] <= 1.0 - threshold)).astype(float))
