"""midna_faber / midna_lc_prior_month_reversal / midna_distance_pair_shares — Midna's three Quantpedia paper books
(src/lib/equity/quantpedia.ts @ cursor/paper-desk-f184 68315288, blob 22f5f86f), each its own $100,000 account, ported
line for line (applyQuantpedia, stepFaber, stepReversal, stepPairs, buy, sell). Signals: desk/feedlib/midna_signals.py
(the vendored quantpedia-signals.py).

  act       on the regular session right after the signal session (tradingDaysAfter(asOf, today) == 1) from 10:00
            ET, and only on signals from the book's birth session on
  Faber     for each of SPY EFA BND VNQ GSG in order: sell a held fund that is not above its 10-month average (the
            mean of the ten month-end closes before the current month); buy a fund above it that is not held
  Reversal  the five worst of the 40 large caps by prior calendar-month return: a held name still in the universe but
            out of the five is sold; the five are bought while fewer than five are held
  Pairs     a held cheap leg whose pair is in today's list is sold once |z| < 0.5; for each listed pair (closest
            first) with a long leg and |z| >= 2, the long (cheaper normalized) leg is bought while fewer than five are
            held and the name is not held
  size      dollars = min(cash, equity / 5) (equity = cash + held shares x their last quote); shares =
            floor(dollars / paper price); the paper price is the ask (buy) / bid (sell) to the cent, else last -/+ the
            research cost (0.05% + 0.25% below $5, 0.10% below $20, 0.05% above)

Removed (cutover doctrine): green.ts buyBlockReason — a new long needed QQQ red, VIX up and the name red on the session
(a desk-wide red-day gate); the desk halt (state.halted, a kill switch).

Named divergences: fills are engine children at the paper price the source would have booked (the source filled
instantly); a working entry counts as held and a working exit as gone (common.virtual_book); the signal file hand-off
is the in-pass producer (desk/feedlib/midna_signals.py); quotes are the desk's (common.mq)."""
import math

from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from . import common as M

QP_NAV = 100_000.0
QP_SLOTS = 5
SOURCE = {"repo": "midna", "ref": "cursor/paper-desk-f184", "commit": "68315288cb7af1340ee1a44cf446c6a9bb3e65fa",
          "path": "src/lib/equity/quantpedia.ts", "blob": "22f5f86f42f68ecc8c1209cd87371e1d6044bcae",
          "producer": {"path": "scripts/quantpedia-signals.py", "blob": "8d2b118478ab112518af204fd79d9276fbe27882"}}
REMOVED = ["green.ts buyBlockReason: a new long needs QQQ red + VIX up + the name red (desk-wide red-day gate)",
           "state.halted (desk kill switch)"]
IDS = {"faber": "midna_faber", "reversal": "midna_lc_prior_month_reversal", "pairs": "midna_distance_pair_shares"}


def can_act(now, as_of, born_day):
    if as_of < born_day:
        return False
    if M.trading_days_after(as_of, M.et_ymd(now)) != 1:
        return False
    if M.phase_at(now) != "rth":
        return False
    return M.et_parts(now)["minutes"] >= 10 * 60


def pair_key(a, b):
    return "|".join(sorted([a, b]))


class Account:
    """the source account during one step: cash and open positions, mutated by sell / buy exactly as quantpedia.ts
    does, recording the orders the engine must place."""

    def __init__(self, cash, positions):
        self.cash = cash
        self.positions = positions          # [{"sym", "qty", "entryAvg", "mark", "pairKey"}] open, book order
        self.orders = []

    def opens(self):
        return self.positions

    def open_of(self, sym):
        return next((p for p in self.positions if p["sym"] == sym), None)

    def equity(self):
        return self.cash + M.js_sum(p["qty"] * (p["mark"] or p["entryAvg"]) for p in self.positions)

    def sell(self, position, quote, reason):
        fill = M.paper_fill(quote, "sell")
        if not fill:
            return False
        self.cash = M.round2(self.cash + position["qty"] * fill[0])
        self.positions.remove(position)
        self.orders.append({"side": "sell", "sym": position["sym"], "qty": position["qty"], "px": fill[0],
                            "reason": reason})
        return True

    def buy(self, sym, quote, pk=None):
        fill = M.paper_fill(quote, "buy")
        if not fill:
            return False
        dollars = min(self.cash, self.equity() / QP_SLOTS)
        qty = math.floor(dollars / fill[0])
        if qty < 1:
            return False
        self.cash = M.round2(self.cash - qty * fill[0])
        self.positions.append({"sym": sym, "qty": qty, "entryAvg": fill[0], "mark": quote["last"], "pairKey": pk})
        self.orders.append({"side": "buy", "sym": sym, "qty": qty, "px": fill[0], "pairKey": pk})
        return True


def step_faber(acc, quotes, signals):
    for row in signals["faber"]:
        held = acc.open_of(row["sym"])
        quote = quotes.get(row["sym"])
        if not quote:
            continue
        if not row["above"] and held:
            acc.sell(held, quote, "Below the 10-month average")
        if row["above"] and not acc.open_of(row["sym"]):
            acc.buy(row["sym"], quote)


def step_reversal(acc, quotes, signals):
    universe = {r["sym"] for r in signals["reversal"]}
    targets = [r["sym"] for r in sorted(signals["reversal"], key=lambda r: r["ret"])[:QP_SLOTS]]
    for p in list(acc.opens()):
        if p["sym"] not in universe or p["sym"] in targets:
            continue
        quote = quotes.get(p["sym"])
        if quote:
            acc.sell(p, quote, "Left the loser set")
    for sym in targets:
        if len(acc.opens()) >= QP_SLOTS or acc.open_of(sym):
            continue
        quote = quotes.get(sym)
        if quote:
            acc.buy(sym, quote)


def step_pairs(acc, quotes, signals):
    by_key = {}
    for row in signals["pairs"]:
        by_key[pair_key(row["a"], row["b"])] = row
    for p in list(acc.opens()):
        if not p.get("pairKey") or p["pairKey"] not in by_key:
            continue
        row = by_key[p["pairKey"]]
        if row and abs(row["z"]) >= 0.5:
            continue
        quote = quotes.get(p["sym"])
        if quote:
            acc.sell(p, quote, "Pair spread reverted")
    for row in signals["pairs"]:
        if not row.get("long") or abs(row["z"]) < 2:
            continue
        if len(acc.opens()) >= QP_SLOTS or acc.open_of(row["long"]):
            continue
        quote = quotes.get(row["long"])
        if quote:
            acc.buy(row["long"], quote, pair_key(row["a"], row["b"]))


STEPS = {"faber": step_faber, "reversal": step_reversal, "pairs": step_pairs}


def watch_symbols(signals):
    """quantpediaWatchSymbols (the names the pass quotes)."""
    syms = ["SPY", "EFA", "BND", "VNQ", "GSG"]
    for r in (signals or {}).get("faber") or []:
        syms.append(r["sym"])
    for r in (signals or {}).get("reversal") or []:
        syms.append(r["sym"])
    for r in (signals or {}).get("pairs") or []:
        syms += [r["a"], r["b"]]
    return syms


class QuantpediaBook(Sleeve):
    def __init__(self, side):
        self.side = side
        self.CONFIG = SleeveConfig(
            sleeve_id=IDS[side], family="midna", cadence_s=300, capital=QP_NAV, universe=(), schedule="rth",
            needs={"quotes": {"source": "equity"}, "feeds": ["midna_qp_signals"]},
            params={"book": side, "slots": QP_SLOTS, "removed_gates": REMOVED}, source=dict(SOURCE, book=side),
            state_schema={"born": "str"})
        self.engine = None
        self._st = None

    def bind(self, engine):
        self.engine = engine

    def quote_universe(self, now, book=None):
        held = [i[3:] for i in (book.positions if book else {}) if i.startswith("EQ:")]
        sig = self.engine.feeds.get("midna_qp_signals", self, now) if self.engine is not None and \
            self.engine.feeds is not None else None
        return list(dict.fromkeys(held + watch_symbols(sig)))

    def signal(self, view):
        st = dict(view.state or {})
        st.setdefault("born", view.session)
        self._st = st
        sig = view.extra.get("midna_qp_signals")
        if not sig or not sig.get("asOf"):
            return []
        if not can_act(view.now, sig["asOf"], st["born"]):
            return []
        book, cash = M.virtual_book(view)
        positions = []
        for sym, p in book.items():
            q = M.mq(view.quotes.get(sym))
            positions.append({"sym": sym, "qty": p["qty"], "entryAvg": p["avg"],
                              "mark": q["last"] if q else (p["mark"] or p["avg"]),
                              "pairKey": p["meta"].get("pairKey") or _key_pair(p.get("key"))})
        quotes = {s: M.mq(view.quotes.get(s)) for s in set(watch_symbols(sig)) | set(book)}
        acc = Account(cash, positions)
        STEPS[self.side](acc, {k: v for k, v in quotes.items() if v}, sig)
        close = M.et_to_epoch(view.session, 0, 0) + M.session_close_minutes(view.session) * 60
        window = max(60.0, close - view.now)
        out = []
        for o in acc.orders:
            key = f"{self.side}:{sig['asOf']}:{o['sym']}"
            if o["side"] == "sell":
                out.append(Intent("exit", o["sym"], price_hint=o["px"], signal_key=key + ":sell", reason=o["reason"],
                                  order=OrderSpec(window_s=window)))
            else:
                pk = o.get("pairKey")
                out.append(Intent("enter", o["sym"], qty=float(o["qty"]), price_hint=o["px"],
                                  signal_key=key + ":buy" + (f":{pk}" if pk else ""),
                                  reason=f"{self.side} signal {sig['asOf']}", order=OrderSpec(window_s=window),
                                  meta={"position_meta": {"pairKey": pk, "signal": sig["asOf"]} if pk else
                                        {"signal": sig["asOf"]}}))
        return out

    def update_state(self, view, intents):
        return self._st if self._st is not None else dict(view.state or {})


def _key_pair(key):
    """a working pairs entry carries its pair in the signal key (pairs:<asOf>:<sym>:buy:<a|b>)."""
    parts = str(key or "").split(":")
    return parts[4] if len(parts) >= 5 and parts[0] == "pairs" and parts[3] == "buy" else None


def sleeves():
    return [QuantpediaBook(s) for s in ("faber", "reversal", "pairs")]
