"""v3 sleeve aster_pead_vertical_b — Aster batch 2. See desk3/aster_b2.py + FIDELITY-LEDGER.md."""
from desk3.aster_b2 import evaluate as _ev, INPUTS_COMMON, PRODUCERS, PRODUCERS_PEAD
SLEEVE_ID="aster_pead_vertical_b"
INPUTS=INPUTS_COMMON+("earnings_events",) if "aster_pead_vertical_b".startswith("aster_pead") else INPUTS_COMMON
PRODUCERS=PRODUCERS_PEAD if "aster_pead_vertical_b".startswith("aster_pead") else PRODUCERS
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
