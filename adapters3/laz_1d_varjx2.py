"""v3 Lazarus variation sleeve 1d_varjx2 (JITTER_horizon_x2 arm: horizon 80, stop 0.15, target 0.20). Engine: desk3/lazarus.py.

GOING-LIVE-VARIATIONS-20261115 (CONV-30): live variation beside its
parent 1d under GUTTING AS VARIATION (the parent is never
edited into the variation). The variation consumes the parent's own
fire stream, re-addressed to its own id by desk3/var_fires.py, and
carries the registered arm profile in desk3/lazarus.py SPECS under
its own id; the parent's SPECS entry is byte-untouched.
"""
from desk3.lazarus import evaluate as _ev, INPUTS
from desk3.var_fires import clone_view_for_parent
SLEEVE_ID = "1d_varjx2"
PARENT_ID = "1d"
INPUTS = INPUTS
def evaluate(view, ctx):
    return _ev(SLEEVE_ID, clone_view_for_parent(view, PARENT_ID, SLEEVE_ID), ctx)
