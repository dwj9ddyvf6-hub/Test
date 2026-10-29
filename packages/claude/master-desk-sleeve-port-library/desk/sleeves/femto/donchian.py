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
"""
import math
from datetime import datetime, timezone

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig

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
    if float(bars[-1].get("v") or 0) <= 0:   # master-desk: old detect_breakout requires volume > 0
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


def size_qty(equity, ref_px, atr=None):
    """master-desk: the old size_qty verbatim — 0.25% risk on the 25%
    disaster-stop distance, capped at the 25% notional (the femto port
    sized on 2 x ATR, which is not the SPEC's rule). atr is unused."""
    risk_amt = equity * RISK_FRACTION
    risk_per_share = (ref_px or 0) * DISASTER_STOP
    if risk_per_share <= 0:
        return 0
    qty = int(risk_amt / risk_per_share)
    max_qty = int((equity * SLEEVE_NOTIONAL_CAP) / ref_px) if ref_px > 0 else 0
    return min(qty, max_qty)


def trail_level(bars, entry_date, entry_px, window=100):
    """master-desk: the old ratcheting ATR trail, recomputed purely from
    bars — initial fill x 0.96, then each daily pass after the entry
    ratchets max(trail, close - ATR_MULT x ATR(14)) on the bar window
    the old pass fetched (100 bars). Never loosens."""
    trail = round(float(entry_px) * 0.96, 2) if entry_px else None
    dates = _dates(bars)
    for k in range(len(bars)):
        if dates[k] < str(entry_date):
            continue
        atr = calc_atr(bars[max(0, k + 1 - window):k + 1])
        if atr is None:
            continue
        new = float(bars[k]["c"]) - ATR_MULT * atr
        trail = new if trail is None else max(trail, new)
    return trail


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
                     if (state.get(s) or {}).get("position")
                     or (state.get(s) or {}).get("pending_entry"))
        used = sum(float((state.get(s) or {}).get("position", {}).get("qty") or 0)
                   * float((state.get(s) or {}).get("position", {}).get("entry_px") or 0)
                   for s in universe if (state.get(s) or {}).get("position"))
        for sym in universe:
            bl = bars.get(sym) or []
            if len(bl) < WARMUP_BARS:
                continue
            st = state.get(sym) or {}
            pos = st.get("position")
            dates = _dates(bl)
            last_px = float(bl[-1]["c"])
            if pos:
                qty = int(float(pos.get("qty") or 0))
                if qty <= 0:
                    continue
                # exits: channel break, ATR trail, or time stop (old
                # check_exit order; the trail is the old ratchet)
                trail = trail_level(bl, pos.get("entry_date") or "",
                                    pos.get("entry_px"))
                trail_hit = trail is not None and float(bl[-1]["l"]) <= trail
                due = pos.get("entry_date") and dates and \
                    sum(1 for d in dates if d > str(pos["entry_date"])) >= HOLD_DAYS
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
                if qty <= 0 or used + qty * last_px > SLEEVE_NOTIONAL_CAP * equity:
                    continue                 # old check_sleeve_notional_cap (sleeve-wide)
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
        return intents


def _sessions_since(dates, entry_date):
    try:
        return len(dates) - 1 - dates.index(entry_date)
    except ValueError:
        return 0


def signal(bars, slice_state, context):
    return Donchian().signal(bars, slice_state, context)
