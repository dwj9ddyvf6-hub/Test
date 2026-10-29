"""FREE_OPT_WHEEL — lean-desk port (Wave D, Decision #119 family).

master-desk: the Aurelia source desk's FREE_OPT_WHEEL_V1 descendant (preserves OPT_WHEEL_LIFECYCLE) restored on the
engine (Agentic-Trading-Desk aurelia-paper-desk @1720157f768e: desk/free_options.py evaluate / execute — vendored
as desk/vendor/aurelia/free_options.py, execute() in free_opt_core — and the lifecycle of
desk/option_packages.py wheel_apply). The wheel: a cash-secured put, assignment, the shares, a covered call.

  put ...... evaluate(): the put's indicative quote fresh (source <= 90 s, receipt <= 30 s, 2 s future tolerance,
             bid > 0, ask >= bid), a strike, cash >= strike x 100 (cash covers assignment) and a "P" in the symbol
             -> sell_to_open 1 at the bid, a day limit; execute(): while the market is open, re-checked at the send,
             once per session; outside the session the day's working entry is withdrawn.
  lifecycle  expiry or assignment (the engine settles an expiring put: worthless, or assigned — 100 shares per
             contract booked at the settlement close); against the owned shares, wheel_apply's open_call: one call
             sold at its bid only while 100 shares are free of other calls (a call is never sold without reserved
             shares), once per session; the call ends at expiry or call assignment (the engine delivers the shares).
             No early exit: the contract's exit is "expiry or call assignment".

  contracts  selected on the desk (the source's wheel_contract was never produced and wheel_apply took the call's
             strike and bid from fixtures): desk/feedlib/free_options_inputs.wheel on the decision chain — the
             corpus's 30-delta weekly SPY wheel: the put (and, against assigned shares, the call) on the nearest
             7-14 DTE expiry with |delta| nearest .30, then the strike nearest the spot. The cash: the book's cash
             less the strike value of its short puts and its working put sales; the shares: the book's.

Gone under the cutover doctrine: the desk kill switch and the pre-trade clock-skew block (free_paper.run passed
send=False when either fired); the Femto fences of the old desk's copy (no snapshot fetch, a sim book); the
missing-producer block (status monitor).
Named divergences: the contract rule above (the source names "one cash-secured put" and "a covered call" and no
strike or expiry); the decision moment is the chain's receipt when the pass fetched it after its start; its own
$100,000 book (the source's descendants shared the $100,000 FREE_OPTIONS pool);
"cash" is that book's free cash after the strike value of its short puts (the source's caller passed none, 0);
assignment and expiry are the engine's settlement (wheel_apply was a fixture ledger the cycle never called); an
order the broker refuses still trades the virtual book (the OMS's labelled quote fill; the source's rejected order
left no position); a pass every 5 minutes of the session (the source evaluated every ~20-second cycle).

Inputs via context.extra:
  "quote"          the put's indicative quote {"symbol","strike","bp","ap","t"|"source_at","received_at"}
                   (free_options_inputs.wheel, "put")
  "call_quote"     the covered call's quote {"symbol","strike","bp","ap"} (free_options_inputs.wheel, "call")
  "decided_at"     the chain's receipt when later than the pass's clock (free_opt_core.moment_of)
  "cash"           free cash: the book's cash less the strike value of its short puts and working put sales
  "shares"         {SYM: shares held} (assigned)
  "market_open"    the clock's is_open
  "legs"           the sleeve's option positions {OCC: {"qty","avg","opened_at","meta"}}
  "pending"        its working option orders [{"action","occ","side","qty","limit","key","meta"}]
  "meta"           {"sent": {client id: session}, "calls": {session: OCC}}
"""
from .compat import BaseSleeve, Intent, SleeveConfig
from . import free_opt_core as C

SPEC_ID = "FREE_OPT_WHEEL_V1"
ACCOUNT = "free_options"
BUDGET_USD = 100_000.0
MULTIPLIER = 100

CONFIG = SleeveConfig(
    sleeve_id="free_opt_wheel", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=None)


def underlying_of(occ):
    return str(occ)[:-15].strip() or str(occ)


def is_call(occ):
    s = str(occ)
    return len(s) > 15 and s[-9] == "C"


def free_shares(sym, shares, legs, pending):
    """shares of `sym` not reserved by a held or working short call (100 per call)."""
    calls = sum(-float(p.get("qty") or 0) for o, p in (legs or {}).items()
                if is_call(o) and underlying_of(o) == sym and float(p.get("qty") or 0) < 0)
    calls += sum(float(o.get("qty") or 0) for o in pending or () if o.get("action") == "enter" and
                 o.get("side") == "sell" and is_call(o.get("occ")) and underlying_of(o.get("occ")) == sym)
    return float((shares or {}).get(sym) or 0) - MULTIPLIER * calls


def covered_call(context, legs, pending, calls_sent):
    """wheel_apply("open_call"): reserved shares (100 free) and a call bid -> sell 1 at the bid; once a session."""
    q = (context.extra or {}).get("call_quote") or {}
    occ = q.get("symbol") or ""
    if not is_call(occ) or context.session in (calls_sent or {}):
        return None
    sym = underlying_of(occ)
    if free_shares(sym, (context.extra or {}).get("shares"), legs, pending) < MULTIPLIER:
        return None
    bid = float(q.get("bp") or q.get("bid") or 0)
    if bid <= 0:
        return None
    return Intent("enter", sym, qty_hint=1, asset="option",
                  legs=({"symbol": occ, "side": "sell", "ratio": 1, "position_intent": "sell_to_open"},),
                  order={"type": "limit", "limit_price": round(bid, 2)},
                  signal_key="free-opt:%s:call:%s:%s" % (SPEC_ID, occ, context.session),
                  position_meta={"spec": SPEC_ID, "wheel": "covered_call", "strike": q.get("strike")},
                  reason="%s sell_to_open 1 covered call %s @%.2f against 100 assigned %s shares"
                         % (SPEC_ID, occ, bid, sym))


def decide(bars, context):
    extra = context.extra or {}
    meta = extra.get("meta") or {}
    sent = dict(meta.get("sent") or {})
    calls = dict(meta.get("calls") or {})
    legs, pending = extra.get("legs") or {}, extra.get("pending") or []
    row = C.evaluate_row(SPEC_ID, context)
    res = C.single(row, context, sent, pending)
    intents = []
    if res["order"]:
        intents.append(C.single_intent(SPEC_ID, res, underlying_of,
                                       {"wheel": "cash_secured_put", "strike": res["order"].get("strike")}))
        sent[res["order"]["client_order_id"]] = context.session
    if res["cancel"]:
        intents.append(Intent("cancel", underlying_of(row["order"]["symbol"]), signal_key=res["cancel"],
                              reason="%s: %s" % (SPEC_ID, res["reason"])))
    if C.market_open(context):
        call = covered_call(context, legs, pending, calls)
        if call is not None:
            intents.append(call)
            calls[context.session] = call.legs[0]["symbol"]
    return {"row": res, "intents": intents, "sent": {k: v for k, v in sent.items() if v == context.session},
            "calls": {k: v for k, v in calls.items() if k == context.session}}


def _pass(bars, context):
    extra = context.extra
    memo = extra.get("_free_opt_pass") if isinstance(extra, dict) else None
    if memo is None or memo[0] is not context:           # one decision per pass's context (identity, not id())
        memo = (context, decide(bars, context))
        if isinstance(extra, dict):
            extra["_free_opt_pass"] = memo
    return memo[1]


class FreeOptWheel(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        return list(_pass(bars, context)["intents"])


def signal(bars, slice_state, context):
    return FreeOptWheel().signal(bars, slice_state, context)


def next_meta(bars, slice_state, context, intents=()):
    meta = dict((context.extra or {}).get("meta") or {})
    p = _pass(bars, context)
    meta["sent"], meta["calls"] = p["sent"], p["calls"]
    return meta


def monitor(mod, bars, context):
    r = _pass(bars, context)["row"]
    return [("SPY", "%s %s: %s" % (SPEC_ID, r["status"], r.get("reason") or ""), {"status": r["status"]})]
