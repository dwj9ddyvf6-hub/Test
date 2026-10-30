"""v3 sleeve module for daily_cyan_gbm — faithful port (batch 1).

Strategy + v2 adapter are byte-identical copies under sleeves/ and
adapters/ (strategy hash-pinned by tests/test_port_batch1_blockers.py).
This module is only the v3 worker entrypoint: evaluate(view, ctx)
rebuilds the v2 SleeveContext from the cycle snapshot and delegates.
INPUTS is the producer-registry declaration for this sleeve.
"""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "daily_cyan_gbm"
INPUTS = ['bars', 'positions']


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return importlib.import_module("adapters.daily_cyan_gbm").evaluate(sctx) or []
