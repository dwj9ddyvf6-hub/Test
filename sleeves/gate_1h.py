"""Gate 1H — lean-desk port. (A STRATEGY named 'Gate 1H'; not the
core chart gate.)

EXTRACTED from the old desk's gate_1h_sleeve.py. The gated daily event
(leader1d research frame: score >= 3 AND gate, >= 252 daily bars) is a
core Data product here (named misfit, ports/gate_1h.md); the 1H timing
logic — first RTH 1H bar strictly after the event date, 20-bar
de-overlap, 20-bar hold counted on the RTH 1H grid — is ported
verbatim. -25% disaster stop (2026-10-10 audit, Decision #18);
MAX_POSITIONS 10 (sleeve_core).

Old grid law (2026-10-07 HIGH fix): HOLD/DEOVERLAP bars count on the
RTH-only 1H grid (13:00-19:00Z bar starts); core Data must supply
RTH-filtered 1H bars in extra["bars_1h"] — the saved cache convention
keeps full bars, the signal read filters (core Data's job now).

Inputs via context.extra:
  "leader_events": {SYM: "YYYY-MM-DD"} (daily gated events)
  "bars_1h": {SYM: [RTH 1H bar dicts {"t","o","h","l","c","v"}]}
  "sleeve_state": {SYM: {"position": {"entry_px","entry_bar_t","qty"} | None}}
  "last_event": {SYM: "YYYY-MM-DD"}, "last_entry_bar": {SYM: t}
Bars (arg): daily dicts for the 42-name basket (SIVEF excluded by the
old basket reader; the core supplies the universe).
"""
from datetime import date, datetime, timezone

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

HOLD_BARS = 20
DEOVERLAP_BARS = 20
MIN_BARS = 252
MAX_POSITIONS = 10
DISASTER_STOP = 0.25
COST_BPS_SIDE = 0.001

CONFIG = SleeveConfig(
    sleeve_id="gate_1h", cadence_s=300, universe=(),
    state_schema={"position": "dict|None", "last_event": "dict",
                  "last_entry_bar": "dict"},
    risk_pct=None)


def _h1_date(b):
    return datetime.fromtimestamp(float(b["t"]),
                                  tz=timezone.utc).date()


def enhance_enabled(extra):
    """ENH gate_1h (IMPROVE-gate_1h): stale-entry refusal switch,
    ctx.extra['gate_1h_enhance']['enabled'], default ON; OFF restores
    the pre-change rule exactly (enter at b0 whenever evaluated)."""
    ov = (extra or {}).get("gate_1h_enhance")
    if isinstance(ov, dict) and "enabled" in ov:
        return bool(ov["enabled"])
    if isinstance(ov, bool):
        return ov
    return True


def first_bar_after(h1, event_date):
    """First 1H bar strictly after event_date — verbatim old logic
    (bar's UTC date > event date on the RTH grid)."""
    ev = date.fromisoformat(event_date)
    for i, b in enumerate(h1):
        if _h1_date(b) > ev:
            return i
    return None


class Gate1H(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        last_event = extra.get("last_event") or {}
        last_entry_bar = extra.get("last_entry_bar") or {}
        events = extra.get("leader_events") or {}
        h1map = extra.get("bars_1h") or {}
        equity = float(context.equity or 0.0)
        intents = []
        self._paired = []
        self.last_evaluation = {"sleeve": "gate_1h",
                                "enhance_switch": enhance_enabled(extra),
                                "paired": self._paired}
        book = {s: (state.get(s) or {}).get("position")
                for s in state if (state.get(s) or {}).get("position")}
        # exits: >= HOLD_BARS 1H bars since the entry bar
        for sym, p in book.items():
            h1 = h1map.get(sym) or []
            entry_t = p.get("entry_bar_t")
            if not h1:
                continue
            if entry_t:
                try:
                    ei = next(i for i, b in enumerate(h1)
                              if float(b["t"]) >= float(entry_t))
                except StopIteration:
                    continue
            elif p.get("entry_date"):
                # Core dispatch records positions as {qty, entry_px,
                # entry_date, stop_px} — no entry_bar_t — so the old
                # branch stranded every core-recorded position (audit
                # 2026-10-15 batch 4). Fall back to the first RTH 1H
                # bar on/after the recorded entry session.
                try:
                    ed = date.fromisoformat(str(p["entry_date"])[:10])
                except ValueError:
                    continue
                ei = next((i for i, b in enumerate(h1)
                           if _h1_date(b) >= ed), None)
                if ei is None:
                    continue
            else:
                continue
            if len(h1) - 1 - ei >= HOLD_BARS:
                qty = int(float(p.get("qty") or 0))
                if qty > 0:
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty,
                        price_hint=round(float(h1[-1]["c"]), 2),
                        reason="gate_1h hold complete: %d 1H bars since entry"
                               % (len(h1) - 1 - ei)))
        if equity <= 0:
            return intents
        room = MAX_POSITIONS - len(book)
        for sym in sorted(events):
            if room <= 0:
                break
            if sym in book:
                continue
            dbl = bars.get(sym) or []
            if len(dbl) < MIN_BARS:
                continue
            ev = events[sym]
            if last_event.get(sym) == ev:
                continue
            h1 = h1map.get(sym) or []
            if len(h1) < HOLD_BARS + 2:
                continue
            b0 = first_bar_after(h1, ev)
            if b0 is None:
                continue
            # ENH: refuse when the first post-event bar is not the
            # latest served RTH 1H bar (designed entry moment passed).
            # Control (pre-change rule) is recorded paired on
            # self.last_evaluation; a refusal does not consume the
            # event (last_event is core-persisted from entries only).
            enh_on = enhance_enabled(extra)
            paired = getattr(self, "_paired", None)
            if paired is not None:
                paired.append({
                    "symbol": sym, "event": ev, "b0": b0,
                    "latest_idx": len(h1) - 1,
                    "control": "enter",
                    "treatment": "refuse_stale" if (enh_on and b0 < len(h1) - 1) else "enter",
                    "switch_on": enh_on})
            if enh_on and b0 < len(h1) - 1:
                continue
            prev_t = last_entry_bar.get(sym)
            if prev_t is not None:
                # AUDIT3-A2-03 (2026-10-16): core stamps
                # last_entry_bar with the TICK epoch (entry_bar_t =
                # the fill pass's now), never a bar's own timestamp
                # — the pre-cure exact-equality search therefore
                # never matched and the 20-bar de-overlap was dead
                # in live wiring. The entry bar is the last bar at
                # or before the stamp; count bars from it.
                try:
                    stamp = float(prev_t)
                    prev_i = None
                    for i, b in enumerate(h1):
                        if float(b["t"]) <= stamp:
                            prev_i = i
                        else:
                            break
                    if prev_i is not None \
                            and b0 - prev_i < DEOVERLAP_BARS:
                        continue
                except (TypeError, ValueError):
                    pass
            px = float(h1[b0]["o"])
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
                stop=stop_px, exit_rules=(ExitRule("stop", stop_px),),
                reason="gate_1h: event %s, entry at first 1H bar after "
                       "(bar_idx=%d)" % (ev, b0)))
            room -= 1
        return intents


def signal(bars, slice_state, context):
    return Gate1H().signal(bars, slice_state, context)
