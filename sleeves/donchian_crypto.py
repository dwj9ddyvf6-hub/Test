"""Donchian Crypto (SOL 15m) — lean-desk port (Wave C).

EXTRACTED from the old desk's donchian_crypto_sleeve.py (SPEC:
desk/sleeves/donchian_crypto/SPEC.md) — the TraderDev-validated Donchian
on the asset/timeframe it was validated on (SOL, 15-minute bars).

Signal (closed 15m bars only): close > max(high[t-20..t-1]) strict (ties
do NOT count), volume > 0, >= 40 closed bars warmup.
Exits (first trigger wins): close < min(low[t-10..t-1]), OR low <= the
synthetic ATR(14) x 2.0 trailing stop (crypto has no native stops on the
broker — the trail is core-executed synthetic logic; here the ratcheted
trail is expressed in the intent reason and recomputed purely from bars
by trail_level() — see the port report for the state misfit).
Risk: 0.25% equity/trade on the 2.0 x ATR stop distance; single symbol
SOLUSD, max 1 position; 25% sleeve notional cap; $10 minimum notional
with the post-floor rail re-check (floored qty that breaches risk or cap
=> no trade). Long only. No time stop (validated spec has none).
Bars come from Kraken public OHLC on the old desk (the broker's crypto
market-data endpoints 404) — in the lean desk bars are a core Data
product; the sleeve reads only the `bars` argument (15m SOLUSD bars).

Inputs via context.extra:
  "sleeve_state": {"SOLUSD": {"position": {"entry_px","entry_date","qty",
                    "trail"} | None}}
Bars: 15m dicts {"t","o","h","l","c","v"} ascending.

ENH (IMPROVE-donchian_crypto, Edge program 2026-10-24): one added
entry refusal — refuse a breakout whose close sits more than the
coded stop distance above the breakout level, i.e.
close - max(prior 20 highs) > ATR_MULT x ATR(14). Switched by
context.extra["donchian_crypto_improve"]["chase_gate"] (default ON;
OFF restores the pre-change rule exactly). Refusals record a paired
control/treatment record on self.last_evaluation["enhance_exp"].
"""
import math

from core.sleeve import BaseSleeve, Intent, SleeveConfig

SYMBOL = "SOLUSD"
ENTRY_CHANNEL = 20
EXIT_CHANNEL = 10
WARMUP_BARS = 40
ATR_PERIOD = 14
ATR_MULT = 2.0
RISK_FRACTION = 0.0025
MAX_POSITIONS = 1
SLEEVE_NOTIONAL_CAP = 0.25
MIN_NOTIONAL = 10.0

CONFIG = SleeveConfig(
    sleeve_id="donchian_crypto", cadence_s=900, universe=(SYMBOL,),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


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


def detect_breakout(bars):
    """Verbatim: last closed bar close > max prior-20 highs, vol > 0,
    >= WARMUP_BARS of history. Non-finite values fail closed."""
    if len(bars) < WARMUP_BARS:
        return False
    last = bars[-1]
    if not float(last["v"]) > 0:
        return False
    prior = [float(b["h"]) for b in bars[-(ENTRY_CHANNEL + 1):-1]]
    if not prior or not all(math.isfinite(x) for x in prior) \
            or not math.isfinite(float(last["c"])):
        return False
    return bool(float(last["c"]) > max(prior))


# ------------------------------------------------------------ ENH experiment
EXP_ID = "ENH-DONCHIAN-CRYPTO-20261024"

def chase_gate_enabled(extra):
    ov = (extra or {}).get("donchian_crypto_improve")
    if isinstance(ov, dict) and "chase_gate" in ov:
        return bool(ov["chase_gate"])
    return True

def chase_refused(close, level, atr):
    """True when the chase premium exceeds the trade's own stop
    distance: close - level > ATR_MULT x ATR(14)."""
    if atr is None or level is None:
        return False
    return (close - level) > ATR_MULT * atr

def trail_level(bars, prior_trail=None):
    """The ratcheted synthetic trail implied by the bars: max over the
    trailing window of (close - 2.0 x ATR at that bar), never loosening
    below prior_trail. Pure recomputation of the old update_trail
    ratchet (which mutated state bar by bar)."""
    atr = calc_atr(bars)
    if atr is None or not bars:
        return prior_trail
    cand = float(bars[-1]["c"]) - ATR_MULT * atr
    if prior_trail is None:
        return cand
    return max(float(prior_trail), cand)


def check_exit(pos, bars):
    """Verbatim port of the old check_exit: channel break first, then
    the ATR trail. AUDIT3-06a (2026-10-16): the recorded trail is
    the ratchet's PRIOR — trail_level(bars, prior_trail=recorded)
    — not a replacement for it. The pre-cure code used the
    entry-time trail_init verbatim whenever present, so the
    trailing stop never tightened for the life of the position
    (dispatch persists trail_init once, at entry; nothing rewrites
    it — the ratchet the port's own trail_level docstring defines
    never ran)."""
    if len(bars) < EXIT_CHANNEL + 1:
        return None
    last = bars[-1]
    prior_lows = [float(b["l"]) for b in bars[-(EXIT_CHANNEL + 1):-1]]
    if prior_lows and float(last["c"]) < min(prior_lows):
        return "donchian_exit"
    recorded = pos.get("trail") if isinstance(pos, dict) else None
    trail = trail_level(
        bars, prior_trail=(float(recorded)
                           if recorded is not None else None))
    if trail and float(last["l"]) <= float(trail):
        return "atr_trail"
    return None


def size_qty(equity, entry_px, atr):
    """Verbatim port of the old size_qty (returns a float — fractional
    SOL is tradable): 0.25% risk on 2.0 x ATR, 25% notional cap, $10
    minimum notional floored ONLY when the floored qty still respects
    both rails, else 0 (no trade)."""
    if not entry_px or entry_px <= 0 or not equity or equity <= 0:
        return 0.0
    if atr is not None and not math.isfinite(float(atr)):
        # A corrupt bar outside the channel windows (e.g. a NaN low in
        # old history) poisons Wilder ATR; sizing off NaN emitted an
        # intent carrying qty_sol=nan / trail_init=nan. Fail closed.
        return 0.0
    stop_dist = ATR_MULT * (atr or entry_px * 0.02)
    if stop_dist <= 0 or not math.isfinite(stop_dist):
        return 0.0
    qty = (equity * RISK_FRACTION) / stop_dist
    max_qty = (equity * SLEEVE_NOTIONAL_CAP) / entry_px
    qty = min(qty, max_qty)
    qty = round(qty, 6)
    if qty * entry_px < MIN_NOTIONAL:
        floored = math.ceil(MIN_NOTIONAL / entry_px * 1e6) / 1e6
        if floored * stop_dist > equity * RISK_FRACTION:
            return 0.0
        if floored * entry_px > equity * SLEEVE_NOTIONAL_CAP:
            return 0.0
        qty = floored
    return qty


class DonchianCrypto(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        equity = float(context.equity or 0.0)
        bl = bars.get(SYMBOL) or []
        st = state.get(SYMBOL) or {}
        pos = st.get("position") if isinstance(st, dict) else None
        intents = []
        if pos:
            qty = float(pos.get("qty") or 0)
            reason = check_exit(pos, bl)
            if reason and qty > 0:
                intents.append(Intent(
                    "exit", SYMBOL, qty=qty,
                    price_hint=round(float(bl[-1]["c"]), 2),
                    reason="donchian_crypto exit: %s trail=%s"
                           % (reason, pos.get("trail"))))
            return intents
        if equity <= 0 or not detect_breakout(bl):
            return intents
        atr = calc_atr(bl)
        px = float(bl[-1]["c"])
        level = max(float(b["h"]) for b in bl[-(ENTRY_CHANNEL + 1):-1])
        gate_on = chase_gate_enabled(extra)
        refused = chase_refused(px, level, atr)
        if refused or gate_on:
            self.last_evaluation = {"enhance_exp": {
                "exp_id": EXP_ID, "switch_on": gate_on,
                "records": [{"symbol": SYMBOL, "close": px,
                             "level": level, "atr": atr,
                             "overshoot": px - level,
                             "control_enter": True,
                             "treatment_enter": not refused}]}}
        if gate_on and refused:
            return intents
        qty = size_qty(equity, px, atr)
        if qty <= 0 or not math.isfinite(qty):
            return intents
        # C-1 cured (2026-10-16): the fractional SOL qty rides the
        # intent's qty field (the contract grew it under the owner's ruling);
        # the reason keeps qty_sol= for the record. Before the cure the
        # qty rode ONLY in the reason and dispatch substituted generic
        # whole-unit sizing (and a day TIF Alpaca rejects for crypto).
        intents.append(Intent(
            "enter", SYMBOL, qty=qty, price_hint=round(px, 2),
            reason="donchian_crypto 20-bar breakout: close=%.2f atr=%s "
                   "qty_sol=%.6f trail_init=%.2f"
                   % (px, None if atr is None else round(atr, 4), qty,
                      px - ATR_MULT * (atr or px * 0.02))))
        return intents


def signal(bars, slice_state, context):
    return DonchianCrypto().signal(bars, slice_state, context)
