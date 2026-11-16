"""v3 sleeve aster_abs_link_4h_varhx2, Aster batch 1 absorption
LINKUSDT, horizon-doubled form. Engine: desk3/aster_batch1.py.

GOING-LIVE-VARIATIONS-20261115 (CONV-29): live variation beside
aster_abs_link_4h under GUTTING AS VARIATION; its SPECS entry
carries hold_h=32 against the parent's default 16h deadline, the
registered arm's doubled hold in this engine's own form. The
parent's SPECS entry is byte-untouched.
"""
from desk3.aster_batch1 import evaluate as _ev, inputs_for, PRODUCERS
SLEEVE_ID = "aster_abs_link_4h_varhx2"
INPUTS = inputs_for(SLEEVE_ID)
PRODUCERS = PRODUCERS
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
