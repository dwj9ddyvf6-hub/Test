"""Batch-2 port registry declarations (10 sleeves from muse-desk-v2).

Producer-registry inputs per sleeve, re-expressed from the v2 adapter's
documented producer inputs (context.extra doors + warmed bars), and the
config rows (slice/cadence/session/flatten) copied unchanged from
muse-desk-v2/config/sleeves.json @ 3593668. Producers themselves are
registered by the warm layer; a sleeve whose declared input is
unproduced or stale is UNFED by the Registry contract.
"""
from __future__ import annotations

# producer name -> (outputs, freshness SLA s)
PRODUCERS = {
    "bars": (("bars",), 3600.0),
    "broker_readback": (("positions",), 3600.0),
    "options": (("options",), 3600.0),
    "kraken": (("kraken",), 7200.0),
    "earnings": (("earnings",), 86400.0),
    "buyback_scan": (("buyback_scan",), 86400.0),
    "quotes": (("quotes",), 600.0),
    # EXPECTED-MOVE-FILING-20261030: the live VixProducer emits
    # the scalar "vix" and the literal VIX daily rows under
    # their own names; it never emitted a bare "extra" channel.
    "vix": (("vix", "bars:VIX:1Day"), 3600.0),
    "etf_books": (("extra",), 86400.0),
}

# sleeve_id -> declared snapshot input keys (producer outputs)
INPUTS = {
    "donchian_crypto": ("bars", "positions"),
    "earnings_buyback": ("bars", "positions", "options", "earnings",
                         "buyback_scan"),
    # EXPECTED-MOVE-FILING-20261030: was ("bars", "positions",
    # "options", "extra"); no live producer emits a bare "extra"
    # channel, so the sleeve was UNFED forever. Its real external
    # dependency is the VIX daily series, emitted by the live
    # VixProducer as "vix" + "bars:VIX:1Day".
    "em_1587": ("bars", "positions", "options", "vix",
                "bars:VIX:1Day"),
    "ema_vwap": ("bars", "positions"),
    "ema_vwap_options": ("bars", "positions", "options"),
    "fear_premium": ("bars", "positions", "options"),
    "free_etf": ("positions", "extra", "quotes"),
    "free_kraken_ada_basis": ("kraken", "positions"),
    "free_kraken_ada_breakdown": ("bars", "kraken", "positions"),
    "free_kraken_ada_crowded": ("bars", "kraken", "positions"),
}

# sleeve_id -> config row (verbatim fields from v2 config/sleeves.json)
CONFIG_ROWS = {
    "donchian_crypto": {"module": "adapters3.donchian_crypto", "cadence_s": 900, "session": "24h", "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}, "bp_buffer_frac": 0.02, "flat_by_close": False, "flatten_time_et": None, "params": {}},
    "earnings_buyback": {"module": "adapters3.earnings_buyback", "cadence_s": 300, "session": "rth", "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}, "bp_buffer_frac": 0.02, "flat_by_close": False, "flatten_time_et": None, "params": {}},
    "em_1587": {"module": "adapters3.em_1587", "cadence_s": 60, "session": "rth", "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}, "bp_buffer_frac": 0.02, "flat_by_close": False, "flatten_time_et": None, "params": {}},
    "ema_vwap": {"module": "adapters3.ema_vwap", "cadence_s": 300, "session": "rth", "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}, "bp_buffer_frac": 0.02, "flat_by_close": False, "flatten_time_et": None, "params": {}},
    "ema_vwap_options": {"module": "adapters3.ema_vwap_options", "cadence_s": 300, "session": "rth", "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}, "bp_buffer_frac": 0.02, "flat_by_close": False, "flatten_time_et": None, "session": "rth", "params": {}},
    "fear_premium": {"module": "adapters3.fear_premium", "cadence_s": 300, "session": "rth", "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}, "bp_buffer_frac": 0.02, "flat_by_close": False, "flatten_time_et": None, "params": {}},
    "free_etf": {"module": "adapters3.free_etf", "cadence_s": 60, "session": "24h", "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}, "bp_buffer_frac": 0.02, "flat_by_close": False, "flatten_time_et": None, "params": {}},
    "free_kraken_ada_basis": {"module": "adapters3.free_kraken_ada_basis", "cadence_s": 3600, "session": "24h", "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}, "bp_buffer_frac": 0.02, "flat_by_close": False, "flatten_time_et": None, "params": {}},
    "free_kraken_ada_breakdown": {"module": "adapters3.free_kraken_ada_breakdown", "cadence_s": 3600, "session": "24h", "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}, "bp_buffer_frac": 0.02, "flat_by_close": False, "flatten_time_et": None, "params": {}},
    "free_kraken_ada_crowded": {"module": "adapters3.free_kraken_ada_crowded", "cadence_s": 3600, "session": "24h", "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}, "bp_buffer_frac": 0.02, "flat_by_close": False, "flatten_time_et": None, "params": {}},
}


def register(registry):
    """Register batch-2 producers (idempotent) + sleeve input rows."""
    for name, (outputs, sla) in PRODUCERS.items():
        if name not in registry.producers:
            registry.register_producer(name, outputs, sla)
    for sid, inputs in INPUTS.items():
        registry.register_sleeve(sid, inputs)
    return registry


def install(desk):
    """Register producers + sleeves (config rows) on a Desk instance."""
    register(desk.registry)
    for sid, row in CONFIG_ROWS.items():
        desk.add_sleeve(sid, row["module"], INPUTS[sid], row["cadence_s"],
                        row["slice"]["capital_usd"])
    return desk
