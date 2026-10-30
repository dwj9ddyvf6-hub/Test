"""v3 Lazarus fire-consumer sleeve s_1wg_small (batch 2). Engine: desk3/lazarus.py.

1W Green tier A small (CSV off, Shadow). Catalog rule in desk3.lazarus SPECS + FIDELITY-LEDGER LAZ2.
"""
from desk3.lazarus import evaluate as _ev, INPUTS
SLEEVE_ID = "s_1wg_small"
INPUTS = INPUTS
def evaluate(view, ctx):
    return _ev(SLEEVE_ID, view, ctx)
