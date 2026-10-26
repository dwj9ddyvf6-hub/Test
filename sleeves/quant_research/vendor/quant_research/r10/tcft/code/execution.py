"""R10 exact funded-swap and causal admission helpers, not a broker/strategy.

Inputs are explicitly supplied hypothetical execution prices and session slots.
The helper never invents a price for a missing bar, assumes a stop fill, or
certifies historical observations as executable native quotes.
"""
from decimal import Decimal, localcontext
from datetime import datetime
import math

VERSION = "r10-funded-swap-admission-v1"

def _d(x):
    if isinstance(x, bool):
        raise ValueError("boolean amount")
    d = Decimal(str(x))
    if not d.is_finite():
        raise ValueError("finite amount required")
    return d

def _t(s):
    if not isinstance(s, str):
        raise ValueError("clock must be an ISO string")
    t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError("aware clock required")
    return t

def target_gate(row, cutoff):
    """Required receipt/transform clocks and original target identity, no backdating."""
    try:
        end = _t(cutoff)
        clock = [_t(row[k]) for k in ("first_received", "ingested", "ready")]
        if not clock[0] <= clock[1] <= clock[2] <= end:
            return "NO_TRADE_CLOCK_ORDER_OR_FUTURE"
        if row.get("kind") != "ORIGINAL_INDEX_TARGET":
            return "NO_TRADE_CURRENT_HOLDINGS_NOT_TARGET"
        if any(not isinstance(row.get(k), str) or not row[k].strip() for k in
               ("owner_id", "security_id", "revision_id", "source_sha256")):
            return "NO_TRADE_IDENTITY"
        if len(row["source_sha256"]) != 64 or any(c not in "0123456789abcdef" for c in row["source_sha256"]):
            return "NO_TRADE_HASH"
        if row.get("allowances_complete") is not True:
            return "NO_TRADE_UNBOUNDED_MODEL_ALLOWANCE"
        if not (_t(row["announcement_time"]) <= clock[0] and
                _t(row["implementation_close"]) < _t(row["effective_open"])):
            return "NO_TRADE_EVENT_CLOCK"
        return "INPUT_SCHEMA_VALID_NOT_TRADE_AUTHORIZATION"
    except (KeyError, ValueError, TypeError):
        return "NO_TRADE_MALFORMED"

def risk_exit(last_entry, received_bid, halted=False, missing=False, stop=0.05):
    """Observed threshold triggers a request; next actual executable bid is required."""
    if halted or missing or received_bid is None:
        return {"action": "PRESERVE_POSITION_CANCEL_ENTRIES", "fill_price": None}
    entry, bid, threshold = map(_d, (last_entry, received_bid, stop))
    if entry <= 0 or bid <= 0 or not 0 < threshold < 1:
        raise ValueError("invalid price/stop")
    return {"action": "REQUEST_NEXT_OBTAINABLE_EXIT" if bid <= entry*(1-threshold) else "HOLD",
            "fill_price": None}

def completed_swap(notional, fee, fill_fraction, qqq_prices, stock_entry,
                   stock_exit, stock_entry_slot, stock_exit_slot,
                   donor_settlement_slot, restore_slot):
    """Exact four/two-leg cash accounting from already-held QQQ to restored QQQ.

    Quotes are given hypothetical raw execution prices, fee excludes any spread
    already in those prices. Empty stock entry after an actual donor sale still
    pays donor/restore fees and retains the entire displaced QQQ opportunity cost.
    Session slots describe an external calendar; no synthetic slot is called T+1.
    """
    with localcontext() as ctx:
        ctx.prec = 70
        n, c, f = map(_d, (notional, fee, fill_fraction))
        q = [_d(x) for x in qqq_prices]
        if n <= 0 or not 0 <= c < 1 or not 0 <= f <= 1 or any(x <= 0 for x in q):
            raise ValueError("invalid amounts")
        slots = (stock_entry_slot, stock_exit_slot, donor_settlement_slot, restore_slot)
        if any(type(x) is not int for x in slots) or not 0 < donor_settlement_slot <= stock_entry_slot < stock_exit_slot < restore_slot < len(q):
            raise ValueError("unsettled purchase or incomplete chronological restore")
        pe, px = map(_d, (stock_entry, stock_exit))
        if pe <= 0 or px <= 0:
            raise ValueError("positive stock execution prices required")
        fees = n*c
        proceeds = n*(1-c)
        spent = proceeds*f
        stock_units = spent/(pe*(1+c))
        stock_buy_fee = stock_units*pe*c
        stock_value = stock_units*px
        stock_sell_fee = stock_value*c
        cash = proceeds-spent + stock_value-stock_sell_fee
        restored_units = cash/(q[restore_slot]*(1+c))
        restore_fee = restored_units*q[restore_slot]*c
        fees += stock_buy_fee+stock_sell_fee+restore_fee
        control_units = n/q[0]
        wealth = restored_units*q[restore_slot]
        control = control_units*q[restore_slot]
        identity = ((1-c)/(1+c))*((1-f)+f*(px/pe)*((1-c)/(1+c)))/(q[restore_slot]/q[0])
        ratio = wealth/control
        if abs(ratio-identity) > Decimal("1e-60"):
            raise ArithmeticError("independent cash identity mismatch")
        return {"restored_mark_wealth": str(wealth), "held_core_wealth": str(control),
                "relative_wealth_ratio": str(ratio), "relative_log_wealth": str(ratio.ln()),
                "fees_paid": str(fees), "stock_units": str(stock_units),
                "stock_occupancy_sessions": stock_exit_slot-stock_entry_slot if stock_units else 0,
                "donor_displacement_sessions": restore_slot,
                "stock_sell_pending_until": restore_slot,
                "cash_before_stock_entry": str(proceeds),
                "prices_are_hypothetical": True, "canonical_execution_validated": False}
