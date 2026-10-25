"""v3 sleeve aster_rec_vwap20_long_fixed_b — Aster batch 3. See desk3/aster_batch3.py + FIDELITY-LEDGER.md (ASTER-B3)."""
from desk3.aster_batch3 import evaluate as _ev, INPUTS, PRODUCERS
SLEEVE_ID = "aster_rec_vwap20_long_fixed_b"
INPUTS = INPUTS
PRODUCERS = PRODUCERS
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
