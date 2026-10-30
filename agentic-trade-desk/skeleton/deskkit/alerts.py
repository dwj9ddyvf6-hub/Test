"""Alert, don't halt.

A desk-wide kill switch that blocks all trading turned small data problems into missed
entries and missed exits. Preferred pattern:
  * a failing sleeve is isolated and reported; the others continue;
  * missing data means "skip this decision and alert", never "guess";
  * the only hard stops are per-trade risk exits and an operator's explicit order.
"""
from __future__ import annotations
import time


class Alerts:
    def __init__(self, ledger=None, dedupe_s: float = 3600):
        self.ledger, self.dedupe_s = ledger, dedupe_s
        self._last: dict[str, float] = {}
        self.items: list[dict] = []

    def raise_(self, key: str, severity: str, message: str, **extra):
        now = time.monotonic()
        if now - self._last.get(key, -1e9) < self.dedupe_s:
            return False  # dedupe: one alert per key per window, not one per pass
        self._last[key] = now
        item = {"key": key, "severity": severity, "message": message, **extra}
        self.items.append(item)
        if self.ledger is not None:
            self.ledger.append("alert", item)
        return True
