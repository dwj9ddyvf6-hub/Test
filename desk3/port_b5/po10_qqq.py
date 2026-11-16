"""v3 wrapper for po10_qqq — strategy in sleeves/po10_qqq.py (byte-identical
to v2), interface glue in adapters/po10_qqq.py (byte-identical to v2).
INPUTS is the producer-registry declaration for this sleeve.

ACCOUNTING BASIS (WIN-RATE-BASIS-20261031): the strategy header in
sleeves/po10_qqq.py republishes the source's published line (392
trades, 59% win rate, PF 1.86). The source does not state the
accounting basis of that win rate or profit factor: the basis is
NOT STATED by the source — it is not FIFO-lot-verified and not
equity-based-verified, and it must never be read or republished as
either. The basis statement lives here, on the module the roster
actually loads, because sleeves/po10_qqq.py is byte-pinned to the
v2 port (tests/test_port_b5_blockers.py). Desk rule: win rate and
profit factor appear on a surface only with their basis (FIFO-lot
vs equity-based) stated, or not at all."""
from ._ctx import run as _run

SLEEVE_ID = "po10_qqq"
INPUTS = ('bars', 'positions', 'quotes', 'session_fills')
CADENCE_S = 60

# The republished source figure and its accounting-basis status,
# stated once on the loaded entrypoint (see docstring above).
REPUBLISHED_SOURCE_FIGURE = {
    "trades": 392,
    "win_rate": 0.59,
    "profit_factor": 1.86,
    "accounting_basis": "not_stated_by_source",
    "fifo_lot_verified": False,
    "equity_based_verified": False,
}


def evaluate(view, ctx):
    return _run("po10_qqq", view, ctx)
