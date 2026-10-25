"""Donchian (equity) — lean-desk port.

EXTRACTED from the old desk's donchian_sleeve.py (SPEC: desk/sleeves/
donchian/SPEC.md). Pure decision logic verbatim in behavior; plumbing
(broker, cids, files, desk gates) is core-owned. See ports/donchian.md.

Strategy (old module docstring):
  Entry: close > max(high[t-20..t-1]) (20-day Donchian breakout).
  Exits: close < min(low[t-10..t-1]) (10-day exit channel); ATR(14)
  trailing stop at 2.0x ATR; 20-trading-day time stop; -25% GTC disaster
  stop (desk norm, Decision #18).
  Risk: 0.25% equity/trade (RISK_FRACTION); max 8 positions; sleeve
  notional cap 25% of equity.

Inputs via context.extra:
  "sleeve_state": {SYM: {"position": {"entry_px","entry_date","qty",
                    "atr"} | None}}
  "universe": optional override list (default: the desk basket passed
                    as bars keys — the old sleeve read basket.json)
Bars: daily dicts {"t","o","h","l","c","v"} ascending.

ENH (IMPROVE-donchian, Edge program 2026-10-24): the 20-session time
stop is conditioned on profitability — at >= HOLD_DAYS sessions it
fires only when the last close is at or below the position's entry
price; a profitable position lives under the channel and ATR-trail
exits alone (re-tested every pass). Switched by
context.extra["donchian_improve"]["time_stop_profit_gate"] (default
ON; OFF restores the pre-change unconditional time stop exactly).
Every position reaching the time-stop test records a paired
control/treatment record on self.last_evaluation["enhance_exp"].
"""
import math
from datetime import datetime, timezone

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

ENTRY_CHANNEL = 20     # breakout: close > max(high, last 20)
EXIT_CHANNEL = 10      # exit: close < min(low, last 10)
WARMUP_BARS = 25
ATR_PERIOD = 14
ATR_MULT = 2.0         # trailing stop distance
HOLD_DAYS = 20         # time stop
DISASTER_STOP = 0.25
RISK_FRACTION = 0.0025
MAX_POSITIONS = 8
SLEEVE_NOTIONAL_CAP = 0.25

CONFIG = SleeveConfig(
    sleeve_id="donchian", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"},
    risk_pct=RISK_FRACTION)


def _dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


def calc_atr(bars, period=ATR_PERIOD):
    """Wilder's ATR — verbatim port of the old calc_atr."""
    if len(bars) < period + 1:
        return None
    trs = []
    for i in range(1, len(bars)):
        h, l, pc = float(bars[i]["h"]), float(bars[i]["l"]), float(bars[i - 1]["c"])
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    atr = sum(trs[:period]) / period
    for tr in trs[period:]:
        atr = (atr * (period - 1) + tr) / period
    return atr


def entry_signal(bars):
    """True when the last closed bar breaks the 20-day high channel."""
    if len(bars) < ENTRY_CHANNEL + 1:
        return False
    c = float(bars[-1]["c"])
    if not math.isfinite(c):
        return False
    # SPEC + old detect_breakout (donchian_sleeve.py:910): the breakout
    # bar itself must have traded — volume > 0. (Repair 2026-10-15 P3:
    # the port dropped this condition.)
    try:
        if not float(bars[-1].get("v") or 0) > 0:
            return False
    except (TypeError, ValueError):
        return False
    prior = [float(b["h"]) for b in bars[-ENTRY_CHANNEL - 1:-1]]
    if not all(math.isfinite(x) for x in prior):
        return False
    return c > max(prior)


def exit_channel_hit(bars):
    """True when the last closed bar breaks the 10-day low channel."""
    if len(bars) < EXIT_CHANNEL + 1:
        return False
    c = float(bars[-1]["c"])
    prior = [float(b["l"]) for b in bars[-EXIT_CHANNEL - 1:-1]]
    if not all(math.isfinite(x) for x in prior):
        return False
    return c < min(prior)


def atr_trail_level(bars, entry_date=None):
    """The ATR trailing-stop LEVEL the exit test uses (SPEC:
    trailing stop at ATR_MULT x ATR below the price): the highest
    close from entry through the PREVIOUS bar minus ATR_MULT x
    ATR(14) computed on bars through the previous bar — only bars
    closed before the decision bar set the level (no lookahead).
    None when the level is not computable. LC-6 (2026-10-18): this
    is the ONE computation of the level — atr_trail_hit tests it
    and the exit reason prints it (the ported reason printed
    last close - ATR_MULT x ATR(current bars) instead, a figure
    no test ever used)."""
    if len(bars) < ATR_PERIOD + 2:
        return None
    start = 0
    if entry_date:
        dates = _dates(bars)
        try:
            start = dates.index(entry_date)
        except ValueError:
            start = 0
    window = bars[start:]
    if len(window) < 2:
        return None
    atr_prev = calc_atr(bars[:-1])
    if not atr_prev:
        return None
    return max(float(b["c"]) for b in window[:-1]) - ATR_MULT * atr_prev


def atr_trail_hit(bars, entry_date=None):
    """True when the last bar reaches the ATR trailing stop.
    Repair 2026-10-15 (census2 batch 1): the ported code computed
    a trail figure for the exit reason string but never tested
    it, so this documented exit could never fire."""
    level = atr_trail_level(bars, entry_date)
    if level is None:
        return False
    last = bars[-1]
    return float(last["l"]) <= level or float(last["c"]) <= level


def size_qty(equity, ref_px, atr):
    """Risk-sized qty: risk budget / (ATR_MULT x ATR); never
    negative. OBS-1 (ruling 2026-10-22): no 1-share minimum —
    a risk budget that sizes to zero takes no position, and
    bad inputs size to zero (fail closed), never to a share."""
    if not atr or atr <= 0 or not ref_px or ref_px <= 0:
        return 0
    qty = int((equity * RISK_FRACTION) // (ATR_MULT * atr))
    return max(0, qty)


class Donchian(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        universe = extra.get("universe") or sorted(bars.keys())
        equity = float(context.equity or 0.0)
        today = context.session
        intents = []
        open_n = sum(1 for s in universe
                     if (state.get(s) or {}).get("position"))
        # Sleeve notional already committed (old check_sleeve_notional_cap
        # is cumulative sleeve-wide, donchian_sleeve.py:801): held
        # positions at entry price (last close as fallback) plus this
        # pass's staged entries count against the 25% cap. (Repair
        # 2026-10-15 P3: the port checked only the single new order and
        # only when a position was already open, so the stated cap was
        # never actually enforced.)
        used_notional = 0.0
        for s in universe:
            p = (state.get(s) or {}).get("position")
            if not p:
                continue
            try:
                ref = float(p.get("entry_px") or 0) or float(
                    (bars.get(s) or [{}])[-1].get("c") or 0)
                used_notional += int(float(p.get("qty") or 0)) * ref
            except (TypeError, ValueError):
                continue
        pass_adds = 0.0
        gate_on = time_stop_profit_gate_enabled(extra)
        exp_records = []
        for sym in universe:
            bl = bars.get(sym) or []
            st = state.get(sym) or {}
            pos = st.get("position")
            # READINESS-20261022 F-A5: exits need only the exit
            # channel (11 bars) / ATR trail (~15); the 25-bar
            # warmup guards ENTRIES only (D-B6 shape).
            if pos:
                if len(bl) < EXIT_CHANNEL + 1:
                    continue
            elif len(bl) < WARMUP_BARS:
                continue
            dates = _dates(bl)
            last_px = float(bl[-1]["c"])
            if pos:
                qty = int(float(pos.get("qty") or 0))
                if qty <= 0:
                    continue
                # exits: channel break, ATR trail, or time stop
                # LC-6: the reason's atr_trail= figure is the level
                # atr_trail_hit actually tests, from the one
                # computation of it (atr_trail_level).
                trail = atr_trail_level(bl, pos.get("entry_date"))
                held = _sessions_since(dates, pos["entry_date"]) \
                    if pos.get("entry_date") and dates else 0
                try:
                    entry_px_f = float(pos.get("entry_px"))
                except (TypeError, ValueError):
                    entry_px_f = None
                due_control = time_stop_fires(held, last_px, entry_px_f,
                                              gate_on=False)
                due = time_stop_fires(held, last_px, entry_px_f,
                                      gate_on=gate_on)
                if due_control or due:
                    exp_records.append({
                        "symbol": sym, "sessions_held": held,
                        "close": last_px, "entry_px": entry_px_f,
                        "control_time_exit": bool(due_control),
                        "treatment_time_exit": bool(due),
                        "switch_on": gate_on})
                trail_hit = atr_trail_hit(bl, pos.get("entry_date"))
                if exit_channel_hit(bl) or trail_hit or due:
                    rules = (ExitRule("stop",
                                      round(float(pos["entry_px"]) *
                                            (1 - DISASTER_STOP), 2)),)
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty, price_hint=round(last_px, 2),
                        exit_rules=rules,
                        reason="donchian exit: channel=%s trail_hit=%s time_due=%s atr_trail=%s"
                               % (exit_channel_hit(bl), trail_hit, bool(due),
                                  None if trail is None else round(trail, 2))))
                continue
            if open_n >= MAX_POSITIONS or equity <= 0:
                continue
            if entry_signal(bl):
                atr = calc_atr(bl)
                qty = size_qty(equity, last_px, atr)
                if qty < 1:
                    continue  # OBS-1: sized to zero — no position
                if (used_notional + pass_adds + qty * last_px
                        > SLEEVE_NOTIONAL_CAP * equity):
                    continue
                stop_px = round(last_px * (1 - DISASTER_STOP), 2)
                intents.append(Intent(
                    "enter", sym, qty_hint=qty, price_hint=round(last_px, 2),
                    stop=stop_px,
                    exit_rules=(ExitRule("stop", stop_px),
                                ExitRule("time_bars", float(HOLD_DAYS)),
                                ExitRule("trailing_pct", 0.0)),
                    reason="donchian 20d breakout: close=%.2f atr=%s"
                           % (last_px, None if atr is None else round(atr, 4))))
                open_n += 1
                pass_adds += qty * last_px
        if exp_records:
            self.last_evaluation = {"enhance_exp": {
                "exp_id": EXP_ID, "switch_on": gate_on,
                "records": exp_records}}
        return intents


# ------------------------------------------------------------ ENH experiment
EXP_ID = "ENH-DONCHIAN-20261024"

def time_stop_profit_gate_enabled(extra):
    ov = (extra or {}).get("donchian_improve")
    if isinstance(ov, dict) and "time_stop_profit_gate" in ov:
        return bool(ov["time_stop_profit_gate"])
    return True

def time_stop_fires(sessions_held, close, entry_px, gate_on=True):
    """Time-stop decision: due at >= HOLD_DAYS sessions; with the ENH
    gate ON a profitable close (close > entry price) does not fire."""
    if sessions_held is None or sessions_held < HOLD_DAYS:
        return False
    if gate_on and entry_px is not None and close > entry_px:
        return False
    return True

def _sessions_since(dates, entry_date):
    """Sessions elapsed since entry: the count of delivered dates
    strictly after the entry date (the old counting law). Identical
    to the index form whenever the entry bar is in the list; the
    index form returned 0 when the entry bar had aged out of the
    delivered window, silently disabling the time exit (P3 audit
    2026-10-15, coordinator consistency cure — same class as the
    cyan-family sessions_since cure)."""
    entry = str(entry_date)[:10]
    return sum(1 for d in dates if str(d)[:10] > entry)


def signal(bars, slice_state, context):
    return Donchian().signal(bars, slice_state, context)
