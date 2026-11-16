"""v3 sleeve b3_midday_fade_var: C03 session-segment shape
(midday leg) variation, live (Conversion Program CONV-108,
SEGMENT-CONSTRUCTION-20261116): the shared intraday segment
engine in desk3/intraday_segments.py, rostered live under the
owner ruling of Sun 2026-11-15 22:35 ET (no shadow sleeves;
live only) under the register row's own proposed id. See
config/segment_sleeves_20261116.json for the registered
falsifier and kill rule, byte-identical to the Conversion
Register row."""
from desk3.intraday_segments import evaluate as _ev, INPUTS, PRODUCERS
SLEEVE_ID = "b3_midday_fade_var"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
