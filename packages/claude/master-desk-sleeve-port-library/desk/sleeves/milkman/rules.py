"""The twelve Milkman v2 daily rules (dstrats.py) as bar programs: the research's batch functions restated as what
happens on each daily bar, in the order the research's engines resolve it, so that the same program can be fed
completed bars (replay, parity) or a live session phase by phase.

A bar is processed in four phases:
  open   events at the session open (market-on-open entries/exits; a level the open has already gapped through)
  touch  levels reached by the session's range (stop entries, voids, stops, targets, touch exits); the research's
         same-bar conventions decide when several levels are newly reached in one observation (void before
         entry, stop before target, entry-bar target before the close-through stop)
  close  events at the close (close entries, signal exits, time exits)
  end    state that needs the completed bar (box locks, filters and stop ratchets for the next bar, the follow-
         through state machine, next-open signals)
open and touch read only the bar's date and open (X.dates[t], X.o[t]) and levels the previous bar's end stored, so
a live session can run them from a quote; close and end read the study's arrays.

Every indicator is the study's own (vendored mlib / dlib / dstrats: _cache, htf_levels, liq_gate); the exit engines
are the study's engines read one bar at a time (eng_d7, eng_hold, eng_trail, eng_bracket, eng_touch,
eng_signal_exit), and the entry expressions are the study's, transcribed (its batch functions drop a trade whose
exit lies beyond the data, so they cannot report today's entry). tools/parity/milkman_daily.py replays every rule
against the study's own functions.

State per (lane, symbol) is plain JSON keyed by bar dates (ISO strings; their order is the bars' order). Events:
  {"kind": "enter"|"exit", "date", "px" (the research's price), "at": "open"|"touch"|"close"|"end", "tid", ...}."""
import math

import numpy as np
import pandas as pd

from . import vendored as V


def D():
    return V.dstrats()


# --------------------------------------------------------------------------------------------- symbol context
class Ctx:
    """one symbol's daily arrays (ascending, the last bar may be provisional) with the study's indicators."""

    def __init__(self, dates, o, h, l, c, v, kind):
        self.dates = list(dates)
        self.idx = {d: i for i, d in enumerate(self.dates)}
        self.o, self.h, self.l, self.c, self.v = (np.asarray(x, dtype=float) for x in (o, h, l, c, v))
        self.kind = kind
        self.n = len(self.c)
        self.d = dict(date=np.array(self.dates, dtype="datetime64[ns]"), o=self.o, h=self.h, l=self.l, c=self.c,
                      v=self.v, kind=kind)
        self.C = D()._cache(self.d)
        self._memo = {}

    def memo(self, key, fn):
        if key not in self._memo:
            self._memo[key] = fn()
        return self._memo[key]

    def i(self, date):
        return self.idx.get(date)


class Day:
    """a session seen live before its bar exists: its date and open (what the open and touch phases read)."""

    def __init__(self, date, o, kind="etf"):
        self.dates, self.o, self.kind, self.n = [date], np.array([float(o)]), kind, 1


def _rolling(x, n, how):
    s = pd.Series(x).rolling(n, min_periods=n)
    return (s.min() if how == "min" else s.max()).values


def _new_trade(ev, side, **kw):
    t = {"tid": ev["tid"], "side": side, "i": ev["date"], "ep": ev["px"]}
    t.update(kw)
    return t


def _ev(kind, date, px, at, tid, **kw):
    e = {"kind": kind, "date": date, "px": float(px), "at": at, "tid": tid}
    e.update(kw)
    return e


def _fresh(S):
    S.setdefault("open", [])
    S.setdefault("busy", None)
    S.setdefault("seq", 0)
    return S


def _tid(S, X, t):
    S["seq"] += 1
    return f"{X.dates[t]}#{S['seq']}"


def _free(S, X, t):
    """the study's nonoverlap: no trade open, and the bar is after the last kept trade's exit bar."""
    return not S["open"] and (S.get("busy") is None or X.dates[t] > S["busy"])


def _close_trade(S, tr, ev, nonoverlap):
    S["open"] = [x for x in S["open"] if x["tid"] != tr["tid"]]
    if nonoverlap:
        S["busy"] = ev["date"]
    return ev


class Rule:
    name = ""
    nonoverlap = False
    sets = ("univ", "index")

    def begin(self, S, X, t, side, cell, period_last=None, left=None):
        return None

    def open(self, S, X, t, side, cell):
        return []

    def touch(self, S, X, t, side, cell, lo, hi, first):
        return []

    def close(self, S, X, t, side, cell):
        return []

    def end(self, S, X, t, side, cell):
        return []

    def levels(self, S, side, cell):
        """the price levels the touch phase watches (the live poll's watch list)."""
        return []


# --------------------------------------------------------------------------------------------- 1. Connors Double 7
class D7(Rule):
    name, nonoverlap = "D7", True

    def close(self, S, X, t, side, cell):
        N, ma, cap = int(cell["N"]), int(cell["ma"]), int(cell.get("cap", 60))
        c, out = X.c, []
        for tr in list(S["open"]):                       # eng_d7: first N-day closing extreme, or cap, at the close
            i = X.i(tr["i"])
            if i is None or t <= i:
                continue
            lo = max(0, t - N + 1)
            ok = all(not (c[q] > c[t]) for q in range(lo, t)) if side > 0 else \
                all(not (c[q] < c[t]) for q in range(lo, t))
            if ok or t == i + cap:
                out.append(_close_trade(S, tr, _ev("exit", X.dates[t], c[t], "close", tr["tid"]), True))
        if _free(S, X, t) and t >= max(ma, N):
            s = X.C["s200"] if ma == 200 else X.C["s100"]
            ext = X.memo(("rmin" if side > 0 else "rmax", N), lambda: _rolling(c, N, "min" if side > 0 else "max"))
            trend = (c[t] > s[t]) if side > 0 else (c[t] < s[t])
            hit = (c[t] <= ext[t]) if side > 0 else (c[t] >= ext[t])
            if trend and hit and X.C["liq"][t]:
                ev = _ev("enter", X.dates[t], c[t], "close", _tid(S, X, t))
                S["open"].append(_new_trade(ev, side))
                out.append(ev)
        return out


# --------------------------------------------------------------------------------------------- 2. Legend's Buy Day
class LBD(Rule):
    name = "LBD"

    def open(self, S, X, t, side, cell):
        out = []
        for tr in list(S["open"]):                       # eng_hold mode 2: close[i] -> open of the next bar
            if tr["i"] < X.dates[t]:
                out.append(_close_trade(S, tr, _ev("exit", X.dates[t], X.o[t], "open", tr["tid"]), False))
        return out

    def close(self, S, X, t, side, cell):
        k, exact = int(cell["k"]), bool(cell["exact"])
        c = X.c
        run = X.memo(("run", side), lambda: _runs(c, side))
        sig = (run[t] == k) if exact else (run[t] >= k)
        if sig and X.C["liq"][t]:
            ev = _ev("enter", X.dates[t], c[t], "close", _tid(S, X, t))
            S["open"].append(_new_trade(ev, side))
            return [ev]
        return []


def _runs(c, side):
    n = len(c)
    dn = np.r_[False, c[1:] < c[:-1]] if side > 0 else np.r_[False, c[1:] > c[:-1]]
    run = np.zeros(n, int)
    for i in range(1, n):
        run[i] = run[i - 1] + 1 if dn[i] else 0
    return run


# --------------------------------------------------------------------------------------------- 3. weekday open->close
class DOW(Rule):
    name, sets = "DOW", ("index",)

    def open(self, S, X, t, side, cell):
        wd = pd.Timestamp(X.dates[t]).weekday()
        if X.kind == "stock":
            raise ValueError("DOW runs on the index set only (its liquidity gate would need today's volume)")
        if wd == int(cell["dow"]):                       # non-stock liq_gate is all-True
            ev = _ev("enter", X.dates[t], X.o[t], "open", _tid(S, X, t))
            S["open"].append(_new_trade(ev, side))
            return [ev]
        return []

    def close(self, S, X, t, side, cell):
        out = []
        for tr in list(S["open"]):                       # eng_hold mode 3: open[i] -> close[i]
            if tr["i"] == X.dates[t]:
                out.append(_close_trade(S, tr, _ev("exit", X.dates[t], X.c[t], "close", tr["tid"]), False))
        return out


# --------------------------------------------------------------------------------------------- 4. Daily Bilbo Box
class DBB(Rule):
    name, nonoverlap = "DBB", True

    def touch(self, S, X, t, side, cell, lo, hi, first):
        out = []
        o, today = X.o[t], X.dates[t]
        for tr in list(S["open"]):                       # stop on bars after the entry (gap-honest); the entry bar
            if today <= tr["i"]:                         # waits for its close
                continue
            st = tr["stop"]
            if (side > 0 and lo <= st) or (side < 0 and hi >= st):
                px = (min(o, st) if side > 0 else max(o, st)) if first else st
                out.append(_close_trade(S, tr, _ev("exit", today, px, "touch", tr["tid"], why="stop"), True))
        for b in list(S.get("boxes") or []):              # armed boxes: void if the low (high) is reached first
            if today <= b["lock"]:
                continue
            out += self._window_bar(S, X, t, side, b, lo, hi, first, b["ok"])
        return out

    def _window_bar(self, S, X, t, side, b, lo, hi, first, ok):
        """one window bar of a locked box (dstrats.bilbo_daily): the void test first, then the break with the
        prior-bar filter; a break that fails the filter does not end the window."""
        o, today = X.o[t], X.dates[t]
        bh, bl = b["bh"], b["bl"]
        if first:
            b["gap_day"] = today if ((side > 0 and o >= bh) or (side < 0 and o <= bl)) else None
        gap = b.get("gap_day") == today
        if side > 0:
            void = (first and o <= bl) or (lo <= bl and not gap)
            trig = hi >= bh
        else:
            void = (first and o >= bh) or (hi >= bh and not gap)
            trig = lo <= bl
        if void:
            S["boxes"].remove(b)
            return []
        if trig and ok:
            S["boxes"].remove(b)                         # the window ends at its first qualified break, kept or not
            if _free(S, X, t):
                px = (max(o, bh) if side > 0 else min(o, bl)) if first else (bh if side > 0 else bl)
                ev = _ev("enter", today, px, "touch", _tid(S, X, t))
                S["open"].append(_new_trade(ev, side, stop=float(bl if side > 0 else bh),
                                            edge=float(bh if side > 0 else bl)))
                return [ev]
        return []

    def close(self, S, X, t, side, cell):
        out = []
        cap = {"h20": 20, "h60": 60}.get(cell["exitm"], int(cell.get("cap", 250)))
        c = X.c
        for tr in list(S["open"]):
            i = X.i(tr["i"])
            if i is None:
                continue
            if t == i:                                   # entry bar: stopped only if the close is through the stop
                out += self._entry_bar_close(S, X, t, side, [tr])
                continue
            if t == i + cap:
                out.append(_close_trade(S, tr, _ev("exit", X.dates[t], c[t], "close", tr["tid"], why="cap"), True))
        return out

    def _entry_bar_close(self, S, X, t, side, trades):
        out = []
        c, h, l = X.c, X.h, X.l
        for tr in trades:
            st = tr["stop"]
            if (side > 0 and c[t] <= st) or (side < 0 and c[t] >= st):
                px = st if ((side > 0 and l[t] <= st) or (side < 0 and h[t] >= st)) else c[t]
                out.append(_close_trade(S, tr, _ev("exit", X.dates[t], px, "close", tr["tid"], why="entry_bar"), True))
        return out

    def end(self, S, X, t, side, cell):
        """on the completed bar: the trailing stop for the next bar (eng_trail ratchets to the prior bar's EMA at each
        bar's start), windows age, a compression onset starts an episode, the box locks at its boxlen-th bar or at
        the episode's end (known at the first non-compression bar, which is then window bar one, decided here)."""
        boxlen, window = int(cell["boxlen"]), int(cell.get("window", 20))
        ex = cell["exitm"]
        trail = X.C["e50"] if ex in ("ema50", "scr3") else (X.C["e20"] if ex == "ema20" else X.C["e50"])
        comp, e21, liq, c = X.C["comp"], X.C["e21"], X.C["liq"], X.c
        out = []
        S.setdefault("boxes", [])
        for b in list(S["boxes"]):
            lk = X.i(b["lock"])
            if lk is not None and t >= lk + window:
                S["boxes"].remove(b)
        ep = S.get("episode")
        if ep is None and t >= 1 and comp[t] == 1 and comp[t - 1] == 0:
            ep = S["episode"] = {"start": X.dates[t], "bh": float(X.h[t]), "bl": float(X.l[t]), "cnt": 1,
                                 "locked": False}
            if ep["cnt"] >= boxlen:
                self._lock(S, X, t, ep)
        elif ep is not None:
            if comp[t] == 1:
                if not ep["locked"]:
                    ep["bh"], ep["bl"] = max(ep["bh"], float(X.h[t])), min(ep["bl"], float(X.l[t]))
                    ep["cnt"] += 1
                    if ep["cnt"] >= boxlen:
                        self._lock(S, X, t, ep)
            else:
                S["episode"] = None                      # the episode ended at t-1: a short box locks there and
                if not ep["locked"]:                     # this bar (t) is its first window bar, decided now
                    b = self._lock(S, X, t - 1, ep)
                    ok = bool(((c[t - 1] > e21[t - 1]) if side > 0 else (c[t - 1] < e21[t - 1])) and liq[t - 1])
                    for ev in self._window_bar(S, X, t, side, b, X.l[t], X.h[t], True, ok):
                        ev["at"] = "end"                 # live: decided on the completed bar, executed next open
                        out.append(ev)
                        out += self._entry_bar_close(S, X, t, side, [x for x in S["open"] if x["tid"] == ev["tid"]])
                    if window <= 1 and b in S["boxes"]:
                        S["boxes"].remove(b)
        for b in S["boxes"]:                             # the next bar's entry filter: this close vs EMA21, liquidity
            b["ok"] = bool(((c[t] > e21[t]) if side > 0 else (c[t] < e21[t])) and liq[t])
        if ex not in ("h20", "h60"):                     # the next bar's stop: ratchet to this bar's EMA
            for tr in S["open"]:
                if np.isfinite(trail[t]):
                    if side > 0 and trail[t] > tr["stop"]:
                        tr["stop"] = float(trail[t])
                    if side < 0 and trail[t] < tr["stop"]:
                        tr["stop"] = float(trail[t])
        return out

    def _lock(self, S, X, lock, ep):
        ep["locked"] = True
        b = {"lock": X.dates[lock], "bh": ep["bh"], "bl": ep["bl"], "ok": False}
        S["boxes"].append(b)
        return b

    def levels(self, S, side, cell):
        out = [(tr["stop"], "below" if side > 0 else "above") for tr in S["open"]]
        for b in S.get("boxes") or []:
            out += [(b["bh"], "above"), (b["bl"], "below")]
        return out


# --------------------------------------------------------------------------------------------- 5/6. Golden Gate
class GG(Rule):
    """Swing GG (monthly ATR) / Multiday GG (weekly ATR): the period's first gate touch decides; filters on the prior
    bar; a resting stop entry at the entry level to the period end; bracket with the target / pivot stop; flat at
    the period's last close."""
    name, nonoverlap = "GG", False

    def begin(self, S, X, t, side, cell, period_last=None, left=None):
        """before bar t: open the bar's period if new; store its levels (prior period close / ATR of the study's
        htf_levels) and whether a gate touch on this bar would arm (filters on bar t-1). period_last = the period's
        last session; left = sessions after t up to it (the study's last[t] - t)."""
        PC, PA, _, _ = X.memo(("htf", cell["freq"]), lambda: D().htf_levels(X.d, cell["freq"]))
        per = S.get("period") or {}
        if per.get("id") != period_last:                # a period is identified by its last session
            per = {"id": period_last, "last": period_last, "decided": False, "entered": False}
        finite = bool(np.isfinite(PA[t]))
        per["finite"] = finite
        if finite:
            lev = lambda x: float(PC[t] + side * x * PA[t])
            per["Lg"], per["Le"], per["T"] = lev(float(cell.get("gate_lvl", 0.382))), lev(float(cell["entry_lvl"])), \
                lev(float(cell.get("tgt_lvl", 1.0)))
            per["S"] = float(PC[t]) if cell["stop"] == "pivot" else lev(0.236)
        e21, po, liq, c = X.C["e21"], X.C["po"], X.C["liq"], X.c
        if not per["decided"]:
            ok = t >= 1 and finite and left >= int(cell.get("min_left", 5)) - 1
            g = cell.get("ema_gate", "with")
            if ok and g == "with":
                ok = (c[t - 1] > e21[t - 1]) if side < 0 else (c[t - 1] < e21[t - 1])
            if ok and g == "trend":
                ok = (c[t - 1] > e21[t - 1]) if side > 0 else (c[t - 1] < e21[t - 1])
            if ok and cell.get("po_filter"):
                ok = (po[t - 1] < -61.8) if side < 0 else (po[t - 1] > 61.8)
            per["ok"] = bool(ok and liq[t - 1])
        S["period"] = per

    def touch(self, S, X, t, side, cell, lo, hi, first):
        out = []
        o, today = X.o[t], X.dates[t]
        for tr in list(S["open"]):                       # bracket: stop first, then target (gap-honest)
            T, Sx = tr["target"], tr["stop"]
            if today == tr["i"]:                         # entry bar (a later look the same day): the target counts
                if (side > 0 and hi >= T) or (side < 0 and lo <= T):
                    out.append(_close_trade(S, tr, _ev("exit", today, T, "touch", tr["tid"], why="target_entry_bar"),
                                            False))
                continue
            if (side > 0 and lo <= Sx) or (side < 0 and hi >= Sx):
                px = ((min(o, Sx) if side > 0 else max(o, Sx)) if first else Sx)
                out.append(_close_trade(S, tr, _ev("exit", today, px, "touch", tr["tid"], why="stop"), False))
            elif (side > 0 and hi >= T) or (side < 0 and lo <= T):
                px = ((max(o, T) if side > 0 else min(o, T)) if first else T)
                out.append(_close_trade(S, tr, _ev("exit", today, px, "touch", tr["tid"], why="target"), False))
        per = S.get("period") or {}
        if not per.get("finite"):
            return out
        if not per.get("decided"):
            if (lo <= per["Lg"]) if side < 0 else (hi >= per["Lg"]):
                per["decided"] = True                    # the period's first gate touch decides
                if per.get("ok"):
                    per["armed"] = {"Le": per["Le"], "T": per["T"], "S": per["S"], "from": today}
        arm = per.get("armed")
        if arm and not per.get("entered"):
            if (lo <= arm["Le"]) if side < 0 else (hi >= arm["Le"]):
                per["entered"] = True
                px = ((min(o, arm["Le"]) if side < 0 else max(o, arm["Le"])) if first else arm["Le"])
                ev = _ev("enter", today, px, "touch", _tid(S, X, t))
                tr = _new_trade(ev, side, target=arm["T"], stop=arm["S"], last=per["last"])
                S["open"].append(tr)
                out.append(ev)
                if (side > 0 and hi >= tr["target"]) or (side < 0 and lo <= tr["target"]):
                    out.append(_close_trade(S, tr, _ev("exit", today, tr["target"], "touch", tr["tid"],
                                                       why="target_entry_bar"), False))
        S["period"] = per
        return out

    def close(self, S, X, t, side, cell):
        out = []
        c, today = X.c, X.dates[t]
        for tr in list(S["open"]):
            if today == tr["i"]:                         # entry bar: the stop counts only on a close through it
                if (side > 0 and c[t] <= tr["stop"]) or (side < 0 and c[t] >= tr["stop"]):
                    out.append(_close_trade(S, tr, _ev("exit", today, c[t], "close", tr["tid"],
                                                       why="stop_close_entry_bar"), False))
                    continue
            if today >= tr["last"]:                      # the period's last session: flat at its close
                out.append(_close_trade(S, tr, _ev("exit", today, c[t], "close", tr["tid"], why="period_end"), False))
        return out

    def levels(self, S, side, cell):
        out = []
        for tr in S["open"]:
            out += [(tr["stop"], "below" if side > 0 else "above"), (tr["target"], "above" if side > 0 else "below")]
        per = S.get("period") or {}
        if per.get("finite") and not per.get("decided"):
            out.append((per["Lg"], "above" if side > 0 else "below"))
        if per.get("armed") and not per.get("entered"):
            out.append((per["armed"]["Le"], "above" if side > 0 else "below"))
        return out


# --------------------------------------------------------------------------------------------- 7. EMA21 reversion
class E21(Rule):
    name, nonoverlap = "E21", True

    def touch(self, S, X, t, side, cell, lo, hi, first):
        out = []
        o, today = X.o[t], X.dates[t]
        for tr in list(S["open"]):                       # eng_touch: the prior bar's EMA21, gap-honest
            if today <= tr["i"] or tr.get("L") is None:
                continue
            L = tr["L"]
            if (side > 0 and hi >= L) or (side < 0 and lo <= L):
                px = ((max(o, L) if side > 0 else min(o, L)) if first else L)
                out.append(_close_trade(S, tr, _ev("exit", today, px, "touch", tr["tid"], why="ema21"), True))
        return out

    def close(self, S, X, t, side, cell):
        out = []
        k, H = float(cell["k"]), int(cell["H"])
        c = X.c
        for tr in list(S["open"]):
            i = X.i(tr["i"])
            if i is not None and t == i + H:
                out.append(_close_trade(S, tr, _ev("exit", X.dates[t], c[t], "close", tr["tid"], why="time"), True))
        if _free(S, X, t) and t >= 30:
            dev = X.memo(("dev",), lambda: (c - X.C["e21"]) / X.C["a"])
            x = lambda j: (dev[j] >= k) if side < 0 else (dev[j] <= -k)
            if x(t) and not (t >= 1 and x(t - 1)) and X.C["liq"][t]:
                ev = _ev("enter", X.dates[t], c[t], "close", _tid(S, X, t))
                S["open"].append(_new_trade(ev, side))
                out.append(ev)
        return out

    def end(self, S, X, t, side, cell):
        for tr in S["open"]:                             # the next bar's touch level: this bar's EMA21
            tr["L"] = float(X.C["e21"][t])
        return []

    def levels(self, S, side, cell):
        return [(tr["L"], "above" if side > 0 else "below") for tr in S["open"] if tr.get("L") is not None]


# --------------------------------------------------------------------------------------------- 8. Phase Oscillator
class PO(Rule):
    name = "PO"

    def close(self, S, X, t, side, cell):
        out = []
        H = int(cell["H"])
        c = X.c
        for tr in list(S["open"]):                       # eng_hold mode 0: close[i] -> close[i+H]
            i = X.i(tr["i"])
            if i is not None and t == i + H:
                out.append(_close_trade(S, tr, _ev("exit", X.dates[t], c[t], "close", tr["tid"]), False))
        if t >= 30:
            p = X.C["po"]
            pp = p[t - 1]
            if cell["kind"] == "accum":
                sig = (pp <= -61.8 and p[t] > -61.8) if side > 0 else (pp >= 61.8 and p[t] < 61.8)
            else:
                sig = (pp <= -100 and p[t] > -100) if side > 0 else (pp >= 100 and p[t] < 100)
            if sig and X.C["liq"][t]:
                ev = _ev("enter", X.dates[t], c[t], "close", _tid(S, X, t))
                S["open"].append(_new_trade(ev, side))
                out.append(ev)
        return out


# --------------------------------------------------------------------------------------------- 9. Pivot Ribbon
class RIB(Rule):
    name = "RIB"

    def close(self, S, X, t, side, cell):
        out = []
        cap = int(cell.get("cap", 120))
        up = X.memo(("up",), lambda: X.C["e13"] > X.C["e48"])
        c = X.c
        if cell["exitm"] == "opposite":
            ex = (not up[t] and t >= 1 and up[t - 1]) if side > 0 else (up[t] and t >= 1 and not up[t - 1])
        else:
            f8 = X.C["e8"][t] > X.C["e21"][t]
            ex = (not f8) if side > 0 else f8
        for tr in list(S["open"]):                       # eng_signal_exit: the exit signal or the cap, at the close
            i = X.i(tr["i"])
            if i is None or t <= i:
                continue
            if cell["exitm"].startswith("h"):
                if t == i + int(cell["exitm"][1:]):
                    out.append(_close_trade(S, tr, _ev("exit", X.dates[t], c[t], "close", tr["tid"]), False))
            elif ex or t == i + cap:
                out.append(_close_trade(S, tr, _ev("exit", X.dates[t], c[t], "close", tr["tid"]), False))
        if t >= 60:
            cross = (up[t] and not up[t - 1]) if side > 0 else (not up[t] and up[t - 1])
            if cross and X.C["liq"][t]:
                ev = _ev("enter", X.dates[t], c[t], "close", _tid(S, X, t))
                S["open"].append(_new_trade(ev, side))
                out.append(ev)
        return out


# --------------------------------------------------------------------------------------------- 10. compression expansion
class CEX(Rule):
    name = "CEX"

    def open(self, S, X, t, side, cell):
        out = []
        for p in list(S.get("next_open") or []):         # eng_hold mode 1: signal i -> open[i+1] -> close[i+H]
            if p["signal"] >= X.dates[t]:
                continue
            S["next_open"].remove(p)
            ev = _ev("enter", X.dates[t], X.o[t], "open", p["tid"], signal=p["signal"])
            S["open"].append(_new_trade(ev, side, signal=p["signal"]))
            out.append(ev)
        return out

    def close(self, S, X, t, side, cell):
        out = []
        H = int(cell["H"])
        for tr in list(S["open"]):
            i = X.i(tr["signal"])
            if i is not None and t == i + H:
                out.append(_close_trade(S, tr, _ev("exit", X.dates[t], X.c[t], "close", tr["tid"]), False))
        return out

    def end(self, S, X, t, side, cell):
        mb = int(cell["minbars"])
        comp = X.C["comp"]
        run = X.memo(("crun",), lambda: _comp_runs(comp))
        if t >= 60 and comp[t] == 0 and run[t - 1] >= mb:
            tr_ok = (X.C["e21"][t] > X.C["e48"][t]) if side > 0 else (X.C["e21"][t] < X.C["e48"][t])
            if tr_ok and X.C["liq"][t]:
                S.setdefault("next_open", []).append({"signal": X.dates[t], "tid": _tid(S, X, t)})
        return []


def _comp_runs(comp):
    n = len(comp)
    run = np.zeros(n, int)
    for i in range(1, n):
        run[i] = run[i - 1] + 1 if comp[i] else 0
    return run


# --------------------------------------------------------------------------------------------- 11. Big down day
class BIG(Rule):
    name, sets = "BIG", ("index",)

    def close(self, S, X, t, side, cell):
        out = []
        H, thr = int(cell["H"]), float(cell["thr"])
        c = X.c
        for tr in list(S["open"]):
            i = X.i(tr["i"])
            if i is not None and t == i + H:
                out.append(_close_trade(S, tr, _ev("exit", X.dates[t], c[t], "close", tr["tid"]), False))
        if t >= 1 and (c[t] / c[t - 1] - 1) * 100 <= thr and X.C["liq"][t]:
            ev = _ev("enter", X.dates[t], c[t], "close", _tid(S, X, t))
            S["open"].append(_new_trade(ev, side))
            out.append(ev)
        return out


# --------------------------------------------------------------------------------------------- 12. follow-through day
class FTD(Rule):
    name, sets = "FTD", ("index",)
    LB = 63

    def touch(self, S, X, t, side, cell, lo, hi, first):
        out = []
        o, today = X.o[t], X.dates[t]
        for tr in list(S["open"]):                       # eng_bracket mode 2 from the bar after entry: stop, then target
            if today <= tr["i"]:
                continue
            T, Sx = tr["target"], tr["stop"]
            if (side > 0 and lo <= Sx) or (side < 0 and hi >= Sx):
                px = ((min(o, Sx) if side > 0 else max(o, Sx)) if first else Sx)
                out.append(_close_trade(S, tr, _ev("exit", today, px, "touch", tr["tid"], why="stop"), False))
            elif (side > 0 and hi >= T) or (side < 0 and lo <= T):
                px = ((max(o, T) if side > 0 else min(o, T)) if first else T)
                out.append(_close_trade(S, tr, _ev("exit", today, px, "touch", tr["tid"], why="target"), False))
        return out

    def close(self, S, X, t, side, cell):
        out = []
        c = X.c
        for tr in list(S["open"]):
            i = X.i(tr["i"])
            if i is not None and t == i + 120:
                out.append(_close_trade(S, tr, _ev("exit", X.dates[t], c[t], "close", tr["tid"], why="cap"), False))
        st = dict(S.get("ftd") or {"state": 0, "low": None, "d1": None, "d1low": None})
        low = self._advance(st, X, t, cell)
        if low is not None:
            X_ = c[t] - low
            ev = _ev("enter", X.dates[t], c[t], "close", _tid(S, X, t))
            S["open"].append(_new_trade(ev, side, target=float(c[t] + X_ if side > 0 else c[t] - X_),
                                        stop=float(low if side > 0 else c[t] + X_)))
            out.append(ev)
            S["ftd_entered"] = X.dates[t]
        return out

    def end(self, S, X, t, side, cell):
        """commit the state machine on the completed bar (an entry taken on a provisional bar resets it, as the
        study's own entry does)."""
        st = dict(S.get("ftd") or {"state": 0, "low": None, "d1": None, "d1low": None})
        self._advance(st, X, t, cell)
        if S.pop("ftd_entered", None) == X.dates[t]:
            st["state"] = 0
        S["ftd"] = st
        return []

    def _advance(self, st, X, t, cell):
        """one bar of the study's follow-through state machine; returns the correction low when the bar is a
        follow-through day with a positive distance (an entry), else None."""
        if t < self.LB:
            return None
        c, l, v = X.c, X.l, X.v
        hh = X.memo(("hh",), lambda: pd.Series(c).rolling(self.LB, min_periods=20).max().values)
        corr, gain = float(cell["corr"]), float(cell["gain"])
        low = st["low"] if st["low"] is not None else float("nan")
        out = None
        dd = c[t] / hh[t] - 1
        if st["state"] == 0 and dd <= -corr / 100:
            st["state"] = 1
            low = l[t]
        if st["state"] >= 1:
            low = min(low, l[t]) if st["state"] == 1 else low
            if st["state"] == 1 and c[t] > c[t - 1]:
                st["state"] = 2
                st["d1"] = X.dates[t]
                st["d1low"] = float(l[t])
                low = min(low, l[t])
            elif st["state"] == 2:
                d1 = X.i(st["d1"])
                if l[t] < st["d1low"]:
                    st["state"] = 1
                    low = min(low, l[t])
                elif d1 is not None and t - d1 >= 3 and (c[t] / c[t - 1] - 1) * 100 >= gain and v[t] > v[t - 1]:
                    if c[t] - low > 0:
                        out = float(low)
                    st["state"] = 0
            if c[t] >= hh[t] * 0.999:
                st["state"] = 0
        st["low"] = None if (isinstance(low, float) and math.isnan(low)) else float(low)
        return out

    def levels(self, S, side, cell):
        out = []
        for tr in S["open"]:
            out += [(tr["stop"], "below" if side > 0 else "above"), (tr["target"], "above" if side > 0 else "below")]
        return out


# --------------------------------------------------------------------------------------------- 12. Legend's day leg
class LBDD(Rule):
    """Legend's Buy Day, the day leg (milkmantrades.com/legends-buy-day.html section 8; his package's
    02_buyday_backtest.py, LEG 2), long only: after exactly k sessions that each made a lower low than the one before
    (the one before them did not), buy the next open when it sits less than `gate` x ATR over the prior close (ATR =
    the mean of the prior `atrn` daily ranges); stop one tick under the prior low, no trade when the open is already
    at or under it; otherwise sell that session's close. The setup lives for the next session only."""
    name, sets = "LBDD", ("index",)

    def end(self, S, X, t, side, cell):
        k, n = int(cell["k"]), int(cell["atrn"])
        if side <= 0 or t < max(k + 1, n - 1):
            return []
        l = X.l
        if all(l[t - j] < l[t - j - 1] for j in range(k)) and not l[t - k] < l[t - k - 1]:
            atr = float(np.mean(X.h[t - n + 1:t + 1] - l[t - n + 1:t + 1]))
            if atr > 0:
                S.setdefault("next_open", []).append({"signal": X.dates[t], "tid": _tid(S, X, t), "pc": float(X.c[t]),
                                                      "atr": atr, "stop": round(float(l[t]) - float(cell["tick"]), 6)})
        return []

    def open(self, S, X, t, side, cell):
        out = []
        for p in list(S.get("next_open") or []):
            if p["signal"] >= X.dates[t]:
                continue
            S["next_open"].remove(p)
            o = float(X.o[t])
            if (o - p["pc"]) / p["atr"] < float(cell["gate"]) and o > p["stop"]:
                ev = _ev("enter", X.dates[t], o, "open", p["tid"], signal=p["signal"])
                S["open"].append(_new_trade(ev, side, signal=p["signal"], stop=p["stop"]))
                out.append(ev)
        return out

    def touch(self, S, X, t, side, cell, lo, hi, first):
        out = []
        for tr in list(S["open"]):
            if tr["i"] == X.dates[t] and lo <= tr["stop"]:
                out.append(_close_trade(S, tr, _ev("exit", X.dates[t], tr["stop"], "touch", tr["tid"]), False))
        return out

    def close(self, S, X, t, side, cell):
        out = []
        for tr in list(S["open"]):                       # a day trade: whatever is open leaves at the close
            if tr["i"] <= X.dates[t]:
                out.append(_close_trade(S, tr, _ev("exit", X.dates[t], X.c[t], "close", tr["tid"]), False))
        return out

    def levels(self, S, side, cell):
        return [(tr["stop"], "below") for tr in S["open"]]


RULES = {r.name: r for r in (D7(), LBD(), DOW(), DBB(), GG(), E21(), PO(), RIB(), CEX(), BIG(), FTD(), LBDD())}


def replay(name, X, side, cell, gg_last=None):
    """feed every completed bar through the rule (open, touch over the whole bar, close, end); returns (events, state).
    gg_last: per bar, the index of its period's last bar (the study's htf_levels `last`)."""
    rule = RULES[name]
    S = _fresh({})
    evs = []
    for t in range(X.n):
        if name == "GG":
            L = int(gg_last[t])
            rule.begin(S, X, t, side, cell, period_last=X.dates[L], left=L - t)
        evs += rule.open(S, X, t, side, cell)
        evs += rule.touch(S, X, t, side, cell, X.l[t], X.h[t], True)
        evs += rule.close(S, X, t, side, cell)
        evs += rule.end(S, X, t, side, cell)
    return evs, S


def trades(evs):
    """closed trades from events: [(entry date, exit date, entry px, exit px, tid, signal date)] in entry order."""
    ent = {e["tid"]: e for e in evs if e["kind"] == "enter"}
    out = []
    for e in evs:
        if e["kind"] == "exit" and e["tid"] in ent:
            a = ent[e["tid"]]
            out.append((a["date"], e["date"], a["px"], e["px"], e["tid"], a.get("signal")))
    return sorted(out)
