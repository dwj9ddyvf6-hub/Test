
"""Data — the ONE canonical bar door (spec section 2.1, Decision #108).
Tensor bars come ONLY from vendor/canonical_bars.py (byte-identical v698 feed).
Other bars: Alpaca SIP (hourly-or-finer volume rule, Decision #78) with the
SIP recency clamp; Yahoo daily is allowed ONLY for ^VIX price (no volume use).
Every bar set is labeled fresh/stale; non-finite values are rejected."""
import math, time
from datetime import date, timedelta
SIP_RECENCY_CLAMP_S = 1200  # SIP lags ~15-18 min; only bars closed >=20 min ago (old Bilbo convention)
STALE_AFTER_S = 900
def reject_nonfinite(bars):
    for b in bars:
        for k in ("o","h","l","c","v"):
            if k in b and b[k] is not None and not math.isfinite(float(b[k])):
                raise ValueError(f"non-finite bar value {k}={b[k]!r}")
    return bars
def label_freshness(bars, now=None):
    now = now or time.time()
    if not bars: return {"bars": [], "stale": True, "label": "stale:empty"}
    age = now - float(bars[-1]["t"])
    stale = age > STALE_AFTER_S
    return {"bars": bars, "stale": stale, "label": "stale" if stale else "fresh", "age_s": age}
def clamp_sip_recency(bars, now=None):
    """Drop bars not yet closed for at least SIP_RECENCY_CLAMP_S."""
    now = now or time.time()
    return [b for b in bars if float(b["t"]) + SIP_RECENCY_CLAMP_S <= now]
def tensor_bars(symbol, **kw):
    """The single Tensor door: delegates to the vendored canonical feed only."""
    import sys, pathlib
    v = pathlib.Path(__file__).resolve().parent.parent / "vendor"
    if str(v) not in sys.path: sys.path.insert(0, str(v))
    import canonical_bars
    # Vendored API (vendor/canonical_bars.py): get_canonical_1h is the
    # canonical fetch; there is no fetch_canonical_bars/get_bars — the
    # previous lookup raised AttributeError on every call (repair
    # 2026-10-15, systems probe; regression: tests/test_tensor_door_repair_20261015.py).
    fn = getattr(canonical_bars, "get_canonical_1h", None) or getattr(canonical_bars, "fetch_canonical_bars", None)
    if fn is None:
        raise AttributeError("vendored canonical_bars exposes no canonical fetch function")
    return reject_nonfinite(fn(symbol, **kw))
def is_trading_day(d: date) -> bool:
    if d.weekday() >= 5: return False
    return d not in nyse_holidays(d.year)
def nth_trading_days_ago(n, from_date=None):
    d = from_date or date.today(); c = 0
    while True:
        d -= timedelta(days=1)
        if is_trading_day(d):
            c += 1
            if c == n: return d
def nyse_holidays(year):
    from datetime import date as D
    def nth(m, wd, n):
        d = D(year, m, 1)
        return d + timedelta(days=((wd - d.weekday()) % 7) + 7*(n-1))
    def last(m, wd):
        d = nth(m, wd, 5)
        return d - timedelta(days=7) if d.month != m else d
    def obs(d):
        if d.weekday() == 5: return d - timedelta(days=1)
        if d.weekday() == 6: return d + timedelta(days=1)
        return d
    return {obs(D(year,1,1)), nth(1,0,3), nth(2,0,3), D(year,5,last(5,0).day) if False else last(5,0),
            obs(D(year,6,19)), obs(D(year,7,4)), nth(9,0,1), nth(11,3,4), obs(D(year,12,25))}
