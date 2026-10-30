"""v3 sleeve aster_tensor_d20_pv — Aster batch 16. See desk3/aster_batch16.py + FIDELITY-LEDGER.md (ASTER-B16)."""
from desk3.aster_batch16 import evaluate as _ev, D20_INPUTS as INPUTS, PRODUCERS
SLEEVE_ID = "aster_tensor_d20_pv"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
