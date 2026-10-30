"""Adapter for s_mn_reversal (v3 Lazarus batch 8) — interface glue only.

Strategy lives in sleeves/s_mn_reversal.py. Worst prior-21-session large caps, 3 slots, 21-session rotation.
Producer-registry declaration: INPUTS / PRODUCERS below; the same
row is registered in config/sleeves.json. Inputs: bars,positions.
"""
from adapters.laz8_common import make_evaluate

SLEEVE_ID = "s_mn_reversal"
INPUTS = ('bars', 'positions')
PRODUCERS = tuple({"name": n, "outputs": (n,), "freshness_sla_s": 900} for n in INPUTS)
DEFAULT_EQUITY = 3000.0

evaluate = make_evaluate(SLEEVE_ID, DEFAULT_EQUITY)
