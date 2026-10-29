"""FREE_OPT_TAIL — lean-desk port (Wave D, Decision #119 family).

master-desk: the Aurelia source desk's FREE_OPT_TAIL_V1 descendant (preserves OPT_TAIL_STATE) restored on the
engine (Agentic-Trading-Desk aurelia-paper-desk @1720157f768e desk/free_options.py; its rules vendored as
desk/vendor/aurelia/free_options.py and called unchanged, execute() in free_opt_core). Buy ONE put when the
underlying's day return is at or below -3%; this source shape is one contract.

  entry .... evaluate(): the put's indicative quote fresh (source <= 90 s old, receipt <= 30 s, neither more than 2 s
             ahead of the clock, receipt not before the source, bid > 0, ask >= bid), the underlying session return
             <= -0.03 and a "P" in the quote's symbol -> buy_to_open 1 at the ask, a day limit. execute(): only while
             the market is open, the quote re-checked at the send, once per session (client id
             free-opt-FREE_OPT_TAIL_V1-<date>); outside the session the day's working entry is withdrawn.
  exits .... the contract's own: five sessions (the next open after five completed sessions counting the entry's)
             or a 50% premium loss (the put's mark at or below half its fill price); sold at the bid.

  contract . selected on the desk (the source's run() was called without a quote and its SPY probe names no
             contract): desk/feedlib/free_options_inputs.tail on the decision chain — the put with |delta| .50-.65,
             21-35 DTE, expiring at least 7 calendar days past the five-session exit; the nearest expiry, then the
             delta nearest .575, then the strike nearest the spot (the R19 long-put selector); its quote's source_at
             is the chain's quote time, its received_at the fetch. The underlying session return: SPY live mid over
             its last completed close.

Gone under the cutover doctrine: the desk kill switch and the pre-trade clock-skew block (free_paper.run passed
send=False when either fired), and the Femto fences of the old desk's copy (no snapshot fetch, a sim book); the
missing-producer block (status monitor).
Named divergences: the contract rule above (the source names "one put" and nothing more); the decision moment is the
chain's receipt when the pass fetched it after its start; the sleeve trades its own $100,000 book (the source's five
descendants shared the $100,000
FREE_OPTIONS pool of one paper account); the exits are the contract's text (the source's single-order path never
closed a position); an order the broker refuses still trades the virtual book (the OMS's labelled quote fill; the
source's rejected order left no position and used the day's client id); a pass every 5 minutes of the session (the
source evaluated on every ~20-second supervisor cycle).

Inputs via context.extra:
  "quote"              the put's indicative quote {"symbol","bp","ap","t"|"source_at","received_at"}
                       (free_options_inputs.tail)
  "decided_at"         the chain's receipt when later than the pass's clock (free_opt_core.moment_of)
  "underlying_return"  the underlying's session return (SPY live mid / last completed close - 1)
  "market_open"        the clock's is_open
  "legs"               the sleeve's option positions {OCC: {"qty","avg","opened_at","meta"}}
  "pending"            its working option orders [{"action","occ","side","qty","limit","key","meta"}]
  "option_quotes"      {OCC: {"bid","ask"}} — the held puts
  "held_sessions"      {OCC: completed sessions since the fill}
  "meta"               {"sent": {client id: session}}
  "sleeve_state"
"""
from .compat import BaseSleeve, Intent, SleeveConfig
from . import free_opt_core as C

SPEC_ID = "FREE_OPT_TAIL_V1"
ACCOUNT = "free_options"
BUDGET_USD = 100_000.0
HOLD_SESSIONS = 5
PREMIUM_LOSS = 0.50

CONFIG = SleeveConfig(
    sleeve_id="free_opt_tail", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=None)


def underlying_of(occ):
    return str(occ)[:-15].strip() or str(occ)


def mark_of(q):
    """the put's mark: the mid when two-sided, else the bid."""
    try:
        bid, ask = float((q or {}).get("bid") or 0), float((q or {}).get("ask") or 0)
    except (TypeError, ValueError):
        return None
    if bid > 0 and ask >= bid:
        return (bid + ask) / 2
    return bid if bid > 0 else None


def exit_due(pos, quote, sessions):
    """the contract's exit: five sessions, or a 50 percent premium loss."""
    if sessions is not None and int(sessions) >= HOLD_SESSIONS:
        return "held %d sessions" % int(sessions)
    m, paid = mark_of(quote), float(pos.get("avg") or 0)
    if m is not None and paid > 0 and m <= PREMIUM_LOSS * paid:
        return "premium loss: mark %.2f <= 50%% of %.2f" % (m, paid)
    return None


def decide(bars, context):
    extra = context.extra or {}
    meta = extra.get("meta") or {}
    sent = dict(meta.get("sent") or {})
    legs, pending = extra.get("legs") or {}, extra.get("pending") or []
    row = C.evaluate_row(SPEC_ID, context)
    res = C.single(row, context, sent, pending)
    intents = []
    if res["order"]:
        intents.append(C.single_intent(SPEC_ID, res, underlying_of))
        sent[res["order"]["client_order_id"]] = context.session
    if res["cancel"]:
        intents.append(Intent("cancel", underlying_of(row["order"]["symbol"]), signal_key=res["cancel"],
                              reason="%s: %s" % (SPEC_ID, res["reason"])))
    exiting = {o.get("occ") for o in pending if o.get("action") == "exit"}
    oq, held = extra.get("option_quotes") or {}, extra.get("held_sessions") or {}
    for occ, pos in legs.items():
        if float(pos.get("qty") or 0) <= 0 or occ in exiting:
            continue
        why = exit_due(pos, oq.get(occ), held.get(occ))
        bid = float((oq.get(occ) or {}).get("bid") or 0)
        if why and bid > 0:
            intents.append(Intent(
                "exit", underlying_of(occ), qty_hint=int(float(pos["qty"])),
                legs=({"symbol": occ, "side": "sell", "ratio": 1, "position_intent": "sell_to_close"},),
                order={"type": "limit", "limit_price": round(bid, 2)},
                signal_key="free-opt:%s:exit:%s:%s" % (SPEC_ID, occ, context.session),
                reason="%s sell_to_close %s @%.2f: %s" % (SPEC_ID, occ, bid, why)))
    return {"row": res, "intents": intents, "sent": {k: v for k, v in sent.items() if v == context.session}}


def _pass(bars, context):
    extra = context.extra
    memo = extra.get("_free_opt_pass") if isinstance(extra, dict) else None
    if memo is None or memo[0] is not context:           # one decision per pass's context (identity, not id())
        memo = (context, decide(bars, context))
        if isinstance(extra, dict):
            extra["_free_opt_pass"] = memo
    return memo[1]


class FreeOptTail(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        return list(_pass(bars, context)["intents"])


def signal(bars, slice_state, context):
    return FreeOptTail().signal(bars, slice_state, context)


def next_meta(bars, slice_state, context, intents=()):
    meta = dict((context.extra or {}).get("meta") or {})
    meta["sent"] = _pass(bars, context)["sent"]
    return meta


def monitor(mod, bars, context):
    r = _pass(bars, context)["row"]
    return [("SPY", "%s %s: %s" % (SPEC_ID, r["status"], r.get("reason") or ""), {"status": r["status"]})]
