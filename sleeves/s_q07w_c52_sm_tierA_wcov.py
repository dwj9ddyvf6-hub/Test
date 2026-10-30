"""v3 sleeve module for s_q07w_c52_sm_tierA_wcov — Lazarus Q07 batch 2.

s_q07w_c52_sm_tierA_wcov: Q07 w_cyan H52 small tierA+wiki_cov (CSV ON, Live).
Fire-consumer over desk3.lazarus_q07 (catalog §4.1 family rule);
producer inputs declared in INPUTS / config row.
"""
from desk3.lazarus_q07 import evaluate_sleeve, INPUTS, PRODUCERS, SPECS

SLEEVE_ID = "s_q07w_c52_sm_tierA_wcov"
SPEC = SPECS[SLEEVE_ID]


def evaluate(view, ctx):
    return evaluate_sleeve(SLEEVE_ID, view, ctx)
