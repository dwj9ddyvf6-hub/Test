"""Volume: who is in control (up-day against down-day volume), accumulation and distribution days, the volume on
the current pullback or bounce, the last session's volume, and on-balance volume leading or lagging price."""
import math

from . import ta
from .core import Fact, pct


def facts(x):
    out = []
    b, v, c = x.bars, x.vol, x.c
    if x.n < 60 or not x.vol50[-1]:
        return out
    # per day, not in total: more up days than down is the trend, not who controls the volume (the audit's B-H5)
    ups = [v[i] for i in range(x.n - 50, x.n) if c[i] > c[i - 1]]
    dns = [v[i] for i in range(x.n - 50, x.n) if c[i] < c[i - 1]]
    if ups and dns and sum(ups) > 0 and sum(dns) > 0:
        ud = (sum(ups) / len(ups)) / (sum(dns) / len(dns))
        side = 1 if ud >= 1.25 else -1 if ud <= 0.8 else 0
        out.append(Fact("vol.updown", "Volume", "volume", side, min(0.6, abs(math.log(ud))) if side else 0.0,
                        "Buyers control the volume" if side > 0 else "Sellers control the volume" if side < 0 else
                        "Volume evenly split",
                        f"Over ten weeks, an up day traded {ud:.1f}x the volume of a down day.",
                        f"Up/down volume per day (10 weeks): {ud:.1f}x", "updown_volume", 0.25 if side else 0.0,
                        {"ratio": ud},
                        "buyers control the volume" if side > 0 else "sellers control the volume" if side < 0 else ""))
    acc = dist = 0
    for i in range(x.n - 25, x.n):
        if v[i] > v[i - 1] and v[i] > (x.vol50[i] or 0):
            if c[i] > c[i - 1] * 1.002:
                acc += 1
            elif c[i] < c[i - 1] * 0.998:
                dist += 1
    if acc or dist:
        side = 1 if acc >= dist + 3 else -1 if dist >= acc + 3 else 0
        out.append(Fact("vol.accdist", "Volume", "volume", side, 0.35 if side else 0.0,
                        "Accumulation" if side > 0 else "Distribution" if side < 0 else "No clear accumulation",
                        f"In five weeks it had {acc} up day{'s' if acc != 1 else ''} and {dist} down "
                        f"day{'s' if dist != 1 else ''} on volume above both the day before and its average.",
                        f"Accumulation {acc}, distribution {dist} (5 weeks)",
                        "accumulation", 0.3 if side else 0.0, {"acc": acc, "dist": dist},
                        "big buyers have been accumulating" if side > 0 else
                        "heavy-volume selling outnumbers buying (distribution)" if side < 0 else ""))
    out += _leg(x)
    rv = v[-1] / x.vol50[-1]
    chg = (c[-1] / c[-2] - 1.0) * 100.0
    atr_move = (c[-1] - c[-2]) / (x.atrs[-2] or x.atr)
    if rv >= 1.8 and abs(atr_move) >= 1.0:
        side = 1 if chg > 0 else -1
        out.append(Fact("vol.last", "Volume", "volume", side, min(0.8, 0.3 + 0.15 * rv),
                        f"Heavy {'buying' if side > 0 else 'selling'} {x.on(x.n - 1)}",
                        f"{x.on(x.n - 1, cap=True)} it moved {pct(chg)} on {rv:.1f}x its average volume.",
                        f"{x.when(x.n - 1)}: {pct(chg)} on {rv:.1f}x volume", "relative_volume", 0.5,
                        {"rv": rv, "chg": chg}, f"it saw heavy {'buying' if side > 0 else 'selling'} {x.on(x.n - 1)}"))
    else:
        out.append(Fact("vol.last", "Volume", "volume", 0, 0.0, f"{x.when(x.n - 1)} on {rv:.1f}x volume",
                        f"{x.on(x.n - 1, cap=True)} it moved {pct(chg)} on {rv:.1f}x its average volume.",
                        f"{x.when(x.n - 1)}: {pct(chg)} on {rv:.1f}x volume", "relative_volume", 0.0,
                        {"rv": rv, "chg": chg}))
    ob = ta.obv(b)
    yr_o, yr_c = ob[-252:], c[-252:]
    if len(yr_o) >= 200:
        if ob[-1] >= max(yr_o) and c[-1] < max(yr_c) * 0.97:
            out.append(Fact("vol.obv", "Volume", "volume", 1, 0.55, "Volume leads price higher",
                            "On-balance volume is at a 52-week high while price is still under its own: buying is "
                            "running ahead of price.", "On-balance volume: at a 52-week high, ahead of price", "obv",
                            0.6))
        elif ob[-1] <= min(yr_o) and c[-1] > min(yr_c) * 1.03:
            out.append(Fact("vol.obv", "Volume", "volume", -1, 0.55, "Volume leads price lower",
                            "On-balance volume is at a 52-week low while price is still above its own: selling is "
                            "running ahead of price.", "On-balance volume: at a 52-week low, ahead of price", "obv", 0.6))
    return out


def _leg(x):
    """the volume of the swing in progress against the 50-day average: a quiet pullback is profit-taking, a heavy
    one is selling"""
    piv = x.minor
    if len(piv) < 2:
        return []
    last = piv[-1]
    start = piv[-2].i + 1 if last.confirmed is False else last.i + 1
    seg = x.vol[start:]
    if len(seg) < 3:
        return []
    avg = sum(seg) / len(seg)
    base = x.vol50[start - 1] or x.vol50[-1]
    if not base:
        return []
    r = avg / base
    pulling_back = last.kind == "L"                    # the swing in progress is down: a pullback (or a bounce if up)
    if pulling_back:
        if r <= 0.85:
            return [Fact("vol.leg", "Volume", "volume", 1, 0.45, "Quiet selling on the dip",
                         f"Volume on the current pullback runs {(1 - r) * 100:.0f}% below its 50-day average: "
                         "profit-taking, not an exit.", f"Pullback volume: {r:.2f}x average", "pullback_volume", 0.45,
                         {"ratio": r}, "selling on the dip is light")]
        if r >= 1.25:
            return [Fact("vol.leg", "Volume", "volume", -1, 0.45, "Heavy selling on the dip",
                         f"Volume on the current pullback runs {(r - 1) * 100:.0f}% above its 50-day average: "
                         "sellers are leaving in size.", f"Pullback volume: {r:.2f}x average", "pullback_volume", 0.45,
                         {"ratio": r}, "the dip is coming on heavy selling")]
    else:
        if r >= 1.25:
            return [Fact("vol.leg", "Volume", "volume", 1, 0.4, "Heavy buying on the rise",
                         f"Volume on the current rise runs {(r - 1) * 100:.0f}% above its 50-day average.",
                         f"Rally volume: {r:.2f}x average", "rally_volume", 0.35, {"ratio": r},
                         "the rise is coming on heavy buying")]
        if r <= 0.8:
            return [Fact("vol.leg", "Volume", "volume", -1, 0.3, "A thin rise",
                         f"Volume on the current rise runs {(1 - r) * 100:.0f}% below its 50-day average: few "
                         "buyers behind it.", f"Rally volume: {r:.2f}x average", "rally_volume", 0.3, {"ratio": r})]
    return [Fact("vol.leg", "Volume", "volume", 0, 0.0, "Ordinary volume on the swing",
                 f"Volume on the current {'pullback' if pulling_back else 'rise'} is near its 50-day average "
                 f"({r:.2f}x).", f"{'Pullback' if pulling_back else 'Rally'} volume: {r:.2f}x average",
                 "pullback_volume" if pulling_back else "rally_volume", 0.0, {"ratio": r})]
