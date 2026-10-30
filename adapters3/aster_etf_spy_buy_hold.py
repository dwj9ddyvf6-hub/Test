"""v3 sleeve aster_etf_spy_buy_hold — Aster ETF batch 11 (SPY buy-and-hold 100%). See desk3/aster_batch11.py + desk3/aster_etf.py."""
from desk3.aster_batch11 import ETF_INPUTS as INPUTS
from desk3.aster_etf import evaluate as _ev
SLEEVE_ID="aster_etf_spy_buy_hold"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
