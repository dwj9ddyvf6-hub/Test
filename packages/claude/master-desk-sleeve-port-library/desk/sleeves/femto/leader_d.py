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

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig

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


def sell_due(bars, entry_date):
    """Verbatim old staging rule: bars strictly after entry >= 19."""
    if not entry_date or not bars:
        return False
    n = sum(1 for d in _dates(bars) if d > entry_date)
    return n >= HOLD_BARS - 1


# ---------------------------------------------------------------- master-desk: the old runtime, restored
from datetime import date, timedelta  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

from . import sleeve_core as core  # noqa: E402

ET = ZoneInfo("America/New_York")
RANK_HM = (16, 40)            # old cron leader-d-rank Mon-Fri 16:40 ET (after the close)
FILL_HM = (10, 40)            # old cron leader-d-fill Mon-Fri 10:40 ET


def spy_down_regime(spy_bars, asof):
    """old core.spy_down_regime: trailing-60-session SPY return <= 0 (B8); None with < 61 sessions."""
    sc = [b for b in spy_bars or () if _dates([b])[0] <= asof]
    if len(sc) < 61:
        return None
    c0, c1 = float(sc[-61]["c"]), float(sc[-1]["c"])
    if not c0 or not c1:
        return None
    return (c1 / c0 - 1) <= 0


def _phase(context):
    t = datetime.fromtimestamp(float(context.now), tz=ET)
    if t.weekday() >= 5:
        return None
    if (t.hour, t.minute) >= RANK_HM:
        return "rank"
    if FILL_HM <= (t.hour, t.minute) < (16, 0):
        return "fill"
    return None


def rank(bars, context, meta, events):
    """old mode_rank: in a SPY down regime, the genome names (not SPY) through the shared leader rank law.
    Returns (pending, last_event, down, signals)."""
    from . import leader_core
    extra = context.extra or {}
    down = spy_down_regime(bars.get("SPY"), context.session)
    cands = [s for s in bars if s != "SPY"] if down else []
    pending, last_ev, signals = leader_core.rank(bars, extra.get("sleeve_state") or {}, meta, events,
                                                 context.session, cands)
    return pending, last_ev, down, signals


class LeaderD(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        """master-desk: the old two-phase runtime — the 16:40 rank stages pending (next_meta), the 10:40 fill
        executes it through the old sleeve_core fill law (5bp modeled, -25% disaster stop)."""
        if _phase(context) != "fill":
            return []
        extra = context.extra or {}
        meta = extra.get("meta") or {}
        close_ts = datetime.fromtimestamp(float(context.now), tz=ET).replace(hour=16, minute=0, second=0,
                                                                             microsecond=0).timestamp()
        intents, _left = core.fill_intents(Intent, extra.get("sleeve_state") or {}, meta.get("pending") or {},
                                           float(context.equity or 0.0), extra.get("quotes") or {}, COST_BPS_SIDE,
                                           context.session, float(context.now), "leader_d", close_ts,
                                           disaster_stop=DISASTER_STOP)
        return intents


def next_meta(bars, slice_state, context, intents=()):
    extra = context.extra or {}
    meta = dict(extra.get("meta") or {})
    ph = _phase(context)
    if ph == "rank" and meta.get("last_rank_date") != context.session:
        events = extra.get("leader_events")
        if events is not None:                         # the genome job has computed today's frames
            pending, last_ev, down, signals = rank(bars, context, meta, events)
            meta.update(pending=pending, last_event=last_ev, last_rank_date=context.session,
                        spy_down_regime=down, last_signals=len(signals))
    elif ph == "fill":
        _s, _b, left = core.fill(extra.get("sleeve_state") or {}, meta.get("pending") or {},
                                 float(context.equity or 0.0), extra.get("quotes") or {}, COST_BPS_SIDE,
                                 context.session, float(context.now), "leader_d")
        meta["pending"] = left
    return meta


def signal(bars, slice_state, context):
    return LeaderD().signal(bars, slice_state, context)
