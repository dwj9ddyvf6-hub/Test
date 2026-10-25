"""RSI Mean Reversion (equity) — lean-desk port.

EXTRACTED from the old desk's rsi_meanrev_sleeve.py. The Wilder RSI is
ported with the old code's exact seeding (pandas ewm alpha=1/period,
adjust=False — first output equals first input, NOT the textbook SMA
seed); plumbing is core-owned. See ports/rsi_meanrev.md.

Strategy (frozen SPEC 2026-10-09, restored in full by R-PB1
2026-10-16 after AUDIT3 found the port had dropped D1-D5/D7):
entry when RSI(2) < 10 (strict) on the last closed bar AND the
close is above the 200-day SMA — the Connors trend filter; fail
closed when fewer than 200 bars make the average uncomputable.
Entries are also vetoed inside the Decision #8 earnings window
(earnings day and the 3 days before; fail closed on a stale or
unserved calendar). Exits, first trigger wins (the source's
precedence): close above the 5-day SMA (primary), RSI(2) > 70
(backup), +5% profit target, -8% stop (in-signal, close-evaluated
— core/protection.py lists this sleeve's stop as never a broker
stop), 5-trading-day time stop. Risk 0.25%/trade; max 8 positions
(desk-wide 10 is core Risk's).

Inputs via context.extra:
  "sleeve_state": {SYM: {"position": {"entry_px","entry_date","qty"} | None}}
  "universe": optional override (default: bars keys; the old sleeve
              used the 42-name basket.json)
  "earnings": {SYM: "YYYY-MM-DD"|None} and "earnings_fresh": bool
              (served by core/bars_universe from the desk EDGAR
              calendar; absent or stale fails entries closed)
Bars: daily dicts {"t","o","h","l","c","v"} ascending.
"""
import math
from datetime import date, datetime, timezone

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

RSI_PERIOD = 2
RSI_OVERSOLD = 10.0
RSI_OVERBOUGHT = 70.0
MA200_PERIOD = 200    # 200-day SMA trend filter: entries only in uptrend
MA5_PERIOD = 5        # 5-day SMA: primary exit (Connors' original)
PROFIT_TARGET = 0.05
TIME_STOP_DAYS = 5
STOP_LOSS = 0.08
RISK_FRACTION = 0.0025
MAX_POSITIONS = 8
EARNINGS_BLACKOUT_DAYS = 3  # Decision #8: earnings day + 3 days before

CONFIG = SleeveConfig(
    sleeve_id="rsi_meanrev", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


def _dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


def rsi_wilder_last(closes, period=RSI_PERIOD):
    """Last value of the old rsi_wilder series (pandas ewm semantics):
    avg seeded y0 = x0, then avg = avg + alpha*(x - avg); defined once
    `period` deltas exist (min_periods=period). No losses -> 100;
    no movement -> 50. Returns None when not yet defined."""
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    alpha = 1.0 / period
    ag = al = None
    for i, d in enumerate(deltas):
        g = max(d, 0.0)
        l = max(-d, 0.0)
        if ag is None:
            ag, al = g, l
        else:
            ag = ag + alpha * (g - ag)
            al = al + alpha * (l - al)
        if i + 1 < period:
            last = None
            continue
        if al == 0 and ag > 0:
            last = 100.0
        elif ag == 0 and al == 0:
            last = 50.0
        elif al == 0:
            last = 100.0
        else:
            last = 100.0 - 100.0 / (1.0 + ag / al)
    return last


def _sma_last(closes, period):
    """Simple average of the last `period` closes; None when the
    window is short or any member is non-finite (the average cannot
    be computed — callers fail closed on entries, degrade on exits,
    exactly the source's posture)."""
    if len(closes) < period:
        return None
    window = closes[-period:]
    if not all(math.isfinite(c) for c in window):
        return None
    return sum(window) / period


def _earnings_veto(sym, session_iso, earnings, fresh):
    """Decision #8 veto (the source's _earnings_ok): a stale or
    unserved calendar fails closed; an unknown symbol fails closed
    (a missing calendar entry means UNKNOWN, not 'no earnings');
    a confirmed date vetoes from 3 days before through earnings
    day. Returns a reason string or None."""
    if not fresh:
        return "stale_calendar"
    if sym not in earnings:
        return "unknown_date"
    ed = earnings[sym]
    if ed is None:
        return None
    try:
        delta = (date.fromisoformat(str(ed)[:10])
                 - date.fromisoformat(session_iso)).days
    except ValueError:
        return "unknown_date"
    return "blackout_window" if 0 <= delta <= EARNINGS_BLACKOUT_DAYS \
        else None


def size_qty(equity, ref_px):
    """Verbatim old size_qty: risk budget / 8% stop distance, floored
    to whole shares, 0 on bad input or when the budget buys nothing
    (the old caller skips qty <= 0). NO 1-share minimum — the old code
    removed the forced floor as a HIGH bugfix on 2026-10-09 (it ordered
    a share when the 0.25% risk budget computed 0, breaching the risk
    rail); the lean port reintroduced it (P3 audit 2026-10-15)."""
    if not ref_px or ref_px <= 0 or not equity or equity <= 0:
        return 0
    return int((equity * RISK_FRACTION) / (STOP_LOSS * ref_px))


def sma5_exit_removed_enabled(extra):
    """ENH-rsi_meanrev (Edge IMPROVE, Group B / ruling D3): context
    .extra["rsi_meanrev_improve"]["sma5_exit_removed"], default ON;
    OFF restores the pre-change exit stack exactly (control - the
    frozen Connors SPEC, SMA5 first trigger included)."""
    ov = (extra or {}).get("rsi_meanrev_improve")
    if isinstance(ov, dict) and "sma5_exit_removed" in ov:
        return bool(ov["sma5_exit_removed"])
    return True


class RsiMeanRev(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        universe = extra.get("universe") or sorted(bars.keys())
        equity = float(context.equity or 0.0)
        earnings = extra.get("earnings") or {}
        earnings_fresh = bool(extra.get("earnings_fresh"))
        intents = []
        open_n = sum(1 for s in universe if (state.get(s) or {}).get("position"))
        for sym in universe:
            bl = bars.get(sym) or []
            if not bl:
                continue
            st = state.get(sym) or {}
            pos = st.get("position")
            closes = [float(b["c"]) for b in bl]
            last_px = closes[-1]
            if not math.isfinite(last_px):
                continue
            dates = _dates(bl)
            if pos:
                qty = int(float(pos.get("qty") or 0))
                if qty <= 0:
                    continue
                entry_px = float(pos.get("entry_px") or last_px)
                held = _sessions_since(dates, pos.get("entry_date")) \
                    if pos.get("entry_date") else 0
                # Exits are never gated (the source manages on the
                # delivered bars, however many there are). First
                # trigger wins, in the source's precedence.
                rsi = rsi_wilder_last(closes)
                sma5 = _sma_last(closes, MA5_PERIOD)
                trigger = None
                # ENH (IMPROVE-rsi_meanrev section 2, SPEC departure
                # D3): the SMA5 first-trigger exit is deleted under
                # the switch - the position is managed to +5% /
                # RSI(2) > 70 / -8% / the 5-day clock. With the switch
                # OFF the original stack runs byte-identically
                # (control).
                if not sma5_exit_removed_enabled(extra) \
                        and sma5 is not None and last_px > sma5:
                    trigger = "sma5_exit"
                elif rsi is not None and math.isfinite(rsi) \
                        and rsi > RSI_OVERBOUGHT:
                    trigger = "rsi_overbought"
                elif last_px >= entry_px * (1 + PROFIT_TARGET):
                    trigger = "profit_target"
                elif last_px <= entry_px * (1 - STOP_LOSS):
                    trigger = "stop_loss_market"
                elif held >= TIME_STOP_DAYS:
                    trigger = "time_stop"
                if trigger is not None:
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty, price_hint=round(last_px, 2),
                        reason="rsi_meanrev exit: %s px=%.2f entry=%.2f held=%d"
                               % (trigger, last_px, entry_px, held)))
                continue
            if open_n >= MAX_POSITIONS or equity <= 0:
                continue
            # Entry, the source's order: oversold first, then the
            # trend filter (fail closed under 200 bars), then the
            # earnings veto.
            rsi = rsi_wilder_last(closes)
            if rsi is None or not math.isfinite(rsi) \
                    or rsi >= RSI_OVERSOLD:
                continue  # not oversold (strict <, D5)
            sma200 = _sma_last(closes, MA200_PERIOD)
            if sma200 is None:
                continue  # average uncomputable: fail closed (D2)
            if last_px <= sma200:
                continue  # below the trend filter (D1)
            if _earnings_veto(sym, context.session, earnings,
                              earnings_fresh):
                continue  # Decision #8 window / stale calendar (D7)
            qty = size_qty(equity, last_px)
            if qty <= 0:
                continue  # old caller: entry skipped on qty <= 0
            stop_px = round(last_px * (1 - STOP_LOSS), 2)
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(last_px, 2),
                stop=stop_px,
                exit_rules=(ExitRule("stop", stop_px),
                            ExitRule("target", round(last_px * (1 + PROFIT_TARGET), 2)),
                            ExitRule("time_bars", float(TIME_STOP_DAYS))),
                reason="rsi_meanrev entry: RSI(2)=%.2f < %.1f"
                       % (rsi, RSI_OVERSOLD)))
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
    return RsiMeanRev().signal(bars, slice_state, context)
