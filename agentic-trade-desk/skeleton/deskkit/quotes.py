"""Reference-price chain: never guess, always say which fallback was used.

order: fresh last trade -> fresh tight mid -> secondary provider's session price -> older last trade
Every step after the first appends an alert tag. If nothing is available: None (callers wait).
"""
from __future__ import annotations
import time
from typing import Callable, Optional


def reference_price(last: Optional[tuple[float, float]], quote: Optional[tuple[float, float, float]],
                    secondary: Callable[[], Optional[float]], now: float | None = None,
                    max_age_s: float = 600, max_spread: float = 0.02):
    """last=(price, ts) ; quote=(bid, ask, ts). Returns (price|None, tag)."""
    now = now if now is not None else time.time()
    if last and now - last[1] <= max_age_s:
        return last[0], "last"
    if quote:
        bid, ask, ts = quote
        mid = (bid + ask) / 2 if bid and ask else None
        if mid and now - ts <= max_age_s and (ask - bid) / mid <= max_spread:
            return mid, "mid"
    p = secondary()
    if p is not None:
        return p, "secondary"
    if last:
        return last[0], "stale_last"
    return None, "none"
