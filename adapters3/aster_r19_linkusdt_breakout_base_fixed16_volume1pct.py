"""v3 sleeve aster_r19_linkusdt_breakout_base_fixed16_volume1pct — Aster crypto batch 12 (LINKUSDT). See desk3/aster_b12_crypto.py + FIDELITY-LEDGER ASTER-B12."""
from desk3.aster_b12_crypto import evaluate as _ev, INPUTS_BREAKOUT as INPUTS
SLEEVE_ID="aster_r19_linkusdt_breakout_base_fixed16_volume1pct"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
