"""Share reservation, stop pinning, settlement maturity and stale-response guard.

Four small, pure helpers (no I/O). PAPER / SIMULATED USE ONLY.

  * ShareReservations  (P-79): every sell, from any sleeve or any operator, reserves shares first.
    Open, partial and cancel-pending sells count; an UNKNOWN submit keeps its reservation until
    reconciled. A sell that cannot reserve STANDS DOWN with a named reason (no broker rejection).
  * pinned_stop        (P-80): after a partial first fill, the stop is derived from the ACTUAL fill.
  * settle_date        (P-86): cash maturity uses a settlement calendar and FAILS CLOSED when the
    calendar has no data for that year. You must supply the calendar; none is bundled.
  * LatestWins         (P-93): a late/stale response never overwrites a newer accepted one.
"""
from __future__ import annotations
from datetime import date, timedelta


class StandDown(Exception):
    """Raised when a sell cannot reserve shares; carries a named reason."""


class ShareReservations:
    def __init__(self):
        self._held: dict[tuple[str, str], int] = {}       # (account, symbol) -> shares held by broker position
        self._res: dict[str, tuple[tuple[str, str], int, str]] = {}   # order key -> (acct_sym, qty, state)

    def set_position(self, account: str, symbol: str, qty: int):
        self._held[(account, symbol)] = qty

    def reserved(self, account: str, symbol: str) -> int:
        return sum(q for (k, q, st) in self._res.values()
                   if k == (account, symbol) and st in ("OPEN", "PARTIAL", "CANCEL_PENDING", "UNKNOWN"))

    def available(self, account: str, symbol: str) -> int:
        return self._held.get((account, symbol), 0) - self.reserved(account, symbol)

    def reserve(self, order_key: str, account: str, symbol: str, qty: int, owner: str):
        if order_key in self._res:                 # idempotent
            return
        avail = self.available(account, symbol)
        if qty > avail:
            raise StandDown(f"stand_down:{owner}:{symbol}: want {qty}, available {avail}")
        self._res[order_key] = ((account, symbol), qty, "OPEN")

    def mark(self, order_key: str, state: str):
        """state: OPEN, PARTIAL, CANCEL_PENDING, UNKNOWN (keeps reservation), DONE, CANCELLED, REFUSED (release)."""
        k, q, _ = self._res[order_key]
        self._res[order_key] = (k, q, state)


def pinned_stop(fill_price: float, stop_pct: float) -> float:
    """Stop from the actual first fill price (not the planned entry)."""
    return round(fill_price * (1.0 - stop_pct), 4)


def settle_date(trade: date, calendar: dict[int, set[date]], cycle_days: int = 1) -> date:
    """Next `cycle_days` SETTLEMENT days after trade. calendar[year] = set of settlement HOLIDAYS.
    Weekends skipped. Raises KeyError (fail closed) if a year touched has no calendar entry."""
    d, n = trade, 0
    while n < cycle_days:
        d += timedelta(days=1)
        if d.year not in calendar:
            raise KeyError(f"no settlement calendar for {d.year}; fail closed")
        if d.weekday() < 5 and d not in calendar[d.year]:
            n += 1
    return d


class LatestWins:
    """Accept a value only if its sequence/timestamp is newer than the last accepted one."""
    def __init__(self):
        self.seq = None
        self.value = None

    def offer(self, seq: float, value) -> bool:
        if self.seq is not None and seq <= self.seq:
            return False
        self.seq, self.value = seq, value
        return True
