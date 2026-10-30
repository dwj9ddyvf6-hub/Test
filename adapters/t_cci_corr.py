"""v3 sleeve module for t_cci_corr (CCI Correction Pullback).

Strategy in sleeves/t_cci_corr.py; plumbing adapter in
adapters/t_cci_corr.py. This module is only the v3 worker
entrypoint: evaluate(view, ctx) rebuilds the v2 SleeveContext from
the cycle snapshot and delegates. INPUTS is the producer-registry
declaration: 'bars' (daily SIP rows for the screening universe and
SPY) + 'bars:VIX:1Day' (the regime series) keep the sleeve FED.
"""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "t_cci_corr"
INPUTS = ['bars', 'bars:VIX:1Day', 'vix', 'positions', 'session_fills']


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return importlib.import_module("adapters.t_cci_corr").evaluate(sctx) or []
