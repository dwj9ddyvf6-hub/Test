"""bta_onebar_qqq sleeve: the Breakout Trading Academy one bar system.

Provenance: X post by Breakout Trading Academy (verified account,
handle shown truncated as @onl... in the screenshot supplied on
2026-10-30), installed by owner order 2026-10-30. Edge status:
UNPROVEN; the live paper record is the test and no backtest is
claimed. The post's profitability, equity curve (about $210,000),
costs, slippage, contract count and test period are NOT verifiable
from the post. Full analysis: research_notes/onebar-family-2026-10-30/
ANALYSIS.md in the workspace.

Rules, as translated to this desk (frozen):

  * 30-minute bars. Channel = highest high and lowest low of the
    prior 50 completed bars (a Donchian channel), excluding the
    bar being evaluated.
  * Long entry: buy stop at the channel high. Short entry: sell
    stop at the channel low. Both may be armed; the first fill
    wins; one position at a time per symbol. Fill price modelled
    as the channel level, or the bar open when the bar gaps past
    the level. If one bar spans BOTH channel extremes, OHLC data
    cannot say which stop touched first, so no entry is taken
    on that bar (named choice, see ANALYSIS.md).
  * Exit: at the open of the next bar after the entry bar. Fill
    during bar T, exit at the open of bar T+1. No target.
  * Protective stop, the translated $1,000: 1 NQ point is $20, so
    $1,000 is 50 NQ points; at the frozen 25,000 reference index
    level that is 0.20 percent of entry price. STOP_PCT = 0.0020.
    Long stop = entry x (1 - STOP_PCT); short = entry x (1 +
    STOP_PCT). Executed by the dispatcher from ExitRule data.
  * Sizing: the $10,000 slice is the notional cap and the binding
    constraint: qty = floor(slice equity / entry price). At that
    size the modelled stop risk is 0.20 percent of the slice,
    the same fraction the original risks on one contract's
    notional ($1,000 on $500,000). No leverage.
  * Max 2 entries per day per symbol, counted by the entry bar's
    ET date. No re-entry in the same bar after an exit.

Session: this base sleeve consumes every completed 30-minute bar
in the desk warm product for QQQ (Alpaca SIP, cash session
centred). It does NOT reproduce the futures 24-hour session; no
overnight futures bars exist in that product and none are
invented. The RTH variant (bta_onebar_rth) restricts to regular
session bars.

Desk execution note: the core models the intrabar stop fill; the
live dispatcher fills an entry intent at the next available price
after the entry bar completes, so the live fill generally lands
near the open of bar T+1 and the exit near the open of bar T+2.
The one bar holding period is preserved.

State (per symbol plan, per symbol daily entry counts, last exit
bar) is carried in ctx.extra["onebar_state"] and round-tripped by
the adapter, which persists it beside the sleeve journal.
"""
from __future__ import annotations

import math
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")

CHANNEL_BARS = 50
BAR_SECONDS = 1800
STOP_PCT = 0.0020
MAX_ENTRIES_PER_DAY = 2
RTH_START = dtime(9, 30)
RTH_END = dtime(16, 0)
RTH_FLAT_TIME = dtime(15, 55)

CONFIG = SleeveConfig(
    sleeve_id="bta_onebar_qqq",
    cadence_s=60,
    universe=("QQQ",),
    state_schema={"onebar_state": "dict", "position": "dict|None"},
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


def clean_bars(raw, now, rth_only=False):
    """Completed 30-minute bars only, sorted and deduped. A bar
    counts only once its 30-minute period has ended as of `now`,
    so a forming bar never reaches the channel or a trigger."""
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
        if rth_only:
            dt = datetime.fromtimestamp(t, tz=ET)
            if dt.time() < RTH_START or dt.time() >= RTH_END:
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


def channel(prior_bars):
    """(channel_high, channel_low) of exactly the prior bars given,
    or None when fewer than CHANNEL_BARS are supplied."""
    if not prior_bars or len(prior_bars) < CHANNEL_BARS:
        return None
    window = prior_bars[-CHANNEL_BARS:]
    return (max(b["h"] for b in window), min(b["l"] for b in window))


def stop_price(direction, entry):
    if direction == 1:
        return round(entry * (1.0 - STOP_PCT), 4)
    return round(entry * (1.0 + STOP_PCT), 4)


def _et_date(ts):
    return datetime.fromtimestamp(ts, tz=ET).date().isoformat()


class BtaOnebarQqqSleeve(BaseSleeve):
    CONFIG = CONFIG
    SLEEVE_ID = "bta_onebar_qqq"
    SYMBOLS = ("QQQ",)
    RTH_ONLY = False

    def signal(self, bars, slice_state, ctx):
        extra = ctx.extra or {}
        state = dict(extra.get("onebar_state") or {})
        state.setdefault("plans", {})
        state.setdefault("entries", {})
        state.setdefault("last_exit_bar", {})
        self.onebar_state = state
        self.last_evaluation = {"sleeve": self.SLEEVE_ID,
                                "session": ctx.session, "state": "scanning"}
        intents = []
        for sym in self.SYMBOLS:
            intents.extend(self._signal_symbol(sym, bars, slice_state, ctx, state))
        return intents

    # ------------------------------------------------------------ per symbol
    def _signal_symbol(self, sym, bars, slice_state, ctx, state):
        raw = (bars or {}).get(sym) or []
        bars_clean = clean_bars(raw, ctx.now, rth_only=self.RTH_ONLY)
        qty_open = _number((slice_state or {}).get(sym)) or 0.0
        plans = state["plans"]
        plan = plans.get(sym)
        now_dt = datetime.fromtimestamp(ctx.now, tz=ET)
        ev = self.last_evaluation

        # An exit the desk already executed: clear the plan.
        if plan and qty_open == 0 and plan.get("seen_open"):
            plans.pop(sym, None)
            plan = None
            ev[sym] = "exit_observed_plan_cleared"

        # Manage an open position.
        if plan and qty_open != 0:
            plan["seen_open"] = True
            if not bars_clean:
                ev[sym] = "position_open_no_bars"
                return []
            latest = bars_clean[-1]
            rth_flat = (self.RTH_ONLY and now_dt.time() >= RTH_FLAT_TIME)
            if plan.get("exit_emitted_bar") == latest["t"] and not rth_flat:
                ev[sym] = "exit_already_emitted_this_bar"
                return []
            if latest["t"] > float(plan["entry_bar_t"]) or rth_flat:
                plan["exit_emitted_bar"] = latest["t"]
                state["last_exit_bar"][sym] = latest["t"]
                ev[sym] = "onebar_exit" if not rth_flat else "rth_flat_1555_exit"
                reason = (f"{self.SLEEVE_ID} one-bar exit at next bar open: {sym}"
                          if not rth_flat else
                          f"{self.SLEEVE_ID} RTH flat 15:55 ET exit: {sym}")
                px = latest["o"] if not rth_flat else latest["c"]
                return [self._exit(sym, latest, abs(qty_open), qty_open, px, reason)]
            ev[sym] = "position_open_entry_bar"
            return []
        if plan and qty_open == 0:
            ev[sym] = "awaiting_fill"
            return []
        if qty_open != 0:
            if self.RTH_ONLY and now_dt.time() >= RTH_FLAT_TIME and bars_clean:
                latest = bars_clean[-1]
                state["last_exit_bar"][sym] = latest["t"]
                ev[sym] = "rth_flat_1555_exit_no_plan"
                return [self._exit(sym, latest, abs(qty_open), qty_open,
                                   latest["c"],
                                   f"{self.SLEEVE_ID} RTH flat 15:55 ET exit (plan unavailable): {sym}")]
            ev[sym] = "position_open_no_plan"
            return []

        # Entries.
        if len(bars_clean) < CHANNEL_BARS + 1:
            ev[sym] = "channel_forming"
            return []
        latest = bars_clean[-1]
        entry_date = _et_date(latest["t"])
        if entry_date != ctx.session:
            ev[sym] = "latest_bar_not_current_session"
            return []
        if float(state.get("last_exit_bar", {}).get(sym) or 0) == latest["t"]:
            ev[sym] = "no_reentry_same_bar_after_exit"
            return []
        ent = (state["entries"].get(sym) or {})
        count = int(ent.get("count") or 0) if ent.get("date") == entry_date else 0
        if count >= MAX_ENTRIES_PER_DAY:
            ev[sym] = "daily_entry_cap_reached"
            return []
        ch = channel(bars_clean[:-1])
        if ch is None:
            ev[sym] = "channel_forming"
            return []
        ch_high, ch_low = ch
        long_trigger = latest["h"] >= ch_high
        short_trigger = latest["l"] <= ch_low
        if long_trigger and short_trigger:
            ev[sym] = "both_extremes_same_bar_no_entry"
            return []
        if not long_trigger and not short_trigger:
            ev[sym] = "no_breakout"
            return []
        direction = 1 if long_trigger else -1
        if direction == 1:
            entry = max(ch_high, latest["o"])
        else:
            entry = min(ch_low, latest["o"])
        equity = _number(ctx.equity) or 0.0
        if equity <= 0:
            ev[sym] = "blocked_equity_unavailable"
            return []
        qty = int(math.floor(equity / entry))
        if qty <= 0:
            ev[sym] = "blocked_size_zero"
            return []
        stop = stop_price(direction, entry)
        plans[sym] = {"direction": direction, "entry": entry, "stop": stop,
                      "entry_bar_t": latest["t"], "session": entry_date,
                      "seen_open": False, "exit_emitted_bar": None}
        state["entries"][sym] = {"date": entry_date, "count": count + 1}
        ev[sym] = "entry_intent"
        side = "buy" if direction == 1 else "sell"
        reason = (f"{self.SLEEVE_ID} one-bar {'long' if direction == 1 else 'short'} "
                  f"{sym}: channel={ch_low:.4f}-{ch_high:.4f}; entry={entry:.4f}; "
                  f"stop={stop:.4f}; qty={qty}")
        return [Intent(
            "enter", sym, qty=qty, price_hint=round(entry, 4),
            stop=stop, target=None,
            exit_rules=(ExitRule("stop", stop),),
            reason=reason, side=side,
            position_intent="buy_to_open" if direction == 1 else "sell_to_open",
            signal_date=entry_date)]

    def _exit(self, sym, bar, qty, signed_qty, px, reason):
        return Intent("exit", sym, qty=float(qty),
                      price_hint=round(float(px), 4) if px else None,
                      reason=reason,
                      side="buy" if signed_qty < 0 else "sell",
                      position_intent="buy_to_close" if signed_qty < 0
                      else "sell_to_close")


_INSTANCE = BtaOnebarQqqSleeve()


def signal(bars, slice_state, context):
    out = _INSTANCE.signal(bars, slice_state, context)
    signal.last_evaluation = _INSTANCE.last_evaluation
    signal.onebar_state = _INSTANCE.onebar_state
    return out
