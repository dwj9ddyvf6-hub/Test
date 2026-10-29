"""Momentum: RSI's level and the range it has held, MACD against its signal line and zero, the stochastic leaving an
extreme, and divergences between price and seven momentum gauges, daily and weekly."""
from .core import Fact

JUST = 1                          # "just turned": a cross this session or the one before (it fired on 39% of reads
                                  # at six sessions)

_DIV = {"regular bullish": ("Selling is losing force", "lower low", "higher low", "divergence_regular_bull"),
        "hidden bullish": ("Buyers stepping in earlier", "higher low", "lower low", "divergence_hidden_bull"),
        "regular bearish": ("Buying is losing force", "higher high", "lower high", "divergence_regular_bear"),
        "hidden bearish": ("Sellers stepping in earlier", "lower high", "higher high", "divergence_hidden_bear")}


def _names(gs):
    gs = list(gs)
    return gs[0] if len(gs) == 1 else ", ".join(gs[:-1]) + " and " + gs[-1]


def facts(x):
    out = []
    r = x.rsi[-1]
    if r is not None:
        w = [v for v in x.rsi[-63:] if v is not None]
        lo, hi = min(w), max(w)
        bear_range = hi <= 62 and lo <= 32
        if lo >= 38 and hi >= 68:
            out.append(Fact("mom.rsi_range", "Momentum", "momentum", 1, 0.5, "Momentum holding a bull range",
                            f"RSI has stayed above {lo:.0f} on every dip for three months and reached {hi:.0f}: the "
                            "range momentum holds in an uptrend.", f"RSI range 3 months: {lo:.0f} to {hi:.0f} (bull range)",
                            "rsi_range", 0.4, {"lo": lo, "hi": hi},
                            "momentum holds a bull range"))
        elif bear_range:
            out.append(Fact("mom.rsi_range", "Momentum", "momentum", -1, 0.5, "Momentum stuck in a bear range",
                            f"RSI has failed below {hi:.0f} on every bounce for three months and fell to {lo:.0f}: the "
                            "range momentum holds in a downtrend.", f"RSI range 3 months: {lo:.0f} to {hi:.0f} (bear range)",
                            "rsi_range", 0.4, {"lo": lo, "hi": hi},
                            "momentum is stuck in a bear range"))
        if r >= 70:
            out.append(Fact("mom.rsi", "Momentum", "momentum", 0, 0.0, f"Stretched (RSI {r:.0f})",
                            f"RSI reads {r:.0f}, above 70: strong, and stretched for a fresh entry.",
                            f"RSI {r:.0f}: stretched", "rsi", 0.3, {"rsi": r}))
        elif r <= 30:
            # oversold is a buyer's dip only inside an uptrend: price over a rising 200-day. In a falling trend it is
            # the trend's own momentum, which the bear range reads against from the same low (145 reads on
            # 2026-10-16 counted it both ways)
            m, m_ago = x.sma200[-1], x.sma200[-21] if len(x.sma200) > 21 else None
            dip = m is not None and m_ago is not None and x.close > m > m_ago and not bear_range
            if dip:
                out.append(Fact("mom.rsi", "Momentum", "momentum", 1, 0.25, f"Oversold in an uptrend (RSI {r:.0f})",
                                f"RSI reads {r:.0f}, under 30, while price holds above its rising 200-day average: "
                                "a deep dip in an uptrend.", f"RSI {r:.0f}: oversold, above a rising 200-day",
                                "rsi", 0.35, {"rsi": r}, "it is oversold inside an uptrend"))
            else:
                out.append(Fact("mom.rsi", "Momentum", "momentum", 0, 0.0, f"Oversold (RSI {r:.0f})",
                                f"RSI reads {r:.0f}, under 30: sellers have pushed hard.", f"RSI {r:.0f}: oversold",
                                "rsi", 0.2, {"rsi": r}))
        else:
            out.append(Fact("mom.rsi", "Momentum", "momentum", 0, 0.0, f"RSI {r:.0f}",
                            f"RSI reads {r:.0f}, between the extremes.", f"RSI {r:.0f}: neutral", "rsi", 0.0, {"rsi": r}))
    out += _macd(x)
    out += _stoch(x)
    for d in x.divs:
        out.append(_div(x, d, "daily"))
    for d in x.wdivs:
        out.append(_div(x, d, "weekly"))
    return out


def _macd(x):
    line, sig, hist = x.macd
    if line[-1] is None or sig[-1] is None:
        return []
    above, zero = line[-1] > sig[-1], line[-1] > 0
    age = 0
    for i in range(len(line) - 1, 0, -1):
        if line[i - 1] is None or sig[i - 1] is None or (line[i - 1] > sig[i - 1]) != above:
            break
        age += 1
    rising = hist[-1] is not None and hist[-2] is not None and hist[-1] > hist[-2]
    where = "above zero" if zero else "below zero"
    if age <= JUST:                               # this session's cross or the last one's (the audit's B-H7)
        side = 1 if above else -1
        return [Fact("mom.macd", "Momentum", "momentum", side, 0.55,
                     f"MACD just turned {'up' if above else 'down'}",
                     f"MACD crossed {'above' if above else 'below'} its signal line {x.on(x.n - 1 - age)}, {where}"
                     + (": an early turn." if above != zero else ": momentum renewing in the trend's direction."),
                     f"MACD: crossed {'above' if above else 'below'} its signal {x.on(x.n - 1 - age)}, {where}",
                     "macd", 0.45, {"age": age + 1, "above": above, "zero": zero})]
    side = 1 if above and zero else -1 if not above and not zero else 0
    state = ("above its signal line and above zero" if side > 0 else
             "below its signal line and below zero" if side < 0 else
             f"{'above' if above else 'below'} its signal line, {where}")
    return [Fact("mom.macd", "Momentum", "momentum", side, 0.3 if side else 0.0,
                 "MACD " + ("positive" if side > 0 else "negative" if side < 0 else "turning"),
                 f"MACD is {state}, with the histogram {'rising' if rising else 'falling'}.",
                 f"MACD: {where}, {'above' if above else 'below'} its signal", "macd", 0.05,
                 {"above": above, "zero": zero, "rising": rising},
                 "MACD is positive" if side > 0 else "MACD is negative" if side < 0 else "")]


def _stoch(x):
    from . import ta
    k = ta.stochastic(x.bars)
    if k[-1] is None or k[-2] is None:
        return []
    if k[-2] < 20 <= k[-1]:
        return [Fact("mom.stoch", "Momentum", "momentum", 1, 0.3, "Stochastic leaving oversold",
                     f"The stochastic rose back above 20 (to {k[-1]:.0f}) {x.on(x.n - 1)}: selling pressure easing.",
                     f"Stochastic {k[-1]:.0f}: crossing up out of oversold", "stochastic", 0.35, {"k": k[-1]},
                     "the stochastic is leaving oversold")]
    if k[-2] > 80 >= k[-1]:
        return [Fact("mom.stoch", "Momentum", "momentum", -1, 0.3, "Stochastic leaving overbought",
                     f"The stochastic fell back below 80 (to {k[-1]:.0f}) {x.on(x.n - 1)}: buying pressure easing.",
                     f"Stochastic {k[-1]:.0f}: crossing down out of overbought", "stochastic", 0.35, {"k": k[-1]},
                     "the stochastic is leaving overbought")]
    return [Fact("mom.stoch", "Momentum", "momentum", 0, 0.0, f"Stochastic {k[-1]:.0f}",
                 f"The stochastic reads {k[-1]:.0f}.", f"Stochastic {k[-1]:.0f}", "stochastic", 0.0, {"k": k[-1]})]


def _div(x, d, frame):
    head, p_word, g_word, learn = _DIV[d.kind]
    weekly = frame == "weekly"
    bars = x.weekly if weekly else x.bars
    from .levels import when
    n = len(d.gauges)
    strength = min(1.0, (0.45 if "hidden" in d.kind else 0.4) + 0.08 * (n - 1)) * (1.15 if weekly else 1.0)
    gauges = _names(d.gauges) if n <= 3 else f"momentum ({n} of 7 gauges)"
    return Fact(f"div.{d.kind.replace(' ', '_')}.{frame}", "Divergence", "momentum", d.side, min(1.0, strength),
                head + (" (weekly)" if weekly else ""),
                f"{'Weekly: a' if weekly else 'A'} {p_word} in price ({'the week of ' if weekly else ''}"
                f"{when(bars, d.i1)}) against a {g_word} in {gauges}: {d.kind} divergence.",
                f"{d.kind.capitalize()} divergence, {frame}: {n} of 7 gauges", learn,
                0.5 + 0.05 * n + (0.1 if weekly else 0.0), {"gauges": list(d.gauges), "frame": frame})
