"""Aurelia book — lean-desk port (the Aurelia paper desk: its Nasdaq and gold sleeves, one account).

master-desk: the source desk's paper.py run() restored on the engine (Agentic-Trading-Desk aurelia-paper-desk
@1720157f768e) as ONE book, the way the source ran it ("One Alpaca paper account. Two sleeves"): the Nasdaq
sleeve held as QQQ + TQQQ (QQQ + 3 x TQQQ = its exposure, at most 100% of NAV), the gold sleeve as GLD on top,
idle weight >= 2% in BIL, both scaled by one factor when the capital they use would pass 1.80. aurelia_gold's
GLD rides this book: the joint capital cap and the joint margin fit make the two one portfolio.

  signal ... aurelia-gc-band20-v1 (the feed, desk/feedlib/aurelia.py): PRISM trend x volatility targets on the
             last finished session — the Nasdaq-100 total return, capped at 3x, and gold front-month futures.
  band ..... each sleeve's book keeps its exposure until the signal moves by 0.20, or goes to zero
             (session.resolve_book against the last plan's book; a first entry once the signal clears 0.20).
  posture .. the desk's stress caps on the Nasdaq book (brain/judgment.py): VIX >= 40 or a Nasdaq day <= -8%
             -> stand down (<= 0.5x); VIX >= 25 or a day <= -5% -> cautious (<= 1x); gold is never cut. The
             judged book is the one the band carries forward.
  plan ..... build_plan, verbatim: share targets on the book's equity at the finished session's closes, frozen
             for the decision date; an existing name trades only when its weight moves by 2%; buys shrunk until
             initial margin (Reg T, or Alpaca's maintenance rate when higher) fits 90% of equity, then to 95% of
             the overnight buying power; every order market-on-close.
  timing ... decided on the last finished daily bar; sent in a later session while it is open and more than
             15 minutes before the close (submit_block_reason: never a same-day bar, data at most 5 days old);
             filled at that session's official close.

Gone under the cutover doctrine: the desk kill switch. Named divergences: the book is the sleeve's own, sized on
its equity ($500,000 to start, the source's first staged plan; the source read the Alpaca account's); its
overnight buying power is Reg T on the book, 2 x equity - long market value (the source read Alpaca's); the
plan's closes are the desk's split-adjusted daily closes (the source read Yahoo's: the same official close); the
operator's stand-down notices have no channel here (the tape posture is kept); the record-only shadows (GESTALT,
N6, broken hedge, variance value) are not computed (the APEX read rides each plan); dispatch retries are the
OMS's; margin interest on the debit is charged at Alpaca's published rate.

Inputs via context.extra:
  "aurelia"  the feed {"signal_id","as_of","aurelia_ndx","aurelia_gold","vix","ndx_day","requirements",...} or
             {"error"} (fail closed: no plan, no orders)
  "meta"     {"plan": the last plan — band state and frozen targets}
  "clock"    {"is_open","timestamp","next_close"} (the desk calendar in the Alpaca clock's shape)
  "sleeve_state"
Bars: the four names' completed daily bars (the plan's closes)."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

from .compat import BaseSleeve, Intent, SleeveConfig
from ...vendor.aurelia import judgment as AJ
from ...vendor.aurelia import plan as AP
from ...vendor.aurelia import session as AS

ET = ZoneInfo("America/New_York")
SIGNAL_ID = AP.SIGNAL_ID
SYMBOLS = AP.SYMBOLS
STALE_DAYS = AS.STALE_DAYS
PLAN_KEYS = ("as_of", "data_through", "signal_id", "signal_ndx", "signal_gold", "book_ndx", "book_gold", "aurelia_ndx",
             "aurelia_gold", "apex_3x", "trend", "vol", "vix", "ndx_day", "equity", "buying_power", "prices", "weights",
             "achieved_ndx", "targets", "frozen_targets", "orders", "orders_scaled", "margin_requirement", "posture",
             "submit_block", "mode", "decided_at")

CONFIG = SleeveConfig(
    sleeve_id="aurelia_ndx", cadence_s=1800, universe=SYMBOLS,
    state_schema={"position": "dict|None"}, risk_pct=None)


def _date(t):
    return datetime.fromtimestamp(float(t), tz=ET).date().isoformat()


def completed_prices(bars, through):
    """paper.completed_prices on the desk's daily bars: each name's last close on or before `through`, refused
    when that bar is more than 5 days older."""
    out = {}
    for sym in SYMBOLS:
        rows = [b for b in (bars or {}).get(sym) or [] if _date(b["t"]) <= through]
        if not rows:
            raise RuntimeError(f"No finished bar for {sym} on or before {through}")
        last = _date(rows[-1]["t"])
        if (date.fromisoformat(through) - date.fromisoformat(last)).days > 5:
            raise RuntimeError(f"{sym} bars end {last}, decision needs {through}")
        out[sym] = float(rows[-1]["c"])
    return out


def held_of(state):
    out = {}
    for sym in SYMBOLS:
        pos = ((state or {}).get(sym) or {}).get("position") or {}
        q = int(round(float(pos.get("qty") or 0)))
        if q:
            out[sym] = q
    return out


def overnight_buying_power(equity, held, prices):
    """Reg T overnight buying power of a margin book: 2 x (equity - 50% of the long market value)."""
    lmv = sum(abs(q) * float(prices.get(s) or 0.0) for s, q in held.items())
    return max(0.0, 2.0 * float(equity) - lmv)


def decide(exp, prior, held, prices, equity, clock):
    """paper.run() from its exposures on: the band against the last plan, the posture, the frozen book,
    build_plan, the submit block and the plan mode. Returns the plan."""
    raw_ndx, raw_gold = float(exp["aurelia_ndx"]), float(exp["aurelia_gold"])
    if prior and prior.get("signal_id") == SIGNAL_ID:
        book_ndx = AS.resolve_book(raw_ndx, prior.get("book_ndx"))
        book_gold = AS.resolve_book(raw_gold, prior.get("book_gold"))
    else:
        book_ndx = AS.resolve_book(raw_ndx, 0.0)
        book_gold = AS.resolve_book(raw_gold, 0.0)
    view = AJ.posture({"vix": exp.get("vix"), "ndx_day": exp.get("ndx_day")}, [], [])
    book_ndx, book_gold = AJ.apply_posture(book_ndx, book_gold, view["level"])
    e = {k: v for k, v in exp.items() if k not in ("requirements", "status")}
    e.update(signal_ndx=raw_ndx, signal_gold=raw_gold, aurelia_ndx=book_ndx, aurelia_gold=book_gold)
    frozen = prior if AP._same_book(prior, book_ndx, book_gold, e["as_of"]) else None
    plan = AP.build_plan(float(equity), prices, held, exp=e, frozen=frozen,
                         buying_power=overnight_buying_power(equity, held, prices),
                         requirements=exp.get("requirements") or None)
    plan["book_ndx"], plan["book_gold"], plan["signal_id"] = book_ndx, book_gold, SIGNAL_ID
    plan["posture"] = {"level": view["level"], "reasons": view["reasons"]}
    plan["submit_block"] = AS.submit_block_reason(date.fromisoformat(plan["as_of"]), clock)
    prior_same = prior if prior and prior.get("as_of") == plan["as_of"] else None
    if not plan["orders"]:
        plan["mode"] = "in_band"
    elif plan["submit_block"] is None:
        plan["mode"] = "submitted"
    elif prior_same and prior_same.get("mode") == "submitted":
        plan["mode"] = "submitted"
    else:
        plan["mode"] = "staged"
    return plan


def _plan(bars, context):
    extra = context.extra or {}
    memo = extra.get("_aurelia_plan") if isinstance(extra, dict) else None
    if memo is not None and memo.get("ctx") is context:    # one plan per pass's context (identity, not id())
        return memo
    exp = extra.get("aurelia") or {}
    plan = None
    if exp.get("as_of") and exp.get("signal_id") == SIGNAL_ID and not exp.get("error"):
        try:
            prices = completed_prices(bars, exp["as_of"])
            plan = decide(exp, (extra.get("meta") or {}).get("plan"), held_of(extra.get("sleeve_state")), prices,
                          float(context.equity or 0.0), extra.get("clock") or {})
            plan["decided_at"] = float(context.now)
        except (RuntimeError, ValueError, KeyError, TypeError):
            plan = None
    memo = {"plan": plan, "ctx": context}
    if isinstance(extra, dict):
        extra["_aurelia_plan"] = memo
    return memo


class AureliaNdx(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        plan = _plan(bars, context)["plan"]
        if not plan or plan["submit_block"] is not None or float(context.equity or 0.0) <= 0:
            return []
        out = []
        for o in sorted(plan["orders"], key=lambda o: (o["side"] != "sell", o["symbol"])):
            px = round(float(plan["prices"][o["symbol"]]), 2)
            key = "aurelia-%s-%s-%s" % (plan["as_of"], o["symbol"], o["side"])
            why = ("aurelia %s %d %s (MOC): book ndx %.2fx (signal %.2fx) gold %.2fx (signal %.2fx), held as %.2fx; "
                   "posture %s; decided on %s" % (o["side"], o["qty"], o["symbol"], plan["book_ndx"],
                                                  plan["signal_ndx"], plan["book_gold"], plan["signal_gold"],
                                                  plan["achieved_ndx"], plan["posture"]["level"], plan["as_of"]))
            out.append(Intent("enter" if o["side"] == "buy" else "exit", o["symbol"], qty_hint=int(o["qty"]),
                              price_hint=px, order={"type": "market", "tif": "cls"}, signal_key=key, reason=why))
        return out


def signal(bars, slice_state, context):
    return AureliaNdx().signal(bars, slice_state, context)


def next_meta(bars, slice_state, context, intents=()):
    """meta.plan: the last plan (the band's book, the frozen targets of its decision date)."""
    meta = dict((context.extra or {}).get("meta") or {})
    plan = _plan(bars, context)["plan"]
    if plan:
        meta["plan"] = {k: plan.get(k) for k in PLAN_KEYS}
    return meta


def monitor(mod, bars, context):
    """one record per plan state: the signal, the judged book, the posture, the orders."""
    plan = _plan(bars, context)["plan"]
    if not plan:
        err = ((context.extra or {}).get("aurelia") or {}).get("error")
        return [("QQQ", "aurelia: no plan (%s)" % (err or "inputs missing"), {"error": err})]
    orders = ", ".join("%s %d %s" % (o["side"], o["qty"], o["symbol"]) for o in plan["orders"]) or "none (in band)"
    return [("QQQ", "aurelia plan %s: signal ndx %.4f gold %.4f -> book %.2f / %.2f, posture %s, apex %.2f; "
                    "orders %s; %s" % (plan["as_of"], plan["signal_ndx"], plan["signal_gold"], plan["book_ndx"],
                                       plan["book_gold"], plan["posture"]["level"], plan.get("apex_3x") or 0.0,
                                       orders, plan["submit_block"] or "sendable"),
             {"as_of": plan["as_of"], "book_ndx": plan["book_ndx"], "book_gold": plan["book_gold"],
              "mode": plan["mode"], "submit_block": plan["submit_block"]})]
