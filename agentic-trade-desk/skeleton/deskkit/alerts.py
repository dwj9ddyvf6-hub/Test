"""Alert delivery only; deterministic risk gates own order-path controls.

This helper records and deduplicates alerts. It does not decide whether to allow
orders. A complete desk should isolate sleeve-specific failures, block new exposure
when required inputs or invariants fail, and define a tested desk-level emergency
stop for critical shared failures. Position ownership and protective-exit behavior
must remain explicit during a stop; never guess a price or blindly liquidate on stale
data. See the safety-state policy in docs/07_reliability_ops.md.
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
