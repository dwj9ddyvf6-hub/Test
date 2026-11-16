"""Lazarus batch-7 registry: Q07 swing lanes x5, ChartsLector x2,
Midna ports x3. V3-native sleeves in laz_sleeves/ (module == id).

Producer declarations: tensor_fires is served by the desk's Tensor
bundle producer. midna_signals / hedge_signal were declared as
tensor_bundle outputs until 2026-11-14, but the bundle never carried
them (FEED80-MIDNA-20261114); they are served by the midna_signals
ingest producer (desk3/producers3.py MidnaSignalsProducer) from a
drop computed by the desk's own swing machinery. alt_data is the
alt-data tag producer (insider / Wikipedia / gamma / ATS / cap-band
tags).
Q07 lanes keep their source status: Disabled -> parked.
"""
from __future__ import annotations

PRODUCERS = {
    "bars_daily": (("bars_1day",), 93600.0),
    "bars_hourly": (("bars_1hour",), 7200.0),
    "positions": (("positions",), 900.0),
    "tensor_bundle": (("tensor_fires",), 93600.0),
    "midna_signals": (("midna_signals", "hedge_signal"), 93600.0),
    "alt_data": (("alt_data",), 93600.0),
    "vix": (("vix",), 93600.0),
}

# id -> (cadence_s, session, slice_usd, parked, inputs)
_ROWS = {
    "s_q07w_s78_ml_deep70_glow_ins2": (86400, "rth", 1000.0, True,
        ("bars_1day", "positions", "tensor_fires", "alt_data", "vix", "fires")),
    "s_q07w_s52_ml_ins2_mom6_vix20": (86400, "rth", 1984.0, True,
        ("bars_1day", "positions", "tensor_fires", "alt_data", "vix", "fires")),
    "s_q07w_s52_ml_ins2_mom6_wlow": (86400, "rth", 1000.0, True,
        ("bars_1day", "positions", "tensor_fires", "alt_data", "vix", "fires")),
    "s_q07w_s78_mi_ats_z1_cheap5": (86400, "rth", 1000.0, True,
        ("bars_1day", "positions", "tensor_fires", "alt_data", "vix", "fires")),
    "s_q07w_s78_mi_ats_z1_mom6": (86400, "rth", 1000.0, True,
        ("bars_1day", "positions", "tensor_fires", "alt_data", "vix", "fires")),
    "s_cl_qm_small": (86400, "rth", 8000.0, False,
        ("bars_1day", "positions", "alt_data")),
    "s_cl_vmr_qqq": (86400, "rth", 1000.0, False,
        ("bars_1day", "positions", "vix")),
    "s_mn_hourly": (3600, "rth", 12000.0, False,
        ("bars_1hour", "positions", "midna_signals")),
    "s_mn_nostop": (3600, "rth", 1000.0, False,
        ("bars_1hour", "positions", "midna_signals")),
    "s_mn_hedge": (86400, "rth", 1000.0, False,
        ("bars_1day", "positions", "hedge_signal")),
}

SLEEVE_IDS = tuple(_ROWS.keys())


def config_rows():
    rows = []
    for sid, (cadence, session, slice_usd, parked, inputs) in _ROWS.items():
        rows.append({
            "id": sid, "module": f"laz_sleeves.{sid}", "cadence_s": cadence,
            "session": session,
            "slice": {"capital_usd": slice_usd, "cash_usd": slice_usd},
            "bp_buffer_frac": 0.02, "flat_by_close": False,
            "flatten_time_et": None, "params": {}, "inputs": list(inputs),
            "parked": parked,
        })
    return rows


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
