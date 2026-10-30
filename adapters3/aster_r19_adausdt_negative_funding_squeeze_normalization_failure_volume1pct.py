"""Aster batch 6 sleeve aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct — desk3/aster_crypto.py + FIDELITY-LEDGER ASTER-B6."""
from desk3.aster_crypto import evaluate as _ev, INPUTS
SLEEVE_ID="aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
