"""killed_short_candidates: all six candidates of short_candidates_prereg_2026-10-02.md (midna@main 7969b522, blob
97c9c345) with every tested exit, against the sleeve stepped pass by pass on Views.

The study committed no runner (its scripts stayed in /tmp; KILL_INVENTORY.md section C7 cites only the results file),
so the source is the frozen pre-registration and the results' method notes (short_candidates_2026-10-02.md, blob
e4a80014: the reported RTH re-run kept only sessions with exactly 13 30-minute bars). This harness restates each rule
as the pre-registration wrote it, as a batch over the same random series (the approach of
tools/parity/killed_restated.py), and runs the vendored scanner (desk/vendor/old_desk_research/rsiobv.py, blob
9421874c) unchanged for C6, as the study did:

  C1  r2 = c[12]/c[8] - 1 above the linear 80th percentile of the symbol's previous <= 252 13-bar sessions (>= 63
      observations) -> short close t; (a) cover close t+1, (b) cover open t+1
  C2  r1 = c[12]/c[10] - 1, the same quintile -> short close t, cover close t+1
  C3  (c - min20) / (max20 - min20) >= 0.95 (highs / lows incl. t) and c > mean20 + 1.5 x ATR14 (Wilder: TR0 = h - l,
      the first 14 TRs averaged) -> short close t; (a) cover close t+3; (b) cover at the first touch of mean20 (fixed
      at t) on t+1..t+3, else close t+3
  C4  the closes of t-1 and t in the top 20% of their day's range -> short open t+1, cover close t+2 (every streak day)
  C5  open_t / close_t-1 - 1 >= 2% and open_t >= 0.98 x the 252-session high (excl. t) -> short open t; (a) cover at
      the prior close if the first 30 minutes trade there, else at the first-30m close; (b) the first-30m close
  C6  scan_divergences(30m bars, rsi_periods (8, 13, 21), rsi_lookbacks (8,)): BeR, indicator RSI, STRONG or
      SUPERSTRONG; one per symbol per calendar day (earliest) -> long the next 30m open; out at the close of the 4th /
      8th / 16th bar after the knowable bar

Series: real trading days (the desk calendar, early closes included), per session the complete regular-session
30-minute bars (13; 7 on an early close) moving continuously (each bar opens at the previous close); the session's
last bar closes where the 15:30 (12:30) print stood, so the auction-window price is the close (the sleeve decides
C1-C3 there on the live price: named divergence); the daily bar aggregates the session's bars. Half the cases quote
the session's range in the snapshot (the auction-window snapshot carrying the session's final range, the same
convention) and let the last bar extend the range; the other half quote no range (C3 reads the forming bar from the
30-minute bars) and keep the last bar inside the range so far.

Passes per session: the open (09:31, quotes at the open), 09:45 (a price inside the first bar's range), then -
intraday cases - five seconds after every 30-minute bar closes before the auction window (10:00 ... 15:00) and the
auction window (15:30:05, after the 15:00 bar); daily cases - 10:00:05 and the auction window, the scanner returning
nothing (C6 is exact only on the intraday grid, which the intraday cases run). Bars are visible the moment they close
(the hub without the free plan's 15-minute delay: named divergence). Positions follow the sleeve's own intents (filled
at the pass), so each pass's intents are that pass's ledger changes.

Compared exactly, per case:
  tranches  every field: id, symbol, arm, side, notional, units, entry / exit session and moment, entry / exit pass
            time, reference prices, status, return, the event key, C5's prior close, C3b's mean20, entry and exit
            reasons
  intents   every pass: the sleeve's intents vs the source's trades taken through the desk's own ledger
            (common.TrancheBook.intents over the source's tranches): kind, symbol, side, quantity, price hint, order
            type / tif / window, signal key, reason

The batch states the rules on the pass grid with the sleeve's named readings (the quintile history excludes day t,
top = strictly above the linear 80th percentile; touch exits fire at the first pass priced at or through the level and
fill at that price; C6 is classified at its knowable bar on the sleeve's 30-session window, over every regular-session
bar of the live calendar). Where the pre-registration's literal rule differs, the difference is measured, not
compared, and reported per named divergence (named_divergences): C3b / C5a touch fills (the bar's low through the
level, filled at the level), C6's whole-series classification (the study scanned the full history at once: an OBV
divergence completing up to 3 bars later merges into the signal, or a later RSI divergence takes its OBV match),
the 30-session scan window (vs the causal full history), and early closes (the study's 13-bar-session file had none:
its C6 series skipped them, its C5 had no first 30-minute bar there, its C1 / C2 exits on one are not recoverable).

    python3 -m tools.parity.killed_short [n_daily n_intraday]       (PARITY_JOBS=<workers>, default 1)"""
import json
import math
import os
import random
import sys
from bisect import bisect_right
from datetime import date, timedelta

from desk import calendar as cal
from desk.contract import View
from desk.sleeves.killed import common as K
from desk.sleeves.killed import intraday as IN

from . import write_receipt

N_DAILY = 300
N_INTRADAY = 300
SID = "killed_short_candidates"
NOTIONAL = K.CAPITAL / 100
HOLDS = (4, 8, 16)
SCAN_KW = {"rsi_periods": (8, 13, 21), "rsi_lookbacks": (8,)}
STRONG = ("STRONG", "SUPERSTRONG")
CANDIDATES = ("C1", "C2", "C3", "C4", "C5", "C6")
FIELDS = ("id", "sym", "arm", "side", "notional", "units", "enter_day", "enter_at", "exit_day", "exit_at", "status",
          "entry_ref", "exit_ref", "entered_at", "exited_at", "ret_ref", "event", "prev_close", "mean20", "why",
          "exit_why", "void_why")


# -- series ------------------------------------------------------------------------------------------------------
EARLY_CLOSES = [d for d in (date(2023, 6, 1) + timedelta(days=i) for i in range(1100))
                if cal.is_trading_day(d) and cal.close_minutes(d) != 960]


def sessions_from(rnd, n, near_early_close=False):
    d = date(2023, 6, 1).toordinal() + rnd.randint(0, 1000)
    if near_early_close:                              # an early close inside the stepped sessions
        d = rnd.choice(EARLY_CLOSES).toordinal() - rnd.randint(int(n * 0.45), int(n * 0.85)) * 7 // 5
    out = []
    while len(out) < n:
        x = date.fromordinal(d)
        if cal.is_trading_day(x):
            out.append(x.isoformat())
        d += 1
    return out


def n_bars(day):
    return (cal.close_minutes(day) - 570) // 30


def gen_symbol(rnd, days, inside):
    """one symbol's sessions: complete 30-minute bars moving continuously, the last bar closing at the 15:30 print
    (inside the day's range so far when `inside`); the daily bar aggregates them; p45 = a price inside the first
    bar."""
    px, drift, vol = rnd.uniform(15, 300), 0.0, rnd.choice([0.003, 0.0045, 0.006])
    base_v = rnd.uniform(2e4, 2e5)

    def volume(o, c):                                  # volume rises with the bar's move (OBV follows the tape)
        return float(int(base_v * (1 + 200 * abs(c / o - 1)) * rnd.lognormvariate(0, 0.3)))
    rows = []
    for day in days:
        if rnd.random() < 0.06:
            drift = rnd.choice([-0.006, -0.002, 0.0, 0.0, 0.002, 0.005, 0.009])
        nb, t0 = n_bars(day), cal.session_open(day)
        gap_day = rnd.random() < 0.09
        gap = rnd.choice([0.021, 0.026, 0.04]) if gap_day else rnd.gauss(0, 0.004)
        o = round(max(0.5, px * (1 + gap)), 4)
        push = rnd.choice([0.0, 0.0, 0.0, 0.0025, 0.005, -0.0025])     # afternoon drift: strong closes, top afternoons
        shock = -rnd.uniform(0.003, 0.008) if rnd.random() < 0.035 else 0.0   # a reversal day (C3b's mean20 touch)
        bars, p = [], o
        for j in range(nb - 1):
            mu = drift / nb + shock + (push if j >= nb - 6 else 0.0)
            c = round(max(0.5, p * (1 + rnd.gauss(mu, vol))), 4)
            h = round(max(p, c) * (1 + abs(rnd.gauss(0, vol / 2))), 4)
            lo = round(min(p, c) * (1 - abs(rnd.gauss(0, vol / 2))), 4)
            if j == 0 and gap_day and rnd.random() < 0.5:
                lo = round(min(lo, p * (1 - rnd.uniform(0.005, 0.05))), 4)   # the gap trades back toward the prior close
            bars.append({"t": t0 + 1800 * j, "o": p, "h": h, "l": lo, "c": c, "v": volume(p, c)})
            p = c
        hi, lw = max(b["h"] for b in bars), min(b["l"] for b in bars)
        if inside:
            h, lo = min(hi, max(p, round(rnd.uniform(p, hi), 4))), max(lw, min(p, round(rnd.uniform(lw, p), 4)))
        else:
            h, lo = round(p * (1 + abs(rnd.gauss(0, vol))), 4), round(p * (1 - abs(rnd.gauss(0, vol))), 4)
        bars.append({"t": t0 + 1800 * (nb - 1), "o": p, "h": h, "l": lo, "c": p, "v": volume(p, max(h, p))})
        b0 = bars[0]
        rows.append({"day": day, "t": t0, "o": o, "h": max(b["h"] for b in bars), "l": min(b["l"] for b in bars),
                     "c": p, "v": sum(b["v"] for b in bars), "bars": bars,
                     "p45": min(b0["h"], max(b0["l"], round(rnd.uniform(b0["l"], b0["h"]), 4)))})
        px = p
    return rows


# -- the pass grid ---------------------------------------------------------------------------------------------------
def day_passes(day, fine):
    """[(name, now, index of the bar whose close the pass follows, or None)] of one session."""
    o, c = cal.session_open(day), cal.session_close(day)
    nb = n_bars(day)
    out = [("open", o + 60, None), ("p45", o + 900, None)]
    for j in range(nb - 2 if fine else 1):
        out.append((f"b{j}", o + 1800 * (j + 1) + 5, j))
    out.append(("moc", c - 1800 + 5, nb - 2))
    return out


def build_grid(days, first, fine):
    """the global pass list [(k, name, now, j)] from session `first` on."""
    return [(k, name, now, j) for k in range(first, len(days)) for name, now, j in day_passes(days[k], fine)]


def pass_price(row, name, j):
    if name == "open":
        return row["o"]
    if name == "p45":
        return row["p45"]
    return row["bars"][j]["c"]


# -- the vendored scanner, shared ---------------------------------------------------------------------------------
class Scans:
    """the vendored scan_divergences: the sleeve gets its full output, computed fresh at each call; the batch reads the
    BeR rows of the same window (keyed by the window's bars) or scans the window itself."""

    def __init__(self, real):
        self.real, self.memo = real, {}

    @staticmethod
    def key(bars):
        return len(bars), bars[0]["t"], bars[-1]["t"], hash(tuple(b["c"] for b in bars))

    @staticmethod
    def compact(divs):
        return [(d["indicator"], d["strength"], d["knowable_index"]) for d in divs if d["type"] == "BeR"]

    def for_sleeve(self, bars, **kw):
        divs = self.real(bars, **kw)
        if kw == SCAN_KW and bars:
            self.memo[self.key(bars)] = self.compact(divs)
        return divs

    def for_source(self, bars):
        k = self.key(bars)
        got = self.memo.get(k)
        if got is None:
            got = self.memo[k] = self.compact(self.real(bars, **SCAN_KW))
        return got


# -- the sleeve, stepped ------------------------------------------------------------------------------------------
def norm_intent(i):
    o = i.order
    return [i.kind, i.symbol, i.side, i.qty, i.price_hint, o.type if o else None, o.tif if o else None,
            o.window_s if o else None, i.signal_key, i.reason]


def views(data, days, grid, snapshot):
    """per pass: (now, session, bars {30m, 1d}, quotes) - completed bars only, the hub's 3,400 30-minute bars."""
    flat = {s: [b for r in rows for b in r["bars"]] for s, rows in data.items()}
    ends = {s: [b["t"] + 1800 for b in bl] for s, bl in flat.items()}
    daily = {s: [{kk: r[kk] for kk in ("t", "o", "h", "l", "c", "v")} for r in rows] for s, rows in data.items()}
    for k, name, now, j in grid:
        b30 = {}
        for s in data:
            n = bisect_right(ends[s], now)
            b30[s] = flat[s][max(0, n - 3400):n]
        quotes = {}
        for s, rows in data.items():
            row = rows[k]
            px = pass_price(row, name, j)
            q = {"last": px, "t": now, "day_open": row["o"]}
            if snapshot:                               # the snapshot's session range (Alpaca 'full' reads); in the
                done = row["bars"] if name == "moc" else row["bars"][:(j + 1) if j is not None else 0]   # auction: final
                q["day_high"] = max([b["h"] for b in done] + [px])
                q["day_low"] = min([b["l"] for b in done] + [px])
            quotes[s] = q
        yield now, days[k], {"30m": b30, "1d": {s: d[:k] for s, d in daily.items()}}, quotes


def apply_fills(book, intents):
    for i in intents:
        cur = book.get(i.symbol, 0.0)
        if i.kind == "enter":
            cur += i.qty if i.side == "long" else -i.qty
        elif i.kind == "exit":
            cur = cur - i.qty if cur > 0 else cur + i.qty
        book[i.symbol] = cur


def positions_of(book, quotes):
    return {"EQ:" + s: {"qty": q, "avg": 0.0, "opened_at": 0.0, "meta": {}, "mark": quotes[s]["last"]}
            for s, q in book.items() if abs(q) > 1e-9}


def run_case(data, days, first, fine, snapshot):
    """the sleeve stepped over the grid, its book filled from its own intents.
    -> (every tranche by id, last seen state; [(pass, the ledger's view, the sleeve's intents)])"""
    sl = IN.ShortCandidates()
    sl.UNIVERSE = tuple(data)
    st, seen, book, log = {}, {}, {}, []
    for p, (now, day, bars, quotes) in enumerate(views(data, days, build_grid(days, first, fine), snapshot)):
        pos = positions_of(book, quotes)
        extra = {"pending_orders": [], "closed_trades": []}
        v = View(now=now, session=day, state=st, bars=bars, quotes=quotes, positions=pos, equity=K.CAPITAL,
                 extra=extra)
        out = sl.signal(v)
        st = sl._st
        for t in st.get("tranches", []):
            seen[t["id"]] = dict(t)
        log.append((p, View(now=now, session=day, quotes=quotes, positions=pos, extra=extra),
                    [norm_intent(i) for i in out]))
        apply_fills(book, out)
    return seen, log


# -- the source rules, restated on the pass grid -------------------------------------------------------------------
def strong(r):
    return r["h"] > r["l"] and (r["c"] - r["l"]) / (r["h"] - r["l"]) >= 0.8


def top_quintile(value, hist):
    """strictly above the linear 80th percentile of the previous <= 252 values; None below 63 of them."""
    h = sorted(hist[-252:])
    if len(h) < 63:
        return None
    pos = 0.8 * (len(h) - 1)
    i = int(math.floor(pos))
    return value > h[i] + (h[min(i + 1, len(h) - 1)] - h[i]) * (pos - i)


def atr14(rows):
    tr = [rows[0]["h"] - rows[0]["l"]] + [max(r["h"] - r["l"], abs(r["h"] - q["c"]), abs(r["l"] - q["c"]))
                                         for q, r in zip(rows, rows[1:])]
    if len(tr) < 14:
        return None
    a = sum(tr[:14]) / 14
    for x in tr[14:]:
        a = (a * 13 + x) / 14
    return a


def extended(rows, t):
    """C3 on daily bars 0..t -> (signal, mean20)."""
    if t < 20:
        return False, None
    w = rows[t - 19:t + 1]
    hi, lo, c = max(r["h"] for r in w), min(r["l"] for r in w), rows[t]["c"]
    mean20 = sum(r["c"] for r in w) / 20.0
    atr = atr14(rows[:t + 1])
    if hi <= lo or atr is None:
        return False, mean20
    return (c - lo) / (hi - lo) >= 0.95 and c > mean20 + 1.5 * atr, mean20


def qualifies(rows, last):
    """a BeR RSI STRONG / SUPERSTRONG divergence knowable at index `last`."""
    return any(ind == "RSI" and s in STRONG and ki == last for ind, s, ki in rows)


class Source:
    """the restated rules over one case: each study trade as the ledger's tranche (entry and exit pass), plus the
    literal-rule measurements."""

    def __init__(self, data, days, first, fine, scans=None):
        self.data, self.days, self.first = data, days, first
        self.grid = build_grid(days, first, fine)
        self.at = {(k, name): p for p, (k, name, now, j) in enumerate(self.grid)}
        self.trades = []
        self.named = {"c3b_trades": 0, "c3b_touched_literal": 0, "c3b_exit_literal_differs": 0, "c5a_trades": 0,
                      "c5a_exit_literal_differs": 0, "c5_signals_on_early_close": 0,
                      "c1_c2_trades_exiting_on_early_close": 0}
        self.c6 = {"candidate_bars": 0, "signals_sleeve_reading": 0, "signals_literal": 0, "signals_both": 0,
                   "bars_whole_series_classification": 0, "bars_window_vs_full_history": 0,
                   "bars_early_close_filter": 0, "legs_exit_moved_by_early_close": 0}
        self.rank = {s: i for i, s in enumerate(data)}
        self.scans = scans
        for s in data:
            self.daily_rules(s)
            if scans is not None:
                self.c6_rules(s)
        self.trades.sort(key=lambda r: r["_key"])

    def pidx(self, k, name):
        return self.at.get((k, name))

    def price(self, s, p):
        k, name, now, j = self.grid[p]
        return pass_price(self.data[s][k], name, j)

    def add(self, s, arm, side, enter_day, enter_at, exit_day, exit_at, event, p, cls, why, block, arm_rank, **extra):
        tr = {"id": K.stable_id(SID, arm, s, enter_day, enter_at, event), "sym": s, "side": side,
              "notional": NOTIONAL, "units": None, "arm": arm, "enter_day": enter_day, "enter_at": enter_at,
              "exit_day": exit_day, "exit_at": exit_at, "status": "planned", "entry_ref": None, "exit_ref": None,
              "why": why[:200], "event": event, "_entry_p": p, "_entry_cls": cls, "_exit_p": None, "_exit_cls": None,
              "_planned_exit": (exit_day, exit_at), "_key": (p, block, self.rank[s], arm_rank)}
        tr.update(extra)
        self.trades.append(tr)
        return tr

    @staticmethod
    def set_exit(tr, p, cls, exit_day=None, exit_at=None, why=None):
        if p is None:
            return
        tr["_exit_p"], tr["_exit_cls"] = p, cls
        if exit_day is not None:
            tr["exit_day"], tr["exit_at"], tr["exit_why"] = exit_day, exit_at, why[:160]

    # -- C1..C5 -------------------------------------------------------------------------------------------------
    def daily_rules(self, s):
        rows = self.data[s]
        r2h, r1h = [], []
        for k, row in enumerate(rows):
            c = [b["c"] for b in row["bars"]]
            full = len(c) == 13
            if k >= self.first:
                self.open_rules(s, k)
                if full:                                   # decided on the auction-window price, = c[12]
                    self.c1c2(s, k, c[11] / c[8] - 1.0, c[11] / c[10] - 1.0, r2h, r1h)
                self.c3(s, k)
            if full:
                r2h.append(c[12] / c[8] - 1.0)
                r1h.append(c[12] / c[10] - 1.0)

    def open_rules(self, s, k):
        rows, days = self.data[s], self.days
        t, p = k - 1, self.pidx(k, "open")
        if t < 1:
            return
        if strong(rows[t - 1]) and strong(rows[t]):
            x = self.add(s, "C4", -1, days[k], "open", K.add_sessions(days[k], 1), "close", days[t], p, "mkt",
                         f"strong closes {days[t - 1]} + {days[t]}", 0, 0)
            self.set_exit(x, self.pidx(k + 1, "moc"), "cls")
        o, pc = rows[k]["o"], rows[t]["c"]
        hi = max(r["h"] for r in rows[max(0, t - 251):t + 1])
        if not (pc > 0 and (o - pc) / pc >= 0.02 and o >= 0.98 * hi):
            return
        self.named["c5_signals_on_early_close"] += cal.close_minutes(days[k]) != 960
        b0 = rows[k]["bars"][0]
        for arm, rank in (("C5a", 1), ("C5b", 2)):
            x = self.add(s, arm, -1, days[k], "open", None, None, days[k], p, "mkt",
                         f"gap {o / pc - 1:+.4f} at the high", 0, rank, prev_close=pc)
            if arm == "C5a" and rows[k]["p45"] <= pc:
                self.set_exit(x, self.pidx(k, "p45"), "mkt", days[k], "now", "touched the prior close")
            else:
                self.set_exit(x, self.pidx(k, "b0"), "mkt", days[k], "now", "first-30m close")
            if arm == "C5a":
                self.named["c5a_trades"] += 1
                lit = pc if b0["l"] <= pc else b0["c"]
                self.named["c5a_exit_literal_differs"] += lit != self.price(s, x["_exit_p"])

    def c1c2(self, s, k, r2, r1, r2h, r1h):
        days = self.days
        p, nxt = self.pidx(k, "moc"), K.add_sessions(days[k], 1)
        early = k + 1 < len(days) and cal.close_minutes(days[k + 1]) != 960
        if top_quintile(r2, r2h):
            a = self.add(s, "C1a", -1, days[k], "close", nxt, "close", days[k], p, "cls", f"last-2h {r2:+.4f}", 1, 0)
            b = self.add(s, "C1b", -1, days[k], "close", nxt, "open", days[k], p, "cls", f"last-2h {r2:+.4f}", 1, 1)
            self.set_exit(a, self.pidx(k + 1, "moc"), "cls")
            self.set_exit(b, self.pidx(k + 1, "open"), "mkt")
            self.named["c1_c2_trades_exiting_on_early_close"] += 2 * early
        if top_quintile(r1, r1h):
            x = self.add(s, "C2", -1, days[k], "close", nxt, "close", days[k], p, "cls", f"last-hour {r1:+.4f}", 1, 2)
            self.set_exit(x, self.pidx(k + 1, "moc"), "cls")
            self.named["c1_c2_trades_exiting_on_early_close"] += early

    def c3(self, s, k):
        rows, days = self.data[s], self.days
        ok, mean20 = extended(rows, k)
        if not ok:
            return
        p, x3, m20 = self.pidx(k, "moc"), K.add_sessions(days[k], 3), round(mean20, 6)
        a = self.add(s, "C3a", -1, days[k], "close", x3, "close", days[k], p, "cls", "extended", 1, 3)
        b = self.add(s, "C3b", -1, days[k], "close", x3, "close", days[k], p, "cls", "extended", 1, 4, mean20=m20)
        self.set_exit(a, self.pidx(k + 3, "moc"), "cls")
        touch = None                                  # the first pass of t+1..t+3 priced at or below mean20
        for q in range(p + 1, len(self.grid)):
            if self.grid[q][0] > k + 3:
                break
            if self.price(s, q) <= m20:
                touch = q
                break
        if touch is not None:
            self.set_exit(b, touch, "mkt", days[self.grid[touch][0]], "now", f"touched mean20 {m20:.4f}")
        else:
            self.set_exit(b, self.pidx(k + 3, "moc"), "cls")
        self.named["c3b_trades"] += 1
        lit = next((kk for kk in range(k + 1, min(k + 4, len(days))) if rows[kk]["l"] <= m20), None)
        self.named["c3b_touched_literal"] += lit is not None
        if lit is not None and (touch is None or self.grid[touch][0] != lit or self.price(s, touch) != m20):
            self.named["c3b_exit_literal_differs"] += 1

    # -- C6 -------------------------------------------------------------------------------------------------------
    def c6_rules(self, s):
        rows, days = self.data[s], self.days
        bars, where, first_bar = [], [], {}
        for k, r in enumerate(rows):
            first_bar[k] = len(bars)
            for j, b in enumerate(r["bars"]):
                bars.append(b)
                where.append((k, j, len(r["bars"])))
        ends = [b["t"] + 1800 for b in bars]

        def next_pass(i):
            k, j, nb = where[i]
            return self.pidx(k, f"b{j}") if j < nb - 2 else self.pidx(k, "moc") if j == nb - 2 else \
                self.pidx(k + 1, "open")

        def win(i):                                   # the sleeve's window: the last 30 sessions with bars
            return bars[first_bar[max(0, where[i][0] - 29)]:i + 1]

        birth = None                                  # the first pass whose window holds >= 100 bars
        for k, name, now, j in self.grid:
            n = bisect_right(ends, now)
            if n and len(win(n - 1)) >= 100:
                birth = n - 1
                break
        if birth is None:
            return
        upto = bisect_right(ends, self.grid[-1][2])  # the bars the sleeve has seen by the last pass
        cand = {}
        for i in range(birth + 1, upto):
            w = win(i)
            cand[i] = qualifies(self.scans.for_source(w), len(w) - 1)
        self.c6["candidate_bars"] += len(cand)
        # the literal reading: one whole-series scan (A1, on the live calendar; A2, on the 13-bar-session file)
        a1 = {i: False for i in cand}
        for ind, st, ki in self.scans.for_source(bars[:upto]):
            if ki in a1 and ind == "RSI" and st in STRONG:
                a1[ki] = True
        for i in cand:
            if cand[i] != a1[i]:
                if qualifies(self.scans.for_source(bars[:i + 1]), i) == cand[i]:
                    self.c6["bars_whole_series_classification"] += 1
                else:
                    self.c6["bars_window_vs_full_history"] += 1
        keep13 = [i for i in range(upto) if where[i][2] == 13]
        pos13 = {i: n for n, i in enumerate(keep13)}
        a2 = set()
        for ind, st, ki in self.scans.for_source([bars[i] for i in keep13]):
            if keep13[ki] in cand and ind == "RSI" and st in STRONG:
                a2.add(keep13[ki])
        self.c6["bars_early_close_filter"] += sum(1 for i in cand if a1[i] != (i in a2))

        def deoverlap(sig):
            kept, last = [], None
            for i in sorted(sig):
                if where[i][0] != last:
                    kept.append(i)
                    last = where[i][0]
            return kept

        kept, kept_lit = deoverlap(i for i in cand if cand[i]), deoverlap(a2)
        both = set(kept) & set(kept_lit)
        self.c6["signals_sleeve_reading"] += len(kept)
        self.c6["signals_literal"] += len(kept_lit)
        self.c6["signals_both"] += len(both)
        for i in both:
            for h in HOLDS:
                if i + h < len(bars) and pos13[i] + h < len(keep13) and keep13[pos13[i] + h] != i + h:
                    self.c6["legs_exit_moved_by_early_close"] += 1
        for i in kept:
            p = next_pass(i)
            k_in = self.grid[p][0]
            for n_, h in enumerate(HOLDS):
                x = self.add(s, f"C6:{h}", +1, days[k_in], "open", None, None, int(bars[i]["t"]), p, "mkt",
                             "BeR RSI strong fade (long)", 2, n_)
                if i + h >= len(bars):
                    continue
                kx, jx, nbx = where[i + h]
                if jx == nbx - 1:                     # the exit bar is the session's last: market-on-close
                    self.set_exit(x, self.pidx(kx, "moc"), "cls", days[kx], "close",
                                  f"{h} bars held (exit bar is the session's last)")
                else:
                    self.set_exit(x, next_pass(i + h), "mkt", days[kx], "now", f"{h} bars held")

    # -- the ledger records ----------------------------------------------------------------------------------------
    def states(self, upto):
        """the tranche records after pass `upto` (creation order) and that pass's ledger changes."""
        recs, changes = [], []
        for tr in self.trades:
            if tr["_entry_p"] > upto:
                continue
            r = {k: v for k, v in tr.items() if not k.startswith("_")}
            px = self.price(tr["sym"], tr["_entry_p"])
            u = NOTIONAL / px
            r["units"] = float(max(1, math.floor(u))) if tr["side"] < 0 else round(u, 4)
            r["entry_ref"], r["entered_at"], r["status"] = px, self.grid[tr["_entry_p"]][2], "held"
            if tr["_entry_p"] == upto:
                changes.append((tr["sym"], tr["side"] * r["units"], tr["_entry_cls"], tr["id"]))
            if tr["_exit_p"] is not None and tr["_exit_p"] <= upto:
                if tr["_exit_p"] == upto:
                    changes.append((tr["sym"], -tr["side"] * r["units"], tr["_exit_cls"], tr["id"]))
                xp = self.price(tr["sym"], tr["_exit_p"])
                r["exit_ref"], r["exited_at"], r["status"] = xp, self.grid[tr["_exit_p"]][2], "closed"
                r["ret_ref"] = round(tr["side"] * (xp / px - 1.0), 6)
            else:                                      # the exit lies ahead: the record as planned at entry
                r["exit_day"], r["exit_at"] = tr["_planned_exit"]
                r.pop("exit_why", None)
            recs.append(r)
        return recs, changes

    def expected(self, p, view):
        recs, changes = self.states(p)
        tb = K.TrancheBook({"tranches": recs}, view, SID, whole_short=True)
        tb.changes = changes
        return tb.intents()

    def records(self):
        recs, _ = self.states(len(self.grid) - 1)
        return {r["id"]: [r.get(f) for f in FIELDS] for r in recs}

    def paths(self):
        """{arm: entry pass -> exit pass (class, touch)}: which entry and exit paths the case exercised."""
        def where(p):
            name = self.grid[p][1]
            return "bar" if name.startswith("b") else name
        out = {}
        for tr in self.trades:
            ex = "held"
            if tr["_exit_p"] is not None:
                ex = f"{tr['_exit_cls']}@{where(tr['_exit_p'])}" + (":touch" if "touched" in tr.get("exit_why", "")
                                                                      else "")
            key = f"{tr['arm'].split(':')[0]} {where(tr['_entry_p'])}->{ex}"
            out[key] = out.get(key, 0) + 1
        return out


# -- one case ---------------------------------------------------------------------------------------------------------
def one_case(args):
    seed, case, kind = args
    from desk.vendor.old_desk_research import rsiobv as R
    rnd = random.Random(f"{seed}:{case}")
    fine = kind == "intraday"
    if fine:
        first = rnd.randint(8, 12)
        n = first + (rnd.randint(22, 32) if rnd.random() < 0.25 else rnd.randint(4, 18))
        days = sessions_from(rnd, n, near_early_close=rnd.random() < 0.3)
        syms = [f"S{i}" for i in range(1 if rnd.random() < 0.75 else 2)]
    else:
        days = sessions_from(rnd, rnd.randint(75, 150))
        first = rnd.randint(52, 66)
        syms = [f"S{i}" for i in range(rnd.randint(2, 3))]
    snapshot = rnd.random() < 0.5
    data = {s: gen_symbol(rnd, days, inside=not snapshot) for s in syms}
    real = R.scan_divergences
    scans = Scans(real)
    try:
        R.scan_divergences = scans.for_sleeve if fine else (lambda bars, **kw: [])
        seen, log = run_case(data, days, first, fine, snapshot)
    finally:
        R.scan_divergences = real
    src = Source(data, days, first, fine, scans if fine else None)
    bad_intents = []
    for p, v, mine in log:
        want = [norm_intent(i) for i in src.expected(p, v)]
        if mine != want and len(bad_intents) < 4:
            bad_intents.append({"pass": p, "at": f"{v.session} {K.et_hm(v.now)}", "sleeve": mine[:4],
                                "source": want[:4]})
    mine = {tid: [t.get(f) for f in FIELDS] for tid, t in seen.items()}
    want = src.records()
    per = {c: {"trades": 0, "bad": 0} for c in CANDIDATES}
    for r in want.values():
        per[r[2][:2]]["trades"] += 1
    bad_tr = []
    for tid in sorted(set(mine) | set(want)):
        if mine.get(tid) != want.get(tid):
            per[(mine.get(tid) or want.get(tid))[2][:2]]["bad"] += 1
            if len(bad_tr) < 4:
                bad_tr.append({"sleeve": mine.get(tid), "source": want.get(tid)})
    return {"case": case, "kind": kind, "per": per, "bad_tranches": bad_tr, "bad_intents": bad_intents,
            "passes": len(log), "named": src.named, "c6": src.c6 if fine else None, "snapshot": snapshot,
            "paths": src.paths(),
            "early_closes": sum(1 for d in days if cal.close_minutes(d) != 960)}


def run(n_daily=N_DAILY, n_intraday=N_INTRADAY, seed=20261016):
    jobs = [(seed, c, "daily") for c in range(n_daily)] + [(seed, n_daily + c, "intraday") for c in range(n_intraday)]
    workers = int(os.environ.get("PARITY_JOBS") or 1)
    results = []
    if workers > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(workers) as ex:
            for r in ex.map(one_case, jobs, chunksize=2):
                results.append(r)
                if len(results) % 50 == 0:
                    print(f"case {len(results)}/{len(jobs)}", file=sys.stderr, flush=True)
    else:
        for j in jobs:
            results.append(one_case(j))
            if len(results) % 50 == 0:
                print(f"case {len(results)}/{len(jobs)}", file=sys.stderr, flush=True)
    per = {c: {"cases": 0, "cases_traded": 0, "trades": 0, "identical": 0, "diffs": 0} for c in CANDIDATES}
    named, c6, diffs, paths = {}, {}, [], {}
    for r in results:
        for k, v in r["paths"].items():
            paths[k] = paths.get(k, 0) + v
        for c in CANDIDATES:
            if (c in ("C1", "C2") and r["kind"] != "daily") or (c == "C6" and r["kind"] != "intraday"):
                continue
            pc = per[c]
            pc["cases"] += 1
            pc["trades"] += r["per"][c]["trades"]
            pc["cases_traded"] += r["per"][c]["trades"] > 0
            if r["per"][c]["bad"] or r["bad_intents"]:
                pc["diffs"] += 1
            else:
                pc["identical"] += 1
        for k, v in r["named"].items():
            named[k] = named.get(k, 0) + v
        for k, v in (r["c6"] or {}).items():
            c6[k] = c6.get(k, 0) + v
        if r["bad_tranches"] or r["bad_intents"]:
            diffs.append({"case": r["case"], "kind": r["kind"], "tranches": r["bad_tranches"],
                          "intents": r["bad_intents"]})
    n = len(results)
    res = {"cases": n, "identical": n - len(diffs), "n_diffs": len(diffs), "diffs": diffs[:8], "per_candidate": per,
           "passes": sum(r["passes"] for r in results),
           "cases_by_kind": {"daily": n_daily, "intraday": n_intraday},
           "cases_with_early_close": sum(1 for r in results if r["early_closes"]),
           "cases_with_snapshot_quotes": sum(1 for r in results if r["snapshot"]),
           "named_divergences": {"c1_c5": named, "c6": c6},
           "paths": dict(sorted(paths.items())),
           "sleeves": [SID],
           "source": {"repo": "midna@7969b5229c46403a92290d16da23228e59e7b064",
                      "prereg": "workspace/alpaca-swing-desk/desk/research/short_candidates_prereg_2026-10-02.md "
                                "(blob 97c9c3450b1f3aee037e508f379f54c9d7adec93)",
                      "results": "short_candidates_2026-10-02.md (blob e4a8001421f9f8d07f8b6d272c94e783918c2114)",
                      "inventory": "resurrection/KILL_INVENTORY.md section C7 (blob "
                                   "a799c4f1e069d6e45d908d8a456a3b7c345dbd5a)",
                      "scanner": "desk/vendor/old_desk_research/rsiobv.py (blob "
                                 "9421874ce6074a12de52edc4b53431a05717caa9)"},
           "method": "no committed runner exists (the study's scripts stayed in /tmp): the pre-registered rules of "
                     "C1-C6 restated as a batch on the same random series and pass grid (C6 through the vendored "
                     "scanner, unchanged) vs the ShortCandidates sleeve stepped pass by pass on Views, its positions "
                     "filled from its own intents; every tranche field and every pass's intents (the source's trades "
                     "through common.TrancheBook.intents) exact; the literal rule's differences measured per named "
                     "divergence (named_divergences)"}
    write_receipt("killed_short", res)
    return res


if __name__ == "__main__":
    a = sys.argv[1:]
    r = run(int(a[0]) if a else N_DAILY, int(a[1]) if len(a) > 1 else N_INTRADAY)
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "per_candidate", "named_divergences")}))
