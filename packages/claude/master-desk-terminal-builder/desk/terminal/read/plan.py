"""The plan: one long trade per name, built from its own levels, in one of four forms.

  now        price sits on a floor (an anchored area: a tested swing, a retested breakout, a 52-week extreme, or
             levels of several kinds stacked): buy here, up to the cap (0.15 ATR over the last close)
  pullback   a floor lies under the close: buy there. The floor is chosen by its weight times the odds price reaches
             it within the buy window (the zone's distance against the name's daily volatility)
  breakout   price is under a ceiling or a pattern's trigger: buy on a daily close above it
  turn       the chart is falling: buy on a daily close back over the 20-day, the last swing high or the 50-day

The out line sits under the highest structural line below the buy (the floor's lowest member, a swing low, the line
a breakout or a reclaim cleared), by the larger of 0.25 ATR and 0.3%; a line closer than an ATR, or so close that the
target would come before it less than 28% of the time on a driftless walk (ODDS_MIN), gives way to the next line
down; past 3 ATR of risk there is no honest stop and no plan. The first target is the first ceiling, measured move
or projection of the last advance (the trend-based Fibonacci tool, `projections`) at least 1R away and reachable in
40 sessions (in_reach), a ceiling's set just under the shelf (0.1 ATR); a strong ceiling before it blocks the plan.
The horizon is the typical time to the target when the target comes first: H = (a^2 + 2ab) / (3 sigma^2) in log
terms (a to the target, b to the out, sigma the daily volatility), the expected first-passage time of a driftless
walk conditioned on reaching the target before the stop; the time stop is twice that, at most 40 sessions. Prices stay internal; the page shows every line in %
from the last close (Lo & MacKinlay, Osler 2000, Bulkowski; docs/research/2026-10-18-terminal/SETUPS_V2.md)."""
import math
from dataclasses import dataclass, field

from .structure import ceilings, floors, strong

CAP_ATR = 0.15                  # "now": buy up to 0.15 ATR over the last close, never higher
NOW_BAND = 0.35                 # "now" when the close sits within 0.35 ATR over the floor's top
PULLBACK_ATR = 3.0              # floors no deeper than 3 ATR under the close
TRIGGER_ATR = 2.5               # breakout triggers no more than 2.5 ATR over the close
REACH_ATR = 4.0                 # a turn's line, and the always-available plan's, no more than 4 ATR over the close:
                                # about what a name travels in a plan's 10 to 15-session window
MIN_RISK_ATR, MAX_RISK_ATR = 1.0, 3.0
MIN_R = 1.0
ZONE_MIN_ATR, ZONE_MAX_ATR = 0.3, 1.0
H_MIN, H_MAX = 5, 40
WINDOW = {"now": 5, "pullback": 10, "breakout": 10, "turn": 15}
_KIND = {"base": "base", "flag": "flag", "double": "double bottom", "triangle": "triangle"}


@dataclass
class Plan:
    form: str
    zone_lo: float
    zone_hi: float                   # the cap
    out: float
    t1: float
    t2: float = None
    trigger: float = None            # breakout / turn: the daily close that opens the buy
    sessions: int = 10               # if it works, the typical sessions to the first target
    window: int = 5                  # how long the buy stays open
    why_zone: list = field(default_factory=list)
    why_out: str = ""
    why_t1: list = field(default_factory=list)
    why_t2: list = field(default_factory=list)
    source: str = ""                 # "levels", "pattern:<kind>", "swing", "fallback", "wave2"
    p_fill: float = 1.0              # the odds price reaches the zone within the window (pullbacks)
    mode: str = "level"              # "reaction": the buy is a daily close up inside the zone, not the touch
    trim: float = None               # the share sold at the first target, the rest held for the second (wave plans)

    @property
    def risk(self):
        return self.zone_hi - self.out

    @property
    def r(self):
        return (self.t1 - self.zone_hi) / self.risk if self.risk > 0 else 0.0

    @property
    def r2(self):
        return (self.t2 - self.zone_hi) / self.risk if self.t2 and self.risk > 0 else None

    @property
    def breakeven(self):
        """the share of the time the plan must work to break even at the first target"""
        return 1.0 / (1.0 + self.r) if self.r > 0 else 1.0

    @property
    def time_stop(self):
        return min(2 * self.sessions, H_MAX)


def _phi(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def p_reach(x, price, sessions):
    """the odds a driftless walk with the name's daily volatility touches `price` within `sessions` (reflection)"""
    if price >= x.close:
        return 1.0
    d = math.log(x.close / price)
    s = (x.sigma / x.close) * math.sqrt(max(1, sessions))
    return 2.0 * (1.0 - _phi(d / s)) if s > 0 else 0.0


def raw_horizon(x, cap, t1, out):
    """the typical sessions to the first target when the target comes first, unclamped"""
    if out <= 0 or t1 <= cap:
        return float(H_MAX)
    a, b = math.log(t1 / cap), math.log(cap / out)
    s = x.sigma / x.close
    return (a * a + 2 * a * b) / (3 * s * s) if s > 0 else float("inf")


def horizon(x, cap, t1, out):
    """the typical sessions to the first target when the target comes first, clamped to [5, 40]"""
    h = raw_horizon(x, cap, t1, out)
    return max(H_MIN, min(H_MAX, round(h))) if math.isfinite(h) else H_MAX


def in_reach(x, cap, t1, out):
    """the first target is in reach of the hold: its typical time, unclamped, is H_MAX sessions or less. One rule for
    every builder (levels, patterns, turns, waves), so no plan publishes a clamped horizon (the audit's D-C2)"""
    return raw_horizon(x, cap, t1, out) <= H_MAX + 0.5


def noise(x, sessions):
    """the least risk the noise of `sessions` allows: an ATR, and half the name's typical swing over them"""
    return max(MIN_RISK_ATR * x.atr, 0.5 * x.sigma * math.sqrt(sessions))


ODDS_MIN = 1 / math.sqrt(13)     # the driftless odds the first target trades before the out: at least 28%, a reward
                                 # of at most 2.6 times the risk in log terms. It is what "risk outside the hold's
                                 # noise" computed: the noise over the plan's own horizon grows with the risk, and the
                                 # volatility cancels (the audit's D-H1); a tight stop under a far target fails it


def first_odds(cap, t1, out):
    """the driftless odds the first target trades before the out: b / (a + b), a and b the log distances from the
    buy's cap to the target and to the out"""
    a, b = math.log(t1 / cap), math.log(cap / out)
    return b / (a + b) if a + b > 0 else 0.0


def pays_its_risk(x, cap, t1, out):
    """an honest stop for this target: at least an ATR of risk, and the target first often enough (ODDS_MIN)"""
    return cap - out >= MIN_RISK_ATR * x.atr and first_odds(cap, t1, out) >= ODDS_MIN


def _lines_below(x, below):
    """structural lines under `below`, highest first, each with its words: the low edge of every area of weight 1 or
    more, and every confirmed swing low"""
    out = {}
    for a in x.areas:
        named = [m for m in a.members if m.family != "round"]
        if named and a.lo < below and (a.anchored or a.weight >= 1.0):
            lo = min(m.price for m in named)
            out.setdefault(lo, min(named, key=lambda m: m.price).label)
    for pv in x.minor + x.major:
        if pv.kind == "L" and pv.confirmed and pv.price < below:
            out.setdefault(pv.price, f"the {x.when(pv.i)} low")
    return sorted(out.items(), key=lambda kv: -kv[0])


def _targets(x, cap, risk, extra=()):
    """[(price, words)] nearest first. The first real ceiling over the close is the furthest a first target may sit:
    set 0.1 ATR under it (the plan sells before the crowd), and when that is less than 1R from the cap the plan does not
    pay and returns [] (a buy into a ceiling included). Nearer, a lighter area (weight 1 or more) or a measured move at
    1R or more is the first target; so is a projection of the last advance (projections). Every target sits at least a
    quarter ATR over the last close, and over the read's own session's high: a target that session reached already
    traded the day the plan was made, so the next one is the target (batch bs1, item 4). With no ceiling and nothing
    real at 1R (a degenerate chart), one and a half times the risk"""
    atr = x.atr
    traded = float(x.bars[-1]["h"])                      # the read's own session's high
    need = max(cap + MIN_R * risk, x.close + 0.25 * atr)
    cs = [a for a in ceilings(x) if a.hi > cap]            # the ceiling a breakout clears is behind it, not ahead
    pts = [(a.lo - 0.1 * atr, a.labels(3)) for a in x.areas if a.weight >= 1.0 and not strong(a)]
    pts += [(p, [lab]) for p, lab in extra]
    if cs:
        c1 = cs[0]
        top = c1.lo - 0.1 * atr
        if top < need or top <= traded:
            return []                                    # a real ceiling stands before 1R (or traded): no plan
        pts = [t for t in pts if t[0] < top] + [(top, c1.labels(3))]
        later = [(a.lo - 0.1 * atr, a.labels(3)) for a in cs[1:]] + [(p, [lab]) for p, lab in extra if p > top]
        pts += later
    pts = sorted((t for t in pts if t[0] >= need and t[0] > traded), key=lambda t: t[0])
    if not pts:
        t = need + 0.5 * risk
        return [(t, ["one and a half times the risk, with no ceiling in the way"])] if t > traded else []
    return pts


def _finish(x, form, lo, hi, floor_line, floor_words, trigger, why_zone, source, extra=(), p_fill=1.0):
    """the out line, the targets and the horizon for a buy zone; None when no honest stop or no target pays"""
    atr, c = x.atr, x.close
    buf = max(0.25 * atr, 0.003 * c)
    lines = ([(floor_line, floor_words)] if floor_line is not None and floor_line < lo else []) + \
        [(p, w) for p, w in _lines_below(x, lo) if floor_line is None or p < floor_line]
    extra = list(extra) + projections(x, lo)
    for line, words in lines:
        out = line - buf
        risk = hi - out
        if risk > MAX_RISK_ATR * atr or out <= 0:
            return None
        ts = _targets(x, hi, risk, extra)
        if not ts:
            return None
        t1, w1 = ts[0]
        n = horizon(x, hi, t1, out)
        if not pays_its_risk(x, hi, t1, out):
            continue                                     # too tight for its target: the next line down
        later = [(p, w) for p, w in ts[1:] if p >= t1 + max(0.5 * risk, atr)]
        t2, w2 = later[0] if later else (None, [])
        if not in_reach(x, hi, t1, out):
            return None                                  # out of reach within 40 sessions
        return Plan(form, lo, hi, out, t1, t2, trigger, n, WINDOW[form], why_zone, words, w1, w2, source, p_fill)
    return None


def _zone(a, atr):
    lo, hi = a.lo - 0.15 * atr, a.hi + 0.15 * atr
    if hi - lo < ZONE_MIN_ATR * atr:
        mid = (hi + lo) / 2
        lo, hi = mid - ZONE_MIN_ATR * atr / 2, mid + ZONE_MIN_ATR * atr / 2
    if hi - lo > ZONE_MAX_ATR * atr:
        lo = hi - ZONE_MAX_ATR * atr                     # keep the top (the first fill); trim the bottom
    return lo, hi


MIN_ADV = 5                            # an advance of fewer sessions (a gap day) is too short to measure from
PULL_EXT = (1.272, 1.618)              # a pullback's extensions: where a move through its high first runs
ADV_EXT = (1.0, 1.272, 1.618, 2.0, 2.618)  # the advance repeated from the pullback low, and its extensions (1.618 is a
                                           # wave 3's usual reach, 2.0-2.618 an extending one: Echo Analysis)


def projections(x, base=None):
    """[(price, words)]: the levels a move up projects to, the trend-based Fibonacci tool on the last advance. A is
    the advance's start, B its top (the last confirmed swing high), C the pullback's low after it, a higher low than A:
    C + 1.272 and 1.618 x (B - C), and C + 1, 1.272, 1.618, 2 and 2.618 x (B - A). A buy under C (base) measures the
    advance from the buy, and the pullback, not over, projects nothing. The major swings first, else the minor ones. A
    pullback through A broke the advance, and an advance under MIN_ADV sessions (a gap day) is too short: neither
    projects anything"""
    for pv in (x.major, x.minor):
        js = [j for j, q in enumerate(pv) if q.kind == "H" and q.confirmed and 0 < j < len(pv) - 1]
        if not js:
            continue
        a, b, c = pv[js[-1] - 1], pv[js[-1]], pv[js[-1] + 1]
        if a.kind != "L" or c.kind != "L" or not a.price < c.price < b.price or b.i - a.i < MIN_ADV:
            continue
        from_buy = base is not None and base < c.price
        lo = base if from_buy else c.price
        leg, adv = b.price - a.price, f"the {x.when(a.i)}–{x.when(b.i)} advance"
        out = [] if from_buy else [(c.price + k * (b.price - c.price),
                                    f"the {k} extension of the {x.when(b.i)}–{x.when(c.i)} pullback") for k in PULL_EXT]
        for k in ADV_EXT:
            out.append((lo + k * leg, (f"{adv} repeated from " + ("the buy" if from_buy else f"the {x.when(c.i)} low"))
                        if k == 1.0 else f"the {k} extension of {adv}"))
        return out
    return []


def _at_floor(x):
    """now / pullback plans on the three nearest strong floors at or under the close"""
    out = []
    atr, c = x.atr, x.close
    for a in floors(x, PULLBACK_ATR)[:3]:
        if a.lo - 0.2 * atr <= c <= a.hi + NOW_BAND * atr:
            form, hi = "now", c + CAP_ATR * atr
            lo = max(min(a.lo - 0.15 * atr, hi - ZONE_MIN_ATR * atr), hi - ZONE_MAX_ATR * atr)
            pf = 1.0
        else:
            form = "pullback"
            lo, hi = _zone(a, atr)
            hi = min(hi, c - 0.1 * atr)
            pf = p_reach(x, hi, WINDOW["pullback"])
        named = [m for m in a.members if m.family != "round"] or a.members
        lowest = min(m.price for m in named)
        low_words = min(named, key=lambda m: m.price).label
        p = _finish(x, form, lo, hi, lowest if lowest < lo else None, low_words, None, a.labels(3), "levels", (),
                    pf)
        if p:
            out.append(p)
    return out


def _breakouts(x, pattern_facts):
    """breakout plans over each bullish pattern's trigger and over the nearest strong ceiling"""
    out = []
    atr, c = x.atr, x.close
    for f in pattern_facts:
        d = f.data or {}
        trig, floor, tgt = d.get("trigger"), d.get("floor"), d.get("target")
        if f.side <= 0 or trig is None or floor is None:
            continue
        name = d.get("line") or (f.head[0].lower() + f.head[1:])
        if c > trig:                                     # already through: buy now above the trigger, up to the cap
            if (c - trig) / atr > 1.0:
                continue                                 # ran past it: a pullback plan instead
            lo, hi, form, trigger = trig, c + CAP_ATR * atr, "now", None
        else:
            if (trig - c) / atr > TRIGGER_ATR:
                continue
            lo, hi, form, trigger = trig + 0.1 * atr, trig + 0.5 * atr, "breakout", trig + 0.1 * atr
        extra = [(tgt, f"the measured move of the {_KIND.get(d.get('kind'), 'pattern')}")] if tgt else []
        line = trig if floor < trig - 1.0 * atr else floor
        p = _finish(x, form, lo, hi, line, name if line == trig else "the pattern's floor", trigger, [name],
                    "pattern:" + str(d.get("kind")), extra)
        if p:
            out.append(p)
    cs = [a for a in ceilings(x) if (a.hi - c) / atr <= TRIGGER_ATR]
    if cs:
        a = cs[0]
        trig = a.hi + 0.1 * atr
        p = _finish(x, "breakout", trig, trig + 0.5 * atr, a.lo, a.labels(1)[0], trig, a.labels(3), "levels")
        if p:
            out.append(p)
    return out


def _turn(x):
    """the falling chart's long: the first sign of a turn, a daily close back over the 20-day average, the last swing
    high or the 50-day average (the three nearest at least 0.3 ATR over the close, within 4 ATR); the out sits under
    the line it reclaimed (a failed reclaim is the plan proven wrong) or the structure below it"""
    atr, c = x.atr, x.close
    lines = []
    if x.sma20[-1] and x.sma20[-1] > c + 0.3 * atr:
        lines.append((x.sma20[-1], "the 20-day average"))
    hs = [pv for pv in x.minor if pv.kind == "H" and pv.confirmed and pv.price > c + 0.3 * atr]
    if hs:
        lines.append((hs[-1].price, f"the {x.when(hs[-1].i)} high"))
    if x.sma50[-1] and x.sma50[-1] > c + 0.3 * atr:
        lines.append((x.sma50[-1], "the 50-day average"))
    out = []
    for line, label in sorted(lines)[:3]:
        if (line - c) / atr > REACH_ATR:
            continue
        trig = line + 0.1 * atr
        p = _finish(x, "turn", trig, trig + 0.35 * atr, line - 0.75 * atr, label, trig, [label], "swing")
        if p:
            out.append(p)
    return out


def ladder(x, form, reach=REACH_ATR):
    """the always-available long: a daily close over the lowest line above the close (a swing high, the 20, 50 or
    200-day average, the top of a real ceiling) from which the plan pays: an honest stop under the line, a first target
    at 1R or more that no real ceiling blocks. None when nothing within `reach` ATR pays: a trigger further away than
    a name travels in the plan's window is no plan to act on (MU on 2026-10-16 got a close above +27%, out at +21%,
    with reach 12)"""
    atr, c = x.atr, x.close
    lines = [(pv.price, f"the {x.when(pv.i)} high") for pv in x.minor if pv.kind == "H" and pv.confirmed and pv.price > c]
    for m, lab in ((x.sma20[-1], "the 20-day average"), (x.sma50[-1], "the 50-day average"),
                   (x.sma200[-1], "the 200-day average")):
        if m and m > c:
            lines.append((m, lab))
    lines += [(a.hi, a.labels(1)[0]) for a in ceilings(x)]
    for line, label in sorted(set(lines)):
        if (line - c) / atr > reach:
            break
        trig = line + 0.1 * atr
        p = _finish(x, form, trig, trig + 0.35 * atr, line - 0.75 * atr, label, trig, [label], "ladder")
        if p and p.r >= MIN_R:
            return p
    return None


def candidates(x, pattern_facts=()):
    """every valid long plan for the name (R at least MIN_R, risk 1 to 3 ATR, a target in reach)"""
    if not x.atr or not x.sigma:
        return []
    plans = _at_floor(x) + _breakouts(x, pattern_facts) + _turn(x)
    return [p for p in plans if p.r >= MIN_R and p.out < p.zone_lo < p.zone_hi < p.t1]
