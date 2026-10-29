"""Hyperliquid's public book for midna_hyperliquid_momentum_floor — Midna's src/lib/market.ts (@ entire 43f08f96, blob
9e07dd93: loadQuotes, hourlyRangePct; decide.ts averageRangePct) ported:

  quotes   POST https://api.hyperliquid.xyz/info {"type": "metaAndAssetCtxs"}: per listed, not delisted perp with a
           positive markPx and prevDayPx -> {coin, mark, prevDay, changePct = (mark - prevDay) / prevDay, funding,
           openInterest, dayNotional (dayNtlVlm), maxLeverage}; a failure serves the last good book marked stale
  range    POST {"type": "candleSnapshot", "req": {coin, interval "1h", startTime now - 8 h, endTime now}}: the mean
           of (h - l) / c over the finite positive candles, None under three (cached a minute per coin)

The feed also carries the Kraken Futures perpetual each coin trades as on the desk's sim venue (PF_<COIN>USD, BTC as
XBT; the 'k'-prefixed thousand-unit coins and coins Kraken does not list have none) and the hourly ranges of the
coins the scan can pick (the liquid qualifying movers and the held coins)."""
from ..data import http

INFO_URL = "https://api.hyperliquid.xyz/info"
QUOTE_TTL_S = 8.0
CANDLE_TTL_S = 60.0
_CACHE = {"quotes": None, "at": 0.0, "ranges": {}}


def post_info(body, timeout=8.0):
    """one read of the public /info: the same body, headers and single attempt as a plain urlopen, and the same
    errors (HTTPError, URLError, a bad JSON body), now over a pooled keep-alive connection (the read is declared
    idempotent) and through the desk's pacing ledger, refusal breaker (HostCooling while paused) and STATS."""
    return http.post_json(INFO_URL, body, timeout=timeout, idempotent=True,
                          headers={"content-type": "application/json", "User-Agent": "MasterDesk/1.0"})


def parse_quotes(payload):
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError("Hyperliquid returned an unexpected book.")
    universe = (payload[0] or {}).get("universe") or []
    ctxs = payload[1] or []
    out = []
    for i, entry in enumerate(universe):
        ctx = ctxs[i] if i < len(ctxs) else None
        if not entry or not ctx or entry.get("isDelisted"):
            continue
        mark, prev = _num(ctx.get("markPx")), _num(ctx.get("prevDayPx"))
        if not (mark > 0) or not (prev > 0):
            continue
        out.append({"coin": entry["name"], "mark": mark, "prevDay": prev, "changePct": (mark - prev) / prev,
                    "funding": _num(ctx.get("funding")), "openInterest": _num(ctx.get("openInterest")),
                    "dayNotional": _num(ctx.get("dayNtlVlm")), "maxLeverage": entry.get("maxLeverage")})
    if not out:
        raise ValueError("Hyperliquid returned no live perps.")
    return out


def _num(x):
    """Number(x) for the API's decimal strings (NaN when unparseable)."""
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def average_range_pct(candles):
    if len(candles) < 3:
        return None
    ranges = [(c["h"] - c["l"]) / c["c"] for c in candles if c["c"]]
    ranges = [r for r in ranges if r == r and r not in (float("inf"), float("-inf")) and r > 0]
    if len(ranges) < 3:
        return None
    s = 0.0
    for r in ranges:
        s += r
    return s / len(ranges)


def load_quotes(now, poster=post_info):
    if _CACHE["quotes"] is not None and now - _CACHE["at"] < QUOTE_TTL_S:
        return {"quotes": _CACHE["quotes"], "asOf": _CACHE["at"], "error": None, "stale": False}
    try:
        quotes = parse_quotes(poster({"type": "metaAndAssetCtxs"}))
        _CACHE.update(quotes=quotes, at=now)
        return {"quotes": quotes, "asOf": now, "error": None, "stale": False}
    except Exception as e:                                  # noqa: BLE001
        if _CACHE["quotes"] is not None:
            return {"quotes": _CACHE["quotes"], "asOf": _CACHE["at"], "stale": True,
                    "error": f"Live marks failed ({e}). Showing the last good book."}
        return {"quotes": [], "asOf": None, "stale": True,
                "error": f"Hyperliquid is unreachable ({e}). The floor will not invent a price."}


def hourly_range_pct(coin, now, poster=post_info):
    hit = _CACHE["ranges"].get(coin)
    if hit and now - hit[0] < CANDLE_TTL_S:
        return hit[1]
    try:
        ms = int(now * 1000)
        payload = poster({"type": "candleSnapshot", "req": {"coin": coin, "interval": "1h",
                                                             "startTime": ms - 8 * 3600 * 1000, "endTime": ms}})
        if not isinstance(payload, list):
            raise ValueError("bad candles")
        candles = [{"h": _num(r.get("h")), "l": _num(r.get("l")), "c": _num(r.get("c"))}
                   for r in payload if isinstance(r, dict)]
        rng = average_range_pct(candles)
    except Exception:                                       # noqa: BLE001
        rng = None
    _CACHE["ranges"][coin] = (now, rng)
    return rng


def kraken_symbol(coin, listed):
    if coin.startswith("k") and coin[1:2].isupper():
        return None                                         # thousand-unit coins (kPEPE ...): no like-for-like perp
    sym = "PF_" + ("XBT" if coin == "BTC" else coin.upper()) + "USD"
    return sym if sym in listed else None


def feed(feeds, sleeve, now, arg=None):
    from ..sleeves.midna.hyperliquid import candidates
    book = load_quotes(now)
    try:
        # the latest ticker sweep's symbol set (at most an hour old; the mark stage's quote sweep usually serves it):
        # set(tickers()) was a second 136 KB sweep in 411 of this sleeve's 433 passes (2026-10-16/17)
        listed = feeds.hub.kraken_futures.listed() if feeds is not None and feeds.hub is not None else set()
    except Exception:                                       # noqa: BLE001
        listed = set()
    eng = getattr(sleeve, "engine", None)
    st = eng.store.sleeve_get(sleeve.CONFIG.sleeve_id) if eng is not None else {}
    want = sorted(candidates(book["quotes"]) | set(((st or {}).get("pos") or {}).keys()))
    # each coin's range is its own POST: fetched concurrently (in turn they held the pass ~2.4 s, 2026-10-16); the
    # same requests and the same per-coin minute cache as the source
    if len(want) > 2:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(6, len(want))) as ex:
            got = list(ex.map(lambda c: hourly_range_pct(c, now), want))
        ranges = dict(zip(want, got))
    else:
        ranges = {c: hourly_range_pct(c, now) for c in want}
    return dict(book, ranges=ranges, kraken={q["coin"]: kraken_symbol(q["coin"], listed) for q in book["quotes"]})
