"""Aster batch 7 engine — R19 crypto ENJUSDT (books 66-75).

Faithful port of archive source/backend/r19_crypto.py + strategies/
absorption/signals.py + strategies/r19/crypto_rules.json (read directly
from the staged archive at ~/workspace/.scratch-ausar-archive).

Rules (source):
- absorption (signals.py advance): shock bar = volume > 2*EMA20(volume,
  current-inclusive), close < open, close < EMA50(close, incl.);
  confirmation = immediately following bar close > open and close >
  (shock high + shock low)/2. Source _signal requires the row's
  confirmed_absorption flag with indicator_count >= 300.
- breakout: completed 4h close > highest high of the prior 20 bars.
- funding filters (source _signal): negative_funding families require
  an observed funding rate < 0; absorption_nonnegative_funding requires
  >= 0; breakout_base / absorption_base are funding-off controls (a
  funding outage cannot veto them). Missing funding is never assumed 0.
- exit: fixed deadline only for this batch — exit_due = entry + 16h
  (fixed16) or + 96h (fixed96); the deadline survives missing bars /
  funding (source: owned fixed deadlines checked before bar validation).
- sizing: fullcash = slice cash / (ask * (1 + 10bp fee)); volume1pct
  additionally caps qty at 1% of the preceding 4h bar's volume.

Runtime translation (v3 sleeve layer, cf. batch 6): the source's 4h
entry delay, 300s entry window, and observed-quote/depth clocks are
producer/dispatcher-layer mechanics; the sleeve evaluates the latest
completed-bar signal on the snapshot it is given and sizes off the
signal close. Funding is a declared producer input: funding-filtered
sleeves are UNFED without it, never fake-fed. See FIDELITY-LEDGER
ASTER-B7.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from desk3.contract import Intent

FEE = 0.001

# --- ENH 2026-10-24 (Edge IMPROVE batch 7, §2a decision record in
# proof/enhance/<sleeve>.json) -------------------------------------------
# BINDING LEAK: stale-signal entry — no entry window at all. The source
# design entered inside a 300s window after its entry delay; the v3
# translation dropped that window to a producer/dispatcher layer that
# never enforces it, so the sleeve enters on the latest completed 4h
# bar's signal at ANY age (a full 4h cycle window, or indefinitely on
# a stale snapshot after an outage/restart), sized full-cash/
# volume-capped off that bar's stale close, into a fixed 16h/96h hold.
# ONE conceptual change: entries fire only while the signal bar's
# close is fresh — age in [0, ENTRY_WINDOW_S]. ENTRY_WINDOW_S = 900s is
# the sleeves' own declared producer freshness SLA (PRODUCERS below),
# at the 300s cadence = the first 3 cycles after the bar closes.
# Switch: view["extra"]["aster_r19_improve"][<sid>]["signal_window"],
# default ON; OFF restores the pre-change rule exactly (enter at any
# signal age). The pre-change rule is the shadow control: on every
# signal that reaches the gate, a paired record
# {exp_id, sleeve, signal_age_s, control, treatment} is appended to
# view["extra"]["aster_r19_exp_journal"]["records"] when served; the
# control never emits. Exits are never gated (deadlines unchanged).
EXP_ID_B7 = "ENH-ASTER-R19-B7-20261024"
ENTRY_WINDOW_S = 900.0
BAR_H = 4.0


def _enh_enabled(view, sid):
    ov = (view.get("extra") or {}).get("aster_r19_improve")
    if isinstance(ov, dict):
        per = ov.get(sid)
        if isinstance(per, dict) and "signal_window" in per:
            return bool(per["signal_window"])
        if "signal_window" in ov:
            return bool(ov["signal_window"])
    return True


def _paired(view, record):
    j = (view.get("extra") or {}).get("aster_r19_exp_journal")
    if isinstance(j, dict) and isinstance(j.get("records"), list):
        j["records"].append(record)


def _signal_age_s(brs, now):
    """Age (s) of the signal bar's CLOSE: bar 't' is the bar OPEN
    (fixture + Alpaca convention), so close = t + 4h. None when the
    bar carries no parseable stamp — treatment fails closed."""
    if not brs:
        return None
    t = _ts(brs[-1].get("t"))
    if t is None:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return (now - (t + timedelta(hours=BAR_H))).total_seconds()
_P = "aster_r19_enjusdt_"
SPECS = {
 _P+"absorption_base_fixed16_volume1pct": dict(sym="ENJUSDT", fam="absorption_base", exit="fixed16", cap="volume1pct", hold_h=16),
 _P+"absorption_negative_funding_fixed16_fullcash": dict(sym="ENJUSDT", fam="absorption_negative_funding", exit="fixed16", cap="fullcash", hold_h=16),
 _P+"absorption_negative_funding_fixed16_volume1pct": dict(sym="ENJUSDT", fam="absorption_negative_funding", exit="fixed16", cap="volume1pct", hold_h=16),
 _P+"absorption_nonnegative_funding_fixed16_fullcash": dict(sym="ENJUSDT", fam="absorption_nonnegative_funding", exit="fixed16", cap="fullcash", hold_h=16),
 _P+"absorption_nonnegative_funding_fixed16_volume1pct": dict(sym="ENJUSDT", fam="absorption_nonnegative_funding", exit="fixed16", cap="volume1pct", hold_h=16),
 _P+"breakout_base_fixed16_fullcash": dict(sym="ENJUSDT", fam="breakout_base", exit="fixed16", cap="fullcash", hold_h=16),
 _P+"breakout_base_fixed16_volume1pct": dict(sym="ENJUSDT", fam="breakout_base", exit="fixed16", cap="volume1pct", hold_h=16),
 _P+"negative_funding_squeeze_fixed16_fullcash": dict(sym="ENJUSDT", fam="negative_funding_squeeze", exit="fixed16", cap="fullcash", hold_h=16),
 _P+"negative_funding_squeeze_fixed16_volume1pct": dict(sym="ENJUSDT", fam="negative_funding_squeeze", exit="fixed16", cap="volume1pct", hold_h=16),
 _P+"negative_funding_squeeze_fixed96_fullcash": dict(sym="ENJUSDT", fam="negative_funding_squeeze", exit="fixed96", cap="fullcash", hold_h=96),
}
FUNDING_FAMS = {"absorption_negative_funding", "absorption_nonnegative_funding",
                "negative_funding_squeeze"}
PRODUCERS = ({"name": "bars", "outputs": ("bars",), "freshness_sla_s": 900},
             {"name": "funding", "outputs": ("funding",), "freshness_sla_s": 900},
             {"name": "broker_readback", "outputs": ("positions",), "freshness_sla_s": 900})


def inputs_for(sid):
    if SPECS[sid]["fam"] in FUNDING_FAMS:
        return ("bars", "funding", "positions")
    return ("bars", "positions")


def _bars(view, sym):
    m = view.get("bars") or {}
    for k in (f"{sym}|4Hour", f"{sym}|4h", f"{sym}|240min", sym):
        if m.get(k):
            return sorted(m[k], key=lambda r: str(r.get("t")))
    return []


def _funding(view, sym):
    f = view.get("funding")
    if isinstance(f, dict):
        v = f.get(sym)
        if isinstance(v, dict):
            v = v.get("rate")
        if v is not None:
            return float(v)
    e = view.get("extra") or {}
    if e.get("funding_rate") is not None:
        return float(e["funding_rate"])
    return None


def _now(view, ctx):
    n = view.get("now") or (ctx or {}).get("now") or "2026-10-24T00:00:00+00:00"
    d = n if isinstance(n, datetime) else datetime.fromisoformat(str(n).replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _ts(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def _ema(vals, n):
    k = 2 / (n + 1)
    out = []
    for i, v in enumerate(vals):
        out.append(v if i == 0 else v * k + out[-1] * (1 - k))
    return out


def _absorption(brs):
    """signals.py advance(): shock at brs[-2], confirmation at brs[-1],
    indicators seeded over >= 300 completed bars."""
    if len(brs) < 300:
        return False
    vols = [float(b["v"]) for b in brs]
    closes = [float(b["c"]) for b in brs]
    ev = _ema(vols, 20)
    ec = _ema(closes, 50)
    s, c = brs[-2], brs[-1]
    shock = (float(s["v"]) > 2 * ev[-2] and float(s["c"]) < float(s["o"])
             and float(s["c"]) < ec[-2])
    mid = (float(s["h"]) + float(s["l"])) / 2
    return shock and float(c["c"]) > float(c["o"]) and float(c["c"]) > mid


def _breakout(brs):
    return len(brs) >= 21 and float(brs[-1]["c"]) > max(float(b["h"]) for b in brs[-21:-1])


def evaluate(sid, view, ctx=None):
    view = view or {}
    spec = SPECS[sid]
    sym = spec["sym"]
    now = _now(view, ctx)
    brs = _bars(view, sym)
    fund = _funding(view, sym)
    poss = [p for p in (view.get("positions") or [])
            if p.get("symbol", sym) == sym and float(p.get("qty") or 0) != 0]
    out = []
    for p in poss:
        qty = abs(float(p["qty"]))
        opened = _ts(p.get("opened_at") or p.get("entry_time") or "")
        held = ((now - opened).total_seconds() / 3600 if opened
                else float(p.get("age_hours") or 0))
        if held >= spec["hold_h"]:
            out.append(Intent(
                kind="exit", symbol=sym, qty=qty,
                price_hint=float(brs[-1]["c"]) if brs else None,
                reason=f"{sid} exit: aster_deadline_{spec['exit']}_{spec['hold_h']}h held={held:.1f}h",
                side="sell", position_intent="sell_to_close"))
    if out or poss:
        return out
    fam = spec["fam"]
    if fam in ("breakout_base", "negative_funding_squeeze"):
        if not _breakout(brs):
            return []
    else:
        if not _absorption(brs):
            return []
    if fam in ("absorption_negative_funding", "negative_funding_squeeze"):
        if fund is None or fund >= 0:
            return []
    elif fam == "absorption_nonnegative_funding":
        if fund is None or fund < 0:
            return []
    # ENH gate (see header): shadow control = pre-change rule (enter at
    # any age); treatment = enter only inside the freshness window.
    age = _signal_age_s(brs, now)
    fresh = age is not None and 0.0 <= age <= ENTRY_WINDOW_S
    _paired(view, {"exp_id": EXP_ID_B7, "sleeve": sid,
                   "signal_age_s": age, "control": "enter",
                   "treatment": "enter" if fresh else "refused_stale_signal",
                   "switch": "on" if _enh_enabled(view, sid) else "off"})
    if _enh_enabled(view, sid) and not fresh:
        return []
    price = float(brs[-1]["c"])
    cash = float((view.get("slice") or {}).get("cash_usd") or 10000.0)
    qty = cash / (price * (1 + FEE))
    if spec["cap"] == "volume1pct":
        qty = min(qty, 0.01 * float(brs[-2]["v"]))
    if qty <= 0:
        return []
    return [Intent(kind="enter", symbol=sym, qty=round(qty, 8), price_hint=price,
                   reason=f"{sid} entry: {fam} close={price} funding={fund} cap={spec['cap']}",
                   side="buy", position_intent="buy_to_open")]


def config_rows():
    rows = []
    for sid, spec in SPECS.items():
        rows.append({
            "id": sid, "module": f"adapters3.{sid}", "cadence_s": 300,
            "session": "always",
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "bp_buffer_frac": 0.02, "flat_by_close": False,
            "flatten_time_et": None,
            "params": {"family": spec["fam"], "exit_policy": spec["exit"],
                       "capacity": spec["cap"], "symbol": spec["sym"],
                       "fee_bps": 10},
            "inputs": list(inputs_for(sid)), "parked": False,
        })
    return rows
