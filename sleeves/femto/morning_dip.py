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

Inputs (master-desk):
  bars {"QQQ": [1-minute bars incl. the pre-market from 09:00 ET]} -> the
      old 3-minute UTC-grid candles (healthy with >= 2 minute bars)
  context.extra "candles_3min" — accepted instead (femto shape)
  "sleeve_state": {"QQQ": {"position": {...} | None, "pending_entry"}}
"""
import math
from datetime import datetime
from zoneinfo import ZoneInfo

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig

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


def arm_plan(sig, atr, er, equity):
    """Verbatim old _arm_plan minus the cid (core-owned): (plan, None)
    or (None, skip_event)."""
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
    plan = {"qty": qty, "limit": limit_px, "target": target_px,
            "stop": stop_px, "level": level,
            "er": round(er, 4), "atr": round(atr, 4)}
    return plan, None


# ---------------------------------------------------------------- master-desk: the old runtime, restored
CANDLE_S = 180
CLOSED_AFTER_S = 210            # old closed_candles: a 3-min candle is closed 3.5 min after it started


def candles_3min(min_bars, now):
    """old fetch_3min + closed_candles: 1-minute bars from 09:00 ET bucketed on the UTC 3-minute grid
    (bucket = t // 180 * 180), healthy with >= 2 of its 3 minute bars, closed 210 s after its start."""
    if not min_bars:
        return []
    day0 = datetime.fromtimestamp(float(now), tz=ET).replace(hour=9, minute=0, second=0, microsecond=0).timestamp()
    buckets = {}
    for b in min_bars:
        t = float(b["t"])
        if t < day0 or t >= float(now):
            continue
        k = int(t // CANDLE_S) * CANDLE_S
        e = buckets.setdefault(k, {"t": float(k), "o": float(b["o"]), "h": -1e18, "l": 1e18, "c": None, "n": 0})
        e["h"] = max(e["h"], float(b["h"]))
        e["l"] = min(e["l"], float(b["l"]))
        e["c"] = float(b["c"])
        e["n"] += 1
    return [dict(buckets[k], healthy=buckets[k]["n"] >= 2) for k in sorted(buckets)
            if float(now) - k >= CLOSED_AFTER_S]


class MorningDip(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        """master-desk: the old morning_dip pass (every 3 minutes, 10:00-12:00 ET). Held: flat at 12:00 ET (the
        bracket target/stop and the 15-minute time stop are engine exit data). Flat with nothing working and
        a fresh signal candle (closed, starting 10:00-12:00 ET, not acted on before, the last 16 candles
        healthy, ER <= 0.35): arm a DAY limit buy one tick under level = floor(close - ATR), bracket target
        = the candle midpoint, stop = max(4 ticks, ceil(1.5 ATR)) under the limit; unfilled after 9 minutes
        it is cancelled. One order or position at a time. The desk cap clamp (Decision #87), risk gate,
        context gate and Decision #75 staging are desk-wide gates, out of scope by the cutover doctrine."""
        extra = context.extra or {}
        st = (extra.get("sleeve_state") or {}).get(SYMBOL) or {}
        pos = st.get("position")
        now = float(context.now)
        now_et = datetime.fromtimestamp(now, tz=ET)
        intents = []
        if pos:
            qty = abs(float(pos.get("qty") or 0))
            if qty > 0 and not in_window(now_et) and (now_et.hour, now_et.minute) >= WINDOW_END \
                    and not pos.get("exit_submitted"):
                intents.append(Intent("exit", SYMBOL, qty=qty, signal_key="%s:%s:eod" % (SYMBOL, context.session),
                                      reason="morning_dip: flat at the 12:00 ET window end"))
            return intents
        if st.get("pending_entry") or not in_window(now_et):
            return intents                            # one order/position at a time
        if bars.get(SYMBOL):                          # 1-minute bars -> the old 3-minute candles
            candles = candles_3min(bars[SYMBOL], now)
        else:                                         # femto shape: pre-built closed candles
            candles = list(extra.get("candles_3min") or [])
        if len(candles) < ER_CANDLES + 1:
            return intents
        sig = candles[-1]
        sig_et = datetime.fromtimestamp(float(sig["t"]), tz=ET)
        if not (WINDOW_START <= (sig_et.hour, sig_et.minute) < WINDOW_END):
            return intents
        atr, er = indicators(candles)
        if atr is None or atr <= 0 or er is None or er > ER_MAX:
            return intents
        equity = float(context.equity or 0.0)
        if equity <= 0:
            return intents
        plan, _skip = arm_plan(sig, atr, er, equity)
        if plan is None:
            return intents
        intents.append(Intent(
            "enter", SYMBOL, qty_hint=plan["qty"], price_hint=plan["limit"], stop=plan["stop"],
            target=plan["target"], exit_rules=(ExitRule("time_bars", float(TIME_STOP_MIN)),),
            order={"type": "limit", "limit_price": plan["limit"], "not_after": now + ARM_CANCEL_MIN * 60},
            signal_key="%s:%s:mdl:%d" % (SYMBOL, context.session, int(sig["t"])),
            position_meta={"level": plan["level"], "signal_candle": sig_et.strftime("%H:%M")},
            reason="morning_dip arm %s: ER=%.4f ATR=%.4f level=%.2f limit=%.2f target=%.2f stop=%.2f"
                   % (sig_et.strftime("%H:%M"), plan["er"], plan["atr"], plan["level"], plan["limit"],
                      plan["target"], plan["stop"])))
        return intents


def signal(bars, slice_state, context):
    return MorningDip().signal(bars, slice_state, context)
