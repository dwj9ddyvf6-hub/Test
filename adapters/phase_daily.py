"""Adapter for phase_daily (batch 5): v2 ctx -> ported phase_daily signal(). Strategy
module sleeves/phase_daily.py is byte-identical to source; this file is glue only.

ENH (plan R-2 closeout, 2026-10-24): the earnings calendar the
flatten + re-entry arm consumes is produced at warm time only
(runtime/earnings_warm.py -> BarCache cache/earnings/calendar.json,
served via ctx.earnings_calendar()) and injected here under the
documented keys extra["earnings"] / extra["earnings_time"] /
extra["earnings_fresh"] — the _kraken_extra precedent: config
params (top level, then params["extra"]) keep precedence over the
cache, the fixture channel. Evaluations make 0 network calls."""
from adapters._batch5_common import (bar_dicts, bars_map, run_old, run_old_persisted,
                                      state_from_positions)
from sleeves import phase_daily as _strat

SLEEVE_ID = "phase_daily"
WARMUP_BARS = {"1Day": 60}

def _earnings_payload(ctx):
    fn = getattr(ctx, "earnings_calendar", None)
    if not callable(fn):
        return {}
    try:
        return fn() or {}
    except Exception:
        return {}

def _extra(ctx):
    p = ctx.params or {}
    pextra = p.get("extra") or {}
    payload = _earnings_payload(ctx)

    def _pick(key, cache_val):
        if key in p:
            return p[key]
        if key in pextra:
            return pextra[key]
        return cache_val

    return {"sleeve_state": p.get("sleeve_state") or state_from_positions(ctx),
            "universe": p.get("symbols"),
            "earnings": _pick("earnings", payload.get("earnings") or {}),
            "earnings_time": _pick("earnings_time",
                                   payload.get("earnings_time") or {}),
            "earnings_fresh": bool(_pick("earnings_fresh",
                                         bool(payload.get("fresh")))),
            "phase_daily_enhance": p.get("phase_daily_enhance")
            or pextra.get("phase_daily_enhance"),
            "phase_daily_enh_journal": p.get("phase_daily_enh_journal")
            or pextra.get("phase_daily_enh_journal")}

def evaluate(ctx):
    p = ctx.params or {}
    symbols = p.get("symbols") or ["SPY", "QQQ", "IWM", "DIA", "GLD",
        "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "AMD",
        "NFLX", "COST", "MU", "WDC", "ANF", "CLS", "FFIV"]
    bars = bars_map(ctx, symbols, "1Day", 300)
    return run_old_persisted(ctx, SLEEVE_ID, _strat, bars, _extra(ctx), ("phase_daily_enh_journal",))
