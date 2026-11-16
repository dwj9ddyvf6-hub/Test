"""Adapter for tensor_red_dip (batch 7) -- interface glue only (DESIGN S4).

Strategy lives, ported faithfully and unedited, in sleeves/tensor_red_dip.py.
This file only re-shapes v2 cache/positions into the old signal()
inputs (see adapters/_old_bridge.py) and old Intents into v2 dicts.

Tensor bundle (WIRING-SOURCE-MAP §2): the warmer-side producer
(runtime/tensor_warm.py, core/tensor_feeds.TensorProducer over the
vendored hash-pinned engine) persists the bundle in the cache;
_bundle_extra serves this sleeve's slice of it (tensor_signals +
qqq_day_return / day_returns / nyse_holidays). Config params["extra"]
keeps precedence (the fixture channel), the bundle fills the rest.
"""
from adapters._old_bridge import first_bars, old_bars, run_old_persisted

SLEEVE_ID = "tensor_red_dip"
WARMUP_BARS = {'1Day': 5}

def _bundle_extra(ctx):
    fn = getattr(ctx, "tensor_bundle", None)
    bundle = {}
    if callable(fn):
        try:
            data = fn() or {}
        except Exception:
            data = {}
        bundle = dict((data.get("sleeves") or {}).get(SLEEVE_ID) or {})
    params_extra = (ctx.params or {}).get("extra") or {}
    return {k: v for k, v in bundle.items() if k not in params_extra}

def _symbols(ctx):
    syms = ["QQQ", "SPY"]
    for p in ctx.positions or []:
        if p["symbol"] not in syms:
            syms.append(p["symbol"])
    extra = dict((ctx.params or {}).get("extra") or {})
    for k, v in _bundle_extra(ctx).items():
        extra.setdefault(k, v)
    for sig in extra.get("tensor_signals") or []:
        if isinstance(sig, dict) and sig.get("symbol") not in syms:
            syms.append(sig["symbol"])
    return syms

def evaluate(ctx):
    bars = {s: first_bars(ctx, s, ["1Day"], 60) for s in _symbols(ctx)}
    return run_old_persisted(ctx, "sleeves.tensor_red_dip", bars,
                          _bundle_extra(ctx), None)
