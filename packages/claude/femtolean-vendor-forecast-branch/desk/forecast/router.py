"""The router (FACTORY.md §6) is phase P3. P2 ships its precondition only, from the gestalt package (ANALYSIS.md
"Where it goes further than us" 1): a forecast is routed to an instrument only when the lower confidence bound of its
incremental portfolio utility over the best alternative (flat included) is above zero; otherwise DON'T-KNOW.

  delta_u_lower_bound(u, alternatives, z)  u: per-date utility samples of the candidate action; alternatives: {name:
                                           per-date samples} on the same dates (flat = zeros is always added). The
                                           best alternative is the one with the highest mean; LB = mean(d) - z sd(d) /
                                           sqrt(T_eff) on d = u - u_best, T_eff by score.nw_t (Newey-West, lags)
  precondition(...)                        {"route": bool, "lb", "best_alternative"}; route only when lb > 0
  route(...)                               P3: raises NotImplementedError after the precondition passes; DON'T-KNOW
                                           when it fails"""
import math

import numpy as np

from . import score as S

Z = 1.645
DONT_KNOW = "DON'T-KNOW"


def delta_u_lower_bound(u, alternatives=None, z=Z, lags=0):
    u = np.asarray(u, float)
    alts = {"flat": np.zeros_like(u)}
    alts.update({k: np.asarray(v, float) for k, v in (alternatives or {}).items()})
    best = max(alts, key=lambda k: float(np.nanmean(alts[k])))
    d = u - alts[best]
    d = d[np.isfinite(d)]
    r = S.nw_t(d, lags)
    if r["sd"] is None or r["T_eff"] is None:
        return None, best
    return r["mean"] - z * r["sd"] / math.sqrt(r["T_eff"]), best


def precondition(u, alternatives=None, z=Z, lags=0):
    lb, best = delta_u_lower_bound(u, alternatives, z, lags)
    return {"route": lb is not None and lb > 0, "lb": lb, "best_alternative": best}


def route(forecast, u, alternatives=None):
    pre = precondition(u, alternatives)
    if not pre["route"]:
        return {"instrument": DONT_KNOW, "reason": f"delta-U lower bound {pre['lb']} <= 0 vs {pre['best_alternative']}"}
    raise NotImplementedError("the router table is phase P3 (FACTORY.md §6); only its precondition ships in P2")
