"""v3 sleeve module for s_q07w_g52_ml_tierA_wcov — Lazarus Q07 batch 4.

Q07 Green H52 midlarge tierA+wiki_cov (CSV ON).
Fire-consumer over desk3.lazarus_q07 (catalog §4.1 family rule);
producer inputs declared in INPUTS / config row.
"""
from desk3.lazarus_q07 import evaluate_sleeve, INPUTS, PRODUCERS, SPECS

SLEEVE_ID = "s_q07w_g52_ml_tierA_wcov"
SPEC = SPECS[SLEEVE_ID]


def evaluate(view, ctx):
    return evaluate_sleeve(SLEEVE_ID, view, ctx)
