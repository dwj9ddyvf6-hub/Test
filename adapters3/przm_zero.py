"""v3 sleeve module for przm_zero (PRZM-RECREATION-SPEC-2026-10-29).

Strategy in sleeves/przm_zero.py; plumbing adapter in
adapters/przm_zero.py. PARKED: no signed options print-tape producer
exists on the desk today (named reason in config/sleeves.json params
and the sleeve docstring); the engine is complete and fixture-proven
so unparking is a data-route event. INPUTS keeps the SPY 1-minute SIP
bars + options_chain declarations the engine will consume.
"""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "przm_zero"
INPUTS = ['bars', 'bars_1min', 'bars:SPY:1Min', 'options', 'options_chain', 'positions', 'quotes', 'session_fills']


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return importlib.import_module("adapters.przm_zero").evaluate(sctx) or []
