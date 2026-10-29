"""v3 sleeve module for trullas_v04 (S4: TP2 at 66.7 percent).

Variant of trullas_divergence per TRULLAS-VARIANTS-SPEC-2026-10-29
(FROZEN). Strategy in sleeves/trullas_v04.py (thin subclass of the primary);
plumbing adapter in adapters/trullas_v04.py. INPUTS is the producer-registry
declaration: 'bars' + 'bars_1min' + the literal 'bars:QQQ:1Min' key
(the primary install's producer key, reused) keep the sleeve FED
on the warm QQQ 1Min SIP product.
"""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "trullas_v04"
INPUTS = ['bars', 'bars_1min', 'bars:QQQ:1Min', 'positions', 'quotes', 'session_fills']


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return importlib.import_module("adapters.trullas_v04").evaluate(sctx) or []
