"""Milkman v2 study (quant-research-critical@0be4c575 milkman-study/v2): its daily rules and its SPY intraday setups,
each a sleeve under the manifest's exact id, plus the Milkman-family rows built on Author's Tensor lane fires
(Author-research: TENSOR_CREATIVE, bigwinners, and the study's own lane add-on rules). desk/sleeves/milkman/ holds the
rule programs (rules.py, daily.py), the intraday setups (intraday.py), the Tensor-fire sleeves and their producer
(Author.py) and the vendored study code (desk/vendor/milkman/, desk/vendor/Author_engine/); each module's docstring
lists its named divergences."""
from ..milkman import daily as _daily
from ..milkman import Author as _Author
from ..milkman import intraday as _intraday

FEEDS = {
    "milkman_bars": _daily.feed_bars,
    "milkman_quotes": (_daily.feed_quotes, {"per_sleeve": True}),
    "milkman_spy": _intraday.feed_spy,
    "Author": _Author.feed_Author,
    "Author_quotes": (_Author.feed_quotes, {"per_sleeve": True}),
    "Author_chains": (_Author.feed_chains, {"per_sleeve": True}),
}


def _Author_job(run_):
    return lambda engine: run_(engine.hub, engine.root, engine.clock())


# the Author sleeves' producers (desk/sleeves/milkman/Author.py): after each close the Tensor engine over the store_v1
# survivors' daily payloads (1D Green / 1D Swing fires for the lane add-on sleeve); each weekend the weekly fires, vote
# breadth and stock/SPY ratio fires (bigwinners, tensor_creative, lane add-ons)
JOBS = {
    "milkman_Author_daily": ("weekday:12345&et:16:40-23:59", 20 * 3600, _Author_job(_Author.run_daily)),
    "milkman_Author_weekly": ("weekday:67&et:06:00-23:59", 5 * 86400, _Author_job(_Author.run_weekly)),
}


def sleeves():
    return _daily.sleeves() + _intraday.sleeves() + _Author.sleeves()
