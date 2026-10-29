"""Every word the page shows about a read: the glossary (one teaching line per idea, the same line on a card and in
How it works) and the sentences of a call. Sentences are composed from measured numbers only; nothing here decides
anything, and nothing reads a sentence back."""
from datetime import date, datetime

GLOSSARY = {
    "averages_up": ("Rising averages", "Both averages rising with price over them: the long trend points up."),
    "averages_down": ("Falling averages", "Both averages falling with price under them: the long trend points down."),
    "swings_up": ("Rising swings", "Rising swing highs and lows are the steps of an uptrend."),
    "swings_down": ("Falling swings", "Falling swing highs and lows are the steps of a downtrend."),
    "pullback": ("Pullback", "A dip inside an uptrend; buyers often return at support."),
    "bounce": ("Bounce", "A rise inside a downtrend; sellers often return at resistance."),
    "range": ("Range", "Price moving sideways between a floor and a ceiling."),
    "moving_average": ("Moving average", "The average close of the last 20, 50 or 200 sessions; rising averages "
                                         "mark uptrends and often act as support."),
    "stage": ("Weinstein stage", "Stocks cycle through basing, advancing, topping and declining; longs pay in the "
                                 "advancing stage."),
    "high52": ("52-week high", "The highest price of the past year; above it, no one who bought in the last year "
                               "is waiting to sell at breakeven."),
    "low52": ("52-week low", "The lowest price of the past year."),
    "adx": ("ADX", "A 0-100 gauge of trend strength, not direction; above 25 is a strong trend."),
    "trend_quality": ("Trend quality", "How closely price has tracked a straight line; steady trends tend to "
                                       "persist, spikes tend to fade."),
    "relative_strength": ("Relative strength", "How the stock has done against its fund (QQQ for tech, chips and "
                                               "internet names, SPY for the rest); leaders lead."),
    "swing_break": ("Broken structure", "An uptrend's first crack: a close under its latest higher low."),
    "swing_break_up": ("Broken downtrend", "A downtrend's first crack: a close over its latest lower high."),
    "wave2": ("Wave 2", "After five waves up the pullback usually ends between the 0.618 and 0.786 retracement of the "
                        "advance; a close turning up there is the buy."),
    "trigger_failed": ("A trigger that failed before", "A line price closed above and then gave back has failed "
                                                         "once already; the next break has to hold to count."),
    "wave4": ("Wave 4", "Wave 4 usually pulls back to the 0.382–0.5 retracement of wave 3 and holds above wave 1's "
                        "top; the buy comes when price turns up there."),
    "wave_five": ("The end of wave 5", "A fifth wave that peaks with fading momentum often ends the advance; the next "
                                       "buy is the pullback after it, not the high."),
    "wave_trap": ("A pullback that is not done", "A real wave 2 takes three waves and time, on lighter volume. Too "
                                                 "shallow, too quick, one straight leg or rising selling says it has "
                                                 "further to go."),
    "stack": ("Stacked levels", "Different kinds of support at one price (a swing low, an average, a retracement) "
                                "make a stronger floor than any one alone."),
    "support": ("Support", "A price where buyers stepped in before."),
    "resistance": ("Resistance", "A ceiling: sellers stepped in there before."),
    "retest": ("Retest", "After a breakout, price often comes back to the line it broke; old resistance becomes "
                         "new support."),
    "fibonacci": ("Fibonacci retracement", "Pullbacks often stop near 38%, 50% or 62% of the move before; past 62% "
                                           "the move itself is in doubt."),
    "rsi": ("RSI", "A 0-100 gauge of recent gains against losses; above 70 is stretched, under 30 is oversold."),
    "rsi_range": ("RSI range", "In uptrends RSI tends to hold 40 on dips and reach 70; in downtrends it fails near "
                               "60 and reaches 30."),
    "macd": ("MACD", "The gap between a fast and a slow average of price; a cross up through its signal says "
                     "momentum is turning."),
    "stochastic": ("Stochastic", "Where the close sits in the recent range, 0-100; leaving 20 or 80 marks a turn."),
    "divergence_regular_bull": ("Bullish divergence", "Lower price lows with rising momentum lows: sellers are "
                                                      "tiring."),
    "divergence_hidden_bull": ("Hidden bullish divergence", "Higher price lows while momentum sets lower lows: buyers "
                                                            "stepped in earlier, a common sign the uptrend resumes."),
    "divergence_regular_bear": ("Bearish divergence", "Higher price highs with falling momentum highs: buyers are "
                                                      "tiring."),
    "divergence_hidden_bear": ("Hidden bearish divergence", "Lower price highs while momentum sets higher highs: "
                                                            "sellers stepped in earlier; the downtrend often "
                                                            "resumes."),
    "updown_volume": ("Up/down volume", "Volume on up days against volume on down days; above 1 means buyers trade "
                                        "more."),
    "accumulation": ("Accumulation", "Up days on heavy volume mean institutions are buying; heavy down days "
                                     "(distribution) mean they are selling."),
    "pullback_volume": ("Pullback volume", "A dip on light volume is profit-taking; a dip on heavy volume is "
                                           "selling."),
    "rally_volume": ("Rally volume", "A rise on heavy volume has buyers behind it; a thin rise often fades."),
    "relative_volume": ("Relative volume", "A session's volume against its 50-day average; big moves on heavy "
                                           "volume carry more weight."),
    "obv": ("On-balance volume", "A running total of volume on up days minus down days; when it leads price, "
                                 "price tends to follow."),
    "atr": ("ATR", "Average true range: the stock's typical daily move. Plans set their lines in ATR so a calm "
                   "stock and a wild one are judged alike."),
    "squeeze": ("Squeeze", "Unusually narrow Bollinger Bands; quiet stretches tend to end in a large move."),
    "bollinger": ("Bollinger Bands", "Bands two standard deviations around the 20-day average; their width measures "
                                     "volatility."),
    "stretch": ("Stretch", "How far price sits from its 50-day average in ATR; far stretches tend to pause or "
                           "snap back."),
    "nr7": ("Narrow range", "The quietest session in seven; a coiled spring."),
    "hammer": ("Hammer", "A dip the close bought back: a small body over a tall lower shadow."),
    "shooting_star": ("Shooting star", "A rally the close gave back: a small body under a tall upper shadow."),
    "engulfing": ("Engulfing day", "A session whose body swallows the one before: one side has taken over."),
    "outside_day": ("Outside reversal", "A session that trades beyond both ends of the prior day's range and closes "
                                        "at an extreme."),
    "wide_range": ("Wide-range day", "A session far larger than normal that closes at its extreme: a decisive day."),
    "doji": ("Doji", "Open and close nearly equal: indecision."),
    "candles": ("Candles", "Each session's open, high, low and close drawn as one bar."),
    "gap": ("Gap", "A session that opens beyond the prior session's range; an open gap often gets filled later."),
    "gap_breakaway": ("Breakaway gap", "A gap out of a range on heavy volume that holds: the start of a move."),
    "gap_runaway": ("Runaway gap", "A gap in the middle of a trend, with it: the move is accelerating."),
    "gap_exhaustion": ("Exhaustion gap", "A gap late in a long run that quickly fills: the end of the move."),
    "base": ("Base", "A sideways range after a move, where the stock rests before its next leg."),
    "breakout": ("Breakout", "A close above a ceiling that capped price before; strongest on heavy volume."),
    "breakdown": ("Breakdown", "A close below a floor that held before."),
    "failed_breakout": ("Failed breakout", "A breakout that falls back inside its range traps buyers."),
    "failed_breakdown": ("Failed breakdown", "A breakdown that climbs back inside its range traps sellers."),
    "flag": ("Flag", "A sharp move (the pole), then a shallow drift on light volume (the flag); the next leg often "
                     "matches much of the pole."),
    "double_bottom": ("Double bottom", "Two lows at one price with a peak between; the pattern counts once price "
                                       "closes over that peak."),
    "double_top": ("Double top", "Two highs at one price with a low between; the pattern counts once price closes "
                                 "under that low."),
    "ascending_triangle": ("Ascending triangle", "A flat ceiling with rising lows: buyers keep paying more."),
    "descending_triangle": ("Descending triangle", "A flat floor with falling highs: sellers keep taking less."),
    "spring": ("Spring", "A quick break under a range's floor that closes back inside: weak holders shaken out "
                         "before a rise (Wyckoff)."),
    "upthrust": ("Upthrust", "A poke over a range's ceiling that closes back inside: buyers trapped before a fall "
                             "(Wyckoff)."),
    "selling_climax": ("Selling climax", "Capitulation: the heaviest volume of the fall, on a day that closes "
                                         "strong."),
    "buying_climax": ("Buying climax", "Exhausted buying: the heaviest volume of the run, on a day that closes "
                                       "weak."),
    "sign_of_strength": ("Sign of strength", "A wide, heavy up day rising out of a range: demand taking over "
                                             "(Wyckoff)."),
    "buy_zone": ("Buy zone", "The price range where the plan buys; the top of it is the cap, never chased above."),
    "target": ("Target", "Where the plan takes profit, at the next real ceiling."),
    "out": ("Out", "The daily close that proves the plan wrong; the plan sells there."),
    "rr": ("Reward to risk", "What the plan can make for each unit it risks; 2R makes twice the risk."),
    "fear_day": ("Fear day", "A session the stock and the fund it follows both close red; the owner's rule buys "
                             "long setups on such a day."),
    "conviction": ("Conviction", "How many kinds of evidence agree behind the plan, net, each kind counted once: "
                                 "High at three, Solid at two, else Speculative."),
    "gut": ("The desk's take", "The evidence and what it does not hold (support stacked at the buy, the fund it "
                               "follows, earnings inside the hold): Strong, For, Leaning or Against. Recorded "
                               "before the outcome, so it can be scored."),
    "earnings": ("Earnings", "The quarterly report; prices can gap on it, past any plan's lines."),
    "strategies": ("The desk's strategies", "The desk's own trading rules; when several kinds agree on a name, the "
                                           "read counts it."),
    "elliott": ("Elliott wave", "Trends tend to move in five waves (three up, two down) before a larger correction."),
}


def learn(key):
    g = GLOSSARY.get(key)
    return g[1] if g else ""


def day(d):
    """Mon Oct 19"""
    if isinstance(d, str):
        d = date.fromisoformat(d)
    return datetime(d.year, d.month, d.day).strftime("%a %b ") + str(d.day)


def short_day(d):
    """Oct 19"""
    if isinstance(d, str):
        d = date.fromisoformat(d)
    return datetime(d.year, d.month, d.day).strftime("%b ") + str(d.day)


def p(x):
    """a distance from the last close in words: +3.2% / −1.5% / 0% (whole numbers from 10% up)"""
    if abs(x) >= 10:
        v = round(x)
        s = f"{abs(v):d}"
    else:
        v = round(x, 1)
        s = f"{abs(v):.1f}".rstrip("0").rstrip(".")
    if v == 0:
        return "0%"
    return ("+" if v > 0 else "−") + s + "%"


def p_abs(x):
    """a size in words without a sign: 3.2% / 15%"""
    return p(abs(x)).lstrip("+")


def join(items):
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def a(s):
    """s with its article: a 9-week base, an 11-week base, an 8-week base, an exhaustion gap"""
    head = s.split("-")[0].split(" ")[0]
    if head.isdigit():
        vowel = head.startswith("8") or head in ("11", "18")
    else:
        vowel = s[:1].lower() in "aeiou"
    return ("an " if vowel else "a ") + s


def lower(s):
    return s[:1].lower() + s[1:] if s and not s[:2].isupper() else s
