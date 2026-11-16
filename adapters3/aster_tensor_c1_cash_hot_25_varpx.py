"""v3 sleeve aster_tensor_c1_cash_hot_25_varpx — Aster batch 13, F4 PARAM_EXTREME variation of
aster_tensor_c1_cash_hot_25 (VARIATION-ROSTERING-20261115, rostered 2026-11-15): the C1
ret60 floor pushed 31 -> 0 in its own SPECS entry (ret60_min=0);
vol20>=0.07, adv>=2e6, atr and marker conjuncts are the parent's.
See desk3/aster_batch13.py + FIDELITY-LEDGER.md (ASTER-B13).
Falsifier: retire if, over its first 20 resolved forward fires, the mean fwd5 excess vs QQQ is below 0bp; graded on the variation's own record only.
"""
from desk3.aster_batch13 import evaluate as _ev, INPUTS_TENSOR as INPUTS, PRODUCERS
SLEEVE_ID="aster_tensor_c1_cash_hot_25_varpx"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
