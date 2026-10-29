"""EMA-VWAP (equity) — lean-desk port.

EXTRACTED from the old desk's ema_vwap_sleeve.py. Pure decision logic
verbatim in behavior (the pandas indicators re-expressed on bar lists;
outcomes identical); plumbing is core-owned. See ports/ema_vwap.md.

Strategy (old module): 20-day rolling VWAP anchor (typical price,
zero-volume bars excluded as NaN in the old code). Entry: last closed
close >= 2% below the VWAP. Exits: reversion to/above VWAP, +5% profit
target, -8% hard stop, 5-trading-day time stop, -25% disaster stop
(Decision #18). Risk 0.25%/trade; max 8; sleeve notional cap 25%;
per-position notional cap 5%.

Inputs via context.extra:
  "sleeve_state": {SYM: {"position": {"entry_px","entry_date","qty"} | None}}
  "universe": optional override (default: bars keys)
Bars: daily dicts {"t","o","h","l","c","v"} ascending.
"""
import math
from datetime import date, datetime, timedelta, timezone

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig

DEV_PCT = 0.02
PROFIT_TARGET = 0.05
STOP_LOSS = 0.08
TIME_STOP_DAYS = 5
RISK_FRACTION = 0.0025
MAX_POSITIONS = 8
SLEEVE_NOTIONAL_CAP = 0.25
POS_NOTIONAL_CAP = 0.05
DISASTER_STOP = 0.25
WARMUP_BARS = 30
VWAP_WINDOW = 20

CONFIG = SleeveConfig(
    sleeve_id="ema_vwap", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


def _dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


def rolling_vwap(bars, window=VWAP_WINDOW):
    """20-bar rolling VWAP, old add_indicators semantics: typical price
    (h+l+c)/3, zero-volume bars contribute NaN (excluded from both sums
    only via their tp*v term being NaN — pandas sum skips NaN; a fully
    NaN window yields NaN). Returns None until `window` bars exist."""
    if len(bars) < window:
        return None
    num = 0.0
    den = 0.0
    for b in bars[-window:]:
        v = float(b["v"])
        if v == 0:
            # master-desk: pandas rolling(20).sum() is NaN when ANY of the 20
            # values is NaN (min_periods = window) — the old vol.replace(0, NaN)
            # makes a zero-volume bar void the whole window's VWAP.
            return None
        tp = (float(b["h"]) + float(b["l"]) + float(b["c"])) / 3.0
        num += tp * v
        den += v
    if den <= 0:
        return None
    return num / den


def deviation_below(bars, pct=DEV_PCT):
    """Verbatim old deviation_below: needs >= 21 bars; last close strictly
    below vwap*(1-pct)."""
    if len(bars) < 21:
        return False
    v = rolling_vwap(bars)
    c = float(bars[-1]["c"])
    if v is None or not math.isfinite(v) or v <= 0:
        return False
    return bool(c < v * (1.0 - pct))


def reverted_to_vwap(bars):
    if len(bars) < 21:
        return False
    v = rolling_vwap(bars)
    c = float(bars[-1]["c"])
    if v is None or not math.isfinite(v) or v <= 0:
        return False
    return bool(c >= v)


def size_qty(equity, ref_px):
    """master-desk: old size_qty verbatim — 0.25% risk budget on the fixed
    8% stop distance, capped at 5% of equity notional, floored to whole
    shares, 0 allowed (entry skipped)."""
    stop_dist = (ref_px or 0) * STOP_LOSS
    if not ref_px or ref_px <= 0 or not stop_dist or stop_dist <= 0:
        return 0
    raw = equity * RISK_FRACTION / stop_dist
    cap = equity * POS_NOTIONAL_CAP / ref_px
    return max(0, int(min(raw, cap)))


def weekdays_held(entry_date, today):
    """master-desk: the old manage_position count — weekdays in
    (entry_date, today], holidays NOT excluded (the old approximation)."""
    try:
        d0, d1 = date.fromisoformat(str(entry_date)[:10]), date.fromisoformat(str(today)[:10])
    except ValueError:
        return 0
    return sum(1 for i in range((d1 - d0).days) if (d0 + timedelta(days=i + 1)).weekday() < 5)


class EmaVwap(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        universe = extra.get("universe") or sorted(bars.keys())
        equity = float(context.equity or 0.0)
        intents = []
        open_n = sum(1 for s in universe if (state.get(s) or {}).get("position")
                     or (state.get(s) or {}).get("pending_entry"))   # old count_positions
        sleeve_notional = 0.0
        for s in universe:
            p = (state.get(s) or {}).get("position")
            if p:   # old sleeve_notional: qty x the entry's signal close (ref_px)
                sleeve_notional += float(p.get("ref_px") or p.get("entry_px") or 0) * float(p.get("qty") or 0)
        for sym in universe:
            bl = bars.get(sym) or []
            if len(bl) < WARMUP_BARS + 1:      # old daily_pass: < WARMUP+1 bars -> symbol untradeable
                continue
            st = state.get(sym) or {}
            pos = st.get("position")
            last_px = float(bl[-1]["c"])
            dates = _dates(bl)
            if pos:
                qty = int(float(pos.get("qty") or 0))
                if qty <= 0:
                    continue
                if pos.get("entry_date") and dates[-1] < str(pos["entry_date"])[:10]:
                    # master-desk: the spec's exits run "from entry"; a bar that closed before the fill says nothing
                    # about the position (the old desk's hourly pass sold gap-down entries at once: 2026-10-16, 6 of 6)
                    continue
                entry_px = float(pos.get("entry_px") or last_px)
                held = weekdays_held(pos.get("entry_date"), context.session) \
                    if pos.get("entry_date") else 0
                hit_target = last_px >= entry_px * (1 + PROFIT_TARGET)
                hit_stop = last_px <= entry_px * (1 - STOP_LOSS)
                if reverted_to_vwap(bl) or hit_target or hit_stop \
                        or held >= TIME_STOP_DAYS:
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty, price_hint=round(last_px, 2),
                        reason="ema_vwap exit: reverted=%s target=%s stop=%s held=%d"
                               % (reverted_to_vwap(bl), hit_target, hit_stop, held)))
                continue
            if open_n >= MAX_POSITIONS or equity <= 0:
                continue
            if deviation_below(bl):
                if st.get("last_exit_date") and context.session <= str(st["last_exit_date"]):
                    continue                  # old de-overlap: never re-enter on/before the last exit day
                qty = size_qty(equity, last_px)
                if qty <= 0 or sleeve_notional + qty * last_px > SLEEVE_NOTIONAL_CAP * equity:
                    continue
                stop_px = round(last_px * (1 - DISASTER_STOP), 2)
                intents.append(Intent(
                    "enter", sym, qty_hint=qty, price_hint=round(last_px, 2),
                    stop=stop_px,
                    exit_rules=(ExitRule("stop", stop_px),
                                ExitRule("target", round(last_px * (1 + PROFIT_TARGET), 2)),
                                ExitRule("time_bars", float(TIME_STOP_DAYS))),
                    reason="ema_vwap deviation: close=%.2f vwap20=%.4f"
                           % (last_px, rolling_vwap(bl)),
                    position_meta={"ref_px": round(last_px, 2)}))
                open_n += 1
                sleeve_notional += qty * last_px
        return intents


def _sessions_since(dates, entry_date):
    try:
        return len(dates) - 1 - dates.index(entry_date)
    except ValueError:
        return 0


def signal(bars, slice_state, context):
    return EmaVwap().signal(bars, slice_state, context)
