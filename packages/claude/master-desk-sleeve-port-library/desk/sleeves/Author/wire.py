"""The Author paper wire — Author-desk @652db7af src/lib/workdesk/paper-wire.ts (runPaperTicket, runPaperExits,
maybeBookPaper / rankBookSetups and their ledger helpers) and vault.ts retainFills, carried onto the desk engine.

The source's decision code runs as is (desk/sleeves/Author/paper.py judgePaper / exitMath / paperShares ...). What
the wire did against Alpaca becomes intents:
  placePaperBuy        an enter intent (market in the regular session; a resting limit at the plan's buy, extended
                       hours, before 09:30 / after 16:00 — the source's own split) with the bracket as engine-held
                       stop / target exit rules
  closePaperPosition   an exit intent for the whole position
  closePaperPartial    an exit intent for the trim quantity
The paper ledger (`fills`: every sent / held row, retained as vault.ts does: the last 800 rows plus each name's last
sent buy, and here each open position's trims) lives in the sleeve's own state; open names and quantities are the
sleeve's own book. The swing manager's trims fire once per position (alreadyTrimmed reads the ledger since the
position opened and the engine book's closed trades: DEFECT, 2026-10-26)."""
import math
import re
from datetime import datetime

from ...contract import ExitRule, Intent, OrderSpec
from ...util import ET
from ..jsport import js_round
from . import paper as P
from . import tensor as T

FILL_CAP = 800


def et_parts(now):
    d = datetime.fromtimestamp(now, tz=ET)
    return {"dateEt": d.strftime("%Y-%m-%d"), "weekday": d.strftime("%a"), "hour": d.hour, "minute": d.minute}


def iso(now):
    """new Date(now).toISOString()."""
    from datetime import timezone
    ms = int(math.floor(now * 1000))
    d = datetime.fromtimestamp(ms // 1000, tz=timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (ms % 1000)


def day_et(at_iso):
    from datetime import timezone
    try:
        d = datetime.strptime(at_iso[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return ""
    return d.astimezone(ET).strftime("%Y-%m-%d")


def at_s(at_iso):
    """a row's `at` (new Date().toISOString()) as epoch seconds; 0 when unreadable."""
    from datetime import timezone
    for n, fmt in ((23, "%Y-%m-%dT%H:%M:%S.%f"), (19, "%Y-%m-%dT%H:%M:%S")):
        try:
            return datetime.strptime(str(at_iso)[:n], fmt).replace(tzinfo=timezone.utc).timestamp()
        except (TypeError, ValueError):
            continue
    return 0.0


# runPaperExits' trim test (paper-wire.ts:678-680), with readExit's third TRIM reason, "50% in a week — bank half"
# (exit.ts:216), which /trim|overhead/ never matched (DEFECT, 2026-10-26)
TRIM_RX = re.compile(r"trim|overhead|bank half", re.I)


def is_trim(f):
    return f.get("side") == "sell" and f.get("status") == "sent" and bool(TRIM_RX.search(str(f.get("reason") or "")))


def retain_fills(fills, cap=FILL_CAP, held=None):
    """vault.ts retainFills: the last `cap` rows plus each name's last sent buy. held ({symbol: opened_at} of the open
    positions): each one's sent trims since it opened stay as well, because the once-only trim test reads them for the
    life of the position and the held rows a pass writes for each vetoed sell pushed them out of the window within
    hours (DEFECT, 2026-10-26: HAL, JNJ and BCC trimmed again in Author_washout_ppc_coil)."""
    last_buy = {}
    for f in fills:
        if f.get("side") == "buy" and f.get("status") == "sent":
            last_buy[f["symbol"]] = f
    tail = fills[-max(cap, 1):]
    have = {(f["symbol"], f.get("at"), f.get("side"), f.get("status")) for f in tail}
    keep = [f for f in last_buy.values() if (f["symbol"], f.get("at"), f.get("side"), f.get("status")) not in have]
    if held:
        keep += [f for f in fills[:-max(cap, 1)] if f["symbol"] in held and is_trim(f) and
                 at_s(f.get("at")) >= held[f["symbol"]]]
    return keep + tail


def sleeve_of(f):
    if not f:
        return "swing"
    reason = str(f.get("reason") or "")
    import re
    if f.get("sleeve") == "impulse" or re.search(r"impulse|fresh 5m", reason, re.I):
        return "impulse"
    if f.get("sleeve") == "gold" or re.search(r"gold", reason, re.I):
        return "gold"
    if f.get("sleeve") == "echo" or re.search(r"echo", reason, re.I):
        return "echo"
    return "swing"


def _px_round(n):
    """alpaca.ts roundPx (order prices)."""
    if n >= 1:
        return js_round(n * 100) / 100
    return js_round(n * 10000) / 10000


class Wire:
    """One sleeve's paper wire for one pass: its ledger, book, equity, quotes and clock."""

    def __init__(self, sleeve_id, state, now, equity, positions, quotes, trades=None):
        self.sid = sleeve_id
        self.fills = list(state.get("fills") or [])
        self.now = now
        self.ms = int(now * 1000)
        self.equity = equity
        self.positions = positions or {}
        self.quotes = quotes or {}
        self.trades = list(trades or [])            # the engine book's closed trades (view.extra["closed_trades"])
        self.intents = []
        self.parts = et_parts(now)

    # -- ledger helpers (paper-wire.ts) -------------------------------------------------------------------------------
    def open_symbols(self):
        return [s for s, p in self.positions.items() if float(p.get("qty") or 0) > 0]

    def open_qty(self, symbol):
        p = self.positions.get(symbol) or {}
        return max(0.0, float(p.get("qty") or 0))

    def last_buy(self, symbol):
        for f in reversed(self.fills):
            if f["symbol"] == symbol and f["side"] == "buy" and f["status"] == "sent":
                return f
        return None

    def buys_today(self, date_et):
        return len([f for f in self.fills if f["side"] == "buy" and f["status"] == "sent" and day_et(f["at"]) == date_et])

    def touched_today(self, symbol, date_et):
        return any(f["symbol"] == symbol and f["status"] == "sent" and day_et(f["at"]) == date_et for f in self.fills)

    def sleeve_counts(self, open_symbols):
        imp = sw = 0
        for s in open_symbols:
            if sleeve_of(self.last_buy(s)) == "impulse":
                imp += 1
            else:
                sw += 1
        return imp, sw

    def opened_at(self, symbol):
        return float((self.positions.get(symbol) or {}).get("opened_at") or 0)

    def trimmed(self, symbol):
        """readExit's alreadyTrimmed, once per position: a sent trim since the position opened (the engine book's
        opened_at), in the ledger or in the book's closed trades (one per reduction, carrying the position's
        opened_at), which keep it after the ledger row is gone."""
        opened = self.opened_at(symbol)
        if any(f["symbol"] == symbol and is_trim(f) and at_s(f.get("at")) >= opened for f in self.fills):
            return True
        inst = "EQ:" + symbol
        return opened > 0 and any(t.get("inst") == inst and abs(float(t.get("opened_at") or 0) - opened) < 1e-3 and
                                  TRIM_RX.search(str(t.get("reason") or "")) for t in self.trades)

    def push(self, row):
        self.fills.append(row)
        self.fills = retain_fills(self.fills, held={s: self.opened_at(s) for s in self.open_symbols()})

    def seen_hold(self, row):
        return any(f["symbol"] == row["symbol"] and f["barAt"] == row["barAt"] and f["side"] == row["side"] and
                   f["reason"] == row["reason"] for f in self.fills)

    def state(self):
        return {"fills": self.fills}

    # -- orders --------------------------------------------------------------------------------------------------------
    def _buy_intent(self, symbol, qty, buy, stop, target, bar_at, reason, price):
        session = T.classify_session(self.ms)
        extended = session in ("pre", "post")
        spec = OrderSpec(type="limit", limit_price=_px_round(buy), tif="gtc") if extended else OrderSpec()
        self.intents.append(Intent(
            "enter", symbol, qty=float(qty), price_hint=float(price if price > 0 else buy),
            exit_rules=(ExitRule("stop", float(_px_round(stop))), ExitRule("target", float(_px_round(target)))),
            order=spec, signal_key=f"{self.sid}:{symbol}:{bar_at}:buy", reason=f"{self.sid}: {reason}"[:300],
            meta={"Author": {"buy": buy, "stop": stop, "target": target, "barAt": bar_at}}))

    def _close(self, symbol, qty, reason, bar_at, price):
        self.intents.append(Intent("exit", symbol, qty=None if qty is None else float(qty),
                                   price_hint=float(price) if price else None,
                                   signal_key=f"{self.sid}:{symbol}:{bar_at}:sell:{reason}"[:200],
                                   reason=f"{self.sid}: {reason}"[:300]))

    # -- runPaperTicket ------------------------------------------------------------------------------------------------
    def ticket(self, symbol, side, code, price, buy, stop, target, call, bar_at, date_et, hour, minute, eligible=None,
               barUp=None, folioFlatten=None, tensorFlatten=None, goldTicket=None, echoTicket=None, echoAdd=None,
               bookTicket=None, weekend=None, episodeKind=None, chaseKind=None, impulse=None, atr=None,
               antiChase=None, atSupport=None, curlOk=None, coilOk=None, context=None, observe_lock=False):
        at = iso(self.now)
        base = {"symbol": symbol, "side": side, "qty": 0, "price": price, "buy": buy, "stop": stop, "target": target,
                "call": call, "barAt": bar_at, "status": "held", "reason": "not armed", "at": at}
        if goldTicket and side == "buy":
            if any(f["symbol"] == symbol and f["barAt"] == bar_at and f["side"] == "buy" and f["status"] == "sent"
                   for f in self.fills):
                return dict(base, reason="gold already sent on this bar")
            open_syms = self.open_symbols()
            imp, sw = self.sleeve_counts(open_syms)
            j = P.judge_paper(side="buy", code=code, symbol=symbol, price=price, buy=buy, stop=stop, target=target,
                              hour=hour, minute=minute, openCount=len(open_syms), buysToday=self.buys_today(date_et),
                              lastBuyAt=(self.last_buy(symbol) or {}).get("barAt"), barAt=bar_at, hasPosition=False,
                              goldTicket=True, impulseOpen=imp, swingOpen=sw, closedSwing=0, observe_lock=False)
            if j["action"] != "buy":
                row = dict(base, reason=j["reason"])
                self.push(row)
                return row
            px = price if price > 0 else buy
            buy_px = px if px > 0 else buy
            premarket = hour * 60 + minute < P.PAPER_LAW["fullSizeMinute"]
            qty = P.paper_shares(self.equity, buy_px if buy_px > 0 else 1, "gold", stop=stop, premarket=premarket)
            if not qty:
                qty = 1
            tgt = target if target > buy_px else buy_px * 1.35
            stp = stop if (stop > 0 and stop < buy_px) else buy_px * 0.98
            self._buy_intent(symbol, qty, buy_px, stp, tgt, bar_at, j["reason"], price)
            row = dict(base, qty=qty, buy=buy_px, stop=stp, target=tgt, status="sent", reason=j["reason"],
                       sleeve="gold")
            self.push(row)
            return row
        open_syms = self.open_symbols()
        open_qty = self.open_qty(symbol)
        imp, sw = self.sleeve_counts(open_syms)
        lb = self.last_buy(symbol)
        held_sleeve = sleeve_of(lb)
        last_px = float((lb or {}).get("price") or 0)
        verdict = P.judge_paper(
            side=side, code=code, symbol=symbol, price=price, buy=buy, stop=stop, target=target, hour=hour,
            minute=minute, openCount=len(open_syms), buysToday=self.buys_today(date_et),
            lastBuyAt=(lb or {}).get("barAt"), barAt=bar_at, hasPosition=open_qty > 0,
            entry=last_px if last_px > 0 else buy, sameDay=self.touched_today(symbol, date_et),
            clusterOpen=P.same_story_count(symbol, open_syms),
            eligible=eligible if eligible is not None else P.paper_eligible(
                {"status": "LIVE", "call": call, "buy": buy, "stop": stop, "target": target}),
            barUp=barUp, folioFlatten=folioFlatten, tensorFlatten=tensorFlatten,
            goldTicket=goldTicket or (side == "sell" and held_sleeve == "gold"),
            echoTicket=echoTicket or (side == "sell" and held_sleeve == "echo"), echoAdd=echoAdd,
            bookTicket=bookTicket or (side == "sell" and held_sleeve == "swing"), weekend=weekend,
            episodeKind=episodeKind, chaseKind=chaseKind, impulse=impulse, atr=atr, impulseOpen=imp, swingOpen=sw,
            closedSwing=0, antiChase=antiChase, atSupport=atSupport, curlOk=curlOk, coilOk=coilOk, context=context,
            observe_lock=observe_lock)
        if verdict["action"] == "hold":
            row = dict(base, reason=verdict["reason"])
            if not self.seen_hold(row):
                self.push(row)
            return row
        if verdict["action"] == "buy":
            sleeve = "gold" if goldTicket else "echo" if echoTicket else "swing" if bookTicket else \
                "impulse" if impulse else "swing"
            fill_px = price if price > 0 else buy
            premarket = hour * 60 + minute < P.PAPER_LAW["fullSizeMinute"]
            qty = P.paper_shares(self.equity, fill_px, sleeve, stop=stop, premarket=premarket)
            if not qty:
                row = dict(base, status="held", reason="size rounded to zero")
                self.push(row)
                return row
            tgt = P.paper_target(fill_px) if sleeve == "impulse" else (target if target > fill_px else fill_px * 1.35)
            stp = P.paper_stop(fill_px, stop) if sleeve == "impulse" else \
                (stop if (stop > 0 and stop < fill_px) else fill_px * 0.98)
            self._buy_intent(symbol, qty, buy, stp, tgt, bar_at, verdict["reason"], price)
            row = dict(base, qty=qty, stop=stp, target=tgt, status="sent", reason=verdict["reason"])
            if sleeve != "swing":
                row["sleeve"] = sleeve
            if atr is not None:
                row["atr"] = atr
            self.push(row)
            return row
        self._close(symbol, None, verdict["reason"], bar_at, price)
        row = dict(base, qty=open_qty, status="sent", reason=verdict["reason"])
        self.push(row)
        return row

    # -- runPaperExits -------------------------------------------------------------------------------------------------
    def exits(self, date_et, hour, minute, bar_at, daily_bars):
        """daily_bars(symbol) -> the swing manager's daily tape (see the family module's named divergence)."""
        import re
        out = []
        for symbol in self.open_symbols():
            q = self.quotes.get(symbol) or {}
            price = float(q.get("last") or 0)
            if not (price > 0):
                continue
            bought = self.last_buy(symbol)
            entry = float((bought or {}).get("price") or (bought or {}).get("buy") or 0)
            stop = float((bought or {}).get("stop") or 0)
            impulse = (bought or {}).get("sleeve") == "impulse" or bool(
                re.search(r"impulse", str((bought or {}).get("reason") or ""), re.I))
            opened_at = (bought or {}).get("barAt") or 0
            bars = [] if impulse else daily_bars(symbol)
            already_trimmed = self.trimmed(symbol)
            already_added = any(f["symbol"] == symbol and f["side"] == "buy" and f["status"] == "sent" and
                                re.search(r"add", str(f.get("reason") or ""), re.I) for f in self.fills)
            math_ = P.exit_math(price=price, entry=entry, stop=stop, target=float((bought or {}).get("target") or 0),
                                impulse=impulse, openedAt=opened_at or None, now=bar_at, atr=(bought or {}).get("atr"),
                                bars=bars, alreadyTrimmed=already_trimmed, alreadyAdded=already_added, hour=hour,
                                minute=minute)
            if math_["action"] == "hold":
                qty = self.open_qty(symbol)
                if qty > 0 and price * qty > 0 and price * qty < P.PAPER_LAW["crumbNotional"]:
                    self._close(symbol, None, "crumb — flatten junk", bar_at, price)
                    row = {"symbol": symbol, "side": "sell", "qty": qty, "price": price, "buy": entry, "stop": stop,
                           "target": 0, "call": "BUY", "barAt": bar_at, "status": "sent",
                           "reason": "crumb — flatten junk", "at": iso(self.now)}
                    self.push(row)
                    out.append(row)
                continue
            if math_["action"] == "add":
                out.append(self.ticket(symbol, "buy", "ECHO_ADD", price, entry, stop, P.swing_target(entry, 0), "BUY",
                                       bar_at, date_et, hour, minute, eligible=True, echoTicket=True, echoAdd=True))
                continue
            if math_["action"] == "trim":
                qty = self.open_qty(symbol)
                frac = math_["trimPct"] if (math_.get("trimPct") and math_["trimPct"] > 0) else 0.2
                tq = max(1, math.floor(qty * frac)) if qty > 0 else 0
                if tq > 0 and tq < qty:
                    self._close(symbol, tq, math_["reason"], bar_at, price)
                    row = {"symbol": symbol, "side": "sell", "qty": tq, "price": price, "buy": entry, "stop": stop,
                           "target": 0, "call": "BUY", "barAt": bar_at, "status": "sent", "reason": math_["reason"],
                           "at": iso(self.now)}
                    self.push(row)
                    out.append(row)
                    continue
            out.append(self.ticket(symbol, "sell", "STOP" if math_["reason"] == "card stop" else "TARGET", price, entry,
                                   stop, P.paper_target(entry) if impulse else P.swing_target(entry, 0), "BUY",
                                   bar_at, date_et, hour, minute, eligible=True))
        return out


# -- maybeBookPaper ----------------------------------------------------------------------------------------------------
def rank_book_setups(setups):
    def key(s):
        tier = 2 if s.get("tier") == "S" else 1 if s.get("tier") == "A" else 0
        size = 1 if "full" in str(s.get("size") or "").lower() else 0
        return (-tier, -size, -(1 if s.get("atSupport") else 0), -(1 if s.get("curlOk") else 0),
                -float((s.get("plan") or {}).get("rr") or 0))
    return sorted(setups, key=key)


def book_paper(wire, book, date_et, hour, minute, weekend=False):
    """maybeBookPaper: today's book, ranked; each setup a book ticket at the live mark; stop after six sends."""
    if not book or book.get("dateEt") != date_et:
        return []
    if book.get("window") == "weekend" or weekend:
        return []
    setups = book.get("setups") or []
    if not setups:
        return []
    out = []
    for s in rank_book_setups(setups):
        q = wire.quotes.get(s["symbol"]) or {}
        px = float(q.get("last") or 0)
        if not (px > 0):
            px = float(s.get("close") or s["plan"].get("buy") or 0)
        row = wire.ticket(s["symbol"], "buy", "BOOK_BUY", px, s["plan"]["buy"], s["plan"]["stop"], s["plan"]["target"],
                          "BUY" if "full" in str(s.get("size") or "").lower() else "HALF",
                          int(s.get("completedBarAt") or wire.ms), date_et, hour, minute, eligible=True,
                          bookTicket=True, impulse=False, antiChase=s.get("antiChase"), atSupport=s.get("atSupport"),
                          curlOk=s.get("curlOk"), coilOk=s.get("coilOk"), context=None)
        out.append(row)
        if row["status"] == "sent":
            if len([r for r in out if r["status"] == "sent"]) >= P.PAPER_LAW["maxSwingOpen"]:
                break
    return out
