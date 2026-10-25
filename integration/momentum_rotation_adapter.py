"""Adapter for momentum_rotation (batch 5): v2 ctx -> ported momentum_rotation signal(). Strategy
module sleeves/momentum_rotation.py is byte-identical to source; this file is glue only."""
from adapters._batch5_common import (bar_dicts, bars_map, run_old_persisted,
                                      state_from_positions)
from sleeves import momentum_rotation as _strat

SLEEVE_ID = "momentum_rotation"
WARMUP_BARS = {"1Day": 65}

def _extra(ctx):
    p = ctx.params or {}
    st = state_from_positions(ctx)
    return {"sleeve_state": p.get("sleeve_state") or st,
            "last_rebalance": p.get("last_rebalance"),
            "meta": p.get("meta") or {}}

def evaluate(ctx):
    p = ctx.params or {}
    symbols = p.get("symbols") or ["SPY", "QQQ", "IWM", "DIA", "GLD", "TLT",
        "XLF", "XLE", "XLK", "XLV", "AAPL", "MSFT", "NVDA", "AMZN", "META",
        "GOOGL", "TSLA", "AMD", "NFLX", "COST"]
    bars = bars_map(ctx, symbols, "1Day", 200)
    return run_old_persisted(ctx, SLEEVE_ID, _strat, bars, _extra(ctx), ("momentum_rotation_exp_journal",))
