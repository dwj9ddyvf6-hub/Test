"""Adapter for saty_gpt_v02 (batch 6) -- interface glue only (DESIGN S4).

Strategy lives, ported faithfully and unedited, in sleeves/saty_gpt_v02.py.
This file only re-shapes v2 cache/positions into the old signal()
inputs (see adapters/_old_bridge.py) and old Intents into v2 dicts.
Producer inputs the v2 cache does not carry (rule fires, earnings
calendar, options chains/quotes) arrive via ctx.params["extra"] or
the local options cache, exactly the old context.extra channel.
"""
from adapters._common import CANDIDATES
from adapters._old_bridge import first_bars, old_bars, run_old_signal

SLEEVE_ID = "saty_gpt_v02"
WARMUP_BARS = {'5Min': 1000, '1Day': 100}

BASKET_41 = ['SPY']

def _state(ctx):
    """ctx.positions -> old sleeve_state, pass-through plus the old
    record aliases (entry_px / entry_date / entry_time)."""
    state = {}
    for p in ctx.positions or []:
        pos = dict(p)
        if pos.get("avg_price") is not None:
            pos.setdefault("entry_px", pos.get("avg_price"))
            pos.setdefault("entry_premium", pos.get("avg_price"))
        if pos.get("opened_at"):
            pos.setdefault("entry_date", str(pos["opened_at"])[:10])
            pos.setdefault("entry_time", pos["opened_at"])
        state[pos["symbol"]] = {"position": pos if float(pos.get("qty") or 0) != 0 else None}
    return state

def _symbols(ctx):
    syms = list(BASKET_41) + [s for s in CANDIDATES if s not in BASKET_41]
    for s in (ctx.params or {}).get("universe") or []:
        if s not in syms: syms.append(s)
    for p in ctx.positions or []:
        if p["symbol"] not in syms: syms.append(p["symbol"])
    ex = (ctx.params or {}).get("extra") or {}
    for key in ("rule_fires", "rule_fires_1h", "chains", "sleeve_state"):
        d = ex.get(key) or {}
        if isinstance(d, dict):
            for s in d:
                if s not in syms: syms.append(s)
    return syms

def _bars(ctx, tf, n):
    out = {}
    for sym in _symbols(ctx):
        b = old_bars(ctx, sym, tf, n)
        if b: out[sym] = b
    return out

def _serve_journal(ctx):
    """Latest persisted gpt_v02_journal from the sleeve's own journal
    file (the v2-native store), or None. The sleeve's durable state —
    engine checkpoint, lots, emit-once dedupe — rides this channel
    (WIRING-SOURCE-MAP §4); without it every pass restarted fresh."""
    path = getattr(ctx, "_journal", None)
    if not path:
        return None
    try:
        from runtime.journal import tail_lines
        for rec in reversed(tail_lines(path, 2000)):
            if rec.get("event") == "gpt_v02_journal" \
                    and isinstance(rec.get("journal"), dict):
                return rec["journal"]
    except Exception:
        return None
    return None

def evaluate(ctx):
    daily = old_bars(ctx, "SPY", "1Day", 400)
    extra = {"sleeve_state": _state(ctx),
             "bars_5m_long": {"SPY": old_bars(ctx, "SPY", "5Min", 60000)},
             "bars_daily": {"SPY": daily}}
    params_extra = (ctx.params or {}).get("extra") or {}
    if "gpt_v02_journal" not in params_extra:
        served = _serve_journal(ctx)
        if served is not None:
            extra["gpt_v02_journal"] = served
    payload = None
    try: payload = ctx.options_chain("SPY")
    except Exception: payload = None
    if isinstance(payload, dict) and "latest_quote" in payload:
        extra["latest_quote"] = payload["latest_quote"]
    if "latest_quote" not in extra:
        # GAP-CURE: quotes_warm/read_quotes producer existed unwired;
        # the payload has no latest_quote key, so every signal died at
        # the fresh-quote gate.
        try:
            from adapters._bridge import latest_quotes_of, session_fills_of
            _lq = latest_quotes_of(ctx)
            if _lq: extra["latest_quote"] = _lq
            extra.setdefault("session_fills", session_fills_of(ctx))
        except Exception:
            pass
    # Run the sleeve class directly (the module-level signal() builds a
    # throwaway instance, losing the stamp) so the pass stamp — which
    # carries the updated gpt_v02_journal — can be persisted to the
    # sleeve journal and served back on the next pass. Translation and
    # old-context construction are the bridge's, unchanged.
    import importlib
    from adapters import _bridge as _B
    mod = importlib.import_module("sleeves.saty_gpt_v02")
    for k, v in params_extra.items():
        extra.setdefault(k, v)
    state = _B.state_old(ctx)
    old_ctx = _B.old_context_old(ctx, extra)
    inst = mod.SatyGptV02()
    intents = inst.signal({"SPY": daily}, state, old_ctx) or []
    stamp = getattr(inst, "last_evaluation", None) or {}
    journal = stamp.get("gpt_v02_journal")
    if isinstance(journal, dict):
        try: ctx.log("gpt_v02_journal", journal=journal)
        except Exception: pass
    out, seq = [], 0
    for it in intents:
        seq += 1
        t = _B.translate_old(it, ctx, seq)
        if t is not None:
            out.append(t)
    try:
        ctx.log("adapter_eval", module="sleeves.saty_gpt_v02",
                intents=len(out), bars={"SPY": len(daily)})
    except Exception:
        pass
    return out
