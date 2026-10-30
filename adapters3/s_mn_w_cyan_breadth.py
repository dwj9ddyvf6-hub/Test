"""v3 sleeve s_mn_w_cyan_breadth — Lazarus Midna fire-consumer (batch 9). See desk3/lazarus_midna.py + FIDELITY-LEDGER.md."""
from desk3.lazarus_midna import evaluate as _ev, INPUTS, PRODUCERS
SLEEVE_ID="s_mn_w_cyan_breadth"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
