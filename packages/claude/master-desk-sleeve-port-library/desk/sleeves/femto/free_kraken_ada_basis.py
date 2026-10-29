"""FREE_KRAKEN_ADA_BASIS_V1 — lean-desk port (Wave D), restored on the master desk and trading its basis book.

master-desk: the Aurelia source desk's ADA basis book (Agentic-Trading-Desk aurelia-paper-desk @1720157f768e:
desk/kraken_history.py collect() / basis_decision and desk/kraken_paper.py run()'s basis row — the decision vendored
as verbatim excerpts, desk/vendor/aurelia/kraken.py), computed live from Kraken's public books, and traded on the
desk's labelled sim venues as the rule states it (desk/research_descendants.py FWD_RESEARCH_BASIS_V1: "Equal-token
long spot and short perpetual. Exit at the prior mean or 42 four-hour bars").

  books .... Kraken spot ADAUSD 4h OHLC (the API's retained ~720 completed candles) and the PF_ADAUSD perpetual's
             4h trade candles, each completed at now (forming candle dropped, open times deduplicated, a close
             <= 0 or high < low dropped), aligned on their common completed opens from the later first open to
             the earlier last one; a missing interval stays missing (never filled in).
  identity . PF_ADAUSD listed as type flexible_futures, base ADA, quote USD, pair ADA:USD, contract size 1 —
             otherwise BLOCKED_INPUT (the instrument is not the USD contract this book expects).
  decision . basis = perp close / spot close - 1 on the latest aligned candle of a consecutive run of >= 181
             (180 lookback plus the signal); fired when basis > 0 and above the prior 180 candles' mean plus two
             (population) standard deviations, and the latest known funding print (stamped at or before now) has
             fundingRate > 0 and relativeFundingRate > 0 -> "entry_ready" (equal-token long spot / short
             perpetual; exit at the prior mean or 42 completed 4h candles; no entry delay), else WARMING_UP with
             the readiness estimate, or QUALIFIED/AWAITING SIGNAL.
  entry .... an entry_ready row while the book holds neither leg and works no order: BUY 1 ADA spot (SPOT:KRAKEN:
             ADAUSD, sim:kraken) at the live ask and SELL 1 PF_ADAUSD contract (1 ADA; PERP:KRAKEN_FUTURES:PF_ADAUSD,
             sim:kraken_futures) at the live bid, together, each an IOC at its venue's live public quote (a ticker
             with a bid and an ask, the bid not above the ask), each within 10% of the $100,000 budget; once per
             signal candle. A held or working package blocks the next (no overlapping package).
  exits .... the two-leg unwind, both legs together (sell the spot at the bid, buy the contract back at the ask): the
             first completed aligned candle after the signal whose basis is at or below the prior mean recorded at
             entry, or 42 completed 4h candles after the signal candle closed. A leg left alone (its partner's IOC
             did not fill, or its partner's unwind did) is closed on the next pass. Funding accrues on the short
             contract every hourly print (the engine's Kraken funding).

Gone under the cutover doctrine: the Femto fence (the history collector was not imported, so every basis row read
BLOCKED_INPUT "basis history was not collected"); the source's exclusion of *_BASIS_V1 rows from run()'s placement
loop, and its research descendant's BLOCKED_INPUT status (missing: simultaneous books, basis marks, two-leg unwind) —
the desk has both books, marks them, and unwinds both legs.
Named divergences: the basis book trades (the source only recorded the row); the quantity is 1 token per leg (the
source defines no basis size; run() sent quantity 1 on every Kraken row it placed, with budget_usd 100000 and
max_exposure 0.10); the exit's "prior mean" is the prior 180-candle mean recorded with the entry's signal candle
(basis_decision's mean); the 42 candles count from the signal candle's close (the entry has no delay); the legs are
IOC orders at the live quotes with each venue's taker fee (sim:kraken 80 bps, sim:kraken_futures 5 bps); a failed
leg closes its filled partner on the next pass; the perpetual candles are the desk's last 800 completed (the
source's chart call returned the latest 2,000; the alignment starts at the spot window's first open either way);
fresh books every pass (the source's collector refetched every 6 hours); the funding prints are refetched once a
newer hourly print can exist (the source: every 6 hours); a missing input blocks this row with its own reason (the
source's collector failed as one, every book reading its exception text); a pass every 5 minutes plus one at each
4h boundary.

Inputs via context.extra:
  "spot"         {"ADAUSD": completed 4h spot candles} (hub bars source kraken)
  "funding"      [{"timestamp","fundingRate","relativeFundingRate"}, ...] (feed kraken_funding:PF_ADAUSD)
  "instruments"  {"instruments": [...]} the futures instrument list (feed kraken_instruments)
  "spot_quote"   {"bid","ask"} the Kraken spot ticker of ADAUSD (hub quotes, source kraken)
  "perp_quote"   {"bid","ask"} the Kraken futures ticker of PF_ADAUSD (hub quotes, source kraken_futures)
  "sleeve_state" {"ADAUSD": {"position", "pending_entry"}, "PF_ADAUSD": {...}} the two legs
Bars: {"PF_ADAUSD": completed 4h trade candles} (Kraken futures charts)."""
from datetime import datetime, timedelta, timezone

from .compat import BaseSleeve, Intent, SleeveConfig
from ...vendor.aurelia import kraken as K

NAME = "ADA"
ID = "FREE_KRAKEN_ADA_BASIS_V1"
INSTRUMENT = "PF_ADAUSD"
SPOT = "ADAUSD"
UNPAIRED = ("public spot OHLC does not return bars before the retained window; earlier perpetual bars are not "
            "paired and are not fabricated")
MEMO = "_free_kraken_ada_basis"
QUANTITY = 1                     # tokens per leg (kraken_paper.run(): quantity 1 on every Kraken row it placed)
BUDGET_USD = 100000
MAX_EXPOSURE = 0.10
HOLD_BARS = 42
SPOT_VENUE, PERP_VENUE = "sim:kraken", "sim:kraken_futures"

CONFIG = SleeveConfig(
    sleeve_id="free_kraken_ada_basis", cadence_s=300, universe=(INSTRUMENT,),
    state_schema={"position": "dict|None"}, risk_pct=None)


def _utc(ts):
    return datetime.fromtimestamp(float(ts), tz=timezone.utc)


def candle_rows(bars):
    """the desk's 4h candles -> the source's candle rows (kraken_history._bar)."""
    return [K._bar(_utc(b["t"]), b["o"], b["h"], b["l"], b["c"], b.get("v") or 0) for b in bars or []]


def instrument(payload, symbol=INSTRUMENT):
    """kraken_history.instrument() on the instrument list."""
    rows = (payload or {}).get("instruments") or []
    found = next((row for row in rows if row.get("symbol") == symbol), None)
    if found is None:
        return {"symbol": symbol, "listed": False}
    return {"symbol": found.get("symbol"), "listed": True, "type": found.get("type"), "base": found.get("base"),
            "quote": found.get("quote"), "pair": found.get("pair"), "contractSize": found.get("contractSize"),
            "tradeable": found.get("tradeable"), "fundingRateCoefficient": found.get("fundingRateCoefficient")}


def decide(perp, spot, rates, instruments, now):
    """kraken_history.collect() for this book, then kraken_paper.run()'s basis row. perp / spot: candle rows;
    rates: the funding prints as the API lists them (None = unreachable); instruments: the list (None =
    unreachable). Returns {"row": the source's row, "decision": basis_decision's dict, "aligned": the aligned
    candles}."""
    missing = [what for what, v in (("the futures instrument list", instruments), ("the funding prints", rates)) if v is None]
    if missing:
        reason = "Kraken %s %s not fetched." % (" and ".join(missing), "were" if len(missing) > 1 else "was")
        return {"row": {"id": ID, "instrument": INSTRUMENT, "spot": SPOT, "quote_currency": "USD", "contract_size": None,
                        "aligned": None, "required": None, "missing_inside_overlap": None,
                        "unpaired_before_spot_window": None, "funding_prints": None, "status": "BLOCKED_INPUT",
                        "estimated_ready_at": None, "entry_delay_hours": 0, "exit": None, "reason": reason},
                "decision": {"status": "BLOCKED_INPUT", "reason": reason}, "aligned": []}
    meta = instrument(instruments)
    identity_ok = (
        meta.get("listed") is True
        and meta.get("base") == NAME
        and meta.get("quote") == "USD"
        and meta.get("pair") == f"{NAME}:USD"
        and float(meta.get("contractSize") or 0) == 1.0
        and meta.get("type") == "flexible_futures"
    )
    aligned = K.align(spot, perp, now)
    prints = [{"timestamp": r["timestamp"], "fundingRate": float(r["fundingRate"]),
               "relativeFundingRate": float(r["relativeFundingRate"])} for r in rates]   # kraken_history.funding
    decision = K.basis_decision(aligned["aligned"], prints, now) if identity_ok else {
        "status": "BLOCKED_INPUT",
        "reason": "Kraken instrument identity is not the USD contract this book expects.",
        "required": K.REQUIRED,
        "consecutive": 0,
    }
    row = {"id": ID, "instrument": INSTRUMENT, "spot": SPOT, "quote_currency": "USD",
           "contract_size": meta.get("contractSize"), "aligned": len(aligned["aligned"]), "required": K.REQUIRED,
           "missing_inside_overlap": aligned["missing"], "unpaired_before_spot_window": UNPAIRED,
           "funding_prints": len(prints), "status": decision.get("status") or "BLOCKED_INPUT",
           "estimated_ready_at": decision.get("estimated_ready_at"),
           "entry_delay_hours": decision.get("entry_delay_hours", 0), "exit": decision.get("exit"),
           "reason": decision.get("reason") or "Kraken basis history was not collected."}
    return {"row": row, "decision": decision, "aligned": aligned["aligned"] if identity_ok else []}


def quote_ok(quote):
    """kraken_paper: a ticker with a bid and an ask, the bid not above the ask."""
    bid, ask = (quote or {}).get("bid"), (quote or {}).get("ask")
    return bool(bid) and bool(ask) and not float(bid) > float(ask)


def _within_cap(price):
    return QUANTITY * float(price) <= BUDGET_USD * MAX_EXPOSURE


def _leg(st):
    """a leg's state -> (held position | None, working: an entry or this leg's exit is in flight)."""
    st = st or {}
    pos = st.get("position") if isinstance(st.get("position"), dict) else None
    held = pos if pos and float(pos.get("qty") or 0) else None
    return held, bool(st.get("pending_entry")) or bool(held and held.get("exit_submitted"))


def plan(d, now, spot_quote, perp_quote, legs, attempted=None):
    """one pass of the basis book on the decision d (decide()): legs = {"spot": (held, working), "perp": (...)};
    attempted: the signal candle of the last package sent (one attempt per signal candle). Returns {"enter": {...}
    | None, "unwind": {"why", "legs": ["spot", "perp"]} | None}; d["row"] carries the pass's status."""
    row, x = d["row"], d["decision"]
    (spot, spot_w), (perp, perp_w) = legs["spot"], legs["perp"]
    out = {"enter": None, "unwind": None}
    if spot and perp:                                    # the package: its exits
        pm = dict(perp)
        why = None
        close_at = pm.get("signal_close_at")
        if close_at and now >= datetime.fromisoformat(close_at) + K.BAR * HOLD_BARS:
            why = "42 completed 4h candles after the signal candle closed at %s" % close_at
        mean = pm.get("entry_mean")
        if not why and mean is not None and pm.get("signal_open_at"):
            after = [a for a in d.get("aligned") or [] if a["open_at"] > pm["signal_open_at"]]
            if after and after[-1]["basis"] <= float(mean):
                why = "basis %.6f on %s at or below the prior mean %.6f" % (after[-1]["basis"], after[-1]["open_at"],
                                                                         float(mean))
        if why and not (spot_w or perp_w):
            out["unwind"] = {"why": why, "legs": ["spot", "perp"]}
    elif spot or perp:                                   # a leg alone: its partner never filled, or already left
        alone = "spot" if spot else "perp"
        partner_working = perp_w if spot else spot_w
        if not partner_working and not (spot_w if spot else perp_w):
            out["unwind"] = {"why": "the %s leg is alone (its partner did not fill or already closed)" % alone,
                             "legs": [alone]}
    if row.get("status") != "entry_ready":
        return out
    if spot or perp or spot_w or perp_w:
        row["status"] = "position_open"
        row["reason"] = "This sleeve's basis package is already open. No overlapping package is added."
        return out
    if attempted and attempted == x.get("signal_open_at"):
        row["status"] = "duplicate"
        row["reason"] = "This signal candle's package was already sent."
        return out
    if not (quote_ok(spot_quote) and quote_ok(perp_quote)):
        row["status"] = "BLOCKED_INPUT"
        row["reason"] = "Kraken spot or futures ticker is missing or crossed."
        return out
    buy, sell = float(spot_quote["ask"]), float(perp_quote["bid"])
    if not (_within_cap(buy) and _within_cap(sell)):
        row["status"] = "BLOCKED_INPUT"
        row["reason"] = "order exceeds the sleeve exposure cap"
        return out
    out["enter"] = {"spot_price": buy, "perp_price": sell, "signal_open_at": x["signal_open_at"],
                    "signal_close_at": x["signal_close_at"], "basis": x["basis"], "mean": x["mean"],
                    "threshold": x["threshold"],
                    "not_after": (datetime.fromisoformat(x["signal_close_at"]) + K.BAR).timestamp()}
    row["fill"] = "local_paper_ledger"
    row["result_series"] = "local_paper"
    return out


def _pass(bars, context):
    extra = context.extra if isinstance(context.extra, dict) else {}
    memo = extra.get(MEMO)
    if memo is None or memo[0] is not context:              # one decision per pass's context (identity, not id())
        now = _utc(context.now)
        d = decide(candle_rows((bars or {}).get(INSTRUMENT)), candle_rows((extra.get("spot") or {}).get(SPOT)),
                   extra.get("funding"), extra.get("instruments"), now)
        ss = extra.get("sleeve_state") or {}
        d["plan"] = plan(d, now, extra.get("spot_quote"), extra.get("perp_quote"),
                         {"spot": _leg(ss.get(SPOT)), "perp": _leg(ss.get(INSTRUMENT))},
                         (extra.get("meta") or {}).get("attempted"))
        memo = (context, d)
        extra[MEMO] = memo
    return memo[1]


class FreeKrakenAdaBasis(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        d = _pass(bars, context)
        p, out = d["plan"], []
        u = p["unwind"]
        if u:
            ss = (context.extra or {}).get("sleeve_state") or {}
            for leg in u["legs"]:
                sym = SPOT if leg == "spot" else INSTRUMENT
                pos = (ss.get(sym) or {}).get("position") or {}
                key = pos.get("signal_open_at") or pos.get("entry_date") or context.session
                out.append(Intent("exit", sym, qty=abs(float(pos.get("qty") or QUANTITY)), order={"tif": "ioc"},
                                  signal_key="%s:unwind:%s" % (sym, key),
                                  reason="%s unwind %s leg: %s" % (ID, leg, u["why"])))
        e = p["enter"]
        if e:
            meta = {"signal_open_at": e["signal_open_at"], "signal_close_at": e["signal_close_at"],
                    "entry_basis": e["basis"], "entry_mean": e["mean"], "entry_threshold": e["threshold"]}
            why = "basis %.6f > threshold %.6f (prior mean %.6f) on %s, funding positive" % (
                e["basis"], e["threshold"], e["mean"], e["signal_open_at"])
            out.append(Intent("enter", SPOT, side="long", asset="spot", venue=SPOT_VENUE, qty=QUANTITY,
                              price_hint=e["spot_price"], order={"tif": "ioc", "not_after": e["not_after"]},
                              signal_key="%s:%s" % (SPOT, e["signal_open_at"]), position_meta=dict(meta, leg="spot"),
                              reason="%s long %d %s spot at the live ask %s: %s" % (ID, QUANTITY, SPOT,
                                                                                   e["spot_price"], why)))
            out.append(Intent("enter", INSTRUMENT, side="short", asset="perp", venue=PERP_VENUE, qty=QUANTITY,
                              price_hint=e["perp_price"], order={"tif": "ioc", "not_after": e["not_after"]},
                              signal_key="%s:%s" % (INSTRUMENT, e["signal_open_at"]),
                              position_meta=dict(meta, leg="perp"),
                              reason="%s short %d %s at the live bid %s: %s" % (ID, QUANTITY, INSTRUMENT,
                                                                               e["perp_price"], why)))
        return out


def signal(bars, slice_state, context):
    return FreeKrakenAdaBasis().signal(bars, slice_state, context)


def next_meta(bars, slice_state, context):
    """the signal candle of the last package sent: one attempt per signal candle (a package with a failed leg is
    unwound, never re-sent on the same candle)."""
    meta = dict((context.extra or {}).get("meta") or {})
    e = _pass(bars, context)["plan"]["enter"]
    if e:
        meta["attempted"] = e["signal_open_at"]
    return meta


def monitor(mod, bars, context):
    """the basis row, recorded each time it changes."""
    d = _pass(bars, context)
    r, x = d["row"], d["decision"]
    return [(INSTRUMENT, "%s %s: basis %s vs threshold %s on %s (%s aligned, %s required); %s"
             % (ID, r["status"], x.get("basis"), x.get("threshold"), x.get("signal_open_at"), r.get("aligned"),
                r.get("required"), r.get("reason")),
             dict({k: r.get(k) for k in ("status", "aligned", "required", "estimated_ready_at", "funding_prints",
                                         "contract_size")},
                  **{k: x.get(k) for k in ("basis", "mean", "threshold", "signal_open_at", "consecutive")}))]
