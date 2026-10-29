"""Donchian Crypto (SOL 15m) — lean-desk port (Wave C), restored on the master desk.

EXTRACTED from the old desk's donchian_crypto_sleeve.py (SPEC:
desk/sleeves/donchian_crypto/SPEC.md) — the TraderDev-validated Donchian
on the asset/timeframe it was validated on (SOL, 15-minute bars).

Signal (closed 15m bars only): close > max(high[t-20..t-1]) strict (ties
do NOT count), volume > 0, >= 40 closed bars warmup (the last 120 closed
Kraken bars, the old fetch window — ATR(14) is Wilder-seeded on it).
Exits (first trigger wins, every pass): close < min(low[t-10..t-1]), OR
low <= the ATR(14) x 2.0 trailing stop. The trail starts at
round(signal close - 2 x ATR, 2) and ratchets each pass to
max(trail, close - 2 x ATR) BEFORE the check (old update_trail ->
check_exit); master-desk restoration: the ratcheted trail persists per
position (next_symbol_state), where the femto port recomputed an
un-ratcheted close - 2 x ATR every pass.
Risk: 0.25% equity/trade on the 2.0 x ATR stop distance; single symbol
SOLUSD, max 1 position (a working entry counts); 25% sleeve notional cap;
$10 minimum notional with the post-floor rail re-check (floored qty that
breaches risk or cap => no trade). Fractional SOL (qty to 6 dp). Long
only. No time stop (validated spec has none). Market orders, gtc; an entry
not filled within 1 hour is dropped (the SPEC's 15m-signal staleness).
One pass per closed bar ~1 minute after it closes (old cron every 15m,
anchored :00:56). Desk-wide gates (kill switch, chart gate, red-day
analog, 150% cap) are gone per the cutover doctrine.

Inputs via context.extra:
  "sleeve_state": {"SOLUSD": {"position": {"entry_px","qty","trail",
                    "exit_submitted"} | None, "pending_entry": {...}}}
Bars: 15m dicts {"t","o","h","l","c","v"} ascending (Kraken SOLUSD).
"""
import math

from .compat import BaseSleeve, Intent, SleeveConfig

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
PENDING_TTL_SECONDS = 3600

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


def trail_level(bars, prior_trail=None):
    """The old update_trail ratchet: max(prior_trail, close - 2.0 x ATR),
    never loosening; prior_trail None starts it at the candidate."""
    atr = calc_atr(bars)
    if atr is None or not bars:
        return prior_trail
    cand = float(bars[-1]["c"]) - ATR_MULT * atr
    if prior_trail is None:
        return cand
    return max(float(prior_trail), cand)


def check_exit(pos, bars):
    """Verbatim port of the old check_exit: channel break first, then the
    ATR trail — pos["trail"] is the trail already ratcheted this pass."""
    if len(bars) < EXIT_CHANNEL + 1:
        return None
    last = bars[-1]
    prior_lows = [float(b["l"]) for b in bars[-(EXIT_CHANNEL + 1):-1]]
    if prior_lows and float(last["c"]) < min(prior_lows):
        return "donchian_exit"
    trail = pos.get("trail") if isinstance(pos, dict) else None
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
    stop_dist = ATR_MULT * (atr or entry_px * 0.02)
    if stop_dist <= 0:
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


def _position(context):
    st = ((context.extra or {}).get("sleeve_state") or {}).get(SYMBOL) or {}
    return st if isinstance(st, dict) else {}


class DonchianCrypto(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        equity = float(context.equity or 0.0)
        bl = bars.get(SYMBOL) or []
        st = _position(context)
        pos = st.get("position")
        if len(bl) < WARMUP_BARS:
            return []                       # old: skip_warmup (no exits, no entries)
        now = float(context.now)
        key = "%s:%d" % (SYMBOL, int(float(bl[-1]["t"])))
        if pos:
            trail = trail_level(bl, pos.get("trail"))
            reason = check_exit(dict(pos, trail=trail), bl)
            qty = float(pos.get("qty") or 0)
            if not reason or qty <= 0 or pos.get("exit_submitted"):
                return []
            return [Intent("exit", SYMBOL, qty=qty, price_hint=round(float(bl[-1]["c"]), 2),
                           order={"type": "market"}, signal_key=key + ":exit",
                           reason="donchian_crypto exit: %s trail=%.4f" % (reason, trail))]
        if st.get("pending_entry") or equity <= 0 or not detect_breakout(bl):
            return []
        atr = calc_atr(bl)
        px = float(bl[-1]["c"])
        qty = size_qty(equity, px, atr)
        if qty <= 0:
            return []
        trail_init = round(px - ATR_MULT * (atr or px * 0.02), 2)
        return [Intent("enter", SYMBOL, qty=qty, price_hint=round(px, 2),
                       order={"type": "market", "not_after": now + PENDING_TTL_SECONDS},
                       position_meta={"trail": trail_init}, signal_key=key + ":entry",
                       reason="donchian_crypto 20-bar breakout: close=%.2f atr=%s qty_sol=%.6f trail_init=%.2f"
                              % (px, None if atr is None else round(atr, 4), qty, trail_init))]


def next_symbol_state(bars, slice_state, context, intents=()):
    """persist this pass's ratcheted trail on the held position (the old
    state's position["trail"]); a flat book drops it."""
    bl = bars.get(SYMBOL) or []
    pos = _position(context).get("position")
    if not pos:
        return {SYMBOL: {"pos": None}}
    if len(bl) < WARMUP_BARS:
        return {}
    return {SYMBOL: {"pos": {"trail": trail_level(bl, pos.get("trail"))}}}


def signal(bars, slice_state, context):
    return DonchianCrypto().signal(bars, slice_state, context)
