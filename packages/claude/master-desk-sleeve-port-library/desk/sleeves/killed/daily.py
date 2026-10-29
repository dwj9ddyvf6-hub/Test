"""Daily-bar killed studies: golden cross, Leader-1d long and short, naive 20d breakout, RSIxOBV daily.

Each decides on the last completed session t (the closed daily bar) at the first pass of session t+1 and writes
its trades into the tranche ledger (common.TrancheBook) with the study's own entry and exit sessions."""
from ... import calendar as cal
from ...contract import Intent
from ...vendor.universes.old_desk import __file__ as _UNIV
from . import common as K

UNIV_DIR = __import__("os").path.dirname(_UNIV)


def _lines(name):
    with open(__import__("os").path.join(UNIV_DIR, name)) as f:
        return tuple(dict.fromkeys(l.strip().upper() for l in f if l.strip() and not l.startswith("#")))


def _basket():
    import json
    import os
    with open(os.path.join(UNIV_DIR, "basket.json")) as f:
        return tuple(s["symbol"] for s in json.load(f)["symbols"])


GENOME = _lines("genome_universe_1838.txt")
BASKET = _basket()                    # basket.json minus SIVEF (removed 2026-10-04) = the studies' 41 names


signal_day = K.signal_day


def daily_upto(view, sym, t, iv="1d"):
    """the closed daily bars of sym through session t, or None when bar t is missing."""
    bl = K.closed_daily(((view.bars or {}).get(iv) or {}).get(sym) or [], view.now)
    bl = [b for b in bl if K.bar_day(b) <= t]
    if not bl or K.bar_day(bl[-1]) != t:
        return None
    return bl


# -- golden cross -------------------------------------------------------------------------------------------
def sma(xs, n, end):
    """simple mean of xs[end-n+1 .. end]."""
    if end - n + 1 < 0:
        return None
    return sum(xs[end - n + 1:end + 1]) / n


def cross_state(closes):
    """the 50/200 state on the last close: +1 (SMA50 above SMA200: the last cross was golden), -1 (below), 0 tie;
    and the event on that close: 'golden' / 'death' / None."""
    i = len(closes) - 1
    if i < 200:
        return None, None
    f, s = sma(closes, 50, i), sma(closes, 200, i)
    f0, s0 = sma(closes, 50, i - 1), sma(closes, 200, i - 1)
    state = 1 if f > s else (-1 if f < s else 0)
    ev = "golden" if (f > s and f0 <= s0) else ("death" if (f < s and f0 >= s0) else None)
    return state, ev


class GoldenCrossSpy(K.KilledSleeve):
    """SPY long/flat on the 50/200-day SMA cross: the 50-day crossing above the 200-day = buy, the 200-day crossing
    above the 50-day = sell; all-in / all-out (QuantifiedStrat's construction; golden-cross/IMPROVEMENTS.md section A,
    KILL_INVENTORY E1: '50/200d MA cross timing on SPY vs buy-and-hold')."""
    SLEEVE_ID = "killed_golden_cross_spy"
    SOURCE = K.source("golden-cross/IMPROVEMENTS.md", "e32f9a4521905590b385b9bfd8f46ac6c2834dff",
                      inventory={"path": K.RESEARCH + "resurrection/KILL_INVENTORY.md",
                                 "blob": "a799c4f1e069d6e45d908d8a456a3b7c345dbd5a", "section": "E1"})
    UNIVERSE = ("SPY",)
    NEEDS = {"bars": [{"source": "equity_split", "interval": "1d", "n": 320, "symbols": ["SPY"]}],
             "quotes": {"source": "equity", "symbols": ["SPY"]}}
    PARAMS = {"fast": 50, "slow": 200, "sizing": "100% of the sleeve's equity when in, flat when out",
              "removed_gates": []}
    DIVERGENCES = [
        "the cross is read on the closed daily bar t and acted on at the first pass of session t+1 (the study is a "
        "characterization with no fill convention; the desk research convention open_{t+1} is used)",
        "birth: the sleeve holds what the rule holds on its first session (long iff the last cross was golden, i.e. "
        "SMA50 > SMA200) instead of waiting for a fresh cross; a tie keeps the current state",
    ]

    def plan(self, view, st, tb):
        t = signal_day(view.now)
        if t is None or st.get("seen") == t:
            return []
        bl = daily_upto(view, "SPY", t)
        if bl is None or len(bl) < 201:
            return []
        closes = [float(b["c"]) for b in bl]
        state, ev = cross_state(closes)
        st["seen"] = t
        held = tb.open_or_planned("SPY")
        want = state if state != 0 else (1 if held else -1)
        obs = []
        if ev:
            obs.append(Intent("signal", "SPY", price_hint=closes[-1], signal_key=f"gc:{t}:{ev}",
                              reason=f"{ev} cross on {t}: SMA50 {sma(closes, 50, len(closes) - 1):.4f} vs "
                                     f"SMA200 {sma(closes, 200, len(closes) - 1):.4f}"))
        if want > 0 and not held:
            tb.add("SPY", +1, max(0.0, float(view.equity)), "gc", tb.today, "open", None, None,
                   why=f"50/200 state long on {t}" + (f" ({ev} cross)" if ev else " (birth / held state)"), event=t)
        elif want < 0:
            for tr in held:
                if tr["status"] == "held":
                    tb.close_now(tr, f"50/200 state flat on {t}" + (f" ({ev} cross)" if ev else ""), at="now")
                else:
                    tr["status"], tr["void_why"] = "void", "state flat before entry"
        return obs


# -- Leader-1d ------------------------------------------------------------------------------------------------
class _LeaderEvents(K.KilledSleeve):
    """the gated Leader-1d event (score >= 3 of 5 AND buy-cyan/buy-green proxy) on the closed bar t, computed by the
    desk's genome job with the study's own module (desk/vendor/old_desk_research/leader1d_long_fulluniverse_
    2026-10-02.py, blob 2bdb778f, frame() = add_gates(compute_frame(...))) over >= 252 cached daily bars; entry at
    open_{t+1}, exit at close_{t+20}; one active hold per symbol (an event while a hold is active is skipped)."""
    SIDE = +1
    HOLD = 20
    SLOTS = 300
    DIVERGENCES = [
        "the event rows are the genome job's (cache/leader_events.json, the same vendored frame() over the cache's "
        "600 equity_split daily bars instead of the study's 2019-start file; the recursive indicators have converged "
        "long before the event bar)",
        "a session the sleeve misses loses its events (the rows are read for the last completed session only)",
    ]

    def plan(self, view, st, tb):
        t = signal_day(view.now)
        if t is None or st.get("seen") == t:
            return []
        rows = (view.extra or {}).get("killed_leader_last")
        if not rows:
            return []
        st["seen"] = t
        until = st.setdefault("until", {})
        obs, n_ev = [], 0
        for sym in self.UNIVERSE:
            r = rows.get(sym)
            if not r or r[0] != t or not (int(r[1]) >= 3 and bool(r[2])):
                continue
            n_ev += 1
            if until.get(sym) and t < until[sym]:
                obs.append(Intent("signal", sym, signal_key=f"l1d:{t}:{sym}:skip",
                                  reason=f"Leader-1d event on {t} skipped: hold active until {until[sym]}"))
                continue
            exit_day = K.add_sessions(t, self.HOLD)
            until[sym] = exit_day
            tb.add(sym, self.SIDE, K.CAPITAL / self.SLOTS, "l1d", tb.today, "open", exit_day, "close",
                   why=f"Leader-1d event {t}: score {r[1]}, gate", event=t)
        for s in [s for s, d in until.items() if d < K.add_sessions(t, -5)]:
            until.pop(s)
        return obs


class Leader1dLong(_LeaderEvents):
    SLEEVE_ID = "killed_leader1d_long"
    SOURCE = K.source("leader1d_long_fulluniverse_2026-10-02.py", "2bdb778f3efe2c749a139b443164edb13c92f8ee",
                      prereg={"path": K.RESEARCH + "leader1d_long_fulluniverse_prereg_2026-10-02.md",
                              "blob": "3d3315f53f48a3586d6f99ea41f53b37bbe87e29"},
                      results={"path": K.RESEARCH + "leader1d_long_fulluniverse_2026-10-02.md",
                               "blob": "42bdd2e0c64e88d52549913daeb947b268a148db"})
    UNIVERSE = GENOME
    SIDE = +1
    SLOTS = 300
    NEEDS = {"feeds": ["killed_leader_last"], "quotes": {"source": "equity"}}
    PARAMS = {"hold": 20, "side": "long", "universe": "genome 1,838 (>= 252 bars)", "notional": K.CAPITAL / 300,
              "removed_gates": []}


class Leader1dShort(_LeaderEvents):
    SLEEVE_ID = "killed_leader1d_short"
    SOURCE = K.source("leader1d_short_prereg_2026-10-02.md", "52e43968845fda056603df9eaf9ae7c33775a494",
                      results={"path": K.RESEARCH + "leader1d_short_2026-10-02.md",
                               "blob": "71c6b16476cf3ce6abcfab2ff9a189f458af7440"},
                      code="desk/vendor/old_desk_research/leader1d_long_fulluniverse_2026-10-02.py (same frame())")
    UNIVERSE = BASKET
    SIDE = -1
    SLOTS = 41
    NEEDS = {"feeds": ["killed_leader_last"], "quotes": {"source": "equity"}}
    PARAMS = {"hold": 20, "side": "short", "universe": "basket.json minus SIVEF (41)", "notional": K.CAPITAL / 41,
              "borrow": "the venue's (the study's 5%/15% ladder is a reporting overlay)", "removed_gates": [K.LONG_ONLY_RAIL]}


# -- naive 20d breakout ---------------------------------------------------------------------------------------
def breakout(closes):
    """c[t] > max(c[t-20 .. t-1]) on the last bar (strict: ties are not breakouts); needs bar t >= 20 bars in."""
    i = len(closes) - 1
    if i < 20:
        return False
    return closes[i] > max(closes[i - 20:i])


class Naive20dBreakout(K.KilledSleeve):
    """STUDY 3 (naive_breakout_long_prereg_2026-10-02.md): a strict new 20-day closing high on bar t -> LONG at
    open_{t+1}, exit at close_{t+20}; one open position per symbol (a signal during a hold is skipped); 41 names."""
    SLEEVE_ID = "killed_naive_20d_breakout"
    SOURCE = K.source("naive_breakout_long_prereg_2026-10-02.md", "85d2585deee2a1dfac00302bebcdf06946192b06",
                      results={"path": K.RESEARCH + "naive_breakout_validation_2026-10-02.md",
                               "blob": "8d999e8a2cf8b0edf6ea362155c91764fe823536"})
    UNIVERSE = BASKET
    NEEDS = {"bars": [{"source": "equity_split", "interval": "1d", "n": 60}], "quotes": {"source": "equity"}}
    PARAMS = {"lookback": 20, "hold": 20, "notional": K.CAPITAL / 41, "removed_gates": []}
    DIVERGENCES = ["bars are the hub's equity_split daily bars (Alpaca SIP split-adjusted when keyed, else Yahoo's "
                   "split-adjusted closes)"]

    def plan(self, view, st, tb):
        t = signal_day(view.now)
        if t is None or st.get("seen") == t:
            return []
        until = st.setdefault("until", {})
        got = 0
        for sym in self.UNIVERSE:
            bl = daily_upto(view, sym, t)
            if bl is None:
                continue
            got += 1
            if not breakout([float(b["c"]) for b in bl]):
                continue
            if until.get(sym) and t < until[sym]:
                continue
            exit_day = K.add_sessions(t, 20)
            until[sym] = exit_day
            tb.add(sym, +1, K.CAPITAL / 41, "nb20", tb.today, "open", exit_day, "close",
                   why=f"new 20d closing high on {t}", event=t)
        if got:
            st["seen"] = t
        for s in [s for s, d in until.items() if d < K.add_sessions(t, -5)]:
            until.pop(s)
        return []


# -- RSI x OBV daily --------------------------------------------------------------------------------------------
RSIOBV_DAILY = ("MU", "WDC", "ANF", "CLS", "FFIV", "AAOI", "AXTI", "SOXL", "AEHR", "FCEL", "TTMI", "SIMO", "VICR",
                "AG", "SILJ", "SPY", "QQQ", "NVDA", "AAPL")
HOLDS = (5, 10, 20)
GAP = 20


def _rsiobv():
    from ...vendor.old_desk_research import rsiobv
    return rsiobv


def deoverlap(sigs, gap=GAP):
    """per symbol / bucket / direction: keep the earliest, require >= gap bars between kept signals."""
    kept, last = [], None
    for k in sorted(sigs):
        if last is None or k - last >= gap:
            kept.append(k)
            last = k
    return kept


def study_a(divs, exh):
    """{(bucket, direction): [knowable index ...]} - Study A's four buckets."""
    out = {}

    def put(b, d, k):
        out.setdefault((b, d), []).append(k)
    for d in divs:
        ki, dr = d["knowable_index"], d["direction"]
        if d["indicator"] in ("RSI", "RSI+OBV"):
            put("rsi_all", dr, ki)
        if d["indicator"] == "RSI+OBV":
            put("agree", dr, ki)
        if d["indicator"] == "RSI" and d["strength"] in ("STRONG", "SUPERSTRONG") and \
                d["type"] == ("BuR" if dr == 1 else "BeR"):
            put("strong", dr, ki)
    for e in exh:
        put("exhaust", e["direction"], e["index"])
    return out


def tl_line(bars, div, pivot_lb=8):
    """the trendline of rsiobv.trendline_confirmation: (a, b, va, vb) through the two latest pivots at/before i2."""
    R = _rsiobv()
    bull = div["direction"] == 1
    vals = [b["h"] for b in bars] if bull else [b["l"] for b in bars]
    highs, lows = R.pivot_indices(vals, pivot_lb)
    pivs = [p for p in (highs if bull else lows) if p <= div["i2"]]
    if len(pivs) < 2 or pivs[-1] == pivs[-2]:
        return None
    a, b = pivs[-2], pivs[-1]
    return a, b, vals[a], vals[b]


def tl_breaks(bars, div, max_wait=5):
    """{"close": idx, "wick": idx, "close2": idx} - the three Study B formalizations' entry-signal bars."""
    R = _rsiobv()
    out = {"close": R.trendline_confirmation(bars, div, max_wait=max_wait)}
    ln = tl_line(bars, div)
    if ln is None:
        return dict(out, wick=None, close2=None)
    a, b, va, vb = ln
    bull = div["direction"] == 1
    n, ki = len(bars), div["knowable_index"]

    def line(i):
        return va + (vb - va) * (i - a) / (b - a)
    wick = close2 = None
    for k in range(1, max_wait + 1):
        i = ki + k
        if i >= n:
            break
        if (bull and bars[i]["h"] > line(i)) or (not bull and bars[i]["l"] < line(i)):
            wick = i
            break
    for k in range(1, max_wait + 1):
        i = ki + k
        if i >= n:
            break
        c = bars[i]["c"]
        if (bull and c > line(i)) or (not bull and c < line(i)):
            j = i + 1
            if j < n:
                cj = bars[j]["c"]
                if (bull and cj > line(j)) or (not bull and cj < line(j)):
                    close2 = j
            break
    return dict(out, wick=wick, close2=close2)


def rsiobv_daily_signals(bars):
    """every Study A / B / C signal whose entry decision falls on the LAST bar: [(arm, direction, hold_sessions,
    detail)]. hold_sessions = sessions from the signal bar to the exit close."""
    R = _rsiobv()
    last = len(bars) - 1
    divs = R.scan_divergences(bars, rsi_periods=(8, 13, 21), rsi_lookbacks=(8,))
    exh = R.scan_exhaustion(bars)
    out = []
    for (bucket, dr), ks in study_a(divs, exh).items():
        if last in deoverlap(ks):
            for h in HOLDS:
                out.append((f"A:{bucket}:{h}", dr, h, {"ki": last}))
    # Study B: base = RSI regular divergences (BuR / BeR), de-overlapped per direction as in Study A
    base = {}
    for d in divs:
        if d["indicator"] in ("RSI", "RSI+OBV") and d["type"] in ("BuR", "BeR"):
            base.setdefault(d["direction"], {}).setdefault(d["knowable_index"], d)
    for dr, by_k in base.items():
        for k in deoverlap(list(by_k)):
            if k < last - 7:
                continue
            br = tl_breaks(bars, by_k[k])
            for form, idx in br.items():
                if idx == last:
                    for h in HOLDS:
                        out.append((f"B:{form}:{h}", dr, h, {"ki": k, "break": idx}))
    # Study C: 20d closing-high breakout, RSI-extreme filters F1-F4 (no de-overlap; exit close of entry + 20)
    closes = [b["c"] for b in bars]
    if last >= 20 and closes[last] > max(closes[last - 20:last]):
        r = {p: R.wilder_rsi(closes, p)[last] for p in (8, 13, 21)}
        flt = {"F0": True, "F1": r[8] is not None and r[8] <= 30, "F2": r[13] is not None and r[13] <= 30,
               "F3": r[21] is not None and r[21] <= 30}
        flt["F4"] = flt["F1"] or flt["F2"] or flt["F3"]
        for f, ok in flt.items():
            if ok:
                out.append((f"C:{f}:21", 1, 21, {"rsi": r}))
    return out


class RsiObvDaily(K.KilledSleeve):
    """rsiobv_reassessment_prereg_2026-10-02.md, all three studies on 19 names' daily bars (adjustment=all):
    A  divergences (rsi_periods 8/13/21, lookback 8) in four buckets x direction - all RSI, RSI+OBV agreement,
       BuR/BeR RSI STRONG/SUPERSTRONG, exhaustion BLOWOFF(-1)/CAPITULATION(+1) - de-overlapped per symbol / bucket /
       direction (>= 20 trading days between kept signals); entry next open after the knowable bar; holds 5/10/20
       (exit at the close of e+H-1)
    B  the three trendline formalizations (TL-close, TL-wick, TL-close-confirm) on the de-overlapped RSI regular
       divergences; entry next open after the break bar; holds 5/10/20
    C  20d closing-high breakouts long with the RSI-extreme filters F0-F4; exit at the close of the 20th trading day
       after the entry bar
    Every arm is its own tranche (the signal's direction), so the book holds the study's trades side by side."""
    SLEEVE_ID = "killed_rsiobv_daily"
    SOURCE = K.source("rsiobv_reassessment_prereg_2026-10-02.md", "96ee1879f7493b4deb738852e426d088f1033513",
                      results={"path": K.RESEARCH + "rsiobv_daily_reassessment_2026-10-02.md",
                               "blob": "447faa215c67b586e196ac83016a6e649d653320"},
                      code={"path": K.RESEARCH + "rsiobv.py", "blob": "9421874ce6074a12de52edc4b53431a05717caa9",
                            "vendored": "desk/vendor/old_desk_research/rsiobv.py"})
    UNIVERSE = RSIOBV_DAILY
    NEEDS = {"bars": [{"source": "equity", "interval": "1d", "n": 520}], "quotes": {"source": "equity"}}
    PARAMS = {"rsi_periods": [8, 13, 21], "rsi_lookbacks": [8], "holds": list(HOLDS), "gap": GAP,
              "notional_per_tranche": K.CAPITAL / 150, "removed_gates": [K.LONG_ONLY_RAIL]}
    DIVERGENCES = [
        "the scan runs on the last 520 closed daily bars each session instead of the 2016-start series (pivots, "
        "divergences and the 144-bar exhaustion window near the last bar are identical; OBV levels differ by a "
        "constant, which no rule reads); the de-overlap chain restarts at the window start and is synchronised by "
        "the first >= 20-day gap",
        "TL-close-confirm: the first close beyond the line must be followed by a second (no later pair is searched)",
        "RSI+OBV agreement is classified at the knowable bar: an OBV divergence completing up to 3 bars later "
        "(which the study's whole-series scan merged into the RSI divergence - a 3-bar lookahead) does not "
        "reclassify a signal already taken (measured: tools/parity/killed_rsiobv.py)",
        "Study C's exit 'close of the 20th trading day after the entry bar' = close of t+21",
    ]

    def plan(self, view, st, tb):
        t = signal_day(view.now)
        if t is None or st.get("seen") == t:
            return []
        got = 0
        for sym in self.UNIVERSE:
            bl = daily_upto(view, sym, t)
            if bl is None or len(bl) < 200:
                continue
            got += 1
            bars = [{"t": b["t"], "o": float(b["o"]), "h": float(b["h"]), "l": float(b["l"]), "c": float(b["c"]),
                     "v": float(b.get("v") or 0.0)} for b in bl]
            for arm, dr, h, det in rsiobv_daily_signals(bars):
                tb.add(sym, dr, K.CAPITAL / 150, arm, tb.today, "open", K.add_sessions(t, h), "close",
                       why=f"{arm} on {t} {det}", event=t)
        if got:
            st["seen"] = t
        return []
