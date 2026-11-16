"""v3 sleeve module for soxl_pm_breakout (owner commission
2026-11-03: the TrendSpider SOXL PM-high breakout, hold to close).

Strategy in sleeves/soxl_pm_breakout.py; plumbing adapter in
adapters/soxl_pm_breakout.py. This module is only the v3 worker
entrypoint: evaluate(view, ctx) rebuilds the v2 SleeveContext from
the cycle snapshot and delegates. INPUTS is the producer-registry
declaration: 'bars' + the literal 'bars:SOXL:15Min' key declare
the 15-minute all-session SIP product the strategy consumes. No
producer serves bars:SOXL:15Min today (desk3/warm.py
INTRADAY_FETCHES and desk3/producers_g4.py _BARS_TF_KEYS carry no
SOXL 15Min slice), so the sleeve registers UNFED by name in the
health roll until that producer slice is added by the desk lane;
it never silently abstains.
"""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "soxl_pm_breakout"
INPUTS = ['bars', 'bars:SOXL:15Min', 'positions', 'quotes', 'session_fills']


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return importlib.import_module("adapters.soxl_pm_breakout").evaluate(sctx) or []
