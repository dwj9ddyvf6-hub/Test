"""Rule 1D Green Turn-of-Month — lean-desk port (Wave C, GBM/Rule family).

EXTRACTED from the old desk's rule_1d_green_tom.py + rule_sleeve_base.py
(rule V4-1D-GREEN-RAW-H63-ALL-c10e07a0, tier A). Fire detection is the
external Node GBM rule scorer's — fires arrive as a core Data product via
context.extra (a sleeve never shells out; see ports/rule_1d_green_tom.md).

Rule: 1D green fire AND mom121 >= 0.6500771284103396 AND disp between
0.02075970731675625 and 0.02862246334552765 AND tom == 1.

TOM — EXACT NYSE TRADING-DAY LOGIC (the fixed version, Sweep #2 S2-B5-1,
ported verbatim in behavior): the scorer's tom feature is VACUOUS on the
live bar (always 1), so the old sleeve recomputed it from the calendar:
turn-of-month = the last trading day of the month OR one of the first 3
trading days of the month. First-3 is counted exactly off the market day
list; last-trading-day is decided by the NEXT trading day (weekday + NYSE
holiday calendar) falling in a new month. The calendar-day proxy
(day >= 28 or day <= 3) is NOT used — it fired on non-TOM month-end days
and missed real TOM bars (last trading day of Feb 2026 = the 27th; 3rd
trading day of Nov 2026 = the 4th). Holidays come from core.data
.nyse_holidays — the lean core's port of the old desk.nyse_calendar.

Entry: next session close after signal. Hold: 63 sessions; exit staged
at sessions_since >= HOLD-1 (old stage-one-early fix). Eligibility:
$5+ and $1M dv20 on the signal day. Risk 0.1%.

Inputs via context.extra:
  "rule_fires": {SYM: [{"date": iso, "features": {...}}]}
  "trading_days": [iso, ...] market day list for the TOM first-3 count
  "sleeve_state": {SYM: {"position": {...} | None}}
Bars: daily dicts {"t","o","h","l","c","v"} ascending.
"""
import math
from datetime import date as _date, timedelta
from datetime import datetime, timezone

from . import dcg_core
from .compat import BaseSleeve, Intent, SleeveConfig

HOLD_BARS = 63
LANE = "1D"
SIGNAL_KIND = "green"
MIN_PX = 5.0
MIN_DV20 = 1_000_000
RISK_FRACTION = 0.001
MAX_POSITIONS = 10

CONDITIONS = (
    {"feature": "mom121", "op": ">=", "value": 0.6500771284103396},
    {"feature": "disp", "op": "between", "lo": 0.02075970731675625,
     "hi": 0.02862246334552765},
    {"feature": "tom", "op": "==", "value": 1},
)

CONFIG = SleeveConfig(
    sleeve_id="rule_1d_green_tom", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=RISK_FRACTION)


def _dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


def _easter_sunday(year):
    """Anonymous Gregorian algorithm — verbatim from the old
    desk/nyse_calendar.py."""
    a = year % 19
    b, c = divmod(year, 100)
    dd, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - dd - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return _date(year, month, day)


def nyse_holidays(year):
    """Verbatim port of the old desk/nyse_calendar._nyse_holidays —
    INCLUDING Good Friday (Easter - 2d) and the no-Saturday-observance
    New Year rule. NOTE: core.data.nyse_holidays differs (it omits Good
    Friday entirely: 2026-04-03 / 2027-03-26 missing, verified by direct
    set diff) — the old _is_tom used THIS calendar, so this sleeve keeps
    it verbatim; the core calendar gap is named in the port report."""
    def nth_weekday(month, weekday, n):
        d = _date(year, month, 1)
        delta = (weekday - d.weekday()) % 7
        d += timedelta(days=delta)
        if n == -1:
            while (d + timedelta(days=7)).month == month:
                d += timedelta(days=7)
            return d
        return d + timedelta(weeks=n - 1)

    def observed(d):
        if d.weekday() == 5:
            return d - timedelta(days=1)
        if d.weekday() == 6:
            return d + timedelta(days=1)
        return d

    _nyd = _date(year, 1, 1)
    _nyd_obs = (_nyd + timedelta(days=1)) if _nyd.weekday() == 6 else _nyd
    return {
        _nyd_obs,
        nth_weekday(1, 0, 3),                      # MLK
        nth_weekday(2, 0, 3),                      # Presidents
        _easter_sunday(year) - timedelta(days=2),  # Good Friday
        nth_weekday(5, 0, -1),                     # Memorial
        observed(_date(year, 6, 19)),              # Juneteenth
        observed(_date(year, 7, 4)),               # Independence
        nth_weekday(9, 0, 1),                      # Labor
        nth_weekday(11, 3, 4),                     # Thanksgiving
        observed(_date(year, 12, 25)),             # Christmas
    }


def is_tom(d, days):
    """Exact trading-day turn-of-month — verbatim port of the old
    _is_tom (S2-B5-1 fixed version). `d` is a datetime.date; `days` is
    the market day list (iso strings). True when d is one of the first
    3 trading days of its month, or the last trading day of its month
    (next trading day — weekday + NYSE holidays — falls in a new month)."""
    iso = d.isoformat()
    month_days = sorted({str(x)[:10] for x in (days or [])
                         if str(x)[:7] == iso[:7]
                         and str(x)[:10] <= iso})
    if month_days and month_days[-1] == iso and len(month_days) <= 3:
        return True
    try:
        hols = set(nyse_holidays(d.year)) | set(nyse_holidays(d.year + 1))
        hols = {h.isoformat() if hasattr(h, "isoformat") else str(h)
                for h in hols}
    except Exception:
        hols = set()
    nxt = d + timedelta(days=1)
    while nxt.weekday() >= 5 or nxt.isoformat() in hols:
        nxt += timedelta(days=1)
    return nxt.month != d.month


def cond_pass(feats, cond):
    """Verbatim port of rule_sleeve_base.cond_pass (None feature fails)."""
    v = (feats or {}).get(cond["feature"])
    if v is None:
        return False
    try:
        v = float(v)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(v):
        return False
    op = cond["op"]
    if op == "<=":
        return v <= cond["value"]
    if op == ">=":
        return v >= cond["value"]
    if op == "==":
        return v == cond["value"]
    if op == "between":
        return cond["lo"] <= v <= cond["hi"]
    raise ValueError("unknown op %s" % op)


def rule_pass(feats, conditions=CONDITIONS):
    return all(cond_pass(feats, c) for c in conditions)


def dv20(bars):
    if len(bars) < 20:
        return 0.0
    return sum(float(b["c"]) * float(b["v"]) for b in bars[-20:]) / 20.0


def sessions_since(bars, entry_date):
    ds = _dates(bars)
    try:
        return len(ds) - 1 - ds.index(entry_date)
    except ValueError:
        return None


RANK_HM, FILL_HM = (16, 36), (10, 36)       # old crons rank 16:36, fill 10:36 ET
COST_BPS_SIDE = 0.001


def signals(scores, context=None):
    """old mode_rank: the rule on the signal bar (the name's last bar) + the desk filter, scorer order."""
    facts = scores.get("facts") or {}
    out = []
    for s, f in ((scores.get("rules") or {}).get("1D:green") or {}).items():
        fa = facts.get(s) or {}
        if f.get("date") != fa.get("date"):
            continue
        feats = dict(f.get("features") or {})
        feats["tom"] = 1 if is_tom(_date.fromisoformat(fa["date"]), scores.get("recent_days")) else 0
        if not rule_pass(feats, CONDITIONS):
            continue
        px = fa.get("px")
        if px is None or not (px >= MIN_PX):
            continue
        if (fa.get("dv20") or 0) < MIN_DV20:
            continue
        out.append((s, f["date"]))
    return out


class Rule1dGreenTom(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        """master-desk: the old runtime (dcg_core) — the rank stages after the close (next_meta), the next
        session's fill pass executes the old sleeve_core fill law, market-on-close."""
        if dcg_core.phase(context, RANK_HM, FILL_HM) != "fill":
            return []
        meta = (context.extra or {}).get("meta") or {}
        return dcg_core.fill(Intent, context, meta, COST_BPS_SIDE, "rule_1d_green_tom", disaster_stop=None)


def next_meta(bars, slice_state, context, intents=()):
    return dcg_core.next_meta(context, (context.extra or {}).get("meta") or {}, signals, HOLD_BARS, bars,
                              COST_BPS_SIDE, "rule_1d_green_tom", RANK_HM, FILL_HM)


def signal(bars, slice_state, context):
    return Rule1dGreenTom().signal(bars, slice_state, context)
