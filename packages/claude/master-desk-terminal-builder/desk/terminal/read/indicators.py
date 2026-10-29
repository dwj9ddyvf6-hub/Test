"""Indicators: what the owner's list names beside the read's own measures (docs/research/2026-10-19-every-factor/
SCOPE.md rows 19, 20, 22, 27, 28, 31, 32, 33, and the spread and listing age of 56), ported from the study's
point-in-time table (the patterns lab's src/indicators.py; its columns in lab/indicators.md):

  the averages     where price sits against its 10, 20, 50 and 200-day averages, in ATR, and whether they stack
  ChartsLector     his leader screen (Qullamaggie's, without the float filter): seven checks, on or off, since when
  the timeframes   the monthly trend (the 10-month average), the weekly (the 10 and 30-week) and the daily inside them
  momentum         the 6-month return that leaves out the last month, ranked on the session's roster
  relative         the return against SPY and against the name's sector fund over one, three and six months
  money flow       the money flow index (14) and Chaikin money flow (20)
  VWAP             the average price paid over 20 sessions, and since the last earnings report's first session
  liquidity        the bid-ask spread, estimated from daily highs and lows (Corwin and Schultz 2012)
  listing          a young listing's first session, and the usual lockup's end while it runs

Every reading is context: stated, checked, and voting nothing. Each reads bars a voting fact already reads (the
10-month average is the 200-day's ten months, trend.stack; the 30-week is the stage's, trend.stage; the screen's
averages are the stack's; strength against the fund it follows is trend.rs; money flow is the volume kind's up and
down volume), and the study found that none holds alone (PATTERNS.md 1, 2l, 2m: of 166 such measures, none in both
eras). Their side stays 0, so the facts with a side, the evidence, the plan, conviction and the take are the read's
without them. No sentence holds a price: distances are in % from the close and in ATR.

Point in time: a value at the last session uses bars dated that session or earlier. A benchmark's bars are paired by
session, so a benchmark bar after the name's last is never read; an earnings report counts from its first session
in the bars (tests/test_read_indicators.py compares a series cut at sessions with the study's definitions there).

The context it reads from `x.extra` (desk/terminal/reads.py extra_for): "spy" (SPY's daily bars; the fund's own when
the name follows SPY), "sector" ({"sym", "bars"}: its sector fund on the desk's map), "reports" ([[date, release
tag]], the desk's Nasdaq earnings archive, oldest first) and "rates" (the session's roster shares; "mom6:<name>" is
the name's 6-month momentum percentile there, from the roster job's first pass)."""
import csv
import math
import os
from datetime import date, timedelta

from . import ta, words
from .core import BARS_USED, Fact, atr_words, pct

# Every window and line, and where each comes from (the owner, 2026-10-19: nothing arbitrary; each is derived from the
# study's data or from the indicator's published definition, or said to be neither)
AVERAGES = (10, 20, 50, 200)        # the owner's list, row 19
CL_ADR, CL_SHARES, CL_PRICE = 4.0, 3e5, 1.0   # ChartsLector's screen as his code publishes it (desk/vendor/
CL_ADR_N, CL_VOL_N = 14, 60         # chartslector/cl_core.py qullamaggie_nofloat): an average daily range (the mean
CL_EMA = (10, 20)                   # of high/low over 14 sessions) of 4% or more, the EMA10 at or over the EMA20, the
CL_SMA = (50, 150)                  # EMA20 at or over the SMA50, the SMA50 at or over the SMA150, the close at or over
                                    # the EMA20, more than 300,000 shares a day over 60 sessions, a close of at least 1
MONTHS, WEEKS = 10, (10, 30)        # the study's map (lab/indicators.md ind_m10_*, ind_w10_*, ind_w30_*, ind_htf_*):
                                    # the 10-month average and its direction, the 10 and 30-week (Weinstein's 30-week
                                    # among them), and the daily against its 20-day
MOM_SKIP, MOM_BACK = 21, 126        # 6-1 momentum (the study's ind_mom6): the log return from 126 sessions back to 21
                                    # back, six months without the last (momentum research skips the last month, whose
                                    # moves tend to reverse; 21 sessions a month, 252 a year)
RS = (21, 63, 126)                  # one, three and six months (SCOPE row 28; the study's ind_rs_*)
MFI_N = 14                          # the money flow index's published period (Quong and Soudack; ta.mfi)
MFI_HI, MFI_LO = 80.0, 20.0         # its conventional lines (StockCharts' ChartSchool and the charting packages)
CMF_N = 20                          # Chaikin money flow: the study's period and the published default (20, or 21)
VWAP_N = 20                         # the owner's list, row 32
CS_N = 20                           # Corwin and Schultz average their two-day estimates over each month; 20 sessions
                                    # is the study's month (ind_cs_spr)
GAP_DAYS = 30                       # a longer stretch without a bar restarts a name's history (a new security): the
                                    # study's value. In the roster's cache every gap is 7 days or less but three of
                                    # 1,209 days or more (reused tickers), so any value from 8 to 1,208 reads the roster
                                    # alike; the data decides no finer than that, and no definition does
PRE_REPORT_DAYS = 30                # an earnings report this long before the first session: already public (a rename
                                    # or a relisting), not a listing. The study's rule; neither its data nor a
                                    # definition fixes the 30
REACT_DAYS = 7                      # a report whose first session would come later is not placed: the exchange calendar
                                    # never makes a report wait longer (9/11 closed the market Sep 11-14, 2001: seven
                                    # days from a report on the evening of the 10th to the 17th); the study's rule
LOCKUP_DAYS = 180                   # an IPO's usual lockup, in calendar days (the SEC's investor bulletin on lock-up
                                    # agreements). The study's window (sessions 90 to 200, ind_lockup) states no
                                    # derivation, so it is not used
RANK_KEY = "mom6:{}"                # a name's 6-month momentum percentile in the roster's shares (reads.rates)
PRE_MARKET = "time-pre-market"      # Nasdaq's release tags: a pre-market report trades its own session, an after-hours
                                    # or untimed one the next (the desk's rule, sleeves/quant_research/fastnumbers
                                    # TIME_OF: untimed is the end of the day)

GLOSSARY = {
    "averages_four": ("The 10, 20, 50 and 200-day averages", "The average close of the last 10, 20, 50 and 200 "
                      "sessions, the short to the long trend, with price's distance from each in ATR. Stacked in "
                      "order, price is over the 10-day, the 10 over the 20, the 20 over the 50 and the 50 over the "
                      "200 (or each under, falling)."),
    "chartslector": ("ChartsLector's leader screen", "A swing trader's screen for leaders (Qullamaggie's, without his "
                     "float filter), seven checks: an average daily range of 4% or more over 14 sessions, the 10-day "
                     "EMA at or over the 20-day, the 20-day EMA at or over the 50-day average, the 50-day at or over "
                     "the 150-day, the close at or over the 20-day EMA, more than 300,000 shares a day over 60 "
                     "sessions, and a price of at least one. All seven: a leader in his stage 2."),
    "timeframes": ("Higher-timeframe map", "The monthly trend (price against its 10-month average, and whether that "
                   "average rises), the weekly (price against its 10 and 30-week averages) and the daily (price "
                   "against its 20-day). A dip under the 20-day inside higher uptrends is a pullback; a rise over it "
                   "inside higher downtrends is a rally against them."),
    "momentum6": ("6-month momentum", "The return from six months back to one month back: momentum as research "
                  "measures it, leaving out the last month, whose moves tend to reverse."),
    "momentum6_rank": ("6-month momentum, ranked", "The return from six months back to one month back, leaving out "
                       "the last month, and its percentile among every name the desk read that session."),
    "rs_spy": ("Relative strength against the S&P 500", "The stock's return less SPY's over one, three and six months: "
               "above zero it beat the market over that stretch."),
    "rs_sector": ("Relative strength against its sector", "The stock's return less its sector fund's over one, three "
                  "and six months. The sector fund is the one the desk's map files it under: the fund whose daily "
                  "moves it has tracked most closely since September 2023."),
    "mfi": ("Money flow index", "RSI weighted by volume: each session's typical price times its volume, counted as "
            "money in when the typical price rose and out when it fell, over 14 sessions, read from 0 to 100. Over "
            "80 money has poured in; under 20 it has drained out."),
    "cmf": ("Chaikin money flow", "Over 20 sessions, each session's volume weighted by where it closed in its range "
            "(+1 at the high, -1 at the low), over the volume: above zero, more of the volume closed near the highs."),
    "vwap20": ("20-day VWAP", "The average price paid over the last 20 sessions, each session weighted by its volume: "
               "price over it means the month's buyers are in profit on average."),
    "vwap_earnings": ("VWAP from earnings", "The average price paid, weighted by volume, since the first session to "
                      "trade on the last earnings report: price over it means the buyers since the report are in "
                      "profit on average."),
    "spread": ("Spread estimate", "Corwin and Schultz (2012) estimate the gap between the best bid and offer from two "
               "days' highs and lows, averaged here over 20 sessions. On daily bars it ranks names much as their "
               "quoted spreads do, but on liquid names its level runs well above the quote: a gauge of liquidity, not "
               "the cost of a trade."),
    "listing": ("A young listing", "A stock whose whole trading history fits in the two years the read uses: its "
                "averages and levels rest on few sessions. An IPO's insiders are usually locked up for 180 days after "
                "the listing."),
}
words.GLOSSARY.update(GLOSSARY)


def facts(x):
    if x.n < 2 or not x.atr:
        return []
    out = []
    for build in (_averages, _chartslector, _timeframes, _momentum, _relative, _flow, _vwaps, _spread, _listing):
        out += build(x)
    return out


def _context(key, family, head, text, reading, learn, data):
    return Fact(key, family, "context", 0, 0.0, head, text, reading, learn, 0.0, data)


def _sessions(x):
    """each bar's session date, measured once per read"""
    got = x.__dict__.get("_sessions")
    if got is None or len(got) != x.n:
        got = x._sessions = [ta.session_of(b) for b in x.bars]
    return got


def _days(ks, unit="day"):
    """10, 20 and 50-day"""
    ks = [str(k) for k in ks]
    return words.join(ks[:-1] + [f"{ks[-1]}-{unit}"])


def _signed(v):
    s = f"{abs(v):.1f}"
    return s if s == "0.0" else ("+" if v > 0 else "−") + s


# ---- row 19: the 10, 20, 50 and 200-day averages ----

def _averages(x):
    c, atr = x.close, x.atr
    ms = {10: ta.sma(x.c[-10:], 10)[-1] if x.n >= 10 else None, 20: x.sma20[-1], 50: x.sma50[-1], 200: x.sma200[-1]}
    if any(m is None for m in ms.values()):
        return []
    d = {k: (c - ms[k]) / atr for k in AVERAGES}
    over, under = [k for k in AVERAGES if c > ms[k]], [k for k in AVERAGES if c < ms[k]]
    at = [k for k in AVERAGES if c == ms[k]]                  # a close exactly on an average is neither over nor under
    stack = 1 if c > ms[10] > ms[20] > ms[50] > ms[200] else -1 if c < ms[10] < ms[20] < ms[50] < ms[200] else 0
    if len(over) == 4 or len(under) == 4:
        head = f"{'Over' if over else 'Under'} its 10, 20, 50 and 200-day averages"
    else:
        head = ", ".join([f"{w} its {_days(ks)}" for w, ks in (("over", over), ("under", under), ("at", at)) if ks])
        head = head[:1].upper() + head[1:] if head else "At its averages"
    if stack:
        head += ", stacked in order"

    def part(k, first):
        side = "over" if d[k] > 0 else "under"
        avg = " average" if first else ""
        if f"{abs(d[k]):.1f}" == "0.0":                        # under 0.05 ATR prints as 0: say it sits there
            return f"right at its {k}-day{avg}"
        return f"{atr_words(d[k])} {side} its {k}-day{avg}"
    text = "Price is " + words.join([part(k, i == 0) for i, k in enumerate(AVERAGES)])
    order = "over" if stack > 0 else "under"
    text += (f": stacked in order, the 10-day {order} the 20-day, the 20-day {order} the 50-day and the 50-day {order} "
             "the 200-day." if stack else ".")
    reading = "Averages (10, 20, 50, 200-day): price " + ", ".join(_signed(d[k]) for k in AVERAGES) + " ATR from them"
    return [_context("trend.averages", "Trend", head, text, reading, "averages_four",
                     dict({f"d{k}": d[k] for k in AVERAGES}, stack=stack))]


# ---- row 20: ChartsLector's leader screen ----

def _ema_pd(xs, n):
    """pandas' ewm(span=n, adjust=False, min_periods=n), as ChartsLector's code computes its EMAs: from the first value,
    shown from the n-th"""
    a, out, y = 2.0 / (n + 1), [None] * len(xs), None
    for i, v in enumerate(xs):
        y = v if y is None else y + a * (v - y)
        if i >= n - 1:
            out[i] = y
    return out


CL_PARTS = ("adr", "e10e20", "e20s50", "shares", "ce20", "price", "s50s150")


def _rolling_mean(xs, n):
    """the mean of each trailing window of n, None where the window holds a None (a bad print's ratio)"""
    out, s, bad = [None] * len(xs), 0.0, 0
    for i, v in enumerate(xs):
        s, bad = (s, bad + 1) if v is None else (s + v, bad)
        if i >= n:
            old = xs[i - n]
            s, bad = (s, bad - 1) if old is None else (s - old, bad)
        if i >= n - 1 and not bad:
            out[i] = s / n
    return out


def _screen_parts(x):
    """[{check: bool} or None per session]: the seven checks where every input is defined"""
    c = x.c
    e10, e20 = _ema_pd(c, CL_EMA[0]), _ema_pd(c, CL_EMA[1])
    s50, s150 = x.sma50, ta.sma(c, CL_SMA[1])
    av = ta.sma(x.vol, CL_VOL_N)
    adr = _rolling_mean([float(b["h"]) / float(b["l"]) if float(b["l"]) > 0 else None for b in x.bars], CL_ADR_N)
    out = []
    for i in range(x.n):
        if None in (e20[i], s50[i], s150[i], av[i], adr[i]):
            out.append(None)
            continue
        r = (adr[i] - 1.0) * 100.0
        out.append({"adr": r >= CL_ADR, "e10e20": e10[i] >= e20[i], "e20s50": e20[i] >= s50[i],
                    "shares": av[i] > CL_SHARES, "ce20": c[i] >= e20[i], "price": c[i] >= CL_PRICE,
                    "s50s150": s50[i] >= s150[i], "_adr": r, "_av": av[i]})
    return out


def screen(x):
    """the screen on every session of x.bars: True when all seven checks pass (cl_core.qullamaggie_nofloat)"""
    return [bool(p) and all(p[k] for k in CL_PARTS) for p in _screen_parts(x)]


_FAILS = {"adr": lambda p: f"a daily range of 4% or more (its averages {p['_adr']:.1f}% over 14 sessions)",
          "e10e20": lambda p: "the 10-day EMA at or over the 20-day",
          "e20s50": lambda p: "the 20-day EMA at or over the 50-day average",
          "shares": lambda p: f"more than 300,000 shares a day (it averages {_shares(p['_av'])} over 60 sessions)",
          "ce20": lambda p: "a close at or over the 20-day EMA",
          "price": lambda p: "a price of at least one",
          "s50s150": lambda p: "the 50-day average at or over the 150-day"}


def _shares(v):
    return f"{v / 1e6:.1f} million" if v >= 1e6 else f"{v / 1e3:.0f},000" if v >= 1e3 else f"{v:.0f}"


def _chartslector(x):
    parts = _screen_parts(x)
    p = parts[-1]
    if not p:
        return []
    on = [bool(q) and all(q[k] for k in CL_PARTS) for q in parts]
    k = sum(1 for name in CL_PARTS if p[name])
    first = next(i for i, q in enumerate(parts) if q)
    since = new = None
    if on[-1]:
        i = x.n - 1
        while i > first and on[i - 1]:
            i -= 1
        since, new = i, i == x.n - 1 and i > first
    data = {"on": on[-1], "n": k, "parts": {name: p[name] for name in CL_PARTS}, "adr": p["_adr"], "shares": p["_av"],
            "since": ta.session_of(x.bars[since]).isoformat() if since is not None else None, "new": bool(new),
            "age": x.n - 1 - since if since is not None else None, "from_start": since == first if on[-1] else False}
    if new:
        return [_context("trend.cl", "Trend", "ChartsLector's leader screen turned on",
                         f"{x.on(x.n - 1, cap=True)} it passed all seven checks of ChartsLector's leader screen, after "
                         "failing one or more the session before.", f"ChartsLector screen: turned on {x.on(x.n - 1)}",
                         "chartslector", data)]
    if on[-1]:
        start = ", the first the read can check" if since == first else ""
        return [_context("trend.cl", "Trend", "ChartsLector's leader screen: on",
                         f"It passes all seven checks of ChartsLector's leader screen, every session since "
                         f"{x.when(since)}{start}.", f"ChartsLector screen: on since {x.when(since)}", "chartslector",
                         data)]
    fails = [_FAILS[name](p) for name in CL_PARTS if not p[name]]
    return [_context("trend.cl", "Trend", f"ChartsLector's leader screen: {k} of 7",
                     f"It passes {k} of the seven checks of ChartsLector's leader screen; it fails "
                     f"{words.join(fails)}.",
                     f"ChartsLector screen: off, {k} of 7", "chartslector", data)]


# ---- row 22: the higher-timeframe map ----

def _month_closes(x):
    """each calendar month's last close in x.bars, oldest first; the live month's is the last close"""
    out, key = [], None
    for d, c in zip(_sessions(x), x.c):
        k = (d.year, d.month)
        if k != key:
            out.append(c)
            key = k
        else:
            out[-1] = c
    return out


def _timeframes(x):
    mc, wc, m20 = _month_closes(x), [float(w["c"]) for w in x.weekly], x.sma20[-1]
    if len(mc) < MONTHS + 1 or len(wc) < max(WEEKS) or m20 is None:
        return []
    c = x.close
    m10, m10_1 = sum(mc[-MONTHS:]) / MONTHS, sum(mc[-MONTHS - 1:-1]) / MONTHS   # with the live month; the month before
    w10, w30 = sum(wc[-WEEKS[0]:]) / WEEKS[0], sum(wc[-WEEKS[1]:]) / WEEKS[1]
    msl = (m10 / m10_1 - 1.0) * 100.0
    m_up, m_dn = c > m10 and msl > 0, c < m10 and msl < 0
    w_up, w_dn = c > w10 and c > w30, c < w10 and c < w30
    d_up, d_dn = c > m20, c < m20
    pbw, rlw, pbm, rlm = w_up and d_dn, w_dn and d_up, m_up and d_dn, m_dn and d_up
    all_up, all_dn = m_up and w_up and d_up, m_dn and w_dn and d_dn
    slope = "rising" if msl > 0 else "falling" if msl < 0 else "flat"
    where = "over" if c > m10 else "under" if c < m10 else "at"
    monthly = f"{where} its {slope} 10-month average ({pct((c / m10 - 1.0) * 100.0)})"
    weekly = ("over its 10 and 30-week averages" if w_up else "under its 10 and 30-week averages" if w_dn else
              f"{'over' if c > w10 else 'under'} its 10-week average and {'over' if c > w30 else 'under'} its 30-week")
    daily = "over its 20-day average" if d_up else "under its 20-day average" if d_dn else "at its 20-day average"

    def frames(w, m):
        return "weekly and monthly" if w and m else "weekly" if w else "monthly"
    if all_up or all_dn:
        head = f"Every timeframe {'up' if all_up else 'down'}"
        rel = f": every timeframe points {'up' if all_up else 'down'}"
    elif pbw or pbm:
        f = frames(pbw, pbm)
        head, rel = f"A pullback inside the {f} uptrend{'s' if pbw and pbm else ''}", \
            f": a dip inside the {f} uptrend{'s' if pbw and pbm else ''}"
    elif rlw or rlm:
        f = frames(rlw, rlm)
        head, rel = f"A rally inside the {f} downtrend{'s' if rlw and rlm else ''}", \
            f": a rise against the {f} downtrend{'s' if rlw and rlm else ''}"
    else:
        head, rel = "Timeframes out of step", ""
    text = f"Monthly, price is {monthly}; weekly, {weekly}; daily, {daily}{rel}."
    state = ("up" if m_up else "down" if m_dn else "turning", "up" if w_up else "down" if w_dn else "between",
             "up" if d_up else "down" if d_dn else "at its 20-day")
    reading = f"Timeframes: monthly {state[0]}, weekly {state[1]}, daily {state[2]}"
    return [_context("trend.htf", "Trend", head, text, reading, "timeframes",
                     {"m10_dist": (c / m10 - 1.0) * 100.0, "m10_slope": msl, "w10_dist": (c / w10 - 1.0) * 100.0,
                      "w30_dist": (c / w30 - 1.0) * 100.0, "m_up": m_up, "m_dn": m_dn, "w_up": w_up, "w_dn": w_dn,
                      "d_up": d_up, "d_dn": d_dn, "pbw": pbw, "rlw": rlw, "pbm": pbm, "rlm": rlm, "all_up": all_up,
                      "all_down": all_dn})]


# ---- row 27: 6-month momentum and its rank on the roster ----

def mom6(closes):
    """6-1 momentum at the last close: ln(close MOM_SKIP back / close MOM_BACK back), or None"""
    n = len(closes)
    if n <= MOM_BACK or closes[n - 1 - MOM_SKIP] <= 0 or closes[n - 1 - MOM_BACK] <= 0:
        return None
    return math.log(closes[n - 1 - MOM_SKIP] / closes[n - 1 - MOM_BACK])


def mom6_of(bars):
    """a name's 6-1 momentum as its read measures it (its bars as the read cleans them: integrity.clean), or None: the
    roster job's first pass keeps it for the ranks"""
    from . import integrity
    kept = integrity.clean([b for b in bars or () if b.get("c") is not None])[0]
    return mom6([float(b["c"]) for b in kept])


def ranks(values):
    """{RANK_KEY: the share of the names with a value at or below this one's} (0 < share <= 1, the study's
    ind_mom6_pr), for every name with a value"""
    vs = sorted(v for v in values.values() if v is not None)
    if not vs:
        return {}
    from bisect import bisect_right
    return {RANK_KEY.format(s): round(bisect_right(vs, v) / len(vs), 6) for s, v in values.items() if v is not None}


def _ordinal(k):
    return f"{k}{'th' if 10 <= k % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(k % 10, 'th')}"


def _momentum(x):
    m = mom6(x.c)
    if m is None:
        return []
    ret = (math.exp(m) - 1.0) * 100.0
    rank = ((x.extra or {}).get("rates") or {}).get(RANK_KEY.format(x.sym))
    a, b = x.n - 1 - MOM_BACK, x.n - 1 - MOM_SKIP
    text = (f"From {x.when(a)} to {x.when(b)}, six months back to one month back, it moved {pct(ret)}, the momentum "
            "measure that leaves out the last month.")
    head, reading = f"6-month momentum {pct(ret, 0)}", f"6-month momentum: {pct(ret)}"
    if rank:
        o = _ordinal(round(rank * 100))
        text += f" That ranks at the {o} percentile of the names the desk read that session."
        head, reading = head + f", {o} percentile", reading + f", {o} percentile of the roster"
    return [_context("trend.mom6", "Trend", head, text, reading, "momentum6_rank" if rank else "momentum6",
                     {"mom6": m, "ret": ret, "rank": rank})]


# ---- row 28: relative strength against SPY and the sector fund ----

_SECTORS = {}


def is_fund(sym):
    """whether a symbol is a fund (an ETF), not a stock: the feed's fund list, the terminal's extra funds, the map's
    "ETF/self" and the desk's SPY and QQQ families, so a card names it a fund (IGV on 2026-10-26 read "A stock ...")"""
    from ... import lab
    from ...feedlib.node_source import ETFS
    from ..deskview import EXTRA_ETFS
    if not sym:
        return False
    sector_of(sym)                                     # loads the map
    return sym in ETFS or sym in EXTRA_ETFS or sym in lab.SPY_FAMILY or sym in lab.QQQ_FAMILY or \
        _SECTORS.get(sym) == "ETF/self"


def sector_of(sym):
    """the sector fund the desk's map files a name under (desk/lab SECTOR_MAP: the sector fund its daily returns
    tracked best since 2023-09), or None: a fund itself (the map's "ETF/self", the desk's named SPY and QQQ families) or
    a name the map leaves blank"""
    from ... import lab
    if not _SECTORS and os.path.exists(lab.SECTOR_MAP):
        with open(lab.SECTOR_MAP) as f:
            for row in csv.reader(f):
                if len(row) >= 2 and row[0]:
                    _SECTORS[row[0]] = row[1]
    fund = _SECTORS.get(sym) or ""
    if not fund or fund == "ETF/self" or fund == sym or sym in lab.SPY_FAMILY or sym in lab.QQQ_FAMILY:
        return None
    return fund


def sector_funds():
    """every sector fund the desk's map names"""
    sector_of("SPY")                                             # loads the map
    return sorted({f for f in _SECTORS.values() if f and f != "ETF/self"})


_SPAN = {21: "a month", 63: "three months", 126: "six months"}


def rs(x, bench):
    """{k: the name's log return less the benchmark's over k sessions} at the last session, for k in RS; sessions are
    paired by date, so no benchmark bar after the name's last is read"""
    need = {k: x.n - 1 - k for k in (0,) + RS if x.n - 1 - k >= 0}
    ss = _sessions(x)
    days = {ss[i]: i for i in need.values()}
    first = min(days)
    bc = {}
    for b in reversed(bench or ()):
        if b.get("c") is None:
            continue
        d = ta.session_of(b)
        if d < first:
            break
        if d in days:
            bc[days[d]] = float(b["c"])
    i0 = x.n - 1
    if i0 not in bc or bc[i0] <= 0:
        return {}
    out = {}
    for k in RS:
        j = i0 - k
        if j in bc and bc[j] > 0 and x.c[j] > 0:
            out[k] = math.log(x.c[i0] / bc[i0]) - math.log(x.c[j] / bc[j])
    return out


def _relative(x):
    ex = x.extra or {}
    out = []
    spy = ex.get("spy") or (x.index_bars if x.index_sym == "SPY" else None)
    sec = ex.get("sector") or {}
    for key, fund, bars, who, learn in (("trend.vs_spy", "SPY", spy, "the S&P 500 fund", "rs_spy"),
                                        ("trend.vs_sector", sec.get("sym"), sec.get("bars"),
                                         "its sector fund", "rs_sector")):
        if not bars or not fund or fund == x.sym:
            continue
        r = rs(x, bars)
        if not r:
            continue
        p = {k: (math.exp(v) - 1.0) * 100.0 for k, v in r.items()}
        far = max(p)
        out.append(_context(key, "Trend", f"Against {fund}: {pct(p[far], 0)} over {_SPAN[far]}",
                            f"Against {fund}, {who}, it is "
                            + words.join([f"{pct(p[k], 0)} over {_SPAN[k]}" for k in RS if k in p]) + ".",
                            f"Relative strength vs {fund}: "
                            + ", ".join(f"{pct(p[k], 0)} in {k // 21} month{'s' if k > 21 else ''}"
                                        for k in RS if k in p),
                            learn, dict({f"rs{k}": v for k, v in r.items()}, fund=fund)))
    return out


# ---- row 31: the money flow index and Chaikin money flow ----

def _flow(x):
    out = []
    w = x.bars[-(MFI_N + 1):]
    if len(w) == MFI_N + 1 and sum(float(b.get("v") or 0) for b in w[1:]) > 0:
        m = ta.mfi(w, MFI_N)[-1]
        where = (": above 80, money has poured in." if m > MFI_HI else ": under 20, money has drained out."
                 if m < MFI_LO else ", between the 20 and 80 that mark money drained out and poured in.")
        out.append(_context("vol.mfi", "Volume", f"Money flow index {m:.0f}",
                            f"The money flow index reads {m:.0f} over 14 sessions{where}",
                            f"Money flow index (14): {m:.0f}", "mfi", {"mfi": m}))
    w = x.bars[-CMF_N:]
    vol = sum(float(b.get("v") or 0) for b in w)
    if len(w) == CMF_N and vol > 0:
        flow = 0.0
        for b in w:
            h, lo, c = float(b["h"]), float(b["l"]), float(b["c"])
            if h > lo:
                flow += ((c - lo) - (h - c)) / (h - lo) * float(b.get("v") or 0)
        v = flow / vol
        s = f"{abs(v):.2f}"
        s = s if s == "0.00" else ("+" if v > 0 else "−") + s
        say = ("more of the volume closed near the day's high than near its low." if v > 0 else
               "more of the volume closed near the day's low than near its high." if v < 0 else
               "the volume closed as much near the highs as near the lows.")
        out.append(_context("vol.cmf", "Volume", f"Chaikin money flow {s}",
                            f"Chaikin money flow reads {s} over 20 sessions: {say}", f"Chaikin money flow (20): {s}",
                            "cmf", {"cmf": v}))
    return out


# ---- rows 32 and 33: the 20-day VWAP and the VWAP from the last earnings ----

def reaction(x, reports):
    """the index in x.bars of the last earnings report's first session, or None: the report's own session on a
    pre-market tag, the next session otherwise; a report whose session the bars do not hold yet, or that would wait
    more than REACT_DAYS for one, is passed over for the one before"""
    days = _sessions(x)
    best = None
    for day, tag in reports or ():
        try:
            rd = date.fromisoformat(str(day)[:10])
        except ValueError:
            continue
        lo, hi = 0, x.n                                         # the first session on or after the report's date
        while lo < hi:
            mid = (lo + hi) // 2
            if days[mid] < rd:
                lo = mid + 1
            else:
                hi = mid
        i = lo
        if i < x.n and days[i] == rd and tag != PRE_MARKET:
            i += 1
        if i < x.n and (days[i] - rd).days <= REACT_DAYS and (best is None or i > best):
            best = i
    return best


def _level(x, key, head_what, v, lead, who, reading, learn, data):
    pos, d = x.pct_of(v), (x.close - v) / x.atr
    side = "below" if v < x.close else "above"
    gain = "in profit" if v < x.close else "under water"
    head = f"{'Over' if x.close > v else 'Under' if x.close < v else 'At'} its {head_what}"
    return _context(key, "Levels", head,
                    f"{lead} is {pct(pos)} {side} the close ({atr_words(d)}): {who} {gain} on average.",
                    f"{reading}: {pct(pos)} from the close", learn, dict(data, level=v, pct=pos, atr=d))


def _vwaps(x):
    out = []
    if x.n >= VWAP_N and sum(float(b.get("v") or 0) for b in x.bars[-VWAP_N:]) > 0:
        v = ta.avwap(x.bars, x.n - VWAP_N)[-1]                   # each session at its own VWAP when the bar has one
        out.append(_level(x, "levels.vwap20", "20-day VWAP", v,
                          "The 20-day VWAP, the average price paid over the last 20 sessions,",
                          "the month's buyers are", "20-day VWAP", "vwap20", {}))
    r = reaction(x, (x.extra or {}).get("reports"))
    if r is not None and sum(float(b.get("v") or 0) for b in x.bars[r:]) > 0:
        v = ta.avwap(x.bars, r)[-1]
        out.append(_level(x, "levels.vwap_earnings", "VWAP from earnings", v,
                          f"The average price paid since {x.when(r)}, the first session to trade on its last earnings "
                          "report,", "the buyers since the report are", f"VWAP from the {x.when(r)} earnings session",
                          "vwap_earnings", {"session": ta.session_of(x.bars[r]).isoformat()}))
    return out


# ---- row 56: the spread, from daily highs and lows ----

def spread(x):
    """the Corwin-Schultz (2012) spread in % of price: each two-day estimate (the second day's range shifted by the
    overnight gap, a negative estimate set to zero, as the paper allows) averaged over the last CS_N sessions"""
    if x.n < CS_N + 1:
        return None
    k = 3.0 - 2.0 * math.sqrt(2.0)
    tot = 0.0
    for i in range(x.n - CS_N, x.n):
        p, b = x.bars[i - 1], x.bars[i]
        hp, lp, pc = float(p["h"]), float(p["l"]), float(p["c"])
        h, lo = float(b["h"]), float(b["l"])
        adj = lo - pc if lo > pc else h - pc if h < pc else 0.0
        h2, l2 = h - adj, lo - adj
        if min(hp, lp, h2, l2) <= 0:
            return None
        beta = math.log(hp / lp) ** 2 + math.log(h2 / l2) ** 2
        gamma = math.log(max(hp, h2) / min(lp, l2)) ** 2
        alpha = (math.sqrt(2.0 * beta) - math.sqrt(beta)) / k - math.sqrt(gamma / k)
        tot += max(0.0, 2.0 * (math.exp(alpha) - 1.0) / (1.0 + math.exp(alpha)))
    return tot / CS_N * 100.0


def _spread(x):
    """the estimate as a gauge, never as the price of a trade: on the 23 names the desk quotes (cache/spreads.json,
    2026-10-16) it ranked the quoted spreads (Spearman 0.70) but ran a median 11.5 times above them (0.3 to 58 times;
    QQQ 44, NFLX 31): on daily bars the volatility it cannot separate dominates a liquid name's estimate"""
    s = spread(x)
    if s is None:
        return []
    share = s / (x.atr / x.close * 100.0)
    if s <= 0:
        return [_context("ctx.spread", "Liquidity", "Spread estimate 0%",
                         "Its spread estimated from daily highs and lows (Corwin and Schultz) is zero over 20 "
                         "sessions: every two-day estimate came out at zero or under, too narrow to measure this way.",
                         "Spread estimate (Corwin-Schultz, 20 sessions): 0%", "spread",
                         {"spread_pct": 0.0, "of_atr": 0.0})]
    return [_context("ctx.spread", "Liquidity", f"Spread estimate {s:.2f}%",
                     f"Its spread estimated from daily highs and lows (Corwin and Schultz) averages {s:.2f}% of price "
                     f"over 20 sessions, {share:.2f} of its daily range: a gauge of liquidity, not a quote.",
                     f"Spread estimate (Corwin-Schultz, 20 sessions): {s:.2f}% of price", "spread",
                     {"spread_pct": s, "of_atr": share})]


# ---- row 56 (and 59): a young listing ----

def listing(x):
    """(the index in x.bars of the first traded session of the name's current history, its age in sessions) when the
    read holds that whole history, else None. The history restarts after more than GAP_DAYS without a bar; its first
    traded session is its first with volume; an earnings report PRE_REPORT_DAYS or more before it means the name was
    public before (a rename or a relisting)"""
    days = _sessions(x)
    start = next((i for i in range(x.n - 1, 0, -1) if (days[i] - days[i - 1]).days > GAP_DAYS), None)
    if start is None:
        if x.n >= BARS_USED:                                    # the history runs past the read's window: not young
            return None
        start = 0
    i0 = next((i for i in range(start, x.n) if float(x.bars[i].get("v") or 0) > 0), None)
    if i0 is None:
        return None
    cut = days[i0] - timedelta(days=PRE_REPORT_DAYS)
    for day, _ in (x.extra or {}).get("reports") or ():
        try:
            if date.fromisoformat(str(day)[:10]) <= cut:
                return None
        except ValueError:
            continue
    return i0, x.n - 1 - i0


def _listing(x):
    got = listing(x)
    if not got:
        return []
    i0, age = got
    first, last = ta.session_of(x.bars[i0]), ta.session_of(x.bars[-1])
    end = first + timedelta(days=LOCKUP_DAYS)
    inside = last < end
    text = (f"It has traded since {x.when(i0)}: {age + 1} sessions to the {x.when(x.n - 1)} close, a short history for "
            "its averages and levels.")
    if inside:
        text += (f" The usual 180-day IPO lockup from that date runs to {words.short_day(end)}"
                 + ("" if end.year == last.year else f", {end.year}") + ".")
    return [_context("ctx.listing", "Events", "A young listing", text,
                     f"Listing: trading since {x.when(i0)} ({age + 1} sessions)", "listing",
                     {"first": first.isoformat(), "age": age, "lockup": inside, "lockup_end": end.isoformat()})]
