"""investandbefree_dmac_dailyonly — DMAC variant V2: 4H layer removed (weekly+daily stack only). INVESTANDBEFREE-DMAC-VARIANTS-SPEC-2026-10-29.
Paper only; own $10,000 slice, own state, own live record. No
backtest: the live paper record is the test (30-trade minimum
before judging, percent vs SPY/QQQ yardstick; see the variants
spec doc).
"""
from __future__ import annotations

from core.sleeve import SleeveConfig
from sleeves.investandbefree_dmac import (
    SYMBOLS, InvestAndBeFreeDmacSleeve, closed_bars, variant_params)

CONFIG = SleeveConfig(
    sleeve_id="investandbefree_dmac_dailyonly",
    cadence_s=3600,
    universe=SYMBOLS,
    state_schema={"sleeve_state": "dict", "dmac_state": "dict"},
    parked=False,
)


class InvestAndBeFreeDmacDailyOnlySleeve(InvestAndBeFreeDmacSleeve):
    CONFIG = CONFIG
    PARAMS = variant_params(stack_order=("weekly", "daily"), entry_tf="daily")
    REASON_LABEL = "investandbefree_dmac_dailyonly"


# Adapter compatibility alias: adapters/investandbefree_dmac_dailyonly.py instantiates
# strat.InvestAndBeFreeDmacSleeve, which resolves to this class.
InvestAndBeFreeDmacSleeve = InvestAndBeFreeDmacDailyOnlySleeve

_INSTANCE = InvestAndBeFreeDmacDailyOnlySleeve()


def signal(bars, slice_state, context):
    out = _INSTANCE.signal(bars, slice_state, context)
    signal.last_evaluation = _INSTANCE.last_evaluation
    signal.dmac_state = _INSTANCE.dmac_state
    return out
