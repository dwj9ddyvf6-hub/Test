"""The read drawn: what its words say, as chart geometry, from the same numbers the words use.

  marks  [{d, label, kind}]: every bar the read's published words name by its date (levels.citing records each naming
         as it is made), its ISO session, a label of four words or fewer and the kind of reading that named it. A bar
         named twice keeps its best label: the detector's own name for the point (a wave's start or top, a pattern's
         point), else the noun the words give it ("the Oct 14 low", "the Aug 7 higher low"), else the reading's name
         ("Heavy buying on Oct 23" -> "Heavy buying"; KEY_LABEL), else the reading's head when it is short.
  lines  [{d1, p1, d2, p2, label, kind}]: the detectors' own lines in dollars, from session d1 to d2: a base's top and
         bottom, a flag's pole and box, a double bottom's lows and its peak, a triangle's or wedge's sides, a channel's
         lines, a trendline from its first anchor, a wave count's legs. Each fact that draws keeps its segments in its
         data ("draw", made by seg() from the detector's own pivots and line equations); only the facts the read
         publishes draw.
  avgs   {sma20, sma50, sma200}: the 20, 50 and 200-day simple averages at the read's last bar, the averages its words
         name ("the 20-day average", "its rising 50-day"), in dollars.
Prices are the split-adjusted daily bars' (the card's close is the same series); nothing here changes a fact."""
import re

from ... import calendar as cal
from . import sheet as S
from . import ta

MAX_WORDS = 4
NOUNS = ("higher low", "lower high", "higher high", "lower low", "swing high", "swing low", "high", "low",
         "earnings session")
DATE = r"[A-Z][a-z]{2} \d{1,2}(?:, \d{4})?"
# every form levels.when and levels._month name a bar in: "Oct 3", "Nov 3, 2025", "the October breakout level"
NAMING = re.compile(rf"(?<![A-Za-z0-9])(?:{DATE}|the [A-Z][a-z]+(?: \d{{4}})? breakout level)(?![0-9])")
SKIP = (": no pattern",)                         # a reading that names its bar to say nothing is there
NOUN_LABEL = {"earnings session": "Earnings session"}
# a bar named in a range: "the Jul 16–Oct 14 drop" starts at a high and ends at a low; "from Mar 19 to Jul 16" up
RANGE_ENDS = {"drop": ("High", "Low"), "decline": ("High", "Low"), "fall": ("High", "Low"),
              "rise": ("Low", "High"), "advance": ("Low", "High"), "run": ("Low", "High")}
# the reading's name for the bar it dates, when the words give the bar no noun (first matching prefix wins)
KEY_LABEL = (("pattern.breakout", "Breakout"), ("pattern.breakdown", "Breakdown"), ("pattern.failed", "Failed break"),
             ("pattern.double", "Double turn"), ("pattern.flag", "Flag"), ("pattern.", "Pattern break"),
             ("levels.bounce20", "20-day retest"), ("levels.bounce50", "50-day retest"),
             ("levels.reclaim20", "20-day reclaim"), ("levels.reclaim50", "50-day reclaim"),
             ("levels.retest", "Breakout retest"), ("levels.support_line", "Support line"),
             ("levels.resistance_line", "Resistance line"), ("levels.failed", "Trigger failed"),
             ("levels.vwap", "VWAP anchor"), ("levels.", "Level"), ("trend.structure", "Structure break"),
             ("trend.swings", "Swing"), ("trend.high52", "52-week high"), ("trend.low52", "52-week low"),
             ("trend.", "Trend"), ("vol.", "Volume"), ("candle.", "Candle"), ("gap.", "Gap"),
             ("wyckoff.spring", "Spring"), ("wyckoff.upthrust", "Upthrust"), ("wyckoff.climax", "Climax"),
             ("wyckoff.", "Wyckoff"), ("div.", "Divergence"), ("mom.macd", "MACD cross"), ("mom.", "Momentum"),
             ("wave.", "Wave"), ("elliott.", "Wave"), ("vola.", "Volatility"), ("data.adjusted", "Corporate action"))
KIND = {"Trend": "swing", "Levels": "level", "Pattern": "pattern", "Elliott wave": "wave", "Weekly wave": "wave",
        "Volume": "volume", "Candles": "candle", "Gaps": "gap", "Wyckoff": "wyckoff", "Divergence": "divergence",
        "Momentum": "momentum", "Volatility": "volatility", "Events": "event", "Data": "event"}
# label priorities: the detector's own point, a noun in the words, the reading's short name (its head without the
# date, the article or "at a support area"), its key's name, its head, its family
P_POINT, P_NOUN, P_SHORT, P_NAME, P_HEAD, P_FAMILY = 6, 5, 4, 3, 2, 1


def session(bars, i):
    """bar i's ISO session (a weekly bar's is its first session's)"""
    return cal._as_date(float(bars[i]["t"])).isoformat()


def seg(x, i1, p1, i2, p2, label, kind):
    """one segment of a detector's drawing, on the ctx's own bars (daily, or weekly for the weekly read)"""
    return {"d1": session(x.bars, i1), "p1": float(p1), "d2": session(x.bars, i2), "p2": float(p2), "label": label,
            "kind": kind}


def point(x, i, label, kind):
    """a bar a detector names, with its own name for it"""
    return {"d": session(x.bars, i), "label": label, "kind": kind}


def _words(s):
    return len(s.split())


def _price(v):
    """dollars at the card's precision: cents from $1, four decimals under it"""
    return round(v, 2) if abs(v) >= 1 else round(v, 4)


def published(pub):
    """every public string of a read in reading order: [(string, where)]"""
    out = []
    for k in ("standouts", "against", "material"):
        for f in pub.get(k) or ():
            out += [(f.get("head") or "", k), (f.get("text") or "", k)]
    for k in ("take", "gist", "change"):
        out.append((pub.get(k) or "", k))
    pl = pub.get("plan") or {}
    for k in ("why_zone", "why_out", "why_t1", "why_t2"):             # its sentence names only the read's close
        if pl.get(k):
            out.append((pl[k], "plan"))
    out += [(s, "considered") for s in pub.get("considered") or ()]
    for v in (pub.get("sheet") or {}).values():
        out += [(s, "sheet") for s in str(v).split("; ")]
    return [(s, w) for s, w in out if s]


def _source(s, fs):
    """the fact a published string is: one of its own strings, or the fact whose words it carries"""
    for f in fs:
        if s in (f.head, f.text, f.reading):
            return f
    for f in fs:
        for own in (f.text, f.reading):
            if own and len(own) > 12 and (own.rstrip(".") in s or s.rstrip(".") in own):
                return f
    return None


def _named(s, start, end):
    """(label, priority) from the words around a dated mention at s[start:end], or None"""
    if s[start:end].endswith(" breakout level"):                                 # "the October breakout level"
        return "Breakout level", P_NOUN
    after, before = s[end:end + 24].lower(), s[max(0, start - 24):start].lower()
    for n in NOUNS:
        if re.match(rf" {n}s?\b", after):
            return NOUN_LABEL.get(n, n[:1].upper() + n[1:]), P_NOUN
    if before.endswith("the open gap of "):
        return "Open gap", P_NOUN
    m = re.search(r"\b(swing high|swing low|higher low|lower high|high|low) \($", before)
    if m:                                                                        # "the last swing high (Oct 2)"
        return m.group(1)[:1].upper() + m.group(1)[1:], P_NOUN
    m = re.match(rf"–{DATE} (\w+)", s[end:end + 32])                              # the start of "X–Y drop"
    if m and m.group(1).lower() in RANGE_ENDS:
        return RANGE_ENDS[m.group(1).lower()][0], P_NOUN
    m = re.match(r" (\w+)", after)
    if before.endswith("–") and m and m.group(1) in RANGE_ENDS:                    # the end of "X–Y drop"
        return RANGE_ENDS[m.group(1)][1], P_NOUN
    up = re.search(r"\b(up|down) from $", before)
    if up:                                                                       # "five waves up from X to Y"
        return ("Low" if up.group(1) == "up" else "High"), P_NOUN
    m = re.search(rf"\b(up|down) from {DATE} to $", s[max(0, start - 40):start])
    if m:
        return ("High" if m.group(1) == "up" else "Low"), P_NOUN
    m = re.match(r": ([a-z][a-z -]*?)(?: at an? | at the |,|$)", s[end:end + 40])  # "Candle Oct 23: hammer at a ..."
    if m and 0 < _words(m.group(1)) <= MAX_WORDS:
        return m.group(1)[:1].upper() + m.group(1)[1:], P_SHORT
    return None


def _short(head, words):
    """the head as a name of four words or fewer: without the dated phrase, the article and "at a support area"
    ("Heavy buying on Oct 23" -> "Heavy buying"; "A bearish engulfing at a resistance area" -> "Bearish engulfing"),
    or None"""
    h = re.sub(rf"\s*(?:on |since |from |of |at )?(?:the )?{re.escape(words)}\b.*$", "", head) if words in head else head
    h = re.sub(r"\s+at an? (?:support|resistance) area$", "", h.strip(" ,:;"))
    h = re.sub(r"^(?:A|An|The) ", "", h).strip()
    return h[:1].upper() + h[1:] if h and _words(h) <= MAX_WORDS else None


def _key_label(key):
    return next((lab for pre, lab in KEY_LABEL if key == pre or (pre.endswith(".") and key.startswith(pre))), None)


def _label(s, m, src):
    """the best label a mention gives its bar: (label, priority)"""
    got = _named(s, m.start(), m.end())
    if got:
        return got
    if src is not None:
        head = src.head or ""
        short = _short(head, m.group(0))
        if short:
            return short, P_SHORT
        lab = _key_label(src.key)
        if lab:
            return lab, P_NAME
        if head and _words(head) <= MAX_WORDS:
            return head, P_HEAD
        return src.family, P_FAMILY
    return "Cited", P_FAMILY


def marks(pub, fs, cites):
    """[{d, label, kind}] for every bar the read's published words name, oldest first"""
    if not cites:
        return []
    rx = NAMING
    strings = published(pub)
    shown = {s for s, _ in strings}
    told = {s for s, w in strings if w in ("standouts", "against", "material")}
    points = {}                             # a bar two detectors name takes the name of the one the card tells first
    for f in sorted((f for f in fs if f.head in shown or f.text in shown or f.reading in shown),
                    key=lambda f: (f.text not in told and f.head not in told, -abs(f.vote))):
        for p in (f.data or {}).get("marks") or ():
            points.setdefault(p["d"], p)
    best = {}
    for s, where in strings:
        src = None
        for m in rx.finditer(s):
            d = cites.get(m.group(0))
            if d is None or s[m.end():].startswith(SKIP):
                continue
            if src is None:
                src = _source(s, fs) or False
            f = src or None
            label, prio = _label(s, m, f)
            kind = KIND.get(f.family, "level") if f is not None else "level"
            if d in points:
                label, prio, kind = points[d]["label"], P_POINT, points[d]["kind"]
            if d not in best or prio > best[d][0]:
                best[d] = (prio, {"d": d, "label": label, "kind": kind})
    return [best[d][1] for d in sorted(best)]


def drawn(pub, fs):
    """the facts the read publishes in some form (shown, considered or on the sheet, where a daily and a weekly count
    that say the same thing are one line: sheet.says)"""
    strings = {s for s, _ in published(pub)}
    return [f for f in fs if (f.data or {}).get("draw") and
            (f.head in strings or f.text in strings or f.reading in strings or S.says(pub.get("sheet"), f.reading))]


def lines(pub, fs):
    """[{d1, p1, d2, p2, label, kind}]: the drawings of the facts the read publishes, in dollars"""
    out, seen = [], set()
    for f in drawn(pub, fs):
        for g in f.data["draw"]:
            ln = dict(g, p1=_price(g["p1"]), p2=_price(g["p2"]))
            key = (ln["d1"], ln["p1"], ln["d2"], ln["p2"])
            if key not in seen:
                seen.add(key)
                out.append(ln)
    return out


def avgs(bars):
    """{sma20, sma50, sma200} at the last bar, in dollars; an average the bars cannot make yet is left out"""
    c = ta.closes(bars)
    out = {}
    for n in (20, 50, 200):
        v = ta.sma(c, n)[-1] if len(c) >= n else None
        if v is not None:
            out[f"sma{n}"] = _price(v)
    return out
