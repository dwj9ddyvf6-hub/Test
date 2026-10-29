"""v3 sleeve module for przm_fade_edges (PRZM-RECREATION-SPEC-2026-10-29).

Strategy in sleeves/przm_fade_edges.py; plumbing adapter in
adapters/przm_fade_edges.py. PARKED: the options_chain producer serves delta-only rows (no greeks, no open interest), so gamma levels cannot be computed
from any route that exists today (named reason in config
and the sleeve docstring); the engine is complete and fixture-proven
so unparking is a data-route event. INPUTS keeps the SPY 1-minute SIP
bars + options_chain declarations the engine will consume.
"""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "przm_fade_edges"
INPUTS = ['bars', 'bars_1min', 'bars:SPY:1Min', 'options', 'options_chain', 'positions', 'quotes', 'session_fills']


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return importlib.import_module("adapters.przm_fade_edges").evaluate(sctx) or []
