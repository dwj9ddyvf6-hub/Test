"""v3 Lazarus fire-consumer sleeve s_1dgp5 (batch 2). Engine: desk3/lazarus.py.

1D Green under $5 (CSV ON, Live). Catalog rule in desk3.lazarus SPECS + FIDELITY-LEDGER LAZ2.
"""
from desk3.lazarus import evaluate as _ev, INPUTS
from desk3.enhance18 import filter_entries
SLEEVE_ID = "s_1dgp5"
INPUTS = INPUTS
def evaluate(view, ctx):
    return filter_entries(SLEEVE_ID, _ev(SLEEVE_ID, view, ctx), view)
