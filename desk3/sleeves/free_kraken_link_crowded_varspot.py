"""v3 adapter for free_kraken_link_crowded_varspot: snapshot view
-> variation signal -> v3 intent dicts. Spot-expression variation
of free_kraken_link_crowded (PF-SPOT-VARIATIONS-20261116);
strategy math lives in
desk3/strategies/free_kraken_link_crowded_varspot.py.

Producer inputs, from the snapshot only:
- the served LINK/USD spot 4h tape (view bars LINK/USD|4Hour),
  keyed under the traded symbol LINK/USD — the spot substitution
  for the parent's PF_LINKUSD bars;
- extra["funding_rates"]: the PF_LINKUSD series of the
  snapshot's kraken.funding key — the parent's own funding gate
  input, carried unchanged (a PF-market conditioner, named in
  the strategy docstring, never replaced with a spot proxy).
  Same wiring shape as the parent LINK crowded adapter;
- the served BTC/USD spot 4h tape (view bars BTC/USD|4Hour) —
  the paired relative-value anchor leg's tape
  (PF-PAIRED-RV-20261116, MAKE-IT-WORK Decision C 2026-11-16),
  served by the same bars producer (warm CRYPTO_FETCHES BTC/USD
  4Hour), so INPUTS is unchanged: "bars" already declares both
  tapes, matching the config row's inputs.
"""
from desk3.bridge import ViewCtx, build_extra, old_bars, old_context, to_v2_intents

from desk3.strategies.free_kraken_link_crowded_varspot import signal as _signal

SLEEVE_ID = "free_kraken_link_crowded_varspot"
INPUTS = ("bars", "kraken.quote", "kraken.funding")


def evaluate(view, ctx):
    c = ViewCtx(view, ctx)
    extra = build_extra(c)
    if "sleeve_state_flat" in extra:
        extra["sleeve_state"] = extra["sleeve_state_flat"]
    if "funding_rates" not in extra:
        _fund = (view or {}).get("kraken.funding") or {}
        _rates = _fund.get("PF_LINKUSD") if isinstance(_fund, dict) else None
        if _rates is not None:
            extra["funding_rates"] = _rates
    bars = {"LINK/USD": old_bars(c, "LINK/USD", "4Hour", 500),
            "BTC/USD": old_bars(c, "BTC/USD", "4Hour", 500)}
    return to_v2_intents(c, SLEEVE_ID, _signal(bars, {}, old_context(c, extra)))
