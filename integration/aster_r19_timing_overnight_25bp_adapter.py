"""v3 sleeve aster_r19_timing_overnight_25bp — Aster batch 15. See desk3/aster_batch15.py + FIDELITY-LEDGER.md."""
from desk3.aster_batch15 import evaluate as _ev, PRODUCERS
SLEEVE_ID = "aster_r19_timing_overnight_25bp"
INPUTS = ('bars', 'positions', 'quotes')
PRODUCERS = PRODUCERS
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
