"""Milkman v2 study (quant-research-critical@0be4c575 milkman-study/v2): its daily rules and its SPY intraday setups,
each a sleeve under the manifest's exact id, plus the Milkman-family rows built on Galath's Tensor lane fires
(galath-research: TENSOR_CREATIVE, bigwinners, and the study's own lane add-on rules). desk/sleeves/milkman/ holds the
rule programs (rules.py, daily.py), the intraday setups (intraday.py), the Tensor-fire sleeves and their producer
(galath.py) and the vendored study code (desk/vendor/milkman/, desk/vendor/galath_engine/); each module's docstring
lists its named divergences."""
from ..milkman import daily as _daily
from ..milkman import galath as _galath
from ..milkman import intraday as _intraday

FEEDS = {
    "milkman_bars": _daily.feed_bars,
    "milkman_quotes": (_daily.feed_quotes, {"per_sleeve": True}),
    "milkman_spy": _intraday.feed_spy,
    "galath": _galath.feed_galath,
    "galath_quotes": (_galath.feed_quotes, {"per_sleeve": True}),
    "galath_chains": (_galath.feed_chains, {"per_sleeve": True}),
}


def _galath_job(run_):
    return lambda engine: run_(engine.hub, engine.root, engine.clock())


# the galath sleeves' producers (desk/sleeves/milkman/galath.py): after each close the Tensor engine over the store_v1
# survivors' daily payloads (1D Green / 1D Swing fires for the lane add-on sleeve); each weekend the weekly fires, vote
# breadth and stock/SPY ratio fires (bigwinners, tensor_creative, lane add-ons)
JOBS = {
    "milkman_galath_daily": ("weekday:12345&et:16:40-23:59", 20 * 3600, _galath_job(_galath.run_daily)),
    "milkman_galath_weekly": ("weekday:67&et:06:00-23:59", 5 * 86400, _galath_job(_galath.run_weekly)),
}


def sleeves():
    return _daily.sleeves() + _intraday.sleeves() + _galath.sleeves()
