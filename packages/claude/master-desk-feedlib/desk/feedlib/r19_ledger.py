"""The R19 ledger's execution obligations for equity and native crypto spot cash books (backend/r19_core.py
Ledger.process / _execute / _housekeeping), as a pure model the R19 wrappers keep in their sleeve state while the desk
book holds the fills:

  * cancel_signal_ids withdraw the signal's pending / partial order before any intent executes;
  * one order per (signal, symbol, side): its requested quantity is fixed at creation (|target - owned|), a later
    re-emission may not change the target, a filled or cancelled order is idempotent, a partial one continues
    with min(desired, remaining);
  * each fill: min(desired, displayed size net of what this book already took from that displayed quote),
    whole native units, sells capped by the holding, buys capped by settled cash at price x (1 + fee) and the
    book's gross capacity, at the ask (buy) / bid (sell); the window (expires_at), the 2-second quote clock, an
    open equity session (crypto: a spot identity and contract metadata current at execution), a verified action
    census and an active tradable asset for buys, the frozen fee rule;
  * sale proceeds wait for the settlement release (vendored settlement_terms: T+1 from 2024-05-28 on the frozen
    DTCC 2022-2026 calendar, released at the first XNYS opening on or after maturity) before they are spendable.
Removed with the R19 runtime (not the books' rules): the 30 bps spread execution gate and the NAV-withheld coupling
it fed (a held name without a qualifying mark refused every buy), maintenance / margin (these books are cash-only
at gross 1), storage-pressure entry pauses, the operator enable switch.
Desk seam (named divergence of the wrappers): the ledger filled locally at the quote; the desk's venue executes the
decided quantity, and `unfill` returns what it left unexecuted to the order, the quote's depth and the sale claim.
Input extension (named divergence): the frozen settlement calendar ends with 2026 — the source refused every sale
past it; `settlement_terms` keeps the vendored function wherever it covers the sale and otherwise applies the
table's own rule (NYSE rule holidays + Columbus / Veterans Day), which reproduces the 2022-2026 table exactly."""
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_FLOOR, Decimal

from .. import calendar as dcal
from . import r19_source as RS

UTC = timezone.utc
ZERO = Decimal(0)
EQUITY = ("equity", "US_EQUITY_ETF", "US_EQUITY", "stock")


def dec(x):
    return Decimal(str(x))


def fresh():
    return {"unsettled": [], "orders": {}, "used": {}}


def order_id(book_id, cfg, signal_id, symbol, side):
    m = RS.vendored()["r19_core"]
    return m.digest([m.VERSION, book_id, cfg["version"], cfg["epoch"], signal_id, symbol, side])


def release(model, now):
    """_housekeeping: settlement claims mature at their release clock -> (released amount)."""
    keep, done = [], ZERO
    for u in model["unsettled"]:
        if float(u["release_at"]) <= now:
            done += dec(u["amount"])
        else:
            keep.append(u)
    model["unsettled"] = keep
    return done


def unsettled(model):
    return sum((dec(u["amount"]) for u in model["unsettled"]), ZERO)


def cancel(model, signal_ids):
    out = []
    for oid, o in model["orders"].items():
        if o["signal_id"] in signal_ids and o["status"] in ("pending", "partial"):
            o["status"] = "cancelled_expired"
            out.append(oid)
    return out


def _rule_nonsettlement(day):
    """the frozen DTCC table's own rule (it reproduces NONSETTLEMENT_MONTH_DAYS 2022-2026 exactly; tested): the
    NYSE rule holidays as the exchange observes them, plus the settlement-only Columbus Day and Veterans Day
    (a Sunday Veterans Day moves to Monday; a Saturday one is not moved)."""
    if day in dcal.holidays(day.year) or day == dcal._nth(day.year, 10, 0, 2):
        return True
    vet = date(day.year, 11, 11)
    vet += timedelta(days=1) if vet.weekday() == 6 else timedelta(0)
    return day == vet and vet.weekday() < 5


def settles(day):
    sc = RS.vendored_settlement()
    if day.year in sc.SUPPORTED_YEARS:
        return sc.is_settlement_day(day)
    return day.weekday() < 5 and not _rule_nonsettlement(day)


def settlement_terms(clock):
    """the vendored settlement_terms where its frozen 2022-2026 DTCC calendar covers the sale; past that coverage
    (where the source refused every sale) the same T+1 maturity and first-XNYS-open release on the table's rule
    (named divergence: an input the frozen source does not carry, derived from the rule it encodes)."""
    sc = RS.vendored_settlement()
    try:
        return sc.settlement_terms(clock)
    except sc.SettlementCalendarError:
        pass
    cal = RS.DeskXNYS()
    trade_day = clock.astimezone(sc.NY).date()
    if not cal.is_session(trade_day.isoformat()):
        raise sc.SettlementCalendarError("Observed sale has no covered native equity trade session")
    cycle = 2 if trade_day < date(2024, 5, 28) else 1
    remaining, day = cycle, trade_day
    for _ in range(16):
        day += timedelta(days=1)
        if settles(day):
            remaining -= 1
            if not remaining:
                break
    else:
        raise sc.SettlementCalendarError("No supported economic maturity found")
    release_session = cal.date_to_session(day.isoformat(), direction="next")
    release = cal.session_open(release_session).to_pydatetime().astimezone(UTC)
    return {"policy_version": sc.POLICY_VERSION + "+DESK_RULE_EXTENSION", "calendar_sha256": sc.CALENDAR_SHA256,
            "trade_date": trade_day.isoformat(), "settlement_cycle_business_days": cycle,
            "economic_settlement_date": day.isoformat(), "cash_release_policy": sc.CASH_RELEASE_POLICY,
            "cash_release_at": release.isoformat(), "cash_release_session": str(release_session.date()),
            "actual_broker_settlement_or_cash_observed": False}


def fee_rule(cfg, symbol, price):
    declared = dec(cfg.get("fee_bps", cfg.get("cost_bps_per_side", 15)))
    if cfg.get("module") == "backend.r19_tensor":
        declared = Decimal(10) if symbol == "QQQ" else Decimal(30 if price < 5 else 15 if price < 20 else 10)
    return declared


def execute(model, book_id, cfg, intent, snapshot, owned, cash, nav, held_value, actual, owned_contract=None):
    """one intent -> (fill dict | None, reason). cash: settled cash; owned: whole units held (owned_contract: the
    held position's native contract id); actual: epoch of the acknowledgement. On a fill the model's order / depth
    records are updated (the caller books cash / units)."""
    m = RS.vendored()["r19_core"]
    sym = intent["symbol"]
    if not isinstance(intent.get("signal_id"), str) or not intent["signal_id"] or not isinstance(sym, str) or not sym:
        return None, "Stable signal_id and native symbol required"
    if intent.get("expires_at") and actual >= m.stamp(intent["expires_at"]).timestamp():
        return None, "Intent entry/exit window expired"
    if "target_quantity" in intent:
        target = dec(intent["target_quantity"])
        if target < 0:
            return None, "Negative native target is not a long holding"
        side = "buy" if target > owned else "sell"
        desired = abs(target - owned)
    else:
        side, desired = intent.get("side"), dec(intent.get("quantity", 0))
    if side not in ("buy", "sell") or desired < 0:
        return None, "Invalid long-only execution side/quantity"
    if desired == 0:
        return None, "target_satisfied"
    q = snapshot.get("quotes", {}).get(sym)
    if not q:
        return None, f"missing_quote:{sym}"
    at, market, received = m.stamp(snapshot["asof"]), m.stamp(q["market_at"]), m.stamp(q["received_at"])
    age = float(cfg.get("max_quote_age_seconds", cfg.get("quote_max_age_seconds", 2)))
    if market > received or received > at or (at - market).total_seconds() > age:
        return None, f"quote_clock_or_staleness:{sym}"
    if q.get("currency") != cfg["currency"] or not q.get("contract_id"):
        return None, f"quote_native_identity:{sym}"
    if q.get("symbol", sym) != sym:
        return None, f"quote_symbol_mismatch:{sym}"
    if q.get("indicative") or q.get("feed") in (None, "indicative"):
        return None, f"nonexecutable_indicative_quote:{sym}"
    bid, ask = dec(q["bid"]), dec(q["ask"])
    if bid <= 0 or ask < bid:
        return None, f"invalid_quote:{sym}"
    if dec(q.get("bid_size", 0)) < 0 or dec(q.get("ask_size", 0)) < 0:
        return None, "Negative quote size"
    if q["asset_class"] in EQUITY and not snapshot.get("calendar", {}).get("is_open"):
        return None, "Equity market closed"
    if actual < at.timestamp() or actual - market.timestamp() > age:
        return None, "Actual execution clock exceeds fresh quote; snapshot replay forbidden"
    if owned > 0 and q["contract_id"] != owned_contract:
        return None, "Owned contract mismatch"
    if side == "buy" and not q.get("actions_verified", q["asset_class"] == "crypto"):
        return None, "Native action census unavailable"
    if side == "buy" and q["asset_class"] in EQUITY and (q.get("tradable") is not True or q.get("status") != "active"):
        return None, "Native equity contract not currently active and tradable"
    if q["asset_class"] in EQUITY:
        cal = snapshot.get("calendar", {})
        if not cal.get("open") or not cal.get("close") or \
                not m.stamp(cal["open"]).timestamp() <= actual < m.stamp(cal["close"]).timestamp():
            return None, "Actual execution outside regular native equity session"
    if q["asset_class"] == "crypto":                    # the R19 crypto books (r19_core.py Ledger._execute)
        if q.get("market_kind") != "spot":
            return None, "Native crypto execution requires spot identity"
        if not q.get("contract_received_at") or not q.get("contract_valid_until") or not \
                m.stamp(q["contract_received_at"]).timestamp() <= actual <= m.stamp(q["contract_valid_until"]).timestamp():
            return None, "Native crypto contract metadata expired at actual execution"
    is_equity = q["asset_class"] in EQUITY
    step = dec(q.get("step_size", 1 if is_equity else "0"))
    if step <= 0 or (is_equity and step != 1):
        return None, "Unqualified native lot step"
    if desired % step:
        return None, "Intent quantity does not match native units"
    oid = order_id(book_id, cfg, intent["signal_id"], sym, side)
    old = model["orders"].get(oid)
    if old:
        if ("target_quantity" in intent) != ("target" in old) or \
                ("target_quantity" in intent and dec(intent["target_quantity"]) != dec(old["target"])):
            return None, "Stable order target changed"
        if old["status"] == "filled" or old["status"].startswith("cancelled"):
            return None, "idempotent"
        desired = min(desired, dec(old["requested"]) - dec(old["filled"]))
    key = m.Ledger._depth_key(sym, q)
    used = dec(model["used"].get(key + ":" + side, 0))
    displayed = max(ZERO, dec(q["ask_size"] if side == "buy" else q["bid_size"]) - used)
    quantity = (min(desired, displayed) / step).to_integral_value(rounding=ROUND_FLOOR) * step
    if side == "sell":
        quantity = min(quantity, owned)
    price = ask if side == "buy" else bid
    declared = fee_rule(cfg, sym, price)
    fee_bps = dec(intent.get("metadata", {}).get("fee_bps", declared))
    if fee_bps != declared:
        return None, "Intent fee schedule differs from frozen native rule"
    fee_rate = fee_bps / 10000
    if fee_rate < 0 or fee_rate > Decimal(".05"):
        return None, "Invalid execution fee rule"
    if side == "buy":
        if nav is None:
            return None, "NAV withheld; cannot size new risk"
        if nav <= 0:
            return None, "Nonpositive equity"
        gross_target = min(Decimal(1), dec(cfg.get("margin", {}).get("gross_target", cfg.get("gross_target", 1))))
        gross_unit = gross_target * price + (1 - gross_target) * bid + gross_target * price * fee_rate
        capacity = max(ZERO, gross_target * nav - held_value)
        affordable = max(ZERO, cash)
        quantity = min(quantity, (affordable / (price * (1 + fee_rate)) / step).to_integral_value(rounding=ROUND_FLOOR) * step,
                       (capacity / gross_unit / step).to_integral_value(rounding=ROUND_FLOOR) * step)
    if quantity <= 0:                                   # a refusal rolls back to the savepoint: no order row
        return None, "No executable funded native quantity"
    maximum = dec(q.get("maximum_qty", q.get("max_qty", quantity)))
    minimum = dec(q.get("minimum_qty", q.get("min_qty", 0)))
    min_notional = dec(q.get("min_notional", 0))
    if maximum <= 0 or minimum < 0 or min_notional < 0 or minimum > maximum:
        return None, "Invalid native quantity or notional bounds"
    quantity = (min(quantity, maximum) / step).to_integral_value(rounding=ROUND_FLOOR) * step
    if quantity <= 0:
        return None, "No positive native quantity after lot caps"
    if quantity < minimum:
        return None, "Native minimum quantity"
    notional = quantity * price
    if notional < min_notional:
        return None, "Native minimum notional"
    fee = notional * fee_rate
    terms = None
    if side == "sell" and is_equity:
        try:
            terms = settlement_terms(datetime.fromtimestamp(actual, tz=UTC))     # fail before any mutation
        except ValueError as exc:
            return None, str(exc)
    if not old:
        old = model["orders"][oid] = {"signal_id": intent["signal_id"], "symbol": sym, "side": side,
                                      "requested": str(desired), "filled": "0", "status": "pending",
                                      **({"target": str(intent["target_quantity"])} if "target_quantity" in intent else {})}
    filled = dec(old["filled"]) + quantity
    old["filled"] = str(filled)
    old["status"] = "filled" if filled >= dec(old["requested"]) else "partial"
    model["used"][key + ":" + side] = str(used + quantity)
    out = {"symbol": sym, "side": side, "quantity": quantity, "price": price, "fee": fee, "order_id": oid,
           "signal_id": intent["signal_id"], "contract_id": q["contract_id"], "depth_key": key + ":" + side}
    if terms is not None:
        out["release_at"] = m.stamp(terms["cash_release_at"]).timestamp()
        model["unsettled"].append({"amount": str(notional - fee), "release_at": out["release_at"], "order": oid,
                                   "qty": str(quantity)})
    return out, "filled"


def unfill(model, fill, short):
    """the desk's venue left `short` units of a decided fill unexecuted (its child lapsed): the order's remainder
    reopens for a later quote, the displayed depth it claimed is returned, a sale's settlement claim shrinks to
    the units actually sold. (The ledger's local fill could not fall short; this is the acknowledgement seam.)"""
    short = dec(short)
    if short <= 0:
        return
    o = model["orders"].get(fill["order_id"])
    if o is not None:
        o["filled"] = str(max(ZERO, dec(o["filled"]) - short))
        if not o["status"].startswith("cancelled"):
            o["status"] = "partial" if dec(o["filled"]) > 0 else "pending"
    k = fill.get("depth_key")
    if k in model["used"]:
        model["used"][k] = str(max(ZERO, dec(model["used"][k]) - short))
    if fill["side"] == "sell":
        for u in reversed(model["unsettled"]):
            if u.get("order") == fill["order_id"] and float(u["release_at"]) == float(fill.get("release_at", -1)):
                q = dec(u["qty"])
                left = max(ZERO, q - short)
                u["amount"] = str(dec(u["amount"]) * left / q) if q > 0 else "0"
                u["qty"] = str(left)
                break
        model["unsettled"] = [u for u in model["unsettled"] if dec(u["amount"]) > 0]


def trim(model, keep_orders=500, keep_used=400):
    for k in ("orders", "used"):
        d = model[k]
        lim = keep_orders if k == "orders" else keep_used
        if len(d) > lim:
            for kk in list(d)[:len(d) - lim]:
                d.pop(kk)
    return model
