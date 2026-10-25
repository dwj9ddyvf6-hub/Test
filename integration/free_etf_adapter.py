"""v3 sleeve module for free_etf — faithful port (batch 2).

Strategy + v2 adapter are byte-identical copies under sleeves/ and
adapters/ (hash-pinned by tests/test_port_batch2_blockers.py). This
module is only the v3 worker entrypoint: evaluate(view, ctx) rebuilds
the v2 SleeveContext from the cycle snapshot and delegates.
"""
from adapters3._snapshot_ctx import evaluate_ported

SLEEVE_ID = "free_etf"


def evaluate(view, ctx):
    return evaluate_ported(SLEEVE_ID, view, ctx)
