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
