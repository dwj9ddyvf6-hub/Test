"""Rule 1H Cyan Raw — lean-desk port (Wave C, GBM/Rule family).

EXTRACTED from the old desk's rule_1h_cyan_raw.py (rule
V3-1H-CYAN-RAW-H7-aab0a308). Fire detection is the external Node 1H scorer
(dcg_rule_1h.mjs) — fires arrive as a core Data product via context.extra
(a sleeve never shells out; ports/rule_1h_cyan_raw.md).

Rule (exact thresholds): 1H cyan fire AND signal-bar range >= 2.05 x
ATR14 (feature "rangeatr") AND WaveTrend spread (wt1-wt2, "wtgap") >=
6.88 AND SMH weekly uptrend ("smhUp" == 1). The old per-fire guards are
ported: non-dict fire rows, missing/non-numeric rangeatr/wtgap, and NaN
scores are SKIPPED per-fire (a NaN was truthy and False-comparing in the
pre-fix code — the BC14S-9 class).
Eligibility: $5+ and $1M 20-day dollar volume, point-in-time: dv20 from
the DAILY bars, ending at the latest daily bar <= the signal's ET session
date (the old 2026-10-06 fix — an exact-date match always missed intraday
and killed every signal; this sleeve had never traded on that bug).
Entry: next hourly bar after the signal bar. Hold: 7 hourly bars after
entry, counted with the old _bar_after law (a bare-date entry_time counts
only bars on a LATER ET date — pre-fill bars of the entry day never
count). Risk 0.1%. Universe: the old 41-name 1H basket (bars keys here).

Inputs via context.extra:
  "rule_fires_1h": {SYM: [{"t": iso-ts, "rangeatr": .., "wtgap": ..,
                    "smhUp": 0|1}]}   (Data product, 1H scorer)
  "daily_bars": {SYM: [daily bar dicts]}  (for the dv20 desk filter)
  "sleeve_state": {SYM: {"position": {"entry_date"|"entry_time","qty"} | None}}
Bars (the `bars` argument): 1H dicts {"t","o","h","l","c","v"} ascending,
"t" epoch seconds of the bar open. Only the latest CLOSED bar can be the
signal bar: the core delivers closed bars only; a fire whose "t" is not
the last bar's timestamp is ignored (old law).
"""
import math
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from . import sleeve_core as core
from .compat import BaseSleeve, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")

HOLD_BARS = 7
MIN_PX = 5.0
MIN_DV20 = 1_000_000
RANGE_ATR_MIN = 2.05
WTGAP_MIN = 6.88
RISK_FRACTION = 0.001
MAX_POSITIONS = 10

CONFIG = SleeveConfig(
    sleeve_id="rule_1h_cyan_raw", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


def _iso_t(epoch):
    return datetime.fromtimestamp(float(epoch), tz=timezone.utc).isoformat()


def _et_date_of_ts(epoch):
    return datetime.fromtimestamp(float(epoch), tz=ET).date().isoformat()


def bar_after(entry_t, bar_epoch):
    """Old _bar_after law, epoch form: True when the bar is strictly
    after the entry. A bare YYYY-MM-DD entry counts only bars whose ET
    date is LATER than the entry date (never same-day pre-fill bars)."""
    et = str(entry_t)
    if len(et) == 10:
        return _et_date_of_ts(bar_epoch) > et
    try:
        entry_epoch = datetime.fromisoformat(
            et.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return _iso_t(bar_epoch) > et
    return float(bar_epoch) > entry_epoch


def fire_passes(f):
    """(ok, rangeatr, wtgap): the rule conditions + per-fire NaN/type
    guards, verbatim in effect from the old rank loop."""
    if not isinstance(f, dict):
        return False, None, None
    try:
        ra = float(f.get("rangeatr"))
        wg = float(f.get("wtgap"))
    except (TypeError, ValueError):
        return False, None, None
    if not (math.isfinite(ra) and math.isfinite(wg)):
        return False, None, None
    if ra < RANGE_ATR_MIN or wg < WTGAP_MIN:
        return False, ra, wg
    if f.get("smhUp") != 1:
        return False, ra, wg
    return True, ra, wg


def dv20_daily(daily_bars, signal_date):
    """20d dollar volume ending at the latest daily bar <= signal_date
    (point-in-time; old 2026-10-06 fix). 0 when insufficient history."""
    if not daily_bars:
        return 0.0
    dates = [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                    tz=timezone.utc).date().isoformat()
             for b in daily_bars]
    idx = None
    for i, d in enumerate(dates):
        if d <= signal_date:
            idx = i
        else:
            break
    if idx is None or idx < 19:
        return 0.0
    return sum(float(b["c"]) * float(b["v"])
               for b in daily_bars[idx - 19:idx + 1]) / 20.0


COST_BPS_SIDE = 0.001


def _phase(context):
    """the old crons: fill hourly at :04, scan hourly at :26, 10:00-15:59 ET (main() skips other hours)."""
    t = datetime.fromtimestamp(float(context.now), tz=ET)
    if t.weekday() >= 5 or not (10 <= t.hour <= 15):
        return None
    return "rank" if t.minute >= 20 else "fill"


def _same_t(a, b):
    """the fire's bar start is the signal bar's (any ISO spelling of the same instant)."""
    if a == b:
        return True
    try:
        return abs(datetime.fromisoformat(str(a).replace("Z", "+00:00")).timestamp()
                   - datetime.fromisoformat(str(b).replace("Z", "+00:00")).timestamp()) < 1.0
    except ValueError:
        return False


def signals(bars_1h, daily, fires):
    """old mode_rank: fires on each name's latest closed 1H bar passing the rule, the signal bar's close $5+,
    the $1M dv20 ending at the latest daily bar <= the signal's ET date; the scorer's (symbol) order."""
    out = []
    for s in sorted(fires):
        bl = bars_1h.get(s) or []
        if len(bl) < 100:
            continue
        last_t = datetime.fromtimestamp(float(bl[-1]["t"]), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for f in fires.get(s) or []:
            if not isinstance(f, dict) or not _same_t(f.get("t"), last_t):
                continue
            ok, _ra, _wg = fire_passes(f)
            if not ok:
                continue
            if float(bl[-1]["c"]) < MIN_PX:
                continue
            if dv20_daily(daily.get(s) or [], _et_date_of_ts(bl[-1]["t"])) < MIN_DV20:
                continue
            out.append(s)
    return out


def rank(bars_1h, daily, fires, context, meta):
    extra = context.extra or {}
    state = extra.get("sleeve_state") or {}
    book = core.book_of(state)
    old = dict(meta.get("pending") or {})
    surv = list(old.get("buys") or [])
    buys, seen = [], set()
    for s in signals(bars_1h, daily, fires):
        if s in book or s in seen:
            continue
        if len(buys) + len(surv) + len(book) >= core.MAX_POSITIONS:
            break
        seen.add(s)
        buys.append(s)
    sells = []
    for s, p in book.items():
        bl = bars_1h.get(s) or []
        opened = p.get("opened_at")
        entry_t = _iso_t(opened) if opened else (p.get("entry_time") or p.get("entry_date"))
        if not entry_t or not bl:
            continue
        if sum(1 for b in bl if bar_after(entry_t, b["t"])) >= HOLD_BARS:
            sells.append(s)
    today = datetime.fromtimestamp(float(context.now), tz=ET).date()
    exit_dates = dict(old.get("exit_dates") or {})
    exit_dates.update({s: (today + timedelta(days=2)).isoformat() for s in buys})
    old_sells = list(old.get("sells") or [])
    return {"buys": core.merge_pending_buys(surv, buys, len(book)),
            "sells": old_sells + [s for s in sells if s not in old_sells], "exit_dates": exit_dates}


class Rule1hCyanRaw(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        """master-desk: the old hourly runtime — the :26 scan stages (next_meta), the :04 fill executes the old
        sleeve_core fill law (market, the day's session)."""
        if _phase(context) != "fill":
            return []
        extra = context.extra or {}
        close_ts = datetime.fromtimestamp(float(context.now), tz=ET).replace(hour=16, minute=0, second=0,
                                                                             microsecond=0).timestamp()
        intents, _left = core.fill_intents(Intent, extra.get("sleeve_state") or {},
                                           (extra.get("meta") or {}).get("pending") or {},
                                           float(context.equity or 0.0), extra.get("quotes") or {}, COST_BPS_SIDE,
                                           context.session, float(context.now), "rule_1h_cyan_raw", close_ts)
        return intents


def next_meta(bars, slice_state, context, intents=()):
    extra = context.extra or {}
    meta = dict(extra.get("meta") or {})
    ph = _phase(context)
    if ph == "rank":
        fires = extra.get("fires_1h")
        if fires is not None:
            meta["pending"] = rank(extra.get("bars_1h") or {}, bars, fires, context, meta)
            meta["last_rank"] = float(context.now)
    elif ph == "fill":
        _s, _b, left = core.fill(extra.get("sleeve_state") or {}, meta.get("pending") or {},
                                 float(context.equity or 0.0), extra.get("quotes") or {}, COST_BPS_SIDE,
                                 context.session, float(context.now), "rule_1h_cyan_raw")
        meta["pending"] = left
    return meta


def signal(bars, slice_state, context):
    return Rule1hCyanRaw().signal(bars, slice_state, context)
