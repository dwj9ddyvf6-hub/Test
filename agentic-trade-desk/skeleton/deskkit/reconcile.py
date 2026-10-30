"""Reconcile the internal book against the broker, tolerate in-flight orders, import orphans.

Rules:
  * Compare per (account, symbol) summed across sleeves.
  * A broker position may *lead* the book by the quantity of a pending order (a fill that has
    landed but not yet been read back). Anything beyond that is a real mismatch -> ALERT.
  * Positions/orders that exist at the broker with a desk-owned id prefix but are missing from
    the book (e.g. placed by the standby while the primary was down) are IMPORTED, ADD-ONLY.
  * Never "fix" a mismatch by trading. Alert, then repair the book from broker truth.
"""
from __future__ import annotations


def reconcile(book_qty: dict[str, float], broker_qty: dict[str, float],
              pending_buy: dict[str, float] | None = None,
              pending_sell: dict[str, float] | None = None, eps: float = 1e-6) -> list[dict]:
    pending_buy, pending_sell = pending_buy or {}, pending_sell or {}
    issues = []
    for sym in sorted(set(book_qty) | set(broker_qty)):
        b, k = book_qty.get(sym, 0.0), broker_qty.get(sym, 0.0)
        lo = b - pending_sell.get(sym, 0.0)
        hi = b + pending_buy.get(sym, 0.0)
        if not (lo - eps <= k <= hi + eps):
            issues.append({"symbol": sym, "book": b, "broker": k,
                           "allowed": (lo, hi)})
    return issues


def orphans(broker_orders: list[dict], book_cids: set[str], prefixes: tuple[str, ...]) -> list[dict]:
    """Desk-owned broker orders (by client-id prefix) that the book does not know about."""
    return [o for o in broker_orders
            if o["client_order_id"].startswith(prefixes) and o["client_order_id"] not in book_cids]
