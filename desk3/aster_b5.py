"""Aster batch-5 registry: ADAUSDT spot sleeves (ASTER-BUILD-MAP §5).

Producer declarations: bars/positions are desk warm products; funding
is the Binance perp funding capture named in ASTER-BUILD-MAP §4 — no
v3 producer serves it yet, so funding-conditioned sleeves register
UNFED in the live desk (never fake-fed) until that producer lands.
Slice: standard v3 $10,000 (map §3); R19 fullcash = full slice cash,
volume1pct = 1% of the entry interval's native volume (unchanged).
"""
from __future__ import annotations

PRODUCERS = {
    "bars": (("bars",), 93600.0),
    "positions": (("positions",), 900.0),
    "funding": (("funding",), 43200.0),
}

# id -> (module, cadence_s, inputs)
_ROWS = {
    "aster_pub_rsi2_ada": ("aster_sleeves.aster_pub_rsi2_ada", 3600,
                           ("bars", "positions")),
    "aster_abs_base_ada_fullcash": ("aster_sleeves.aster_abs_base_ada_fullcash", 3600, ("bars", "positions")),
    "aster_abs_base_ada_vol1pct": ("aster_sleeves.aster_abs_base_ada_vol1pct", 3600, ("bars", "positions")),
    "aster_abs_neg_ada_fullcash": ("aster_sleeves.aster_abs_neg_ada_fullcash", 3600, ("bars", "positions", "funding")),
    "aster_abs_neg_ada_vol1pct": ("aster_sleeves.aster_abs_neg_ada_vol1pct", 3600, ("bars", "positions", "funding")),
    "aster_abs_nonneg_ada_fullcash": ("aster_sleeves.aster_abs_nonneg_ada_fullcash", 3600, ("bars", "positions", "funding")),
    "aster_abs_nonneg_ada_vol1pct": ("aster_sleeves.aster_abs_nonneg_ada_vol1pct", 3600, ("bars", "positions", "funding")),
    "aster_breakout_ada_fullcash": ("aster_sleeves.aster_breakout_ada_fullcash", 3600, ("bars", "positions")),
    "aster_breakout_ada_vol1pct": ("aster_sleeves.aster_breakout_ada_vol1pct", 3600, ("bars", "positions")),
    "aster_squeeze_ada_fullcash": ("aster_sleeves.aster_squeeze_ada_fullcash", 3600, ("bars", "positions", "funding")),
}

SLEEVE_IDS = tuple(_ROWS.keys())


def config_rows():
    rows = []
    for sid, (module, cadence, inputs) in _ROWS.items():
        rows.append({
            "id": sid, "module": module, "cadence_s": cadence,
            "session": "24h",
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "bp_buffer_frac": 0.02, "flat_by_close": False,
            "flatten_time_et": None, "params": {}, "inputs": list(inputs),
            "parked": False,
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
