"""FWD_COINBASE_SMA200_V1 — lean-desk port (Wave D), restored on the master desk.

master-desk: the Aurelia source desk's Coinbase daily sleeve (Agentic-Trading-Desk aurelia-paper-desk @1720157f768e:
desk/forward_sleeves.py coinbase_forward() on desk/coinbase_schedule.py — vendored byte-exact as
desk/vendor/aurelia/coinbase_schedule.py — as desk/forward_cycle.py run_cycle() ran it) on its own virtual book:
BTC-USD on the desk's labelled sim venue (SPOT:COINBASE:BTC-USD) at Coinbase's live public ticker.

  decision . one per (sleeve, version coinbase-daily-v1, product, UTC day): the day's first decision stands, a
             later pass that day is a duplicate. Inside 00:00-00:05 UTC only (else "outside-window"); 200
             consecutive completed daily candles (fewer, or a gap, blocks); a native quote at most 30 s old at the
             decision (missing, stale or future blocks); the just-closed day present -> executable.
  rule ..... the SMA200 entry and exit the name promises (the owner's decision Q41, 2026-10-26: Midna's v3 design
             of 2026-10-24, which the owner approved for her desk). On an executable day SMA200 is the mean of the
             200 completed consecutive closes the gate proved, the just-closed close the last of them. Flat: a close
             above SMA200 buys 0.01 BTC; held: a close below SMA200 sells the whole held qty at the bid; equality
             trades on neither side. The source's code for this id had no sell and no SMA200 comparison: it bought
             0.01 BTC on every executable day.
  order .... a buy at the ask, the quote with ask > 0 and bid <= ask, and 0.01 x ask within 10% of the $100,000
             budget (else BLOCKED; the day's decision is spent either way); a sell at the bid, bid > 0 and bid <= ask.

Gone under the cutover doctrine: the desk kill switch (run_cycle's kill).
Named divergences: the quote's age runs from its receipt to the decision that reads it (a quote received during
this pass is 0 s old) — the source read its decision clock before fetching the quote and stamped the quote at
receipt, so every live decision failed its own "stale or future" test and was blocked; a pass without a ticker or
without candles decides nothing (the source's cycle raised on the failed call before deciding and retried on its
next loop; the desk's bar cache can serve candles the source would have refetched); passes only inside the
window, every 60 s (the source decided at the day's first pass wherever it fell, recording a missed window as
"outside-window" — no order either way); the daily candles come from the desk's Coinbase bar cache (the source read
the candles endpoint's latest page); the buy is one IOC attempt on the sim venue at the live ask with its taker
fee (the source's isolated ledger booked the ask without a fee).

Inputs via context.extra:
  "quote"  {"bid","ask","received_at"} the Coinbase ticker (hub quotes, source coinbase), received_at = its receipt
  "meta"   {"decisions": {decision_id: record}} the decisions made (the last 40 days kept)
Bars: {"BTC-USD": completed daily candles {"t","o","h","l","c","v"}} (Coinbase Exchange)."""
from datetime import datetime, timedelta, timezone

from .compat import BaseSleeve, Intent, SleeveConfig
from ...vendor.aurelia import coinbase_schedule as CS

SLEEVE = "FWD_COINBASE_SMA200_V1"
PRODUCT = "BTC-USD"
QUANTITY = 0.01
BUDGET_USD = 100000
MAX_EXPOSURE = 0.10
QUOTE_MAX_AGE_S = 30
VENUE = "sim:coinbase"
KEEP_DAYS = 40
MEMO = "_fwd_coinbase_sma200"

CONFIG = SleeveConfig(
    sleeve_id="fwd_coinbase_sma200", cadence_s=60, universe=(PRODUCT,),
    state_schema={"decisions": "dict"}, risk_pct=None)


def history_of(bars, now):
    """forward_cycle._coinbase_history over the desk's daily candles: {"date","complete": True,"close"} for every
    candle closed by now, by date."""
    rows = []
    for b in bars or []:
        opened = datetime.fromtimestamp(float(b["t"]), tz=timezone.utc)
        if opened + timedelta(days=1) > now:
            continue
        rows.append({"date": opened.date().isoformat(), "complete": True, "close": float(b["c"])})
    rows.sort(key=lambda row: row["date"])
    return rows


def quote_of(q, now):
    """the desk's ticker -> the source's native quote {"bid","ask","as_of"}: as_of = its receipt, no later than the
    decision that reads it (None without a receipt)."""
    if not q or q.get("received_at") is None or q.get("bid") is None or q.get("ask") is None:
        return None                                       # (the source's float(payload["bid"]) raised on these)
    at = min(float(q["received_at"]), now.timestamp())
    return {"bid": q.get("bid"), "ask": q.get("ask"), "as_of": datetime.fromtimestamp(at, tz=timezone.utc).isoformat()}


def _refusal(quote, moment):
    """experiment_executor.submit's checks on the buy (its ledger-identity checks have no counterpart here)."""
    quoted = datetime.fromisoformat(quote["as_of"])
    if moment - quoted > timedelta(seconds=QUOTE_MAX_AGE_S):
        return None, "quote is stale"
    if quoted > moment:
        return None, "quote is in the future"
    price = float(quote["ask"])
    if price <= 0 or float(quote["bid"]) > float(quote["ask"]):
        return price, "quote is incomplete or crossed"
    if QUANTITY * price > BUDGET_USD * MAX_EXPOSURE:
        return price, "order exceeds the sleeve exposure cap"
    return price, None


def decide(moment, history, quote, decisions, held=0.0):
    """forward_sleeves.coinbase_forward(moment, history, quote, state, place=True): the day's decision
    (coinbase_schedule.decide, recorded in state["decisions"]) and, when executable, the SMA200 rule (the module
    docstring) on `held`, the BTC this book holds. Returns (decision, order | None, decisions after this pass):
    a buy {price, qty}, a sell {price, qty, exit: True}."""
    state = {"decisions": dict(decisions or {}), "missed": []}
    decision = CS.decide(SLEEVE, PRODUCT, moment, history, quote, state)
    decision["sleeve"] = SLEEVE
    order = None
    if not decision.get("duplicate") and decision["status"] == "executable":
        closes = [float(r["close"]) for r in history[-200:]]   # the 200 completed consecutive days the gate proved
        sma, close = sum(closes) / len(closes), closes[-1]
        decision["sma200"] = round(sma, 2)
        if held > 0 and close < sma:
            bid, ask = float(quote["bid"]), float(quote["ask"])
            if bid > 0 and bid <= ask:
                order = {"price": bid, "qty": held, "exit": True}
                decision["status"] = "PAPER-EXIT"
            else:
                decision["status"], decision["reason"] = "BLOCKED", "quote is incomplete or crossed"
        elif held > 0:
            decision["status"], decision["reason"] = "HOLD", "close at or above SMA200"
        elif close <= sma:
            decision["status"], decision["reason"] = "FLAT", "close not above SMA200"
        else:
            price, refused = _refusal(quote, moment)
            if refused:
                decision["status"], decision["reason"] = "BLOCKED", refused
            else:
                order = {"price": price, "qty": QUANTITY}
                decision["status"] = "PAPER-ACTIVE"
    decision["order"] = order
    return decision, order, state["decisions"]


def pass_decision(now, candles, quote_row, prior, held=0.0):
    """forward_cycle.run_cycle's Coinbase step: outside the window it decides on nothing fetched
    (coinbase_forward(now, [], None, state, place=False)); inside it, a pass without a ticker or without candles
    decides nothing — (None, None, prior) — as the source's cycle raised on the failed Coinbase call before
    decide(), recording nothing, and retried on its next loop."""
    if not CS.in_window(now):
        return decide(now, [], None, prior)
    quote = quote_of(quote_row, now)
    if quote is None or not candles:
        return None, None, dict(prior)
    return decide(now, history_of(candles, now), quote, prior, held)


def held_of(extra):
    """the BTC this book holds (the femto adapter's sleeve_state), 0 when flat or while its exit is working."""
    pos = (((extra or {}).get("sleeve_state") or {}).get(PRODUCT) or {}).get("position") or {}
    if pos.get("exit_submitted"):
        return 0.0
    return max(0.0, float(pos.get("qty") or 0.0))


def _pass(bars, context):
    extra = context.extra if isinstance(context.extra, dict) else {}
    memo = extra.get(MEMO)
    if memo is None or memo[0] is not context:              # one decision per pass's context (identity, not id())
        now = datetime.fromtimestamp(float(context.now), tz=timezone.utc)
        memo = (context, pass_decision(now, (bars or {}).get(PRODUCT), extra.get("quote"),
                                       (extra.get("meta") or {}).get("decisions") or {}, held_of(extra)))
        extra[MEMO] = memo
    return memo[1]


class FwdCoinbaseSma200(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        decision, order, _ = _pass(bars, context)
        if not order:
            return []
        if order.get("exit"):
            return [Intent("exit", PRODUCT, side="long", asset="spot", venue=VENUE, qty=order["qty"],
                           price_hint=order["price"], order={"tif": "ioc", "window_s": 1.0},
                           signal_key=decision["id"] + "|exit",
                           reason="%s sell %g %s at the bid %s: decision %s, close %s below SMA200 %s"
                                  % (SLEEVE, order["qty"], PRODUCT, order["price"], decision["id"],
                                     decision.get("close"), decision.get("sma200")))]
        return [Intent("enter", PRODUCT, side="long", asset="spot", venue=VENUE, qty=order["qty"],
                       price_hint=order["price"], order={"tif": "ioc", "window_s": 1.0}, signal_key=decision["id"],
                       reason="%s buy %g %s at the ask %s: decision %s, 200 completed days through %s, close %s"
                              % (SLEEVE, order["qty"], PRODUCT, order["price"], decision["id"], decision["day"],
                                 decision.get("close")))]


def signal(bars, slice_state, context):
    return FwdCoinbaseSma200().signal(bars, slice_state, context)


def next_meta(bars, slice_state, context, intents=()):
    """meta.decisions: the day's decision once made (coinbase_schedule's state), the last 40 days kept."""
    meta = dict((context.extra or {}).get("meta") or {})
    _, _, decisions = _pass(bars, context)
    cut = (datetime.fromtimestamp(float(context.now), tz=timezone.utc) - timedelta(days=KEEP_DAYS)).date().isoformat()
    meta["decisions"] = {k: v for k, v in decisions.items() if str(v.get("day") or "") >= cut}
    return meta


def monitor(mod, bars, context):
    """the day's decision, recorded once."""
    decision, _, _ = _pass(bars, context)
    if not decision or decision.get("duplicate"):
        return []
    return [(PRODUCT, "%s %s %s: %s" % (SLEEVE, decision["day"], decision["status"], decision.get("reason")),
             {"id": decision["id"], "status": decision["status"], "close": decision.get("close")})]
