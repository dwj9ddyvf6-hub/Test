"""v3 sleeve aster_r19_linkusdt_absorption_base_fixed16_fullcash_varhx2 — Aster crypto batch 11 (LINKUSDT fixed16),
horizon-doubled form. See desk3/aster_b11_crypto.py.

GOING-LIVE-VARIATIONS-20261115 (CONV-29): live variation beside
aster_r19_linkusdt_absorption_base_fixed16_fullcash under GUTTING AS VARIATION; its SPECS entry carries hold_h=32
against the parent's 16, the registered arm's doubled hold. The
parent's SPECS entry is byte-untouched.
"""
from desk3.aster_b11_crypto import evaluate as _ev, INPUTS
SLEEVE_ID="aster_r19_linkusdt_absorption_base_fixed16_fullcash_varhx2"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
