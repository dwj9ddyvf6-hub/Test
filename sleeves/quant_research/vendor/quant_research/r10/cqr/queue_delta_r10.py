"""R10 one-period LP, resource-normalized and independently certified.

Version r10-row-scaled-v1; copied from immutable R4 reference.

No payment timing, taxes, inventories, integer setups or terminal value are
implemented. Units are contract units, resource units, and USD. SciPy is an
existing runtime dependency; no external data, authentication or orders.
"""
from dataclasses import dataclass
from math import isfinite
from numbers import Real
from typing import Sequence

import numpy as np
from scipy.optimize import linprog


def _number(value, label, nonnegative=False):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a real number, not a boolean")
    if not isfinite(float(value)) or (nonnegative and value < 0):
        raise ValueError(f"{label} must be finite" + (" and nonnegative" if nonnegative else ""))
    return float(value)


@dataclass(frozen=True)
class Order:
    name: str
    quantity: float
    contribution_usd_per_unit: float
    resource_per_unit: tuple[float, ...]
    mandatory: bool
    shortfall_penalty_usd_per_unit: float | None = None


def solve_book(orders: Sequence[Order], capacity: Sequence[float], fixed_net_cash=0.0):
    """Maximize avoidable contribution less documented mandatory shortfall cost.

    Optional demand is merely an upper bound, not a funding commitment. Mandatory
    orders cannot be discarded without explicitly paying their given penalty.
    Choosing that penalty correctly is outside this reference kernel's scope.
    """
    caps = np.array([_number(v, "capacity", True) for v in capacity])
    if len(caps) == 0:
        raise ValueError("at least one documented resource is required")
    fixed = _number(fixed_net_cash, "fixed net cash")
    names = [o.name for o in orders]
    if any(not isinstance(v, str) or not v for v in names) or len(set(names)) != len(names):
        raise ValueError("order names must be nonempty and unique")
    if len(orders) == 0:
        return {"value_usd": fixed, "delivered": {}, "shortfall": {},
                "resource_used": [0.0] * len(caps), "capacity_shadow_usd_per_unit": [0.0] * len(caps)}
    n = len(orders)
    qty = []
    margin = []
    penalties = []
    resource = []
    bounds = []
    eq_rows = []
    eq_rhs = []
    for i, order in enumerate(orders):
        if not isinstance(order.mandatory, bool):
            raise ValueError("mandatory must be a boolean")
        q = _number(order.quantity, "quantity", True)
        m = _number(order.contribution_usd_per_unit, "contribution")
        if order.mandatory and order.shortfall_penalty_usd_per_unit is None:
            raise ValueError("Mandatory order requires an explicit documented shortfall remedy; unknown is not zero")
        p = _number(0.0 if order.shortfall_penalty_usd_per_unit is None else order.shortfall_penalty_usd_per_unit, "penalty", True)
        a = [_number(v, "resource coefficient", True) for v in order.resource_per_unit]
        if len(a) != len(caps) or (q > 0 and not any(v > 0 for v in a)):
            raise ValueError("resource dimensions must match and positive delivery must consume a resource")
        if not order.mandatory and p != 0:
            raise ValueError("optional demand has no contractual shortfall penalty in this kernel")
        qty.append(q)
        margin.append(m)
        penalties.append(p)
        resource.append(a)
        bounds.append((0.0, 1.0 if q > 0 else 0.0))
        if order.mandatory:
            row = np.zeros(2 * n)
            row[i] = row[n + i] = 1.0
            eq_rows.append(row)
            eq_rhs.append(1.0 if q > 0 else 0.0)
    bounds += [(0.0, 1.0 if orders[i].mandatory and qty[i] > 0 else 0.0) for i in range(n)]
    a_ub = np.zeros((len(caps), 2 * n))
    a_ub[:, :n] = np.asarray(resource).T * np.asarray(qty)[None, :]
    if np.any((np.asarray(resource).T > 0) & (np.asarray(qty)[None, :] > 0) & (a_ub[:, :n] == 0)):
        raise ValueError("Resource coefficient underflow")
    # Resource-unit invariance: normalize each physical row before HiGHS.
    # Tight tolerances alone cannot restore coefficients discarded by the solver.
    row_scale = np.maximum(np.max(np.abs(a_ub), axis=1), caps)
    row_scale[row_scale == 0] = 1.0
    scaled_a = a_ub / row_scale[:, None]
    scaled_caps = caps / row_scale
    positive = scaled_a[scaled_a > 0]
    if positive.size and np.min(positive) <= 1e-9:
        raise ValueError("Resource row dynamic range exceeds certified solver domain")
    objective = np.r_[-np.asarray(margin)*np.asarray(qty), np.asarray(penalties)*np.asarray(qty)]
    objective_scale = float(np.max(np.abs(objective))) or 1.0
    scaled_objective = objective / objective_scale
    nz = np.abs(scaled_objective[scaled_objective != 0])
    if nz.size and np.min(nz) <= 1e-9:
        raise ValueError("Objective dynamic range exceeds certified solver domain")
    result = linprog(scaled_objective,
                     A_ub=scaled_a, b_ub=scaled_caps,
                     A_eq=np.asarray(eq_rows) if eq_rows else None,
                     b_eq=np.asarray(eq_rhs) if eq_rhs else None,
                     bounds=bounds, method="highs",
                     options={"primal_feasibility_tolerance":1e-9,
                              "dual_feasibility_tolerance":1e-9})
    if not result.success:
        raise RuntimeError(f"queue LP failed: status {result.status}")
    used = a_ub @ result.x
    scaled_used = scaled_a @ result.x
    local_tol = 2e-8 * np.maximum(1.0, np.abs(scaled_caps))
    if (np.any(scaled_used > scaled_caps + local_tol) or
        np.any(result.x < -2e-8) or
        any(caps[r] == 0 and used[r] > 0 for r in range(len(caps)))):
        raise RuntimeError("solver returned an invalid physical allocation")
    actual_x = result.x * np.r_[np.asarray(qty), np.asarray(qty)]
    for i in range(n):
        tol = 2e-8 * max(1.0, qty[i])
        if actual_x[i] > qty[i] + tol or actual_x[n+i] > (qty[i] if orders[i].mandatory else 0.0) + tol:
            raise RuntimeError("solver violated quantity bounds")
        if orders[i].mandatory and abs(actual_x[i] + actual_x[n+i] - qty[i]) > tol:
            raise RuntimeError("solver violated mandatory quantity conservation")
    recomputed_objective = float(objective @ result.x)
    if not np.isfinite(recomputed_objective) or not np.isfinite(result.fun):
        raise RuntimeError("nonfinite objective")
    if abs(recomputed_objective - result.fun*objective_scale) > 2e-8*max(1.0, abs(recomputed_objective)):
        raise RuntimeError("solver objective mismatch")
    value = float(-recomputed_objective + fixed)
    if not isfinite(value):
        raise ValueError("Book value outside finite numeric domain")
    return {"value_usd": value,
            "delivered": dict(zip(names, map(float, actual_x[:n]))),
            "shortfall": dict(zip(names, map(float, actual_x[n:]))),
            "resource_used": used.tolist(),
            "capacity_shadow_usd_per_unit": (-result.ineqlin.marginals * objective_scale / row_scale).tolist()}


def paired_delta(before, after, capacity, net_settlement_usd=0.0):
    """Both books see exactly the same physical capacity, avoiding state mismatch."""
    settlement = _number(net_settlement_usd, "settlement")
    old = solve_book(before, capacity)
    new = solve_book(after, capacity)
    return {"before": old, "after": new, "net_settlement_usd": settlement,
            "delta_usd": new["value_usd"] - old["value_usd"] + settlement}
