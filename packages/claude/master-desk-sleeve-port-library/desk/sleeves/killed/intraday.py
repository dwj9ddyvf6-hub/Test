"""Intraday killed studies: Gao et al. intraday momentum (SPY/QQQ 5m), RSIxOBV intraday (5m), the six short candidates
(30m RTH + daily). Decisions are made on the live tape at the study's own clock; trades go through the tranche
ledger (common.TrancheBook)."""
import math
from datetime import datetime, timedelta

from ... import calendar as cal
from ...contract import Intent
from ...util import ET
from . import common as K
from .daily import BASKET, deoverlap  # noqa: F401  (deoverlap re-exported for the harness)


def day_map(bars, day):
    """{"HH:MM": bar} of the bars starting on ET date `day` (bar-start stamps)."""
    out = {}
    for b in bars or ():
        t = K.bar_et(b)
        if t.date().isoformat() == day:
            out[t.strftime("%H:%M")] = b
    return out


# -- Gao, Han, Li, Zhou (2018) market intraday momentum ---------------------------------------------------------------
FIRST_HM = ["09:30", "09:35", "09:40", "09:45", "09:50", "09:55"]
LAST_HM = ["15:30", "15:35", "15:40", "15:45", "15:50", "15:55"]


def r_first(m):
    """the study's r_first = c[09:55] / o[09:30] - 1 when the six first-window bars exist with volume, else None
    (vendored intraday_momentum_2026_10_02.day_returns / eligible_days, first-window half)."""
    if not all(h in m for h in FIRST_HM):
        return None
    if sum(m[h].get("v") or 0 for h in FIRST_HM) == 0:
        return None
    return m["09:55"]["c"] / m["09:30"]["o"] - 1.0


class IntradayMomentumGao(K.KilledSleeve):
    """intraday_momentum_prereg_2026-10-02.md Test 2 (the tradable version) on SPY (primary) and QQQ (secondary):
    every eligible day at 15:30 ET take a position in sign(r_first) (long if > 0, short if < 0), r_first = the
    09:30-10:00 return off 5-minute bars; exit at 16:00 (close of the 15:55 bar). Half-days (close before 16:00),
    a missing first-window bar or a zero-volume first window: no trade."""
    SLEEVE_ID = "killed_intraday_momentum_gao"
    SOURCE = K.source("intraday_momentum_2026-10-02.py", "515fe5e6af7d718c451aee461a6b186dbaa7f3f7",
                      prereg={"path": K.RESEARCH + "intraday_momentum_prereg_2026-10-02.md",
                              "blob": "69bfc5ee794527c2ca362a2c2e4cfef0beaf692c"},
                      results={"path": K.RESEARCH + "intraday_momentum_2026-10-02.md",
                               "blob": "595dd539e1c6853b14c76f1fd22ada9813184736"},
                      vendored="desk/vendor/midna_research/intraday_momentum_2026_10_02.py")
    UNIVERSE = ("SPY", "QQQ")
    SCHEDULE = "close-31:close-9"
    CADENCE = 60
    WHOLE_SHORT = False
    NEEDS = {"bars": [{"source": "equity", "interval": "5m", "n": 120}],
             "quotes": {"source": "equity", "symbols": ["SPY", "QQQ"]}}
    PARAMS = {"first_window": "09:30-10:00", "entry": "15:30", "exit": "16:00 (market-on-close)",
              "notional": K.CAPITAL / 2, "removed_gates": [K.LONG_ONLY_RAIL]}
    DIVERGENCES = [
        "entry is the first pass at/after 15:30:00 (marketable) instead of the 15:30 bar's open print; exit is the "
        "market-on-close order instead of the 15:55 bar's close",
        "the last-window completeness / zero-volume exclusions cannot be known at 15:30 - the trade is taken and "
        "the exclusion is the post-hoc reader's",
        "5-minute bars are the hub's equity source (Alpaca SIP when keyed, else Yahoo's consolidated 5m bars)",
    ]

    def plan(self, view, st, tb):
        d = tb.today
        if not cal.is_trading_day(d) or st.get("day") == d:
            return []
        if cal.close_minutes(d) != 16 * 60:
            st["day"] = d
            return [Intent("signal", "SPY", signal_key=f"gao:{d}:half", reason=f"{d}: half-day, no last-30 window")]
        if view.now < cal.session_close(d) - 30 * 60 or not K.before_cutoff(view.now):
            return []
        obs = []
        for sym in self.UNIVERSE:
            m = day_map(((view.bars or {}).get("5m") or {}).get(sym), d)
            rf = r_first(m)
            if rf is None or rf == 0:
                obs.append(Intent("signal", sym, signal_key=f"gao:{d}:{sym}:skip",
                                  reason=f"{d}: not eligible (first window incomplete / zero volume / r_first = 0)"))
                continue
            tb.add(sym, 1 if rf > 0 else -1, K.CAPITAL / 2, "gao", d, "open", d, "close",
                   why=f"r_first {rf:+.5f}", event=d)
        st["day"] = d
        return obs


# -- RSI x OBV intraday (the validated bucket) -------------------------------------------------------------------
RSIOBV_INTRADAY = ("MU", "ARM", "SNDK", "WDC", "CLS", "ANF", "CVNA", "FFIV")
FWD_BARS = (24, 48, 96)          # 2h / 4h / 8h of 5-minute bars


def rsiobv_bucket(divs):
    """the validation-pass target: BuR + RSI indicator + STRONG/SUPERSTRONG -> {knowable_index: div}."""
    out = {}
    for d in divs:
        if d["type"] == "BuR" and d["indicator"] == "RSI" and d["strength"] in ("STRONG", "SUPERSTRONG"):
            out.setdefault(d["knowable_index"], d)
    return out


def deoverlap_time(times, last_kept=None, gap_s=86400):
    """one signal per symbol per 24h, earliest kept: a signal is kept when >= 24h after the last kept one."""
    kept = []
    for t in sorted(times):
        if last_kept is None or t - last_kept >= gap_s:
            kept.append(t)
            last_kept = t
    return kept


class RsiObvIntraday(K.KilledSleeve):
    """rsiobv_backtest_2026-10-01.md validation pass (the bucket the 10-test battery killed): bullish-regular RSI
    divergences STRONG/SUPERSTRONG (rsiobv.scan_divergences, RSI 8/13/21, lookback 8) on 5-minute bars of the 8
    original names, de-overlapped to one signal per symbol per 24h (earliest kept); LONG at the next bar's open after
    the knowable bar; three forwards: exit at the close of bar ki+24 / ki+48 / ki+96 (2h / 4h / 8h)."""
    SLEEVE_ID = "killed_rsiobv_intraday"
    SOURCE = K.source("rsiobv_backtest_2026-10-01.md", "7dff6133a983674830d5bf9866175002686e215a",
                      code={"path": K.RESEARCH + "rsiobv_backtest.py", "blob": "587bc58c1fd77547d86e9897ab3215428189ccb9"},
                      scanner={"path": K.RESEARCH + "rsiobv.py", "blob": "9421874ce6074a12de52edc4b53431a05717caa9",
                               "vendored": "desk/vendor/old_desk_research/rsiobv.py"})
    UNIVERSE = RSIOBV_INTRADAY
    SCHEDULE = "rth"
    CADENCE = 60
    NEEDS = {"bars": [{"source": "equity", "interval": "5m", "n": 600}], "quotes": {"source": "equity"}}
    PARAMS = {"bucket": "BuR RSI STRONG/SUPERSTRONG", "forwards_bars": list(FWD_BARS), "deoverlap": "24h",
              "notional_per_tranche": K.CAPITAL / 24, "removed_gates": []}
    DIVERGENCES = [
        "US equities route only in the regular session: a signal knowable on an extended-hours bar enters at the "
        "next regular-session pass, and an exit whose bar closes outside the session executes at the next one "
        "(the study's 5m SIP tape includes 04:00-20:00 bars; core capability: extended-hours equity routing)",
        "the scan runs on the last 600 5-minute bars at every pass (divergences at the newest bars are identical to "
        "a full-history scan); the 24h de-overlap chain starts at the sleeve's birth",
        "RSI+OBV agreement is classified at the knowable bar: an OBV divergence completing up to 3 bars later "
        "(which the study's whole-series scan merged into the RSI divergence - a 3-bar lookahead) does not "
        "reclassify a signal already taken (measured: tools/parity/killed_rsiobv.py)",
        "without Alpaca keys the hub serves Yahoo's regular-session 5m bars (no extended hours): bar counts then "
        "run on the regular-session grid",
        "Alpaca's free plan publishes SIP bars 15 minutes late: a signal is taken, and a leg closed, at the first "
        "pass after its bar is published (about 16 minutes after the bar closes), not at the next bar's open",
    ]

    def plan(self, view, st, tb):
        if not K.in_rth(view.now):
            return []
        from ...vendor.old_desk_research import rsiobv as R
        last_t = st.setdefault("last_t", {})            # newest knowable bar already processed per symbol
        kept_t = st.setdefault("kept_t", {})            # the de-overlap chain (last kept signal time)
        legs = st.setdefault("legs", {})                # tranche id -> [symbol, knowable bar t, exit bar count]
        for sym in self.UNIVERSE:
            bl = ((view.bars or {}).get("5m") or {}).get(sym) or []
            if len(bl) < 200:
                continue
            bars = [{"t": float(b["t"]), "o": float(b["o"]), "h": float(b["h"]), "l": float(b["l"]),
                     "c": float(b["c"]), "v": float(b.get("v") or 0.0)} for b in bl]
            times = [b["t"] for b in bars]
            # exits: bars elapsed since each open leg's knowable bar
            for tid, (lsym, kt, k) in list(legs.items()):
                if lsym != sym:
                    continue
                tr = next((x for x in tb.tr if x["id"] == tid), None)
                if tr is None or tr["status"] in ("closed", "void"):
                    legs.pop(tid)
                    continue
                if tr["status"] == "held" and sum(1 for t in times if t > kt) >= k:
                    tb.close_now(tr, f"bar ki+{k} closed")
            prev = last_t.get(sym)
            if prev is not None and times[-1] == prev:
                continue                                # no new bar since the last pass: no signal can be new
            sig = rsiobv_bucket(R.scan_divergences(bars, rsi_periods=(8, 13, 21), rsi_lookbacks=(8,)))
            new = sorted(times[i] for i in sig if prev is None or times[i] > prev)
            last_t[sym] = times[-1]
            if prev is None:
                continue                                # birth: the chain starts with the next bar
            for kt in deoverlap_time(new, kept_t.get(sym)):
                kept_t[sym] = kt
                for k in FWD_BARS:
                    tr = tb.add(sym, +1, K.CAPITAL / 24, f"bur_strong:{k}", tb.today, "open", None, None,
                                why=f"BuR RSI strong knowable at {datetime.fromtimestamp(kt, tz=ET):%m-%d %H:%M}",
                                event=int(kt))
                    if tr:
                        legs[tr["id"]] = [sym, kt, k]
        return []


# -- short candidates (6) -----------------------------------------------------------------------------------------
def rth_days(bars30):
    """{day: [bars in time order]} keeping regular-session 30-minute bars (09:30 <= start < close)."""
    out = {}
    for b in bars30 or ():
        t = K.bar_et(b)
        d = t.date().isoformat()
        if not cal.is_trading_day(d):
            continue
        m = t.hour * 60 + t.minute
        if 9 * 60 + 30 <= m < cal.close_minutes(d):
            out.setdefault(d, []).append(b)
    for d in out:
        out[d].sort(key=lambda b: b["t"])
    return out


def pm_returns(days, upto):
    """[(day, last-2h, last-hour)] for the full 13-bar days before `upto` (c[12]/c[8]-1, c[12]/c[10]-1)."""
    out = []
    for d in sorted(days):
        if d >= upto:
            continue
        bl = days[d]
        if len(bl) != 13:
            continue
        c = [float(b["c"]) for b in bl]
        out.append((d, c[12] / c[8] - 1.0, c[12] / c[10] - 1.0))
    return out


def top_quintile(value, history, min_obs=63, window=252):
    """value in the top quintile of the trailing window (strictly above its 80th percentile, linear)."""
    h = sorted(history[-window:])
    if len(h) < min_obs:
        return None
    pos = 0.8 * (len(h) - 1)
    lo = int(math.floor(pos))
    q = h[lo] + (h[min(lo + 1, len(h) - 1)] - h[lo]) * (pos - lo)
    return value > q


def wilder_atr(bars, n=14):
    tr = []
    for i, b in enumerate(bars):
        h, l = float(b["h"]), float(b["l"])
        if i == 0:
            tr.append(h - l)
        else:
            pc = float(bars[i - 1]["c"])
            tr.append(max(h - l, abs(h - pc), abs(l - pc)))
    if len(tr) < n:
        return None
    a = sum(tr[:n]) / n
    for x in tr[n:]:
        a = (a * (n - 1) + x) / n
    return a


def extended(daily, close_now=None):
    """C3 on the last bar (its close replaced by close_now when deciding before the print): (c - min20)/(max20 -
    min20) >= 0.95 over highs/lows incl. t AND c > mean20 + 1.5 x ATR14 (Wilder). -> (bool, mean20)"""
    if len(daily) < 21:
        return False, None
    bl = list(daily)
    if close_now is not None:
        last = dict(bl[-1], c=close_now, h=max(float(bl[-1]["h"]), close_now), l=min(float(bl[-1]["l"]), close_now))
        bl[-1] = last
    w = bl[-20:]
    hi, lo = max(float(b["h"]) for b in w), min(float(b["l"]) for b in w)
    c = float(bl[-1]["c"])
    mean20 = sum(float(b["c"]) for b in w) / 20.0
    atr = wilder_atr(bl, 14)
    if hi <= lo or atr is None:
        return False, mean20
    return ((c - lo) / (hi - lo) >= 0.95 and c > mean20 + 1.5 * atr), mean20


def strong_close(b):
    h, l, c = float(b["h"]), float(b["l"]), float(b["c"])
    return h > l and (c - l) / (h - l) >= 0.8


class ShortCandidates(K.KilledSleeve):
    """short_candidates_prereg_2026-10-02.md, all six candidates (every tested exit) on the 41 names:
    C1  last-2h return (c[12]/c[8]-1 of the 13 RTH 30m bars) in the symbol's trailing-252d top quintile (>= 63 obs)
        -> SHORT at close_t; (a) cover close_{t+1}, (b) cover open_{t+1}
    C2  last-hour return (c[12]/c[10]-1) top quintile -> SHORT at close_t, cover close_{t+1}
    C3  (c-min20)/(max20-min20) >= 0.95 AND c > mean20 + 1.5 ATR14 -> SHORT at close_t; (a) cover close_{t+3},
        (b) cover at the first touch of mean20 (fixed at t) on t+1..t+3, else close_{t+3}
    C4  closes of t-1 and t both in the top 20% of their day range -> SHORT at open_{t+1}, cover close_{t+2}
        (every streak day signals; overlapping holds allowed)
    C5  gap (open_t/close_{t-1}-1) >= 2% AND open_t >= 0.98 x trailing-252d high -> SHORT at open_t; (a) cover at
        close_{t-1} if the first 30m bar trades there, else at the first-30m close; (b) cover at the first-30m close
    C6  BeR RSI STRONG/SUPERSTRONG divergences on 30m bars, one per symbol per calendar day (earliest) -> LONG at the
        next 30m open; holds 4 / 8 / 16 bars"""
    SLEEVE_ID = "killed_short_candidates"
    SOURCE = K.source("short_candidates_prereg_2026-10-02.md", "97c9c3450b1f3aee037e508f379f54c9d7adec93",
                      results={"path": K.RESEARCH + "short_candidates_2026-10-02.md",
                               "blob": "e4a8001421f9f8d07f8b6d272c94e783918c2114"},
                      scanner="desk/vendor/old_desk_research/rsiobv.py (blob 9421874c)")
    UNIVERSE = BASKET
    SCHEDULE = "rth"
    CADENCE = 60
    NEEDS = {"bars": [{"source": "equity", "interval": "30m", "n": 3400},
                      {"source": "equity_split", "interval": "1d", "n": 260}],
             "quotes": {"source": "equity"}}
    PARAMS = {"notional_per_tranche": K.CAPITAL / 100, "quintile_window": 252, "min_obs": 63,
              "c6_holds_bars": [4, 8, 16], "removed_gates": [K.LONG_ONLY_RAIL]}
    DIVERGENCES = [
        "C1/C2/C3 decide inside the auction window on the live price as the day's close (the 15:30 bar is still "
        "forming) and enter market-on-close",
        "C1/C2 quintiles: the symbol's previous <= 252 full 13-bar days (the day itself excluded), top = strictly "
        "above the linear 80th percentile; the 63-observation floor holds the arm until the history exists",
        "C5 reads open_t as the first quote of the session; touch exits (C3b mean20, C5a prior close) fire at the "
        "first pass the live price reaches the level and fill at the market, not at the level (measured: "
        "tools/parity/killed_short.py)",
        "C6 exits at the pass after its exit bar closes (market-on-close when the exit bar is the session's last)",
        "RSI+OBV agreement is classified at the knowable bar: an OBV divergence completing up to 3 bars later "
        "(which the study's whole-series scan merged into the RSI divergence - a 3-bar lookahead) does not "
        "reclassify a signal already taken, nor does a later RSI divergence taking that OBV match (measured: "
        "tools/parity/killed_short.py; the 5m bucket: tools/parity/killed_rsiobv.py)",
        "C6 scans the last 30 sessions of 30-minute bars at every pass (the study scanned its whole history once; the "
        "newest bar's signal measured against the causal full history: tools/parity/killed_short.py)",
        "early closes: the study's 30-minute file kept only 13-bar sessions, so it had none - here C6 scans an early "
        "close's 7 bars and counts them in its holds, C5 trades an early-close gap (the study had no first 30-minute "
        "bar there) and C1 / C2 exit on one (the study's price for that exit is not recoverable); measured: "
        "tools/parity/killed_short.py",
        "a regular session missing a 30-minute bar (a halt): the pre-registration required >= 12 bars on day t, the "
        "reported run kept only 13-bar sessions; C1 / C2 need c[8] and c[10] of day t and count only 13-bar sessions "
        "in their quintiles, C6 scans the bars there are (not in the parity corpus, whose sessions are complete)",
        "30-minute bars are Alpaca SIP (regular-session filtered); without Alpaca keys the arms needing 30m bars wait",
        "Alpaca's free plan publishes SIP bars 15 minutes late: C1 / C2 decide on c[8], c[10] and the live price without waiting for the 15:00 bar; C3's forming bar misses the latest unpublished half hour's range (the live price is in it); C6 sees its 30-minute bar when it is published",
    ]

    def quote_universe(self, now, book=None):
        base = set(super().quote_universe(now, book))
        m = cal.minutes_to_close(now)
        if cal.is_rth(now) and (now - cal.session_open(K.et_day(now)) <= 35 * 60 or (m is not None and m <= 35)):
            base |= set(self.UNIVERSE)
        return sorted(base)

    def plan(self, view, st, tb):
        if not K.in_rth(view.now):
            return []
        from ...vendor.old_desk_research import rsiobv as R
        d, now = tb.today, view.now
        b30 = (view.bars or {}).get("30m") or {}
        b1d = (view.bars or {}).get("1d") or {}
        n = K.CAPITAL / 100
        mins_open = (now - cal.session_open(d)) / 60.0
        # -- the open: C4 entries, C5 entries (first pass of the session) ----------------------------------------
        if st.get("open_day") != d:
            st["open_day"] = d
            t = K.add_sessions(d, -1)
            for sym in self.UNIVERSE:
                daily = [b for b in K.closed_daily(b1d.get(sym) or [], now) if K.bar_day(b) <= t]
                if len(daily) >= 2 and K.bar_day(daily[-1]) == t:
                    if strong_close(daily[-1]) and strong_close(daily[-2]):
                        tb.add(sym, -1, n, "C4", d, "open", K.add_sessions(d, 1), "close",
                               why=f"strong closes {K.bar_day(daily[-2])} + {t}", event=t)
                q = (view.quotes or {}).get(sym) or {}
                o = q.get("day_open") or K.fresh_last(view, sym)
                if o and len(daily) >= 2 and K.bar_day(daily[-1]) == t and mins_open <= 30:
                    pc = float(daily[-1]["c"])
                    hi252 = max(float(b["h"]) for b in daily[-252:])
                    if pc > 0 and (o - pc) / pc >= 0.02 and o >= 0.98 * hi252:
                        for arm in ("C5a", "C5b"):
                            tb.add(sym, -1, n, arm, d, "open", None, None, why=f"gap {o / pc - 1:+.4f} at the high",
                                   event=d, prev_close=pc)
        # -- C5 exits: the first-30m close, or C5a's touch of the prior close ------------------------------------
        for tr in tb.held():
            if tr["arm"] in ("C5a", "C5b") and tr["enter_day"] == d:
                px = K.fresh_last(view, tr["sym"])
                if mins_open >= 30:
                    tb.close_now(tr, "first-30m close")
                elif tr["arm"] == "C5a" and px is not None and px <= tr["prev_close"]:
                    tb.close_now(tr, "touched the prior close")
            elif tr["arm"] in ("C5a", "C5b") and tr["enter_day"] < d:
                tb.close_now(tr, "first-30m close (overdue)")
        # -- C3b: the mean20 touch on t+1..t+3 --------------------------------------------------------------------
        for tr in tb.held(arm="C3b"):
            px = K.fresh_last(view, tr["sym"])
            if tr["enter_day"] < d <= tr["exit_day"] and px is not None and px <= tr["mean20"]:
                tb.close_now(tr, f"touched mean20 {tr['mean20']:.4f}")
        # -- the auction window: C1, C2, C3 entries --------------------------------------------------------------
        if K.in_moc_window(now) and st.get("moc_day") != d:
            st["moc_day"] = d
            for sym in self.UNIVERSE:
                px = K.fresh_last(view, sym)
                if px is None:
                    continue
                days = rth_days(b30.get(sym))
                today_bars = days.get(d) or []
                hist = pm_returns(days, d)
                c = {}
                for b in today_bars:
                    t = K.bar_et(b)
                    c[(t.hour * 60 + t.minute - 570) // 30] = float(b["c"])
                if 8 in c and 10 in c:                       # c[8], c[10] closed (the 15:00 bar may lag)
                    r2, r1 = px / c[8] - 1.0, px / c[10] - 1.0
                    if top_quintile(r2, [h[1] for h in hist]):
                        tb.add(sym, -1, n, "C1a", d, "close", K.add_sessions(d, 1), "close", why=f"last-2h {r2:+.4f}",
                               event=d)
                        tb.add(sym, -1, n, "C1b", d, "close", K.add_sessions(d, 1), "open", why=f"last-2h {r2:+.4f}",
                               event=d)
                    if top_quintile(r1, [h[2] for h in hist]):
                        tb.add(sym, -1, n, "C2", d, "close", K.add_sessions(d, 1), "close", why=f"last-hour {r1:+.4f}",
                               event=d)
                daily = [b for b in K.closed_daily(b1d.get(sym) or [], now) if K.bar_day(b) < d]
                q = (view.quotes or {}).get(sym) or {}
                forming = None
                if q.get("day_high") and q.get("day_low"):           # the snapshot's session bar (Alpaca)
                    forming = {"t": now, "o": q.get("day_open") or px, "h": max(float(q["day_high"]), px),
                               "l": min(float(q["day_low"]), px), "c": px}
                elif today_bars:                                      # else the session's 30m bars so far
                    forming = {"t": now, "o": float(today_bars[0]["o"]),
                               "h": max([float(b["h"]) for b in today_bars] + [px]),
                               "l": min([float(b["l"]) for b in today_bars] + [px]), "c": px}
                if daily and forming:
                    ok, mean20 = extended(daily + [forming])
                    if ok:
                        x3 = K.add_sessions(d, 3)
                        tb.add(sym, -1, n, "C3a", d, "close", x3, "close", why="extended", event=d)
                        tb.add(sym, -1, n, "C3b", d, "close", x3, "close", why="extended", event=d,
                               mean20=round(mean20, 6))
        # -- C6: BeR RSI strong on 30m bars, one per symbol per day, LONG next 30m open -------------------------
        seen = st.setdefault("c6_last", {})
        legs = st.setdefault("c6_legs", {})
        for sym in self.UNIVERSE:
            days = rth_days(b30.get(sym))
            bars = [dict(t=float(b["t"]), o=float(b["o"]), h=float(b["h"]), l=float(b["l"]), c=float(b["c"]),
                         v=float(b.get("v") or 0.0)) for dd in sorted(days)[-30:] for b in days[dd]]
            if len(bars) < 100:
                continue
            times = [b["t"] for b in bars]
            for tid, (lsym, kt, k) in list(legs.items()):
                if lsym != sym:
                    continue
                tr = next((x for x in tb.tr if x["id"] == tid), None)
                if tr is None or tr["status"] in ("closed", "void"):
                    legs.pop(tid)
                    continue
                after = [t for t in times if t > kt]
                if tr["status"] == "held" and len(after) >= k:
                    tb.close_now(tr, f"{k} bars held")
                elif tr["status"] == "held" and len(after) == k - 1 and \
                        K.bar_et({"t": after[-1]}).date().isoformat() == d and K.in_moc_window(now) and \
                        cal.session_close(d) - (after[-1] + 1800) <= 1800:
                    tb.close_now(tr, f"{k} bars held (exit bar is the session's last)", at="close")
            prev = seen.get(sym)
            seen[sym] = times[-1]
            if prev is None or times[-1] == prev:
                continue                                # birth, or no new bar since the last pass: nothing new
            divs = R.scan_divergences(bars, rsi_periods=(8, 13, 21), rsi_lookbacks=(8,))
            new = {}
            for dv in divs:
                if dv["type"] == "BeR" and dv["indicator"] == "RSI" and dv["strength"] in ("STRONG", "SUPERSTRONG"):
                    kt = times[dv["knowable_index"]]
                    if kt > prev:
                        new.setdefault(K.bar_et({"t": kt}).date().isoformat(), []).append(kt)
            kept_days = st.setdefault("c6_days", {})
            for day, kts in new.items():
                if kept_days.get(sym) == day:
                    continue
                kt = min(kts)
                kept_days[sym] = day
                for k in (4, 8, 16):
                    tr = tb.add(sym, +1, n, f"C6:{k}", d, "open", None, None, why="BeR RSI strong fade (long)",
                                event=int(kt))
                    if tr:
                        legs[tr["id"]] = [sym, kt, k]
        return []
