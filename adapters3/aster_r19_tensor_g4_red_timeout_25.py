"""v3 sleeve aster_r19_tensor_g4_red_timeout_25 — Aster batch 15. See desk3/aster_batch15.py + FIDELITY-LEDGER.md."""
from desk3.aster_batch15 import evaluate as _ev, PRODUCERS
SLEEVE_ID = "aster_r19_tensor_g4_red_timeout_25"
INPUTS = ('tensor_fires', 'bars', 'positions')
PRODUCERS = PRODUCERS
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
