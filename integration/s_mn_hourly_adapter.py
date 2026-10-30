"""Lazarus s_mn_hourly -- Midna port (v3-native).

Catalog SS5.2: Tensor hourly signal (Midna rules); 15% stop or
60-bar time exit. 12 slots x $1,000. Source status Live. Signal
arrives via the desk Tensor-bundle hourly product (ledger
substitution LAZ-B7: the research midna_fires file is
unreachable from this box)."""
from laz_sleeves._common import mn_hourly_evaluate

SLEEVE_ID = "s_mn_hourly"
INPUTS = ("bars_1hour", "positions", "midna_signals")


def evaluate(view, ctx):
    return mn_hourly_evaluate(view, ctx, SLEEVE_ID, stop=True, slots=12)
