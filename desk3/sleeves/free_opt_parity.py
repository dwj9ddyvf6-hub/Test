"""v3 adapter for free_opt_parity: snapshot view -> v2 old-contract signal ->
v3 intent dicts. Faithful port of the muse-desk-v2 adapter; strategy
math lives unedited in desk3/strategies/free_opt_parity.py (single import-line
diff vs v2). Producer inputs arrive in the snapshot (view["extra"],
view["kraken_inputs"], view["options_chain"], view["bars"])."""
from desk3.bridge import ViewCtx, build_extra, old_bars, old_context, to_v2_intents

from desk3.strategies.free_opt_parity import signal as _signal
from desk3.enh2_edge16 import filter_parity_max_dte
SLEEVE_ID = "free_opt_parity"
INPUTS = ("options.chain", "bars")

def _parity_extra(c):
    extra = build_extra(c)
    if "parity_quotes" not in extra:
        try: chain = c.options_chain("SPY") or {}
        except Exception: chain = {}
        if isinstance(chain, dict) and chain.get("quotes") is not None:
            extra["parity_quotes"] = chain["quotes"]
    if "parity_spot" not in extra:
        for tf in ("1Day", "1Hour"):
            try: bars = c.bars("SPY", tf, 1)
            except Exception: bars = []
            if bars:
                try: extra["parity_spot"] = float(bars[-1].c)
                except (TypeError, ValueError): pass
                break
    return extra

def _expand_packages(intents):
    out = []
    for d in intents:
        legs = d.get("legs")
        if not legs:
            out.append(d); continue
        for j, leg in enumerate(legs, 1):
            leg_d = {"intent_id": "%s-%d" % (d["intent_id"], j),
                     "kind": d["kind"], "symbol": leg["symbol"],
                     "side": leg.get("side") or d["side"],
                     "qty": leg.get("qty", d["qty"]),
                     "order_type": "limit" if leg.get("limit_price") else "market",
                     "reason": "%s leg %d/%d %s %s" % (
                         d["reason"], j, len(legs), leg["symbol"],
                         leg.get("position_intent") or ""),
                     "time_in_force": d.get("time_in_force", "day"),
                     "legs": [dict(x) for x in legs]}
            if leg.get("limit_price"): leg_d["limit_price"] = float(leg["limit_price"])
            if leg.get("position_intent"): leg_d["position_intent"] = leg["position_intent"]
            if d.get("package_id"): leg_d["package_id"] = d["package_id"]
            out.append(leg_d)
    return out

def evaluate(view, ctx):
    c = ViewCtx(view, ctx)
    extra = _parity_extra(c)
    out = _expand_packages(to_v2_intents(c, SLEEVE_ID, _signal({}, {}, old_context(c, extra))))
    # ENH2 (Edge16): refuse boxes expiring >60 DTE (capital locked to expiry).
    return filter_parity_max_dte(out, view.get("extra") or {}, SLEEVE_ID,
                                 str(view.get("now") or "")[:10], 60)
