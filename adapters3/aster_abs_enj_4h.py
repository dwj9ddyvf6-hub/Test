"""v3 sleeve aster_abs_enj_4h — Aster batch 1: Four-hour confirmed absorption ENJUSDT. Engine: desk3/aster_batch1.py."""
from desk3.aster_batch1 import evaluate as _ev, inputs_for, PRODUCERS
SLEEVE_ID = "aster_abs_enj_4h"
INPUTS = inputs_for(SLEEVE_ID)
PRODUCERS = PRODUCERS
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
