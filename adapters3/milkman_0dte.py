"""v3 sleeve module for mk_zerodte_spx (Milkman 0DTE SPX).

Strategy in sleeves/milkman_0dte.py; plumbing adapter in
adapters/milkman_0dte.py. This module is only the v3 worker
entrypoint: evaluate(view, ctx) rebuilds the v2 SleeveContext from
the cycle snapshot and delegates.

INPUTS is the producer-registry declaration. 'milkman_0dte_chain'
(the SPX 0DTE chain in the authored row shape, greeks included) has
NO producer on this desk: the options producer serves SPY/QQQ/IWM/
XSP via feed=indicative, which carries no greeks, and SPX is not in
its underlying set. Declaring the key by name keeps the sleeve
visibly UNFED in the registry, never fake-fed, until a
greeks-bearing SPX route is proven (desk3/milkman_0dte/spx_probe.py
is the evidence path; PROVENANCE.md gaps 1-2 name both blockers).
The config row is parked: true for the same reasons.
"""
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "mk_zerodte_spx"
INPUTS = ['bars', 'positions', 'milkman_0dte_chain']


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    return importlib.import_module("adapters.milkman_0dte").evaluate(sctx) or []
