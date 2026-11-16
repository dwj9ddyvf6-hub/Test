"""Adapter for po10_qqq (batch 5): v2 ctx -> ported po10_qqq signal(). Strategy
module sleeves/po10_qqq.py is byte-identical to source; this file is glue only."""
from adapters._batch5_common import (bar_dicts, bars_map, run_old,
                                      state_from_positions)
from sleeves import po10_qqq as _strat

SLEEVE_ID = "po10_qqq"
WARMUP_BARS = {"5Min": 600}

def _fills(ctx):
    fn = getattr(ctx, "session_fills", None)
    try: return (fn() or []) if callable(fn) else []
    except Exception: return []

def _extra(ctx):
    p = ctx.params or {}
    bars5 = bar_dicts(ctx, "QQQ", "5Min", 4000)
    quote = p.get("latest_quote")
    if quote is None:
        # GAP-CURE: was fabricated from the last bar close +/-0.01
        # stamped t=now, defeating the sleeve's QUOTE_STALE fail-closed
        # gate and its one-entry-per-session proof. Serve the warmed
        # latest-quote cache instead; absent = sleeve fails closed.
        fn = getattr(ctx, "latest_quotes", None)
        try: quote = (fn() or {}) if callable(fn) else {}
        except Exception: quote = {}
    return {"bars_5m_long": {"QQQ": bars5},
            "sleeve_state": p.get("sleeve_state") or state_from_positions(ctx),
            "session_fills": p.get("session_fills") or _fills(ctx),
            "latest_quote": quote or {}}

def evaluate(ctx):
    return run_old(ctx, SLEEVE_ID, _strat, {}, _extra(ctx))
