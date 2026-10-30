"""Adapter for s_mn_macd (v3 Lazarus batch 8) — interface glue only.

Strategy lives in sleeves/s_mn_macd.py. MACD(12,26,9) cross up/down on daily closes; 1 slot.
Producer-registry declaration: INPUTS / PRODUCERS below; the same
row is registered in config/sleeves.json. Inputs: bars,positions.
"""
from adapters.laz8_common import make_evaluate

SLEEVE_ID = "s_mn_macd"
INPUTS = ('bars', 'positions')
PRODUCERS = tuple({"name": n, "outputs": (n,), "freshness_sla_s": 900} for n in INPUTS)
DEFAULT_EQUITY = 1000.0

evaluate = make_evaluate(SLEEVE_ID, DEFAULT_EQUITY)
