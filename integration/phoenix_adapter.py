"""Adapter for phoenix (batch 5): v2 ctx -> ported phoenix signal(). Strategy
module sleeves/phoenix.py is byte-identical to source; this file is glue only."""
from adapters._batch5_common import (bar_dicts, bars_map, run_old,
                                      state_from_positions)
from sleeves import phoenix as _strat

SLEEVE_ID = "phoenix"
WARMUP_BARS = {"1Day": 61}

def _cal(ctx):
    fn = getattr(ctx, "earnings_calendar", None)
    if not callable(fn): return {}
    try: return fn() or {}
    except Exception: return {}

def _extra(ctx):
    p = ctx.params or {}
    _caldata = _cal(ctx)
    forming = {}
    for sym in _strat.CONFIG.universe:
        bl = bar_dicts(ctx, sym, "1Day", 1)
        if bl:
            b = bl[-1]
            forming[sym] = {"o": b["o"], "c": b["c"], "v": b["v"]}
    return {"sleeve_state": p.get("sleeve_state") or state_from_positions(ctx),
            "meta": p.get("meta") or {},
            "forming": p.get("forming") or forming,
            "earnings": p.get("earnings") or _caldata.get("earnings") or {},
            "earnings_fresh": bool(p.get("earnings_fresh") or _caldata.get("fresh")),
            "broker_qty": {pos["symbol"]: float(pos.get("qty") or 0)
                           for pos in ctx.positions or []},
            "foreign_holders": p.get("foreign_holders") or {}}

def evaluate(ctx):
    bars = bars_map(ctx, list(_strat.CONFIG.universe), "1Day", 300)
    return run_old(ctx, SLEEVE_ID, _strat, bars, _extra(ctx))
