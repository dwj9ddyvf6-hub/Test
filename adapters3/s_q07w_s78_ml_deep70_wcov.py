"""v3 sleeve module for s_q07w_s78_ml_deep70_wcov — Lazarus Q07 batch 5.

Q07 Swing H78 midlarge deep70+wiki_cov (CSV off). Fire-consumer over desk3.lazarus_q07 (catalog §4.1 family
rule); producer inputs declared in INPUTS / config row.
"""
from desk3.lazarus_q07 import evaluate_sleeve, INPUTS, PRODUCERS, SPECS

SLEEVE_ID = "s_q07w_s78_ml_deep70_wcov"
SPEC = SPECS[SLEEVE_ID]
PARAMS = {"family": SPEC["family"], "cap_band": "ml",
          "horizon_weeks": SPEC["horizon_w"], "filters": SPEC["filters"],
          "parked": SPEC["parked"]}


def evaluate(view, ctx):
    return evaluate_sleeve(SLEEVE_ID, view, ctx)
