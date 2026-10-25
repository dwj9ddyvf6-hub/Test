"""v3 port of v2 sleeve iron_condor (batch 4).

Strategy: desk3/vendor/sleeves/iron_condor.py — byte-identical copy of the v2
sleeve (sha256-pinned by tests/test_port_batch4_blockers.py).
Adapter: the v2 adapter body below, copied with import lines rewritten
to the vendored bridge (desk3/port4_bridge.py) only; logic untouched,
including every Edge enhancement switch/default and gap-audit cure.
Inputs are re-expressed as the INPUTS producer-registry declaration;
evaluate(view, ctx) serves them from the v3 snapshot via
desk3/port4_context.py.
"""
from desk3.port4_context import evaluate_via

INPUTS = ('bars:*:1Day', 'bars:VIX:1Day', 'options:chains', 'earnings', 'iv')

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from desk3.port4_bridge import CANDIDATES, ET, OldContext
from desk3.port4_bridge import bar_dict_common as bar_dict
from desk3.port4_bridge import epoch_common as _epoch
from desk3.port4_bridge import fetch_bars, held_map, make_old_context
from desk3.port4_bridge import state_common as sleeve_state_from_positions
from desk3.port4_bridge import symbols_for
from desk3.port4_bridge import translate_common as translate_intents

from desk3.port4_context import load_strategy
strat = load_strategy("iron_condor")
SLEEVE_ID = "iron_condor"
WARMUP_BARS = {"1Day": 30}
def _evaluate_v2(ctx):
    syms = list(strat.WATCHLIST)
    bars = fetch_bars(ctx, syms, "1Day", 60)
    derived = {"sleeve_state": sleeve_state_from_positions(ctx)}
    # Options products arrive via params.extra or the options cache payload
    # shaped as the old extra dict; absent them entries fail closed in the
    # strategy itself, while DTE/max-hold exits still evaluate from bars.
    for sym in syms:
        try:
            chain = ctx.options_chain(sym)
        except Exception:
            chain = None
        if isinstance(chain, dict) and ("chains" in chain or "quotes" in chain):
            for k, v in chain.items():
                if isinstance(v, dict):
                    cur = derived.setdefault(k, {})
                    if isinstance(cur, dict):
                        cur.update(v)
    # GAP-CURE: serve the produced inputs the sleeve gates on — VIX from
    # warmed VIX bars (momentum precedent), earnings_in_days from the
    # warmed calendar, iv/iv_history from the warm-time IV ledger.
    if not derived.get("vix"):
        _vb = fetch_bars(ctx, ["VIX"], "1Day", 10).get("VIX") or []
        if len(_vb) >= 2:
            from datetime import datetime as _dt, timezone as _tz
            derived["vix"] = (float(_vb[-1]["c"]), float(_vb[-2]["c"]),
                              _dt.fromtimestamp(float(_vb[-1]["t"]), tz=_tz.utc).date().isoformat(), "cache")
    try:
        _cal = ctx.earnings_calendar() or {}
        _earn = _cal.get("earnings") or {}
        if _earn:
            from datetime import date as _date
            _today = ctx.now.date()
            derived.setdefault("earnings_in_days", {
                s: (_date.fromisoformat(str(v)[:10]) - _today).days
                for s, v in _earn.items() if v})
    except Exception:
        pass
    try:
        _iv = {}
        _hist = {}
        for sym in syms:
            _p = ctx.iv_history(sym) or {}
            if _p.get("history"): _hist[sym] = _p["history"]
            if _p.get("current") is not None: _iv[sym] = _p["current"]
        if _iv: derived.setdefault("iv", _iv)
        if _hist: derived.setdefault("iv_history", _hist)
    except Exception:
        pass
    old = make_old_context(ctx, derived)
    out = translate_intents(strat.signal(bars, {}, old), SLEEVE_ID, ctx, held_map(ctx))
    # GAP-CURE: fan the 4-leg condor out to per-leg OCC intents (parity
    # precedent) carrying the condor map + entry credit, instead of one
    # underlying-symbol sale the dispatcher priced as a stock.
    import re as _re
    _OCC = r"([A-Z]{1,6}\d{6}[CP]\d{8})"
    res = []
    for d in out:
        r = d.get("reason") or ""
        mp = _re.search(r"put=" + _OCC + r"@[0-9.]+/" + _OCC + r"@[0-9.]+", r)
        mc = _re.search(r"call=" + _OCC + r"@[0-9.]+/" + _OCC + r"@[0-9.]+", r)
        if d["kind"] == "entry" and mp and mc:
            _cr = _re.search(r"credit=([0-9.]+)", r); _wd = _re.search(r"width=([0-9.]+)", r)
            _ex = _re.search(r"expiry=(\d{4}-\d{2}-\d{2})", r)
            condor = {"put_short_occ": mp.group(1), "put_long_occ": mp.group(2),
                      "call_short_occ": mc.group(1), "call_long_occ": mc.group(2),
                      "width": float(_wd.group(1)) if _wd else None,
                      "expiry": _ex.group(1) if _ex else None}
            legs = ((mp.group(1), "sell_to_open"), (mp.group(2), "buy_to_open"),
                    (mc.group(1), "sell_to_open"), (mc.group(2), "buy_to_open"))
            for j, (occ, pi) in enumerate(legs, 1):
                leg = dict(d)
                leg["intent_id"] = "%s-%d" % (d["intent_id"], j)
                leg["symbol"] = occ; leg["position_intent"] = pi
                leg["side"] = "buy" if pi.startswith("buy") else "sell"
                leg["condor"] = condor
                if _cr: leg["entry_credit"] = float(_cr.group(1))
                leg["package_id"] = d["intent_id"]
                res.append(leg)
            continue
        res.append(d)
    return res


def evaluate(view, ctx):
    return evaluate_via(view, ctx, _evaluate_v2)
