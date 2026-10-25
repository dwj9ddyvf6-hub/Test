"""v3 sleeve module for s_q07w_c52_sm_cheap5_ins2_mom6 — Lazarus Q07 batch 5.

Q07 Cyan H52 small cheap5+insider2+mom6 (CSV ON). Fire-consumer over desk3.lazarus_q07 (catalog §4.1 family
rule); producer inputs declared in INPUTS / config row.
"""
from desk3.lazarus_q07 import evaluate_sleeve, INPUTS, PRODUCERS, SPECS

SLEEVE_ID = "s_q07w_c52_sm_cheap5_ins2_mom6"
SPEC = SPECS[SLEEVE_ID]
PARAMS = {"family": SPEC["family"], "cap_band": "sm",
          "horizon_weeks": SPEC["horizon_w"], "filters": SPEC["filters"],
          "parked": SPEC["parked"]}


def evaluate(view, ctx):
    return evaluate_sleeve(SLEEVE_ID, view, ctx)
