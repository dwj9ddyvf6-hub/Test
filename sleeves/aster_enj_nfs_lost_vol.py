"""v3 sleeve aster_enj_nfs_lost_vol — Aster batch 8 (negative_funding_squeeze ENJUSDT). See desk3/aster_batch8.py + FIDELITY-LEDGER.md ASTER-B8."""
from desk3.aster_batch8 import evaluate as _ev, INPUTS_CRYPTO as INPUTS, PRODUCERS
SLEEVE_ID="aster_enj_nfs_lost_vol"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
