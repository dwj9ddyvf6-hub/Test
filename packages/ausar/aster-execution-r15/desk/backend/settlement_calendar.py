"""Versioned US listed-equity regular-way maturity and local-paper cash policy.

DTCC service availability is product-specific: limited DTC inquiry/delivery
services on Good Friday do not make it a regular-way equity CNS maturity day.
January 9, 2025, conversely, was a cash/securities settlement day although XNYS
closed for national mourning. Economic maturity is a DATE; this module's first
XNYS-open-on/after-maturity cash release is an explicit local-paper convention,
not an observation of completed DTC payment or real broker buying power.
"""
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from zoneinfo import ZoneInfo

UTC = timezone.utc
NY = ZoneInfo("America/New_York")
POLICY_VERSION = "US_EQ_REGULAR_WAY_DTCC_2022_2026_V2"
LEGACY_POLICY_VERSION = "LEGACY_NEXT_XNYS_OPEN_V1"
CASH_RELEASE_POLICY = "LOCAL_PAPER_FIRST_XNYS_OPEN_ON_OR_AFTER_MATURITY_V2"
SUPPORTED_YEARS = frozenset(range(2022, 2027))
# Explicit normal regular-way equity CNS/DTC maturity closures, including
# settlement-only Columbus/Veterans holidays. Saturdays are not generically
# moved to Fridays: November 10, 2023 is a normal processing day.
NONSETTLEMENT_MONTH_DAYS = {
    2022: ("01-17", "02-21", "04-15", "05-30", "06-20", "07-04", "09-05", "10-10", "11-11", "11-24", "12-26"),
    2023: ("01-02", "01-16", "02-20", "04-07", "05-29", "06-19", "07-04", "09-04", "10-09", "11-23", "12-25"),
    2024: ("01-01", "01-15", "02-19", "03-29", "05-27", "06-19", "07-04", "09-02", "10-14", "11-11", "11-28", "12-25"),
    2025: ("01-01", "01-20", "02-17", "04-18", "05-26", "06-19", "07-04", "09-01", "10-13", "11-11", "11-27", "12-25"),
    2026: ("01-01", "01-19", "02-16", "04-03", "05-25", "06-19", "07-03", "09-07", "10-12", "11-11", "11-26", "12-25"),
}
CALENDAR_DEFINITION = {
    "version": POLICY_VERSION,
    "scope": "ordinary US listed-equity regular-way CNS maturity; 2022 through 2026",
    "nonsettlement_month_days": NONSETTLEMENT_MONTH_DAYS,
    "weekends": "Saturday and Sunday closed",
    "special_settlement_open": ["2025-01-09"],
    "cycle": "T+2 for trade dates before 2024-05-28; T+1 thereafter",
    "cash_release_policy": CASH_RELEASE_POLICY,
    "authorities": ["SEC T+1 implementation FAQ", "DTC19404-23", "DTC20972-24", "DTC23036-25", "DTC19835-24", "DTC21560-25", "DTCC0275 Carter national mourning", "Nasdaq ETA2025-1", "DTC24351-26", "DTC24807-26"],
    "limitations": "ordinary dated processing calendar; exceptional service outages require new evidence/policy, not inferred actual broker cash",
}
CALENDAR_SHA256 = hashlib.sha256(json.dumps(CALENDAR_DEFINITION, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class SettlementCalendarError(ValueError):
    pass


def is_settlement_day(day):
    if not isinstance(day, date) or isinstance(day, datetime) or day.year not in SUPPORTED_YEARS:
        raise SettlementCalendarError("Regular-way settlement calendar coverage unavailable")
    return day.weekday() < 5 and day.strftime("%m-%d") not in NONSETTLEMENT_MONTH_DAYS[day.year]


def settlement_terms(clock, calendar=None):
    """Return frozen provenance-bearing terms before any accounting mutation."""
    if not isinstance(clock, datetime) or clock.tzinfo is None or clock.utcoffset() is None:
        raise SettlementCalendarError("Observed sale clock must be timezone-aware")
    if calendar is None:
        from .providers import _nyse
        calendar = _nyse()
    trade_day = clock.astimezone(NY).date()
    if trade_day.year not in SUPPORTED_YEARS or not calendar.is_session(trade_day.isoformat()):
        raise SettlementCalendarError("Observed sale has no covered native equity trade session")
    cycle = 2 if trade_day < date(2024, 5, 28) else 1
    remaining, day = cycle, trade_day
    for _ in range(16):
        day += timedelta(days=1)
        if is_settlement_day(day):
            remaining -= 1
            if not remaining:
                break
    else:
        raise SettlementCalendarError("No supported economic maturity found")
    # Jan 9, 2025 is the explicit example where economic maturity and local
    # exchange-opening cash release occur on different dates.
    release_session = calendar.date_to_session(day.isoformat(), direction="next")
    release = calendar.session_open(release_session).to_pydatetime().astimezone(UTC)
    return {"policy_version": POLICY_VERSION, "calendar_sha256": CALENDAR_SHA256,
            "trade_date": trade_day.isoformat(), "settlement_cycle_business_days": cycle,
            "economic_settlement_date": day.isoformat(), "cash_release_policy": CASH_RELEASE_POLICY,
            "cash_release_at": release.isoformat(), "cash_release_session": str(release_session.date()),
            "actual_broker_settlement_or_cash_observed": False}


def legacy_release_at(clock, calendar=None):
    """Replay the exact prior policy for compatibility, never for new sales."""
    if calendar is None:
        from .providers import _nyse
        calendar = _nyse()
    day = clock.astimezone(NY).date().isoformat()
    trade_session = calendar.date_to_session(day, direction="previous")
    following = calendar.next_session(trade_session)
    return calendar.session_open(following).to_pydatetime().astimezone(UTC).isoformat()
