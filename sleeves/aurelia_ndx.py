"""Aurelia NDX book — lean-desk port (Wave D, Decision #119 family).

EXTRACTED from the old desk's aurelia_paper.py + aurelia_allocate.py
(source: Agentic-Trading-Desk aurelia-paper-desk 1720157f768e). One of the
two traded Aurelia book sleeves on signal aurelia-gc-band20-v1, held as
QQQ + TQQQ (QQQ + 3xTQQQ == Nasdaq exposure, capital used <= 100% NAV),
idle weight >= 2% in BIL.

SIZING BASIS (AURELIA-EXEC, 2026-10-18): the old sleeve sized on its
own flat $500,000 sim book (aurelia_paper_book.jsonl) and filled
there. On the lean desk that basis was a defect (desk audit V-04):
the sleeve executes at the real broker, so targets now size off
context.equity — the broker-refreshed account equity the dispatcher
injects, the basis every other sleeve on the desk uses. No equity
basis (0 / unreadable) -> the sleeve is inert. Holdings arrive as
context.extra["sleeve_state"] ({symbol: {"qty": n}}). The core
Broker serves fills; the private sim book does NOT come over.

Inputs via context.extra:
  "exposures": {"ndx": raw_signal, "gold": raw_signal} (required;
  supplied by core.book_feeds from the aurelia-gc-band20-v1
  producer, core/aurelia_signal.py)
  "book": {"ndx": prior_book_exposure, "gold": prior} (band state)
  "posture_cap": float | None (caps the Nasdaq book, as on the old desk)
  "sleeve_state": {"QQQ": {"qty": n}, ...}
Bars: daily dicts {"t","o","h","l","c","v"} for QQQ/TQQQ/GLD/BIL; the
last close is the plan price (the old desk's completed prices).
Shadows (gestalt, n6, broken_hedge, variance_value) were record-only on
the old desk and created no orders; they stay core/Ledger records here.
"""
import math

from core.sleeve import BaseSleeve, Intent, SleeveConfig

SIGNAL_ID = "aurelia-gc-band20-v1"
ACCOUNT = "aurelia_ndx"
SYMBOLS = ("QQQ", "TQQQ", "GLD", "BIL")
OWN_SYMBOLS = ("QQQ", "TQQQ", "BIL")  # GLD deltas belong to aurelia_gold
EXPOSURE_BAND = 0.20
GROSS_CAP = 1.80
NDX_CAP = 3.0
MIN_WEIGHT = 0.02

CONFIG = SleeveConfig(
    sleeve_id="aurelia_ndx", cadence_s=300, universe=SYMBOLS,
    state_schema={"position": "dict|None"}, risk_pct=None)


# --- aurelia_allocate.py, verbatim -------------------------------------
def _capital(ndx, gold):
    return (ndx if ndx <= 1.0 else 1.0) + gold


def cap_exposures(ndx, gold, gross_cap=GROSS_CAP):
    ndx = min(max(float(ndx), 0.0), NDX_CAP)
    gold = max(float(gold), 0.0)
    if _capital(ndx, gold) <= gross_cap:
        return ndx, gold
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2.0
        if _capital(ndx * mid, gold * mid) <= gross_cap:
            lo = mid
        else:
            hi = mid
    return ndx * lo, gold * lo


def sleeve_weights(ndx, gold):
    ndx, gold = cap_exposures(ndx, gold)
    if ndx <= 1.0:
        weights = {"QQQ": ndx, "TQQQ": 0.0}
        used = ndx
    else:
        tqqq = (ndx - 1.0) / 2.0
        weights = {"QQQ": 1.0 - tqqq, "TQQQ": tqqq}
        used = 1.0
    weights["GLD"] = gold
    used += gold
    cash = max(0.0, 1.0 - used)
    weights["BIL"] = cash if cash >= MIN_WEIGHT else 0.0
    return {k: round(v, 6) for k, v in weights.items() if v > 1e-8}


def ndx_exposure(weights):
    return weights.get("QQQ", 0.0) + 3.0 * weights.get("TQQQ", 0.0)


def share_targets(weights, equity, prices):
    out = {}
    for symbol, weight in weights.items():
        px = prices.get(symbol)
        if not px or px <= 0 or weight <= 0:
            continue
        qty = int(equity * weight / px)
        if qty > 0:
            out[symbol] = qty
    return out


def fit_to_buying_power(orders, prices, buying_power, buffer=0.95):
    """aurelia_common.fit_to_buying_power, verbatim (RR3 item 2,
    2026-10-15): the old Aurelia executor fitted every plan through
    this bound (aurelia_paper.build_plan) — the port dropped it
    (ports/aurelia_ndx.md M1) and on 2026-10-15 the sleeve submitted
    BUY 5463 BIL (~$500k) against $87,468 buying power (broker 403).
    Sells untouched; buys scaled proportionally to 95% of buying
    power; buys dropped entirely when there is no room."""
    sells = [dict(o) for o in orders if o["side"] == "sell"]
    buys = [dict(o) for o in orders if o["side"] == "buy"]
    other = [dict(o) for o in orders if o["side"] not in ("buy", "sell")]
    buy_notional = sum(o["qty"] * float(prices.get(o["symbol"]) or 0.0) for o in buys)
    room = max(0.0, float(buying_power)) * buffer
    if buy_notional <= room or buy_notional <= 0:
        return sells + buys + other, False
    if room <= 0:
        return sells + other, True
    scale = room / buy_notional
    scaled = []
    for order in buys:
        qty = int(order["qty"] * scale)
        if qty > 0:
            scaled.append({**order, "qty": qty})
    return sells + scaled + other, True


def order_deltas(targets, held, prices, equity, band=MIN_WEIGHT):
    """Verbatim: a new name always trades; an existing name trades only
    when its weight moves by `band` (2%)."""
    orders = []
    symbols = set(targets) | {s for s, q in held.items() if q}
    for symbol in sorted(symbols):
        have = int(held.get(symbol, 0))
        want = int(targets.get(symbol, 0))
        px = prices.get(symbol) or 0.0
        if have and px and equity:
            if abs(want - have) * px / equity < band:
                continue
        delta = want - have
        if delta == 0:
            continue
        orders.append({"symbol": symbol, "side": "buy" if delta > 0 else "sell",
                       "qty": abs(delta)})
    return orders


# --- aurelia_common.resolve_book, verbatim ------------------------------
def resolve_book(signal, book):
    """Exposure the book keeps until the signal moves by 0.20, or leaves zero."""
    try:
        signal = float(signal)
    except (TypeError, ValueError):
        signal = 0.0
    if not math.isfinite(signal):
        signal = 0.0
    signal = max(0.0, signal)
    try:
        held = 0.0 if book is None else float(book)
    except (TypeError, ValueError):
        held = 0.0
    if not math.isfinite(held):
        held = 0.0
    held = max(0.0, held)
    if signal == 0.0 and held > 0.0:
        return 0.0
    if abs(signal - held) >= EXPOSURE_BAND - 1e-12:
        return signal
    return held


def _safe_float(value, default):
    """float() that never raises: junk input takes the fail-closed
    default instead of crashing the whole signal tick."""
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def plan_targets(exp, book, posture_cap, prices, held, equity):
    """The old build_plan core: band-resolve both books, weights, targets.
    `equity` is the sizing basis (context.equity — AURELIA-EXEC)."""
    # resolve_book IS the sanitizer (verbatim aurelia_common: non-float /
    # non-finite signals become 0.0). Pre-converting with float() here
    # defeated it — a None exposure raised TypeError and killed the tick.
    book_ndx = resolve_book(exp["ndx"], (book or {}).get("ndx"))
    book_gold = resolve_book(exp["gold"], (book or {}).get("gold"))
    if posture_cap is not None:
        # An unreadable cap caps to zero (fail closed), never uncapped.
        book_ndx = min(book_ndx, _safe_float(posture_cap, 0.0))
    weights = sleeve_weights(book_ndx, book_gold)
    targets = share_targets(weights, equity, prices)
    return book_ndx, book_gold, weights, targets


class AureliaNdx(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        exp = extra.get("exposures")
        if not isinstance(exp, dict) or "ndx" not in exp or "gold" not in exp:
            return []  # fail closed: exposures are the decision input
        # AURELIA-EXEC: the sizing basis is the broker-refreshed
        # account equity on the context (dispatcher's basis for every
        # sleeve). Absent/unreadable -> inert, never a fallback book.
        equity = _safe_float(getattr(context, "equity", 0.0), 0.0)
        if equity <= 0:
            return []
        state = extra.get("sleeve_state") or {}
        held = {}
        for s in SYMBOLS:
            row = state.get(s) or {}
            q = row.get("qty") if isinstance(row, dict) else None
            if q:
                held[s] = int(q)
        prices = {}
        for s in SYMBOLS:
            bl = bars.get(s) or []
            if bl:
                px = _safe_float(bl[-1].get("c"), 0.0)
                if px > 0:
                    prices[s] = px  # non-finite / non-positive close = no price
        if not prices:
            return []
        book_ndx, book_gold, weights, targets = plan_targets(
            exp, extra.get("book"), extra.get("posture_cap"), prices, held,
            equity)
        orders = order_deltas(targets, {s: q for s, q in held.items() if s in SYMBOLS},
                              prices, equity)
        bp_scaled = False
        if extra.get("buying_power") is not None:
            # Restored old-executor bound (see fit_to_buying_power).
            # Absent key = the old run()'s buying_power=None case:
            # no fit, exactly as ported.
            orders, bp_scaled = fit_to_buying_power(
                orders, prices, _safe_float(extra["buying_power"], 0.0))
        intents = []
        for o in orders:
            if o["symbol"] not in OWN_SYMBOLS:
                continue
            if o["symbol"] not in prices:
                # Held (or targeted) with no bar this tick: an intent
                # cannot be priced, and indexing prices[] raised
                # KeyError — killing every other intent in the tick,
                # valid exits included. Skip the unpriceable order
                # only; it re-presents when its bar returns.
                continue
            px = round(float(prices[o["symbol"]]), 2)
            if o["side"] == "buy":
                intents.append(Intent(
                    "enter", o["symbol"], qty_hint=o["qty"], price_hint=px,
                    reason="aurelia_ndx rebalance (account=%s book_ndx=%.4f "
                           "achieved=%.4f signal=%s%s)" % (
                               ACCOUNT, book_ndx, ndx_exposure(weights), SIGNAL_ID,
                               " bp_fit=scaled95" if bp_scaled else "")))
            else:
                intents.append(Intent(
                    "exit", o["symbol"], qty_hint=o["qty"], price_hint=px,
                    reason="aurelia_ndx rebalance down (account=%s book_ndx=%.4f "
                           "signal=%s)" % (ACCOUNT, book_ndx, SIGNAL_ID)))
        # ENH: first-evaluation-per-session freeze (see block below).
        _journal = _aurelia_ndx_journal(extra)
        _emitted = set(_journal.get("emitted_sessions") or []) \
            | _EMITTED_SESSIONS
        _record = {"exp_id": EXP_ID_AURELIA_NDX,
                   "session": context.session,
                   "control_intents": len(intents),
                   "treatment_intents": len(intents)}
        if _aurelia_ndx_enh_enabled(extra) \
                and context.session in _emitted:
            _record["treatment_intents"] = 0
            _record["treatment"] = "refused_repeat_session_eval"
            if isinstance(_journal.get("records"), list):
                _journal["records"].append(_record)
            self.last_evaluation = {
                "sleeve": "aurelia_ndx",
                "aurelia_ndx_exp_journal": _journal}
            return []
        _record["treatment"] = "emit_first_session_eval"
        if isinstance(_journal.get("records"), list):
            _journal["records"].append(_record)
        if context.session not in _journal["emitted_sessions"]:
            _journal["emitted_sessions"].append(context.session)
        _EMITTED_SESSIONS.add(context.session)
        self.last_evaluation = {
            "sleeve": "aurelia_ndx",
            "aurelia_ndx_exp_journal": _journal}
        return intents


def signal(bars, slice_state, context):
    return AureliaNdx().signal(bars, slice_state, context)


# --- ENH 2026-10-24 (Edge IMPROVE-aurelia_ndx, Group A DEDUCED) --------
# Emit rebalance deltas only on the sleeve's first evaluation of each
# session; later same-session evaluations emit nothing (the signal is
# daily; intraday band crossings are price drift, not signal). Switch:
# extra["aurelia_ndx_improve"] {"first_eval_only": bool}, default ON;
# OFF restores the pre-change every-tick rule exactly. Emitted sessions
# ride the exp journal (extra["aurelia_ndx_exp_journal"], pilot
# round-trip idiom, also stamped on self.last_evaluation); paired
# records go to its "records" list when served.
EXP_ID_AURELIA_NDX = "ENH-AURELIA-NDX-20261024"
_EMITTED_SESSIONS = set()


def _aurelia_ndx_enh_enabled(extra):
    ov = (extra or {}).get("aurelia_ndx_improve")
    if isinstance(ov, dict) and "first_eval_only" in ov:
        return bool(ov["first_eval_only"])
    return True


def _aurelia_ndx_journal(extra):
    j = (extra or {}).get("aurelia_ndx_exp_journal")
    if isinstance(j, dict):
        j.setdefault("emitted_sessions", [])
        j.setdefault("records", [])
        return j
    return {"emitted_sessions": [], "records": []}
