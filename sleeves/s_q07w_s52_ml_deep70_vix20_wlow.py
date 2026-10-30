"""v3 sleeve module for s_q07w_s52_ml_deep70_vix20_wlow — Lazarus Q07 batch 5.

Q07 Swing H52 midlarge deep70+stress_vix20+wiki_low (CSV off). Fire-consumer over desk3.lazarus_q07 (catalog §4.1 family
rule); producer inputs declared in INPUTS / config row.
"""
from desk3.lazarus_q07 import evaluate_sleeve, INPUTS, PRODUCERS, SPECS

SLEEVE_ID = "s_q07w_s52_ml_deep70_vix20_wlow"
SPEC = SPECS[SLEEVE_ID]
PARAMS = {"family": SPEC["family"], "cap_band": "ml",
          "horizon_weeks": SPEC["horizon_w"], "filters": SPEC["filters"],
          "parked": SPEC["parked"]}


def evaluate(view, ctx):
    return evaluate_sleeve(SLEEVE_ID, view, ctx)
