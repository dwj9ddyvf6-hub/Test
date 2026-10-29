"""The read's two building blocks. A Fact is one thing the desk measured on a name, already in plain words: which way
it points (side +1 for the long case, -1 for the short case, 0 for neither), how strongly (0..1), how unusual it is
(0..1, the standouts rise by it), its class (structure counts twice, momentum, volume and the desk's own strategies
once, the market and events not at all: they shape the desk's take, never the evidence) and the numbers behind it.
A Ctx holds everything measured once per name (series, swing points, levels), so no family recomputes another's work.
Nothing here holds or prints a price: facts speak in %, ATR, counts and dates."""
import math
from dataclasses import dataclass, field

from . import divergence, levels, pivots, ta

CLASS_WEIGHT = {"structure": 2.0, "momentum": 1.0, "volume": 1.0, "desk": 1.0, "context": 0.0}
MINOR_K, MAJOR_K = 2.0, 4.0           # swing degrees in ATR: the minor swings traders mark, the major legs
BARS_USED = 520                       # two years of sessions: the 200-day average, the 52-week range, 100 weeks
WEEK_AVGS = (50, 200)                 # the weekly averages, taken from every bar the read is given (five years on
                                      # the host): two years hold about 104 weeks, too few for the 200-week

_VERBS = {"Broke", "Lost", "Reclaimed", "Gave", "Recovered", "Closed", "Bottomed", "Topped"}
_STATES = {"Breaking", "Holding", "Retesting", "Sitting", "Leading", "Lagging", "Back", "Below", "Between", "In",
           "Pulling", "At", "Stretched", "Ahead", "Behind", "Oversold", "Overbought"}


@dataclass
class Fact:
    key: str                          # stable id, e.g. "trend.stack"
    family: str                       # Trend, Levels, Momentum, Divergence, Volume, Volatility, Candles, Gaps, ...
    cls: str                          # a CLASS_WEIGHT key
    side: int                         # +1 long case, -1 short case, 0 neither
    strength: float                   # 0..1
    head: str                         # a few plain words: "Pulling back to support"
    text: str                         # one plain sentence, no price
    reading: str                      # the one-line "also considered" form: "RSI 48, neutral"
    learn: str = ""                   # a glossary key: the teaching line the page shows with it
    rarity: float = 0.0               # 0..1: how unusual this reading is for any chart
    data: dict = field(default_factory=dict)
    clause: str = ""                  # the fact as a lowercase clause for the desk's paragraph ("selling on the dip
                                      # is light"); the head, lowercased, when empty
    wrong: tuple = None               # the close that makes this reading false: (price, its words[, "weekly"]), above
                                      # the close for a reading against the long, below it for one for it

    def as_clause(self):
        """the fact as a clause: its own when set, else its head made into one ("Broke out of a base" -> "it broke out
        of a base", "A bull flag" -> "there is a bull flag", "Buyers stepping in" -> "buyers are stepping in")"""
        if self.clause:
            return self.clause
        h = self.head
        first, _, rest = h.partition(" ")
        low = h if (len(first) > 1 and first.isupper()) else h[:1].lower() + h[1:]   # keep RSI, MACD, QQQ
        if first in _VERBS:
            return "it " + low
        if first in _STATES:
            return "it is " + low
        if first in ("A", "An"):
            return "there is " + low
        if rest.split(" ")[0].endswith("ing") and first.endswith("s") and first not in ("Swings",):
            return f"{first.lower()} are {rest}"
        return low


    @property
    def vote(self):
        return CLASS_WEIGHT[self.cls] * self.strength * self.side


def pct(x, nd=1):
    """a signed percent in words: +2.4% / −0.8% / 0% (whole numbers from 10% up)"""
    if abs(x) >= 10:
        nd = 0
    v = round(x, nd)
    if v == 0:
        return "0%"
    s = f"{abs(v):.{nd}f}"
    if nd > 0:
        s = s.rstrip("0").rstrip(".")                # 2.50 -> 2.5, never 80 -> 8 (the audit's C-C6)
    return ("+" if v > 0 else "−") + s + "%"


def atr_words(x):
    """an ATR distance in words: 0.5 ATR / 1.3 ATR"""
    return f"{abs(x):.1f}".rstrip("0").rstrip(".") + " ATR"


class Ctx:
    """one name's measured state on its completed daily bars"""

    def __init__(self, sym, bars, index_sym=None, index_bars=None, extra=None, degree="daily"):
        full = [b for b in bars if b.get("c") is not None]
        bars = full[-BARS_USED:]
        self.sym, self.bars, self.n, self.degree = sym, bars, len(bars), degree
        self.extra = extra or {}
        self.c = ta.closes(bars)
        self.close = self.c[-1]
        self.atrs = ta.atr(bars)
        self.atr = self.atrs[-1]
        rets = [math.log(b / a) for a, b in zip(self.c[-61:], self.c[-60:]) if a > 0 and b > 0]
        sd = (sum((r - sum(rets) / len(rets)) ** 2 for r in rets) / (len(rets) - 1)) ** 0.5 if len(rets) > 20 else None
        self.sigma = sd * self.close if sd else (self.atr * 0.8 if self.atr else None)   # one day's typical move
        self.sma20, self.sma50, self.sma200 = ta.sma(self.c, 20), ta.sma(self.c, 50), ta.sma(self.c, 200)
        self.rsi = ta.rsi(self.c)
        self.macd = ta.macd(self.c)
        self.adx = ta.adx(bars)
        self.bb = ta.bollinger(self.c)
        self.vol = [float(b.get("v") or 0) for b in bars]
        self.vol50 = ta.sma(self.vol, 50)
        self.minor = pivots.zigzag(bars, self.atrs, MINOR_K)
        self.major = pivots.zigzag(bars, self.atrs, MAJOR_K)
        if degree == "weekly":                    # its own 50 and 200 bars are the weekly averages
            self.wk_avg = {}
        else:
            wc = [float(w["c"]) for w in ta.weekly(full)]
            self.wk_avg = {n: sum(wc[-n:]) / n for n in WEEK_AVGS if len(wc) >= n}
        self.levels = levels.collect(bars, self.atrs, self.minor, self.major, weekly=self.wk_avg,
                                     unit="week" if degree == "weekly" else "day")
        self.areas = levels.areas(self.levels, self.atr, bars) if self.atr else []
        self.weekly = ta.weekly(bars)
        self.divs = divergence.find(bars)
        self.wdivs = divergence.find(self.weekly, fresh=3) if len(self.weekly) > 30 else []
        self.index_sym = index_sym
        self.index_bars = [b for b in (index_bars or []) if b.get("c") is not None][-BARS_USED:]

    def at_atr(self, price):
        """price's distance from the last close in ATR (+ above)"""
        return (price - self.close) / self.atr

    def pct_of(self, price):
        """price's distance from the last close in % (+ above)"""
        return (price / self.close - 1.0) * 100.0

    def when(self, i):
        return levels.when(self.bars, i)

    def on(self, i, cap=False):
        """an event's session for a sentence: "on Oct 16" ("On Oct 16" to open one); never "today" or "N sessions
        ago", which a card frozen at its listing read would carry past their day"""
        return ("On " if cap else "on ") + self.when(i)
