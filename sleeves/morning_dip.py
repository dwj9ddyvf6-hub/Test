"""Morning Dip — lean-desk port.

EXTRACTED from the old desk's morning_dip.py (Milkman Morning Dip
Limit, QQQ). indicators() and _arm_plan() are ported VERBATIM (the old
_arm_plan was already a pure function; cid generation is dropped —
core Broker owns ids). Plumbing (bracket orders, chart-gate staging,
state) is core-owned. See ports/morning_dip.md.

Strategy (old module docstring): 3-min QQQ candles, window 10:00-12:00
ET. ER <= 0.35 arms a buy limit at (signal close - 1.0 ATR) floored to
the tick, rested 1 tick below the level; target = signal candle
midpoint; stop = max(4 ticks, ceil(1.5 ATR)) below the LIMIT price;
cancel unfilled after 9 min; time stop 15 min; flat at 12:00 ET.
ATR = simple mean of last 14 true ranges; ER over the last 16 candles
(all 16 must be healthy). One position at a time. Risk 0.25%/trade.

Decision #87 (desk-cap-aware sizing): the old _cap_clamp_qty clamped
the arm qty to 150%-gross headroom at stage AND release. In the lean
desk that clamp is core Risk's cap leg — this sleeve emits the
UNCLAMPED strategy qty as a hint and names the dependency in the port
report; Risk applies the identical clamp downstream.

Inputs via context.extra:
  "candles_3min": [closed 3-min candle dicts {"t","o","h","l","c",
                   "healthy"}] for QQQ (core Data product)
  "sleeve_state": {"QQQ": {"position": {...} | None}}
Bars (arg): unused for the signal (3-min candles arrive via extra);
accepted for contract shape.
"""
import math
from datetime import datetime
from zoneinfo import ZoneInfo

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")
SYMBOL = "QQQ"
RISK_FRACTION = 0.0025
TICK = 0.01
WINDOW_START = (10, 0)
WINDOW_END = (12, 0)
ARM_CANCEL_MIN = 9
TIME_STOP_MIN = 15
ER_MAX = 0.35
ATR_LEN = 14
ER_CANDLES = 15

CONFIG = SleeveConfig(
    sleeve_id="morning_dip", cadence_s=180, universe=(SYMBOL,),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


def in_window(now_et):
    """Verbatim: weekday and WINDOW_START <= t < WINDOW_END (ET)."""
    if now_et.weekday() >= 5:
        return False
    t = (now_et.hour, now_et.minute)
    return WINDOW_START <= t < WINDOW_END


def true_range(b, prev_c):
    return max(b["h"] - b["l"], abs(b["h"] - prev_c), abs(b["l"] - prev_c))


def indicators(candles):
    """(atr, er) on the last closed candle, or (None, None) — verbatim."""
    n = len(candles)
    if n < ER_CANDLES + 1:
        return None, None
    win = candles[-(ER_CANDLES + 1):]
    if not all(c.get("healthy") for c in win):
        return None, None
    trs = [true_range(win[i], win[i - 1]["c"])
           for i in range(len(win) - ATR_LEN, len(win))]
    atr = sum(trs) / len(trs)
    closes = [c["c"] for c in win]
    den = sum(abs(closes[i] - closes[i - 1]) for i in range(1, len(closes)))
    er = (abs(closes[-1] - closes[0]) / den) if den > 0 else 1.0
    return atr, er


def rr_geometry_gate_enabled(extra):
    """ENH-morning_dip (Edge IMPROVE, Group A): context.extra
    ["morning_dip_improve"]["rr_geometry_gate"], default ON; OFF
    restores the pre-change arm rule exactly (control)."""
    ov = (extra or {}).get("morning_dip_improve")
    if isinstance(ov, dict) and "rr_geometry_gate" in ov:
        return bool(ov["rr_geometry_gate"])
    return True


def arm_plan(sig, atr, er, equity, enhanced=True):
    """Verbatim old _arm_plan minus the cid (core-owned): (plan, None)
    or (None, skip_event). ENH: with enhanced=True (the default), an
    arm whose coded reward (target - limit) is smaller than its coded
    risk (limit - stop) is refused - reward-to-risk < 1 on the plan's
    own computed values (IMPROVE-morning_dip section 2)."""
    risk_dollars = equity * RISK_FRACTION
    level = math.floor((sig["c"] - atr) * 100 + 1e-8) / 100
    if (sig["c"] - level) < TICK - 1e-8:
        return None, {"event": "skip_shape",
                      "reason": "level<1 tick under close",
                      "er": round(er, 3)}
    reward = math.ceil(((sig["h"] + sig["l"]) / 2 - level) * 100 - 1e-8) / 100
    if reward < 2 * TICK - 1e-8:
        return None, {"event": "skip_shape", "reason": "reward<2 ticks",
                      "er": round(er, 3)}
    target_px = round(level + reward, 2)
    limit_px = round(level - TICK, 2)
    stopdist = max(4 * TICK, math.ceil(1.5 * atr * 100 - 1e-8) / 100)
    stop_px = round(limit_px - stopdist, 2)
    qty = int(risk_dollars // stopdist)
    if qty < 1:
        return None, {"event": "skip_size", "reason": "qty<1",
                      "atr": round(atr, 3)}
    if target_px <= limit_px:
        return None, {"event": "skip_shape",
                      "reason": "target<=limit (no room)",
                      "er": round(er, 3)}
    if enhanced and (target_px - limit_px) < (limit_px - stop_px):
        return None, {"event": "skip_geometry",
                      "reason": "reward<risk: target-limit %.2f < "
                                "limit-stop %.2f"
                                % (target_px - limit_px,
                                   limit_px - stop_px),
                      "er": round(er, 3)}
    plan = {"qty": qty, "limit": limit_px, "target": target_px,
            "stop": stop_px, "level": level,
            "er": round(er, 4), "atr": round(atr, 4)}
    return plan, None


class MorningDip(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        pos = (state.get(SYMBOL) or {}).get("position")
        now_et = datetime.fromtimestamp(float(context.now), tz=ET)
        intents = []
        if pos:
            qty = int(float(pos.get("qty") or 0))
            if qty > 0:
                # AUDIT3-B-03 (2026-10-16): the arm plan's stop,
                # target and 15-minute time stop were emitted as
                # ExitRule data for a core executor that does not
                # exist — protection skips this sleeve because its
                # stop is "evaluated in-signal", and the sleeve
                # never evaluated it. The only exit was the 12:00
                # flatten. Evaluate the record's own levels on
                # the 3-minute frame and the time stop from the
                # record's fill_t (entry_t for legacy records),
                # in-signal.
                stop = target = None
                for r in pos.get("exit_rules") or ():
                    if isinstance(r, dict):
                        if r.get("kind") == "stop":
                            stop = float(r["value"])
                        elif r.get("kind") == "target":
                            target = float(r["value"])
                if stop is None and pos.get("stop_px") is not None:
                    stop = float(pos["stop_px"])
                candles = extra.get("candles_3min") or []
                last = None
                if candles:
                    try:
                        last = float(candles[-1]["c"])
                    except (TypeError, ValueError, KeyError):
                        last = None
                hit = None
                if last is not None and stop is not None \
                        and last <= stop:
                    hit = "stop %.2f (close %.2f)" % (stop, last)
                elif last is not None and target is not None \
                        and last >= target:
                    hit = "target %.2f (close %.2f)" % (target, last)
                elif (pos.get("fill_t") or pos.get("entry_t")) \
                        and float(context.now) \
                        - float(pos.get("fill_t") or pos["entry_t"]) \
                        >= TIME_STOP_MIN * 60:
                    # CURE2-MDIP-FILL-CLOCK (2026-10-19): the
                    # 15-minute stop clocks the POSITION, so it
                    # runs from the first FILL (fill_t, stamped
                    # from broker truth), not from order
                    # submission (entry_t) — a limit arm may rest
                    # up to ARM_CANCEL_MIN before filling, and
                    # that resting time was being spent from the
                    # position's 15 minutes. Legacy records with
                    # no fill_t keep the entry_t clock (fallback
                    # above), never an unbounded hold.
                    hit = "time stop %d min" % TIME_STOP_MIN
                if hit:
                    intents.append(Intent(
                        "exit", SYMBOL, qty_hint=qty,
                        price_hint=(round(last, 2)
                                    if last is not None else None),
                        reason="morning_dip: exit — %s" % hit))
                    return intents
            if qty > 0 and not in_window(now_et):
                intents.append(Intent(
                    "exit", SYMBOL, qty_hint=qty,
                    reason="morning_dip: flat at/after window end 12:00 ET"))
            return intents
        if not in_window(now_et):
            return intents
        candles = extra.get("candles_3min") or []
        atr, er = indicators(candles)
        if atr is None or er is None:
            return intents
        if er > ER_MAX:
            return intents  # ER gate: only a clean directional morning arms
        equity = float(context.equity or 0.0)
        if equity <= 0:
            return intents
        plan, _skip = arm_plan(candles[-1], atr, er, equity,
                               enhanced=rr_geometry_gate_enabled(extra))
        if plan is None:
            return intents
        intents.append(Intent(
            "enter", SYMBOL, qty_hint=plan["qty"],
            limit_price=plan["limit"],
            price_hint=plan["limit"], stop=plan["stop"],
            target=plan["target"],
            exit_rules=(ExitRule("stop", plan["stop"]),
                        ExitRule("target", plan["target"])),
            reason="morning_dip arm: ER=%.4f ATR=%.4f level=%.2f limit=%.2f "
                   "(cancel %d min unfilled, time stop %d min — core timers)"
                   % (plan["er"], plan["atr"], plan["level"], plan["limit"],
                      ARM_CANCEL_MIN, TIME_STOP_MIN)))
        return intents


def signal(bars, slice_state, context):
    return MorningDip().signal(bars, slice_state, context)
