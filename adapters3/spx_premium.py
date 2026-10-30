"""v3 sleeve module for spx_premium — faithful port (batch 7).

Strategy + v2 adapter are byte-identical copies under sleeves/ and
adapters/ (hash-pinned by tests/test_port_b7_blockers.py). This module
is only the v3 worker entrypoint: evaluate(view, ctx) rebuilds the v2
SleeveContext from the cycle snapshot and delegates. The journal path
is set on the context so the v2 persisted-journal channel
(serve_journal / gpt_v02_journal) works across cycles."""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

from desk3.enhance26 import filter_entries

SLEEVE_ID = "spx_premium"
INPUTS = ['bars', 'options']


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return filter_entries(SLEEVE_ID,
        importlib.import_module("adapters.spx_premium").evaluate(sctx) or [],
        view)
