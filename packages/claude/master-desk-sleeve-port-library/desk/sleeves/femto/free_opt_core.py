"""Free-paper option descendants — the shared execution (master-desk; no Femto-lean source).

The Aurelia source desk's free_options.execute() and option_packages.submit_package() / manage_exits() as decisions
on a sleeve's own book (Agentic-Trading-Desk aurelia-paper-desk @1720157f768e). The rules they act on are the
source's text, vendored: desk/vendor/aurelia/free_options.py (contracts, evaluate, package_skew, _fresh_legs,
_local_ack) and desk/vendor/aurelia/quote_freshness.py.

  single ... a row's order goes out once per session (the client id free-opt-<ID>-<UTC date>, kept in meta.sent) while
             the market is open and its quote passes the freshness rule again at the send; outside the session a
             working entry of the day is withdrawn.
  package .. a package goes out once (its own client id, kept in meta.packages): not a model test, deliverable, all
             its required legs, every leg fresh (90 s source / 30 s receipt / 2 s future tolerance) and within 30 s
             of the next, its max loss inside its risk cap (risk_cap, else the max loss) and the $100,000 pool of open
             reservations; a broker_mleg package is one multi-leg order at the price the source's journal booked
             (its legs' asks paid / bids received); any other execution one order per leg at that leg's price, sent
             only when every leg has its side of the market (the source's local fill rejected the package at the
             first leg without it, after buying the legs before it at the ask and selling them back at the bid).
  exits .... an open package closes once its exit_at has passed while the market is open (manage_exits); the legs of
             a package whose other leg never filled close (a failed leg closes the filled leg)."""
from datetime import datetime, timezone

from .compat import Intent
from ...vendor.aurelia import free_options as FO
from ...vendor.aurelia.quote_freshness import assess

POOL_USD = 100_000.0                    # option_packages.submit_package(pool=100_000)
OPEN = ("open", "exit_waiting_on_quote")


def moment_of(context):
    """the decision moment: the pass's clock, or — when the pass fetched its option chain later than its start (a
    pass runs its sleeves one after another) — that chain's receipt (context.extra "decided_at"): the source decided
    on the cycle's clock with the snapshot fetched at once, its receipt stamped at that moment."""
    at = (context.extra or {}).get("decided_at") if isinstance(context.extra, dict) else None
    now = max(float(context.now), float(at)) if at else float(context.now)
    return datetime.fromtimestamp(now, tz=timezone.utc)


def market_open(context):
    """the clock's is_open (the source's run(market_open=...)); evaluate()'s own default when not supplied."""
    v = (context.extra or {}).get("market_open")
    return True if v is None else bool(v)


def evaluate_row(spec_id, context):
    """free_options.evaluate() on this pass's inputs: the sleeve's own row."""
    extra = context.extra or {}
    rows = FO.evaluate(moment_of(context), extra.get("quote"), extra.get("underlying_return"),
                       float(extra.get("cash") or 0), list(extra.get("events") or []), package=extra.get("package"),
                       market_open=market_open(context))
    return next(r for r in rows if r["id"] == spec_id)


def client_id(spec_id, moment):
    return f"free-opt-{spec_id}-{moment.date().isoformat()}"[:48]


def single(row, context, sent, pending=()):
    """execute() for a single-order row -> {"status", "reason", "order" (to send) | None, "cancel": key | None}."""
    order = row.get("order")
    out = {"status": row["status"], "reason": row.get("reason"), "order": None, "cancel": None}
    if not order or row.get("execution") == "model_test" or order.get("package"):
        return out
    moment = moment_of(context)
    client = client_id(row["id"], moment)
    if not market_open(context):
        if any(o.get("key") == client for o in pending or ()):
            out.update(status="canceled", cancel=client,
                       reason="Entry cancel requested because the session is closed. A fill during the cancel is kept.")
        else:
            out.update(status="QUALIFIED/OUTSIDE WINDOW",
                       reason="The equity session is closed, so the indicative decision is not sent.")
        return out
    checked = assess(moment, order.get("source_at"), order.get("received_at"))
    if order.get("symbol") and checked["block"]:
        out.update(status="BLOCKED_INPUT", reason=checked["block"])
        return out
    if client in (sent or {}):
        out.update(status="duplicate")
        return out
    out.update(status="sent", order=dict(order, client_order_id=client))
    return out


RELEASED = ("closed", "orphan_recovered", "rejected")


def reservations(packages):
    """open risk reservations: packages that reserved a max loss and are still open (a package that closed, or
    never opened, releases its reservation)."""
    return [(p.get("book_id"), float(p.get("amount") or 0.0)) for p in (packages or {}).values()
            if float(p.get("amount") or 0.0) > 0 and p.get("status") not in RELEASED]


def package(spec, context, packages):
    """submit_package()'s decision -> {"status", "reason", "record" (to keep in meta.packages) | None,
    "send": "mleg" | "legs" | None, "legs", "qty", "net"}."""
    moment = moment_of(context)
    client = str((spec or {}).get("client_order_id") or "")
    out = {"status": None, "reason": None, "record": None, "send": None, "legs": [], "qty": None, "net": None,
           "client": client}
    if not client:
        out.update(status="invalid", reason="client_order_id is required")
        return out
    if client in (packages or {}):
        out.update(status="duplicate")
        return out
    mode = spec.get("execution") or "local"
    legs = [dict(leg) for leg in spec.get("legs") or []]
    required = int(spec.get("legs_required") or len(legs) or 0)
    rec = {"status": None, "at": float(context.now), "exit_at": spec.get("exit_at"), "execution": mode,
           "shape": spec.get("shape"), "book_id": str(spec.get("book_id") or client), "amount": 0.0,
           "legs": [{"symbol": l.get("symbol"), "side": l.get("side"), "quantity": l.get("quantity"),
                     "underlying": l.get("underlying")} for l in legs]}
    out["record"] = rec

    def done(status, reason=None):
        rec["status"] = status
        out.update(status=status, reason=reason)
        return out

    if mode == "model_test":
        return done("MODEL_TEST_ONLY")
    if spec.get("deliverable_ok") is False:
        return done("BLOCKED_INPUT", spec.get("blocker") or "unsupported contract")
    if required > 1 and len(legs) < required:
        return done("BLOCKED_INPUT", f"{spec.get('shape')} needs {required} legs; a single leg was not sent")
    block = FO._fresh_legs(legs, moment, mode) or FO._fresh_legs(legs, moment, mode)
    if block:
        return done("BLOCKED_INPUT", block)
    amount = float(spec.get("max_loss") or 0)
    if amount > 0:
        cap = float(spec.get("risk_cap") or amount)
        held = reservations(packages)
        if sum(a for b, a in held if b == rec["book_id"]) + amount > cap + 1e-9:
            return done("BLOCKED_INPUT", f"{rec['book_id']} would exceed its risk cap")
        if POOL_USD - sum(a for _, a in held) + 1e-9 < amount:
            return done("BLOCKED_INPUT", "shared paper cash does not cover this book")
        rec["amount"] = amount
    qty = float(legs[0].get("quantity") or 1) if legs else 1.0
    if mode == "broker_mleg":
        net = sum((1 if l["side"] == "buy" else -1) * float(l["ask"] if l["side"] == "buy" else l["bid"]) for l in legs)
        out.update(send="mleg", legs=legs, qty=qty, net=round(net, 4))
        return done("open")
    for i, leg in enumerate(legs):                    # the local fill, leg by leg
        if FO._local_ack(leg)["status"] == "rejected":
            return done("orphan_recovered" if i else "rejected", "quote is incomplete or crossed")
    out.update(send="legs", legs=legs, qty=qty)
    return done("open")


def entry_intents(spec_id, plan, underlying_of):
    """the sends of package() as intents (one multi-leg package, or one order per leg)."""
    key = "free-opt:%s:pkg:%s" % (spec_id, plan["client"])
    why = "%s package %s (%s)" % (spec_id, plan["client"], plan["record"].get("shape"))
    if plan["send"] == "mleg":
        legs = tuple({"symbol": l["symbol"], "side": l["side"], "ratio": 1,
                      "position_intent": "buy_to_open" if l["side"] == "buy" else "sell_to_open"} for l in plan["legs"])
        return [Intent("enter", underlying_of(plan["legs"][0]["symbol"]), qty_hint=int(plan["qty"]), asset="mleg",
                       legs=legs, net_price=plan["net"], signal_key=key,
                       position_meta={"package": plan["client"], "spec": spec_id},
                       reason="%s: multi-leg at its natural %.2f x%d" % (why, plan["net"], int(plan["qty"])))]
    out = []
    for l in plan["legs"]:
        px = float(l["ask"] if l["side"] == "buy" else l["bid"])
        out.append(Intent(
            "enter", underlying_of(l["symbol"]), qty_hint=int(float(l.get("quantity") or plan["qty"])), asset="option",
            legs=({"symbol": l["symbol"], "side": l["side"], "ratio": 1,
                   "position_intent": "buy_to_open" if l["side"] == "buy" else "sell_to_open"},),
            order={"type": "limit", "limit_price": round(px, 2)}, signal_key="%s:%s" % (key, l["symbol"]),
            position_meta={"package": plan["client"], "spec": spec_id},
            reason="%s: leg %s %s @%.2f" % (why, l["side"], l["symbol"], px)))
    return out


def package_exits(spec_id, context, packages, legs, pending, underlying_of):
    """manage_exits() and the failed-leg rule -> (intents, {client: new status})."""
    moment, now = moment_of(context), float(context.now)
    out, upd = [], {}
    entering = {o.get("occ") for o in pending or () if o.get("action") == "enter"}
    exiting = {o.get("occ") for o in pending or () if o.get("action") == "exit"}
    for client, p in (packages or {}).items():
        st = p.get("status")
        if st not in OPEN + ("exit_submitted",) or float(p.get("at") or 0.0) >= now:
            continue
        mine = [l["symbol"] for l in p.get("legs") or [] if l.get("symbol")]
        held = [o for o in mine if float(((legs or {}).get(o) or {}).get("qty") or 0.0)]
        if not held:
            if not any(o in entering or o in exiting for o in mine):
                upd[client] = "closed"                  # nothing filled, or everything closed: the risk is released
            continue
        if any(o in exiting for o in held):
            continue                                    # its exit is working
        why, unfilled = None, [o for o in mine if o not in held and o not in entering]
        if st == "exit_submitted":
            why = "closing again (the last exit did not fill)"
        elif unfilled:
            why = "a failed leg closes the filled leg (%s did not fill)" % ", ".join(unfilled)
        else:
            at = p.get("exit_at")
            try:
                due = bool(at) and datetime.fromisoformat(str(at)) <= moment
            except (TypeError, ValueError):
                due = False
            if due and not market_open(context):
                upd[client] = "exit_waiting_on_quote"
                continue
            if due:
                why = "exit_at %s has passed" % at
        if not why:
            continue
        upd[client] = "exit_submitted"
        key = "free-opt:%s:exit:%s" % (spec_id, client)
        unders = {underlying_of(o) for o in held}
        sides = {o: ("sell" if float(legs[o]["qty"]) > 0 else "buy") for o in held}
        if len(held) > 1 and len(unders) == 1:
            out.append(Intent("exit", underlying_of(held[0]), legs=tuple(
                {"symbol": o, "side": sides[o], "ratio": 1,
                 "position_intent": "sell_to_close" if sides[o] == "sell" else "buy_to_close"} for o in held),
                signal_key=key, reason="%s package %s: %s" % (spec_id, client, why)))
            continue
        for o in held:                                  # one leg, or legs on two underlyings: one order each
            out.append(Intent("exit", underlying_of(o), legs=(
                {"symbol": o, "side": sides[o], "ratio": 1,
                 "position_intent": "sell_to_close" if sides[o] == "sell" else "buy_to_close"},),
                signal_key="%s:%s" % (key, o), reason="%s package %s: %s" % (spec_id, client, why)))
    return out, upd


def underlying_of(occ):
    """the OCC root (SPY, QQQ, ...): a contract's underlying."""
    return str(occ)[:-15].strip() or str(occ)


def decide_packages(spec_id, context):
    """one pass of a package descendant (own-IV, release, pair): execute() -> submit_package() for an entry-ready
    row, then manage_exits() and the failed-leg rule. -> {"row", "intents", "packages" (meta.packages next)}."""
    extra = context.extra or {}
    packages = {k: dict(v) for k, v in ((extra.get("meta") or {}).get("packages") or {}).items()}
    legs, pending = extra.get("legs") or {}, extra.get("pending") or []
    row = evaluate_row(spec_id, context)
    res = {"status": row["status"], "reason": row.get("reason"), "client": None}
    intents = []
    pkg = (row.get("order") or {}).get("package")
    if pkg is not None and row.get("execution") != "model_test":
        if not market_open(context):
            res.update(status="QUALIFIED/OUTSIDE WINDOW",
                       reason="The equity session is closed, so the indicative decision is not sent.")
        else:
            plan = package(pkg, context, packages)
            res.update(status=plan["status"], reason=plan["reason"], client=plan["client"], send=plan["send"],
                       qty=plan["qty"], net=plan["net"])
            if plan["record"] is not None:
                packages[plan["client"]] = plan["record"]
            if plan["send"]:
                intents += entry_intents(spec_id, plan, underlying_of)
    exits, upd = package_exits(spec_id, context, packages, legs, pending, underlying_of)
    intents += exits
    for client, st in upd.items():
        packages[client]["status"] = st
    return {"row": res, "intents": intents, "packages": packages, "exits": sorted(upd)}


def single_intent(spec_id, sent, underlying_of, position_meta=None):
    """the single order of a row as an option intent (buy_to_open / sell_to_open at the row's limit)."""
    o = sent["order"]
    return Intent("enter", underlying_of(o["symbol"]), qty_hint=int(o.get("qty") or 1), asset="option",
                  legs=({"symbol": o["symbol"], "side": o["side"], "ratio": 1, "position_intent": o["position_intent"]},),
                  order={"type": "limit", "limit_price": round(float(o["limit_price"]), 2)},
                  signal_key=o["client_order_id"], position_meta=dict(position_meta or {}, spec=spec_id),
                  reason="%s %s 1 %s @%.2f (%s)" % (spec_id, o["position_intent"], o["symbol"],
                                                     float(o["limit_price"]), o["client_order_id"]))
