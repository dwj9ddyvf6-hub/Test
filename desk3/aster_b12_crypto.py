"""Aster R19 crypto engine — batch 12 (LINKUSDT breakout_base volume arm
+ negative_funding_squeeze x9).

Source-verified against the staged archive
(~/workspace/.scratch-ausar-archive/handoff-20261024):
source/backend/r19_crypto.py (_signal, evaluate) +
source/strategies/r19/crypto_rules.json. Shared bar/funding/now
primitives are imported from the batch-11 engine (one source of truth).

Faithful rules:
- Entry (both families): completed native 4h bar close > highest high of
  the prior 20 bars. negative_funding_squeeze additionally requires the
  latest actually-observed funding rate < 0 (archive known_funding:
  settled+received before the decision, <=12h old at the signal close;
  the v3 funding producer input carries the observed rate). Missing
  funding refuses NFS entry — never assumed.
- breakout_base is the price-only control: archive _signal passes
  funding=None for it, funding errors never gate it, and it declares no
  funding input.
- Sizing: fullcash = slice cash / (price x (1+10bp fee)) in the archive;
  the desk's established v3 translation (batches 6/11) is cash net of
  fee, cash*(1-0.001)/price — used here for cross-batch consistency.
  volume1pct = min(fullcash, 1% of the preceding 4h bar's volume in base
  units) (archive: volume of the entry interval following the signal;
  snapshot translation uses the bar preceding the signal bar, batches
  6/11 reading).
- Exits: fixed16/fixed96 sell at/after the 16h/96h deadline from entry.
  Structural arms (lost_breakout, normalization,
  normalization_failure) carry the archive's installed deadline:
  exit_due = entry_due + 96h for every non-fixed16 policy (archive
  candidate construction), which fires even when bars/funding are
  missing (owned deadlines survive missing inputs).
  Structural triggers, on completed bars after entry (archive):
  lost_breakout = close < the position's stored breakout level;
  normalization = observed funding >= 0; normalization_failure =
  funding >= 0 AND close < lowest low of the prior 3 bars. A structural
  exit is executable no earlier than 4h after the trigger bar closes
  (archive execute_at = max(bar close + 4h, bar availability, funding
  receipt)); the runtime form evaluates the latest completed bar, whose
  close is its t + 4h, so execution requires now >= t + 8h.
- Funding is a declared producer input: no v3 funding producer is wired
  yet, so the NFS sleeves land visibly UNFED, never fake-fed.
"""
from __future__ import annotations
from datetime import timedelta
from desk3.contract import Intent
from desk3.aster_b11_crypto import _bars, _funding, _now, _ts, _breakout, _stale_blocked

FEE = 0.001
P = "aster_r19_linkusdt_"
SPECS = {
 P + "breakout_base_fixed16_volume1pct": dict(sym="LINKUSDT", fam="breakout_base", exit="fixed16", cap="volume1pct", hold_h=16),
 P + "negative_funding_squeeze_fixed16_fullcash": dict(sym="LINKUSDT", fam="nfs", exit="fixed16", cap="fullcash", hold_h=16),
 P + "negative_funding_squeeze_fixed16_volume1pct": dict(sym="LINKUSDT", fam="nfs", exit="fixed16", cap="volume1pct", hold_h=16),
 P + "negative_funding_squeeze_fixed96_fullcash": dict(sym="LINKUSDT", fam="nfs", exit="fixed96", cap="fullcash", hold_h=96),
 P + "negative_funding_squeeze_fixed96_volume1pct": dict(sym="LINKUSDT", fam="nfs", exit="fixed96", cap="volume1pct", hold_h=96),
 P + "negative_funding_squeeze_lost_breakout_fullcash": dict(sym="LINKUSDT", fam="nfs", exit="lost_breakout", cap="fullcash", hold_h=96),
 P + "negative_funding_squeeze_lost_breakout_volume1pct": dict(sym="LINKUSDT", fam="nfs", exit="lost_breakout", cap="volume1pct", hold_h=96),
 P + "negative_funding_squeeze_normalization_failure_fullcash": dict(sym="LINKUSDT", fam="nfs", exit="normalization_failure", cap="fullcash", hold_h=96),
 P + "negative_funding_squeeze_normalization_failure_volume1pct": dict(sym="LINKUSDT", fam="nfs", exit="normalization_failure", cap="volume1pct", hold_h=96),
 P + "negative_funding_squeeze_normalization_fullcash": dict(sym="LINKUSDT", fam="nfs", exit="normalization", cap="fullcash", hold_h=96),
}
INPUTS = ("bars", "funding", "positions")
INPUTS_BREAKOUT = ("bars", "positions")


def _trigger_executable(brs, now):
    """Latest bar t is its open; it closes at t+4h and a structural exit
    executes no earlier than close+4h (archive execute_at)."""
    if not brs:
        return False
    t = _ts(brs[-1].get("t"))
    return t is not None and now >= t + timedelta(hours=8)


# --- EDGE BATCH 9 enhancement: latched structural-trigger scan ---------
# Binding leak: the pre-change rule evaluated the structural trigger
# ONLY on the latest bar and only once that bar itself was executable
# (t+8h). A trigger on an earlier, already-executable bar was therefore
# (a) blocked during the 4h dead zone after the latest bar closes and
# (b) replaced/evaporated if the latest bar recovered. The squeeze had
# already failed; the sleeve rode it to the 96h deadline. Cure (switch
# enhance_trigger_latch, default ON): scan EVERY post-entry bar whose
# execute_at (t+8h) has arrived. OFF restores latest-bar-only exactly.
def _enh_on(sid, view, ctx):
    for src in ((ctx or {}), (view or {}).get("params") or {},
                (view or {}).get("extra") or {}):
        if isinstance(src, dict):
            sub = src.get(sid) if isinstance(src.get(sid), dict) else src
            if "enhance_trigger_latch" in sub:
                return bool(sub["enhance_trigger_latch"])
    return True


def _executable_bars(brs, now, opened=None):
    out = []
    for j, b in enumerate(brs):
        t = _ts(b.get("t"))
        if t is None or now < t + timedelta(hours=8):
            continue
        if opened is not None and t + timedelta(hours=4) <= opened:
            continue
        out.append(j)
    return out


def _shadow_journal(ctx, sid, rec):
    sd = (ctx or {}).get("state_dir") if isinstance(ctx, dict) else None
    if not sd:
        return
    try:
        import json as _j, os as _o
        _o.makedirs(sd, exist_ok=True)
        with open(_o.path.join(sd, "enhance_journal.jsonl"), "a") as fh:
            fh.write(_j.dumps({"sleeve": sid, **rec}, sort_keys=True) + "\n")
    except Exception:
        pass


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
        reason = None
        if held >= spec["hold_h"]:
            reason = f"aster_deadline_{spec['exit']}_{spec['hold_h']}h held={held:.1f}h"
        elif spec["exit"] == "lost_breakout" and brs and _trigger_executable(brs, now):
            lvl = p.get("breakout_level") or p.get("entry_breakout_level")
            if lvl is not None and float(brs[-1]["c"]) < float(lvl):
                reason = f"aster_lost_breakout close={brs[-1]['c']} level={lvl}"
        elif spec["exit"] == "normalization" and fund is not None and fund >= 0 \
                and _trigger_executable(brs, now):
            reason = f"aster_funding_normalized rate={fund}"
        elif spec["exit"] == "normalization_failure" and fund is not None and fund >= 0 \
                and len(brs) >= 4 and (_trigger_executable(brs, now)
                                       or _enh_on(sid, view, ctx)):
            if _trigger_executable(brs, now) and float(brs[-1]["c"]) < min(
                    float(b["l"]) for b in brs[-4:-1]):
                reason = "aster_normalization_failure"
            elif _enh_on(sid, view, ctx):
                for j in _executable_bars(brs, now, opened):
                    if j >= 3 and float(brs[j]["c"]) < min(
                            float(b["l"]) for b in brs[j - 3:j]):
                        reason = "aster_normalization_failure latched_trigger_scan"
                        _shadow_journal(ctx, sid, {"event": "enhance_exit",
                            "enhanced": reason,
                            "shadow": "no_exit_trigger_evaporated_on_latest_bar",
                            "ts": now.isoformat()})
                        break
        if reason:
            px = float(brs[-1]["c"]) if brs else float(p.get("avg_price") or 0)
            out.append(Intent(kind="exit", symbol=sym, qty=qty, price_hint=px or None,
                reason=f"{sid} exit: {reason}", side="sell", position_intent="sell_to_close"))
    if out or poss:
        return out
    if not _breakout(brs):
        return []
    if spec["fam"] == "nfs" and (fund is None or fund >= 0):
        return []
    if _stale_blocked(view, sid, brs, now):  # ENH-B8 stale-signal gate (see aster_b11_crypto)
        return []
    price = float(brs[-1]["c"]); cash = float((view.get("slice") or {}).get("cash_usd") or 10000.0)
    qty = cash * (1 - FEE) / price
    if spec["cap"] == "volume1pct":
        qty = min(qty, 0.01 * float(brs[-2]["v"]))
    if qty <= 0:
        return []
    return [Intent(kind="enter", symbol=sym, qty=round(qty, 8), price_hint=price,
        reason=f"{sid} entry: {spec['fam']} breakout close={price} funding={fund} cap={spec['cap']}",
        side="buy", position_intent="buy_to_open")]
