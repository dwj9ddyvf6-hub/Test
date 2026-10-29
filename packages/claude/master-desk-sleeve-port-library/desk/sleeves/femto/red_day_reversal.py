"""Red-Day Reversal — lean-desk port.

EXTRACTED from the old desk's red_day_reversal_sleeve.py. detect_washout
and its Wilder RSI (textbook SMA seed — note: DIFFERENT seeding from
rsi_meanrev's ewm seed; both preserved verbatim per sleeve) ported
exactly; plumbing is core-owned. See ports/red_day_reversal.md.

Strategy (old module): washout = day return <= -3% AND RSI(2) <= 10
AND close above the 200DMA (quality filter). Risk 0.25%/trade on a 2%
hard stop (=> ~12.5% equity notional, capped 25%/name); +4% take
profit; 3-day time exit; max 8; earnings blackout 5 days (core Gate/
Risk own blackout enforcement desk-wide; the sleeve's own check is
expressed via context.extra earnings data when present).

Inputs via context.extra:
  "sleeve_state": {SYM: {"position": {"entry_px","entry_date","qty"} | None}}
  "earnings": {SYM: "YYYY-MM-DD"|None} (absent = no sleeve-level veto)
  "universe": optional override (default: bars keys)
Bars: daily dicts {"t","o","h","l","c","v"} ascending.
"""
import math
from datetime import date as _date, datetime, timezone
from zoneinfo import ZoneInfo

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig

RED_DAY_THRESHOLD = -0.03
RSI_PERIOD = 2
RSI_MAX = 10.0
SMA_LONG = 200
RISK_FRACTION = 0.0025
STOP_PCT = 0.02
SLEEVE_NOTIONAL_CAP = 0.25
PROFIT_TARGET_PCT = 0.04
TIME_EXIT_DAYS = 3
MAX_POSITIONS = 8
EARNINGS_BLACKOUT_DAYS = 5
NO_EARNINGS_ETFS = {"QQQ", "SPY", "SOXL", "TQQQ", "VXX", "UVXY"}
ET = ZoneInfo("America/New_York")

CONFIG = SleeveConfig(
    sleeve_id="red_day_reversal", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


def _dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


def wilder_rsi(closes, period=RSI_PERIOD):
    """Verbatim old wilder_rsi (SMA-of-first-period seed)."""
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        chg = closes[i] - closes[i - 1]
        gains.append(max(chg, 0.0))
        losses.append(max(-chg, 0.0))
    avg_g = sum(gains[:period]) / period
    avg_l = sum(losses[:period]) / period
    for g, l in zip(gains[period:], losses[period:]):
        avg_g = (avg_g * (period - 1) + g) / period
        avg_l = (avg_l * (period - 1) + l) / period
    if avg_l == 0:
        return 100.0
    rs = avg_g / avg_l
    return 100.0 - (100.0 / (1.0 + rs))


def sma(closes, period):
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period


def detect_washout(bars):
    """(is_signal, day_pct, rsi2, above_sma200) — verbatim old logic on
    bar dicts. Last completed bar only."""
    if len(bars) < SMA_LONG + 2:
        return False, None, None, None
    closes = [float(b["c"]) for b in bars]
    last, prev = closes[-1], closes[-2]
    if prev <= 0:
        return False, None, None, None
    day_pct = last / prev - 1.0
    rsi = wilder_rsi(closes)
    sma200 = sma(closes, SMA_LONG)
    if rsi is None or sma200 is None:
        return False, day_pct, rsi, None
    above = last > sma200
    sig = day_pct <= RED_DAY_THRESHOLD and rsi <= RSI_MAX and above
    return sig, day_pct, rsi, above


def is_below_200dma_washout(day_pct, rsi, above):
    """Verbatim: washout criteria met, only the 200DMA filter rejects
    (Decision #92 shadow cohort — telemetry in the old desk; here it is
    simply not an entry, see port report)."""
    return (above is False and day_pct is not None and rsi is not None
            and day_pct <= RED_DAY_THRESHOLD and rsi <= RSI_MAX)


def size_shares(equity, ref_px):
    """master-desk: old size_shares verbatim — floor(0.25% risk / 2% stop),
    capped at floor(25% notional / px); 0 allowed (entry skipped)."""
    if equity is None or equity <= 0 or not ref_px or ref_px <= 0:
        return 0
    n = math.floor(equity * RISK_FRACTION / (ref_px * STOP_PCT))
    n = min(n, math.floor((equity * SLEEVE_NOTIONAL_CAP) / ref_px))
    return max(0, int(n))


def in_rth(now):
    """old in_rth: entries only 09:30-16:00 ET on weekdays (never chase)."""
    t = datetime.fromtimestamp(float(now), tz=ET)
    mins = t.hour * 60 + t.minute
    return t.weekday() < 5 and 9 * 60 + 30 <= mins < 16 * 60


def exit_due(pos, now, mark):
    """master-desk: old exit_due verbatim on the fill-relative levels the old
    promote_fills stored (target_px = fill x 1.04, stop_px = fill x 0.98) and
    the fill time; mark = a fresh intraday price (None -> only the time exit).
    Returns (reason, order_type, limit_px) or (None, None, None)."""
    fill = float(pos.get("entry_px") or 0)
    if fill > 0 and mark is not None and mark > 0:
        target_px = round(fill * (1 + PROFIT_TARGET_PCT), 2)
        stop_px = round(fill * (1 - STOP_PCT), 2)
        if mark >= target_px:
            return "profit_target_4pct", "limit", target_px
        if mark <= stop_px:
            return "hard_stop_2pct", "market", None
    opened = pos.get("opened_at")
    if opened is not None and (float(now) - float(opened)) // 86400 >= TIME_EXIT_DAYS:
        return "time_stop_3d", "market", None
    return None, None, None


def _earnings_veto(sym, today_iso, earnings):
    if sym in NO_EARNINGS_ETFS or not earnings or sym not in earnings:
        return False
    ed = earnings[sym]
    if not ed:
        return False
    try:
        delta = (_date.fromisoformat(str(ed)[:10])
                 - _date.fromisoformat(today_iso)).days
    except ValueError:
        return False
    return 0 <= delta <= EARNINGS_BLACKOUT_DAYS


class RedDayReversal(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        earnings = extra.get("earnings") or {}
        universe = extra.get("universe") or sorted(bars.keys())
        equity = float(context.equity or 0.0)
        today = context.session
        intents = []
        marks = extra.get("marks") or {}
        open_n = sum(1 for s in universe if (state.get(s) or {}).get("position")
                     or (state.get(s) or {}).get("pending_entry"))   # old _slot_count
        for sym in universe:
            bl = bars.get(sym) or []
            if len(bl) < SMA_LONG + 2:
                continue
            st = state.get(sym) or {}
            pos = st.get("position")
            last_px = float(bl[-1]["c"])
            dates = _dates(bl)
            if pos:
                qty = int(float(pos.get("qty") or 0))
                if qty <= 0:
                    continue
                # old manage_positions: hourly, on a fresh intraday mark
                why, otype, lpx = exit_due(pos, context.now, marks.get(sym))
                if why:
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty, price_hint=lpx or marks.get(sym),
                        order=({"type": "limit", "limit_price": lpx} if otype == "limit" else None),
                        reason="red_day_reversal exit: %s mark=%s entry=%.2f"
                               % (why, marks.get(sym), float(pos.get("entry_px") or 0))))
                continue
            if open_n >= MAX_POSITIONS or equity <= 0:
                continue
            sig, day_pct, rsi, above = detect_washout(bl)
            if not sig:
                continue
            if _earnings_veto(sym, today, earnings):
                continue
            qty = size_shares(equity, last_px)
            if qty <= 0 or not in_rth(context.now):
                continue                  # old: zero shares skipped; RTH entries only
            stop_px = round(last_px * (1 - STOP_PCT), 2)
            close_et = datetime.fromtimestamp(float(context.now), tz=ET).replace(hour=16, minute=0, second=0,
                                                                                 microsecond=0)
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(last_px, 2),
                stop=stop_px,
                exit_rules=(ExitRule("stop", stop_px),
                            ExitRule("target", round(last_px * (1 + PROFIT_TARGET_PCT), 2)),
                            ExitRule("time_bars", float(TIME_EXIT_DAYS))),
                # old _submit_entry: a LIMIT buy at the last close (never chase), a day order
                order={"type": "limit", "limit_price": round(last_px, 2), "not_after": close_et.timestamp()},
                reason="red_day_reversal washout: day=%.4f rsi2=%.2f above200=%s"
                       % (day_pct, rsi, above)))
            open_n += 1
        return intents


def _sessions_since(dates, entry_date):
    try:
        return len(dates) - 1 - dates.index(entry_date)
    except ValueError:
        return 0


def signal(bars, slice_state, context):
    return RedDayReversal().signal(bars, slice_state, context)
