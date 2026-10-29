"""Promotion gates adopted from the gestalt package (ANALYSIS.md "Where it goes further than us" 3 and 6, P2).

paper_promotion   the forward (paper) promotion gate. The gestalt bar is >= 30 closed broker-paper outcomes across >= 5
                  sessions under one frozen policy hash, with no simulated replay; P1/FACTORY §5 asks >= 60 forward
                  dates and >= 300 forecasts with a date-clustered t >= 2. The stricter of each is taken:
                  sessions >= max(5, 60) = 60, closed outcomes >= max(30, 300) = 300, one frozen policy hash on every
                  outcome, no replay or simulated source, and t >= 2 on the per-session means.
per_opportunity   the opportunity denominator: a mean over every eligible opportunity, a missed fill counting as its
                  no-fill value (0 R by default), never a mean over fills only (the filled-pullback lesson: a 31% fill
                  rate hid the edge's disappearance)."""
import math

import numpy as np

from . import score as S

GESTALT_MIN_OUTCOMES, GESTALT_MIN_SESSIONS = 30, 5
P1_MIN_FORECASTS, P1_MIN_DATES = 300, 60
MIN_OUTCOMES = max(GESTALT_MIN_OUTCOMES, P1_MIN_FORECASTS)
MIN_SESSIONS = max(GESTALT_MIN_SESSIONS, P1_MIN_DATES)
MIN_T = 2.0
SIMULATED = {"replay", "sim", "simulated", "backtest"}


def paper_promotion(outcomes, policy_hash):
    """outcomes: [{session, value, policy_hash, closed: bool, source}] -> {pass, reasons, n, sessions, t}"""
    reasons = []
    closed = [o for o in outcomes if o.get("closed")]
    if any(o.get("policy_hash") != policy_hash for o in closed):
        reasons.append("an outcome under another policy hash (the policy must stay frozen)")
    if any(str(o.get("source", "")).lower() in SIMULATED for o in closed):
        reasons.append("a simulated or replayed outcome (paper outcomes only)")
    good = [o for o in closed if o.get("policy_hash") == policy_hash
            and str(o.get("source", "")).lower() not in SIMULATED]
    sessions = sorted({o["session"] for o in good})
    if len(good) < MIN_OUTCOMES:
        reasons.append(f"{len(good)} closed outcomes < {MIN_OUTCOMES}")
    if len(sessions) < MIN_SESSIONS:
        reasons.append(f"{len(sessions)} sessions < {MIN_SESSIONS}")
    t = None
    if sessions:
        per = [np.mean([o["value"] for o in good if o["session"] == s]) for s in sessions]
        r = S.nw_t(per, 0)
        t = r["t"]
        if t is None or not math.isfinite(t) or t < MIN_T:
            reasons.append(f"session-clustered t {t} < {MIN_T}")
    return {"pass": not reasons, "reasons": reasons, "n": len(good), "sessions": len(sessions), "t": t}


def per_opportunity(values, filled, missed_value=0.0):
    """{mean, n_opportunities, n_filled, fill_rate, mean_if_filled}: every opportunity counts"""
    v = np.asarray(values, float)
    f = np.asarray(filled, bool)
    x = np.where(f, v, missed_value)
    n = len(x)
    return {"mean": float(x.mean()) if n else None, "n_opportunities": n, "n_filled": int(f.sum()),
            "fill_rate": float(f.mean()) if n else None,
            "mean_if_filled": float(v[f].mean()) if f.any() else None}
