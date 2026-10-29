"""v3 Lazarus fire-consumer sleeve s_1dg (batch 1). Engine: desk3/lazarus.py.

ENH2 (Edge batch 18): stale_bar_gate post-filter via desk3.enhance18
(default ON; OFF via extra["s_1dg_enh2"]["stale_bar_gate"]=False).
"""
from desk3.lazarus import evaluate as _ev, INPUTS
from desk3.enhance18 import filter_entries
SLEEVE_ID = "s_1dg"
INPUTS = INPUTS
def evaluate(view, ctx):
    return filter_entries(SLEEVE_ID, _ev(SLEEVE_ID, view, ctx), view)
