"""v3 wrapper for qullamaggie — strategy in sleeves/qullamaggie.py (byte-identical
to v2), interface glue in adapters/qullamaggie.py (byte-identical to v2).
INPUTS is the producer-registry declaration for this sleeve."""
from ._ctx import run as _run
from ._enh2 import run_enh2

SLEEVE_ID = "qullamaggie"
INPUTS = ('bars', 'positions')
CADENCE_S = 1800


def evaluate(view, ctx):
    return run_enh2("qullamaggie", view, ctx, _run)
