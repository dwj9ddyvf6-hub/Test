"""The lab's execution policies and their evaluator: one decision (time, side, price, ATR) executed under each policy on
the bars that followed it (docs/research/2026-10-18-lab/DESIGN.md section 3).

Point in time, by construction: the evaluator sees a view of the tape that holds only bars starting after the decision
(the daily bars of the sessions opening after it, the hourly bars starting after it). The two facts from before it that
a policy needs come in from the caller: the ATR (bars completed at the decision) and, for the gap rule, the close
before the next session's open (known before that open, where the rule acts). Prices are side-adjusted (a short's bars
are negated and their highs and lows swapped), so one set of rules serves both sides: a stop is below, a target above.
Session indices count from the next session (0); the decision session, when the decision falls inside it, is -1.

Mechanics: a gap through a level at a bar's open exits at the open; a stop and a target inside one bar is the stop; in
the bar a limit filled in only the stop is checked (its high may have come before the fill); breakeven and the
chandelier's ratchet apply from the bar after the one that set them; a time exit N is the open of the N-th session
after the entry session (the desk's time_sessions rule). Market-type fills pay COST_BPS a side; limit entries, targets
and the paper benchmark pay nothing. An unfilled or skipped policy is a zero outcome.

Outcome states: pending (the entry cannot be known yet), open (entered, the exit not yet known), done (final: filled
and exited, or not filled), nodata (no ATR, or no decision price for a policy that needs one)."""
from datetime import date

from .. import calendar as cal
from .tape import in_session

COST_BPS = 5.0
REFERENCE = "nso_t5"
BENCHMARKS = ("paper_t5",)
WINDOWS = (1, 5, 10, 20)                 # MAE / MFE windows, sessions after the entry session
OPEN, INTRABAR = "open", "intrabar"      # how a path's first bar was entered: at its open, or inside it at a limit

# name: (entry, entry argument, exit), the reference first
POLICIES = {
    "nso_t5": ("nso", None, ("time", 5)),
    "nbo_t5": ("nbo", None, ("time", 5)),
    "nsc_t5": ("nsc", None, ("time", 5)),
    "lim_1s_t5": ("limit", (0.0, 1), ("time", 5)),
    "pull_3s_t5": ("limit", (0.5, 3), ("time", 5)),
    "gapA_t5": ("gap", -1.0, ("time", 5)),
    "gapF_t5": ("gap", 1.0, ("time", 5)),
    "paper_t5": ("paper", None, ("time", 5)),
    "nso_t1": ("nso", None, ("time", 1)),
    "nso_t10": ("nso", None, ("time", 10)),
    "nso_t20": ("nso", None, ("time", 20)),
    "nso_b15": ("nso", None, ("bracket", 1.5, 3.0, 10, False)),
    "nso_be": ("nso", None, ("bracket", 1.5, 3.0, 10, True)),
    "nso_ch": ("nso", None, ("chandelier", 2.0, 3.0, 20)),
    # the open family's own arms (OPEN_TESTS below): rules the desks' studies rejected, or never tested at a realistic
    # cost, re-tested forward rather than taken as settled; each is judged against the same hold without it
    "nso_s8_t20": ("nso", None, ("pct", 0.08, None, 20)),
    "nso_s15_t20": ("nso", None, ("pct", 0.15, None, 20)),
    "nso_tp5_t20": ("nso", None, ("pct", None, 0.05, 20)),
    "nso_tp10_t20": ("nso", None, ("pct", None, 0.10, 20)),
    "nso_cts5_t20": ("nso", None, ("cond", 5, 20)),
    # red-day entries (EXECUTION-KNOWLEDGE.md A2-A5): the first red index close within 5 sessions with the name at or
    # under 1.02x the decision price; held to the plain entry's own exit (the open of session 20), so the comparison
    # is the entry alone
    "red5c_spy": ("red", ("SPY", 5, 1.02, "close", "close"), ("until", 20)),
    "red5c_own": ("red", ("own", 5, 1.02, "close", "close"), ("until", 20)),
    "red5o_own": ("red", ("own", 5, 1.02, "open", "open"), ("until", 20)),
    "red5o_skip_own": ("red", ("own", 5, 1.02, "open", "skip"), ("until", 20)),
    # the owner's fear-day rule (2026-10-18): buy only on a day the index and the name both close red, within 5
    # sessions; the same exit as the plain entry
    "fear5c_own": ("fear", ("own", 5, "close", "skip"), ("until", 20)),
    "fear5c_qqq": ("fear", ("QQQ", 5, "close", "skip"), ("until", 20)),
    "fear5c_spy": ("fear", ("SPY", 5, "close", "skip"), ("until", 20)),
    "fear5c_own_fb": ("fear", ("own", 5, "close", "close"), ("until", 20)),
    "fear5o_own": ("fear", ("own", 5, "open", "skip"), ("until", 20)),
    # exp1's intraday arms (desk/lab/arms.py ARMS; DESIGN.md section 14): entries on the decision's own intraday path,
    # inside the sleeve's own entry window, against the immediate entry on the same path ("now"); each held to the open
    # of session 20, so the comparison is the entry alone. Long only. In no primary or open comparison (ARM_ONLY)
    "now_u20": ("now", None, ("until", 20)),
    "lod_u20": ("lod", (0.65, 0.04, 0.10), ("until", 20)),
    "piv30_u20": ("piv30", None, ("until", 20)),
}
TEXT = {
    "nso_t5": "next session open, exit after 5 sessions (the reference)",
    "nbo_t5": "next bar open (1h where cached, else the next session open), 5 sessions",
    "nsc_t5": "next session close, 5 sessions",
    "lim_1s_t5": "limit at the decision price for 1 session (never chase), 5 sessions",
    "pull_3s_t5": "limit at the decision price - 0.5 ATR for 3 sessions (pullback), 5 sessions",
    "gapA_t5": "next session open, skipped on a gap > 1 ATR against, 5 sessions",
    "gapF_t5": "next session open, skipped on a gap > 1 ATR in favour, 5 sessions",
    "paper_t5": "the decision price at the decision time, 5 sessions (benchmark: never recommended)",
    "nso_t1": "next session open, exit after 1 session",
    "nso_t10": "next session open, exit after 10 sessions",
    "nso_t20": "next session open, exit after 20 sessions",
    "nso_b15": "next session open, 1.5 ATR stop / 3 ATR target within 10 sessions",
    "nso_be": "next session open, 1.5 ATR stop / 3 ATR target within 10 sessions, breakeven after +1R",
    "nso_ch": "next session open, 2 ATR stop + 3 ATR chandelier trail within 20 sessions",
    "nso_s8_t20": "next session open, an 8% stop, 20 sessions",
    "nso_s15_t20": "next session open, a 15% stop, 20 sessions",
    "nso_tp5_t20": "next session open, a 5% profit cap, 20 sessions",
    "nso_tp10_t20": "next session open, a 10% profit cap, 20 sessions",
    "nso_cts5_t20": "next session open, out at session 5 unless in profit, else 20 sessions",
    "red5c_spy": "the first red SPY close within 5 sessions (name <= 1.02x), else the 5th close; out at session 20",
    "red5c_own": "the first red close of the name's own index within 5 sessions (name <= 1.02x), else the 5th close",
    "red5o_own": "the open after the first red own-index close within 5 sessions, else the 6th open",
    "red5o_skip_own": "the open after the first red own-index close within 5 sessions, else no trade",
    "fear5c_own": "the close of the first day the name's own index and the name both close red within 5 sessions, "
                  "else no trade",
    "fear5c_qqq": "the close of the first day QQQ and the name both close red within 5 sessions, else no trade",
    "fear5c_spy": "the close of the first day SPY and the name both close red within 5 sessions, else no trade",
    "fear5c_own_fb": "the close of the first own-index-and-name red day within 5 sessions, else the 5th close",
    "fear5o_own": "the open after the first own-index-and-name red close within 5 sessions, else no trade",
    "now_u20": "the first intraday bar's open inside the entry window (the intraday arms' comparator); out at "
               "session 20",
    "lod_u20": "ChartsLector's LoD entry: the first price inside the window at most the day's low + 0.65 ATR with the "
               "stop (the low - 0.1 ATR) under 4% of price, else no trade; out at session 20",
    "piv30_u20": "ChartsLector's 30-minute pivot: the half hour's open after the first of his two 4-bar patterns inside "
                 "the window, else no trade; out at session 20",
}
# The open family: comparisons the primary family (every policy against the reference) does not make, each a paired
# difference on the same signals against the matching hold, with its own BH (a re-test never raises the primary
# family's bar). The ids name the verdicts re-tested (docs/research/2026-10-18-lab/EXECUTION-KNOWLEDGE.md). Kept open
# on purpose: those verdicts came from one strong 2023-25 tape, gates built for false positives only, conditional
# measurement and, for the femto studies, a 150 bp cost hurdle (EXECUTION-KNOWLEDGE.md section 4).
OPEN_TESTS = {
    "hard_stop_8pct": ("nso_s8_t20", "nso_t20", "an 8% stop on a 20-session hold (B2: rejected on daily lanes)"),
    "hard_stop_15pct": ("nso_s15_t20", "nso_t20", "a 15% stop on a 20-session hold (B2, B4)"),
    "profit_cap_5pct": ("nso_tp5_t20", "nso_t20", "a 5% profit cap on a 20-session hold (C2: rejected)"),
    "profit_cap_10pct": ("nso_tp10_t20", "nso_t20", "a 10% profit cap on a 20-session hold (C2: rejected)"),
    "chandelier_trail": ("nso_ch", "nso_t20", "a 2 ATR stop and 3 ATR chandelier trail on the same 20 sessions "
                                              "(C7: 159 of 159 significant results harmful, all in one tape)"),
    "breakeven": ("nso_be", "nso_b15", "breakeven after +1R inside the same 1.5 / 3 ATR bracket (C8)"),
    "no_progress_exit": ("nso_cts5_t20", "nso_t20", "out at session 5 unless in profit (untested: METHODS.md X5)"),
    "red_close_spy": ("red5c_spy", "nso_t20", "buy the first red SPY close, else the 5th close (A2, A3: lc2's RED5-FB "
                                              "on SPY for every name; the close is known only at the bell, a small "
                                              "look-ahead)"),
    "red_close_own": ("red5c_own", "nso_t20", "lc2's RED5-FB on the name's own index (QQQ for semis, memory, tech and "
                                              "internet names, SPY for the rest and for broad funds)"),
    "red_next_open_own": ("red5o_own", "nso_t20", "buy the open after the first red own-index close, else the 6th "
                                                  "open (R19's causal version)"),
    "red_or_skip_own": ("red5o_skip_own", "nso_t20", "the open after a red own-index close, else no trade (A4, A5: "
                                                     "rejected as harmful on book tests; Lazarus runs a stricter one)"),
    "fear_day_own": ("fear5c_own", "nso_t20", "buy only on a day the name's own index (QQQ for semis, memory, tech "
                                              "and internet, SPY else) and the name both close red, within 5 "
                                              "sessions (the owner's rule; Lazarus fear_day without its cap)"),
    "fear_day_own_uptrend": ("fear5c_own", "nso_t20", "the same, on names in an uptrend at the signal (close above "
                                                      "the 50-day, the 50-day above the 200-day)"),
    "fear_day_qqq": ("fear5c_qqq", "nso_t20", "the same with QQQ for every name"),
    "fear_day_spy": ("fear5c_spy", "nso_t20", "the same with SPY for every name"),
    "fear_day_own_else_close": ("fear5c_own_fb", "nso_t20", "the same, but the 5th close when no fear day comes: "
                                                            "the timing alone, nothing skipped"),
    "fear_day_own_next_open": ("fear5o_own", "nso_t20", "the open after the fear-day close (no look-ahead: a close "
                                                        "is known only at the bell)"),
}
OPEN_CONTEXT = {"fear_day_own_uptrend": "uptrend"}     # a test run on the rows whose context flag is true
OPEN_ONLY = tuple(sorted({a for a, _, _ in OPEN_TESTS.values()} - {"nso_ch", "nso_be"}))   # in no primary comparison
ARM_ONLY = ("lod_u20", "now_u20", "piv30_u20")   # exp1's arms: judged by their own rules (desk/lab/arms.py)
UNTIL_N = max(spec[1] for _, _, spec in POLICIES.values() if spec[0] == "until")   # the furthest absolute exit
INTRADAY = ("now", "lod", "piv30")     # entries on the window's intraday path (After.path; piv30: After.path30)
EMA_N = 20                             # the pivot's EMA of the 30-minute closes
MARK_S = 1800                          # the intraday arms' mark-out horizon: 30 minutes after the fill


class After:
    """the bars of a tape that start after t0, side-adjusted: days (session, open_t, close_t, o, h, l, c, v) of the
    sessions opening after t0, and live, the hourly bars of the decision session after t0 (hourly: they cover it).
    window (the intraday arms; long only): {"session", "start", "end", "low0"} -> path, every bar of the window's
    session that starts after t0 on the finest series covering it (tape.window_path), its interval path_iv, the
    session index e of that session (-1: the decision's own, 0: the next), and win, the state when the path cannot be
    read: "pending" (the session has not closed by the tape's clock) or "nodata" (no intraday series covers it)"""

    def __init__(self, tape, t0, sgn, hourly, window=None):
        k = tape.next_day(t0)
        days = tape.days[k:] if k is not None else []
        session = in_session(t0)
        live = [b for b in tape.hours_after(t0, session)] if (hourly and session) else []
        if sgn < 0:
            days = [(s, a, b, -o, -l, -h, -c, v) for s, a, b, o, h, l, c, v in days]
            live = [(s, e, -o, -l, -h, -c, d) for s, e, o, h, l, c, d in live]
        assert all(d[1] > t0 for d in days) and all(b[0] > t0 for b in live)
        self.days, self.live = days, live
        self.path, self.path_iv, self.win, self.window, self.e = [], None, "nodata", window, None
        self.path30 = []
        if window and sgn > 0:
            d = window["session"]
            self.e = -1 if d == session else 0
            if cal.session_close(d) > tape.until:
                self.win = "pending"
            elif self.e == 0 and not (days and days[0][0] == d):
                self.win = "nodata"                     # the window's session has no daily bar after the decision
            else:
                self.path_iv, self.path = tape.window_path(t0, float("inf"), d)
                self.win = None if self.path_iv else "nodata"
                if tape.covers("30m", d):               # the pivot reads half hours only (his is30min)
                    self.path30 = [b for b in tape.bars_of("30m", d) if b[0] > t0]
        assert all(b[0] > t0 for b in self.path) and all(b[0] > t0 for b in self.path30)


def _hour(b, how=None):
    return (b[2], b[3], b[4], b[5], -1, how, b[0], b[1])


def _day(d, j, how=None):
    return (d[3], d[4], d[5], d[6], j, how, d[1], d[2])


def _bar(b, j, how=None):
    """an intraday path bar (start, end, o, h, l, c, session) as a path element of session index j"""
    return (b[2], b[3], b[4], b[5], j, how, b[0], b[1])


def _win_fill(v, i, px, how, cost, path=None, path_iv=None, **extra):
    """an intraday arm's fill at path bar i, at px: the rest of the window's session is the path's head. The mark-out:
    the open of the first path bar starting MARK_S after the fill bar's start (else the session's last close)"""
    path = v.path if path is None else path
    b = path[i]
    nxt = next((x for x in path[i:] if x[0] >= b[0] + MARK_S), None)
    mark, mark_at = (nxt[2], nxt[0]) if nxt else (path[-1][5], path[-1][1])
    extra.update(path_iv=path_iv or v.path_iv, mark30_bps=round((mark / px - 1.0) * 1e4, 2),
                 mark_s=round(mark_at - b[0]))
    return {"state": "filled", "at": b[0], "px": px, "e": v.e, "next": v.e + 1, "cost": cost, "extra": extra,
            "head": [_bar(b, v.e, how)] + [_bar(x, v.e) for x in path[i + 1:]]}


def pivot(b0, b1, b2, b3, s):
    """ChartsLector's two 4-bar patterns on 30-minute bars (o, h, l, c), b0 the bar closing now, s EMA20 of the
    30-minute closes through b0 -> "cond1", "cond2" or None, exactly as `30 min Pivot` codes them"""
    o0, h0, l0, c0 = b0
    o1, h1, l1, c1 = b1
    o2, h2, l2, c2 = b2
    o3, h3, l3, c3 = b3
    if abs(c0 - s) / c0 < 0.05 and o0 < s and c0 > o0 and c0 > o2 and c0 > c1 and o2 > c2 and c2 < c1 and o1 < c1 \
            and o3 > c3 and c3 > c2 and c0 > o3:
        return "cond1"
    if o3 < c3 and o2 < c2 and o1 < c1 and h2 < h3 and h1 < h3 and l2 > l3 and l1 > l3 and c0 > c1 and c0 > c2 \
            and c0 > c3 and h0 < h3:
        return "cond2"
    return None


def _intraday(v, kind, arg, atr, cost):
    """the intraday arms' entries on the window's path (long only): now, the first bar's open inside the window; lod,
    ChartsLector's LoD entry (his BLUE state): the first price at most the running day's low + band x ATR with the
    stop, the low - buf x ATR, under cap of the price. At a bar's open the running low includes the open; inside a bar
    the price falls to the ceiling before it can make a new low (the ceiling is above the low while 0.1 ATR < 4% of
    the low), so a bar reaching the ceiling fills there"""
    if v.window is None or v.e is None:
        return {"state": "nodata"}
    if v.win:
        return {"state": v.win}
    lo, hi = v.window.get("start") or float("-inf"), v.window["end"]
    inside = [i for i, b in enumerate(v.path) if lo <= b[0] < hi]
    if not inside:
        return {"state": "nodata", "skip": "no intraday bar inside the window"}
    if kind == "now":
        return _win_fill(v, inside[0], v.path[inside[0]][2], OPEN, cost)
    if kind == "piv30":
        return _pivot(v, lo, hi, cost)
    band, cap, buf = arg
    low = v.window.get("low0")                          # the running low through the decision (completed bars)
    for i, b in enumerate(v.path):
        if b[0] >= hi:
            break
        o, lw = b[2], b[4]
        run = o if low is None else min(low, o)
        if b[0] >= lo:
            ceil = min(run + band * atr, (run - buf * atr) / (1.0 - cap))
            if o <= ceil or lw <= ceil:
                px = o if o <= ceil else ceil
                return _win_fill(v, i, px, OPEN if o <= ceil else INTRABAR, cost, lod=round(run, 6),
                                 stop=round(run - buf * atr, 6), stop_pct=round(100 * (1 - (run - buf * atr) / px), 3))
        low = min(run, lw)
    return {"state": "skipped", "skip": "never within %g ATR of the day's low with the stop under %g%% inside the "
                                        "window" % (band, 100 * cap)}


def _pivot(v, lo, hi, cost):
    """the half hour's open after the first pattern bar inside the window (a close is known only at the bell), the
    entry bar inside the window too; else a skip. The EMA and the last three half hours before the path come in with
    the window (window.piv: completed by the path's first close)"""
    pv = v.window.get("piv") or {}
    if not v.path30 or pv.get("ema") is None or len(pv.get("hist") or ()) < 3:
        return {"state": "nodata", "skip": "no 30-minute bars cover the window's session"}
    alpha = 2.0 / (EMA_N + 1)
    ema, prev = pv["ema"], [tuple(x) for x in pv["hist"]]       # prev: the three half hours before, oldest first
    for i, b in enumerate(v.path30):
        if b[0] >= hi:
            break
        bar = (b[2], b[3], b[4], b[5])
        ema = alpha * b[5] + (1.0 - alpha) * ema
        hit = pivot(bar, prev[-1], prev[-2], prev[-3], ema) if b[0] >= lo else None
        prev = prev[1:] + [bar]
        if hit and i + 1 < len(v.path30) and v.path30[i + 1][0] < hi:
            nb = v.path30[i + 1]
            return _win_fill(v, i + 1, nb[2], OPEN, cost, path=v.path30, path_iv="30m", pattern=hit, signal_at=b[0])
    return {"state": "skipped", "skip": "no 30-minute pattern inside the window"}


def _buy_at(v, j, at_, cost):
    """a buy at session j's close, or at the open after it (j + 1); pending while that open is not cached"""
    if at_ == "close":
        d = v.days[j]
        return {"state": "filled", "at": d[2], "px": d[6], "e": j, "head": [], "next": j + 1, "cost": cost}
    if j + 1 >= len(v.days):
        return {"state": "pending"}
    d = v.days[j + 1]
    return {"state": "filled", "at": d[1], "px": d[3], "e": j + 1, "head": [_day(d, j + 1, OPEN)], "next": j + 2,
            "cost": cost}


def _entry(v, kind, arg, t0, px, atr, prev, ctx=None):
    """-> {"state": filled|skipped|pending|nodata, ...}: when and where the policy's entry fills (side-adjusted), the
    session index it belongs to (e), the path's first bars after the entry (head) and where the daily path resumes"""
    cost = COST_BPS / 1e4
    if kind in INTRADAY:                                 # exp1's intraday arms, on the window's own path
        return _intraday(v, kind, arg, atr, cost)
    if kind == "paper":                                  # held from the decision (the session before the next open)
        if px is None:
            return {"state": "nodata"}
        return {"state": "filled", "at": t0, "px": px, "e": -1, "head": [_hour(b) for b in v.live], "next": 0,
                "cost": 0.0}
    if kind == "nbo" and v.live:                         # the next hourly bar of the decision session
        return {"state": "filled", "at": v.live[0][0], "px": v.live[0][2], "e": -1, "next": 0, "cost": cost,
                "head": [_hour(b, OPEN if i == 0 else None) for i, b in enumerate(v.live)]}
    if kind == "limit":
        if px is None:
            return {"state": "nodata"}
        off, n = arg
        lim = px - off * atr
        work = [(_hour(b), i) for i, b in enumerate(v.live)] + [(_day(d, j), None) for j, d in enumerate(v.days[:n])]
        for b, i in work:
            o, h, lo, c, j, _, s, end = b
            if o <= lim or lo <= lim:
                fill = (o, h, lo, c, j, OPEN if o <= lim else INTRABAR, s, end)
                rest = [_hour(x) for x in v.live[i + 1:]] if i is not None else []
                return {"state": "filled", "at": s, "px": o if o <= lim else lim, "e": j, "head": [fill] + rest,
                        "next": j + 1, "cost": 0.0}
        return {"state": "skipped", "skip": "limit not reached"} if len(v.days) >= n else {"state": "pending"}
    if kind in ("red", "fear"):                          # waiting for the market's red day (EXECUTION-KNOWLEDGE A2-A5)
        if kind == "red":                                # red: the index closes red, the name <= cap x px
            index, n, cap, at_, fb = arg
        else:                                            # fear: the index and the name both close red
            (index, n, at_, fb), cap = arg, None
        if index == "own":                               # the name's own index (desk/lab own_index)
            index = (ctx or {}).get("own")
        red = ((ctx or {}).get("red") or {}).get(index)
        if red is None or (kind == "red" and px is None):
            return {"state": "nodata"}
        last = prev                                      # the name's close before each session (fear)
        for j, d in enumerate(v.days[:n]):
            hit = d[0] in red and (d[6] <= cap * px if kind == "red" else last is not None and d[6] < last)
            last = d[6]
            if hit:
                return _buy_at(v, j, at_, cost)
        if len(v.days) < n + (1 if at_ == "open" and fb == "open" else 0):
            return {"state": "pending"}
        if fb in ("close", "open"):
            return _buy_at(v, n - 1, fb, cost)
        what = "red %s close" % index if kind == "red" else "day %s and the name both closed red" % index
        return {"state": "skipped", "skip": "no %s in %d sessions" % (what, n)}
    if kind == "nwk":                                    # the next week's first open (FEED-06's Monday open)
        wk = cal._as_date(float(t0)).isocalendar()[:2]
        for j, d in enumerate(v.days):
            if date.fromisoformat(d[0]).isocalendar()[:2] > wk:
                return {"state": "filled", "at": d[1], "px": d[3], "e": j, "head": [_day(d, j, OPEN)], "next": j + 1,
                        "cost": cost}
        return {"state": "pending"}
    if not v.days:
        return {"state": "pending"}
    d = v.days[0]
    if kind == "gap":
        if prev is None:
            return {"state": "nodata"}
        g = (d[3] - prev) / atr
        if (arg < 0 and g < arg) or (arg > 0 and g > arg):
            return {"state": "skipped", "skip": "gap %+.2f ATR" % g}
    if kind == "nsc":
        return {"state": "filled", "at": d[2], "px": d[6], "e": 0, "head": [], "next": 1, "cost": cost}
    return {"state": "filled", "at": d[1], "px": d[3], "e": 0, "head": [_day(d, 0, OPEN)], "next": 1, "cost": cost}


def _path(v, ent, horizon):
    """the bars after the entry, (o, h, l, c, session index, how entered, start, end), to session e + horizon, and at
    least to UNTIL_N: an "until" exit is an absolute session, which an entry in the decision's own session (e = -1)
    would otherwise never reach"""
    for b in ent["head"]:
        yield b
    for j in range(ent["next"], min(len(v.days), max(ent["e"] + horizon, UNTIL_N) + 1)):
        yield _day(v.days[j], j)


def _horizon(spec):
    return spec[3] if spec[0] in ("bracket", "pct") else spec[-1]


def _exit(path, ent, spec, atr):
    """-> (reason, price, at, session index) of the exit, or None while it is not known yet"""
    ep, e, n = ent["px"], ent["e"], _horizon(spec)
    if spec[0] == "until":                               # a common exit: the open of session n after the decision
        for b in path:
            if b[4] >= n:
                return "time", b[0], b[6], b[4]
        return None
    if spec[0] == "time":
        for b in path:
            if b[4] >= e + n:
                return "time", b[0], b[6], b[4]
        return None
    if spec[0] == "cond":                                # at the open of session e + k: out unless in profit, then hold
        checked = False
        for b in path:
            if b[4] >= e + n:
                return "time", b[0], b[6], b[4]
            if not checked and b[4] >= e + spec[1]:
                checked = True
                if b[0] <= ep:
                    return "no_progress", b[0], b[6], b[4]
        return None
    if spec[0] == "pct":                                 # a stop and / or a cap as a share of the entry price: the
        u = abs(ep) / atr                                # bracket's rules in this decision's ATR units
        spec = ("bracket", None if spec[1] is None else spec[1] * u, None if spec[2] is None else spec[2] * u,
                spec[3], False)
    stop = first = ep - spec[1] * atr if spec[1] is not None else float("-inf")
    tgt = ep + spec[2] * atr if spec[0] == "bracket" and spec[2] is not None else None
    trig = ep + spec[1] * atr if spec[1] is not None else float("inf")    # +1R: the bracket's initial risk
    hh = ep
    moved = "breakeven" if spec[0] == "bracket" else "trail"
    for o, h, lo, c, j, how, s, end in path:
        if j >= e + n:
            return "time", o, s, j
        if how is None:                                  # a later bar: its open may gap through a level
            if o <= stop:
                return ("stop" if stop <= first else moved), o, s, j
            if tgt is not None and o >= tgt:
                return "target", o, s, j
        if lo <= stop:                                   # stop first: a bar reaching both is the stop
            return ("stop" if stop <= first else moved), stop, end, j
        if tgt is not None and how != INTRABAR and h >= tgt:
            return "target", tgt, end, j
        top = c if how == INTRABAR else h
        if spec[0] == "bracket" and spec[4] and top >= trig:
            stop = max(stop, ep)                         # breakeven, from the next bar
        if spec[0] == "chandelier":
            hh = max(hh, top)
            stop = max(stop, hh - spec[2] * atr)
    return None


def _excursions(bars, ent, atr):
    """(MAE, MFE) in ATR from the entry over each window (to the open of session e + N), None where incomplete"""
    ep, e = ent["px"], ent["e"]
    mae, mfe = [], []
    for n in WINDOWS:
        lo = hi = ep
        done = False
        for o, h, low, c, j, how, s, end in bars:
            if j >= e + n:
                lo, hi, done = min(lo, o), max(hi, o), True
                break
            lo, hi = min(lo, low), max(hi, c if how == INTRABAR else h)
        mae.append(round((ep - lo) / atr, 4) if done else None)
        mfe.append(round((hi - ep) / atr, 4) if done else None)
    return mae, mfe


def evaluate(tape, t0, side, px, atr, hourly=False, prev_close=None, policies=None, ctx=None, window=None):
    """{policy: outcome} for one decision: at t0, `side` ("long" / "short"), decision price px (None: no paper or
    limit policy), the ATR at the decision, hourly (the tape's hourly bars cover the decision session) and prev_close
    (the close before the next session's open, for the gap rule); ctx {"red": {index: the sessions it closed red}}
    for the red-day entries, which are long-only (a short is nodata); window (the intraday arms, long only):
    {"session", "start", "end", "low0": the running low through the decision, from completed bars}"""
    policies = POLICIES if policies is None else policies
    if not atr or atr <= 0:
        return {name: {"state": "nodata"} for name in policies}
    sgn = 1.0 if side == "long" else -1.0
    v = After(tape, t0, sgn, hourly, window)
    spx = None if px is None else sgn * float(px)
    prev = None if prev_close is None else sgn * float(prev_close)
    entries, out = {}, {}
    for name, (kind, arg, spec) in policies.items():
        if (kind, arg) not in entries:
            ent = entries[(kind, arg)] = {"state": "nodata"} if kind in ("red", "fear") + INTRADAY and sgn < 0 else \
                _entry(v, kind, arg, t0, spx, atr, prev, ctx)
            if ent["state"] == "filled":
                ent["path"] = list(_path(v, ent, max(WINDOWS)))
                ent["mae"], ent["mfe"] = _excursions(ent["path"], ent, atr)
        ent = entries[(kind, arg)]
        if ent["state"] != "filled":
            st = "done" if ent["state"] == "skipped" else ent["state"]
            out[name] = {"state": st, "filled": False if st == "done" else None, "skip": ent.get("skip")}
            continue
        o = {"state": "open", "filled": True, "skip": None, "entry_at": round(ent["at"]),
             "entry_px": _px(sgn * ent["px"]), "mae": ent["mae"], "mfe": ent["mfe"], **(ent.get("extra") or {})}
        x = _exit(ent["path"], ent, spec, atr)
        if x is not None:
            reason, xp, xat, j = x
            ret = (xp - ent["px"]) / abs(ent["px"]) - ent["cost"] - (0.0 if reason == "target" else COST_BPS / 1e4)
            o.update(state="done", exit=reason, exit_at=round(xat), exit_px=_px(sgn * xp), held=j - ent["e"],
                     ret_pct=round(100 * ret, 4), r=round(ret * abs(ent["px"]) / atr, 4))
        out[name] = o
    return out


def _px(x):
    return round(float(x), 6)
