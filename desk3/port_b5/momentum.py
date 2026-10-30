"""v3 wrapper for momentum — strategy in sleeves/momentum.py (byte-identical
to v2), interface glue in adapters/momentum.py (byte-identical to v2).
INPUTS is the producer-registry declaration for this sleeve."""
from ._ctx import run as _run
from ._enh2 import run_enh2

SLEEVE_ID = "momentum"
INPUTS = ('bars', 'positions')
CADENCE_S = 300


def evaluate(view, ctx):
    return run_enh2("momentum", view, ctx, _run)
