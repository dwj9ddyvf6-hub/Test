"""v3 adapter for free_kraken_link_basis_varspot: snapshot view ->
variation signal -> v3 intent dicts. Spot-expression variation of
free_kraken_link_basis (PF-SPOT-VARIATIONS-20261116); strategy
math lives in desk3/strategies/free_kraken_link_basis_varspot.py.

Producer inputs, from the snapshot only:
- extra["basis"]: the PARENT sleeve's kraken basis entry
  (kraken_inputs sleeves[free_kraken_link_basis]) — the parent's
  own perp-vs-spot series, the variation's unchanged signal
  (the parent LINK breakdown/crowded adapters read the parent
  basis sleeve's quote the same way).
- extra["spot_reference"]: {price, bar_t} from the newest bar of
  the served LINK/USD spot tape (view bars LINK/USD|4Hour).
"""
from desk3.bridge import ViewCtx, build_extra, old_bars, old_context, to_v2_intents

from desk3.strategies.free_kraken_link_basis_varspot import signal as _signal
from desk3.enhance15 import filter_entries

SLEEVE_ID = "free_kraken_link_basis_varspot"
PARENT_ID = "free_kraken_link_basis"
INPUTS = ("kraken.basis", "kraken.quote", "bars")


def _kraken_extra(c):
    try:
        data = c.kraken_inputs() or {}
    except Exception:
        return {}
    return dict((data.get("sleeves") or {}).get(PARENT_ID) or {})


def evaluate(view, ctx):
    c = ViewCtx(view, ctx)
    extra = build_extra(c)
    if "sleeve_state_flat" in extra:
        extra["sleeve_state"] = extra["sleeve_state_flat"]
    if "basis" not in extra:
        _k = _kraken_extra(c).get("basis")
        if _k is not None:
            extra["basis"] = _k
    spot = old_bars(c, "LINK/USD", "4Hour", 500)
    if spot:
        from datetime import datetime, timezone
        last = spot[-1]
        extra["spot_reference"] = {
            "price": last["c"],
            "bar_t": datetime.fromtimestamp(last["t"],
                                            tz=timezone.utc).isoformat()}
    return filter_entries(
        SLEEVE_ID,
        to_v2_intents(c, SLEEVE_ID, _signal({}, {}, old_context(c, extra))),
        view, extra)
