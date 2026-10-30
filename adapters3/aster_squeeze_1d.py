"""v3 sleeve aster_squeeze_1d — Aster batch 1: Volatility-squeeze breakout 1d (TRADER_SQUEEZE20). Engine: desk3/aster_batch1.py."""
from desk3.aster_batch1 import evaluate as _ev, inputs_for, PRODUCERS
SLEEVE_ID = "aster_squeeze_1d"
INPUTS = inputs_for(SLEEVE_ID)
PRODUCERS = PRODUCERS
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
