"""Time helpers: exchange time zone, monotonic deadlines, VM-pause (wall-clock jump) detection.

Failure stories:
  * Hard-coded UTC-4 offsets were wrong after the daylight-saving change. Use a tz database.
  * On a VM that is paused/snapshotted, the WALL clock jumps forward on resume while the
    MONOTONIC clock does not. Wall-clock heartbeat ages then look hours stale and healthy
    processes get killed. Detect the jump and apply a grace period instead.
  * `timeout 7200 cmd` style limits count wall time on some platforms; use a monotonic limit.
"""
from __future__ import annotations
import datetime as dt
import time
from zoneinfo import ZoneInfo

EXCHANGE_TZ = ZoneInfo("America/New_York")


def now_exchange() -> dt.datetime:
    return dt.datetime.now(EXCHANGE_TZ)


def session_date(ts: dt.datetime | None = None) -> dt.date:
    """The trading date a timestamp belongs to. Pin it ONCE per pass; after midnight a pass that
    started at 23:58 must not silently change date half way through."""
    return (ts or now_exchange()).astimezone(EXCHANGE_TZ).date()


def in_window(start: str, end: str, ts: dt.datetime | None = None) -> bool:
    t = (ts or now_exchange()).astimezone(EXCHANGE_TZ).time()
    s, e = dt.time.fromisoformat(start), dt.time.fromisoformat(end)
    return s <= t < e


class JumpDetector:
    """Detects that the wall clock advanced much more than the monotonic clock (VM resume)."""

    def __init__(self, threshold_s: float = 180.0):
        self.threshold = threshold_s
        self._w, self._m = time.time(), time.monotonic()

    def check(self) -> float:
        """Return the size of the jump in seconds (0.0 if none) and re-baseline."""
        w, m = time.time(), time.monotonic()
        jump = (w - self._w) - (m - self._m)
        self._w, self._m = w, m
        return jump if jump > self.threshold else 0.0
