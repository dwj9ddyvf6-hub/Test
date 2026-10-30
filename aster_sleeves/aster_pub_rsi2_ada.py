"""Aster batch 5: public_recipe::Filtered RSI2 dip rebound · ADAUSDT
(TSV #46 / SM PUBLIC_TOMAZETTI_RSI2_SPOT100). Hourly Wilder RSI2<10,
close>SMA200, SMA4(RSI2)<30; exit close>SMA5; stop disabled; long only;
100% available-cash sizing. Engine: aster_sleeves._common (archive
public_source_sleeves.py tomazetti_rsi2)."""
from aster_sleeves._common import evaluate_rsi2

SLEEVE_ID = "aster_pub_rsi2_ada"
INPUTS = ('bars', 'positions')
CADENCE_S = 3600


def evaluate(view, ctx):
    return evaluate_rsi2(view, ctx, SLEEVE_ID)
