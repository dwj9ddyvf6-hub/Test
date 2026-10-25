"""Aurelia Gold book — lean-desk port (Wave D, Decision #119 family).

EXTRACTED from the old desk's aurelia_paper.py + aurelia_allocate.py.
The gold sleeve of the Aurelia book on signal aurelia-gc-band20-v1:
GLD one-for-one with the (band-resolved, gross-capped) gold exposure
— gold sits ON TOP of the Nasdaq capital (book gross cap 1.80 in
cap_exposures).

SIZING BASIS (AURELIA-EXEC, 2026-10-18): the two book sleeves once
sized on ONE flat $500,000 sim book (aurelia_common.BUDGETS). On the
lean desk that basis was a defect (desk audit V-04/V-06): the sleeve
executes at the real broker, so targets now size off context.equity
— the broker-refreshed account equity the dispatcher injects, the
basis every other sleeve on the desk uses. No equity basis
(0 / unreadable) -> the sleeve is inert. Holdings arrive as
context.extra["sleeve_state"] ({"GLD": {"qty": n}}). Only GLD deltas
are emitted here; QQQ/TQQQ/BIL deltas belong to aurelia_ndx. Inputs
via context.extra: "exposures" {"ndx","gold"} (required; supplied
by core.book_feeds from the aurelia-gc-band20-v1 producer,
core/aurelia_signal.py), "book" prior band state, "posture_cap"
(caps Nasdaq only; gold is never posture-capped, as on the old desk).
"""
import math

from core.sleeve import BaseSleeve, Intent, SleeveConfig

SIGNAL_ID = "aurelia-gc-band20-v1"
ACCOUNT = "aurelia_gold"
SYMBOLS = ("QQQ", "TQQQ", "GLD", "BIL")
EXPOSURE_BAND = 0.20
GROSS_CAP = 1.80
NDX_CAP = 3.0
MIN_WEIGHT = 0.02

CONFIG = SleeveConfig(
    sleeve_id="aurelia_gold", cadence_s=300, universe=("GLD",),
    state_schema={"position": "dict|None"}, risk_pct=None)


# --- aurelia_allocate.py, verbatim (same copy as aurelia_ndx) -----------
def _capital(ndx, gold):
    return (ndx if ndx <= 1.0 else 1.0) + gold


def cap_exposures(ndx, gold, gross_cap=GROSS_CAP):
    ndx = min(max(float(ndx), 0.0), NDX_CAP)
    gold = max(float(gold), 0.0)
    if _capital(ndx, gold) <= gross_cap:
        return ndx, gold
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2.0
        if _capital(ndx * mid, gold * mid) <= gross_cap:
            lo = mid
        else:
            hi = mid
    return ndx * lo, gold * lo


def sleeve_weights(ndx, gold):
    ndx, gold = cap_exposures(ndx, gold)
    if ndx <= 1.0:
        weights = {"QQQ": ndx, "TQQQ": 0.0}
        used = ndx
    else:
        tqqq = (ndx - 1.0) / 2.0
        weights = {"QQQ": 1.0 - tqqq, "TQQQ": tqqq}
        used = 1.0
    weights["GLD"] = gold
    used += gold
    cash = max(0.0, 1.0 - used)
    weights["BIL"] = cash if cash >= MIN_WEIGHT else 0.0
    return {k: round(v, 6) for k, v in weights.items() if v > 1e-8}


def share_targets(weights, equity, prices):
    out = {}
    for symbol, weight in weights.items():
        px = prices.get(symbol)
        if not px or px <= 0 or weight <= 0:
            continue
        qty = int(equity * weight / px)
        if qty > 0:
            out[symbol] = qty
    return out


def order_deltas(targets, held, prices, equity, band=MIN_WEIGHT):
    orders = []
    symbols = set(targets) | {s for s, q in held.items() if q}
    for symbol in sorted(symbols):
        have = int(held.get(symbol, 0))
        want = int(targets.get(symbol, 0))
        px = prices.get(symbol) or 0.0
        if have and px and equity:
            if abs(want - have) * px / equity < band:
                continue
        delta = want - have
        if delta == 0:
            continue
        orders.append({"symbol": symbol, "side": "buy" if delta > 0 else "sell",
                       "qty": abs(delta)})
    return orders


def resolve_book(signal, book):
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


def _safe_float(value, default):
    """float() that never raises: junk input takes the fail-closed
    default instead of crashing the whole signal tick."""
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def fit_to_buying_power(orders, prices, buying_power, buffer=0.95):
    """aurelia_common.fit_to_buying_power, verbatim (same copy as
    aurelia_ndx; RR3 item 2, 2026-10-15): the old executor fitted the
    ONE shared Aurelia plan — gold orders included — through this
    bound before dispatch."""
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


class AureliaGold(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        exp = extra.get("exposures")
        if not isinstance(exp, dict) or "ndx" not in exp or "gold" not in exp:
            return []
        # AURELIA-EXEC: sizing basis = broker-refreshed account
        # equity on the context; absent/unreadable -> inert.
        equity = _safe_float(getattr(context, "equity", 0.0), 0.0)
        if equity <= 0:
            return []
        state = extra.get("sleeve_state") or {}
        held = {}
        for s in SYMBOLS:
            row = state.get(s) or {}
            q = row.get("qty") if isinstance(row, dict) else None
            if q:
                held[s] = int(q)
        prices = {}
        for s in SYMBOLS:
            bl = bars.get(s) or []
            if bl:
                px = _safe_float(bl[-1].get("c"), 0.0)
                if px > 0:
                    prices[s] = px  # non-finite / non-positive close = no price
        if "GLD" not in prices:
            return []
        book = extra.get("book") or {}
        # resolve_book IS the sanitizer (verbatim aurelia_common);
        # float() pre-conversion defeated it (None -> TypeError crash).
        book_ndx = resolve_book(exp["ndx"], book.get("ndx"))
        if extra.get("posture_cap") is not None:
            # An unreadable cap caps to zero (fail closed), never uncapped.
            book_ndx = min(book_ndx, _safe_float(extra["posture_cap"], 0.0))
        book_gold = resolve_book(exp["gold"], book.get("gold"))
        weights = sleeve_weights(book_ndx, book_gold)
        targets = share_targets(weights, equity, prices)
        orders = order_deltas(targets, held, prices, equity)
        bp_scaled = False
        if extra.get("buying_power") is not None:
            orders, bp_scaled = fit_to_buying_power(
                orders, prices, _safe_float(extra["buying_power"], 0.0))
        intents = []
        for o in orders:
            if o["symbol"] != "GLD":
                continue
            px = round(float(prices["GLD"]), 2)
            kind = "enter" if o["side"] == "buy" else "exit"
            intents.append(Intent(
                kind, "GLD", qty_hint=o["qty"], price_hint=px,
                reason="aurelia_gold rebalance (account=%s book_gold=%.4f "
                       "signal=%s%s)" % (ACCOUNT, book_gold, SIGNAL_ID,
                                         " bp_fit=scaled95" if bp_scaled else "")))
        return intents


def signal(bars, slice_state, context):
    return AureliaGold().signal(bars, slice_state, context)
