#!/usr/bin/env python3
"""desk/canonical_bars.py -- canonical Tensor 1H bar feed (2026-10-13).

THE Tensor input policy for 1H swing signals. Production FolioTend (canonical production — v698 pin, Part III)
does NOT consume Alpaca bars: it consumes Yahoo Finance chart bars,
RTH-only, open-anchored at :30 past the hour (SPEC.md in the staging
packet canonical_tensor_20261013; parity proven in PARITY.md: on the
canonical feed the five 2026-10-13 names TEM/HUT/CORZ/ARM/CVNA print NO
swing events, exactly as FolioTend showed, while the desk's Alpaca :00
extended-hours feed printed a spurious RECLAIM conf=7 on all five).

Canonical axes (SPEC SS1-9 -- do not "fix" any of these to desk norms):
  vendor      Yahoo Finance chart API, query1 then query2, serially
  endpoint    GET /v8/finance/chart/{SYM}?range=1y&interval=60m
              &includePrePost=false&events=div,splits
              &includeAdjustedClose=false
  session     RTH only (provider flag, not a parser-side clock filter)
  anchoring   bar timestamps are OPEN times: 09:30, 10:30, ..., 15:30 ET
              (the 15:30 bar is the 30-min closing stub to the 16:00 bell)
  adjustment  none -- Yahoo quote OHLC exactly as delivered (no adjclose)
  volume      indicators.quote[0].volume passed through untouched;
              missing / non-finite / negative -> 0.
              KNOWN DEFECT, DELIBERATE (Decision #78): Yahoo hourly
              volume was found corrupt desk-side (13-48x the tape,
              2026-10-09). Production consumes it anyway, so canonical
              parity REQUIRES it, unscaled and unsubstituted. Any
              volume-sensitive Tensor vote inherits the defect by
              design of the canonical source -- flagged, never silently
              "repaired" with Alpaca/SIP volume.
  forming bar dropped: a bar is served only once timestamp+3600 <= now
              (completed bars only; also drops Yahoo's flat zero-volume
              official-close sentinel appended near 'now').
  early close on 13:00-close sessions Yahoo appends one stub bar
              stamped 13:00 ET (seen 2025-11-28 / 2025-12-24 in the
              parity fixtures); production's parser passes it through
              and the parity runs consumed it, so it is served as-is
              (is_canonical_open). Yahoo also occasionally drops bars
              mid-series (TEM holes 2026-01-30 / 2026-02-02) -- served
              as delivered; the engine, not the feed, owns gaps.

Caching (the fetch-layer pattern of desk/fetch_layer.py, which the desk
adopted 2026-10-13 -- this module follows it, it does not fork it):
  * Completed bars are IMMUTABLE. The on-disk series
    (desk/cache/bars/v1/yahoo-canonical-1h/<SYM>.json + .meta.json,
    the fetch_layer cache layout) is served with NO provider call while
    it already ends at the newest completed RTH bar for 'now': a new
    completed bar can only appear at a bar-close instant (10:30, 11:30,
    ..., 16:00 ET), so between closes a refetch could only re-download
    the same ~1,740 bars. Worst case provider load is therefore
    <= 1 fetch per symbol per completed bar (<= 7/day/symbol), never
    one fetch per scan -- the per-scan refetch storm this replaces.
  * When a fetch IS due, the full 1y series replaces the cached series
    wholesale (Yahoo revises intraday prints slightly between fetches;
    wholesale replacement keeps the served series exactly one Yahoo
    snapshot, never a splice of two).
  * Concurrent callers coalesce through a per-symbol fcntl file lock
    with a double-checked re-read inside the lock (fetch_layer Step 3).
  * Cache writes are atomic (tmp file + os.replace), as in fetch_layer.
  * Fetch failure posture: if every Yahoo origin fails AND a cached
    series exists, the cache is served and last_status() reports
    "stale_cache" (signals on slightly old canonical bars are still
    canonical-grid signals; the alternative -- falling back to the
    Alpaca :00 feed -- is the exact bug this module exists to kill, and
    is NEVER done). With no cache at all, CanonicalFeedError is raised
    and the caller fails closed / skips the symbol.

Output: [{"t": epoch_seconds_int, "o","h","l","c","v"}] oldest->newest,
the exact payload shape engine/tensor_exact.py::exact_swing_signal
consumes. bars_to_desk_shape() adapts to the desk's ISO-"t" bar dicts
for legacy callers (scan_and_trade.bars_to_exact et al).

Stdlib only. Never places orders; data path only.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

ORIGINS = ("https://query1.finance.yahoo.com",
           "https://query2.finance.yahoo.com")
QUERY = ("range=1y&interval=60m&includePrePost=false"
         "&events=div,splits&includeAdjustedClose=false")
HEADERS = {
    "accept": "application/json",
    "user-agent": "Mozilla/5.0 (compatible; FolioTendVector/1.0; "
                  "chart-generator)",
}
BAR_SECONDS = 3600
SOURCE = "yahoo-canonical-1h"
MIN_BARS = 200  # production adapter gate for 1h (SPEC S5); warn below it

_HERE = os.path.dirname(os.path.abspath(__file__))
# Same cache root as desk/fetch_layer.py: desk/cache/bars/v1/<source>/<tf>/
CACHE_ROOT = os.path.join(_HERE, "cache", "bars", "v1")
TIMEFRAME_DIR = "1h"

_provider = None  # test hook: fn(symbol) -> payload dict
_last_status: dict[str, str] = {}


class CanonicalFeedError(RuntimeError):
    """All Yahoo origins failed and no cached canonical series exists."""


# ------------------------------------------------------------ status hook
def last_status(symbol: str) -> str | None:
    """Outcome of the last get_canonical_1h() for a symbol:
    'cache' | 'fetch' | 'stale_cache' | None (never fetched)."""
    return _last_status.get(str(symbol).upper())


def set_provider(fn) -> None:
    """Inject a payload provider (tests). None restores the Yahoo fetch."""
    global _provider
    _provider = fn


def cache_root() -> str:
    """Directory this module caches under (tests may monkeypatch)."""
    return os.path.join(CACHE_ROOT, SOURCE, TIMEFRAME_DIR)


# ------------------------------------------------------------- RTH grid
def rth_opens(day) -> list[int]:
    """Epoch-second OPEN times of one ET date's RTH 60m bars.

    Anchored at the 09:30 session open: 09:30..15:30 ET (7 bars; the
    15:30 bar is the closing stub). Empty for Sat/Sun. Holiday handling
    is Yahoo's: a holiday simply returns no bars, and freshness logic
    below only ever asks whether a NEWER completed bar could exist.
    """
    if day.weekday() >= 5:
        return []
    open_dt = datetime(day.year, day.month, day.day, 9, 30, tzinfo=ET)
    return [int((open_dt + timedelta(hours=k)).timestamp())
            for k in range(7)]


def _nth_weekday(year: int, month: int, weekday: int, n: int):
    """Date of the n-th `weekday` (Mon=0) of a month."""
    from datetime import date as _date
    d = _date(year, month, 1)
    d += timedelta(days=(weekday - d.weekday()) % 7 + 7 * (n - 1))
    return d


def is_early_close(day) -> bool:
    """True iff `day` is an NYSE 13:00-ET early-close session.

    Total audit MF-017 (2026-10-13): freshness used to be judged against
    the full 7-bar grid, so after an early-close session the cache could
    NEVER be fresh (its last bar is the 13:00 stub, not 15:30) and every
    call refetched a full year of Yahoo data for days. The recurring
    early closes are: the Friday after Thanksgiving, Christmas Eve
    (Mon-Thu; a Friday Dec 24 is the observed Christmas holiday -- no
    session at all), and Jul 3 when Jul 4 falls Tue-Fri (Jul 4 on
    Saturday makes Jul 3 the observed holiday -- no session)."""
    if day.weekday() >= 5:
        return False
    if day.month == 11:  # Friday after the 4th Thursday of November
        if day == _nth_weekday(day.year, 11, 3, 4) + timedelta(days=1):
            return True
    if day.month == 12 and day.day == 24 and day.weekday() <= 3:
        return True
    if day.month == 7 and day.day == 3:
        from datetime import date as _date
        if _date(day.year, 7, 4).weekday() in (1, 2, 3, 4):
            return True
    return False


def session_opens(day) -> list[int]:
    """Epoch-second OPEN times of every bar a session actually emits:
    the full 7-bar grid on a normal day; on an early-close day the
    09:30/10:30/11:30 bars plus Yahoo's 13:00 stub (see module doc)."""
    if day.weekday() >= 5:
        return []
    if not is_early_close(day):
        return rth_opens(day)
    base = datetime(day.year, day.month, day.day, 9, 30, tzinfo=ET)
    opens = [int((base + timedelta(hours=k)).timestamp())
             for k in range(3)]
    stub = datetime(day.year, day.month, day.day, 13, 0, tzinfo=ET)
    opens.append(int(stub.timestamp()))
    return opens


def latest_completed_open(now_s: int) -> int | None:
    """Open time of the newest RTH bar whose window has fully ended by
    now_s (t + 3600 <= now_s), searching back up to 10 days. None only
    before the first session in that window. Early-close sessions are
    judged on session_opens(), so a cache ending at the 13:00 stub IS
    fresh (MF-017)."""
    now_s = int(now_s)
    day = datetime.fromtimestamp(now_s, ET).date()
    for back in range(0, 11):
        for t in reversed(session_opens(day - timedelta(days=back))):
            if t + BAR_SECONDS <= now_s:
                return t
    return None


def is_rth_open(t: int) -> bool:
    """True iff epoch t is a canonical bar open (:30-anchored, RTH)."""
    dt = datetime.fromtimestamp(int(t), ET)
    return (dt.minute == 30 and dt.second == 0 and dt.weekday() < 5
            and (9, 30) <= (dt.hour, dt.minute) < (16, 0))


def is_canonical_open(t: int) -> bool:
    """True iff t is a bar open the canonical feed actually emits:
    an is_rth_open(), OR Yahoo's early-close stub -- on 13:00-close
    sessions (e.g. 2025-11-28, 2025-12-24 in the parity fixtures)
    Yahoo appends one bar stamped 13:00 ET after the 11:30 bar. The
    production parser passes it through and the parity-proven engine
    runs consumed it, so this module passes it through too; it is
    the ONLY :00 stamp in a canonical series."""
    if is_rth_open(t):
        return True
    dt = datetime.fromtimestamp(int(t), ET)
    return (dt.hour, dt.minute, dt.second) == (13, 0, 0) \
        and dt.weekday() < 5


def is_close_sentinel(bar) -> bool:
    """True iff `bar` is Yahoo's official-close sentinel: stamped
    16:00 ET (the session close instant, not an open on the :30 grid),
    flat (o == h == l == c) at the official close, zero volume.

    Desk repair 2026-10-15 (Decision #108 re-pin of this desk-authored
    module; investigation TENSOR_FEED_INVESTIGATION_2026-10-15):
    production v698 has no grid assert and consumes this bar as an
    ordinary inert trailing bar, so the desk assert tolerates it the
    same way it tolerates the 13:00 early-close stub. The exception is
    EXACTLY this shape -- a 16:00 bar with any range or any volume, or
    any other off-grid bar, still rejects fail-closed."""
    try:
        dt = datetime.fromtimestamp(int(bar["t"]), ET)
        return (dt.hour, dt.minute, dt.second) == (16, 0, 0) \
            and dt.weekday() < 5 \
            and float(bar["o"]) == float(bar["h"]) \
            == float(bar["l"]) == float(bar["c"]) \
            and float(bar["v"]) == 0.0
    except (KeyError, TypeError, ValueError):
        return False


# ------------------------------------------------------------ Yahoo fetch
def fetch_yahoo_payload(symbol: str) -> tuple[dict, str]:
    """Try origins serially in production order; return (payload, origin).

    Route failure != impossibility: a failed origin falls through to
    the next; only total failure raises.
    """
    if _provider is not None:
        return _provider(symbol), "injected"
    last_err: Exception | None = None
    for origin in ORIGINS:
        url = "%s/v8/finance/chart/%s?%s" % (origin, symbol, QUERY)
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8")), origin
        except Exception as exc:  # noqa: BLE001 -- next origin, see above
            last_err = exc
    raise CanonicalFeedError(
        "all Yahoo origins failed for %s: %r" % (symbol, last_err))


# ------------------------------------------------------- production parse
def _pos_int(x):
    return (int(x) if isinstance(x, (int, float))
            and float(x).is_integer() and x > 0 else None)


def _fin_pos(x):
    return (float(x) if isinstance(x, (int, float))
            and math.isfinite(x) and x > 0 else None)


def _fin_nonneg(x):
    return (float(x) if isinstance(x, (int, float))
            and math.isfinite(x) and x >= 0 else None)


def parse_yahoo_history(payload: dict, expected_symbol: str) -> list[dict]:
    """Production parseYahooReplicaHistory semantics for 1h (SPEC SS1/5-7).

    Reads chart.result[0].timestamp[] + indicators.quote[0] OHLCV only
    (never adjclose). Drops rows with a non-positive-integer timestamp
    or non-finite / non-positive OHLC, or high < max(o,c), or
    low > min(o,c). Volume missing/non-finite/negative -> 0, otherwise
    passed through untouched. De-duplicated by timestamp (last wins),
    sorted ascending.
    """
    result = ((payload.get("chart") or {}).get("result") or [None])[0]
    if not result or not result.get("meta"):
        raise ValueError("payload missing chart.result[0].meta")
    meta = result["meta"]
    if str(meta.get("symbol", "")).upper() != expected_symbol.upper():
        raise ValueError("symbol mismatch: meta=%r want=%r"
                         % (meta.get("symbol"), expected_symbol))
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    ts = result.get("timestamp") or []
    n = len(ts)

    def _col(name):
        col = quote.get(name) or []
        return list(col) + [None] * max(0, n - len(col))

    opens, highs, lows, closes, vols = (
        _col("open"), _col("high"), _col("low"), _col("close"),
        _col("volume"))
    by_ts: dict[int, dict] = {}
    for i, raw_t in enumerate(ts):
        t = _pos_int(raw_t)
        o, h, l, c = (_fin_pos(opens[i]), _fin_pos(highs[i]),
                      _fin_pos(lows[i]), _fin_pos(closes[i]))
        if t is None or o is None or h is None or l is None or c is None:
            continue
        if h < max(o, c) or l > min(o, c):
            continue
        v = _fin_nonneg(vols[i])
        by_ts[t] = {"t": t, "o": o, "h": h, "l": l, "c": c,
                    "v": v if v is not None else 0}
    return [by_ts[t] for t in sorted(by_ts)]


def completed_only(bars: list[dict], now_s: int | None = None) -> list[dict]:
    """Keep bars whose full 60m window has ended by now (SPEC S8)."""
    now = int(now_s if now_s is not None else time.time())
    return [b for b in bars if int(b["t"]) + BAR_SECONDS <= now]


# --------------------------------------------------------------- cache io
def _safe(sym: str) -> str:
    return (str(sym).upper().replace("/", "_").replace(".", "_")
            .replace("^", ""))


def _paths(sym: str) -> tuple[str, str]:
    d = cache_root()
    return (os.path.join(d, _safe(sym) + ".json"),
            os.path.join(d, _safe(sym) + ".meta.json"))


def _read_cache(sym: str):
    path, mpath = _paths(sym)
    try:
        with open(path) as fh:
            bars = json.load(fh)
        with open(mpath) as fh:
            meta = json.load(fh)
        if isinstance(bars, list) and isinstance(meta, dict):
            return bars, meta
    except Exception:  # noqa: BLE001 -- a bad cache is a cache miss
        pass
    return None, None


def _write_cache(sym: str, bars: list[dict], meta: dict) -> None:
    path, mpath = _paths(sym)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for target, obj in ((path, bars), (mpath, meta)):
        tmp = "%s.tmp%d" % (target, os.getpid())
        with open(tmp, "w") as fh:
            json.dump(obj, fh)
        os.replace(tmp, target)


def _lock_path(sym: str) -> str:
    d = os.path.join(CACHE_ROOT, "locks")
    os.makedirs(d, exist_ok=True)
    key = hashlib.sha1(
        ("%s|%s|%s" % (SOURCE, TIMEFRAME_DIR, _safe(sym))).encode()
    ).hexdigest()
    return os.path.join(d, key + ".lock")


def _is_fresh(bars: list[dict], now_s: int) -> bool:
    """True iff the cached series already ends at the newest completed
    RTH bar for now_s -- i.e. no provider call could add a bar. This is
    the immutability rule: completed bars never change under us, so the
    only event that can stale the cache is a bar CLOSE (see module doc).
    """
    if not bars:
        return False
    newest = latest_completed_open(now_s)
    if newest is None:
        return True  # no completed bar exists in the lookback window
    return int(bars[-1]["t"]) >= newest


def _record(consumer: str) -> None:
    """Fetch-layer telemetry, when the desk fetch layer is importable."""
    try:
        from desk.fetch_layer import record_request
        record_request(consumer, "yahoo_canonical_chart", "1h")
    except Exception:  # noqa: BLE001 -- telemetry never breaks a fetch
        pass


# ------------------------------------------------------------ public API
def _assert_canonical(bars, sym=""):
    """fixall2 2026-10-14 R-002: assert :30 RTH grid + strictly increasing.
    2026-10-15 repair: the 16:00 official-close sentinel (is_close_
    sentinel) is tolerated as inert, mirroring production v698, which
    consumes it as an ordinary trailing bar; every other off-grid bar
    still rejects fail-closed."""
    prev=None
    for b in bars:
        tt=int(b["t"])
        if not is_canonical_open(tt) and not is_close_sentinel(b):
            raise CanonicalFeedError(f"non-canonical bar open for {sym}: {tt}")
        if prev is not None and tt<=prev:
            raise CanonicalFeedError(f"non-monotonic canonical bars for {sym}")
        prev=tt
    return bars

def get_canonical_1h(symbol: str, now_s: int | None = None,
                     consumer: str = "canonical_bars") -> list[dict]:
    """Canonical completed 1H bars for one symbol, oldest->newest.

    Serves the immutable cache with zero provider calls while it ends
    at the newest completed bar; otherwise performs ONE coalesced
    fetch (see module docstring). Raises CanonicalFeedError only when
    no canonical bars exist anywhere (no cache, all origins down) --
    callers must fail closed / skip the symbol, never substitute the
    Alpaca :00 feed.
    """
    sym = str(symbol).upper()
    now = int(now_s if now_s is not None else time.time())

    bars, _meta = _read_cache(sym)
    if bars and _is_fresh(bars, now):
        _last_status[sym] = "cache"
        return _assert_canonical(completed_only(bars, now), sym)

    with open(_lock_path(sym), "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            bars, _meta = _read_cache(sym)  # double-checked re-read
            if bars and _is_fresh(bars, now):
                _last_status[sym] = "cache"
                return _assert_canonical(completed_only(bars, now), sym)
            try:
                _record(consumer)
                payload, origin = fetch_yahoo_payload(sym)
                fresh = completed_only(parse_yahoo_history(payload, sym),
                                       now)
            except Exception as exc:
                if bars:  # stale canonical beats non-canonical, always
                    _last_status[sym] = "stale_cache"
                    return _assert_canonical(completed_only(bars, now), sym)
                raise CanonicalFeedError(
                    "no canonical bars for %s (fetch failed, no cache): "
                    "%r" % (sym, exc)) from exc
            if not fresh:
                if bars:
                    _last_status[sym] = "stale_cache"
                    return _assert_canonical(completed_only(bars, now), sym)
                raise CanonicalFeedError(
                    "Yahoo returned no completed bars for %s" % sym)
            # 2026-10-15 repair: assert BEFORE the cache write. The
            # pre-repair order wrote first and asserted on return, so
            # a rejected (post-17:00) fetch permanently poisoned the
            # symbol's cache. A rejected frame must never reach disk.
            _assert_canonical(fresh, sym)
            _write_cache(sym, fresh, {
                "fetched_at": time.time(), "source": SOURCE,
                "origin": origin, "schema_v": 1, "bars": len(fresh),
                "last_bar_t": int(fresh[-1]["t"])})
            _last_status[sym] = "fetch"
            return fresh
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def canonical_bars(symbol: str, now_s: int | None = None,
                   consumer: str = "canonical_bars"):
    """Staging-feed-compatible wrapper: returns (bars, info dict).

    Kept so parity/replay code written against
    feed/canonical_feed.py::canonical_bars runs unchanged against the
    production module.
    """
    bars = get_canonical_1h(symbol, now_s=now_s, consumer=consumer)
    return bars, {"source": SOURCE, "status": last_status(symbol),
                  "completed_bars": len(bars),
                  "below_production_gate": len(bars) < MIN_BARS}


def bars_to_desk_shape(bars: list[dict]) -> list[dict]:
    """Adapt epoch bars to the desk's ISO-"t" bar dicts (the shape
    scan_and_trade.run_cli returns and bars_to_exact / strip_forming_bar
    consume), so a caller can swap its fetch line and nothing else."""
    out = []
    for b in bars:
        iso = datetime.fromtimestamp(int(b["t"]), timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        out.append({"t": iso, "o": b["o"], "h": b["h"], "l": b["l"],
                    "c": b["c"], "v": b["v"]})
    return out


if __name__ == "__main__":  # manual smoke check only; not a desk entry
    import sys
    sym = (sys.argv[1] if len(sys.argv) > 1 else "TEM").upper()
    _bars, _info = canonical_bars(sym)
    print(sym, _info)
    if _bars:
        print("first", _bars[0])
        print("last ", _bars[-1])
