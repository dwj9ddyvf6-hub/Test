"""bta_onebar_rth: the one bar system, regular session only.

Identical rules and parameters to sleeves/bta_onebar_qqq.py (the
frozen base core), with three session restrictions: the channel
and entries are computed only on regular session bars (bar start
09:30 ET to before 16:00 ET), entries occur only during RTH, and
any position open at 15:55 ET exits at market instead of holding
past the close. Paper only, own $10,000 slice, own live record.
Edge UNPROVEN; no backtest is claimed.
"""
from __future__ import annotations

from core.sleeve import SleeveConfig
from sleeves.bta_onebar_qqq import BtaOnebarQqqSleeve

SYMBOLS = ("QQQ",)

CONFIG = SleeveConfig(
    sleeve_id="bta_onebar_rth",
    cadence_s=60,
    universe=SYMBOLS,
    state_schema={"onebar_state": "dict", "position": "dict|None"},
    parked=False,
)


class BtaOnebarRthSleeve(BtaOnebarQqqSleeve):
    CONFIG = CONFIG
    SLEEVE_ID = "bta_onebar_rth"
    SYMBOLS = SYMBOLS
    RTH_ONLY = True


# Adapter compatibility alias.
BtaOnebarSleeve = BtaOnebarRthSleeve

_INSTANCE = BtaOnebarRthSleeve()


def signal(bars, slice_state, context):
    out = _INSTANCE.signal(bars, slice_state, context)
    signal.last_evaluation = _INSTANCE.last_evaluation
    signal.onebar_state = _INSTANCE.onebar_state
    return out
