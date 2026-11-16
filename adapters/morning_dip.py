"""Adapter for morning_dip (batch 5): v2 ctx -> ported morning_dip signal(). Strategy
module sleeves/morning_dip.py is byte-identical to source; this file is glue only."""
from adapters._batch5_common import (bar_dicts, bars_map, run_old,
                                      state_from_positions)
from sleeves import morning_dip as _strat

SLEEVE_ID = "morning_dip"
WARMUP_BARS = {"3Min": 16}

def _extra(ctx):
    p = ctx.params or {}
    return {"sleeve_state": p.get("sleeve_state") or state_from_positions(ctx),
            "candles_3min": bar_dicts(ctx, "QQQ", "3Min", 200),
            "morning_dip_improve": p.get("morning_dip_improve")
            or (p.get("extra") or {}).get("morning_dip_improve")}

def evaluate(ctx):
    return run_old(ctx, SLEEVE_ID, _strat, {}, _extra(ctx))
