"""Shared helpers for Lazarus batch 8 (s_mn_* Midna ports).

Local contract (same semantics as sleeves/vix_hedge.py's embedded
contract), bar math, and position-state shaping. Strategy rules live
in each sleeve module; this file is plumbing only.
"""
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class SleeveConfig:
    sleeve_id: str
    cadence_s: int
    universe: tuple = ()
    state_schema: dict = field(default_factory=dict)
    risk_pct: float = 0.0


@dataclass(frozen=True)
class Intent:
    kind: str
    symbol: str
    qty_hint: int | None = None
    qty: float | None = None
    limit_price: float | None = None
    price_hint: float | None = None
    stop: float | None = None
    target: float | None = None
    exit_rules: tuple = ()
    reason: str = ""
    side: str | None = None
    position_intent: str | None = None
    legs: tuple | None = None
    package_id: str | None = None
    signal_date: str | None = None

    def __post_init__(self):
        if self.kind not in ("enter", "exit"):
            raise ValueError(f"intent kind must be enter|exit, got {self.kind!r}")
        if self.qty_hint is not None and (int(self.qty_hint) != self.qty_hint or self.qty_hint <= 0):
            raise ValueError("qty_hint must be a positive whole number")


def bar_dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


def closes(bars):
    return [float(b["c"]) for b in bars]


def ema_series(vals, n):
    if not vals:
        return []
    k = 2.0 / (n + 1.0)
    out = [float(vals[0])]
    for v in vals[1:]:
        out.append(out[-1] + k * (float(v) - out[-1]))
    return out


def sma(vals, n, i=None):
    i = len(vals) - 1 if i is None else i
    if i + 1 < n:
        return None
    return sum(vals[i - n + 1:i + 1]) / n


def atr(bars, n=14):
    if len(bars) < 2:
        return None
    trs = []
    for i in range(1, len(bars)):
        h, l, pc = float(bars[i]["h"]), float(bars[i]["l"]), float(bars[i - 1]["c"])
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    if len(trs) < n:
        return None
    return sum(trs[-n:]) / n


def sessions_held(bars, entry_date):
    """Sessions strictly after entry_date present in the bar series."""
    if not entry_date:
        return 0
    return sum(1 for d in bar_dates(bars) if d > str(entry_date)[:10])


def held_positions(slice_state):
    out = {}
    for sym, rec in (slice_state or {}).items():
        pos = (rec or {}).get("position")
        if pos and float(pos.get("qty") or 0) != 0:
            out[sym] = pos
    return out


def qty_for(budget, price):
    if price is None or price <= 0 or budget <= 0:
        return 0
    return int(math.floor(budget / price))


EXP_ID_ENH20 = "ENH20-LAZ8-XSTALE-20261024"
XSTALE_MAX_LAG_DAYS = 4


def _last_bar_date(b):
    if not b:
        return None
    t = b[-1].get("t")
    try:
        if isinstance(t, (int, float)):
            return datetime.fromtimestamp(float(t) + 4 * 3600,
                                          tz=timezone.utc).date()
        from datetime import date as _d
        return _d.fromisoformat(str(t)[:10])
    except (TypeError, ValueError, OSError):
        return None


def xstale_refused(context, sleeve_id, bars, sym):
    """ENH20 binding leak (cross-symbol stale feed): a sleeve decides
    on each symbol's last bar as if current, even when that symbol's
    feed stopped days before the rest of the snapshot (halt/delist/
    producer lag) -- entries fire on a dead cross at a dead price.
    ON (default): refuse the ENTRY when sym's last bar lags the
    universe's latest bar by >4 calendar days; journal the paired
    shadow record (faithful would enter). OFF (extra
    {sleeve_id}_enh20.stale_gate=False): pre-change rule exactly.
    Exits are never gated. Single-symbol universes cannot lag."""
    extra = getattr(context, "extra", None) or {}
    cfg = extra.get(f"{sleeve_id}_enh20") or {}
    if cfg.get("stale_gate", True) is False:
        return False
    dates = {}
    for k, v in (bars or {}).items():
        d = _last_bar_date(v)
        if d is not None:
            dates[k] = d
    if sym not in dates or len(dates) < 2:
        return False
    lag = (max(dates.values()) - dates[sym]).days
    if lag <= XSTALE_MAX_LAG_DAYS:
        return False
    j = extra.get("enh20_journal")
    if isinstance(j, list):
        j.append({"exp_id": EXP_ID_ENH20, "sleeve": sleeve_id,
                  "symbol": sym, "enhanced": "refuse_xstale_entry",
                  "shadow_faithful": "enter", "lag_days": lag,
                  "last_bar": dates[sym].isoformat()})
    return True
