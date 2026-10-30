"""v3 sleeve aster_r19_linkusdt_negative_funding_squeeze_fixed96_fullcash — Aster crypto batch 12 (LINKUSDT). See desk3/aster_b12_crypto.py + FIDELITY-LEDGER ASTER-B12."""
from desk3.aster_b12_crypto import evaluate as _ev, INPUTS
SLEEVE_ID="aster_r19_linkusdt_negative_funding_squeeze_fixed96_fullcash"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
