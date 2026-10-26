"""The Aurelia paper desk's plan builder (desk/paper.py build_plan, _same_book). Its imports are the
vendored allocate / session modules.

Source: Agentic-Trading-Desk aurelia-paper-desk @1720157f768e63ebe76b148aa3d7d1a409ac9673. Each block after a `# >>> excerpt` marker is the
exact text of that source line range (the marker carries its sha256; tests/test_aurelia.py re-hashes every block)."""
from __future__ import annotations

from .allocate import ndx_exposure, order_deltas, share_targets, sleeve_weights
from .session import fit_to_buying_power, fit_to_margin, margin_requirement, position_after


# >>> excerpt desk/paper.py lines 46-50 blob 5e57d0d8cba1a673a2348f643d15e206c210140e sha256 d271722c4b2b60c1c013a22827416f2e15522703d0055fe0dad374cf66f1b052
SYMBOLS = ("QQQ", "TQQQ", "GLD", "BIL")
# Gold signal is the front-month future, which is what the Aurelia test used.
# The account holds that exposure in GLD. The book changes only when a sleeve
# moves by 0.20, the same band as the backtest.
SIGNAL_ID = "aurelia-gc-band20-v1"


# >>> excerpt desk/paper.py lines 278-333 blob 5e57d0d8cba1a673a2348f643d15e206c210140e sha256 77e9a6b1a40de17848e84c80278d1f15c539aa5d027c8da721ead04c77008128
def build_plan(equity: float, prices: dict[str, float], held: dict[str, int] | None = None,
               exp: dict | None = None, frozen: dict | None = None, buying_power: float | None = None,
               requirements: dict[str, float] | None = None) -> dict:
    if exp is None:
        raise ValueError("exp is required")
    held = held or {}
    if frozen and frozen.get("as_of") == exp["as_of"] and frozen.get("frozen_targets"):
        targets = {k: int(v) for k, v in frozen["frozen_targets"].items()}
        weights = frozen["weights"]
        prices = {**prices, **{k: float(v) for k, v in frozen.get("prices", {}).items()}}
    else:
        weights = sleeve_weights(exp["aurelia_ndx"], exp["aurelia_gold"])
        targets = share_targets(weights, equity, prices)
    orders = order_deltas(targets, {s: q for s, q in held.items() if s in SYMBOLS}, prices, equity)
    orders = [o for o in orders if o["symbol"] in SYMBOLS and prices.get(o["symbol"])]
    held_book = {s: q for s, q in held.items() if s in SYMBOLS}
    scaled = False
    if requirements:
        orders, scaled_margin = fit_to_margin(orders, held_book, prices, equity, requirements)
        scaled = scaled or scaled_margin
    if buying_power is not None:
        orders, scaled_bp = fit_to_buying_power(orders, prices, buying_power)
        scaled = scaled or scaled_bp
    for order in orders:
        order["type"] = "market"
        order["time_in_force"] = "cls"
    ignored = sorted(s for s in held if s not in SYMBOLS and held[s])
    return {
        **exp,
        "equity": equity,
        "buying_power": buying_power,
        "prices": prices,
        "weights": weights,
        "achieved_ndx": ndx_exposure(weights),
        "targets": targets,
        "frozen_targets": targets,
        "orders": orders,
        "orders_scaled": scaled,
        "margin_requirement": margin_requirement(position_after(held_book, orders), prices, requirements or {}),
        "ignored_positions": ignored,
        "sleeves_traded": ["aurelia_ndx", "aurelia_gold"],
        "sleeves_shadow": ["gestalt", "n6", "broken_hedge", "variance_value"],
    }


def _same_book(prior: dict | None, book_ndx: float, book_gold: float, as_of: str) -> bool:
    """True when this session's share counts were already frozen for this book."""
    if not prior or prior.get("signal_id") != SIGNAL_ID or prior.get("as_of") != as_of:
        return False
    if not prior.get("frozen_targets"):
        return False
    try:
        return abs(float(prior.get("book_ndx")) - book_ndx) < 1e-6 and abs(float(prior.get("book_gold")) - book_gold) < 1e-6
    except (TypeError, ValueError):
        return False
