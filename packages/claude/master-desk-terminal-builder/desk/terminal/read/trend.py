"""Trend: the averages, the swing structure, the weekly stage, the 52-week range, trend strength and quality, and
strength against the fund the name follows."""
from . import pivots, ta
from .core import Fact, atr_words, pct


def _slope(series, k):
    a, b = series[-1], series[-1 - k] if len(series) > k else None
    return None if a is None or b is None else (a / b - 1.0) * 100.0


def facts(x):
    out = []
    c, m50, m200 = x.close, x.sma50[-1], x.sma200[-1]
    s50, s200 = _slope(x.sma50, 10), _slope(x.sma200, 20)
    if m50 is not None and m200 is not None and s50 is not None and s200 is not None:
        up50, up200 = s50 > 0, s200 > 0
        d50 = x.at_atr(m50)
        if c > m50 > m200 and up50 and up200:
            out.append(Fact("trend.stack", "Trend", "structure", 1, 0.8, "Uptrend on every average",
                            "Price is above its rising 50-day and 200-day averages, and the 50-day is above the "
                            "200-day.", "Averages: above both, both rising", "averages_up",
                            0.2, {"d50_atr": -d50}, "it is in an uptrend on every average"))
        elif c < m50 < m200 and not up50 and not up200:
            out.append(Fact("trend.stack", "Trend", "structure", -1, 0.8, "Downtrend on every average",
                            "Price is below its falling 50-day and 200-day averages, and the 50-day is below the "
                            "200-day.", "Averages: below both, both falling", "averages_down",
                            0.2, {"d50_atr": -d50}, "it is in a downtrend on every average",
                            wrong=(m50, "the 50-day average")))
        elif m50 > m200 and up200 and c > m200:
            out.append(Fact("trend.stack", "Trend", "structure", 1, 0.45, "Pullback in an uptrend",
                            f"Price has dipped {'below' if c < m50 else 'toward'} its 50-day average but holds above "
                            "the rising 200-day, with the 50-day above the 200-day.",
                            "Averages: under the 50-day, over a rising 200-day" if c < m50 else
                            "Averages: above both, the 50-day flattening", "pullback", 0.25, {},
                            "it is pulling back inside an uptrend"))
        elif m50 < m200 and not up200 and c < m200:
            out.append(Fact("trend.stack", "Trend", "structure", -1, 0.45, "Bounce in a downtrend",
                            f"Price has bounced {'above' if c > m50 else 'toward'} its 50-day average but stays under "
                            "the falling 200-day, with the 50-day below the 200-day.",
                            "Averages: bouncing, under a falling 200-day", "bounce", 0.25, {},
                            "it is bouncing inside a downtrend", wrong=(m200, "the 200-day average")))
        elif c > m50 and c > m200:
            out.append(Fact("trend.stack", "Trend", "structure", 1, 0.3, "Back above its averages",
                            "Price has climbed back above both its 50-day and 200-day averages.",
                            "Averages: back above the 50-day and 200-day", "moving_average", 0.3, {},
                            "it is back above its averages"))
        elif c < m50 and c < m200:
            out.append(Fact("trend.stack", "Trend", "structure", -1, 0.3, "Below its averages",
                            "Price has slipped below both its 50-day and 200-day averages.",
                            "Averages: below the 50-day and 200-day", "moving_average", 0.3, {},
                            "it is below its averages",
                            wrong=max((m50, "the 50-day average"), (m200, "the 200-day average"))))
        else:
            out.append(Fact("trend.stack", "Trend", "structure", 0, 0.0, "Between its averages",
                            "Price sits between its 50-day and 200-day averages.",
                            "Averages: between the 50-day and the 200-day", "moving_average"))
    st = pivots.structure(x.minor)
    conf = [p for p in x.minor if p.confirmed]
    last_l = next((p for p in reversed(conf) if p.kind == "L"), None)
    last_h = next((p for p in reversed(conf) if p.kind == "H"), None)
    if st == "up" and last_l and c < last_l.price:
        out.append(Fact("trend.swings", "Trend", "structure", -1, 0.5, "Uptrend broken: under its last swing low",
                        f"The swings had been climbing, but price has closed under the last swing low "
                        f"({x.when(last_l.i)}): the run of higher lows is broken.",
                        "Swings: the higher-low run broke", "swing_break", 0.45, {"level": last_l.price},
                        "it has closed under its last swing low", wrong=(last_l.price, f"the {x.when(last_l.i)} low")))
    elif st == "down" and last_h and c > last_h.price:
        out.append(Fact("trend.swings", "Trend", "structure", 1, 0.5, "Downtrend broken: over its last swing high",
                        f"The swings had been falling, but price has closed over the last swing high "
                        f"({x.when(last_h.i)}): the run of lower highs is broken.",
                        "Swings: the lower-high run broke", "swing_break_up", 0.45, {"level": last_h.price},
                        "it has closed over its last swing high"))
    elif st == "up":                                   # pivots.structure compares the last two of each
        out.append(Fact("trend.swings", "Trend", "structure", 1, 0.5, "A higher high and a higher low",
                        "Its last swing high and swing low each topped the one before.",
                        "Swings: higher high, higher low", "swings_up", 0.2, {},
                        "its last swing high and low topped the ones before"))
    elif st == "down":
        out.append(Fact("trend.swings", "Trend", "structure", -1, 0.5, "A lower high and a lower low",
                        "Its last swing high and swing low each came in under the one before.",
                        "Swings: lower high, lower low", "swings_down", 0.2, {},
                        "its last swing high and low came in under the ones before",
                        wrong=(last_h.price, f"the {x.when(last_h.i)} high") if last_h else None))
    elif st == "range":
        out.append(Fact("trend.swings", "Trend", "structure", 0, 0.0, "Swings going sideways",
                        "The recent swings neither climb nor fall in step.", "Swings: sideways", "range"))
    out += _stage(x)
    out += _range52(x)
    out += _adx(x)
    out += _quality(x)
    out += _relative(x)
    return out


def _stage(x):
    """Weinstein's stage on the weekly chart: the 30-week average's slope and price's side of it"""
    wk = x.weekly
    if len(wk) < 40:
        return []
    wc = [w["c"] for w in wk]
    m30 = ta.sma(wc, 30)
    if m30[-1] is None or m30[-6] is None:
        return []
    slope = (m30[-1] / m30[-6] - 1.0) * 100.0                     # the 30-week average over five weeks
    above = wc[-1] > m30[-1]
    if slope > 1.0 and above:
        return [Fact("trend.stage", "Trend", "structure", 1, 0.6, "Weekly chart: advancing",
                     "Price is above a rising 30-week average: the advancing stage.",
                     "Weekly stage: advancing", "stage", 0.2, {"stage": 2},
                     "the weekly chart is in its advancing stage")]
    if slope < -1.0 and not above:
        return [Fact("trend.stage", "Trend", "structure", -1, 0.6, "Weekly chart: declining",
                     "Price is below a falling 30-week average: the declining stage.",
                     "Weekly stage: declining", "stage", 0.2, {"stage": 4},
                     "the weekly chart is in its declining stage", wrong=(m30[-1], "the 30-week average", "weekly"))]
    if abs(slope) <= 1.0:
        prior = m30[-21] if len(m30) > 21 and m30[-21] else None
        topping = prior is not None and m30[-6] > prior * 1.05
        if topping:
            return [Fact("trend.stage", "Trend", "structure", -1 if not above else 0, 0.3,
                         "Weekly chart: rolling over" if not above else "Weekly chart: flattening",
                         "The 30-week average has flattened after a long rise"
                         + (", and price has slipped under it." if not above else "."),
                         "Weekly stage: flattening after a rise", "stage", 0.3, {"stage": 3},
                         "the weekly chart is rolling over" if not above else "the weekly chart is flattening",
                         wrong=(m30[-1], "the 30-week average", "weekly") if not above else None)]
        return [Fact("trend.stage", "Trend", "structure", 1 if above else 0, 0.2 if above else 0.0,
                     "Weekly chart: basing",
                     "The 30-week average is flat: a base"
                     + (", with price on its top side." if above else "."),
                     "Weekly stage: basing", "stage", 0.3, {"stage": 1},
                     "the weekly chart is basing")]
    return [Fact("trend.stage", "Trend", "structure", 0, 0.0, "Weekly chart: turning",
                 "Price has crossed its 30-week average against the average's slope.",
                 "Weekly stage: price crossing the 30-week average", "stage", 0.3)]


def _range52(x):
    yr = x.bars[-252:]
    if len(yr) < 200:
        return []
    hi, lo = max(float(b["h"]) for b in yr), min(float(b["l"]) for b in yr)
    off_hi, off_lo = (x.close / hi - 1.0) * 100.0, (x.close / lo - 1.0) * 100.0
    recent = range(x.n - 5, x.n)
    i_hi = max((i for i in recent if float(x.bars[i]["h"]) >= hi), default=None)
    i_lo = max((i for i in recent if float(x.bars[i]["l"]) <= lo), default=None)
    # "at" the extreme only where the levels add no line there (the audit's A1, levels.AT_EXTREME_ATR): a high more
    # than 0.1 ATR over the close is resistance, so "no seller from the past year is above it" would be false (A on
    # 2026-10-16 read it beside "resistance +2% above: the 52-week high"). Within an ATR it is near the extreme, the
    # same strength, said as a distance; further, a distance with no side (audit B's C1: P read "at a 52-week high"
    # 21% under it)
    from .levels import AT_EXTREME_ATR
    if i_hi is not None and hi - x.close <= AT_EXTREME_ATR * x.atr:
        return [Fact("trend.high52", "Trend", "structure", 1, 0.55, "At a 52-week high",
                     f"Price set a new 52-week high {x.on(i_hi)}: no seller from the past year is above it.",
                     f"52-week range: at the high", "high52", 0.55, {"off_hi": off_hi})]
    if i_lo is not None and x.close - lo <= AT_EXTREME_ATR * x.atr:
        return [Fact("trend.low52", "Trend", "structure", -1, 0.55, "At a 52-week low",
                     f"Price set a new 52-week low {x.on(i_lo)}: every buyer from the past year is under water.",
                     "52-week range: at the low", "low52", 0.55, {"off_lo": off_lo})]
    if i_hi is not None and hi - x.close <= x.atr:
        return [Fact("trend.high52", "Trend", "structure", 1, 0.55, "Near a 52-week high",
                     f"Price set a new 52-week high {x.on(i_hi)} and closed {pct(off_hi).lstrip('−')} under it "
                     f"({atr_words((hi - x.close) / x.atr)}).", f"52-week range: {pct(off_hi)} from the high it just set",
                     "high52", 0.55, {"off_hi": off_hi}, "it is near its 52-week high")]
    if i_lo is not None and x.close - lo <= x.atr:
        return [Fact("trend.low52", "Trend", "structure", -1, 0.55, "Near a 52-week low",
                     f"Price set a new 52-week low {x.on(i_lo)} and closed {pct(off_lo).lstrip('+')} over it "
                     f"({atr_words((x.close - lo) / x.atr)}).", f"52-week range: {pct(off_lo)} from the low it just set",
                     "low52", 0.55, {"off_lo": off_lo}, "it is near its 52-week low")]
    if i_hi is not None or i_lo is not None:
        hi_side = i_hi is not None
        off = off_hi if hi_side else off_lo
        what = "high" if hi_side else "low"
        return [Fact("trend.range52", "Trend", "structure", 0, 0.0,
                     f"{pct(off)} from the 52-week {what} it set {x.on(i_hi if hi_side else i_lo)}",
                     f"Price set a new 52-week {what} {x.on(i_hi if hi_side else i_lo)} and has "
                     f"{'given back' if hi_side else 'come back'} {pct(off).lstrip('−+')} since.",
                     f"52-week range: {pct(off)} from the {what} it just set", "high52", 0.1,
                     {"off_hi": off_hi, "off_lo": off_lo})]
    where = (x.close - lo) / (hi - lo) if hi > lo else 0.5
    side = 1 if where >= 0.75 else -1 if where <= 0.25 else 0
    return [Fact("trend.range52", "Trend", "structure", side, 0.2 if side else 0.0,
                 f"{pct(off_hi)} from its 52-week high",
                 f"The 52-week low is {pct(off_lo).lstrip('+−')} under the price.",
                 f"52-week range: {pct(off_hi)} from the high", "high52", 0.1, {"off_hi": off_hi, "off_lo": off_lo},
                 f"it is {pct(off_hi).lstrip('−+')} below its 52-week high")]


def _adx(x):
    a, p, m = x.adx[0][-1], x.adx[1][-1], x.adx[2][-1]
    if a is None:
        return []
    if a >= 25:
        side = 1 if p > m else -1
        return [Fact("trend.adx", "Trend", "momentum", side, min(1.0, 0.3 + (a - 25) / 50),
                     f"Strong {'up' if side > 0 else 'down'}trend (ADX {a:.0f})",
                     f"Trend strength (ADX) reads {a:.0f}, above the 25 that marks a strong trend, with "
                     f"{'buyers' if side > 0 else 'sellers'} in control of the directional lines.",
                     f"ADX {a:.0f}: strong trend, {'up' if side > 0 else 'down'}", "adx", 0.2, {"adx": a},
                     f"the {'up' if side > 0 else 'down'}trend is strong (ADX {a:.0f})")]
    if a < 20:
        return [Fact("trend.adx", "Trend", "momentum", 0, 0.0, f"No strong trend (ADX {a:.0f})",
                     f"Trend strength (ADX) reads {a:.0f}, under 20: no strong trend either way.",
                     f"ADX {a:.0f}: no strong trend", "adx", 0.1, {"adx": a})]
    return [Fact("trend.adx", "Trend", "momentum", 0, 0.0, f"Moderate trend (ADX {a:.0f})",
                 f"Trend strength (ADX) reads {a:.0f}: a moderate trend.", f"ADX {a:.0f}: moderate", "adx", 0.0,
                 {"adx": a})]


def _quality(x):
    import math
    ys = [math.log(v) for v in x.c[-63:] if v > 0]
    if len(ys) < 40:
        return []
    b, r2 = ta.linreg(ys)
    line = (math.exp(b * (len(ys) - 1)) - 1.0) * 100.0            # the fitted line's change: the test
    ret = (x.c[-1] / x.c[-len(ys)] - 1.0) * 100.0             # the close's own change: the sentence (B's C2)
    if r2 >= 0.8 and abs(line) >= 8:
        side = 1 if b > 0 else -1
        moved = (f"{'climbed' if side > 0 else 'fallen'} {pct(ret, 0)}" if ret * side > 0 else
                 f"moved {pct(ret, 0)}")
        return [Fact("trend.quality", "Trend", "structure", side, 0.3,
                     f"A smooth, steady {'up' if side > 0 else 'down'}trend",
                     f"Over three months price has {moved} along a steady line (fit {r2:.2f} of 1): an orderly "
                     "trend, not a spike.",
                     f"Trend quality: steady ({r2:.2f} fit, {pct(ret, 0)} in 3 months)", "trend_quality", 0.45,
                     {"r2": r2, "ret": ret, "line": line},
                     f"it is in a smooth, steady {'up' if side > 0 else 'down'}trend")]
    return [Fact("trend.quality", "Trend", "structure", 0, 0.0, "An uneven path",
                 f"Over three months price has moved {pct(ret, 0)} on an uneven path (fit {r2:.2f} of 1).",
                 f"Trend quality: uneven ({r2:.2f} fit)", "trend_quality", 0.0, {"r2": r2, "ret": ret, "line": line})]


def _relative(x):
    """strength against the fund the name follows over three months, and whether the ratio is at a 52-week high"""
    ib = x.index_bars
    if not ib or not x.index_sym or x.index_sym == x.sym:
        return []
    ic = {ta.session_of(b): float(b["c"]) for b in ib}
    pairs = [(float(b["c"]), ic.get(ta.session_of(b))) for b in x.bars]
    pairs = [(a, b) for a, b in pairs if b]
    if len(pairs) < 70:
        return []
    ratio = [a / b for a, b in pairs]
    r63 = (ratio[-1] / ratio[-64] - 1.0) * 100.0
    yr = ratio[-252:]
    fund = x.index_sym
    if ratio[-1] >= max(yr) * 0.995 and r63 > 0:
        return [Fact("trend.rs", "Trend", "momentum", 1, 0.6, f"Leading {fund}",
                     f"Against {fund} it is {pct(r63, 0)} better over three months, and the "
                     "ratio of the two sits at a 52-week high: a leader.",
                     f"Relative strength vs {fund}: {pct(r63, 0)} in 3 months, a 52-week high", "relative_strength",
                     0.55, {"rs63": r63})]
    if ratio[-1] <= min(yr) * 1.005 and r63 < 0:
        return [Fact("trend.rs", "Trend", "momentum", -1, 0.6, f"Lagging {fund}",
                     f"Against {fund} it is {pct(r63, 0)} worse over three months, and the "
                     "ratio of the two sits at a 52-week low: a laggard.",
                     f"Relative strength vs {fund}: {pct(r63, 0)} in 3 months, a 52-week low", "relative_strength",
                     0.55, {"rs63": r63})]
    side = 1 if r63 >= 5 else -1 if r63 <= -5 else 0
    return [Fact("trend.rs", "Trend", "momentum", side, 0.3 if side else 0.0,
                 f"In step with {fund}" if abs(r63) < 2 else f"{'Ahead of' if r63 > 0 else 'Behind'} {fund}",
                 f"Against {fund} it is {pct(r63, 0)} over three months.",
                 f"Relative strength vs {fund}: {pct(r63, 0)} in 3 months", "relative_strength", 0.1, {"rs63": r63})]
