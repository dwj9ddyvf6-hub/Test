"""v3 sleeve aster_rec_vwap20_vert_fixed_b — Aster batch 4. See desk3/aster_b4.py + FIDELITY-LEDGER.md (ASTER-B4)."""
from desk3.aster_b4 import evaluate as _ev, INPUTS_COMMON, INPUTS_XSP, PRODUCERS, PRODUCERS_XSP
SLEEVE_ID="aster_rec_vwap20_vert_fixed_b"
INPUTS=INPUTS_COMMON
PRODUCERS=PRODUCERS
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
