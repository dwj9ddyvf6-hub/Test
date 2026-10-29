"""Kraken public inputs of the Aurelia source desk's Kraken books (free_kraken_* sleeves) that the DataHub does not
serve: the perpetuals' hourly funding prints, the futures instrument list and the ENJ/USD spot book. Public
endpoints only; no credential.

funding(symbol, now)   the source's historical-funding-rates call (kraken_paper.funding / kraken_history.funding):
                       the rows exactly as Kraken returns them, oldest first —
                       [{"timestamp": "...Z", "fundingRate": x, "relativeFundingRate": y}]. Cached per symbol and
                       refetched once a newer hourly print can exist (its newest stamp + 1 hour), at most once a
                       minute. A failed refetch serves nothing (the sleeve fails closed), never an older list as
                       if it were current.
instruments(now)       the futures instrument list (the basis books' contract identity; whether any ENJ contract is
                       listed): {"instruments": [...]}, cached 6 hours (the source's collect cadence).
depth(pair, now)       the Kraken spot order book (Depth, count=5) — the source's enj_spot call: the `result` book
                       {"asks": [[px, qty, ts], ...], "bids": [...]}; fetched on every call.
Each returns None when the endpoint is unreachable."""
import threading
from datetime import datetime

FUNDING = "https://futures.kraken.com/derivatives/api/v3/historical-funding-rates"
INSTRUMENTS = "https://futures.kraken.com/derivatives/api/v3/instruments"
DEPTH = "https://api.kraken.com/0/public/Depth"
INSTRUMENTS_TTL = 6 * 3600
RETRY_S = 60
_LOCK = threading.Lock()
_FUNDING = {}           # symbol -> {"at": fetch epoch, "rates": [...]}
_INSTRUMENTS = {}       # "x" -> {"at", "body"}


def _get(url, params=None):
    from ..data.http import get
    return get(url, params)


def _stamp(text):
    return datetime.fromisoformat(str(text).replace("Z", "+00:00")).timestamp()


def funding(symbol, now):
    with _LOCK:
        c = _FUNDING.get(symbol)
        if c is not None:
            newest = _stamp(c["rates"][-1]["timestamp"]) if c["rates"] else None
            if c["ok"] and newest is not None and now < newest + 3600:     # no newer hourly print can exist yet
                return c["rates"]
            if now - c["at"] < RETRY_S:                                     # (re)fetched under a minute ago
                return c["rates"] if c["ok"] else None
        try:
            body = _get(FUNDING, {"symbol": symbol}) or {}
            rates = list(body.get("rates") or [])
        except Exception:
            _FUNDING[symbol] = {"at": now, "rates": [], "ok": False}
            return None
        _FUNDING[symbol] = {"at": now, "rates": rates, "ok": True}
        return rates


def instruments(now):
    with _LOCK:
        c = _INSTRUMENTS.get("x")
        if c is not None and now - c["at"] < INSTRUMENTS_TTL:
            return c["body"]
        try:
            body = _get(INSTRUMENTS)
        except Exception:
            return None
        if not isinstance(body, dict) or "instruments" not in body:
            return None
        _INSTRUMENTS["x"] = {"at": now, "body": body}
        return body


def depth(pair, now):
    try:
        payload = _get(DEPTH, {"pair": pair, "count": 5}) or {}
    except Exception:
        return None
    return next(iter((payload.get("result") or {}).values()), {})


def reset():
    """drop the caches (tests)."""
    with _LOCK:
        _FUNDING.clear()
        _INSTRUMENTS.clear()
