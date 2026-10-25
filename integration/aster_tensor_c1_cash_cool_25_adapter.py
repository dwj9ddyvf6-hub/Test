"""v3 sleeve aster_tensor_c1_cash_cool_25 — Aster batch 13. See desk3/aster_batch13.py + FIDELITY-LEDGER.md (ASTER-B13)."""
from desk3.aster_batch13 import evaluate as _ev, INPUTS_TENSOR as INPUTS, PRODUCERS
SLEEVE_ID="aster_tensor_c1_cash_cool_25"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
