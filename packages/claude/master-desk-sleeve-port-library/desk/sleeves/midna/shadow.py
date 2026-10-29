"""midna_qqq_flip5_tza and midna_w_cyan_moonshot — Midna's shadow books (src/lib/equity/shadow.ts @
cursor/lector-desk-f184 fd0e0a07, blob 388b0ed1: stepHedge, stepMoonshot, closeShadow), ported line for line, on the
watch's shadow feed (desk/feedlib/midna_watch.py: the QQQ flip and the weekly moonshot fires).

  flip5 TZA  each new feed session S (QQQ's last closed daily replica bar, with TZA's bar of S): a pending BUY opens
             TZA at S's open for 30% x $100,000 = $30,000 notional (qty = notional / open); a pending SELL closes it at
             S's open; a held position counts one more session (held); then flip5 on S with nothing held stages BUY,
             and a held position with flip5 off or held >= 20 stages SELL — each for the next session's open
  moonshot   a weekly buy-cyan fire (close <= 14.94, depth60 >= 70.35, latest per name, <= 10 days old) not seen
             before, on a name not held, while fewer than 10 are open: a regular-hours fresh quote (<= 15 min) buys
             floor(min(cash, $1,000) / paper price) shares; it closes at the first fresh regular-hours print at or
             after the close of its 78th week (timeExitAt 1w from the entry session's 09:30); no stop; key seen once
             (entered / rejected / held / cash)

Removed gates: none — the lector books carried no desk gate on these two steps.

Named divergences: the hedge booked S's opening print once S's daily bar was in the feed (after the close); here the
order is sent at S's first regular-hours pass and fills at the engine's price (cost: the source charged 0.1% per side
in its own ledger, the engine its venue schedule). A feed session the watch missed leaves the staged order for the
next session's open (the source waited for the next feed session and booked its open). Moonshot fills are engine
children at the paper price; a working order counts as done (common.virtual_book). The feed hand-off
(shadow-feed.json) is the watch job's cache."""
import math

from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from . import common as M

SOURCE = {"repo": "midna", "ref": "cursor/lector-desk-f184", "commit": "fd0e0a07caaf658b0c349517115e1d5491e9d79e",
          "path": "src/lib/equity/shadow.ts", "blob": "388b0ed160f8e023466ce99edcfdbcbefbb7fb33",
          "producer": {"path": "scripts/tensor-watch.mjs", "blob": "c3777a913452223d86b5c9013f4addcae04e8081"}}
CHEAP_MAX = 14.94
DEPTH60_MIN = 70.35
MOONSHOT_SLOTS = 10
MOONSHOT_WEIGHT = 0.01
HEDGE_WEIGHT = 0.3
HEDGE_MAX_SESSIONS = 20
BASE = 100_000.0


# -- the hedge --------------------------------------------------------------------------------------------------
def hedge_session(hedge, signal):
    """stepHedge's bookkeeping when the feed shows a session: returns the action executed at that session's open
    ("BUY" / "SELL" / None) and updates hedge = {lastSession, pending, pos: {entryDay, held} | None}."""
    if not signal or hedge.get("lastSession") == signal["session"]:
        return None
    if not (signal.get("tzaOpen") or 0) > 0 or not (signal.get("tzaClose") or 0) > 0:
        return None
    session = signal["session"]
    action = None
    if hedge.get("pending") == "BUY" and not hedge.get("pos"):
        hedge["pos"] = {"entryDay": session, "held": 0, "entry": signal["tzaOpen"],
                        "qty": HEDGE_WEIGHT * BASE / signal["tzaOpen"]}
        hedge["pending"] = None
        action = "BUY"
    elif hedge.get("pending") == "SELL" and hedge.get("pos"):
        hedge["pos"] = None
        hedge["pending"] = None
        action = "SELL"
    if hedge.get("pos"):
        hedge["pos"]["held"] += 1
    on = bool(signal["flip5"])
    if not hedge.get("pos") and on:
        hedge["pending"] = "BUY"
    elif hedge.get("pos") and (not on or hedge["pos"]["held"] >= HEDGE_MAX_SESSIONS):
        hedge["pending"] = "SELL"
    hedge["signalOn"] = on
    hedge["lastSession"] = session
    return action


class QqqFlip5Tza(Sleeve):
    def __init__(self):
        self.CONFIG = SleeveConfig(
            sleeve_id="midna_qqq_flip5_tza", family="midna", cadence_s=300, capital=BASE, universe=("TZA",),
            schedule="always", needs={"quotes": {"source": "equity", "symbols": ["TZA"]}, "feeds": ["midna_watch"]},
            params={"weight": HEDGE_WEIGHT, "max_sessions": HEDGE_MAX_SESSIONS, "removed_gates": []},
            source=dict(SOURCE, step="stepHedge"),
            state_schema={"lastSession": "str|None", "pending": "str|None", "pending_from": "str|None", "pos": "dict|None"})
        self._st = None

    def signal(self, view):
        st = dict(view.state or {})
        hedge = {"lastSession": st.get("lastSession"), "pending": st.get("pending"), "pos": st.get("pos"),
                 "signalOn": st.get("signalOn")}
        intents = []
        today = view.session
        # the staged order executes at the open of the session after its signal session (the source booked that open)
        if hedge["pending"] and st.get("pending_from") and today > st["pending_from"] and M.phase_at(view.now) == "rth" \
                and st.get("sent_for") != st["pending_from"]:
            held = M.equity_positions(view).get("TZA")
            q = M.mq(view.quotes.get("TZA"))
            px = (q or {}).get("ask") or (q or {}).get("last")
            if hedge["pending"] == "BUY" and not held and px:
                intents.append(Intent("enter", "TZA", notional=HEDGE_WEIGHT * BASE, price_hint=float(px),
                                      signal_key=f"flip5:{st['pending_from']}:buy",
                                      reason=f"QQQ flip5 on {st['pending_from']}: TZA at the next open",
                                      order=OrderSpec(window_s=6 * 3600)))
                st["sent_for"] = st["pending_from"]
            elif hedge["pending"] == "SELL" and held:
                intents.append(Intent("exit", "TZA", price_hint=float(px) if px else None,
                                      signal_key=f"flip5:{st['pending_from']}:sell",
                                      reason=f"QQQ flip5 off or {HEDGE_MAX_SESSIONS} sessions ({st['pending_from']})",
                                      order=OrderSpec(window_s=6 * 3600)))
                st["sent_for"] = st["pending_from"]
        signal = (view.extra.get("midna_watch") or {}).get("qqq")
        before = hedge.get("pending")
        hedge_session(hedge, signal)
        if hedge.get("pending") and (hedge.get("pending") != before or hedge.get("lastSession") != st.get("lastSession")):
            st["pending_from"] = hedge["lastSession"]
        st.update(lastSession=hedge["lastSession"], pending=hedge["pending"], pos=hedge["pos"],
                  signalOn=hedge.get("signalOn"))
        self._st = st
        return intents

    def update_state(self, view, intents):
        return self._st if self._st is not None else dict(view.state or {})


# -- the moonshot book ------------------------------------------------------------------------------------------
def time_exit_1w(entry_start, max_bars):
    """rules.ts timeExitAt("1w", entryStart, maxBars): the close of the last session of week max_bars (entry week = 1)."""
    p = M.et_parts(entry_start)
    monday_offset = (p["weekday"] + 6) % 7
    monday = M.add_days(p["ymd"], -monday_offset + (max_bars - 1) * 7)
    friday = M.add_days(monday, 4)
    while not M.is_trading_day(friday):
        friday = M.add_days(friday, -1)
    close = M.session_close_minutes(friday)
    return M.et_to_epoch(friday, close // 60, close % 60)


def moonshot_step(book, now, quotes, moonshots):
    """stepMoonshot without marks: book = {"cash", "positions": [{sym, qty, timeExitAt, key}], "seen"}; mutated;
    -> orders."""
    orders = []
    rth = M.phase_at(now) == "rth"
    for p in list(book["positions"]):
        q = quotes.get(p["sym"])
        if not q or not q["last"] > 0:
            continue
        if not rth or not M.quote_is_fresh(q, now):
            continue
        if now < p["timeExitAt"]:
            continue
        fill = M.paper_fill(q, "sell")
        if not fill:
            continue
        book["cash"] = M.round2(book["cash"] + p["qty"] * fill[0])
        book["positions"].remove(p)
        orders.append({"side": "sell", "sym": p["sym"], "qty": p["qty"], "px": fill[0], "key": p["key"],
                       "reason": "moonshot W78 time exit"})
    used = len(book["positions"])
    for fire in moonshots:
        if book["seen"].get(fire["key"]) or used >= MOONSHOT_SLOTS:
            continue
        if fire["close"] > CHEAP_MAX or fire["depth60"] < DEPTH60_MIN:
            book["seen"][fire["key"]] = "rejected"
            continue
        if any(p["sym"] == fire["sym"] for p in book["positions"]):
            book["seen"][fire["key"]] = "held"
            continue
        q = quotes.get(fire["sym"])
        if not rth or not M.quote_is_fresh(q, now):
            continue
        fill = M.paper_fill(q, "buy")
        if not fill:
            continue
        slot = min(book["cash"], BASE * MOONSHOT_WEIGHT)
        qty = math.floor(slot / fill[0])
        if qty < 1 or qty * fill[0] > book["cash"]:
            book["seen"][fire["key"]] = "cash"
            continue
        start = M.et_to_epoch(M.et_ymd(now), 9, 30)
        te = time_exit_1w(start, 78)
        book["positions"].append({"sym": fire["sym"], "qty": qty, "timeExitAt": te, "key": fire["key"]})
        book["cash"] = M.round2(book["cash"] - qty * fill[0])
        book["seen"][fire["key"]] = "enter"
        used += 1
        orders.append({"side": "buy", "sym": fire["sym"], "qty": qty, "px": fill[0], "key": fire["key"],
                       "timeExitAt": te, "depth60": fire["depth60"], "close": fire["close"]})
    return orders


class WeeklyCyanMoonshot(Sleeve):
    def __init__(self):
        self.CONFIG = SleeveConfig(
            sleeve_id="midna_w_cyan_moonshot", family="midna_tensor", cadence_s=300, capital=BASE, universe=(),
            schedule="always", needs={"quotes": {"source": "equity"}, "feeds": ["midna_watch"]},
            params={"cheap_max": CHEAP_MAX, "depth60_min": DEPTH60_MIN, "slots": MOONSHOT_SLOTS,
                    "weight": MOONSHOT_WEIGHT, "hold_weeks": 78, "removed_gates": []},
            source=dict(SOURCE, step="stepMoonshot"), state_schema={"seen": "dict", "pos": "dict"})
        self.engine = None
        self._st = None

    def bind(self, engine):
        self.engine = engine

    def quote_universe(self, now, book=None):
        held = [i[3:] for i in (book.positions if book else {}) if i.startswith("EQ:")]
        feed = self.engine.feeds.get("midna_watch", self, now) if self.engine is not None and \
            self.engine.feeds is not None else None
        return list(dict.fromkeys(held + [m["sym"] for m in (feed or {}).get("moonshots") or []]))

    def signal(self, view):
        st = dict(view.state or {})
        seen = dict(st.get("seen") or {})
        rec = dict(st.get("pos") or {})
        vb, cash = M.virtual_book(view)
        positions = []
        for sym, p in vb.items():
            r = rec.get(sym) or p["meta"] or {}
            te = r.get("timeExitAt")
            if te is None:
                opened = p.get("opened_at") or view.now
                te = time_exit_1w(M.et_to_epoch(M.et_ymd(opened), 9, 30), 78)
            positions.append({"sym": sym, "qty": p["qty"], "timeExitAt": float(te), "key": r.get("key") or sym})
        moons = (view.extra.get("midna_watch") or {}).get("moonshots") or []
        quotes = {}
        for sym in {p["sym"] for p in positions} | {m["sym"] for m in moons}:
            q = M.mq(view.quotes.get(sym))
            if q:
                quotes[sym] = q
        book = {"cash": cash, "positions": positions, "seen": seen}
        orders = moonshot_step(book, view.now, quotes, moons)
        out = []
        for o in orders:
            if o["side"] == "buy":
                out.append(Intent("enter", o["sym"], qty=float(o["qty"]), price_hint=o["px"], signal_key=o["key"],
                                  reason=f"weekly cyan moonshot depth60 {o['depth60']:.1f} close {o['close']}",
                                  order=OrderSpec(window_s=3600),
                                  meta={"position_meta": {"timeExitAt": o["timeExitAt"], "key": o["key"]}}))
            else:
                out.append(Intent("exit", o["sym"], price_hint=o["px"], signal_key=o["key"] + ":exit",
                                  reason=o["reason"], order=OrderSpec(window_s=3600)))
        keep = {p["sym"]: {"timeExitAt": p["timeExitAt"], "key": p["key"]} for p in book["positions"]}
        for sym in M.equity_positions(view):
            if sym not in keep and sym in rec:
                keep[sym] = rec[sym]
        if len(seen) > 3000:
            for k in list(seen)[:len(seen) - 3000]:
                seen.pop(k)
        st.update(seen=book["seen"], pos=keep)
        self._st = st
        return out

    def update_state(self, view, intents):
        return self._st if self._st is not None else dict(view.state or {})
