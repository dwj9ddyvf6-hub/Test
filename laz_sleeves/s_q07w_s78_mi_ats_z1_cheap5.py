"""Lazarus Q07 swing lane s_q07w_s78_mi_ats_z1_cheap5 -- v3-native build.

Catalog rule (SS4.1 family rule + lane row): Tensor 1W Swing signal,
micro band, filters ('ats_z1', 'cheap5'); buy only on a QQQ-down day within 5
sessions of the signal; exit 15% stop or 78-week horizon.
Source status Disabled -> parked in v3 config (evaluates, dispatcher
skips entries while parked). Fires arrive via the desk Tensor bundle
producer (ledger substitution LAZ-B7)."""
from laz_sleeves._common import q07_evaluate

SLEEVE_ID = "s_q07w_s78_mi_ats_z1_cheap5"
INPUTS = ("bars_1day", "positions", "tensor_fires", "alt_data", "vix")


def evaluate(view, ctx):
    return q07_evaluate(view, ctx, SLEEVE_ID, band="micro",
                        horizon_weeks=78, filters=('ats_z1', 'cheap5'),
                        slots=1, slot_usd=1000.0)
