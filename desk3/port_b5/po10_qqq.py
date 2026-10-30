"""v3 wrapper for po10_qqq — strategy in sleeves/po10_qqq.py (byte-identical
to v2), interface glue in adapters/po10_qqq.py (byte-identical to v2).
INPUTS is the producer-registry declaration for this sleeve."""
from ._ctx import run as _run

SLEEVE_ID = "po10_qqq"
INPUTS = ('bars', 'positions', 'quotes', 'session_fills')
CADENCE_S = 60


def evaluate(view, ctx):
    return _run("po10_qqq", view, ctx)
