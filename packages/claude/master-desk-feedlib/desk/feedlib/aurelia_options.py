"""Inputs of the Aurelia source desk's free-paper option descendants (Agentic-Trading-Desk aurelia-paper-desk
@1720157f768e), as desk feeds.

frozen_hedge(spy, qqq): desk/option_inputs.py _hedge(), the arithmetic verbatim, on {session: close} maps — the
  SPY/QQQ hedge "frozen from prior closes": the 61 common sessions before the latest one form the fit (60 daily
  returns; the latest bar is never inside it), beta = cov / var (population moments), the residual's mean and
  population deviation, and the latest session's residual z against them; signal = |z| > 2. {} with fewer than 62
  common sessions or no variance.
feed(feeds, sleeve, now): that hedge on the desk's completed daily closes of SPY and QQQ (split-adjusted; the source
  read raw SIP closes — SPY and QQQ had no split in any fit window here — fetched once, when its store was empty, and
  never refreshed: here the fit moves with every finished session)."""
from datetime import datetime, timedelta

from .. import calendar as cal
from ..util import ET

SYMBOLS = ("SPY", "QQQ")
LOOKBACK = 80


def frozen_hedge(spy, qqq):
    sessions = sorted(set(spy) & set(qqq))
    if len(sessions) < 62:
        return {}
    fit, last = sessions[-61:-1], sessions[-1]
    rs, rq = [], []
    for older, newer in zip(fit, fit[1:]):
        rs.append(spy[newer] / spy[older] - 1)
        rq.append(qqq[newer] / qqq[older] - 1)
    mean_s = sum(rs) / len(rs)
    var = sum((value - mean_s) ** 2 for value in rs) / len(rs)
    if var <= 0:
        return {}
    cov = sum((a - mean_s) * (b - sum(rq) / len(rq)) for a, b in zip(rs, rq)) / len(rs)
    beta = cov / var
    residual = [b - beta * a for a, b in zip(rs, rq)]
    center = sum(residual) / len(residual)
    scale = (sum((value - center) ** 2 for value in residual) / len(residual)) ** 0.5
    live = (qqq[last] / qqq[fit[-1]] - 1) - beta * (spy[last] / spy[fit[-1]] - 1)
    z = (live - center) / scale if scale else 0.0
    return {
        "beta": beta,
        "z": z,
        "asof": fit[-1],
        "signal_session": last,
        "signal": abs(z) > 2,
        "reason": f"Hedge frozen through {fit[-1]}. Latest residual z is {z:.2f}.",
    }


def completed_through(now):
    """the newest session whose close has passed (the running session's bar is not a close yet)."""
    d = cal._as_date(now)
    while not (cal.is_trading_day(d) and float(now) >= cal.session_close(d)):
        d = d - timedelta(days=1)
    return d.isoformat()


def closes(rows, through):
    """{ET session date: close} of daily bars dated on or before `through`."""
    out = {}
    for b in rows or []:
        d = datetime.fromtimestamp(float(b["t"]), tz=ET).date().isoformat()
        if d <= through and b.get("c"):
            out[d] = float(b["c"])
    return out


def feed(feeds, sleeve, now, arg=None):
    got = feeds.hub.bars("equity_split", "1d", list(SYMBOLS), LOOKBACK)
    through = completed_through(now)
    return frozen_hedge(closes(got.get("SPY"), through), closes(got.get("QQQ"), through))
