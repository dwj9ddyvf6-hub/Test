"""Trullas variant sleeve trullas_v05 — S5: hidden divergences included.

TRULLAS-VARIANTS-SPEC-2026-10-29 (FROZEN). A thin subclass of the
primary TrullasDivergenceSleeve (sleeves/trullas_divergence.py): all
divergence logic is shared with the primary; exactly one joint differs: include_hidden=True.
Paper only; own $10,000 slice, own state, own live record. No backtest:
the live paper record is the test.
"""
from __future__ import annotations

from core.sleeve import SleeveConfig
from sleeves.trullas_divergence import (
    PRIMARY_PARAMS, SYMBOL, TrullasDivergenceSleeve, UNIT_RISK_PCT,
    variant_params)

CONFIG = SleeveConfig(
    sleeve_id="trullas_v05",
    cadence_s=60,
    universe=(SYMBOL,),
    state_schema={"trullas_state": "dict", "position": "dict|None"},
    risk_pct=UNIT_RISK_PCT,
    parked=False,
)


class TrullasV05Sleeve(TrullasDivergenceSleeve):
    CONFIG = CONFIG
    PARAMS = variant_params(include_hidden=True)
    REASON_LABEL = "trullas_v05"


# Adapter compatibility alias: adapters/trullas_v05.py instantiates
# strat.TrullasDivergenceSleeve, which resolves to this variant class.
TrullasDivergenceSleeve = TrullasV05Sleeve

_INSTANCE = TrullasV05Sleeve()


def signal(bars, slice_state, context):
    out = _INSTANCE.signal(bars, slice_state, context)
    signal.last_evaluation = _INSTANCE.last_evaluation
    signal.trullas_state = _INSTANCE.trullas_state
    return out
