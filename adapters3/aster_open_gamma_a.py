"""v3 sleeve aster_open_gamma_a — Aster batch 1: Opening-range options long 2.0% risk (OPT_OPENING_GAMMA_A). Engine: desk3/aster_batch1.py."""
from desk3.aster_batch1 import evaluate as _ev, inputs_for, PRODUCERS
SLEEVE_ID = "aster_open_gamma_a"
INPUTS = inputs_for(SLEEVE_ID)
PRODUCERS = PRODUCERS
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
