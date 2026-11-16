"""v3 Lazarus variation sleeve s_1dg_vardh (DROP_horizon arm: no
time exit). Engine: desk3/lazarus.py.

GOING-LIVE-VARIATIONS-20261115 (CONV-31): live variation beside its
parent s_1dg under GUTTING AS VARIATION. Mirrors the parent adapter
exactly, including the ENH2 stale-bar post-filter via
desk3.enhance18; the parent's fires are re-addressed to the
variation id by desk3/var_fires.py and the registered arm profile
rides desk3/lazarus.py SPECS under the variation's own id.
"""
from desk3.lazarus import evaluate as _ev, INPUTS
from desk3.enhance18 import filter_entries
from desk3.var_fires import clone_view_for_parent
SLEEVE_ID = "s_1dg_vardh"
PARENT_ID = "s_1dg"
INPUTS = INPUTS
def evaluate(view, ctx):
    v = clone_view_for_parent(view, PARENT_ID, SLEEVE_ID)
    return filter_entries(SLEEVE_ID, _ev(SLEEVE_ID, v, ctx), v)
