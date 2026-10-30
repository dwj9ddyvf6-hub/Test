"""v3 sleeve module for s_q07w_c52_ml_mom6_wspike2 — Lazarus Q07 batch 3.

s_q07w_c52_ml_mom6_wspike2: Q07 w_cyan H52 midlarge mom6+wiki_spike2 (CSV ON, Live per catalog §4.1).
Fire-consumer over desk3.lazarus_q07 (catalog §4.1 family rule);
producer inputs declared in INPUTS / config row.
"""
from desk3.lazarus_q07 import evaluate_sleeve, INPUTS, PRODUCERS, SPECS

SLEEVE_ID = "s_q07w_c52_ml_mom6_wspike2"
SPEC = SPECS[SLEEVE_ID]


def evaluate(view, ctx):
    return evaluate_sleeve(SLEEVE_ID, view, ctx)
