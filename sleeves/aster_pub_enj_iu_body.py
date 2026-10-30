"""v3 sleeve aster_pub_enj_iu_body — Aster batch 4. See desk3/aster_b4.py + FIDELITY-LEDGER.md (ASTER-B4)."""
from desk3.aster_b4 import evaluate_enj_iu_body as _f, PUB_INPUTS, PRODUCERS
SLEEVE_ID="aster_pub_enj_iu_body"
INPUTS=PUB_INPUTS
PRODUCERS=PRODUCERS
def evaluate(view, ctx=None):
    return _f(view, ctx, SLEEVE_ID)
