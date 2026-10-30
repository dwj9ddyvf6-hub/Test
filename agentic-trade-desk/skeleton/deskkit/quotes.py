"""Select a fresh reference price; never silently fall back to stale data.

Inputs are already-fetched observations represented as (price, provider_timestamp)
in Unix seconds. The caller must also validate instrument identity, feed entitlement,
adjustment basis, and receipt time. A midpoint is a reference, not an executable bid
or ask. If no observation meets the configured policy, callers must not invent one.
"""
from __future__ import annotations

import math
import time
from typing import Optional


def _fresh_price(observation: Optional[tuple[float, float]], now: float,
                 max_age_s: float) -> Optional[float]:
    if observation is None or len(observation) != 2:
        return None
    price, timestamp = observation
    if not isinstance(price, (int, float)) or not isinstance(timestamp, (int, float)):
        return None
    if not math.isfinite(price) or not math.isfinite(timestamp) or price <= 0:
        return None
    age_s = now - timestamp
    if age_s < 0 or age_s > max_age_s:
        return None
    return float(price)


def reference_price(last: Optional[tuple[float, float]],
                    quote: Optional[tuple[float, float, float]],
                    secondary: Optional[tuple[float, float]],
                    now: float | None = None,
                    max_age_s: float = 600,
                    max_spread: float = 0.02):
    """Return (price|None, tag) from fresh last, fresh tight mid, or fresh secondary.

    ``quote`` is (bid, ask, provider_timestamp); ``secondary`` is a separately
    fetched (price, provider_timestamp). The age and spread values are example
    parameters and must be set from the strategy's documented policy.
    """
    now = now if now is not None else time.time()
    if (not isinstance(now, (int, float)) or not math.isfinite(now)
            or not isinstance(max_age_s, (int, float)) or not math.isfinite(max_age_s)
            or max_age_s < 0 or not isinstance(max_spread, (int, float))
            or not math.isfinite(max_spread) or max_spread < 0):
        return None, "invalid_policy"
    now = float(now)

    price = _fresh_price(last, now, float(max_age_s))
    if price is not None:
        return price, "last"

    if quote is not None and len(quote) == 3:
        bid, ask, timestamp = quote
        if all(isinstance(v, (int, float)) and math.isfinite(v)
               for v in (bid, ask, timestamp)) and bid > 0 and ask >= bid:
            age_s = now - timestamp
            mid = (bid + ask) / 2
            spread = (ask - bid) / mid
            if 0 <= age_s <= max_age_s and spread <= max_spread:
                return float(mid), "mid"

    price = _fresh_price(secondary, now, float(max_age_s))
    if price is not None:
        return price, "secondary"

    return None, "none"
