"""Qullamaggie Breakout — lean-desk port (Wave C; Femto's own sleeve).

EXTRACTED from the old desk's qullamaggie_sleeve.py (rebuilt 2026-10-10;
converged spec S1 Sol superthesis v3 / S2 Sol desk / S3 Grok desk_fixed /
S4 GitHub rule registry — every constant below cites its source in the
old file and is copied exactly). master-desk: the pure research functions
are the old file's own numpy/pandas arithmetic, verbatim (bit-identical
thresholds — tools/parity/qullamaggie), on bar dicts instead of frames:

  Leader ... top 2% in ANY 21/63/126-session horizon (max tie-aware
             percentile rank >= 0.98) over the genome; reservation order
             by descending leader score, symbol tiebreak (MF-015).
  Impulse .. >= 30% over 63 sessions INCLUSIVE of the base:
             max(H[-63:]) / C[-64] - 1.
  Base ..... 10 sessions; width (maxH-minL)/C[-1] <= 28%; tightening
             late/early <= 1.0; higher lows (slope of base lows >= 0);
             MA support >= 70% of base closes >= 0.97*SMA10 or
             0.97*SMA20; SMA10/SMA20 rising vs 3 bars ago.
  Liquidity  $5M 20-day ADV.
  Trigger .. 5-min opening range (>= 12 bars of today's complete 09:30
             grid); trigger = max(OR high, pivot); entry = NEXT bar's
             open after the trigger bar, skip if that open < trigger
             (no-chase); only a trigger <= 30 min old; stop = intraday
             pre-trigger low; skip if entry-stop > 1 x ATR(20).
  Sizing ... 0.35% risk/trade of the session's open-mark equity on
             stressed loss/share (stop distance + 95th-pct adverse
             overnight gap + 2bp slip + 1bp comm round-trip friction);
             20% name cap; 1% ADV participation cap; max 10 positions
             (book + entries in flight).
  Manage ... on the last COMPLETED daily close: 1/3 scale after 3+
             calendar days if profitable (once, qty >= 3), residual stop
             -> breakeven on the fill; close below the stop level -> exit;
             trail breach at close vs 10MA (20MA when extended > 1.5 ATR
             above 10MA), held >= 3 days -> exit. The GTC stop at the
             pre-trigger low is the engine stop.

master-desk runtime (the old crons: leader screen 08:45 pre-market, enter
then manage every 30 min 09:30-16:00 ET; the desk gates — risk gate,
Decision #75 chart/red-day/context gates, 150% cap — are gone under the
cutover doctrine):
  screen ... the first pass of the session (pre-market) ranks the genome's
             completed daily bars and records today's leaders and their
             setups in meta; the watch list (setups) is what the 5-min
             bars and quotes are fetched for.
  enter .... every 5-min pass in the session, right after a bar closes:
             the old mode_enter law per leader in score order. The next
             bar's open is read from the bars when that bar has closed;
             when it is still forming (the trigger bar just closed) the
             live price at the pass stands for it (named divergence: the
             old 30-min cron acted 10-40 minutes after a trigger, its
             5-min fetch refused by the free plan's recent-SIP window).
             A trigger decided once (skipped) is not re-decided; a name
             that already round-tripped today is not re-entered.
  manage ... from 09:45 (the old first pass 09:46) on every pass: the old
             mode_manage law; a scale and a stop/trail exit due on the
             same close collapse into the one exit (the old submitted
             both and the exit was refused for the shares the scale sell
             held, completing a pass later).

Inputs via context.extra:
  "sleeve_state" {SYM: {"position": {qty, entry_px, entry_date, stop_px,
                  stop_level, scaled_third, exit_submitted} | None,
                  "pending_entry", "last_exit_date", "scale_sent"}}
  "meta"         the sleeve's stamps: screen, watch, sizing_equity, tried
  "genome"       {SYM: completed daily bars} — only on a screen pass
  "bars_5m"      {SYM: completed 5-min RTH bars} for the watch list
  "quotes"       {SYM: {bid, ask, last, t}} for held + watch names
  "last_session" the last completed session (YYYY-MM-DD)
Bars (the `bars` argument): the held names' completed daily bars."""
import math
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")

RISK_FRACTION = 0.0035          # per-trade risk [S1:234, S3]
MAX_NAME_NOTIONAL_PCT = 0.20    # [S1:454, S3]
MAX_ADV_PARTICIPATION = 0.01    # 1% of ADV (shares) [S4 rule_registry R27]
MAX_POSITIONS = 10              # [S3 config]
LEADER_PCT = 0.98               # top 2% [S1:165, S3, S4]
LEADER_HORIZONS = (21, 63, 126)  # sessions [S1:165, S3, S4]
IMPULSE_MIN = 0.30              # [S1:168, S3]
BASE_WINDOW = 10                # [S1:174, S3]
BASE_WIDTH_MAX = 0.28           # INFERRED hypothesis [S3, S4]
TIGHTENING_MAX = 1.0            # [S3 config]
LOW_SLOPE_MIN = 0.0             # [S3 config]
MA_SUPPORT_MIN = 0.70           # [S3 code]
MA_TOL = 0.97                   # close within 3% below SMA counts [S3 code]
OR_MINUTES = 5                  # [S1:210, S3, S4]
MAX_STOP_ATR = 1.0              # [S2/S3 max_stop_atr]
ADV_MIN = 5_000_000             # $5M 20-day ADV [S3]
SCALE_DAYS = 3                  # [S1:236, S2/S3]
SCALE_FRACTION = 1 / 3          # [S1:236, S2/S3]
TRAIL_HELD_MIN = 3              # [S3: held >= 3]
EXTENSION_ATR = 1.5             # 20MA trail when extended [S1:236, S3]
GAP_QUANTILE = 0.95             # [S3 overnight_gap_quantile]
SLIP_BPS = 2.0                  # [S3 slippage_bps]
COMM_BPS = 1.0                  # [S3 commission_bps]

DAILY_LIMIT = 150               # old get_daily_bars(symbol, limit=150)
RETURN_CLOSES = 130             # old _symbol_returns: closes of the last 130 bars
SCREEN_MIN = 50                 # old select_leaders: the screen needs >= 50 names with returns
TRIGGER_FRESH_S = 30 * 60       # old mode_enter: act only on a trigger <= 30 min old
LIVE_PX_MAX_AGE_S = 120         # master-desk: the live price standing for a forming bar's open
MANAGE_FROM_MIN = 15            # master-desk: manage from 09:45 (the old cron's first pass 09:46)
SCREEN_RETRY_S = 1800           # master-desk: a stale genome is re-read every 30 min

CONFIG = SleeveConfig(
    sleeve_id="qullamaggie", cadence_s=240, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


# ---------------------------------------------------------------------------
# pure research logic — the old file's functions, verbatim arithmetic
# ---------------------------------------------------------------------------
def _cols(bars):
    """bar dicts -> the old frame's columns (float arrays)."""
    return {"open": np.asarray([float(b["o"]) for b in bars], dtype=float),
            "high": np.asarray([float(b["h"]) for b in bars], dtype=float),
            "low": np.asarray([float(b["l"]) for b in bars], dtype=float),
            "close": np.asarray([float(b["c"]) for b in bars], dtype=float),
            "volume": np.asarray([float(b.get("v") or 0.0) for b in bars], dtype=float)}


def trailing_returns(closes):
    """(r21, r63, r126): close[-1]/close[-22]-1, /close[-64]-1, /close[-127]-1. None if too short."""
    c = np.asarray(closes, dtype=float)
    if len(c) < 127 or np.any(c <= 0):
        return None
    last = c[-1]
    return (last / c[-22] - 1, last / c[-64] - 1, last / c[-127] - 1)


def leader_max_percentile(returns_by_symbol):
    """max_h PercentileRank(R_i,h) per symbol [S1:165]; tie-aware: the fraction of symbols at-or-below."""
    syms = list(returns_by_symbol)
    n = len(syms)
    max_pct = {s: 0.0 for s in syms}
    for k in range(3):
        ordered = sorted(syms, key=lambda s: returns_by_symbol[s][k])
        i = 0
        while i < n:
            j = i + 1
            while (j < n and
                   returns_by_symbol[ordered[j]][k] == returns_by_symbol[ordered[i]][k]):
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
    """Breakout setup features from completed daily bars. Returns dict or None (the converged spec)."""
    if bars is None or len(bars) < 130:
        return None
    d = _cols(bars)
    close, high, low, vol = d["close"], d["high"], d["low"], d["volume"]

    impulse = float(np.max(high[-63:]) / close[-64] - 1)
    if impulse < IMPULSE_MIN:
        return None

    base_h, base_l = high[-BASE_WINDOW:], low[-BASE_WINDOW:]
    width = float((np.max(base_h) - np.min(base_l)) / close[-1])
    if width > BASE_WIDTH_MAX:
        return None

    half = BASE_WINDOW // 2
    early = ((np.max(base_h[:half]) - np.min(base_l[:half]))
             / np.mean(close[-BASE_WINDOW:-half]))
    late = ((np.max(base_h[half:]) - np.min(base_l[half:]))
            / np.mean(close[-half:]))
    if early <= 0:
        return None
    tightening = float(late / early)
    if tightening > TIGHTENING_MAX:
        return None

    low_slope = float(np.polyfit(np.arange(BASE_WINDOW), base_l, 1)[0])
    if low_slope < LOW_SLOPE_MIN:
        return None

    s10 = pd.Series(close).rolling(10).mean().to_numpy()
    s20 = pd.Series(close).rolling(20).mean().to_numpy()
    ma_sup = float(np.mean((close[-BASE_WINDOW:] >= s10[-BASE_WINDOW:] * MA_TOL)
                           | (close[-BASE_WINDOW:] >= s20[-BASE_WINDOW:] * MA_TOL)))
    if ma_sup < MA_SUPPORT_MIN:
        return None
    if not (s10[-1] > s10[-4] and s20[-1] > s20[-4]):
        return None

    adv = float(np.mean(close[-20:] * vol[-20:]))
    if adv < ADV_MIN:
        return None
    adv_shares = float(np.mean(vol[-20:]))

    return {"pivot": float(np.max(base_h)), "impulse": impulse,
            "base_width": width, "tightening": tightening,
            "low_slope": low_slope, "ma_support": ma_sup, "adv": adv,
            "adv_shares": adv_shares}


def find_trigger(rows, pivot):
    """OR trigger scan over today's 5-min rows [{"minute_from_open","o","h","l","c"}]. Returns
    (minute, level, pre_low) or None. trigger = max(OR high, pivot); pre_low = the lowest low from 09:30
    through the bar BEFORE the trigger bar (the structural stop) [S2/S3]."""
    if not rows or len(rows) < 12:
        return None
    bars = sorted(rows, key=lambda b: b["minute_from_open"])
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


def validate_minute_bars(minutes):
    """MF-015 P0 #5: the session's 5-min bars must be the complete contiguous grid 0, 5, 10, ... from the
    09:30 open — no gaps, no duplicates; anything else is rejected fail-closed."""
    try:
        mins = [int(m) for m in minutes]
    except (TypeError, ValueError):
        return False
    if not mins:
        return False
    return mins == [5 * i for i in range(len(mins))]


def atr20(bars):
    """20-session ATR (matches S3 stock_features)."""
    d = _cols(bars)
    c, h, l = d["close"], d["high"], d["low"]
    if len(c) < 21:
        return 0.0
    tr = np.maximum(h[1:] - l[1:],
                    np.maximum(np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])))
    return float(np.mean(tr[-20:]))


def gap_buffer_pct(bars):
    """95th-percentile adverse overnight gap over 126 sessions [S3]."""
    d = _cols(bars)
    c, o = d["close"], d["open"]
    if len(c) < 21:
        return 0.0
    prev_close, next_open = c[:-1][-126:], o[1:][-126:]
    adverse = np.maximum(0.0, (prev_close - next_open) / prev_close)
    if len(adverse) < 20:
        return 0.0
    return float(np.quantile(adverse, GAP_QUANTILE))


def size_position(equity, entry, stop, gap_pct, adv_shares=0):
    """Shares to buy: stressed loss/share = stop dist + gap buffer + round-trip friction; 0.35% risk;
    20% name cap; 1% ADV participation cap [S1:234, S3, S4 R27]. 0 if un-sizeable."""
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
    """(trail_ma, label): 20MA when extended (>1.5 ATR above 10MA), else 10MA [S1:236, S3]."""
    c = _cols(bars)["close"]
    if len(c) < 20:
        return None, "none"
    ma10 = float(np.mean(c[-10:]))
    ma20 = float(np.mean(c[-20:]))
    atr = atr20(bars)
    if atr > 0 and c[-1] - ma10 > EXTENSION_ATR * atr:
        return ma20, "20MA-ext"
    return ma10, "10MA"


# ---------------------------------------------------------------------------
# runtime (master-desk): screen, enter, manage
# ---------------------------------------------------------------------------
def _bar_date(b):
    return datetime.fromtimestamp(float(b["t"]) + 4 * 3600, tz=timezone.utc).date().isoformat()


def _rth_minute(now):
    """minutes since the 09:30 ET open on a weekday session, None outside 09:30-16:00."""
    t = datetime.fromtimestamp(float(now), tz=ET)
    m = t.hour * 60 + t.minute - 570
    if t.weekday() >= 5 or m < 0 or m >= 390:
        return None
    return m + t.second / 60.0


def _open_ts(today):
    d = date.fromisoformat(today)
    return datetime(d.year, d.month, d.day, 9, 30, tzinfo=ET).timestamp()


def intraday_rows(bars5, today):
    """old get_intraday_bars: today's 5-min bars with minute_from_open (09:30 ET = 0), bars before the open
    dropped; None when the series is not the complete contiguous grid (fail closed: no trigger, no entry)."""
    rows = []
    for b in bars5 or []:
        t = datetime.fromtimestamp(float(b["t"]), tz=ET)
        if t.date().isoformat() != today:
            continue
        m = ((t.hour * 60 + t.minute) - (9 * 60 + 30)) // 5 * 5
        if m < 0:
            continue
        rows.append({"minute_from_open": m, "o": float(b["o"]), "h": float(b["h"]), "l": float(b["l"]),
                     "c": float(b["c"]), "v": float(b.get("v") or 0.0)})
    rows.sort(key=lambda r: r["minute_from_open"])
    if not rows or not validate_minute_bars([r["minute_from_open"] for r in rows]):
        return None
    return rows


def screen(genome, last_session):
    """old select_leaders + the setup each leader's completed bars carry (the old mode_enter recomputed it
    every pass from the same bars). master-desk: only names whose cache carries the last completed session
    rank (a halted name's stale return never leads); fewer than SCREEN_MIN such names = the genome is stale
    -> None (wait; the old fell back to ten megacaps when its own fetch failed)."""
    rets, fresh = {}, {}
    for sym, bl in (genome or {}).items():
        if not bl or _bar_date(bl[-1]) != last_session:
            continue
        fresh[sym] = bl[-DAILY_LIMIT:]
        r = trailing_returns([float(b["c"]) for b in bl[-RETURN_CLOSES:]])
        if r is not None:
            rets[sym] = r
    if len(rets) < SCREEN_MIN:
        return None
    max_pct = leader_max_percentile(rets)
    leaders = order_leaders_by_score({s: p for s, p in max_pct.items() if p >= LEADER_PCT})
    setups = {}
    for s in leaders:
        daily = fresh[s]
        feat = compute_features(daily)
        if feat:
            setups[s] = dict(feat, atr=atr20(daily), gap=gap_buffer_pct(daily), score=float(max_pct[s]))
    return {"asof": last_session, "universe": len(rets), "leaders": leaders, "setups": setups}


def book_of(state):
    return {s: v["position"] for s, v in (state or {}).items() if isinstance(v, dict) and v.get("position")}


def working_of(state):
    return {s: v["pending_entry"] for s, v in (state or {}).items()
            if isinstance(v, dict) and v.get("pending_entry") and not v.get("position")}


def live_px(q, now):
    """the live price at the pass: mid of a quote <= LIVE_PX_MAX_AGE_S old, else its last; None if stale."""
    if not q:
        return None
    try:
        t = float(q.get("t"))
    except (TypeError, ValueError):
        return None
    if now - t > LIVE_PX_MAX_AGE_S or t > now + 5:
        return None
    try:
        bid, ask = float(q.get("bid") or 0), float(q.get("ask") or 0)
        last = float(q.get("last") or 0)
    except (TypeError, ValueError):
        return None
    px = (bid + ask) / 2 if (bid > 0 and ask >= bid) else last
    return px if px > 0 and math.isfinite(px) else None


def sizing_equity(meta, today, equity):
    """MF-015 P0 #1: every entry today sizes off the session's pinned first-mark equity."""
    rec = (meta or {}).get("sizing_equity") or {}
    if rec.get("date") == today:
        try:
            pinned = float(rec.get("equity") or 0)
        except (TypeError, ValueError):
            pinned = 0.0
        if pinned > 0:
            return pinned
    return float(equity or 0.0)


def tried_of(meta, today):
    rec = (meta or {}).get("tried") or {}
    return dict(rec.get("syms") or {}) if rec.get("date") == today else {}


def entries(sc, bars5, quotes, state, tried, equity, now, today):
    """old mode_enter over today's leaders (score order). Returns (enter intents, {sym: trigger minute}
    decided this pass — a skipped trigger is not re-decided)."""
    owned, pending = book_of(state), working_of(state)
    out, decided = [], {}
    if len(owned) + len(pending) >= MAX_POSITIONS:
        return out, decided
    setups = sc.get("setups") or {}
    for sym in sc.get("leaders") or []:
        if sym in owned or sym in pending:
            continue
        feat = setups.get(sym)
        if not feat:
            continue
        if ((state.get(sym) or {}).get("last_exit_date") or "") == today:
            continue                                    # round-tripped today (old: the 30-min cadence)
        rows = intraday_rows(bars5.get(sym), today)
        if rows is None:
            continue
        trig = find_trigger(rows, feat["pivot"])
        if not trig:
            continue
        trig_min, trig_level, pre_low = trig
        if tried.get(sym) == trig_min:
            continue
        age = now - (_open_ts(today) + trig_min * 60)
        if age < 0 or age > TRIGGER_FRESH_S:
            continue                                    # trigger_stale
        after = [r for r in rows if r["minute_from_open"] > trig_min]
        if after:
            entry_price, via = float(after[0]["o"]), "next bar open"
        else:
            entry_price, via = live_px(quotes.get(sym), now), "live (next bar forming)"
            if entry_price is None:
                continue                                # the next pass reads the bar
        if entry_price < trig_level:
            decided[sym] = trig_min                     # no_chase
            continue
        stop = float(pre_low)
        risk_dist = entry_price - stop
        if risk_dist <= 0:
            decided[sym] = trig_min
            continue
        atr = float(feat.get("atr") or 0.0)
        if atr > 0 and risk_dist > MAX_STOP_ATR * atr:
            decided[sym] = trig_min                     # stop_too_wide
            continue
        qty = size_position(equity, entry_price, stop, float(feat.get("gap") or 0.0),
                            feat.get("adv_shares", 0))
        if qty < 1:
            decided[sym] = trig_min
            continue
        if len(owned) + len(pending) + len(out) >= MAX_POSITIONS:
            continue                                    # max_positions_mid_sweep
        out.append(Intent(
            "enter", sym, qty_hint=int(qty), price_hint=round(entry_price, 4), stop=round(stop, 2),
            exit_rules=(ExitRule("stop", round(stop, 2)),),
            signal_key=f"{sym}:{today}:enter",
            position_meta={"stop_level": stop, "trigger_level": trig_level, "trigger_min": trig_min,
                           "entry_ref": entry_price, "pivot": feat["pivot"]},
            reason="qullamaggie breakout: leader_pct=%.3f impulse=%.3f pivot=%.2f trigger_min=%d level=%.2f "
                   "entry=%.2f (%s) stop=%.2f" % (feat.get("score") or 0.0, feat["impulse"], feat["pivot"],
                                                  trig_min, trig_level, entry_price, via, stop)))
    return out, decided


def scale_view(p, st):
    """(scaled, scale_in_flight, stop_level) of a held position — the old two-phase scale: a scale sell
    that filled (the slice shrank) commits the third and moves the residual stop to breakeven."""
    entry = round(float(p.get("entry_px") or 0.0), 2)
    base = p.get("stop_level")
    if base is None:
        base = p.get("stop_px")
    sent = (st or {}).get("scale_sent") or None
    qty = float(p.get("qty") or 0.0)
    if p.get("scaled_third"):
        return True, False, float(p.get("stop_level") or entry)
    if sent and qty < float(sent.get("qty") or 0.0) - 1e-9:
        return True, False, round(max(float(base or entry), entry), 2)
    if sent and p.get("exit_submitted"):
        return False, True, float(base or entry)
    return False, False, float(base or entry)


def _days_held(entry_date, today):
    try:
        return (date.fromisoformat(today) - date.fromisoformat(str(entry_date)[:10])).days
    except (TypeError, ValueError):
        return 0


def manage(bars, state, last_session, today):
    """old mode_manage per held slice, on the last completed daily close."""
    out = []
    for sym, p in book_of(state).items():
        if p.get("exit_submitted"):
            continue
        st = state.get(sym) or {}
        scaled, in_flight, stop_level = scale_view(p, st)
        if in_flight:
            continue
        qty = int(float(p.get("qty") or 0))
        entry = round(float(p.get("entry_px") or 0.0), 2)
        if qty <= 0:
            continue
        daily = (bars.get(sym) or [])[-DAILY_LIMIT:]
        if len(daily) < 20:
            continue
        if last_session and _bar_date(daily[-1]) < last_session:
            continue                                    # master-desk: decide on the last completed session only
        curr = float(daily[-1]["c"])
        stop_level = float(stop_level or entry or 0)
        pnl_pct = (curr - entry) / entry if entry else 0
        days_held = _days_held(p.get("entry_date") or today, today)
        trail_ma, ma_lbl = trail_target(daily)
        if curr < stop_level:
            out.append(Intent("exit", sym, qty_hint=qty, price_hint=round(curr, 2), signal_key=f"{sym}:{today}:stop",
                              reason="qullamaggie stop: close %.2f < stop %.2f" % (curr, stop_level)))
        elif trail_ma is not None and days_held >= TRAIL_HELD_MIN and curr < trail_ma:
            out.append(Intent("exit", sym, qty_hint=qty, price_hint=round(curr, 2), signal_key=f"{sym}:{today}:trail",
                              reason="qullamaggie trail (%s): close %.2f < %.2f, held %dd"
                                     % (ma_lbl, curr, trail_ma, days_held)))
        elif not scaled and days_held >= SCALE_DAYS and pnl_pct > 0 and qty >= 3:
            sell_qty = max(1, int(qty * SCALE_FRACTION))
            out.append(Intent("exit", sym, qty_hint=sell_qty, price_hint=round(curr, 2),
                              signal_key=f"{sym}:{today}:scale",
                              reason="qullamaggie scale 1/3: %d of %d, held %dd, +%.1f%%; residual stop -> "
                                     "breakeven %.2f" % (sell_qty, qty, days_held, pnl_pct * 100, entry)))
    return out


class Qullamaggie(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        m = _rth_minute(context.now)
        if m is None:
            return []                                   # the pre-market pass screens (next_meta)
        state = extra.get("sleeve_state") or {}
        meta = extra.get("meta") or {}
        today = context.session
        out = []
        sc = meta.get("screen") or {}
        if sc.get("date") == today:
            ents, _ = entries(sc, extra.get("bars_5m") or {}, extra.get("quotes") or {}, state,
                              tried_of(meta, today), sizing_equity(meta, today, context.equity),
                              float(context.now), today)
            out += ents
        if m >= MANAGE_FROM_MIN:
            out += manage(bars, state, extra.get("last_session"), today)
        return out


def signal(bars, slice_state, context):
    return Qullamaggie().signal(bars, slice_state, context)


def next_meta(bars, slice_state, context, intents=()):
    """the session's stamps: today's screen + watch list (once the genome carries the last session), the
    open-mark sizing equity (the first pass in the session), the triggers decided this pass."""
    extra = context.extra or {}
    meta0 = extra.get("meta") or {}
    meta = dict(meta0)
    today = context.session
    now = float(context.now)
    if meta.get("screened") != today and extra.get("genome"):
        res = screen(extra.get("genome"), extra.get("last_session"))
        if res is None:
            meta["screen_retry_at"] = now + SCREEN_RETRY_S
            meta["screen_wait"] = {"date": today, "at": now, "why": "genome lacks the last session %s"
                                   % extra.get("last_session")}
        else:
            meta.update(screen=dict(res, date=today), screened=today,
                        watch={"date": today, "symbols": list(res["setups"])})
            meta.pop("screen_wait", None)
            meta.pop("screen_retry_at", None)
    if _rth_minute(now) is not None:
        if (meta.get("sizing_equity") or {}).get("date") != today and float(context.equity or 0) > 0:
            meta["sizing_equity"] = {"date": today, "equity": float(context.equity)}
        sc = meta0.get("screen") or {}
        if sc.get("date") == today:
            tried = tried_of(meta0, today)
            _, decided = entries(sc, extra.get("bars_5m") or {}, extra.get("quotes") or {},
                                 extra.get("sleeve_state") or {}, tried, sizing_equity(meta0, today, context.equity),
                                 now, today)
            if decided or (meta0.get("tried") or {}).get("date") != today:
                tried.update(decided)
                meta["tried"] = {"date": today, "syms": tried}
    return meta


def next_symbol_state(bars, slice_state, context, intents=()):
    """the old two-phase scale: a scale sell sent this pass is remembered with the slice it came from; a later
    pass that sees the slice shrink commits it (scaled_third, breakeven stop level — the old _commit_scale);
    one that sees it unchanged and no exit working drops it (the old scale_unfilled: the original stop stays)."""
    state = (context.extra or {}).get("sleeve_state") or {}
    out = {}
    for sym, st in state.items():
        if not isinstance(st, dict) or not st.get("scale_sent"):
            continue
        p = st.get("position")
        if not p:
            out[sym] = {"scale_sent": None}
            continue
        scaled, in_flight, be = scale_view(p, st)
        if scaled:
            out[sym] = {"scale_sent": None, "pos": {"scaled_third": True, "stop_level": be}}
        elif not in_flight:
            out[sym] = {"scale_sent": None}
    for fi in intents or ():
        if fi.kind == "exit" and (fi.signal_key or "").endswith(":scale"):
            p = (state.get(fi.symbol) or {}).get("position") or {}
            out.setdefault(fi.symbol, {})["scale_sent"] = {"qty": float(p.get("qty") or 0.0),
                                                           "sell": fi.qty_hint, "at": float(context.now)}
    return out


def stop_levels(bars, slice_state, context):
    """the residual stop of a scaled slice: breakeven (the engine ratchets; it never lowers a stop)."""
    state = (context.extra or {}).get("sleeve_state") or {}
    out = {}
    for sym, p in book_of(state).items():
        scaled, _f, be = scale_view(p, state.get(sym) or {})
        if scaled and be:
            out[sym] = round(float(be), 2)
    return out
