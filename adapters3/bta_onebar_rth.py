"""v3 sleeve module for bta_onebar_rth.

RTH variant: QQQ, regular session bars only, 15:55 ET flat.
Strategy in sleeves/bta_onebar_rth.py (base core sleeves/bta_onebar_qqq.py);
plumbing adapter in adapters/bta_onebar_rth.py. INPUTS is the
producer-registry declaration: the literal bars:SYM:30Min keys keep
the sleeve FED on the warm 30-minute SIP product.
"""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "bta_onebar_rth"
INPUTS = ['bars', 'bars_30min', 'bars:QQQ:30Min', 'positions', 'quotes', 'session_fills']


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return importlib.import_module("adapters.bta_onebar_rth").evaluate(sctx) or []
