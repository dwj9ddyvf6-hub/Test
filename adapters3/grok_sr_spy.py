"""v3 sleeve module for grok_sr_spy (GROK-SR-SPY-SPEC-2026-10-28).

Strategy in sleeves/grok_sr_spy.py; plumbing adapter in
adapters/grok_sr_spy.py. This module is only the v3 worker
entrypoint: evaluate(view, ctx) rebuilds the v2 SleeveContext from the
cycle snapshot and delegates. INPUTS is the producer-registry
declaration: 'bars' + 'bars_1min' + the literal 'bars:SPY:1Min' key
(added to producers_g4._BARS_TF_KEYS at install) keep the sleeve FED
on the warm SPY 1-minute SIP product.
"""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "grok_sr_spy"
INPUTS = ['bars', 'bars_1min', 'bars:SPY:1Min', 'positions', 'quotes', 'session_fills']


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return importlib.import_module("adapters.grok_sr_spy").evaluate(sctx) or []
