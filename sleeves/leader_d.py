"""Leader Daily — lean-desk port.

EXTRACTED from the old desk's leader_d_sleeve.py. The event detector
(the leader1d research frame: score >= 3 AND gate on the latest closed
daily bar, >= 252 bars) is a research-module computation; in the lean
desk it arrives as a core Data product via context.extra (named
misfit, ports/leader_d.md). Everything downstream of the event —
SPY-down-regime gating, dedupe by last_event, capacity, the 20-bar
hold with the one-session-early sell staging — is ported verbatim.

Old facts: signals fire ONLY in a SPY down regime (sleeve_core
spy_down_regime); SPY itself excluded; sell staged when the count of
bars after the entry date >= HOLD_BARS - 1 (2026-10-07 fix: fills land
the next morning, so staging at 19 puts the exit on the 20th session);
MAX_POSITIONS 10 (sleeve_core); -25% disaster stop (Decision #18);
cost model 5bp/side.

Inputs via context.extra:
  "leader_events": {SYM: "YYYY-MM-DD"} — latest gated event date per
                   symbol from the core Data/research-frame product
  "spy_down_regime": bool (core Data product)
  "sleeve_state": {SYM: {"position": {"entry_px","entry_date","qty"} | None}}
  "last_event": {SYM: "YYYY-MM-DD"} (core-persisted dedupe)
Bars: daily dicts {"t","o","h","l","c","v"} ascending.
"""
from datetime import datetime, timezone

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

HOLD_BARS = 20
MIN_BARS = 252
MAX_POSITIONS = 10
DISASTER_STOP = 0.25
COST_BPS_SIDE = 0.0005

CONFIG = SleeveConfig(
    sleeve_id="leader_d", cadence_s=300, universe=(),
    state_schema={"position": "dict|None", "last_event": "dict"},
    risk_pct=None)


def _dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


def enhance_enabled(extra):
    """ENH leader_d (IMPROVE-leader_d): stale-event refusal switch,
    ctx.extra['leader_d_enhance']['enabled'], default ON; OFF restores
    the pre-change rule exactly (any unconsumed event enters)."""
    ov = (extra or {}).get("leader_d_enhance")
    if isinstance(ov, dict) and "enabled" in ov:
        return bool(ov["enabled"])
    if isinstance(ov, bool):
        return ov
    return True


def sell_due(bars, entry_date):
    """Verbatim old staging rule: bars strictly after entry >= 19."""
    if not entry_date or not bars:
        return False
    n = sum(1 for d in _dates(bars) if d > entry_date)
    return n >= HOLD_BARS - 1


class LeaderD(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        last_event = extra.get("last_event") or {}
        events = extra.get("leader_events") or {}
        equity = float(context.equity or 0.0)
        intents = []
        self._paired = []
        self.last_evaluation = {"sleeve": "leader_d",
                                "enhance_switch": enhance_enabled(extra),
                                "paired": self._paired}
        book = {s: (state.get(s) or {}).get("position")
                for s in state if (state.get(s) or {}).get("position")}
        for sym, p in book.items():
            if sell_due(bars.get(sym) or [], p.get("entry_date")):
                qty = int(float(p.get("qty") or 0))
                if qty > 0:
                    bl = bars.get(sym) or []
                    px = round(float(bl[-1]["c"]), 2) if bl else None
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty, price_hint=px,
                        reason="leader_d hold complete: bars_after_entry >= %d"
                               % (HOLD_BARS - 1)))
        if equity <= 0 or not extra.get("spy_down_regime"):
            return intents
        room = MAX_POSITIONS - len(book)
        for sym in sorted(events):
            if room <= 0:
                break
            if sym == "SPY" or sym in book:
                continue
            bl = bars.get(sym) or []
            if len(bl) < MIN_BARS:
                continue
            ev = events[sym]
            if last_event.get(sym) == ev:
                continue
            # ENH: refuse when the event date is not the latest served
            # daily bar's date (the frame defines its event on the
            # latest closed bar). Paired control recorded; refusal
            # does not consume the event.
            enh_on = enhance_enabled(extra)
            latest_date = _dates(bl)[-1]
            stale = str(ev) != latest_date
            self._paired.append({
                "symbol": sym, "event": ev, "latest_bar_date": latest_date,
                "control": "enter",
                "treatment": "refuse_stale" if (enh_on and stale) else "enter",
                "switch_on": enh_on})
            if enh_on and stale:
                continue
            px = float(bl[-1]["c"])
            if px <= 0:
                continue
            qty = int((equity * 0.01) // px)
            if qty < 1:
                # OBS-1 (ruling 2026-10-22): the sleeve's own
                # sizing is the law — a budget that buys
                # nothing takes no position. No forced floor.
                continue
            stop_px = round(px * (1 - DISASTER_STOP), 2)
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(px, 2),
                stop=stop_px,
                exit_rules=(ExitRule("stop", stop_px),
                            ExitRule("time_bars", float(HOLD_BARS))),
                reason="leader_d event %s in SPY down regime (score>=3 & gate)"
                       % ev))
            room -= 1
        return intents


def signal(bars, slice_state, context):
    return LeaderD().signal(bars, slice_state, context)
