"""v3 sleeve aster_r19_linkusdt_absorption_negative_funding_fixed16_fullcash — Aster crypto batch 11 (LINKUSDT fixed16). See desk3/aster_b11_crypto.py."""
from desk3.aster_b11_crypto import evaluate as _ev, INPUTS
SLEEVE_ID="aster_r19_linkusdt_absorption_negative_funding_fixed16_fullcash"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
