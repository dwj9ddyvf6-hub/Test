"""v3 sleeve overnight_basket8: the basket8 overnight basket, live (Conversion Program CONV-03,
GOING-LIVE-BASKETS-20261115): the overnight basket engine in
desk3/overnight_baskets.py, rostered live under the owner
ruling of Sun 2026-11-15 22:35 ET (no shadow sleeves; live
only). See config/overnight_baskets_20261115.json for the
registered falsifier and kill rule."""
from desk3.overnight_baskets import evaluate as _ev, INPUTS, PRODUCERS
SLEEVE_ID = "overnight_basket8"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
