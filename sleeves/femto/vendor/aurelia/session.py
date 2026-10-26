"""Session clock rules for the paper desk. Pure: no broker and no market data.

A decision uses the last finished daily bar. The order for that decision is a
market-on-close order on a later session, and only until 15 minutes before the
close Alpaca advertises. Early closes move `next_close`, so the cutoff moves with them.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
MOC_CUTOFF = timedelta(minutes=15)
STALE_DAYS = 5
EXPOSURE_BAND = 0.20

RETRY_STATUSES = frozenset({"canceled", "expired", "rejected", "suspended"})
WORKING_STATUSES = frozenset({
    "new", "accepted", "pending_new", "accepted_for_bidding", "partially_filled", "filled",
    "calculated", "held", "pending_replace", "already_working", "already_submitted",
})
MAX_ATTEMPTS = 3


def parse_ts(value: str) -> datetime:
    """Parse an Alpaca timestamp. The clock emits nanoseconds; datetime accepts microseconds."""
    text = value.strip().replace("Z", "+00:00")
    if "." in text:
        head, rest = text.split(".", 1)
        digits: list[str] = []
        i = 0
        while i < len(rest) and rest[i].isdigit():
            digits.append(rest[i])
            i += 1
        frac = "".join(digits)[:6]
        text = f"{head}.{frac}{rest[i:]}" if frac else f"{head}{rest[i:]}"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ET)
    return parsed.astimezone(ET)


def completed_through(clock: dict) -> datetime.date:
    """Last calendar date whose daily bar is a finished session.

    While `next_close` is still ahead, that date has not finished, so the prior
    date is the last one a strategy may use. After the close timestamp has passed
    and the clock has not rolled forward, that close's own date is finished.
    """
    now = parse_ts(clock["timestamp"])
    close = parse_ts(clock["next_close"])
    if now >= close:
        return close.date()
    return close.date() - timedelta(days=1)


def moc_window(clock: dict) -> bool:
    """True only inside a regular session, at least 15 minutes before the advertised close."""
    if not clock.get("is_open"):
        return False
    now = parse_ts(clock["timestamp"])
    close = parse_ts(clock["next_close"])
    return now < close - MOC_CUTOFF


def refresh_allowed(clock: dict) -> bool:
    """Downloads stay out of the order window and the 45 minutes before the open."""
    if clock.get("is_open"):
        return False
    now = parse_ts(clock["timestamp"])
    opens = parse_ts(clock["next_open"])
    return opens - now >= timedelta(minutes=45)


def submit_block_reason(as_of: datetime.date, clock: dict) -> str | None:
    """None when an order for `as_of` may be sent. Otherwise a stable reason code."""
    if not clock.get("is_open"):
        return "market_closed"
    now = parse_ts(clock["timestamp"])
    close = parse_ts(clock["next_close"])
    if now >= close - MOC_CUTOFF:
        return "after_cutoff"
    session = now.date()
    if as_of >= session:
        return "same_day_bar"
    if (session - as_of).days > STALE_DAYS:
        return "stale_data"
    return None


def resolve_book(signal: float, book: float | None) -> float:
    """Exposure the book keeps until the signal moves by 0.20, or leaves zero.

    This is the band in the Aurelia backtest: the target decided at a close is
    held, and it is replaced only when the new target differs by at least 0.20
    or the sleeve is going flat. A first entry from a flat book happens once
    the signal itself clears 0.20.
    """
    try:
        signal = float(signal)
    except (TypeError, ValueError):
        signal = 0.0
    if not math.isfinite(signal):
        signal = 0.0
    signal = max(0.0, signal)
    try:
        held = 0.0 if book is None else float(book)
    except (TypeError, ValueError):
        held = 0.0
    if not math.isfinite(held):
        held = 0.0
    held = max(0.0, held)
    if signal == 0.0 and held > 0.0:
        return 0.0
    if abs(signal - held) >= EXPOSURE_BAND - 1e-12:
        return signal
    return held


def order_client_id(as_of: str, symbol: str, side: str, attempt: int) -> str:
    base = f"aurelia-{as_of}-{symbol}-{side}"
    if attempt > 1:
        base = f"{base}-r{attempt}"
    return base[:48]


def plan_dispatch(as_of: str, symbol: str, side: str, broker_orders: list[dict]) -> tuple[str, str]:
    """Decide whether to send, skip, or halt for one name.

    A working or filled order blocks a second send. A rejected, canceled, or
    expired order consumes an attempt. Three failures halt until the next decision.
    """
    base = f"aurelia-{as_of}-{symbol}-{side}"
    related = [o for o in broker_orders if str(o.get("client_order_id") or "").startswith(base)]
    working = [o for o in related if o.get("status") not in RETRY_STATUSES]
    if working:
        return "skip", str(working[-1].get("client_order_id") or base)
    failures = [o for o in related if o.get("status") in RETRY_STATUSES]
    if len(failures) >= MAX_ATTEMPTS:
        last = str(failures[-1].get("client_order_id") or base)
        return "halt", last
    return "send", order_client_id(as_of, symbol, side, len(failures) + 1)


def ticket_mode(statuses: set[str | None]) -> str:
    """Collapse broker acknowledgements into one plan mode.

    A rejected or canceled ticket stays in ``retry`` so the next cycle sends it
    again. ``submitted`` is only for orders the broker has accepted or filled.
    """
    clean = {s for s in statuses if s}
    if not clean:
        return "staged"
    if clean <= {"halted"}:
        return "halted"
    if clean & RETRY_STATUSES:
        return "retry"
    return "submitted"


def broker_ticket_open(sent: list[dict], broker_orders: list[dict]) -> bool:
    """True when every sent client id is still working or filled at the broker."""
    if not sent:
        return False
    by_id = {o.get("client_order_id"): o.get("status") for o in broker_orders}
    for row in sent:
        client_id = row.get("client_order_id")
        if not client_id:
            return False
        status = by_id.get(client_id)
        if status not in WORKING_STATUSES:
            return False
    return True


def overnight_buying_power(account: dict) -> float:
    """Buying power that can fund a position held past the close.

    Alpaca's `buying_power` can be the larger day-trade figure. A market-on-close
    order is still on the book overnight, so the Reg-T figure is the one that binds.
    """
    regt = float(account.get("regt_buying_power") or 0.0)
    quoted = float(account.get("buying_power") or 0.0)
    if regt > 0 and quoted > 0:
        return min(regt, quoted)
    return regt or quoted


def position_after(held: dict[str, int], orders: list[dict]) -> dict[str, int]:
    pos = {k: int(v) for k, v in held.items()}
    for order in orders:
        sign = 1 if order["side"] == "buy" else -1
        pos[order["symbol"]] = pos.get(order["symbol"], 0) + sign * int(order["qty"])
    return pos


def margin_requirement(positions: dict[str, int], prices: dict[str, float], requirements: dict[str, float]) -> float:
    total = 0.0
    for symbol, qty in positions.items():
        if not qty:
            continue
        total += abs(qty) * float(prices.get(symbol) or 0.0) * float(requirements.get(symbol) or 0.5)
    return total


def fit_to_margin(orders: list[dict], held: dict[str, int], prices: dict[str, float], equity: float,
                  requirements: dict[str, float], buffer: float = 0.90) -> tuple[list[dict], bool]:
    """Shrink buys until projected initial margin fits inside equity.

    Requirements are fractions of notional (Reg T, or the name's maintenance
    requirement when that is higher). Sells stay, because they reduce the requirement.
    """
    sells = [dict(o) for o in orders if o["side"] == "sell"]
    buys = [dict(o) for o in orders if o["side"] == "buy"]
    other = [dict(o) for o in orders if o["side"] not in ("buy", "sell")]
    limit = max(0.0, float(equity)) * buffer
    if margin_requirement(position_after(held, sells + buys + other), prices, requirements) <= limit:
        return sells + buys + other, False
    lo, hi = 0.0, 1.0
    best: list[dict] = []
    for _ in range(24):
        mid = (lo + hi) / 2.0
        scaled = []
        for order in buys:
            qty = int(order["qty"] * mid)
            if qty > 0:
                scaled.append({**order, "qty": qty})
        if margin_requirement(position_after(held, sells + scaled), prices, requirements) <= limit:
            best = scaled
            lo = mid
        else:
            hi = mid
    return sells + best + other, True


def fit_to_buying_power(orders: list[dict], prices: dict[str, float], buying_power: float, buffer: float = 0.95) -> tuple[list[dict], bool]:
    """Scale buys so their notional fits in buying power. Sells are unchanged.

    Sell proceeds are not assumed available: a market-on-close sell and buy
    fill together, so the sell does not fund the buy at submission.
    """
    sells = [dict(o) for o in orders if o["side"] == "sell"]
    buys = [dict(o) for o in orders if o["side"] == "buy"]
    other = [dict(o) for o in orders if o["side"] not in ("buy", "sell")]
    buy_notional = sum(o["qty"] * float(prices.get(o["symbol"]) or 0.0) for o in buys)
    room = max(0.0, float(buying_power)) * buffer
    if buy_notional <= room or buy_notional <= 0:
        return sells + buys + other, False
    if room <= 0:
        return sells + other, True
    scale = room / buy_notional
    scaled = []
    for order in buys:
        qty = int(order["qty"] * scale)
        if qty > 0:
            scaled.append({**order, "qty": qty})
    return sells + scaled + other, True
