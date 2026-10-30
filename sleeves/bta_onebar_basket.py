"""bta_onebar_basket: the one bar portability claim, tested directly.

Identical rules and parameters to sleeves/bta_onebar_qqq.py (the
frozen base core), run independently per symbol on SPY, QQQ, MDY
and DIA: the ETF counterparts of the S&P 500, NASDAQ, MidCap 400
and Dow Jones instruments the source post names. Per-symbol
state, per-symbol 2-entry daily cap, one position per symbol at
a time. Paper only, own $10,000 slice, own live record. Edge
UNPROVEN; no backtest is claimed.
"""
from __future__ import annotations

from core.sleeve import SleeveConfig
from sleeves.bta_onebar_qqq import BtaOnebarQqqSleeve

SYMBOLS = ("SPY", "QQQ", "MDY", "DIA")

CONFIG = SleeveConfig(
    sleeve_id="bta_onebar_basket",
    cadence_s=60,
    universe=SYMBOLS,
    state_schema={"onebar_state": "dict", "position": "dict|None"},
    parked=False,
)


class BtaOnebarBasketSleeve(BtaOnebarQqqSleeve):
    CONFIG = CONFIG
    SLEEVE_ID = "bta_onebar_basket"
    SYMBOLS = SYMBOLS
    RTH_ONLY = False


# Adapter compatibility alias.
BtaOnebarSleeve = BtaOnebarBasketSleeve

_INSTANCE = BtaOnebarBasketSleeve()


def signal(bars, slice_state, context):
    out = _INSTANCE.signal(bars, slice_state, context)
    signal.last_evaluation = _INSTANCE.last_evaluation
    signal.onebar_state = _INSTANCE.onebar_state
    return out
