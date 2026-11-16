"""v3 sleeve revival_basket: the CONV-123 graveyard revival
basket, live (CONV123-REVIVAL-20261116): the revival basket
engine in desk3/revival_basket.py, rostered live under the
Conversion Program. Each pulse family (turn-of-month, pairs
Gatev form, PEAD drift form) enters only when its frozen
revival rule fires on the accrual served by
desk3/revival_producers.py; accrual counts from Mon
2026-11-16. See config/revival_basket_20261116.json for the
registered falsifier and kill rule."""
from desk3.revival_basket import evaluate as _ev, INPUTS, PRODUCERS
SLEEVE_ID = "revival_basket"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
