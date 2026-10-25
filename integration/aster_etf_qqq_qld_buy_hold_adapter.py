"""v3 sleeve aster_etf_qqq_qld_buy_hold — Aster ETF batch 10. See desk3/aster_etf.py + FIDELITY-LEDGER.md."""
from desk3.aster_etf import evaluate as _ev, INPUTS, PRODUCERS
SLEEVE_ID="aster_etf_qqq_qld_buy_hold"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
