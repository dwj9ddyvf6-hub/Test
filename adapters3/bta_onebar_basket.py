"""v3 sleeve module for bta_onebar_basket.

Basket sleeve: SPY, QQQ, MDY, DIA independently, identical rules per symbol.
Strategy in sleeves/bta_onebar_basket.py (base core sleeves/bta_onebar_qqq.py);
plumbing adapter in adapters/bta_onebar_basket.py. INPUTS is the
producer-registry declaration: the literal bars:SYM:30Min keys keep
the sleeve FED on the warm 30-minute SIP product.
"""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "bta_onebar_basket"
INPUTS = ['bars', 'bars_30min', 'bars:SPY:30Min', 'bars:QQQ:30Min', 'bars:MDY:30Min', 'bars:DIA:30Min', 'positions', 'quotes', 'session_fills']


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return importlib.import_module("adapters.bta_onebar_basket").evaluate(sctx) or []
