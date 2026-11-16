"""F4-CRYPTO-BARKEY-20261114: archive-USDT bar-key resolution.

The Aster crypto engines were translated from an archive whose bar
keys are Binance-style (``ADAUSDT|4Hour``, ``LINKUSDT|4Hour``). No
producer in this desk serves a ``*USDT`` bar key: the warm layer
(desk3/warm.py CRYPTO_FETCHES) serves the desk's actual tape, the
Alpaca spot pairs, as ``LINK/USD|4Hour`` (544 bars on the retained
2026-11-14 snapshots) and ``ADA/USD|1Hour`` (735 bars) — and no
``ADA/USD|4Hour`` at all. The engines therefore resolved 0 bars on
every cycle while classified ARMED (Lane D fixture drives,
FIXTURE-DRIVES-2-2026-11-14 family F4: 39 sleeves).

Resolution order for an archive ``BASEUSDT`` symbol (the ONLY form
translated; every other symbol passes through untouched):

1. The archive keys themselves, exactly as each engine has always
   tried them — a view that does carry them behaves identically to
   pre-cure (pinned by the gatecure-crypto blockers).
2. The served spot form ``BASE/USD|<tf>`` — the same underlying's
   Alpaca spot bars, the desk's door and tape.
3. For 4Hour only, when no native 4Hour spot series is served:
   a deterministic resample of the served ``BASE/USD|1Hour`` tape
   (complete UTC 4h buckets only; o=first, h=max, l=min, c=last,
   v=sum). This is an aggregation of the desk's real bars, never a
   synthesized series, and it is used only where the native frame
   is absent — step 2 wins the moment the warm layer serves it.

The Kraken perp series (``PF_ADAUSD|4Hour`` etc.) is deliberately
NOT a fallback: it is a different instrument on a different venue,
and consuming it as spot signal bars would mislabel provenance.
ENJ resolved nothing under this scheme until CLEAR-THE-BOARD-
20261114: Alpaca lists no ENJ/USD spot pair (the warm layer's
ENJ/USD fetch returns nothing), but Kraken's public spot market
DOES trade ENJ/USD, and the desk's KrakenProducer now serves that
real spot tape under ``ENJ/USD|4Hour`` (the same rows it always
served as ``ENJUSD|240Min`` for free_kraken_enj_spot) — so ENJ
resolves at step 2 like ADA and LINK, from a real bar with its
venue provenance stamped in the producer. The perp refusal above
is untouched: no PF_* series is ever consumed as spot.
"""
from __future__ import annotations

from datetime import datetime, timezone

_TF_ALIASES = {"4Hour": ("4Hour", "4h", "4H", "240min"),
               "4H": ("4Hour", "4h", "4H", "240min"),
               "240min": ("4Hour", "4h", "4H", "240min")}


def _sort_key(row):
    """Chronological key tolerant of every stamp shape the engines
    carry: ISO strings and epoch numbers sort by epoch; anything
    else (fixture stamps like 'h7') sorts naturally, digits as
    numbers — a plain str() sort scrambles both float epochs and
    h10-vs-h2 stamps, which the incumbent unsorted helpers never
    did."""
    t = row.get("t")
    ep = _epoch(t)
    if ep is not None:
        return (0, ep, "")
    import re
    segs = tuple((0, int(s), "") if s.isdigit() else (1, 0, s)
                 for s in re.split(r"(\d+)", str(t)))
    return (1, 0, segs)


def _epoch(t):
    if isinstance(t, (int, float)):
        return float(t)
    try:
        d = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.timestamp()


def resample_1h_to_4h(rows):
    """Aggregate hourly bars into complete UTC 4h bars.

    A bucket is emitted only when it holds exactly 4 hourly bars;
    a trailing partial bucket is dropped (strategies read completed
    bars). Output stamps are the bucket start, ISO Z form.
    """
    buckets = {}
    for r in rows or []:
        try:
            ep = _epoch(r.get("t"))
            if ep is None:
                continue
            start = int(ep // 14400) * 14400
            buckets.setdefault(start, []).append((ep, r))
        except (TypeError, ValueError, KeyError):
            continue
    out = []
    for start in sorted(buckets):
        hrs = sorted(buckets[start], key=lambda x: x[0])
        if len(hrs) != 4:
            continue
        rs = [r for _, r in hrs]
        try:
            out.append({
                "t": datetime.fromtimestamp(start, timezone.utc)
                    .strftime("%Y-%m-%dT%H:%M:%SZ"),
                "o": float(rs[0]["o"]),
                "h": max(float(r["h"]) for r in rs),
                "l": min(float(r["l"]) for r in rs),
                "c": float(rs[-1]["c"]),
                "v": sum(float(r["v"]) for r in rs),
            })
        except (TypeError, ValueError, KeyError):
            continue
    return out


def resolve_bars(bars_map, sym, timeframes=("4Hour",)):
    """Resolve bars for `sym` under the F4 scheme.

    `timeframes` is the engine's own frame preference order. Returns
    a list (possibly empty), sorted by bar stamp when stamps parse
    as text, exactly as the incumbent engine helpers returned.
    """
    m = bars_map or {}
    # 1. Archive keys, in the engine's frame order (plus the bare
    # symbol, as the incumbent helpers tried last per frame; here it
    # is tried once after all framed archive keys).
    for tf in timeframes:
        for form in _TF_ALIASES.get(tf, (tf,)):
            rows = m.get(f"{sym}|{form}")
            if rows:
                return sorted(rows, key=_sort_key)
    if m.get(sym):
        return sorted(m[sym], key=_sort_key)
    # 2/3. Served spot forms — archive USDT names only.
    if not (isinstance(sym, str) and sym.endswith("USDT")):
        return []
    spot = sym[:-4] + "/USD"
    for tf in timeframes:
        for form in _TF_ALIASES.get(tf, (tf,)):
            rows = m.get(f"{spot}|{form}")
            if rows:
                return sorted(rows, key=_sort_key)
    if m.get(spot):
        return sorted(m[spot], key=_sort_key)
    for tf in timeframes:
        if tf in _TF_ALIASES:  # a 4h-family frame was requested
            rows = resample_1h_to_4h(m.get(f"{spot}|1Hour") or [])
            if rows:
                return rows
    return []
