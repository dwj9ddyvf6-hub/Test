"""Aster batch 5: negative_funding_squeeze · ADAUSDT, 16-hour hold, fullcash sizing
(ASTER-BUILD-MAP batch 5; archive r19_crypto.py + absorption/signals.py
+ crypto_rules.json). Engine: aster_sleeves._common."""
from aster_sleeves._common import evaluate_crypto

SLEEVE_ID = "aster_squeeze_ada_fullcash"
FAMILY = "negative_funding_squeeze"
CAPACITY = "fullcash"
INPUTS = ('bars', 'positions', 'funding')
CADENCE_S = 3600


def evaluate(view, ctx):
    return evaluate_crypto(view, ctx, SLEEVE_ID, FAMILY, CAPACITY)
