"""Adapter for s_mn_moonshot (v3 Lazarus batch 8) — interface glue only.

Strategy lives in sleeves/s_mn_moonshot.py. Fire-consumer: upstream Midna moonshot pick via lazarus_fire_ingest (substitution for the unreachable midna_fires_v1.json); no stop, 78-week hold.
Producer-registry declaration: INPUTS / PRODUCERS below; the same
row is registered in config/sleeves.json. Inputs: bars,positions,fires.
"""
from adapters.laz8_common import make_evaluate

SLEEVE_ID = "s_mn_moonshot"
INPUTS = ('bars', 'positions', 'fires')
PRODUCERS = tuple({"name": n, "outputs": (n,), "freshness_sla_s": 900} for n in INPUTS)
DEFAULT_EQUITY = 1000.0

evaluate = make_evaluate(SLEEVE_ID, DEFAULT_EQUITY)
