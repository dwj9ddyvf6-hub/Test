"""v3 adapter for free_kraken_link_basis: snapshot view -> v2 old-contract signal ->
v3 intent dicts. Faithful port of the muse-desk-v2 adapter; strategy
math lives unedited in desk3/strategies/free_kraken_link_basis.py (single import-line
diff vs v2). Producer inputs arrive in the snapshot (view["extra"],
view["kraken_inputs"], view["options_chain"], view["bars"])."""
from desk3.bridge import ViewCtx, build_extra, old_bars, old_context, to_v2_intents

from desk3.strategies.free_kraken_link_basis import signal as _signal
from desk3.enhance15 import filter_entries
SLEEVE_ID = "free_kraken_link_basis"
INPUTS = ("kraken.basis", "kraken.quote")

def _kraken_extra(c):
    try: data = c.kraken_inputs() or {}
    except Exception: return {}
    return dict((data.get("sleeves") or {}).get(SLEEVE_ID) or {})

def evaluate(view, ctx):
    c = ViewCtx(view, ctx)
    extra = build_extra(c)
    if "sleeve_state_flat" in extra:
        extra["sleeve_state"] = extra["sleeve_state_flat"]
    if "basis" not in extra:
        _k = _kraken_extra(c).get("basis")
        if _k is not None: extra["basis"] = _k
    if "quote" not in extra:
        _kx = _kraken_extra(c)
        _kq = _kx.get("quote")
        if _kq is None and isinstance(_kx.get("basis"), dict):
            _kq = _kx["basis"].get("quote")
        if _kq is not None: extra["quote"] = _kq
    return filter_entries(SLEEVE_ID, to_v2_intents(c, SLEEVE_ID, _signal({}, {}, old_context(c, extra))), view, extra)
