"""FREE_KRAKEN_ADA_BREAKDOWN_V1 — lean-desk port (Wave D), restored on the master desk.

master-desk: the Aurelia source desk's ADA breakdown short (Agentic-Trading-Desk aurelia-paper-desk @1720157f768e:
desk/kraken_paper.py run() and _cover_due on desk/kraken_clock.py — vendored byte-exact as
desk/vendor/aurelia/kraken_clock.py; the candle rows as its history collector kept them, desk/vendor/aurelia/kraken.py)
on its own virtual book: PF_ADAUSD, Kraken's USD linear perpetual (contract size 1 ADA), on the desk's labelled sim
venue (PERP:KRAKEN_FUTURES:PF_ADAUSD) at Kraken's live public ticker.

  signal ... completed 4h trade candles indexed by open time (forming candle dropped, open times deduplicated, a
             candle with close <= 0 or high < low dropped); the signal bar is the latest one whose open(i+2)
             = open + 8h has arrived; it fires when its close is below the lowest low of the 20 bars before it;
             >= 22 completed candles (kraken_clock.breakdown_decision).
  entry .... flat: short 1 contract at the live bid once open(i+2) has arrived (the candle open is never the
             fill), on a ticker with a bid and an ask and the bid not above the ask; the sleeve's cap: 1 x bid
             within 10% of its $100,000 budget. A held or working short blocks the next (no overlapping short).
  exit ..... the 16-hour hold: buy the contract back at the live ask on the first pass once entry due + 16h has
             arrived (kraken_clock.exit_due_at), on a ticker with a bid and an ask, the bid not above the ask.

Gone under the cutover doctrine: the desk kill switch and the pre-trade clock-skew block (free_paper's
block_reason), and the Femto fence (its history collector was never imported, so no row ever ran live).
Named divergences: one entry per signal event (the source keyed its local fill by sleeve and UTC date, which
refused a second breakdown event of the same UTC day, after the first short was covered, as a duplicate); the
cover clock is the entry decision's own entry_due_at, kept on the position (the source replayed the decision at
the fill on its history collector's candles and covered only a timing_valid fill, keyed by sleeve and exit-due
date: a prior cover on the same exit-due date blocked the next cover for good, and no fill was covered while the
collector was down); fresh candles every pass (the source reused its collector's candles for up to 6 hours, so a
pass could read an older signal bar than the rule names); a pass every 5 minutes plus one at each 4h boundary
(the source's supervisor looped every ~20 s); each entry / cover is an IOC on the sim venue at the live bid / ask,
retried every engine pass while it holds, with the venue's taker fee (the source's isolated ledger booked the bid /
ask at once, without a fee).

Inputs via context.extra:
  "quote"         {"bid","ask"} the Kraken futures ticker (hub quotes, source kraken_futures)
  "sleeve_state"  {"PF_ADAUSD": {"position": {"qty": -1, "entry_due_at", "signal_event_id", "exit_submitted"}
                   | None, "pending_entry": {...}}}
Bars: {"PF_ADAUSD": completed 4h trade candles {"t","o","h","l","c","v"}} (Kraken futures charts)."""
from datetime import datetime, timezone

from .compat import BaseSleeve, Intent, SleeveConfig
from ...vendor.aurelia import kraken as K
from ...vendor.aurelia import kraken_clock as KC

ID = "FREE_KRAKEN_ADA_BREAKDOWN_V1"
INSTRUMENT = "PF_ADAUSD"
QUANTITY = 1
BUDGET_USD = 100000
MAX_EXPOSURE = 0.10
VENUE = "sim:kraken_futures"
MEMO = "_free_kraken_ada_breakdown"

CONFIG = SleeveConfig(
    sleeve_id="free_kraken_ada_breakdown", cadence_s=300, universe=(INSTRUMENT,),
    state_schema={"position": "dict|None"}, risk_pct=None)


def _utc(ts):
    return datetime.fromtimestamp(float(ts), tz=timezone.utc)


def candle_rows(bars, now):
    """the desk's 4h candles -> the source's candle rows (kraken_history._bar), kept the way its history collector
    kept them at `now` (kraken_history.completed)."""
    rows = [K._bar(_utc(b["t"]), b["o"], b["h"], b["l"], b["c"], b.get("v") or 0) for b in bars or []]
    return K.completed(rows, now)


def quote_ok(quote):
    """kraken_paper: a ticker with a bid and an ask, the bid not above the ask."""
    bid, ask = (quote or {}).get("bid"), (quote or {}).get("ask")
    return bool(bid) and bool(ask) and not float(bid) > float(ask)


def _fill_refusal(side, qty, quote):
    """experiment_executor.submit's checks on a fill at the live quote (its client-id and staleness checks have no
    counterpart here): the price is positive, the book uncrossed, the notional within the sleeve's cap."""
    price = float(quote["ask"] if side == "buy" else quote["bid"])
    if price <= 0 or float(quote["bid"]) > float(quote["ask"]):
        return price, "quote is incomplete or crossed"
    if qty * price > BUDGET_USD * MAX_EXPOSURE:
        return price, "order exceeds the sleeve exposure cap"
    return price, None


def decide(rows, now, quote, held=None, working=False):
    """kraken_paper.run() for this sleeve's row on one pass, then _cover_due. held: the short's position
    ({"qty" < 0, "entry_due_at"}) or None; working: an entry (or the cover) is in flight.
    Returns {"row", "enter": {price, entry_due_at, signal_event_id, signal_open_at, not_after} | None,
    "cover": {qty, price, exit_due_at} | None}."""
    signal = KC.breakdown_decision(rows, now, instrument=INSTRUMENT)
    row = {"id": ID, "instrument": INSTRUMENT, "quote_currency": "USD", "venue": "kraken_public_reference", **signal}
    out = {"row": row, "enter": None, "cover": None}
    if row.get("status") == "entry_ready":
        if held or working:
            row["status"] = "position_open"
            row["reason"] = "This sleeve's local short is already open. No overlapping short is added."
        elif not quote_ok(quote):
            row["status"] = "BLOCKED_INPUT"
            row["reason"] = "Kraken ticker is missing or crossed."
        else:
            price, refused = _fill_refusal("sell", QUANTITY, quote)
            if refused:
                row["status"], row["reason"] = "BLOCKED_INPUT", refused
            else:
                due = KC._parse(signal["entry_due_at"])
                out["enter"] = {"price": price, "entry_due_at": signal["entry_due_at"],
                                "signal_event_id": signal["signal_event_id"], "signal_open_at": signal["signal_open_at"],
                                "not_after": (due + KC.BAR).timestamp()}
                row["fill"] = "local_paper_ledger"
                row["result_series"] = "local_paper"
    if held and held.get("entry_due_at") and float(held.get("qty") or 0) < 0:
        due = KC.exit_due_at(KC._parse(held["entry_due_at"]))
        if now >= due and quote_ok(quote) and not held.get("exit_submitted"):
            qty = abs(float(held["qty"]))
            price, refused = _fill_refusal("buy", qty, quote)
            if not refused:
                out["cover"] = {"qty": qty, "price": price, "exit_due_at": due.isoformat()}
    return out


def _pass(bars, context):
    extra = context.extra if isinstance(context.extra, dict) else {}
    memo = extra.get(MEMO)
    if memo is None or memo[0] is not context:              # one decision per pass's context (identity, not id())
        now = _utc(context.now)
        st = (extra.get("sleeve_state") or {}).get(INSTRUMENT) or {}
        pos = st.get("position") if isinstance(st.get("position"), dict) else None
        held = pos if pos and float(pos.get("qty") or 0) < 0 else None
        working = bool(st.get("pending_entry")) or bool(held and held.get("exit_submitted"))
        memo = (context, decide(candle_rows((bars or {}).get(INSTRUMENT), now), now, extra.get("quote"), held, working))
        extra[MEMO] = memo
    return memo[1]


class FreeKrakenAdaBreakdown(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        d = _pass(bars, context)
        out = []
        if d["cover"]:
            c = d["cover"]
            out.append(Intent("exit", INSTRUMENT, qty=c["qty"], price_hint=c["price"], order={"tif": "ioc"},
                              signal_key="%s:cover:%s" % (INSTRUMENT, c["exit_due_at"]),
                              reason="%s cover: buy %g at the live ask %s, 16h exit due %s"
                                     % (ID, c["qty"], c["price"], c["exit_due_at"])))
        if d["enter"]:
            e = d["enter"]
            out.append(Intent("enter", INSTRUMENT, side="short", asset="perp", venue=VENUE, qty=QUANTITY,
                              price_hint=e["price"], order={"tif": "ioc", "not_after": e["not_after"]},
                              signal_key="%s:%s" % (INSTRUMENT, e["signal_event_id"]),
                              position_meta={"entry_due_at": e["entry_due_at"], "signal_event_id": e["signal_event_id"],
                                             "signal_open_at": e["signal_open_at"]},
                              reason="%s short %d at the live bid %s: close %s below the prior 20 lows %s; signal %s, "
                                     "open(i+2) %s, event %s" % (ID, QUANTITY, e["price"], d["row"]["signal_close"],
                                                                 d["row"]["prior_20_low"], e["signal_open_at"],
                                                                 e["entry_due_at"], e["signal_event_id"])))
        return out


def signal(bars, slice_state, context):
    return FreeKrakenAdaBreakdown().signal(bars, slice_state, context)


def monitor(mod, bars, context):
    """one record per decision state: the row's status, its signal bar and its reason."""
    r = _pass(bars, context)["row"]
    return [(INSTRUMENT, "%s %s: signal %s; %s" % (ID, r.get("status"), r.get("signal_open_at"), r.get("reason")),
             {k: r.get(k) for k in ("status", "signal_open_at", "entry_due_at", "signal_event_id", "prior_20_low",
                                    "signal_close")})]
