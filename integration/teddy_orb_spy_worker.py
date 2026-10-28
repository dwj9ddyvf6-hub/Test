"""v3 sleeve module for teddy_orb_spy (TEDDY-ORB-SPY-SPEC-2026-10-28).

Strategy in sleeves/teddy_orb_spy.py; plumbing adapter in
adapters/teddy_orb_spy.py. This module is only the v3 worker
entrypoint: evaluate(view, ctx) rebuilds the v2 SleeveContext from the
cycle snapshot and delegates. INPUTS is the producer-registry
declaration: 'bars' + 'bars_1min' + the literal 'bars:SPY:1Min' key
(the grok_sr_spy install's producer key, reused with zero producer
edits) keep the sleeve FED on the warm SPY 1-minute SIP product; the
core aggregates those 1-minute bars into 5-minute bars itself,
because the desk serves no native bars:SPY:5Min key.
"""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "teddy_orb_spy"
INPUTS = ['bars', 'bars_1min', 'bars:SPY:1Min', 'positions', 'quotes', 'session_fills']


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return importlib.import_module("adapters.teddy_orb_spy").evaluate(sctx) or []
