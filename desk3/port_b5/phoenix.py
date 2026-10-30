"""v3 wrapper for phoenix — strategy in sleeves/phoenix.py (byte-identical
to v2), interface glue in adapters/phoenix.py (byte-identical to v2).
INPUTS is the producer-registry declaration for this sleeve."""
from ._ctx import run as _run

SLEEVE_ID = "phoenix"
INPUTS = ('bars', 'positions', 'earnings')
CADENCE_S = 300


def evaluate(view, ctx):
    return _run("phoenix", view, ctx)
