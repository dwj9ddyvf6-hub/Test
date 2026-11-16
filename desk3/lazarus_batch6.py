"""Lazarus batch-6 registry: the ten Q07 alt-data confluence lanes
(s_q07w_*). Authored for v3 (no v2 source); logic in desk3/q07_engine.py,
per-lane modules in adapters3/. Inputs are producer-registry
declarations: sleeve_fires (the sleeve_feed composer of the CSV —
tracker ledger + alt-data tags, sleeve_fires_v1.json), daily bars,
the VIX level, and broker positions. A lane whose declared input is
unproduced or stale is UNFED, never silently abstaining. Green lanes
were Live on Lazarus; Swing lanes were Disabled there, so their rows
carry parked=True (present, genuine, not dispatched until unparked).
"""
from __future__ import annotations

PRODUCERS = {
    "sleeve_feed": (("sleeve_fires",), 93600.0),
    "bars_daily": (("bars_1day",), 93600.0),
    "vix_level": (("vix",), 93600.0),
    "positions": (("positions",), 900.0),
}

# id -> parked (True = Lazarus Disabled)
_ROWS = {
    "s_q07w_g52_sm_ins2_wcov": False,
    "s_q07w_g78_mi_cheap5_deep70_ins2": False,
    "s_q07w_g52_ml_ins2_wlow": False,
    "s_q07w_s78_sm_cheap5_ins2_vix20": True,
    "s_q07w_s52_sm_cheap5_ins2_vix20": True,
    "s_q07w_s78_mi_cheap5_ins2_mom6": True,
    "s_q07w_s78_ml_deep70_ins2_vix20": True,
    "s_q07w_s52_ml_deep70_ins2_vix20": True,
    "s_q07w_s78_sm_deep70_ins2": True,
    "s_q07w_s52_sm_cheap5_deep70_ins2": True,
}
SLEEVE_IDS = tuple(_ROWS)
INPUTS = ("sleeve_fires", "bars_1day", "vix", "positions")


def config_rows():
    return [{
        "id": sid, "module": f"adapters3.{sid}", "cadence_s": 300,
        "parked": parked,
        "slice": {"capital_usd": 1000.0, "cash_usd": 1000.0},
        "bp_buffer_frac": 0.02, "flat_by_close": False,
        "flatten_time_et": None, "session": "rth", "timeout_s": None,
        "params": {}, "inputs": list(INPUTS),
    } for sid, parked in _ROWS.items()]


def register_into(desk, producer_fns=None):
    producer_fns = producer_fns or {}
    for name, (outputs, sla) in PRODUCERS.items():
        fn = producer_fns.get(name)
        if fn is not None:
            desk.add_producer(name, fn, outputs, sla)
        else:
            desk.registry.register_producer(name, outputs, sla)
    for row in config_rows():
        desk.add_sleeve(row["id"], row["module"],
                        inputs=tuple(row["inputs"]),
                        cadence_s=row["cadence_s"],
                        slice_usd=row["slice"]["capital_usd"])
    return desk
