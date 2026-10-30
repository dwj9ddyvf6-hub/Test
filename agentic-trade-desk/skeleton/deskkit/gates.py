"""Entry gates as pure functions returning allow / wait / skip.

  allow : proceed
  wait  : not yet (outside window, input unknown). Does NOT consume the session's decision.
  skip  : final for this fire (rule says no, window closed for good). Record the reason.

Unknown input => WAIT, never SKIP and never a guess (a fire dropped forever because one input
was momentarily unavailable on its last valid day is the classic loss).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class Decision:
    verdict: str            # allow | wait | skip
    why: str = ""

ALLOW = Decision("allow")


def window_gate(in_window: bool, past_deadline: bool) -> Decision:
    if past_deadline:
        return Decision("skip", "window_closed")
    return ALLOW if in_window else Decision("wait", "not_in_window")


def market_condition_gate(index_change: Optional[float], stock_change: Optional[float],
                          last_valid_day: bool) -> Decision:
    """Example research rule: only buy when BOTH the index and the stock are down today."""
    if index_change is None or stock_change is None:
        return Decision("wait", "input_unknown")      # even on the last day: wait, the next pass may know
    if index_change < 0 and stock_change < 0:
        return ALLOW
    return Decision("skip" if last_valid_day else "wait", "condition_not_met")


def price_cap_gate(ref_price: Optional[float], limit: Optional[float], cap_mult: float = 1.02) -> Decision:
    if ref_price is None or limit is None:
        return Decision("wait", "price_unknown")
    return ALLOW if limit <= ref_price * cap_mult + 1e-9 else Decision("wait", "above_cap")


def run_gates(gates: list[Callable[[], Decision]]) -> Decision:
    """First non-allow wins; order matters (cheap/structural first)."""
    for g in gates:
        d = g()
        if d.verdict != "allow":
            return d
    return ALLOW
