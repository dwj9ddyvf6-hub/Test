"""quant_research: the research-archive strategy rows (quant-research-critical / quant-research-backup), each a
sleeve under the manifest's exact id. desk/sleeves/quant_research/ holds the sleeves, their producers and the shared
plumbing; desk/vendor/quant_research/ the vendored source (each module's docstring names its source, its named
divergences and its parity receipt)."""
from ..quant_research import airt as _airt
from ..quant_research import alphaqcm as _alphaqcm
from ..quant_research import bolt as _bolt
from ..quant_research import carm as _carm
from ..quant_research import cer as _cer
from ..quant_research import cqr as _cqr
from ..quant_research import crd as _crd
from ..quant_research import crg as _crg
from ..quant_research import factor_books as _factor_books
from ..quant_research import fastnumbers as _fastnumbers
from ..quant_research import finrlx as _finrlx
from ..quant_research import kronos as _kronos
from ..quant_research import news121 as _news121
from ..quant_research import relay as _relay
from ..quant_research import scores as _scores
from ..quant_research import sed as _sed
from ..quant_research import tcft as _tcft
from ..quant_research import uir as _uir

FEEDS = {
    "qr_scores": _scores.feed_scores,
    "qr_kronos": _kronos.feed_kronos,
    "qr_macro_cal": _bolt.feed_calendar,
    "qr_bolt_chains": (_bolt.feed_chains, {"per_sleeve": True}),
    "qr_fn_refresh": _fastnumbers.feed_refresh,
    "qr_news121": _news121.feed_snapshot,
    "qr_relay": _relay.feed_events,
    # prefilled (desk/feeds.py PREFILL's rule): the tape depends on the pass clock, SED's fixed universe and its own
    # module state only -- no hub bars or quotes, one sleeve -- so its bounded stream reads run beside the pass's
    # other network reads instead of inside SED's turn
    "qr_sed_tape": (_sed.feed_tape, {"prefill": True}),
}

# the family's producers. qr_scores / qr_kronos: after each close the AlphaMemo / QuantaAlpha frozen-model scores and,
# on each ten-session forecast date, the Kronos-base forecasts (kronos_runner.py under QR_KRONOS_PYTHON); each run is
# a no-op once the session's document is written, so they retry every half hour until it is. qr_macro_cal: weekday
# mornings, the BLS CPI / Employment Situation schedules BOLT's event calendar reads.
JOBS = {
    "qr_scores": ("weekday:12345&et:16:50-23:59", 1800,
                  lambda engine: _scores.run(engine.hub, engine.root, engine.clock())),
    "qr_kronos": ("weekday:12345&et:16:55-23:59", 1800,
                  lambda engine: _kronos.run(engine.hub, engine.root, engine.clock())),
    "qr_macro_cal": ("weekday:12345&et:07:00-09:20", 20 * 3600,
                     lambda engine: _bolt.run_calendar(engine.root, engine.clock())),
    # News 12-1's monthly snapshot (S&P 500 12-1 momentum pool) after each month's final session; a no-op until due
    "qr_news121": ("weekday:12345&et:16:25-23:59", 1800,
                   lambda engine: _news121.run(engine.hub, engine.root, engine.clock())),
    # UIR / CRG source events: CAT, DE, MSFT quarterly filings (SEC companyfacts + acceptance times), after the close
    "qr_relay": ("weekday:12345&et:16:20-23:59", 6 * 3600,
                 lambda engine: _relay.run(engine.root, engine.clock())),
}


def sleeves():
    return (_finrlx.sleeves() + _alphaqcm.sleeves() + _factor_books.sleeves() + _kronos.sleeves() + _bolt.sleeves()
            + _fastnumbers.sleeves() + _news121.sleeves() + _cer.sleeves() + _cqr.sleeves() + _tcft.sleeves()
            + _carm.sleeves() + _uir.sleeves() + _crg.sleeves() + _airt.sleeves() + _sed.sleeves()
            + _crd.sleeves())
