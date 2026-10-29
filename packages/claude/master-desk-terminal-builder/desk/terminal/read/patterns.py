"""Chart patterns, kept to the ones a trader can draw without argument: a base (a sideways range after a move) and
its breakout or breakdown, a flag (a sharp pole, then a shallow drift), a double bottom or top, and an ascending or
descending triangle. Each pattern names the line that triggers it, the line that breaks it, and its measured move
(the pattern's height carried from the trigger), which the plan may use as a target. Lines are held internally as
prices; the page shows them in % from the last close. Each fact keeps the bars it reads (data "span"), every break
states its quality (formations.quality), and the study's patterns these four do not draw follow them (formations),
each stretch of bars read once."""
from . import formations as F
from . import words as W
from .core import Fact, pct
from . import geometry as G

MIN_BASE, MAX_BASE = 15, 65                 # three to thirteen weeks
MAX_DEPTH_ATR, MAX_DEPTH_PCT = 5.0, 25.0    # a base no deeper than 5 ATR and 25%
BREAKOUT_LOOKBACK = 5
VOL_CONFIRM = 1.4                           # a breakout on 1.4x average volume or more is confirmed by volume


def base(x, end):
    """(start, end, top, bottom) of the longest sideways range ending at bar `end`, or None"""
    if end < MIN_BASE:
        return None
    hi, lo, s = float(x.bars[end]["h"]), float(x.bars[end]["l"]), end
    best = None
    limit_atr = MAX_DEPTH_ATR * (x.atrs[end] or x.atr)
    for i in range(end, max(-1, end - MAX_BASE), -1):
        hi, lo = max(hi, float(x.bars[i]["h"])), min(lo, float(x.bars[i]["l"]))
        if hi - lo > limit_atr or (hi / lo - 1.0) * 100.0 > MAX_DEPTH_PCT:
            break
        s = i
        if end - s + 1 >= MIN_BASE:
            best = (s, end, hi, lo)
    return best


def _weeks(n):
    w = round(n / 5)
    return f"{w}-week"


def facts(x):
    out = []
    if x.n < 80 or not x.atr:
        return out
    out += _base(x)
    out += _flag(x)
    out += _double(x)
    out += _triangle(x)
    return out + F.facts(x, out)                 # the study's patterns these four lack, each stretch read once


def _base(x):
    for j in range(0, BREAKOUT_LOOKBACK):
        end = x.n - 2 - j
        b = base(x, end)
        if not b:
            continue
        s, e, top, bot = b
        after = x.c[e + 1:]
        height = top - bot
        depth = (top / bot - 1.0) * 100.0
        prior = x.c[max(0, s - 60):s]
        run = (top / min(prior) - 1.0) * 100.0 if prior else 0.0
        ctxt = f" after a {pct(run, 0)} advance" if run >= 20 else ""
        name = f"{_weeks(e - s + 1)} base"
        draw = [G.seg(x, s, top, e, top, "Base top", "pattern"), G.seg(x, s, bot, e, bot, "Base bottom", "pattern")]
        if any(c > top for c in after):
            k = next(i for i, c in enumerate(after) if c > top) + e + 1
            rv = x.vol[k] / (x.vol50[k - 1] or 1)
            q = F.quality(x, top, 1, k)
            if x.close >= top - 0.25 * x.atr:
                vol_ok = rv >= VOL_CONFIRM
                return [Fact("pattern.breakout", "Pattern", "structure", 1, 0.8 if vol_ok else 0.55,
                             f"Broke out of {W.a(name)}",
                             f"{x.on(k, cap=True)} it closed "
                             f"above the base's top ({depth:.0f}% deep){ctxt}, on {rv:.1f}x average volume"
                             + ("." if vol_ok else ", lighter than a strong breakout carries.")
                             + " " + F.quality_text(q, 1),
                             f"Pattern: breakout, {name} ({rv:.1f}x volume{F.quality_reading(q)})", "breakout",
                             0.6, {"trigger": top, "floor": bot, "target": top + height, "vol": rv,
                                   "weeks": (e - s + 1) / 5, "kind": "base", "line": f"the top of its {name}",
                                   "span": (s, e), "name": name, "draw": draw,
                                   "marks": [G.point(x, k, "Breakout", "pattern")], **q})]
            return [Fact("pattern.failed", "Pattern", "structure", -1, 0.5, f"A failed breakout from {W.a(name)}",
                         "It closed above the base's top but has fallen back inside: a failed breakout. "
                         + F.quality_text(q, 1),
                         f"Pattern: failed breakout, {name}", "failed_breakout", 0.5,
                         {"trigger": top, "floor": bot, "kind": "base", "span": (s, e), "name": name, "draw": draw,
                          "marks": [G.point(x, k, "Breakout", "pattern")], **q},
                         wrong=(top, f"the top of the {name}"))]
        if any(c < bot for c in after):
            k = next(i for i, c in enumerate(after) if c < bot) + e + 1
            rv = x.vol[k] / (x.vol50[k - 1] or 1)
            q = F.quality(x, bot, -1, k)
            if x.close <= bot + 0.25 * x.atr:
                return [Fact("pattern.breakdown", "Pattern", "structure", -1, 0.75 if rv >= VOL_CONFIRM else 0.5,
                             f"Broke down from {W.a(name)}",
                             f"It closed below the base's bottom on {rv:.1f}x average volume. "
                             + F.quality_text(q, -1),
                             f"Pattern: breakdown, {name} ({rv:.1f}x volume{F.quality_reading(q)})",
                             "breakdown", 0.55, {"trigger": bot, "ceiling": top, "target": bot - height, "vol": rv,
                                                 "kind": "base", "span": (s, e), "name": name, "draw": draw,
                                                 "marks": [G.point(x, k, "Breakdown", "pattern")], **q},
                             wrong=(bot, f"the bottom of the {name}"))]
            return [Fact("pattern.failed", "Pattern", "structure", 1, 0.45, f"A failed breakdown from {W.a(name)}",
                         "It closed below the base's bottom but has climbed back inside: a failed breakdown, "
                         "which traps sellers. " + F.quality_text(q, -1), f"Pattern: failed breakdown, {name}",
                         "failed_breakdown", 0.5,
                         {"trigger": top, "floor": bot, "kind": "base", "span": (s, e), "name": name, "draw": draw,
                          "marks": [G.point(x, k, "Breakdown", "pattern")], **q})]
        if j == 0:
            near_top = (top - x.close) <= 1.0 * x.atr
            side = 1 if run >= 20 else 0
            return [Fact("pattern.base", "Pattern", "structure", side, 0.4 if side and near_top else 0.25 if side else 0.0,
                         f"In " + W.a(name) + (", near its top" if near_top else ""),
                         f"It has moved sideways for {round((e - s + 1) / 5)} weeks in a range {depth:.0f}% deep{ctxt}"
                         + (", and sits near the top of it." if near_top else "."),
                         f"Pattern: {name}, {depth:.0f}% deep" + (", near the top" if near_top else ""), "base",
                         0.35 if near_top else 0.2,
                         {"trigger": top, "floor": bot, "target": top + height, "weeks": (e - s + 1) / 5,
                          "kind": "base", "near_top": near_top, "line": f"the top of its {name}", "span": (s, e),
                          "name": name, "draw": draw})]
    return []


def _flag(x):
    """a pole of 5 ATR or more within 15 sessions, then 4 to 20 sessions giving back at most half of it on lighter
    volume"""
    n = x.n
    for top_i in range(n - 5, max(n - 22, 20), -1):
        seg = x.bars[top_i + 1:]
        if len(seg) < 4:
            continue
        hi = float(x.bars[top_i]["h"])
        if any(float(b["h"]) > hi for b in seg[:-1]):
            continue
        lo_i = min(range(max(0, top_i - 15), top_i), key=lambda i: float(x.bars[i]["l"]))
        pole = hi - float(x.bars[lo_i]["l"])
        a = x.atrs[top_i] or x.atr
        if pole < 5 * a or (hi / float(x.bars[lo_i]["l"]) - 1.0) * 100.0 < 12:
            continue
        flag_lo = min(float(b["l"]) for b in seg)
        if hi - flag_lo > 0.5 * pole:
            continue
        pv = sum(x.vol[lo_i:top_i + 1]) / (top_i - lo_i + 1)
        fv = sum(x.vol[top_i + 1:]) / len(seg)
        if fv >= pv:
            continue
        broke = x.close > hi
        gain = (hi / float(x.bars[lo_i]["l"]) - 1.0) * 100.0
        q = F.quality(x, hi, 1, n - 1) if broke else {}  # no high over the pole's top before the last session
        return [Fact("pattern.flag", "Pattern", "structure", 1, 0.7 if broke else 0.5,
                     "Breaking out of a bull flag" if broke else "A bull flag",
                     f"It ran {pct(gain, 0)} in {top_i - lo_i} sessions, then drifted for {len(seg)} sessions on lighter "
                     f"volume, giving back {(hi - flag_lo) / pole * 100:.0f}% of the run"
                     + (", and has now cleared the top. " + F.quality_text(q, 1) if broke else
                        ": a pause that often precedes the next leg."),
                     f"Pattern: bull flag ({pct(gain, 0)} pole, {len(seg)}-session flag"
                     + (F.quality_reading(q) if broke else "") + ")", "flag", 0.55,
                     {"trigger": hi, "floor": flag_lo, "target": hi + pole * 0.75, "kind": "flag", "broke": broke,
                      "line": "the top of the flag", "span": (lo_i, n - 1), "name": "bull flag",
                      "draw": [G.seg(x, lo_i, float(x.bars[lo_i]["l"]), top_i, hi, "Flag pole", "pattern"),
                               G.seg(x, top_i, hi, n - 1, hi, "Flag top", "pattern"),
                               G.seg(x, top_i, flag_lo, n - 1, flag_lo, "Flag low", "pattern")], **q})]
    for bot_i in range(n - 5, max(n - 22, 20), -1):
        seg = x.bars[bot_i + 1:]
        if len(seg) < 4:
            continue
        lo = float(x.bars[bot_i]["l"])
        if any(float(b["l"]) < lo for b in seg[:-1]):
            continue
        hi_i = max(range(max(0, bot_i - 15), bot_i), key=lambda i: float(x.bars[i]["h"]))
        pole = float(x.bars[hi_i]["h"]) - lo
        a = x.atrs[bot_i] or x.atr
        if pole < 5 * a or (1.0 - lo / float(x.bars[hi_i]["h"])) * 100.0 < 12:
            continue
        flag_hi = max(float(b["h"]) for b in seg)
        if flag_hi - lo > 0.5 * pole:
            continue
        pv = sum(x.vol[hi_i:bot_i + 1]) / (bot_i - hi_i + 1)
        fv = sum(x.vol[bot_i + 1:]) / len(seg)
        if fv >= pv:
            continue
        broke = x.close < lo
        drop = (lo / float(x.bars[hi_i]["h"]) - 1.0) * 100.0
        q = F.quality(x, lo, -1, n - 1) if broke else {}  # no low under the pole's low before the last session
        return [Fact("pattern.flag", "Pattern", "structure", -1, 0.7 if broke else 0.5,
                     "Breaking down from a bear flag" if broke else "A bear flag",
                     f"It fell {pct(drop, 0)} in {bot_i - hi_i} sessions, then bounced weakly for {len(seg)} sessions on "
                     f"lighter volume" + (", and has now broken the low. " + F.quality_text(q, -1) if broke else
                                          ": a pause that often precedes the next leg down."),
                     f"Pattern: bear flag ({pct(drop, 0)} pole" + (F.quality_reading(q) if broke else "") + ")",
                     "flag", 0.55,
                     {"trigger": lo, "ceiling": flag_hi, "target": lo - pole * 0.75, "kind": "flag", "broke": broke,
                      "span": (hi_i, n - 1), "name": "bear flag",
                      "draw": [G.seg(x, hi_i, float(x.bars[hi_i]["h"]), bot_i, lo, "Flag pole", "pattern"),
                               G.seg(x, bot_i, lo, n - 1, lo, "Flag bottom", "pattern"),
                               G.seg(x, bot_i, flag_hi, n - 1, flag_hi, "Flag high", "pattern")], **q},
                     wrong=(flag_hi, "the top of the flag"))]
    return []


def _double(x):
    """two swing lows (highs) within 0.75 ATR, 10 to 80 sessions apart, with a peak (trough) at least 3 ATR between"""
    conf = [p for p in x.minor if p.confirmed]
    for kind, side in (("L", 1), ("H", -1)):
        pts = [p for p in conf if p.kind == kind][-2:]
        if len(pts) < 2:
            continue
        a, b = pts
        if not (10 <= b.i - a.i <= 80) or x.n - 1 - b.i > 30:
            continue
        atr = x.atrs[b.i] or x.atr
        if abs(a.price - b.price) > 0.75 * atr:
            continue
        mid = [p for p in conf if p.kind != kind and a.i < p.i < b.i]
        if not mid:
            continue
        neck = max(p.price for p in mid) if kind == "L" else min(p.price for p in mid)
        depth = abs(neck - (a.price + b.price) / 2)
        if depth < 3 * atr:
            continue
        lowpt = min(a.price, b.price) if kind == "L" else max(a.price, b.price)
        name = "double bottom" if kind == "L" else "double top"
        done = x.close > neck if kind == "L" else x.close < neck
        failed = x.close < lowpt if kind == "L" else x.close > lowpt
        if failed:
            continue
        tgt = neck + depth if kind == "L" else neck - depth
        q = {}
        if done:                                 # the confirmation: the first close past the line after the second turn
            k = next((i for i in range(b.i + 1, x.n) if side * (x.c[i] - neck) > 0), x.n - 1)
            q = F.quality(x, neck, side, k)
        return [Fact(f"pattern.double", "Pattern", "structure", side, 0.7 if done else 0.35,
                     ("Confirmed " if done else "A possible ") + name,
                     f"It {'bottomed' if kind == 'L' else 'topped'} twice at one level ({x.when(a.i)} and "
                     f"{x.when(b.i)})" + (f" and has closed {'above' if kind == 'L' else 'below'} the "
                                          f"{'peak' if kind == 'L' else 'low'} between them: a confirmed {name}. "
                                          + F.quality_text(q, side)
                                          if done else f"; a close {'above' if kind == 'L' else 'below'} the "
                                          f"{'peak' if kind == 'L' else 'low'} between them confirms the {name}."),
                     f"Pattern: {name}" + (f" (confirmed{F.quality_reading(q)})" if done else " (forming)"),
                     "double_bottom" if kind == "L" else "double_top", 0.55 if done else 0.35,
                     {"trigger": neck, "floor" if kind == "L" else "ceiling": lowpt, "target": tgt, "kind": "double",
                      "done": done, "line": "the peak between its two lows" if kind == "L" else "the low between its two highs",
                      "span": (a.i, b.i), "name": name,
                      "draw": [G.seg(x, a.i, a.price, b.i, b.price, "Double bottom" if kind == "L" else "Double top",
                                   "pattern"),
                               G.seg(x, a.i, neck, b.i, neck, "Peak between" if kind == "L" else "Low between",
                                   "pattern")],
                      "marks": [G.point(x, a.i, "First low" if kind == "L" else "First high", "pattern"),
                                G.point(x, b.i, "Second low" if kind == "L" else "Second high", "pattern")], **q},
                     f"it has confirmed a {name}" if done else "",
                     wrong=(lowpt, "the two highs") if kind == "H" else None)]
    return []


def _triangle(x):
    """two or more swing highs (lows) within 0.5 ATR of each other, the swing lows (highs) between them rising
    (falling), in the last 60 sessions"""
    conf = [p for p in x.minor if p.confirmed and p.i >= x.n - 60]
    hs, ls = [p for p in conf if p.kind == "H"], [p for p in conf if p.kind == "L"]
    out = []
    if len(hs) >= 2 and len(ls) >= 2:
        top = hs[-2:]
        if abs(top[0].price - top[1].price) <= 0.5 * x.atr and ls[-1].price > ls[-2].price + 0.5 * x.atr:
            line = max(p.price for p in top)
            broke = x.close > line
            h = line - ls[-2].price
            pts = [p.i for p in top + ls[-2:]]
            q = F.quality(x, line, 1, next((i for i in range(max(pts) + 1, x.n) if x.c[i] > line), x.n - 1)) \
                if broke else {}                 # the break: the first close over the top after the last touch
            out.append(Fact("pattern.triangle", "Pattern", "structure", 1, 0.65 if broke else 0.4,
                            "Breaking out of an ascending triangle" if broke else "An ascending triangle",
                            "Sellers have capped it at the same level twice while each dip stops higher"
                            + (": it has now closed above that ceiling. " + F.quality_text(q, 1) if broke else
                               ": pressure building under the ceiling."),
                            "Pattern: ascending triangle" + (f" (breakout{F.quality_reading(q)})" if broke else ""),
                            "ascending_triangle", 0.5,
                            {"trigger": line, "floor": ls[-1].price, "target": line + h, "kind": "triangle",
                             "broke": broke, "line": "the triangle's flat top", "span": (min(pts), max(pts)),
                             "name": "ascending triangle",
                             "draw": [G.seg(x, min(pts), line, max(pts), line, "Triangle top", "pattern"),
                                      G.seg(x, ls[-2].i, ls[-2].price, ls[-1].i, ls[-1].price, "Rising lows",
                                          "pattern")], **q}))
        bot = ls[-2:]
        if abs(bot[0].price - bot[1].price) <= 0.5 * x.atr and hs[-1].price < hs[-2].price - 0.5 * x.atr:
            line = min(p.price for p in bot)
            broke = x.close < line
            h = hs[-2].price - line
            pts = [p.i for p in bot + hs[-2:]]
            q = F.quality(x, line, -1, next((i for i in range(max(pts) + 1, x.n) if x.c[i] < line), x.n - 1)) \
                if broke else {}                 # the break: the first close under the floor after the last touch
            out.append(Fact("pattern.triangle", "Pattern", "structure", -1, 0.65 if broke else 0.4,
                            "Breaking down from a descending triangle" if broke else "A descending triangle",
                            "Buyers have held the same floor twice while each bounce stops lower"
                            + (": it has now closed below that floor. " + F.quality_text(q, -1) if broke else
                               ": pressure building on the floor."),
                            "Pattern: descending triangle" + (f" (breakdown{F.quality_reading(q)})" if broke else ""),
                            "descending_triangle", 0.5,
                            {"trigger": line, "ceiling": hs[-1].price, "target": line - h, "kind": "triangle",
                             "broke": broke, "span": (min(pts), max(pts)), "name": "descending triangle",
                             "draw": [G.seg(x, min(pts), line, max(pts), line, "Triangle floor", "pattern"),
                                      G.seg(x, hs[-2].i, hs[-2].price, hs[-1].i, hs[-1].price, "Falling highs",
                                          "pattern")], **q},
                            wrong=(hs[-1].price, "the triangle's last lower high")))
    return out[:1]
