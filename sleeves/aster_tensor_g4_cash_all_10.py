"""v3 sleeve aster_tensor_g4_cash_all_10 — Aster batch 14. See desk3/aster_batch14.py + FIDELITY-LEDGER.md (ASTER-B14)."""
from desk3.aster_batch14 import evaluate as _ev, INPUTS, PRODUCERS
SLEEVE_ID="aster_tensor_g4_cash_all_10"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
