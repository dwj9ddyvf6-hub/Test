"""Adapter for raschke_pf3 (batch 5): v2 ctx -> ported raschke_pf3 signal(). Strategy
module sleeves/raschke_pf3.py is byte-identical to source; this file is glue only."""
from adapters._batch5_common import (bar_dicts, bars_map, run_old, run_old_persisted,
                                      state_from_positions)
from sleeves import raschke_pf3 as _strat

SLEEVE_ID = "raschke_pf3"
WARMUP_BARS = {"5Min": 28}

def _extra(ctx):
    p = ctx.params or {}
    return {"bars_5m_long": {"SPY": bar_dicts(ctx, "SPY", "5Min", 2000)},
            "sleeve_state": p.get("sleeve_state") or state_from_positions(ctx),
            "session_fills": p.get("session_fills") or []}

def evaluate(ctx):
    return run_old_persisted(ctx, SLEEVE_ID, _strat, {}, _extra(ctx), ("gpf3_journal",))
