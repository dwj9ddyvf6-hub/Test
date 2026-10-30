"""v3 sleeve aster_rec_rsi2_long_touch_a — Aster batch 2. See desk3/aster_b2.py + FIDELITY-LEDGER.md."""
from desk3.aster_b2 import evaluate as _ev, INPUTS_COMMON, PRODUCERS, PRODUCERS_PEAD
SLEEVE_ID="aster_rec_rsi2_long_touch_a"
INPUTS=INPUTS_COMMON+("earnings_events",) if "aster_rec_rsi2_long_touch_a".startswith("aster_pead") else INPUTS_COMMON
PRODUCERS=PRODUCERS_PEAD if "aster_rec_rsi2_long_touch_a".startswith("aster_pead") else PRODUCERS
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
