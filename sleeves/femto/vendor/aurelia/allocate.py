"""Turn Aurelia exposures into share targets. Pure: no broker, no clock.

The Nasdaq sleeve is QQQ plus TQQQ, sized so QQQ + 3 × TQQQ equals the Nasdaq exposure
and the two together never use more than 100% of NAV. Gold is GLD, one for one.
If the capital the two sleeves use would exceed GROSS_CAP, both exposures are scaled
by the same factor before the mapping, so the 3× identity survives.
Idle weight above 2% sits in BIL.
"""

from __future__ import annotations

# Capital used, not exposure. A 3x Nasdaq sleeve uses 100% of NAV via TQQQ.
# Gold sits on top, so the account may use a modest amount of margin. 1.80 keeps
# a fully invested Nasdaq sleeve plus a 0.80 gold sleeve inside the paper buying power.
GROSS_CAP = 1.80
NDX_CAP = 3.0
MIN_WEIGHT = 0.02


def _capital(ndx: float, gold: float) -> float:
    return (ndx if ndx <= 1.0 else 1.0) + gold


def cap_exposures(ndx: float, gold: float, gross_cap: float = GROSS_CAP) -> tuple[float, float]:
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


def sleeve_weights(ndx: float, gold: float) -> dict[str, float]:
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


def ndx_exposure(weights: dict[str, float]) -> float:
    return weights.get("QQQ", 0.0) + 3.0 * weights.get("TQQQ", 0.0)


def share_targets(weights: dict[str, float], equity: float, prices: dict[str, float]) -> dict[str, int]:
    out = {}
    for symbol, weight in weights.items():
        px = prices.get(symbol)
        if not px or px <= 0 or weight <= 0:
            continue
        qty = int(equity * weight / px)
        if qty > 0:
            out[symbol] = qty
    return out


def order_deltas(targets: dict[str, int], held: dict[str, int], prices: dict[str, float], equity: float,
                 band: float = MIN_WEIGHT) -> list[dict]:
    """Share diffs. A new name always trades. An existing name trades only when its weight moves by `band`."""
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
        orders.append({"symbol": symbol, "side": "buy" if delta > 0 else "sell", "qty": abs(delta)})
    return orders
