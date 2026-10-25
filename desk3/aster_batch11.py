"""Aster batch 11 registry (ASTER-BUILD-MAP batch 11, TSV 106-115).

ETF rows reuse the batch-10 ETF engine (desk3/aster_etf.py) — SPY specs
are registered into its SPECS additively here (policy/frequency/
gross/fixed_weights verified against archive etf_rules.json:
SPY_HOLD_FULL BUY_HOLD gross 1.0 {SPY:1}; SPY_MONTHLY MONTHLY gross
0.98 / 1.5 {SPY:1}). Crypto rows use desk3/aster_b11_crypto.py.
Inputs: ETF bars/positions/quotes (v3 producers); crypto bars/funding/
positions — no funding producer is wired in v3 yet, so funding-gated
crypto sleeves land visibly UNFED (build-map §4), never fake-fed.
"""
from __future__ import annotations
import desk3.aster_etf as _etf
from desk3.aster_b11_crypto import SPECS as CRYPTO_SPECS, INPUTS as CRYPTO_INPUTS

ETF_SPECS = {
 "aster_etf_spy_buy_hold": dict(policy="SPY_HOLD_FULL", freq="BUY_HOLD", gross=1.0, weights={"SPY": 1.0}),
 "aster_etf_spy_monthly_c098": dict(policy="SPY_MONTHLY", freq="MONTHLY", gross=0.98, weights={"SPY": 1.0}),
 "aster_etf_spy_monthly_m150": dict(policy="SPY_MONTHLY", freq="MONTHLY", gross=1.5, weights={"SPY": 1.0}),
}
for _sid, _spec in ETF_SPECS.items():
    _etf.SPECS.setdefault(_sid, _spec)

ETF_IDS = tuple(ETF_SPECS)
CRYPTO_IDS = tuple(CRYPTO_SPECS)
SLEEVE_IDS = ETF_IDS + CRYPTO_IDS
ETF_INPUTS = ("bars", "positions", "quotes")

PRODUCERS = {
 "bars": ({"name": "bars", "outputs": ("bars",), "freshness_sla_s": 900},),
 "crypto_bars": ({"name": "crypto_bars", "outputs": ("bars",), "freshness_sla_s": 14400},),
 "funding": ({"name": "binance_funding", "outputs": ("funding",), "freshness_sla_s": 28800},),
 "positions": ({"name": "broker_readback", "outputs": ("positions",), "freshness_sla_s": 900},),
 "quotes": ({"name": "quotes", "outputs": ("quotes",), "freshness_sla_s": 60},),
}

def config_rows():
    rows = []
    for sid in ETF_IDS:
        rows.append({"id": sid, "module": f"adapters3.{sid}", "cadence_s": 300,
            "session": "rth", "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "bp_buffer_frac": 0.02, "flat_by_close": False, "flatten_time_et": None,
            "params": {}, "inputs": list(ETF_INPUTS), "parked": False})
    for sid in CRYPTO_IDS:
        rows.append({"id": sid, "module": f"adapters3.{sid}", "cadence_s": 14400,
            "session": "24h", "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "bp_buffer_frac": 0.02, "flat_by_close": False, "flatten_time_et": None,
            "params": {}, "inputs": list(CRYPTO_INPUTS), "parked": False})
    return rows
