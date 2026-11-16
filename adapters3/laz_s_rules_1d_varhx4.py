"""v3 Lazarus variation sleeve s_rules_1d_varhx4 (EXTREME_horizon_x4 arm: horizon 88). Engine: desk3/lazarus.py.

GOING-LIVE-VARIATIONS-20261115 (CONV-32): live variation beside its
parent s_rules_1d under GUTTING AS VARIATION (the parent is never
edited into the variation). The variation consumes the parent's own
fire stream, re-addressed to its own id by desk3/var_fires.py, and
carries the registered arm profile in desk3/lazarus.py SPECS under
its own id; the parent's SPECS entry is byte-untouched.
"""
from desk3.lazarus import evaluate as _ev, INPUTS
from desk3.var_fires import clone_view_for_parent
SLEEVE_ID = "s_rules_1d_varhx4"
PARENT_ID = "s_rules_1d"
INPUTS = INPUTS
def evaluate(view, ctx):
    return _ev(SLEEVE_ID, clone_view_for_parent(view, PARENT_ID, SLEEVE_ID), ctx)
