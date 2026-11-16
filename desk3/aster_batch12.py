"""Aster batch 12 registry (ASTER-BUILD-MAP batch 12, TSV 116-125).

All rows are LINKUSDT R19 crypto arms on desk3/aster_b12_crypto.py:
breakout_base fixed16 volume1pct (the funding-OFF price-only control —
declares bars/positions only) + negative_funding_squeeze x9 (fixed16 x2,
fixed96 x2, lost_breakout x2, normalization_failure x2, normalization
fullcash). Inputs: bars (native 4h crypto producer), funding (Binance
fundingRate capture named in ASTER-BUILD-MAP §4 — not yet wired, so the
NFS sleeves land visibly UNFED, never fake-fed), positions (broker
read-back).
"""
from __future__ import annotations
from desk3.aster_b12_crypto import SPECS, INPUTS, INPUTS_BREAKOUT

SLEEVE_IDS = tuple(SPECS)

PRODUCERS = {
 "crypto_bars": ({"name": "crypto_bars", "outputs": ("bars",), "freshness_sla_s": 14400},),
 "funding": ({"name": "binance_funding", "outputs": ("funding",), "freshness_sla_s": 28800},),
 "positions": ({"name": "broker_readback", "outputs": ("positions",), "freshness_sla_s": 900},),
}


def _inputs(sid):
    return INPUTS_BREAKOUT if SPECS[sid]["fam"] == "breakout_base" else INPUTS


def config_rows():
    return [{"id": sid, "module": f"adapters3.{sid}", "cadence_s": 14400,
             "session": "24h",
             "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
             "bp_buffer_frac": 0.02, "flat_by_close": False,
             "flatten_time_et": None, "params": {}, "inputs": list(_inputs(sid)),
             "parked": False} for sid in SLEEVE_IDS]
