"""v3 Lazarus fire-consumer sleeve 1dc (batch 1). Engine: desk3/lazarus.py."""
from desk3.lazarus import evaluate as _ev, INPUTS
SLEEVE_ID = "1dc"
INPUTS = INPUTS
def evaluate(view, ctx):
    return _ev(SLEEVE_ID, view, ctx)
