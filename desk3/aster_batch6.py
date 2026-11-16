"""Aster batch 6 registry rows. Inputs: bars (4h crypto producer),
funding (Binance funding producer named in ASTER-BUILD-MAP §4 — not yet
wired, so these sleeves land visibly UNFED), positions (broker read-back)."""
from desk3.aster_crypto import SPECS, INPUTS
PRODUCERS={"bars":({"name":"crypto_bars","outputs":("bars",),"freshness_sla_s":14400},),
 "funding":({"name":"binance_funding","outputs":("funding",),"freshness_sla_s":28800},),
 "positions":({"name":"broker_readback","outputs":("positions",),"freshness_sla_s":900},)}
def config_rows():
    return [{"id":sid,"module":f"adapters3.{sid}","cadence_s":14400,"session":"24h",
             "slice":{"capital_usd":10000.0,"cash_usd":10000.0},"bp_buffer_frac":0.02,
             "flat_by_close":False,"flatten_time_et":None,"params":{},"inputs":list(INPUTS),
             "parked":False} for sid in SPECS]
