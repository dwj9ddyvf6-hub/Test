"""The owner's fear-day rule on the terminal (2026-10-18): buy a long setup only on a day its own index fund and the name
both close red, within the 5 sessions opening after the signal; no such day, no trade. The fund is the one the name
follows (desk/lab own_index: QQQ for semis, memory, tech and internet names, SPY for the rest). The Execution Lab
measures the rule forward (desk/lab/policies.py fear5c_own); the terminal says where each listed long stands, on
completed daily closes only (the hub caches completed sessions only):

  came      the first fear day in the window: the rule's buy, at that close
  waiting   the window is open and no fear day has come yet
  none      the five sessions passed without one: the rule passes on the setup

A short, or a name or fund the desk's caches hold no closes for, gets no status. The banner says whether the last
session both funds hold was a broad fear day (QQQ and SPY both red). Words and dates only: no price, no index value."""
from datetime import datetime

from .. import calendar as cal
from ..util import ET

WINDOW = 5
FUNDS = ("QQQ", "SPY")


def _closes(bars):
    """{session date: close} of daily bars"""
    out = {}
    for b in bars or ():
        try:
            out[cal._as_date(float(b["t"]))] = float(b["c"])
        except (KeyError, TypeError, ValueError):
            continue
    return out


def _red(closes, d):
    """True / False: the close of session d is below the session before's; None when either close is missing"""
    p = cal.prev_trading_day(d)
    if d not in closes or p not in closes:
        return None
    return closes[d] < closes[p]


def _day(d):
    return datetime(d.year, d.month, d.day).strftime("%a %b ") + str(d.day)


def window(signal_at):
    """the WINDOW sessions opening after the signal (a signal before a session's open counts that session)"""
    d = cal._as_date(signal_at)
    if not (cal.is_trading_day(d) and float(signal_at) < cal.session_open(d)):
        d = cal.next_trading_day(d)
    out = [d]
    while len(out) < WINDOW:
        out.append(cal.next_trading_day(out[-1]))
    return out


def status(sym, side, signal_at, bars):
    """{state, fund, date, label, text} for a long setup, or None. bars: {symbol: daily bars}"""
    from ..lab import own_index                                  # the lab's rule, so the page and the lab agree
    if side != "long":
        return None
    fund = own_index(sym)
    name, idx = _closes(bars.get(sym)), _closes(bars.get(fund))
    if not name or not idx:
        return None
    days = window(signal_at)
    both = sym if fund == sym else f"{fund} and {sym}"                # QQQ or SPY on the board: its own fund
    seen = 0
    for d in days:
        r_idx, r_name = _red(idx, d), _red(name, d)
        if r_idx is None or r_name is None:
            break                                                # not closed yet, or not in the caches
        seen += 1
        if r_idx and r_name:
            return {"state": "came", "fund": fund, "date": d.isoformat(), "label": "Fear day: " + _day(d), "short": _day(d),
                    "text": f"{_day(d)}: {both} {'closed' if fund == sym else 'both closed'} red, the rule's buy "
                            "(at that close)."}
    if seen == WINDOW:
        return {"state": "none", "fund": fund, "date": None, "label": "No fear day", "short": "none",
                "text": f"No fear day in its five sessions ({_day(days[0])} to {_day(days[-1])}): the rule passes on it."}
    return {"state": "waiting", "fund": fund, "date": None, "label": "Fear day: waiting", "short": "waiting",
            "text": f"Waiting for {both} to close red{'' if fund == sym else ' on the same day'}, through "
                    f"{_day(days[-1])}."}


def banner(bars):
    """{date, both, text}: the last session both funds hold, and which closed red; None without both"""
    q, s = _closes(bars.get("QQQ")), _closes(bars.get("SPY"))
    common = sorted(set(q) & set(s))
    for d in reversed(common):
        rq, rs = _red(q, d), _red(s, d)
        if rq is None or rs is None:
            continue
        if rq and rs:
            text = "QQQ and SPY both closed red, a broad fear day."
        elif rq or rs:
            text = ("QQQ closed red, SPY did not." if rq else "SPY closed red, QQQ did not.")
        else:
            text = "neither QQQ nor SPY closed red."
        return {"date": d.isoformat(), "both": bool(rq and rs), "text": f"{_day(d)}: {text}"}
    return None
