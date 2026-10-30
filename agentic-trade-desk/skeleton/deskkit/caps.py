"""Lane (sleeve) slot caps and budgets.

Rules learned the hard way:
  * A slot is held by an OPEN position OR a QUEUED/PENDING entry order. (A queued entry that
    never expires holds a slot forever; give every queued entry a deadline.)
  * A slot is taken by an actual order only; a signal that is merely "being looked at" must not
    consume one (a lane once blocked valid signals behind out-of-window ones).
  * A refused order releases its slot.
  * Budgets are ceilings, not set-asides: the sum of lane budgets may exceed buying power by
    design, but then you MUST measure the overshoot and alert on it (see budget_vs_capacity).
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Lane:
    name: str
    max_slots: int
    budget_usd: float
    open_positions: int = 0
    queued_entries: int = 0

    @property
    def used(self) -> int:
        return self.open_positions + self.queued_entries

    def can_take(self) -> bool:
        return self.used < self.max_slots

    def take(self):
        if not self.can_take():
            raise RuntimeError(f"lane {self.name} full ({self.used}/{self.max_slots})")
        self.queued_entries += 1

    def release(self):
        self.queued_entries = max(0, self.queued_entries - 1)


def budget_vs_capacity(lanes: list[Lane], overnight_capacity_usd: float) -> dict:
    """Compare the sum of lane budgets with what the account can really hold overnight.

    Margin accounts advertise intraday buying power (e.g. 4x) that cannot be held overnight
    (Reg T allows about 2x). Size to the OVERNIGHT number, or accept and monitor the overshoot.
    """
    total = sum(l.budget_usd for l in lanes)
    return {"total_budget": total, "capacity": overnight_capacity_usd,
            "overshoot_ratio": round(total / overnight_capacity_usd, 3) if overnight_capacity_usd else None,
            "alert": total > overnight_capacity_usd}
