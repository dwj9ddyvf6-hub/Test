"""v3 sleeve aster_tensor_g4_varmk — Tensor G4 marker variation
(CONV-57, CONV57-G4-VARIATION-20261116): Form C of
pass2/CONV57-G4-VARIATION-PROPOSAL.md rostered live beside the
G4 parents, which are byte-untouched. See desk3/aster_g4_varmk.py.
Falsifier: existence check first (zero qualifiers over a full
quarter of forward weekly bundles returns it as an open anatomy
row); retire if, over its first 20 resolved forward fires, the
mean fwd5 excess vs QQQ is below 0."""
from desk3.aster_g4_varmk import evaluate as _ev, INPUTS, PRODUCERS
SLEEVE_ID = "aster_tensor_g4_varmk"


def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
