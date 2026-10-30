"""v3 Lazarus fire-consumer sleeve s_1wsw (batch 1). Engine: desk3/lazarus.py."""
from desk3.lazarus import evaluate as _ev, INPUTS
SLEEVE_ID = "s_1wsw"
INPUTS = INPUTS
def evaluate(view, ctx):
    return _ev(SLEEVE_ID, view, ctx)
