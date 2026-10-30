"""v3 sleeve aster_xsp_pcs_calm_a — Aster batch 4. See desk3/aster_b4.py + FIDELITY-LEDGER.md (ASTER-B4)."""
from desk3.aster_b4 import evaluate as _ev, INPUTS_COMMON, INPUTS_XSP, PRODUCERS, PRODUCERS_XSP
SLEEVE_ID="aster_xsp_pcs_calm_a"
INPUTS=INPUTS_XSP
PRODUCERS=PRODUCERS_XSP
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
