"""Data hub: fetch each series once per pass, fan out, cache by version, treat missing as unknown.

* `Missing` is a value, not an exception and not a zero. Sleeves must handle it (wait + alert).
* Cache is keyed by (symbol, timeframe) with a *version* (e.g. file mtime). A new version REPLACES the old
  frame (bounded memory) and is visible immediately (no process-lifetime staleness).
* Staleness limit: bars whose last timestamp is older than `max_age_days` are Missing('stale'), not signals.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class Missing:
    reason: str


class DataHub:
    def __init__(self, loader: Callable[[str, str], tuple[object, list[str]]], max_age_days: int = 5):
        """loader(symbol, tf) -> (version, bars) where bars is a list of ISO dates/timestamps in ascending order
        (this skeleton keeps it generic: replace `bars` with a DataFrame)."""
        self.loader, self.max_age_days = loader, max_age_days
        self._cache: dict[tuple[str, str], tuple[object, object]] = {}
        self.pass_fetches = 0

    def new_pass(self):
        self.pass_fetches = 0
        self._seen: set = set()

    def bars(self, symbol: str, tf: str, today_iso: str):
        key = (symbol, tf)
        try:
            version, data = self.loader(symbol, tf)
        except Exception as e:                       # provider failure => Missing, not a crash
            return Missing(f"loader_error:{type(e).__name__}")
        cached = self._cache.get(key)
        if cached is None or cached[0] != version:   # replace, don't accumulate
            self._cache[key] = (version, data)
        data = self._cache[key][1]
        if not data:
            return Missing("empty")
        from datetime import date
        last = date.fromisoformat(str(data[-1])[:10])
        if (date.fromisoformat(today_iso) - last).days > self.max_age_days:
            return Missing("stale")
        return data
