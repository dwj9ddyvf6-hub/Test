"""v3 sleeve aster_etf_drift1_m150 — Aster ETF batch 9. See desk3/aster_etf_b9.py + FIDELITY-LEDGER.md."""
from desk3.aster_etf_b9 import evaluate as _ev, inputs_for, PRODUCERS
SLEEVE_ID="aster_etf_drift1_m150"
INPUTS=inputs_for(SLEEVE_ID)
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
