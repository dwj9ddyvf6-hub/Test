"""v3 sleeve module for trullas_divergence (PRIMARY ARM, TRULLAS-SPEC v1.0).

Strategy in sleeves/trullas_divergence.py; plumbing adapter in
adapters/trullas_divergence.py. This module is only the v3 worker
entrypoint: evaluate(view, ctx) rebuilds the v2 SleeveContext from the
cycle snapshot and delegates. INPUTS is the producer-registry
declaration: 'bars' + 'bars_1min' + the literal 'bars:QQQ:1Min' key
(added to producers_g4._BARS_TF_KEYS at install) keep the sleeve FED
on the warm QQQ 1-minute SIP product.
"""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "trullas_divergence"
INPUTS = ['bars', 'bars_1min', 'bars:QQQ:1Min', 'positions', 'quotes', 'session_fills']


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return importlib.import_module("adapters.trullas_divergence").evaluate(sctx) or []
