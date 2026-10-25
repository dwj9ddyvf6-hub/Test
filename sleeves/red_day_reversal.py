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

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

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
    """Verbatim old size_shares: risk budget / 2% stop, capped at 25%
    of equity notional per name, floored to whole shares — 0 on bad
    input or when the budget buys nothing (old semantics; NO 1-share
    minimum — the lean port's forced floor reintroduced the risk-rail
    breach the old desk removed, P3 audit 2026-10-15)."""
    if equity is None or equity <= 0 or not ref_px or ref_px <= 0:
        return 0
    n = math.floor(equity * RISK_FRACTION / (ref_px * STOP_PCT))
    n = min(n, math.floor((equity * SLEEVE_NOTIONAL_CAP) / ref_px))
    return max(0, int(n))


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


def range_within_target_gate_enabled(extra):
    """ENH-red_day_reversal (Edge IMPROVE, Group A): context.extra
    ["red_day_reversal_improve"]["range_within_target_gate"], default
    ON; OFF restores the pre-change entry rule exactly (control)."""
    ov = (extra or {}).get("red_day_reversal_improve")
    if isinstance(ov, dict) and "range_within_target_gate" in ov:
        return bool(ov["range_within_target_gate"])
    return True


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
        open_n = sum(1 for s in universe if (state.get(s) or {}).get("position"))
        for sym in universe:
            bl = bars.get(sym) or []
            st = state.get(sym) or {}
            pos = st.get("position")
            if pos:
                # D-B6 cure (2026-10-22): exit evaluation runs on
                # however many bars are delivered — the 202-bar
                # entry minimum must not gate a held position's
                # profit/stop/time exits (exit math needs only
                # entry_px + last close + dates).
                if not bl:
                    continue
                last_px = float(bl[-1]["c"])
                dates = _dates(bl)
                qty = int(float(pos.get("qty") or 0))
                if qty <= 0:
                    continue
                entry_px = float(pos.get("entry_px") or last_px)
                held = _sessions_since(dates, pos.get("entry_date")) \
                    if pos.get("entry_date") else 0
                if last_px >= entry_px * (1 + PROFIT_TARGET_PCT) \
                        or last_px <= entry_px * (1 - STOP_PCT) \
                        or held >= TIME_EXIT_DAYS:
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty, price_hint=round(last_px, 2),
                        reason="red_day_reversal exit: px=%.2f entry=%.2f held=%d"
                               % (last_px, entry_px, held)))
                continue
            if len(bl) < SMA_LONG + 2:
                continue
            last_px = float(bl[-1]["c"])
            if open_n >= MAX_POSITIONS or equity <= 0:
                continue
            sig, day_pct, rsi, above = detect_washout(bl)
            if not sig:
                continue
            # ENH (IMPROVE-red_day_reversal section 2): refuse the
            # entry when the washout day's own range - (high - low) /
            # last close of the signal bar, values detect_washout
            # already reads - exceeds the sleeve's coded +4% profit
            # target: the day's demonstrated noise band is wider than
            # everything the trade can gain.
            if range_within_target_gate_enabled(extra):
                _sig_bar = bl[-1]
                _range_pct = (float(_sig_bar["h"]) - float(_sig_bar["l"])) \
                    / last_px if last_px > 0 else 0.0
                if _range_pct > PROFIT_TARGET_PCT:
                    continue
            if _earnings_veto(sym, today, earnings):
                continue
            qty = size_shares(equity, last_px)
            if qty <= 0:
                continue  # risk budget buys nothing: no entry (old semantics)
            stop_px = round(last_px * (1 - STOP_PCT), 2)
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(last_px, 2),
                stop=stop_px,
                exit_rules=(ExitRule("stop", stop_px),
                            ExitRule("target", round(last_px * (1 + PROFIT_TARGET_PCT), 2)),
                            ExitRule("time_bars", float(TIME_EXIT_DAYS))),
                reason="red_day_reversal washout: day=%.4f rsi2=%.2f above200=%s"
                       % (day_pct, rsi, above)))
            open_n += 1
        return intents


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
    return RedDayReversal().signal(bars, slice_state, context)
