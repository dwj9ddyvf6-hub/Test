"""v3 sleeve aster_r19_enjusdt_absorption_negative_funding_fixed16_volume1pct — Aster batch 7 (R19 ENJUSDT). See desk3/aster_batch7.py + FIDELITY-LEDGER.md (ASTER-B7)."""
from desk3.aster_batch7 import evaluate as _ev, inputs_for
SLEEVE_ID="aster_r19_enjusdt_absorption_negative_funding_fixed16_volume1pct"
INPUTS=inputs_for(SLEEVE_ID)
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
