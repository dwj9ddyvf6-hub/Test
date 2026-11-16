"""v3 sleeve s_mn_hourly_1w_varn1, Lazarus Midna fire-consumer
variation (batch 9 form). See desk3/lazarus_midna.py.

GOING-LIVE-VARIATIONS-20261115 (CONV-37): night-1 exit variation
beside s_mn_hourly_1w under GUTTING AS VARIATION: entries identical
to the parent's (its fires re-addressed by desk3/var_fires.py),
exits after night 1 under the variation's own SPECS entry
(hold_sessions 1, stop None) in desk3/lazarus_midna.py; the
parent's SPECS entry is byte-untouched.
"""
from desk3.lazarus_midna import evaluate as _ev, INPUTS, PRODUCERS
from desk3.var_fires import clone_view_for_parent
SLEEVE_ID = "s_mn_hourly_1w_varn1"
PARENT_ID = "s_mn_hourly_1w"
INPUTS = INPUTS
PRODUCERS = PRODUCERS
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, clone_view_for_parent(view, PARENT_ID, SLEEVE_ID), ctx)
