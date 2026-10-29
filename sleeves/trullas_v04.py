"""Trullas variant sleeve trullas_v04 — S4: TP2 at 66.7 percent.

TRULLAS-VARIANTS-SPEC-2026-10-29 (FROZEN). A thin subclass of the
primary TrullasDivergenceSleeve (sleeves/trullas_divergence.py): all
divergence logic is shared with the primary; exactly one joint differs: tp2_level=0.667.
Paper only; own $10,000 slice, own state, own live record. No backtest:
the live paper record is the test.
"""
from __future__ import annotations

from core.sleeve import SleeveConfig
from sleeves.trullas_divergence import (
    PRIMARY_PARAMS, SYMBOL, TrullasDivergenceSleeve, UNIT_RISK_PCT,
    variant_params)

CONFIG = SleeveConfig(
    sleeve_id="trullas_v04",
    cadence_s=60,
    universe=(SYMBOL,),
    state_schema={"trullas_state": "dict", "position": "dict|None"},
    risk_pct=UNIT_RISK_PCT,
    parked=False,
)


class TrullasV04Sleeve(TrullasDivergenceSleeve):
    CONFIG = CONFIG
    PARAMS = variant_params(tp2_level=0.667)
    REASON_LABEL = "trullas_v04"


# Adapter compatibility alias: adapters/trullas_v04.py instantiates
# strat.TrullasDivergenceSleeve, which resolves to this variant class.
TrullasDivergenceSleeve = TrullasV04Sleeve

_INSTANCE = TrullasV04Sleeve()


def signal(bars, slice_state, context):
    out = _INSTANCE.signal(bars, slice_state, context)
    signal.last_evaluation = _INSTANCE.last_evaluation
    signal.trullas_state = _INSTANCE.trullas_state
    return out
