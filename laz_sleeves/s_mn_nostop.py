"""Lazarus s_mn_nostop -- Midna port (v3-native).

Catalog SS5.2: the same hourly Tensor signal as s_mn_hourly, run
with NO stop; time exit after 60 bars only. 1 slot x $1,000.
Source status Live."""
from laz_sleeves._common import mn_hourly_evaluate

SLEEVE_ID = "s_mn_nostop"
INPUTS = ("bars_1hour", "positions", "midna_signals")


def evaluate(view, ctx):
    return mn_hourly_evaluate(view, ctx, SLEEVE_ID, stop=False, slots=1)
