"""v3 sleeve module for s_q07w_g78_sm_deep70_ins2 — Lazarus Q07 batch 5.

Q07 Green H78 small deep70+insider2 (CSV ON). Fire-consumer over desk3.lazarus_q07 (catalog §4.1 family
rule); producer inputs declared in INPUTS / config row.
"""
from desk3.lazarus_q07 import evaluate_sleeve, INPUTS, PRODUCERS, SPECS

SLEEVE_ID = "s_q07w_g78_sm_deep70_ins2"
SPEC = SPECS[SLEEVE_ID]
PARAMS = {"family": SPEC["family"], "cap_band": "sm",
          "horizon_weeks": SPEC["horizon_w"], "filters": SPEC["filters"],
          "parked": SPEC["parked"]}


def evaluate(view, ctx):
    return evaluate_sleeve(SLEEVE_ID, view, ctx)
