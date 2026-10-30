"""v3 sleeve module for s_q07w_c78_ml_mom6_tierA_wlow — Lazarus Q07 batch 3.

s_q07w_c78_ml_mom6_tierA_wlow: Q07 w_cyan H78 midlarge mom6+tierA+wiki_low (CSV ON, Live per catalog §4.1).
Fire-consumer over desk3.lazarus_q07 (catalog §4.1 family rule);
producer inputs declared in INPUTS / config row.
"""
from desk3.lazarus_q07 import evaluate_sleeve, INPUTS, PRODUCERS, SPECS

SLEEVE_ID = "s_q07w_c78_ml_mom6_tierA_wlow"
SPEC = SPECS[SLEEVE_ID]


def evaluate(view, ctx):
    return evaluate_sleeve(SLEEVE_ID, view, ctx)
