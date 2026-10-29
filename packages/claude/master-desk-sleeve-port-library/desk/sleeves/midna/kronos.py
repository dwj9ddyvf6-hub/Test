"""midna_kronos_topk — Midna's Kronos-base TopkDropout shadow (src/lib/equity/kronos.ts @ cursor/paper-desk-f184
68315288, blob 62dd754a: applyKronos, kronosTargets, tradingDaysAfter, takeShares, sell), ported line for line, its own
$100,000 book, on the Kronos-base forecast of desk/feedlib/midna_kronos.py (the kronos-forecast.py port).

  universe  the frozen 24 names (8 October reconstruction)
  signal    the forecast's scores (the ten-session forecast close / the last close - 1), rebuilt every ten sessions
  act       on a regular session 1..10 sessions after the signal session, from 10:00 ET; never on a forecast from
            before the book's birth day
  targets   once per signal: Qlib TopkDropout (top 4, drop 1, minimum hold 5 sessions): the worst held name (by
            score) that has been held >= 5 sessions and is not in today's top 5 is dropped (at most one), then the
            best names fill the book back to 4; a name held < 5 sessions stays even past 4
  trade     sells first (every held name not targeted, at last x (1 - 0.1%) to the cent); a missing quote holds the
            buys back until the sale can be made; buys: slice = 95% of equity / max(names, 4), qty = floor(min(slice,
            cash) / (last x (1 + 0.1%) to the cent)); a buy that cannot fill is retried each pass of the window

Removed (cutover doctrine): green.ts buyBlockReason on every buy (QQQ red AND VIX up AND the name red — the
desk-wide red-day gate) and state.halted (the desk kill switch).

Named divergences: fills are engine children at the source's paper prices (last -/+ 0.1%), a working order counts
as done (common.virtual_book); the forecast hand-off (kronos-forecast.json) is the producer job's cache; the
forecast's daily bars are read through the desk's data hub by that job (kronos-forecast.py fetched Yahoo's chart
itself; the hub's yahoo source serves the same chart OHLCV under the shared rate budget, and Nasdaq's same
split-adjusted OHLCV while Yahoo refuses)."""
import math

from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from . import common as M

SOURCE = {"repo": "midna", "ref": "cursor/paper-desk-f184", "commit": "68315288cb7af1340ee1a44cf446c6a9bb3e65fa",
          "path": "src/lib/equity/kronos.ts", "blob": "62dd754a276bd1abf7bfe31100b21ef0907fcd3e",
          "producer": {"path": "scripts/kronos-forecast.py", "blob": "f44b3aef8b40ff4b75274c805c3d2ec926b7f73f",
                       "model": "NeoQuasar/Kronos-base@2b554741eca47781b64468546e77fef3e85130e6"}}
UNIVERSE = ("ABBV", "ABNB", "ADI", "AMZN", "AON", "AXP", "CHWY", "COST", "CRWD", "DIS", "DKNG", "FCX", "MCK", "MO",
            "ORCL", "PEP", "PM", "PYPL", "SBUX", "SMCI", "TMO", "TSLA", "WFC", "ZS")
NAV = 100_000.0
TOPK, DROP, MIN_HOLD = 4, 1, 5
RISK, COST, HORIZON = 0.95, 0.001, 10
REMOVED = ["green.ts buyBlockReason on every buy: QQQ red + VIX up + the name red (desk-wide red-day gate)",
           "state.halted (desk kill switch)"]


def kronos_targets(scores, held):
    """kronosTargets: scores [{sym, score}], held [{sym, held}] -> the target list (kept first, then buys)."""
    ranked = sorted([r for r in scores if isinstance(r.get("score"), (int, float)) and math.isfinite(r["score"])],
                    key=lambda r: (-r["score"], M.locale_key(r["sym"])))
    today = {r["sym"] for r in ranked[:TOPK + DROP]}
    score_of = {r["sym"]: r["score"] for r in ranked}
    sessions = {h["sym"]: h["held"] for h in held}
    worst = sorted([h["sym"] for h in held], key=lambda s: (score_of.get(s, -math.inf), M.locale_key(s)))
    sell = []
    for sym in worst:
        if (sessions.get(sym) or 0) < MIN_HOLD:
            continue
        if sym in today:
            continue
        sell.append(sym)
        if len(sell) >= DROP:
            break
    kept = [h["sym"] for h in held if h["sym"] not in sell]
    need = max(0, TOPK - len(kept))
    buy = []
    for r in ranked:
        if len(buy) >= need:
            break
        if r["sym"] in kept:
            continue
        buy.append(r["sym"])
    return kept + buy


def can_fill(now, signal_day):
    after = M.trading_days_after(signal_day, M.et_ymd(now))
    if after < 1 or after > HORIZON:
        return False
    if M.phase_at(now) != "rth":
        return False
    return M.et_parts(now)["minutes"] >= 10 * 60


def apply(book, now, quotes, forecast):
    """applyKronos without the removed gates. book = {"cash", "positions": [{sym, qty, entryAvg, entryDay, mark}],
    "bornDay", "signalDay", "appliedDay", "targets", "pending"} (mutated). -> orders."""
    orders = []
    for p in book["positions"]:                             # markBook
        q = quotes.get(p["sym"])
        if q and q["last"] > 0:
            p["mark"] = q["last"]
    if not forecast or forecast.get("status") != "ready" or not forecast.get("signalDay") or not forecast.get("scores"):
        return orders
    if forecast["signalDay"] < book["bornDay"]:
        return orders
    if not can_fill(now, forecast["signalDay"]):
        return orders
    as_of = forecast["signalDay"]
    if book.get("appliedDay") != forecast["signalDay"] or not book.get("targets"):
        held = [{"sym": p["sym"], "held": M.trading_days_after(p["entryDay"], as_of)} for p in book["positions"]]
        book["targets"] = kronos_targets(forecast["scores"], held)
        book["signalDay"] = book["appliedDay"] = forecast["signalDay"]
        book["pending"] = []
    targets = set(book["targets"])
    waiting = []
    for p in list(book["positions"]):
        if p["sym"] in targets:
            continue
        q = quotes.get(p["sym"])
        if not q or not (q["last"] > 0):
            waiting.append(p["sym"])
            continue
        px = M.round2(q["last"] * (1 - COST))
        book["cash"] = M.round2(book["cash"] + p["qty"] * px)
        book["positions"].remove(p)
        orders.append({"side": "sell", "sym": p["sym"], "qty": p["qty"], "px": px})
    if waiting:
        book["pending"] = [s for s in book["targets"] if not any(p["sym"] == s for p in book["positions"])]
        return orders
    equity = book["cash"] + M.js_sum(p["qty"] * (p.get("mark") or p["entryAvg"]) for p in book["positions"])
    buy_list = [s for s in book["targets"] if not any(p["sym"] == s for p in book["positions"])]
    slots = len(buy_list) + len(book["positions"])
    slice_ = (equity * RISK) / max(slots, TOPK) if slots > 0 else 0
    still = []
    for sym in buy_list:
        if sym not in UNIVERSE:
            continue
        q = quotes.get(sym)
        if not q or not (q["last"] > 0):
            still.append(sym)
            continue
        px = M.round2(q["last"] * (1 + COST))
        qty = math.floor(min(slice_, book["cash"]) / px) if px > 0 else 0
        if not (px > 0) or qty < 1:
            still.append(sym)
            continue
        book["cash"] = M.round2(book["cash"] - qty * px)
        book["positions"].append({"sym": sym, "qty": qty, "entryAvg": px, "entryDay": M.et_ymd(now), "mark": q["last"]})
        orders.append({"side": "buy", "sym": sym, "qty": qty, "px": px})
    book["pending"] = still
    return orders


class KronosTopk(Sleeve):
    def __init__(self):
        self.CONFIG = SleeveConfig(
            sleeve_id="midna_kronos_topk", family="midna", cadence_s=300, capital=NAV, universe=UNIVERSE,
            schedule="always", needs={"quotes": {"source": "equity", "symbols": list(UNIVERSE)},
                                      "feeds": ["midna_kronos_forecast"]},
            params={"topk": TOPK, "drop": DROP, "min_hold": MIN_HOLD, "risk": RISK, "cost": COST, "horizon": HORIZON,
                    "removed_gates": REMOVED}, source=SOURCE,
            state_schema={"bornDay": "str", "signalDay": "str|None", "appliedDay": "str|None", "targets": "list|None",
                          "pending": "list", "pos": "dict"})
        self.engine = None
        self._st = None

    def bind(self, engine):
        self.engine = engine

    def signal(self, view):
        st = dict(view.state or {})
        st.setdefault("bornDay", M.et_ymd(view.now))
        vb, cash = M.virtual_book(view)
        rec = dict(st.get("pos") or {})
        positions = []
        for sym, p in vb.items():
            r = rec.get(sym) or p["meta"] or {}
            positions.append({"sym": sym, "qty": p["qty"], "entryAvg": r.get("entryAvg") or p["avg"],
                              "entryDay": r.get("entryDay") or M.et_ymd(p.get("opened_at") or view.now),
                              "mark": p.get("mark")})
        quotes = {s: M.mq(view.quotes.get(s)) for s in set(UNIVERSE) | {p["sym"] for p in positions}}
        book = {"cash": cash, "positions": positions, "bornDay": st["bornDay"], "signalDay": st.get("signalDay"),
                "appliedDay": st.get("appliedDay"), "targets": st.get("targets"), "pending": st.get("pending") or []}
        orders = apply(book, view.now, {k: v for k, v in quotes.items() if v}, view.extra.get("midna_kronos_forecast"))
        close = M.et_to_epoch(view.session, 0, 0) + M.session_close_minutes(view.session) * 60
        window = max(60.0, close - view.now)
        out = []
        for o in orders:
            if o["side"] == "sell":
                out.append(Intent("exit", o["sym"], price_hint=o["px"], reason="Kronos top-4 replacement",
                                  signal_key=f"kronos:{book['signalDay']}:{o['sym']}:sell", order=OrderSpec(window_s=window)))
            else:
                out.append(Intent("enter", o["sym"], qty=float(o["qty"]), price_hint=o["px"],
                                  reason=f"Kronos top-4 from the {book['signalDay']} forecast",
                                  signal_key=f"kronos:{book['signalDay']}:{o['sym']}:buy", order=OrderSpec(window_s=window),
                                  meta={"position_meta": {"entryDay": M.et_ymd(view.now), "entryAvg": o["px"]}}))
        keep = {p["sym"]: {"entryDay": p["entryDay"], "entryAvg": p["entryAvg"]} for p in book["positions"]}
        for sym in M.equity_positions(view):
            if sym not in keep and sym in rec:
                keep[sym] = rec[sym]
        st.update(signalDay=book["signalDay"], appliedDay=book["appliedDay"], targets=book["targets"],
                  pending=book["pending"], pos=keep)
        self._st = st
        return out

    def update_state(self, view, intents):
        return self._st if self._st is not None else dict(view.state or {})
