# Technical Analysis Mastery, Volume II: The External Companion

## The Craft, Learned From Every Available Source

Date: 2026-10-30. Companion volume to the internal mastery study.

Purpose. This volume learns the craft of reading charts from every available external source: the open source code that had to define every pattern in numbers, the written canon that turned identification into checkable rules, the Wyckoff and classical traditions that read ranges and boundaries, and the working practitioners whose routines, journals, and drills show how the craft is actually operated day after day. The posture throughout is learn to do it: state the prior trend, earn the pattern name by passing its checks, draw the lines, write the confirmation and the invalidation before the next bar, and grade the read later against what price did. Sources are named inline wherever a rule comes from a specific teacher, so any rule in this volume can be traced back to its origin. The full inventory behind this volume, with read status per source, is the external census filed with the mastery study.

The four sections run in the order a reader grows: first the code canon, which gives the eye a ruler; then identification craft, which gives the eye a checklist; then Wyckoff and classical charting, which give the eye a frame; then practitioner craft, which gives the eye a routine.

---

# Section E1: The Code Canon: What Open Source Code Teaches the Eye

## Why code is a teacher

A human can point at a chart and say that looks like a hammer. Code cannot. Code has to decide, in numbers that work on the next chart and the next thousand charts, how long a body is, how long a shadow is, how equal two shoulders are, and how close two highs must be before they count as the same level. That forced precision is the gift of the open source canon. Read the code not to automate the eye away, but to sharpen it. Every threshold in this section becomes a question you ask by eye, in order, before you name a pattern.

Two bodies of code carry most of the teaching. The first is TA-Lib, the C library whose 61 candlestick functions (the CDL family) are the de facto definition of candlestick reading in software, wrapped for Python by mrjbq7/ta-lib and explained most clearly in the serkor1/ta-lib-R vignette. The second is the geometric pattern literature on GitHub: zeta-zetra/chart_patterns for classical shapes, GregoryMorse/trendln for trendlines and support and resistance, PatternPy and white07S/TradingPatternScanner for screener style detection, and shuhanchang12/TechnicalAnalysisAutomation for competing ways to choose the points that matter. Where this section states a number, that number comes from one of those sources, named inline.

Posture for the whole section: a pattern name is a conclusion, not a starting point. You earn the name by passing its checks.

## Part One: The TA-Lib Candlestick Canon

### 1. The hidden measuring system underneath every pattern

Most candlestick teaching says long body, short body, long shadow, as if those words were self evident. TA-Lib, as surfaced in the serkor1/ta-lib-R vignette, judges every candle against its recent neighbours. Learn this system first, because every family below is built from it.

The vocabulary is fixed. The real body runs from open to close. The upper shadow runs from the top of the body to the high. The lower shadow runs from the bottom of the body to the low. The range runs from high to low. Nothing else is measured.

The comparisons, from the vignette settings table:

| Judgement | TA-Lib setting | Visual rule you run by eye |
|---|---|---|
| Long body | BodyLong: N 10, alpha 1.0 | This body is larger than the average body of the prior 10 candles. |
| Very long body | BodyVeryLong: N 10, alpha 3.0 | This body is more than three times that 10 candle average. Rare. Treat it as climactic. |
| Short body | BodyShort: N 10, alpha 1.0 | This body is smaller than the average body of the prior 10 candles. |
| Doji like body | BodyDoji: N 10, alpha 0.1 | This body is less than 10 percent of the average high to low range of the prior 10 candles. |
| Long shadow | ShadowLong: N 0, alpha 1.0 | This shadow is longer than the real body itself. |
| Very long shadow | ShadowVeryLong: N 0, alpha 2.0 | This shadow is more than twice the real body. |
| Short shadow | ShadowShort: N 10, alpha 1.0 | This shadow is less than half the average of upper plus lower shadows over the prior 10. |
| Very short shadow | ShadowVeryShort: N 10, alpha 0.1 | This shadow is less than 10 percent of the average range. |
| Near | Near: N 5, alpha 0.2 | Two prices sit within 20 percent of the average range of the prior 5 candles. |
| Far | Far: N 5, alpha 0.6 | Two prices sit at least 60 percent of that average range apart. |
| Equal | Equal: N 5, alpha 0.05 | Two prices sit within 5 percent of that average range. Effectively the same price. |

Three eye skills follow directly.

First, calibrate before you classify. Glance at the prior 10 candles and form an average body and an average range in your head. A body that is long on a quiet chart may be ordinary on a volatile chart. TA-Lib never judges a candle in isolation, and neither should you.

Second, separate size from position. A short body at the top of its range with a very long lower shadow is a different object from the same short body at the bottom of its range with a very long upper shadow. The families below differ mostly in where the small body sits and which shadow dominates.

Third, expect a lookback. In TA-Lib every pattern returns no reading until enough prior candles exist to build the reference averages. By eye the equivalent rule is simple: do not name a pattern on the first few candles of a chart, a listing, or a session segment. You have no ruler yet.

Penetration is the second hidden system. Seven TA-Lib patterns take a penetration parameter, eps, with default 0 in the R vignette: Morning Star, Evening Star, Morning Doji Star, Evening Doji Star, Abandoned Baby, Dark Cloud Cover, and Mat Hold. With eps set to 0.3, for example, an Evening Star follow through or a Dark Cloud Cover must intrude 30 percent into the prior real body to count. By eye: ask not merely did the second candle enter the prior body, but how far. A close that barely crosses the midpoint is a weaker read than a close that drives two thirds through. The midpoint of the prior body is the working line for Piercing and Dark Cloud work below.

A final warning the code teaches honestly. TA-Lib pattern functions check candle shape far more completely than they check preceding trend. The vignette and the census note this plainly: a Hammer shape is returned on shape, and trend filtering is the caller's job. By eye that means trend context and confirmation, stated for every family below, are not optional decoration. They are the half of the definition the oldest code leaves to you.

### 2. The single candle vocabulary

Before the families, fix four single candle objects, because the families reuse them.

Marubozu: a long body with very short or absent shadows. Buying or selling pressure ran from open to close with almost no rejection at either end. Read it as conviction in the direction of the close, strongest when it breaks a level.

Long Legged Doji and the standard Doji: a doji like body, per BodyDoji above, near the middle of the range for the standard form, with long shadows both ways for the long legged form. Indecision with range: buyers and sellers both pushed and both were rejected.

Dragonfly Doji and Gravestone Doji: a doji like body at one extreme of the range. Dragonfly sits at the top, with a long lower shadow and almost no upper shadow: lows were strongly rejected. Gravestone sits at the bottom, with a long upper shadow and almost no lower shadow: highs were strongly rejected. Position inside the range is the whole distinction.

Spinning Top: a short body with shadows longer than the body on both sides, but not extreme enough for a long legged doji. Momentum is pausing, not reversing by itself. It matters most as the middle candle of a star or as a pause after a long body.

### 3. Engulfing: the body swallows the prior body

TA-Lib function: CDLENGULFING. Drivers: BodyLong plus BodyShort comparisons and the containment test between two real bodies.

Recognition rules, run in order:

1. Trend context first. Bullish engulfing belongs after a decline or at a tested support area. Bearish engulfing belongs after an advance or at tested resistance. The same two candles in the middle of a sideways range carry far less information.
2. The second real body completely contains the first real body. Open of candle two is beyond the close of candle one, and close of candle two is beyond the open of candle one. Judge bodies, not shadows. Wicks may protrude; bodies may not.
3. The engulfing body should read as long against the prior 10 candle average, and the engulfed body should not be a doji. A large body swallowing a tiny body proves little, because there was little to swallow.
4. Colour confirms direction. Bullish: candle one closes down, candle two closes up and ends above candle one's open. Bearish is the mirror.
5. Confirmation: the next candle closes in the engulfing direction, or price holds above the engulfing close for the bullish case and below it for the bearish case. A bullish engulfing whose low is lost on a closing basis the next day has failed its own story.

Common false positive the code prevents: two candles where the second is larger in range only because of a long wick. If the real body does not contain the prior real body, it is not engulfing, whatever the range suggests at a glance.

Related two candle forms in the canon: Counterattack Lines, where the second close lands Equal to the first close (within 5 percent of average range, per the Equal setting) without engulfing, and Kicking, where a Marubozu gaps away from and engulfs in the most abrupt form. Both teach the same eye lesson: measure the close against the prior body with a tolerance, and name the tolerance.

### 4. Harami: the body is contained, and momentum has stalled

TA-Lib functions: CDLHARAMI and CDLHARAMICROSS.

Recognition rules:

1. Candle one has a long real body in the direction of the prevailing move: down in a decline for a bullish harami setup, up in an advance for a bearish harami setup.
2. Candle two has a short real body that sits entirely inside the real body of candle one. Again, bodies judge containment. Shadows of candle two may extend, but the cleanest examples keep the whole candle contained as well.
3. Harami Cross replaces the short second body with a doji like body, per BodyDoji. The stall is stronger because candle two barely moved from open to close at all.
4. Harami is a stall pattern, not a reversal proof. Its honest reading is: the force that produced the long body failed to extend on the next candle. Confirmation is mandatory. Bullish harami needs a subsequent close above the midpoint, then above the high, of the long down body. Bearish harami needs the mirror closes below.
5. Position improves the read. A harami whose second candle sits near the end of the first body in the direction of a possible turn, at a known level, after an extended move, deserves more attention than a harami in mid range after two candles of travel.

Eye contrast to memorise: engulfing expands beyond the prior body; harami contracts inside it. Expansion claims control has changed hands. Contraction claims control has paused. Do not trade them with the same confidence or the same confirmation standard.

### 5. The Doji family: equality of open and close, judged by context

TA-Lib functions include CDLDOJI, CDLDOJISTAR, CDLDRAGONFLYDOJI, CDLGRAVESTONEDOJI, and CDLLONGLEGGEDDOJI.

Recognition rules:

1. Pass the BodyDoji test first. The body must be less than 10 percent of the average range of the prior 10 candles. A small body is not automatically a doji. On a chart of small candles, a small body may be entirely normal.
2. Name the shadow structure. Both shadows long: Long Legged Doji. Lower shadow very long, upper shadow very short: Dragonfly. Upper shadow very long, lower shadow very short: Gravestone. Both shadows short: a plain Doji, closer to a pause print than a rejection print.
3. Context assigns meaning. A doji after a long body in an extended move says the driving side failed to close the candle in its favour despite intraday travel. A doji in a tight range says nothing new: indecision was already the regime.
4. Doji Star adds a gap condition in spirit: the doji body sits away from the prior long body, up after an advance or down after a decline, so that the stall is separated from the prior close. The cleaner the separation, the cleaner the star read in the three candle stars below.
5. Confirmation: a doji never completes a turn by itself in disciplined reading. Require the next candle to close beyond the doji range in the turn direction. A Gravestone Doji followed by a strong up close is a rejected rejection, and the code habit of marking the doji alone must not override that follow through.

Practice drill from the settings: cover the candle names on a chart, and for 20 consecutive dojis write only three fields: body as percent of range, longer shadow and its multiple of the body, prior trend. Naming comes after those three fields, never before.

### 6. Hammer, Hanging Man, Inverted Hammer, Shooting Star: one geometry, four contexts

TA-Lib functions: CDLHAMMER, CDLHANGINGMAN, CDLINVERTEDHAMMER, CDLSHOOTINGSTAR. Drivers: BodyShort plus ShadowLong and ShadowVeryLong.

The shared geometry:

1. A short real body.
2. One shadow at least as long as the body, and in the strong form more than twice the body (ShadowVeryLong).
3. The opposite shadow is short or absent.
4. The body sits at the extreme of the range opposite the long shadow. Long lower shadow, body near the top: hammer shape. Long upper shadow, body near the bottom: inverted shape.

Context and position assign the four names:

| Name | Prior move | Long shadow | Body position | Honest reading |
|---|---|---|---|---|
| Hammer | Decline | Lower | Near the high of the range | Lows were probed and rejected. Potential turn up, pending confirmation. |
| Hanging Man | Advance | Lower | Near the high of the range | Identical shape to a hammer. At highs it warns that intraday selling appeared and was only just absorbed. |
| Inverted Hammer | Decline | Upper | Near the low of the range | Highs were probed after a decline. A tentative bid, weaker than a hammer because the close stayed low. Needs an up close to confirm. |
| Shooting Star | Advance | Upper | Near the low of the range | Highs were probed and rejected after an advance. Potential turn down, pending confirmation. |

Confirmation standards differ, and the difference is craft:

- Hammer: confirm with a close above the hammer high, ideally on a body that is long against the 10 candle average. The hammer low is the invalidation line. A close below it cancels the rejection story.
- Hanging Man: because the shape at highs still closed near its high, wait for a down close, ideally below the hanging man body, before treating distribution as real. Many hanging men are simply absorbed.
- Shooting Star: confirm with a close below its low or a long down body next. The star high is invalidation.
- Inverted Hammer: demand the most confirmation of the four. Its close near the low means buyers did not hold their probe. Only a subsequent strong up close promotes it.

The code lesson is sharp here: TA-Lib must return different names for identical geometry based on surrounding candles, which is the library admitting that shape alone does not read a chart. Location is part of the pattern.

### 7. Morning Star and Evening Star: the three act turn

TA-Lib functions: CDLMORNINGSTAR, CDLEVENINGSTAR, plus the Doji Star variants and CDLABANDONEDBABY. These are among the seven penetration parameter patterns.

Morning Star, act by act:

1. Act one: a long down body, long against the 10 candle average, closing near its low. The decline is still in control at the close.
2. Act two: a short body or a doji, the star, that does not make material new progress down. In the classic form its body gaps or sits below the first body. In modern continuous markets judge separation by body position and by a low that stalls, not by demanding a literal price gap on every instrument.
3. Act three: an up body that closes well into act one's real body. Use the penetration discipline: at minimum past the midpoint of act one, and the deeper the penetration, the stronger the read. The R vignette example of eps 0.3 is a useful floor for attention: 30 percent intrusion is a minimum claim, not a strong one. A close that recovers most of act one is the tradable form.
4. Shadows refine, they do not rescue. A star with a long lower shadow shows rejection inside the stall. A star with a long upper shadow in a Morning Star warns that the turn attempt was already being sold.
5. Confirmation and invalidation: holding above the act three close, or a fourth candle continuing up, confirms. A close back below the star low invalidates.

Evening Star is the exact mirror: long up body, stalling short or doji body at the top, then a down body penetrating well into the first body, midpoint as the working line.

Abandoned Baby sharpens both: the star is a doji, and its shadows do not overlap the bodies around it, so the middle session is fully separated. It is rare precisely because the separation condition is strict. Do not loosen the name onto an ordinary star. The rarity is the information.

Morning and Evening Doji Stars keep the three act structure with a doji as act two. The act three penetration rule carries the read; the doji alone carries none.

### 8. Three White Soldiers and Three Black Crows: sustained bodies, controlled overlap

TA-Lib functions: CDL3WHITESOLDIERS and CDL3BLACKCROWS.

Three White Soldiers:

1. Three consecutive up candles, each with a body that is long or at least solid against the recent average, appearing after a decline or a base.
2. Each candle opens inside the prior real body, ideally in its upper half, and closes above the prior close, making a new high close in sequence. Opens that gap far above the prior body and then stall are not soldiers; that is exhaustion behaviour.
3. Upper shadows stay short. Long upper shadows on the second or third soldier mean supply is meeting the advance, and the formation degrades toward a stall.
4. The staircase matters more than any single candle: higher opens inside prior bodies, higher closes, controlled shadows. Read the three as one three session push.
5. Overextension check: if the third soldier is a very long body (BodyVeryLong, three times average) after a steep run, treat climax risk as part of the read rather than pure continuation.

Three Black Crows is the mirror: three down bodies after an advance or at a top, each opening inside the prior body and closing lower, lower shadows short, closes near lows. Short lower shadows matter because long lower shadows would show the declines being bought, contradicting the crow story.

Close relatives that sharpen the eye: Three Inside Up and Down and Three Outside Up and Down in TA-Lib combine a harami or engulfing with a third confirming candle built in. They encode, in code, the confirmation rule this section keeps repeating: two candle patterns plus a third candle that closes in the turn direction are a stronger object than either two candle pattern alone. Rising and Falling Three Methods and Mat Hold extend the same idea to continuation: a long body, small counter bodies that stay inside its story, then a resuming body. If you learn to see the confirming third candle as part of the pattern, your false signal rate on two candle patterns falls immediately.

### 9. Piercing Line and Dark Cloud Cover: the half body test

TA-Lib functions: CDLPIERCING and CDLDARKCLOUDCOVER. Dark Cloud Cover is one of the seven penetration parameter patterns.

Piercing Line:

1. After a decline, candle one is a long down body.
2. Candle two opens below the low or close of candle one, in the strong form gapping down, then rallies to close above the midpoint of candle one's real body, while still closing below candle one's open. That last clause separates Piercing from bullish engulfing: the second body enters deeply but does not fully swallow.
3. The deeper the close penetrates toward, and beyond, two thirds of the prior body, the stronger the read. A close one tick above the midpoint passes the code test and deserves the weakest weight.
4. Confirm with a hold or a further up close. Invalidate on a close below candle two's low.

Dark Cloud Cover mirrors it after an advance: a long up body, then a candle that opens above and closes below the midpoint of the prior up body, without engulfing it fully. The name is literal: the second close darkens more than half the prior body.

Eye rule for both: find the midpoint of the first body before you look at anything else. Draw it mentally or, in review, draw it on the chart with the mplfinance hlines convention described in Part Two. Without the midpoint line there is no pattern test, only an impression.

### 10. The candlestick eye checklist

Run this sequence on any candidate, in this order. It is TA-Lib translated into a reading routine.

1. Ruler: what are the average body and average range of the prior 10 candles?
2. Body: long, short, or doji like against that ruler? Give the judgement a rough ratio.
3. Shadows: which shadow dominates, and by what multiple of the body? Which shadow is nearly absent?
4. Position: where does the body sit inside its own range, and where does the candle sit inside the recent move?
5. Relation: for two and three candle patterns, state containment, penetration, or equality in words: engulfs, sits inside, penetrates past midpoint, closes equal within tolerance.
6. Trend context: what move preceded, how extended is it, and what level is being tested?
7. Confirmation: what exact next close would confirm, and what exact close would invalidate? Write both before the next candle prints in live reading, or cover the right edge in review and predict both.

If any step cannot be answered from the chart in front of you, the pattern is not identified yet. That sentence, borrowed from the geometric code in Part Two, governs candles too.

## Part Two: Algorithmic Chart Pattern Detection

### 11. Pivots before patterns: the three ways code chooses turning points

Every serious detector in zeta-zetra/chart_patterns, PatternPy, TradingPatternScanner, and TechnicalAnalysisAutomation follows the same pipeline: reduce OHLC to pivot highs and lows, sequence the pivots, validate geometry, draw the defining lines, confirm on a break. The detectors differ almost entirely in step one. Choosing a pivot method is choosing what kind of chart reader you will be.

Method A: the local window pivot. zeta-zetra's core primitive is pivot_id(l, n1, n2): a bar is a pivot high if its high is the extreme against n1 bars to its left and n2 bars to its right, a pivot low on the mirror test, with returns for high, low, both, or none. The tutorial fractal method in the census is the same idea with a fixed window: five candles, middle candle holding the lowest low or highest high of the five. scipy argrelextrema with an order parameter, used across tutorial notebooks, is the library form of the same test.

Eye translation: a swing high is not the highest tick you can see. It is a high with lower highs on both sides for a stated number of bars. Small n finds every wiggle and floods the chart with candidate patterns. Large n finds only major swings and misses early structure. State your n before you mark swings in any review session, and keep it fixed inside that session. Changing n mid chart to make a pattern appear is the human version of overfitting.

Method B: the directional change pivot. TechnicalAnalysisAutomation extracts turning points when price reverses by a threshold, sigma. The census records its granularity lesson directly: sigma 0.01 produces many extremes and a short term read, 0.02 a moderate set, 0.03 to 0.04 only major swings and a long term read, and the code ensembles across sigmas. Eye translation: this is percentage thinking. On a noisy intraday chart, ignore reversals smaller than a stated fraction of price or of average range. The method ignores time entirely and keeps only moves large enough to matter, which is exactly what an experienced eye does when it skips flat chop.

Method C: perceptually important points, PIP. The same project implements PIP extraction: the points a viewer would keep if forced to redraw the chart from a handful of points. Eye translation: after any session, redraw the chart from memory with five to nine points. Those points are your PIPs. If a pattern depends on a point you would not have kept, the pattern is probably manufactured.

Rolling window extrema, the PatternPy and TradingPatternScanner base method, is Method A applied inside a moving window rather than around confirmed pivots. Its stated practitioner rule from the TradingPatternScanner README, verified in the primary text in this pass: a smaller window is more sensitive and produces more false positives; a larger window is less sensitive and produces fewer, cleaner detections. That sentence applies to the human eye word for word. Zooming in manufactures patterns. Zooming out deletes them. Neither zoom is the truth; the honest read names the window it used.

Denoising is the fourth choice, and TradingPatternScanner teaches it best. The same head and shoulders detector run on raw rolling windows, on Savitzky-Golay filtered data, on Kalman filtered data, and on wavelet denoised data scored, on its synthetic test set, 78.5 percent, 78.5 percent, 73.5 percent, and 84.5 percent respectively, with wavelet best because it removes noise while preserving features. The README itself warns that synthetic data is not the real market and each user must test on their own data. The eye lesson survives the warning: every reader smooths the chart somehow, by timeframe choice, by ignoring wicks, by using closes only, or by looking at a line chart. Name your smoothing. A pattern that exists only under one aggressive smoothing is a property of the smoothing, not of the market.

### 12. Trendlines: fitted, ranked, and drawn in plural

GregoryMorse/trendln is the most complete open source answer to which trendline is the right one, and its answer is: compute candidates, rank them, draw more than one.

Its protocol in calc_support_resistance:

1. Find extrema first, with a stated finder. The library offers naive local extrema, a consecutive flat handling variant, and a default numerical differentiation method (METHOD_NUMDIFF). Lines are fitted to extrema, never to arbitrary candles.
2. Generate candidate lines through the extrema by competing methods: exhaustive three point search (METHOD_NCUBED, slowest), a two point sorted slope search (METHOD_NSQUAREDLOGN, the default), and Hough transform methods on points or on the chart image (METHOD_HOUGHPOINTS, METHOD_HOUGHLINES, METHOD_PROBHOUGH).
3. Rank each candidate by fit quality: slope, intercept, sum of squared residuals, slope error, intercept error, and area between the line and price averaged per time unit. The defaults encode judgement: a search window of 125 bars, a maximum slope standard error errpct of 0.005, and lines kept within a bound pctbound of 0.1, meaning 10 percent of the data range beyond the high and low.
4. Draw the summary and the leaders: the average best fit line through all minima for support and through all maxima for resistance, plus the top two support and top two resistance lines (numbest 2).

Eye protocol drawn from trendln:

- Anchor only on swing points you have already passed through your pivot rule. A line through random candle bodies is decoration.
- Draw at least two plausible lines when two exist: the average line and the steepest defensible line, for example. Disagreement between your candidate lines is information about trend stability.
- Rank by touches and by violations. A line price has crossed and stayed across, the wrong side area in trendln terms, is demoted or discarded. A line with three clean touches and no closing violations outranks a line with two perfect touches drawn through older data.
- Respect slope error intuitively: if tiny changes in anchor choice swing the line wildly, the trend is not line like at that scale. Say range or channel instead, and stop forcing a single line.

Tutorial code in the census adds the regression channel variant: fit channels anchored at the most recent highest high, the most recent lowest low, and the flattest segment, then treat confluence of slope and price region across anchors as the stronger read. The principle matches trendln: multiple anchored fits, agreement earns confidence.

### 13. Support and resistance: clusters, not single prices

Code builds levels three ways, and each way teaches a drawing habit.

Pivot clusters: in zeta-zetra/chart_patterns, horizontal levels are clusters of pivot highs or lows at approximately the same price, using a Near or Equal style tolerance rather than exact equality. Drawing habit: mark a level where at least two, and preferably three, independent swing points agree within a small band. One touch is an extreme, not a level.

Binning and averaging: tutorial methods catalogued in the census bin nearby candidate levels and replace them with their mean, and other notebooks cluster level prices with K means or build them from volume profile nodes. Drawing habit: draw a zone spanning the cluster, with its centre at the average of the touches. The zone width is data: it is the spread of the touches, not your preference.

Fractal levels: the five candle fractal marks the middle extreme as the level, and the tutorial corollaries state the reading rules plainly: more tests make a level more important, and broken resistance becomes support and broken support becomes resistance on a retest. Drawing habit: when a level breaks on a close, do not erase it. Extend it and watch the retest from the other side. Role reversal is part of the level's life, and every serious repo keeps broken levels on the chart for exactly this reason.

Confirmation standard for levels: a level is tested by a touch and reaction, violated by a close through it that holds, and broken decisively by a close through it followed by a failed retest from the other side. Intraday wick excursions through a zone are probes, to be weighed with the candle rules in Part One, not automatic breaks.

### 14. Head and shoulders: the minimum honest definition

zeta-zetra/chart_patterns gives the cleanest teachable detector. PatternPy and TradingPatternScanner implement the same object in rolling window form.

The algorithm, as a visual checklist:

1. Extract pivot highs with a stated pivot rule.
2. Find three consecutive pivot highs where the middle high, the head, is higher than both the left and right shoulder highs.
3. Check shoulder symmetry: the shoulders are similar in height. Code must set a tolerance; by eye, shoulders that differ by a large fraction of the head to neckline height fail the classical read. Symmetry in time also matters: a right shoulder built over far longer than the left is a different, weaker structure.
4. Draw the neckline through the two pivot lows that sit between left shoulder and head, and between head and right shoulder. The neckline may slope. Its slope is part of the read: a down sloping neckline in a top shows sellers pressing earlier.
5. The pattern is a candidate until price closes through the neckline. The break, not the right shoulder, completes it. A right shoulder that rallies back above the head invalidates outright.
6. Inverse head and shoulders is the identical test on pivot lows after a decline, with the neckline through the two intervening pivot highs.

What the algorithm reveals about honesty: remove any one element and the name collapses. Three highs without a higher middle high is a triple top test, not head and shoulders. A higher middle high without comparable shoulders is a spike, not head and shoulders. Shoulders and head without a drawn neckline is an opinion, because there is no break line to confirm or fail against. When you annotate a chart, draw the neckline first in your review workflow, then label the shoulders. If you cannot place the two neckline troughs without argument, do not use the name.

TradingPatternScanner adds the denoising caution from section 11: its Savitzky-Golay variant also checks head height to reject false heads. By eye: require the head to clear the shoulders by a visible margin relative to the pattern height. A head that exceeds the shoulders by a trivial amount is three tests of resistance wearing a costume.

Triple tops and bottoms, also in zeta-zetra, are the neighbouring test: three pivots at approximately the same level with proper spacing. Spacing is a real criterion in code, because three pivots on consecutive bars are one event sampled three times, not three tests. By eye, demand separation: a meaningful pullback between tests, so each test is an independent decision by the market.

### 15. Triangles and wedges: slope classification, not shape naming

zeta-zetra fits least squares regression lines (scipy linregress) to the pivot highs and to the pivot lows separately, then classifies the pair of slopes. This is the most useful single idea in geometric detection, because it replaces naming a silhouette with measuring two lines.

Triangles:

- Ascending triangle: the line through pivot lows rises, the line through pivot highs is approximately flat. Repeated equal highs with higher lows: demand is rising into fixed supply.
- Descending triangle: the line through pivot highs falls, the line through pivot lows is approximately flat. Supply presses down onto fixed demand.
- Symmetrical triangle: the high line falls and the low line rises. Both sides converge.
- All triangles require convergence: the two lines must meet at an intersection point ahead of the data at a sensible distance. Lines that converge far in the past, or that would meet years ahead, describe a range or a trend, not a compression.

Wedges, from the same source:

1. Fit the high line and the low line as above.
2. Both slopes share the same sign: both rise in a rising wedge, both fall in a falling wedge.
3. The lines converge toward a future intersection.
4. The slope ratio test: the ratio of the two slopes must sit within 0.75 to 1.25 in zeta-zetra's implementation. In plain terms, the two sides are advancing at comparable rates while converging. If one side is nearly flat, you are looking at a triangle, not a wedge. If the lines are parallel, you are looking at a channel, not a wedge.

That ratio is the minimum honest definition made visible. Wedge versus triangle versus channel is not a matter of taste. Flat side: triangle. Parallel sides: channel. Same sign slopes, converging, comparable rates: wedge. Rising wedge after an advance and falling wedge after a decline carry the classic reversal lean in the scanner literature, while wedges with the prevailing trend more often resolve as continuation pauses; either way, the break of the nearer line, confirmed on a close, is the event, and the pre break lean is only a prior.

Drawing standard for both: you need at least two pivot highs and two pivot lows to fit either line, and three touches per side makes the fit trustworthy. A triangle drawn on one high and one low per side is two lines through two points each, which always fit perfectly and prove nothing. Count touches out loud when you review: two is a hypothesis, three is a pattern, four is a structure.

Rounding bottom completes the zeta-zetra set and teaches a different fitting habit: fit a second degree polynomial to the pivot lows and require positive curvature, a genuine U with gradual slope change, rather than a V. By eye, a rounding bottom takes time and shows many small pivots along a smooth arc. If the turn is two candles, it is a V reversal, and calling it a rounding bottom hides the very fact that matters, which is speed.

Rectangles and channels close the taxonomy in PatternPy and TradingPatternScanner: multiple tops and bottoms at horizontal bounds define a range, and parallel rising or falling bounds define a channel. Their one line definitions in the scanner README are themselves a checklist: range is repeated failure at both bounds, channel is a strong trend held between parallel lines, and higher highs with higher lows, or the reverse, is the trend sequence underneath everything else.

### 16. Drawing standards: the picture is part of the proof

Every serious repo in the census renders its detection back onto the candles with its defining lines drawn. zeta-zetra crops around the pattern and overlays its lines. TechnicalAnalysisAutomation draws harmonic XABCD legs in white, reference diagonals, ratio labels, and the pattern name with its error score. mplfinance, the plotting standard most of these projects use, formalises the human equivalents: hlines for horizontal levels, tlines and alines for trendlines and anchored lines, vlines for event boundaries, and make_addplot for markers and overlays in the main pane or a sub pane. finplot adds a practitioner idiom worth copying: compute lower wick length as min(open, close) minus low, and mark only the top one percent by quantile with a marker. Extreme wicks are events; marking all of them marks none of them.

Adopt these as hand drawing rules:

1. No name without lines. Head and shoulders gets its neckline. Triangle and wedge get both fitted lines extended to their convergence. Support and resistance get zones, not hairlines, spanning the touch cluster.
2. Extend pattern lines to the decision point. The reader of your chart, including future you, must be able to see what close would confirm and what close would invalidate without redrawing anything.
3. Annotate the measurements, not just the label. Write the penetration for a star, the slope relation for a wedge, the touch count for a level, in the margin of a review chart. Code prints its ratios; imitate it.
4. Restore your view. finplot's view restore feature, which returns you to the same zoom and pan, encodes a review discipline: compare like with like. In journal review, revisit a pattern at the same timeframe and window you used when you called it. Reframing after the fact rewrites the evidence.
5. When patterns overlap on the same candle, rank, do not stack. The census records a tutorial repo that collapses TA-Lib's sparse 61 pattern output to one best label per bar using Bulkowski's performance rankings as the priority order, and yfinance-ta-patterns builds a confluence score from trend alignment, relative volume, RSI, and ATR around the candle signal. The human version: a candle at a tested level, with the trend, carries the label. The other labels the same candle technically satisfies are footnotes.

### 17. The minimum honest definition: what the algorithms settle

Read across the code canon, each pattern reduces to a short list of necessary conditions. If one condition fails, use a plainer name: range, spike, stall, trend. Precision in naming is not pedantry; it is what keeps a journal gradeable.

| Pattern | Necessary conditions code enforces |
|---|---|
| Engulfing | Second real body fully contains first real body; opposite colours; non trivial first body. |
| Harami | Second short body fully inside a prior long body; confirmation still outstanding by definition. |
| Doji | Body under 10 percent of the 10 candle average range; meaning assigned only by shadow structure and context. |
| Hammer family | Short body, dominant shadow at least the body length and ideally twice it, body at the opposite extreme; name assigned by prior trend. |
| Morning or Evening Star | Long first body, stalling second body, third body penetrating at least to the midpoint of the first body. |
| Three Soldiers or Crows | Three bodies in sequence, each opening inside the prior body and closing beyond its close, controlled shadows on the exit side. |
| Piercing or Dark Cloud | Second close crosses the midpoint of the first body without fully engulfing it. |
| Swing point | Extreme held against a stated number of bars on both sides, or a stated reversal threshold. |
| Trendline | Fitted to swing extrema, ranked against rival lines by error and violations; plural by default. |
| Support or resistance level | At least two independent swing touches clustered within tolerance, drawn as a zone. |
| Head and shoulders | Three pivot highs or lows, middle extreme highest or lowest, shoulders comparable, neckline through the two intervening pivots, completion only on a neckline close. |
| Triangle | Two fitted lines, one flat side or converging opposite slopes, future convergence, at least two touches per side. |
| Wedge | Two fitted lines with same sign slopes, converging, slope ratio near unity (0.75 to 1.25 in zeta-zetra). |
| Rounding bottom | Pivot lows fit a positively curved arc over many pivots; a fast turn is a V, not a U. |

### 18. Closing routine: the code canon as a daily practice

Do this in chart review until it becomes reflex.

First pass, candles only. Mark long bodies, doji like bodies, and dominant shadows against the 10 candle ruler. Name engulfing, harami, stars, soldiers, crows, piercing, and dark cloud only where containment, penetration, or equality can be stated in one sentence each.

Second pass, structure only. Mark swings with a fixed pivot rule. Fit lines to the swing highs and lows. Classify the slope pair before naming any shape. Cluster swing extremes into level zones and count touches.

Third pass, verdict. For each surviving pattern write four fields: name, defining lines drawn, confirmation close, invalidation close. A pattern missing either close is a watch item, not a read.

That is what open source code teaches the eye at its best: not more patterns, but fewer, better earned ones. TA-Lib gives the candle a ruler. zeta-zetra gives the shape a skeleton of pivots and fitted lines. trendln gives the line a ranking contest it must win. TradingPatternScanner gives every reader a warning label about smoothing and window choice. Carry those four gifts onto every chart and the names will start to mean something again.

Sources named in this section: TA-Lib (TA-Lib/ta-lib) and mrjbq7/ta-lib; serkor1/ta-lib-R candlestick vignette; zeta-zetra/chart_patterns via its DeepWiki algorithm pages; GregoryMorse/trendln; keithorange/PatternPy; white07S/TradingPatternScanner README including its denoising accuracy table and window sensitivity rule; shuhanchang12/TechnicalAnalysisAutomation including its Directional Change, PIP, and harmonic material; matplotlib/mplfinance; highfestiva/finplot examples wiki; Sortefi sortefi-ta and eminsk/yfinance-ta-patterns as confluence extensions noted in the census; tutorial fractal, argrelextrema, clustering, and regression channel methods catalogued in the external GitHub census.

---

# Section E2: Identification Craft

## The Drawing and Identification Discipline from Bulkowski and StockCharts ChartSchool

Identification comes before interpretation, before entry, and before any statistic. That is the shared lesson of the two strongest open sources in this volume: Thomas Bulkowski at ThePatternSite and the StockCharts ChartSchool in the Murphy tradition. ChartSchool teaches a reading order. Bulkowski turns that order into checkable rows. Together they give the eye a discipline: state the prior trend, name the anatomy in order, count the touches, test whether price fills the space, wait for a close outside the defining line, then measure. A shape that fails an early row does not get rescued by a good story later.

Sources named inline throughout: Bulkowski, ThePatternSite (thepatternsite.com) and *Encyclopedia of Chart Patterns*, 3rd Edition; StockCharts ChartSchool (chartschool.stockcharts.com); Peter Brandt on classical validity, via his public Factor excerpts; William O'Neil on cup with handle, via the ChartSchool and Bulkowski comparison tables; zeta-zetra/chart_patterns and GregoryMorse/trendln from the public code canon, used only where their pivot and line fitting rules sharpen the hand drawn standard.

### 1. The two protocols, and how to run them together

**The ChartSchool protocol (applies to every pattern).**

1. Prior trend first. A reversal pattern needs a trend to reverse. ChartSchool states it flatly for head and shoulders: without a prior uptrend to reverse, there cannot be a head and shoulders reversal pattern, or any reversal pattern. Establish trend by peak and trough sequence, by trendline, or by moving average. Classify it as major (over 6 months), intermediate (1 to 6 months), or minor (under 1 month).
2. Name the anatomy in order, point by point, before calling the pattern.
3. Read volume as part of the pattern, not as decoration after it.
4. The pattern does not exist until the break. Confirmation is a convincing break of the defining line, ideally with volume expansion. An intraday poke through a line is not the finished standard.
5. Expect polarity. Broken support becomes resistance and broken resistance becomes support. The retest, called a throwback after an upward break and a pullback after a downward break in Bulkowski, is a second test and a second chance entry, not a surprise.
6. Measure, then subordinate the measure. Project the pattern height from the breakout point, then check that target against prior support and resistance, Fibonacci levels, and long term moving averages. ChartSchool calls the measured target a rough guide, in those words.

**Bulkowski's identification first method (the stricter layer).**

Every Bulkowski pattern page opens with the same instrument: an Identification Guidelines table, Characteristic in one column and Discussion in the other. Run it row by row, in writing, before you look at his statistics. The rows that recur, and that discipline any pattern, are these:

1. Price trend row. State the direction leading in. Head and shoulders top: upward. Double bottom: downward. Descending triangle: any. If you cannot state it, stop.
2. Touch minima. A line is not real on one touch. Triangles need at least 3 touches on one line and 2 on the other, as distinct peaks and valleys. Wedges need 5 touches total, 3 on one line and 2 on the other. Broadening formations need at least 5 touches total, 3 on one side and 2 or more on the other. Channels and rectangles need at least 2 touches per line, with rectangles at 3 on one line and 2 on the other for a good specimen. Code canon agrees in its own language: zeta-zetra builds every detector on pivot highs and lows first (`pivot_id`, comparing a bar to bars left and right), and only then sequences pivots into a shape.
3. The crossing test, also called the white space test. Price must cross the pattern from trendline to trendline, nearly filling the available space. A candidate with abundant white space inside its lines is rejected. This is Bulkowski's most distinctive visual test, and the one beginners skip most often. A tight flag or pennant is defined in part by the absence of white space; a loose one, where price meanders, pokes outside the boundary, and leaves white space, performs worse and often is not the pattern at all.
4. Duration floors. A converging pause under about 3 weeks is a pennant, not a wedge or a symmetrical triangle. A cup runs 7 to 65 weeks. A flag runs under about 3 weeks, ideally under 15 trading days. Brandt adds the same discipline from practice: a dependable flag or pennant completes and breaks out within about 4 weeks; a 7 to 10 week upward sloping channel is not a flag and must not be expected to behave like one. Most public mislabelling is a duration violation.
5. Confirmation is a close outside the boundary. Bulkowski repeats the sentence across patterns: the pattern confirms as a valid one when price closes outside one of the trendlines. For a down sloping head and shoulders neckline, confirm on a close below the right armpit drawn horizontally, because price may never close below a steep neckline.
6. The measure rule is pattern specific and discounted. Compute the pattern height, multiply by that pattern's published percentage meeting price target, and project from the breakout price. Do not project the full naive height as if it were a promise. ChartSchool teaches the full height as the first estimate; Bulkowski teaches you how much of it to expect, pattern by pattern.
7. Know the failure language before you enter. Throwback and pullback rates are published per pattern and they hurt performance when you are unprepared for them. A busted pattern, one that breaks one way by 10 percent or less, reverses, and closes beyond the opposite side, becomes a new signal in the new direction. Failure is information, handled by rule, not by hope.
8. Context filters. Position in the yearly range, length and steepness of the inbound trend, volume trend direction, and, for triangles, how far toward the apex the breakout occurs, all change expectancy. They are identification context, not trivia.

**The combined eye checklist.** Before naming any pattern in this section, answer aloud: What trend leads in? What are the pivots, in order? How many distinct touches per line? Does price cross side to side and fill the space? How long has it lasted, and does that duration belong to this pattern or to a neighbour? What line, closed beyond, confirms it? What is the height, the discounted target, and the next real level beyond it? What closes back inside and invalidates it? If any answer is vague, the pattern is not identified yet.

### 2. Head and shoulders

The reference reversal. Top after an uptrend, bottom after a downtrend, mirror images with one asymmetry noted below.

**Identification checklist (ChartSchool, read in full; Bulkowski head and shoulders tops, read in full).**

- Prior trend present and stated: uptrend for the top, downtrend for the bottom.
- Three successive peaks (top) or troughs (bottom). The middle one, the head, is highest or deepest. The two shoulders are lower or shallower and roughly equal.
- Bulkowski symmetry rule, stricter than ChartSchool: shoulders should peak near the same price, sit nearly the same distance from the head, and look similar, both wide or both narrow. A lopsided specimen is suspect. Brandt's public validity test agrees: three distinct peaks, right shoulder lower than the head, roughly symmetric in time and height.
- Neckline: connect the two reaction lows between the peaks (the armpits, for a top) or the two reaction highs between the troughs (for a bottom). Note its slope. A down sloping neckline on a top is more bearish than an up sloping one.
- Volume script for a top: highest ideally on the left shoulder advance, diminished on the head advance (a new high on less volume is warning one), a pick up on the decline from the head (warning two), a decrease on the right shoulder advance, and expansion on the neckline break. Bulkowski: volume is highest on the left shoulder, then the head, and trends downward 61 percent of the time. Brandt rejected a widely advertised index head and shoulders top because the largest volume sat in the right shoulder. Volume placement can disqualify the pattern.
- Complex variant: multiple heads or multiple shoulders are allowed, usually many of one and not both.

**Most common drawing mistakes.**

- Drawing the neckline through closes on one armpit and through a wick extreme on the other, to make the break look cleaner. Pick the armpits, both of them, and draw once.
- Forcing symmetry where there is none: a right shoulder far above or far wider than the left is not a shoulder with character, it is a different structure.
- Calling the pattern at the right shoulder peak. Until the neckline closes, you have two shoulders and a head as a candidate, nothing more.
- Using the sloping neckline as the trigger when it slopes down steeply on a top. Bulkowski's fix: draw the horizontal line through the right armpit and require a close below it.
- Ignoring the prior trend and labelling any three peaks in a trading range as a reversal.

**What confirms.** A convincing close beyond the neckline, with volume expansion on the break. For the bottom, ChartSchool states that volume expansion on the breakout is absolutely required, whereas for the top the price break can complete the pattern with volume as strong support rather than an absolute gate. After the break, the neckline often flips polarity and is retested from the other side.

**Measure rule.** Vertical distance from the head to the neckline, projected from the neckline break point: subtracted below for a top, added above for a bottom. Bulkowski discounts it by the pattern's percentage meeting target (51 percent meet the adjusted target for tops in his bull market sample of over 2,800 perfect trades; performance rank 9 of 36, break even failure rate 19 percent, average decline 16 percent, pullback rate 68 percent).

**Invalidation.** A close back above the neckline after a top break, and especially a close above the right shoulder high, kills the read. Treat a break that reverses quickly and closes beyond the opposite extreme as a busted pattern with its own signal, per Bulkowski.

### 3. Double tops and double bottoms: the Adam and Eve taxonomy

Two tests of one level, separated by a real swing. Bulkowski's contribution is to split the family by the shape of each test, because the shapes carry different statistics. Learn to see Adam versus Eve and the identification gets sharper at once.

**Adam versus Eve (Bulkowski, Eve and Adam double bottoms and Eve and Adam double tops, read in full).**

- Adam: narrow, tall, pointed. A V shaped valley or an inverted V peak, often a single bar or a one day spike, slender through its whole height.
- Eve: wide and rounded. A conglomeration of bars near the same price that widens as it rises or falls. If Eve has spikes, they are more numerous and shorter than an Adam spike.
- The field test he teaches: ask whether the two extremes look the same or different. Adam and Eve and Eve and Adam must look different. Adam and Adam and Eve and Eve must look alike. Name them left to right, in the order they formed.
- Big M and Big W are the large relatives: a steep, near straight line rise into the first peak of a Big M, often about twice the peak to valley depth. A rounded rise into it disqualifies the Big M label; that is a plain double top.

**Identification checklist (double bottom form; mirror every price word for the top).**

- Prior trend: downtrend into a double bottom, uptrend into a double top.
- Two valleys near the same price. Bulkowski tolerance: bottoms within 0 to 4 percent of each other for Eve and Adam bottoms; peaks within about 3 percent for double tops. Near, not identical, and not far.
- The rise between the bottoms measures at least 10 percent, with variations allowed. For tops, the valley drop between the peaks measures at least 10 percent, with exceptions allowed. A shallower intervening swing is two wiggles in a range, not a double.
- Separation: several weeks, mostly 2 to 7 weeks (median 23 days for Eve and Adam bottoms; 2 to 6 weeks is the common range quoted for tops). Peaks a few days apart are a single top tested twice intraday, not a double.
- Volume: usually higher on the left bottom or left peak than on the right.

**Most common drawing mistakes.**

- Calling twin highs a double top before confirmation. Bulkowski warns that unconfirmed twin peaks fail 60 percent of the time; price rises instead of falling. The same caution governs bottoms: without waiting for confirmation, about 48 percent of Eve and Adam bottom candidates in his warning continue lower.
- Drawing the confirmation line at the pattern extreme instead of at the intervening swing. The line that matters is the peak between the valleys (bottom) or the valley between the peaks (top).
- Demanding identical extremes and rejecting good patterns over a 1 or 2 percent difference, or accepting extremes 8 percent apart because the silhouette looks right. Use the stated tolerances.
- Confusing an Eve and Eve bottom with a rounding bottom, or an Eve and Eve top with a rounding top. If there are two distinct valleys with a clear intervening peak, it is a double. If there is one continuous rounded turn, it is not.

**What confirms.** For a bottom, a close above the peak between the two valleys. For a top, a close below the valley between the two peaks. No close, no pattern, whatever the silhouette.

**Measure rule.** Height from the highest peak (top) or lowest valley (bottom) to the intervening swing point, multiplied by the variety's percentage meeting target, projected from the breakout point. Eve and Adam double bottoms in Bulkowski's sample of 759 perfect trades: rank 20 of 39, failure rate 12 percent, average rise 42 percent, throwback rate 67 percent, target met 72 percent of the time.

**Tactics worth carrying (Bulkowski).** A Big W with a tall, steep, clean left side tends to retrace toward the origin of the downtrend. A handle that forms after confirmation, a sideways waffle that then breaks in the pattern direction, often starts a strong trend. Do not buy a confirmed double bottom that is merely a retrace inside a primary downtrend without noting that context; his failure lesson chart is exactly that case.

### 4. Triangles: ascending, descending, symmetrical

A triangle is a volatility contraction drawn honestly: two converging lines, price crossing between them, volume drying up inside, resolution on a close outside.

**Identification checklist (ChartSchool symmetrical triangle, read via extract; Bulkowski descending triangle, read in full; Bulkowski general triangle rules).**

- Classify by the lines, not by hope. Ascending: flat resistance on top, rising support below. Descending: flat support below, falling resistance on top. Symmetrical: falling resistance and rising support converging at similar slopes. The code canon classifies the same way, by the signs and flatness of regression lines fitted to pivot highs and lows (zeta-zetra).
- Touches: Bulkowski requires at least 3 touches on one line and 2 on the other, as distinct peaks and valleys. ChartSchool's symmetrical triangle minimum is 4 points total, 2 per line, with 6 points (3 per side) as the ideal before a breakout.
- Crossing and white space: price must travel from line to line and nearly fill the shape. A triangle drawn around price that sits in one corner is a pair of lines in search of a pattern.
- Prior trend: state it. Symmetrical triangles are usually continuation patterns in ChartSchool, and can mark reversals; the prior trend is the context, never the guarantee of breakout direction. Descending triangles in Bulkowski can follow any inbound trend; when price rises into the pattern, upward breakouts occur 63 percent of the time in his sample, against 53 percent overall.
- Volume: contracts inside the pattern, quite low just before the breakout (Bulkowski: volume recedes 78 percent of the time in descending triangles), and expands on the breakout.
- Duration and apex position: a symmetrical triangle usually runs a few weeks to a few months, commonly about 3 months in ChartSchool. Under 3 weeks, reclassify it as a pennant. The ideal breakout arrives halfway to three quarters of the way from the base to the apex (ChartSchool). Bulkowski's median for descending triangles is 61 to 65 percent of the way to the apex. A break very close to the apex has little room left in the structure and is often insignificant; a break before the halfway point may be premature.

**Most common drawing mistakes.**

- Drawing both lines through wick tips that price never revisited, so the touches are artefacts of two extreme bars rather than reactions.
- Calling parallel lines a triangle. If the lines do not converge, you have a channel or a rectangle.
- Anticipating direction in a symmetrical triangle. ChartSchool is explicit: the direction of the next major move can only be determined after a valid breakout, and guessing it is dangerous even when the prior trend suggests continuation.
- Ignoring where the breakout sits relative to the apex. A late, apex crowded break and an early break are not the same event as a two thirds break.
- Labelling a wedge as a triangle. In a triangle the lines converge from opposite slopes or from one flat line. In a wedge both lines slope the same way. See Section 5.

**What confirms.** A close outside either trendline. Direction is whatever the close says: ascending triangles break up on a close above flat resistance, descending triangles break down on a close below flat support, symmetrical triangles resolve either way. Volume expansion supports the close.

**Measure rule.** Height at the widest part of the triangle, the base, projected from the breakout point. Bulkowski discounts by the pattern percentage: descending triangles meet target 64 percent of the time on up breakouts and 50 percent on down breakouts in his sample of over 1,300 trades (failure 22 to 23 percent, average rise 38 percent, average decline 15 percent). ChartSchool's second method for symmetrical triangles: draw a line parallel to the broken line through the opposite extreme of the base and read the projection against it. Price often turns near the apex date itself, so mark the apex on the calendar as well as on the price scale.

### 5. Wedges: rising and falling

Both lines slope the same way and converge. That tilt against, or with, momentum is the whole read: a rising wedge shows buyers paying higher prices in narrowing steps, a falling wedge shows sellers pressing lower in narrowing steps.

**Identification checklist (ChartSchool falling and rising wedge rules; Bulkowski wedge guidelines).**

- Rising wedge: both lines slope up, the lower support line steeper than the upper resistance line, lines converging, pattern beginning wide and contracting as price rises. Bearish in ChartSchool regardless of whether it appears as reversal or continuation, confirmed only by a break below support.
- Falling wedge: both lines slope down, the upper resistance line steeper than the lower support line, lines converging. As a reversal, ChartSchool asks for a prior downtrend at least 3 months old, with the wedge typically forming over 3 to 6 months. As a continuation in an uptrend, the same geometry applies with the prior trend stated as up.
- Touches: 5 total minimum in Bulkowski, 3 on one line and 2 on the other. ChartSchool's floor is lower, at least 2 reaction points per line and ideally 3 on the upper line of a falling wedge. When the two sources differ, say which standard you are using. This playbook uses Bulkowski's 5 touch floor for a tradeable call and ChartSchool's 2 per line as the earliest point at which you may draw the lines tentatively.
- Duration: at least about 3 weeks in Bulkowski. Shorter than that, the converging pause is a pennant.
- Volume: falls inside the wedge (Bulkowski: downward trend until breakout in about 72 to 79 percent of cases, by variety), and better performance follows a breakout on heavier volume.
- Slope check from the code canon: zeta-zetra requires both fitted slopes to share a sign, the lines to converge to a future intersection, and the slope ratio to sit within 0.75 to 1.25. A human version of the same test: if one line is dramatically steeper in a way that makes the shape a triangle with a tilted base, reclassify it before you trade it.

**Most common drawing mistakes.**

- Parallel lines called a wedge. Parallel up sloping lines are a rising channel; parallel down sloping lines are a descending channel. No convergence, no wedge.
- Counting touches on closes for one line and on wicks for the other, inflating the count to reach five.
- Forgetting the duration floor and promoting a 6 day pennant into a wedge with wedge statistics.
- Assuming direction. Bulkowski's breakouts go the expected way most of the time, falling wedges up 68 percent and rising wedges down about 60 to 69 percent by sample and edition, which means a large minority break the other way. Wait for the close.

**What confirms.** A close outside a trendline: above the upper line for a falling wedge, below the lower line for a rising wedge. ChartSchool adds for the falling wedge that an intraday break without a close and volume does not confirm.

**Measure rule.** Bulkowski's practical target for wedges is conservative: use the pattern height discounted by the percentage meeting target, and keep the origin of the wedge in view, since a rising wedge breakdown often retraces toward where the wedge began. Respect his performance warning while you use the shape: falling wedges rank 31 of 39 for upward breakouts and rising wedges sit at or near the bottom of his bearish table for downward breakouts, with high break even failure rates. Identification can be correct and the pattern can still be a modest one. That ranking is part of identification craft, because it tells you how much proof to demand from the breakout close and volume before acting.

### 6. Flags and pennants

The shortest honest patterns in the book: a steep pole, a brief pause that fills its small shape, and resumption. If there is no pole, there is no flag. Bulkowski states the rule in one sentence: if you do not have a straight line, quick price run leading in, the flagpole, then you do not have a flag.

**Identification checklist (Bulkowski flags and pennants, read via extract; ChartSchool flags and pennants summary; Brandt duration rule).**

- Flagpole first: an unusually steep, quick run, lasting several days, near vertical in the best specimens. The high, tight flag is the extreme case: price rises at least 90 percent, shooting for a double, in 2 months or less, then pauses.
- Flag shape: a small rectangle or parallelogram, usually tilted against the prevailing trend. Best performance in Bulkowski comes when an upward inbound trend meets a downward tilting flag. The flag portion lasts under about 3 weeks, and in his automated work ideally under 15 trading days. Beyond that, reclassify it as a rectangle or a channel.
- Pennant shape: a small symmetrical triangle, price between two converging trendlines, 3 weeks long or less. Longer than 3 weeks, it is a symmetrical triangle or a wedge.
- Tight versus loose: a tight flag or pennant, price contained, no pokes outside the boundary, no white space, outperforms a loose one. Judge tightness before direction.
- Volume: trends downward during the formation (pennants: downward 86 percent of the time in Bulkowski), then expands on resumption.
- Half mast position: classically the pause sits near the midpoint of the whole move, which is what makes the measure rule below more than arithmetic. Bulkowski is honest about the frequency: pennants mark the midway point in that useful way only about 30 percent of the time, so treat half mast as a check, not as a given.

**Most common drawing mistakes.**

- No pole: labelling any small sideways drift after a gradual rise as a flag. The pole must be steep and quick relative to what came before it.
- Duration creep: a pause in its fourth or fifth week is still being called a flag because the trader likes the entry. Brandt's 4 week outer limit and Bulkowski's 3 week rule exist to stop exactly this.
- Drawing the flag lines so wide that price only touches each side once. A flag is a small channel or a small triangle and obeys the same touch and crossing discipline, scaled down.
- Entering the high, tight flag on a trendline break inside the pattern. Bulkowski's updated rule: buy only on a close above the highest peak in the whole pattern, including the flagpole top, because trendline breaks inside high, tight flags fail too often.

**What confirms.** A close outside the flag or pennant boundary in the direction of the pole, on expanding volume. For the high, tight flag, the stricter confirmation above applies: a close above the pattern's highest peak.

**Measure rule.** Flagpole height, from the start of the inbound swing to its end, multiplied by the pattern's percentage meeting target, projected from the breakout edge of the flag (Bulkowski lays out four combinations of start and projection points; the conservative habit is to project from the far side of the flag in the breakout direction and to set targets conservatively). For the high, tight flag, take half the pole height and add it to the bottom of the flag. Worked logic: pole from 10 to 20, flag between 18 and 20, upward break. Full flag measure projects 10 points from the breakout area; the high, tight variant projects 5. State which one you are using on the chart.

### 7. Cup with handle

A rounded base with a small second act. Popularised by William O'Neil in *How to Make Money in Stocks* (1988); measured by Bulkowski, who ranks it 3 of 39 for bull market performance.

**Identification checklist (Bulkowski cup with handle guidelines, read via search extract of the primary page; ChartSchool and O'Neil criteria as tabulated by Bulkowski).**

- Prior advance: price rises into the start of the cup. O'Neil's original asks for a prior uptrend of at least 30 percent. Bulkowski notes he pays less attention to this row, but ChartSchool treats the pattern as a continuation, so with no prior advance there is nothing to continue.
- Cup shape: a rounded, U shaped turn, not a V. Allow variations, but a sharp V bottom is too abrupt to qualify in both ChartSchool and Bulkowski. Bulkowski's zeta style test from the code canon is useful by eye: a rounding structure curves; a V has a single pivot and straight sides.
- Cup rims near the same price level, flexibly judged. Equal highs are ideal in ChartSchool and not required.
- Cup duration: 7 to 65 weeks in Bulkowski. ChartSchool frames the cup at 1 to 6 months on daily charts, sometimes longer on weekly charts. A 2 week dip is not a cup.
- Cup depth, from O'Neil via Bulkowski's table: commonly 12 or 15 percent to 33 percent, with some cups declining 40 to 50 percent. ChartSchool's guide: ideally a third or less of the prior advance, up to a half in volatile markets, two thirds as an extreme maximum.
- Handle: mandatory in Bulkowski; cups without handles belong to a different pattern in O'Neil's scheme. The handle sits on the right side, forms in the upper half of the cup, and lasts at least 1 week with no stated maximum. ChartSchool puts the handle at 1 to 4 weeks ideally, drifting down, retracing up to a third of the cup's advance and usually less. Volume should dry up in the handle, and handles shorter than Bulkowski's median of 22 days performed better after breakout in his sample.
- Position filter from O'Neil: the handle forms above the 200 day moving average in his selection, and the stock shows a substantial volume increase in the prior uptrend and improving relative strength. Note these as O'Neil selection rules, distinct from the shape rules.

**Most common drawing mistakes.**

- Accepting a V as a cup because the rims line up. Shape is a row in the table, not a preference.
- A handle in the lower half of the cup. That fails Bulkowski's upper half rule outright, and it changes the supply picture: price has given back most of the recovery before trying again.
- A handle that rises above the right cup rim before the breakout, or, in the inverted cup, a handle that violates the cup boundary the other way. For the inverted cup with handle, Bulkowski requires the handle not to rise above the cup top, with a typical retrace of 30 to 60 percent of cup height, confirming on a close below the right cup lip.
- Cups inside cups, unnoted. Bulkowski observes that cups often form inside larger cups. Name the one you are measuring; do not mix the inner cup's handle with the outer cup's rim.

**What confirms.** Standard Bulkowski entry: a close above the right cup rim. Early entry he also teaches: draw a down sloping trendline across the handle's peaks and take a close above that line as the early signal. ChartSchool and O'Neil both want substantial volume expansion on the breakout; O'Neil's figure is at least 50 percent above normal.

**Measure rule.** For the normal cup, project the cup depth from the breakout point, discounted in Bulkowski fashion; his bull market sample reports a 5 percent break even failure rate and a 54 percent average rise across 913 perfect trades. For the inverted cup, Bulkowski's stated rule is narrower: compute the handle height and subtract it from the price of the right rim low. Tall cups with short handles and a higher left cup lip performed better in his results snapshot.

### 8. Rectangles

A horizontal channel with a memory: price enters from one side, crosses between two near horizontal lines, and leaves in either direction. Rectangle top means price entered from below after a rise; rectangle bottom means price entered from above after a decline. The name records the inbound trend, not the breakout direction.

**Identification checklist (Bulkowski rectangle tops, read via extract; rectangle bottoms via his Pattern Review).**

- Shape: flat tops and flat bottoms, price crossing the pattern from side to side between two parallel, near horizontal trendlines.
- Touches: at least 3 on one trendline and 2 on the other in Bulkowski's rectangle top guidelines, using distinct peaks and valleys, with flexibility allowed. His review of rectangle bottoms states the working floor as at least 2 distinct touches per line. Draw to the stricter standard when the chart offers it.
- Crossing: as with channels and broadening formations, the side to side travel is what separates a rectangle from two unrelated horizontal levels with a gap of white space between them.
- Volume: trends downward about 70 percent of the time inside rectangle tops.
- Inbound trend stated: upward into a rectangle top, downward into a rectangle bottom.

**Most common drawing mistakes.**

- Calling any two horizontal levels a rectangle when price has touched each only once, or when price never crossed the full height.
- Tilting the lines to fit. Lines with a clear common slope are a channel; lines converging are a triangle or a wedge. A rectangle's lines are near horizontal and near parallel.
- Assuming the breakout continues the inbound trend. Rectangle tops break upward 63 percent of the time in Bulkowski; the exit can be in any direction, so the identification is complete only when the close chooses one.
- Missing the partial move signal. A partial decline inside an established rectangle (price touches the top line, falls, but turns up before reaching the bottom line) predicts an upward breakout, with a 91 percent success rate for rectangle tops and 80 percent for rectangle bottoms in Bulkowski's partial decline table. A partial rise is the mirror predictor of a downward breakout. Do not look for a partial move until the rectangle itself passes every guideline above.

**What confirms.** A close outside either trendline. Since direction is open, Bulkowski's tactic is explicit: wait for price to close outside the trendline before taking a position. If the rectangle is tall enough, an intrapattern trade, buying at the bottom line and selling at the top, is a separate, range bound tactic with its own exit at the opposite line, not a breakout trade.

**Measure rule.** Height between the two trendlines, multiplied by the percentage meeting target (78 percent for up breakouts and 54 percent for down breakouts in rectangle tops), added to the top line for an up breakout or subtracted from the bottom line for a down breakout. Tall rectangles perform better than short ones. Nearby support and resistance can stall the move before the target, so check the path, per his rectangle bottom review.

### 9. Broadening formations: the megaphone

The mirror discipline of the triangle: instead of contraction, expansion. Higher peaks and lower valleys, diverging lines, rising volatility inside the shape. If a triangle is a market going quiet, a broadening formation is a market losing agreement, swing by swing.

**Identification checklist (Bulkowski broadening bottoms and broadening tops, read via extract; right angled variants noted).**

- Shape: a megaphone. Successive peaks higher, successive valleys lower. For a broadening bottom, the inbound price trend is downward; for a broadening top, upward. Right angled variants have one horizontal line: ascending right angled has a horizontal bottom and a rising top; descending right angled is its mirror.
- Trendlines: the top line slopes up, the bottom line slopes down, diverging from left to right. In a broadening wedge variant, both lines slope the same way while still diverging; Bulkowski's ascending broadening wedge guidelines call for at least 3 peaks and 3 valleys touching their boundaries.
- Touches: at least 5 total, 3 peaks or 3 valleys on one line and 2 or more on the other. Ideally the second of the three touches actually touches the line rather than coming close; that detail prevents misreading a down sloping channel with a late upward spike as a broadening formation.
- White space: price should cross the pattern from side to side, filling the area with movement. A broadening outline drawn around a price path that hugs one side is not identified.
- Volume: unlike triangles, volume tends to trend upward inside broadening formations, 65 to 67 percent of the time in broadening bottoms and about 62 to 63 percent in right angled ascending formations. Rising volume with widening swings is part of the picture, not a contradiction.

**Most common drawing mistakes.**

- Extending the diverging lines from the first two extremes and then counting every later bar that crosses the extension as a touch. Touches are distinct peaks and valleys at the line, in sequence, each one wider than the last.
- Confusing a broadening formation with a sloppy channel after two wide swings. Two swings make two points per side at most; the 5 touch floor exists because expansion needs repeated proof.
- Ignoring the partial move, the family's best signal. A partial decline in a broadening bottom (price rises to the top line, turns down, fails to reach the bottom line, and turns back up) predicts an upward breakout, at 80 percent in broadening bottoms and 72 percent in broadening tops in Bulkowski's table, with right angled ascending at 81 percent. A partial rise predicts the downward mirror. Bulkowski calls the partial decline the broadening bottom's one redeeming value, given its mid list base ranking (break even failure rank 25 of 39 for broadening bottoms; broadening tops rank 22 of 39 up and 28 of 36 down).
- Trading the middle. The tradable events in a broadening formation are the turns at the lines and the confirmed breakout, not opinions formed halfway across a widening range where risk cannot be defined against a nearby line.

**What confirms.** A close outside either diverging trendline, in either direction. Partial moves let a practitioner position earlier, at the turn back toward the line about to be broken, with the explicit added risk Bulkowski notes.

**Measure rule.** Height as the difference between the highest peak and the lowest valley in the pattern, multiplied by the percentage meeting target, added to the pattern top for an up breakout (broadening tops: works 66 percent of the time) or subtracted from the pattern bottom for a down breakout (works 42 percent). For right angled variants, measure from the highest peak to the horizontal line and project from the peak (up) or from the horizontal line (down). Because the height of a broadening pattern is by definition its widest swing, treat the full projection with more than the usual caution and check intervening levels first.

### 10. ChartSchool standards: trendlines and channels

Patterns are built from lines, so line discipline is pattern discipline. ChartSchool's trend line standard and Bulkowski's channel rules, read together, give a complete drawing protocol.

**Drawing a trendline (ChartSchool Trend Lines and TA 101 Part 8).**

- An uptrend line has a positive slope and connects two or more low points. It acts as support. Price above it: uptrend intact. A break below it: demand has weakened and a trend change could be imminent.
- A downtrend line has a negative slope and connects two or more high points. It acts as resistance. A break above it says supply is decreasing.
- The first two points establish the line. Additional points validate it. That sentence is the whole apprenticeship: two points are a hypothesis, the third touch is evidence, and every later touch is more evidence. Do not present a two point line with the confidence of a five point line.
- Draw through the reaction points themselves, wick extremes in the classical convention, consistently. A line that cuts through the bodies of the bars it is supposed to contain is drawn wrong; reposition it to the extremes or treat the misfit as information that the slope has changed.
- Steeper lines are less durable. ChartSchool's teaching, echoed in every summary of the article, is that very steep trendlines break easily and carry less weight as support or resistance than gradual ones that have governed price for longer. Record the line's age and touch count next to it on the chart.
- Scale: ChartSchool notes that trendlines and channels often fit reaction highs and lows best on semi logarithmic scales, especially over long spans where percentage moves, not point moves, are the comparable unit. On a multi year chart, check the line on log scale before trusting it.
- A trend can be read as a tilted support or resistance zone. Draw the line, then respect a small zone around it rather than demanding tick perfect touches, the same zone logic ChartSchool applies to horizontal levels in Section 12.

The code canon sharpens the same craft without replacing the hand: GregoryMorse/trendln fits candidate lines to extrema and ranks them by slope error, then draws the average line plus the top two support and top two resistance lines. The transferable habit is the ranking step. When two plausible lines compete on your chart, prefer the one with more distinct touches, smaller misses at those touches, and no price spending sustained time on the wrong side of it, and say why you kept it.

**Drawing a channel (ChartSchool Price Channel; Bulkowski Channels, read in full).**

- A channel is a main trendline plus a parallel return line. ChartSchool: draw the main line first, on at least two reaction lows for a bullish channel or two reaction highs for a bearish channel. Then draw the channel line parallel to it. Ideally the channel line also rests on two reaction points; ChartSchool allows one reaction high or low to place it once the main line is established, with the understanding that a one point channel line is provisional.
- Bulkowski's stricter standard for a tradeable channel: both lines tilted the same way, up or down, at least 2 touches per line as distinct peaks and valleys, price crossing from line to line and filling the space. A horizontal pair of lines is a rectangle, not a channel.
- Inside the lines, the lines do the work: the upper line marks resistance in a rising channel and support roles reverse in a falling one per ChartSchool's channel article, the main trendline marks support in a bullish channel and resistance in a bearish one. Price trading inside the channel keeps the read alive; the trend is considered intact while price advances and trades within the channel.
- Bulkowski's trading protocol, worth copying onto the chart: trade with the channel slope. Buy rebounds at the bottom line of an up channel and sell at the top; never short an up channel and never buy a down channel as a channel trade. A close outside the channel against your position is the exit, and possibly the start of a new trend read.
- Partial moves predict channel breakouts as they do in rectangles and broadening formations: a partial rise inside the pattern (price falls from the top line but turns up short of the bottom line, in the down breakout mirror, or the partial decline form) points to a breakout through the line price failed to reach from. Learn the partial move once and you own it in three families.
- No performance statistics are published by Bulkowski for channels. He states that plainly, and the honesty is itself a standard: draw channels as structure and trade location, not as a pattern with a ranked expectancy.

**Common line drawing errors, collected.**

- Drawing the line to fit the conclusion: anchoring on the most recent extreme and a convenient old extreme so the line passes exactly where a breakout would be flattering. Redraw from the earliest valid pair and let the recent price sit where it sits.
- Redrawing after every touch until the line can never be broken. One repositioning to correct an initial misfit is craft. Serial redrawing is refusal to take the signal.
- Mixing timeframes on one line, using a weekly extreme and a daily extreme as the two establishing points on a daily chart.
- Drawing a fan of near duplicate lines. Two or three governing lines per chart is ChartSchool practice in spirit and in the trendln drawing protocol; beyond that, the chart stops being a read and becomes a hedge against ever being wrong.

### 11. ChartSchool standards: gaps

A gap is a range where no trading occurred: an up gap means today's low is above yesterday's high; a down gap means today's high is below yesterday's low. Identification is exact, which is why gaps reward the checklist habit. All rules below are ChartSchool, Gaps and Gap Analysis and TA 101 Part 15, read via extract.

**The four gap types, identified by location and volume, in order of the questions to ask.**

1. Where did it occur? Inside a trading range, at the edge of a pattern, mid trend, or at the end of a long trend. Location does most of the classification before volume is even checked.
2. Common gap: occurs inside a trading range or shortly after a sharp move, carries no change in psychology, and tends to fill. Do not build a thesis on a common gap.
3. Breakaway gap: gaps out of a base, a top, or a consolidation, at a pattern completion, on above average volume. It signals a change in market psychology. For the read to remain valid, the gap should stay unfilled; the near edge of the gap becomes strong support (up gap) or resistance (down gap). A breakaway gap is often the confirmation event of the patterns in Sections 2 to 9 arriving by jump instead of by grind.
4. Runaway gap, also called a continuation or measuring gap: occurs near the middle of a short or intermediate trend, in the direction of the trend. It can come in a series. Its measuring use: project the move travelled before the gap forward from the gap to estimate the second half of the move. That is a measured move read, subject to the same subordination to real levels as every target in this section.
5. Exhaustion gap: occurs in the trend direction at the end of an extended trend, on exceptionally high volume, with near panic buying or euphoric selling in the move. It is valid as exhaustion only if price reverses soon after and fills the gap. Discriminator against the runaway gap, which it closely resembles on the day it prints: climax volume plus a quick fill. You cannot finally separate an exhaustion gap from a runaway gap on the gap day alone; the fill, or its absence, over the following sessions completes the identification. Write the candidate label and the test on the chart: fills within days and reverses, exhaustion; holds and trend continues, runaway.

**Drawing and reading standards.**

- Mark the gap as a zone, from yesterday's extreme to today's extreme, and extend it forward. Gaps are read as zones on return, like support and resistance zones, not as single prices.
- Record volume against its recent average on the gap day. Without the volume note, the classification cannot be defended later.
- Retire the slogan in its naive form. ChartSchool's canon warning: the claim that all gaps get filled does not hold for breakaway and runaway gaps. Common and exhaustion gaps fill as part of their definition; breakaway and runaway gaps are defined in part by not filling promptly.
- A gap that fills and closes beyond the far edge has been negated, not merely tested. Update the label rather than defending the original read.

### 12. ChartSchool standards: support and resistance zones

Support is a level or zone where demand is thought strong enough to prevent further decline; resistance is where supply is thought strong enough to prevent further rise. ChartSchool's article on support and resistance, read in full, is the standard this playbook adopts.

**Establishing a level.**

- Support comes from prior reaction lows. Resistance comes from prior reaction highs. Those are the sources; a level invented from a round number or a Fibonacci line alone has not been established by price until price reacts there.
- Strength grows with repeated tests and with timeframe. A level tested three times on a weekly chart outranks a level tested twice on an hourly chart. Count the tests and note the timeframe, on the chart.
- Trends themselves supply levels: a rising trendline is a tilted support zone, a falling one a tilted resistance zone, governed by Section 10.

**Zones, not lines, by default.**

- Because technical analysis is not an exact science, ChartSchool teaches zones when the range of reaction points is wide or the level has been in force for a long time, and exact levels when the range is tight, its guideline being a narrow range over less than about two months. Draw the zone as a band spanning the reaction extremes that created it.
- A close a small fraction beyond a level (ChartSchool's worked discussion uses a close 1/8 beyond as its example of an amount that does not automatically count) does not by itself declare a break. Judge the break by the close, by its distance, by volume, and by whether price holds beyond the zone on the following bars. This is the horizontal twin of the convincing break standard used for necklines and triangle lines.
- When the reaction lows align better on a slight slope than on a flat line, draw the sloped line. ChartSchool's Lucent example makes the point operationally: the sloped line through the lows gave the break signal one point earlier than the horizontal support would have. Fit the line the points offer, not the line your template prefers.

**Polarity, the principle that ties the whole section together.**

- Broken support becomes resistance and broken resistance becomes support. The mechanism ChartSchool teaches is human: buyers trapped at a broken support sell at breakeven when price returns, creating supply at the old floor; sellers trapped above a broken resistance buy back at the old ceiling, creating demand. Expect the retest of a broken level from the other side, name it in advance (throwback, pullback, return move), and use how price behaves at the flipped level as validation or invalidation of the break.
- Trading range logic follows: a range is balance between the zone pair. A convincing break above the resistance zone says buyers won the range; a convincing break below support says sellers won it. ChartSchool's false breakout cautionary example (WorldCom: a brief poke above 62, then a gap down that nullified it, then the support at 55 breaking) is the standing warning against treating a poke as a win.

**The support and resistance checklist.**

1. Which reaction points created this level, and how many distinct tests has it had?
2. Line or zone? Apply the width and age guideline and draw accordingly.
3. What timeframe established it, and what timeframe am I trading against it?
4. If it breaks, where does polarity say price will be retested, and what close back inside the zone invalidates the break?
5. What is the next established level beyond it, in the breakout direction? That level, not the measured target alone, frames the realistic objective.

### 13. The identification drill: how Bulkowski's approach disciplines the eye

Close the section with the practice method, because identification is a trained perception, not a talent. Bulkowski's approach, in the *Encyclopedia of Chart Patterns* and across ThePatternSite, adds four habits that ChartSchool's textbook order assumes but does not drill.

**Habit one: guidelines before statistics, every time.** For each candidate, write the Identification Guidelines table from memory for that pattern and mark each row pass, fail, or borderline before you consult any performance number. A pattern that fails the shape row does not get rehabilitated by a good rank. This ordering is the single strongest protection against motivated seeing.

**Habit two: quizzes and scored repetition.** Bulkowski publishes slider quizzes per pattern (his pennant quiz is one example) in which you classify chart after chart and get corrected. The transferable routine: keep a folder of candidate charts, label each with the checklist verdict and the confirming close or the failure, and review the folder after the outcomes are known. Your personal hit record by pattern, not your memory of your best call, is your calibration.

**Habit three: rank patterns against each other.** Cup with handle ranks near the top of his bull market table (3 of 39, 5 percent failure) and the falling wedge near the bottom (31 of 39). Eve and Adam double bottoms fail 12 percent of the time; head and shoulders tops 19 percent; descending triangles over 20 percent. Knowing the rank changes behaviour at the moment of identification: the lower the rank, the more you should demand from touches, volume, and the confirming close before the pattern earns capital.

**Habit four: measure from the breakout, to a named objective, and log the throwback.** Every pattern in this section ends with three numbers on the chart: the confirming close price, the discounted measured target, and the invalidation close, plus a note that a throwback or pullback is expected at the published rate (68 percent for head and shoulders tops, 67 percent for Eve and Adam double bottoms, roughly 60 percent for triangles). When the throwback arrives on schedule, you read it as the pattern behaving normally. When price instead closes back through the defining line and beyond the pattern extreme, you read a busted pattern and reverse the read by rule.

Run the drill on one chart a day: prior trend sentence, pivots numbered, touches counted, white space judged, duration checked against the floor, confirming line drawn, target discounted and written, invalidation written. Ten disciplined minutes per chart, in that order, is how the identification first approach becomes the way you see, rather than a table you once read.

*Primary sources for this section: Thomas Bulkowski, ThePatternSite, pattern pages for head and shoulders tops, descending triangles, Eve and Adam double bottoms and double tops, Adam and Eve double tops, cup with handle, inverted cup with handle, flags, pennants, high and tight flags, rectangle tops, broadening bottoms, broadening tops, channels, and partial declines (identification guidelines, trading tips, and bull market results as cited); StockCharts ChartSchool articles on head and shoulders top and bottom, symmetrical triangle, falling and rising wedges, flags and pennants, cup with handle, trend lines, price channels, gaps and gap analysis, and support and resistance; Peter Brandt, public Factor and interview excerpts on flag duration and head and shoulders validity; William O'Neil cup with handle criteria as tabulated by Bulkowski and ChartSchool; zeta-zetra/chart_patterns pivot and slope classification; GregoryMorse/trendln line fitting and ranking protocol.*

---

# E3. Wyckoff and Classical Charting

## How to use this section

This section teaches three linked crafts that share one chart and one discipline.

1. Wyckoff tells you what a trading range is doing: who is absorbing, who is testing, and whether demand or supply is winning.
2. Classical charting in Peter Brandt's form tells you when a pattern is finished enough to act on: a boundary line, drawn correctly, broken decisively.
3. Stan Weinstein's stage analysis tells you where the whole campaign sits in its weekly life: basing, advancing, topping, or declining.

Run them in that order of scale, not in that order of excitement. Frame first on the weekly chart with Weinstein. Read the range bar by bar with Wyckoff. Let a Brandt boundary completion supply the trigger and the invalidation. Sources are named inline throughout. The core Wyckoff text used here is the StockCharts ChartSchool presentation of the Wyckoff Method, carrying the Wyckoff Analytics tutorial text (ChartSchool, *The Wyckoff Method*). The Brandt material follows his own Factor Member Q and A page, his *Diary of a Professional Commodity Trader* (2011), and the teacher census summaries of his Factor teaching. The Weinstein material follows *Secrets for Profiting in Bull and Bear Markets* (1988) as summarised in the AlphaMethodX rule summary read for the census.

Two Wyckoff meta rules govern everything that follows, quoted in substance from ChartSchool.

- Rule One: do not expect the market to behave exactly the same way twice. The schematic is a model with variants, not a stencil.
- Rule Two: today's behaviour means something only against yesterday, last week, and last year. Every read in this section is comparative: this bar against the bars before it, this test against the last test, this range against the trend that delivered price into it.

---

## Part 1. The Wyckoff method

### 1.1 What you are looking at

Richard D. Wyckoff, writing from *Studies in Tape Reading* (1910) through his 1931 correspondence course, taught a complete routine for judging a market from its own price and volume record. Keep two charts for every name you study seriously, exactly as the tradition prescribes:

- A vertical bar chart with volume. This is the diagnostic chart. Spread, close location, and volume bar by bar live here.
- A point and figure chart. This is the measuring chart. The horizontal width of a range lives here, and with it the price objective. Hank Pruden's formulation, carried in the StockCharts point and figure construction article, is the clean division of labour: use the vertical chart to diagnose present position and trend, because it carries volume; use the figure chart to estimate the potential extent of the move.

Then work Wyckoff's five steps in order (ChartSchool, *The Wyckoff Method*):

1. Determine the broad market's present position and probable trend. Rising peaks and troughs, falling peaks and troughs, or a range until a break proves otherwise.
2. Select stocks in harmony with that trend, showing relative strength against the index. In an uptrend, a strong stock rises by a larger percentage on rallies and falls by a smaller percentage on reactions than the index. Judge it by direct chart comparison, not by reputation.
3. Select stocks with a sufficient cause to meet your objective. Cause is measured by the point and figure count in section 1.9 below.
4. Determine readiness to move. This is the phase and event analysis of the range, sections 1.4 to 1.8.
5. Time the commitment with the broad market. Prefer longs when a general uptrend has pulled back rather than when it is extended, and shorts when a general downtrend has bounced rather than when it is washed out. Do not open fresh longs into an overbought general market or fresh shorts into an oversold one.

Skipping step 1 is the most common way a beautiful individual base still fails. The range read comes fourth, not first.

### 1.2 The three laws

Every label in the schematics is an application of one of three laws (ChartSchool, *The Wyckoff Method*).

**Law 1. Supply and demand.** Price rises when demand exceeds supply and falls when supply exceeds demand. You read the balance bar by bar from price and volume together. Neither half of the pair is optional.

**Law 2. Cause and effect.** A trading range builds a cause. The markup or markdown that follows is the effect, and the size of the effect tends to be proportional to the size of the cause. Cause is not a metaphor in Wyckoff. It is counted, in columns, on the point and figure chart (section 1.9).

**Law 3. Effort versus result.** Volume is the effort. Price spread and progress are the result. When the two agree, the move is harmonious and likely genuine. When they disagree, someone large is absorbing the effort of the other side, and that absorption is the earliest warning a range gives you (section 1.8).

### 1.3 The Composite Operator as a reading device

Wyckoff asked his students to study every fluctuation as if it were planned and executed by one person: the Composite Man, also called the Composite Operator. Treat the device exactly as he presented it and as modern summaries such as the LuxAlgo Library entry on the Composite Man restate it: a useful fiction, not a literal claim that one actor controls a market. The aggregate behaviour of large, informed interests leaves footprints that look like one campaign, and reading through the fiction forces the right questions.

Use him as a checklist of intent. At every important bar or swing inside a range, ask four questions in writing:

1. If one well funded operator wanted a large position cheaply, what would he need the chart to look like right now?
2. Is he absorbing supply here (taking everything sellers offer without letting price fall), distributing supply here (feeding stock out without letting price rise), or testing here (probing to learn how much of the other side is left)?
3. Who is trapped if price moves one range width from here, and who profits?
4. What single piece of price and volume evidence on the next few bars would confirm or destroy this reading?

The device earns its keep at the two moments where a large position cannot be built in the open. To buy size, the operator needs frightened sellers, so accumulation happens into weakness, climaxes, and shakeouts. To sell size, he needs eager buyers, so distribution happens into strength, climaxes, and failed breakouts. When a move looks dramatic, ask who it serves before you ask what it predicts. Then tie the answer to checkable evidence: spread, close, and volume. A Composite Man story with no bar evidence attached is not a Wyckoff read.

### 1.4 The grammar of a range

Before the phases, fix the drawing standard for any trading range, hereafter TR.

- Draw the upper boundary at the high of the Automatic Rally in accumulation, or the Buying Climax in distribution (those events are defined below). Draw the lower boundary at the low of the Selling Climax in accumulation, or the Automatic Reaction in distribution.
- Wyckoff practitioners often call the upper boundary the Creek and the lower boundary the Ice. The older vocabulary is functional: a Sign of Strength is a jump across the Creek; a Sign of Weakness is a fall through the Ice.
- Keep the original boundaries on the chart for the life of the range. Springs, upthrusts, and tests are defined by their relationship to these lines. Redrawing the boundaries to fit the latest bars destroys the read.
- Annotate every event label at the bar where it happened, with its volume character beside it: expanding, diminished, or climactic relative to the range average. A schematic drawn from price shape alone, with no volume notes, is half a read.

### 1.5 Accumulation, Phase A to E, event by event

Assume the standard case: a downtrend arrives at a range, and the range resolves upward. Read each event by its recognition rule, not by its position in a picture.

**Phase A. Stopping the downtrend.**

- **PS, Preliminary Support.** The first substantial buying inside the downtrend. Recognition: down bars stop making easy progress; spreads widen on increased volume and closes improve off the lows. It says large buying has appeared, not that the low is in.
- **SC, Selling Climax.** Panic selling absorbed by professionals. Recognition: a very wide spread down bar or thrust on climactic, often the heaviest volume of the decline, closing well off its low or reversing sharply. ChartSchool's worked example is instructive: at the October 2011 S and P low, price broke support intraday and closed back well above it on high volume. The close, not the low print, is the climax signature.
- **AR, Automatic Rally.** The sharp bounce as selling exhausts and short covering meets returning demand. Recognition: a fast advance on widening spreads with little effort. The AR high, with the SC low, sets the TR boundaries. Measure nothing until both exist.
- **ST, Secondary Test.** A revisit of the SC area. Recognition for a good test: narrower spread than the SC, decreased volume, and a hold at or above the SC low. A test that undercuts the SC low on expanding volume is not yet a completed Phase A. Let it prove itself again.

Phase A is complete when the ST holds. Your conclusion at this point is narrow and powerful: the downtrend has been stopped. Nothing yet says a markup is coming.

**Phase B. Building the cause.**

Price ranges between the SC low and the AR high, often for far longer than Phases A, C, and D combined. Institutions accumulate here. Expect multiple secondary tests, probes toward both boundaries, and generally diminishing volume as the phase matures.

Read Phase B actively, with three running observations:

1. Where do rallies stop? Repeated failure at the same supply line tells you where stock is still for sale.
2. Where do declines stop? Rising reaction lows inside the range say demand is arriving earlier on each dip.
3. Is volume shrinking on declines faster than on rallies? That asymmetry is absorption in progress.

Upthrust type probes can occur at the top of a Phase B accumulation range. Do not relabel the whole structure distribution because of one probe. In Phase B the question is always comparative: is supply smaller than it was at the last test of the same level?

**Phase C. The decisive test.**

- **Spring, or shakeout.** Price moves below TR support established in Phases A and B, then quickly reverses back inside the TR. Recognition rules, all four required for the textbook case:
  1. There is a pre existing TR with a drawn support line that has already been tested.
  2. Price penetrates that support, briefly, taking out the stops and the weak holders below it.
  3. Price recovers back inside the range promptly rather than building a new lower range.
  4. The follow through test (below) shows supply is gone.
- **Test of the spring.** After the spring, price revisits the spring low area. The high probability version is a low volume test: narrow spread, volume clearly diminished versus the spring and versus Phase B declines, and a hold at or above the spring low, often making a higher low. ChartSchool's rule is direct: a low volume spring, or a low volume test of a shakeout, marks supply exhausted and is a high probability point to initiate at least a partial long position.
- **The high volume spring variant.** A spring on heavy volume means substantial supply was met and absorbed, but it demands a more careful, and usually lower volume, test before you trust it, because heavy supply existed at the low. Weight the test, not the spring bar.
- **Phase C without a spring.** Wyckoff Analytics, via ChartSchool, states this variant plainly: Phase C can also occur as a test at a higher level inside the TR, with no penetration of support at all. This is the hard case to identify in real time. Your evidence is a sequence of higher lows on diminishing volume late in Phase B, followed promptly by a Sign of Strength. Label it provisionally and let Phase D confirm or deny it.

**Phase D. Demand dominates.**

- **SOS, Sign of Strength.** An advance on widening spread and increasing volume that carries at least to the top of the TR, and in the full case through resistance: the jump across the Creek. Recognition: the up bars in this swing are visibly wider than the range's typical up bars, volume expands, and closes sit near the highs. One strong bar that stalls at resistance is an attempt. A swing that clears the top and holds is a Sign of Strength.
- **LPS, Last Point of Support.** The reaction after an SOS. Recognition: smaller spread and diminished volume than the SOS advance, holding at or above former resistance, which has now flipped to support. There can be more than one LPS. Each LPS that holds higher, on less volume, strengthens the read.
- The Phase D sequence to memorise: advances strong, reactions weak. SOS, then LPS, then another SOS. If reactions start matching advances in spread and volume, demand is not dominating and the label is wrong.

**Phase E. Markup.**

Price leaves the TR and trends. Demand is in full control, reactions are short lived, and re accumulation ranges, the stepping stones, may form on the way up. Your work in Phase E changes character: stop labelling the old base and start reading each reaction against the trend. A stepping stone is a small accumulation TR inside markup, and it gets the same A to E treatment at its own scale.

**The five classical buy points** (ChartSchool's summary of the full cycle):

1. At the spring or selling climax. Aggressive, highest reward, highest failure rate.
2. On the breakout through resistance on expanding volume.
3. On the throwback to broken resistance turned support.
4. On a re accumulation breakout inside markup.
5. On a pullback to trendline support, prior consolidation support, or the 50 percent retracement of the last up leg.

### 1.6 Distribution, Phase A to E, the mirror read

Assume an uptrend arrives at a range and the range resolves downward. The events mirror accumulation, with one asymmetry Wyckoff himself stressed via ChartSchool: tops are usually long and drawn out, bottoms relatively short and violent. Give a suspected top more time to prove itself than a suspected bottom.

**Phase A. Stopping the uptrend.**

- **PSY, Preliminary Supply.** First substantial selling inside the uptrend: widening spreads on increased volume on down moves, rallies losing ease.
- **BC, Buying Climax.** A sharp advance on heavy volume met by professional selling. Recognition: climactic volume, wide spread, and a close that fails to hold the high ground the bar reached.
- **AR, Automatic Reaction.** The decline that follows as buying exhausts. The AR low, with the BC high, sets the TR boundaries.
- **ST, Secondary Test.** A revisit of the BC area on diminished volume and narrower spread, ideally failing below the BC high.

**Phase B. Building the cause for markdown.** Ranging at the top. The running tell ChartSchool draws from the 2007 Dow top is volume character: down day volume beginning to exceed up day volume inside the range. Rallies are sold earlier each time. Support tests multiply and each bounce off the Ice is weaker.

**Phase C. The trap at the top.**

- **UT, Upthrust.** A brief move above TR resistance that fails back inside the range.
- **UTAD, Upthrust After Distribution.** The late, larger version: a move above the BC high, late in the range, that fails. This is the classic bull trap, engineered in Composite Man terms to transfer the operator's remaining stock to late, eager buyers and to stop in short sellers whose covering adds demand to sell into.
- Recognition rules for UT and UTAD, mirroring the spring: a pre existing TR with a drawn resistance line; a penetration above it; a prompt failure back inside; and a subsequent test, a weak rally back toward the penetration area on diminished volume, that cannot recover the high. Distribution can complete with no UTAD at all, a schematic variant ChartSchool notes explicitly, in which case Phase C shows only as a weak test at the top of the range.

**Phase D. Supply dominates.**

- **SOW, Sign of Weakness.** A decline on widening spread and increased volume toward or through TR support: the fall through the Ice. Mirror of the SOS.
- **LPSY, Last Point of Supply.** A weak, low volume rally back to former support, now resistance, after an SOW. The textbook short initiation point, the mirror of the LPS.
- The Phase D sequence to memorise: declines strong, rallies weak.

**Phase E. Markdown.** Price leaves the TR downward. Re distribution ranges form as stepping stones on the way down.

**The five classical sell and short points** mirror the buy points: the lower peak inside distribution, the support breakdown on expanding volume, the throwback to broken support turned resistance, the re distribution breakdown in markdown, and the 50 percent bounce meeting resistance.

### 1.7 Step by step: reading one base by eye

This is the routine this section exists to teach. Run it on paper, in order, on any base you intend to call Wyckoff. Allow no step to be skipped because a later step looks exciting.

1. **Set the frame.** Weekly chart first. What trend delivered price into this range, and how long and steep was it? Note the general market's position (five step routine, step 1).
2. **Draw the box.** Mark the climax low and the automatic move that followed it. Draw both boundaries and freeze them.
3. **Prove Phase A.** Can you point to PS, SC, AR, and ST with volume notes for each? If the ST has not held, you have a falling market with a bounce, not a base. Wait.
4. **Work Phase B comparatively.** List each test of support and each test of resistance in date order. Beside each, write spread and volume versus the previous test of the same level. You are building the absorption ledger: same level, less effect, less volume means supply is shrinking.
5. **Interrogate the edges with effort versus result.** At each boundary approach, ask the section 1.8 question: how much volume did it take to move price how far?
6. **Wait for Phase C to declare itself.** Either a spring below support with a prompt recovery, or the hard case, a higher low test pattern late in the range on dry volume. Write down, before the next session, what a successful test must look like: the price area it may reach, the volume ceiling it must stay under, and the close it must print.
7. **Judge the test, not the hope.** A successful low volume test is permission to act at least partially. A test that expands in volume and spread through the spring low is a failed spring. The range read resets, and the invalidation in section 1.10 governs.
8. **Demand Phase D confirmation.** Look for the SOS: wide spreads up, expanding volume, a run at or through the Creek. Then look for the LPS: a quiet reaction holding above the flipped level. An SOS with no LPS, followed by a heavy volume fall back into the range, is a failed Sign of Strength. Relabel it honestly: in a range at highs that same bar would be read toward upthrust.
9. **Count the cause.** Build or update the point and figure chart and take the horizontal count (section 1.9). If the count cannot reach your minimum objective, the base, however pretty, is the wrong vehicle. This is five step routine step 3, applied late on purpose: count when the range is mature enough for the count to mean something.
10. **Write the read in one paragraph.** Phase, last event, next event you expect, the level that proves you wrong, and the count objective. File it with the dated chart. Wyckoff reading improves only when yesterday's labels are graded against today's bars.

### 1.8 Effort versus result, bar by bar

This law does most of the daily work. Effort is volume. Result is price progress: the bar's spread and where it closes, and at swing scale, how far the swing travelled.

| What you see | Harmonious or divergent | The Wyckoff read |
|---|---|---|
| Wide spread up bar, closing near its high, on expanding volume | Harmonious | Demand is effective. Inside a range top approach, this is SOS character. |
| Wide spread down bar, closing near its low, on expanding volume | Harmonious | Supply is effective. Inside a range, this is SOW character. |
| Heavy volume, narrow spread, little price progress | Divergent | Absorption. At support, sellers are being absorbed by a large buyer. At resistance, buyers are being absorbed by a large seller. Location decides the direction of the read. |
| Heavy volume thrust below support that closes back inside the range | Divergent at the edge | Spring or climax absorption. Supply was spent into hands that wanted it. Now demand the low volume test. |
| Heavy volume thrust above resistance that closes back inside the range | Divergent at the edge | Upthrust absorption. Demand was spent into hands that were selling. Now watch for the weak test rally. |
| Rally on diminishing volume into a known supply line | Divergent | No demand behind the advance. In distribution this is LPSY character; in accumulation Phase B it warns the Creek is not ready to be jumped. |
| Decline on diminishing volume into a known demand line | Divergent | No supply behind the decline. In accumulation this is test character; late in Phase B it is the footprint of a coming spring or SOS. |
| Successive tests of the same level, each on less volume and narrower spread | Progressively divergent for the attacking side | The attacking side is exhausting. This comparative sequence, not any single bar, is the strongest Phase B evidence. |

Three working rules keep the table honest:

- Always compare against the range's own norms. Heavy and light mean heavy and light for this stock in this range, judged against its recent average volume and typical spread.
- Location outranks shape. The identical heavy volume narrow bar means opposite things at the Ice and at the Creek.
- One divergent bar is a warning. A divergent swing, three to five bars telling the same story, is evidence.

### 1.9 Cause and effect: the point and figure count

The count converts a finished or maturing range into an objective. The full construction rules are in Part 3. The Wyckoff procedure is:

1. On the point and figure chart of the range, choose the count line: a horizontal row through the range where most columns are filled, classically anchored at the row of the Last Point of Support or the spring for an accumulation count.
2. Count the columns the count line crosses, including the range walls.
3. Multiply: columns times box size times the reversal value (for a 3 box reversal chart, multiply by 3; classic Wyckoff counting was done on 1 box reversal charts, where the multiplier is simply the box size).
4. For an upside objective, add the product to the range low for the conservative objective. Practitioners also compute from the count line level itself. For a downside objective from distribution, subtract the product from the range high or the count line level.
5. Treat the result as a zone for planning, never as a promise, and take more than one count where the range offers nested counts at different rows.

Worked example in round numbers: a base prints 20 columns along its count line on a 1 point box, 3 box reversal chart. Projection equals 20 times 1 times 3, which is 60 points. From a range low of 40, the conservative objective is 100. ChartSchool's own worked examples follow exactly this arithmetic at index scale, including a 34 column count on the 2007 S and P top and nested 20 column and 42 column counts from the 2009 low that projected to different, successively larger objectives, with Wyckoff's own caution attached: do not take projections too seriously. Use the count to size the opportunity and to reject undersized causes, and use stepping stone counts in Phase E as confirmation: when a re accumulation range partway up projects to roughly the original objective, the campaign is confirming itself.

### 1.10 Invalidation and variants, stated as standards

- A spring fails when price closes and builds below the spring low on expanding spread and volume. At that moment the event is no longer a shakeout. It is a breakdown, and any long exposure taken on the spring read is governed by that level.
- An SOS fails when price falls back through the Creek on heavy volume and cannot recover it on the next rally. Failed strength at the top of a range is distribution evidence.
- An upthrust is confirmed as a trap only by what follows: a weak test and then an SOW. Price merely poking above resistance and continuing upward on expanding spreads is a breakout, and the UT label must be surrendered.
- Re accumulation and re distribution are not exceptions to the schematic. They are the schematic running again, inside markup or markdown, at a smaller scale. Label them as their own A to E and count them as stepping stones.
- When two labels fit, prefer the one that requires the least invention, write the alternate beside it, and name the bar that will decide between them. That habit, preferred read plus alternate plus deciding level, is the professional form of every Wyckoff opinion.

**Wyckoff eye checklist. Run it aloud over any range.**

- [ ] Prior trend named, and general market position noted.
- [ ] Boundaries drawn from the climax and automatic move, and left fixed.
- [ ] Phase A events identified with volume character, ST holding.
- [ ] Phase B tests listed in order, each compared with the last test of the same level.
- [ ] Effort versus result judged at both boundaries.
- [ ] Phase C event named: spring, upthrust, or the no spring test variant.
- [ ] Test criteria written in advance: area, volume ceiling, required close.
- [ ] SOS or SOW confirmed by spread, volume, and follow through, not by one bar.
- [ ] LPS or LPSY holding at the flipped boundary.
- [ ] Point and figure count taken, objective sufficient for the risk.
- [ ] Invalidation level written on the chart before any position is considered.

---

## Part 2. Classical charting, Peter Brandt's discipline

### 2.1 Lineage and posture

Brandt states his lineage without decoration: he is a classical chartist in the line of Richard W. Schabacker (1934), carried forward by Edwards and Magee in *Technical Analysis of Stock Trends* (1948). The rules already exist. The chartist's job is to apply them as written and to refuse to invent a pattern to fit a bias. Brandt's best known public teaching act is exactly that refusal: rejecting widely shared pattern labels, in print, because the formation violates a duration, symmetry, or volume condition. Learn that reflex. A rejected pattern is this method working, not failing.

His own condensed approach, from the Factor Member Q and A page in his words in substance: he trades primarily futures and forex; he trades breakouts of certain classical patterns, namely horizontal patterns, rectangles, right angled triangles, and head and shoulders patterns, plus pennants and flags during an ongoing strong trend; 10 to 26 weeks is his sweet spot for duration; maximum risk is 1 percent of nominal capital per trade, sized from entry and initial protective stop; he advances stop protection aggressively; he takes profits at the target determined by the completed pattern; and his long term win rate is under 50 percent, with more than 80 percent of profits coming from under 20 percent of trades. Hold those numbers in mind while learning the geometry. In this school the pattern does not predict. It organises a trade: a level to enter on, a level that proves you wrong, and a level to take profits at.

Brandt's self test, quoted in the teacher census from his teaching: when I place a trade, I ask whether a year from now, looking back at the chart, I will be able to see the day and the price at which I took the position. If yes, it is a good trade. Apply it before entry, not after.

### 2.2 The primacy of the boundary line

Everything in Brandt's method hangs on one drawn object: the pattern's boundary line. Get it right and the rest of the method is arithmetic. Get it wrong and every later step inherits the error.

Drawing standards:

1. **Draw the boundary through the congestion, not through the extremes.** In *Diary of a Professional Commodity Trader*, Brandt's silver lesson is explicit: his lower boundary was drawn through the May 20 low area to best describe the price congestion, and the single bar that poked beyond it is named an out of line movement and excluded from the line. A boundary describes where trade actually clustered and turned. One stray print does not move it.
2. **A boundary needs repeated contact.** One touch is a point. Two touches make a candidate line. The pattern earns trust as later turns keep respecting the same line. This agrees with the wider canon: Bulkowski's identification guidelines require minimum touches per line, and ChartSchool requires two or more points to establish a trendline and further points to validate it.
3. **The boundary is the trade.** Entry is defined by its break, invalidation by a return through it, and the target by the pattern height measured from it. If you cannot draw one clean boundary, there is no classical trade, whatever the shape in the middle looks like.
4. **Name the flipped boundary the ice line.** After a valid completion, the broken boundary becomes the line price should not reclaim. Brandt's repeated observation in *Diary*: on the retest that follows a major completion, price is characteristically unable to get back beyond the ice line. A retest that holds at the ice is confirmation. A close back beyond it is the failure signal, and it usually arrives fast.

### 2.3 Rectilinear patterns: why Brandt prefers straight lines and right angles

Brandt divides patterns by the geometry of their boundaries, and his preference is a stated rule, not a taste (Factor teaching and Member Q and A):

- **Preferred: horizontal, or rectilinear, patterns.** Rectangles, with two horizontal boundaries. Right angled triangles, ascending and descending, with one horizontal boundary and one diagonal boundary. Head and shoulders patterns, whose decisive boundary, the neckline, is horizontal or nearly so.
- **Deprioritised: diagonal patterns.** Symmetrical triangles, wedges, and formations bounded by two sloping lines. Brandt minimises these because both boundaries move, the completion point keeps shifting, and the formation readily morphs into a larger pattern. His stated reasoning in teaching transcripts: horizontal patterns are far more reliable than diagonal patterns, because a flat boundary line fixes the exact price at which the pattern completes and the exact price at which it has failed.
- **The one diagonal exception with strict terms: flags and pennants inside a strong ongoing trend.** And here the duration rule does the guarding (Brandt's public flag ruling, 2026, captured in the teacher census): a dependable flag or pennant completes and breaks out within about 4 weeks. It is a brief pause at half mast after an aggressive move. An upward sloping channel of 7 to 10 weeks is not a flag, whatever it resembles, and must not be traded with flag expectations.

Why the horizontal boundary matters, in practical terms a student can verify on any chart: a horizontal line is a price, and a price can be watched, alerted, and acted on identically by every reader of the chart. Trapped capital is also defined by it. Everyone who bought inside a rectangle bought under one ceiling. When that ceiling breaks, the entire population of the pattern is profitable at once and the shorts inside it are wrong at once. That is the fuel Brandt points to in the maxim the longer the base, the higher the space.

### 2.4 Recognition standards for the preferred set

**Rectangle.** Two horizontal boundaries, each touched at least twice as distinct turns, with price crossing the space between them rather than hugging one side. Duration in Brandt's sweet spot: 10 to 26 weeks for a major trade. Completion: a decisive close beyond either boundary. Target: the height of the rectangle projected from the breakout boundary. Role: continuation or reversal, decided by the prior trend and by which boundary breaks. Do not pre assign its direction while price is still inside it. Brandt's stated habit is to avoid trades while price is range bound and to act on completed patterns only.

**Right angled triangle.** Ascending: a horizontal resistance line with rising reaction lows beneath it. Descending: a horizontal support line with falling reaction highs above it. The horizontal side is the boundary that matters: completion is a close through the flat side, never through the sloping side. The sloping side is evidence, showing buyers arriving earlier (ascending) or sellers arriving earlier (descending). Target: maximum height of the triangle projected from the breakout point.

**Head and shoulders.** Brandt's validity conditions, from his Factor teaching as captured in the census, are stricter than the popular version:

- Three distinct peaks (or troughs, inverted), with the head clearly the extreme.
- The right shoulder must fail: lower than the head on a top, and it must form as a genuine separate turn, roughly symmetric with the left shoulder in time and height.
- The neckline connects the two reaction lows between the peaks (the two reaction highs, inverted). Horizontal or slightly sloped is a neckline. A steeply rising line under the pattern is wedge logic and disqualifies the H and S label.
- Volume must be greatest on the left shoulder and head, and lightest on the right shoulder. Brandt publicly rejected a widely advertised index head and shoulders top on exactly this ground: the largest volume sat in the right shoulder, which is the signature of continuing demand, not of a failing top.
- Completion: a close through the neckline. Then the ice line logic applies to the neckline on any retest.

**Flags and pennants, continuation only.** A sharp, near vertical prior move, the pole. A brief, tight counter drift or small triangle, the flag, lasting days to about 4 weeks on clearly diminishing volume. Completion: a close through the flag boundary in the direction of the pole. A pause that drags past the duration limit, deepens into a real correction, or expands in volume has left the category. Relabel it as the larger consolidation it has become.

### 2.5 Completed, fulfilled, failed, and recompleted

Brandt's vocabulary separates four states that casual charting merges into one. Keep them separate in your journal, because each state has a different correct action.

1. **Completed.** The pattern is finished as a formation when price closes decisively beyond its boundary line. Before completion there is no trade, only a pattern under construction. Brandt's public formulation, repeated across his posts: no breakout yet, so no trade. Completion is an event on a specific date at a specific close, and it is the first moment entry, stop, and target all exist simultaneously.
2. **Fulfilled.** The completed pattern fulfils when price reaches the objective the pattern itself projects: its height, measured at its widest relevant span, projected from the completion boundary in the direction of the break. Brandt's routine is to take profits at the target determined by the completed pattern and to advance protection at chart pivot points on the way, on at least half the position. A fulfilled pattern has done its full job. Anything beyond the objective is a new pattern's business, not this one's promise.
3. **Failed.** The completion is falsified when price closes back beyond the ice line, the boundary it had just broken. Treat the failure immediately and mechanically: the premise is gone. Note the wider canon agreement: Bulkowski's busted pattern doctrine treats a break that reverses through the opposite side as a new signal in the new direction, and Adam Grimes teaches pattern failure itself as a trade. Brandt's contribution is the discipline: the ice line decides, not your hope for a second chance.
4. **Recompleted.** A pattern that completes, fails back inside, builds again, and completes a second time through the same boundary. *Diary* treats recompletion as a real and tradable development, and warns that belabored patterns, formations that have ground on and on with repeated false completions, lose quality. Judge a recompletion by its freshness: a tight, quiet rebuild under the same boundary can be excellent; a wide, noisy, months long saga usually is not. The GBP/CHF rounding top in *Diary* is the worked temperament lesson: a premature breakout, a return above the ice line, then the valid breakout. Rounding patterns, Brandt notes, are notorious for not providing clean breakouts, which is precisely why the close beyond the boundary, and not the first poke, is the standard.

Two further Brandt standards complete the picture:

- **The close is the verdict.** The most significant price of the day is its close; of the week, Friday's close. Intraday penetrations of a boundary are information. Closes are decisions.
- **Possibilities, not probabilities.** From his Member Q and A: chart patterns represent possibilities, not probabilities, and certainly not certainties; the better metric is the win to loss ratio the pattern's geometry offers, stop to target. Before entering, compute it from your drawn lines: distance from completion close to ice line failure versus distance from completion close to objective. If the geometry does not pay for being wrong more often than right, the pattern, however handsome, is not a Brandt trade.

**Brandt eye checklist. Run it before calling any pattern tradable.**

- [ ] Lineage check: is this one of the preferred forms (rectangle, right angled triangle, head and shoulders, or a brief flag or pennant in trend)?
- [ ] Duration check: major patterns in the 10 to 26 week sweet spot; flags and pennants inside about 4 weeks.
- [ ] Boundary drawn through the congestion, out of line movements excluded, at least two clean contacts.
- [ ] For head and shoulders: symmetry acceptable, right shoulder failing, neckline near horizontal, volume lightest on the right shoulder.
- [ ] Completion defined in advance as a specific close beyond a specific price.
- [ ] Ice line failure level and measured objective both written down, and the ratio between them acceptable.
- [ ] Retest plan settled: act on completion, on the ice line retest, or split between them. Decided now, not improvised later.
- [ ] The one year test passed: will this entry be visible on the chart a year from now?

---

## Part 3. Point and figure basics, the noise filter

### 3.1 What point and figure removes, and what it keeps

A point and figure chart plots price change only. Time is not an axis. Volume is not shown. A column advances only when price reverses by a set amount. The result, in mplfinance and finplot terms from the GitHub census, is a chart type alongside candle, line, and renko whose entire purpose is filtering: small fluctuations never print, so the support, resistance, and range width that survive are the ones built from real movement. Wyckoff used it as the cause and effect chart. Brandt's tradition uses it as a second opinion on congestion. Use it the same way: not instead of the bar chart, but after it.

### 3.2 Construction, step by step

1. **Choose the box size.** One box equals a fixed price increment. The traditional scaling rule carried in the StockCharts construction article: above 100, a box is 2 points; from 20 to 100, a box is 1 point; from 5 to 20, a box is one half point; below 5, smaller still. Modern practice often sets box size from average true range instead. Either way, write the box size on the chart. A count taken at one box size cannot be checked at another.
2. **Choose the reversal value.** Three boxes is the standard chart: price must reverse by three full boxes to start a new column. One box reversal charts, the classic Wyckoff counting chart, print far more columns and far more noise. A three box chart reads, in time feel, roughly like a weekly bar chart.
3. **Plot columns of X and O.** Rising price prints a column of Xs, one X per full box gained. When price falls by the full reversal amount, move one column right and begin a column of Os, one O per full box lost. A move that does not complete a full box prints nothing. That silence is the filter working.
4. **Respect the two entry rule for counting charts.** The StockCharts construction article, citing Pruden, requires at least two entries in a column for an accurate horizontal count on Wyckoff construction. Single print columns distort the count.

### 3.3 Reading standards

- **Horizontal levels dominate.** On point and figure, support and resistance appear as rows repeatedly filled across many columns. A row that has stopped price six times is visible at a glance, with no time axis diluting it.
- **The elementary signals.** A double top is a column of Xs that reaches the exact top of the prior X column; a buy signal prints when a column of Xs exceeds the prior X column by one box. The double bottom and the sell signal mirror it. Triple tops and bottoms, the same level broken after three tests, carry more weight, matching the touch logic of the bar chart canon.
- **Trendlines on point and figure are drawn at 45 degrees** from a significant top or bottom, the bull support and bear resistance lines. They are conventions of the grid, not fitted lines, which is their virtue: no discretion in the angle.
- **Congestion is measurable.** Count the columns across a completed range and you hold the cause in a single integer. That is the bridge back to section 1.9.

### 3.4 Choosing settings without fooling yourself

- Box too small: every wiggle prints, columns multiply, and counts inflate. You have rebuilt the noise you came here to remove.
- Box too large: real tests vanish, springs and upthrusts may not print at all, and the range looks cleaner than it was.
- The professional habit: keep one standard setting per instrument, fixed in advance, and use it for every count. Changing box size until the objective suits your hopes is the point and figure form of redrawing a Wyckoff boundary, and it is forbidden for the same reason.
- Remember the division of labour from section 1.1. Point and figure carries no volume, so it cannot judge effort versus result, springs, or tests. Any event label still has to be earned on the bar chart.

**Point and figure eye checklist.**

- [ ] Box size and reversal value written on the chart and unchanged from your standard for this instrument.
- [ ] Columns built only from full box moves; no partial prints.
- [ ] Key rows identified by repeated fills, not by one column's extreme.
- [ ] Count line chosen through the fullest row of the range, anchored at the LPS or spring row for accumulation.
- [ ] Columns counted including the walls; arithmetic shown on the chart: columns times box times reversal, added to or subtracted from the stated base level.
- [ ] Objective recorded as a zone, and the bar chart checked for real levels between here and there.

---

## Part 4. Weinstein stage analysis, the weekly frame

### 4.1 The setup

Stan Weinstein's *Secrets for Profiting in Bull and Bear Markets* (1988) reduces the weekly frame to one chart and one line: the weekly chart, and the 30 week simple moving average, the average of the last 30 weekly closes, roughly a 150 day average on a daily chart. Add Mansfield relative strength against the market, and volume on the weeks that matter. That is the whole instrument panel. Its power is that it classifies every chart you own in under a minute, identically, every week (AlphaMethodX rule summary of the book, read for the census; the @stageanalysis practice account applies the same rules as a weekly watchlist discipline).

Reading order is fixed and is Weinstein's most quoted structural rule: forest before trees.

1. The major averages and the advance decline line: what stage is the market in?
2. The groups and sectors: which are in Stage 2?
3. The individual stocks inside those groups.

A Stage 2 stock in a Stage 4 market and a Stage 4 group is fighting two currents. Weinstein's order exists to stop you from falling in love with the tree.

### 4.2 The four stages, recognition rules

| Stage | Price versus the 30 week average | Average's slope | Chart character | Standing instruction |
|---|---|---|---|---|
| Stage 1, Basing | Price crosses above and below the average repeatedly | Flat, after having fallen | A sideways range after a decline; rallies stop at the same ceiling; declines lose momentum | Watch and prepare. No buying yet. This is where Wyckoff accumulation does its work. |
| Stage 2, Advancing | Price above the average and holding above it on reactions | Rising | Higher highs and higher lows; breakouts hold; pullbacks find support at or above the average | The only stage for longs. Buy the entry rules in 4.3. |
| Stage 3, Topping | Price whips around the average, making less progress on each push | Flattening | A sideways range after an advance; failed breakouts appear; support tests multiply | Sell into strength, tighten stops. This is where Wyckoff distribution does its work. No new longs. |
| Stage 4, Declining | Price below the average, rallies failing under it | Falling | Lower highs and lower lows; bounces are sold | Untouched for longs, however cheap it looks. The short side's home stage. |

Stages are conditions, not a fixed sequence. A base can fail back into Stage 4. A topping range can resolve upward and re enter Stage 2. A sharp break can skip a stage. Classify what the chart shows this week, with the average's slope as the deciding evidence, and never argue a stock into a stage because of where it has been.

Two slope judgements do most of the work in practice:

- Compare the average now with the average about four weeks ago. Clearly higher is rising, clearly lower is falling, indistinguishable is flat. Flat after a decline points to Stage 1; flat after an advance points to Stage 3. The trend before the flatness decides which.
- Judge breaks on weekly closes. A daily spike through the average, or through a base ceiling, is not a stage change. Weinstein's frame is deliberately slow, and its slowness is the filter.

### 4.3 The Stage 1 to Stage 2 entry, in full

This is the single most valuable transition in the system, and Weinstein specifies it tightly:

1. **The base exists.** A Stage 1 range with a defined ceiling: the price where earlier rallies stopped. Draw it. It is the same line Brandt would call the boundary and Wyckoff would call the Creek, which is why the three methods in this section interlock so cleanly.
2. **The breakout.** A weekly close above the ceiling of the base, with the 30 week average flattening or turning up beneath it. Not an intraday poke. Not a daily close. A weekly close.
3. **Volume confirmation.** The breakout week should show volume around twice normal, as a single week surge or as a multi week build up into the break. A quiet breakout through a major ceiling is suspect.
4. **Relative strength confirmation.** Mansfield relative strength above zero, or rising decisively toward it. The stock should be beating the market, not being carried by it.
5. **Overhead check.** Look above the breakout for old peaks. A breakout that runs immediately into a shelf of prior highs has supply waiting. Prefer the name with clear space above it.
6. **The second entry.** If the breakout week is missed, the first pullback to the breakout level, holding at or just above it on lighter volume, is Weinstein's secondary entry. Recognise it for what it also is: Wyckoff's LPS and Brandt's ice line retest, described by a third author. When three schools name the same bar, pay attention.

**Stop discipline** (Weinstein, via the AlphaMethodX summary):

- The initial stop goes under support, meaning under the low of the base, never at an arbitrary percentage below the entry. A 10 percent stop that sits in mid air respects nothing on the chart.
- Raise the stop as the advance develops, under each successive significant pullback low and under the rising 30 week average. Never lower a stop. Ever.
- Set stops just under round numbers, where clustered orders sit above the level, rather than exactly on the obvious figure.
- Tighten when the average flattens. That flattening is Stage 3 arriving, and it is a warning to protect, not a signal to hope.
- Do not hold a Stage 4 stock for taxes, dividends, a low price to earnings ratio, or admiration for the company. None of those changes the chart.

**The short side mirrors everything.** The Stage 3 to Stage 4 transition, a weekly close below the floor of a topping range with the average flattening or turning down, on expanding volume and weak relative strength, is the short entry, with stops above the range and trailed above successive rally highs.

### 4.4 The weekly review ritual

Weinstein's method is a routine before it is a set of signals. Run it on the same day each week, after the Friday close:

1. Classify the major averages: stage, average slope, relative strength direction.
2. Classify each sector or group you follow. Mark Stage 2 groups.
3. Classify every holding. Any holding that has entered Stage 3 gets its stop tightened in writing. Any holding in Stage 4 is sold by rule, not debated.
4. Scan Stage 1 bases inside Stage 2 groups for ceilings about to be tested. For each candidate, draw the ceiling, note the average's slope, and pre write the breakout volume and relative strength evidence you require.
5. Grade last week's classifications against this week's bars. A stage call that keeps flipping weekly means you are reading daily noise through a weekly tool. Slow down.

**Weinstein eye checklist.**

- [ ] Weekly chart, 30 week simple average plotted, slope judged against four weeks ago.
- [ ] Stage named for market, group, and stock, in that order.
- [ ] For a buy candidate: Stage 1 base with a drawn ceiling, weekly close through it, average flattening or rising.
- [ ] Breakout week volume about twice normal, or a visible multi week build up.
- [ ] Mansfield relative strength positive or rising decisively.
- [ ] Overhead peaks above the breakout checked and named.
- [ ] Stop placed under structure, with the raise only rule understood.
- [ ] Absolute rule honoured: no long position held or opened below a declining 30 week average.

---

## Part 5. The three methods working as one read

Close with a single worked sequence, because in practice you will never use these methods separately.

**The frame (Weinstein).** A stock has declined for a year, then ranged for five months. The 30 week average, falling all year, has been flat for eight weeks. Stage 1. Its group has just turned up; the market is basing. Forest and trees both permit attention.

**The range read (Wyckoff).** Inside the five month range you can label a Selling Climax on climactic volume, an Automatic Rally that set the ceiling, and three Secondary Tests, each narrower and quieter than the last. Last month price slipped below the range floor for four sessions and recovered: a spring. Its test last week printed the lowest volume of the entire range and held above the spring low. The cause, counted on the point and figure chart at your standard box size, projects well beyond the next overhead level. Phase C, tested. Phase D is what you now require.

**The trigger (Brandt).** The ceiling of the range is also a clean horizontal boundary with four contacts, a rectilinear top. There is no trade until a close beyond it. You write down, in advance: the completion price, the ice line level a retest must hold, the pattern height objective, and the failure close back inside that ends the idea.

**The event.** Price closes the week above the ceiling on twice normal volume, spread wide, close at the high: simultaneously Weinstein's Stage 2 breakout week, Wyckoff's Sign of Strength jumping the Creek, and Brandt's completed pattern. Three methods, one bar, no contradiction. The pullback two weeks later, quiet, holding at the ceiling, is LPS, ice line retest, and Weinstein's secondary entry at the same price, for the same reason, in three vocabularies.

That convergence is the standard this playbook holds a chart read to. When the vocabularies disagree, the disagreement is the information: a Wyckoff spring inside a Stage 4 decline with a falling 30 week average is a speculation against the frame, sized and labelled as such, or not taken. A Brandt completion with no Wyckoff cause behind it and no volume on the break is a pattern floating on nothing. Name the missing leg in your journal, in the open, every time.

**Final combined checklist.**

- [ ] Weinstein: market, group, stock staged on weekly closes against the 30 week average.
- [ ] Wyckoff: phase and last event labelled with volume evidence; next expected event written down.
- [ ] Effort versus result: harmonious where the read requires strength, divergent where it requires absorption.
- [ ] Cause counted on point and figure at standard settings; objective sufficient.
- [ ] Brandt: boundary drawn through congestion, completion defined as a close, ice line and objective written.
- [ ] Invalidation agreed by all three methods, or the disagreement named and the position treated accordingly.

---

## Sources named in this section

- StockCharts ChartSchool, *The Wyckoff Method*, presenting the Wyckoff Analytics tutorial text: three laws, five step routine, accumulation and distribution schematics with Phases A to E, springs, upthrusts, SOS, SOW, LPS, LPSY, and point and figure cause counting examples.
- Richard D. Wyckoff, *Studies in Tape Reading* (1910), *How I Trade and Invest in Stocks and Bonds* (1924), and the 1931 correspondence course: origin of the method and of the Composite Man.
- Hank Pruden, *The Three Skills of Top Trading*, as cited in the StockCharts article *Intro to Point and Figure Construction*: Wyckoff point and figure construction, the two entry rule, and the vertical chart versus figure chart division of labour.
- LuxAlgo Library, entries on the Composite Man and on Point and Figure Cause Counting: modern restatements of the composite operator as a reading device and of the horizontal count formula.
- Peter Brandt, Factor Member Q and A collection, peterlbrandt.com: his condensed approach, preferred horizontal patterns, 10 to 26 week sweet spot, risk and profit taking routine, and possibilities not probabilities doctrine.
- Peter Brandt, *Diary of a Professional Commodity Trader* (Wiley, 2011): boundary drawn through congestion, out of line movements, the ice line and retest behaviour, pattern completion, recompletion, and objectives.
- Peter Brandt, Factor teaching and public posts as captured in the external teacher and X censuses: head and shoulders volume and symmetry validity, the 4 week flag and pennant duration limit, and horizontal over diagonal pattern preference, in the Schabacker and Edwards and Magee lineage.
- Stan Weinstein, *Secrets for Profiting in Bull and Bear Markets* (1988), via the AlphaMethodX rule summary read for the census: the four stages, the 30 week average, forest to trees order, breakout volume and relative strength confirmation, and structure based stop discipline.
- Thomas Bulkowski, ThePatternSite, and StockCharts ChartSchool pattern articles: corroborating standards for touch minima, close based confirmation, polarity, and busted patterns, cited where they agree with the Brandt standards above.
- mplfinance and finplot documentation via the external GitHub census: point and figure as a standard chart type in the modern drawing toolkit.

---

# Section E4: Practitioner Craft

## How Working Chart Readers Actually Operate

Volume II, Section E4. Sources are named inline throughout. The census behind this section covers the practitioner forums (Elite Trader, Forex Factory, TradingView Education, Reddit communities), the X chart teachers, and the classic teachers (Stan Weinstein, Peter Brandt, Mark Minervini, Linda Raschke, Adam Grimes, Brian Shannon, Thomas Bulkowski, the Wyckoff tradition via StockCharts ChartSchool, and the CMT Program syllabus).

The pattern across all of them is simple to state and hard to do. Masters do not start with a pattern. They start with a routine, run the same routine in the same order every time, draw very little, write the invalidation before the entry, and then grade the read later against what price actually did. This section teaches that operating system in the order a working reader uses it: first look, drawing, watchlist, journal, review, drills, and the heuristics that hold the whole craft together.

## 1. The First-Look Routine

### 1.1 The rule underneath every routine

Reading order is always top down and outside in. No community in the census teaches trigger first reading.

- Forex Factory, Strat's PASR: Big Boss (monthly) first, then Boss (weekly), then Worker (daily). Lower timeframes such as H4 and H1 are management timeframes only.
- Forex Factory, Candle Cartel: one post per pair walks Monthly, Weekly, Daily, 4H, 1H, with one verdict per timeframe and a single conclusion that names the invalidation.
- Elite Trader, IronFist price action thread: four charts always. A very short timeframe chart to get a feel for price action, the medium timeframe trading chart stared at most, a long timeframe chart of the stock for trend, and a long timeframe chart of the overall market, synced, for sentiment and direction.
- Reddit, r/RealDayTrading wiki system (Pete Stolcers and Hari Seldon): market first, stock second, always relative to SPY. Read SPY direction and intraday posture before any single name is considered.
- Stan Weinstein, via the classic teachers census and Stage Analysis: forest to trees. Market stage first, then Stage 2 groups, then stocks inside those groups.
- Wyckoff Method via StockCharts ChartSchool: five steps in fixed order. (1) Determine the broad market position and probable trend. (2) Select stocks in harmony with that trend, showing relative strength. (3) Select stocks with a sufficient cause to meet the objective. (4) Determine readiness to move. (5) Time the commitment with the broad market.
- David Keller, CMT, on X and StockCharts: the Morning Coffee Routine runs long term market trend, short term trend, trend model, U.S. indexes, global ETFs, intermarket, breadth, sentiment, ratios, sector ETFs, then individual stocks, ending with intraday SPY. The order is the skill. Situational awareness comes from never changing it.

Run that order even when a lower timeframe chart is shouting. A beautiful trigger against the higher timeframe is, in Echo Analysis language, a bounce until the higher timeframe says otherwise. Echo Analysis teaches: draw the higher timeframe first, weekly before daily and daily before 4 hour, and when timeframes disagree the higher one wins.

### 1.2 The 60 second first look, by eye

Use this on any single chart before you draw anything. It is a synthesis of the ChartSchool reading protocol, the PASR journal template, and the NextElliott reading order taught on Forex Factory (Trend, Structure, Cycle, Confirmation, Hurdle, Action).

1. Name the market context. Is the index in an uptrend, a downtrend, or a range today, and on the weekly chart?
2. Name the stage or cycle before the pattern. Weinstein Stage 1 basing, 2 advancing, 3 topping, or 4 declining, read off price against the 30 week moving average and its slope. Or Oliver Kell's Cycle of Price Action: Reversal Extension, Wedge Pop, EMA Crossback, Base and Break, Exhaustion Extension, or Wedge Drop, read off price against the 10 and 20 EMAs. Classification dictates the allowed action.
3. Name the prior trend in words. ChartSchool: without a prior uptrend to reverse, there cannot be a reversal pattern. Rising peaks and troughs, falling peaks and troughs, or horizontal. Say it out loud: up, down, or range.
4. Name the structure. List the last three swing highs and swing lows as higher high, higher low, lower high, or lower low. That sequence is the read. Everything else is commentary on it.
5. Locate price inside the structure. At the top of a range, the middle, or the bottom? At a prior reaction high or low? Next to a level, or in open space with a hurdle too close? Forex Factory, NextElliott: direction is not the same as trade location, and trend direction is not the same as entry timing. A correct directional read with support too close becomes Watch or Protect, not a new entry.
6. Read volume against its script. Is volume contracting inside the consolidation, expanding on the break, climaxing at an extreme, or diverging from price progress? Wyckoff effort vs result: heavy volume with narrow spread and little progress is absorption by the other side, the earliest warning.
7. Only now name a candidate pattern, and name what would kill it. If you cannot state the invalidation in one sentence, you do not have a read yet. You have an impression.

### 1.3 The 10 minute deep first look

For a name that passes the 60 second pass, add:

- Relative strength. Compare the name and its sector against SPY and QQQ. r/technicalanalysis protocol: always name the benchmark and the lookback. An RS line making a new high before price is quiet leadership. Short term RS up while weekly RS is still falling is a bounce, not a leadership change. J.C. Parets: the powerful signal is price breaking out and its RS line breaking out at the same time.
- The control frame. Strat's PASR: is there a Big Boss or Boss control candle whose range brackets current action? A Weekly Control Candle stays in force until a weekly candle closes outside its range, and that closing candle is not itself a new control candle. Box the frame before you judge the bars inside it.
- Average price since the event that mattered. Brian Shannon, Anchored VWAP: anchor at earnings, a major gap, a significant swing high or low, a high volume day at about 1.5 times normal volume or more, or the start of the year. Price above that AVWAP means buyers since the anchor are in profit and in control. Price below means sellers are. Check the slope as well as the position: a move above a declining VWAP will often fail, and a move below an advancing VWAP will often fail.
- The day classification, for intraday readers. IronFist: always classify the day as inside or outside, upside or downside, and account for time of day. Elite Trader, Naked Chart thread, Directional Day Filter: take the first minutes' average, plot it through the first hour, and count how many bars sit above versus below it. Roughly equal counts mean a choppy, trendless day is expected.

## 2. Annotation Conventions: What Gets Drawn, What Stays Off

### 2.1 The dressing of the working chart

Masters keep the base chart deliberately plain so the marks they do make carry meaning.

- IronFist (Elite Trader): candles in shades of grey, not red and green, to remove color bias. A couple of EMAs only, to stay oriented to direction. Several horizontal lines on the long timeframe charts, only a couple on the trading chart, in his words so he does not get wrapped around the axle. Find the moving average that this specific equity respects, on wild moves, in ranges, and on minor pullbacks, by trial and error. Every equity has a personality. Keep the average equivalent across timeframes, for example 20 on the 5 minute is about 100 on the 1 minute, so timeframes do not contradict each other.
- Peter Brandt: price only, one pattern boundary pair, a measured move target, and almost nothing else. No indicator stack. Indicators are derivatives of price.
- J.C. Parets, All Star Charts: price, one horizontal level, a 200 period SMA, and at most one indicator window underneath. A second indicator means a second chart. His line for it: do not be lazy.
- Oliver Kell: price plus the 10 EMA and the 20 EMA, adjusted to 8 and 21 when that is what the market is respecting, and a stage label. Sparse by design.
- Helene Meisler: charts drawn by hand on semi log paper, about 200 stock charts posted daily, with a small fixed statistic set kept separately (advance decline line, new highs and new lows, McClellan Summation Index, her 10 day overbought oversold oscillator). Her claim is the method: after years of hand posting she can redraw a stock's shape from memory. The one month she stopped, in 1996, she no longer knew what was going on in the market until she back filled the month by hand.
- Veteran end state, Elite Trader Naked Chart thread: one reader who started decades ago with thousands of indicators and triangles and rays and arcs and butterflies and Elliott waves and fibs now has nothing except a zig zag line. Forex Factory, The Basics: you need nothing more than price and manually drawn lines. Minimalism in every community is an earned end state, not a starting pose. Screen time on naked charts comes first, then tools are added back one at a time.

### 2.2 What gets drawn: the short approved list

Draw only objects that answer a decision. Across the census, five families of marks earn their place.

**1. Horizontal zones from repeated reactions.**
TradingView Education canon, Forex Factory, and Elite Trader agree: zones, not lines. Draw a rectangle, for example 24,480 to 24,530, not a single price at 24,500. Work from the higher timeframe. Mark swing highs and swing lows. A valid level needs at least two clear reactions, three is stronger, and it must be obvious. The test taught on TradingView: if you have to squint, it is not a real level. ChartSchool adds the polarity principle: broken support becomes resistance and broken resistance becomes support, because trapped holders sell at breakeven on the return. Always watch the retest after the break. LuxAlgo's open source work on TradingView codifies the modern standard: a drawn level should also be labelled with what price did there: Breakout, Test, Retest, or Rejection. Annotation of behavior, not just geometry. Keep the count of displayed levels low, about five as the readable sweet spot.

**2. One boundary pair for the pattern in progress.**
Brandt draws the rectangle boundaries, the horizontal boundary of a right angle triangle, or the head and shoulders neckline, and nothing else about the pattern. Bulkowski's standard is stricter on touches: triangles need at least three touches on one line and two on the other, channels at least two per line, broadening formations at least five total, and price must cross the pattern from line to line nearly filling the available space. Abundant white space inside the lines rejects the pattern. Minervini and the VCP school draw successive contraction depths inside the base and one horizontal pivot line at the final contraction's high. David Ryan's simplification, quoted in the classic teachers census: draw a line across the top of where most of the stock's trading has taken place, then buy as it moves through that line.

**3. One trend line, drawn to the community standard.**
TradingView Education, 3 touch rule: one touch is a point, two touches are a hypothesis, three or more touches are a validated trendline. An uptrend line connects rising swing lows, a downtrend line connects falling swing highs. Draw it on the timeframe you trade. Angle is information: too steep is not a trend, it is a chase. A slow angle is sustainable and swing friendly. A break needs acceptance, a close and follow through, not one candle poking through. Alex Desjardins, PrimeTrading, adds a useful pair convention: the down trend line over a pullback is drawn solid, and higher lows forming inside the base are marked with a dashed up trend line. The dashed line is the tell he watches before every setup in his playbook.

**4. Anchored average price, when an event reset the cost basis.**
Shannon AVWAP lines from named anchors, Jake Wujastyk's hand off method (anchor a new AVWAP at the point where price touches the previous AVWAP for the last time, and repeat, so the chain maps where equilibrium reset at each leg), and volume by price shelves where volume actually traded. Wujastyk's repeatable pattern is the pinch: a volume shelf and an AVWAP converging at the same zone. Ian McMillan frames the question the line answers: who is in control since something important happened? Earnings. A gap. A major low. A breakout. The beginning of the year.

**5. Fibonacci zones, drawn to the Echo Analysis standard.**
Echo Analysis is the only source in the X census with a fully written drawing standard, and it is worth following exactly. Use two different tools for two different jobs. The retracement tool, two clicks, swing low then swing high, measures a pullback: use it for Wave 2, Wave 4, and the pullback after a completed five. The trend based extension tool, three clicks, start of Wave 1, end of Wave 1, end of Wave 2, projects targets: use it for Wave 3, Wave 5, and Wave C targets. Anchor wick to wick, because price traded at the wick. Draw in the direction of the move, higher timeframe first, log scale on weekly and monthly charts or any move of several hundred percent. Levels are zones. A wick through a level does not kill it. Invalidation is a close through the bottom of the zone. A read needs a minimum of two Fibonacci levels in the same zone before it is called high probability, and a moving average, trendline, or old support on top makes it stronger.

### 2.3 Fibonacci reference bands worth memorizing

From Echo Analysis: Wave 2 zone 0.5 to 0.786, most often 0.618 to 0.786; 0.886 is still possible but low conviction; 1.0 retracement is invalidation, because there was no Wave 1. Wave 4 zone 0.236 to 0.5, most often 0.382 to 0.5. Wave 3 targets: 1.272 is a stall point, 1.618 is the primary target, and 2.0 to 2.618 means Wave 3 is extending and the degree should be rechecked.

### 2.4 The entry, stop, target triplet printed on the chart

The Reddit swing trading canon and the TradingView Ideas house style converge on the same template. No published read is complete without all three, drawn, with risk visible.

- ENTRY, SL, TARGET printed on the chart itself, not buried in prose.
- The position tool or an equivalent drawing so the reward to risk is visible at a glance.
- Bias statement first, then the marked chart, then the explicit invalidation in words (for example: primary scenario remains bullish while price holds above this support zone), then scenario B, what you will conclude if the invalidation prints.
- Bulkowski's measure discipline on the target: pattern height multiplied by the percentage that pattern historically meets its target, projected from the breakout price. ChartSchool's simpler version, pattern height projected from the break point, is the starting estimate. Both treat the target as provisional and subordinate it to the next real level.
- Brandt's self test, which belongs taped above every desk: when I place a trade, will I, a year from now when I look back at the chart, be able to see in the chart the day and the price at which I took the position? If yes, it is a good trade. If the entry is invisible on the finished chart, it was never clean.

Wyckoff readers add event labels inside ranges: PS, SC, AR, ST, Spring, SOS, LPS in accumulation, and PSY, BC, AR, ST, UT, UTAD, SOW, LPSY in distribution (ChartSchool Wyckoff Method). Hershey's SCT corpus on Elite Trader goes furthest: three nested channel levels at all times, inner channels in unobtrusive grey and projected, with the price volume relationship read on every traverse. Dominant segments carry increasing volume, non dominant segments carry decreasing volume, volume peaks at Point 2 of a channel and troughs at Point 3. The transferable lesson is not the vocabulary. It is that the labels name events and volume behavior, not decorations.

### 2.5 What stays off the chart

- Any line you cannot state a rule for. If a line has fewer than two reactions, no anchor event, and no pattern boundary role, delete it.
- A second and third indicator measuring the same thing as the first. Parets: one indicator window, or make a second chart.
- Lines drawn on a lower timeframe that contradict the higher timeframe frame. Redraw from the top down, or remove them.
- Steep trendlines through a vertical move, untested extensions, and Fibonacci levels drawn body to body, on a linear scale over a multi hundred percent move, or with a single level and no confluence. All three are named errors in the Echo Analysis standard.
- Yesterday's intraday drawings left to clutter today's session. The day trading canon clears and redraws. Old marks are journal material, saved as a screenshot, not live chart furniture.
- Color as analysis. Grey candles (IronFist) exist precisely to stop green from meaning go.

A useful fixed scale habit comes from the Forex Factory naked chart school: lock the chart's y axis scale by timeframe (their quoted standard for FX is 50 pips for M1, 100 for M5, 150 for M15, 200 for H1) so bar geometry stays comparable from day to day instead of auto scaling to fit the narrative. The exact numbers belong to their market. The principle transfers to any market: comparable geometry is what lets bar size mean anything.

## 3. Watchlist Construction From Scans

### 3.1 The funnel every school uses

PrimeTrading states the funnel cleanly: Universe List about 500 names, Watch List 10 to 100, Focus List 0 to 10, then execute. Every other school in the census runs the same shape with different filters.

- Universe: everything the scan can see. No judgment yet.
- Watch: names that pass the structural gate (trend template, stage, relative strength, liquidity).
- Focus: names with a drawn setup, a named pivot, and an alert set on the level. PrimeTrading sets alerts on the drawn levels in TradingView. Nothing reaches Focus without a line and a price.
- Execute: only Focus names that trigger, with the stop already written.

A zero name Focus List is a valid, common result. Kell's corollary, repeated across the breakout schools: most of the time the right move is to do nothing and sit in cash until an A plus setup appears (Kristjan Kullamaggie, Qullamaggie).

### 3.2 The gates, school by school

Pick one gate set as your primary and run it consistently. The census offers these complete, ready to use versions.

**Trend Template gate, Mark Minervini.** A chart must pass all eight before pattern reading is even allowed: price above the 150 and 200 day averages; 150 day above the 200 day; 200 day rising for at least a month; 50 day above both the 150 and 200 day; price above the 50 day; price at least 30 percent above its 52 week low; price within 25 percent of its 52 week high; relative strength strong, 70 minimum in most codifications and 80 to 90 preferred. Then the VCP must qualify: 2 to 4 contractions, each roughly half the depth of the prior (for example minus 24 percent, minus 12, minus 6, minus 2.5), volume drying to multi week lows in the final contraction, and a single pivot to buy through.

**Stage gate, Weinstein via Stage Analysis.** Weekly watchlists, each name carrying a stage label, the moving average being tested, a relative strength note, and the breakout condition. Buy only a Stage 2 breakout: price through a well defined resistance, above a rising 30 week average, on expanded volume (TraderLion's guide states ideally 2 to 3 times average), with relative strength confirming and the sector supportive. Never buy below a declining 30 week average, no matter how cheap it looks.

**PrimeTrading technical filters.** Above the 200 DMA, above the 50 DMA, 20 DMA above 50 DMA, plus relative strength rankings at 1, 3, and 6 months, after a liquidity screen. Then the pattern work is deliberately finite: seven named setups built from the down trend line and the pivot (Wedge Break, Wedge Break Pullback, the breakout retest family long and short, Breakout 10 EMA Pullback, Breakout 21 EMA Pullback, plus the Second Entry or Higher Lows bonus).

**Episodic Pivot gate, Pradeep Bonde (Stockbee).** A real surprise catalyst, not an upgrade or hype; a stock neglected sideways for months to years; a gap that clears all moving averages and the recent range into free air with no trapped sellers overhead; volume so large that a normal day's volume can trade in the first 5 to 15 minutes. The EP9 variant qualifies on volume at or above about 9 million shares and price at or above 3 dollars, which cuts a roughly 12,000 name universe to a handful. Delayed EP is the disciplined second chance: the catalyst is real but the first move is too far to chase, so wait for an orderly pullback holding EMA support, pre stage the order, and take the renewed break. Three stopped attempts on the same name means walk away.

**Relative strength sorting, r/RealDayTrading.** Real Relative Strength, RRS equals (PC minus expectedPC) divided by ATR, where expectedPC equals (market percent change divided by market ATR) times the stock's ATR. RRS above zero means the name is outperforming the market on an ATR normalized basis, so names are comparable. Use it to sort the watchlist, longs from strength and shorts from weakness, with the daily chart agreeing, rather than as a visual overlay.

**Hershey stock selection, Elite Trader.** Universe priced 10 to 50 dollars with 500K plus daily volume, ranked by volume dry up (5 day average volume under 50 percent of the 30 day) and volume change, sorted into quality tiers. A dry up ranking is a watchlist tool: quiet names near a pivot are the ones that can move on a normal volume return.

**New highs bucketing, David Keller.** Run the new three month highs list regularly and bucket every result into exactly three chart types: up and to the right long and strong charts; new accumulation phase charts exiting a consolidation with higher highs and higher lows; and charts just breaking above a key moving average. The breakouts are the actionable bucket. The other two are context and patience.

### 3.3 Building the list: the weekly and nightly builds

- Weekly build (Stage Analysis cadence, Keller routine): run the gates on the weekly timeframe, classify every survivor by stage, write the breakout condition next to each name, and date the list. A watchlist without a date and a condition is a pile of tickers.
- Nightly build (r/Daytrading and PrimeTrading cadence): re sort by relative strength, demote any name whose drawn level broke the wrong way or whose volume script failed, promote names whose final contraction or retest completed that day, and set or move alerts to the drawn pivots. Bonde's decision frame sits above the nightly build: market breadth first. If breadth says no portfolio risk, the Focus List stays empty no matter how good the charts look. PrimeTrading states the same gate as a market read against the index's 21 day structure first.
- Pre market build, day traders (TradingView day trading key level checklist, mingjong education series): before the session, mark previous day high and low, overnight high and low, swing highs and lows from the last few days, and swings forming intraday. Chart the extended hours channel for reject and base levels. Have the contracts and setups pre selected. Nothing gets discovered after the open that should have been marked before it.

Promotion and demotion rules, stated as a checklist:

- Promote to Focus only when: gate passed, pattern named, pivot price written on the chart, stop location structural and measured, and alert set.
- Demote immediately when: price closes through the invalidation zone, the RS line rolls over while price makes a new high, volume expands against the setup inside the base, or the pattern outlives its duration limit. Brandt's duration discipline is the model here: a dependable flag or pennant completes and breaks within about 4 weeks, and a 7 to 10 week upward sloping channel is not a flag and should not be expected to behave like one. Time is an identification rule, not a detail (Brandt, Linda Raschke's 4 session age rule for a Turtle Soup 20 day extreme, O'Neil's 7 to 8 week minimum base, Weinstein's 30 weeks, Bulkowski's exact touch and duration floors).

## 4. The Chart Journal

### 4.1 Why the journal is a chart, not a diary

Every serious community in the census journals on the chart itself, because prose written later quietly edits what you actually saw.

Forex Factory, Candle Cartel states the doctrine in one line: journal your reasoning, not just entries and exits. That is where real edge develops.

### 4.2 The screenshot journal, day trading standard

From r/Daytrading's community standard method:

1. Do not write prose during the session. Keep all intraday drawings on the chart.
2. Mark start and stop times with vertical lines. Note the news times you stood aside for.
3. Note tendencies, errors, and missed trades as text on the chart, at the place they happened.
4. Screenshot the whole day in 1 to 3 shots. Include 1 to 2 hours of pre session price action for context.
5. Record the result in points, ticks, or pips, not dollars, so the record stays size independent and comparable across months.

### 4.3 The trade post template, Strat's PASR and Terry's Journal

Terry's Journal on Forex Factory is the best worked template in the forum census. For each timeframe, Big Boss, Boss, and Worker, state two things in order: the Strat Shadow direction (the EMA and SMA stack, up or down, positive or negative) and the price structure (swing sequence, breaks, retests). Then name the trigger candle (Hammer, Shooting Star, bullish engulfing and its PASR abbreviations) rejecting a named level: shadow, control candle edge, 200 EMA, or round number. Then the plan, with numbers: entry as a stop order a small buffer beyond the trigger candle, stop the same buffer beyond the other side, first target at the next timeframe's level, remainder held until a reverse PASR signal. PASR stop distances on higher timeframe trades run wide, 78 to 160 pips in the journal's FX examples. The transferable point is that the stop is placed at the structure, measured, and written before entry, whatever the market.

Note the inversion rule Terry's Journal teaches alongside it: a failed Shooting Star or Hammer, where price closes through it, is itself a tradable signal in the opposite direction. Journal the failures with the same care as the successes. Adam Grimes builds an entire module on this: Pattern Failures as a trade in themselves, and the Failure Test, where price probes beyond a level, fails, and reverses.

### 4.4 The minimum journal record for a swing read

For every read you intend to grade later, capture at the time of the read:

- Date and time of the read, ticker, timeframe set used.
- A clean screenshot before any later bars exist, with the approved marks only: zones, boundary pair, pivot, AVWAP anchor named, Fibonacci zone if used.
- Market and stage classification in one line each.
- Pattern name, or the words no pattern, structure only.
- ENTRY, SL, TARGET with prices, and the invalidation sentence.
- The volume script you expect next, written as a prediction: for example, volume should dry up further in this contraction and expand at least 40 to 50 percent above average on the pivot break (Minervini's commonly cited confirmation band; David Ryan's minimum is plus 25 percent, best plus 100 percent or more).
- Scenario B: what you will conclude, and do, if the invalidation prints.
- Position state or paper state, size, and risk in percent. PrimeTrading's dated portfolio updates, which disclose entries, exits, and losses by name and percent, are the honesty standard the X census singles out.

Richard Moglen's TraderLion case study format is the teaching version of the same record: show the unlabelled chart first and identify where risk could be managed, then show the same chart marked up, across full daily, zoomed daily, and a 65 minute chart side by side. Journal both versions. The gap between what you saw unlabelled and what you see labelled is your real recognition skill, measured.

## 5. The Post-Read Review: Grading Your Own Reads

### 5.1 The nightly redraw

From the MapleStax routine circulated in r/Daytrading:

1. Review every trade, and every graded read, that night.
2. Top down redraw, Daily to Hourly to 10 minute to 5 minute, drawing the trend, support and resistance, supply and demand, pivots, and flags you missed live. Draw only the most obvious formations. The point is to train live recognition speed, not to decorate hindsight.
3. Plot your actual entries and exits onto the redrawn chart. Did you trade with or against the larger trend the redraw now shows?
4. Add the live in trade notes for psychology, exactly as written at the time.
5. Log exterior influences: index behavior, news, FOMC, options expiry.
6. Close with explicit improvement questions: chasing? FOMO entry? Stop respected? Over confirming?

### 5.2 The end of week frame review

Strat's PASR review ritual, from Terry's Journal: at week's end, re examine the control candle frame itself. Reset the Big Boss control candle using its top and bottom along with the daily Strat Shadow. Note which internal levels price respected (shadow, 200 EMA, control edges), which attempt at a level succeeded (the journal's example: a fourth attempt at resistance succeeded and turned into support), and what to watch on all three timeframes at the next Big Boss level. Drop to H1 and H4 only when price arrives there. The weekly review grades the frame, not just the trades, because a wrong frame makes every trigger inside it suspect.

### 5.3 The 2 to 4 week grading review

This is the habit that turns journaling into mastery, and the one this playbook requires for every logged personal read. At 2 weeks and again at 4 weeks after the read, pull the original screenshot, place it beside the current chart with the same drawings extended and nothing redrawn, and grade the read against what price did next. Do not grade the outcome of a position. Grade the read.

Score each dimension 0, 1, or 2. Maximum 14.

| Dimension | 2 | 1 | 0 |
| --- | --- | --- | --- |
| Direction | Price resolved the way the read called it | Price went sideways in the named range | Price resolved the other way |
| Level quality | Price reacted at the drawn zone, wick or close, more than once | Price reacted near the zone, offset by a visible margin | Price cut the zone with no reaction |
| Invalidation discipline | Invalidation never printed, or printed and scenario B was the correct next read | Invalidation printed late or ambiguously | Invalidation printed early and the original read had no scenario B |
| Volume script | Volume did what the journal predicted, contraction, expansion, or climax, at the right place | Volume was neutral or mixed | Volume contradicted the script at the decision point |
| Timing | The move the read targeted began within the stated window | Move began, but late, after a second pattern completed | Move never began, or began only after the pattern expired by its duration rule |
| Target honesty | Price reached the measured target zone, or stopped at the named next level the read subordinated it to | Price reached at least half the measured move | Price reversed well before half the move with no named level there |
| Drawing honesty | Original marks still fit, no redraw needed to make the read look right | Minor extension of a zone is defensible by the original rule | The read only survives if the lines are moved |

Grade bands: 12 to 14, a master read, file it as a model example. 9 to 11, a sound read with one named flaw, write the flaw as the lesson. 6 to 8, a partial read, the pattern or the frame was half right, identify which half. 0 to 5, a failed read, and failed reads get the full treatment below, not a shrug.

Bulkowski supplies the discipline for calling a failure a failure. His template defines failure precisely (in his statistical work, failure to move at least 5 percent in the breakout direction), publishes throwback and pullback rates per pattern because they change entries, and treats busted patterns, which break one way by 10 percent or less, reverse, and close beyond the opposite side, as a new and powerful signal in the new direction. Use that language in your review. A busted read is not nothing. It is a new read, graded separately, and only if you logged it at the time.

Three review rules that keep the grading honest:

- Never move a line before grading. Extend lines forward in time, yes. Shift them in price, never. A moved line converts a failed read into a fake pass and destroys the whole record.
- Grade the screenshot you saved, not your memory of the read. If there is no screenshot, the read is ungradable and scores as a process failure regardless of what price did.
- Separate read quality from money. A correct read can lose money on a throwback that stops a tight entry (Bulkowski publishes pullback rates of about 60 to 68 percent for common patterns, so this is normal, not an excuse). A wrong read can make money by accident. The 2 to 4 week grade judges the read. The account judges the trading. Keep the two ledgers apart.

Keep a running tally by pattern and by flaw. After 20 graded reads, your own statistics replace generic advice: the pattern you overcall, the level you draw too thin, the timeframe you skip. That tally is the most personal technical analysis document you own.

## 6. Drills Masters Recommend

### 6.1 Bar Replay: the hidden future drill

TradingView community standard, and the single most prescribed drill in the census.

Protocol:

1. Pick a chart and a date in the past. Rewind with Bar Replay so future bars are hidden. Some community practice tools add a grey curtain over everything after a chosen Now.
2. Run your full first look routine at that bar, out loud, in order: market, stage, prior trend, structure, location, volume.
3. Draw only the approved marks. Write ENTRY, SL, TARGET and the invalidation sentence. Write the volume script you expect.
4. Advance one bar at a time, or step forward in fixed increments. At each decision bar, state hold, enter, or pass, before advancing again.
5. Log the result in the journal format of Section 4, including the reads you passed on that would have worked. Missed trades are drill data.
6. At the end, grade with the Section 5 rubric. Replay grading is stricter, because there was no money and no excuse.

The explicit purpose, as the community frames it: this is the cure for hindsight bias. Recognition speed in replay, at one bar per decision with no future visible, is the closest measurable proxy for live recognition.

### 6.2 Annotation drills: drawing accuracy as the trained skill

Jack Hershey's SCT corpus on Elite Trader contains the purest statement of this drill family. The Emergency Exit Drill (reverse at the failure to traverse, or, if you miss it, when the right channel line is breached) is described by its own author as being more about doing good annotations of channels than anything else. Annotation accuracy is the skill. Hershey warns that a full SCT day of correct annotation is initially impossible, that one hour of correct annotation is an accomplishment, and that six mental drills build the stamina.

Scaled to any method, the drill is: take one session, one timeframe, and annotate every swing, channel, or event in your system's grammar, completely, with no trading decisions at all. Count the annotations you had to correct on review. That correction count, falling week over week, is progress you can measure.

### 6.3 The naked observation apprenticeship

Forex Factory, The Basics and The Real Basics:

1. Watch a naked chart for a long time without the pressure of making a decision. Paper and pencil. Note what price does over and over.
2. Mark where price seemed to turn. When price returns to that place, observe precisely: does it break, by how much, with what force, and what happens after? If it holds, how far did it poke through before holding, and how fast did it reverse?
3. Only after that observation base exists, add the minimal grammar: candlestick patterns, fractals for support and resistance, Fibonacci for retracement and extension targets.

James16's Forex Factory thread prescribes the same apprenticeship at trade level: blank chart, daily and weekly timeframes, trades only at significant support and resistance and only with the trend. His bar grammar is precise enough to drill: the pin bar with a long nose protruding from surrounding prices and open and close clustered near one end; bullish and bearish outside vertical bars (BUOVB, BEOVB); double bar low with higher close and double bar high with lower close (DBLHC, DBHLC); inside bars as compression. The drill rule is his confluence rule: a bar pattern alone is never a setup. It counts only clustered at a pre marked level: horizontal support or resistance, trendline, round number, or Fibonacci level. In replay, count how many textbook bars appeared at no level. That count teaches the rule faster than any lecture.

### 6.4 Pattern spotting sets

- Bulkowski, ThePatternSite: every pattern page carries an Identification Guidelines table, characteristic by characteristic, each row a checkable visual rule, plus worked examples and quizzes. Drill method: cover the label, run the table row by row against the chart (prior trend, touches, white space crossing test, duration floor, confirmation close), and only then uncover the answer. His white space test is the highest value row in the table: price must cross the pattern from line to line, nearly filling the available space, or the candidate is rejected.
- TraderLion and Moglen: unlabelled chart exercises are the house format. Given a chart with no marks, identify entries where risk could be managed, name the significant price and volume features, and state the ideal characteristics the setup should have. Then compare against the marked version.
- Qullamaggie: pattern recognition trained by volume of examples. His stated method is studying charts for hours, going back through the biggest winners in market history, until the tight base after a 30 to 100 percent advance, surfing the rising 10 or 20 day average for 2 to 8 weeks, is recognized on sight. Build a personal model book the same way: 50 historical examples of your one primary pattern, each annotated with the same template, before you trust your live recognition of it.
- Brandt's 4 week flag test as a spotting drill: take 30 charts labelled flag by posters or scanners and reject every one that took longer than about 4 weeks to complete, slopes the wrong way, or lacks the aggressive pole. Most public mislabelling is a duration violation, and this one drill proves it.

### 6.5 One pattern immersion

The finite playbook teachers agree on depth over breadth. Qullamaggie trades three setups only. PrimeTrading teaches seven. Grimes organizes his free MarketLife course as one module per setup: the Pullback, the Anti, the Failure Test, Breakouts, Pattern Failures, each studied as a complete unit. Raschke's Street Smarts library works the same way: each named setup (Turtle Soup, Holy Grail, the Anti, 80 20s) carries its entry stop, protective stop, and re entry rule specified before the trade.

Run an immersion in two week blocks:

- Days 1 to 2: definition only. Write the identification table for the one pattern from its strictest source (Bulkowski for geometry, ChartSchool for volume script and confirmation, the pattern's own teacher for entry and stop). Write the duration floor and the touch minimums at the top of the page.
- Days 3 to 5: historical set. Find and annotate 20 past examples and 10 near misses that fail exactly one row of the table. The near misses teach more than the examples.
- Week 2: replay only. Bar Replay sessions on that pattern alone, full journal record per repetition, minimum 20 repetitions.
- End of block: grade every repetition with the Section 5 rubric immediately, since replay outcomes are already known, and write the one flaw that cost the most points. That flaw is the next block's warm up drill.
- Then either repeat the block or promote a second pattern. Never run two immersions at once. A reader who has immersed in three patterns (for most readers: one breakout pattern, one pullback pattern, and one failure or reversal pattern) owns a complete working vocabulary. Grimes's trio of Pullback, Anti, and Failure Test is a ready made set, as is Raschke's.

One concrete immersion example, Raschke's Holy Grail, because its rule is complete in the census: 14 period ADX above 30 and rising (very high ADX, above about 60, warns of exhaustion instead). Wait for the first retracement to the 20 period average. Entry stop above the high of the bar that touches the average, protective stop under the new swing low, exit part at the most recent swing high, one re entry at the original price if stopped, and a second trade requires ADX to turn up above 30 again. A student can run 20 replay repetitions of that rule with zero judgment calls left open, which is exactly what an immersion needs.

### 6.6 The self testing protocol from the professionals

CMT Association study protocol, from the classic teachers census: read each chapter's learning objectives before the chapter, then after it write sentences demonstrating competence on each objective. Applied to this playbook: before a drill block, write what you should be able to do in sentences. After the block, write the sentences again from your graded journal, not from the text. Any sentence you cannot write from your own graded examples is your next drill. The CMT Level I weights tell you where the profession puts the effort: Chart and Pattern Analysis 23 percent, Trend Analysis 16 percent, Selection and Decision Making 13 percent. Drawing and trend work are more than a third of the foundation. Train in that proportion.

Hand posting, Meisler's drill, deserves its own line because no software replicates it: posting prices by hand, daily, for a fixed personal list, builds shape memory that screen scrolling does not. A modern minimum version: hand sketch, from memory, the weekly shape of your five most watched charts every Sunday, then check against the real charts and journal the differences. Meisler's standard is redraw from memory. The sketch drill is the on ramp.

## 7. Heuristics That Recur Across Independent Practitioners

These rules appear in at least three independent sources in the census, in different vocabularies. That recurrence is why they are in the playbook.

1. Market first, always. RealDayTrading, Weinstein, Wyckoff Step 1, Keller's routine, Bonde's breadth first frame, PrimeTrading's index gate. No single name read outranks the market read.
2. Higher timeframe wins. PASR's Big Boss hierarchy, Echo's drawing order, Candle Cartel's tone alignment (every higher timeframe candle carries a tone, and the craft is aligning the lower timeframe tones with it), IronFist's synced long timeframe market chart.
3. Zones, not lines. TradingView canon, ChartSchool, Grimes, Wujastyk, Echo. A wick through a zone is information. A close through the bottom of the zone is invalidation.
4. Obvious beats clever. TradingView's squint test, the 3 touch rule, Brandt's clean boundaries, Ryan's single line across the top. If only you can see it, it is not a level.
5. Context before pattern, level before trigger. James16's confluence rule, PASR's control candle frame, Elite Trader's horizontal lines drawn on the higher timeframe first. The pattern is the trigger. The level is the setup.
6. Do not buy the level. Buy the reaction to it. Echo Analysis says it verbatim: the zone tells you where to watch, price tells you when to act. Zanger's rule that a buy point being touched is not by itself a buy, Brandt's decisive close requirement, Bonde's opening range high trigger, and PrimeTrading's trigger ladder (down trend line break, or breakout day's high, or first hour high intraday) are the same heuristic in four vocabularies.
7. Volume has a script, and the script is part of the pattern. Contraction inside bases and triangles, dry up at the point of maximum tightness (Minervini, O'Neil handle, VCP canon), expansion on the break (Weinstein about 2 times, O'Neil plus 50 percent or more, Ryan plus 25 percent minimum), climax at climaxes (Wyckoff SC and BC, exhaustion gaps), peak at Point 2 and trough at Point 3 in a channel traverse (Hershey). A break that violates its volume script is downgraded, not celebrated.
8. Confirmation is a close. ChartSchool's convincing break, Bulkowski's close outside the boundary (and, for a steep down sloping head and shoulders neckline, a close below the right armpit instead, because price may never close below the steep line), Brandt's Friday close as the most significant price of the week, Weinstein's weekly close through the base top. Intraday pokes are tests, not verdicts.
9. Broken levels flip, and the retest is a separate, named event. Polarity (ChartSchool), throwback and pullback (Bulkowski), LPS and LPSY (Wyckoff), PrimeTrading's retest setups, PASR's fourth attempt that succeeded and turned into support. Plan the retest when you plan the break.
10. Every read carries its invalidation, written in advance, and stops are structural. Low of the breakout day (Qullamaggie, Bonde), low of the final contraction (Minervini), opposite pattern boundary (Brandt), beyond the pin bar nose (James16, stop beyond the nose tip with entry beyond the opposite end), buffer beyond the trigger candle (PASR), under the base low rather than at a percentage (Weinstein, who raises the stop under each successive pullback low and never lowers it). Percentage caps such as Minervini's 7 to 8 percent maximum and Qullamaggie's one average daily range act as vetoes on structurally wide stops, never as substitutes for them.
11. Time is an identification rule. Brandt's 4 week flag, Raschke's rule that the prior 20 day extreme must be at least 4 sessions old for Turtle Soup (buy stop 5 to 10 ticks back inside the old extreme, good for the day only, stop 1 tick beyond the new extreme), O'Neil's 7 to 8 week base minimum and buy zone within 5 percent above the pivot with no chasing beyond it (Zanger's version: never pay up by more than 5 percent above the trend line), Bulkowski's triangle breakout clustering 61 to 65 percent of the way to the apex. When a candidate violates its duration, rename it. It is a different pattern with different expectations.
12. Trade the failure as seriously as the pattern. Grimes's Failure Test and Pattern Failures modules, Raschke's Turtle Soup (a failed breakout trade by design), Bulkowski's busted patterns, PASR's failed signal inversion, Parets's failed move rule (from false moves come fast moves in the opposite direction). A level that fails tells you who is trapped. That is tradable information, and the journal should log it as a fresh read.
13. Classify before you act, and let the classification choose the action. Weinstein stages, Kell's six stage cycle (size up early in the cycle, size down late, trim at Exhaustion Extension, exit at Wedge Drop, and do not short the hole at Reversal Extension), Wyckoff phases. Two readers can disagree on a pattern and agree completely once both name the stage.
14. Strong opinions, weakly held (Brandt's motto). Every count, pattern, and frame carries scenario B. Elliott Wave practice in the canon formalizes it: a preferred count and ranked alternates, each with a hard invalidation level, and a rule break forces a recount immediately. A read you cannot abandon on its own stated evidence was never a read. It was a position in search of a chart.
15. Minimalism is earned, and routine is the visible proof. Grey candles and two EMAs (IronFist), a single zig zag (Elite Trader veteran), blank chart and hand drawn lines (James16, Forex Factory Basics), hand posted charts (Meisler), the same ordered ChartLists every morning (Keller), the same dated weekly watchlist (Stage Analysis), dated entries and exits including losses (PrimeTrading). The teachers with a fixed routine teach process by repetition. The feed, the list, and the journal are the routine made visible.

## 8. The One Page Operating Checklist

Photocopy this page. Run it in order. Do not skip steps because a chart looks obvious. Obvious is when routine matters most.

**Before the session**

- [ ] Market read written: index trend, stage, and breadth state, in that order.
- [ ] Watchlist rebuilt: gates run, Focus List holds only names with a drawn pivot, a named pattern, a structural stop measured, and an alert set.
- [ ] Key levels marked pre session: prior day high and low, overnight high and low, multi day swings, control candle edges, AVWAP anchors that matter today.
- [ ] Breadth and index gate decided: full risk, reduced risk, or no new risk today, written down.

**First look, per chart (60 seconds)**

- [ ] Stage or cycle named. Prior trend named. Last three swings sequenced.
- [ ] Location named: top, middle, or bottom of the range, and distance to the nearest hurdle.
- [ ] Volume script stated: what volume is doing now, and what it must do next to confirm.
- [ ] Candidate pattern named, or no pattern recorded. Invalidation stated in one sentence.

**Drawing**

- [ ] Zones as rectangles from the higher timeframe, two reactions minimum, no squint levels, about five levels maximum.
- [ ] One boundary pair, touch counts met, white space test passed, duration floor met.
- [ ] Trend line only at three touches, sane angle. Fibonacci only wick to wick, correct tool for the job, two level confluence minimum, log scale where required.
- [ ] ENTRY, SL, TARGET printed on the chart with the invalidation sentence and scenario B.

**Journal, at the time of the read**

- [ ] Clean screenshot saved before later bars exist. Unlabelled impression recorded where the drill requires it.
- [ ] Expected volume script written as a prediction. Size and risk in percent recorded.

**Review**

- [ ] Nightly: top down redraw with fills plotted, missed formations drawn, improvement questions answered in writing.
- [ ] Weekly: frame review, control levels reset, watchlist grades noted.
- [ ] At 2 weeks and at 4 weeks: every logged read graded on the 7 dimension rubric, lines unmoved, tally updated by pattern and by flaw, top flaw assigned as the next drill.

**Drills, weekly minimum**

- [ ] Two Bar Replay sessions with full journal records.
- [ ] One annotation accuracy session, corrections counted.
- [ ] One pattern immersion block in progress, never two at once.
- [ ] Sunday memory sketches of the five most watched weekly charts, checked and journaled.

## Sources Named in This Section

Elite Trader: IronFist price action thread; Naked Chart Trading thread and Directional Day Filter; Jack Hershey SCT corpus. Forex Factory: James16 Chart Thread; Strat's PASR and Terry's Journal; Candle Cartel; The Basics and The Real Basics; NextElliott reading order. TradingView Education: support and resistance canon, trendline standard, day trading key level checklist (mingjong series), Bar Replay practice culture, LuxAlgo event labelled levels. Reddit: r/technicalanalysis RS and Wyckoff protocols, r/swingtrading pattern annotation canon, r/Daytrading screenshot journal and MapleStax nightly review, r/RealDayTrading wiki and Real Relative Strength. X teachers: Echo Analysis (Fibonacci drawing standard), Alex Desjardins of PrimeTrading (playbook and funnel), Oliver Kell (Cycle of Price Action), Pradeep Bonde (Episodic Pivot, EP9, Delayed EP), Stage Analysis (Weinstein watchlists), Brian Shannon (Anchored VWAP), Kristjan Kullamaggie (breakout, episodic pivot, parabolic short, winner study method), Mark Minervini (Trend Template, VCP), Peter Brandt (classical charting, duration and close rules), Dan Zanger (ten rules), Richard Moglen of TraderLion (closing range, case study format), Helene Meisler (hand posting, breadth statistics), David Keller CMT (Morning Coffee Routine, three month highs buckets), J.C. Parets (one level charting, RSI ranges, failed moves), Jake Wujastyk (AVWAP hand off, volume shelf pinch), Ian McMillan (AVWAP control question). Classic teachers: Stan Weinstein (Stage Analysis, forest to trees, structural stops), Linda Raschke with Larry Connors (Turtle Soup, Holy Grail, the Anti, 80 20s), Adam Grimes (Pullback, Anti, Failure Test, Pattern Failures, two forces model, MarketLife course modules), David Ryan (two entries, single line rule, breakout volume minimum), William O'Neil CANSLIM lineage (base duration, pivot, volume confirmation), Thomas Bulkowski of ThePatternSite (identification guidelines template, white space test, close confirmation, failure and busted pattern definitions, quizzes), StockCharts ChartSchool (reading protocol, polarity, Wyckoff Method five steps, three laws, phase events), CMT Association (learning objectives, study protocol, Level I weights).

---

## Sources

Every source actually used in this volume, with URLs where the source lives online. Read status for each source is recorded in the external census filed with this study.

### Code canon

- TA-Lib, C core: https://github.com/TA-Lib/ta-lib
- mrjbq7/ta-lib, Python wrapper: https://github.com/mrjbq7/ta-lib
- serkor1/ta-lib-R and its candlestick vignette: https://github.com/serkor1/ta-lib-R/
- zeta-zetra/chart_patterns: https://github.com/zeta-zetra/chart_patterns
- GregoryMorse/trendln: https://github.com/GregoryMorse/trendln ; https://pypi.org/project/trendln/
- keithorange/PatternPy: https://github.com/keithorange/PatternPy ; https://pypi.org/project/m-patternpy/
- white07S/TradingPatternScanner: https://github.com/white07S/TradingPatternScanner
- shuhanchang12/TechnicalAnalysisAutomation: https://github.com/shuhanchang12/TechnicalAnalysisAutomation
- matplotlib/mplfinance: https://github.com/matplotlib/mplfinance
- highfestiva/finplot: https://github.com/highfestiva/finplot
- pandas-ta and pandas-ta-classic: https://github.com/twopirllc/pandas-ta ; https://github.com/xgboosted/pandas-ta-classic
- Tulip Indicators and tulipy: https://github.com/TulipCharts/tulipindicators ; https://github.com/cirla/tulipy
- Sortefi sortefi-ta: https://github.com/Sortefi/sortefi-ta
- eminsk/yfinance-ta-patterns: https://github.com/eminsk/yfinance-ta-patterns
- wilsonfreitas/awesome-quant: https://github.com/wilsonfreitas/awesome-quant
- gianlucamalato/machinelearning support and resistance notebook: https://github.com/gianlucamalato/machinelearning
- TradingView Lightweight Charts: https://github.com/tradingview/lightweight-charts ; https://github.com/louisnw01/lightweight-charts-python
- foduucom stockmarket pattern detection YOLOv8 model: https://huggingface.co/foduucom/stockmarket-pattern-detection-yolov8

### Written canon

- StockCharts ChartSchool: https://chartschool.stockcharts.com
- Thomas Bulkowski, ThePatternSite: https://thepatternsite.com ; Head and Shoulders Tops: https://thepatternsite.com/hst.html ; Descending Triangles: http://thepatternsite.com/dt.html ; Eve and Adam Double Bottoms: http://thepatternsite.com/eadb.html ; Channels: https://thepatternsite.com/channels.html ; Downside Weekly Reversals: https://thepatternsite.com/WeeklyRevsDownside.html
- Wyckoff Method, ChartSchool tutorial with Wyckoff Analytics text: https://chartschool.stockcharts.com
- Wyckoff Analytics tutorial reproduction: https://fliphtml5.com/yfvuy/tjut/Wyckoff-Method_Wyckoff-Analytics_english/2/
- Chart Whisperer, Wyckoff Method explainer: https://chartwhisperer.ca/wyckoff-method
- BrokerSpecs, Wyckoff Method explainer: https://brokerspecs.com/education/wyckoff-method
- Elliott Wave International: https://www.elliottwave.com ; tutorial text via https://www.scribd.com/document/395521533/Elliott-Wave-International-2-pdf and https://docsbay.net/doc/889935/elliott-waves-a-comprehensive-course-on-the-wave-principle ; contents listing: https://www.forexcycle.com/elliott-wave-courses/30-elliott-wave-tutorial.html
- Zipmex Learn pattern and divergence explainers: https://zipmex.com/blog/falling-wedge/ ; https://zipmex.com/blog/rising-wedge/ ; https://zipmex.com/blog/bullish-divergence/

### Forums and communities

- r/technicalanalysis: https://www.reddit.com/r/technicalanalysis/
- r/swingtrading: https://www.reddit.com/r/swingtrading/
- r/Daytrading: https://www.reddit.com/r/Daytrading/
- r/RealDayTrading: https://www.reddit.com/r/RealDayTrading/
- Elite Trader, IronFist price action thread: https://www.elitetrader.com/et/threads/in-this-thread-ironfist-learns-the-elusive-price-action.146764/
- Elite Trader, Naked Chart Trading and discussion: https://www.elitetrader.com/et/threads/naked-chart-trading-and-discussion.371584/
- Elite Trader, Jack Hershey SCT corpus: https://www.elitetrader.com/et/threads/making-jh-sct-and-all-his-material-alive.320588/
- Forex Factory, Strat PASR: https://www.forexfactory.com/thread/708441-strats-pasr-long-term-stress-free-trading
- Forex Factory, Terry Journal: https://www.forexfactory.com/thread/705590-terrys-journal
- Forex Factory, Candle Cartel: https://www.forexfactory.com/thread/1396448-candle-cartel
- Forex Factory, The Basics: https://www.forexfactory.com/thread/959644-the-basics ; The Real Basics: https://www.forexfactory.com/thread/959764-the-real-basics-how-to-start-and
- Forex Factory, NextElliott Momentum Cycle Suite: https://www.forexfactory.com/thread/1417934-nextelliott-momentum-cycle-suite-cycle-momentum
- James16 Chart Thread, decoded summary: https://www.scribd.com/document/94786443/James-16-Decoded
- TradingView Ideas and Education: https://www.tradingview.com/ideas/ ; support and resistance ideas: https://www.tradingview.com/ideas/supportandresistance/ ; pitchfork education: https://www.tradingview.com/ideas/pitchfork/?type=education
- TrendSpider Anchored VWAP documentation: https://help.trendspider.com/kb/anchored-indicators/anchored-vwap-volume-weighted-average-price

### X practitioners

- Echo Analysis, @EchoAnalysis: https://x.com/EchoAnalysis ; Fibonacci newsletter: https://echoanalysis.kit.com/posts/how-to-use-fibonacci
- Alex Desjardins, PrimeTrading, @PrimeTrading_: https://x.com/PrimeTrading_ ; setups playbook: https://primetrading.substack.com/p/alexs-technical-setups-playbook- ; method republication: https://qullamaggie.net/alex-desjardinss-method/
- Oliver Kell, @OliverKell_: https://x.com/OliverKell_ ; Cycle of Price Action republication: https://cyclesedge.substack.com/p/follow-the-cycle-of-price-action
- Pradeep Bonde, @PradeepBonde: https://x.com/PradeepBonde ; EP9 exposition: https://breakoutshappen.com/stock-news/ep9-million-method-how-the-stockbee-framework-works
- Stage Analysis, @stageanalysis: https://x.com/stageanalysis ; method guide: https://traderlion.com/trading-strategies/stage-analysis/
- Brian Shannon, @alphatrends: https://x.com/alphatrends
- Kristjan Kullamaggie, @Qullamaggie: https://x.com/Qullamaggie ; https://qullamaggie.com ; study: https://www.geckomode.ai/blog/qullamaggie-modern-breakout-master
- Mark Minervini, @markminervini: https://x.com/markminervini ; VCP guide: https://traderlion.com/technical-analysis/volatility-contraction-pattern/
- Peter Brandt, @PeterLBrandt: https://x.com/PeterLBrandt ; https://www.peterlbrandt.com
- Dan Zanger: https://www.chartpattern.com ; ten rules thread republication: https://threadreaderapp.com/thread/1257686400931180544.html
- Richard Moglen, @RichardMoglen: https://x.com/RichardMoglen ; price and volume thread republication: https://en.rattibha.com/thread/1334966057795276800
- Leif Soreide, @LeifSoreide: https://x.com/LeifSoreide
- Matt Caruso, @Trader_mcaruso: https://x.com/Trader_mcaruso ; https://www.carusoinsights.com
- Helene Meisler, @hmeisler: https://x.com/hmeisler ; indicator primer: https://www.thestreet.com/opinion/helene-meislers-technical-indicators-a-primer-722372
- David Keller, CMT, @DKellerCMT: https://x.com/DKellerCMT ; https://www.marketmisbehavior.com ; https://stockcharts.com/articles/bios/david-keller.html
- J.C. Parets, @allstarcharts: https://x.com/allstarcharts ; https://allstarcharts.com ; momentum explainer: https://www.thechartreport.com/2019-01-30/jc-parets-identifying-momentum
- Jake Wujastyk, @Jake__Wujastyk: https://x.com/Jake__Wujastyk ; https://trendspider.com ; AMD case study: https://tradersummit.net/amd-case-study/
- Ian McMillan, CMT, @the_chart_life: https://x.com/the_chart_life

### Classic teachers

- Adam Grimes: https://www.adamhgrimes.com/what-works/ ; CXO Advisory book notes: https://www.cxoadvisory.com/technical-trading/a-few-notes-on-the-art-and-science-of-technical-analysis/
- Peter Brandt profile and rules synthesis: https://pictureperfectportfolios.com/how-to-invest-like-peter-brandt-commodities-trader-and-chartist/
- Linda Raschke and Larry Connors, Street Smarts: Turtle Soup rule comparison: https://proea.app/en/blog/turtle-soup ; Holy Grail: https://tradersmastermind.com/linda-raschke-trading-strategy/
- Mark Minervini and David Ryan, Momentum Masters excerpt: https://pubhtml5.com/pklzi/jywe/basic/51-100
- Stan Weinstein rule summary: https://alphamethodx.com/blog/secrets-for-profiting-review/
- CMT Association learning objectives: https://cmtassociation.org/cmt-program/learning-objectives/ ; Investopedia CMT guide: https://www.investopedia.com/terms/c/cmt.asp
- Brian Shannon Anchored VWAP, TrendSpider documentation: https://help.trendspider.com/kb/anchored-indicators/anchored-vwap-volume-weighted-average-price
