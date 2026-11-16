"""v3 sleeve ls9_midday_short: LS9 short the midday segment,
only after an up drive, live (Conversion Program CONV-88,
SEGMENT-CONSTRUCTION-20261116): the shared intraday segment
engine in desk3/intraday_segments.py, rostered live under the
owner ruling of Sun 2026-11-15 22:35 ET (no shadow sleeves;
live only). See config/segment_sleeves_20261116.json for the
registered falsifier and kill rule, byte-identical to the
Conversion Register row."""
from desk3.intraday_segments import evaluate as _ev, INPUTS, PRODUCERS
SLEEVE_ID = "ls9_midday_short"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
