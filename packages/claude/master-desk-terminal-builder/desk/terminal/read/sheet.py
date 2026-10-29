"""The owner's list, line by line (docs/research/2026-10-19-every-factor/SCOPE.md): every read considers every line,
and the card highlights the lines most material to that setup.

A line is answered three ways. Found: the read's own readings for it (the facts whose keys the line names, or the
plan for the plan's lines). Checked, none: the read measures it and nothing is there ("No divergence on the daily or
weekly swings"). Not measured: the read has no measurement for it yet; the registry says so for every read alike, and
a line measured only in part says which part is still missing. Nothing on the list is silently left out: the test
(tests/test_terminal_sheet.py) holds the owner's list verbatim and fails on any line without an answer.

What is material (`material`): at most five lines, in this order, each rule from the desk's study or its record:
  1. risk to the plan itself: earnings inside the hold (a report can gap a trade through its out: in the replay such
     trades did no worse on average, but their losses ran to -1.7R against about -1.1R: genius lab 3, Nightingale),
     a name too thin for the board's bar;
  2. the market's state: the fund it follows under its 200-day average. Stated as a fact only: the replay found that
     a falling market made no difference to the read's own calls;
  3. the study's warnings: a buy signal inside a downtrend on every average (a broken stock flashing a bullish signal
     lagged the market in both eras: PATTERNS 2n), a bullish divergence at the year's low (it trailed: PATTERNS 2p);
  4. then the read's strongest readings, for and against, by their vote (structure first).
A fact material states is stated there only (compose: standouts and against leave it out); the desk holding the name
is the card's held chip and a fear day the card's fear-day block, so neither is repeated here (the language diet,
read/diet.py).

Each reading answers one line (`distinct`): a reading two lines share is the first line's (the value area the volume
line's), the later line keeping it only when it has nothing else; the levels' count of kinds is the stack line's and
MACD's cross the cross line's; the plan's lines give its numbers (the levels are the plan's own words)."""
import re
from dataclasses import dataclass

from . import words as W
from .core import CLASS_WEIGHT

GROUPS = ("Chart patterns", "Price structure", "Measured levels and targets", "Trend and averages", "Momentum",
          "Volume", "Divergences", "Stretch and volatility", "Candles and gaps", "Chart reading", "Tensor",
          "Timing and the plan", "Options and positioning", "The desk's own book", "Liquidity", "Company and market")
NOT_YET = "Not measured yet."
MAX_MATERIAL = 5


@dataclass(frozen=True)
class Line:
    n: int                     # the owner's order
    id: str                    # stable id
    group: str                 # the owner's heading
    label: str                 # the owner's words, verbatim
    keys: tuple = ()           # fact keys (or key prefixes ending in ".") that answer the line
    none: str = ""             # the answer when the read measured it and nothing is there
    missing: str = ""          # set when the read does not measure the line at all yet
    pending: str = ""          # set when the read measures only part of it: the part still missing
    mark: str = ""             # the owner's mark: "new" or "addition"
    plan: str = ""             # a line the plan answers: "target", "zone", "wrong"
    test: str = ""             # a narrower test on the matching facts: "cross" (MACD's cross), "vwap" (an anchored
                               # VWAP among the levels), "profile" (the volume profile among the levels)


P, S, M, T, MO, V, D, ST, C, R, TE, TP, O, B, L, CM = GROUPS
LINES = (
    Line(1, "pattern.hs", P, "Head and shoulders, and inverse head and shoulders", ("pattern.hs",),
         "No head and shoulders on the chart."),
    Line(2, "pattern.double", P, "Double top, double bottom, and triple top", ("pattern.double", "pattern.triple"),
         "No double or triple top or bottom on the chart."),
    Line(3, "pattern.triangle", P, "Ascending, descending, and symmetrical triangles",
         ("pattern.triangle", "pattern.symmetrical"), "No triangle on the chart."),
    Line(4, "pattern.wedge", P, "Rising, falling, and expanding wedges", ("pattern.wedge", "pattern.broadening"),
         "No wedge or broadening formation on the chart."),
    Line(5, "pattern.flag", P, "Bull and bear flags and pennants", ("pattern.flag", "pattern.pennant"),
         "No flag or pennant on the chart."),
    Line(6, "pattern.cup", P, "Cup and handle, and inverted cup and handle", ("pattern.cup",),
         "No cup on the chart."),
    Line(7, "pattern.rectangle", P, "Rectangles", ("pattern.rectangle", "pattern.base"),
         "No rectangle, base or trading range on the chart."),
    Line(8, "pattern.channel", P, "Rising and falling channels", ("pattern.channel",),
         "No channel on the chart."),
    Line(9, "pattern.break", P, "Breakouts and breakdowns, with breakout quality: closes held above the line, and "
         "whether the break was a stretched spike", ("pattern.breakout", "pattern.breakdown", "pattern.failed"),
         "No breakout or breakdown in the last few sessions."),
    Line(10, "structure.swings", S, "Swing highs and lows, each dated to the day it was confirmed", ("trend.swings",),
         "No confirmed swings yet."),
    Line(11, "structure.trendlines", S, "Support and resistance trendlines",
         ("levels.support_line", "levels.resistance_line"), "No trendline with three touches near the price."),
    Line(12, "structure.zones", S, "Support and resistance zones from swings, the volume profile, and round numbers",
         ("levels.floor", "levels.ceiling", "levels.on", "levels.value_area"), "No support or resistance within reach."),
    Line(13, "structure.stack", S, "How many separate levels stack up at the same price",
         ("levels.on", "levels.floor", "levels.ceiling"), "No levels stacked near the price.", mark="new"),
    Line(14, "structure.retests", S, "Retests and reclaims of the 20-day and 50-day, and retests of a level after a "
         "breakout", ("levels.bounce20", "levels.bounce50", "levels.reclaim20", "levels.reclaim50", "levels.retest"),
         "No retest or reclaim in the last few sessions.", mark="new"),
    Line(15, "structure.state", S, "Whether the structure is intact or broken, and any warnings",
         ("trend.structure", "trend.swings", "pattern.failed", "levels.failed"), "No break in the structure."),
    Line(16, "levels.fib_year", M, "Fibonacci retracement of the one-year swing: how much it has given back, which "
         "band it's in, and whether the 200-day sits there", ("levels.fib_year",), "No one-year swing to measure."),
    Line(17, "levels.targets", M, "Targets from a pattern's measured move, the swing measured move (AB=CD), and the "
         "1.272 and 1.618 extensions", none="No plan, so no target.", plan="target"),
    Line(18, "levels.range52", M, "52-week high and low", ("trend.high52", "trend.low52", "trend.range52"),
         "Under a year of history."),
    Line(19, "trend.averages", T, "10, 20, 50, and 200-day averages, and where price sits against each",
         ("trend.averages", "trend.stack"), "Too little history for the averages."),
    Line(20, "trend.stages", T, "Weinstein stage and ChartsLector stage", ("trend.stage", "trend.cl"),
         "Too little weekly history for a stage."),
    Line(21, "trend.elliott", T, "Elliott wave count and its invalidation level", ("wave.",),
         "No wave count on this chart."),
    Line(22, "trend.htf", T, "The higher-timeframe map: monthly and weekly trend, and where the daily setup sits "
         "inside it", ("trend.htf", "trend.stage", "wave.w."), "No weekly reading.", mark="addition"),
    Line(23, "mom.rsi", MO, "RSI", ("mom.rsi", "mom.rsi_range"), "Too little history for RSI."),
    Line(24, "mom.macd", MO, "MACD line, signal, and histogram", ("mom.macd",), "Too little history for MACD."),
    Line(25, "mom.macd_cross", MO, "MACD crossovers as events", ("mom.macd",),
         "No MACD cross in the last two sessions.", mark="new", test="cross"),
    Line(26, "mom.stoch", MO, "Slow stochastic", ("mom.stoch",), "Too little history for the stochastic."),
    Line(27, "mom.rank6", MO, "6-month momentum, and how it ranks against other stocks", ("trend.mom6",),
         "Under seven months of history."),
    Line(28, "trend.rs", MO, "Relative strength against the S&P 500 and the stock's sector",
         ("trend.vs_spy", "trend.vs_sector", "trend.rs"), "Its fund's history is too short.", mark="new"),
    Line(29, "trend.adx", MO, "ADX / DMI — trend strength", ("trend.adx",), "Too little history for ADX.",
         mark="addition"),
    Line(30, "vol.relative", V, "Relative volume and breakout volume", ("vol.last", "vol.leg"),
         "Too little volume history."),
    Line(31, "vol.flow", V, "On-balance volume, the accumulation/distribution line, and money flow index",
         ("vol.mfi", "vol.cmf", "vol.obv", "vol.accdist", "vol.updown"), "No volume-flow reading."),
    Line(32, "vol.vwap", V, "20-day VWAP, plus the value area: its high, its low, and the price where the most volume "
         "traded", ("levels.vwap20", "levels.value_area"), "Too little volume history."),
    Line(33, "vol.avwap", V, "Anchored VWAP from the last earnings date and the major swing anchor",
         ("levels.vwap_earnings",), "No earnings report on record to anchor it.", mark="addition",
         pending="The VWAP anchored at the major swing is not read yet."),
    Line(34, "div.gauges", D, "7 gauges checked on daily and weekly swings, grouped into momentum and volume",
         ("div.",), "No divergence on the daily or weekly swings."),
    Line(35, "vola.atr", ST, "ATR (average daily range)", ("vola.atr",), "Too little history for ATR."),
    Line(36, "vola.stretch", ST, "How far price is from its average in ATRs, ranked against the stock's own year",
         ("vola.stretch",), "Too little history to rank the stretch."),
    Line(37, "vola.squeeze", ST, "Bollinger band width percentile and squeeze state", ("vola.squeeze", "vola.nr7"),
         "Too little history for the bands.", mark="addition"),
    Line(38, "candle.detectors", C, "50 candlestick detectors and gap ups and downs, counted only when they land on a "
         "key level", ("candle.",), "No candle signal at a key level."),
    Line(39, "gap.taxonomy", C, "Gap taxonomy — breakaway, runaway, exhaustion, common — and unfilled gaps carried as "
         "levels", ("gap.",), "No gap in the last few sessions.", mark="addition"),
    Line(40, "wyckoff", R, "Wyckoff phase and events: accumulation/distribution phase, springs, upthrusts, effort vs. "
         "result", ("wyckoff.",), "No Wyckoff event on the chart.", mark="addition"),
    Line(41, "tensor.states", TE, "Slow and fast states, markers, votes, and trend strength on weekly, daily, and "
         "hourly bars", missing=NOT_YET),
    Line(42, "tensor.agree", TE, "Whether those timeframes agree", missing=NOT_YET),
    Line(43, "timing.fear", TP, "Fear-day rule: buy on a red QQQ day between 3:20 and 3:50 PM ET", ("ctx.fear",),
         "Not a fear day: the name and its fund did not both close red."),
    Line(44, "plan.zone", TP, "Buy zone, buy cap, and buy window, and how far price is from the cap",
         none="Stands aside: no buy zone.", plan="zone"),
    Line(45, "plan.wrong", TP, "Where the setup is wrong, the good case, and the bad case",
         none="Stands aside: no call to be wrong about.", plan="wrong"),
    Line(46, "desk.sleeve", TP, "Which sleeve holds it, and that sleeve's own exits and stops", ("desk.holds",),
         "No sleeve holds it.", pending="Which sleeve, and its exits and stops, are not named yet."),
    # 47-50 and 58's news: the session's gather from Alpaca for the board's names and SPY, QQQ, IWM (read/optnews.py)
    Line(47, "options.iv", O, "Options implied volatility and positioning on the name", ("options.iv",),
         "No option chain read for it this session."),
    Line(48, "options.ivrank", O, "IV rank, and realized vs. implied volatility", ("options.ivrv",),
         "Too little history for realized volatility.", mark="addition",
         pending="IV rank needs a year of stored IV30 readings: 252 sessions, about October 2027."),
    Line(49, "options.gex", O, "Per-name dealer gamma exposure", ("options.gex",),
         "No dealer gamma read for it this session.", mark="addition"),
    Line(50, "options.market", O, "The market's put/call ratio and dealer gamma", ("options.market",),
         "No market options read this session."),
    Line(51, "short.data", O, "Short interest, days to cover, short volume, and fails to deliver", missing=NOT_YET),
    Line(52, "insiders", O, "Insider buys", missing=NOT_YET),
    Line(53, "book.exposure", B, "Existing exposure in the name and its sector", ("desk.holds",),
         "The desk holds no position in it.", mark="addition",
         pending="The sector's exposure is not read yet."),
    Line(54, "book.sleeves", B, "Which sleeves already hold it", missing=NOT_YET, mark="addition"),
    Line(55, "book.history", B, "The desk's prior trade history in the name", missing=NOT_YET, mark="addition"),
    Line(56, "liquidity", L, "Market cap, float, average dollar volume, and typical spread",
         ("ctx.liquidity", "ctx.spread"), "Too little volume history.", mark="addition",
         pending="Market cap and float are not read yet."),
    Line(57, "peers", CM, "How peers in the same industry did over the last 21 days", missing=NOT_YET),
    Line(58, "company", CM, "SEC 8-K filings, quarterly fundamentals, news counts, earnings dates, and past earnings "
         "reactions", ("ctx.earnings", "news.count"), "No earnings date or news count on record.",
         pending="Filings, fundamentals and past reactions are not read yet."),
    Line(59, "events", CM, "The per-name event calendar beyond earnings: splits, dividends, index changes, lockup "
         "expiries", ("ctx.listing",), "No listing in the last year, so no lockup to expire.", mark="addition",
         pending="Splits, dividends and index changes are not read yet."),
    Line(60, "analysts", CM, "Analyst revisions as catalyst context — never as plan levels", missing=NOT_YET,
         mark="addition"),
    Line(61, "market", CM, "Market regime, VIX, breadth, rates, credit, and the dollar", ("ctx.market", "ctx.fund"),
         "No market reading.", pending="Rates, credit and the dollar are not read yet."),
    Line(62, "calendar", CM, "The economic calendar and geopolitical news", missing=NOT_YET),
    Line(63, "attention", CM, "Wikipedia and Reddit attention, and seasonality", missing=NOT_YET),
)
BY_ID = {ln.id: ln for ln in LINES}


def _hits(ln, fs):
    """the facts that answer a line, strongest vote first"""
    out = []
    for f in fs:
        if any(f.key == k or (k.endswith(".") and f.key.startswith(k)) for k in ln.keys):
            if ln.test == "cross" and "cross" not in f.text.lower():
                continue
            if ln.test == "vwap" and "average price paid" not in f.text:
                continue
            if ln.test == "profile" and "most-traded" not in f.text and "average price paid" not in f.text:
                continue
            out.append(f)
    return sorted(out, key=lambda f: -abs(f.vote))


def _reading(f):
    return (f.reading or f.head or "").strip().replace("; ", ", ")     # "; " joins a line's readings


def _plan_line(ln, plan):
    """the plan's own lines in its numbers (its levels' names are the plan's why_zone, why_out and why_t1); a read
    that stands aside has none"""
    if not plan or plan.get("out") is None:
        return None
    if ln.plan == "target":
        t = _pct(plan.get("t1"))
        return t + (f", then {_pct(plan['t2'])}" if plan.get("trim") and plan.get("t2") is not None else "")
    if ln.plan == "zone":
        z = (f"Over {_pct(plan['trigger'])}, up to {_pct(plan.get('zone_hi'))}" if plan.get("trigger") is not None
             else f"{_pct(plan.get('zone_lo'))} to {_pct(plan.get('zone_hi'))}")
        return z + (f", through {W.short_day(plan['window'])}" if plan.get("window") else "")
    if ln.plan == "wrong":
        return f"Wrong below {_pct(plan['out'])}, the bad case; the good case {_pct(plan.get('t1'))}"
    return None


def _pct(v):
    if v is None:
        return "?"
    s = f"{abs(v):.1f}".rstrip("0").rstrip(".") if abs(v) < 10 else f"{abs(v):.0f}"
    return "0%" if s == "0" else ("+" if v > 0 else "−") + s + "%"


MAX_PARTS = 2                       # readings per line
HOME = {"Value area: ": "vol.vwap"}  # a reading two lines share, at home in this line rather than the first
_ON = re.compile(r"^Levels: on (support|resistance) \((\d+) kinds? stacked\)$")
_NEAR = re.compile(r"^Nearest (support|resistance): (\S+) \((\d+) kinds?\)$")
_CROSS = re.compile(r"^MACD: crossed (above|below) its signal (.+), (above|below) zero$")


def _kinds(k):
    return f"{k} kind{'' if k == '1' else 's'}"


LEGACY = (                          # a reading's words before the language diet -> today's (a listed read keeps its own)
    (re.compile(r"^Swings: a (higher|lower) high and a (higher|lower) low$"), r"Swings: \1 high, \2 low"),
    (re.compile(r"^(Weekly stage: \w+) \((?:above a rising|below a falling|a flat) 30-week average\)$"), r"\1"),
    (re.compile(r"^Averages: price above the rising 50-day and 200-day$"), "Averages: above both, both rising"),
    (re.compile(r"^Averages: price below the falling 50-day and 200-day$"), "Averages: below both, both falling"),
    (re.compile(r"^Averages: under the 50-day, above the rising 200-day$"), "Averages: under the 50-day, over a rising "
                                                                           "200-day"),
    (re.compile(r"^Averages: bouncing under the falling 200-day$"), "Averages: bouncing, under a falling 200-day"),
    (re.compile(r"^Pattern: (failed )?(breakout|breakdown) from an? "), r"Pattern: \1\2, "),
    (re.compile(r"^(Candles? [^:]+: .+?) at (a (?:support|resistance) area)$"), r"\1 (\2)"),
    (re.compile(r"^MACD: (above|below) its signal line and (above|below) zero$"), r"MACD: \2 zero, \1 its signal"),
    (re.compile(r"^((?:Weekly )?Elliott wave: wave [24]) turned up from the zone"), r"\1 up from the zone"),
    (re.compile(r"^((?:Weekly )?Elliott wave): five waves up look complete$"), r"\1: a finished five"),
    (re.compile(r"^(Relative strength vs \S+: .+), at (a 52-week (?:high|low))$"), r"\1, \2"),
    (re.compile(r"; the larger swings (?:are )?(intact|broken|sideways|show a lower high|have no higher low)$"),
     lambda m: ", larger swings: " + {"show a lower high": "a lower high", "have no higher low": "no higher low"}.get(
         m.group(1), m.group(1))),
    (re.compile(r"^Desk book: holds a position$"), "Held"),
)


def _shown(line_id, r):
    """a reading as one line shows it: the levels' count of kinds on the stack line alone, MACD's cross on the cross
    line and its state on the MACD line, the desk's book as the one word the held chip says"""
    for pat, rep in LEGACY:
        r = pat.sub(rep, r)
    m, n, c = _ON.match(r), _NEAR.match(r), _CROSS.match(r)
    if line_id == "structure.stack":
        return f"{_kinds(m.group(2))} at the price" if m else f"{_kinds(n.group(3))} at {n.group(2)}" if n else r
    if m:
        return f"Levels: on {m.group(1)}"
    if n:
        return f"Nearest {n.group(1)}: {n.group(2)}"
    if c and line_id == "mom.macd_cross":
        return f"Crossed {'up' if c.group(1) == 'above' else 'down'} {c.group(2)}"
    if c:
        return f"MACD: {c.group(3)} zero, {c.group(1)} its signal"
    return r


_PAREN = re.compile(r" \([^()]*\)$")


def _label(r):
    return r.split(": ", 1)[0] if ": " in r else None


def _value(r):
    return r.split(": ", 1)[1] if ": " in r else r


def _items(r):
    return _value(r).split(", ")


def _frame(label):
    """a reading's name without its timeframe: "Weekly Elliott wave" and "Elliott wave" are one name"""
    return (label or "").replace("Weekly ", "").replace(", daily and weekly", "").lower()


def _merge(parts):
    """the readings of one name said once: "Relative strength vs SPY: +7% in 3 months, a 52-week high" joins the
    one that gives 1, 3 and 6 months (its own items only), and a daily and a weekly reading that say the same thing
    are one reading of both"""
    out = []
    for r in parts:
        lab = _label(r)
        for i, o in enumerate(out):
            lo = _label(o)
            if not lab or not lo:
                continue
            if lab == lo and "(" not in r and "(" not in o:
                base, extra = (o, r) if len(o) >= len(r) else (r, o)
                have = _items(base)
                out[i] = base + "".join(", " + it for it in _items(extra) if it not in have)
                break
            if lab != lo and _frame(lab) == _frame(lo) and _PAREN.sub("", _value(r)) == _PAREN.sub("", _value(o)):
                daily, one = (lab, r) if not lab.startswith("Weekly ") else (lo, o)
                out[i] = f"{daily}, daily and weekly: {_value(one)}"
                break
        else:
            out.append(r)
    return out


def _twin(r, o):
    """a daily and a weekly reading of one name that say the same thing (their counts in brackets aside)"""
    a, b = _label(r), _label(o)
    return bool(a and b and a != b and _frame(a) == _frame(b) and
                _PAREN.sub("", _value(r)) == _PAREN.sub("", _value(o)))


def covered(r, answer):
    """whether a line's answer already says reading r: it holds it, or a reading of the same name holds all of its
    items"""
    for p in str(answer).split("; "):
        if r == p:
            return True
        if _label(r) and _label(p) and _frame(_label(r)) == _frame(_label(p)):
            if _label(r) == _label(p) and all(it in _items(p) for it in _items(r)):
                return True
            if _label(p).endswith(", daily and weekly") and _PAREN.sub("", _value(r)) == _PAREN.sub("", _value(p)):
                return True
    return False


def says(answers, r):
    """whether a line of the sheet says reading r as that line shows it: held, or one reading of a daily and weekly
    pair (covered). The drawing draws a fact the sheet states in any of its forms (geometry.drawn)"""
    return bool(r) and any(covered(_shown(k, r), v) for k, v in (answers or {}).items())


def _parts(line_id, v):
    """a line's readings as it shows them, once each"""
    out = []
    for r in (x.strip() for x in str(v).split("; ")):
        r = _shown(line_id, r)
        if r and r not in out:
            out.append(r)
    return out


FILED = {"Timeframes": "trend.htf", "Structure": "structure.state"}   # a line's own reading, by its name


def refile(answers, considered):
    """(answers, considered) with a line's own reading back on its line: a read published before distinct kept two
    readings a line by their vote, so a line whose own reading lost its place (the map of timeframes behind the
    weekly stage and count it shares) holds it again, and what else the read considered no longer does"""
    out, rest = dict(answers), []
    for c in considered or ():
        lid = FILED.get(_label(c) or "")
        if lid in out and not covered(c, out[lid]):
            out[lid] = f"{out[lid]}; {c}"
        else:
            rest.append(c)
    return out, rest


def _raw(line_id, v):
    """a line's answer in today's words when its old words joined two readings' units (the market's dealer gamma)"""
    if line_id == "options.market" and " dollars per 1% move" in v:
        v = v.replace(" dollars per 1% move", " dollars") + "; dealer gamma per 1% move"
    return v


def distinct(answers, plan=None):
    """the sheet with each reading in one line only: a reading an earlier line already says (covered) is that line's,
    unless HOME names its home, and a later line keeps it only when it has nothing else; at most MAX_PARTS readings
    a line, the readings of one name merged (_merge); the plan's lines in its numbers. Idempotent, and it reads the
    answers alone, so a read published before it is cut the same way"""
    shown = {}
    for ln in LINES:
        if ln.id in answers:
            shown[ln.id] = [_plan_line(ln, plan) or str(answers[ln.id])] if ln.plan else \
                _parts(ln.id, _raw(ln.id, str(answers[ln.id])))
    ids = [lid for lid in shown if not BY_ID[lid].plan]
    for i, a in enumerate(ids):                  # a weekly reading whose daily twin an earlier line says joins it there
        for b in ids[i + 1:]:
            for r in shown[b]:
                if r not in shown[a] and any(_twin(r, o) for o in shown[a]):
                    shown[a].append(r)
    full = {lid: "; ".join(_merge(parts)) for lid, parts in shown.items()}
    out = {}
    for ln in LINES:
        parts = shown.get(ln.id)
        if not parts:
            continue
        if ln.plan:
            out[ln.id] = parts[0]
            continue

        def elsewhere(r):
            pref = next((h for pre, h in HOME.items() if r.startswith(pre)), None)
            if pref and pref != ln.id and pref in full and covered(r, full[pref]):
                return True
            return any(covered(r, v) for v in out.values()) and pref != ln.id

        mine = [r for r in parts if not elsewhere(r)]
        out[ln.id] = "; ".join(_merge(mine or parts)[:MAX_PARTS])
    return out


def found(fs, plan=None):
    """{line id: the read's answer} for every line the read answered, each reading in one line (distinct); a line it
    measures but found nothing for, and a line it does not measure yet, are absent here and answered by the registry
    (none / missing)"""
    out = {}
    for ln in LINES:
        if ln.missing:
            continue
        if ln.plan:
            t = _plan_line(ln, plan)
            if t:
                out[ln.id] = t
            continue
        parts = [r for r in (_reading(f) for f in _hits(ln, fs)) if r]
        if parts:
            out[ln.id] = "; ".join(dict.fromkeys(parts))
    return distinct(out, plan)


def _facts_shown(ln, fs, answered):
    """the facts whose readings a line shows"""
    answer = answered.get(ln.id, "")
    return [f for f in _hits(ln, fs) if covered(_shown(ln.id, _reading(f)), answer)]


def sides(fs, answered):
    """{line id: 1 for the long, -1 against it, 0 neither} for every line the read answered (found): the dominant
    side of the facts the line shows (each fact's side by its strength, a fact that points a way but votes nothing
    counting a hair), the plan's own lines neither"""
    out = {}
    for ln in LINES:
        if ln.id not in answered:
            continue
        score = 0.0 if ln.plan else sum(f.side * max(f.strength, 0.01) for f in _facts_shown(ln, fs, answered)
                                         if f.side)
        out[ln.id] = 1 if score > 0 else -1 if score < 0 else 0
    return out


def on_sheet(fs, answered):
    """the ids of the facts whose readings the sheet shows (compose: considered holds only the others)"""
    return {id(f) for ln in LINES if ln.id in answered and not ln.plan for f in _facts_shown(ln, fs, answered)}


def registry():
    """the list as the page lays it out: every line the read measures, its heading, the owner's words, and the read's
    standing answer when it found nothing (none). A line the read cannot measure yet is left out (the owner's rule: the
    public page carries no pipeline gaps); it appears once a batch measures it. coverage() is the whole list."""
    out = []
    for ln in LINES:
        if ln.missing:
            continue
        r = {"n": ln.n, "id": ln.id, "group": ln.group, "label": ln.label, "none": ln.none}
        if ln.mark:
            r["mark"] = ln.mark
        out.append(r)
    return out


def coverage():
    """every line of the owner's list with its standing: measured, measured in part (pending: the part not yet
    measured) or not measured (missing: why). Internal: the acceptance matrix and the tests read it, the page never."""
    return [{"n": ln.n, "id": ln.id, "group": ln.group, "label": ln.label,
             "state": "missing" if ln.missing else "partial" if ln.pending else "measured",
             "note": ln.missing or ln.pending or ""} for ln in LINES]


def _f(head, text, learn=""):
    return {"head": head, "text": text, "learn": learn}


def _down_everywhere(fs):
    return any(f.key == "trend.stack" and f.side < 0 and f.strength >= 0.6 for f in fs)


THIN = "The board's bar: 20 million a day at 5 dollars or more."


def picks(fs, form, liquid=True, k=MAX_MATERIAL):
    """[(entry, fact)]: the lines that matter most for this setup, at most k, in the module's order of rules; each a
    fact as the page shows one (head, text) and the fact it states, or None for the study's warning about a fact,
    which keeps its own entry. Facts are taken as the read states them; the study's warnings are said as the study
    measured them"""
    out, used = [], set()

    def take(f, head=None, text=None, rank=0.0, states=True):
        if id(f) in used:
            return
        used.add(id(f))
        out.append((rank, _f(head or f.head, f.text if text is None else text), f if states else None))

    by = {}
    for f in fs:
        by.setdefault(f.key, []).append(f)
    buy = form not in (None, "wait")
    # 1. risk to the plan itself
    for f in by.get("ctx.earnings", []):
        if f.side < 0:                                   # compose marks earnings that fall inside the hold
            take(f, rank=100, text="")                   # its head says it: "Earnings Oct 28, inside the hold"
    if not liquid:
        for f in by.get("ctx.liquidity", []):
            take(f, rank=85, head="Thin for the board", text=THIN)
    # 2. the market's state when it changes what a buy means
    if buy:
        for f in by.get("ctx.fund", []):
            if f.side < 0:
                take(f, rank=80)
    # 3. the study's warnings
    bull = [f for f in fs if f.side > 0 and f.cls == "structure" and f.family in ("Pattern", "Levels")]
    if buy and _down_everywhere(fs) and bull:
        f = max(bull, key=lambda f: f.vote)
        take(f, rank=75, head="A buy signal in a broken trend", text="Such signals lagged the market in the desk's "
             "study.", states=False)
    lows = by.get("trend.low52", [])
    for f in fs:
        if f.key.startswith("div.regular_bullish") and f.side > 0 and lows:
            take(f, rank=74, head="A bullish divergence at the year's low",
                 text="Such divergences trailed the market over the next month in the desk's study.", states=False)
            break
    # 4. the strongest readings, structure first: for a buy, the readings for it only (a reading against the long is
    # what argues against it, never a reason to buy: CRGY on 2026-10-26 listed "A lower high and a lower low" here);
    # with no call, the strongest either way
    for f in sorted(fs, key=lambda f: -abs(f.vote)):
        if f.side and (f.side > 0 or not buy) and f.strength > 0 and CLASS_WEIGHT.get(f.cls, 0) > 0:
            take(f, rank=10 * abs(f.vote))
    out.sort(key=lambda p: -p[0])
    return [(e, f) for _, e, f in out[:k]]


def material(fs, form, liquid=True, k=MAX_MATERIAL):
    """the entries of picks(), each fact with its teaching line"""
    return [dict(e, learn=W.learn(f.learn)) if f is not None else e for e, f in picks(fs, form, liquid, k)]


MIN_PRICE, MIN_DOLLAR_VOLUME = 5.0, 20e6             # the board's bar (desk/terminal/reads.py)


def liquid(fs, close):
    """whether the name clears the board's bar, from the read's own liquidity fact (its 20-session median dollar
    volume) and the close; True when the read has no liquidity fact (too little history to say otherwise)"""
    f = next((f for f in fs if f.key == "ctx.liquidity"), None)
    if f is None:
        return True
    return close >= MIN_PRICE and float(f.data.get("dollar_volume") or 0.0) >= MIN_DOLLAR_VOLUME
