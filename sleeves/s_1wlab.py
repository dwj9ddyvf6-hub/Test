"""v3 Lazarus fire-consumer sleeve s_1wlab (batch 1). Engine: desk3/lazarus.py."""
from desk3.lazarus import evaluate as _ev, INPUTS
SLEEVE_ID = "s_1wlab"
INPUTS = INPUTS
def evaluate(view, ctx):
    return _ev(SLEEVE_ID, view, ctx)
