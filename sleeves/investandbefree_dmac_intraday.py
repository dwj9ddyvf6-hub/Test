"""investandbefree_dmac_intraday — DMAC variant V1: intraday form (15m/30m/4H stack from closed 5Min bars, 30m entry, >=5d expiry, flat by 15:55 ET). INVESTANDBEFREE-DMAC-VARIANTS-SPEC-2026-10-29.
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
    sleeve_id="investandbefree_dmac_intraday",
    cadence_s=300,
    universe=SYMBOLS,
    state_schema={"sleeve_state": "dict", "dmac_state": "dict"},
    parked=False,
)


class InvestAndBeFreeDmacIntradaySleeve(InvestAndBeFreeDmacSleeve):
    CONFIG = CONFIG
    PARAMS = variant_params(stack_order=("h4", "m30", "m15"), entry_tf="m30", min_dte=5, flat_by_close=True)
    REASON_LABEL = "investandbefree_dmac_intraday"


# Adapter compatibility alias: adapters/investandbefree_dmac_intraday.py instantiates
# strat.InvestAndBeFreeDmacSleeve, which resolves to this class.
InvestAndBeFreeDmacSleeve = InvestAndBeFreeDmacIntradaySleeve

_INSTANCE = InvestAndBeFreeDmacIntradaySleeve()


def signal(bars, slice_state, context):
    out = _INSTANCE.signal(bars, slice_state, context)
    signal.last_evaluation = _INSTANCE.last_evaluation
    signal.dmac_state = _INSTANCE.dmac_state
    return out
