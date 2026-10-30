"""v3 sleeve module for confluence — faithful port (batch 1).

Strategy + v2 adapter are byte-identical copies under sleeves/ and
adapters/ (strategy hash-pinned by tests/test_port_batch1_blockers.py).
This module is only the v3 worker entrypoint: evaluate(view, ctx)
rebuilds the v2 SleeveContext from the cycle snapshot and delegates.
INPUTS is the producer-registry declaration for this sleeve.
"""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "confluence"
INPUTS = ['bars', 'positions']


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    from desk3.enhance14 import filter_entries
    return filter_entries(SLEEVE_ID, importlib.import_module(
        "adapters.confluence").evaluate(sctx) or [], view)
