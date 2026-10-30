"""Teaching helpers for share reservations, stop references, settlement and stale reads.

These examples do no I/O. Reservations and latest-response state are in-memory only;
production use requires durable transactional state, one fenced writer, and broker
read-back/reconciliation. PAPER / SIMULATED USE ONLY.

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
import math


class StandDown(Exception):
    """Raised when a sell cannot reserve shares; carries a named reason."""


class ShareReservations:
    def __init__(self):
        self._held: dict[tuple[str, str], int] = {}       # (account, symbol) -> shares held by broker position
        # order key -> (account/symbol, original qty, remaining qty, state, owner)
        self._res: dict[str, tuple[tuple[str, str], int, int, str, str]] = {}

    def set_position(self, account: str, symbol: str, qty: int):
        self._validate_identity(account, symbol)
        self._validate_qty(qty, allow_zero=True)
        self._held[(account, symbol)] = qty

    def reserved(self, account: str, symbol: str) -> int:
        self._validate_identity(account, symbol)
        return sum(remaining for (k, _original, remaining, state, _owner) in self._res.values()
                   if k == (account, symbol) and state in ("OPEN", "PARTIAL", "CANCEL_PENDING", "UNKNOWN"))

    def available(self, account: str, symbol: str) -> int:
        return self._held.get((account, symbol), 0) - self.reserved(account, symbol)

    def reserve(self, order_key: str, account: str, symbol: str, qty: int, owner: str):
        self._validate_identity(account, symbol)
        self._validate_qty(qty)
        if not isinstance(order_key, str) or not order_key.strip() or not isinstance(owner, str) or not owner.strip():
            raise ValueError("order_key and owner are required")
        existing = self._res.get(order_key)
        if existing is not None:
            if existing[0] != (account, symbol) or existing[1] != qty or existing[4] != owner:
                raise StandDown(f"order_key_conflict:{order_key}")
            return
        avail = self.available(account, symbol)
        if qty > avail:
            raise StandDown(f"stand_down:{owner}:{symbol}: want {qty}, available {avail}")
        self._res[order_key] = ((account, symbol), qty, qty, "OPEN", owner)

    def mark(self, order_key: str, state: str, remaining_qty: int | None = None):
        """Update broker-read-back state; PARTIAL requires its unfilled remaining quantity."""
        active = {"OPEN", "PARTIAL", "CANCEL_PENDING", "UNKNOWN"}
        terminal = {"DONE", "CANCELLED", "REFUSED"}
        if state not in active | terminal:
            raise ValueError(f"invalid reservation state: {state}")
        k, original, remaining, current, owner = self._res[order_key]
        if current in terminal and state != current:
            raise StandDown(f"terminal_order_state:{order_key}:{current}")
        if state == "PARTIAL":
            if remaining_qty is None:
                raise ValueError("PARTIAL requires broker-confirmed remaining_qty")
            self._validate_qty(remaining_qty, allow_zero=True)
            if remaining_qty > remaining:
                raise StandDown(f"remaining_qty_increased:{order_key}")
            if remaining_qty == 0:
                state = "DONE"
        elif remaining_qty is not None:
            self._validate_qty(remaining_qty, allow_zero=True)
            if remaining_qty > remaining:
                raise StandDown(f"remaining_qty_increased:{order_key}")
            remaining = remaining_qty
        if state in terminal:
            remaining = 0
        self._res[order_key] = (k, original, remaining, state, owner)

    @staticmethod
    def _validate_identity(account: str, symbol: str):
        if not isinstance(account, str) or not account.strip() or not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("account and symbol are required")

    @staticmethod
    def _validate_qty(qty: int, allow_zero: bool = False):
        if isinstance(qty, bool) or not isinstance(qty, int) or qty < (0 if allow_zero else 1):
            raise ValueError("quantity must be a positive integer" if not allow_zero else "quantity must be a non-negative integer")


def pinned_stop(fill_price: float, stop_pct: float, side: str = "long") -> float:
    """Unrounded stop reference from the actual first fill, not a broker order price.

    The caller selects a strategy-specific risk fraction and applies the instrument's
    authoritative tick/order policy. This helper does not recommend a stop distance.
    """
    if (not isinstance(fill_price, (int, float)) or not math.isfinite(fill_price)
            or fill_price <= 0 or not isinstance(stop_pct, (int, float))
            or not math.isfinite(stop_pct) or not 0 < stop_pct < 1):
        raise ValueError("fill_price must be positive and stop_pct must be between 0 and 1")
    if side not in {"long", "short"}:
        raise ValueError("side must be 'long' or 'short'")
    return fill_price * (1.0 - stop_pct if side == "long" else 1.0 + stop_pct)


def settle_date(trade: date, calendar: dict[int, set[date]], cycle_days: int = 1) -> date:
    """Next `cycle_days` SETTLEMENT days after trade. calendar[year] = set of settlement HOLIDAYS.
    Weekends skipped. Raises KeyError (fail closed) if a year touched has no calendar entry."""
    if isinstance(cycle_days, bool) or not isinstance(cycle_days, int) or cycle_days < 1:
        raise ValueError("cycle_days must be a positive integer")
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
        if not isinstance(seq, (int, float)) or isinstance(seq, bool) or not math.isfinite(seq):
            return False
        if self.seq is not None and seq <= self.seq:
            return False
        self.seq, self.value = seq, value
        return True
