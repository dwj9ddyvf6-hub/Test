"""Adapter for qullamaggie (batch 5): v2 ctx -> ported qullamaggie signal(). Strategy
module sleeves/qullamaggie.py is byte-identical to source; this file is glue only."""
from adapters._batch5_common import (bar_dicts, bars_map, run_old,
                                      state_from_positions)
from sleeves import qullamaggie as _strat

SLEEVE_ID = "qullamaggie"
WARMUP_BARS = {"1Day": 127}

def _extra(ctx):
    p = ctx.params or {}
    return {"sleeve_state": p.get("sleeve_state") or state_from_positions(ctx),
            "trigger": p.get("trigger") or {},
            "qullamaggie_improve": p.get("qullamaggie_improve")
            or (p.get("extra") or {}).get("qullamaggie_improve")}

def evaluate(ctx):
    p = ctx.params or {}
    symbols = p.get("symbols") or ["NVDA", "AVGO", "META", "AMZN", "AAPL",
        "MSFT", "GOOGL", "TSLA", "AMD", "NFLX", "COST", "LLY", "JPM", "CAT",
        "GE", "PLTR", "CRWD", "AMAT", "MU", "PANW", "SPY", "QQQ", "IWM",
        "DIA", "GLD", "TLT", "XLF", "XLE", "XLK", "XLV", "WDC", "ANF",
        "CLS", "FFIV", "AAOI", "AXTI", "SOXL", "AEHR", "FCEL", "TTMI",
        "SIMO", "VICR", "AG", "SILJ", "SMCI", "APP", "HOOD", "COIN",
        "MSTR", "ARM", "MRVL", "SHOP", "UBER", "ABNB", "DDOG", "SNOW"]
    bars = bars_map(ctx, symbols, "1Day", 300)
    return run_old(ctx, SLEEVE_ID, _strat, bars, _extra(ctx))
