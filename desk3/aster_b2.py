"""Aster batch 2 engine — pead / core_reserve / recovery(RSI2) options sleeves.

Faithful port of archive `source/backend/r19_options.py` evaluate paths for
families pead, core_reserve, recovery + books in options_rules.json:
- recovery/core RSI2: 200 completed sessions, close>SMA200 and RSI2<10
  (source rsi2 smoothing reproduced verbatim); entry window 09:35-09:40 ET.
- pead: producer-built event (source build_pead_event/pead_signal): pass iff
  surprise <= 20th-percentile threshold of >=200 prior events, spot>=5,
  mean20 dollar volume >= $1M, and today == entry_session (event_date+3).
- Contract selection: DTE/delta bands, min (expiry, |delta-mid|, |strike-spot|);
  vertical wing = strike nearest spot*1.02 (call) / spot*0.95 (put) beyond long.
- Sizing: risk_budget = risk_fraction x $10,000 slice; qty=floor(risk/per-contract
  cash debit incl. fees), capped by displayed size. Long: debit/(spot*100)<=
  max_premium_spot; vertical: debit/width<=max_debit_width.
- Exits (source _exit_intents): planned session exit at hold_sessions;
  pre-expiry guard (session >= day before expiry); touch sleeves only:
  underlying bid >= entry_spot*1.02 while market open. Core QQQ leg: source
  emits it once at 95% of capital and NEVER exits it (no rule) — preserved.
Fees: source reads snapshot option_fees.per_contract_per_fill; v3 producer
does not supply it, so $0.65/contract/leg is used (recorded in FIDELITY-LEDGER).
Inputs not produced by v3 producers (options chain, earnings_events) leave
the sleeves UNFED in the registry — never fake-fed.
"""
from __future__ import annotations
from datetime import date, datetime, timedelta

FEE_PER_CONTRACT = 0.65
SLICE = 10000.0
SPECS = {
 "aster_pead_long_a":      dict(book="OPT_PEAD_LONG_A", family="pead", structure="long", risk=0.02, dte=(21,35), delta=(0.5,0.65), hold=10, max_debit_width=0.6, max_premium_spot=0.04, exit_rule="fixed"),
 "aster_pead_long_b":      dict(book="OPT_PEAD_LONG_B", family="pead", structure="long", risk=0.005, dte=(21,35), delta=(0.5,0.65), hold=10, max_debit_width=0.45, max_premium_spot=0.02, exit_rule="fixed"),
 "aster_pead_vertical_a":  dict(book="OPT_PEAD_VERTICAL_A", family="pead", structure="vertical", risk=0.02, dte=(21,35), delta=(0.5,0.65), hold=10, max_debit_width=0.6, max_premium_spot=0.04, exit_rule="fixed"),
 "aster_pead_vertical_b":  dict(book="OPT_PEAD_VERTICAL_B", family="pead", structure="vertical", risk=0.005, dte=(21,35), delta=(0.5,0.65), hold=10, max_debit_width=0.45, max_premium_spot=0.02, exit_rule="fixed"),
 "aster_core_rsi2_long":   dict(book="OPT_QQQ95_RSI2_LONG", family="core_reserve", signal="RSI2", structure="long", risk=0.005, dte=(14,21), delta=(0.5,0.6), hold=5, max_debit_width=0.45, max_premium_spot=0.015, exit_rule="touch", core=True),
 "aster_core_rsi2_vertical": dict(book="OPT_QQQ95_RSI2_VERTICAL", family="core_reserve", signal="RSI2", structure="vertical", risk=0.005, dte=(14,21), delta=(0.5,0.6), hold=5, max_debit_width=0.45, max_premium_spot=0.015, exit_rule="touch", core=True),
 "aster_rec_rsi2_long_fixed_a": dict(book="OPT_RSI2_LONG_FIXED_A", family="recovery", signal="RSI2", structure="long", risk=0.02, dte=(14,21), delta=(0.5,0.6), hold=5, max_debit_width=0.6, max_premium_spot=0.025, exit_rule="fixed"),
 "aster_rec_rsi2_long_fixed_b": dict(book="OPT_RSI2_LONG_FIXED_B", family="recovery", signal="RSI2", structure="long", risk=0.005, dte=(14,21), delta=(0.5,0.6), hold=5, max_debit_width=0.45, max_premium_spot=0.015, exit_rule="fixed"),
 "aster_rec_rsi2_long_touch_a": dict(book="OPT_RSI2_LONG_TOUCH_A", family="recovery", signal="RSI2", structure="long", risk=0.02, dte=(14,21), delta=(0.5,0.6), hold=5, max_debit_width=0.6, max_premium_spot=0.025, exit_rule="touch"),
 "aster_rec_rsi2_long_touch_b": dict(book="OPT_RSI2_LONG_TOUCH_B", family="recovery", signal="RSI2", structure="long", risk=0.005, dte=(14,21), delta=(0.5,0.6), hold=5, max_debit_width=0.45, max_premium_spot=0.015, exit_rule="touch"),
}
INPUTS_COMMON = ("bars", "options", "positions")
PRODUCERS = ({"name": "bars", "outputs": ("bars",), "freshness_sla_s": 900},
             {"name": "options_chain", "outputs": ("options",), "freshness_sla_s": 900},
             {"name": "broker_readback", "outputs": ("positions",), "freshness_sla_s": 900})
PRODUCERS_PEAD = PRODUCERS + ({"name": "earnings_events", "outputs": ("earnings_events",), "freshness_sla_s": 86400},)

# --- ENH (Edge IMPROVE batch 10, 2026-10-24): mid-price limit execution.
# Binding leak: entries pay the full ask and exits take the full bid on
# 5-session recovery options (market orders, no price instruction) — the
# quoted spread is crossed twice on a short-horizon edge. Treatment:
# limit at the package mid. Switch: extra["enh_<sid>"] or
# extra["aster_b2_enh"] {"mid_limit": bool}, default ON; OFF restores
# the pre-change market order exactly. Shadow control = the ask/bid
# market price the pre-change rule would have crossed, recorded paired
# on the intent ("enhance_exp") and in extra["aster_enh_exp_journal"].
EXP_ID_B2 = "ENH-ASTERB2-MIDLIMIT-20261024"

def _enh_on(view, sid):
    ex = (view or {}).get("extra") or {}
    ov = ex.get(f"enh_{sid}") or ex.get("aster_b2_enh")
    if isinstance(ov, dict) and "mid_limit" in ov:
        return bool(ov["mid_limit"])
    return True

def _paired(view, rec):
    j = ((view or {}).get("extra") or {}).get("aster_enh_exp_journal")
    if isinstance(j, dict) and isinstance(j.get("records"), list):
        j["records"].append(rec)

def _mid(row):
    try:
        b = float(row.get("bid") or 0); a = float(row.get("ask") or 0)
    except Exception:
        return None
    return (b + a) / 2 if b > 0 and a >= b > 0 else None

def _rsi2(closes):
    if len(closes) < 3: return None
    ch = [float(b)-float(a) for a, b in zip(closes, closes[1:])]
    gain = sum(max(x, 0) for x in ch[:2])/2; loss = sum(max(-x, 0) for x in ch[:2])/2
    for x in ch[2:]:
        gain = (gain+max(x, 0))/2; loss = (loss+max(-x, 0))/2
    return 50.0 if gain == loss == 0 else 100.0 if loss == 0 else 100-100/(1+gain/loss)

def _quantile(xs, p):
    v = sorted(float(x) for x in xs); idx = (len(v)-1)*p; lo = int(idx)
    return v[lo]+(v[min(lo+1, len(v)-1)]-v[lo])*(idx-lo)

def _bars(view, sym):
    m = view.get("bars") or {}
    for k in (f"{sym}|1Day", f"{sym}|1D", sym):
        if m.get(k): return m[k]
    return []

def _sess(view, ctx):
    s = (ctx or {}).get("session") if isinstance(ctx, dict) else None
    return str(s or (view.get("now") or "2026-10-24"))[:10]

def _in_window(view, ctx):
    t = str((ctx or {}).get("now") or view.get("now") or "")
    if "T" not in t: return True
    try: hm = (int(t[11:13]), int(t[14:16]))
    except Exception: return True
    return (9, 35) <= hm < (9, 40)  # source entry window (non-opening_gamma)

def _contracts(view):
    """G4 batch-2 producer shape: view["options"] may be the fixture
    list of contract rows OR the live producer's per-underlying dict
    {UND: {"chains": {UND: [full rows]}, "quotes": {...}}} (the
    runtime-cache shape the base sleeves read). Normalize to rows."""
    raw = view.get("options") or []
    if isinstance(raw, list):
        return [c for c in raw if isinstance(c, dict)]
    if isinstance(raw, dict):
        out = []
        for payload in raw.values():
            if isinstance(payload, list):
                out.extend(c for c in payload if isinstance(c, dict))
            elif isinstance(payload, dict):
                chains = payload.get("chains") or {}
                if isinstance(chains, dict):
                    for rows in chains.values():
                        if isinstance(rows, list):
                            out.extend(c for c in rows if isinstance(c, dict))
                elif isinstance(chains, list):
                    out.extend(c for c in chains if isinstance(c, dict))
        return out
    return []

def _select(view, sym, right, spec, sess, spot):
    today = date.fromisoformat(sess); mid = sum(spec["delta"])/2; cands = []
    for c in _contracts(view):
        if c.get("underlying") != sym or c.get("right") != right: continue
        try: dte = (date.fromisoformat(str(c["expiry"])[:10])-today).days
        except Exception: continue
        d = abs(float(c.get("delta") or 0))
        if spec["dte"][0] <= dte <= spec["dte"][1] and spec["delta"][0] <= d <= spec["delta"][1]:
            cands.append(c)
    if not cands: return None
    long = min(cands, key=lambda x: (str(x["expiry"]), abs(abs(float(x["delta"]))-mid), abs(float(x["strike"])-spot), str(x["symbol"])))
    legs = [dict(long, ratio=1)]
    if spec["structure"] == "vertical":
        target = spot*(1.02 if right == "call" else 0.95); wings = []
        for x in _contracts(view):
            if x.get("underlying") != sym or x.get("right") != right or str(x.get("expiry"))[:10] != str(long["expiry"])[:10]: continue
            if (float(x["strike"]) > float(long["strike"])) == (right == "call") and float(x["strike"]) != float(long["strike"]): wings.append(x)
        if not wings: return None
        legs.append(dict(min(wings, key=lambda x: (abs(float(x["strike"])-target), str(x["symbol"]))), ratio=-1))
    return legs

# ENH edge-batch2 (2026-10-24): per-sleeve switch + paired shadow records.
# (helpers suffixed 2: batch-10's mid-limit ENH above owns _enh_on/_paired)
def _enh2_on(view, ctx, sid, key):
    for src in ((ctx or {}), (view or {}).get("extra") or {}):
        if isinstance(src, dict):
            ov = src.get(f"{sid}_enhance")
            if isinstance(ov, dict) and key in ov:
                return bool(ov[key])
    return True


def _paired2(view, ctx, rec):
    if isinstance(ctx, dict):
        ctx.setdefault("enhance_paired", []).append(rec)


def _entry(view, ctx, sid, spec, sym, right, spot, signal_id):
    legs = _select(view, sym, right, spec, _sess(view, ctx), spot)
    if not legs: return None
    debit_ps = sum(float(l["ask"]) if l["ratio"] > 0 else -float(l["bid"]) for l in legs) if spec["structure"] == "vertical" else float(legs[0]["ask"])
    if debit_ps <= 0: return None
    # ENH (core sleeves only): spread-blind selection pays the full ask on
    # wide-spread contracts via a market order. Refuse when the long leg's
    # spread exceeds 25% of its ask (pre-registered experiment threshold).
    if spec.get("core") and _enh2_on(view, ctx, sid, "spread_gate"):
        ask0, bid0 = float(legs[0]["ask"]), float(legs[0].get("bid") or 0)
        wide = ask0 > 0 and (ask0 - bid0) > 0.25 * ask0
        _paired2(view, ctx, {"exp_id": "ENH-EDGE-B2-" + sid, "sleeve": sid,
                            "control": "enter", "treatment": "refuse_wide_spread" if wide else "enter",
                            "ask": ask0, "bid": bid0, "enhance_switch": True})
        if wide: return None
    if spec["structure"] == "vertical":
        width = abs(float(legs[0]["strike"])-float(legs[1]["strike"]))
        if width <= 0 or debit_ps/width > spec["max_debit_width"]: return None
    elif (debit_ps*100)/(spot*100) > spec["max_premium_spot"]: return None
    per = debit_ps*100 + FEE_PER_CONTRACT*len(legs)
    qty = int((spec["risk"]*SLICE)//per)
    cap = min(int(l["ask_size"]) if l["ratio"] > 0 else int(l["bid_size"]) for l in legs)
    qty = min(qty, cap)
    if qty < 1: return None
    n = _entry.n = getattr(_entry, "n", 0)+1
    it = {"intent_id": f"{sid}-{signal_id}-{n}", "kind": "entry", "symbol": legs[0]["symbol"], "side": "buy",
            "qty": qty, "order_type": "market", "limit_price": None, "stop_price": None,
            "reason": f"{sid} entry: {spec['family']}_qualified_entry book={spec['book']} signal={signal_id} debit={debit_ps:.2f} risk_budget={spec['risk']*SLICE:.0f}",
            "time_in_force": "day", "position_intent": "buy_to_open", "price_hint": float(spot),
            "legs": [{"symbol": l["symbol"], "side": "buy" if l["ratio"] > 0 else "sell", "position_intent": "buy_to_open" if l["ratio"] > 0 else "sell_to_open", "ratio": l["ratio"], "strike": float(l["strike"]), "expiry": str(l["expiry"])[:10], "right": right} for l in legs],
            "entry_spot": float(spot), "exit_rule": spec["exit_rule"], "hold_sessions": spec["hold"]}
    if _enh_on(view, sid):
        mids = [_mid(l) for l in legs]
        if all(m is not None for m in mids):
            mid_ps = sum(m if l["ratio"] > 0 else -m
                         for m, l in zip(mids, legs))
            if mid_ps > 0:
                rec = {"exp_id": EXP_ID_B2, "sleeve": sid, "kind": "entry",
                       "switch_on": True, "control_price_ps": round(debit_ps, 4),
                       "treatment_limit_ps": round(mid_ps, 4),
                       "spread_saved_ps": round(debit_ps - mid_ps, 4)}
                it["order_type"] = "limit"
                it["limit_price"] = round(mid_ps, 2)
                it["enhance_exp"] = rec
                _paired(view, rec)
    return it

# --- ENH-B5-PEAD-CATCHUP (Edge pass batch 5, 2026-10-24) — SECOND
# look at the PEAD sleeves (first look: ENH-ASTERB2-MIDLIMIT above,
# entry pricing). Binding leak: PEAD entries exist on exactly ONE
# session (entry_session = event_date+3) inside a 5-minute window
# (09:35-09:40) at 300s cadence — one wedged/unfed cycle forfeits the
# whole 10-session drift the sleeve exists to capture. Treatment:
# on entry_session only, a PEAD sleeve may still enter the SAME
# qualified event later the same session (09:40-15:55); every other
# gate (surprise percentile, spot, dollar volume, contract, sizing,
# mid-limit) is unchanged. Switch: extra[f"enh_{sid}"] or
# extra["aster_b2_enh"] {"pead_catchup": bool}, default ON; OFF
# restores the window-only rule exactly. Shadow control = the
# window-only decision, paired on the entry intent + journal.
EXP_ID_PEAD = "ENH-B5-PEAD-CATCHUP-20261024"

def _pead_catchup_on(view, sid):
    ex = (view or {}).get("extra") or {}
    ov = ex.get(f"enh_{sid}") or ex.get("aster_b2_enh")
    if isinstance(ov, dict) and "pead_catchup" in ov:
        return bool(ov["pead_catchup"])
    return True

def _in_catchup_window(view, ctx):
    t = str((ctx or {}).get("now") or view.get("now") or "")
    if "T" not in t: return False
    try: hm = (int(t[11:13]), int(t[14:16]))
    except Exception: return False
    return (9, 40) <= hm < (15, 55)

def evaluate(sleeve_id, view, ctx=None):
    view = view or {}; ctx = ctx or {}; spec = SPECS[sleeve_id]; sess = _sess(view, ctx)
    positions = [p for p in (view.get("positions") or []) if float(p.get("qty") or 0) != 0]
    out = []
    # Exits first (source evaluates exits even when entries are blocked)
    for p in positions:
        legs = p.get("legs")
        if not legs: continue  # equity core leg: source has NO exit rule for it
        expiry = str(legs[0].get("expiry") or "")[:10]; held = p.get("sessions_held")
        if held is None:
            sym0 = legs[0].get("underlying"); b = _bars(view, sym0) if sym0 else []
            ed = str(p.get("opened_at") or p.get("entry_date") or "")[:10]
            held = sum(1 for x in b if str(x.get("t"))[:10] > ed) if ed else 0
        reason = None
        try:
            if expiry and (date.fromisoformat(expiry)-date.fromisoformat(sess)).days <= 1: reason = "pre_expiry_obligation_exit"
        except Exception: pass
        if not reason and int(held) >= spec["hold"]: reason = "planned_session_exit"
        if not reason and spec["exit_rule"] == "touch":
            sym0 = legs[0].get("underlying"); b = _bars(view, sym0) if sym0 else []
            spot = float(b[-1]["c"]) if b else float(p.get("entry_spot") or 0)
            if p.get("entry_spot") and spot >= float(p["entry_spot"])*1.02: reason = "touch_two_percent_recovery_exit"
        if reason:
            xit = {"intent_id": f"{sleeve_id}-exit-{p['symbol']}", "kind": "exit", "symbol": p["symbol"], "side": "sell",
                        "qty": int(abs(float(p["qty"]))), "order_type": "market", "limit_price": None, "stop_price": None,
                        "reason": f"{sleeve_id} exit: {reason} held={held}", "time_in_force": "day", "position_intent": "sell_to_close",
                        "price_hint": float(p.get("avg_price") or 0) or None,
                        "legs": [{"symbol": l["symbol"], "side": "sell" if l.get("ratio", 1) > 0 else "buy", "position_intent": "sell_to_close" if l.get("ratio", 1) > 0 else "buy_to_close", "ratio": l.get("ratio", 1)} for l in legs]}
            if _enh_on(view, sleeve_id):
                rows = {c.get("symbol"): c for c in _contracts(view)}
                mids, bids = [], []
                ok = True
                for l in legs:
                    r = rows.get(l.get("symbol"))
                    m = _mid(r) if r else None
                    if m is None:
                        ok = False; break
                    mids.append(m)
                    bids.append(float(r.get("bid") or 0)
                                if l.get("ratio", 1) > 0
                                else -float(r.get("ask") or 0))
                if ok:
                    mid_ps = sum(m if l.get("ratio", 1) > 0 else -m
                                 for m, l in zip(mids, legs))
                    if mid_ps > 0:
                        rec = {"exp_id": EXP_ID_B2, "sleeve": sleeve_id,
                               "kind": "exit", "switch_on": True,
                               "control_price_ps": round(sum(bids), 4),
                               "treatment_limit_ps": round(mid_ps, 4),
                               "spread_saved_ps": round(mid_ps - sum(bids), 4)}
                        xit["order_type"] = "limit"
                        xit["limit_price"] = round(mid_ps, 2)
                        xit["enhance_exp"] = rec
                        _paired(view, rec)
            out.append(xit)
    if out: return out
    if any(p.get("legs") for p in positions): return []  # one package per book (source)
    _catchup = False
    if not _in_window(view, ctx):
        if spec["family"] == "pead" and _pead_catchup_on(view, sleeve_id) \
                and _in_catchup_window(view, ctx):
            _catchup = True
        else:
            return []
    # Core leg first (source returns after core intent)
    if spec.get("core") and not any(p["symbol"] == "QQQ" and not p.get("legs") for p in positions):
        b = _bars(view, "QQQ")
        if not b: return []
        spot = float(b[-1]["c"]); qty = int((SLICE*0.95)/(spot*1.0015))
        if qty < 1: return []
        return [{"intent_id": f"{sleeve_id}-core-init", "kind": "entry", "symbol": "QQQ", "side": "buy", "qty": qty,
                 "order_type": "market", "limit_price": None, "stop_price": None,
                 "reason": f"{sleeve_id} entry: funded_95_percent_QQQ_core book={spec['book']} reserve=0.05",
                 "time_in_force": "day", "position_intent": "buy_to_open", "price_hint": spot}]
    if spec["family"] == "pead":
        for evv in sorted(view.get("earnings_events") or [], key=lambda x: (x.get("entry_session", ""), x.get("symbol", ""))):
            if evv.get("entry_session") != sess: continue
            thr = evv.get("threshold")
            if thr is None and evv.get("prior_surprises") is not None:
                if len(evv["prior_surprises"]) < 200: continue
                thr = _quantile(evv["prior_surprises"], 0.2)
            if thr is None: continue
            if float(evv["surprise"]) <= float(thr) and float(evv.get("spot_at_signal") or 0) >= 5 and float(evv.get("mean20_dollar_volume") or 0) >= 1000000:
                e = _entry(view, ctx, sleeve_id, spec, evv["symbol"], "put", float(evv["spot_at_signal"]), evv.get("event_id", "pead"))
                if e:
                    if _catchup:
                        rec = {"exp_id": EXP_ID_PEAD, "sleeve": sleeve_id,
                               "control_decision": "no_entry_window_missed",
                               "treatment_decision": "same_session_catchup_entry"}
                        e["reason"] += f" enh:{EXP_ID_PEAD} catchup_after_missed_window"
                        e["enhance_exp_catchup"] = rec
                        _paired(view, rec)
                    return [e]
        return []
    # recovery / core_reserve RSI2
    for sym in ("IWM", "QQQ", "SPY"):
        b = _bars(view, sym)
        if len(b) < 200: continue
        closes = [float(x["c"]) for x in b]
        sma = sum(closes[-200:])/200; r = _rsi2(closes)
        if r is not None and closes[-1] > sma and r < 10:
            e = _entry(view, ctx, sleeve_id, spec, sym, "call", closes[-1], f"{sym}:{sess}")
            if e: return [e]
    return []
