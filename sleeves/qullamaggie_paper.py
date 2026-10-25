"""v3 wrapper for qullamaggie_paper — strategy in sleeves/qullamaggie_paper.py (byte-identical
to v2), interface glue in adapters/qullamaggie_paper.py (byte-identical to v2).
INPUTS is the producer-registry declaration for this sleeve."""
from ._ctx import run as _run

SLEEVE_ID = "qullamaggie_paper"
INPUTS = ('positions', 'qulla')
CADENCE_S = 300


def evaluate(view, ctx):
    return _run("qullamaggie_paper", view, ctx)
