"""v3 sleeve module for s_q07w_g52_ml_tierA_wcov_vargd — F4 GATE_DROP variation of s_q07w_g52_ml_tierA_wcov
(VARIATION-ROSTERING-20261115, rostered 2026-11-15).

s_q07w_g52_ml_tierA_wcov_vargd: Q07 green H52 midlarge filters
() (parent s_q07w_g52_ml_tierA_wcov filters
('tierA', 'wcov'); the alt-data gates are dropped per
config/f4_variations_20261115.json, operator GATE_DROP; every other
spec field is the parent's). Fire-consumer over desk3.lazarus_q07;
producer inputs declared in INPUTS / config row.
Falsifier: retire if, over its first 20 resolved forward fires, the mean fwd5 excess vs QQQ is below 0bp; graded on the variation's own record only.
"""
from desk3.lazarus_q07 import evaluate_sleeve, INPUTS, PRODUCERS, SPECS

SLEEVE_ID = "s_q07w_g52_ml_tierA_wcov_vargd"
SPEC = SPECS[SLEEVE_ID]


def evaluate(view, ctx):
    return evaluate_sleeve(SLEEVE_ID, view, ctx)
