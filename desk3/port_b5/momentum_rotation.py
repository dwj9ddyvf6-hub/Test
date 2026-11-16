"""v3 wrapper for momentum_rotation — strategy in sleeves/momentum_rotation.py (byte-identical
to v2), interface glue in adapters/momentum_rotation.py (byte-identical to v2).
INPUTS is the producer-registry declaration for this sleeve."""
from ._ctx import run as _run
from ._enh2 import run_enh2

SLEEVE_ID = "momentum_rotation"
INPUTS = ('bars', 'positions')
CADENCE_S = 300

# WEIGHT-LAG-20261031 (quants-mechanisms steal, mechanism 1)
# + WEIGHT-LAG-ACTIVE-20261031 (owner rulings 2026-10-31 10:39 ET
# and 2026-10-31 11:44 ET): the stolen form shifts target weights
# forward by 1 day at the engine layer to prevent look-ahead bias.
# The owner ruled the one-bar lag ON for the live books. The lag
# lives at this wrapper's consumption point (the v3 entrypoint; the
# byte-identical strategy port under sleeves/ is untouched): the
# intents the delegated book computes at one evaluation (from
# CLOSED daily bars only, bars[-1] is the last closed bar served)
# are held and emitted at the next evaluation. The first evaluation
# after activation therefore emits nothing for newly computed
# weights. A non-due rebalance returns no intents and does NOT
# advance the lag: pending intents are neither emitted early nor
# overwritten by an empty computation. Pending state persists
# under the cycle state_dir when one is served (weight_lag_pending
# .json beside the sleeve journal), in-memory otherwise. Pinned by
# tests/test_weight_lag_20261031_blockers.py.
WEIGHT_LAG_POLICY = {
    "mechanism": "weight-lag",
    "lag_bars": 1,
    "applied": True,
    "basis": "closed_bar_gating_only",
    "status": "ACTIVE",
    "reason": ("Shift weights forward by 1 day to prevent look-ahead "
               "bias (the engine-layer form). Applied here as a "
               "one-evaluation lag at the wrapper consumption point: "
               "intents computed from the last CLOSED bar at one "
               "evaluation are emitted at the next evaluation."),
    "ruling_needed": ("None: owner ruling 2026-10-31 10:39 ET "
                      "authorized the one-bar weight lag on the live "
                      "books and ruling 2026-10-31 11:44 ET authorized "
                      "landing it; entries and rebalances fire one "
                      "evaluation later by design."),
}

# WEIGHT-LAG-ACTIVE-20261031: in-memory pending fallback, used when
# no state_dir is served on the cycle ctx.
_PENDING_IN_MEMORY = {}


def _weight_lag_pending_path(ctx):
    sd = (ctx or {}).get("state_dir") if isinstance(ctx, dict) else None
    if not sd:
        return None
    import os
    return os.path.join(sd, "weight_lag_pending.json")


def _weight_lag_load(ctx):
    """(found, pending_intents) for this book's lag state."""
    path = _weight_lag_pending_path(ctx)
    if path is None:
        if SLEEVE_ID in _PENDING_IN_MEMORY:
            return True, _PENDING_IN_MEMORY[SLEEVE_ID]
        return False, []
    import json
    import os
    if not os.path.exists(path):
        return False, []
    try:
        with open(path) as fh:
            data = json.load(fh)
    except Exception:
        return False, []
    if isinstance(data, dict) and isinstance(data.get("intents"), list):
        return True, data["intents"]
    return False, []


def _weight_lag_store(ctx, intents):
    path = _weight_lag_pending_path(ctx)
    if path is None:
        _PENDING_IN_MEMORY[SLEEVE_ID] = intents
        return
    import json
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump({"mechanism": "weight-lag", "sleeve": SLEEVE_ID,
                   "intents": intents}, fh)


def _apply_weight_lag(fresh, ctx):
    """Hold this evaluation's intents; emit the previous ones.

    Empty fresh intents (a non-due rebalance) neither emit the
    pending intents early nor overwrite them: the lag advances
    only when weights were actually computed."""
    if not fresh:
        return []
    found, pending = _weight_lag_load(ctx)
    _weight_lag_store(ctx, list(fresh))
    if not found:
        return []
    return pending


# REBALANCE-POLICY-20261031 (quants-mechanisms steal, mechanism 6)
# + REBALANCE-ENFORCE-20261031 (owner ruling 2026-10-31):
# rebalance policy as a first-class object, ENFORCED for exactly
# the dimensions this book declares concrete values for, stated
# once here (the v3 entrypoint; the byte-identical strategy port
# under sleeves/ is untouched). Frequency is the book's own spec:
# weekly, enforced in the delegated strategy's rebalance path
# (sleeves/momentum_rotation.py REBALANCE_DAYS = 7; its signal()
# returns no intents until rebalance_due(last_rebalance, today)),
# and when due the book rebalances on its rank/signal change
# (signal_change_rebalance True). There is no drift band, no
# tracking-error trigger and no turnover budget declared on this
# book (explicit Nones), so those dimensions stay
# declared_not_enforced and are named in ruling_needed; no value
# was invented for them. Trading toward the target is full, not
# partial. The dispatcher never reads this object; pinned by
# tests/test_rebalance_policy_20261031_blockers.py. The contract
# object is desk3.contract.RebalancePolicy.
REBALANCE_POLICY = {
    "mechanism": "rebalance-policy",
    "frequency": "weekly",
    "drift_threshold": None,
    "drift_type": None,
    "partial_rebalance": False,
    "tracking_error_threshold": None,
    "tracking_error_window_days": None,
    "max_annual_turnover": None,
    "signal_change_rebalance": True,
    "execution_timing": "on_evaluation",
    "enforcement": "enforced_for_declared_dimensions",
    "status": "ACTIVE_DECLARED_DIMENSIONS_ONLY",
    "enforced_dimensions": ["frequency", "signal_change_rebalance"],
    "declared_only_dimensions": ["drift_threshold",
                                 "tracking_error_threshold",
                                 "max_annual_turnover"],
    "ruling_needed": ("A declared value for a drift band, a "
                      "tracking-error trigger, or a turnover "
                      "budget on the live books: none is declared "
                      "today (all explicit Nones), so those "
                      "dimensions cannot be enforced until a "
                      "value is declared by ruling."),
}


def evaluate(view, ctx):
    fresh = run_enh2("momentum_rotation", view, ctx, _run)
    return _apply_weight_lag(fresh, ctx)
