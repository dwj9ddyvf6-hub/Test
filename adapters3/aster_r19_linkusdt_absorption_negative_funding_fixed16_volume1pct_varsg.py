"""v3 sleeve aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct_varsg — Aster crypto batch 11 (LINKUSDT fixed16), F4
SIGN_GATE_DROP variation of aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct (VARIATION-ROSTERING-20261115,
rostered 2026-11-15): the funding sign leg is dropped in its own
SPECS entry (drop_funding_sign=True; any OBSERVED rate admits,
unobserved funding still fails closed); absorption bar condition,
16h hold and volume1pct sizing are the parent's. See
desk3/aster_b11_crypto.py.
Falsifier: retire if, over its first 20 resolved forward fires, the mean fwd5 excess vs QQQ is below 0bp; graded on the variation's own record only.
"""
from desk3.aster_b11_crypto import evaluate as _ev, INPUTS
SLEEVE_ID="aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct_varsg"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
