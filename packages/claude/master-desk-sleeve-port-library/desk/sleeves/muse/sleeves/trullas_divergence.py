"""Trullas divergence sleeve — PRIMARY ARM of TRULLAS-SPEC-2026-10-25 v1.0 (FROZEN).

Mechanical skeleton of David Trullas Vila's divergence method, exactly as
the frozen spec defines the primary arm (QQQ, 1-minute SIP bars):

  * Pivots k=5, usable only after the 5 right-side bars have closed
    (anti-repaint: no pivot is ever used before its confirmation bar).
  * Pairing: two consecutive confirmed pivots of the same kind, same
    trading day, 10..120 bars apart.
  * MACD(12,26,9) read on the MACD line; MACD divergence is REQUIRED.
    RSI(14) divergence and volume divergence (second extreme on lower
    bar volume) are counted; divergence count 1..3 maps to risk units.
  * Fibonacci swing (bearish): A = lowest low between the two highs,
    B = second pivot high; level(p) = B - p*(B-A). Bullish mirrored.
  * Entry trigger at level(0.236) minus one tick ($0.01), expiring
    after 30 bars or on a trade beyond the extreme + one tick.
  * Stop one tick beyond the extreme; TP1 at 38.2 (exit half, stop to
    entry), TP2 at 61.8. Pessimistic intrabar ordering: when one bar
    spans both stop and target, the stop outcome is taken first.
  * Entries only 09:30-11:00 ET; hard flat 12:00 ET; max 5 entries/day;
    daily loss stop at -0.75% of slice equity; unit risk 0.25% of
    slice equity; notional cap 25% of slice equity per trade.

The control / secondary / sensitivity arms of the spec are backtest
machinery and are NOT sleeve behavior; they do not exist here.

State (pending setup, open-trade plan, day counters) is carried in
ctx.extra["trullas_state"] and round-tripped by the adapter, which
persists it in the sleeve's own state file. The strategy itself is
pure: clock only via Context.now, no files, no broker.
"""
from __future__ import annotations

import math
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")

SYMBOL = "QQQ"
PIVOT_K = 5
MIN_SEPARATION = 10
MAX_SEPARATION = 120
MACD_FAST, MACD_SLOW, MACD_SIGNAL = 12, 26, 9
RSI_LENGTH = 14
TICK = 0.01
ENTRY_LEVEL = 0.236
TP1_LEVEL = 0.382
TP2_LEVEL = 0.618
ENTRY_EXPIRY_BARS = 30
ENTRY_START = dtime(9, 30)
ENTRY_END = dtime(11, 0)
FLAT_TIME = dtime(12, 0)
MAX_ENTRIES_PER_DAY = 5
DAILY_LOSS_STOP_PCT = 0.0075
UNIT_RISK_PCT = 0.0025
NOTIONAL_CAP_PCT = 0.25

CONFIG = SleeveConfig(
    sleeve_id="trullas_divergence",
    cadence_s=60,
    universe=(SYMBOL,),
    state_schema={"trullas_state": "dict", "position": "dict|None"},
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


def _rth_bars(raw):
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
        if dt.time() < dtime(9, 30) or dt.time() >= dtime(16, 0):
            continue
        if v <= 0:
            continue  # spec section 2: zero-volume bars dropped
        out.append({"t": t, "o": o, "h": h, "l": l, "c": c, "v": v})
    out.sort(key=lambda b: b["t"])
    deduped = []
    for b in out:
        if deduped and b["t"] == deduped[-1]["t"]:
            deduped[-1] = b
        else:
            deduped.append(b)
    return deduped


def _ema(values, period):
    out = [None] * len(values)
    if len(values) < period:
        return out
    k = 2.0 / (period + 1.0)
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    prev = seed
    for i in range(period, len(values)):
        prev = values[i] * k + prev * (1.0 - k)
        out[i] = prev
    return out


def macd_line(closes):
    fast = _ema(closes, MACD_FAST)
    slow = _ema(closes, MACD_SLOW)
    return [(f - s) if (f is not None and s is not None) else None
            for f, s in zip(fast, slow)]


def rsi_wilder(closes):
    n = len(closes)
    out = [None] * n
    if n <= RSI_LENGTH:
        return out
    gains, losses = [], []
    for j in range(1, RSI_LENGTH + 1):
        d = closes[j] - closes[j - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    avg_g, avg_l = sum(gains) / RSI_LENGTH, sum(losses) / RSI_LENGTH
    for i in range(RSI_LENGTH, n):
        if i > RSI_LENGTH:
            d = closes[i] - closes[i - 1]
            avg_g = (avg_g * (RSI_LENGTH - 1) + max(d, 0.0)) / RSI_LENGTH
            avg_l = (avg_l * (RSI_LENGTH - 1) + max(-d, 0.0)) / RSI_LENGTH
        if avg_l == 0.0:
            out[i] = 100.0 if avg_g > 0.0 else 50.0
        else:
            out[i] = 100.0 - 100.0 / (1.0 + avg_g / avg_l)
    return out


def find_pivots(bars, k=PIVOT_K):
    """Confirmed pivots only. A pivot at index i is returned with
    confirm_index = i + k: it is knowable only once bar i+k exists.
    Strictly highest/lowest over the 2k+1 window (spec section 4)."""
    highs, lows = [], []
    n = len(bars)
    for i in range(k, n - k):
        window_h = [bars[j]["h"] for j in range(i - k, i + k + 1)]
        if bars[i]["h"] == max(window_h) and window_h.count(bars[i]["h"]) == 1:
            highs.append({"index": i, "price": bars[i]["h"],
                          "confirm_index": i + k, "t": bars[i]["t"]})
        window_l = [bars[j]["l"] for j in range(i - k, i + k + 1)]
        if bars[i]["l"] == min(window_l) and window_l.count(bars[i]["l"]) == 1:
            lows.append({"index": i, "price": bars[i]["l"],
                         "confirm_index": i + k, "t": bars[i]["t"]})
    return highs, lows


def detect_setups(bars):
    """All divergence setups whose decision (confirmation) bar exists
    in `bars`. Each setup dict carries the frozen Fib geometry."""
    closes = [b["c"] for b in bars]
    macd = macd_line(closes)
    rsi = rsi_wilder(closes)
    highs, lows = find_pivots(bars)
    setups = []

    def day(idx):
        return datetime.fromtimestamp(bars[idx]["t"], tz=ET).date()

    for pivots, kind in ((highs, "high"), (lows, "low")):
        for first, second in zip(pivots, pivots[1:]):
            gap = second["index"] - first["index"]
            if not (MIN_SEPARATION <= gap <= MAX_SEPARATION):
                continue
            if day(first["index"]) != day(second["index"]):
                continue
            i1, i2 = first["index"], second["index"]
            if macd[i1] is None or macd[i2] is None or rsi[i1] is None or rsi[i2] is None:
                continue
            bearish = kind == "high"
            if bearish:
                price_div = second["price"] > first["price"]
                macd_div = macd[i2] < macd[i1]
                rsi_div = rsi[i2] < rsi[i1]
            else:
                price_div = second["price"] < first["price"]
                macd_div = macd[i2] > macd[i1]
                rsi_div = rsi[i2] > rsi[i1]
            vol_div = bars[i2]["v"] < bars[i1]["v"]
            if not price_div or not macd_div:
                continue  # MACD divergence is REQUIRED (spec section 5)
            count = int(macd_div) + int(rsi_div) + int(vol_div)
            if bearish:
                a = min(bars[j]["l"] for j in range(i1, i2 + 1))
                b = second["price"]
                if b <= a:
                    continue
                lvl = lambda p: b - p * (b - a)
                entry_trigger = lvl(ENTRY_LEVEL) - TICK
                stop = b + TICK
                tp1, tp2 = lvl(TP1_LEVEL), lvl(TP2_LEVEL)
                direction = -1
            else:
                a = max(bars[j]["h"] for j in range(i1, i2 + 1))
                b = second["price"]
                if a <= b:
                    continue
                lvl = lambda p: b + p * (a - b)
                entry_trigger = lvl(ENTRY_LEVEL) + TICK
                stop = b - TICK
                tp1, tp2 = lvl(TP1_LEVEL), lvl(TP2_LEVEL)
                direction = 1
            setups.append({
                "direction": direction, "kind": kind,
                "first_index": i1, "second_index": i2,
                "confirm_index": second["confirm_index"],
                "confirm_t": bars[second["confirm_index"]]["t"],
                "session": day(i2).isoformat(),
                "first_price": first["price"], "second_price": second["price"],
                "swing_a": a, "swing_b": b,
                "macd_first": macd[i1], "macd_second": macd[i2],
                "rsi_first": rsi[i1], "rsi_second": rsi[i2],
                "vol_first": bars[i1]["v"], "vol_second": bars[i2]["v"],
                "divergence_count": count,
                "entry_trigger": entry_trigger, "stop": stop,
                "tp1": tp1, "tp2": tp2,
            })
    setups.sort(key=lambda s: s["confirm_index"])
    return setups


# ------------------------------------------------------------------ sleeve
class TrullasDivergenceSleeve(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, ctx):
        extra = ctx.extra or {}
        state = dict(extra.get("trullas_state") or {})
        session = ctx.session
        if state.get("day") != session:
            state = {"day": session, "entries_today": 0,
                     "realized_pnl": 0.0, "pending": None, "plan": None,
                     "traded_pairs": []}
        self.last_evaluation = {"sleeve": CONFIG.sleeve_id,
                                "session": session, "state": "scanning"}
        raw = (bars or {}).get(SYMBOL) or []
        bars1m = _rth_bars(raw)
        self.trullas_state = state
        if not bars1m:
            self.last_evaluation["state"] = "no_bars"
            return []
        latest = bars1m[-1]
        now_dt = datetime.fromtimestamp(ctx.now, tz=ET)
        equity = _number(ctx.equity) or 0.0
        qty_open = _number((slice_state or {}).get(SYMBOL)) or 0.0

        # ---- manage an open position --------------------------------
        plan = state.get("plan")
        if qty_open != 0 and plan:
            return self._manage(bars1m, latest, state, plan, qty_open, ctx)
        if qty_open != 0:
            # Plan lost (state rebuilt): only the hard flat is knowable.
            if now_dt.time() >= FLAT_TIME:
                self.last_evaluation["state"] = "flat_1200_no_plan"
                return [self._exit(latest, abs(qty_open), qty_open,
                                   "trullas flat 12:00 ET (plan unavailable)")]
            self.last_evaluation["state"] = "position_open_no_plan"
            return []

        # ---- refresh pending setup from confirmations on/before now --
        setups = [s for s in detect_setups(bars1m)
                  if s["session"] == session
                  and s["confirm_t"] <= latest["t"]
                  and (s["first_index"], s["second_index"])
                  not in [tuple(p) for p in state.get("traded_pairs") or []]]
        if setups:
            newest = setups[-1]
            pending = state.get("pending")
            if (not pending
                    or (pending["first_index"], pending["second_index"])
                    != (newest["first_index"], newest["second_index"])):
                state["pending"] = {k: newest[k] for k in (
                    "direction", "first_index", "second_index",
                    "confirm_index", "session", "swing_a", "swing_b",
                    "divergence_count", "entry_trigger", "stop",
                    "tp1", "tp2")}
                self.last_evaluation["pending_set"] = dict(state["pending"])

        pending = state.get("pending")
        if not pending:
            self.last_evaluation["state"] = "no_setup"
            return []

        # ---- pending expiry / invalidation ---------------------------
        bars_since = len(bars1m) - 1 - pending["confirm_index"]
        if bars_since > ENTRY_EXPIRY_BARS:
            state["pending"] = None
            self.last_evaluation["state"] = "setup_expired_30_bars"
            return []
        if pending["direction"] == -1 and latest["h"] > pending["swing_b"] + TICK:
            state["pending"] = None
            self.last_evaluation["state"] = "setup_void_extreme_break"
            return []
        if pending["direction"] == 1 and latest["l"] < pending["swing_b"] - TICK:
            state["pending"] = None
            self.last_evaluation["state"] = "setup_void_extreme_break"
            return []

        # ---- entry gates ---------------------------------------------
        latest_dt = datetime.fromtimestamp(latest["t"], tz=ET)
        if not (ENTRY_START <= latest_dt.time() < ENTRY_END):
            self.last_evaluation["state"] = "outside_entry_window"
            return []
        if int(state.get("entries_today") or 0) >= MAX_ENTRIES_PER_DAY:
            self.last_evaluation["state"] = "blocked_max_entries_5"
            return []
        if equity <= 0:
            self.last_evaluation["state"] = "blocked_equity_unavailable"
            return []
        if float(state.get("realized_pnl") or 0.0) <= -DAILY_LOSS_STOP_PCT * equity:
            self.last_evaluation["state"] = "blocked_daily_loss_stop"
            return []

        # ---- trigger --------------------------------------------------
        d = pending["direction"]
        triggered = (latest["l"] <= pending["entry_trigger"]) if d == -1 \
            else (latest["h"] >= pending["entry_trigger"])
        if not triggered:
            self.last_evaluation["state"] = "setup_pending"
            return []
        fill_px = pending["entry_trigger"]  # trigger tick (spec section 6)
        stop = pending["stop"]
        risk_per_share = abs(stop - fill_px)
        if risk_per_share <= 0:
            state["pending"] = None
            return []
        units = int(pending["divergence_count"])
        qty = int(math.floor(min(
            units * UNIT_RISK_PCT * equity / risk_per_share,
            NOTIONAL_CAP_PCT * equity / fill_px)))
        if qty <= 0:
            self.last_evaluation["state"] = "blocked_size_zero"
            return []
        state["entries_today"] = int(state.get("entries_today") or 0) + 1
        state.setdefault("traded_pairs", []).append(
            [pending["first_index"], pending["second_index"]])
        state["plan"] = {
            "direction": d, "entry": fill_px, "stop": stop,
            "tp1": pending["tp1"], "tp2": pending["tp2"],
            "tp1_done": False, "qty_initial": qty,
            "session": session}
        state["pending"] = None
        self.last_evaluation["state"] = "entry_intent"
        self.last_evaluation["divergence_count"] = units
        reason = (
            f"trullas_divergence primary {'short' if d == -1 else 'long'}: "
            f"divergences={units}; swing_a={pending['swing_a']:.4f}; "
            f"swing_b={pending['swing_b']:.4f}; entry={fill_px:.4f}; "
            f"stop={stop:.4f}; tp1={pending['tp1']:.4f}; "
            f"tp2={pending['tp2']:.4f}; qty={qty}")
        return [Intent(
            "enter", SYMBOL, qty=qty, price_hint=fill_px,
            stop=stop, target=pending["tp2"],
            exit_rules=(ExitRule("stop", stop),
                        ExitRule("target", pending["tp2"])),
            reason=reason,
            side="sell" if d == -1 else "buy",
            position_intent="sell_to_open" if d == -1 else "buy_to_open",
            signal_date=session)]

    # ------------------------------------------------------------ exits
    def _exit(self, bar, qty, signed_qty, reason):
        return Intent("exit", SYMBOL, qty=float(qty),
                      price_hint=bar["c"], reason=reason,
                      side="buy" if signed_qty < 0 else "sell",
                      position_intent="buy_to_close" if signed_qty < 0
                      else "sell_to_close")

    def _manage(self, bars1m, latest, state, plan, qty_open, ctx):
        now_dt = datetime.fromtimestamp(ctx.now, tz=ET)
        d = int(plan["direction"])
        signed = qty_open
        # Hard flat first: 12:00 ET exits everything at market.
        if now_dt.time() >= FLAT_TIME:
            pnl = (latest["c"] - plan["entry"]) * signed
            state["realized_pnl"] = float(state.get("realized_pnl") or 0.0) + pnl
            state["plan"] = None
            self.last_evaluation["state"] = "flat_1200"
            return [self._exit(latest, abs(signed), signed,
                               "trullas flat 12:00 ET")]
        stop = float(plan["stop"])
        # Pessimistic ordering: stop is checked before any target the
        # same bar also spans (spec section 6).
        stop_hit = (latest["h"] >= stop) if d == -1 else (latest["l"] <= stop)
        if stop_hit:
            pnl = (stop - plan["entry"]) * signed
            state["realized_pnl"] = float(state.get("realized_pnl") or 0.0) + pnl
            state["plan"] = None
            self.last_evaluation["state"] = "stop_exit"
            return [self._exit(latest, abs(signed), signed,
                               f"trullas stop hit stop={stop:.4f}")]
        if not plan.get("tp1_done"):
            tp1 = float(plan["tp1"])
            tp1_hit = (latest["l"] <= tp1) if d == -1 else (latest["h"] >= tp1)
            if tp1_hit:
                half = abs(signed) / 2.0
                # Whole-share half: exit floor(qty/2), keep the rest.
                exit_qty = max(1, int(abs(signed)) // 2) if abs(signed) >= 2 else abs(signed)
                pnl = (tp1 - plan["entry"]) * (exit_qty if d == 1 else -exit_qty)
                state["realized_pnl"] = float(state.get("realized_pnl") or 0.0) + pnl
                if exit_qty >= abs(signed):
                    state["plan"] = None
                else:
                    plan["tp1_done"] = True
                    plan["stop"] = float(plan["entry"])  # stop to breakeven
                self.last_evaluation["state"] = "tp1_half_exit"
                return [self._exit(latest, exit_qty, signed,
                                   f"trullas TP1 half exit tp1={tp1:.4f}; stop to entry")]
        else:
            tp2 = float(plan["tp2"])
            tp2_hit = (latest["l"] <= tp2) if d == -1 else (latest["h"] >= tp2)
            if tp2_hit:
                pnl = (tp2 - plan["entry"]) * signed
                state["realized_pnl"] = float(state.get("realized_pnl") or 0.0) + pnl
                state["plan"] = None
                self.last_evaluation["state"] = "tp2_exit"
                return [self._exit(latest, abs(signed), signed,
                                   f"trullas TP2 exit tp2={tp2:.4f}")]
        self.last_evaluation["state"] = "position_open"
        return []


_INSTANCE = TrullasDivergenceSleeve()


def signal(bars, slice_state, context):
    out = _INSTANCE.signal(bars, slice_state, context)
    signal.last_evaluation = _INSTANCE.last_evaluation
    signal.trullas_state = _INSTANCE.trullas_state
    return out
