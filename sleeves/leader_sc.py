"""Leader Small-Cap — lean-desk port.

EXTRACTED from the old desk's leader_sc_sleeve.py. Same leader-1d
event family as Leader Daily, restricted to the small-cap band:
band_symbols (bottom decile by trailing-52w mean weekly dollar
volume, point-in-time) is ported verbatim below — including the
2026-10-11 fix that ACCUMULATES weekly volume across the week's bars
instead of keeping only the last day's. The event frame itself is a
core Data product (named misfit, ports/leader_sc.md). Hold 20 bars
with the one-session-early sell staging; MAX_POSITIONS 10; -25%
disaster stop; cost model 150bp/side.

Inputs via context.extra:
  "leader_events": {SYM: "YYYY-MM-DD"}
  "spy_down_regime": bool
  "weekly": {SYM: [weekly bar dicts]} for the band computation
  "sleeve_state": {SYM: {"position": {...} | None}}
  "last_event": {SYM: "YYYY-MM-DD"}
Bars: daily dicts {"t","o","h","l","c","v"} ascending.
"""
from bisect import bisect_left
from datetime import date, datetime, timedelta, timezone

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

HOLD_BARS = 20
MIN_BARS = 252
BAND_FRAC = 0.10
MAX_POSITIONS = 10
DISASTER_STOP = 0.25
COST_BPS_SIDE = 0.015

CONFIG = SleeveConfig(
    sleeve_id="leader_sc", cadence_s=300, universe=(),
    state_schema={"position": "dict|None", "last_event": "dict"},
    risk_pct=None)


def _dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


def _bar_date(b):
    return datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                  tz=timezone.utc).date()


def monday_of(d):
    return d - timedelta(days=d.weekday())


def band_symbols(weekly, asof):
    """Verbatim port: bottom decile by trailing-52w mean wk$vol,
    point-in-time at `asof` (ISO date). Weekly volume accumulates
    across the week's bars (2026-10-11 fix)."""
    M = monday_of(date.fromisoformat(asof))
    cands = []
    for s, bl in weekly.items():
        mons, closes, vols = [], [], []
        for b in bl:
            m = monday_of(_bar_date(b))
            if m not in mons:
                mons.append(m)
                closes.append(float(b["c"]))
                vols.append(float(b["v"] or 0))
            else:
                i = mons.index(m)
                closes[i] = float(b["c"])
                vols[i] += float(b["v"] or 0)
        order = sorted(range(len(mons)), key=lambda i: mons[i])
        mons = [mons[i] for i in order]
        closes = [closes[i] for i in order]
        vols = [vols[i] for i in order]
        widx = bisect_left(mons, M) - 1
        if widx < 51:
            continue
        wsum = sum((closes[j] or 0) * (vols[j] or 0)
                   for j in range(widx - 51, widx + 1))
        cands.append((s, wsum / 52))
    if not cands:
        return set()
    cands.sort(key=lambda x: x[1])
    n_band = max(9, int(len(cands) * BAND_FRAC))
    return {s for s, _ in cands[:n_band]}


def sell_due(bars, entry_date):
    if not entry_date or not bars:
        return False
    n = sum(1 for d in _dates(bars) if d > entry_date)
    return n >= HOLD_BARS - 1


def band_means(weekly, asof):
    """{SYM: trailing-52w mean weekly dollar volume} — the quantities
    band_symbols already computes, exposed for the ENH sizing cap."""
    M = monday_of(date.fromisoformat(asof))
    out = {}
    for s, bl in weekly.items():
        mons, closes, vols = [], [], []
        for b in bl:
            m = monday_of(_bar_date(b))
            if m not in mons:
                mons.append(m)
                closes.append(float(b["c"]))
                vols.append(float(b["v"] or 0))
            else:
                i = mons.index(m)
                closes[i] = float(b["c"])
                vols[i] += float(b["v"] or 0)
        order = sorted(range(len(mons)), key=lambda i: mons[i])
        mons = [mons[i] for i in order]
        closes = [closes[i] for i in order]
        vols = [vols[i] for i in order]
        widx = bisect_left(mons, M) - 1
        if widx < 51:
            continue
        wsum = sum((closes[j] or 0) * (vols[j] or 0)
                   for j in range(widx - 51, widx + 1))
        out[s] = wsum / 52
    return out


def enhance_enabled(extra):
    """ENH leader_sc (IMPROVE-leader_sc): volume-cap switch,
    ctx.extra['leader_sc_enhance']['enabled'], default ON; OFF
    restores the pre-change flat-1% sizing exactly."""
    ov = (extra or {}).get("leader_sc_enhance")
    if isinstance(ov, dict) and "enabled" in ov:
        return bool(ov["enabled"])
    if isinstance(ov, bool):
        return ov
    return True


class LeaderSc(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        last_event = extra.get("last_event") or {}
        events = extra.get("leader_events") or {}
        weekly = extra.get("weekly") or {}
        equity = float(context.equity or 0.0)
        today = context.session
        intents = []
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
                        reason="leader_sc hold complete: bars_after_entry >= %d"
                               % (HOLD_BARS - 1)))
        if equity <= 0 or not extra.get("spy_down_regime") or not weekly:
            return intents
        enh_on = enhance_enabled(extra)
        self._paired = []
        self.last_evaluation = {"sleeve": "leader_sc",
                                "enhance_switch": enh_on,
                                "paired": self._paired}
        means = band_means(weekly, today)
        band = band_symbols(weekly, today)
        room = MAX_POSITIONS - len(book)
        for sym in sorted(events):
            if room <= 0:
                break
            if sym == "SPY" or sym in book or sym not in band:
                continue
            bl = bars.get(sym) or []
            if len(bl) < MIN_BARS:
                continue
            ev = events[sym]
            if last_event.get(sym) == ev:
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
            # ENH: cap the position at the name's mean daily dollar
            # volume (band-computed weekly mean / 5); refuse when the
            # cap buys nothing (OBS-1). Paired control = uncapped qty.
            if enh_on:
                daily_cap = (means.get(sym) or 0.0) / 5.0
                capped = min(qty, int(daily_cap // px))
                self._paired.append({
                    "symbol": sym, "mean_weekly_dollar_vol": means.get(sym),
                    "daily_cap_usd": daily_cap, "control_qty": qty,
                    "treatment_qty": capped, "switch_on": True})
                qty = capped
                if qty < 1:
                    continue
            else:
                self._paired.append({
                    "symbol": sym, "mean_weekly_dollar_vol": means.get(sym),
                    "control_qty": qty, "treatment_qty": qty,
                    "switch_on": False})
            stop_px = round(px * (1 - DISASTER_STOP), 2)
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(px, 2),
                stop=stop_px,
                exit_rules=(ExitRule("stop", stop_px),
                            ExitRule("time_bars", float(HOLD_BARS))),
                reason="leader_sc event %s in SPY down regime, small-cap band"
                       % ev))
            room -= 1
        return intents


def signal(bars, slice_state, context):
    return LeaderSc().signal(bars, slice_state, context)
