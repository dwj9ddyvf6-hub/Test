"""Midna runtime helpers, ported line for line from the Midna TypeScript desk (dwj9ddyvf6-hub/midna):

  src/lib/equity/rules.ts     etParts, addDays, isTradingDay, sessionCloseMinutes, nextTradingDay, phaseAt,
                              quoteIsFresh, researchCostPct, quotedFill, paperFill, round2, isoWeek
  src/lib/equity/context.ts   contextCostBps, lastCompletedSession, prevTradingDay, sessionsSince
  src/lib/equity/kronos.ts    tradingDaysAfter
  src/lib/equity/forward.ts   sessionsAfter, tradingGap, mondayKey, weekJustClosed, nextTradingDay

JavaScript number semantics are kept where they decide an order: Math.round rounds half toward +infinity
(js_round), Math.floor, IEEE doubles, string comparison of YYYY-MM-DD dates.

Named divergence (calendar): rules.ts carries the 2026 NYSE table only (HOLIDAYS, EARLY_CLOSE); these helpers read the
desk calendar (desk/calendar.py). Both agree on every 2026 date (tests/test_midna.py); after 2026 the source table
would have counted the 2027 holidays as sessions.

Named divergence (quotes): Midna priced from its own Yahoo chart quote (regularMarketPrice / regularMarketTime, bid and
ask rarely present); the engine supplies the desk quote (Alpaca IEX snapshot when keyed: bid, ask, last trade,
previous close; Yahoo otherwise). The source rules read that quote unchanged (mq)."""
import math
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from ... import calendar as cal

ET = ZoneInfo("America/New_York")
QUOTE_FRESH_MS = 15 * 60_000
ETF_COST = frozenset(["SPY", "IWM", "GLD", "TLT", "BTC-USD", "HYG", "IEF"])   # context.ts ETF (COMBO + carry legs)


# -- JavaScript number semantics --------------------------------------------------------------------------------
def js_round(x):
    """Math.round: the nearest integer, a tie toward +infinity."""
    r = math.floor(x)
    return r + 1 if x - r >= 0.5 else r


def round2(n):
    """rules.ts round2: Math.round(n * 100) / 100."""
    return js_round(n * 100) / 100


def js_sum(values, start=0.0):
    """Array.prototype.reduce((s, v) => s + v, start): plain left-to-right double addition (Python's sum() of floats
    is compensated since 3.12 and can differ in the last bit)."""
    s = start
    for v in values:
        s = s + v
    return s


def js_num(x):
    """String(x) for the numbers the reason texts print (an integral double prints without '.0')."""
    if x is None:
        return "null"
    x = float(x)
    if math.isfinite(x) and x == int(x) and abs(x) < 1e21:
        return str(int(x))
    return repr(x)


def locale_key(s):
    """String.prototype.localeCompare order (ICU root collation) for ticker symbols: punctuation (. - ^) before
    digits before letters, letters case-insensitively first — the code-point order of upper-case tickers, '^' moved
    before the digits."""
    return [(0 if c in "^" else 1, c.upper(), c) for c in str(s)]


def finite(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return False
    return math.isfinite(v)


def pos(x):
    """value > 0 as a float, else None (positive() in rules.ts)."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


# -- the Eastern clock and the session calendar ----------------------------------------------------------------
def et_parts(now):
    t = datetime.fromtimestamp(float(now), tz=ET)
    return {"ymd": t.date().isoformat(), "year": t.year, "month": t.month, "day": t.day, "hour": t.hour,
            "minute": t.minute, "weekday": (t.weekday() + 1) % 7, "minutes": t.hour * 60 + t.minute}


def et_ymd(now):
    return datetime.fromtimestamp(float(now), tz=ET).date().isoformat()


def et_to_epoch(ymd, hour, minute, second=0):
    d = date.fromisoformat(ymd)
    return datetime(d.year, d.month, d.day, hour, minute, second, tzinfo=ET).timestamp()


def add_days(ymd, n):
    return (date.fromisoformat(ymd) + timedelta(days=n)).isoformat()


def is_trading_day(ymd):
    return cal.is_trading_day(date.fromisoformat(ymd))


def session_close_minutes(ymd):
    return cal.close_minutes(date.fromisoformat(ymd))


def next_trading_day(ymd):
    cursor = add_days(ymd, 1)
    while not is_trading_day(cursor):
        cursor = add_days(cursor, 1)
    return cursor


def prev_trading_day(ymd):
    cursor = add_days(ymd, -1)
    while not is_trading_day(cursor):
        cursor = add_days(cursor, -1)
    return cursor


def phase_at(now):
    p = et_parts(now)
    if not is_trading_day(p["ymd"]):
        return "closed"
    close = session_close_minutes(p["ymd"])
    m = p["minutes"]
    if 9 * 60 + 20 <= m < 9 * 60 + 30:
        return "preopen"
    if 9 * 60 + 30 <= m < close:
        return "rth"
    return "after"


def last_completed_session(now):
    p = et_parts(now)
    ymd = p["ymd"]
    if not is_trading_day(ymd) or p["minutes"] < session_close_minutes(ymd):
        ymd = add_days(ymd, -1)
        while not is_trading_day(ymd):
            ymd = add_days(ymd, -1)
    return ymd


def trading_days_after(frm, to):
    """kronos.ts tradingDaysAfter: trading days in (from, to]."""
    if to < frm:
        return 0
    count, cursor = 0, add_days(frm, 1)
    while cursor <= to:
        if is_trading_day(cursor):
            count += 1
        cursor = add_days(cursor, 1)
    return count


def sessions_after(frm, to):
    """forward.ts sessionsAfter: trading sessions strictly after `from`, through `to` (counting stops at 400)."""
    if to <= frm:
        return 0
    count, cursor = 0, frm
    while cursor < to and count < 400:
        cursor = add_days(cursor, 1)
        if cursor <= to and is_trading_day(cursor):
            count += 1
    return count


def trading_gap(frm, to):
    """forward.ts tradingGap: sessions in (from, to], counting stops at 8."""
    if to <= frm:
        return 0
    count, cursor = 0, frm
    while cursor < to and count < 8:
        cursor = add_days(cursor, 1)
        if is_trading_day(cursor):
            count += 1
    return count


def sessions_since(clock, frm, to):
    """context.ts sessionsSince: index distance on the panel clock (infinity when either day is missing)."""
    if not frm:
        return math.inf
    try:
        return clock.index(to) - clock.index(frm)
    except ValueError:
        return math.inf


def monday_key(ymd):
    d = date.fromisoformat(ymd)
    return (d - timedelta(days=d.weekday())).isoformat()


def week_just_closed(ymd):
    """forward.ts weekJustClosed: the Monday-start week ends with this session."""
    return monday_key(ymd) != monday_key(next_trading_day(ymd))


def calendar_days(frm, to):
    return (date.fromisoformat(to) - date.fromisoformat(frm)).days


def iso_week(ymd):
    """rules.ts isoWeek: 'YYYY-Www'."""
    y, w, _ = date.fromisoformat(ymd).isocalendar()
    return f"{y}-W{w:02d}"


# -- quotes and paper prices -----------------------------------------------------------------------------------
def mq(q):
    """the desk quote {bid, ask, last, prev_close, t} as Midna's Quote {last, bid, ask, previousClose, timeMs};
    None without a positive last (every Midna rule requires quote.last > 0)."""
    if not q:
        return None
    last = pos(q.get("last"))
    if last is None:
        return None
    t = q.get("t")
    return {"last": last, "bid": q.get("bid"), "ask": q.get("ask"), "previousClose": q.get("prev_close"),
            "timeMs": float(t) * 1000.0 if t is not None else None}


def quote_is_fresh(quote, now):
    """rules.ts quoteIsFresh: last > 0 and a quote clock under 15 minutes old and not more than a minute ahead."""
    if not quote or not (quote.get("last") or 0) > 0 or quote.get("timeMs") is None:
        return False
    age = float(now) * 1000.0 - float(quote["timeMs"])
    return -60_000 <= age <= QUOTE_FRESH_MS


def research_cost_pct(px):
    base = 0.25 if px < 5 else 0.1 if px < 20 else 0.05
    return 0.05 + base


def quoted_fill(quote, side):
    """rules.ts quotedFill: the ask (buy) / bid (sell) when quoted and the book is not crossed, else last on the
    cost schedule. -> (price, schedule) | None"""
    last = quote.get("last") or 0
    if not last > 0:
        return None
    b, a = quote.get("bid"), quote.get("ask")
    crossed = b is not None and a is not None and b > a
    bid = b if (not crossed and b is not None and b > 0) else None
    ask = a if (not crossed and a is not None and a > 0) else None
    if side == "buy" and ask is not None:
        return float(ask), False
    if side == "sell" and bid is not None:
        return float(bid), False
    return float(last), True


def paper_fill(quote, side):
    """rules.ts paperFill: the quoted side to the cent, else last +/- the research cost. -> (price, how) | None"""
    quoted = quoted_fill(quote, side)
    if quoted is None:
        return None
    price, schedule = quoted
    if not schedule:
        p = round2(price)
        return (p, "bid-ask") if p > 0 else None
    last = float(quote["last"])
    slip = research_cost_pct(last) / 100
    raw = last * (1 + slip) if side == "buy" else last * (1 - slip)
    p = round2(raw)
    return (p, "schedule") if p > 0 else None


def context_cost_bps(sym, price):
    if sym in ETF_COST:
        return 5
    if price >= 20:
        return 10
    if price >= 5:
        return 25
    return 50


def priced(quote, side):
    """context.ts priced / forward.ts orderPx: quotedFill to the cent, else last (schedule)."""
    f = quoted_fill(quote, side)
    if f is None:
        return round2(quote["last"]), True
    return round2(f[0]), f[1]


# -- the engine view, read the way the Midna books read their own state ---------------------------------------
def equity_positions(view):
    """{SYM: {qty, avg, opened_at, meta, mark}} — this sleeve's long and short share positions."""
    out = {}
    for inst, p in (view.positions or {}).items():
        if inst.startswith("EQ:") and abs(float(p.get("qty") or 0.0)) > 1e-9:
            out[inst[3:]] = p
    return out


def pending_by_sym(view, action=None):
    """{SYM: [pending child, ...]} for this sleeve's working equity orders (optionally one action)."""
    out = {}
    for p in view.extra.get("pending_orders", []) or []:
        if not str(p.get("inst", "")).startswith("EQ:"):
            continue
        if action and p.get("action") != action:
            continue
        out.setdefault(p["inst"][3:], []).append(p)
    return out


def quotes_of(view, syms):
    return {s: mq(view.quotes.get(s)) for s in syms}


def virtual_book(view):
    """this sleeve's share book as the source's instant-fill book would hold it: the filled positions, plus every
    working entry at its reference price, less every working exit (Named divergence: the source booked its paper
    fill at once; here an order is a child the engine fills later, so a working child counts as done).
    -> ({SYM: {"qty", "avg", "mark", "meta", "opened_at", "pending", "key"}}, cash)"""
    book, cash = {}, float(view.cash)
    for sym, p in equity_positions(view).items():
        book[sym] = {"qty": float(p["qty"]), "avg": float(p["avg"]), "mark": p.get("mark"),
                     "meta": (p.get("meta") or {}).get("position_meta") or {}, "opened_at": p.get("opened_at"),
                     "pending": False, "key": (p.get("meta") or {}).get("signal_key")}
    for ch in view.extra.get("pending_orders", []) or []:
        inst = str(ch.get("inst", ""))
        if not inst.startswith("EQ:"):
            continue
        sym = inst[3:]
        rem = float(ch.get("vqty") or 0.0) - float(ch.get("filled_v") or 0.0)
        ref = float(ch.get("ref") or 0.0)
        if rem <= 1e-9:
            continue
        sgn = 1.0 if ch.get("side") == "buy" else -1.0
        cur = book.get(sym)
        if cur is None:
            if sgn < 0:
                continue
            cur = book[sym] = {"qty": 0.0, "avg": ref, "mark": ref, "meta": {}, "opened_at": None, "pending": True,
                               "key": ch.get("signal_key")}
        cur["qty"] += sgn * rem
        cash -= sgn * rem * ref
        if cur["qty"] <= 1e-9:
            book.pop(sym)
    return book, cash
