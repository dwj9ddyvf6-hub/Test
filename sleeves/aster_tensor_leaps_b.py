"""v3 sleeve aster_tensor_leaps_b — Aster batch 3. See desk3/aster_batch3.py + FIDELITY-LEDGER.md (ASTER-B3)."""
from desk3.aster_batch3 import evaluate as _ev, INPUTS, PRODUCERS
SLEEVE_ID = "aster_tensor_leaps_b"
INPUTS = INPUTS
PRODUCERS = PRODUCERS
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
