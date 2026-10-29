"""v3 sleeve module for trullas_v01 (S1: 5-minute bars).

Variant of trullas_divergence per TRULLAS-VARIANTS-SPEC-2026-10-29
(FROZEN). Strategy in sleeves/trullas_v01.py (thin subclass of the primary);
plumbing adapter in adapters/trullas_v01.py. INPUTS is the producer-registry
declaration: 'bars' + 'bars_5min' + the literal 'bars:QQQ:5Min' key
(added to producers_g4._BARS_TF_KEYS at this variant's install) keep the sleeve FED
on the warm QQQ 5Min SIP product.
"""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "trullas_v01"
INPUTS = ['bars', 'bars_5min', 'bars:QQQ:5Min', 'positions', 'quotes', 'session_fills']


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return importlib.import_module("adapters.trullas_v01").evaluate(sctx) or []
