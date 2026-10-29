"""FREE_OPT_PARITY — lean-desk port (Wave D, Decision #119 family).

EXTRACTED from aurelia_free_options.py contracts(): shape parity_model,
execution model_test — "No economic order." Indicative conversion is
recorded and is not an economic order (MODEL_TEST_ONLY on the old desk,
permanently). This sleeve therefore NEVER emits an intent; parity_status()
returns the old desk's row for the core Ledger to record.

VIRTUAL BOOK MAPPING: none — no Ledger account, no budget. It is a
monitor, ported as a monitor.
"""
from core.sleeve import BaseSleeve, SleeveConfig

CONFIG = SleeveConfig(
    sleeve_id="free_opt_parity", cadence_s=300, universe=(), monitor_only=True,
    state_schema={}, risk_pct=None)


def parity_status():
    return {"id": "FREE_OPT_PARITY_V1", "preserves": "OPT_PARITY_MONITOR",
            "status": "MODEL_TEST_ONLY", "broker_order": False,
            "economic_forward": False,
            "reason": "Indicative conversion is recorded and is not an economic order."}


class FreeOptParity(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        return []  # model test only — by contract design, forever


def signal(bars, slice_state, context):
    return FreeOptParity().signal(bars, slice_state, context)
