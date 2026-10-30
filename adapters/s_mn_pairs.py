"""Adapter for s_mn_pairs (v3 Lazarus batch 8) — interface glue only.

Strategy lives in sleeves/s_mn_pairs.py. Distance pairs, 60-session log-spread z>=2, exit |z|<=0.25.
Producer-registry declaration: INPUTS / PRODUCERS below; the same
row is registered in config/sleeves.json. Inputs: bars,positions.
"""
from adapters.laz8_common import make_evaluate

SLEEVE_ID = "s_mn_pairs"
INPUTS = ('bars', 'positions')
PRODUCERS = tuple({"name": n, "outputs": (n,), "freshness_sla_s": 900} for n in INPUTS)
DEFAULT_EQUITY = 3000.0

evaluate = make_evaluate(SLEEVE_ID, DEFAULT_EQUITY)
