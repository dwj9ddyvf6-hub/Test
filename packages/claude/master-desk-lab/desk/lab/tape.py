"""One symbol's cached bars as the lab reads them, and the point-in-time questions it asks of them: what had completed
at a decision, and what came after it.

  days   (session, open_t, close_t, o, h, l, c, v), one per regular session, ascending. A daily bar's session is its
         UTC date (desk/data/cache.py _session: Alpaca's midnight-ET stamp and Yahoo's open stamp both fall on it); it
         spans the session's open to its close
  hours / fine  (start, end, o, h, l, c, session) of intraday bars that start inside the regular session: a clock-grid
         09:00 hour straddles the open and an extended-hours bar is no price the desk can trade, so both are dropped;
         a bar ends at min(start + step, the session's close)
  hours, per session (EQ-06): the hub's hourly bars where they reach the session's close, else the canonical 1H
         store's (desk/lab/intraday.py; the open-anchored grid) where those do; h1_src names which covered each
         session ("hub" / "canonical"); a session neither covers keeps what the hub holds of it, uncovered
Nothing here reads the network or writes anything: the bars are what desk/data/hub.py serves cache_only."""
import bisect
import statistics
from datetime import datetime, timezone

from .. import calendar as cal
from ..data.cache import INTERVAL_S

ATR_N = 14


def _session_utc(t):
    return datetime.fromtimestamp(float(t), tz=timezone.utc).date()


_DAILY = {}                                              # date -> (session, open, close), or None: no trading day


def _days(bars, until):
    out = {}
    for b in bars or ():
        try:
            d = _session_utc(b["t"])
            row = (float(b["o"]), float(b["h"]), float(b["l"]), float(b["c"]), float(b.get("v") or 0.0))
        except (KeyError, TypeError, ValueError):
            continue
        if d not in _DAILY:                              # the calendar asked once per date, not once per bar
            _DAILY[d] = (d.isoformat(), cal.session_open(d), cal.session_close(d)) if cal.is_trading_day(d) else None
        s = _DAILY[d]
        if s is not None and s[2] <= until:
            out[s[0]] = s + row
    return [out[k] for k in sorted(out)]


_DAY = {}                                                # day number -> (open, close, session) or None


def _session_of(t):
    """(open, close, session) of the ET trading day whose window holds t, or None: the calendar is asked once per day,
    not once per bar (a year of half hours, extended hours included, is ~8,000 bars over 252 sessions; asking per bar
    made the tapes the lab's dominant cost, 2026-10-26). A day's window runs from 06:00 UTC (01:00 EST, 02:00 EDT),
    an hour no US equity bar prints in either season, and its date is read at the window's 12:00 UTC, never from a
    bar. A bar outside the session's [open, close) is no session bar whatever its window, as before."""
    k = int((t - 21600.0) // 86400.0)
    if k not in _DAY:
        d = cal._as_date(k * 86400.0 + 43200.0)
        _DAY[k] = (cal.session_open(d), cal.session_close(d), d.isoformat()) if cal.is_trading_day(d) else None
    return _DAY[k]


def _intraday(bars, step, until):
    out = {}
    for b in bars or ():
        try:
            s = float(b["t"])
            row = (float(b["o"]), float(b["h"]), float(b["l"]), float(b["c"]))
        except (KeyError, TypeError, ValueError):
            continue
        day = _session_of(s)
        if day is None:
            continue
        o, c, iso = day
        if o <= s < c and min(s + step, c) <= until:
            out[s] = (s, min(s + step, c)) + row + (iso,)
    return [out[k] for k in sorted(out)]


_CLOSE = {}                                              # session -> its close


def _close(d):
    if d not in _CLOSE:
        _CLOSE[d] = cal.session_close(d)
    return _CLOSE[d]


def _covered(bars):
    """{session: True} where a session's bars reach its close"""
    last = {}
    for b in bars:
        last[b[6]] = b[1]
    return {d: end >= _close(d) for d, end in last.items()}


def _merge_hours(primary, alt):
    """per session: the primary (hub) bars where they reach the close, else the alternate (canonical store) bars where
    they do, else the primary's (an uncovered session keeps what the hub holds) -> (bars, {session: source})"""
    if not alt:
        return primary, {d: "hub" for d, ok in _covered(primary).items() if ok}
    p_ok, a_ok = _covered(primary), _covered(alt)
    src = {}
    for d in set(p_ok) | set(a_ok):
        if p_ok.get(d):
            src[d] = "hub"
        elif a_ok.get(d):
            src[d] = "canonical"
    out = [b for b in primary if src.get(b[6]) != "canonical"] + [b for b in alt if src.get(b[6]) == "canonical"]
    return sorted(out), src


class Tape:
    """until: bars completed after it are left out (a run never sees what its own clock could not have); hourly_alt:
    the canonical 1H store's hours, used for a session the hub's hourly bars do not cover (EQ-06); m30: the canonical
    store's SIP half hours (the intraday arms' path where no 5-minute series covers a session)"""

    def __init__(self, daily=(), hourly=(), fine=(), fine_iv="5m", until=float("inf"), hourly_alt=(), m30=()):
        self.days = _days(daily, until)
        self.hours, self.h1_src = _merge_hours(_intraday(hourly, INTERVAL_S["1h"], until),
                                               _intraday(hourly_alt, INTERVAL_S["1h"], until))
        self.fine = _intraday(fine, INTERVAL_S[fine_iv], until)
        self.m30 = _intraday(m30, 1800, until)
        self._cov, self._by_sess, self._ema30 = {}, {}, None
        self._m30start = [b[0] for b in self.m30]
        self.until = until
        self.fine_iv = fine_iv
        self._open = [d[1] for d in self.days]
        self._close = [d[2] for d in self.days]
        self._sess = [d[0] for d in self.days]
        self._day = {d: i for i, d in enumerate(self._sess)}
        self._hstart = [b[0] for b in self.hours]
        self._hend = [b[1] for b in self.hours]
        self._fend = [b[1] for b in self.fine]

    # -- what had completed at t --------------------------------------------------------------------------
    def n_done(self, t):
        """the number of daily bars completed at t (their session closed at or before it)"""
        return bisect.bisect_right(self._close, t)

    def atr(self, t, n=ATR_N):
        """the mean true range of the last n daily bars completed at t (n + 1 bars needed), else None"""
        k = self.n_done(t)
        if k < n + 1:
            return None
        bars = self.days[k - n - 1:k]
        trs = [max(b[4] - b[5], abs(b[4] - a[6]), abs(b[5] - a[6])) for a, b in zip(bars, bars[1:])]
        v = sum(trs) / len(trs)
        return v if v > 0 else None

    def median_dv(self, session, n=20):
        """the median dollar volume (close x volume) of the n daily bars before `session`, or None with fewer"""
        k = bisect.bisect_left(self._sess, session)
        if k < n:
            return None
        return statistics.median(d[6] * d[7] for d in self.days[k - n:k])

    def completed(self, t):
        """[(interval, end, session, close)] of the freshest completed bars at t, freshest first (a session's last hour
        and its daily bar end together: the daily bar first): the last fine and hourly bars and the last three daily
        bars (a basis two sessions old is still found)"""
        out = []
        i = bisect.bisect_right(self._fend, t)
        if i:
            b = self.fine[i - 1]
            out.append((self.fine_iv, b[1], b[6], b[5]))
        i = bisect.bisect_right(self._hend, t)
        if i:
            b = self.hours[i - 1]
            out.append(("1h", b[1], b[6], b[5]))
        k = self.n_done(t)
        for d in reversed(self.days[max(0, k - 3):k]):
            out.append(("1d", d[2], d[0], d[6]))
        out.sort(key=lambda x: (-x[1], x[0] != "1d", x[0] != "1h"))      # a session's close: its daily bar
        return out

    def uptrend(self, t, fast=50, slow=200):
        """the name's trend at t from the daily closes completed by then: the last close above its 50-session average
        and that average above the 200-session one (one definition, fixed in advance); None without 200 closes"""
        closes = [d[6] for d in self.days[:self.n_done(t)]]
        if len(closes) < slow:
            return None
        f, s = sum(closes[-fast:]) / fast, sum(closes[-slow:]) / slow
        return closes[-1] > f > s

    def last_close(self, t):
        """(close, end, interval) of the freshest bar completed at t, or None"""
        c = self.completed(t)
        return (c[0][3], c[0][1], c[0][0]) if c else None

    # -- what came after t ---------------------------------------------------------------------------------
    def next_day(self, t):
        """the index of the first daily bar whose session opens after t, or None when none is cached yet"""
        k = bisect.bisect_right(self._open, t)
        return k if k < len(self.days) else None

    def day_index(self, session):
        return self._day.get(session)

    def prev_close(self, t):
        """the close of the session before the next one opening after t (the gap rule's reference, known before that
        open), when both are cached and adjacent"""
        k = self.next_day(t)
        if not k:
            return None
        a, b = self.days[k - 1], self.days[k]
        return a[6] if cal.prev_trading_day(b[0]).isoformat() == a[0] else None

    def hours_after(self, t, session):
        """the hourly bars of `session` that start after t"""
        out = []
        for b in self.hours[bisect.bisect_right(self._hstart, t):]:
            if b[6] != session:
                break
            out.append(b)
        return out

    def covers_hours(self, session):
        """the hourly series holds `session` to its close (its last regular-session hour is cached)"""
        c = cal.session_close(session)
        i = bisect.bisect_left(self._hend, c)
        return i < len(self.hours) and self.hours[i][6] == session and self.hours[i][1] >= c

    # -- the intraday arms' path (desk/lab/arms.py): the finest series that covers a session --------------------
    def series(self, iv):
        return {self.fine_iv: self.fine, "30m": self.m30, "1h": self.hours}.get(iv) or []

    def covers(self, iv, session):
        """the `iv` series holds `session` to its close"""
        if iv not in self._cov:
            self._cov[iv] = _covered(self.series(iv))
        return bool(self._cov[iv].get(session))

    def path_iv(self, session):
        """the finest intraday series covering `session` (5m, else the canonical half hours, else 1h), or None"""
        return next((iv for iv in (self.fine_iv, "30m", "1h") if self.covers(iv, session)), None)

    def bars_of(self, iv, session):
        """the `iv` series' bars of one session (each series indexed by session once)"""
        if iv not in self._by_sess:
            idx = {}
            for b in self.series(iv):
                idx.setdefault(b[6], []).append(b)
            self._by_sess[iv] = idx
        return self._by_sess[iv].get(session, [])

    def window_path(self, t0, end, session):
        """(interval, bars) of `session` starting after t0 and before `end`, on the finest series covering it, or
        (None, []) when none covers it"""
        iv = self.path_iv(session)
        if iv is None:
            return None, []
        return iv, [b for b in self.bars_of(iv, session) if t0 < b[0] < end]

    def pivot_state(self, t, n=20):
        """the 30-minute pivot's facts before a path that starts after t: EMA(n) of the half hours' closes through the
        last one starting at or before t (seeded by the first close, as Pine's ta.ema), and those last three half
        hours (o, h, l, c), oldest first; None with fewer than three"""
        k = bisect.bisect_right(self._m30start, t)
        if k < 3:
            return None
        if self._ema30 is None:
            a, e, out = 2.0 / (n + 1), None, []
            for b in self.m30:
                e = b[5] if e is None else a * b[5] + (1.0 - a) * e
                out.append(e)
            self._ema30 = out
        return {"ema": self._ema30[k - 1], "hist": [list(self.m30[i][2:6]) for i in range(k - 3, k)]}

    def price_at(self, t, session):
        """(the close of the bar of `session` in which t falls, its interval) on the finest series of bars no longer
        than 30 minutes that covers the session, or None: the price at a moment, to the bar"""
        for iv in (self.fine_iv, "30m"):
            if self.covers(iv, session):
                for b in self.bars_of(iv, session):
                    if b[0] <= t < b[1]:
                        return b[5], iv
                return None
        return None

    def day_low(self, t):
        """(the running low at t, its interval): inside a session, the lowest low of its intraday bars ended by t
        (the finest series holding any, covering first), None before its first bar ends; outside a session, the
        last completed daily bar's low"""
        session = in_session(t)
        if session is None:
            k = self.n_done(t)
            return (self.days[k - 1][5], "1d") if k else None
        ivs = [self.path_iv(session)] + [iv for iv in (self.fine_iv, "30m", "1h") if iv != self.path_iv(session)]
        for iv in ivs:
            if iv is None:
                continue
            lows = [b[4] for b in self.bars_of(iv, session) if b[1] <= t]
            if lows:
                return min(lows), iv
        return None


def in_session(t):
    """the ET session t falls inside (open <= t < close), or None"""
    d = cal._as_date(float(t))
    return d.isoformat() if cal.is_rth(float(t)) else None


def nbo_source(tape, t0):
    """(where a decision's next-bar price comes from, the hourly series that covered its session) - EQ-06:
      "1h"        an hourly bar of the decision session, after the decision
      "next_open" the next session's open, which is the next bar: the decision came outside the session, or after its
                  last hourly bar started, on hours that cover the session
      "fallback"  the next session's open standing in for the decision session's missing hourly bars (neither the
                  hub's cache nor the canonical store covers it): flagged, never a silent replacement"""
    live = in_session(t0)
    if not live:
        return "next_open", None
    if not tape.covers_hours(live):
        return "fallback", None
    return ("1h" if tape.hours_after(t0, live) else "next_open"), tape.h1_src.get(live)


def session_for(t):
    """the session a decision at t acts on: the first whose close is at or after it (after-close and weekend decisions
    act on the next session)"""
    d = cal._as_date(float(t))
    if cal.is_trading_day(d) and float(t) <= cal.session_close(d):
        return d.isoformat()
    return cal.next_trading_day(d).isoformat()
