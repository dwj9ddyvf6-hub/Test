"""Aurelia Gold book — lean-desk port (Wave D, Decision #119 family).

EXTRACTED from the old desk's aurelia_paper.py + aurelia_allocate.py.
The gold sleeve of the Aurelia book on signal aurelia-gc-band20-v1:
GLD one-for-one with the (band-resolved, gross-capped) gold exposure,
sized on the same flat $500,000 Aurelia book as aurelia_ndx — gold sits
ON TOP of the Nasdaq capital (book gross cap 1.80 in cap_exposures).

VIRTUAL BOOK MAPPING: Ledger account "aurelia_gold", budget config
BUDGET_USD = 500,000 (the shared Aurelia book budget, per
aurelia_common.BUDGETS: aurelia_ndx and aurelia_gold are sleeves of ONE
$500k book). Holdings arrive as context.extra["sleeve_state"]
({"GLD": {"qty": n}}). Only GLD deltas are emitted here; QQQ/TQQQ/BIL
deltas belong to aurelia_ndx. Inputs via context.extra: "exposures"
{"ndx","gold"} (required), "book" prior band state, "posture_cap"
(caps Nasdaq only; gold is never posture-capped, as on the old desk).
"""
import math

from .compat import BaseSleeve, Intent, SleeveConfig

SIGNAL_ID = "aurelia-gc-band20-v1"
BUDGET_USD = 500_000.0
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


class AureliaGold(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        exp = extra.get("exposures")
        if not isinstance(exp, dict) or "ndx" not in exp or "gold" not in exp:
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
                prices[s] = float(bl[-1]["c"])
        gld = bars.get("GLD") or []
        if not gld:
            return []
        book = extra.get("book") or {}
        book_ndx = resolve_book(float(exp["ndx"]), book.get("ndx"))
        if extra.get("posture_cap") is not None:
            book_ndx = min(book_ndx, float(extra["posture_cap"]))
        book_gold = resolve_book(float(exp["gold"]), book.get("gold"))
        weights = sleeve_weights(book_ndx, book_gold)
        targets = share_targets(weights, BUDGET_USD, prices)
        orders = order_deltas(targets, held, prices, BUDGET_USD)
        intents = []
        for o in orders:
            if o["symbol"] != "GLD":
                continue
            px = round(float(prices["GLD"]), 2)
            kind = "enter" if o["side"] == "buy" else "exit"
            intents.append(Intent(
                kind, "GLD", qty_hint=o["qty"], price_hint=px,
                reason="aurelia_gold rebalance (account=%s book_gold=%.4f "
                       "signal=%s)" % (ACCOUNT, book_gold, SIGNAL_ID)))
        return intents


def signal(bars, slice_state, context):
    return AureliaGold().signal(bars, slice_state, context)
