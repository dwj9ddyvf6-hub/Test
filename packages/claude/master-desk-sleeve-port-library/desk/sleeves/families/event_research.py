"""Griffith R4 earnings-drift candidates (agentic-trading-desk main @4c8c179c, strategy_tournament.py CANDIDATES and
r4_parallel_strategy_lab.py SPECS): the source registered the rules and froze them, but blocked them on a timestamped
consensus/actual lane it never connected; the desk now runs them on that lane's free public substitute
(desk/feedlib/griffith_earnings.py: Nasdaq's archived earnings calendar — reported EPS, consensus forecast, release
time), exactly as registered:

  griffith_pead_sue        PEAD_1_0_0 "positive_standardized_earnings_surprise_with_post_event_drift", 20 sessions:
                           an announcement whose surprise (actual - consensus) / |consensus| is positive (the
                           source's own normalisation, r4_candidate_evidence: nonzero estimate required);
  griffith_top_decile_sue  PEAD_SUE_20D_1_0_0 "TOP_DECILE_STANDARDIZED_UNEXPECTED_EARNINGS", minimumPriorQuarters 8,
                           20 sessions: SUE = (actual - consensus) / the sample standard deviation of the name's
                           eight prior point-in-time surprises; top decile = at or above the 90th percentile of the
                           universe's SUEs known over the trailing 91 days (at least 10);
  griffith_momentum_pead   MOMENTUM_PEAD_COMBINATION_1_0_0 "liquid_momentum_trend_and_positive_pead", 20 sessions:
                           a positive PEAD event on a name the tournament's LIQUID_MOMENTUM_TREND_1_0_0 marks SETUP on
                           its last completed daily bar (the vendored evaluate_daily_candidate on the Griffith tape).
Timing (point in time): a pre-market report trades at that session's open; every other report at the next session's
open. Exit: market-on-close in the close window of the 20th session (entry session = 1). Portfolio: the R4 lab's
equal-weight research portfolio in calendar time — at each session's first pass every active event is targeted at
1 / (number of active events) of the sleeve. Universe: the frozen SCOPE universe's names (ETFs report no earnings).

Named divergences: Nasdaq's public calendar in place of the Alpha Vantage EARNINGS lane (street EPS and the
Nasdaq/Zacks consensus; history pages carry no release time, so a history day's reports count from the next open);
the top-decile breakpoint window (trailing 91 days) and the equal-weight calendar-time sizing are the port's (the
registry fixed neither); entries at the open after the event is public (the study books the event close)."""
import statistics

from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from ...feedlib import griffith as tape
from ...feedlib import griffith_earnings as earn
from .griffith import FEED, SOURCE, vendored

HORIZON = 20
PRIOR = 8
DECILE_WINDOW_DAYS = 91
MIN_CROSS_SECTION = 10
EARN_FEED = "griffith_earnings_events"
SPECS = {"griffith_pead_sue": "PEAD_1_0_0", "griffith_top_decile_sue": "PEAD_SUE_20D_1_0_0",
         "griffith_momentum_pead": "MOMENTUM_PEAD_COMBINATION_1_0_0"}
SRC = {"PEAD_1_0_0": dict(SOURCE, path="strategy_tournament.py", blob="a7ef5ee9a901899315711e703d99586c9a31f87d",
                          lines="33-36"),
       "MOMENTUM_PEAD_COMBINATION_1_0_0": dict(SOURCE, path="strategy_tournament.py",
                                               blob="a7ef5ee9a901899315711e703d99586c9a31f87d", lines="37-40"),
       "PEAD_SUE_20D_1_0_0": dict(SOURCE, path="r4_parallel_strategy_lab.py",
                                  blob="224b31c200b277bc82fefac552ff22b01a51cdb4", lines="32")}


def universe():
    lab = vendored().r4_parallel_strategy_lab
    return [s for s in tape.tape_symbols() if s not in lab.ETF_BASKET]


def surprise_fraction(r):
    est, act = r.get("consensus"), r.get("eps")
    if est is None or act is None or est == 0:
        return None
    return (act - est) / abs(est)


def sue_series(rows):
    """[(row, SUE)] for each announcement with >= 8 prior point-in-time surprises (sample std of the prior 8)."""
    out, prior = [], []
    for r in rows:
        if r.get("eps") is None or r.get("consensus") is None:
            continue
        s = r["eps"] - r["consensus"]
        if len(prior) >= PRIOR:
            sd = statistics.stdev(prior[-PRIOR:])
            if sd > 0:
                out.append((r, s / sd))
        prior.append(s)
    return out


def entry_session(r):
    """the session whose open first trades a report (pre-market: its own day; else the next session)."""
    d = cal._as_date(r["date"])
    if r.get("time") == "time-pre-market" and cal.is_trading_day(d):
        return d.isoformat()
    return cal.next_trading_day(d).isoformat()


def events(feeds, sleeve, now, arg=None):
    """FEED griffith_earnings_events: the universe's public announcements as of this pass (today's page refreshed
    once per session at the open)."""
    root = sleeve.engine.root if getattr(sleeve, "engine", None) is not None else None
    if root is None:
        return None
    memo = feeds.__dict__.setdefault("_griffith_earn_refresh", {})
    day = cal._as_date(now).isoformat()
    if memo.get("day") != day and cal.is_rth(now):
        earn.refresh_today(root, now)
        memo["day"] = day
    return {"events": earn.known_events(root, universe(), now), "day": day}


def trigger(spec, sym, rows, cross, ls_setup):
    """does the latest public report on `sym` trigger `spec`? -> the triggering row or None."""
    if not rows:
        return None
    r = rows[-1]
    if spec == "PEAD_SUE_20D_1_0_0":
        sues = sue_series(rows)
        if not sues or sues[-1][0] is not r:
            return None
        if len(cross) < MIN_CROSS_SECTION:
            return None
        cut = sorted(cross)[int(0.9 * (len(cross) - 1))] if cross else None
        return r if cut is not None and sues[-1][1] >= cut else None
    sf = surprise_fraction(r)
    if sf is None or sf <= 0:
        return None
    if spec == "MOMENTUM_PEAD_COMBINATION_1_0_0" and not ls_setup:
        return None
    return r


def cross_section(events_by_sym, day):
    """the universe's SUEs on reports public within the trailing 91 days (point in time)."""
    lo = cal._as_date(day).toordinal() - DECILE_WINDOW_DAYS
    out = []
    for rows in events_by_sym.values():
        for r, sue in sue_series(rows):
            if lo <= cal._as_date(r["date"]).toordinal() and entry_session(r) <= day:
                out.append(sue)
    return out


class EarningsDrift(Sleeve):
    def __init__(self, sleeve_id, spec):
        self.spec = spec
        self.engine = None
        self.CONFIG = SleeveConfig(
            sleeve_id=sleeve_id, family="event_research", cadence_s=300, universe=tuple(universe()),
            needs={"feeds": [EARN_FEED] + ([FEED] if spec == "MOMENTUM_PEAD_COMBINATION_1_0_0" else []),
                   "quotes": {"source": "equity"}},
            schedule="rth", params={"spec": spec, "horizon_sessions": HORIZON, "prior_quarters": PRIOR},
            source=dict(SRC[spec], spec=spec), state_schema={"active": "dict", "day": "str|None"})

    def bind(self, engine):
        self.engine = engine

    def _stored(self):
        return (self.engine.store.sleeve_get(self.CONFIG.sleeve_id) or {}) if self.engine is not None else {}

    def wants_tape(self, now):
        return self._stored().get("day") != cal._as_date(now).isoformat()

    def quote_universe(self, now, book):
        st = self._stored()
        return sorted(set(st.get("active") or {}) | set(st.get("pending_entries") or [])
                      | {i.split(":", 1)[1] for i in book.positions if i.startswith("EQ:")})

    def signal(self, view):
        st = dict(view.state or {})
        now, day = float(view.now), view.session
        active = dict(st.get("active") or {})            # sym -> {"entry": session, "event": date}
        held = {i.split(":", 1)[1]: p for i, p in view.positions.items() if i.startswith("EQ:") and float(p["qty"])}
        for s in list(active):
            if s in held:
                active[s]["seen"] = True
            elif active[s].get("seen") or cal.trading_days_between(active[s]["entry"], day) > HORIZON:
                active.pop(s)                             # exited since the last pass (or never filled)
        intents = []
        if st.get("day") != day:
            ev = (view.extra.get(EARN_FEED) or {}).get("events")
            if ev is None:
                self._st = st
                return []
            ls = set()
            if self.spec == "MOMENTUM_PEAD_COMBINATION_1_0_0":
                t = view.extra.get(FEED)
                bars = t.get("bars") if isinstance(t, dict) else None
                if not bars:
                    self._st = st
                    return []
                V = vendored()
                ls = {s for s in ev if s in bars and V.strategy_tournament.evaluate_daily_candidate(
                    "LIQUID_MOMENTUM_TREND_1_0_0", tape.raw_rows(bars[s])).get("status") == "SETUP"}
            cross = cross_section(ev, day) if self.spec == "PEAD_SUE_20D_1_0_0" else []
            new = []
            for s in sorted(ev):
                r = trigger(self.spec, s, ev[s], cross, s in ls)
                if r is None or entry_session(r) != day or s in active or s in held:
                    continue
                active[s] = {"entry": day, "event": r["date"], "eps": r["eps"], "consensus": r["consensus"]}
                new.append(s)
            st.update(day=day, pending_entries=new, cross=len(cross))
        # the calendar-time equal-weight book: every active event at 1/N, re-targeted at the session's first passes
        # (an event in its last session keeps its shares for the market-on-close exit)
        names = sorted(s for s, a in active.items() if cal.trading_days_between(a["entry"], day) + 1 < HORIZON)
        if names and st.get("targeted") != day and all((view.quotes.get(s) or {}).get("ask") or
                                                       (view.quotes.get(s) or {}).get("last") for s in names):
            w = 1.0 / len(names)
            for s in names:
                q = view.quotes.get(s) or {}
                intents.append(Intent("target", s, weight=w, price_hint=q.get("ask") or q.get("last"),
                                      signal_key=f"{s}:{active[s]['event']}:{day}",
                                      reason=f"{self.spec}: event {active[s]['event']} (entered {active[s]['entry']}), "
                                             f"1/{len(names)} of the book", order=OrderSpec(window_s=3600)))
            st["targeted"] = day
        if (cal.minutes_to_close(now) or 99) <= 25:
            for s, a in list(active.items()):
                n = cal.trading_days_between(a["entry"], day) + 1
                if n >= HORIZON and s in held:
                    intents.append(Intent("exit", s, signal_key=f"{s}:{a['event']}:h{HORIZON}",
                                          reason=f"{self.spec}: session {n} of {HORIZON}, exit at the close",
                                          order=OrderSpec(type="market", tif="cls", window_s=3600)))
        st["active"] = active
        self._st = st
        return intents

    def update_state(self, view, intents):
        return getattr(self, "_st", None)


def sleeves():
    return [EarningsDrift(sid, spec) for sid, spec in SPECS.items()]


FEEDS = {EARN_FEED: events}
