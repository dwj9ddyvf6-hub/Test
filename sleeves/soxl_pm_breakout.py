"""soxl_pm_breakout sleeve: SOXL premarket-high breakout, hold to close.

Provenance: TrendSpider shared strategy "SOXL: PM-high breakout,
hold to close" (published 2026-11-03), commissioned as a paper
sleeve by owner order 2026-11-03 ("Make it a sleeve"). The rules
were frozen and replicated on the desk's own SIP tape BEFORE this
install: research_notes/trendspider-soxl-pmhigh-test-20261103/
(SPEC-FREEZE.md, REPORT.md). Replication verdict PARTIAL: a real
but thin per-trade edge (1,116 trades 2016-2026, cost-case average
+0.263 percent, PF 1.29), vendor headline NOT reproduced, and the
strategy trails SOXL buy-and-hold over the full span. Edge status
on this desk: UNPROVEN until its live paper record says otherwise;
the live record is the test.

Rules, frozen exactly as replicated (SPEC-FREEZE items 2-7):

  * 15-minute SIP bars, all sessions. Premarket segment = bars
    starting 04:00 through 09:15 ET. Premarket high = the highest
    high of today's premarket bars. A day with no premarket bars
    is untradable.
  * Entry (first qualifying bar only, one entry per day): a
    regular-session bar whose CLOSE is above today's premarket
    high, whose volume is at least 1.5x its 20-bar SMA of volume
    (RTH bars only, including the signal bar, rolling across
    days), and whose close time is at or before 14:15 ET. The
    intent is emitted on the completed signal bar; the desk
    dispatcher fills at the next available price, the live
    equivalent of the replication's next-bar-open fill.
  * Exit: hold to close. No stop, no target. The sleeve emits its
    exit intent at the first evaluation at or after 15:45 ET with
    the position open (the config row also carries flat_by_close
    with flatten_time_et 15:45). No overnight holds, ever.
  * Sizing: the $10,000 slice is the notional cap: qty =
    floor(slice equity / signal close). No leverage.

Feed boundary, named: the desk warm product serves no SOXL 15Min
slice today (desk3/warm.py INTRADAY_FETCHES carries no SOXL entry
and desk3/producers_g4.py _BARS_TF_KEYS carries no bars:SOXL:15Min
key), so until a producer supplies that key this sleeve is UNFED
by name in the cycle health roll, by design, never silently
abstaining. When the slice exists, the adapter consumes
ctx.bars("SOXL", "15Min", N) exactly as the bta_onebar family
consumes its 30Min product, and the premarket bars ride the same
all-session SIP fetch the QQQ 15Min lane already uses.

State (plan, per-day entry counts) is carried in
ctx.extra["soxl_state"] and round-tripped by the adapter, which
persists it beside the sleeve journal.
"""
from __future__ import annotations

import math
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

from core.sleeve import BaseSleeve, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")

BAR_SECONDS = 900
VOLUME_SMA_BARS = 20
VOLUME_MULT = 1.5
CUTOFF_CLOSE = dtime(14, 15)      # signal bar close time <= 14:15 ET
EXIT_TIME = dtime(15, 45)         # exit intent from 15:45 ET
PM_START = dtime(4, 0)
PM_LAST_START = dtime(9, 15)
RTH_START = dtime(9, 30)
RTH_LAST_START = dtime(15, 45)

CONFIG = SleeveConfig(
    sleeve_id="soxl_pm_breakout",
    cadence_s=60,
    universe=("SOXL",),
    state_schema={"soxl_state": "dict", "position": "dict|None"},
    parked=False,
)


def _number(v):
    if isinstance(v, bool):
        return None
    try:
        out = float(v)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def _epoch(v):
    n = _number(v)
    if n is not None:
        return n / 1000.0 if n > 1.0e12 else n
    if not isinstance(v, str):
        return None
    try:
        p = datetime.fromisoformat(v.replace("Z", "+00:00"))
        from datetime import timezone
        if p.tzinfo is None:
            p = p.replace(tzinfo=timezone.utc)
        return p.timestamp()
    except (TypeError, ValueError, OverflowError):
        return None


def clean_bars(raw, now):
    """Completed 15-minute bars only (all sessions), sorted and
    deduped. A bar counts only once its 15-minute period has ended
    as of `now`, so a forming bar never reaches a trigger."""
    out = []
    for row in raw or []:
        if not isinstance(row, dict):
            continue
        t = _epoch(row.get("t"))
        o, h, l, c = (_number(row.get(k)) for k in ("o", "h", "l", "c"))
        v = _number(row.get("v")) or 0.0
        if None in (t, o, h, l, c) or min(o, h, l, c) <= 0 or h < l:
            continue
        if t + BAR_SECONDS > now:
            continue
        out.append({"t": t, "o": o, "h": h, "l": l, "c": c, "v": v})
    out.sort(key=lambda b: b["t"])
    deduped = []
    for b in out:
        if deduped and b["t"] == deduped[-1]["t"]:
            deduped[-1] = b
        else:
            deduped.append(b)
    return deduped


def _et(ts):
    return datetime.fromtimestamp(ts, tz=ET)


def is_premarket(bar):
    t = _et(bar["t"]).time()
    return PM_START <= t <= PM_LAST_START


def is_rth(bar):
    t = _et(bar["t"]).time()
    return RTH_START <= t <= RTH_LAST_START


def premarket_high(bars, et_date):
    """Highest high of the ET date's premarket bars, or None when
    the day has no premarket bars (the day is then untradable)."""
    highs = [b["h"] for b in bars
             if is_premarket(b) and _et(b["t"]).date().isoformat() == et_date]
    return max(highs) if highs else None


def volume_sma20(rth_bars, idx):
    """20-bar SMA of volume over the RTH series including index
    `idx`, rolling across days; None until 20 bars exist."""
    if idx < VOLUME_SMA_BARS - 1:
        return None
    window = rth_bars[idx - VOLUME_SMA_BARS + 1: idx + 1]
    return sum(b["v"] for b in window) / VOLUME_SMA_BARS


def first_breakout(rth_today, pmh, rth_all):
    """The first of today's RTH bars (in order) meeting every entry
    condition, or None. `rth_all` is the full RTH series (for the
    rolling volume SMA indices)."""
    index_of = {b["t"]: i for i, b in enumerate(rth_all)}
    for bar in rth_today:
        close_time = _et(bar["t"] + BAR_SECONDS).time()
        if close_time > CUTOFF_CLOSE:
            break
        sma = volume_sma20(rth_all, index_of[bar["t"]])
        if sma is None:
            continue
        if bar["c"] > pmh and bar["v"] >= VOLUME_MULT * sma:
            return bar
    return None


class SoxlPmBreakoutSleeve(BaseSleeve):
    CONFIG = CONFIG
    SLEEVE_ID = "soxl_pm_breakout"
    SYMBOLS = ("SOXL",)

    def signal(self, bars, slice_state, ctx):
        extra = ctx.extra or {}
        state = dict(extra.get("soxl_state") or {})
        state.setdefault("plan", None)
        state.setdefault("entries", {})
        self.soxl_state = state
        ev = {"sleeve": self.SLEEVE_ID, "session": ctx.session,
              "state": "scanning"}
        self.last_evaluation = ev
        sym = "SOXL"
        raw = (bars or {}).get(sym) or []
        clean = clean_bars(raw, ctx.now)
        qty_open = _number((slice_state or {}).get(sym)) or 0.0
        plan = state.get("plan")
        now_dt = _et(ctx.now)

        # An exit the desk already executed: clear the plan.
        if plan and qty_open == 0 and plan.get("seen_open"):
            state["plan"] = None
            plan = None
            ev[sym] = "exit_observed_plan_cleared"

        # Manage an open position: hold to close, exit from 15:45 ET.
        if qty_open != 0:
            if plan:
                plan["seen_open"] = True
            overdue = plan is not None and plan.get("session") != ctx.session
            if now_dt.time() >= EXIT_TIME or overdue:
                if plan is not None and plan.get("exit_emitted_at") == ctx.now:
                    ev[sym] = "exit_already_emitted"
                    return []
                if plan is not None:
                    plan["exit_emitted_at"] = ctx.now
                px = clean[-1]["c"] if clean else None
                ev[sym] = "hold_to_close_exit" if not overdue else \
                    "overdue_exit_prior_session_position"
                reason = (f"{self.SLEEVE_ID} hold-to-close exit {sym}: "
                          f"exit from 15:45 ET per frozen spec"
                          if not overdue else
                          f"{self.SLEEVE_ID} overdue exit {sym}: position "
                          f"from a prior session, no overnight holds")
                return [Intent("exit", sym, qty=float(abs(qty_open)),
                               price_hint=round(px, 4) if px else None,
                               reason=reason, side="sell",
                               position_intent="sell_to_close")]
            ev[sym] = "position_open_holding_to_close"
            return []

        if plan:
            if plan.get("session") == ctx.session:
                ev[sym] = "awaiting_fill"
                return []
            # A plan from a prior session that never filled is dead.
            state["plan"] = None
            plan = None
            ev[sym] = "stale_plan_cleared"

        # Entries.
        entries = state["entries"]
        count = int((entries.get(ctx.session) or {}).get("count") or 0)
        if count >= 1:
            ev[sym] = "daily_entry_cap_reached"
            return []
        rth_all = [b for b in clean if is_rth(b)]
        rth_today = [b for b in rth_all
                     if _et(b["t"]).date().isoformat() == ctx.session]
        if not rth_today:
            ev[sym] = "no_rth_bars_today"
            return []
        pmh = premarket_high(clean, ctx.session)
        if pmh is None:
            ev[sym] = "no_premarket_bars_untradable"
            return []
        hit = first_breakout(rth_today, pmh, rth_all)
        if hit is None:
            ev[sym] = "no_qualifying_breakout"
            return []
        latest = rth_today[-1]
        if hit["t"] != latest["t"]:
            ev[sym] = "first_breakout_bar_already_past"
            return []
        equity = _number(ctx.equity) or 0.0
        if equity <= 0:
            ev[sym] = "blocked_equity_unavailable"
            return []
        qty = int(math.floor(equity / hit["c"]))
        if qty <= 0:
            ev[sym] = "blocked_size_zero"
            return []
        sma = volume_sma20(rth_all, len(rth_all) - 1
                           if rth_all[-1]["t"] == hit["t"] else
                           [b["t"] for b in rth_all].index(hit["t"]))
        state["plan"] = {"signal_close": hit["c"], "pmh": pmh,
                         "signal_bar_t": hit["t"], "session": ctx.session,
                         "seen_open": False, "exit_emitted_at": None}
        entries[ctx.session] = {"count": count + 1}
        ev[sym] = "entry_intent"
        reason = (f"{self.SLEEVE_ID} PM-high breakout long {sym}: "
                  f"close={hit['c']:.4f} > pm_high={pmh:.4f}; "
                  f"vol={hit['v']:.0f} >= 1.5 x sma20="
                  f"{(VOLUME_MULT * sma) if sma else 0:.0f}; "
                  f"qty={qty}; hold to close, exit from 15:45 ET")
        return [Intent("enter", sym, qty=qty,
                       price_hint=round(hit["c"], 4),
                       reason=reason, side="buy",
                       position_intent="buy_to_open",
                       signal_date=ctx.session)]


_INSTANCE = SoxlPmBreakoutSleeve()


def signal(bars, slice_state, context):
    out = _INSTANCE.signal(bars, slice_state, context)
    signal.last_evaluation = _INSTANCE.last_evaluation
    signal.soxl_state = _INSTANCE.soxl_state
    return out
