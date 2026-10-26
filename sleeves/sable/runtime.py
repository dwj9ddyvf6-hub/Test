"""The Sable unattended paper pass — line-by-line port of autopilot-desk @48e8f90f:

  src/lib/desk/ledger-core.mjs      blob 6342ddc8  swingAtr / swingStopPrice / swingTargetPrice / swingSizeShares /
                                                    swingTimeStopDue / swingTrailStop / swingThesisBroken /
                                                    deskDiscretionAllowsBuy / mapTensorToDeskDecision /
                                                    canEnterUnderMandate
  src/lib/desk/unattended-core.mjs  blob 8fb33e59  runUnattendedPaperPass (applyStopsAndTargets, flattenToFillCap,
                                                    considerHeld, considerWatch, placePaperBuy, canEnter, exitPaper,
                                                    applySimulatorFill)
  src/lib/desk/always-on-core.mjs   blob 0acb87a7  equitySession / sessionForEntry / sessionAllowsNewRisk
  src/lib/scanner/contract.mjs      blob 3777a9ce  candidateFor / scannerAvailable

run_pass(state, reads, now_ms, clock_ms) mutates a Sable desk state dict exactly as the source's simulator path does
(fills at the quote, positions with their swing stop / target) and returns the actions it took, in order:
("buy", ticker, qty, price, reason, key) / ("sell", ticker, qty, price, reason, key) / ("cancel", ticker, why).
The family module (desk/sleeves/families/sable.py) turns those actions into engine intents.

Removed under the cutover doctrine (not the strategy's own rules) — the callers pass state without them:
  * runState gates ("Desk is paused.", daily-loss park at mandate.maxDailyLossPct = 2%, stale-tape park);
  * the Edge overlay (state.edge: blockNewEntries, parked names, sizeDown = quarter-risk sizing);
  * the Tensor SELL veto in deskDiscretionAllowsBuy (a 5-minute chart gate on a daily location entry; the Sable
    law itself: "Tensor is a badge") — reads carry paperSell=False here."""
import math
from datetime import datetime
from zoneinfo import ZoneInfo

from ..jsport import gt, js_str, jor, number, round2, truthy

ET = ZoneInfo("America/New_York")
MEGA = ("AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "AVGO", "LLY", "UNH", "JPM", "V", "MA", "TSLA")

DEFAULT_MANDATE = {          # src/lib/desk/types.ts defaultMandate() (the fields the paper pass reads)
    "tempo": "swing", "universe": "broad", "sectors": [], "autonomy": "autopilot", "maxPositions": 6,
    "maxPctPerPosition": 12, "maxDailyLossPct": 2, "startingCapital": 100_000, "allowOvernight": True,
    "allowExtendedHours": False, "allowEtfs": True, "allowStocks": True, "assetClass": "both", "antiChase": True,
    "allowEarningsWindow": False, "allowStressBuys": False, "excludeMegaCaps": False, "tensorTiming": "optional",
    "watchlist": ["SPY", "QQQ", "IWM", "SMH", "AAPL", "MSFT", "NVDA", "AMZN", "JPM", "XOM"],
}


# -- ledger-core.mjs -------------------------------------------------------------------------------------------------
def swing_atr(quote_atr, price):
    px = number(price)
    floor = px * 0.015
    a = number(quote_atr)
    if math.isfinite(a) and a >= floor:
        return a
    if math.isfinite(floor) and floor > 0:
        return floor
    return a if (math.isfinite(a) and a > 0) else 0


def swing_stop_price(avg, atr):
    px = number(avg)
    a = swing_atr(atr, px)
    if not px > 0 or not a > 0:
        return None
    return round2(px - a * 1.6)


def swing_target_price(avg, atr):
    px = number(avg)
    a = swing_atr(atr, px)
    if not px > 0 or not a > 0:
        return None
    return round2(px + a * 2.8)


def swing_thesis_broken(hit):
    import re
    hit = hit or {}
    reason = str(hit.get("reason") if hit.get("reason") is not None else
                 (hit.get("publicReason") if hit.get("publicReason") is not None else ""))
    if re.search(r"50-day still falling|Not on a rising 50-day|Too far from the 52-week high|Laggard|Collapsing 50",
                 reason, re.I):
        return True
    action = re.sub(r"\s+", "_", str(hit.get("action") if hit.get("action") is not None else "").upper())
    return action in ("SKIP", "PASS", "LEAVE")


def swing_size_shares(equity=None, cash=None, price=None, atr=None, size_down=False):
    px = number(price)
    stop_dist = swing_atr(atr, px) * 1.6
    eq = number(equity) if number(equity) > 0 else number(cash)
    cash_amt = number(cash)
    if not px > 0 or not stop_dist > 0 or not eq > 0 or not cash_amt > 0:
        return 0
    risk_pct = 0.0025 if size_down else 0.005
    notional_pct = 0.08 if size_down else 0.15
    by_risk = math.floor((eq * risk_pct) / stop_dist)
    by_notional = math.floor((eq * notional_pct) / px)
    by_cash = math.floor((cash_amt * 0.98) / px)
    return max(0, min(by_risk, by_notional, by_cash))


def swing_time_stop_due(opened_at, now, pnl=0):
    pnl = 0 if pnl is None else pnl                     # the default (undefined) and Number(null) are both 0
    if not number(opened_at) > 0:
        return False
    if now - number(opened_at) < 15 * 24 * 60 * 60 * 1000:
        return False
    return number(pnl) <= 0


def swing_trail_stop(avg, atr, last, current_stop):
    px = number(avg)
    a = swing_atr(atr, px)
    one_r = a * 1.6
    if not px > 0 or not one_r > 0:
        return current_stop
    if number(last) >= px + one_r:
        be = round2(px)
        return max(jor(number(current_stop), be), be)
    return current_stop


def map_tensor_to_desk_decision(paper_buy=False, paper_sell=False, has_position=False, parked=False,
                                autonomy="approve", scanner_available=False, desk_buy=None, desk_buy_reason=""):
    if parked:
        return {"kind": "SYSTEM", "reason": "Desk is parked. New risk is blocked."}
    if has_position:
        return {"kind": "HOLD", "reason": ("Tensor SELL is a badge on a swing. Do not round-trip the same session."
                                           if paper_sell else "Position remains inside the plan. No chase, no exit.")}
    if paper_buy and not has_position:
        if desk_buy is False:
            return {"kind": "WAIT", "reason": "Tensor BUY without a desk SETUP. Location-first picks the names."}
        if autonomy == "observe":
            return {"kind": "WAIT", "reason": "Observe mode records the Tensor BUY and waits."}
        return {"kind": "BUY", "reason": "Tensor printed a completed-bar BUY. Used as a timing tool, not the only vote."}
    if desk_buy and not has_position and not paper_sell:
        if autonomy == "observe":
            return {"kind": "WAIT", "reason": "Observe mode records the desk SETUP and waits."}
        return {"kind": "BUY", "reason": desk_buy_reason or
                "Desk discretion: completed-bar SETUP, location, and risk. Tensor was NEUTRAL and did not veto."}
    return {"kind": "WAIT", "reason": ("No SETUP, or chase/risk blocked. Tensor did not print a BUY and the desk did "
                                       "not override.") if scanner_available else
            "No desk-scanner setup on the last completed bar."}


def desk_discretion_allows_buy(quote=None, scanner_hit=None, paper_sell=False, paper_buy=False, completed_bar_at=None,
                               tensor_state=None, mandate=None, tensor_timing=None):
    q = quote or {}
    hit = scanner_hit
    timing = "required" if ((mandate or {}).get("tensorTiming") == "required" or tensor_timing == "required") \
        else "optional"
    kind = str(q.get("kind") or (hit or {}).get("kind") or "").lower()
    if paper_buy is True:
        if kind == "etf":
            return {"ok": False, "why": "ETF is context. Stock book first."}
        if not hit or str(hit.get("action") or "").upper() != "SETUP":
            return {"ok": False, "why": "Tensor BUY without a desk SETUP. Location-first picks the names."}
        return {"ok": True, "why": "Tensor completed-bar BUY (timing tool)."}
    if paper_sell is True:
        return {"ok": False, "why": "Tensor SELL veto."}
    if kind == "etf":
        return {"ok": False, "why": "ETF is context. Stock book first."}
    if timing == "required":
        return {"ok": False, "why": "This mandate waits for a completed-bar Tensor BUY."}
    location_first = str((hit or {}).get("origin") or "") == "location-first"
    bar_at = number(completed_bar_at)
    if location_first:
        if not hit or str(hit.get("action") or "").upper() != "SETUP":
            return {"ok": False, "why": "Scanner is not SETUP."}
        if str(hit.get("antiChase") or "") == "blocked":
            return {"ok": False, "why": "Anti-chase blocked."}
        da = hit.get("dailyBarAt") if hit.get("dailyBarAt") is not None else \
            (q.get("locationFirstAt") if q.get("locationFirstAt") is not None else completed_bar_at)
        daily_at = number(da)
        if not math.isfinite(daily_at) or daily_at <= 0:
            return {"ok": False, "why": "No completed daily bar."}
        reason = hit.get("reason") or "Under the 50-day, on support, MACD recently lifting."
        return {"ok": True, "why": f"Location-first {hit.get('tier') or 'A'} SETUP. {reason}".strip()}
    if not math.isfinite(bar_at) or bar_at <= 0:
        return {"ok": False, "why": "No completed bar."}
    if not hit or str(hit.get("action") or "").upper() != "SETUP":
        return {"ok": False, "why": "Scanner is not SETUP."}
    if str(hit.get("antiChase") or "") == "blocked":
        return {"ok": False, "why": "Anti-chase blocked."}
    rsi, ext, macd = number(q.get("rsi")), number(q.get("extensionAtr")), number(q.get("macdHist"))
    if math.isfinite(rsi) and rsi > 68:
        return {"ok": False, "why": "RSI extended. No chase."}
    if math.isfinite(ext) and ext > 1.6:
        return {"ok": False, "why": "Too far from support."}
    if math.isfinite(rsi) and rsi < 38:
        return {"ok": False, "why": "Momentum broken."}
    if math.isfinite(macd) and macd < -0.15:
        return {"ok": False, "why": "MACD deteriorating."}
    loc = str(hit.get("location") or q.get("location") or "")
    if "extended" in loc.lower():
        return {"ok": False, "why": "Location extended."}
    rsi_txt = _to_fixed0(rsi) if math.isfinite(rsi) else "n/a"
    ticker = str(hit.get("ticker") or q.get("ticker") or "").upper()
    return {"ok": True, "why": (f"Desk discretion on {ticker}: {hit.get('tier') or 'S'} SETUP, support/location ok, RSI "
                                f"{rsi_txt}. Tensor {tensor_state or 'NEUTRAL'} was optional. {hit.get('reason') or ''}"
                                ).strip()}


def _to_fixed0(x):
    from ..jsport import to_fixed
    return to_fixed(x, 0)


def can_enter_under_mandate(mandate, quote, session="regular"):
    if not mandate or not quote:
        return "Missing mandate or quote."
    if quote.get("kind") == "etf":
        return "ETF is context. Stock book first."
    if quote.get("kind") == "stock" and mandate.get("allowStocks") is False:
        return "Stocks disabled."
    if mandate.get("excludeMegaCaps") and str(quote.get("ticker") or "").upper() in MEGA:
        return "Mega-caps are excluded."
    if mandate.get("allowOvernight") is False and session not in ("regular", "paper"):
        return "Overnight entries are disabled."
    if mandate.get("allowExtendedHours") is False and session not in ("regular", "paper"):
        return "Extended-hours entries are disabled."
    if mandate.get("allowStressBuys") is False and quote.get("regime") == "hostile":
        return "Stress-buy block is on."
    if mandate.get("allowEarningsWindow") is False and truthy(quote.get("earningsImminent")):
        return "Earnings-window entries are disabled."
    location_first = number(quote.get("locationFirstAt")) > 0 or str(quote.get("origin") or "") == "location-first"
    if not location_first:
        if number(quote.get("extensionAtr")) > 1.85:
            return "Price is extended — anti-chase."
        r = number(quote.get("rsi"))
        if math.isfinite(r) and r > 72:
            return "Momentum is stretched."
    return None


# -- always-on-core.mjs / contract.mjs ---------------------------------------------------------------------------------
def equity_session(now_ms):
    d = datetime.fromtimestamp(now_ms / 1000.0, tz=ET)
    if d.weekday() >= 5:
        return "closed"
    mins = d.hour * 60 + d.minute
    if 9 * 60 + 30 <= mins <= 16 * 60:
        return "regular"
    if 4 * 60 <= mins < 9 * 60 + 30:
        return "premarket"
    if 16 * 60 < mins < 20 * 60:
        return "afterhours"
    return "closed"


def session_for_entry(market_session, completed_bar_at, now_ms):
    if market_session == "paper":
        return "paper"
    if truthy(completed_bar_at) and equity_session(number(completed_bar_at)) == "regular":
        return "regular"
    return market_session if market_session is not None else equity_session(now_ms)


def session_allows_new_risk(session, mandate=None):
    if session in ("regular", "paper"):
        return True
    if session in ("premarket", "afterhours"):
        return (mandate or {}).get("allowExtendedHours") is True
    return False


def scanner_available(bundle):
    return (bundle or {}).get("status") == "ready" and isinstance((bundle or {}).get("candidates"), list) and \
        len(bundle["candidates"]) > 0


def candidate_for(bundle, ticker):
    sym = str(ticker or "").upper()
    for row in (bundle or {}).get("candidates") or []:
        if row.get("ticker") == sym:
            return row
    return None


def working_order_open(status):
    return status in ("accepted", "proposed")


def _buy_side(row):
    """desk-core.mjs isBuySideCandidate."""
    return str(row.get("tier") if row.get("tier") is not None else "") in ("S", "A", "B") and \
        str(row.get("action") if row.get("action") is not None else "") in ("SETUP", "WATCH")


# -- unattended-core.mjs ------------------------------------------------------------------------------------------------
class Pass:
    """one runUnattendedPaperPass over `state` (simulator path: fills at the quote). `clock_ms` stands for the
    source's Date.now() where it read the wall clock instead of the pass's `now` (soldThisSession, exits from
    applyStopsAndTargets, the simulator fill stamps)."""

    def __init__(self, state, reads=None, now_ms=None, clock_ms=None, uid=None):
        self.s = state
        self.reads = reads or {}
        self.now = now_ms
        self.clock = clock_ms if clock_ms is not None else now_ms
        self.actions = []
        self._n = 0
        self._uid = uid

    def uid(self, prefix):
        if self._uid:
            return self._uid(prefix)
        self._n += 1
        return f"{prefix}_{self._n}"

    # sizing
    def size_for(self, price, atr):
        s = self.s
        broker = s.get("broker") or {}
        cash = number(broker.get("cash")) if number(broker.get("cash")) > 0 else number(s.get("cash"))
        equity = number(broker.get("equity")) if number(broker.get("equity")) > 0 else number(s.get("cash"))
        return swing_size_shares(equity=equity, cash=cash, price=price, atr=atr,
                                 size_down=bool((s.get("edge") or {}).get("sizeDown")))

    def open_buy_risk(self):
        s = self.s
        working = len([o for o in s.get("orders") or [] if o.get("side") == "buy" and working_order_open(o.get("status"))])
        return len(s.get("positions") or []) + working

    def sold_this_session(self, ticker):
        sym = str(ticker or "").upper()
        since = self.clock - 8 * 60 * 60 * 1000
        for e in self.s.get("events") or []:
            kind = str(e.get("kind") or "").upper()
            if str(e.get("ticker") or "").upper() == sym and kind in ("SELL", "EXIT", "TRIM") and \
                    number(e.get("createdAt")) >= since:
                return True
        return False

    def can_enter(self, ticker):
        s = self.s
        if s.get("runState") != "running":
            return "Desk is paused."
        edge = s.get("edge") or {}
        if edge.get("blockNewEntries"):
            return "Edge is standing aside. New risk is blocked."
        if ticker in (edge.get("parked") or []):
            return "Edge parked this name."
        if self.sold_this_session(ticker):
            return "Sold this session. Do not round-trip."
        if any(p.get("ticker") == ticker for p in s["positions"]):
            return "Already holding."
        cap = number(s["mandate"].get("maxPositions"))
        if math.isfinite(cap) and cap > 0 and self.open_buy_risk() >= cap:
            return "Position cap reached."
        if any(e.get("kind") == "BUY" and e.get("ticker") == ticker and not e.get("resolved") and e.get("requiresAction")
               for e in s["events"]):
            return "Open proposal already exists."
        q = s["quotes"].get(ticker)
        if not q:
            return "No quote."
        if self.size_for(q.get("price"), q.get("atr")) < 1:
            return "Insufficient cash."
        if not session_allows_new_risk((s.get("market") or {}).get("session"), s["mandate"]):
            return "Session is closed to new paper risk."
        if any(o.get("ticker") == ticker and o.get("side") == "buy" and working_order_open(o.get("status"))
               for o in s["orders"]):
            return "Working paper order already exists."
        qq = dict(q, regime=q.get("regime") if q.get("regime") is not None else "supportive")
        cba = q.get("completedBarAt") if q.get("completedBarAt") is not None else \
            (s.get("freshness") or {}).get("lastCompletedBarAt")
        return can_enter_under_mandate(s["mandate"], qq, session_for_entry((s.get("market") or {}).get("session"),
                                                                            cba, self.clock))

    def push_event(self, event):
        s = self.s
        if any(r.get("idempotencyKey") and r.get("idempotencyKey") == event.get("idempotencyKey")
               for r in s["events"]):
            return False
        s["events"] = ([event] + s["events"])[:400]
        return True

    def apply_simulator_fill(self, order, fill):
        s = self.s
        order.update(status="filled", fillPrice=fill, filledAt=self.clock)
        if order["side"] == "buy":
            cost = fill * order["qty"]
            s["cash"] = round2(s["cash"] - cost)
            ex = next((p for p in s["positions"] if p["ticker"] == order["ticker"]), None)
            if ex:
                total = ex["avgPrice"] * ex["qty"] + cost
                ex["qty"] += order["qty"]
                ex["avgPrice"] = round2(total / ex["qty"])
            else:
                q = s["quotes"].get(order["ticker"]) or {}
                atr = max(jor(number(q.get("atr")), 0), fill * 0.015)
                s["positions"].insert(0, {"id": self.uid("pos"), "ticker": order["ticker"], "side": "long",
                                          "qty": order["qty"], "avgPrice": fill, "openedAt": self.clock,
                                          "stop": round2(fill - atr * 1.6), "target": round2(fill + atr * 2.8),
                                          "eventId": order.get("eventId")})
        else:
            pos = next((p for p in s["positions"] if p["ticker"] == order["ticker"]), None)
            if pos:
                qty = min(pos["qty"], order["qty"])
                s["cash"] = round2(s["cash"] + fill * qty)
                pos["qty"] -= qty
                if pos["qty"] <= 0:
                    s["positions"] = [p for p in s["positions"] if p["id"] != pos["id"]]
        return order

    def place_paper_buy(self, ticker, reason, bar_at):
        s = self.s
        blocked = self.can_enter(ticker)
        if blocked:
            return {"ok": False, "reason": blocked}
        q = s["quotes"][ticker]
        qty = self.size_for(q.get("price"), q.get("atr"))
        key = f"buy:{ticker}:{js_str(bar_at) if bar_at is not None else js_str(math.floor(self.clock / 180_000))}"
        autonomy = s["mandate"].get("autonomy")
        event = {"id": self.uid("evt"), "idempotencyKey": key, "kind": "BUY", "ticker": ticker,
                 "title": f"Buy {ticker}", "body": reason, "price": q.get("price"), "qty": qty,
                 "createdAt": self.clock, "requiresAction": autonomy == "approve", "resolved": autonomy == "autopilot"}
        if autonomy == "observe":
            event.update(kind="WAIT", requiresAction=False, resolved=True)
            self.push_event(event)
            return {"ok": True, "event": event}
        if not self.push_event(event):
            return {"ok": False, "reason": "Duplicate event."}
        order = {"id": self.uid("ord"), "eventId": event["id"], "ticker": ticker, "side": "buy", "qty": qty,
                 "limit": q.get("price"), "status": "proposed" if event["requiresAction"] else "accepted",
                 "createdAt": self.clock, "venue": "simulator"}
        s["orders"] = ([order] + s["orders"])[:240]
        if autonomy == "autopilot":
            self.apply_simulator_fill(order, q.get("price"))
            event["price"] = q.get("price")
            event["body"] = f"Bought {ticker} at {js_str(q.get('price'))} on the desk simulator. {reason}"
            self.actions.append(("buy", ticker, qty, q.get("price"), reason, key))
        return {"ok": True, "event": event, "order": order}

    def exit_paper(self, ticker, why, kind="EXIT", qty_override=None, now=None):
        s = self.s
        now = self.clock if now is None else now
        pos = next((p for p in s["positions"] if p["ticker"] == ticker), None)
        if not pos or not number(pos.get("qty")) > 0:
            return {"ok": False, "reason": "No long position."}
        q = s["quotes"].get(ticker)
        px = q.get("price") if (q and q.get("price") is not None) else pos["avgPrice"]
        qty = min(max(0, jor(number(pos.get("qty")), 0)), qty_override if qty_override is not None else pos["qty"])
        if not qty > 0:
            return {"ok": False, "reason": "No shares to exit."}
        title = f"Trimmed {ticker}" if kind == "TRIM" else f"Sold {ticker}" if kind == "SELL" else f"Exited {ticker}"
        key = f"{kind.lower()}:{ticker}:{pos['id']}:{js_str(qty)}:{js_str(math.floor(now / 60_000))}"
        event = {"id": self.uid("evt"), "idempotencyKey": key, "kind": kind, "ticker": ticker, "title": title,
                 "body": why, "price": px, "qty": qty, "createdAt": now, "requiresAction": False, "resolved": True}
        order = {"id": self.uid("ord"), "eventId": event["id"], "ticker": ticker, "side": "sell", "qty": qty,
                 "limit": px, "status": "accepted", "createdAt": now, "venue": "simulator"}
        if not self.push_event(event):
            return {"ok": False, "reason": "Duplicate exit."}
        s["orders"] = [order] + s["orders"]
        self.apply_simulator_fill(order, px)
        self.actions.append(("sell", ticker, qty, px, why, key))
        return {"ok": True, "event": event, "order": order}

    def apply_stops_and_targets(self):
        s = self.s
        for pos in list(s["positions"]):
            q = s["quotes"].get(pos["ticker"])
            if not q:
                continue
            self._floors(pos, q)
            if number(q.get("price")) <= number(pos["stop"]):
                self.exit_paper(pos["ticker"], f"Invalidation at {js_str(pos['stop'])} was reached.", "EXIT")
            elif number(q.get("price")) >= number(pos["target"]):
                self.exit_paper(pos["ticker"], f"Target plan at {js_str(pos['target'])} was reached.", "EXIT")

    def _floors(self, pos, q):
        floor_stop = swing_stop_price(pos["avgPrice"], q.get("atr"))
        if floor_stop is not None and not (number(pos.get("stop")) <= floor_stop):
            pos["stop"] = floor_stop
        floor_target = swing_target_price(pos["avgPrice"], q.get("atr"))
        if floor_target is not None and not (number(pos.get("target")) >= floor_target):
            pos["target"] = floor_target
        pos["stop"] = swing_trail_stop(pos["avgPrice"], q.get("atr"), q.get("price"), pos["stop"])

    def flatten_to_fill_cap(self):
        s = self.s
        cap = number(s["mandate"].get("maxPositions"))
        if not math.isfinite(cap) or cap <= 0:
            return
        keep = []
        for row in (s.get("scanner") or {}).get("hands") or []:
            if str(row.get("action") or "").upper() == "SETUP":
                t = str(row.get("ticker") or "").upper()
                if t:
                    keep.append(t)
        keep = set(keep[:int(cap)])
        for order in s.get("orders") or []:
            if order.get("side") != "buy" or not working_order_open(order.get("status")):
                continue
            t = str(order.get("ticker") or "").upper()
            if keep and t not in keep:
                order["status"] = "cancelled"
                order["rejectReason"] = "Mandate is the best two names. Extra paper buys cancelled."
                self.actions.append(("cancel", t, order["rejectReason"]))
        if len(s["positions"]) <= cap:
            return
        extras = [p for p in s["positions"] if str(p["ticker"]).upper() not in keep] if keep else s["positions"][int(cap):]
        for pos in extras:
            if len(s["positions"]) <= cap:
                break
            self.exit_paper(pos["ticker"], "Mandate is the best two names. Flattening to the fill cap.", "EXIT",
                            None, self.now)
        if len(s["positions"]) > cap:
            for pos in list(s["positions"])[int(cap):]:
                if len(s["positions"]) <= cap:
                    break
                self.exit_paper(pos["ticker"], "Mandate is the best two names. Flattening to the fill cap.", "EXIT",
                                None, self.now)

    def consider_held(self, pos, q, read):
        s = self.s
        self._floors(pos, q)
        pnl = (number(q.get("price")) - number(pos["avgPrice"])) * number(pos["qty"])
        if swing_time_stop_due(pos.get("openedAt"), self.now, pnl):
            return self.exit_paper(pos["ticker"], "Time stop. Fifteen days and the rest never paid.", "EXIT", None,
                                   self.now)
        hit = candidate_for(s.get("scanner"), pos["ticker"])
        if swing_thesis_broken(hit):
            why = (hit or {}).get("reason") or (hit or {}).get("action") or "Leader rest is dead."
            return self.exit_paper(pos["ticker"], f"Thesis broke. {why}", "EXIT", None, self.now)
        return {"ok": True, "kind": "HOLD"}

    def consider_watch(self, q, read):
        s = self.s
        hit = candidate_for(s.get("scanner"), q["ticker"])
        ok = scanner_available(s.get("scanner"))
        cba = read.get("completedBarAt") if read.get("completedBarAt") is not None else q.get("completedBarAt")
        disc = desk_discretion_allows_buy(quote=q, scanner_hit=hit, paper_sell=read.get("paperSell"),
                                          paper_buy=read.get("paperBuy"), completed_bar_at=cba,
                                          tensor_state=read.get("state"), mandate=s["mandate"])
        mapped = map_tensor_to_desk_decision(paper_buy=read.get("paperBuy"), paper_sell=read.get("paperSell"),
                                             has_position=False, parked=False, autonomy=s["mandate"].get("autonomy"),
                                             scanner_available=ok, desk_buy=disc["ok"], desk_buy_reason=disc["why"])
        if mapped["kind"] == "BUY":
            reason = mapped["reason"] if read.get("paperBuy") else disc["why"]
            return self.place_paper_buy(q["ticker"], reason, cba)
        if hit and not read.get("paperBuy") and _buy_side(hit):
            rca = read.get("completedBarAt")
            key = f"attention:{q['ticker']}:{js_str(rca) if rca is not None else js_str(math.floor(self.now / 300_000))}"
            self.push_event({"id": self.uid("evt"), "idempotencyKey": key, "kind": "ATTENTION", "ticker": q["ticker"],
                             "title": f"Scanner named {q['ticker']}",
                             "body": f"Desk scanner listed {q['ticker']} as {js_str(hit.get('tier'))} "
                                     f"{js_str(hit.get('action'))}. Desk did not take it.",
                             "createdAt": self.now, "requiresAction": False, "resolved": True})
        return {"ok": False, "reason": mapped["reason"], "kind": mapped["kind"]}

    def run(self):
        s = self.s
        self.apply_stops_and_targets()
        self.flatten_to_fill_cap()
        for pos in list(s["positions"]):
            q = s["quotes"].get(pos["ticker"])
            read = self.reads.get(pos["ticker"])
            if q and read:
                self.consider_held(pos, q, read)
        if s.get("runState") != "running":
            return self.actions
        hands = [r for r in (s.get("scanner") or {}).get("hands") or [] if str(r.get("action") or "").upper() == "SETUP"]
        src = hands if hands else ((s.get("scanner") or {}).get("candidates") or [])
        named = []
        for row in src:
            if str(row.get("action") or "").upper() == "SETUP" and str(row.get("kind") or "") != "etf":
                t = str(row.get("ticker") or "").upper()
                if t and t not in named:
                    named.append(t)
        for ticker in named:
            if any(p["ticker"] == ticker for p in s["positions"]):
                continue
            q = s["quotes"].get(ticker)
            if not q:
                continue
            read = self.reads.get(ticker) or {
                "paperBuy": False, "paperSell": False,
                "completedBarAt": q.get("locationFirstAt") if q.get("locationFirstAt") is not None else
                q.get("completedBarAt"), "state": "NEUTRAL", "evidence": {}}
            self.consider_watch(q, read)
        return self.actions


def run_pass(state, reads=None, now_ms=None, clock_ms=None, uid=None):
    return Pass(state, reads, now_ms, clock_ms, uid).run()
