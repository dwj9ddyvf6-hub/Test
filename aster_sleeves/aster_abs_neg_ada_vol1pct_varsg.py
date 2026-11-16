"""Aster batch 5: absorption_negative_funding · ADAUSDT, 16-hour hold,
volume1pct sizing — F4 SIGN_GATE_DROP variation of aster_abs_neg_ada_vol1pct
(VARIATION-ROSTERING-20261115, rostered 2026-11-15): the funding sign
leg is dropped (entries admitted at any OBSERVED funding rate;
unobserved funding still fails closed); the absorption bar
condition, 16h hold and volume1pct sizing are the parent's. The
fullcash arm of the same signal is NOT varied (its sign leg is
load-bearing). Engine: aster_sleeves._common.
Falsifier: retire if, over its first 20 resolved forward fires, the mean fwd5 excess vs QQQ is below 0bp; graded on the variation's own record only.
"""
from aster_sleeves._common import evaluate_crypto

SLEEVE_ID = "aster_abs_neg_ada_vol1pct_varsg"
FAMILY = "absorption_negative_funding"
CAPACITY = "volume1pct"
INPUTS = ('bars', 'positions', 'funding')
CADENCE_S = 3600


def evaluate(view, ctx):
    return evaluate_crypto(view, ctx, SLEEVE_ID, FAMILY, CAPACITY,
                           drop_funding_sign=True)
