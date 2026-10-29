"""Capitulation Reversal (equity) — lean-desk port (Wave B).

EXTRACTED from the old desk's capitulation_sleeve.py (SPEC in the old
desk/sleeves/capitulation/). Pure decision logic verbatim in behavior;
plumbing (broker, state files, chart-gate staging, risk gate) is
core-owned. See ports/capitulation.md.

Strategy (old module): closed 1H RTH bars only.
  1H RSI(14) < 20 AND climax-bar volume > 2x the 20 bars BEFORE it AND
  climax-bar low within 2% of the daily 200-day EMA (Decision #102)
  AND first green 1H bar after the climax with RSI turning up AND
  daily ATR(14)/close > 5% (choppiness filter).
Entry: on the first green bar's close; SixSigma scale-in (User
2026-10-10): tranche 1 = half the size on the signal, tranche 2 = the
remainder when the daily 5/20 EMA turn confirms within 5 sessions.
Exits (first trigger): 1H close >= session VWAP, +5% target, -8% stop,
3-trading-day time stop; -25% GTC disaster stop as ExitRule data.
Risk 0.25%/trade on the 8% stop distance; max 5; sleeve cap 25%.
Fear gate (User 2026-10-10): entries DEFER unless the desk composite
is FEAR+ — the core supplies it as extra["fear_ok"]; absent = fail-open
exactly as the old code (sentiment errors never blocked).

master-desk — gone under the cutover doctrine: the Decision #8 earnings
blackout (entries vetoed 3 days before through the earnings date, a stale
calendar halting all entries); the SPEC lists it with the desk-wide rails
(kill switch, chart gate, drawdown brake), not as a capitulation rule.

Inputs via context.extra:
  "bars_1h":      {SYM: [closed 1H bar dicts]}
  "sleeve_state": {SYM: {"position": {...} | None}}
  "fear_ok":      bool (optional; absent == fail-open pass)
Bars (arg): daily dicts {"t","o","h","l","c","v"} ascending.
"""
import math
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")

RSI_PERIOD = 14
RSI_OVERSOLD = 20
VOL_CLIMAX_MULT = 2.0
VOL_LOOKBACK = 20
EMA200_PERIOD = 200
EMA_TOLERANCE = 0.02     # Decision #102 (2026-10-13)
SHADOW_EMA_BAND = 0.05   # telemetry only; never an entry
ATR_PCT_FILTER = 0.05
ATR_PERIOD = 14
PROFIT_TARGET = 0.05
STOP_LOSS = 0.08
HOLD_DAYS = 3
DISASTER_STOP = 0.25
RISK_FRACTION = 0.0025
MAX_POSITIONS = 5
SLEEVE_NOTIONAL_CAP = 0.25
DAILY_BARS_LIMIT = 260
TRANCHE1_FRACTION = 0.5
TRANCHE2_MAX_WAIT = 5
TURN_FAST = 5
TURN_SLOW = 20
BLACKOUT_DAYS_BEFORE = 3  # Decision #8

CONFIG = SleeveConfig(
    sleeve_id="capitulation", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


def _dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


def calc_atr_pct(daily_bars, period=ATR_PERIOD):
    """Daily Wilder ATR as a fraction of the last close. Verbatim."""
    if len(daily_bars) < period + 1:
        return None
    trs = []
    for i in range(1, len(daily_bars)):
        h, l, pc = (daily_bars[i]["h"], daily_bars[i]["l"],
                    daily_bars[i - 1]["c"])
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    atr = sum(trs[:period]) / period
    for tr in trs[period:]:
        atr = (atr * (period - 1) + tr) / period
    close = daily_bars[-1]["c"]
    return atr / close if close > 0 else None


def calc_ema200(daily_bars):
    """200-day EMA, SMA-seeded. Verbatim. None if insufficient."""
    if len(daily_bars) < EMA200_PERIOD:
        return None
    closes = [b["c"] for b in daily_bars]
    ema = sum(closes[:EMA200_PERIOD]) / EMA200_PERIOD
    k = 2.0 / (EMA200_PERIOD + 1)
    for c in closes[EMA200_PERIOD:]:
        ema = c * k + ema * (1 - k)
    return ema


def _ema_series(closes, period):
    if len(closes) < period:
        return None
    ema = sum(closes[:period]) / period
    out = [None] * (period - 1) + [ema]
    k = 2.0 / (period + 1)
    for c in closes[period:]:
        ema = c * k + ema * (1 - k)
        out.append(ema)
    return out


def turn_confirmed(daily_bars):
    """5-day EMA above 20-day EMA on the last daily close. Fail-closed."""
    closes = [b["c"] for b in daily_bars]
    e5 = _ema_series(closes, TURN_FAST)
    e20 = _ema_series(closes, TURN_SLOW)
    if e5 is None or e20 is None:
        return False
    return e5[-1] > e20[-1]


def calc_rsi_1h(closes, period=RSI_PERIOD):
    """Wilder RSI series aligned with closes (SMA seed). Verbatim."""
    n = len(closes)
    if n < period + 1:
        return [None] * n
    gains, losses = [], []
    for i in range(1, n):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    avg_g = sum(gains[:period]) / period
    avg_l = sum(losses[:period]) / period
    rsi = [None] * period
    for i in range(period, n):
        if i > period:
            avg_g = (avg_g * (period - 1) + gains[i - 1]) / period
            avg_l = (avg_l * (period - 1) + losses[i - 1]) / period
        if avg_l == 0:
            rsi.append(100.0 if avg_g > 0 else 50.0)
        else:
            rsi.append(100.0 - (100.0 / (1.0 + avg_g / avg_l)))
    return rsi


def detect_capitulation(h1_bars, daily_bars):
    """The 5-part signature on the last closed 1H bar (parts 1-4 here;
    part 5, the ATR filter, is atr_filter_ok). Verbatim, including the
    2026-10-09 baseline fix: the climax bar is NOT in its own 20-bar
    volume baseline. The old shadow-band log row becomes the returned
    dict's "shadow_beyond_ema_band" marker (telemetry, never entry)."""
    if len(h1_bars) < VOL_LOOKBACK + RSI_PERIOD + 2:
        return None
    if len(daily_bars) < EMA200_PERIOD:
        return None
    closes = [b["c"] for b in h1_bars]
    rsi = calc_rsi_1h(closes)
    last, prev = h1_bars[-1], h1_bars[-2]
    rsi_last, rsi_prev = rsi[-1], rsi[-2]
    if rsi_last is None or rsi_prev is None:
        return None
    if not (last["c"] > last["o"]):
        return None
    if not (rsi_last > rsi_prev):
        return None
    if not (rsi_prev < RSI_OVERSOLD):
        return None
    vols = [b.get("v") or 0 for b in h1_bars[-(VOL_LOOKBACK + 2):-2]]
    avg_vol = sum(vols) / len(vols) if vols else 0
    if avg_vol <= 0 or prev.get("v", 0) <= VOL_CLIMAX_MULT * avg_vol:
        return None
    ema200 = calc_ema200(daily_bars)
    if ema200 is None or ema200 <= 0:
        return None
    ema_dist = abs(prev["l"] - ema200) / ema200
    if ema_dist > EMA_TOLERANCE:
        if ema_dist <= SHADOW_EMA_BAND:
            return {"shadow_beyond_ema_band": True,
                    "distance": round(ema_dist, 4),
                    "climax_low": round(prev["l"], 2),
                    "ema200": round(ema200, 2)}
        return None
    return {"rsi": round(rsi_prev, 1), "rsi_now": round(rsi_last, 1),
            "climax_vol_mult": round(prev["v"] / avg_vol, 2),
            "ema200": round(ema200, 2), "climax_low": round(prev["l"], 2)}


def atr_filter_ok(daily_bars):
    """Part 5: daily ATR(14)/close strictly > 5%."""
    a = calc_atr_pct(daily_bars)
    return a is not None and a > ATR_PCT_FILTER


def session_vwap(h1_bars, session_iso):
    """Session VWAP (typical price x volume) over the bars whose ET
    date == session_iso. Old code used the wall-clock 'today'; the
    contract's clock is context.session."""
    pv, vv = 0.0, 0.0
    for b in h1_bars:
        try:
            bt = datetime.fromtimestamp(float(b["t"]), tz=timezone.utc)
            if bt.astimezone(ET).date().isoformat() != session_iso:
                continue
            tp = (float(b["h"]) + float(b["l"]) + float(b["c"])) / 3.0
            v = float(b.get("v") or 0)
        except (TypeError, ValueError, KeyError):
            continue
        pv += tp * v
        vv += v
    return pv / vv if vv > 0 else None


def size_qty(equity, entry_px):
    """0.25% risk on the 8% stop distance. Verbatim (0 on bad input)."""
    if not equity or not entry_px or entry_px <= 0:
        return 0
    risk_per_share = entry_px * STOP_LOSS
    if risk_per_share <= 0:
        return 0
    return int((equity * RISK_FRACTION) / risk_per_share)


def check_exit(pos, h1_bars, session_iso):
    """Exit reason or None. Verbatim order: VWAP reversion, +5%, -8%,
    3-trading-day time stop (weekdays counted entry->session)."""
    if not h1_bars:
        return None
    last_close = h1_bars[-1]["c"]
    entry_px = pos["entry_px"]
    vwap = session_vwap(h1_bars, session_iso)
    if vwap and last_close >= vwap:
        return "vwap_reversion"
    if last_close >= entry_px * (1 + PROFIT_TARGET):
        return "profit_target"
    if last_close <= entry_px * (1 - STOP_LOSS):
        return "stop_loss"
    try:
        from datetime import date as _date
        entry_d = _date.fromisoformat(str(pos["entry_date"])[:10])
        end_d = _date.fromisoformat(session_iso)
        days_held = 0
        d = entry_d
        while d < end_d:
            d += timedelta(days=1)
            if d.weekday() < 5:
                days_held += 1
        if days_held >= HOLD_DAYS:
            return "time_stop"
    except (ValueError, TypeError, KeyError):
        pass
    return None


class Capitulation(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        h1map = extra.get("bars_1h") or {}
        fear_ok = extra.get("fear_ok", True)  # old: fail-open on errors
        equity = float(context.equity or 0.0)
        universe = extra.get("universe") or sorted(bars.keys())
        intents = []
        # master-desk: old scan_pass open_count = positions + pending entries; the old sleeve defined
        # SLEEVE_NOTIONAL_CAP but never enforced it (the femto port's notional check is not the strategy)
        open_n = sum(1 for s in universe if (state.get(s) or {}).get("position")
                     or (state.get(s) or {}).get("pending_entry"))
        for sym in universe:
            daily = bars.get(sym) or []
            h1 = h1map.get(sym) or []
            if len(daily) < EMA200_PERIOD or not h1:
                continue
            st = state.get(sym) or {}
            pos = st.get("position")
            if pos:
                qty = int(float(pos.get("qty") or 0))
                if qty <= 0:
                    continue
                reason = check_exit(pos, h1, context.session)
                if reason:
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty,
                        price_hint=round(float(h1[-1]["c"]), 2),
                        reason="capitulation exit: %s" % reason))
                    continue
                # Tranche 2: remainder on the 5/20 turn within 5 sessions (old _maybe_tranche2: weekday
                # sessions from the tranche-1 fill date, exclusive, to today; > 5 expires; no stacking).
                t2 = int(float(pos.get("tranche2_qty") or 0))
                if t2 > 0 and pos.get("entry_date") and not pos.get("exit_submitted") \
                        and not st.get("pending_entry"):
                    from datetime import date as _date
                    waited = 0
                    d = _date.fromisoformat(str(pos["entry_date"])[:10])
                    while d < _date.fromisoformat(context.session):
                        d += timedelta(days=1)
                        if d.weekday() < 5:
                            waited += 1
                    if waited <= TRANCHE2_MAX_WAIT and turn_confirmed(daily):
                        stop_px = round(float(pos["entry_px"]) * (1 - DISASTER_STOP), 2)
                        intents.append(Intent(
                            "enter", sym, qty_hint=t2,
                            price_hint=round(float(daily[-1]["c"]), 2),
                            stop=stop_px,
                            exit_rules=(ExitRule("stop", stop_px),
                                        ExitRule("time_bars", float(HOLD_DAYS))),
                            reason="capitulation tranche2: 5/20 turn confirmed, "
                                   "waited=%d sessions" % waited,
                            signal_key="%s:%s:t2" % (sym, context.session),
                            state={"pos": {"tranche2_qty": 0}}))
                continue
            if open_n >= MAX_POSITIONS or equity <= 0:
                continue
            if not atr_filter_ok(daily):
                continue
            sig = detect_capitulation(h1, daily)
            if not sig or sig.get("shadow_beyond_ema_band"):
                continue
            if not fear_ok:
                continue  # DEFER (old semantics): signal stays eligible
            ref_px = float(h1[-1]["c"])
            full = size_qty(equity, ref_px)
            if full <= 0:
                continue
            t1 = max(1, int(full * TRANCHE1_FRACTION))
            stop_px = round(ref_px * (1 - DISASTER_STOP), 2)
            intents.append(Intent(
                "enter", sym, qty_hint=t1, price_hint=round(ref_px, 2),
                stop=stop_px,
                exit_rules=(ExitRule("stop", stop_px),
                            ExitRule("target", round(ref_px * (1 + PROFIT_TARGET), 2)),
                            ExitRule("time_bars", float(HOLD_DAYS))),
                reason="capitulation tranche1 (of full %d): rsi=%.1f "
                       "vol_mult=%.2f ema200=%.2f"
                       % (full, sig["rsi"], sig["climax_vol_mult"], sig["ema200"]),
                position_meta={"tranche2_qty": full - t1, "signal_date": context.session}))
            open_n += 1
        return intents


def signal(bars, slice_state, context):
    return Capitulation().signal(bars, slice_state, context)
