"""v3 sleeve module for investandbefree_dmac
(INVESTANDBEFREE-DMAC-SPEC-2026-10-29).

Strategy in sleeves/investandbefree_dmac.py; plumbing adapter in
adapters/investandbefree_dmac.py. This module is only the v3 worker
entrypoint: evaluate(view, ctx) rebuilds the v2 SleeveContext from
the cycle snapshot and delegates. INPUTS is the producer-registry
declaration: 'bars' plus the wildcard 'bars:*:1Day' / 'bars:*:1Hour'
/ 'bars:*:1Week' keys (already in producers_g4._BARS_TF_KEYS) keep
the sleeve fed on the warm SPY/QQQ daily, hourly and weekly
products; 'options' is the established options-chain input.
"""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "investandbefree_dmac"
INPUTS = ['bars', 'bars:*:1Day', 'bars:*:1Hour', 'bars:*:1Week',
          'options', 'positions', 'quotes', 'session_fills']


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return importlib.import_module(
        "adapters.investandbefree_dmac").evaluate(sctx) or []
