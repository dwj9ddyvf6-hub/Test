"""v3 sleeve aster_link_nfs_norm_vol — Aster batch 13. See desk3/aster_batch13.py + FIDELITY-LEDGER.md (ASTER-B13)."""
from desk3.aster_batch13 import evaluate as _ev, INPUTS_CRYPTO as INPUTS, PRODUCERS
SLEEVE_ID="aster_link_nfs_norm_vol"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
