"""investandbefree_dmac — double-MACD multi-timeframe alignment options
sleeve (INVESTANDBEFREE-DMAC-SPEC-2026-10-29, FROZEN 2026-10-29).

Provenance (see the desk spec doc for the full labels): the
double-MACD pair (Wilder + exponential), the long-term stack
(4H / daily / weekly), alignment/dominance as concepts, crossover
and curl triggers, long-premium-only construction, the +100%
partial-into-runner management and the daily-layer hold are
extracted from public material about the vendor method. Recreated
defaults frozen here: periods 12/26/9, ATM strike, the 30-calendar-
day expiry bound, the 50% premium stop, the USD 2,000 budget with a
25% slice cap, the 10% spread gate, the exact alignment/dominance/
curl step forms, the 5-DTE runner bound. Deviations from the source
SPEC: no ladder fallback, no overbought/oversold runner exit, no
event-calendar gate (named in the desk spec doc).

Edge status: UNPROVEN. An extraction is not a backtest; the live
paper record is the test. No backtest is claimed by this module.

Closed bars only, enforced here: signal() filters every timeframe
through closed_bars() against Context.now before any MACD is
computed (a bar counts only once its period has ended; the 4H
stack is aggregated from closed 1Hour bars only), and the adapter
applies the same filter at the desk boundary.

Pure core: no files, no broker, no clock except Context.now. State
(the open-position plan per underlying, including the partial-done
flag and contract identity) travels through ctx.extra["sleeve_state"]
in the capitulation_options shape {SYM: {"position": {...}}} plus
ctx.extra["dmac_state"] for the partial flag and direction, which
the adapter round-trips to disk; the core itself keeps the same
state on self.dmac_state for the adapter to persist.

MACD smoothing detail: both MACDs are built from a fast and a slow
smoothed series; the signal line is smoothed the same way as its
own MACD. Series are seeded with the simple mean of the first
`period` values (the standard textbook seed for both EMA and
Wilder smoothing); before the seed index the series is None. A MACD
line value exists only once the slow series exists (index 25 for
12/26); a signal value exists once 9 MACD values exist (index 33).
"""
from __future__ import annotations

import math
from datetime import date as _date
from datetime import datetime, time as _dtime, timedelta
from zoneinfo import ZoneInfo

from core.sleeve import BaseSleeve, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")

SYMBOLS = ("SPY", "QQQ")
FAST, SLOW, SIGNAL = 12, 26, 9
PREMIUM_BUDGET_USD = 2000.0
PREMIUM_CAP_FRAC = 0.25
QUOTE_GATE_FRAC = 0.10
MIN_DTE = 30
PREMIUM_STOP_FRAC = 0.50
PARTIAL_TRIGGER_MULT = 2.0  # +100% over entry
RUNNER_EXIT_DTE = 5
RTH_START = _dtime(9, 30)
RTH_END = _dtime(16, 0)

CONFIG = SleeveConfig(
    sleeve_id="investandbefree_dmac",
    cadence_s=3600,
    universe=SYMBOLS,
    state_schema={"sleeve_state": "dict", "dmac_state": "dict"},
    parked=False,
)


# ------------------------------------------------------------------ utils
def _number(v):
    if isinstance(v, bool):
        return None
    try:
        out = float(v)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def _closes(bars):
    out = []
    for row in bars or []:
        if not isinstance(row, dict):
            continue
        c = _number(row.get("c"))
        if c is not None and c > 0:
            out.append(c)
    return out


def _bar_time(row):
    t = row.get("t")
    n = _number(t)
    if n is not None:
        return n / 1000.0 if n > 1.0e12 else n
    if isinstance(t, str):
        try:
            p = datetime.fromisoformat(t.replace("Z", "+00:00"))
            from datetime import timezone
            if p.tzinfo is None:
                p = p.replace(tzinfo=timezone.utc)
            return p.timestamp()
        except (TypeError, ValueError, OverflowError):
            return None
    return None


def _period_end(t, timeframe):
    """Epoch second at which the bar starting at `t` is complete.
    1Hour bars end one hour after their start. 1Day bars are dated
    by their ET session date and end at the next ET midnight.
    1Week bars belong to the ET week (Monday-anchored) of their
    date and end at the next Monday 00:00 ET."""
    if timeframe == "1Hour":
        return t + 3600.0
    dt = datetime.fromtimestamp(t, tz=ET)
    if timeframe == "1Week":
        end_day = dt.date() - timedelta(days=dt.weekday()) \
            + timedelta(days=7)
    else:  # 1Day
        end_day = dt.date() + timedelta(days=1)
    return datetime.combine(end_day, _dtime.min, tzinfo=ET).timestamp()


def closed_bars(bars, timeframe, now):
    """The frozen spec's closed-bars-only rule: keep only bars
    whose period has ended as of `now` (epoch seconds, from
    Context.now). A bar with no readable timestamp cannot be
    proven closed and is dropped. Applied in signal() to every
    timeframe (daily, weekly, and the 1Hour bars the 4H stack is
    aggregated from) and again in the adapter at the desk
    boundary, so a forming bar can never reach the MACDs."""
    out = []
    for row in bars or []:
        if not isinstance(row, dict):
            continue
        t = _bar_time(row)
        if t is None:
            continue
        if _period_end(t, timeframe) <= float(now):
            out.append(row)
    return out


# ------------------------------------------------------------- smoothing
def _smooth(values, period, wilder):
    """Smoothed series, None before the seed index (period - 1).
    Seed = simple mean of the first `period` values. Exponential:
    alpha = 2/(period+1). Wilder: alpha = 1/period."""
    out = [None] * len(values)
    if len(values) < period:
        return out
    alpha = 1.0 / period if wilder else 2.0 / (period + 1)
    prev = sum(values[:period]) / period
    out[period - 1] = prev
    for i in range(period, len(values)):
        prev = prev + alpha * (values[i] - prev)
        out[i] = prev
    return out


def ema_exponential(values, period=FAST):
    """Standard exponential smoothing (MACD-E component)."""
    return _smooth(list(values), period, wilder=False)


def ema_wilder(values, period=FAST):
    """Wilder smoothing (MACD-W component)."""
    return _smooth(list(values), period, wilder=True)


def macd_series(closes, wilder):
    """(macd_line, signal_line) aligned to `closes`; None where
    undefined. The signal line is smoothed with the same method as
    the MACD it smooths."""
    closes = list(closes)
    fast = _smooth(closes, FAST, wilder)
    slow = _smooth(closes, SLOW, wilder)
    macd = [None] * len(closes)
    for i, (f, s) in enumerate(zip(fast, slow)):
        if f is not None and s is not None:
            macd[i] = f - s
    # Signal: smooth the defined MACD values as a series, then map
    # back to absolute indices (seed = mean of the first 9 MACD vals).
    defined = [(i, v) for i, v in enumerate(macd) if v is not None]
    vals = [v for _, v in defined]
    sig_vals = _smooth(vals, SIGNAL, wilder)
    signal = [None] * len(closes)
    for (i, _), sv in zip(defined, sig_vals):
        signal[i] = sv
    return macd, signal


def alignment_of(closes):
    """+1 bullish, -1 bearish, None otherwise (either MACD pair
    unaligned, equal to its signal, or too short). Uses the LAST
    value of each series only."""
    if len(closes) < SLOW + SIGNAL:
        return None
    dirs = []
    for wilder in (True, False):
        macd, signal = macd_series(closes, wilder)
        m, s = macd[-1], signal[-1]
        if m is None or s is None or m == s:
            return None
        dirs.append(1 if m > s else -1)
    return dirs[0] if dirs[0] == dirs[1] else None


def aggregate_4h(hourly_bars):
    """RTH 4H buckets from 1H bars. RTH bars only (ET bar start
    09:30-16:00), grouped by ET session date, chunked in consecutive
    groups of 4 hourly bars anchored at the session's first RTH bar;
    a bucket is emitted only when it holds exactly 4 consecutive
    hourly bars (3600s apart). Output bars carry t of the last bar,
    o of the first, h/l extremes, c of the last, summed volume."""
    rows = []
    for row in hourly_bars or []:
        if not isinstance(row, dict):
            continue
        t = _bar_time(row)
        vals = [_number(row.get(k)) for k in ("o", "h", "l", "c")]
        if t is None or any(v is None for v in vals):
            continue
        dt = datetime.fromtimestamp(t, tz=ET)
        if not (RTH_START <= dt.time() < RTH_END):
            continue
        rows.append({"t": t, "o": vals[0], "h": vals[1], "l": vals[2],
                     "c": vals[3], "v": _number(row.get("v")) or 0.0})
    rows.sort(key=lambda b: b["t"])
    by_day = {}
    for b in rows:
        by_day.setdefault(datetime.fromtimestamp(b["t"], tz=ET).date(), []).append(b)
    out = []
    for day in sorted(by_day):
        bars = by_day[day]
        for i in range(0, len(bars) - 3, 4):
            chunk = bars[i:i + 4]
            if len(chunk) != 4:
                continue
            if any(chunk[j + 1]["t"] - chunk[j]["t"] != 3600 for j in range(3)):
                continue
            out.append({"t": chunk[-1]["t"], "o": chunk[0]["o"],
                        "h": max(b["h"] for b in chunk),
                        "l": min(b["l"] for b in chunk),
                        "c": chunk[-1]["c"],
                        "v": sum(b["v"] for b in chunk)})
    return out


def evaluate_timeframes(daily_closes, weekly_closes, h4_closes):
    """Per-timeframe alignments and dominance. Returns a dict with
    keys weekly/daily/h4 (directions or None), dominant_tf and
    dominant_dir (slowest aligned timeframe, or None)."""
    dirs = {"weekly": alignment_of(weekly_closes),
            "daily": alignment_of(daily_closes),
            "h4": alignment_of(h4_closes)}
    dominant_tf = dominant_dir = None
    for tf in ("weekly", "daily", "h4"):
        if dirs[tf] is not None:
            dominant_tf, dominant_dir = tf, dirs[tf]
            break
    return {**dirs, "dominant_tf": dominant_tf, "dominant_dir": dominant_dir}


def _crossed(closes, direction, wilder):
    """True when MACD(-wilder) crosses its signal in `direction` on
    the last closed bar: previous diff against-or-zero, last diff
    strictly into the direction."""
    macd, signal = macd_series(closes, wilder)
    if len(macd) < 2 or macd[-1] is None or macd[-2] is None \
            or signal[-1] is None or signal[-2] is None:
        return False
    prev = macd[-2] - signal[-2]
    last = macd[-1] - signal[-1]
    if direction == 1:
        return prev <= 0 and last > 0
    return prev >= 0 and last < 0


def _curl(closes, direction, wilder):
    """True when the MACD line's last step is into `direction` and at
    least one of the two preceding steps was against `direction`
    (a pullback followed by a curl back). Needs 4 defined values."""
    macd, _ = macd_series(closes, wilder)
    vals = [v for v in macd if v is not None]
    if len(vals) < 4:
        return False
    steps = [vals[-1] - vals[-2], vals[-2] - vals[-3], vals[-3] - vals[-4]]
    if direction == 1:
        return steps[0] > 0 and any(s < 0 for s in steps[1:])
    return steps[0] < 0 and any(s > 0 for s in steps[1:])


def find_trigger(daily_closes, direction):
    """'crossover' if MACD-E crosses its signal in `direction` on the
    last closed daily bar, else 'curl' if MACD-W or MACD-E curls back
    into `direction` after a pullback, else None."""
    if _crossed(daily_closes, direction, wilder=False):
        return "crossover"
    if _curl(daily_closes, direction, wilder=True) or \
            _curl(daily_closes, direction, wilder=False):
        return "curl"
    return None


# ------------------------------------------------------------ contracts
def _row_right(row):
    r = str(row.get("right") or row.get("type") or "").lower()
    if r in ("call", "c"):
        return "call"
    if r in ("put", "p"):
        return "put"
    occ = str(row.get("symbol") or row.get("occ") or "")
    if len(occ) >= 9 and occ[-9] in ("C", "P"):
        return "call" if occ[-9] == "C" else "put"
    return None


def _row_expiry(row):
    for key in ("expiry", "expiration", "expiration_date"):
        v = row.get(key)
        if v:
            return str(v)[:10]
    return None


def _dte(expiry, session_iso):
    try:
        return (_date.fromisoformat(expiry) - _date.fromisoformat(session_iso)).days
    except (TypeError, ValueError):
        return None


def select_contract(chain, quotes, spot, session_iso, direction):
    """Nearest expiry >= 30 calendar days out, then nearest-to-the-
    money strike (ties: lower strike), for the direction's right.
    Returns None when no chain row passes the quote gate:
    ask > 0, bid > 0, (ask-bid)/mid <= 0.10. Result carries occ,
    strike, expiry, bid, ask, mid."""
    want = "call" if direction == 1 else "put"
    cands = []
    for row in chain or []:
        if not isinstance(row, dict):
            continue
        if _row_right(row) != want:
            continue
        expiry = _row_expiry(row)
        strike = _number(row.get("strike"))
        occ = row.get("symbol") or row.get("occ")
        if expiry is None or strike is None or not occ:
            continue
        dte = _dte(expiry, session_iso)
        if dte is None or dte < MIN_DTE:
            continue
        q = (quotes or {}).get(occ) or {}
        bid = _number(q.get("bid")) if q.get("bid") is not None else _number(row.get("bid"))
        ask = _number(q.get("ask")) if q.get("ask") is not None else _number(row.get("ask"))
        if ask is None or ask <= 0 or bid is None or bid <= 0:
            continue
        mid = (ask + bid) / 2.0
        if (ask - bid) / mid > QUOTE_GATE_FRAC:
            continue
        cands.append({"occ": occ, "strike": strike, "expiry": expiry,
                      "bid": bid, "ask": ask, "mid": mid, "dte": dte})
    if not cands:
        return None
    best_expiry = min(c["dte"] for c in cands)
    at_exp = [c for c in cands if c["dte"] == best_expiry]
    return min(at_exp, key=lambda c: (abs(c["strike"] - spot), c["strike"]))


def qty_for_position(ask, capital):
    """floor(budget / (ask x 100)), capped so total premium stays
    within 25% of slice capital; 0 when one contract alone exceeds
    the hard cap or inputs are invalid."""
    if not ask or ask <= 0 or not capital or capital <= 0:
        return 0
    cap = PREMIUM_CAP_FRAC * capital
    if ask * 100.0 > cap:
        return 0
    qty = int(math.floor(PREMIUM_BUDGET_USD / (ask * 100.0)))
    qty = min(qty, int(math.floor(cap / (ask * 100.0))))
    return max(0, qty)


def partial_qty(qty, entry_premium, current_premium):
    """Contracts to sell to recover the full original premium when
    current >= 2x entry, else None. Always leaves >= 1 runner; qty 1
    is a full exit. Returns 0 only when no partial is due."""
    if qty <= 0 or entry_premium <= 0 or current_premium is None:
        return 0
    if current_premium < PARTIAL_TRIGGER_MULT * entry_premium:
        return 0
    sell = int(math.ceil(qty * entry_premium / current_premium))
    if qty == 1:
        return 1
    return max(1, min(sell, qty - 1))


# ---------------------------------------------------------------- sleeve
class InvestAndBeFreeDmacSleeve(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, ctx):
        extra = ctx.extra or {}
        sleeve_state = extra.get("sleeve_state") or {}
        dmac_state = dict(extra.get("dmac_state") or {})
        self.dmac_state = dmac_state
        self.last_evaluation = {"sleeve": CONFIG.sleeve_id,
                                "session": ctx.session, "state": "scanning"}
        weekly_map = extra.get("bars_weekly") or {}
        h1_map = extra.get("bars_1h") or {}
        chains = extra.get("chains") or {}
        quotes = extra.get("quotes") or {}
        equity = _number(ctx.equity) or 0.0
        intents = []
        now = float(ctx.now)
        for sym in SYMBOLS:
            daily = closed_bars(bars.get(sym) or [], "1Day", now)
            daily_closes = _closes(daily)
            weekly_closes = _closes(closed_bars(
                weekly_map.get(sym) or [], "1Week", now))
            h4 = aggregate_4h(closed_bars(
                h1_map.get(sym) or [], "1Hour", now))
            h4_closes = _closes(h4)
            frames = evaluate_timeframes(daily_closes, weekly_closes, h4_closes)
            st = sleeve_state.get(sym) or {}
            pos = st.get("position") if isinstance(st, dict) else None
            if pos:
                out = self._manage(sym, pos, frames, daily_closes,
                                   quotes, ctx.session)
                if out is not None:
                    intents.append(out)
                continue
            if not daily:
                continue
            if frames["dominant_dir"] is None or frames["daily"] is None:
                self.last_evaluation.setdefault("blocked", {})[sym] = \
                    "no_alignment_or_dominance"
                continue
            if frames["dominant_dir"] != frames["daily"]:
                self.last_evaluation.setdefault("blocked", {})[sym] = \
                    "dominant_daily_disagreement"
                continue
            direction = frames["daily"]
            trigger = find_trigger(daily_closes, direction)
            if trigger is None:
                continue
            spot = daily_closes[-1]
            sel = select_contract(chains.get(sym), quotes, spot,
                                  ctx.session, direction)
            if sel is None:
                self.last_evaluation.setdefault("blocked", {})[sym] = \
                    "no_qualifying_contract"
                continue
            qty = qty_for_position(sel["ask"], equity)
            if qty <= 0:
                self.last_evaluation.setdefault("blocked", {})[sym] = \
                    "sizing_zero_or_cap"
                continue
            plan = {"occ": sel["occ"], "strike": sel["strike"],
                    "expiry": sel["expiry"], "entry_premium": sel["ask"],
                    "qty": qty, "direction": direction,
                    "partial_done": False}
            dmac_state[sym] = plan
            self.last_evaluation["state"] = "entry_intent"
            intents.append(Intent(
                "enter", sym, qty=qty, price_hint=round(spot, 2),
                reason="investandbefree_dmac %s %s: occ=%s strike=%.2f "
                       "expiry=%s ask=%.2f qty=%d trigger=%s dominant=%s"
                       % ("long_call" if direction == 1 else "long_put",
                          sym, sel["occ"], sel["strike"], sel["expiry"],
                          sel["ask"], qty, trigger, frames["dominant_tf"]),
                side="buy", position_intent="buy_to_open",
                signal_date=ctx.session))
        self.dmac_state = dmac_state
        return intents

    def _manage(self, sym, pos, frames, daily_closes, quotes, session):
        """One exit intent, or None. Order: premium stop, dominant
        break, partial (+100%), runner exit (MACD-E cross against or
        5 DTE). An alignment reading of None (no alignment on that
        layer, including a complete loss of alignment on every
        timeframe) counts as a break, not as 'no change': exit rule
        (2) is a break of the alignment the position was opened
        under. The runner ignores 4H flips while daily alignment
        holds: only a daily alignment break (flip or loss) closes
        it on alignment."""
        qty = int(float(pos.get("qty") or 0))
        if qty <= 0:
            return None
        occ = pos.get("occ")
        entry = _number(pos.get("entry_premium")) or 0.0
        direction = int(pos.get("direction") or 1)
        partial_done = bool(pos.get("partial_done"))
        q = (quotes or {}).get(occ) or {}
        bid, ask = _number(q.get("bid")), _number(q.get("ask"))
        mid = (bid + ask) / 2.0 if bid and ask else None
        dte = _dte(pos.get("expiry"), session) if pos.get("expiry") else None
        reason = None
        sell_qty = qty
        if mid is not None and entry > 0 and mid <= PREMIUM_STOP_FRAC * entry:
            reason = "premium_stop_50pct"
        elif not partial_done and frames["dominant_dir"] != direction:
            reason = "dominant_alignment_break"
        elif partial_done and frames["daily"] != direction:
            reason = "daily_alignment_break_runner"
        elif not partial_done and mid is not None and entry > 0:
            sell = partial_qty(qty, entry, mid)
            if sell:
                if sell >= qty:
                    reason = "partial_full_exit_qty1"
                else:
                    reason = "partial_100pct"
                    sell_qty = sell
        if reason is None and partial_done:
            if _crossed(daily_closes, -direction, wilder=False):
                reason = "runner_macde_cross_against"
            elif dte is not None and dte <= RUNNER_EXIT_DTE:
                reason = "runner_5dte"
        if reason is None:
            self.last_evaluation["state"] = "position_open"
            return None
        if reason == "partial_100pct":
            self.dmac_state.setdefault(sym, {})["partial_done"] = True
            self.last_evaluation["state"] = "partial_exit"
        else:
            self.dmac_state.pop(sym, None)
            self.last_evaluation["state"] = "exit"
        return Intent(
            "exit", sym, qty=sell_qty, price_hint=round(mid, 2) if mid else None,
            reason="investandbefree_dmac exit: %s occ=%s qty=%d"
                   % (reason, occ, sell_qty),
            side="sell", position_intent="sell_to_close")


_INSTANCE = InvestAndBeFreeDmacSleeve()


def signal(bars, slice_state, context):
    out = _INSTANCE.signal(bars, slice_state, context)
    signal.last_evaluation = _INSTANCE.last_evaluation
    signal.dmac_state = _INSTANCE.dmac_state
    return out
