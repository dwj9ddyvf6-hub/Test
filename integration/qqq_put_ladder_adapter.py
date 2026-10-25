"""Adapter for qqq_put_ladder (batch 5): v2 ctx -> ported qqq_put_ladder signal(). Strategy
module sleeves/qqq_put_ladder.py is byte-identical to source; this file is glue only."""
from adapters._batch5_common import (bar_dicts, bars_map, run_old,
                                      state_from_positions)
from sleeves import qqq_put_ladder as _strat

SLEEVE_ID = "qqq_put_ladder"
WARMUP_BARS = {"1Day": 10}

def _extra(ctx):
    p = ctx.params or {}
    chain = ctx.options_chain("QQQ") or {}
    quotes = chain.get("quotes") if isinstance(chain, dict) else None
    closes = [b["c"] for b in bar_dicts(ctx, "QQQ", "1Day", 30)]
    layers = p.get("layers")
    if layers is None:
        # GAP-CURE: layers ARE the book state; build them from the
        # sleeve's own open OCC positions (adapter served [] always, so
        # no 21-DTE/challenged/5-DTE management could ever fire).
        layers = []
        from runtime.options_warm import parse_occ
        for pos in getattr(ctx, "positions", None) or []:
            parsed = parse_occ(pos.get("symbol") or "")
            if not parsed: continue
            layers.append({"id": pos["symbol"], "symbol": pos["symbol"],
                           "strike": parsed["strike"], "expiration": parsed["expiration"],
                           "qty": int(float(pos.get("qty") or 0)),
                           "entry_delta": None, "status": "open",
                           "entry_spot": None})
    return {"quotes": p.get("quotes") or quotes or [],
            "layers": layers,
            "spot": p.get("spot"), "posture": p.get("posture") or "unknown",
            "qqq_closes": closes,
            "buying_power": float((ctx.slice or {}).get("cash_usd") or 0),
            "week_opened": p.get("week_opened"),
            "qqq_put_ladder_improve": p.get("qqq_put_ladder_improve")
            or (p.get("extra") or {}).get("qqq_put_ladder_improve")}

def evaluate(ctx):
    bars = bars_map(ctx, ["QQQ"], "1Day", 30)
    return run_old(ctx, SLEEVE_ID, _strat, bars, _extra(ctx))
