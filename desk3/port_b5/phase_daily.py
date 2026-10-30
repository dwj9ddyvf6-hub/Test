"""v3 wrapper for phase_daily — strategy in sleeves/phase_daily.py (byte-identical
to v2), interface glue in adapters/phase_daily.py (byte-identical to v2).
INPUTS is the producer-registry declaration for this sleeve."""
from ._ctx import run as _run

SLEEVE_ID = "phase_daily"
INPUTS = ('bars', 'positions', 'earnings', 'journal')
CADENCE_S = 300


def evaluate(view, ctx):
    return _run("phase_daily", view, ctx)
