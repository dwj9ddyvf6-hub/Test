"""midna_turtle_s1 / midna_macd_cci / midna_ema4_vwap — Midna's three TraderDev books (src/lib/equity/board.ts @ entire
43f08f96, blob c7abb46c; the rules the 2026-10-09 report quant-research/reports/traderdev_three_2026-10-09.md named),
each its own $100,000 account, ported line for line (applyBoard, manageStops, pyramid, applyEntries, exitOnSignal,
enterTurtle, enterRanked, buyUnit, sell, unitShares). Signals: desk/feedlib/midna_signals.py (the vendored
board-signals.py over the swing basket's completed daily bars).

  Turtle    System 1: a fresh close above the prior 20-day high (or 55-day) buys one unit = min(floor(1% of equity /
            N), floor(cash / price)) with N = ATR(20) (Wilder, seeded on the first 20 true ranges), stop at entry -
            2N; adds a unit each +0.5N over the last add, up to 4 units (the stop moves to the add - 2N when higher);
            exits on the 2N stop (any regular-hours print) or a close under the prior 10-day low (signal);
            at most 4 names, alphabetical; a 20-day breakout after a winning exit is skipped once (the 55-day one is
            still taken)
  MACD-CCI  MACD(12, 26) crossing above its EMA(9) signal with CCI(20) > 100, highest CCI first; one unit (N =
            ATR(14)); exits on the cross back down or a 3 x ATR(14) chandelier under the peak print since entry
  EMA4-VWAP EMA(4) crossing above the 20-session volume-weighted typical price while that VWAP is above its value 5
            sessions earlier, alphabetical; one unit (N = ATR(14)); exits on the cross back or the 3 ATR chandelier
  clock     signal entries and signal exits on the regular session right after the signal session from 10:00 ET (and
            only signals from the book's birth on); stops and chandeliers on every regular-hours pass; Turtle adds
            from 10:00 ET; every buy and sell needs a fresh quote (<= 15 min, <= 1 min ahead) and its paper price

Removed (cutover doctrine): green.ts buyBlockReason on every buy and add (QQQ red AND VIX up AND the name red —
a desk-wide red-day gate); entriesHeld (the desk halt and the ledger-break halt — kill switches).

Named divergences: fills are engine children at the source's paper price (it filled instantly); a working order
counts as done (common.virtual_book) and a unit's bookkeeping (units, last add, stop, N) moves when its order is sent;
the peak print, the units and the skip flags live in this sleeve's state; a Turtle exit's win (the skip rule) is
judged when the exit is sent, from the position's fill average and the paper exit price; the signal file hand-off is
the in-pass producer."""
import math

from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from . import common as M

BOARD_NAV = 100_000.0
BOARD_MAX_NAMES = 4
BOARD_RISK = 0.01
BOARD_UNITS = 4
SOURCE = {"repo": "midna", "ref": "entire", "commit": "43f08f96fce33ee67521002e09f8bc7534cfe264",
          "path": "quant-research/reports/traderdev_three_2026-10-09.md", "blob": "283b2e3bd3fc2c83eda88ca21cf0ea37bcbcb1d7",
          "code": {"path": "src/lib/equity/board.ts", "blob": "c7abb46c3014"},
          "producer": {"path": "scripts/board-signals.py", "blob": "e3efe1ad300c7c886a1c1bbe5e977ab7df05ae19"}}
REMOVED = ["green.ts buyBlockReason on buys and adds: QQQ red + VIX up + the name red (desk-wide red-day gate)",
           "entriesHeld: the desk halt and the ledger-break halt (kill switches)"]
IDS = {"turtle": "midna_turtle_s1", "macd": "midna_macd_cci", "vwap": "midna_ema4_vwap"}
LABEL = {"turtle": "Turtle", "macd": "MACD-CCI", "vwap": "EMA4-VWAP"}


def unit_shares(equity, n, price, cash):
    if not equity > 0 or not n > 0 or not price > 0 or not cash > 0:
        return 0
    risk = math.floor((equity * BOARD_RISK) / n)
    affordable = math.floor(cash / price)
    return max(0, min(risk, affordable))


def can_act(now, as_of, born_day):
    if as_of < born_day:
        return False
    if M.trading_days_after(as_of, M.et_ymd(now)) != 1:
        return False
    if M.phase_at(now) != "rth":
        return False
    return M.et_parts(now)["minutes"] >= 10 * 60


class Account:
    """one board account during one pass, mutated exactly as board.ts mutates it; `orders` = what to send."""

    def __init__(self, side, cash, positions, skip20=None, skipped_for=None, won_on=None, pending_signal=None):
        self.id = side
        self.cash = cash
        self.positions = positions      # [{sym, qty, units, entryAvg, lastAdd, stop, peak, n, atr14, mark}] open
        self.skip20 = dict(skip20 or {})
        self.skipped_for = dict(skipped_for or {})
        self.won_on = dict(won_on or {})
        self.just_won = {}
        self.pending_signal = pending_signal
        self.orders = []

    def opens(self):
        return self.positions

    def open_of(self, sym):
        return next((p for p in self.positions if p["sym"] == sym), None)

    def equity(self):
        return self.cash + M.js_sum(p["qty"] * (p["mark"] or p["entryAvg"]) for p in self.positions)

    def sell(self, p, now, quote, reason):
        if not M.quote_is_fresh(quote, now):
            return False
        fill = M.paper_fill(quote, "sell")
        if not fill:
            return False
        pnl = (fill[0] - p["entryAvg"]) * p["qty"]
        self.cash = M.round2(self.cash + p["qty"] * fill[0])
        self.positions.remove(p)
        self.orders.append({"side": "sell", "sym": p["sym"], "qty": p["qty"], "px": fill[0], "reason": reason})
        if self.id == "turtle":
            self.skip20[p["sym"]] = pnl > 0
            if pnl > 0:
                self.won_on[p["sym"]] = self.pending_signal or ""
                self.just_won[p["sym"]] = True
        return True

    def buy_unit(self, sym, n, atr14, now, quote):
        if not M.quote_is_fresh(quote, now):
            return False
        fill = M.paper_fill(quote, "buy")
        if not fill:
            return False
        held = self.open_of(sym)
        qty = unit_shares(self.equity(), n, fill[0], self.cash)
        if qty < 1:
            return False
        self.cash = M.round2(self.cash - qty * fill[0])
        if not held:
            stop = fill[0] - 2 * n if self.id == "turtle" else 0
            self.positions.append({"sym": sym, "qty": qty, "units": 1, "entryAvg": fill[0], "lastAdd": fill[0],
                                   "stop": stop, "peak": quote["last"], "n": n, "atr14": atr14, "mark": quote["last"]})
            self.orders.append({"side": "buy", "sym": sym, "qty": qty, "px": fill[0], "unit": 1})
            return True
        nxt = held["qty"] + qty
        held["entryAvg"] = (held["entryAvg"] * held["qty"] + fill[0] * qty) / nxt
        held["qty"] = nxt
        held["units"] += 1
        held["lastAdd"] = fill[0]
        held["stop"] = max(held["stop"], fill[0] - 2 * held["n"])
        held["mark"] = quote["last"]
        self.orders.append({"side": "buy", "sym": sym, "qty": qty, "px": fill[0], "unit": held["units"]})
        return True


def mark_account(acc, quotes):
    for p in acc.opens():
        q = quotes.get(p["sym"])
        if not q or not q["last"] > 0:
            continue
        p["mark"] = q["last"]
        if q["last"] > p["peak"]:
            p["peak"] = q["last"]


def manage_stops(acc, now, quotes, by_sym):
    for p in list(acc.opens()):
        q = quotes.get(p["sym"])
        if not q or not q["last"] > 0 or M.phase_at(now) != "rth":
            continue
        bar = by_sym.get(p["sym"])
        if bar and bar["atr14"] > 0:
            p["atr14"] = bar["atr14"]
        if acc.id == "turtle" and q["last"] <= p["stop"]:
            acc.sell(p, now, q, "Turtle 2N stop")
            continue
        if acc.id != "turtle" and p["atr14"] > 0 and q["last"] < p["peak"] - 3 * p["atr14"]:
            acc.sell(p, now, q, "3 ATR chandelier")


def pyramid(acc, now, quotes):
    if acc.id != "turtle" or M.phase_at(now) != "rth" or M.et_parts(now)["minutes"] < 10 * 60:
        return
    for p in list(acc.opens()):
        if p["units"] >= BOARD_UNITS:
            continue
        q = quotes.get(p["sym"])
        if not q or not q["last"] > 0:
            continue
        if q["last"] < p["lastAdd"] + 0.5 * p["n"]:
            continue
        acc.buy_unit(p["sym"], p["n"], p["atr14"], now, q)


def exit_on_signal(acc, now, quotes, signals, hit, reason):
    for bar in signals["bars"]:
        if not hit(bar):
            continue
        p = acc.open_of(bar["sym"])
        q = quotes.get(bar["sym"])
        if not p or not q:
            continue
        acc.sell(p, now, q, reason)


def enter_turtle(acc, now, quotes, signals):
    wanted = sorted([b for b in signals["bars"] if b["enter55"] or b["enter20"]], key=lambda b: b["sym"])
    for bar in wanted:
        sym = bar["sym"]
        if len(acc.opens()) >= BOARD_MAX_NAMES and not acc.open_of(sym):
            break
        if acc.open_of(sym):
            continue
        q = quotes.get(sym)
        if not q or not bar["atr20"] > 0:
            continue
        seen, won = acc.skipped_for, acc.just_won
        if bar["enter20"] and not bar["enter55"] and (won.get(sym) or acc.skip20.get(sym) or seen.get(sym) == signals["asOf"]):
            if not won.get(sym) and seen.get(sym) != signals["asOf"]:
                seen[sym] = signals["asOf"]
                if signals["asOf"] > (acc.won_on.get(sym) or ""):
                    acc.skip20[sym] = False
            continue
        if not bar["enter55"] and not bar["enter20"]:
            continue
        if acc.buy_unit(sym, bar["atr20"], bar["atr14"], now, q):
            acc.skip20[sym] = False


def enter_ranked(acc, now, quotes, signals):
    if acc.id == "macd":
        wanted = sorted([b for b in signals["bars"] if b["macdUp"] and b["cci"] > 100], key=lambda b: -b["cci"])
    else:
        wanted = sorted([b for b in signals["bars"] if b["vwapUp"] and b["vwapRising"]], key=lambda b: b["sym"])
    for bar in wanted:
        if len(acc.opens()) >= BOARD_MAX_NAMES:
            break
        if acc.open_of(bar["sym"]):
            continue
        q = quotes.get(bar["sym"])
        n = bar["atr14"]
        if not q or not n > 0:
            continue
        acc.buy_unit(bar["sym"], n, bar["atr14"], now, q)


def step(acc, now, quotes, signals, born_day):
    """applyBoard for one account (without the removed gates)."""
    by_sym = {b["sym"]: b for b in (signals or {}).get("bars") or []}
    acc.pending_signal = (signals or {}).get("asOf")
    mark_account(acc, quotes)
    manage_stops(acc, now, quotes, by_sym)
    pyramid(acc, now, quotes)
    if not signals or not signals.get("asOf") or not signals.get("bars"):
        acc.just_won = {}
        return
    if not can_act(now, signals["asOf"], born_day):
        acc.just_won = {}
        return
    hits = {"turtle": lambda b: b["exit10"], "macd": lambda b: b["macdDown"], "vwap": lambda b: b["vwapDown"]}
    reasons = {"turtle": "Turtle 10-day exit", "macd": "MACD cross down", "vwap": "EMA4 cross under VWAP"}
    exit_on_signal(acc, now, quotes, signals, hits[acc.id], reasons[acc.id])
    if acc.id == "turtle":
        enter_turtle(acc, now, quotes, signals)
    else:
        enter_ranked(acc, now, quotes, signals)
    acc.just_won = {}


def watch_symbols(signals, held):
    out = list(held)
    for b in (signals or {}).get("bars") or []:
        if b["enter20"] or b["enter55"] or b["exit10"] or b["macdUp"] or b["macdDown"] or b["vwapUp"] or b["vwapDown"]:
            out.append(b["sym"])
    return list(dict.fromkeys(out))


class BoardBook(Sleeve):
    def __init__(self, side):
        self.side = side
        self.CONFIG = SleeveConfig(
            sleeve_id=IDS[side], family="midna", cadence_s=300, capital=BOARD_NAV, universe=(), schedule="always",
            needs={"quotes": {"source": "equity"}, "feeds": ["midna_board_signals"]},
            params={"book": side, "max_names": BOARD_MAX_NAMES, "risk": BOARD_RISK, "units": BOARD_UNITS,
                    "removed_gates": REMOVED},
            source=dict(SOURCE, book=side),
            state_schema={"born": "str", "pos": "dict", "skip20": "dict", "skippedFor": "dict", "wonOn": "dict"})
        self.engine = None
        self._st = None

    def bind(self, engine):
        self.engine = engine

    def quote_universe(self, now, book=None):
        held = [i[3:] for i in (book.positions if book else {}) if i.startswith("EQ:")]
        sig = self.engine.feeds.get("midna_board_signals", self, now) if self.engine is not None and \
            self.engine.feeds is not None else None
        return watch_symbols(sig, held)

    def signal(self, view):
        st = dict(view.state or {})
        st.setdefault("born", view.session)
        sig = view.extra.get("midna_board_signals")
        book, cash = M.virtual_book(view)
        rec = dict(st.get("pos") or {})
        positions = []
        for sym, p in book.items():
            r = rec.get(sym) or {}
            q = M.mq(view.quotes.get(sym))
            positions.append({"sym": sym, "qty": p["qty"], "units": int(r.get("units") or 1), "entryAvg": p["avg"],
                              "lastAdd": float(r.get("lastAdd") or p["avg"]), "stop": float(r.get("stop") or 0.0),
                              "peak": float(r.get("peak") or (q["last"] if q else p["avg"])),
                              "n": float(r.get("n") or 0.0), "atr14": float(r.get("atr14") or 0.0),
                              "mark": float(r.get("mark") or p["mark"] or p["avg"])})
        quotes = {}
        for sym in set(book) | {b["sym"] for b in (sig or {}).get("bars") or []}:
            q = M.mq(view.quotes.get(sym))
            if q:
                quotes[sym] = q
        acc = Account(self.side, cash, positions, st.get("skip20"), st.get("skippedFor"), st.get("wonOn"))
        step(acc, view.now, quotes, sig, st["born"])
        close = M.et_to_epoch(view.session, 0, 0) + M.session_close_minutes(view.session) * 60
        window = max(60.0, close - view.now)
        out = []
        for o in acc.orders:
            if o["side"] == "sell":
                out.append(Intent("exit", o["sym"], price_hint=o["px"], reason=o["reason"],
                                  signal_key=f"{self.side}:{o['sym']}:{view.session}:sell",
                                  order=OrderSpec(window_s=window)))
            else:
                out.append(Intent("enter", o["sym"], qty=float(o["qty"]), price_hint=o["px"],
                                  signal_key=f"{self.side}:{o['sym']}:{view.session}:unit{o['unit']}",
                                  reason=f"{LABEL[self.side]} unit {o['unit']} (signal {sig.get('asOf') if sig else None})",
                                  order=OrderSpec(window_s=window)))
        keep = {p["sym"]: {k: p[k] for k in ("units", "lastAdd", "stop", "peak", "n", "atr14", "mark")}
                for p in acc.positions}
        for sym in M.equity_positions(view):             # an exit still working keeps its record until it fills
            if sym not in keep and sym in rec:
                keep[sym] = rec[sym]
        st["pos"] = keep
        st.update(skip20=acc.skip20, skippedFor=acc.skipped_for, wonOn=acc.won_on)
        self._st = st
        return out

    def update_state(self, view, intents):
        return self._st if self._st is not None else dict(view.state or {})


def sleeves():
    return [BoardBook(s) for s in ("turtle", "macd", "vwap")]
