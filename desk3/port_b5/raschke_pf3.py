"""v3 wrapper for raschke_pf3 — strategy in sleeves/raschke_pf3.py (byte-identical
to v2), interface glue in adapters/raschke_pf3.py (byte-identical to v2).
INPUTS is the producer-registry declaration for this sleeve."""
from ._ctx import run as _run

SLEEVE_ID = "raschke_pf3"
INPUTS = ('bars', 'positions', 'journal')
CADENCE_S = 60


def evaluate(view, ctx):
    return _run("raschke_pf3", view, ctx)
