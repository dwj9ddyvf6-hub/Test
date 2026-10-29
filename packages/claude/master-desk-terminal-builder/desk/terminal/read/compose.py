"""One read, assembled: the facts, the plan the evidence earns, conviction, the desk's take, and every sentence the
page shows, all in % from the last close. read() is the single place a read is made: the board, the watching list
and the on-demand reads all call it, and every surface only formats what it returns.

The public dict carries no price. The record (for the calls ledger, never published) carries the plan's prices so
the call can be scored on later closes."""
import math
from dataclasses import replace

from ... import calendar as cal
from . import call as C
from . import plan as planmod
from . import diet, geometry, integrity, lenses, levels, sheet, waves
from . import words as W
from .core import Ctx
from .words import join, p

VERSION = "read/1"
MAX_ATR_SHARE = 0.25            # a name whose typical day moves a quarter of its price gets no read
OVERSHOOT = 0.5826              # an out checked on daily closes is passed, on average, by 0.5826 of a day's volatility
                                # (Broadie, Glasserman and Kou 1997, the correction for a barrier checked once a step)


def breakeven(x, pl):
    """the share of the time the plan must work to break even: L / (R + L), L the loss in R when the out is hit on a
    close, past its line by the overshoot (the audit's D-H5: 1 / (1 + R) assumed an exit at the line). A trim plan
    works when it reaches its second target, and R is its scaled payoff, a fifth at the first and the rest at the
    second (D-H6)"""
    b = math.log(pl.zone_hi / pl.out)
    loss = (1.0 - math.exp(-(b + OVERSHOOT * x.sigma / x.close))) / (1.0 - math.exp(-b))
    r = pl.r
    if getattr(pl, "trim", None) and pl.t2 is not None:
        r = pl.trim * pl.r + (1.0 - pl.trim) * pl.r2
    return loss / (r + loss) if r > 0 else 1.0


def _until(as_of, sessions):
    d = as_of
    for _ in range(sessions):
        d = cal.next_trading_day(d)
    return d


RECENT = 10                      # the last resort's out may sit under the lowest low of the last ten sessions
NO_LINE = "a half-day's move up"  # the last resort's trigger when no line lies above the close: no line at all
WAIT_PLAN = "Stand aside: no line within reach to buy at and be wrong under."
TRIGGER_LOOKBACK = 20            # a trigger's history: the closes above it and given back in the last 20 sessions


def trigger_history(x, pl, n=TRIGGER_LOOKBACK):
    """a breakout's or turn's trigger that price already closed above and gave back in the last n sessions: a Fact
    against the call (the line has failed before; 27 of 230 board-eligible breakout triggers on 2026-10-16), or None"""
    if pl.form not in ("breakout", "turn") or pl.trigger is None:
        return None
    from .core import Fact
    above, failed, first = False, 0, None
    for i in range(max(1, x.n - n), x.n):
        if x.c[i] > pl.trigger:
            first = i if first is None else first
            above = True
        elif above:
            above, failed = False, failed + 1
    if not failed:
        return None
    times = "once" if failed == 1 else f"{failed} times"
    return Fact("levels.failed", "Levels", "structure", -1, min(0.6, 0.3 + 0.1 * failed), "The trigger failed before",
                f"It closed above this line {times} since {x.when(first)} and gave it back "
                + ("each time." if failed > 1 else "."), f"Trigger: closed above and gave back, {times} in {n} sessions",
                "trigger_failed", 0.5, {"failed": failed}, "the trigger has failed before")


def _fallback(x, falling=True):
    """the always-available long: the trigger ladder (plan.ladder); when even that finds nothing that pays within
    REACH_ATR (sellers stacked shelf over shelf), a daily close over the nearest line above, within reach, with the out
    under the highest real line below the hold's noise (a swing low, an area's low edge or the recent low, named; with
    no line within 3 ATR, outside the noise and unnamed) and a target at the first real level 1R or more up (a
    ceiling, or a projection of the last advance past the sellers, said so in its words)"""
    form = "turn" if falling else "breakout"
    p = planmod.ladder(x, form)
    if p:
        return p
    atr, c = x.atr, x.close
    reach = c + planmod.REACH_ATR * atr
    lines = [(pv.price, f"the {x.when(pv.i)} high") for pv in x.minor if pv.kind == "H" and pv.confirmed
             and c < pv.price <= reach]
    for m, lab in ((x.sma20[-1], "the 20-day average"), (x.sma50[-1], "the 50-day average")):
        if m and c < m <= reach:
            lines.append((m, lab))
    line, label = min(lines) if lines else (c + 0.5 * atr, NO_LINE)
    trig = line + 0.1 * atr
    hi = trig + 0.35 * atr
    floor = hi - planmod.MAX_RISK_ATR * atr
    buf = max(0.25 * atr, 0.003 * c)
    below = min(c - 0.5 * atr, hi - planmod.noise(x, 10))
    k = min(range(max(0, x.n - RECENT), x.n), key=lambda i: float(x.bars[i]["l"]))      # the recent low, confirmed or not
    lines = planmod._lines_below(x, below + buf) + [(float(x.bars[k]["l"]), f"the {x.when(k)} low")]
    out, out_words = next(((q - buf, w) for q, w in sorted(lines, key=lambda t: -t[0])
                           if q < below + buf and floor <= q - buf and q - buf > 0), (max(below, floor), ""))
    risk = hi - out
    need = hi + planmod.MIN_R * risk
    cs = [a for a in planmod.ceilings(x) if a.hi > hi]
    # the first real level at 1R or more within 6 ATR of it: a ceiling, or a projection of the last advance (past the
    # sellers in the way, said so); one risk unit through them, or one and a half with none, only when nothing is real
    real = sorted(((a.lo - 0.1 * atr, a.labels(3)) for a in cs), key=lambda t: t[0]) + \
        sorted(((q, [w]) for q, w in planmod.projections(x, trig)), key=lambda t: t[0])
    real = sorted((t for t in real if need <= t[0] <= need + 6 * atr and t[0] > float(x.bars[-1]["h"])),
                  key=lambda t: t[0])                    # none its own session already traded (bs1 item 4)
    if real:
        t1, w1 = real[0]
        if cs and t1 > cs[0].lo:
            w1 = [f"{w1[0]}, past the sellers at {cs[0].labels(1)[0]}"]
    elif cs:
        t1, w1 = need, [f"one risk unit, through the sellers at {cs[0].labels(1)[0]}"]
    else:
        t1, w1 = hi + 1.5 * risk, ["one and a half times the risk, with no ceiling in the way"]
    n = planmod.horizon(x, hi, t1, out)
    return planmod.Plan(form, trig, hi, out, t1, None, trig, n, planmod.WINDOW[form], [label],
                        out_words, w1, [], "fallback")


def structural(x, pl):
    """a call with a line to be wrong at: a named out, a trigger over a real line, the first target in reach of the
    hold (and not already traded on the read's own session) and the odds rule. Every builder's plan is one
    (plan._finish); the last resort may not be: its out 3 ATR under the buy when no swing low or level lies there, its
    trigger "a half-day's move up" when no line lies above (127 and 13 reads on 2026-10-16). A stop with no reason is
    no invalidation"""
    if pl.source != "fallback":
        return True
    return bool(pl.why_out) and pl.why_zone != [NO_LINE] and planmod.in_reach(x, pl.zone_hi, pl.t1, pl.out) and \
        planmod.first_odds(pl.zone_hi, pl.t1, pl.out) >= planmod.ODDS_MIN and pl.t1 > float(x.bars[-1]["h"])


def _side_word(d):
    return "above" if d >= 0 else "below"


def pcts(pl, x):
    """every plan line in % from the last close, rounded once: the record every sentence and surface formats"""
    r = lambda v: None if v is None else round(x.pct_of(v), 2)                         # noqa: E731
    return {"zone_lo": r(pl.zone_lo), "zone_hi": r(pl.zone_hi), "trigger": r(pl.trigger), "out": r(pl.out),
            "t1": r(pl.t1), "t2": r(pl.t2)}


def time_stop(x, pl):
    """the record's time stop: twice the horizon, at most H_MAX sessions; a plan that scales out measures it to the
    second target"""
    if getattr(pl, "trim", None) and pl.t2 is not None:
        return min(2 * planmod.horizon(x, pl.zone_hi, pl.t2, pl.out), planmod.H_MAX)
    return pl.time_stop


def plan_sentence(pl, P, day_word, stop=None):
    ref = f"the {day_word} close"
    if pl.form == "wait":
        return WAIT_PLAN
    if pl.form == "now" and getattr(pl, "mode", "level") == "reaction":
        buy = (f"Buy the reaction between {p(P['zone_lo'])} and {p(P['zone_hi'])} from {ref}: a daily close up "
               "inside the zone")
    elif pl.form == "pullback" and getattr(pl, "mode", "level") == "reaction":
        buy = (f"Buy the reaction between {p(P['zone_hi'])} and {p(P['zone_lo'])} from {ref}: a daily close up "
               "inside the zone")                       # the action says it is a pullback (read/diet.py)
    elif pl.form == "now":
        buy = f"Buy between {p(P['zone_lo'])} and {p(P['zone_hi'])} from {ref}"
    elif pl.form == "pullback":
        buy = f"Buy between {p(P['zone_hi'])} and {p(P['zone_lo'])} from {ref}"
    elif pl.form == "breakout":
        buy = f"Buy on a daily close above {p(P['trigger'])} from {ref}, up to {p(P['zone_hi'])}"
    else:
        buy = f"Buy only after a daily close above {p(P['trigger'])} from {ref}, up to {p(P['zone_hi'])}"
    tgt = f"Target {p(P['t1'])}"                       # the record sells the whole plan there (the audit's F11)
    if getattr(pl, "trim", None) and P["t2"] is not None:                 # his management: trim, never the whole
        tgt = f"Take a fifth off at {p(P['t1'])}; hold the rest for {p(P['t2'])}" + \
            (f", for at most {stop} sessions" if stop else "")                # the record's time stop ends it
    if pl.form in ("breakout", "turn"):                # its out can sit above the close it names; the buy's own
        return f"{buy}. {tgt}. Once in, out on a close below {p(P['out'])}."      # words said "daily close" once
    return f"{buy}. {tgt}. Out on a daily close below {p(P['out'])}."


def _subject(fs):
    """the chart in a few words, the averages and the swings read together: over rising averages a lower swing high
    and low are a pullback inside the uptrend, never "in an uptrend" beside swings that fall (203 reads)"""
    lower = any(f.key == "trend.swings" and f.side < 0 for f in fs)
    if any(f.key == "trend.rs" and f.side > 0 and f.strength >= 0.6 for f in fs):
        return "A leader pulling back" if lower else "A leader"
    if C._uptrend(fs):
        return "A stock pulling back in an uptrend" if lower else "A stock in an uptrend"
    if C._downtrend(fs):
        return "A falling stock"
    return "A stock"


def plain_gist(form, near=None, subject="A stock"):
    """the setup in fully plain words from the call's own fields alone (its form, how near its trigger sits, and the
    chart's subject when the read has it): the face's last resort when no plain form of the gist is left"""
    if form == "now":
        return f"{subject} at a price where buyers stepped in before."
    if form == "pullback":
        return f"{subject}; the buy is lower, at a price where buyers stepped in before."
    if form == "breakout":
        where = "pressing against" if near else "below" if near is not None else "under"
        return f"{subject} {where} a price where sellers stepped in before; a daily close above it starts the move."
    if form == "turn":
        return f"{subject}; the buy comes only once it turns back up."
    return f"{subject}, with no setup yet."


def gist(pl, fs, near=True, rates=None, sym=None):
    """the face in one plain sentence: the chart in a few words (its subject) and where the price sits; near: a
    trigger within an ATR of the close (pressing against the line rather than under it). The levels are the plan's
    and the evidence the lists' (the language diet: read/diet.py), so the face names neither; it fails closed
    (plain.clean) to the sentence the call's own fields make (plain_gist)"""
    from .plain import clean
    from .indicators import is_fund
    subj = diet.subject(_subject(fs), is_fund(sym))
    broke = any(f.side > 0 and f.head.startswith(diet.BROKE_OUT) for f in fs)
    s = clean(diet.gist(pl.form, subj, near, broke)) or plain_gist(pl.form, near, subj)
    return s[0].upper() + s[1:]


# the card face's words (web/terminal/app.js face and fill): the gist, the plan's sentence (the face's line when no
# dollar order can be drawn), the action, the conviction word, the flags and the cautions (each a short head and its
# words, credited). The fear-day tag names the owner's rule by its own name ("Fear day: Fri Oct 23") and is a tag, not
# a sentence. Everything else (the take, the standouts, what argues against it, the plan rows) is the open card's,
# where the technical detail lives (the owner's rule)
FACE = ("gist", "plan.sentence", "action", "conviction.word", "flags", "cautions")


def _near(plan):
    """a trigger within an ATR of the close, from the published plan (its % and its risk in ATR); None unknown"""
    t, hi, out, k = (plan.get(n) for n in ("trigger", "zone_hi", "out", "risk_atr"))
    if t is None or hi is None or out is None or not k:
        return None
    return t <= (hi - out) / k


def face_guard(pub):
    """the read (or a listed card) with every word its face shows in plain words, for reads made before a rule
    changed and as the publisher's last check: the gist through plain.clean, else the sentence the call's own fields
    make; the plan's sentence, the action and the conviction word rebuilt from the call's fields when one fails; a
    flag that fails dropped. -> a copy; the read itself is not changed"""
    from types import SimpleNamespace
    from .plain import clean, violations
    out = dict(pub)
    form, plan = out.get("form"), dict(out.get("plan") or {})
    if violations(out.get("gist")):
        g = clean(out["gist"]) or plain_gist(form, _near(plan))
        out["gist"] = g[0].upper() + g[1:]
    if violations(plan.get("sentence")):
        P = {k: plan.get(k) for k in ("zone_lo", "zone_hi", "trigger", "out", "t1", "t2")}
        ns = SimpleNamespace(form=form, mode=plan.get("mode") or "level", trim=plan.get("trim"))
        plan["sentence"] = WAIT_PLAN if form == "wait" or P["out"] is None else \
            plan_sentence(ns, P, W.short_day(out["as_of"]), plan.get("time_stop"))
        out["plan"] = plan
    if violations(out.get("action")) and form in C.ACTION:
        out["action"] = C.ACTION[form]
    cv = out.get("conviction")
    if isinstance(cv, dict) and violations(cv.get("word")):
        out["conviction"] = dict(cv, word=C.CONVICTION.get(cv.get("level"), "Speculative"))
    if out.get("flags"):
        out["flags"] = [f for f in out["flags"] if not violations(f)]
    if out.get("cautions"):                             # a caution's head and words show on the face: in plain words
        out["cautions"] = [c for c in (_plain_caution(c, clean, violations) for c in out["cautions"]) if c]
    return out


def _plain_caution(c, clean, violations):
    """a caution in plain words: its head, text and credit through plain.clean; None (dropped) when one has no plain
    form"""
    c = dict(c)
    for k in ("head", "text", "credit"):
        if c.get(k) and violations(c[k]):
            v = clean(c[k])
            if not v:
                return None
            c[k] = v.rstrip(".") if k != "text" else v
    return c


def watch_guard(row):
    """a watching line (board.watching) in plain words: its line (the row's text when no dollar order can be drawn)
    through plain.clean, else the sentence its form makes; its action and conviction word are the read's, which
    face_guard already passed"""
    from .plain import clean, violations
    out = dict(row)
    if violations(out.get("line")):
        form = {v: k for k, v in C.ACTION.items()}.get(out.get("action"))
        out["line"] = clean(out["line"]) or plain_gist(form)
    return out


def take(gut_why, form, word):
    """the desk's verdict in one line: how the evidence nets and what caps it (diet.take). The facts behind it are
    the lists' and the sharpest conflict is first in what argues against it, so the take names none of them"""
    return diet.take(gut_why, form, word)


def case_against(fs, ceiling_pct=None):
    """the case against the call: the sharpest conflict (call.sharpest), the one the take and the desk's reasons name;
    resistance the pullback sentence already states is not named again"""
    return C.sharpest(fs, skip={"levels.ceiling"} if ceiling_pct is not None else ())


def falsifier(x, pl, sharp):
    """(the close that proves the case against wrong, in words; its % or None): over the close by its own test (the
    fact's `wrong` line), or the close that starts the buy when a trigger clears it. None without such a line"""
    w = getattr(sharp, "wrong", None) if sharp is not None else None
    if not w or w[0] <= x.close:
        return None, None
    frame = w[2] if len(w) > 2 else "daily"
    if pl.form in ("breakout", "turn") and pl.trigger is not None and frame == "daily" and w[0] <= pl.trigger:
        return "the close that starts the buy", None
    q = p(x.pct_of(w[0]))
    return (f"a {frame} close over {q}, {w[1]}", q) if q != "0%" else (None, None)


def change(fails_on):
    """what would change the desk's mind beyond the plan's out (the record's one line, which the plan states): the
    close that proves the case against wrong, by that fact's own test (falsifier); "" when its test names none"""
    return diet.change(fails_on)


def _public_fact(f):
    return {"head": f.head, "text": f.text, "learn": W.learn(f.learn)}


def _lists(fs, form, x, rates=None):
    """(material, standouts, against) with each fact once: material first (sheet.picks), the standouts and what
    argues against it without the facts material states (the language diet: read/diet.py)"""
    mp = sheet.picks(fs, form, sheet.liquid(fs, x.close))
    twin = _twins(fs)
    told = set()                                       # one story told once (_twins): the first told
    mp = [(e, f) for e, f in mp if f is None or not _told(f, twin, told)]
    stated = {id(f) for _, f in mp if f is not None}
    material = [dict(e, learn=W.learn(f.learn)) if f is not None else e for e, f in mp]
    stand = [f for f in C.standouts(fs, 1, 5, rates) if id(f) not in stated and not _told(f, twin, told)]
    against = [f for f in C.against(fs) if id(f) not in stated and not _told(f, twin, told)]
    return material, stand, against, stated


def _twins(fs):
    """{id(fact): its story} for facts that tell one story in the same words: the wave counts on one side (daily and
    weekly, of any degree), and the broken patterns on one side (each says how its break held in the same words). The
    lists tell the first; the sheet keeps every reading, and a count against the long is still told beside one for it"""
    out = {}
    for f in fs:
        if f.key.startswith("wave."):
            out[id(f)] = f"wave.{f.side}"
        elif f.family == "Pattern" and f.side and isinstance(f.data, dict) and f.data.get("at") is not None:
            out[id(f)] = f"break.{f.side}"
    return out


def _told(f, twin, told):
    """whether a twin of f was already told (and mark f told otherwise)"""
    k = twin.get(id(f))
    if k is None:
        return False
    if k in told:
        return True
    told.add(k)
    return False


def _plan_named(text, pl):
    """a fact's words with two or more of the zone's levels called the buy zone, and of the target's the target: the
    plan's why_zone and why_t1 name them (the language diet: read/diet.py)"""
    for labels, name in ((list(pl.why_zone[:3]), "the buy zone"), (list(pl.why_t1[:2]), "the target")):
        for k in (3, 2):
            for i in range(len(labels) - k + 1):
                for said in (join(labels[i:i + k]), ", ".join(labels[i:i + k])):
                    if said in text:
                        text = text.replace(said, name)
    return text


def _published(fs, plan, lists):
    """the read's lists, its sheet, which way each line points, and what else it considered: the readings that are
    neither in the lists nor on the sheet"""
    material, stand, against, stated = lists
    answered = sheet.found(fs, plan)                       # every line of the owner's list: what the read found
    shown = stated | {id(f) for f in stand + against} | sheet.on_sheet(fs, answered)
    return {"standouts": [_public_fact(f) for f in stand], "against": [_public_fact(f) for f in against],
            "material": material, "sheet": answered, "sheet_side": sheet.sides(fs, answered),
            "considered": list(dict.fromkeys(f.reading for f in fs if id(f) not in shown and f.reading))}


def read(sym, bars, index_sym=None, index_bars=None, extra=None):
    """-> (public read dict, record dict), or None when the bars are too short to read (under 260 sessions). A
    corporate action the split-adjusted feed left in (integrity.clean) is taken out first. The public read carries
    its drawing (read/geometry.py): marks, every bar its words name; lines, its detectors' own lines; avgs, the
    averages its words name"""
    with levels.citing() as cites:
        r = _read(sym, bars, index_sym, index_bars, extra)
    if r is None:
        return None
    pub, rec, fs, x = r
    pub = diet.diet(pub)                               # each fact once, no caveat (the guard over every rule)
    marks, lines = geometry.marks(pub, fs, cites), geometry.lines(pub, fs)
    if marks:
        pub["marks"] = marks
    if lines:
        pub["lines"] = lines
    pub["avgs"] = geometry.avgs(x.bars)
    return pub, rec


def drawing(pub, bars, index_sym=None, index_bars=None, extra=None):
    """{marks, lines, sheet_side} for a read published earlier (a listed card keeps the read it was listed with): the same bars
    read again, through the read's own session, and its geometry drawn against the earlier read's own words, so a
    mark is a bar those words name and a line belongs to a fact those words state ({} when nothing matches)"""
    with levels.citing() as cites:
        r = _read(pub["symbol"], bars, index_sym, index_bars, extra)
    if r is None:
        return {}
    _, _, fs, _ = r
    out = {"marks": geometry.marks(pub, fs, cites), "lines": geometry.lines(pub, fs)}
    if pub.get("sheet") and "sheet_side" not in pub:      # its own sheet's lines, which way each answer points
        out["sheet_side"] = sheet.sides(fs, sheet.distinct(pub["sheet"], pub.get("plan")))
    return {k: v for k, v in out.items() if v}


def _read(sym, bars, index_sym=None, index_bars=None, extra=None):
    """read()'s body -> (public read, record, the facts, the ctx), or None"""
    extra = extra or {}
    bars, adjusted = integrity.clean([b for b in bars if b.get("c") is not None])
    if len(bars) < 260:
        return None
    x = Ctx(sym, bars, index_sym, index_bars, extra)
    if not x.atr or not x.sigma or x.atr > MAX_ATR_SHARE * x.close:
        return None                                    # no range to read, or too wild to plan honestly
    fs = C.all_facts(x) + waves.weekly_facts(waves.weekly_ctx(x, bars))   # his higher timeframe, read beside the daily
    adj = integrity.fact(x, adjusted)
    if adj:
        fs.append(adj)
    pats = [f for f in fs if f.family == "Pattern"]
    plans = planmod.candidates(x, pats) + waves.plans(x)
    falling = C._downtrend(fs) or C.evidence(fs) <= C.BEARISH
    pl = C.choose(x, fs + C.context_facts(x, extra), plans) or _fallback(x, falling)
    as_of = cal._as_date(float(x.bars[-1]["t"]))
    # the hold the record scores: from the buy, which can come at the window's end, to the time stop (D-H4)
    by, window, stop = _until(as_of, pl.sessions), _until(as_of, pl.window), time_stop(x, pl)
    hold = _until(as_of, pl.window + stop)
    fs = fs + C.context_facts(x, extra)
    th = trigger_history(x, pl)                         # the plan's own line: counted once, against
    level, pts, cwhy = C.conviction(fs + ([th] if th else []), pl)
    gword, gpts, gwhy = C.gut(x, fs + ([th] if th else []), pl, hold)
    five = any(f.key in ("wave.five", "wave.w.five") and f.side < 0 and f.cls != "context" for f in fs)
    if (gword == "Against" or five) and pl.form == "now":
        # the desk does not buy against its own judgment, nor into a finished fifth wave (his rule: the buy is the
        # next wave 2, not this high): it waits for the close that would prove it wrong
        alt = [q for q in plans if q.form in ("breakout", "turn")]
        pl = max(alt, key=lambda q: q.r) if alt else _fallback(x, falling)
        by, window, stop = _until(as_of, pl.sessions), _until(as_of, pl.window), time_stop(x, pl)
        hold = _until(as_of, pl.window + stop)
        th = trigger_history(x, pl)
        level, pts, cwhy = C.conviction(fs + ([th] if th else []), pl)
        gword, gpts, gwhy = C.gut(x, fs + ([th] if th else []), pl, hold)
    if not structural(x, pl):
        # no line to be wrong at: no call. The read stands aside, says what would make a plan, and keeps its evidence,
        # its take and the case against with its line (COHERENCE_2026-10-19.md)
        pl, th = replace(pl, form="wait"), None
        level, pts, cwhy = C.conviction(fs, pl)
        gword, gpts, gwhy = C.gut(x, fs, pl, None)           # no buy, so no hold for earnings to fall inside
    if th:
        fs = fs + [th]
    ceil = next((a for a in planmod.ceilings(x)), None)
    ceiling_pct = x.pct_of(max(ceil.lo, x.close)) if ceil and pl.form == "pullback" and \
        (ceil.lo - x.close) / x.atr <= 2.0 else None
    e = next((f for f in fs if f.key == "ctx.earnings"), None)
    if e and pl.form != "wait" and e.data.get("date") and as_of.isoformat() < e.data["date"] <= hold.isoformat():
        e.side, e.strength = -1, 0.0
        e.head = f"Earnings {W.short_day(e.data['date'])}, inside the hold"
    day_word = W.short_day(as_of)            # "the Oct 16 close": a listed card keeps its read, so never "Friday's"
    rates = extra.get("rates")                          # the session roster's shares: what is unusual today
    sharp = case_against(fs, ceiling_pct)
    fails_on, fails_pct = falsifier(x, pl, sharp)
    lists = _lists(fs, pl.form, x, rates)
    lx = lenses.inputs(x, fs, bars, pl)                 # the eight lenses' and Conviction 8's measures (context)
    if pl.form == "wait":
        pub, rec = _wait_read(sym, x, as_of, pl, fs, level, pts, gword, gpts, gwhy, lists, fails_on, fails_pct, rates)
        if lx:
            rec["lens"] = lx
        return pub, rec, fs, x
    P = pcts(pl, x)
    if ceiling_pct is not None:
        ceiling_pct = round(ceiling_pct, 2)
    pub = {
        "symbol": sym, "as_of": as_of.isoformat(), "action": C.ACTION[pl.form], "form": pl.form,
        "conviction": {"level": level, "word": C.CONVICTION[level]},
        "gut": {"word": gword, "why": []},                    # its reasons are the take's (diet.take)
        "plan": dict(P, r=round(pl.r, 1), risk_atr=round(pl.risk / x.atr, 1), by=by.isoformat(),
                     breakeven=round(breakeven(x, pl), 2),
                     window=window.isoformat(), sessions=pl.sessions, sentence=plan_sentence(pl, P, day_word, stop),
                     why_zone=join(pl.why_zone[:3]), why_out=pl.why_out, why_t1=join(pl.why_t1[:2]),
                     mode=getattr(pl, "mode", "level")),
        "_quoted": ([p(ceiling_pct)] if ceiling_pct is not None and p(ceiling_pct) != "0%" else []) +
                   ([fails_pct] if fails_pct else []),
        "gist": gist(pl, fs, pl.trigger is None or (pl.trigger - x.close) / x.atr <= 1.0, rates, sym),
        "take": take(gwhy, pl.form, gword), "change": change(fails_on), "evidence": round(C.evidence(fs), 1)}
    if getattr(pl, "trim", None) and pl.t2 is not None:
        pub["plan"].update(trim=pl.trim, r2=round(pl.r2, 1), why_t2=join(pl.why_t2[:1]), time_stop=stop)
    pub.update(_published(fs, pub["plan"], lists))
    for k in diet.FACT_LISTS:                                 # the plan names the levels it stands on
        pub[k] = [dict(f, text=_plan_named(f["text"], pl)) for f in pub[k]]
    rec = {"v": VERSION, "symbol": sym, "as_of": as_of.isoformat(), "form": pl.form, "source": pl.source,
           "mode": getattr(pl, "mode", "level"),
           "close": x.close, "atr": x.atr, "sigma": x.sigma, "zone": [pl.zone_lo, pl.zone_hi], "trigger": pl.trigger,
           "out": pl.out, "t1": pl.t1, "t2": pl.t2, "by": by.isoformat(), "window": window.isoformat(),
           "conviction": level, "points": round(pts, 3), "gut": gword, "gut_points": round(gpts, 3),
           "evidence": round(C.evidence(fs), 4), "kinds": kinds(fs),
           "facts": [[f.key, f.side, round(f.strength, 2)] for f in fs if f.side], "run10": run10(x)}
    if getattr(pl, "trim", None) and pl.t2 is not None:
        rec.update(trim=pl.trim, time_stop=stop)
    if lx:
        rec["lens"] = lx
    return pub, rec, fs, x


def kinds(fs):
    """{kind: its one vote} to four decimals (call.family_votes): the parts the evidence sums (the board's ranking)"""
    return {k: round(v, 4) for k, v in sorted(C.family_votes(fs).items())}


def run10(x):
    """the last ten sessions' move in % (the board's spike rule, board.SPIKE_PCT), None with fewer bars"""
    return round((x.c[-1] / x.c[-11] - 1) * 100, 2) if x.n > 10 and x.c[-11] > 0 else None


def _wait_read(sym, x, as_of, pl, fs, level, pts, gword, gpts, gwhy, lists, fails_on, fails_pct, rates):
    """a read that stands aside: no buy, out or target; the evidence, the take and the case against as any read.
    Its record carries no plan, so the forward ledger scores no call (ledger.record_session)"""
    e = round(C.evidence(fs), 4)
    pub = {"symbol": sym, "as_of": as_of.isoformat(), "action": C.ACTION["wait"], "form": "wait",
           "conviction": {"level": level, "word": C.CONVICTION[level]}, "gut": {"word": gword, "why": []},
           "plan": {"sentence": WAIT_PLAN, "mode": "level"}, "_quoted": [fails_pct] if fails_pct else [],
           "gist": gist(pl, fs, True, rates, sym), "take": take(gwhy, "wait", gword), "change": change(fails_on),
           "evidence": round(e, 1)}
    pub.update(_published(fs, None, lists))
    rec = {"v": VERSION, "symbol": sym, "as_of": as_of.isoformat(), "form": "wait", "source": pl.source,
           "mode": "level", "close": x.close, "atr": x.atr, "sigma": x.sigma, "conviction": level,
           "points": round(pts, 3), "gut": gword, "gut_points": round(gpts, 3), "evidence": e, "kinds": kinds(fs),
           "facts": [[f.key, f.side, round(f.strength, 2)] for f in fs if f.side], "run10": run10(x)}
    return pub, rec


_PCT = __import__("re").compile(r"[+−-]?\d+(?:\.\d+)?%(?! retracement)")      # a retracement's % is its name


def audit(pub):
    """every % a sentence states that neither the plan nor a stated fact holds: [] for a sound read. The plan's own
    numbers (zone, trigger, out, targets) and the numbers inside the facts the read shows are the only sources a
    sentence may quote"""
    pl = pub["plan"]
    allowed = set()
    for k in ("zone_lo", "zone_hi", "trigger", "out", "t1", "t2"):
        if pl.get(k) is not None:
            allowed.add(p(pl[k]))
            allowed.add(W.p_abs(pl[k]))
    for f in pub["standouts"] + pub["against"] + (pub.get("material") or []):
        allowed.update(_PCT.findall(f["text"]))
        allowed.update(m.lstrip("+−-") for m in _PCT.findall(f["text"]))
    for extra in pub.get("_quoted", ()):
        allowed.add(extra)
        allowed.add(extra.lstrip("+−-"))
    bad = []
    for field_ in ("sentence",):
        bad += [m for m in _PCT.findall(pl[field_]) if m not in allowed]
    for field_ in ("gist", "take", "change"):
        bad += [m for m in _PCT.findall(pub[field_]) if m not in allowed and m.lstrip("+−-") not in allowed]
    return bad
