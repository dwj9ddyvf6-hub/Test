"""v3 sleeve module for s_q07w_s52_sm_cheap5_wcov — Lazarus Q07 batch 4.

Q07 Swing H52 small cheap5+wiki_cov (CSV off => parked; exits managed).
Fire-consumer over desk3.lazarus_q07 (catalog §4.1 family rule);
producer inputs declared in INPUTS / config row.
"""
from desk3.lazarus_q07 import evaluate_sleeve, INPUTS, PRODUCERS, SPECS

SLEEVE_ID = "s_q07w_s52_sm_cheap5_wcov"
SPEC = SPECS[SLEEVE_ID]


def evaluate(view, ctx):
    return evaluate_sleeve(SLEEVE_ID, view, ctx)
