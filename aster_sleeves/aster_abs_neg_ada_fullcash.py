"""Aster batch 5: absorption_negative_funding · ADAUSDT, 16-hour hold, fullcash sizing
(ASTER-BUILD-MAP batch 5; archive r19_crypto.py + absorption/signals.py
+ crypto_rules.json). Engine: aster_sleeves._common."""
from aster_sleeves._common import evaluate_crypto

SLEEVE_ID = "aster_abs_neg_ada_fullcash"
FAMILY = "absorption_negative_funding"
CAPACITY = "fullcash"
INPUTS = ('bars', 'positions', 'funding')
CADENCE_S = 3600


def evaluate(view, ctx):
    return evaluate_crypto(view, ctx, SLEEVE_ID, FAMILY, CAPACITY)
