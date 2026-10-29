"""FREE_OPT_PARITY — lean-desk port (Wave D, Decision #119 family), restored on the master desk with its economic
action.

master-desk: the Aurelia source desk's FREE_OPT_PARITY_V1 descendant (preserves OPT_PARITY_MONITOR; Agentic-Trading-Desk
aurelia-paper-desk @1720157f768e). Its free-paper row is the source's own, unchanged: desk/free_options.py contracts()
and evaluate() (vendored as desk/vendor/aurelia/free_options.py) answer MODEL_TEST_ONLY on every pass ("Indicative
conversion is recorded and is not an economic order."), recorded as the monitor observation. The economic action is
the one the same source tree defines for this parent and left unauthorized — desk/research_descendants.py
FWD_RESEARCH_PARITY_V1 ("Synchronized European call, put, and carry package when residual after cost is positive.
Exit: Residual at or below zero, or the shared expiry. Stop: Package residual moves against entry by the entry
residual. Size: One package, at most 10% of the sleeve budget.") and desk/forward_review.py FWD_PARITY_V1 ("Buy the
cheap synthetic and sell the rich one only when the source residual after cost is positive ... Exit: Residual at or
below zero, or five sessions.") — on the residual arithmetic of the parent monitor (backend/r19_options.py
monitor_diagnostic, parity: low = K + (C_bid - P_ask)/df, high = K + (C_ask - P_bid)/df against the carry's bid and
ask, the crossing residual after costs).

  quotes ... the SPY chain fetched for the decision (receipt <= 20 s) and the underlying's bid / ask: on CBOE's
             delayed chain both come from one snapshot (one market time); on Alpaca's indicative chain each contract
             carries its own quote time and the carry is the live equity quote. Every leg and the carry must pass the
             free descendants' freshness rule at the decision (source <= 90 s, receipt <= 30 s) and lie within 30 s
             of each other (their package skew) — the synchronization the parity residual needs.
  carry .... SPY shares financed at the 3-month T-bill rate (FRED DTB3, desk/feedlib/tbill.py): df = exp(-r x days /
             365); only expiries before SPY's next ex-dividend date (the third Friday of March, June, September,
             December) are admitted, so no dividend enters the carry and no early call exercise is due.
  residual . per share, for each same-expiry same-strike call / put pair with both quotes two-sided, 1-45 DTE, strike
             within 5% of the spot: conversion (sell the synthetic forward, buy the carry) = (C_bid - P_ask) -
             (S_ask - K x df) - costs — the source's low - carry_ask, discounted; reversal (buy the synthetic, sell
             the carry) = (S_bid - K) - (C_ask - P_bid) - costs — the American bound C - P >= S - K (the contracts
             are American: the source's "American_exercise_dividend_bounds_required"); costs = the option fee on both
             legs, in and out ($0.03 a contract a fill).
  entry .... no package held, the session open: the pair with the largest positive residual -> one package: 100 SPY
             shares (bought for a conversion, sold short for a reversal), 1 put and 1 call (put bought / call sold,
             or the reverse), each a limit at its side of the snapshot — on CBOE's snapshot all three on the
             labelled sim venue sim:options (the snapshot's own prices), on Alpaca's live quotes the desk's default
             route — only when the package's risk (its unwind cost at the snapshot's spreads: the loss if the
             residual closed at once) is within 10% of the book and the book's cash covers a conversion's debit.
  exits .... all legs together, at their side of the snapshot: the package's live residual (the same direction, same
             pair, current snapshot) at or below zero — which is also the stop (the residual has moved against the
             entry by the entry residual) — or five completed sessions; held to the shared expiry, the engine settles
             it (exercise / assignment delivers the shares against the carry). A package missing a leg closes the
             legs it holds.

Gone under the cutover doctrine: the model-test lane's refusal of an economic order (free_options: execution
model_test) and the research descendant's BLOCKED_PERMISSION; the Femto fences of the old desk's copy.
Named divergences: the instruments — SPY's American options and shares stand in for the "European call and put" and
the native index carry the source names (the desk has no synchronized European chain with a tradable carry); the
American reversal bound; the T-bill carry and the ex-dividend window; the quotes are the desk's indicative chain
(CBOE's delayed snapshot, its time the snapshot's; the source required OPRA quotes <= 10 s old); the exit is the
residual, five sessions or the expiry, whichever comes first (the two drafts named five sessions and the expiry);
"at most 10% of the sleeve budget" is read as the package's risk — its unwind cost — against the $100,000 book (a
100-share package's notional, ~$76,000, is most of the book; its locked payoff risks only the spreads), and the
book's cash must cover a conversion's debit; on CBOE's delayed snapshot the carry leg
trades on sim:options at the snapshot's underlying quote, commission-free (config fees_bps sim:options 0), never at a
live quote against delayed option prices; the legs' synchronization is the free descendants' 30 s skew (the parent
monitor asked OPRA quotes within 2 s).

Inputs via context.extra:
  "quote"         the indicative probe (evaluate() reads it; the parity row ignores it)
  "market_open"   the clock's is_open
  "parity_chain"  {"rows", "spot_bid", "spot_ask", "spot_t", "spot_received_at", "received_at", "venue"}: the SPY
                  chain for the decision, the underlying's quote and the package's venue ("sim:options" on CBOE's
                  snapshot, "" — the default route — on Alpaca's)
  "rate"          {"rate" (percent), "date"}: DTB3 (feed tbill)
  "legs"          the sleeve's option positions {OCC: {"qty","avg","opened_at","meta"}}
  "shares"        {SYM: shares held}
  "cash"          the book's cash (a conversion's debit is paid from it)
  "working"       the sleeve's live orders [{"inst","action","side","signal_key"}]
  "meta"          {"package": the open package's record}
  "decided_at"    the chain's receipt when later than the pass's clock (free_opt_core.moment_of)
"""
import math
from datetime import date, datetime, timedelta, timezone

from .compat import BaseSleeve, Intent, SleeveConfig
from . import free_opt_core as C
from ...vendor.aurelia.quote_freshness import assess

SPEC_ID = "FREE_OPT_PARITY_V1"
UNDERLYING = "SPY"
VENUE = "sim:options"
MULTIPLIER = 100
BUDGET_FRACTION = 0.10
HOLD_SESSIONS = 5
DTE = (1, 45)
MONEYNESS = 0.05
OPTION_FEE = 0.03
COSTS = 4 * OPTION_FEE / MULTIPLIER          # both option legs, in and out, per share

CONFIG = SleeveConfig(
    sleeve_id="free_opt_parity", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=None)


def parity_status(context=None):
    """the source's row for this descendant (evaluate(); MODEL_TEST_ONLY on every pass)."""
    from .compat import Context
    row = C.evaluate_row(SPEC_ID, context or Context(now=0.0, session="1970-01-01"))
    return {"id": row["id"], "preserves": row["preserves"], "status": row["status"],
            "broker_order": row["broker_order"], "economic_forward": row["economic_forward"], "reason": row["reason"]}


def next_ex_dividend(day):
    """SPY's next ex-dividend date on or after `day`: the third Friday of March, June, September or December."""
    d = date.fromisoformat(str(day)[:10])
    for y in (d.year, d.year + 1):
        for m in (3, 6, 9, 12):
            first = date(y, m, 1)
            third = first + timedelta(days=(4 - first.weekday()) % 7 + 14)
            if third >= d:
                return third
    raise ValueError(day)


def _two_sided(r):
    try:
        return float(r.get("bid") or 0) > 0 and float(r.get("ask") or 0) >= float(r.get("bid") or 0)
    except (TypeError, ValueError):
        return False


def residuals(rows, spot_bid, spot_ask, session, rate):
    """[{"expiration","strike","call","put","df","conversion","reversal"}] for the admissible pairs (residuals per
    share, after costs)."""
    today = date.fromisoformat(session)
    last = next_ex_dividend(session) - timedelta(days=1)       # an expiry before the ex-date's eve
    mid = (float(spot_bid) + float(spot_ask)) / 2
    by = {}
    for r in rows or ():
        if r.get("underlying", UNDERLYING) != UNDERLYING or not _two_sided(r):
            continue
        e = date.fromisoformat(r["expiration"])
        if not (DTE[0] <= (e - today).days <= DTE[1]) or e >= last or abs(r["strike"] / mid - 1) > MONEYNESS:
            continue
        by.setdefault((r["expiration"], r["strike"]), {})[r["type"]] = r
    out = []
    for (e, k), legs in sorted(by.items()):
        c, p = legs.get("call"), legs.get("put")
        if not (c and p):
            continue
        df = math.exp(-float(rate) / 100.0 * (date.fromisoformat(e) - today).days / 365.0)
        conv = (float(c["bid"]) - float(p["ask"])) - (float(spot_ask) - k * df) - COSTS
        rev = (float(spot_bid) - k) - (float(c["ask"]) - float(p["bid"])) - COSTS
        out.append({"expiration": e, "strike": k, "call": c, "put": p, "df": df, "conversion": conv, "reversal": rev})
    return out


def _iso(ts):
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()


def _snapshot_ok(snap, moment):
    """the underlying's quote of the snapshot passes the freshness rule; None, or the block."""
    if not snap or not snap.get("rows") or not snap.get("spot_bid") or not snap.get("spot_ask") \
            or not snap.get("spot_t"):
        return "the SPY chain snapshot (with the underlying's bid and ask) was not fetched"
    m = datetime.fromtimestamp(float(moment), tz=timezone.utc)
    return assess(m, _iso(snap["spot_t"]), _iso(snap.get("spot_received_at") or snap["received_at"]))["block"]


def synchronized(x, snap, moment):
    """a candidate's legs and carry pass the freshness rule at the decision and lie within 30 s of each other (the
    free descendants' package skew); None, or the block."""
    m = datetime.fromtimestamp(float(moment), tz=timezone.utc)
    stamps = [float(snap["spot_t"])]
    for leg in (x["call"], x["put"]):
        if leg.get("t") is None:
            return "a leg has no quote time"
        block = assess(m, _iso(leg["t"]), _iso(snap["received_at"]))["block"]
        if block:
            return block
        stamps.append(float(leg["t"]))
    return "cross-leg timestamp skew exceeds 30 seconds" if max(stamps) - min(stamps) > 30 else None


def _sessions(opened, now):
    from ... import calendar as cal
    return cal.trading_days_between(float(opened), float(now))


def _intent(kind, sym, side, qty, px, key, why, venue, occ=None, meta=None):
    """one leg: an option (occ) or the SPY carry, a limit at its side of the snapshot, on the package's venue."""
    order = {"type": "limit", "limit_price": round(float(px), 4)}
    venue = venue or None
    if occ:
        intent = ("buy_to_open" if side == "buy" else "sell_to_open") if kind == "enter" else \
            ("buy_to_close" if side == "buy" else "sell_to_close")
        return Intent(kind, occ, qty_hint=int(qty), asset="option", venue=venue,
                      legs=({"symbol": occ, "side": side, "ratio": 1, "position_intent": intent},), order=order,
                      signal_key=key, position_meta=meta, reason=why)
    if kind == "enter":
        return Intent(kind, sym, side="long" if side == "buy" else "short", asset="equity", venue=venue, qty=float(qty),
                      price_hint=float(px), order=order, signal_key=key, position_meta=meta, reason=why)
    return Intent(kind, sym, qty=float(qty), venue=venue, price_hint=float(px), order=order, signal_key=key,
                  reason=why)


def trade(context):
    """the economic layer on one pass -> {"intents", "package" (meta.package next), "record": {"status","reason"}}."""
    extra = context.extra or {}
    pkg = dict((extra.get("meta") or {}).get("package") or {}) or None
    out = {"intents": [], "package": pkg, "record": {"status": None, "reason": None}}

    def rec(status, reason):
        out["record"] = {"status": status, "reason": reason}
        return out

    if not C.market_open(context):
        return rec("QUALIFIED/OUTSIDE WINDOW", "the equity session is closed")
    moment = C.moment_of(context).timestamp()
    snap = extra.get("parity_chain")
    block = _snapshot_ok(snap, moment)
    legs = extra.get("legs") or {}
    shares = float((extra.get("shares") or {}).get(UNDERLYING) or 0.0)
    working = [w for w in extra.get("working") or [] if w.get("action") in ("enter", "exit", "target")]
    quotes = {r["symbol"]: r for r in (snap or {}).get("rows") or ()}
    if pkg:
        if working:
            return rec("working", "the package's orders are working")
        held = {o: float((legs.get(o) or {}).get("qty") or 0.0) for o in (pkg["call"], pkg["put"])}
        held = {o: q for o, q in held.items() if q}
        if not held and not shares:
            out["package"] = None                              # flat: the package is done (closed or settled)
            return rec("closed", "package %s is flat" % pkg["id"])
        complete = len(held) == 2 and shares
        why = None
        if not complete:
            why = "a failed leg closes the filled legs"
        elif _sessions(pkg["opened_at"], moment) >= HOLD_SESSIONS:
            why = "five sessions"
        elif not block:
            live = next((x for x in residuals(snap["rows"], snap["spot_bid"], snap["spot_ask"], context.session,
                                              pkg["rate"])
                         if x["expiration"] == pkg["expiration"] and x["strike"] == pkg["strike"]), None)
            if live is not None and synchronized(live, snap, moment) is None and live[pkg["direction"]] <= 0:
                why = "the residual is at or below zero (%.4f; entry %.4f): exit, and the stop" % (
                    live[pkg["direction"]], pkg["entry_residual"])
        if not why:
            return rec("open", "package %s held" % pkg["id"])
        if block:
            return rec("BLOCKED_INPUT", "exit due (%s) but the snapshot is not usable: %s" % (why, block))
        key, venue = "%s:exit:%d" % (pkg["id"], int(moment)), pkg.get("venue", VENUE)
        for o, q in held.items():
            r = quotes.get(o)
            if r is None or not _two_sided(r):
                return rec("BLOCKED_INPUT", "exit due (%s) but %s has no two-sided quote" % (why, o))
            side = "sell" if q > 0 else "buy"
            out["intents"].append(_intent("exit", UNDERLYING, side, abs(q), r["bid"] if side == "sell" else r["ask"],
                                          "%s:%s" % (key, o), "%s package %s: %s" % (SPEC_ID, pkg["id"], why), venue,
                                          occ=o))
        if shares:
            px = snap["spot_bid"] if shares > 0 else snap["spot_ask"]
            out["intents"].append(_intent("exit", UNDERLYING, "sell" if shares > 0 else "buy", abs(shares), px,
                                          "%s:%s" % (key, UNDERLYING), "%s package %s: %s" % (SPEC_ID, pkg["id"], why),
                                          venue))
        return rec("exit_submitted", why)
    if block:
        return rec("BLOCKED_INPUT", block)
    rate = (extra.get("rate") or {}).get("rate")
    if rate is None:
        return rec("BLOCKED_INPUT", "no discount rate (DTB3) is loaded")
    cands = residuals(snap["rows"], snap["spot_bid"], snap["spot_ask"], context.session, rate)
    if not cands:
        return rec("BLOCKED_INPUT", "no admissible same-strike call / put pair before the ex-dividend date")
    cands = [x for x in cands if synchronized(x, snap, moment) is None]
    if not cands:
        return rec("BLOCKED_INPUT", "no pair's quotes are fresh and synchronized with the carry")
    best = max(cands, key=lambda x: (max(x["conversion"], x["reversal"]), x["expiration"], -x["strike"]))
    direction = "conversion" if best["conversion"] >= best["reversal"] else "reversal"
    res = best[direction]
    if res <= 0:
        return rec("QUALIFIED/AWAITING SIGNAL", "no positive residual after cost (best %.4f per share)" % res)
    c, p, k, e = best["call"], best["put"], best["strike"], best["expiration"]
    risk = MULTIPLIER * sum(float(x["ask"]) - float(x["bid"]) for x in (c, p)) + \
        MULTIPLIER * (float(snap["spot_ask"]) - float(snap["spot_bid"]))   # the package's unwind cost: its loss if
    if risk > BUDGET_FRACTION * float(context.equity or 0):                # the residual closes at once
        return rec("BLOCKED_INPUT", "the package's %.2f risk exceeds 10%% of the sleeve budget" % risk)
    debit = MULTIPLIER * (float(snap["spot_ask"]) + float(p["ask"]) - float(c["bid"])) if direction == "conversion" \
        else 0.0
    if debit > float(extra.get("cash") or 0):
        return rec("BLOCKED_INPUT", "the book's cash does not cover the package's %.2f debit" % debit)
    pid = "parity-%s-%d" % (context.session, int(moment) % 86400)
    why = "%s %s K %g: residual %.4f per share after cost (df %.6f, rate %s%%)" % (direction, e, k, res, best["df"],
                                                                                    rate)
    meta = {"package": pid, "spec": SPEC_ID, "direction": direction}
    v = snap.get("venue", VENUE)
    if direction == "conversion":
        out["intents"] += [_intent("enter", UNDERLYING, "buy", MULTIPLIER, snap["spot_ask"], pid + ":carry", why, v,
                                   meta=dict(meta, leg="carry")),
                           _intent("enter", UNDERLYING, "buy", 1, p["ask"], pid + ":put", why, v, occ=p["symbol"],
                                   meta=dict(meta, leg="put")),
                           _intent("enter", UNDERLYING, "sell", 1, c["bid"], pid + ":call", why, v, occ=c["symbol"],
                                   meta=dict(meta, leg="call"))]
    else:
        out["intents"] += [_intent("enter", UNDERLYING, "sell", MULTIPLIER, snap["spot_bid"], pid + ":carry", why, v,
                                   meta=dict(meta, leg="carry")),
                           _intent("enter", UNDERLYING, "sell", 1, p["bid"], pid + ":put", why, v, occ=p["symbol"],
                                   meta=dict(meta, leg="put")),
                           _intent("enter", UNDERLYING, "buy", 1, c["ask"], pid + ":call", why, v, occ=c["symbol"],
                                   meta=dict(meta, leg="call"))]
    out["package"] = {"id": pid, "direction": direction, "expiration": e, "strike": k, "call": c["symbol"],
                      "put": p["symbol"], "entry_residual": round(res, 6), "rate": rate, "opened_at": moment,
                      "session": context.session, "venue": v}
    return rec("sent", why)


def decide(bars, context):
    """the source's row (MODEL_TEST_ONLY, recorded) and the economic layer's intents (trade())."""
    row = C.evaluate_row(SPEC_ID, context)
    econ = trade(context)
    return {"row": {"status": row["status"], "reason": row.get("reason")}, "intents": econ["intents"],
            "package": econ["package"], "economic": econ["record"]}


def _pass(bars, context):
    extra = context.extra
    memo = extra.get("_free_opt_pass") if isinstance(extra, dict) else None
    if memo is None or memo[0] is not context:           # one decision per pass's context (identity, not id())
        memo = (context, decide(bars, context))
        if isinstance(extra, dict):
            extra["_free_opt_pass"] = memo
    return memo[1]


class FreeOptParity(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        return list(_pass(bars, context)["intents"])


def signal(bars, slice_state, context):
    return FreeOptParity().signal(bars, slice_state, context)


def next_meta(bars, slice_state, context, intents=()):
    meta = dict((context.extra or {}).get("meta") or {})
    pkg = _pass(bars, context)["package"]
    if pkg:
        meta["package"] = pkg
    else:
        meta.pop("package", None)
    return meta


def monitor(mod, bars, context):
    r = parity_status(context)
    e = _pass(bars, context).get("economic") or {}
    return [("SPY", "%s %s: %s [economic: %s]" % (SPEC_ID, r["status"], r["reason"], e.get("status")),
             {"status": r["status"], "economic": e.get("status"), "detail": e.get("reason")})]
