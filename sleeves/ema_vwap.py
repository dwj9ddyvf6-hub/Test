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

ENH (IMPROVE-ema_vwap, Edge program 2026-10-24): one added entry
refusal — refuse when the distance from the entry close back to the
VWAP is smaller than the coded stop distance, i.e.
(VWAP - close) / close < STOP_LOSS (0.08); in deviation terms only
entries at ~7.4% or more below the anchor are taken. Switched by
context.extra["ema_vwap_improve"]["deviation_geometry_gate"]
(default ON; OFF restores the pre-change rule exactly). Every
qualifier records a paired control/treatment record on
self.last_evaluation["enhance_exp"].
"""
import math
from datetime import datetime, timezone

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

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
    (h+l+c)/3 over (tp*vol).rolling(20).sum() / vol.rolling(20).sum()
    with vol.replace(0, NaN). pandas rolling sum defaults to
    min_periods=window, i.e. it needs `window` VALID (non-NaN) terms:
    ANY zero-volume bar inside the 20-bar window makes the old VWAP
    NaN (no anchor, no signal) — it is NOT excluded-and-averaged over
    the remaining bars. Returns None until `window` bars exist, and
    None whenever the window contains a zero/missing-volume bar
    (P3 audit 2026-10-15: exclusion semantics diverged from the old
    desk whenever a halt/zero-volume day fell in the window)."""
    if len(bars) < window:
        return None
    num = 0.0
    den = 0.0
    for b in bars[-window:]:
        v = b.get("v")
        if v is None or float(v) == 0:
            return None  # old: NaN term in window -> rolling sum is NaN
        v = float(v)
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
    """Verbatim old size_qty: risk budget / 8% stop distance, capped by
    the 5% per-position notional cap, floored to whole shares — and 0
    when the budget buys nothing or inputs are bad (the old caller
    skips qty <= 0). NO 1-share minimum: forcing one share when the
    0.25% risk budget computes 0 breaches the risk rail (the old desk
    removed exactly that floor from rsi_meanrev as a HIGH bugfix,
    2026-10-09; the lean port reintroduced it — P3 audit 2026-10-15)."""
    if not ref_px or ref_px <= 0 or equity <= 0:
        return 0
    raw = equity * RISK_FRACTION / (STOP_LOSS * ref_px)
    cap = equity * POS_NOTIONAL_CAP / ref_px
    return max(0, int(min(raw, cap)))


# ------------------------------------------------------------ ENH experiment
EXP_ID = "ENH-EMA-VWAP-20261024"

def deviation_geometry_gate_enabled(extra):
    ov = (extra or {}).get("ema_vwap_improve")
    if isinstance(ov, dict) and "deviation_geometry_gate" in ov:
        return bool(ov["deviation_geometry_gate"])
    return True

def geometry_refused(close, vwap):
    """True when the max coded gain (full reversion to the VWAP) is
    smaller than the coded stop: (vwap - close) / close < STOP_LOSS."""
    if vwap is None or not close or close <= 0:
        return False
    return (vwap - close) / close < STOP_LOSS

class EmaVwap(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        universe = extra.get("universe") or sorted(bars.keys())
        equity = float(context.equity or 0.0)
        intents = []
        gate_on = deviation_geometry_gate_enabled(extra)
        exp_records = []
        open_n = sum(1 for s in universe if (state.get(s) or {}).get("position"))
        sleeve_notional = 0.0
        for s in universe:
            p = (state.get(s) or {}).get("position")
            if p:
                sleeve_notional += float(p.get("entry_px") or 0) * float(p.get("qty") or 0)
        for sym in universe:
            bl = bars.get(sym) or []
            st = state.get(sym) or {}
            pos = st.get("position")
            # READINESS-20261022 F-A6: the stop/target/time exits
            # need only the last close and the session dates; the
            # 30-bar warmup guards ENTRIES only (D-B6 shape). The
            # VWAP-reversion leg keeps its own 21-bar need inside
            # reverted_to_vwap().
            if pos:
                if not bl:
                    continue
            elif len(bl) < WARMUP_BARS:
                continue
            last_px = float(bl[-1]["c"])
            dates = _dates(bl)
            if pos:
                qty = int(float(pos.get("qty") or 0))
                if qty <= 0:
                    continue
                entry_px = float(pos.get("entry_px") or last_px)
                held = _sessions_since(dates, pos.get("entry_date")) \
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
                vwap_now = rolling_vwap(bl)
                refused = geometry_refused(last_px, vwap_now)
                exp_records.append({
                    "symbol": sym, "close": last_px, "vwap": vwap_now,
                    "distance_to_vwap": None if vwap_now is None else
                    (vwap_now - last_px) / last_px,
                    "control_enter": True,
                    "treatment_enter": not refused,
                    "switch_on": gate_on})
                if gate_on and refused:
                    continue
                qty = size_qty(equity, last_px)
                if qty <= 0:
                    continue  # old caller: entry skipped on qty <= 0
                if sleeve_notional + qty * last_px > SLEEVE_NOTIONAL_CAP * equity:
                    continue
                stop_px = round(last_px * (1 - DISASTER_STOP), 2)
                intents.append(Intent(
                    "enter", sym, qty_hint=qty, price_hint=round(last_px, 2),
                    stop=stop_px,
                    exit_rules=(ExitRule("stop", stop_px),
                                ExitRule("target", round(last_px * (1 + PROFIT_TARGET), 2)),
                                ExitRule("time_bars", float(TIME_STOP_DAYS))),
                    reason="ema_vwap deviation: close=%.2f vwap20=%.4f"
                           % (last_px, rolling_vwap(bl))))
                open_n += 1
                sleeve_notional += qty * last_px
        if exp_records:
            self.last_evaluation = {"enhance_exp": {
                "exp_id": EXP_ID, "switch_on": gate_on,
                "records": exp_records}}
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
    return EmaVwap().signal(bars, slice_state, context)
