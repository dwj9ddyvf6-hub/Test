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
$5+ and $1M dv20 on the signal day.

Inputs via context.extra:
  "rule_fires": {SYM: [{"date": iso, "features": {...}}]}
  "trading_days": [iso, ...] market day list for the TOM first-3 count
  "sleeve_state": {SYM: {"position": {...} | None}}
Bars: daily dicts {"t","o","h","l","c","v"} ascending.

Sizing (A2-06 reconciliation, 2026-10-16): 1% of equity notional per
position (NOTIONAL_FRACTION, carried on the intent's qty_hint), max
10 positions. No risk-fraction sizing exists in the source: the old
framework sized centrally in sleeve_core.run_fill (equal weight over
a 30% sleeve cap, Decision #20), sleeves never computed a quantity,
and the 0.001 in the old Sleeve(...) constructor was its
cost_bps_side (10bp/side cost model) -- the "Risk 0.1%" this port
originally declared was that cost arg misread (EVIDENCE-FINAL2).
Stops: none in the source -- the old sleeve set no
disaster_stop_pct; the only exit is the time hold above.
"""
import math
from datetime import date as _date, timedelta
from datetime import datetime, timezone

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

HOLD_BARS = 63
LANE = "1D"
SIGNAL_KIND = "green"
MIN_PX = 5.0
MIN_DV20 = 1_000_000
NOTIONAL_FRACTION = 0.01  # A2-06: the executed sizing law
# (1% of equity notional per position) -- see docstring note
MAX_POSITIONS = 10

CONDITIONS = (
    {"feature": "mom121", "op": ">=", "value": 0.6500771284103396},
    {"feature": "disp", "op": "between", "lo": 0.02075970731675625,
     "hi": 0.02862246334552765},
    {"feature": "tom", "op": "==", "value": 1},
)

CONFIG = SleeveConfig(
    sleeve_id="rule_1d_green_tom", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=None)


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


def _is_first3(d, days):
    """First-3-trading-days branch of _is_tom, on the supplied day
    list ONLY (iso strings)."""
    iso = d.isoformat()
    month_days = sorted({str(x)[:10] for x in (days or [])
                         if str(x)[:7] == iso[:7]
                         and str(x)[:10] <= iso})
    return bool(month_days) and month_days[-1] == iso \
        and len(month_days) <= 3


def _is_last_trading_day(d):
    """Last-trading-day branch of _is_tom: decided by the NEXT trading
    day (weekday + NYSE holidays) falling in a new month. Never used
    the market day list."""
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


def is_tom(d, days):
    """Exact trading-day turn-of-month — verbatim port of the old
    _is_tom (S2-B5-1 fixed version). `d` is a datetime.date; `days` is
    the market day list (iso strings). True when d is one of the first
    3 trading days of its month, or the last trading day of its month
    (next trading day — weekday + NYSE holidays — falls in a new month)."""
    return _is_first3(d, days) or _is_last_trading_day(d)


# ------------------------------------------------------------ ENH
# ENH (IMPROVE-rule_1d_green_tom, Edge program 2026-10-24): the
# first-3 branch may only be satisfied from the MARKET day list
# (extra["trading_days"]). When the list is absent or empty the
# first-3 branch fails closed; the list-independent last-trading-day
# branch stands exactly as today. The pre-change rule (control)
# silently fell back to the SYMBOL's own bar dates when the list was
# missing — a different rule than the sleeve's stated law. Switched
# by context.extra["rule_1d_green_tom_enhance"]["tom_fail_closed"]
# (default ON; OFF restores the pre-change rule exactly). Paired
# records ride the rule_1d_green_tom_enh_journal.
ENH_EXP_ID = "ENH-RULE-1D-GREEN-TOM-20261024"


def tom_fail_closed_enabled(extra):
    """ctx.extra['rule_1d_green_tom_enhance']['tom_fail_closed'],
    default ON; non-dict override ignored (ENH2 idiom)."""
    ov = (extra or {}).get("rule_1d_green_tom_enhance")
    if isinstance(ov, dict) and "tom_fail_closed" in ov:
        return bool(ov["tom_fail_closed"])
    return True


def _enh_journal(extra):
    raw = (extra or {}).get("rule_1d_green_tom_enh_journal")
    if isinstance(raw, dict) and raw.get("exp_id") == ENH_EXP_ID \
            and isinstance(raw.get("records"), list):
        return raw
    return {"exp_id": ENH_EXP_ID, "records": []}


def tom_enhanced(d, trading_days):
    """Treatment TOM: first-3 ONLY from the market list (fail closed
    when absent/empty); last-trading-day branch unchanged."""
    first3 = _is_first3(d, trading_days) if trading_days else False
    return first3 or _is_last_trading_day(d)


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
    """Sessions elapsed since entry — the old counting law (old sells
    loop: bars dated strictly after the entry date). Identical to the
    index count when the entry bar is in the list, and still correct
    when it has aged out of the delivered window (P3 audit 2026-10-15:
    the index form returned None then, so the sleeve exit never fired)."""
    entry = str(entry_date)[:10]
    return sum(1 for d in _dates(bars) if d > entry)


class Rule1dGreenTom(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        fires = extra.get("rule_fires") or {}
        trading_days = extra.get("trading_days") or []
        equity = float(context.equity or 0.0)
        enh_on = tom_fail_closed_enabled(extra)
        journal = _enh_journal(extra)
        intents = []
        book = {s: (state.get(s) or {}).get("position")
                for s in state if (state.get(s) or {}).get("position")}
        for sym, p in book.items():
            bl = bars.get(sym) or []
            n = sessions_since(bl, p.get("entry_date")) if p.get("entry_date") else None
            if n is not None and n >= HOLD_BARS - 1:
                qty = int(float(p.get("qty") or 0))
                if qty > 0 and bl:
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty,
                        price_hint=round(float(bl[-1]["c"]), 2),
                        exit_rules=(ExitRule("time_bars", float(HOLD_BARS)),),
                        reason="rule_1d_green_tom: %d sessions >= hold %d (staged early)"
                               % (n, HOLD_BARS)))
        if equity <= 0 or not fires:
            self.last_evaluation = {
                "rule_1d_green_tom_enh_journal": journal}
            return intents
        open_n = len(book)
        for sym in sorted(fires):
            if sym in book or open_n >= MAX_POSITIONS:
                continue
            bl = bars.get(sym) or []
            if not bl:
                continue
            dates = _dates(bl)
            last_date = dates[-1]
            px = float(bl[-1]["c"])
            hit = None
            for f in fires.get(sym) or []:
                if not isinstance(f, dict) or f.get("date") != last_date:
                    continue
                feats = dict(f.get("features") or {})
                # TOM recomputed exactly (scorer tom is vacuous live).
                try:
                    d = _date.fromisoformat(str(f["date"])[:10])
                    days = trading_days or dates
                    control_tom = 1 if is_tom(d, days) else 0
                    treat_tom = 1 if tom_enhanced(d, trading_days) else 0
                    journal["records"].append({
                        "symbol": sym, "date": str(f["date"])[:10],
                        "control": {"tom": control_tom},
                        "treatment": {"tom": treat_tom},
                        "trading_days_supplied": bool(trading_days),
                        "enhance_switch": enh_on})
                    feats["tom"] = treat_tom if enh_on else control_tom
                except Exception:
                    pass  # old law: keep scorer value on parse failure
                if rule_pass(feats):
                    hit = f
                    break
            if hit is None:
                continue
            if px < MIN_PX or dv20(bl) < MIN_DV20:
                continue
            qty = int((equity * NOTIONAL_FRACTION) // px)
            if qty < 1:
                # OBS-1 (ruling 2026-10-22): the sleeve's own
                # sizing is the law — a budget that buys
                # nothing takes no position. No forced floor.
                continue
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(px, 2),
                exit_rules=(ExitRule("time_bars", float(HOLD_BARS)),),
                reason="rule_1d_green_tom: green fire %s mom121/disp pass, "
                       "tom=1 (exact trading-day), px=%.2f dv20=%.0f"
                       % (last_date, px, dv20(bl))))
            open_n += 1
        self.last_evaluation = {"rule_1d_green_tom_enh_journal": journal}
        return intents


def signal(bars, slice_state, context):
    return Rule1dGreenTom().signal(bars, slice_state, context)
