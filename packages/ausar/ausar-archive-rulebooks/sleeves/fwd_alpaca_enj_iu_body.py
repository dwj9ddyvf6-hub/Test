"""FWD Alpaca ENJ IU-body — lean-desk port (Wave D, Decision #119).

EXTRACTED from aurelia_alpaca_forward.py BOOKS: FWD_ALPACA_ENJ_IU_BODY_V1
(preserves PUBLIC_IU_BODY_SPOT100) is listed=False in the source: the
venue returned HTTP 404 for ENJ/USD (and ENJ/USDT is absent); the
original ENJUSDT sleeve stays blocked on Binance HTTP 451 and NO other
ticker is substituted. The port preserves the ruling exactly: this
sleeve never emits an intent, and LIST_ERROR carries the source's
reason verbatim. If the venue ever lists the pair, that is a new
ruling, not a silent un-block.

VIRTUAL BOOK MAPPING: none while unlisted — no account is funded.
"""
from core.sleeve import BaseSleeve, SleeveConfig

LIST_ERROR = ("Alpaca GET /v2/assets/ENJ/USD returned HTTP 404 asset not found. "
              "ENJ/USDT is also absent. The original ENJUSDT sleeve stays blocked "
              "on Binance HTTP 451. No other ticker is substituted.")

CONFIG = SleeveConfig(
    sleeve_id="fwd_alpaca_enj_iu_body", cadence_s=300, universe=("ENJ/USD",), monitor_only=True,
    state_schema={}, risk_pct=None)


def status():
    return {"id": "FWD_ALPACA_ENJ_IU_BODY_V1", "preserves": "PUBLIC_IU_BODY_SPOT100",
            "status": "BLOCKED", "reason": LIST_ERROR, "orders_disabled": True}


class FwdEnjIuBody(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        return []  # unlisted instrument — blocked in the source, blocked here


def signal(bars, slice_state, context):
    return FwdEnjIuBody().signal(bars, slice_state, context)
