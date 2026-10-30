"""Broker interface, a simulated (shadow) broker, and a paper-broker client skeleton.

TWO order paths exist on purpose:
  * ShadowBroker  : never touches a network; fills at the last observed mark. Safe default.
  * PaperBroker   : sends real *paper* orders. Exactly ONE component in the whole system may
                    own this path (see docs/05_execution_and_order_safety.md).

Key behaviours (each is a real failure story):
  * client order id is persisted BEFORE the network call; a retry looks the id up first;
  * HTTP 4xx (except 429) = refusal; transport error / 5xx = *unknown* (order may exist);
  * "final" states are only filled/canceled/expired/rejected/replaced. `done_for_day`,
    `stopped`, `suspended` can still fill or resume and must keep being polled;
  * limit prices obey the tick size (>= $1: 2 decimals, < $1: 4 decimals) and never cross a cap
    after rounding.
"""
from __future__ import annotations
import json
import math
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Protocol

FINAL_STATES = {"filled", "canceled", "expired", "rejected", "replaced"}


@dataclass
class Order:
    cid: str
    symbol: str
    side: str          # buy | sell
    qty: float
    limit: float | None = None
    status: str = "new"
    filled_qty: float = 0.0
    avg_price: float | None = None


class SendUnknown(Exception):
    """Transport failure: the order may or may not exist at the broker. Resolve by cid lookup."""


class Refused(Exception):
    """Broker definitively rejected the order (4xx). Safe to retry under a NEW attempt id."""


class Broker(Protocol):
    def submit(self, o: Order) -> Order: ...
    def lookup(self, cid: str) -> Order | None: ...


def tick_round(price: float, side: str, cap: float | None = None) -> float:
    """Round a limit price to a legal tick, away from crossing; never above `cap` for buys."""
    dp = 2 if price >= 1 else 4
    f = 10 ** dp
    p = math.floor(price * f) / f if side == "buy" else math.ceil(price * f) / f
    if side == "buy" and cap is not None and p > cap:
        p = math.floor(cap * f) / f
    return round(p, dp)


class ShadowBroker:
    """Simulated fills at the last observed mark. Idempotent by cid. No network."""

    def __init__(self, marks: dict[str, float]):
        self.marks, self.orders = marks, {}

    def submit(self, o: Order) -> Order:
        if o.cid in self.orders:                      # idempotent
            return self.orders[o.cid]
        px = self.marks.get(o.symbol)
        if px is None:                                # missing data: no fill, no guess
            o.status = "rejected"
        else:
            o.status, o.filled_qty, o.avg_price = "filled", o.qty, px
        self.orders[o.cid] = o
        return o

    def lookup(self, cid: str):
        return self.orders.get(cid)


@dataclass
class PaperBroker:
    """Skeleton REST client for a paper brokerage. Fill in `base_url` and auth for YOUR broker.

    Never hard-code keys: read them from the environment or a 0600 file outside any repository.
    """
    base_url: str
    headers: dict = field(default_factory=dict)
    timeout_s: float = 20.0

    def _req(self, method: str, path: str, body: dict | None = None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base_url + path, data=data, method=method,
                                     headers={"content-type": "application/json", **self.headers})
        return urllib.request.urlopen(req, timeout=self.timeout_s)

    def lookup(self, cid: str) -> Order | None:
        try:
            with self._req("GET", f"/orders:by_client_order_id?client_order_id={cid}") as r:
                d = json.load(r)
            return Order(cid, d["symbol"], d["side"], float(d["qty"]), status=d["status"],
                         filled_qty=float(d.get("filled_qty") or 0),
                         avg_price=float(d["filled_avg_price"]) if d.get("filled_avg_price") else None)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

    def submit(self, o: Order) -> Order:
        # 1. caller has ALREADY persisted `entry_sent`/cid in the ledger before calling us.
        # 2. look up first: after a crash or timeout the order may already exist.
        existing = self.lookup(o.cid)
        if existing is not None:
            return existing
        body = {"symbol": o.symbol, "side": o.side, "qty": str(o.qty), "type": "limit" if o.limit else "market",
                "time_in_force": "day", "client_order_id": o.cid}
        if o.limit:
            body["limit_price"] = str(o.limit)
        try:
            with self._req("POST", "/orders", body) as r:
                d = json.load(r)
            o.status = d["status"]
            return o
        except urllib.error.HTTPError as e:
            if 400 <= e.code < 500 and e.code != 429:
                raise Refused(f"HTTP {e.code}") from e
            raise SendUnknown(f"HTTP {e.code}") from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise SendUnknown(str(e)) from e
