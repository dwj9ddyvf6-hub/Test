"""FREE_KRAKEN_LINK_CROWDED_V1 — lean-desk port (Wave D), restored on the master desk.

master-desk: the Aurelia source desk's LINK crowded-long failure short (Agentic-Trading-Desk aurelia-paper-desk
@1720157f768e: desk/kraken_paper.py run() and crowded() on desk/kraken_clock.py — vendored as
desk/vendor/aurelia/kraken_clock.py (byte-exact) and desk/vendor/aurelia/kraken.py (verbatim excerpts)) on its own
virtual book: PF_LINKUSD, Kraken's USD linear perpetual (contract size 1 LINK), on the desk's labelled sim venue
(PERP:KRAKEN_FUTURES:PF_LINKUSD) at Kraken's live public ticker. "The breakdown rule plus" Kraken's own funding.

  signal ... the breakdown (free_kraken_link_breakdown: the latest bar whose open(i+2) has arrived closed below the
             lowest low of the 20 bars before it, >= 22 completed 4h candles), and then Kraken's HOURLY funding
             prints (not an 8-hour Binance settlement; the instrument's coefficient is not applied again): the
             prints stamped at or before now, >= 30 of them in the last 90 days, the latest print (the API's order)
             above zero and above the 90-day window's 75th percentile (sorted[int(0.75 x (n - 1))]) — crowded().
             While the breakdown is not entry_ready this row waits on it ("Crowded-long waits on the same
             breakdown. ...").
  entry .... flat: short 1 contract at the live bid, on a ticker with a bid and an ask and the bid not above the
             ask; the sleeve's cap: 1 x bid within 10% of its $100,000 budget; no overlapping short.
  exit ..... the breakdown's 16-hour hold: buy the contract back at the live ask on the first pass once entry due +
             16h has arrived (kraken_clock.exit_due_at), on a ticker with a bid and an ask, bid not above the ask.

Gone under the cutover doctrine: the desk kill switch and the pre-trade clock-skew block (free_paper's
block_reason), and the Femto fence (its history collector was never imported, so no row ever ran live).
Named divergences: the crowded short is covered on the breakdown's 16-hour clock (the source's _cover_due matched
only BREAKDOWN ledger rows, so a crowded short was never bought back — its rule is "the breakdown rule plus" the
funding gate, research_descendants FWD_RESEARCH_CROWDED_V1, and that rule holds 16 hours); an empty funding list
is crowded()'s own WARMING_UP (the source's run() took the breakdown's entry_ready row instead when the funding call
returned no rows, firing without the funding gate); an unreachable funding endpoint blocks this row only
(BLOCKED_INPUT; the source's pass failed for every Kraken book); the funding prints are refetched once a newer
hourly print can exist (the source cached them for 6 hours, so its "latest" print could be up to 6 prints old);
one entry per signal event (the source keyed its fill by sleeve and UTC date); the cover clock is the entry
decision's own entry_due_at, kept on the position; fresh candles every pass (the source reused its collector's
candles for up to 6 hours); a pass every 5 minutes plus one at each 4h boundary (the source looped every ~20 s);
each entry / cover is an IOC on the sim venue at the live bid / ask, retried every engine pass while it holds, with
the venue's taker fee (the source's ledger booked them at once, without a fee).

Inputs via context.extra:
  "quote"         {"bid","ask"} the Kraken futures ticker (hub quotes, source kraken_futures)
  "funding"       [{"timestamp","fundingRate","relativeFundingRate"}, ...] Kraken's historical funding prints for
                  PF_LINKUSD as the API lists them (feed kraken_funding:PF_LINKUSD; None when unreachable)
  "sleeve_state"  {"PF_LINKUSD": {"position": {"qty": -1, "entry_due_at", ...} | None, "pending_entry": {...}}}
Bars: {"PF_LINKUSD": completed 4h trade candles {"t","o","h","l","c","v"}} (Kraken futures charts)."""
from datetime import datetime, timezone

from .compat import BaseSleeve, Intent, SleeveConfig
from ...vendor.aurelia import kraken as K
from ...vendor.aurelia import kraken_clock as KC

ID = "FREE_KRAKEN_LINK_CROWDED_V1"
INSTRUMENT = "PF_LINKUSD"
QUANTITY = 1
BUDGET_USD = 100000
MAX_EXPOSURE = 0.10
VENUE = "sim:kraken_futures"
MEMO = "_free_kraken_link_crowded"

CONFIG = SleeveConfig(
    sleeve_id="free_kraken_link_crowded", cadence_s=300, universe=(INSTRUMENT,),
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
    """experiment_executor.submit's checks on a fill at the live quote: price positive, book uncrossed, the
    notional within the sleeve's cap."""
    price = float(quote["ask"] if side == "buy" else quote["bid"])
    if price <= 0 or float(quote["bid"]) > float(quote["ask"]):
        return price, "quote is incomplete or crossed"
    if qty * price > BUDGET_USD * MAX_EXPOSURE:
        return price, "order exceeds the sleeve exposure cap"
    return price, None


def decide(rows, rates, now, quote, held=None, working=False):
    """kraken_paper.run() for this sleeve's row on one pass, then the cover. rates: the funding prints (None =
    unreachable); held: the short's position or None; working: an entry (or the cover) in flight."""
    signal = KC.breakdown_decision(rows, now, instrument=INSTRUMENT)
    if signal.get("status") != "entry_ready":
        crowd = {**signal, "reason": "Crowded-long waits on the same breakdown. " + signal.get("reason", "")}
    elif rates is None:
        crowd = {"status": "BLOCKED_INPUT", "reason": "Kraken funding prints were not fetched."}
    else:
        crowd = K.crowded(rows, list(rates), now)
    row = {"id": ID, "instrument": INSTRUMENT, "quote_currency": "USD", **crowd}
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
        memo = (context, decide(candle_rows((bars or {}).get(INSTRUMENT), now), extra.get("funding"), now,
                                extra.get("quote"), held, working))
        extra[MEMO] = memo
    return memo[1]


class FreeKrakenLinkCrowded(BaseSleeve):
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
                              reason="%s short %d at the live bid %s: crowded-long failure on Kraken hourly funding; "
                                     "breakdown signal %s, open(i+2) %s, event %s"
                                     % (ID, QUANTITY, e["price"], e["signal_open_at"], e["entry_due_at"],
                                        e["signal_event_id"])))
        return out


def signal(bars, slice_state, context):
    return FreeKrakenLinkCrowded().signal(bars, slice_state, context)


def monitor(mod, bars, context):
    """one record per decision state: the row's status, its signal bar and its reason."""
    r = _pass(bars, context)["row"]
    return [(INSTRUMENT, "%s %s: signal %s; %s" % (ID, r.get("status"), r.get("signal_open_at"), r.get("reason")),
             {k: r.get(k) for k in ("status", "signal_open_at", "entry_due_at", "signal_event_id")})]
