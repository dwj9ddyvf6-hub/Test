"""v3 sleeve aster_etf_qqq_qld_monthly_inv — CONV-21 inverted form of
aster_etf_qqq_qld_monthly (Conversion Register CONV-21, QLD monthly
inversion). See desk3/aster_etf.py CONV21-INVERT-20261116: negative
targets, sell_to_open entries, buy_to_close covers, DH2 borrow priced
in-path. Rosters only on the register row's first-trade condition
(the 10-fire both-sides grade); this adapter is the evaluator's
door, not a rostering."""
from desk3.aster_etf import evaluate as _ev, INPUTS, PRODUCERS
SLEEVE_ID="aster_etf_qqq_qld_monthly_inv"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
