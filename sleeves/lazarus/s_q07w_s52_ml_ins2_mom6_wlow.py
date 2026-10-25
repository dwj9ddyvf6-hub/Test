"""Lazarus Q07 swing lane s_q07w_s52_ml_ins2_mom6_wlow -- v3-native build.

Catalog rule (SS4.1 family rule + lane row): Tensor 1W Swing signal,
midlarge band, filters ('ins2', 'mom6', 'wlow'); buy only on a QQQ-down day within 5
sessions of the signal; exit 15% stop or 52-week horizon.
Source status Disabled -> parked in v3 config (evaluates, dispatcher
skips entries while parked). Fires arrive via the desk Tensor bundle
producer (ledger substitution LAZ-B7)."""
from laz_sleeves._common import q07_evaluate

SLEEVE_ID = "s_q07w_s52_ml_ins2_mom6_wlow"
INPUTS = ("bars_1day", "positions", "tensor_fires", "alt_data", "vix")


def evaluate(view, ctx):
    return q07_evaluate(view, ctx, SLEEVE_ID, band="midlarge",
                        horizon_weeks=52, filters=('ins2', 'mom6', 'wlow'),
                        slots=1, slot_usd=1000.0)
