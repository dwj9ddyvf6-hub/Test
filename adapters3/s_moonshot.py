"""v3 Lazarus fire-consumer sleeve s_moonshot (batch 2). Engine: desk3/lazarus.py.

Moonshot (CSV off, Shadow). Catalog rule in desk3.lazarus SPECS + FIDELITY-LEDGER LAZ2.
"""
from desk3.lazarus import evaluate as _ev, INPUTS
SLEEVE_ID = "s_moonshot"
INPUTS = INPUTS
def evaluate(view, ctx):
    return _ev(SLEEVE_ID, view, ctx)
