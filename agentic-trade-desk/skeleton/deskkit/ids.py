"""Deterministic, restart-safe identifiers.

RULE: an identifier for a trading decision is derived ONLY from data that does not change
across process restarts: sleeve, symbol, the *data bar* that produced the signal, the side,
the leg and the attempt number. NEVER from the wall clock of the current pass.

Failure story this prevents: a strategy library stamped each signal with the time of the
current pass. Every supervisor restart produced a "new" signal id, so already-taken signals
were re-entered several times in one morning.
"""
from __future__ import annotations
import hashlib
import re

_SAFE = re.compile(r"[^A-Za-z0-9._-]")


def signal_key(sleeve: str, symbol: str, bar_ts: str, kind: str, side: str) -> str:
    """Stable key for 'this sleeve wants to do <kind>/<side> on <symbol> because of bar <bar_ts>'.

    bar_ts must be the timestamp of the newest *data bar* the decision was computed from
    (ISO string in the exchange time zone or UTC), never datetime.now().
    """
    raw = "|".join([sleeve, symbol.upper(), bar_ts, kind, side])
    return _SAFE.sub("_", raw)


def client_order_id(prefix: str, key: str, leg: int = 0, attempt: int = 0, max_len: int = 48) -> str:
    """Deterministic broker client order id. Brokers cap the length (often 48 chars), so hash the key.

    attempt 0 is the first try. A *refused* (never accepted) order may be retried under attempt+1.
    A *timed-out* order (unknown outcome) must NOT be retried under a new id: look it up first.
    """
    digest = hashlib.sha256(key.encode()).hexdigest()[:16]
    cid = f"{prefix}-{digest}-{leg}-{attempt}"
    return cid[:max_len]
