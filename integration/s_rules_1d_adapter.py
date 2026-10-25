"""v3 Lazarus fire-consumer sleeve s_rules_1d (batch 2). Engine: desk3/lazarus.py.

Lab rule 1D — 43 frozen rules (CSV ON, Live). Catalog rule in desk3.lazarus SPECS + FIDELITY-LEDGER LAZ2.
"""
from desk3.lazarus import evaluate as _ev, INPUTS
SLEEVE_ID = "s_rules_1d"
INPUTS = INPUTS
def evaluate(view, ctx):
    return _ev(SLEEVE_ID, view, ctx)
