"""Two midna recorders converted into funded paper books (the owner's ruling D32, 2026-10-26, narrowed at 03:55 UTC to
trading strategies on bars of 1H or longer). Both run on daily bars; their rules are the source's, ported line for
line below (midna@43f08f96, vendored byte-exact under desk/vendor/midna_mon) and proved against the source under Node
(tests/test_recorder_books.py). docs/research/2026-10-26-recorders/CONVERT.md carries the source lines.

  mon_midna_weekly_8_20_50_pullback  the weekly 8/20/50 pullback's primary book: src/lib/felipe/pullback.ts runPullback
      with the options scripts/felipe-pullback.ts names primary (35: stop "week-atr", path "daily", cost 0.001, slots
      10, oversold null; 109: "a weekly ATR(5) stop, checked every day, 25 percent off at one reward unit, the rest out
      five weeks later, ten names at one tenth of equity"), over the nineteen FELIPE_ETFS.
        signal  a completed week (completedWeeks 93-98) with EMA8 > EMA20 > EMA50, close > EMA50, low <= EMA8 and
                close > low (readingSignal 607-623); entry the week's close, stop entry - weekly ATR(5), target entry +
                ATR, deadline the last session of the fifth completed week after (collectSignals 568-605);
        entry   at most ten names held, the week's signals by RSI ascending then symbol (404-415), each at a tenth of
                equity and never more than the cash (openAt 312-336);
        exit    the stop on any day, a quarter at the target the first time it is reached, the rest at the deadline
                session's close (374-402).
  mon_midna_tsmom_forms  the TSMOM study's book on this row's own panel (DIVERSIFIED, scripts/tsmom-forms.ts 22-29).
      The row recorded seven forms; the study trades them only on a stock panel that is not vendored and, on this ETF
      panel, one long-or-cash book, "etf-12-1-flat" (331-339): its primary 12-1 form. The row is converted as that
      book (the coordinator's ruling, 2026-10-26).
        signal  sign12: the adjusted close 21 sessions back over the one 252 sessions before it, minus one, > 0
                (src/lib/research/tsmom.ts 10-17, 68-70), on the panel aligned to SPY's sessions (loadPanel 231-268);
        entry / exit  every 21 sessions the book is set to equal weights over the names whose sign is positive
                (equalWeights 96-102) and the rest to cash (simulate 127-158); the weights drift in between.

Named divergences (plumbing, not rules):
  pullback
    1. fills: the source fills at the signal week's close; the book decides after that close and buys at its first
       pass of the next session (open+5); a name already at or under its stop is not bought (the source's position
       would leave at that open);
    2. the stop is held by the engine on the live mark (the source checked each day's open and low); the quarter at
       the target is sold at the book's pass once the live price reaches it (the source checked the day's high); the
       rest leaves by a market-on-close order on the deadline session;
    3. a week that does not end on a Friday is completed only once the next week begins (completedWeeks 93-98); its
       signal is then at least a session old and is not bought late;
    4. tapes: the desk's Yahoo daily bars, adjusted as the source's live board adjusts them (live.ts 93-106: OHLC times
       adjclose / close); when the provider gives no adjclose (the Nasdaq fallback), the bars as they are.
  tsmom
    1. the study rebalanced every 21 sessions from its bar file's 260th session; the book counts 21 sessions from its
       own first session;
    2. the study's weights apply from the rebalance session's close: the book sends them as market-on-close orders
       before the auction cutoff;
    3. adjusted closes are the hub's adjclose (the close when the provider gives none).
The research costs (0.1% a side, 5 bps) stay research numbers: the desk charges its own fills, as for every sleeve
(owner decision D16 pending); only openAt's sizing divides by (1 + 0.001), as the source sizes.
Removed gates: none."""
from datetime import date as _date, timedelta

from ... import calendar as cal
from ...contract import ExitRule, Intent, OrderSpec, Sleeve, SleeveConfig
from ...util import et_date
from . import midna_mon as MM

NAN = float("nan")


def _pos(x):
    return x is not None and x == x and x > 0


# == src/lib/lector/pine.ts ==========================================================================================
def ema(values, length):
    """SMA-seeded exponential average, alpha = 2 / (length + 1)."""
    out = [None] * len(values)
    if length < 1 or len(values) < length:
        return out
    s = 0.0
    for i in range(length):
        s += values[i]
    prev = s / length
    out[length - 1] = prev
    alpha = 2 / (length + 1)
    for i in range(length, len(values)):
        prev = values[i] * alpha + prev * (1 - alpha)
        out[i] = prev
    return out


def rma(values, length):
    """Wilder average. The seed is the simple average of the first `length` values."""
    out = [None] * len(values)
    if length < 1 or len(values) < length:
        return out
    s = 0.0
    for i in range(length):
        s += values[i]
    prev = s / length
    out[length - 1] = prev
    for i in range(length, len(values)):
        prev = (prev * (length - 1) + values[i]) / length
        out[i] = prev
    return out


def rsi(closes, length):
    out = [None] * len(closes)
    if length < 1 or len(closes) <= length:
        return out
    gain = loss = 0.0
    for i in range(1, length + 1):
        change = closes[i] - closes[i - 1]
        if change >= 0:
            gain += change
        else:
            loss -= change
    avg_gain, avg_loss = gain / length, loss / length

    def read(up, down):
        return 100 if down == 0 else 100 - 100 / (1 + up / down)
    out[length] = read(avg_gain, avg_loss)
    for i in range(length + 1, len(closes)):
        change = closes[i] - closes[i - 1]
        up = change if change > 0 else 0
        down = -change if change < 0 else 0
        avg_gain = (avg_gain * (length - 1) + up) / length
        avg_loss = (avg_loss * (length - 1) + down) / length
        out[i] = read(avg_gain, avg_loss)
    return out


def true_range(bars):
    out = []
    for i, bar in enumerate(bars):
        span = bar["high"] - bar["low"]
        if i == 0:
            out.append(span)
            continue
        prev = bars[i - 1]["close"]
        out.append(max(span, abs(bar["high"] - prev), abs(bar["low"] - prev)))
    return out


def atr(bars, length):
    return rma(true_range(bars), length)


# == src/lib/felipe/pullback.ts ======================================================================================
FELIPE_ETFS = MM.FELIPE_ETFS
PRIMARY = {"stop": "week-atr", "path": "daily", "cost": 0.001, "slots": 10, "oversold": None}   # felipe-pullback.ts 35


def _ymd(d):
    y, m, dd = (int(x) for x in d.split("-"))
    return _date(y, m, dd)


def week_start(d):
    day = _ymd(d)
    dow = (day.weekday() + 1) % 7                     # getUTCDay: 0 = Sunday
    offset = -6 if dow == 0 else 1 - dow
    return (day + timedelta(days=offset)).isoformat()


def weekday(d):
    return (_ymd(d).weekday() + 1) % 7


def clean_days(days):
    m = {}
    for day in days:
        if not _pos(day.get("close")) or not _pos(day.get("high")):
            continue
        op = day["open"] if _pos(day.get("open")) else day["close"]
        lo = day["low"] if _pos(day.get("low")) else min(op, day["close"])
        m[day["date"]] = {"date": day["date"], "open": op, "high": max(day["high"], op, day["close"], lo),
                          "low": min(lo, op, day["close"]), "close": day["close"]}
    return [m[k] for k in sorted(m)]


def to_weeks(days):
    groups = {}
    for day in days:
        key = week_start(day["date"])
        ex = groups.get(key)
        if ex is None:
            groups[key] = {"date": day["date"], "open": day["open"], "high": day["high"], "low": day["low"],
                           "close": day["close"]}
            continue
        ex["high"] = max(ex["high"], day["high"])
        ex["low"] = min(ex["low"], day["low"])
        ex["close"] = day["close"]
        ex["date"] = day["date"]
    return sorted(groups.values(), key=lambda w: w["date"])


def completed_weeks(days):
    """drops the unfinished week at the end of the file (a week whose last session is not a Friday)."""
    weeks = to_weeks(clean_days(days))
    if weeks and weekday(weeks[-1]["date"]) != 5:
        weeks.pop()
    return weeks


def reading_signal(week, e8, e20, e50, osc, oversold):
    if e8 is None or e20 is None or e50 is None:
        return None
    if oversold is not None and (osc is None or not (osc <= oversold)):
        return None
    if not (e8 > e20 and e20 > e50):
        return None
    if not (week["close"] > e50):
        return None
    if not (week["low"] <= e8):
        return None
    if not (week["close"] > week["low"]):
        return None
    risk = week["close"] - week["low"]
    return {"date": week["date"], "entry": week["close"], "stop": week["low"], "target": week["close"] + risk,
            "rsi": osc if osc is not None else 50}


def pullback_signals(weeks, oversold=40):
    if len(weeks) < 60:
        return []
    closes = [w["close"] for w in weeks]
    fast, mid, slow, strength = ema(closes, 8), ema(closes, 20), ema(closes, 50), rsi(closes, 14)
    out = []
    for i in range(50, len(weeks)):
        sig = reading_signal(weeks[i], fast[i], mid[i], slow[i], strength[i], oversold)
        if sig:
            out.append(sig)
    return out


def collect_signals(tapes, oversold, stop_mode):
    out = []
    for sym, days in tapes.items():
        weeks = completed_weeks(days)
        weekly_atr = atr(weeks, 5)
        daily_at = None
        if stop_mode == "day-atr":
            da = atr(days, 5)
            daily_at = {day["date"]: da[i] for i, day in enumerate(days)}
        idx = {w["date"]: i for i, w in reversed(list(enumerate(weeks)))}     # findIndex: the first match
        for sig in pullback_signals(weeks, oversold):
            index = idx.get(sig["date"], -1)
            if index < 0:
                continue
            stop, target = sig["stop"], sig["target"]
            if stop_mode == "week-atr":
                width = weekly_atr[index]
                if width is None or not (width > 0):
                    continue
                stop, target = sig["entry"] - width, sig["entry"] + width
            elif stop_mode == "day-atr":
                width = (daily_at or {}).get(sig["date"])
                if width is None or not (width > 0):
                    continue
                stop, target = sig["entry"] - width, sig["entry"] + width
            if not (sig["entry"] > stop) or not (target > sig["entry"]):
                continue
            out.append({"sym": sym, "date": sig["date"], "rsi": sig["rsi"], "entry": sig["entry"], "stop": stop,
                        "target": target, "deadline": weeks[index + 5]["date"] if index + 5 < len(weeks) else ""})
    return out


def _lagged_prices(signal, op, stop_mode):
    if not (op > 0):
        return None
    if stop_mode == "week-low":
        stop = signal["stop"]
        if not (op > stop):
            return {"entry": op, "stop": stop, "target": op}
        return {"entry": op, "stop": stop, "target": op + (op - stop)}
    width = signal["entry"] - signal["stop"]
    if not (width > 0):
        return None
    return {"entry": op, "stop": op - width, "target": op + width}


def run_pullback(tapes, options=None):
    """runPullback 205-433 (trips, the positions open at the end, fired, taken): the source's own fills, for the
    parity proof of this port; the book below trades the same rules at live prices."""
    o = options or {}
    slots = o.get("slots", 10)
    weight = o.get("weight", 1 / slots)
    cost = o.get("cost", 0.001)
    partial_frac = o.get("partial", 0.25)
    stop_mode = o.get("stop", "week-atr")
    path = o.get("path", "daily")
    entry_from, entry_to = o.get("entryFrom", "0000-01-01"), o.get("entryTo", "9999-12-31")
    curve_from, curve_to = o.get("curveFrom", entry_from), o.get("curveTo")
    entry_lag, allow_lev = o.get("entryLag", False), o.get("allowLeverage", False)
    oversold = o["oversold"] if "oversold" in o else 40
    cleaned = {sym: clean_days(days) for sym, days in tapes.items()}
    signals = [s for s in collect_signals(cleaned, oversold, stop_mode) if entry_from <= s["date"] < entry_to]
    by_date = {}
    for s in signals:
        by_date.setdefault(s["date"], []).append(s)
    lookup = {}
    for sym, days in cleaned.items():
        weeks = completed_weeks(days)
        bars = weeks if path == "weekly" else days
        lookup[sym] = (bars, {b["date"]: b for b in bars})
    lag_by_date = {}
    if entry_lag:
        for sym, (bars, _m) in lookup.items():
            nxt = {bars[i]["date"]: bars[i + 1]["date"] for i in range(len(bars) - 1)}
            for s in signals:
                if s["sym"] != sym:
                    continue
                fill = nxt.get(s["date"])
                if fill:
                    lag_by_date.setdefault(fill, []).append(s)
    clock = sorted({b["date"] for bars, _m in lookup.values() for b in bars if b["date"] >= curve_from})
    positions, trips = [], []
    state = {"cash": 1.0, "taken": 0}

    def equity_now():
        v = state["cash"]
        for p in positions:
            v += p["remaining"] * p["notional"] * (p["last"] / p["entry"])
        return v

    def finish(p, px, exit_date, stopped):
        piece = p["remaining"] * p["notional"] * (px / p["entry"])
        p["grossOut"] += piece
        fill = piece * (1 - cost)
        p["got"] += fill
        state["cash"] += fill
        paid = p["notional"] * (1 + cost)
        multiple = 1 if p["notional"] == 0 else p["grossOut"] / p["notional"]
        trips.append({"sym": p["sym"], "entryDate": p["entryDate"], "exitDate": exit_date,
                      "ret": 0 if paid == 0 else p["got"] / paid - 1,
                      "r": 0 if p["risk"] == 0 else (multiple - 1) * p["entry"] / p["risk"], "stopped": stopped,
                      "partial": p["partial"]})

    def open_at(s, entry, stop, target, entry_date, active_after):
        eq = equity_now()
        wanted = eq * weight
        budget = wanted if allow_lev else min(wanted, max(state["cash"], 0))
        if not (budget > 0) or not (entry > stop) or not (target > entry):
            return
        notional = budget / (1 + cost)
        state["cash"] -= budget
        state["taken"] += 1
        positions.append({"sym": s["sym"], "entry": entry, "stop": stop, "target": target, "entryDate": entry_date,
                          "activeAfter": active_after, "deadline": s["deadline"], "notional": notional,
                          "remaining": 1, "partial": False, "got": 0, "grossOut": 0, "last": entry,
                          "risk": entry - stop})

    for d in clock:
        past = curve_to is not None and d >= curve_to
        if past and not positions:
            break
        if entry_lag and not past:
            for s in lag_by_date.get(d, []):
                if any(p["sym"] == s["sym"] for p in positions):
                    continue
                bar = lookup.get(s["sym"], ([], {}))[1].get(d)
                if not bar:
                    continue
                placed = _lagged_prices(s, bar["open"], stop_mode)
                if not placed:
                    continue
                if not (bar["open"] > placed["stop"]):
                    eq = equity_now()
                    wanted = eq * weight
                    budget = wanted if allow_lev else min(wanted, max(state["cash"], 0))
                    if not (budget > 0):
                        continue
                    notional = budget / (1 + cost)
                    got = notional * (1 - cost)
                    state["cash"] += got - budget
                    state["taken"] += 1
                    trips.append({"sym": s["sym"], "entryDate": d, "exitDate": d, "ret": got / budget - 1, "r": 0,
                                  "stopped": True, "partial": False})
                    continue
                open_at(s, placed["entry"], placed["stop"], placed["target"], d, s["date"])
        for i in range(len(positions) - 1, -1, -1):
            p = positions[i]
            bar = lookup.get(p["sym"], ([], {}))[1].get(d)
            if not bar or bar["date"] <= p["activeAfter"]:
                continue
            p["last"] = bar["close"]
            if bar["open"] <= p["stop"]:
                finish(p, bar["open"], bar["date"], True)
                positions.pop(i)
                continue
            if bar["low"] <= p["stop"]:
                finish(p, p["stop"], bar["date"], True)
                positions.pop(i)
                continue
            if not p["partial"] and partial_frac > 0 and bar["high"] >= p["target"]:
                piece = partial_frac * p["notional"] * (p["target"] / p["entry"])
                p["grossOut"] += piece
                fill = piece * (1 - cost)
                p["got"] += fill
                state["cash"] += fill
                p["remaining"] -= partial_frac
                p["partial"] = True
            if p["deadline"] and bar["date"] >= p["deadline"]:
                finish(p, bar["close"], bar["date"], False)
                positions.pop(i)
        if not entry_lag and not past and entry_from <= d < entry_to:
            room = slots - len(positions)
            if room > 0:
                cands = sorted((s for s in by_date.get(d, []) if not any(p["sym"] == s["sym"] for p in positions)),
                               key=lambda s: (s["rsi"], s["sym"]))
                for s in cands[:room]:
                    entry = s["entry"] if s.get("entry") is not None else \
                        (lookup.get(s["sym"], ([], {}))[1].get(d) or {}).get("close")
                    if entry is None:
                        continue
                    open_at(s, entry, s["stop"], s["target"], d, d)
        if past and not positions:
            break
    opened = [{"sym": p["sym"], "entryDate": p["entryDate"],
               "ret": (0 if p["notional"] * (1 + cost) == 0 else
                       (p["got"] + p["remaining"] * p["notional"] * (p["last"] / p["entry"])) / (p["notional"] * (1 + cost)) - 1)}
              for p in positions]
    return {"trips": trips, "open": opened, "fired": len(signals), "taken": state["taken"]}


def adjusted_days(rows):
    """the hub's daily bars -> the source's Day rows, adjusted as live.ts fetchDaily adjusts them (93-106): OHLC times
    adjclose / close; the bars as they are when the provider gives no adjclose."""
    out = {}
    for b in rows or []:
        c, ac = b.get("c"), b.get("ac")
        if not _pos(c):
            continue
        f = (ac / c) if _pos(ac) else 1.0
        adj = c * f if _pos(ac) else c
        op = (b.get("o") if b.get("o") is not None else c) * f
        hi = (b.get("h") if b.get("h") is not None else c) * f
        lo = (b.get("l") if b.get("l") is not None else c) * f
        out[et_date(b["t"])] = {"date": et_date(b["t"]), "open": op, "high": max(hi, op, adj, lo),
                                "low": min(lo, op, adj), "close": adj}
    return [out[k] for k in sorted(out)]


def deadline_of(signal_date):
    """weeks[index + 5].date: the last session of the fifth week with sessions after the signal's week."""
    d, n = _ymd(week_start(signal_date)), 0
    while n < 5:
        d += timedelta(days=7)
        if any(cal.is_trading_day(d + timedelta(days=k)) for k in range(5)):
            n += 1
    return cal.week_last_session(d).isoformat()


# == scripts/tsmom-forms.ts / src/lib/research/tsmom.ts ==============================================================
DIVERSIFIED = MM.DIVERSIFIED


def trailing_return(adj, end, lookback):
    start = end - lookback
    if start < 0 or end < 0:
        return None
    now, past = adj[end] if end < len(adj) else NAN, adj[start]
    if not _pos(now) or not _pos(past):
        return None
    return now / past - 1


def sign12(adj, index):
    r = trailing_return(adj, index - 21, 252)
    return r is not None and r > 0


def panel(rows_by_sym):
    """loadPanel 231-268 on the hub's completed daily bars: SPY's sessions are the panel's dates, each name's adjusted
    closes aligned to them (NaN where a session is missing), a name kept with >= 260 valid sessions."""
    def rows(bl):
        return [(et_date(b["t"]), b.get("ac") if _pos(b.get("ac")) else b.get("c"), b.get("c")) for b in bl or []]
    spy = rows(rows_by_sym.get("SPY"))
    if len(spy) < 260:
        return [], {}
    dates = [r[0] for r in spy]
    at = {d: i for i, d in enumerate(dates)}
    out = {}
    for sym, bl in rows_by_sym.items():
        rr = rows(bl)
        if len(rr) < 260:
            continue
        adj, valid = [NAN] * len(dates), 0
        for d, a, c in rr:
            i = at.get(d)
            if i is None or not _pos(a) or not _pos(c):
                continue
            adj[i] = a
            valid += 1
        if valid >= 260:
            out[sym] = adj
    return dates, out


# == the books ========================================================================================================
REPO = dict(MM.REPO)


def _held(view):
    return {inst.split(":", 1)[1]: float(p.get("qty") or 0) for inst, p in (view.positions or {}).items()
            if inst.startswith("EQ:") and abs(float(p.get("qty") or 0)) > 1e-12}


def _working(view):
    return {str(o.get("inst") or "").split(":", 1)[-1] for o in (view.extra or {}).get("pending_orders") or []}


def _stored(sleeve):
    try:
        return sleeve.engine.store.sleeve_get(sleeve.CONFIG.sleeve_id) or {} if sleeve.engine is not None else {}
    except Exception:
        return {}


MOC = OrderSpec(type="market", tif="cls", window_s=3600)


class PullbackBook(Sleeve):
    """the weekly 8/20/50 pullback's primary book (see the module docstring)."""
    SLOTS, WEIGHT, COST, PARTIAL = 10, 0.1, 0.001, 0.25

    def __init__(self):
        self.CONFIG = SleeveConfig(
            sleeve_id="mon_midna_weekly_8_20_50_pullback", family="monitor", cadence_s=300, universe=FELIPE_ETFS,
            schedule="rth&open+5:open+400,!close-40:close-15,after_close+20:after_close+300",
            needs={"bars": [{"source": "yahoo", "interval": "1d", "n": 1600, "symbols_for": "after_close"}],
                   "quotes": {"source": "equity"}},
            params={"book": "runPullback primary (felipe-pullback.ts 35)", "slots": 10, "weight": 0.1,
                    "partial": 0.25, "stop": "week-atr", "path": "daily"},
            source=dict(REPO, path="src/lib/felipe/pullback.ts", blob_sha="da620bd787610653ccb4b3b46ba46e828a3b6944",
                        line_start=1, line_end=674))
        self.engine = None
        self._st = None

    def bind(self, engine):
        self.engine = engine

    @staticmethod
    def _after_close(now):
        d = cal._as_date(now)
        return cal.is_trading_day(d) and now >= cal.session_close(d)

    def bar_symbols(self, spec, now, book=None):
        """the daily tapes only on the evening's deciding passes (none in the session, none once decided)."""
        if not self._after_close(now) or _stored(self).get("decided") == et_date(now):
            return []
        return list(self.CONFIG.universe)

    def quote_universe(self, now, book=None):
        st = _stored(self)
        names = set((st.get("pos") or {}))
        todo = st.get("todo") or {}
        if todo.get("for") == et_date(now):
            names |= {r["sym"] for r in todo.get("rows") or [] if not r.get("sent")}
        return sorted(names)

    def signal(self, view):
        st = dict(view.state or {})
        st["pos"] = {k: dict(v) for k, v in (st.get("pos") or {}).items()}
        held, working = _held(view), _working(view)
        for s in list(st["pos"]):                      # a position the engine's stop (or anything) closed
            if s not in held and s not in working:
                del st["pos"][s]
        out = []
        day = et_date(view.now)
        if self._after_close(view.now) and st.get("decided") != day:
            out += self._decide(view, st, day, held)
        if cal.is_rth(view.now):
            out += self._send(view, st, day, held, working)
        self._st = st
        return out

    def _decide(self, view, st, day, held):
        tapes = {s: adjusted_days((view.bars.get("1d") or {}).get(s)) for s in self.CONFIG.universe}
        if not any(t and t[-1]["date"] == day for t in tapes.values()):
            return []                                  # the session's bars are not final yet: decided next pass
        st["decided"] = day
        weeks = [completed_weeks(t) for t in tapes.values() if t]
        weeks_end = [w[-1]["date"] for w in weeks if w]
        if not weeks_end or max(weeks_end) != day:
            return []                                  # no week completed with this session (divergence 3)
        sigs = [s for s in collect_signals({k: v for k, v in tapes.items() if v}, PRIMARY["oversold"], "week-atr")
                if s["date"] == day]
        room = self.SLOTS - len(st["pos"])
        cands = sorted((s for s in sigs if s["sym"] not in st["pos"] and s["sym"] not in held),
                       key=lambda s: (s["rsi"], s["sym"]))
        rows = [dict(s, deadline=deadline_of(s["date"])) for s in cands[:max(room, 0)]]
        st["todo"] = {"for": cal.next_trading_day(day).isoformat(), "rows": rows}
        return [Intent("signal", "PULLBACK", reason=("weekly pullback %s: %s" % (day, ", ".join(
            "%s rsi %.1f" % (s["sym"], s["rsi"]) for s in sorted(sigs, key=lambda s: (s["rsi"], s["sym"]))) or "none"))[:300],
            signal_key="pullback:%s" % day, meta={"signals": [{k: s[k] for k in ("sym", "rsi", "entry", "stop", "target")}
                                                          for s in sigs], "taken": [r["sym"] for r in rows]})]

    def _send(self, view, st, day, held, working):
        out = []
        q = view.quotes or {}
        todo = st.get("todo") or {}
        if todo.get("for") == day:
            cash = float(view.cash)
            for r in todo.get("rows") or []:
                if r.get("sent") or r["sym"] in held or r["sym"] in st["pos"]:
                    continue
                px = float((q.get(r["sym"]) or {}).get("last") or 0)
                if not (px > 0):
                    continue
                r["sent"] = True
                if px <= r["stop"]:
                    r["skipped"] = "at or under its stop at the open (divergence 1)"
                    continue
                budget = min(float(view.equity) * self.WEIGHT, max(cash, 0.0))
                if not (budget > 0):
                    continue
                cash -= budget
                st["pos"][r["sym"]] = {k: r[k] for k in ("date", "entry", "stop", "target", "deadline", "rsi")}
                st["pos"][r["sym"]].update(partial=False, qty0=None, entered=day)
                out.append(Intent("enter", r["sym"], notional=budget / (1 + self.COST), price_hint=px,
                                  exit_rules=(ExitRule("stop", r["stop"]),),
                                  signal_key="%s:%s:%s:buy" % (self.CONFIG.sleeve_id, r["sym"], r["date"]),
                                  reason=("weekly pullback %s: entry %.4f stop %.4f target %.4f, out %s" % (
                                      r["date"], r["entry"], r["stop"], r["target"], r["deadline"]))[:300],
                                  meta={"signal": r["date"], "stop": r["stop"], "target": r["target"],
                                        "deadline": r["deadline"]}))
        close_window = (cal.minutes_to_close(view.now) or 999) <= 40
        for s, p in st["pos"].items():
            if s not in held:
                continue
            if p.get("qty0") is None:
                p["qty0"] = held[s]
            px = float((q.get(s) or {}).get("last") or 0)
            if p["deadline"] and day >= p["deadline"] and close_window:
                if p.get("out") != day:
                    p["out"] = day
                    out.append(Intent("exit", s, order=MOC, signal_key="%s:%s:%s:deadline" % (
                        self.CONFIG.sleeve_id, s, p["date"]), reason="weekly pullback %s: the deadline %s, out at the "
                                                                    "close" % (p["date"], p["deadline"])))
                continue
            if not p["partial"] and px > 0 and px >= p["target"]:
                p["partial"] = True
                out.append(Intent("exit", s, qty=self.PARTIAL * p["qty0"], signal_key="%s:%s:%s:partial" % (
                    self.CONFIG.sleeve_id, s, p["date"]), reason="weekly pullback %s: a quarter at the target %.4f" % (
                    p["date"], p["target"])))
        return out

    def update_state(self, view, intents):
        st, self._st = self._st, None
        return st if st is not None else dict(view.state or {})


class TsmomBook(Sleeve):
    """the TSMOM study's ETF book, etf-12-1-flat (see the module docstring)."""
    EVERY = 21

    def __init__(self):
        self.CONFIG = SleeveConfig(
            sleeve_id="mon_midna_tsmom_forms", family="monitor", cadence_s=300, universe=DIVERSIFIED,
            schedule="rth&close-40:close-15",
            needs={"bars": [{"source": "yahoo", "interval": "1d", "n": 600, "symbols_for": "rebalance"}],
                   "quotes": {"source": "equity"}},
            params={"book": "etf-12-1-flat (tsmom-forms.ts 331-339)", "every": 21, "form": "primary-12-1",
                    "converted_as": "the study's ETF 12-1 book: its primary form on this row's panel"},
            source=dict(REPO, path="scripts/tsmom-forms.ts", blob_sha="64445a687634142efdd9bae5b4b393fb4663dfff",
                        line_start=331, line_end=339))
        self.engine = None
        self._st = None

    def bind(self, engine):
        self.engine = engine

    def _due(self, now, st):
        day = et_date(now)
        if not cal.is_trading_day(day) or st.get("rebalanced") == day:
            return False
        anchor = st.get("anchor") or day
        return cal.trading_days_between(anchor, day) % self.EVERY == 0

    def bar_symbols(self, spec, now, book=None):
        return list(self.CONFIG.universe) if self._due(now, _stored(self)) else []

    def quote_universe(self, now, book=None):
        st = _stored(self)
        if not self._due(now, st):
            return []
        held = {i.split(":", 1)[1] for i in ((book.positions if book is not None else {}) or {}) if i.startswith("EQ:")}
        return sorted(set(self.CONFIG.universe) | held)

    def longs(self, rows_by_sym, day):
        """the names whose 12-1 sign is positive at the rebalance session `day` (index = its place after the newest
        completed session), in DIVERSIFIED order."""
        dates, adj = panel(rows_by_sym)
        if not dates or dates[-1] >= day:
            return None
        index = len(dates)
        return [s for s in DIVERSIFIED if s in adj and sign12(adj[s], index)]

    def signal(self, view):
        st = dict(view.state or {})
        day = et_date(view.now)
        st.setdefault("anchor", day)
        if not self._due(view.now, st) or not cal.is_rth(view.now):
            self._st = st
            return []
        bars = {s: [b for b in bl if et_date(b["t"]) < day] for s, bl in (view.bars.get("1d") or {}).items()}
        longs = self.longs(bars, day)
        if longs is None:
            self._st = st
            return []                                  # no completed panel: the next pass tries again
        st["rebalanced"], st["longs"] = day, longs
        held = _held(view)
        out = [Intent("signal", "TSMOM", reason=("tsmom 12-1 %s: long %s" % (day, " ".join(longs) or "none"))[:300],
                      signal_key="tsmom:%s" % day, meta={"longs": longs})]
        w = 1.0 / len(longs) if longs else 0.0
        q = view.quotes or {}
        for s in longs:
            px = (q.get(s) or {}).get("last") or (q.get(s) or {}).get("ask")
            out.append(Intent("target", s, weight=w, price_hint=float(px) if px else None, order=MOC,
                              signal_key="%s:%s:%s" % (self.CONFIG.sleeve_id, s, day),
                              reason="tsmom 12-1 %s: 1/%d of the book" % (day, len(longs))))
        for s in sorted(set(held) - set(longs)):
            out.append(Intent("exit", s, order=MOC, signal_key="%s:%s:%s:cash" % (self.CONFIG.sleeve_id, s, day),
                              reason="tsmom 12-1 %s: sign not positive, to cash" % day))
        self._st = st
        return out

    def update_state(self, view, intents):
        st, self._st = self._st, None
        return st if st is not None else dict(view.state or {})


BOOKS = {"mon_midna_weekly_8_20_50_pullback": PullbackBook, "mon_midna_tsmom_forms": TsmomBook}
