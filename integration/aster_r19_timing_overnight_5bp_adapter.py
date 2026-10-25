"""v3 sleeve aster_r19_timing_overnight_5bp — Aster batch 16. See desk3/aster_batch16.py + FIDELITY-LEDGER.md (ASTER-B16)."""
from desk3.aster_batch16 import evaluate as _ev, TIMING_INPUTS as INPUTS, PRODUCERS
SLEEVE_ID = "aster_r19_timing_overnight_5bp"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
