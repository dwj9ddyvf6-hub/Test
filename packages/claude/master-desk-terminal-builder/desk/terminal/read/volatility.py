"""Stretch and volatility: the daily range against the name's own year, a Bollinger squeeze, the distance from the
50-day average against its own year, and the quiet sessions that often come before a move."""
from . import ta
from .core import Fact, atr_words, pct


def facts(x):
    out = []
    if x.n < 130 or not x.atr:
        return out
    ap = x.atr / x.close * 100.0
    yr = [a / c * 100.0 for a, c in zip(x.atrs[-252:], x.c[-252:]) if a]
    rank = ta.pct_rank(yr, ap)
    out.append(Fact("vola.atr", "Volatility", "context", 0, 0.0, f"Daily range {ap:.1f}%",
                    f"Its average daily range (ATR) is {ap:.1f}% of price, "
                    + ("among the widest of its year." if rank >= 0.9 else "among the narrowest of its year."
                       if rank <= 0.1 else "normal for it."),
                    f"Average daily range: {ap:.1f}% ({'wide' if rank >= 0.9 else 'narrow' if rank <= 0.1 else 'normal'} "
                    "for its year)", "atr", 0.2 if rank >= 0.9 or rank <= 0.1 else 0.0, {"atr_pct": ap, "rank": rank}))
    wd = x.bb[3]
    w = [v for v in wd[-126:] if v is not None]
    if wd[-1] is not None and len(w) > 60:
        r = ta.pct_rank(w, wd[-1])
        if r <= 0.1:
            least = wd[-1] <= min(w)                    # "the tightest" only when it is (audit B's C3)
            where = "the tightest in six months" if least else "among the tightest tenth of six months"
            out.append(Fact("vola.squeeze", "Volatility", "context", 0, 0.0, "A volatility squeeze",
                            f"Its Bollinger Bands are {where}: quiet like this often comes before a large move.",
                            f"Bollinger width: {where.replace('the tightest', 'tightest')} (squeeze)", "squeeze", 0.65,
                            {"rank": r, "least": least}))
        else:
            out.append(Fact("vola.squeeze", "Volatility", "context", 0, 0.0, "No squeeze",
                            f"Its Bollinger Band width ranks in the {int(r * 100)}th percentile of six months.",
                            f"Bollinger width: {int(r * 100)}th percentile of 6 months", "bollinger", 0.0, {"rank": r}))
    m50 = x.sma50[-1]
    if m50:
        d = (x.close - m50) / x.atr
        hist = [(c - m) / a for c, m, a in zip(x.c[-252:], x.sma50[-252:], x.atrs[-252:]) if m and a]
        r = ta.pct_rank([abs(h) for h in hist], abs(d))
        if r >= 0.9 and abs(d) >= 2.5:
            side = -1 if d > 0 else 1
            out.append(Fact("vola.stretch", "Volatility", "momentum", side, 0.35,
                            "Stretched above its 50-day" if d > 0 else "Stretched below its 50-day",
                            f"{atr_words(d)} {'over' if d > 0 else 'under'} the 50-day average "
                            f"({pct((x.close / m50 - 1.0) * 100.0)} away), among its widest gaps of the year.",
                            f"Distance from the 50-day: {atr_words(d)} {'above' if d > 0 else 'below'} (top decile)",
                            "stretch", 0.5, {"d50_atr": d}))
        else:
            out.append(Fact("vola.stretch", "Volatility", "momentum", 0, 0.0,
                            f"{atr_words(d)} {'above' if d >= 0 else 'below'} its 50-day",
                            f"Price is {atr_words(d)} {'above' if d >= 0 else 'below'} its 50-day average.",
                            f"Distance from the 50-day: {atr_words(d)} {'above' if d >= 0 else 'below'}", "stretch", 0.0,
                            {"d50_atr": d}))
    rng = [float(b["h"]) - float(b["l"]) for b in x.bars[-7:]]
    if len(rng) == 7 and rng[-1] == min(rng):
        b, p = x.bars[-1], x.bars[-2]
        inside = float(b["h"]) <= float(p["h"]) and float(b["l"]) >= float(p["l"])
        out.append(Fact("vola.nr7", "Volatility", "context", 0, 0.0,
                        "The quietest session in seven" + (", inside the day before" if inside else ""),
                        f"{x.on(x.n - 1, cap=True)} it had the narrowest range of the last seven sessions"
                        + (", inside the session before" if inside else "") + ": a coiled spring.",
                        f"{x.when(x.n - 1)}: narrowest range in 7" + (" (inside day)" if inside else ""), "nr7", 0.35))
    return out
