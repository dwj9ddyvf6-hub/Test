"""v3 sleeve module for ema_vwap — faithful port (batch 2).

Strategy + v2 adapter are byte-identical copies under sleeves/ and
adapters/ (hash-pinned by tests/test_port_batch2_blockers.py). This
module is only the v3 worker entrypoint: evaluate(view, ctx) rebuilds
the v2 SleeveContext from the cycle snapshot and delegates.
"""
from adapters3._snapshot_ctx import evaluate_ported
from desk3.enhance15 import filter_entries

SLEEVE_ID = "ema_vwap"


def evaluate(view, ctx):
    return filter_entries(SLEEVE_ID, evaluate_ported(SLEEVE_ID, view, ctx), view)
