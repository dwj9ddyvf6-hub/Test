"""Pair trading: the killed distance + cointegration spec (pair-trading/RESULTS_DEV.md, 05_backtest_dev.py) and its V1
news-filtered variant (pair-trading/IMPROVEMENTS.md section C, killed at feasibility), forward-tested on the half-year
window the desk's formation job builds (desk/feedlib/killed_data.pairs_form_job).

Each day inside the auction window the sleeve rebuilds each pair's normalised adjusted-close series (formation base,
formation mean / sigma of the spread, the trading window forward-filled, bad ticks cleaned as 04_clean_adj.py does),
reads today's z on the live price and steps the pair's state machine; the position decided on day t is held from the
close of t (05_backtest_dev.trade_pair: "position held during day t decided by signals through close t-1"), so
entries and exits are market-on-close orders. $1/$1 self-financing: each leg is half of the pair's capital."""
import numpy as np

from ... import calendar as cal
from ...contract import Intent
from . import common as K

N_PAIRS = 20
PAIR_CAPITAL = K.CAPITAL / N_PAIRS


def step_distance(state, z, entry=2.0, exit_=0.5, stop=4.0):
    """05_backtest_dev.trade_pair's transition on one day's z (state +1 = long A / short B, -1 = short A / long B).
    -> (new state, event) with event in {None, "open", "converge", "adverse_stop"}."""
    if state == 0:
        if z > entry:
            return -1, "open"
        if z < -entry:
            return 1, "open"
        return 0, None
    if state == 1:
        if abs(z) < exit_ or z < -stop:
            return 0, ("adverse_stop" if z < -stop else "converge")
        return 1, None
    if abs(z) < exit_ or z > stop:
        return 0, ("adverse_stop" if z > stop else "converge")
    return -1, None


def step_v1(state, z, held_days, clean, entry=2.5, exit_=0.5, time_stop=10):
    """V1: entry |z| > 2.5 only when neither leg had firm-specific news in the prior 5 sessions; exit |z| < 0.5 or
    10 sessions after entry (the time stop replaces the 4-sigma distance stop)."""
    if state == 0:
        if z > entry and clean:
            return -1, "open"
        if z < -entry and clean:
            return 1, "open"
        return 0, None
    if abs(z) < exit_:
        return 0, "converge"
    if held_days >= time_stop:
        return 0, "time_stop"
    return state, None


def replay_distance(z):
    """the vendored trade_pair over a window-to-date z path with one repeated final element: the state after today's
    z (the source's force-close entry at the last index = still open)."""
    from ...vendor.midna_research import pairs_backtest_dev as P
    n = len(z)
    # trade_pair rebuilds z = (na - nb - mu) / sigma: feed it z directly (mu = 0, sigma = 1, nb = 1000 so the
    # per-day leg returns it also computes stay finite)
    nb = np.full(n + 1, 1000.0)
    zz = np.append(np.asarray(z, float), z[-1])
    na = zz + nb
    res = P.trade_pair(na, nb, 0.0, 1.0, tdates=list(range(n + 1)), emit=True)
    tr = res.get("trades") or []
    if tr and tr[-1]["outcome"] == "force_close" and int(tr[-1]["exit_date"]) == n:
        return int(tr[-1]["direction"]), int(tr[-1]["entry_date"])
    return 0, None


def series_for(view, sym, upto_day, live=None):
    """[(day, adjusted close, volume)] of the completed bars before upto_day, plus the live price for it."""
    bl = ((view.bars or {}).get("1d") or {}).get(sym) or []
    rows = []
    for b in bl:
        d = K.bar_day(b)
        if d < upto_day:
            rows.append((d, float(b["ac"]) if b.get("ac") is not None else float(b["c"]), float(b.get("v") or 0.0)))
    if live is not None:
        rows.append((upto_day, float(live), None))
    return rows


def pair_z(view, p, fs, fe, ts, today, live_a, live_b, cache=None):
    """(z path over the trading window through today, tdays) or None. Formation base / mean / sigma from the current
    adjusted series (the study's one adjusted dataset), trading window forward-filled, bad ticks cleaned. `cache`
    (one per pass) keeps each leg's series for the pairs that share it."""
    from ...feedlib.killed_data import clean_bad_ticks
    cache = {} if cache is None else cache
    for sym, live in ((p["a"], live_a), (p["b"], live_b)):
        if sym not in cache:
            cache[sym] = {d: (c, v) for d, c, v in series_for(view, sym, today, live)}
    da, db = cache[p["a"]], cache[p["b"]]
    if not da or not db:
        return None
    fdays = sorted(d for d in set(da) | set(db) if fs <= d <= fe)
    if not fdays or any(d not in da or d not in db for d in fdays):
        return None
    tdays = sorted(d for d in set(da) | set(db) if ts <= d <= today)
    if not tdays or tdays[-1] != today:
        return None
    out = {}
    for leg, dd, medk in (("a", da, "med_v_a"), ("b", db, "med_v_b")):
        allds = fdays + tdays
        adj = [dd.get(d, (None, None))[0] for d in allds]
        vol = [dd.get(d, (None, None))[1] for d in allds]
        adj = clean_bad_ticks(adj, vol, float(p.get(medk) or 0.0))
        f, t = adj[:len(fdays)], adj[len(fdays):]
        if any(x is None for x in f):
            return None
        last = None
        tt = []
        for x in t:                               # ffill, then bfill
            last = x if x is not None else last
            tt.append(last)
        first = next((x for x in tt if x is not None), None)
        if first is None:
            return None
        tt = [first if x is None else x for x in tt]
        out[leg] = (np.array(f) / f[0], np.array(tt) / f[0])
    fa, ta = out["a"]
    fb, tb_ = out["b"]
    s = fa - fb
    mu, sd = float(s.mean()), float(s.std())
    if not (np.isfinite(sd) and sd > 0):
        return None
    return list((ta - tb_ - mu) / sd), tdays


class _Pairs(K.KilledSleeve):
    SCHEDULE = "close-60:close-11"
    CADENCE = 300
    WHOLE_SHORT = True
    V1 = False
    FEEDS_EXTRA = []

    _legs = set()

    def bar_symbols(self, spec, now, book=None):
        return sorted(self._legs)

    def plan(self, view, st, tb):
        from ...feedlib.killed_data import window_of
        doc = (view.extra or {}).get("killed_pairs")
        d = tb.today
        if not doc or not cal.is_trading_day(d):
            return []
        fs, fe, ts, te = window_of(d)
        if doc.get("trading", [None])[0] != ts:
            return []
        self._legs = {p["a"] for p in doc["pairs"]} | {p["b"] for p in doc["pairs"]}
        self._extra_want = set(self._legs)
        if not K.in_moc_window(view.now) or st.get("day") == d:
            return []
        news = (view.extra or {}).get("killed_pairs_news") if self.V1 else None
        last_day = te if cal.is_trading_day(te) else cal.prev_trading_day(te).isoformat()
        if self.V1 and not news and d < last_day:
            return []                                     # the gate's inputs for today are not written yet
        # (the window's last session closes every pair with or without the gate: closing reads no news, and a skipped
        #  force close would carry the old window's legs into a new window that starts from empty pair state)
        pst = st.setdefault("pairs", {})
        if st.get("window") != ts:
            st["window"], pst = ts, {}
            st["pairs"] = pst
        obs, legs_cache = [], {}
        for k, p in enumerate(doc["pairs"]):
            key = f"{p['a']}/{p['b']}"
            la, lb = K.fresh_last(view, p["a"]), K.fresh_last(view, p["b"])
            if la is None or lb is None:
                continue
            got = pair_z(view, p, fs, fe, ts, d, la, lb, legs_cache)
            if got is None:
                continue
            z, tdays = got
            cur = pst.get(key)
            if cur is None:                               # birth / new window: the source's state since the window start
                if self.V1:
                    cur = {"state": 0, "entry_day": None}
                else:
                    s0, e0 = replay_distance(z[:-1]) if len(z) > 1 else (0, None)
                    cur = {"state": s0, "entry_day": tdays[e0] if e0 is not None else None, "warm": True}
                    if s0:
                        self._open(tb, p, s0, d, f"warm start: open since {cur['entry_day']}")
                pst[key] = cur
            zt = z[-1]
            if d >= last_day:                             # trading-window end: force close, no new entries
                if cur["state"]:
                    self._close(tb, p, "window end (force close)")
                cur.update(state=0, entry_day=None, event="force_close" if cur["state"] else cur.get("event"))
                continue
            if self.V1:
                legs = (news.get("legs") or {})
                clean = not any((legs.get(s) or {}).get(f) for s in (p["a"], p["b"]) for f in ("news", "earnings", "exdiv"))
                held = K.sessions_between(cur["entry_day"], d) if cur.get("entry_day") else 0
                new, ev = step_v1(cur["state"], zt, held, clean)
            else:
                new, ev = step_distance(cur["state"], zt)
            if ev == "open":
                self._open(tb, p, new, d, f"z {zt:+.3f}")
                cur.update(state=new, entry_day=d, event="open")
            elif ev:
                self._close(tb, p, f"{ev} at z {zt:+.3f}")
                cur.update(state=0, entry_day=None, event=ev)
            obs.append(Intent("signal", p["a"], signal_key=f"pz:{d}:{key}",
                              reason=f"{key} z {zt:+.3f} state {cur['state']}", meta={"z": round(zt, 6)}))
        st["day"] = d
        return obs

    def _open(self, tb, p, direction, d, why):
        tb.add(p["a"], direction, PAIR_CAPITAL / 2, f"pair:{p['a']}/{p['b']}", d, "close", None, None, why=why,
               event=f"{d}:a")
        tb.add(p["b"], -direction, PAIR_CAPITAL / 2, f"pair:{p['a']}/{p['b']}", d, "close", None, None, why=why,
               event=f"{d}:b")

    def _close(self, tb, p, why):
        for t in tb.open_or_planned(arm=f"pair:{p['a']}/{p['b']}"):
            if t["status"] == "held":
                tb.close_now(t, why, at="close")
            else:
                t["status"], t["void_why"] = "void", why


class PairsDistance(_Pairs):
    """RESULTS_DEV.md / 05_backtest_dev.py (killed): top-20 Gatev SSD pairs of the 12-month formation, entry |z| > 2.0
    (formation sigma), exit |z| < 0.5, adverse 4-sigma stop, force-close at the 6-month window end; pairs may reopen.
    The Engle-Granger ADF(1) top-20 (the secondary arm) is formed and recorded with the formation, not traded."""
    SLEEVE_ID = "killed_pairs_distance_coint"
    SOURCE = K.source("pair-trading/code/05_backtest_dev.py", "b308b58eda6864f07cdc79242fb3d36feb4b51a0",
                      results={"path": K.RESEARCH + "pair-trading/RESULTS_DEV.md",
                               "blob": "be35c0843bd1e49714ff500debf6e9e1862f3f80"},
                      prereg={"path": K.RESEARCH + "pair-trading/PRE_REGISTRATION.md",
                              "blob": "e16a7bbb746f1c4ff6afa3b08e5be07463842054"},
                      filters={"path": K.RESEARCH + "pair-trading/code/03_filter_and_fetch_adj.py",
                               "blob": "bcc2ccf86636b53dc4fef157cf79f641ea4bf380"},
                      cleaning={"path": K.RESEARCH + "pair-trading/code/04_clean_adj.py",
                                "blob": "f28890654bbb680ae89b35240b24c5b5bae64776"},
                      vendored="desk/vendor/midna_research/pairs_backtest_dev.py")
    NEEDS = {"feeds": ["killed_pairs"], "bars": [{"source": "equity", "interval": "1d", "n": 420, "symbols_for": True}],
             "quotes": {"source": "equity"}}
    PARAMS = {"pairs": N_PAIRS, "entry_z": 2.0, "exit_z": 0.5, "stop_z": 4.0, "pair_capital": PAIR_CAPITAL,
              "formation": "12 months, half-year windows (Jan-Jun from the prior calendar year, Jul-Dec from Jul-Jun)",
              "removed_gates": [K.LONG_ONLY_RAIL]}
    DIVERGENCES = [
        "universe: NASDAQ Trader symbol directories (NYSE / NASDAQ / AMEX listings, test issues dropped) instead of "
        "Alpaca /v2/assets (a broker endpoint this desk does not call); the 240/252 completeness, $1M median dollar "
        "volume, $5 median price and complete-formation filters are the study's",
        "today's z is read on the live price inside the auction window and the trade is the market-on-close order "
        "(the study decided on the close itself)",
        "birth / a new window starts from the vendored trade_pair replayed over the window to date (an open replay "
        "position is opened at that close); later days step the same transition on each day's z",
        "the adjusted series is the hub's (Alpaca adjustment=all when keyed, else Yahoo's dividend-adjusted close); "
        "the study's borrow drag (35bp/yr) is the venue's",
        "04_clean_adj's bad-print rule cleans the history the sleeve rebuilds each day, but the day's decision reads "
        "the live price (the study dropped a bad print after the fact, and back-filled a dropped first-window bar "
        "from the next session)",
    ]


class PairsNewsFiltered(_Pairs):
    """pair-trading/IMPROVEMENTS.md section C (V1, killed at feasibility for lack of PIT news): the same formation and
    top-20; entry |z| > 2.5 only if neither leg had firm-specific news (earnings, dividend, abnormal news) in the
    prior 5 trading days; exit |z| < 0.5, a 10-trading-day time stop, or the window end."""
    SLEEVE_ID = "killed_pairs_news_filtered"
    V1 = True
    SOURCE = K.source("pair-trading/v1_feasibility_death_2026-10-02.md", "31334e3522772c234fecb4d8ccffb3e5d44e4dcb",
                      spec={"path": K.RESEARCH + "pair-trading/IMPROVEMENTS.md", "section": "C (V1)"},
                      base="pair-trading/code/05_backtest_dev.py (formation)")
    NEEDS = {"feeds": ["killed_pairs", "killed_pairs_news"],
             "bars": [{"source": "equity", "interval": "1d", "n": 420, "symbols_for": True}],
             "quotes": {"source": "equity"}}
    PARAMS = {"pairs": N_PAIRS, "entry_z": 2.5, "exit_z": 0.5, "time_stop_sessions": 10, "news_window_sessions": 5,
              "pair_capital": PAIR_CAPITAL, "removed_gates": [K.LONG_ONLY_RAIL]}
    DIVERGENCES = PairsDistance.DIVERGENCES[:2] + [
        "news: Alpaca /v1beta1/news items naming a leg (the T3-18 probe's source and its contamination rule: >= 1 "
        "item) when keyed, else Yahoo Finance RSS headlines; earnings and ex-dividend dates from Nasdaq's public "
        "calendars; window = the 5 sessions before today through the gate job's last run before the decision (40-75 "
        "minutes before the close; the study's 'prior 5 trading days' excluded the decision day: measured, "
        "tools/parity/killed_pairs.py v1.literal_*)",
        "the state machine starts flat at birth (the gate's news history before birth is not reconstructed)",
    ]
