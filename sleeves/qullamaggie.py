"""Qullamaggie Breakout — lean-desk port (Wave C; Femto's own sleeve).

EXTRACTED from the old desk's qullamaggie_sleeve.py (rebuilt 2026-10-10;
converged spec S1 Sol superthesis v3 / S2 Sol desk / S3 Grok desk_fixed /
S4 GitHub rule registry — every constant below cites its source in the
old file and is copied exactly). The pure research functions are ported
verbatim in behavior from numpy/pandas to plain lists (differential
spot-checks in tests/test_wave_c_ports.py):

  Leader ... top 2% in ANY 21/63/126-session horizon (max tie-aware
             percentile rank >= 0.98); reservation order by descending
             leader score, symbol tiebreak (MF-015).
  Impulse .. >= 30% over 63 sessions INCLUSIVE of the base:
             max(H[-63:]) / C[-64] - 1.
  Base ..... 10 sessions; width (maxH-minL)/C[-1] <= 28%; tightening
             late/early <= 1.0; higher lows (slope of base lows >= 0);
             MA support >= 70% of base closes >= 0.97*SMA10 or
             0.97*SMA20; SMA10/SMA20 rising vs 3 bars ago.
  Liquidity  $5M 20-day ADV.
  Trigger .. 5-min opening range; trigger = max(OR high, pivot); entry =
             NEXT bar's open after the trigger bar, skip if that open <
             trigger (no-chase); stop = intraday pre-trigger low; skip if
             entry-stop > 1 x ATR(20). The intraday trigger machinery is
             intraday-core work: entries here stage at the pivot with the
             stop expressed as data when the core supplies the trigger
             via extra (named misfit, ports/qullamaggie.md).
  Sizing ... 0.35% risk/trade on stressed loss/share (stop distance +
             95th-pct adverse overnight gap + 2bp slip + 1bp comm
             round-trip friction); 20% name cap; 1% ADV participation
             cap; max 10 positions.
  Manage ... 1/3 scale after 3+ days if profitable (once, qty >= 3),
             residual stop -> breakeven; trail breach at close vs 10MA
             (20MA when extended > 1.5 ATR above 10MA), held >= 3 days.
             Stop-breach and scale/trail exits are emitted as intents;
             the GTC stop lifecycle itself is core Broker work.

Inputs via context.extra:
  "sleeve_state": {SYM: {"position": {"entry_px","entry_date","qty",
                    "stop","scaled_third"} | None}}
  "trigger": {SYM: {"entry_px","stop","minute"}} — a core-computed
             intraday OR trigger for today (optional; without it the
             sleeve stages nothing — fail closed, no pivot guessing)
Bars: daily dicts {"t","o","h","l","c","v"} ascending (genome universe).
"""
import math
from datetime import datetime, timezone

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

# CONSTANTS-PROVENANCE-20261116: every constant in this block is restated with its value in the
# module header above (Leader 0.98, Impulse 0.30, Base 10/0.28/1.0, MA support
# 0.70/0.97, OR 5 min, stop 1x ATR, ADV $5M, risk 0.35%, caps 20%/1%/10,
# scale 3d, trail held 3d, extension 1.5 ATR, gap 95th pct, slip 2bp) and the
# header records each cites its source in the old desk's qullamaggie_sleeve.py,
# copied exactly (converged spec S1-S4).
RISK_FRACTION = 0.0035
MAX_NAME_NOTIONAL_PCT = 0.20
MAX_ADV_PARTICIPATION = 0.01
MAX_POSITIONS = 10
LEADER_PCT = 0.98
LEADER_HORIZONS = (21, 63, 126)
IMPULSE_MIN = 0.30
BASE_WINDOW = 10
BASE_WIDTH_MAX = 0.28
TIGHTENING_MAX = 1.0
LOW_SLOPE_MIN = 0.0
MA_SUPPORT_MIN = 0.70
MA_TOL = 0.97
OR_MINUTES = 5
MAX_STOP_ATR = 1.0
ADV_MIN = 5_000_000
SCALE_DAYS = 3
SCALE_FRACTION = 1 / 3
TRAIL_HELD_MIN = 3
EXTENSION_ATR = 1.5
GAP_QUANTILE = 0.95
SLIP_BPS = 2.0
COMM_BPS = 1.0

CONFIG = SleeveConfig(
    sleeve_id="qullamaggie", cadence_s=1800, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


def _dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


def _sma(vals, period):
    out = [None] * len(vals)
    for i in range(period - 1, len(vals)):
        out[i] = sum(vals[i - period + 1:i + 1]) / period
    return out


def trailing_returns(closes):
    """(r21, r63, r126) — verbatim: close[-1]/close[-22|-64|-127] - 1;
    None when < 127 closes or any close <= 0 / non-finite."""
    if len(closes) < 127:
        return None
    if any((not math.isfinite(float(c))) or float(c) <= 0 for c in closes):
        return None
    last = float(closes[-1])
    return (last / float(closes[-22]) - 1,
            last / float(closes[-64]) - 1,
            last / float(closes[-127]) - 1)


def leader_max_percentile(returns_by_symbol):
    """Tie-aware max percentile per symbol — verbatim port (fraction of
    symbols at-or-below, ties share the block's top percentile)."""
    syms = list(returns_by_symbol)
    n = len(syms)
    max_pct = {s: 0.0 for s in syms}
    for k in range(3):
        ordered = sorted(syms, key=lambda s: returns_by_symbol[s][k])
        i = 0
        while i < n:
            j = i + 1
            while j < n and returns_by_symbol[ordered[j]][k] \
                    == returns_by_symbol[ordered[i]][k]:
                j += 1
            pct = j / n
            for s in ordered[i:j]:
                if pct > max_pct[s]:
                    max_pct[s] = pct
            i = j
    return max_pct


def order_leaders_by_score(score_by_symbol):
    """MF-015: descending leader score, symbol name as tiebreak only."""
    return sorted(score_by_symbol,
                  key=lambda s: (-float(score_by_symbol[s]), s))


def compute_features(bars):
    """Breakout setup features from daily bars — verbatim port of the
    old compute_features (dict-of-columns -> bar dicts). None = no setup."""
    if not bars or len(bars) < 130:
        return None
    close = [float(b["c"]) for b in bars]
    high = [float(b["h"]) for b in bars]
    low = [float(b["l"]) for b in bars]
    vol = [float(b["v"]) for b in bars]
    if not all(math.isfinite(x) for x in close + high + low):
        return None
    # Repair 2026-10-15 P3: the divisor closes must be positive — a
    # zero close (corrupt/split artifact) raised ZeroDivisionError out
    # of signal() instead of failing closed with no setup. The old
    # numpy code produced inf/nan and continued; neither is a setup.
    if close[-1] <= 0 or close[-64] <= 0:
        return None
    impulse = max(high[-63:]) / close[-64] - 1
    if impulse < IMPULSE_MIN:
        return None
    base_h, base_l = high[-BASE_WINDOW:], low[-BASE_WINDOW:]
    width = (max(base_h) - min(base_l)) / close[-1]
    if width > BASE_WIDTH_MAX:
        return None
    half = BASE_WINDOW // 2
    early = (max(base_h[:half]) - min(base_l[:half])) \
        / (sum(close[-BASE_WINDOW:-half]) / len(close[-BASE_WINDOW:-half]))
    late = (max(base_h[half:]) - min(base_l[half:])) \
        / (sum(close[-half:]) / len(close[-half:]))
    if early <= 0:
        return None
    tightening = late / early
    if tightening > TIGHTENING_MAX:
        return None
    # slope of base lows (old np.polyfit degree 1)
    xs = list(range(BASE_WINDOW))
    mx = sum(xs) / BASE_WINDOW
    my = sum(base_l) / BASE_WINDOW
    denom = sum((x - mx) ** 2 for x in xs)
    low_slope = sum((x - mx) * (y - my) for x, y in zip(xs, base_l)) / denom \
        if denom else 0.0
    if low_slope < LOW_SLOPE_MIN:
        return None
    s10 = _sma(close, 10)
    s20 = _sma(close, 20)
    hits = 0
    for i in range(len(close) - BASE_WINDOW, len(close)):
        if close[i] >= s10[i] * MA_TOL or close[i] >= s20[i] * MA_TOL:
            hits += 1
    ma_sup = hits / BASE_WINDOW
    if ma_sup < MA_SUPPORT_MIN:
        return None
    if not (s10[-1] > s10[-4] and s20[-1] > s20[-4]):
        return None
    adv = sum(close[-20:][i] * vol[-20:][i] for i in range(20)) / 20
    if adv < ADV_MIN:
        return None
    adv_shares = sum(vol[-20:]) / 20
    return {"pivot": float(max(base_h)), "impulse": impulse,
            "base_width": width, "tightening": tightening,
            "low_slope": low_slope, "ma_support": ma_sup, "adv": adv,
            "adv_shares": adv_shares}


def atr20(bars):
    """20-session mean true range — verbatim port (0.0 when < 21 bars)."""
    if len(bars) < 21:
        return 0.0
    trs = []
    for i in range(1, len(bars)):
        h, l, pc = float(bars[i]["h"]), float(bars[i]["l"]), float(bars[i - 1]["c"])
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs[-20:]) / 20


def gap_buffer_pct(bars):
    """95th-percentile adverse overnight gap over 126 sessions — verbatim
    port (linear-interpolation quantile, numpy default)."""
    if len(bars) < 21:
        return 0.0
    pairs = [(float(bars[i - 1]["c"]), float(bars[i]["o"]))
             for i in range(1, len(bars))][-126:]
    adverse = sorted(max(0.0, (pc - o) / pc) if pc else 0.0
                     for pc, o in pairs)
    if len(adverse) < 20:
        return 0.0
    pos = GAP_QUANTILE * (len(adverse) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(adverse) - 1)
    return adverse[lo] + (adverse[hi] - adverse[lo]) * (pos - lo)


def size_position(equity, entry, stop, gap_pct, adv_shares=0):
    """Verbatim port: stressed-loss sizing; 0 when un-sizeable."""
    risk_dist = entry - stop
    if risk_dist <= 0 or equity <= 0 or entry <= 0:
        return 0
    friction_ps = entry * 2 * (SLIP_BPS + COMM_BPS) / 10_000
    stressed = risk_dist + gap_pct * entry + friction_ps
    if stressed <= 0:
        return 0
    qty = int((equity * RISK_FRACTION) / stressed)
    qty = min(qty, int((equity * MAX_NAME_NOTIONAL_PCT) / entry))
    if adv_shares > 0:
        qty = min(qty, int(adv_shares * MAX_ADV_PARTICIPATION))
    return max(qty, 0)


def trail_target(bars):
    """(trail_ma, label): 20MA when extended > 1.5 ATR above 10MA, else
    10MA — verbatim port."""
    if len(bars) < 20:
        return None, "none"
    close = [float(b["c"]) for b in bars]
    ma10 = sum(close[-10:]) / 10
    ma20 = sum(close[-20:]) / 20
    atr = atr20(bars)
    if atr > 0 and close[-1] - ma10 > EXTENSION_ATR * atr:
        return ma20, "20MA-ext"
    return ma10, "10MA"


def validate_minute_grid(minutes):
    """MF-015 P0 #5: the session's 5-min bars must be the complete
    contiguous grid 0,5,10,... — verbatim port."""
    try:
        mins = [int(m) for m in minutes]
    except (TypeError, ValueError):
        return False
    if not mins:
        return False
    return mins == [5 * i for i in range(len(mins))]


def find_trigger(minute_bars, pivot):
    """OR trigger scan over 1-min bars — verbatim port. minute_bars:
    [{"minute_from_open","o","h","l","c","v"}]. Returns
    (minute, level, pre_low) or None."""
    if not minute_bars or len(minute_bars) < 12:
        return None
    bars = sorted(minute_bars, key=lambda b: b["minute_from_open"])
    opening = [b for b in bars if b["minute_from_open"] < OR_MINUTES]
    if not opening:
        return None
    level = max(max(float(b["h"]) for b in opening), float(pivot))
    pre_low = min(float(b["l"]) for b in opening)
    for b in bars:
        if b["minute_from_open"] < OR_MINUTES:
            continue
        if float(b["h"]) >= level:
            return int(b["minute_from_open"]), level, pre_low
        pre_low = min(pre_low, float(b["l"]))
    return None


def sessions_held_datecount_enabled(extra):
    """ENH-qullamaggie (Edge IMPROVE, Group A): context.extra
    ["qullamaggie_improve"]["sessions_held_datecount"], default ON;
    OFF restores the pre-change index form exactly (control)."""
    ov = (extra or {}).get("qullamaggie_improve")
    if isinstance(ov, dict) and "sessions_held_datecount" in ov:
        return bool(ov["sessions_held_datecount"])
    return True


def _sessions_held(bars, entry_date, enhanced=True):
    ds = _dates(bars)
    if not enhanced:
        try:
            return len(ds) - 1 - ds.index(entry_date)
        except ValueError:
            return 0
    # ENH: the sibling sleeves' cured date-count form (rsi_meanrev /
    # red_day_reversal _sessions_since, P3 cure 2026-10-15): count the
    # delivered dates strictly after the entry date, so an entry date
    # aged out of the delivered window no longer collapses the count
    # to 0 and silently disarms the scale-out / trail exits
    # (IMPROVE-qullamaggie section 2). Identical to the index form
    # whenever the entry date is inside the delivered window.
    entry = str(entry_date)[:10]
    return sum(1 for d in ds if str(d)[:10] > entry)


class Qullamaggie(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        triggers = extra.get("trigger") or {}
        equity = float(context.equity or 0.0)
        intents = []
        book = {s: (state.get(s) or {}).get("position")
                for s in state if (state.get(s) or {}).get("position")}
        # ---- manage (exits never gated): stop breach, scale, trail
        for sym, p in book.items():
            bl = bars.get(sym) or []
            if len(bl) < 20:
                continue
            qty = int(float(p.get("qty") or 0))
            entry = float(p.get("entry_px") or 0)
            if qty <= 0 or entry <= 0:
                continue
            curr = float(bl[-1]["c"])
            held = _sessions_held(
                bl, p.get("entry_date"),
                enhanced=sessions_held_datecount_enabled(extra)) \
                if p.get("entry_date") else 0
            stop_level = float(p.get("stop") or p.get("stop_px") or entry)
            # repair 2026-10-15: core dispatch records the fill stop as
            # "stop_px" (_record_position_state); without the fallback
            # the stop silently became the entry price (breakeven).
            if curr < stop_level:
                intents.append(Intent(
                    "exit", sym, qty_hint=qty, price_hint=round(curr, 2),
                    reason="qullamaggie stop breach: close %.2f < stop %.2f"
                           % (curr, stop_level)))
                continue
            if not p.get("scaled_third") and held >= SCALE_DAYS \
                    and curr > entry and qty >= 3:
                sell = max(1, int(qty * SCALE_FRACTION))
                intents.append(Intent(
                    "exit", sym, qty_hint=sell, price_hint=round(curr, 2),
                    reason="qullamaggie scale 1/3: held %dd profitable; "
                           "residual stop -> breakeven %.2f scaled_third=1"
                           % (held, entry)))
                continue
            ma, lbl = trail_target(bl)
            if ma is not None and held >= TRAIL_HELD_MIN and curr < ma:
                intents.append(Intent(
                    "exit", sym, qty_hint=qty, price_hint=round(curr, 2),
                    reason="qullamaggie trail breach (%s): close %.2f < %.2f"
                           % (lbl, curr, ma)))
        if equity <= 0:
            return intents
        # ---- entries: leader screen -> setup -> core-supplied trigger
        rets = {}
        for sym, bl in bars.items():
            if sym in book:
                continue
            r = trailing_returns([float(b["c"]) for b in (bl or [])])
            if r is not None:
                rets[sym] = r
        if not rets:
            return intents
        pct = leader_max_percentile(rets)
        scores = {s: pct[s] for s in rets if pct[s] >= LEADER_PCT}
        open_n = len(book)
        for sym in order_leaders_by_score(scores):
            if open_n >= MAX_POSITIONS:
                break
            bl = bars.get(sym) or []
            feat = compute_features(bl)
            if feat is None:
                continue
            trig = triggers.get(sym)
            if not trig:
                continue  # fail closed: no core trigger, no entry
            entry_px = float(trig.get("entry_px") or 0)
            stop = float(trig.get("stop") or 0)
            if entry_px <= 0 or stop <= 0 or entry_px <= stop:
                continue
            atr = atr20(bl)
            if atr > 0 and (entry_px - stop) > MAX_STOP_ATR * atr:
                continue  # stop too wide (old law: skip)
            qty = size_position(equity, entry_px, stop,
                                gap_buffer_pct(bl), feat["adv_shares"])
            if qty <= 0:
                continue
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(entry_px, 2),
                stop=round(stop, 2),
                exit_rules=(ExitRule("stop", round(stop, 2)),),
                reason="qullamaggie breakout: leader_pct=%.3f impulse=%.3f "
                       "pivot=%.2f trigger_min=%s stop=%.2f"
                       % (scores[sym], feat["impulse"], feat["pivot"],
                          trig.get("minute"), stop)))
            open_n += 1
        return intents


def signal(bars, slice_state, context):
    return Qullamaggie().signal(bars, slice_state, context)
