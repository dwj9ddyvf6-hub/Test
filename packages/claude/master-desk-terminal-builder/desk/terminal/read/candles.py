"""Candles and gaps in the last few sessions, read where they happen: a hammer on a floor or an engulfing day at a
ceiling means more than the same candle in the middle of nowhere. Gaps are typed by where they happen too:
breakaway (out of a base, on volume), runaway (mid-trend, with it), exhaustion (late in a run, then reversed)."""
from . import candlesticks
from . import words as W
from .core import Fact, pct

NEAR_ATR = 0.6           # a candle "at" a level: within 0.6 ATR of a floor or ceiling of two or more kinds
PRIOR_ATR = 1.0          # the move a reversal candle reverses: the ten sessions before it, an ATR or more


def _parts(b):
    o, h, l, c = float(b["o"]), float(b["h"]), float(b["l"]), float(b["c"])
    rng = max(h - l, 1e-12)
    return o, h, l, c, rng, abs(c - o), h - max(o, c), min(o, c) - l


def _at_level(x, price, below=True):
    """a floor (below) or ceiling of two or more kinds near `price`; a level the last session printed itself (its own
    new high) does not count (the audit's B-H8)"""
    from .levels import Area
    for a in x.areas:
        if any(m.i == x.n - 1 for m in a.members):
            rest = [m for m in a.members if m.i != x.n - 1]
            if not rest:
                continue
            a = Area(rest, x.bars, x.atr)
        if a.confluence < 2 and a.weight < 1.5:
            continue
        if abs(a.price - price) <= NEAR_ATR * x.atr and ((a.price <= x.close) if below else (a.price >= x.close)):
            return a
    return None


def facts(x):
    out = []
    if x.n < 30 or not x.atr:
        return out
    b, p = x.bars[-1], x.bars[-2]
    o, h, l, c, rng, body, up_w, lo_w = _parts(b)
    po, ph, pl, pc, prng, pbody, _, _ = _parts(p)
    floor, ceil = _at_level(x, l, True), _at_level(x, h, False)
    where_f = " at a support area" if floor else ""
    where_c = " at a resistance area" if ceil else ""
    # a reversal candle reverses the move before it (the audit's B-H3): the ten sessions before, in ATR
    before = (x.c[-2] - x.c[-12]) / x.atr if x.n >= 12 else 0.0
    fell, rose = before <= -PRIOR_ATR, before >= PRIOR_ATR
    when = x.on(x.n - 1, cap=True)
    if lo_w >= 2 * body and lo_w >= 0.6 * rng and up_w <= 0.25 * rng and (fell or rose):
        if fell:
            out.append(Fact("candle.hammer", "Candles", "structure", 1, 0.45 if floor else 0.25, "A hammer" + where_f,
                            f"{when} it dipped and closed near its high, leaving a long lower wick: buyers "
                            "rejected the lows after a decline.",
                            f"Candle {x.when(x.n - 1)}: hammer" + (f" ({where_f.strip()[3:]})" if floor else ""),
                            "hammer", 0.45 if floor else 0.25))
        else:
            out.append(Fact("candle.hammer", "Candles", "structure", 0, 0.0, "A hanging man",
                            f"{when} it dipped and closed near its high after a rise, leaving a long lower wick: the "
                            "shape of a hammer at the top of a move, a hanging man, which needs a lower close to mean "
                            "anything.", f"Candle {x.when(x.n - 1)}: hanging man", "hammer", 0.1))
    elif up_w >= 2 * body and up_w >= 0.6 * rng and lo_w <= 0.25 * rng and (fell or rose):
        if rose:
            out.append(Fact("candle.star", "Candles", "structure", -1, 0.45 if ceil else 0.25,
                            "A shooting star" + where_c,
                            f"{when} it rallied and closed near its low, leaving a long upper wick: sellers "
                            "rejected the highs after a rise.",
                            f"Candle {x.when(x.n - 1)}: shooting star" + (f" ({where_c.strip()[3:]})" if ceil else ""),
                            "shooting_star", 0.45 if ceil else 0.25, wrong=(h, "the star's high")))
        else:
            out.append(Fact("candle.star", "Candles", "structure", 0, 0.0, "An inverted hammer",
                            f"{when} it rallied and closed near its low after a decline, leaving a long upper wick: an "
                            "inverted hammer, which needs a higher close to mean anything.",
                            f"Candle {x.when(x.n - 1)}: inverted hammer", "shooting_star", 0.1))
    real = pbody >= 0.25 * prng                          # a body to engulf, not a doji's (B-M2)
    if c > o and pc < po and c >= po and o <= pc and body > pbody and real and fell:
        out.append(Fact("candle.engulf", "Candles", "structure", 1, 0.45 if floor else 0.3, "A bullish engulfing day" + where_f,
                        f"{x.on(x.n - 1, cap=True)} it opened under the prior close and closed above the prior open: "
                        "buyers took the day back in full.", f"Candles {x.when(x.n - 2)}–{x.when(x.n - 1)}: bullish engulfing"
                        + (f" ({where_f.strip()[3:]})" if floor else ""), "engulfing",
                        0.45))
    elif c < o and pc > po and c <= po and o >= pc and body > pbody and real and rose:
        out.append(Fact("candle.engulf", "Candles", "structure", -1, 0.45 if ceil else 0.3, "A bearish engulfing day" + where_c,
                        f"{x.on(x.n - 1, cap=True)} it opened over the prior close and closed under the prior open: "
                        "sellers took the day back in full.", f"Candles {x.when(x.n - 2)}–{x.when(x.n - 1)}: bearish engulfing"
                        + (f" ({where_c.strip()[3:]})" if ceil else ""),
                        "engulfing", 0.45, wrong=(h, "the engulfing day's high")))
    if h > ph and l < pl and rng >= 1.3 * x.atr:
        if c >= h - 0.2 * rng and c > pc:
            out.append(Fact("candle.outside", "Candles", "structure", 1, 0.4, "An outside reversal up",
                            f"{x.on(x.n - 1, cap=True)} it traded below the prior low and above the prior high, then closed near "
                            "its top: a key reversal.", f"Candle {x.when(x.n - 1)}: outside reversal up", "outside_day", 0.5))
        elif c <= l + 0.2 * rng and c < pc:
            out.append(Fact("candle.outside", "Candles", "structure", -1, 0.4, "An outside reversal down",
                            f"{x.on(x.n - 1, cap=True)} it traded above the prior high and below the prior low, then closed near "
                            "its bottom: a key reversal.", f"Candle {x.when(x.n - 1)}: outside reversal down", "outside_day", 0.5,
                            wrong=(h, "the reversal day's high")))
    if rng >= 1.8 * x.atr and body >= 0.7 * rng:
        side = 1 if c > o else -1
        out.append(Fact("candle.wide", "Candles", "structure", side, 0.35,
                        "A wide-range day " + ("up" if side > 0 else "down"),
                        f"{x.on(x.n - 1, cap=True)} it covered {rng / x.atr:.1f}x a normal day's range and closed near its "
                        f"{'high' if side > 0 else 'low'}: a decisive day.",
                        f"Candle {x.when(x.n - 1)}: wide-range {'up' if side > 0 else 'down'} day ({rng / x.atr:.1f} ATR)", "wide_range",
                        0.45, wrong=(h, "the wide day's high") if side < 0 else None))
    if body <= 0.1 * rng and (floor or ceil):
        out.append(Fact("candle.doji", "Candles", "structure", 0, 0.0, "Indecision at a level",
                        f"{x.on(x.n - 1, cap=True)} it closed almost where it opened, at a level: buyers and sellers are even.",
                        f"Candle {x.when(x.n - 1)}: doji at a level", "doji", 0.25))
    out += _gaps(x)
    out += candlesticks.facts(x, out)          # the study's 62 named patterns, on levels, once per session
    if not [f for f in out if f.family == "Candles"]:
        cl = (c - l) / rng
        out.append(Fact("candle.close", "Candles", "structure", 0, 0.0,
                        "Closed " + ("near the high" if cl >= 0.75 else "near the low" if cl <= 0.25 else "mid-range"),
                        f"{x.on(x.n - 1, cap=True)} it closed in the {'top' if cl >= 0.75 else 'bottom' if cl <= 0.25 else 'middle'} "
                        "of its range.", f"Candle {x.when(x.n - 1)}: no pattern", "candles", 0.0, {"close_loc": cl}))
    return out


def _gaps(x):
    """the most recent gap of at least half an ATR in the last ten sessions, typed"""
    for i in range(x.n - 1, max(x.n - 11, 30), -1):
        b, p = x.bars[i], x.bars[i - 1]
        a = x.atrs[i - 1] or x.atr
        up = float(b["l"]) > float(p["h"]) and (float(b["l"]) - float(p["h"])) >= 0.5 * a
        dn = float(b["h"]) < float(p["l"]) and (float(p["l"]) - float(b["h"])) >= 0.5 * a
        if not (up or dn):
            continue
        side = 1 if up else -1
        size = (float(b["o"]) / float(p["c"]) - 1.0) * 100.0
        rv = x.vol[i] / (x.vol50[i - 1] or x.vol50[-1] or 1)
        after = x.bars[i + 1:]
        filled = any(float(q["l"]) <= float(p["h"]) for q in after) if up else \
            any(float(q["h"]) >= float(p["l"]) for q in after)
        prior = x.c[max(0, i - 40):i]
        run = (x.c[i - 1] / min(prior) - 1.0) * 100.0 if up else (x.c[i - 1] / max(prior) - 1.0) * 100.0
        base = max(prior[-20:]) / min(prior[-20:]) - 1.0 if len(prior) >= 20 else 1.0
        trend = 1 if x.c[i - 1] > x.c[max(0, i - 21)] else -1
        held = not filled
        ago = x.n - 1 - i
        day = x.on(i)
        if base <= 0.12 and rv >= 1.5 and held:
            kind, learn, st, rar = "breakaway", "gap_breakaway", 0.6, 0.6
            words = f"it gapped {'up out of' if up else 'down out of'} a tight range on {rv:.1f}x volume and has held"
        elif filled and abs(run) >= 25:
            kind, learn, st, rar, side = "exhaustion", "gap_exhaustion", 0.45, 0.55, -side
            words = (f"after a {pct(run, 0)} run it gapped {'up' if up else 'down'} and then filled the gap: a "
                     "sign the run is spent")
        elif held and trend == side:
            kind, learn, st, rar = "runaway", "gap_runaway", 0.35, 0.35
            words = f"it gapped {'up' if up else 'down'} with the trend and has not looked back"
        elif held:
            kind, learn, st, rar = "open", "gap", 0.35, 0.3
            words = (f"it gapped {'up' if up else 'down'} against the trend and has not filled the gap: "
                     f"{'buyers' if up else 'sellers'} still hold it")
        else:
            kind, learn, st, rar, side = "common", "gap", 0.0, 0.0, 0
            words = f"it gapped {'up' if up else 'down'} and has since filled the gap"
        return [Fact(f"gap.{kind}", "Gaps", "structure", side, st,
                     (W.a(f"{kind} gap {'up' if up else 'down'}").capitalize() if kind not in ("common", "open") else
                      "A filled gap" if kind == "common" else f"An open gap {'up' if up else 'down'}"),
                     f"{x.on(i, cap=True)} {words} ({pct(size)} at the open).",
                     f"Gap: {kind} {'up' if up else 'down'} {day} ({pct(size)})", learn, rar,
                     {"kind": kind, "ago": ago, "size": size, "rv": rv},
                     wrong=(float(p["l"]), "the top of the gap") if side < 0 and dn and held else None)]
    return []
