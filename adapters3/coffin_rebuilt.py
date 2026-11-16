"""v3 sleeve module for coffin_rebuilt (owner ruling 2026-11-09:
the desk exists to test individual sleeves; CAND-ROT-04 "The Coffin
Rebuilt" executes on the desk as a paper sleeve).

Strategy in sleeves/coffin_rebuilt.py; plumbing adapter in
adapters/coffin_rebuilt.py. This module is only the v3 worker
entrypoint: evaluate(view, ctx) rebuilds the v2 SleeveContext from
the cycle snapshot and delegates. INPUTS declares the snapshot
products the sleeve consumes: generic daily 'bars' (the adapter
requests 1Day bars for the 11 SPDR sector ETFs plus SPY) and
'positions' (the slice's broker read-back, for fill adoption).
"""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "coffin_rebuilt"
INPUTS = ['bars', 'positions']


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return importlib.import_module("adapters.coffin_rebuilt").evaluate(sctx) or []
