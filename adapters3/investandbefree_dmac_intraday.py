"""v3 sleeve module for investandbefree_dmac_intraday
(INVESTANDBEFREE-DMAC-VARIANTS-SPEC-2026-10-29).

Strategy in sleeves/investandbefree_dmac_intraday.py (thin subclass of the parameterized
base core); plumbing adapter in adapters/investandbefree_dmac_intraday.py. INPUTS is the
producer-registry declaration keeping this variant fed.
"""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "investandbefree_dmac_intraday"
INPUTS = ['bars', 'bars_5min', 'bars:SPY:5Min', 'bars:QQQ:5Min', 'options', 'positions', 'quotes', 'session_fills']


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return importlib.import_module(
        "adapters.investandbefree_dmac_intraday").evaluate(sctx) or []
