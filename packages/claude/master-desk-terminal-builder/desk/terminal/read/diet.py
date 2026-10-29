"""The language diet (the owner, 2026-10-26: "No disclaimers or superfluous irrelevant information, no redundant or
duplicated language"): a card states each fact once, in its one home, in its shortest plain form.

  the plan        its numbers and why_zone, why_out, why_t1, why_t2: every level the plan stands on, and its out (the
                  record's one line); the sheet's plan lines give its numbers only, a fact that names the zone's or
                  the target's levels calls them the buy zone or the target, and an out under the zone's own level
                  is said to be under the buy zone (under the trigger line for a breakout or a turn)
  the face        the gist: the chart in a few plain words and where the price sits, naming no level and no fact the
                  lists state
  the lists       material first, then standouts and against: each fact once, its teaching line once per card
  the take        how the evidence nets and what caps the verdict (its one home: gut.why is published empty)
  change          the close that proves the case against wrong, when that fact's own test names one, else ""
  the sheet       one answer per line of the owner's list, each reading in one line only
  considered      the readings no line of the sheet holds
  the fear day    the card's fear-day block, never again in material; holding it: the held chip, never a sentence

diet(pub)      a copy with the rules applied from the published fields alone, so a card listed before them keeps its
               read and its plan with its words cut to the rules; idempotent: a read made under them passes unchanged
phrases(pub)   the card's public strings [(path, text)], the words the backend composes (not the news headlines, not
               the drawing's chart labels)
repeats(pub)   {four-word phrase: [paths]} for every phrase said more than once on the card; a phrase is words, so
               four tokens with fewer than two words of three letters or more ("+4% in 1 month") are numbers
disclaimers(s) the banned disclaimer and caveat phrases in a string (BANNED)"""
import re

from . import sheet as S

BANNED = ("investment advice", "hypothetical", "paper result", "paper trading", "simulated", "not real money",
          "for entertainment", "past performance", "no guarantee", "not a recommendation", "do your own research",
          "at your own risk", "educational purposes", "did no worse on average", "the desk's replay",
          "not read this session", "not read yet", "needs a year of stored readings", "not a fact",
          "the usual convention", "alpaca gives none")

EVIDENCE = ("the evidence is broad", "the evidence leans its way", "the evidence nets against it")
CAP = "chasing a finished fifth wave"
CAPPED = "capped at Leaning: it would chase a finished fifth wave"
LOWER = "only the lower price makes it worth owning"
SUBJECTS = ("A stock pulling back in an uptrend", "A leader pulling back", "A stock in an uptrend", "A falling stock",
            "A leader", "A stock")                 # compose._subject's words, longest first
SUBJECTS = tuple(s.replace("stock", "fund") for s in SUBJECTS if "stock" in s) + SUBJECTS   # a fund's (subject)
BROKE_OUT = ("Broke out of ", "Breaking out of ")  # a held upside break's head (read/patterns.py, formations.py)
HELD = "Held"
STALE = ("Options: ", "Realized volatility ", "Net dealer gamma ", "News: ", "SPY put/call", "QQQ put/call",
         "IWM put/call")                            # a listed read's own options and news lines (read/optnews.py)                                       # the desk's book on the sheet; the card's chip is `held`


def disclaimers(s):
    low = (s or "").lower()
    return [b for b in BANNED if b in low]


# ------------------------------------------------------------------------------------------ the words of a card
def take(gut_why, form, word):
    """the verdict's reasons in one line: how the evidence nets, and what caps it. The facts behind it are the
    lists' (the sharpest conflict is first in what argues against it); "" when the evidence is mixed and nothing caps"""
    parts = [w for w in gut_why or () if w in EVIDENCE]
    if CAP in (gut_why or ()):
        parts.append(CAPPED)
    if form == "pullback" and word == "Against":
        parts.append(LOWER)
    s = "; ".join(parts)
    return s[:1].upper() + s[1:] + "." if s else ""


def change(fails_on):
    """what would change the desk's mind beyond the plan's own out (the plan's line, never said again): the close
    that proves the case against it wrong, when that fact's test names one, else \"\""""
    if not fails_on:
        return ""
    s = _fails_on(fails_on)
    return f"{s[:1].upper()}{s[1:]} answers the case against."


_OVER = re.compile(r"^an? (daily|weekly) close (?:over|above) ([^,]+), (.+)$")


def _fails_on(s):
    """the close in plain words, its level in brackets: "a daily close over +0.2%, the Oct 7 high" read as a list
    of three things beside "proves the case against wrong" (CRGY on 2026-10-26); said plainly it is "a daily close
    over +0.2% (the Oct 7 high)"."""
    s = s[:1].lower() + s[1:]
    m = _OVER.match(s)
    return f"a {m.group(1)} close over {m.group(2)} ({m.group(3)})" if m else s


def subject(words, fund=False):
    """the chart's subject with its noun: a fund is a fund, never "a stock" (IGV on 2026-10-26)"""
    return words.replace("stock", "fund") if fund else words.replace("fund", "stock")


def gist(form, subject, near=True, broke=False):
    """the face: the chart in a few plain words and where the price sits (the levels are the plan's, the evidence the
    lists'); broke: a held break out of a pattern, so a buy now is a buy above that break, never "at support" (COLB
    on 2026-10-26 broke out of its base on 2.0x volume and read "A stock at support")"""
    if form == "now":
        return f"{subject} holding above where it broke out." if broke else f"{subject} at support."
    if form == "pullback":
        return f"{subject}, above support."
    if form == "breakout":
        return f"{subject} {'pressing against' if near else 'below'} resistance."
    return f"{subject}."


# ------------------------------------------------------------------------------------------ the public strings
FACT_LISTS = ("material", "standouts", "against")
PLAN_WORDS = ("sentence", "why_zone", "why_out", "why_t1", "why_t2")


def phrases(pub):
    """[(path, text)]: every string of the card the backend composes"""
    out = [(k, pub[k]) for k in ("gist", "take", "change", "action") if isinstance(pub.get(k), str)]
    cv, gut, pl, fear = (pub.get(k) or {} for k in ("conviction", "gut", "plan", "fear"))
    if isinstance(cv, dict) and cv.get("word"):
        out.append(("conviction.word", cv["word"]))
    out += [("gut.why", w) for w in (gut.get("why") or ()) if isinstance(gut, dict)]
    out += [(f"plan.{k}", pl[k]) for k in PLAN_WORDS if isinstance(pl, dict) and pl.get(k)]
    for k in FACT_LISTS:
        for f in pub.get(k) or ():
            out += [(f"{k}.{part}", f[part]) for part in ("head", "text", "learn") if f.get(part)]
    out += [(f"sheet.{k}", v) for k, v in (pub.get("sheet") or {}).items() if isinstance(v, str)]
    out += [("considered", s) for s in pub.get("considered") or ()]
    out += [(f"fear.{k}", fear[k]) for k in ("label", "text") if isinstance(fear, dict) and fear.get(k)]
    out += [("flags", s) for s in pub.get("flags") or ()]
    for c in pub.get("cautions") or ():
        out += [(f"cautions.{part}", c[part]) for part in ("head", "text") if c.get(part)]
    eng = pub.get("engine") or {}
    out += [(f"engine.{k}", eng[k]) for k in ("status", "note") if eng.get(k)]
    return [(p, t) for p, t in out if t]


_BOUND = re.compile(r"[;:,()?!—]|\.(?=\s|$)|\s[–-]\s")
_WORD = re.compile(r"^[a-z][a-z'’-]{2,}$")
_AVG = re.compile(r"^\d+-(?:day|week)$")
_MOVES = {"drop", "rise", "decline", "advance", "pullback", "fall", "run"}    # "the Aug 5–Sep 30 drop"
_MONTHS = {"jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec", "january", "february",
           "march", "april", "june", "july", "august", "september", "october", "november", "december"}


def grams(text, n=4):
    """the n-word phrases of a string: words inside one clause (a phrase never runs across . ; : , or brackets), at
    least two of them words of three letters or more, none of them a month or a level's word: a dated bar or a
    level ("the May 26 low", "the 61.8% retracement of the Jun 23–Sep 23 rise") is a name the plan and a fact may
    both give"""
    for seg in _BOUND.split(text.lower()):
        w = [t.strip("\"'“”‘’") for t in seg.split()]
        w = [t for t in w if t]
        for i in range(len(w) - n + 1):
            g = w[i:i + n]
            if sum(1 for t in g if _WORD.match(t)) >= 2 and not _name(g):
                yield " ".join(g)


def _name(g):
    """a phrase inside a level's or a bar's name, or the join of two names: a date or a month, a retracement, an
    extension, a breakout level, the average price paid since a bar, the most-traded price, an open gap, a 50-day or
    30-week average, a wave's start or high ("the start of wave 1", "the fifth wave's high", "the wave-1 high")"""
    w = set(g) | {p for t in g for p in t.split("–")}      # "5–sep": a range of dates
    return any((
        _MONTHS & w,
        w & {"retracement", "extension", "most-traded"},
        {"breakout", "level"} <= w,
        g[1] in _MOVES and g[0][:1].isdigit(),             # "30 drop and the": a range's end
        {"average", "price"} <= w or {"price", "paid"} <= w,
        {"price", "of"} <= w and w & {"months", "year"},     # "the most-traded price of six months"
        {"open", "gap"} <= w,
        {"start", "wave"} <= w or any(t.endswith("wave's") or t.startswith("wave-") for t in g),
        "average" in w and any(_AVG.match(t) for t in g),
        {"and", "the"} <= w and (w & {"high", "low"} or any(t[:1].isdigit() for t in g)),   # two names joined
    ))


def repeats(pub, n=4):
    seen = {}
    for path, text in phrases(pub):
        for g in grams(text, n):
            seen.setdefault(g, []).append(path)
    return {g: ps for g, ps in seen.items() if len(ps) > 1}


# ------------------------------------------------------------------------------------------ the rules, applied
_CAVEATS = (                                                    # a caveat said by code before the diet, cut
    (re.compile(r"; implied volatility not read this session"), ""),
    (re.compile(r"; its implied volatility was not read this session"), ""),
    (re.compile(r"(?:\. |; )IV rank(?: needs a year of stored readings(?: \(\d+ of \d+ sessions\))?|: a year of "
                r"readings is stored \(\d+ of \d+ sessions\), the rank not read yet)"), ""),
    (re.compile(r"^Its realized volatility over the last 20 sessions is (\S+) a year; its implied volatility was not "
                r"read this session\.$"), r"Its realized volatility over the last 20 sessions is \1 a year."),
    (re.compile(r", counting the [^,;]* of the open interest that carries a gamma \(Alpaca gives none for same-day "
                r"expiries or for contracts without a quote\)"), ""),
    (re.compile(r", if dealers are long the calls and short the puts: the usual convention, not a fact"), ""),
    (re.compile(r"; dealer gamma counts only open interest that carries a gamma \(Alpaca gives none for same-day "
                r"expiries or for contracts without a quote\)"), ""),
    (re.compile(r"; dealer gamma counts dealers long the calls and short the puts, a convention, not a fact"), ""),
)
_WARNINGS = (                                                   # the study's warnings, without restating the fact
    (re.compile(r"^.* inside a downtrend on every average\. In the desk's study, a broken stock flashing a bullish "
                r"signal lagged the market\.$"), "Such signals lagged the market in the desk's study."),
    (re.compile(r"^.*\. In the desk's study, bullish divergences at the year's low trailed the market over the next "
                r"month\.$"), "Such divergences trailed the market over the next month in the desk's study."),
    (re.compile(r"^.*, under the board's bar of 20 million dollars a day at 5 dollars or more\.$"), S.THIN),
    (re.compile(r"^The board needs 20 million dollars a day at 5 dollars or more\.$"), S.THIN),
)


_LEGACY = (                                                     # a fact's words before the diet -> today's
    (re.compile(r"^On the weekly chart:? (\w)"), lambda m: m.group(1).upper()),
    (re.compile(r"^Against (\S+), the fund it follows, it is "), r"Against \1 it is "),
    (re.compile(r", its sector fund on the desk's map, it is "), ", its sector fund, it is "),
    (re.compile(r": moves this stretched tend to pause or snap back\.$"), "."),
    (re.compile(r"\. A daily close above the wave-1 high \(([^)]*)\) says wave 3 is under way\.$"),
     r"; a close over the wave-1 high (\1) says wave 3 is under way."),
    (re.compile(r"The count is wrong on a daily close under the wave-1 high"), "The count is wrong on a close under the "
                                                                                "wave-1 high"),
    (re.compile(r" usually takes three waves and reaches "), " usually unfolds in three waves and reaches "),
    (re.compile(r"^Buy (the reaction )?on a pullback to between "), r"Buy \1between "),
    (re.compile(r"\. Once in, out on a daily close below "), ". Once in, out on a close below "),
)


def _uncaveat(s):
    for pat, rep in _CAVEATS + _LEGACY:
        s = pat.sub(rep, s)
    return s


def _unlearn(f):
    """a teaching line that says its fact's own words again, or its own twice, says nothing new: dropped"""
    g = list(grams(f.get("learn") or ""))
    if g and (set(g) & set(grams(f.get("text") or "")) or len(set(g)) < len(g)):
        return dict(f, learn="")
    return f


_WAVE_UP = re.compile(r"^(?:weekly: )?(?:a\* setup: wave 2 of wave 3|a deep wave [24]|wave [24] (?:in its buy zone|"
                      r"turning up from its zone|still above its zone))$")
_WAVE_DOWN = re.compile(r"^(?:weekly: )?(?:five waves up look complete|a pullback that is not done)$")


def _story(head):
    """the story a fact's head tells: the wave counts on one side are one, and a weekly fact tells its daily twin's"""
    h = (head or "").lower()
    if _WAVE_UP.match(h):
        return "wave.up"
    if _WAVE_DOWN.match(h):
        return "wave.down"
    return h[len("weekly: "):] if h.startswith("weekly: ") else h


def _material(pub):
    """material without what has its own home (the held chip, the fear-day block), each entry in its shortest form:
    earnings inside the hold is its head alone (its teaching line says why it matters)"""
    out = []
    for m in pub.get("material") or ():
        head, text = m.get("head") or "", m.get("text") or ""
        if head in ("The desk holds it", HELD) or head.startswith("Fear day"):
            continue
        if head.startswith("Earnings ") and head.endswith(", inside the hold"):
            text = ""
        for pat, rep in _WARNINGS:
            if pat.match(text):
                text = rep
        out.append(dict(m, head=head, text=_uncaveat(text), learn=m.get("learn") or ""))
    return out


def _lists(pub, mat):
    """standouts and against without the facts material states, their teaching lines kept on the material entry;
    then each teaching line once per card, in the page's order"""
    heads = {m["head"] for m in mat}
    learn = {}
    lists = {"material": mat}
    for k in ("standouts", "against"):
        keep = []
        for f in pub.get(k) or ():
            if f.get("head") in heads:
                learn.setdefault(f["head"], f.get("learn") or "")
            else:
                keep.append(dict(f, text=_uncaveat(f.get("text") or "")))
        lists[k] = keep
    lists["material"] = [dict(m, learn=m["learn"] or learn.get(m["head"], "")) for m in mat]
    told = set()                                       # one story once: the first entry that tells it
    for k in FACT_LISTS:
        keep = []
        for f in lists[k]:
            if _story(f.get("head")) not in told:
                told.add(_story(f.get("head")))
                keep.append(f)
        lists[k] = keep
    said = set()
    for k in FACT_LISTS:
        lists[k] = [_unlearn(f) for f in lists[k]]
        for f in lists[k]:
            if f.get("learn") in said:
                f["learn"] = ""
            elif f.get("learn"):
                said.add(f["learn"])
    return lists


def _gist(pub):
    g = pub.get("gist") or ""
    subj = next((s for s in SUBJECTS if g.startswith(s)), None)
    if subj is None:
        return g
    from .indicators import is_fund
    broke = any((f.get("head") or "").startswith(BROKE_OUT) for k in FACT_LISTS for f in pub.get(k) or ())
    return gist(pub.get("form"), subject(subj, is_fund(pub.get("symbol"))), near="pressing against" in g, broke=broke)


_CASE = re.compile(r"The case against, that .*, fails on (.*)\.$")
_OLD_CHANGE = ("A daily close below ", "No trade until a daily close above ", "Until a daily close above ",
               "No plan until the chart offers a line")


_PROVES = re.compile(r"^(.*?),? proves the case against wrong\.$")


def _change(s):
    m = _CASE.search(s or "") or _PROVES.match(s or "")
    if m:
        return change(m.group(1))
    return "" if (s or "").startswith(_OLD_CHANGE) else (s or "")


def _plan(pub):
    """the plan's words: an out under a level the zone names is under the buy zone (the trigger line for a breakout
    or a turn): the level is named once, by the zone"""
    pl = pub.get("plan")
    if not isinstance(pl, dict) or not pl.get("why_out") or not pl.get("why_zone"):
        return pl
    if pl["why_out"] in pl["why_zone"]:
        return dict(pl, why_out="the trigger line" if pub.get("form") in ("breakout", "turn") else "the buy zone")
    return pl


def _named(text, pl):
    """a fact's words with the plan's lists of levels called by their place in the plan (a list of two or more
    levels is the zone's or the target's to name)"""
    for k, name in (("why_zone", "the buy zone"), ("why_t1", "the target")):
        v = (pl or {}).get(k) or ""
        if (" and " in v or ", " in v) and v in text:
            text = text.replace(v, name)
    return text


# the lists' coherence (the owner, 2026-10-26: "no contradictions and no logical gaps on any card"), for a read made
# before these rules as well as a new one (structure.facts and sheet.picks say it right at the source)
_BEAR = re.compile(r"^(?:Weekly: )?(?:A lower high and a lower low|Uptrend broken|Broke down from|Breaking down from|"
                   r"A failed breakout|Downtrend on every average)")                  # the long's case against, by its head
_FLOOR = re.compile(r"^(?:Next support|Support) ([+−-]?\d[\d.]*%) below$")
_SITS = re.compile(r"^Sitting on (?:stacked )?support$")
_LEVEL = re.compile(r"^(?:Next support|Support|Resistance) [+−-]?\d[\d.]*% (?:below|above)$")
_LABELS = re.compile(r", (?=the )| and (?=the )")


def _plan_labels(pl):
    """the levels the plan places (its zone, its out, its targets), each by its own words"""
    out = set()
    for k in ("why_zone", "why_out", "why_t1", "why_t2"):
        out |= {w.strip() for w in _LABELS.split((pl or {}).get(k) or "") if w.strip().startswith("the ")}
    return out


def _at_zone(pl):
    """whether the close sits inside the plan's buy zone or within one ATR of it (its % and its risk in ATR); None
    without the plan's fields"""
    lo, hi, out, k = (pl.get(n) for n in ("zone_lo", "zone_hi", "out", "risk_atr")) if isinstance(pl, dict) else \
        (None,) * 4
    if lo is None or hi is None or out is None or not k:
        return None
    atr = (hi - out) / k
    return lo - atr <= 0.0 <= hi + atr


def _coherent(out):
    """the lists without a contradiction: a reading against the long is never a reason for a buy (it moves to what
    argues against it: CRGY's "A lower high and a lower low"); a level the plan places is placed once, by the plan
    (IGV's "Support −1.3% below: the August breakout level" beside a zone at that level); "sits on the buy zone" only
    when the close is in the zone or within an ATR of it; and a floor beside "Sitting on support" is the next one
    under it (NE's "Support −5.3% below" beside "Sitting on support")"""
    buy = out.get("form") not in (None, "wait")
    pl = out.get("plan") if isinstance(out.get("plan"), dict) else {}
    placed, at = _plan_labels(pl), _at_zone(pl)
    lists = {k: list(out.get(k) or ()) for k in FACT_LISTS}
    if buy:
        moved = [f for f in lists["material"] if _BEAR.match(f.get("head") or "")]
        lists["material"] = [f for f in lists["material"] if f not in moved]
        heads = {f.get("head") for f in lists["against"]}
        lists["against"] = [f for f in moved if f.get("head") not in heads] + lists["against"]
    for k in FACT_LISTS:
        lists[k] = [f for f in lists[k]
                    if not (_LEVEL.match(f.get("head") or "") and any(w in (f.get("text") or "") for w in placed
                                                                       | {"the buy zone", "the target"}))
                    and not (_SITS.match(f.get("head") or "") and "the buy zone" in (f.get("text") or "")
                             and at is False)]
    sits = any(_SITS.match(f.get("head") or "") for k in FACT_LISTS for f in lists[k])
    if sits:
        for k in FACT_LISTS:
            lists[k] = [dict(f, head=f"Next support {m.group(1)} below",
                             text=(f.get("text") or "").replace("The nearest floor is", "The next floor under it is"))
                        if (m := _FLOOR.match(f.get("head") or "")) else f for f in lists[k]]
    out.update(lists)
    return out


def diet(pub):
    """the card with each fact once, in its home, without a caveat (module docstring); the plan, the evidence, the
    record's fields and the drawing are untouched"""
    out = dict(pub)
    if isinstance(out.get("sheet"), dict):           # the caveats first: a cut never depends on one
        out["sheet"] = {k: _uncaveat(str(v)) for k, v in out["sheet"].items()}
    if out.get("considered"):
        out["considered"] = [_uncaveat(c) for c in out["considered"]]
    if isinstance(out.get("plan"), dict) and out["plan"].get("sentence"):
        out["plan"] = dict(out["plan"], sentence=_uncaveat(out["plan"]["sentence"]))
    gut = dict(out.get("gut") or {})
    if gut.get("why"):                                 # a read made before the diet: its take from its reasons
        out["take"] = take(gut["why"], out.get("form"), gut.get("word"))
        gut["why"] = []
        out["gut"] = gut
    if "gist" in out:
        out["gist"] = _gist(out)
    if "change" in out:
        out["change"] = _change(out["change"])
    lists = _lists(out, _material(out))
    pl = out.get("plan")
    for k in FACT_LISTS:
        out[k] = [dict(f, text=_named(f.get("text") or "", pl)) for f in lists[k]]
    if "plan" in out:
        out["plan"] = _plan(out)
    out = _coherent(out)
    if out.get("sheet"):
        before = [str(v) for v in out["sheet"].values()]
        out["sheet"], out["considered"] = S.refile(out["sheet"], out.get("considered"))
        out["sheet"] = S.distinct(out["sheet"], out.get("plan"))
        if out.get("sheet_side"):
            out["sheet_side"] = {k: v for k, v in out["sheet_side"].items() if k in out["sheet"]}
        said = before + [str(v) for v in out["sheet"].values()]
        live = any(k.startswith("options.") for k in out["sheet"])       # the session's options lines are the sheet's
        out["considered"] = [c for c in out.get("considered") or () if not any(c in v or S.covered(c, v)
                                                                            for v in said)
                             and not (live and c.startswith(STALE))]
    return out
