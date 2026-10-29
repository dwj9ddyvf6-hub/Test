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

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig

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


# ---------------------------------------------------------------- master-desk: the old runtime, restored
from zoneinfo import ZoneInfo  # noqa: E402

from . import leader_core  # noqa: E402
from . import sleeve_core as core  # noqa: E402

ET = ZoneInfo("America/New_York")
RANK_HM = (16, 50)            # old cron leader-sc-rank Mon-Fri 16:50 ET
FILL_HM = (10, 50)            # old cron leader-sc-fill Mon-Fri 10:50 ET


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
    """old mode_rank: the point-in-time small-cap band (bottom decile of the genome by trailing-52w mean
    weekly dollar volume; weekly = the daily bars accumulated by Monday) through the shared leader rank law.
    No SPY regime gate (the femto port had added one). Returns (pending, last_event, band, signals)."""
    extra = context.extra or {}
    band = band_symbols({s: bl for s, bl in bars.items() if bl}, context.session)
    pending, last_ev, signals = leader_core.rank(bars, extra.get("sleeve_state") or {}, meta, events,
                                                 context.session, band)
    return pending, last_ev, band, signals


class LeaderSc(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        """master-desk: the old two-phase runtime — the 16:50 rank stages pending (next_meta), the 10:50 fill
        executes it through the old sleeve_core fill law (150bp modeled, -25% disaster stop)."""
        if _phase(context) != "fill":
            return []
        extra = context.extra or {}
        meta = extra.get("meta") or {}
        close_ts = datetime.fromtimestamp(float(context.now), tz=ET).replace(hour=16, minute=0, second=0,
                                                                             microsecond=0).timestamp()
        intents, _left = core.fill_intents(Intent, extra.get("sleeve_state") or {}, meta.get("pending") or {},
                                           float(context.equity or 0.0), extra.get("quotes") or {}, COST_BPS_SIDE,
                                           context.session, float(context.now), "leader_sc", close_ts,
                                           disaster_stop=DISASTER_STOP)
        return intents


def next_meta(bars, slice_state, context, intents=()):
    extra = context.extra or {}
    meta = dict(extra.get("meta") or {})
    ph = _phase(context)
    if ph == "rank" and meta.get("last_rank_date") != context.session:
        events = extra.get("leader_events")
        if events is not None:
            pending, last_ev, band, signals = rank(bars, context, meta, events)
            meta.update(pending=pending, last_event=last_ev, last_rank_date=context.session, band_size=len(band),
                        last_signals=len(signals))
    elif ph == "fill":
        _s, _b, left = core.fill(extra.get("sleeve_state") or {}, meta.get("pending") or {},
                                 float(context.equity or 0.0), extra.get("quotes") or {}, COST_BPS_SIDE,
                                 context.session, float(context.now), "leader_sc")
        meta["pending"] = left
    return meta


def signal(bars, slice_state, context):
    return LeaderSc().signal(bars, slice_state, context)
