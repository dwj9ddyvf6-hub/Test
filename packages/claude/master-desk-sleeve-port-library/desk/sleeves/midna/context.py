"""midna_liquid_126_momentum — Midna's context book (src/lib/equity/context.ts @ cursor/paper-desk-f184 68315288, blob
f4158077), ported line for line: rankContext, the 63-session review, workFor / applyWork / setQty.

  rank      liquid names of the swing basket (close >= $5, adj > 0, mean close x volume of the last 20 sessions with
            >= 15 valid >= $1M; SOXL excluded) ranked by the adjusted 126-session return (retN: the nearest positive
            adjusted close up to 3 sessions back at either end); top floor(10%) (min 1) when >= 10 names are liquid
  staging   on a fresh panel (asOf = the last completed session) the rank is staged when 63 panel sessions have
            passed since the last staging (the first staging at birth); `applied` is cleared
  review    regular hours from 10:00 ET on a fresh panel, until applied: equal dollars = equity / len(target);
            positions outside the target are closed, target names are set to floor(dollars / (px x (1 + cost bps)))
            shares (px = the quoted ask/bid to the cent, else last on the cost schedule: 5 bps ETFs, 10 bps >= $20,
            25 bps >= $5, 50 bps below); every quote must be fresh (<= 15 min, <= 1 min ahead) or the review waits;
            sells and trims first, then buys, each buy capped by the cash left (affordable shares at px x (1 + bps));
            applied once nothing is missed (a target name with a quote, affordable at one share, left at zero)
  exit      the rank: a name leaves at the next review it is not in

Removed (cutover doctrine; not this book's own rules):
  * green.ts buyBlockReason (QQQ red AND VIX up AND the name red on the session, else the buy waits) — a desk-wide
    red-day gate applied to every Midna book;
  * shockFreeze (VIX > 32, VIX +25% on the day, SPY 20-session return < -8% with VIX rising) and newRiskBlock
    (Friday from 14:00 ET, the last five sessions of the year, the FOMC session and the session before) — the
    desk's shared volatility / calendar risk gates;
  * the desk halt (state.halted) — a kill switch;
  * applyRuin, the 40% adverse circuit breaker (a fresh print 40% through the entry closes the name) — a circuit
    breaker; the lab cell this book is ("liquid names, 126 sessions, skip 0, top 10%, every 63") had no stop.

Named divergences:
  1. fills: Midna filled instantly at its own paper price (setQty at quotedFill's price); here each review row is a
     `target` (or exit) child at the same reference price, filled by the engine; the share counts are the source's.
  2. cash: the buy cap reads the sleeve's cash plus the proceeds of the sells this review sends first (the source had
     already booked them); equity = cash + quantity x the quote's last (markPositions), else the book mark.
  3. a review row whose child ends unfilled is sent again on a later pass (the OMS attempt n+1); the source re-ran the
     whole review while a name stayed missed (re-sizing every row to the then-equal weight).
  4. the retired combo / carry sleeves (closed by the source when found open) hold nothing here.
  5. the panel: desk/feedlib/midna_panel.py (its own named divergences)."""
import math

from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from . import common as M

RULE_ID = "context-2"
NAV = 100_000.0
CSMOM_WEIGHT = 1
CSMOM_EVERY = 63
MIN_LIQUID_NAMES = 10
COMBO_NAMES = ("SPY", "IWM", "GLD", "TLT", "BTC-USD")
NOT_A_STOCK = {"SOXL"}
SOURCE = {"repo": "midna", "ref": "cursor/paper-desk-f184", "commit": "68315288cb7af1340ee1a44cf446c6a9bb3e65fa",
          "path": "src/lib/equity/context.ts", "blob": "f4158077ec2a390eb6d95a01d143bf338e0a6deb"}
REMOVED = ["green.ts buyBlockReason: QQQ red + VIX up + name red on the session (desk-wide red-day gate)",
           "shockFreeze: VIX > 32 / VIX +25% day / SPY 20d < -8% with VIX rising (desk risk gate)",
           "newRiskBlock: Friday >= 14:00 ET, last five sessions of the year, FOMC session and the one before",
           "state.halted (desk kill switch)",
           "applyRuin: 40% adverse circuit breaker"]


def _g(series, i, key):
    if series is None or i < 0 or i >= len(series):
        return 0.0
    v = series[i].get(key)
    return float(v) if v is not None else 0.0


def ret_n(series, i, n):
    if not series or i < 0 or i - n < 0:
        return None
    now = _g(series, i, "adj")
    past = _g(series, i - n, "adj")
    if not now > 0:
        for k in (1, 2, 3):
            if _g(series, i - k, "adj") > 0:
                now = _g(series, i - k, "adj")
                break
    if not past > 0:
        for k in (1, 2, 3):
            j = i - n - k
            if j >= 0 and _g(series, j, "adj") > 0:
                past = _g(series, j, "adj")
                break
    if not past > 0 or not now > 0:
        return None
    return now / past - 1


def dv20(series, i):
    if i < 19:
        return None
    s, n = 0.0, 0
    for k in range(i - 19, i + 1):
        c, v = _g(series, k, "close"), _g(series, k, "volume")
        if c > 0 and v > 0:
            s += c * v
            n += 1
    if n < 15:
        return None
    return s / n


def depth_n(series, i, n):
    if i - n + 1 < 0:
        return None
    hi, count = -math.inf, 0
    for k in range(i - n + 1, i + 1):
        h = _g(series, k, "high")
        if h > 0:
            hi = max(hi, h)
            count += 1
    if count < n * 0.8:
        return None
    close = _g(series, i, "close")
    if not hi > 0 or not close > 0:
        return None
    return (1 - close / hi) * 100


def liquid(series, i):
    price = _g(series, i, "close")
    if not price >= 5 or not _g(series, i, "adj") > 0:
        return False
    d = dv20(series, i)
    return d is not None and d >= 1_000_000


def flag_for(near_high, predeclared):
    if predeclared and near_high:
        return "Also in the 252-day top fifth. Within 5% of the high, and still held."
    if predeclared:
        return "Also in the 252-day top fifth, the pre-declared rule that beat random books on liquid names."
    if near_high:
        return "Within 5% of the 252-session high. Still held. The near-high filter is a separate rule."
    return "126-day book."


def _js_sort_desc(rows):
    """b.score - a.score || a.sym.localeCompare(b.sym) (symbols are ASCII tickers: ordinal compare)."""
    return sorted(rows, key=lambda r: (-r["score"], r["sym"]))


def rank_context(panel):
    clock = panel["clock"]
    i = len(clock) - 1
    empty = {"csmom": [], "combo": [], "eligible": 0, "overlap": 0, "spy20": None, "spy126": None}
    if i < 0:
        return empty
    spy = panel["series"].get("SPY")
    spy20 = ret_n(spy, i, 20) if spy else None
    spy126 = ret_n(spy, i, 126) if spy else None
    rows, pre_rows = [], []
    for sym in panel["universe"]:
        if sym in NOT_A_STOCK:
            continue
        series = panel["series"].get(sym)
        if not series or not liquid(series, i):
            continue
        pre = ret_n(series, i - 21, 252)
        if pre is not None:
            pre_rows.append({"sym": sym, "score": pre})
        score = ret_n(series, i, 126)
        if score is None:
            continue
        deep = depth_n(series, i, 252)
        rows.append({"sym": sym, "score": score, "nearHigh": deep is not None and deep < 5, "predeclared": False})
    pre_rows = _js_sort_desc(pre_rows)
    pre_count = max(1, math.floor(len(pre_rows) * 0.2))
    pre_set = {r["sym"] for r in pre_rows[:pre_count]}
    for r in rows:
        r["predeclared"] = r["sym"] in pre_set
    combo = [s for s in COMBO_NAMES if (lambda v: v is not None and v > 0)(ret_n(panel["series"].get(s) or [], i, 126))]
    if len(rows) < MIN_LIQUID_NAMES:
        return {"csmom": [], "combo": combo, "eligible": len(rows), "overlap": 0, "spy20": spy20, "spy126": spy126}
    rows = _js_sort_desc(rows)
    count = max(1, math.floor(len(rows) * 0.1))
    picked = rows[:count]
    return {"csmom": [{"sym": r["sym"], "score": r["score"], "flag": flag_for(r["nearHigh"], r["predeclared"])}
                      for r in picked],
            "combo": combo, "eligible": len(rows), "overlap": sum(1 for r in picked if r["predeclared"]),
            "spy20": spy20, "spy126": spy126}


def panel_stale(panel, now):
    completed = M.last_completed_session(now)
    return (not panel) or panel["asOf"] != completed or (panel["clock"][-1] if panel["clock"] else None) != panel["asOf"]


def fill_ok(now):
    p = M.et_parts(now)
    return M.phase_at(now) == "rth" and p["minutes"] >= 10 * 60


def desired_qty(dollars, px, sym, schedule=True):
    if not dollars > 0 or not px > 0:
        return 0
    bps = M.context_cost_bps(sym, px) / 10_000 if schedule else 0
    q = math.floor(dollars / (px * (1 + bps)))
    return q if q >= 1 else 0


def stage(state, panel, ranked, now):
    """the staging step of advanceContext: (target, set_on, applied) after this pass."""
    target, set_on, applied = state.get("target") or [], state.get("set_on"), bool(state.get("applied"))
    if panel and ranked is not None and not panel_stale(panel, now):
        if M.sessions_since(panel["clock"], set_on, panel["asOf"]) >= CSMOM_EVERY:
            return list(ranked["csmom"]), panel["asOf"], False
    return target, set_on, applied


def plan_review(held, cash, target, quotes, now):
    """workFor + applyWork + setQty for the csmom sleeve, without the removed gates.
    held: {sym: {"qty", "mark"}} in book order; quotes: {sym: Midna quote}. -> {"rows", "incomplete", "missed",
    "equity", "cash"} where rows = [{"sym", "cur", "qty", "px", "schedule"}] in execution order (qty = the shares the
    row ends at) and cash = the book's cash once they are done at their prices (setQty)."""
    equity = cash + M.js_sum(float(p["qty"]) * float(p["mark"]) for p in held.values())
    each = (equity * CSMOM_WEIGHT) / len(target) if target else 0.0
    wanted = {r["sym"] for r in target}
    work, incomplete = [], False
    for sym, p in held.items():
        if sym in wanted:
            continue
        q = quotes.get(sym)
        if not M.quote_is_fresh(q, now):
            incomplete = True
            continue
        px, sch = M.priced(q, "buy" if float(p["qty"]) < 0 else "sell")
        work.append({"sym": sym, "qty": 0, "px": px, "schedule": sch})
    for r in target:
        q = quotes.get(r["sym"])
        if not M.quote_is_fresh(q, now):
            incomplete = True
            continue
        px, sch = M.priced(q, "buy")
        work.append({"sym": r["sym"], "qty": desired_qty(each, px, r["sym"], sch), "px": px, "schedule": sch})
    if incomplete:
        return {"rows": [], "incomplete": True, "missed": True, "equity": equity, "cash": cash}
    cur = {s: float(p["qty"]) for s, p in held.items()}

    def klass(w):
        c = cur.get(w["sym"], 0.0)
        return 0 if (w["qty"] == 0 or abs(w["qty"]) < abs(c)) else (1 if w["qty"] < 0 else 2)
    ordered = sorted(work, key=klass)                    # Array.prototype.sort is stable
    rows = []
    for w in ordered:
        c = cur.get(w["sym"], 0.0)
        if c == w["qty"]:
            continue
        nxt = w["qty"]
        delta = nxt - c
        bps = M.context_cost_bps(w["sym"], w["px"]) / 10_000 if w["schedule"] else 0
        if delta > 0:
            affordable = math.floor(cash / (w["px"] * (1 + bps)))
            if affordable < delta:
                nxt = c + max(0, affordable)
            delta = nxt - c
            if delta <= 0:
                continue
        cost = abs(delta) * w["px"] * bps
        cash = M.round2(cash - delta * w["px"] - cost)
        cur[w["sym"]] = nxt
        rows.append({"sym": w["sym"], "cur": c, "qty": nxt, "px": w["px"], "schedule": w["schedule"]})
    missed = False
    for r in target:
        q = quotes.get(r["sym"])
        if not q or not (q.get("last") or 0) > 0:
            missed = True
            break
        if each < q["last"]:
            continue
        if cur.get(r["sym"], 0.0) < 1:
            missed = True
            break
    return {"rows": rows, "incomplete": False, "missed": missed, "equity": equity, "cash": cash}


class LiquidMomentum(Sleeve):
    def __init__(self):
        self.CONFIG = SleeveConfig(
            sleeve_id="midna_liquid_126_momentum", family="midna", cadence_s=300, capital=NAV,
            universe=(), schedule="always",
            needs={"quotes": {"source": "equity"}, "feeds": ["midna_panel"]},
            params={"rule_id": RULE_ID, "every": CSMOM_EVERY, "top": 0.1, "min_liquid": MIN_LIQUID_NAMES,
                    "removed_gates": REMOVED},
            source=dict(SOURCE), state_schema={"target": "list", "set_on": "str|None", "applied": "bool"})
        self._st = None
        self.engine = None

    def bind(self, engine):
        self.engine = engine

    def quote_universe(self, now, book=None):
        """context.ts quoteSymbolsFor: open names, the staged target, and the fresh rank while a review is due."""
        held = [i[3:] for i in (book.positions if book else {}) if i.startswith("EQ:")]
        st, panel = {}, None
        if self.engine is not None:
            st = self.engine.store.sleeve_get(self.CONFIG.sleeve_id) or {}
            if self.engine.feeds is not None:
                panel = self.engine.feeds.get("midna_panel", self, now)
        syms = held + [r["sym"] for r in st.get("target") or []]
        if panel and panel.get("clock"):
            due = not st.get("applied") or M.sessions_since(panel["clock"], st.get("set_on"), panel["asOf"]) >= CSMOM_EVERY
            if due or st.get("set_on") is None:
                syms += [r["sym"] for r in rank_context(panel)["csmom"]]
        return list(dict.fromkeys(syms))

    def signal(self, view):
        st = dict(view.state or {})
        panel = view.extra.get("midna_panel")
        now = view.now
        ranked = rank_context(panel) if panel and panel.get("clock") else None
        target, set_on, applied = stage(st, panel, ranked, now)
        st.update(target=target, set_on=set_on, applied=applied)
        intents = []
        stale = panel_stale(panel, now)
        if fill_ok(now) and panel and not stale and not applied:
            held = {}
            for sym, p in M.equity_positions(view).items():
                q = M.mq(view.quotes.get(sym))
                mark = q["last"] if q else (p.get("mark") or p["avg"])
                held[sym] = {"qty": float(p["qty"]), "mark": float(mark)}
            quotes = {s: M.mq(view.quotes.get(s)) for s in set(held) | {r["sym"] for r in target}}
            plan = plan_review(held, float(view.cash), target, quotes, now)
            if not plan["incomplete"]:
                for r in plan["rows"]:
                    key = f"csmom:{set_on}:{r['sym']}"
                    if r["qty"] == 0:
                        intents.append(Intent("exit", r["sym"], price_hint=r["px"], signal_key=key + ":out",
                                              reason="63-session rank review", order=OrderSpec(window_s=3600)))
                    else:
                        intents.append(Intent("target", r["sym"], qty=float(r["qty"]), price_hint=r["px"],
                                              signal_key=key, reason=f"63-session rank review {set_on}",
                                              order=OrderSpec(window_s=3600),
                                              meta={"position_meta": {"set_on": set_on}}))
                if not target or not plan["missed"]:
                    st["applied"] = True
        self._st = st
        return intents

    def update_state(self, view, intents):
        return self._st if self._st is not None else dict(view.state or {})
