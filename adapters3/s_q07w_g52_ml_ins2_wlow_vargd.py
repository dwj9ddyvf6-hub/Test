"""v3 sleeve module for s_q07w_g52_ml_ins2_wlow_vargd — F4 GATE_DROP variation of s_q07w_g52_ml_ins2_wlow
(VARIATION-ROSTERING-20261115, rostered 2026-11-15).

Catalog form: Tensor 1W green signal, ml cap band, filters
() (parent s_q07w_g52_ml_ins2_wlow filters ('ins2', 'wlow'); the alt-data
gates are dropped per config/f4_variations_20261115.json, operator
GATE_DROP; family/band/horizon are the parent's). Buy only on a
QQQ-down day within 5 sessions of the signal; exit on a 15% stop or
at the 52-week horizon; 1 slot at $1,000. Logic
lives in desk3/q07_engine.py (one engine, per-lane spec).
Falsifier: retire if, over its first 20 resolved forward fires, the mean fwd5 excess vs QQQ is below 0bp; graded on the variation's own record only.
"""
from desk3.q07_engine import evaluate_q07

SLEEVE_ID = "s_q07w_g52_ml_ins2_wlow_vargd"
SPEC = {"id": "s_q07w_g52_ml_ins2_wlow_vargd", "family": "green", "horizon_wk": 52,
        "band": "ml", "filters": ()}
INPUTS = ["sleeve_fires", "bars_1day", "vix", "positions"]


def evaluate(view, ctx):
    return evaluate_q07(SPEC, view, ctx)
