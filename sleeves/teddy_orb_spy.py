"""teddy_orb_spy sleeve - TEDDY-ORB-SPY-SPEC-2026-10-28 (FROZEN).

Provenance: X post by @ThiccTeddy, strategy from his posted video,
installed by owner order 2026-10-28. Edge status: UNPROVEN; the live
paper record is the test and no backtest is claimed.

SPY opening-range breakout with volume, exactly per the frozen spec:

  * Opening range: the first six 5-minute RTH bars (09:30-10:00 ET);
    OR high / OR low are fixed at 10:00 ET and never repaint.
  * Data route: the desk serves no native bars:SPY:5Min producer key,
    so the pure core aggregates the proven SPY 1-minute Alpaca SIP
    bars into 5-minute bars deterministically: buckets anchored at
    09:30 ET, o=first, h=max, l=min, c=last, v=sum, and a bucket is
    emitted ONLY when all 5 constituent minutes are present (an
    incomplete trailing bucket is dropped: causal, no repaint).
  * Breakout qualification (no entry yet): a 5-min bar closes above
    OR high (long) or below OR low (short) with volume at least 1.5x
    the mean volume of the six opening-range bars. A close through
    the range without that volume does NOT qualify. The breakout
    must occur by 12:00 ET.
  * Pullback and entry: after a qualified breakout, a pullback of 1
    to 6 bars retraces toward the broken edge (a counter-move close
    versus the prior bar) WITHOUT any bar closing back inside the
    range, and with every pullback bar's volume below the breakout
    bar's volume (a pullback bar at/above the breakout volume kills
    the setup: that pullback is not the lower-volume pullback the
    rule requires). Entry trigger: the first bar after the pullback
    that closes beyond the pullback's extreme in the breakout
    direction (above the pullback high for longs, below the pullback
    low for shorts) with volume greater than the last pullback bar.
    If no entry triggers within the 6-bar pullback window plus 6
    further bars (12 bars after the breakout bar), the setup expires.
  * Invalidation: any 5-min close back inside the opening range
    after the breakout, before entry, kills the setup for that
    direction for the session; after entry it exits the trade (the
    intent emitted on that bar's close fills at the next bar open,
    per desk convention).
  * Stop: just beyond the broken edge, inside the range (longs OR
    high - 0.10; shorts OR low + 0.10). Target: the measured move
    (OR height projected from the broken edge) or 2R from entry,
    whichever is closer.
  * One open position at a time; one qualified breakout per
    direction per day (an invalidated, expired, or completed
    direction is dead for the session; the opposite direction may
    still qualify once); no entries after 12:30 ET; hard flat
    14:00 ET (the sleeve's own rule - config flat_by_close stays
    false so no second flatten path exists).

Sizing (spec names stop/target math but NO sizing formula; the
choice is stated here and in TEDDY-ORB-SPY-BUILD.md + the install
proof): unit risk 0.25% of slice equity per trade with a 25%
notional cap, the trullas_divergence / grok_sr_spy install norm.

Data law: intraday bars are Alpaca SIP (enforced by the desk warm /
adapter path; volume signals on intraday bars use SIP only).

State (open-trade plan, dead directions) is carried in
ctx.extra["teddy_state"] and round-tripped by the adapter, which
persists it beside the sleeve journal. The day's setup sequence is
recomputed deterministically each cycle from today's completed
5-minute bars only, so no setup state needs to persist: only the
open-trade plan and dead directions do.
"""
from __future__ import annotations

import math
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")

SYMBOL = "SPY"
OR_BARS = 6
BREAKOUT_VOL_MULT = 1.5
STOP_INSIDE = 0.10
TARGET_R_MULT = 2.0
MAX_PULLBACK_BARS = 6
DRIFT_BARS = 6
ENTRY_CUTOFF = dtime(12, 30)
BREAKOUT_CUTOFF = dtime(12, 0)
FLAT_TIME = dtime(14, 0)
UNIT_RISK_PCT = 0.0025
NOTIONAL_CAP_PCT = 0.25

CONFIG = SleeveConfig(
    sleeve_id="teddy_orb_spy",
    cadence_s=60,
    universe=(SYMBOL,),
    state_schema={"teddy_state": "dict", "position": "dict|None"},
    risk_pct=UNIT_RISK_PCT,
    parked=False,
)


# ------------------------------------------------------------------ utils
def _number(v):
    if isinstance(v, bool):
        return None
    try:
        out = float(v)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def _epoch(v):
    n = _number(v)
    if n is not None:
        return n / 1000.0 if n > 1.0e12 else n
    if not isinstance(v, str):
        return None
    try:
        p = datetime.fromisoformat(v.replace("Z", "+00:00"))
        from datetime import timezone
        if p.tzinfo is None:
            p = p.replace(tzinfo=timezone.utc)
        return p.timestamp()
    except (TypeError, ValueError, OverflowError):
        return None


def _rth_bars_1min(raw, session):
    """Current-session RTH 1-minute bars only, sorted and deduped."""
    out = []
    for row in raw or []:
        if not isinstance(row, dict):
            continue
        t = _epoch(row.get("t"))
        o, h, l, c = (_number(row.get(k)) for k in ("o", "h", "l", "c"))
        v = _number(row.get("v")) or 0.0
        if None in (t, o, h, l, c) or min(o, h, l, c) <= 0 or h < l:
            continue
        dt = datetime.fromtimestamp(t, tz=ET)
        if dt.date().isoformat() != session:
            continue
        if dt.time() < dtime(9, 30) or dt.time() >= dtime(16, 0):
            continue
        if v <= 0:
            continue
        out.append({"t": t, "o": o, "h": h, "l": l, "c": c, "v": v})
    out.sort(key=lambda b: b["t"])
    deduped = []
    for b in out:
        if deduped and b["t"] == deduped[-1]["t"]:
            deduped[-1] = b
        else:
            deduped.append(b)
    return deduped


def aggregate_5min(bars_1min):
    """Deterministically aggregate RTH 1-minute bars into 5-minute
    bars: buckets anchored at 09:30 ET (bucket start = 09:30 + 5k
    minutes), o=first, h=max, l=min, c=last, v=sum. A bucket is
    emitted ONLY when all 5 constituent minutes are present, so the
    trailing forming bucket never appears and never repaints."""
    buckets = {}
    for b in bars_1min or []:
        dt = datetime.fromtimestamp(b["t"], tz=ET)
        minutes = (dt.hour * 60 + dt.minute) - (9 * 60 + 30)
        if minutes < 0:
            continue
        start = minutes // 5
        buckets.setdefault(start, []).append(b)
    out = []
    for start in sorted(buckets):
        rows = buckets[start]
        if len(rows) != 5:
            continue
        rows = sorted(rows, key=lambda b: b["t"])
        out.append({
            "t": rows[0]["t"], "o": rows[0]["o"],
            "h": max(r["h"] for r in rows), "l": min(r["l"] for r in rows),
            "c": rows[-1]["c"], "v": sum(r["v"] for r in rows)})
    return out


def opening_range(bars5):
    """(or_high, or_low, or_mean_volume) from the first six 5-minute
    bars, or None when fewer than six exist. Pure function of the
    first six bars: later bars can never move the range."""
    if not bars5 or len(bars5) < OR_BARS:
        return None
    first = bars5[:OR_BARS]
    return (max(b["h"] for b in first), min(b["l"] for b in first),
            sum(b["v"] for b in first) / OR_BARS)


def _bar_time(bar):
    return datetime.fromtimestamp(bar["t"], tz=ET).time()


def _inside(close, or_high, or_low):
    return or_low <= close <= or_high


def _stop_target(direction, entry, or_high, or_low):
    """Frozen stop/target math. Stop just inside the broken edge;
    target the measured move or 2R, whichever is closer."""
    height = or_high - or_low
    if direction == 1:
        stop = round(or_high - STOP_INSIDE, 4)
        risk = entry - stop
        if risk <= 0:
            return stop, None
        target = min(or_high + height, entry + TARGET_R_MULT * risk)
    else:
        stop = round(or_low + STOP_INSIDE, 4)
        risk = stop - entry
        if risk <= 0:
            return stop, None
        target = max(or_low - height, entry - TARGET_R_MULT * risk)
    return stop, round(target, 4)


def _scan(bars5, or_high, or_low, or_mean_vol, dead_dirs):
    """Replay today's post-OR bars deterministically. Returns one of:
      ("trigger", direction, bar_index)  - the LAST bar is a valid
        continuation-entry trigger;
      ("trigger_missed", direction)    - a trigger completed before
        the last bar (direction consumed; never emitted late);
      ("invalidated", direction)       - the last bar closed back
        inside the range on a live pending setup;
      ("pending", direction) / (None, None) otherwise.
    Pure function of the bars and the dead-direction set."""
    dead = set(dead_dirs or ())
    pending = None
    last = len(bars5) - 1
    for i in range(OR_BARS, len(bars5)):
        bar = bars5[i]
        if pending is None:
            if _bar_time(bar) >= BREAKOUT_CUTOFF:
                break
            if (1 not in dead and bar["c"] > or_high
                    and bar["v"] >= BREAKOUT_VOL_MULT * or_mean_vol):
                pending = {"direction": 1, "idx": i, "vol": bar["v"],
                           "pullback": []}
            elif (-1 not in dead and bar["c"] < or_low
                    and bar["v"] >= BREAKOUT_VOL_MULT * or_mean_vol):
                pending = {"direction": -1, "idx": i, "vol": bar["v"],
                           "pullback": []}
            continue
        d = pending["direction"]
        # Expiry: 6-bar pullback window + 6 further bars of drift.
        if i > pending["idx"] + MAX_PULLBACK_BARS + DRIFT_BARS:
            dead.add(d)
            pending = None
            continue
        # Invalidation: a close back inside the range kills the setup.
        if _inside(bar["c"], or_high, or_low):
            dead.add(d)
            pending = None
            if i == last:
                return ("invalidated", d)
            continue
        pullback = pending["pullback"]
        if len(pullback) >= 1:
            if d == 1:
                extreme = max(b["h"] for b in pullback)
                triggered = bar["c"] > extreme
            else:
                extreme = min(b["l"] for b in pullback)
                triggered = bar["c"] < extreme
            if triggered and bar["v"] > pullback[-1]["v"]:
                if i == last:
                    return ("trigger", d)
                dead.add(d)
                pending = None
                return ("trigger_missed", d)
        # Pullback bar: a counter-move close toward the broken edge.
        prev = bars5[i - 1]
        is_pullback = bar["c"] < prev["c"] if d == 1 else bar["c"] > prev["c"]
        if is_pullback:
            if bar["v"] >= pending["vol"]:
                # Not the lower-volume pullback the rule requires.
                dead.add(d)
                pending = None
                continue
            pullback.append(bar)
            if len(pullback) > MAX_PULLBACK_BARS:
                dead.add(d)
                pending = None
                continue
    if pending is not None:
        return ("pending", pending["direction"])
    return (None, None)


# ------------------------------------------------------------------ sleeve
class TeddyOrbSpySleeve(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, ctx):
        extra = ctx.extra or {}
        state = dict(extra.get("teddy_state") or {})
        session = ctx.session
        if state.get("day") != session:
            state = {"day": session, "plan": None, "dead_directions": []}
        state.setdefault("plan", None)
        state.setdefault("dead_directions", [])
        self.teddy_state = state
        self.last_evaluation = {"sleeve": CONFIG.sleeve_id,
                                "session": session, "state": "scanning"}
        raw = (bars or {}).get(SYMBOL) or []
        bars1 = _rth_bars_1min(raw, session)
        bars5 = aggregate_5min(bars1)
        qty_open = _number((slice_state or {}).get(SYMBOL)) or 0.0
        now_dt = datetime.fromtimestamp(ctx.now, tz=ET)
        plan = state.get("plan")

        # ---- an exit the desk already executed: direction dies -----
        if plan and qty_open == 0 and plan.get("seen_open"):
            d = int(plan.get("direction") or 0)
            if d and d not in state["dead_directions"]:
                state["dead_directions"].append(d)
            state["plan"] = None
            plan = None
            self.last_evaluation["state"] = "exit_observed_direction_dead"

        # ---- manage an open position --------------------------------
        if plan and qty_open != 0:
            plan["seen_open"] = True
            return self._manage(bars5, state, plan, qty_open, now_dt)
        if plan and qty_open == 0:
            self.last_evaluation["state"] = "awaiting_fill"
            return []
        if qty_open != 0:
            if now_dt.time() >= FLAT_TIME:
                self.last_evaluation["state"] = "flat_1400_no_plan"
                latest = bars5[-1] if bars5 else None
                return [self._exit(latest, abs(qty_open), qty_open,
                                   "teddy_orb_spy flat 14:00 ET (plan unavailable)")]
            self.last_evaluation["state"] = "position_open_no_plan"
            return []

        # ---- entries --------------------------------------------------
        if len(bars5) < OR_BARS:
            self.last_evaluation["state"] = "opening_range_forming"
            return []
        or_high, or_low, or_mean_vol = opening_range(bars5)
        self.last_evaluation["or_high"] = or_high
        self.last_evaluation["or_low"] = or_low
        self.last_evaluation["or_mean_volume"] = or_mean_vol
        latest = bars5[-1]
        if _bar_time(latest) >= ENTRY_CUTOFF:
            self.last_evaluation["state"] = "past_entry_cutoff_1230"
            return []
        outcome, direction = _scan(bars5, or_high, or_low, or_mean_vol,
                                   state.get("dead_directions"))
        if outcome == "invalidated":
            self.last_evaluation["state"] = "setup_invalidated_close_inside"
            return []
        if outcome == "trigger_missed":
            if direction not in state["dead_directions"]:
                state["dead_directions"].append(direction)
            self.last_evaluation["state"] = "trigger_missed_direction_consumed"
            return []
        if outcome != "trigger":
            self.last_evaluation["state"] = (
                "setup_pending" if outcome == "pending" else "no_setup")
            return []
        equity = _number(ctx.equity) or 0.0
        if equity <= 0:
            self.last_evaluation["state"] = "blocked_equity_unavailable"
            return []
        entry = latest["c"]
        stop, target = _stop_target(direction, entry, or_high, or_low)
        if target is None:
            self.last_evaluation["state"] = "blocked_zero_risk"
            return []
        risk = abs(entry - stop)
        qty = int(math.floor(min(UNIT_RISK_PCT * equity / risk,
                                 NOTIONAL_CAP_PCT * equity / entry)))
        if qty <= 0:
            self.last_evaluation["state"] = "blocked_size_zero"
            return []
        state["plan"] = {
            "direction": direction, "entry": entry, "stop": stop,
            "target": target, "or_high": or_high, "or_low": or_low,
            "session": session, "seen_open": False}
        state["dead_directions"] = list(
            state.get("dead_directions") or [])  # direction dies on exit
        self.last_evaluation["state"] = "entry_intent"
        side = "buy" if direction == 1 else "sell"
        reason = (
            f"teddy_orb_spy ORB {'long' if direction == 1 else 'short'}: "
            f"or={or_low:.2f}-{or_high:.2f}; entry={entry:.4f}; "
            f"stop={stop:.4f}; target={target:.4f}; qty={qty}")
        return [Intent(
            "enter", SYMBOL, qty=qty, price_hint=entry,
            stop=stop, target=target,
            exit_rules=(ExitRule("stop", stop), ExitRule("target", target)),
            reason=reason, side=side,
            position_intent="buy_to_open" if direction == 1 else "sell_to_open",
            signal_date=session)]

    # ------------------------------------------------------------ exits
    def _exit(self, bar, qty, signed_qty, reason):
        return Intent("exit", SYMBOL, qty=float(qty),
                      price_hint=bar["c"] if bar else None, reason=reason,
                      side="buy" if signed_qty < 0 else "sell",
                      position_intent="buy_to_close" if signed_qty < 0
                      else "sell_to_close")

    def _manage(self, bars5, state, plan, qty_open, now_dt):
        signed = qty_open
        latest = bars5[-1] if bars5 else None
        # Hard flat first: 14:00 ET exits everything.
        if now_dt.time() >= FLAT_TIME:
            d = int(plan.get("direction") or 0)
            if d and d not in state["dead_directions"]:
                state["dead_directions"].append(d)
            state["plan"] = None
            self.last_evaluation["state"] = "flat_1400"
            return [self._exit(latest, abs(signed), signed,
                               "teddy_orb_spy flat 14:00 ET")]
        if latest is None:
            self.last_evaluation["state"] = "position_open"
            return []
        # Invalidation: a close back inside the opening range exits.
        if _inside(latest["c"], float(plan["or_high"]), float(plan["or_low"])):
            d = int(plan.get("direction") or 0)
            if d and d not in state["dead_directions"]:
                state["dead_directions"].append(d)
            state["plan"] = None
            self.last_evaluation["state"] = "invalidation_exit"
            return [self._exit(latest, abs(signed), signed,
                               "teddy_orb_spy close back inside opening range: exit next open")]
        self.last_evaluation["state"] = "position_open"
        return []


_INSTANCE = TeddyOrbSpySleeve()


def signal(bars, slice_state, context):
    out = _INSTANCE.signal(bars, slice_state, context)
    signal.last_evaluation = _INSTANCE.last_evaluation
    signal.teddy_state = _INSTANCE.teddy_state
    return out
