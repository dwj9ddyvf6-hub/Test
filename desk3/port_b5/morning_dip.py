"""v3 wrapper for morning_dip — strategy in sleeves/morning_dip.py (byte-identical
to v2), interface glue in adapters/morning_dip.py (byte-identical to v2).
INPUTS is the producer-registry declaration for this sleeve."""
from ._ctx import run as _run
from ._enh2 import run_enh2

SLEEVE_ID = "morning_dip"
INPUTS = ('bars', 'positions')
CADENCE_S = 180


def evaluate(view, ctx):
    return run_enh2("morning_dip", view, ctx, _run, {"3Min": 180})
