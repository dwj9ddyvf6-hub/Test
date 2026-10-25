"""Aster R19 crypto engine — batch 11 (LINKUSDT fixed16 arms).

Source-verified against the staged archive (found at
~/workspace/.scratch-ausar-archive/handoff-20261024 on this box):
source/backend/r19_crypto.py (_signal, evaluate), source/strategies/
absorption/signals.py (advance), source/strategies/r19/crypto_rules.json.

Faithful rules:
- Absorption (absorption_base / *_funding variants): the PRIOR completed
  4h bar is a bear shock — volume > 2*EMA20(volume, inclusive), close <
  open, close < EMA50(close, inclusive) — and the CURRENT bar confirms:
  close > open and close > (shock high+low)/2; requires >=300 completed
  bars of indicator warmup (archive indicator_count >= 300).
- absorption_negative_funding: additionally the latest actually-observed
  funding rate < 0. absorption_nonnegative_funding: funding >= 0.
  absorption_base is the funding-OFF control: funding never gates it
  (archive _signal passes funding=None for breakout_base/absorption_base).
- breakout_base: price-only control — close > highest high of prior 20
  bars; funding never gates it.
- Exit (all batch-11 arms): fixed16 — sell at/after the 16h deadline
  from entry; the deadline fires even when bars/funding are missing
  (archive: owned fixed deadlines survive missing inputs).
- Sizing: fullcash = slice cash net of the 10bp/side fee; volume1pct =
  min(fullcash, 1% of the preceding 4h bar's volume) (archive capacity
  arm volume1pct, prior entry interval volume — v3 snapshot translation
  uses the bar preceding the signal bar, same reading as batch 6).
- Funding is a declared producer input: absent funding => funding-gated
  sleeves refuse entry and land UNFED in the registry, never fake-fed.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from desk3.contract import Intent

# --- EDGE PASS batch 8 (ENH-B8): stale-signal entry gate -----------------
# Binding leak (measured 2026-10-24, /tmp measure + proof/enhance/*.json):
# entry fired on the latest snapshot bar regardless of its age — a signal
# bar that closed 12h earlier (3 unseen 4h bars) still entered 12/12
# sleeves at the stale close. Enhancement: with the per-sleeve switch ON
# (default), an entry is refused when the signal bar closed more than one
# bar interval (4h) before now — at least one newer completed bar exists
# that the snapshot never showed, so the confirmation/breakout and the
# price_hint are unverifiable. OFF (extra["aster_edge"][sid]
# ["stale_signal_gate"]=False) restores the pre-change rule exactly.
# Exits are untouched: owned deadlines survive stale/missing bars.
# Shadow control: the faithful rule is evaluated on the same opportunity;
# when a caller supplies extra["aster_edge_journal"] (a list), a paired
# record {sleeve, enhanced, shadow_faithful, signal_age_h} is appended —
# the shadow arm never emits an Intent.
STALE_GATE_MAX_AGE_H = 4.0


def _edge_on(view, sid):
    cfg = ((view.get("extra") or {}).get("aster_edge") or {}).get(sid) or {}
    return cfg.get("stale_signal_gate", True) is not False


def _signal_age_h(brs, now):
    if not brs:
        return None
    t = _ts(brs[-1].get("t"))
    if t is None:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return (now - (t + timedelta(hours=4))).total_seconds() / 3600.0


def _edge_record(view, sid, enhanced, shadow, age_h):
    j = (view.get("extra") or {}).get("aster_edge_journal")
    if isinstance(j, list):
        j.append({"sleeve": sid, "enhanced": enhanced,
                  "shadow_faithful": shadow,
                  "signal_age_h": None if age_h is None else round(age_h, 3)})


def _stale_blocked(view, sid, brs, now):
    """True when the ENH-B8 gate refuses this entry opportunity."""
    age = _signal_age_h(brs, now)
    if not _edge_on(view, sid):
        return False
    if age is None or age <= STALE_GATE_MAX_AGE_H:
        _edge_record(view, sid, "enter", "enter", age)
        return False
    _edge_record(view, sid, "refuse_stale_signal", "enter", age)
    return True

FEE = 0.001
P = "aster_r19_linkusdt_"
SPECS = {
 P+"absorption_base_fixed16_fullcash": dict(sym="LINKUSDT", fam="absorption_base", cap="fullcash", hold_h=16),
 P+"absorption_base_fixed16_volume1pct": dict(sym="LINKUSDT", fam="absorption_base", cap="volume1pct", hold_h=16),
 P+"absorption_negative_funding_fixed16_fullcash": dict(sym="LINKUSDT", fam="absorption_negative_funding", cap="fullcash", hold_h=16),
 P+"absorption_negative_funding_fixed16_volume1pct": dict(sym="LINKUSDT", fam="absorption_negative_funding", cap="volume1pct", hold_h=16),
 P+"absorption_nonnegative_funding_fixed16_fullcash": dict(sym="LINKUSDT", fam="absorption_nonnegative_funding", cap="fullcash", hold_h=16),
 P+"absorption_nonnegative_funding_fixed16_volume1pct": dict(sym="LINKUSDT", fam="absorption_nonnegative_funding", cap="volume1pct", hold_h=16),
 P+"breakout_base_fixed16_fullcash": dict(sym="LINKUSDT", fam="breakout_base", cap="fullcash", hold_h=16),
}
INPUTS = ("bars", "funding", "positions")

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
    k = 2 / (n + 1); out = []
    for i, v in enumerate(vals):
        out.append(v if i == 0 else v * k + out[-1] * (1 - k))
    return out

def _absorption(brs):
    if len(brs) < 300:
        return False
    vols = [float(b["v"]) for b in brs]; closes = [float(b["c"]) for b in brs]
    ev = _ema(vols, 20); ec = _ema(closes, 50); s = brs[-2]; c = brs[-1]
    shock = float(s["v"]) > 2 * ev[-2] and float(s["c"]) < float(s["o"]) and float(s["c"]) < ec[-2]
    mid = (float(s["h"]) + float(s["l"])) / 2
    return shock and float(c["c"]) > float(c["o"]) and float(c["c"]) > mid

def _breakout(brs):
    return len(brs) >= 21 and float(brs[-1]["c"]) > max(float(b["h"]) for b in brs[-21:-1])

def evaluate(sid, view, ctx=None):
    view = view or {}; spec = SPECS[sid]; sym = spec["sym"]; now = _now(view, ctx)
    brs = _bars(view, sym); fund = _funding(view, sym)
    poss = [p for p in (view.get("positions") or []) if float(p.get("qty") or 0) != 0]
    out = []
    for p in poss:
        if p.get("symbol") not in (sym, None) and sym not in str(p.get("symbol")):
            continue
        qty = abs(float(p["qty"])); opened = _ts(p.get("opened_at") or p.get("entry_time") or "")
        held = (now - opened).total_seconds() / 3600 if opened else float(p.get("age_hours") or 0)
        if held >= spec["hold_h"]:
            px = float(brs[-1]["c"]) if brs else float(p.get("avg_price") or 0)
            out.append(Intent(kind="exit", symbol=sym, qty=qty, price_hint=px or None,
                reason=f"{sid} exit: aster_deadline_fixed16 held={held:.1f}h",
                side="sell", position_intent="sell_to_close"))
    if out or poss:
        return out
    fam = spec["fam"]
    if fam == "breakout_base":
        if not _breakout(brs):
            return []
    else:
        if not _absorption(brs):
            return []
        if fam == "absorption_negative_funding" and (fund is None or fund >= 0):
            return []
        if fam == "absorption_nonnegative_funding" and (fund is None or fund < 0):
            return []
    if _stale_blocked(view, sid, brs, now):
        return []
    price = float(brs[-1]["c"]); cash = float((view.get("slice") or {}).get("cash_usd") or 10000.0)
    qty = cash * (1 - FEE) / price
    if spec["cap"] == "volume1pct":
        qty = min(qty, 0.01 * float(brs[-2]["v"]))
    if qty <= 0:
        return []
    return [Intent(kind="enter", symbol=sym, qty=round(qty, 8), price_hint=price,
        reason=f"{sid} entry: {fam} close={price} funding={fund} cap={spec['cap']}",
        side="buy", position_intent="buy_to_open")]
