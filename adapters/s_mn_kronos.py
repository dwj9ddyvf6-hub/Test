"""Adapter for s_mn_kronos (v3 Lazarus batch 8) — interface glue only.

Strategy lives in sleeves/s_mn_kronos.py. Fire-consumer: upstream Kronos forecast ranking via lazarus_fire_ingest; top-4 hold, rebalance on forecast change, 5-session min hold.
Producer-registry declaration: INPUTS / PRODUCERS below; the same
row is registered in config/sleeves.json. Inputs: bars,positions,fires.
"""
from adapters.laz8_common import make_evaluate

SLEEVE_ID = "s_mn_kronos"
INPUTS = ('bars', 'positions', 'fires')
PRODUCERS = tuple({"name": n, "outputs": (n,), "freshness_sla_s": 900} for n in INPUTS)
DEFAULT_EQUITY = 2000.0

evaluate = make_evaluate(SLEEVE_ID, DEFAULT_EQUITY)
