"""Aster batch 5: absorption_nonnegative_funding · ADAUSDT, 16-hour hold, volume1pct sizing
(ASTER-BUILD-MAP batch 5; archive r19_crypto.py + absorption/signals.py
+ crypto_rules.json). Engine: aster_sleeves._common."""
from aster_sleeves._common import evaluate_crypto

SLEEVE_ID = "aster_abs_nonneg_ada_vol1pct"
FAMILY = "absorption_nonnegative_funding"
CAPACITY = "volume1pct"
INPUTS = ('bars', 'positions', 'funding')
CADENCE_S = 3600


def evaluate(view, ctx):
    return evaluate_crypto(view, ctx, SLEEVE_ID, FAMILY, CAPACITY)
