"""FWD_ALPACA_LINK_AI_VOLUME_V1 — lean-desk port (Wave D), restored on the master desk.

master-desk: the Aurelia source desk's USD forward of the public AI-volume spot recipe (PUBLIC_AI_VOLUME_SPOT100;
Agentic-Trading-Desk aurelia-paper-desk @1720157f768e: desk/alpaca_forward.py decide() as desk/forward_cycle.py
run_cycle() ran it, on strategies/public_recipes/public_source_sleeves.py of the Ausar archive — vendored:
desk/vendor/aurelia/forward.py (verbatim excerpts) and desk/vendor/ausar/public_source_sleeves.py (byte-exact)) on
its own virtual book: LINK/USD on the Alpaca paper venue (CR:LINK/USD), long only.

  bars ..... the completed native 4Hour bars since 00:00 UTC of the date 40 days back (the source's fetch window;
             the recipe's EMAs are seeded at its first bar); >= 60 completed.
  window ... a decision only within 300 s after the last completed bar's close; a late bar is never replayed.
  entry .... the recipe's long_signal (source_features ai_volume): the bar's volume above twice the 20-bar volume
             EMA, its close above the 50-bar close EMA and above its open; flat (no pyramid).
  exit ..... flat on the fifth completed bar of the position, counting the entry bar (the bars whose close is at
             or after the entry bar's close). No stop in the source recipe.
  order .... an IOC limit at the ask (buy floor(10% of $100,000 / ask) to 8 decimals) or at the bid (sell the whole
             holding), on a quote stamped no more than 10 s before the decision and not after it, with bid > 0,
             bid <= ask and a spread of at most 100 bps of the ask; a buy worth more than $10,000.01 is refused (the
             source's cap check). One send per bar and side, filled or not.

Gone under the cutover doctrine: the desk kill switch (run_cycle's kill), and the Femto fence (the recipe engine
was fenced, so every decision was BLOCKED).
Named divergences: passes every 60 s inside the 300 s window after each 4h close (the source's supervisor looped
every ~20 s); completed bars come from the desk's bar cache (the source refetched them every 60 s, so a revised
bar could differ); the IOC's fill is the paper venue's, on this book's scaled replica, with Alpaca's crypto taker
fee (the source recorded the broker's fill in its isolated ledger without a fee); sale_uncapped: the source's cap
check refused to sell a holding worth more than $10,000.01, trapping a winner until it fell back under the cap —
here a sale is never refused (the whole holding at the bid, the order the source built before its check).

Inputs via context.extra:
  "quote"         {"bid","ask","t"} Alpaca's latest LINK/USD quote, t = its exchange stamp (epoch)
  "meta"          {"sent": {client_order_id: epoch}} the orders already sent (one send per bar and side)
  "sleeve_state"  {"LINK/USD": {"position": {"qty", "entry_close_at", "exit_submitted"} | None, "pending_entry"}}
Bars: {"LINK/USD": completed 4h bars {"t","o","h","l","c","v"}} (Alpaca crypto)."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from .compat import BaseSleeve, Intent, SleeveConfig
from ...vendor.aurelia import forward as FWD

SPEC = next(b for b in FWD.BOOKS if b["id"] == "FWD_ALPACA_LINK_AI_VOLUME_V1")
SYMBOL = SPEC["symbol"]
FETCH_DAYS = 40
SENT_KEEP_S = 7 * 86400
MEMO = "_fwd_link_ai_volume"

CONFIG = SleeveConfig(
    sleeve_id="fwd_alpaca_link_ai_volume", cadence_s=60, universe=(SYMBOL,),
    state_schema={"position": "dict|None"}, risk_pct=None)


def _utc(ts):
    return datetime.fromtimestamp(float(ts), tz=timezone.utc)


def fetch_start(now):
    """forward_cycle: crypto_bars(symbol, timeframe, (now - timedelta(days=40)).date().isoformat()) — 00:00 UTC."""
    d = (now - timedelta(days=FETCH_DAYS)).date()
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def raw_bars(bars, now):
    """the desk's bars -> the source's raw bars (t = the bar's open as an ISO stamp) from the fetch start."""
    start = fetch_start(now).timestamp()
    return [{"t": _utc(b["t"]).isoformat(), "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"]}
            for b in bars or [] if float(b["t"]) >= start]


def quote_of(q):
    """the desk's quote -> forward_cycle._fetch_quote's {"bid","ask","exchange_at"} ({} when there is none)."""
    if not q:
        return {}
    return {"bid": q.get("bid"), "ask": q.get("ask"),
            "exchange_at": _utc(q["t"]).isoformat() if q.get("t") is not None else None}


def decide(now, raw, quote, held, entry_close):
    """forward_cycle.run_cycle() for this book: decide() without a quote, then with it once one is needed.
    held: the holding (Decimal); entry_close: the bar close the holding was bought on (or None)."""
    bars = FWD.completed_bars(raw, SPEC["step_seconds"], now)
    d = FWD.decide(SPEC, now, bars, None, held, entry_close)
    if d.get("needs_quote"):
        d = FWD.decide(SPEC, now, bars, quote, held, entry_close)
    return uncapped_sale(d, bars, quote, held)


def uncapped_sale(d, bars, quote, held):
    """named divergence sale_uncapped: a sale the source's cap check refused (a holding worth more than $10,000.01)
    goes out as the order the source built before the check — the whole holding, an IOC at the bid."""
    if held > 0 and bars and d.get("status") == "BLOCKED" and d.get("reason") == "Order size is outside the sleeve cap.":
        last = bars[-1]["close_at"]
        return dict(d, status="PAPER-ACTIVE", reason="Signal is inside the decision window with a fresh Alpaca quote.",
                    orders_disabled=False, sale_uncapped=True,
                    order={"paper_only": True, "sleeve": SPEC["id"], "symbol": SPEC["symbol"], "side": "sell",
                           "quantity": float(held), "limit_price": float(Decimal(str(quote["bid"]))),
                           "client_order_id": FWD._client(SPEC, last, "sell"), "bar_close_at": last})
    return d


def _pass(bars, context):
    extra = context.extra if isinstance(context.extra, dict) else {}
    memo = extra.get(MEMO)
    if memo is None or memo[0] is not context:              # one decision per pass's context (identity, not id())
        now = _utc(context.now)
        st = (extra.get("sleeve_state") or {}).get(SYMBOL) or {}
        pos = st.get("position") if isinstance(st.get("position"), dict) else None
        qty = float((pos or {}).get("qty") or 0)
        held = Decimal(str(qty)) if qty > 0 else Decimal(0)
        d = decide(now, raw_bars((bars or {}).get(SYMBOL), now), quote_of(extra.get("quote")), held,
                   (pos or {}).get("entry_close_at") if qty > 0 else None)
        order = d.get("order")
        sent = (extra.get("meta") or {}).get("sent") or {}
        working = bool(st.get("pending_entry")) or bool(pos and pos.get("exit_submitted"))
        send = order if order and order["client_order_id"] not in sent and not working else None
        memo = (context, {"decision": d, "send": send})
        extra[MEMO] = memo
    return memo[1]


class FwdLinkAiVolume(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        o = _pass(bars, context)["send"]
        if not o:
            return []
        px = float(o["limit_price"])
        order = {"type": "limit", "limit_price": px, "tif": "ioc", "window_s": 1.0}
        why = "%s %s %s %s at %s (IOC), bar %s, %s" % (SPEC["id"], o["side"], o["quantity"], SYMBOL, px,
                                                         o["bar_close_at"], SPEC["strategy"])
        if o["side"] == "buy":
            return [Intent("enter", SYMBOL, asset="crypto", qty=float(o["quantity"]), price_hint=px, order=order,
                           signal_key=o["client_order_id"], position_meta={"entry_close_at": o["bar_close_at"]},
                           reason=why)]
        return [Intent("exit", SYMBOL, qty=float(o["quantity"]), price_hint=px, order=order,
                       signal_key=o["client_order_id"], reason=why)]


def signal(bars, slice_state, context):
    return FwdLinkAiVolume().signal(bars, slice_state, context)


def next_meta(bars, slice_state, context, intents=()):
    """meta.sent: the client order ids sent (the source's attempts: one send per bar and side), a week kept."""
    meta = dict((context.extra or {}).get("meta") or {})
    now = float(context.now)
    sent = {k: v for k, v in (meta.get("sent") or {}).items() if now - float(v) < SENT_KEEP_S}
    for it in intents or ():
        if it.signal_key:
            sent[it.signal_key] = now
    meta["sent"] = sent
    return meta


def monitor(mod, bars, context):
    """a decision that sends or is blocked is recorded (waiting and out-of-window passes are not)."""
    d = _pass(bars, context)["decision"]
    if d.get("status") not in ("PAPER-ACTIVE", "BLOCKED"):
        return []
    return [(SYMBOL, "%s %s: %s" % (SPEC["id"], d["status"], d.get("reason")),
             {"status": d["status"], "order": d.get("order")})]
