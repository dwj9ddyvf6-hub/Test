"""v3 wrapper for qqq_put_ladder — strategy in sleeves/qqq_put_ladder.py (byte-identical
to v2), interface glue in adapters/qqq_put_ladder.py (byte-identical to v2).
INPUTS is the producer-registry declaration for this sleeve."""
from ._ctx import run as _run

SLEEVE_ID = "qqq_put_ladder"
INPUTS = ('bars', 'positions', 'options')
CADENCE_S = 900


def evaluate(view, ctx):
    return _run("qqq_put_ladder", view, ctx)
