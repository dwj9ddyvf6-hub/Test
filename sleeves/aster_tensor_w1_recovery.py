"""v3 sleeve aster_tensor_w1_recovery — Aster batch 1: Tensor weekly state-repair recovery (WSTATE). Engine: desk3/aster_batch1.py."""
from desk3.aster_batch1 import evaluate as _ev, inputs_for, PRODUCERS
SLEEVE_ID = "aster_tensor_w1_recovery"
INPUTS = inputs_for(SLEEVE_ID)
PRODUCERS = PRODUCERS
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
