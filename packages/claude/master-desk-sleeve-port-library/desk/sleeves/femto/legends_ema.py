"""Legend's EMA — lean-desk port.

EXTRACTED from the old desk's legends_ema.py (QQQ-only). The setup
evaluation (evaluate_setup) and exit_geometry are ported verbatim in
behavior — 15-minute RTH bars arrive via context.extra from core Data
(the old file fetched 1-min bars and built 15m bars itself; the
aggregation is a Data duty now). The OCO lifecycle (place/refresh/
flatten-on-unprotected) is core Broker work — the geometry is emitted
as Intent stop/target data. See ports/legends_ema.md.

Strategy (old module): from the prior RTH session's 15m bars with the
EMA(20) warmed over the prior 5 sessions: trend = |close-open| / range
of the session; trend_day when trend >= TREND_Q80 (0.7686); no_touch
when NO 15m bar of the session touches its EMA value. Armed = trend_day
AND no_touch. Entry at the next session's open window (09:30-09:45 ET
cutoff in the old runner — a core execution detail). Exit geometry:
TP at the EMA target, stop = 0.5 x ATR14 (mean RTH high-low of the
prior 14 sessions) normalized — never a fixed-point stop. Qty =
(equity x 0.25%) // (0.5 x ATR14). Flat by 15:59 ET.

Inputs via context.extra (master-desk):
  "bars_15m": {"QQQ": [15m bars]} — the :00/:15/:30/:45 RTH grid (setup
      session + 5 warmup weekdays; the current session for the TP refresh)
  "forming": {"QQQ": {"o": open print, ...}} — today's open (the entry ref)
  "nyse_holidays", "session_close" — prior session / early-close flat
  "sleeve_state": {"QQQ": {"position": {...} | None, "pending_entry"}}
Bars (arg): daily QQQ bars — ATR14 = mean high-low of the 14 sessions
  dated <= the setup session.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")
SYMBOL = "QQQ"
RISK_FRACTION = 0.0025
EMA_SPAN = 20
WARMUP_SESSIONS = 5
ATR_SESSIONS = 14
STOP_ATR_MULT = 0.5
TREND_Q80 = 0.7686
FLAT_HM = (15, 59)
ENTRY_OPEN_HM = (9, 30)
ENTRY_CUTOFF_HM = (9, 45)

CONFIG = SleeveConfig(
    sleeve_id="legends_ema", cadence_s=300, universe=(SYMBOL,),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


def ema(values, span):
    """Verbatim old ema: seeded at the first value."""
    k = 2.0 / (span + 1.0)
    out = []
    v = values[0]
    for x in values:
        v = x * k + v * (1 - k) if out else x
        out.append(v)
    return out


def evaluate_setup(sessions_bars, daily_ranges):
    """Verbatim port of _evaluate_setup_inner's math on pre-aggregated
    15m sessions. Returns the setup dict or None (fail closed)."""
    if not sessions_bars:
        return None
    setup_bars = sessions_bars[-1]
    all_bars = [b for sess in sessions_bars for b in sess]
    if len(setup_bars) < 10 or len(all_bars) < EMA_SPAN + 2:
        return None
    emas = ema([float(b["c"]) for b in all_bars], EMA_SPAN)
    setup_emas = emas[len(all_bars) - len(setup_bars):]
    sess_o = float(setup_bars[0]["o"])
    sess_c = float(setup_bars[-1]["c"])
    sess_h = max(float(b["h"]) for b in setup_bars)
    sess_l = min(float(b["l"]) for b in setup_bars)
    rng = sess_h - sess_l
    trend = (abs(sess_c - sess_o) / rng) if rng > 0 else 0.0
    no_touch = not any(float(b["l"]) <= e <= float(b["h"])
                       for b, e in zip(setup_bars, setup_emas))
    ranges = [float(r) for r in (daily_ranges or [])][-ATR_SESSIONS:]
    atr14 = sum(ranges) / len(ranges) if len(ranges) == ATR_SESSIONS else None
    if atr14 is None:
        return None
    return {"trend": trend, "trend_day": trend >= TREND_Q80,
            "no_touch": no_touch, "ema_last": setup_emas[-1],
            "atr14": atr14, "n_bars": len(setup_bars),
            "warmup_bars": len(all_bars),
            "direction": "buy" if sess_c >= sess_o else "sell"}


def exit_geometry(side, ref, ema_ref, atr14):
    """Verbatim: TP at the EMA target; stop normalized 0.5 x ATR14."""
    stop_dist = STOP_ATR_MULT * atr14
    tp = round(ema_ref, 2)
    sl = round(ref - stop_dist if side == "buy" else ref + stop_dist, 2)
    return tp, sl


# ---------------------------------------------------------------- master-desk: the old runtime, restored
from datetime import date, timedelta  # noqa: E402

REFRESH_DEADBAND = 0.20        # old: the EMA must move >= $0.20 before the take-profit is refreshed
COMPLETED_GRACE_S = 930        # old current_ema_target: a 15m bar counts once 15m + 30s old
TARGET_SESSIONS = 2            # old current_ema_target warms the in-session EMA with 2 prior sessions


def _et(t):
    return datetime.fromtimestamp(float(t), tz=ET)


def _b15(extra):
    """context.extra['bars_15m']: {SYMBOL: [15m bars]} (the adapter's @bars:15m) or the bare list."""
    b = extra.get("bars_15m")
    return b.get(SYMBOL) if isinstance(b, dict) else b


def _rth_bar(b):
    """old: a 15m bar whose start lies in 09:30 <= t < 15:59 ET (rth_session_bounds, end - 1 minute)."""
    t = _et(b["t"])
    return (9, 30) <= (t.hour, t.minute) < (15, 59)


def _sessions(bars15):
    out = {}
    for b in bars15 or ():
        if _rth_bar(b):
            out.setdefault(_et(b["t"]).date().isoformat(), []).append(b)
    return out


def _prev_td(d, holidays=()):
    p = d - timedelta(days=1)
    while p.weekday() >= 5 or p.isoformat() in holidays:
        p -= timedelta(days=1)
    return p


def _weekdays_back(d, n):
    """old sessions_back: the n weekdays before d (a holiday among them simply has no bars)."""
    out = []
    while len(out) < n:
        d -= timedelta(days=1)
        if d.weekday() < 5:
            out.append(d.isoformat())
    return out


def setup_for(bars15, daily, today, holidays=()):
    """old main(): the setup is the PRIOR RTH session's (trend day + no EMA touch), the EMA warmed over the 5
    sessions before it, ATR14 = mean high-low of the last 14 daily bars dated <= the setup session.
    Returns (setup | None, setup_day)."""
    by = _sessions(bars15)
    setup_day = _prev_td(today, holidays).isoformat()
    if setup_day not in by:
        return None, setup_day                      # the setup session's bars are missing: fail closed
    warm = set(_weekdays_back(date.fromisoformat(setup_day), WARMUP_SESSIONS))
    sessions = [by[d] for d in sorted(by) if d in warm] + [by[setup_day]]
    ranges = [float(b["h"]) - float(b["l"]) for b in daily or ()
              if _et(float(b["t"]) + 4 * 3600).date().isoformat() <= setup_day
              and _et(float(b["t"]) + 4 * 3600).date() < today]
    return evaluate_setup(sessions, ranges), setup_day


def current_ema_target(bars15, now, holidays=()):
    """old current_ema_target: EMA(20) of the last completed 15m RTH bar, warmed with the 2 prior sessions."""
    today = _et(now).date()
    first = date.fromisoformat(min(_weekdays_back(today, TARGET_SESSIONS)))
    bl = [b for b in bars15 or () if _rth_bar(b) and first <= _et(b["t"]).date() <= today
          and now - float(b["t"]) >= COMPLETED_GRACE_S]
    if len(bl) < EMA_SPAN:
        return None
    return ema([float(b["c"]) for b in bl], EMA_SPAN)[-1]


def _flat_hm(context):
    """old: 15:59 ET; on an early close, 5 minutes before it."""
    sc = (context.extra or {}).get("session_close")
    if sc:
        c = _et(sc)
        if (c.hour, c.minute) < (16, 0):
            m = c.hour * 60 + c.minute - 5
            return (m // 60, m % 60)
    return FLAT_HM


def exit_levels(bars, slice_state, context):
    """old TP refresh: the take-profit follows the current EMA target once it moves >= $0.20 (engine target)."""
    extra = context.extra or {}
    pos = ((extra.get("sleeve_state") or {}).get(SYMBOL) or {}).get("position")
    now_et = _et(context.now)
    if not pos or pos.get("exit_submitted") or (now_et.hour, now_et.minute) >= _flat_hm(context):
        return {}
    tp = pos.get("target_px")
    tgt = current_ema_target(_b15(extra), float(context.now), set(extra.get("nyse_holidays") or ()))
    if tgt is None or tp is None or abs(tgt - float(tp)) < REFRESH_DEADBAND:
        return {}
    return {SYMBOL: {"target": tgt, "reason": "legends_ema TP refresh %.2f -> %.4f" % (float(tp), tgt)}}


class LegendsEma(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        """master-desk: the old legends_ema pass. Held: flat at 15:59 ET (5 min before an early close).
        Flat, 09:30-09:45 ET, setup armed: enter TOWARD the EMA at the open (open above the setup EMA -> short,
        below -> long), qty = equity x 0.25% // (0.5 x ATR14); take-profit at the setup EMA (refreshed by
        exit_levels), stop 0.5 x ATR14 from the fill. One trade per session. Desk-wide gates the old runner
        layered on (risk gate, context gate, Decision #75 long gate / short chart staging, 150% cap) are out
        of scope by the cutover doctrine."""
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        st = state.get(SYMBOL) or {}
        pos = st.get("position")
        now_et = _et(context.now)
        hm = (now_et.hour, now_et.minute)
        intents = []
        if pos:
            qty = abs(float(pos.get("qty") or 0))
            if qty > 0 and hm >= _flat_hm(context) and not pos.get("exit_submitted"):
                intents.append(Intent("exit", SYMBOL, qty=qty, signal_key="%s:%s:flat" % (SYMBOL, context.session),
                                      reason="legends_ema: flat by %02d:%02d ET" % _flat_hm(context)))
            return intents
        if st.get("pending_entry") or not (ENTRY_OPEN_HM <= hm < ENTRY_CUTOFF_HM):
            return intents
        holidays = set(extra.get("nyse_holidays") or ())
        setup, setup_day = setup_for(_b15(extra), bars.get(SYMBOL), date.fromisoformat(context.session),
                                     holidays)
        if not setup or not setup["atr14"] or not (setup["trend_day"] and setup["no_touch"]):
            return intents                            # armed = trend_day AND no_touch (verbatim)
        fb = (extra.get("forming") or {}).get(SYMBOL)
        if not fb or not fb.get("o"):
            return intents                            # old: entry_skipped_no_open_print
        ref = float(fb["o"])
        ema_ref = setup["ema_last"]
        side = "sell" if ref > ema_ref else "buy"     # toward the EMA
        equity = float(context.equity or 0.0)
        stop_dist = STOP_ATR_MULT * setup["atr14"]
        if equity <= 0:
            return intents
        qty = int((equity * RISK_FRACTION) // stop_dist)
        if qty < 1:
            return intents                            # old: skip_size (done for the day)
        tp, _sl = exit_geometry(side, ref, ema_ref, setup["atr14"])
        intents.append(Intent(
            "enter", SYMBOL, side="long" if side == "buy" else "short", qty_hint=qty, price_hint=round(ref, 2),
            target=tp, exit_rules=(ExitRule("stop_dist", stop_dist),),
            order={"not_after": float(context.now) + 240},     # old wait_for_fill: 240 s, then cancel (done)
            signal_key="%s:%s:lema" % (SYMBOL, context.session),
            position_meta={"setup_day": setup_day, "ema_ref": round(ema_ref, 4), "atr14": round(setup["atr14"], 4)},
            reason="legends_ema armed (%s): trend=%.4f >= %.4f, no_touch, open %.2f %s EMA %.2f, atr14=%.2f"
                   % (setup_day, setup["trend"], TREND_Q80, ref, "above" if side == "sell" else "below", ema_ref,
                      setup["atr14"])))
        return intents


def signal(bars, slice_state, context):
    return LegendsEma().signal(bars, slice_state, context)
