"""v3 Lazarus variation sleeve s_1wc_ml_vards (DROP_stop arm: horizon 252, stop dropped). Engine: desk3/lazarus.py.

GOING-LIVE-VARIATIONS-20261115 (CONV-33): live variation beside its
parent s_1wc_ml under GUTTING AS VARIATION (the parent is never
edited into the variation). The variation consumes the parent's own
fire stream, re-addressed to its own id by desk3/var_fires.py, and
carries the registered arm profile in desk3/lazarus.py SPECS under
its own id; the parent's SPECS entry is byte-untouched.
"""
from desk3.lazarus import evaluate as _ev, INPUTS
from desk3.var_fires import clone_view_for_parent
SLEEVE_ID = "s_1wc_ml_vards"
PARENT_ID = "s_1wc_ml"
INPUTS = INPUTS
def evaluate(view, ctx):
    return _ev(SLEEVE_ID, clone_view_for_parent(view, PARENT_ID, SLEEVE_ID), ctx)
