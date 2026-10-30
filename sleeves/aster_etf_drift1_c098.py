"""v3 sleeve aster_etf_drift1_c098 — Aster batch 8 (etf). See desk3/aster_batch8.py + FIDELITY-LEDGER.md ASTER-B8."""
from desk3.aster_batch8 import evaluate as _ev, INPUTS_ETF as INPUTS, PRODUCERS
SLEEVE_ID="aster_etf_drift1_c098"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
