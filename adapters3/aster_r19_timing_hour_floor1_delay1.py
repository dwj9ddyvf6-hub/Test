"""v3 sleeve aster_r19_timing_hour_floor1_delay1 — Aster batch 15. See desk3/aster_batch15.py + FIDELITY-LEDGER.md."""
from desk3.aster_batch15 import evaluate as _ev, PRODUCERS
SLEEVE_ID = "aster_r19_timing_hour_floor1_delay1"
INPUTS = ('bars', 'positions', 'quotes', 'timing_signals')
PRODUCERS = PRODUCERS
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
