"""v3 sleeve aster_core_rsi2_long — Aster batch 2. See desk3/aster_b2.py + FIDELITY-LEDGER.md."""
from desk3.aster_b2 import evaluate as _ev, INPUTS_COMMON, PRODUCERS, PRODUCERS_PEAD
SLEEVE_ID="aster_core_rsi2_long"
INPUTS=INPUTS_COMMON+("earnings_events",) if "aster_core_rsi2_long".startswith("aster_pead") else INPUTS_COMMON
PRODUCERS=PRODUCERS_PEAD if "aster_core_rsi2_long".startswith("aster_pead") else PRODUCERS
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
