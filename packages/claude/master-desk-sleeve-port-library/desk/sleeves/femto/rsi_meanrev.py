"""RSI Mean Reversion (equity) — lean-desk port.

EXTRACTED from the old desk's rsi_meanrev_sleeve.py. The Wilder RSI is
ported with the old code's exact seeding (pandas ewm alpha=1/period,
adjust=False — first output equals first input, NOT the textbook SMA
seed); plumbing is core-owned. See ports/rsi_meanrev.md.

Strategy (old module): entry when RSI(2) <= 10 on the last closed bar
(oversold washout mean-reversion). Exits: +5% profit target, -8% GTC
stop (Decision #18 convention), 5-trading-day time stop. Risk
0.25%/trade; max 8 positions (desk-wide 10 is core Risk's).

Inputs via context.extra:
  "sleeve_state": {SYM: {"position": {"entry_px","entry_date","qty"} | None}}
  "universe": optional override (default: bars keys; the old sleeve
              used the 42-name basket.json)
Bars: daily dicts {"t","o","h","l","c","v"} ascending.
"""
import math
from datetime import datetime, timezone

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig

RSI_PERIOD = 2
RSI_OVERSOLD = 10.0
RSI_OVERBOUGHT = 70.0
PROFIT_TARGET = 0.05
TIME_STOP_DAYS = 5
STOP_LOSS = 0.08
RISK_FRACTION = 0.0025
MAX_POSITIONS = 8
WARMUP_BARS = 30
MA200_PERIOD = 200    # master-desk: old 200-day SMA trend filter (entries only in an uptrend)
MA5_PERIOD = 5        # master-desk: old primary exit (close back above the 5-day SMA, Connors' original)

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


def size_qty(equity, ref_px):
    """master-desk: the old size_qty verbatim — 0.25% risk on the -8% stop
    distance, whole shares, NO 1-share minimum (the 2026-10-09 fix: a 0
    computes as 0 and the entry is skipped)."""
    if not ref_px or ref_px <= 0 or not equity or equity <= 0:
        return 0
    return int((equity * RISK_FRACTION) / (ref_px * STOP_LOSS))


class RsiMeanRev(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        universe = extra.get("universe") or sorted(bars.keys())
        equity = float(context.equity or 0.0)
        intents = []
        open_n = sum(1 for s in universe if (state.get(s) or {}).get("position")
                     or (state.get(s) or {}).get("pending_entry"))   # old count_positions
        for sym in universe:
            bl = bars.get(sym) or []
            if len(bl) < WARMUP_BARS:
                continue
            st = state.get(sym) or {}
            pos = st.get("position")
            closes = [float(b["c"]) for b in bl]
            if not all(math.isfinite(c) for c in closes[-WARMUP_BARS:]):
                continue
            last_px = closes[-1]
            dates = _dates(bl)
            if pos:
                qty = int(float(pos.get("qty") or 0))
                if qty <= 0:
                    continue
                if pos.get("entry_date") and dates[-1] < str(pos["entry_date"])[:10]:
                    # master-desk: the spec's exits run "from entry fill"; a bar that closed before the fill says
                    # nothing about the position (the old hourly pass sold a gap entry at once; ema_vwap 2026-10-16)
                    continue
                entry_px = float(pos.get("entry_px") or last_px)
                held = _sessions_since(dates, pos.get("entry_date")) \
                    if pos.get("entry_date") else 0
                # old manage_position order: sma5 -> rsi>70 -> target -> stop -> time
                sma5 = sum(closes[-MA5_PERIOD:]) / MA5_PERIOD if len(closes) >= MA5_PERIOD else None
                rsi_now = rsi_wilder_last(closes)
                why = None
                if sma5 is not None and last_px > sma5:
                    why = "sma5_exit"
                elif rsi_now is not None and rsi_now > RSI_OVERBOUGHT:
                    why = "rsi_overbought"
                elif last_px >= entry_px * (1 + PROFIT_TARGET):
                    why = "profit_target"
                elif last_px <= entry_px * (1 - STOP_LOSS):
                    why = "stop_loss_market"
                elif held >= TIME_STOP_DAYS:
                    why = "time_stop"
                if why:
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty, price_hint=round(last_px, 2),
                        reason="rsi_meanrev exit: %s px=%.2f entry=%.2f held=%d"
                               % (why, last_px, entry_px, held)))
                continue
            if open_n >= MAX_POSITIONS or equity <= 0:
                continue
            rsi = rsi_wilder_last(closes)
            if rsi is not None and rsi < RSI_OVERSOLD:   # old: last_rsi >= 10 -> not oversold
                if len(closes) < MA200_PERIOD:
                    continue                             # old: MA200 warmup fails closed
                if last_px <= sum(closes[-MA200_PERIOD:]) / MA200_PERIOD:
                    continue                             # old: below the 200-day SMA -> no entry
                qty = size_qty(equity, last_px)
                if qty <= 0:
                    continue
                stop_px = round(last_px * (1 - STOP_LOSS), 2)
                intents.append(Intent(
                    "enter", sym, qty_hint=qty, price_hint=round(last_px, 2),
                    stop=stop_px,
                    exit_rules=(ExitRule("stop", stop_px),
                                ExitRule("target", round(last_px * (1 + PROFIT_TARGET), 2)),
                                ExitRule("time_bars", float(TIME_STOP_DAYS))),
                    reason="rsi_meanrev entry: RSI(2)=%.2f <= %.1f"
                           % (rsi, RSI_OVERSOLD)))
                open_n += 1
        return intents


def _sessions_since(dates, entry_date):
    try:
        return len(dates) - 1 - dates.index(entry_date)
    except ValueError:
        return 0


def signal(bars, slice_state, context):
    return RsiMeanRev().signal(bars, slice_state, context)
