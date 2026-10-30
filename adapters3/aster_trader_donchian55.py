"""v3 sleeve aster_trader_donchian55 — Aster batch 16. See desk3/aster_batch16.py + FIDELITY-LEDGER.md (ASTER-B16)."""
from desk3.aster_batch16 import evaluate as _ev, DONCHIAN_INPUTS as INPUTS, PRODUCERS
SLEEVE_ID = "aster_trader_donchian55"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
