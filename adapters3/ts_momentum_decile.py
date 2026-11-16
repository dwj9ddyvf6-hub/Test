"""v3 sleeve module for ts_momentum_decile — faithful port (batch 7).

Strategy + v2 adapter are byte-identical copies under sleeves/ and
adapters/ (hash-pinned by tests/test_port_b7_blockers.py). This module
is only the v3 worker entrypoint: evaluate(view, ctx) rebuilds the v2
SleeveContext from the cycle snapshot and delegates. The journal path
is set on the context so the v2 persisted-journal channel
(serve_journal / gpt_v02_journal) works across cycles."""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

from desk3.enhance26 import filter_entries

SLEEVE_ID = "ts_momentum_decile"
INPUTS = ['bars']

# WEIGHT-LAG-20261031 (quants-mechanisms steal, mechanism 1)
# + WEIGHT-LAG-ACTIVE-20261031 (owner rulings 2026-10-31 10:39 ET
# and 2026-10-31 11:44 ET): the stolen form shifts target weights
# forward by 1 day at the engine layer to prevent look-ahead bias.
# The owner ruled the one-bar lag ON for the live books. The lag
# lives at this wrapper's consumption point (the v3 entrypoint; the
# byte-identical strategy port under sleeves/ is untouched): the
# intents the delegated book computes at one evaluation (rank_decile
# drops the forming bar before ranking, so target weights rest on
# CLOSED bars only) are held and emitted at the next evaluation.
# The first evaluation after activation therefore emits nothing for
# newly computed weights. An evaluation that computes no weights
# (the monthly rebalance gate in evaluate() returns first, or the
# delegated book returns no intents) does NOT advance the lag:
# pending intents are neither emitted early nor overwritten by an
# empty computation. Pending state persists under the cycle
# state_dir when one is served (weight_lag_pending.json in the
# sleeve state dir), in-memory otherwise. Pinned by
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
               "intents computed from CLOSED bars at one evaluation "
               "are emitted at the next evaluation."),
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
    return os.path.join(sd, "weight_lag_pending.json")


def _weight_lag_load(ctx):
    """(found, pending_intents) for this book's lag state."""
    path = _weight_lag_pending_path(ctx)
    if path is None:
        if SLEEVE_ID in _PENDING_IN_MEMORY:
            return True, _PENDING_IN_MEMORY[SLEEVE_ID]
        return False, []
    if not os.path.exists(path):
        return False, []
    import json
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
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump({"mechanism": "weight-lag", "sleeve": SLEEVE_ID,
                   "intents": intents}, fh)


def _apply_weight_lag(fresh, ctx):
    """Hold this evaluation's intents; emit the previous ones.

    Empty fresh intents (no weights computed) neither emit the
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
# under sleeves/ is untouched). Frequency is the book's own frozen
# spec: monthly. The port emits its rebalance diff whenever called
# (its spec leaves gating to the caller), so the monthly gate
# lives here at the loaded entrypoint, with the desk's existing
# MONTHLY semantics (desk3/aster_etf.py): an evaluation whose
# holdings all entered in the current session month is suppressed
# (so an intra-month signal change cannot rebalance the book:
# signal_change_rebalance False, enforced by the same gate);
# initial allocation (no holdings) and a new entry month are
# allowed. There is no drift band, no tracking-error trigger and
# no turnover budget declared on this book (explicit Nones), so
# those dimensions stay declared_not_enforced and are named in
# ruling_needed; no value was invented for them. Trading toward
# the target is full, not partial. The dispatcher never reads
# this object; pinned by
# tests/test_rebalance_policy_20261031_blockers.py. The contract
# object is desk3.contract.RebalancePolicy.
REBALANCE_POLICY = {
    "mechanism": "rebalance-policy",
    "frequency": "monthly",
    "drift_threshold": None,
    "drift_type": None,
    "partial_rebalance": False,
    "tracking_error_threshold": None,
    "tracking_error_window_days": None,
    "max_annual_turnover": None,
    "signal_change_rebalance": False,
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


def _monthly_rebalance_suppressed(view, ctx):
    """REBALANCE-ENFORCE-20261031: the declared monthly frequency,
    enforced with aster_etf's MONTHLY semantics. True when every
    held position entered in the session's month (the book already
    rebalanced this month); False for initial allocation (no
    holdings), a new entry month, or an undatable session/holding
    (fail open to the pre-enforcement behavior, exactly as
    aster_etf's gate does)."""
    view = view or {}
    now = view.get("now") or (ctx or {}).get("now") or \
        (ctx or {}).get("session") or ""
    sess_month = str(now)[:7]
    if len(sess_month) != 7:
        return False
    positions = [p for p in (view.get("positions") or [])
                 if float(p.get("qty") or 0) != 0]
    if not positions:
        return False
    months = {str(p.get("entry_date") or p.get("opened_at") or "")[:7]
              for p in positions}
    return months == {sess_month}


def evaluate(view, ctx):
    import importlib
    if _monthly_rebalance_suppressed(view, ctx):
        return []
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    fresh = filter_entries(SLEEVE_ID,
        importlib.import_module("adapters.ts_momentum_decile").evaluate(sctx) or [],
        view)
    # WEIGHT-LAG-ACTIVE-20261031: the lag state lives beside the
    # sleeve journal in the same state dir the context resolved.
    lag_ctx = dict(ctx) if isinstance(ctx, dict) else {}
    lag_ctx.setdefault("state_dir", sctx._state_dir)
    return _apply_weight_lag(fresh, lag_ctx)
