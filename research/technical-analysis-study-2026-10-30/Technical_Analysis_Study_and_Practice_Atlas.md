# 1 A repeatable chart reading workflow

A chart is a compressed history of transactions. A capable reader reconstructs a sequence: where price came from, what it tried to do, what progress it achieved, how participation changed, and what happened at the next test. Pattern names are useful compression. The real skill is distinguishing two superficially similar pictures that have different context and different next decisions.

Use three separate statements:

1. **Observation:** “Three daily closes are above the previously marked 80–81 resistance zone.”
2. **Interpretation:** “The old ceiling is beginning to behave like an accepted trading area.”
3. **Decision condition:** “A controlled retest that holds that zone and turns upward on the timing chart would provide a different entry from buying today's extended close.”

This keeps the analysis specific without making it timid. It also makes learning possible: an inaccurate observation, weak interpretation and poor execution are different mistakes.

**The recurring questions**

- Is price trending, balancing, transitioning, or accelerating?
- Where is it within that state: early expansion, middle, mature extension, range edge, or range center?
- Which side has achieved progress during the last several swings?
- Is the counter-move becoming easier or harder?
- Has price merely crossed a level, or established itself beyond it?
- Where is the next obstacle, and what would constitute an actual change in character?

Do not begin by asking which indicator can make the answer green. Begin with the price map.


## Eight passes through an unfamiliar chart

A chart reader should be able to describe the picture before naming a trade. The following sequence is an original training protocol, not a claim that one published teacher mandates these exact steps.

**Pass 1: identify the canvas.** Read the symbol, exchange/feed, timeframe, price scale, visible date range, last completed bar, session definition, adjustment settings and volume units. Do not begin with the brightest arrow or indicator. A useful screenshot includes the axes and instrument identity. A cropped image with neither dates nor scale cannot establish exact levels or timing.

**Pass 2: see the large structure.** Temporarily ignore indicators. Locate the left-to-right progression of major highs and lows. Ask whether price is trending, balancing, accelerating, decelerating or transitioning. Mark the largest recent directional leg and the current position within it. A rally at the lower edge of a year-long range and a rally above all visible highs can look identical when tightly cropped but present different problems.

**Pass 3: locate the market.** Identify nearby prior swing zones, range edges, large gaps, breakout shelves and event-origin levels. Describe the distance from price to each in price units and normal volatility units. The nearest obstacle often matters more to a new entry than a distant attractive target.

**Pass 4: inspect the approach.** How did price arrive? Compare the speed, overlap, range and participation of the approach with the previous move away. A fast decline into support and a slow low-volume drift into it need different confirmation. The location tells you where to pay attention; the approach tells you what question to ask.

**Pass 5: inspect the response.** Read bodies, wicks, closes, failed excursions and the next completed bars. Separate a temporary touch from continued trade above/below the level. Record observations such as “three closes above the former range ceiling” rather than attributing unobservable intent to institutions.

**Pass 6: add selected measurements.** Use averages for trend context, momentum for character, and volume tools for participation/location. Each tool should answer a specific question not already answered by another panel.

**Pass 7: connect timeframes.** Begin with the weekly background, use the daily for structural location, the hourly for timing, and the 10-minute for refinement. These roles fit the established workflow; they do not make every timeframe an equal vote. A 10-minute reversal can be an hourly bounce inside a daily downtrend.

**Pass 8: write the decision boundary.** State the working interpretation, the strongest competing interpretation, the next confirming behavior, the behavior that invalidates it, and whether price now offers room relative to the required risk. This is the conversion from chart appreciation into trading judgment.

# 2 Chart construction and visual geometry

Before drawing, record symbol, instrument, venue/feed, adjustment convention, session, timezone, interval, visible dates and last completed bar. A split, dividend adjustment, missing session, stale quote or incomplete candle can create a visually persuasive but different picture. Keep these checks brief and systematic so they support analysis rather than replace it.

Use an uncluttered price pane first, then add volume and only the overlays needed for the question. Keep the vertical scale explicit. Linear axes compare absolute changes; logarithmic axes compare proportional changes. A line spanning a multiyear doubling can look quite different after changing scales. The ChartSchool trendline guide explicitly discusses this distinction and recommends not forcing lines through incompatible pivots. [S02]


CME explains that candlesticks and OHLC bars encode open, high, low and close; line charts suppress much of that intraperiod range information. Candle bodies and wicks make that range readable, while timeframe selection changes what each bar summarizes. The training implication is to use a closing-price line when visual clutter hides structure, then return to candles to inspect the particular decision zone. Neither display adds data missing from the feed. [CME chart types](https://www.cmegroup.com/education/courses/technical-analysis/chart-types-candlestick-line-bar)

Linear axes allocate equal vertical distance to equal absolute price changes. Log axes allocate equal distance to equal proportional changes. This can alter trendline geometry over a large price range. Session, timezone and corporate-action settings are also configurable and should accompany a chart record. [TradingView chart configuration](https://www.tradingview.com/support/solutions/43000748166-how-to-configure-your-supercharts/)

![Identical synthetic growth on linear and logarithmic axes](assets/scale_geometry.png)

**Worked visual case: apparent acceleration.** Both panels contain exactly the synthetic series 10 × 1.06^t, for bars 0–30. On the linear panel the slope steepens; on the logarithmic panel it is straight. Observation: each bar increases by 6%. Inference: the growth rate is constant in percentage terms, despite increasing dollar increments. Competing explanation: a reader looking only at the linear panel might label it accelerating momentum. Decision criterion: specify whether acceleration means dollar change, percentage change or a volatility-adjusted change before assigning the label. A line drawn on the linear panel is not transferable unchanged to the log panel.

Dividend-adjusted charts incorporate distributions and differ from unadjusted quoted-price histories. Record the choice when comparing old levels or screenshots from different platforms. [TradingView dividend adjustments](https://www.tradingview.com/support/solutions/43000590597-how-to-adjust-data-for-dividends/)

**Practical comparison drill:** open two screenshots said to show the same stock. Before judging which analysis is better, reconcile symbol, exchange, timezone, regular/extended hours, bar interval, endpoint, split/dividend treatment and scale. If their bars are different, resolve the data/display question first. Do not invent a technical explanation for a settings mismatch.

# 3 Trend swings support and resistance

An uptrend consists of advancing swing highs and lows; a downtrend consists of declining ones. A sideways sequence has repeated overlap rather than sustained directional progress. Fidelity also distinguishes primary, secondary and minor trends: the smaller movement sits inside a larger one. [S03]

For a reproducible reading, choose a pivot convention and retain it throughout the review. Here is an original training convention:

- A **candidate high** is the highest high so far in the local upswing.
- A **confirmed five-bar pivot high** has two completed bars with lower highs on each side. A low is the converse.
- Record both **pivot date** and **confirmation date**. A Monday high confirmed after Wednesday's close was not known to be that pivot on Monday.
- Use a separate **structural swing** label when a move is important to the trade horizon. Not every five-bar pivot deserves a horizontal level.

This is a training convention, not a universal definition. If equal highs or outside bars occur, state how ties are handled. Changing pivot rules to rescue a pattern defeats the purpose.

Mark the last two meaningful highs and lows. Then ask what broke first. In an uptrend, a lower high is a warning; a break of the important higher low adds different evidence. A very steep trendline can break while the sequence of higher lows survives. A horizontal range may form before any reversal. Do not collapse all three into “trend is dead.”

Dow Theory supplies the larger idea of trend persistence and confirmation across market averages. Its historical confirmation framework concerns the Industrial and Transportation averages; applying an analogous check to an index, sector and individual stock is a modern adaptation, not the original rule. [S04]

### A useful swing-comparison worksheet

For each impulse and correction, record:

| Field | What to inspect | Why it helps |
|---|---|---|
| Distance | Points, percentage and optionally ATR units | Separates economic size from screen appearance |
| Duration | Completed bars | Distinguishes a fast repricing from a slow drift |
| Overlap | How much each bar re-enters prior bars | Identifies smooth movement versus negotiation |
| Close location | Near high, low or center | Describes how much of the excursion remained |
| Participation | Relative volume on comparable intervals | Puts price progress in activity context |
| Boundary result | New extreme, rejection, hold or failure | Connects local action to the structural map |

Compare like with like. An eight-bar correction cannot be judged only by total volume against a two-bar impulse; inspect average activity and the distribution of activity as well.


![Compare a continuing advance with a lower high and loss of the prior higher low. These are synthetic confirmed swing maps, not candles or real securities.](assets/swing_structure.png)

**Read the contrast:** in A, each meaningful high and low advances. In B, 96 fails to exceed 98, then 87 loses the previous 91 low. The subsequent recovery to 91 fails to restore the earlier sequence. The dashed level is a reference for that transition, not a prediction that every retest must fail.

## Zones and trendlines

Support and resistance are areas of repeated interaction, not magical pixel-perfect prices. Prior turning points and accepted ranges are useful anchors; a broken level may later change role. ChartSchool explicitly allows zones when volatility makes a single price too precise. [S01]

An original three-layer zone method:

1. **Core:** the cluster of closes or repeated bodies around the level.
2. **Excursion band:** nearby wicks showing how far price repeatedly probed.
3. **Failure boundary:** the distinct structural extreme beyond which the current interpretation needs revision.

Do not mechanically widen all zones. A wide zone may be accurate but unsuitable for a tight-risk entry. The solution is to wait for a smaller structure or accept that this setup offers poor trade geometry, not invent a tighter structural stop.

Choose levels before examining the outcome. Prioritize the nearest relevant levels plus major higher-timeframe boundaries; a chart covered with twenty lines can explain anything after the fact. Keep a level record: origin, dates tested, type of reaction, timeframe and current role. Fresh tests that produce strong displacement matter differently from repetitive weak bounces that make less progress.

For trendlines, connect meaningful lows in an advance or highs in a decline. Two points establish a candidate; a third separate interaction strengthens the interpretation. Keep the anchors and scale fixed. Record a revised line separately instead of erasing the old one. A break is an event to investigate: did the move merely decelerate, enter a range, or reverse its swing structure? [S02]

**Confluence should mean different information.** A former range top, a rising daily average and an event-anchored cost reference can describe different aspects of the same area. Three similar moving averages derived from the same closes do not supply three independent confirmations. Count the reasons, but also describe them. The practical benefit is a clearer decision area rather than a count of decorative confirmations.

# 4 Candles participation and local response

For an ordinary OHLC candle define range R = H − L; body B = |C − O|; upper wick U = H − max(O,C); lower wick D = min(O,C) − L; close-location fraction CL = (C − L)/R when R > 0. These are transparent descriptive measurements, not automatic trading signals. R = 0 needs explicit handling rather than division. Compare the current bar with its recent neighbors, not with the entire screen's changing vertical zoom.

![Synthetic candle geometry exercise](assets/candle_measurement.png)

**Exercise and answer key:**

- A: range 6, body 4, upper wick 1, lower wick 1, close location 5/6. The close is near the upper end and the net advance is substantial relative to the range.
- B: range 6, body 0.5, upper wick 4.5, lower wick 1, close location 1.5/6. It is green but closes in the lower quarter. Green does not mean the whole bar was strong.
- C: range 6, body 4, upper wick 1, lower wick 1, close location 1/6. The net decline is substantial and the close is near the low.
- D: range 6, body 0.5, upper wick 0.5, lower wick 5, close location 5.5/6. It ends well above the low. The chart alone does not reveal the exact intrabar sequence, who traded, or whether the next bar will confirm a reversal.

**The important distinction:** a small body says little net movement between open and close. It does not mean nothing happened. B and D both have small green bodies, but their excursions and closing positions differ. Read the whole candle.

**Context before vocabulary.** A lower wick near an established floor invites a question about rejection of lower prices. A similar wick in the middle of a wide balance may be ordinary two-way activity. A long positive body breaking a multiweek shelf is different from the same body arriving at a nearby weekly ceiling after an already extended advance. Naming a hammer or engulfing candle is the start of description, not the end of analysis.

![The same candle language asks different questions at a prior boundary. Shaded levels are assumed context, not levels inferred from hidden historical bars.](assets/candle_context_1.png)

**Read A and B:** A shows a declining sequence, a probe beneath the assumed floor and a subsequent advance. B shows an advancing sequence, an excursion above the assumed ceiling and a subsequent decline. Cover the final bar: at the probe, the reading is only a candidate rejection. The response shown afterward is additional evidence.

![Overlapping balance and persistent decline. Both are original synthetic constructions.](assets/candle_context_2.png)

**Read C and D:** C shows overlapping two-way activity without an obvious boundary test. D shows persistent lower closes. Small bodies or momentary pauses have to be interpreted within that larger sequence. The figures are deliberately simplified synthetic constructions; the bar axis is not calendar time.


## Named candle sequences
A bullish engulfing body covers the previous body; it need not cover the full previous high–low range. A hammer after a decline highlights a lower-price rejection; a morning star organizes a decline, hesitation and recovery across three candles. Context and follow-through are part of interpreting a bullish reversal, not optional decoration. [S06]

The bearish counterparts ask whether an advance is losing control. A shooting star emphasizes an upper excursion that was not retained; bearish engulfing and dark-cloud cover show stronger selling after an advance; an evening star organizes advance, hesitation and decline. A small body alone is not bearish: its meaning depends on the preceding move and subsequent resolution. [S07]


## Price and volume together

Volume helps distinguish a quiet pause from active repricing, but it must be attached to the movement it accompanies. Fidelity's educational discussion uses volume as confirmation of a price trend; it does not make a tall histogram sufficient to identify the next direction. [S08]

An original four-cell reading grid:

| Price result | Participation | First interpretation to investigate |
|---|---|---|
| Strong progress | Expanding | Active directional move; inspect location and extension |
| Little progress | Expanding | Two-sided opposition; ask which boundary survives next |
| Modest correction | Contracting | Possible pause; test whether the prior side resumes control |
| Large excursion | Thin | Vulnerability or lack of opposing liquidity; inspect tradability and next response |

The important word is **investigate**. At support, heavy activity with little further decline could precede a rebound; at resistance, heavy activity with little rise could precede a retreat. But an ongoing strong move can also pause and resume. The next test resolves part of that ambiguity.

Compare current intraday volume with historical activity at the same time of day, not with a full-day total. Distinguish consolidated shares, one-venue volume, futures contracts and tick counts. If the source is venue-limited, the reading describes that feed. This makes the interpretation precise enough to use rather than invalidating it.
## Read body and full range as two different grammars

The recovered [candle taxonomy](https://github.com/dwj9ddyvf6-hub/Midna/blob/96e36e379cbe9330441221554d848f270d288800/workspace/alpaca-swing-desk/desk/research/candlestick-patterns-v2/TAXONOMY.md) adds three useful scales: a candle's body and wicks relative to its own range; its size relative to ordinary recent movement; and its role within a multi-bar episode. A nearly wickless tiny candle is not the same event as a large displacement. Separately record body engulfment or containment, full-range expansion or containment, and location at a structural boundary. These relationships can legitimately give different labels.

**Original dual-grammar drill:** first candle O=106, H=110, L=99, C=102; second O=101, H=108, L=100, C=107. The second green body engulfs the first red body, yet its full high-low range remains inside the first range. It is both body engulfing and a TheStrat inside bar under strict exceedance. Add a preceding decline before calling this a classical bullish-reversal setup. Neither label by itself supplies that context.

**Reverse comparison:** first O=102, H=108, L=98, C=106; second O=105, H=109, L=97, C=103. The second body is contained within the first body, while its full range exceeds both old extremes. Body contraction therefore does not necessarily mean a quiet session: this bar has made a two-sided excursion with a smaller net open-to-close displacement.

## Organize candle names into episodes

Use a few progressions rather than memorize isolated silhouettes:

- **Contraction and escape:** a harami or harami cross describes body contraction; a subsequent directional bar supplies new information. Specify whether that confirmation clears a body edge, a close or the full earlier range.
- **Opposition and follow-through:** engulfing describes a two-body relationship; a third confirming bar belongs to a later information time. Do not backdate a three-outside interpretation to an earlier entry.
- **Partial to full recovery:** after a red body from 105 to 100, a later close at 102 recovers less than half, 103 more than half, and 105 reaches the old open. Those close levels alone do not complete thrusting, piercing or engulfing patterns: opening location, candle color, other geometry and context remain necessary.
- **Impulse and digestion:** rising or falling three methods describe progress, counter-move and resumption. Ask whether the final bar restores directional progress or merely rebounds inside the first range.
- **Persistence and deterioration:** several advancing closes may retain large bodies and strong close locations, or begin shrinking while adverse wicks grow. Describe that change before assigning an exhaustion name.

**Confirmation-clock exercise:** freeze a two-bar interpretation, then reveal one bar. Record what became knowable and remeasure remaining room to resistance or support. More confirmation buys information but may worsen location. If the early idea fails and a later reclaim occurs, preserve the first failure and open a new episode rather than revise the old decision.

## Detector names do not guarantee identical construction

The [archived synthesis](https://github.com/dwj9ddyvf6-hub/Midna/blob/96e36e379cbe9330441221554d848f270d288800/workspace/alpaca-swing-desk/desk/research/candlestick-patterns-v2/SYNTHESIS.md) tested custom definitions. Primary implementation documentation clarifies several distinctions without making one library the only discretionary tradition. A tri-star is more specific than three dojis: TA-Lib requires the middle body to gap and the third to return toward the first. Its kicking construction uses opposing marubozu-like candles separated by a gap, not arbitrary shadow-rich candles. [TA-Lib tri-star](https://ta-lib.org/functions/cdltristar.html); [kicking](https://ta-lib.org/functions/cdlkicking.html).

TA-Lib breakaway begins with a body gap and ends with the fifth close inside that original gap; the archive's full-reclaim construction is different. Its ladder bottom requires a meaningful fourth-candle upper shadow and fifth-candle recovery above that high, rather than the archive's much larger recovery over the first open. [Breakaway](https://ta-lib.org/functions/cdlbreakaway.html); [ladder bottom](https://ta-lib.org/functions/cdlladderbottom.html).

For piercing, opening below the previous low is stricter than opening below its close. Morning-star penetration is configurable; TA-Lib's documented default is 30%, not automatically the archive's midpoint criterion. Three-method definitions also differ in middle-candle containment. Preserve the exact recipe before comparing classifications or counts. [Piercing](https://ta-lib.org/functions/cdlpiercing.html); [morning star](https://ta-lib.org/functions/cdlmorningstar.html); [three methods](https://ta-lib.org/functions/cdlrisefall3methods.html).

:::pagebreak

## Learn an instrument's pace without rewriting the future

The recovered [AI-50 atlas](https://github.com/dwj9ddyvf6-hub/Midna/blob/96e36e379cbe9330441221554d848f270d288800/workspace/goals/ai-top50-pattern-study/hidden_files/PATTERN-ATLAS-DRAFT.md) suggests a useful personality card: ordinary versus unusual leg size, elapsed bars, retracement depth, average-relative position and distance to the next obstacle. Its reported statistics come from a selected historical window and fixed-percentage close-based zigzags, not a new result here. Completed zigzag endpoints are retrospective; the live extreme is tentative until its reversal criterion is met.

Compare a fast small constituent with its smoother sector ETF. Ask whether an apparently modest pullback is ordinary for that instrument or unusually deep, and whether it happened in two bars or twenty. State-frequency tables do not establish a joint setup's success probability. Use them to design contrastive examples, not to turn confluence into invented odds.

### A volatility normalized comparison drill

These invented inputs isolate measurement from interpretation. Both instruments have pulled back from 100. Instrument A now trades at 94, with a recent ATR of 4; instrument B trades at 97, with ATR of 1. A has retraced 6% or 1.5 ATR, whereas B has retraced 3% or 3 ATR. The smaller percentage decline is the larger volatility-normalized move. Neither measure alone identifies the better setup.

Suppose A reached its present level in three bars and B in twelve. Record elapsed bars, overlap, close locations and participation. A fast decline could be a sharp interruption of a trend; B's slower decline could be orderly digestion or persistent erosion. Identify the actual swing structure before choosing either explanation.

Now add floors drawn before the comparison at 92 for A and 96 for B, with a first overhead obstacle at 99 for both. From the stated prices, distance to the floor is 2 points versus 1, and room to the obstacle is 5 versus 2. Those distances describe current geometry, not executable rewards or losses. A later confirmation price changes both distances; a stop buffer, gaps and costs would change a trading plan further.

**Write four separate lines:** the instrument's baseline movement; the current structure; the response required for confirmation; and the remaining room at that confirmation. Compare both charts at the same information cutoff. Explain which observation would invalidate each reading before revealing another bar.


# 5 The pattern family handbook

Each family below has four layers: recognizable geometry, structural meaning, completion event and a nearby alternative explanation. A pattern can be useful while still forming, but anticipation and confirmed completion are different entry styles.

## 7.1 Head and shoulders top

After an advance, identify a peak, a higher peak and a later lower peak. Connect the intervening reaction lows as the neckline. The crucial event is loss of neckline support, not merely a symmetrical drawing. A return toward the broken neckline can test its new role. The head-to-neckline height supplies a conventional projection, but intervening support remains relevant. [S09]

**Reading task:** distinguish a lower right shoulder from an ordinary pause beneath a recent high. Until support breaks, the chart may still be a range. Avoid manufacturing symmetry by ignoring inconvenient bars.

## 7.2 Inverse head and shoulders

After a decline, look for a low, a deeper low and a higher low, separated by rebounds defining the neckline. A break above that boundary completes the classical formation. The bottoming guide gives greater weight to expansion in activity on the upside completion than in the topping counterpart. [S10]

**Reading task:** notice the transition from inability to hold a new low to inability to revisit it. A higher right shoulder is promising structure, but the overhead neckline remains an obstacle until overcome.

## 7.3 Double top and double bottom

Two similar peaks after an advance create a possible double top; the intervening trough is the confirmation boundary. Two similar troughs after a decline create a possible double bottom; the intervening high is the confirmation boundary. The first test is normal trend behavior; the second establishes a comparison, not certainty. [S11, S12]

**Reading task:** ask whether the second approach is forceful or hesitant, whether it spends time beyond the first extreme, and whether the reaction breaks the intervening structure. Do not call every pair of highs a top. A sequence of rising lows beneath those highs might instead be an ascending triangle.

## 7.4 Triple tops and bottoms

Three separated similar highs followed by a support break define a completed triple-top reversal. Three separated similar lows followed by a resistance break define a completed triple-bottom reversal. Before completion, the same boundary interactions can belong to a rectangle or triangle. [S13, S14]

**Reading task:** the number of touches is less informative than the path between them. Deeper reactions away from resistance suggest a different balance than increasingly shallow reactions into the same ceiling. Three equal lows with falling rally peaks are not automatically a bullish base.

## 7.5 Ascending, descending and symmetrical triangles

An ascending triangle combines a roughly level ceiling with rising lows; a descending triangle combines a roughly level floor with falling highs. Their conventional directional biases differ. A symmetrical triangle contracts between lower highs and higher lows; its eventual escape direction deserves observation rather than assumption. Participation often contracts during compression and expands on resolution. [S15, S16, S17]

**Reading task:** mark all qualifying swings, not only the two that create the neatest lines. A breakout occurring only because converging lines have nearly reached their intersection may convey less actual displacement than an earlier decisive move. An opposite-side breakout changes the working interpretation.

## 7.6 Rising and falling wedges

Both boundaries slope in the same direction and converge. In a rising wedge, advances are becoming narrower as price climbs; in a falling wedge, declines narrow as price falls. A rising wedge has a conventional bearish bias, a falling wedge a bullish one, but the relevant boundary break supplies completion. The prior trend determines whether the setup would be a continuation or reversal. [S18, S19]

**Reading task:** distinguish a genuinely narrowing structure from a parallel channel. Rising lows do not cease to exist merely because the shape has been labeled bearish. Record the point where the actual swing sequence changes.

## 7.7 Expanding formations and broadening wedges

A megaphone alternates to higher highs and lower lows; it describes expanding rather than contracting swings. It should not be read as a quiet coil. [S20]

For an ascending broadening wedge, both boundaries rise but the upper rises faster; for a descending one, both decline while separating. Bulkowski's own indexed descriptions distinguish these from converging wedges and discuss breakouts and failed breakouts. Direct page opens were blocked, so this study uses the indexed first-party definitions only, not an independently audited performance claim. [S21, S22]

**Reading task:** expanding risk distance can turn an attractive-looking boundary into an impractical entry. Do not import a tight-coil stop into a widening structure.

## 7.8 Flags and pennants, bullish and bearish

First locate the forceful preceding move, the flagpole. The pause is smaller: a flag is commonly a compact parallel consolidation against the move; a pennant is a compact converging one. The directional continuation is completed by a break out of the pause in the prior impulse's direction. A generic sideways patch without an impulse is not automatically a flag. [S23]

**Reading task:** compare the pause's depth, duration and activity with the impulse. Is it compact and controlled, or has it retraced most of the move and acquired its own opposing trend? A bullish flag below major daily resistance has a different route from the same flag above a newly cleared base.

## 7.9 Cup and handle; inverted cup and handle

A cup with handle combines a rounded consolidation, recovery toward the prior rim and a smaller final pullback or pause. The handle breakout is the principal completion event; a very sharp V rebound is not the classic rounded cup. [S24]

The inverted form reverses the broad geometry: a rounded crest and decline followed by a smaller handle before a downside resolution. Bulkowski's first-party indexed examples show varied shapes and durations; the direct page could not be opened, so this is identified as excerpt-based coverage. [S25]

**Reading task:** measure the handle relative to the cup and examine its location. A very deep handle can be a new deterioration rather than a minor final pause. Do not use a name to conceal that difference.

## 7.10 Rectangles and channels

A rectangle repeatedly rotates between approximately horizontal boundaries; a channel does so between approximately parallel sloping boundaries. A rectangle's breakout completes the formation. In a rising channel, lower-boundary support and progress toward the upper boundary matter; failure to reach the upper side can be an early change, while an upside escape may represent acceleration rather than reversal. Reverse the reading for a falling channel. [S26, S28]

**Reading task:** separate trading a rotation inside the structure from trading escape from it. Buying the upper edge with a range-trading premise is inconsistent unless a distinct breakout premise has replaced it.


:::pagebreak

## Compare the structural grammar

![Four simplified synthetic geometries. Each is only a candidate shape; the surrounding trend, participation, completion and failure rules still have to be read.](assets/pattern_grammar.png)

# 6 Breakouts retests and failure sequences

Use a five-stage vocabulary:

1. **Approach:** price is near the marked boundary.
2. **Probe:** price trades beyond it but does not necessarily close there.
3. **Close-through:** the completed chosen bar finishes beyond it.
4. **Acceptance:** subsequent behavior sustains trade beyond the area rather than immediately abandoning it.
5. **Retest and response:** price returns; the next reaction tests whether the role has changed.

This is an original operational vocabulary. Choose beforehand which stage is sufficient for the specific setup. Requiring every stage can miss moves without retests; requiring only a probe accepts more unconfirmed entries. These are tradeoffs to practice, not reasons to keep changing standards afterward.

Record breakout quality in components, not a single magical score:

- Displacement beyond the boundary relative to volatility.
- Closing location and retained distance beyond the zone.
- Number of completed bars holding beyond it.
- Expansion or contraction of participation on comparable intervals.
- Distance to the next meaningful obstacle.
- Stretch from the nearest defensible structure.
- Reaction at a retest, if one occurs.

A dramatic wide-range bar can establish direction and still be a poor new entry because it is too far from the structure that would define the risk. The right reading can therefore be “bullish breakout, wait for a new structure” rather than “bad breakout.”

**Failed patterns are part of learning the craft.** Write what was expected, how soon it should appear, and what actually appeared. A return inside a range after a breakout is an alert; sustained movement through the opposite side is a more substantial reversal of evidence. Do not automatically reverse every stopped-out trade: an unsuccessful entry is not always an opposite setup.

Grimes teaches pullbacks as a core pattern family and describes a nested pullback as a smaller pause during the drive out of a larger one. This can help interpret a second entry opportunity or avoid mistaking every pause for a failure. [S29, S30]


## A controlled two path visual experiment

The original synthetic charts below show two paths with identical OHLC and volume history through bar 19. Neither path can be identified in advance from the shared prefix. The comparison teaches the value of updating the interpretation as new behavior arrives.

![The continuation branch. The entire history through bar 19 is identical to the failure branch shown next.](assets/breakout_acceptance.png)

**At bar 17:** price has approached the shaded 99.7–100.3 zone repeatedly. There is a visible boundary and compressed trading underneath it. Working interpretation: a potential upside resolution. Competing interpretation: continued range trading. Criterion: meaningful completed trade above the zone rather than another small excursion inside it.

**At bar 18:** the close is 102 with increased synthetic volume. Observation: the close is outside the prior ceiling. Inference: an upside break has occurred in this constructed example. Competing interpretation: a temporary extension that could return to the range. Criterion: continuation or subsequent ability to retain/reclaim the shelf. The bar is already farther from the floor than the pre-break price, so a breakout can improve confirmation while worsening entry distance. Those are separate facts.

**At bar 19:** the close is 102.6. Both scenarios remain identical. A statement that the breakout will succeed is not available from the shared history. One can now plan an allowed entry model, wait for a retest, or pass if distance to invalidation exceeds the chosen budget. 

**Path A, bars 20–22:** price pulls back toward the shelf while synthetic volume diminishes. Bar 22 closes 100.4. Observation: closes remain above the upper boundary, while lows approach it. Inference: a retest is developing. Competing interpretation: the first stage of a deeper failure. Criterion: a new upward response without sustained loss of the shelf. Bars 23–25 illustrate that response, but they were not knowable at bar 22.

![The failure branch. Later bars differ, while the original boundary and shared prefix remain unchanged.](assets/breakout_failure.png)

**Path B, bars 20–22:** price returns into the zone and then closes below it, with increasing synthetic volume. Observation: the breakout shelf has been lost. Inference: the original immediate-continuation thesis has deteriorated. Competing interpretation: a shakeout followed by reclaim. Criterion: require the reclaim actually to occur; do not silently rename every failed breakout a shakeout. Bars 23–25 illustrate further decline, not a universal outcome of all failures.

**A useful distinction:** rejection describes an excursion and return; acceptance describes persistence and continued trading in the new area. Operational definitions can use completed closes, elapsed time, retests and range overlap. Choose the definition in advance for the timeframe being studied. “It held” should be traceable to observed behavior, not merely a favorable final screenshot.
:::pagebreak

## Turtle Soup and session sweep variants
**Turtle Soup and Plus One are distinct.** The institutional teaching article specifies a new 20-day low with the earlier low at least four sessions old for Turtle Soup, followed by same-day recovery entry above that earlier level. Plus One uses a three-session age requirement, a close at/below the old low, then next-day recovery entry at that level. Both reverse for shorts. Exact offsets, expiry and protection differ; do not blend the variants. The full books remain unread, and exact Anti/80–20/Momentum Pinball originals are still access gaps. [TradingMarkets teaching article](https://tradingmarkets.com/recent/How_To_Use_TMs_Indicators_The_Turtle_Soup_Plus_One_Lists-665446)

**Sweep-and-reclaim adds session structure.** The retained KZ specification maps prior-day/untouched older extremes and Asia/London ranges before the U.S. opening window. The useful visual sequence is excursion through a mapped level, a completed signal candle back across it, then an opposite-side objective. Distinguish a reclaim from acceptance beyond the boundary. Its source/assumption table is valuable: instrument proxies, which reclaimed level to choose, numerical buffer, scale timing and hard exit are partly new implementation choices. A contradictory example target versus its stated minimum reward/risk remains unresolved. Futures-to-ETF level mapping is a separate approximation, not identical geometry.

For both families, mark the original level before the excursion and use only the low/high known at decision time. A stop using the day's eventual extreme would know the future. A liquidity-sweep label describes price behavior; it does not independently identify whose orders traded.


Archived implementation reference: [session sweep and reclaim specification](https://github.com/dwj9ddyvf6-hub/quant-research-backup/blob/d17352421810995729739dfe0815d46e5e60cddc/research/othersidebj_kz_sweep/strategy_spec.md).


# 7 Indicators with distinct jobs

## EMA: orientation and distance

EMA weights recent observations more heavily than older ones. Fidelity describes trend direction and pullbacks toward a rising EMA as common uses, while stressing that the average responds with delay rather than identifying exact turning points. [Fidelity EMA guide](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/ema)

Original reading drill: first describe the swings without averages. Add the 21- and 50-period averages used in the existing workflow. Record (1) slope, (2) ordering, (3) price location, (4) separation, and (5) how price behaved during earlier approaches. Ask whether the average is summarizing an orderly trend or cutting through repeated overlap. “Price above the EMA” and “the EMA rising” are different observations. A reclaim from underneath differs from a first pullback after a strong advance. Do not change periods until one hugs the current price; keep the chosen lens consistent across examples.

## RSI: momentum character, not a blanket sell label

RSI uses smoothed gains and losses and is typically shown on a 0–100 scale. StockCharts documents both conventional 70/30 reference levels and the possibility of sustained extremes during strong trends; it also discusses bull/bear range behavior. Parameter length and initialization affect the reading. [StockCharts RSI](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi)

Original reading drill: compare three successive price pushes and pullbacks with their RSI excursions. Identify whether RSI is recovering quickly, failing repeatedly near a similar region, or establishing a different range. Annotate the price swing dates used in any divergence. A divergence is a comparison of specified swings, not a vague downward line across convenient peaks. Use the price structure to define what would turn the warning into an actionable change. RSI and relative performance against an index are different measurements.

## MACD histogram: read level and change separately

The usual MACD is EMA12 minus EMA26; its signal is an EMA9 of MACD; the histogram is MACD minus that signal. A histogram approaching zero from below can still be negative, indicating convergence rather than an already positive relationship. [StockCharts MACD histogram](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/macd-histogram)

Original reading drill: write two clauses, “histogram negative” and “histogram rising.” Then ask whether price has stopped making lower lows or merely slowed its decline. Similarly, a shrinking positive histogram can accompany continued rising prices. Track the difference between weakening momentum and a completed trend reversal. Do not treat EMA, MACD and a price-momentum oscillator as three wholly independent observations when all derive from the same prices.

## Fibonacci: a map of the selected swing

Common retracement references include 38.2% and 61.8%; the frequently included 50% midpoint is not a Fibonacci ratio. StockCharts presents these as zones to examine alongside price behavior, not guaranteed reversal prices. [StockCharts Fibonacci retracements](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-annotation-tools/fibonacci-retracements)

Original measurement drill: for an upswing L=80 to H=100, the downward retracement price is H − r(H−L). Thus 38.2%=92.36, 50%=90 and 61.8%=87.64. Record both anchor dates and whether extremes or closing prices define the swing. Identify which swing matters to the trade horizon before drawing the tool. If a daily swing and an hourly swing produce different zones, label them separately. Confluence is useful only when the underlying references have a reason to matter; redrawing anchors until a ratio lands on today's turn is not disciplined reading.

## Anchored VWAP: an event-specific cost reference

Anchored VWAP begins the price-volume accumulation at a selected bar rather than restarting with every session. Event anchors can include a major gap, high, low or earnings event. [StockCharts anchored VWAP](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/anchored-vwap)

Original reading drill: predeclare the anchor's rationale. Read price above/below the line, the line's slope, repeated interactions and the space to nearby structural zones. A high anchored line and a low anchored line describe different windows, not two independent votes. Specify whether the implementation uses actual transaction prices or bar-based typical-price approximations. The line does not establish the exact inventory or cost basis of all current holders. A reclaim is a price event to inspect; the instrument can cross the average many times in balance.

## Volume profile: where activity accumulated

StockCharts Volume-by-Price bins closing-price observations over the displayed period; its up/down colors are based on up/down periods, not direct buyer/seller identities. Its current profile must not be applied to earlier decisions using later observations. Other platforms' volume-profile algorithms can differ. [StockCharts Volume-by-Price](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/volume-by-price)

Original reading drill: freeze the lookback window and binning. Mark high-activity areas and lower-activity corridors, then inspect actual behavior when price reaches them. A large node can act as an area of balance rather than a precise reversal line. If the visible-range profile changes as you zoom, the underlying question has changed. Save the window with your screenshot. Never mistake a red/green profile for proof of dealer positioning, net accumulation or aggressive order flow unless the feed and classification actually measure those things.


## Build a coherent panel

Use price structure to describe the path. Use an average to summarize trend. Use a momentum measure to examine the rate and persistence of movement. Use volume or another genuinely distinct input to inspect participation. Use a volatility measure to put distances in context. A new panel should answer a question that the existing panel does not answer clearly.

Original example: a stock rallies from 80 to 100, pulls back to 94, then reaches 102. Suppose its first rally was fast and its second slow. A lower momentum peak indicates weaker measured momentum while the price trend can still make higher highs and higher lows. The question is then whether support at 94 and the most recent intermediate swing remain intact. Do not silently translate “weaker measured momentum” into “price must fall.” Conversely, if price breaks that swing, fails to recover it, and the next rally stalls lower, the structural reading has changed even if a slower indicator has not crossed yet.

Practice separate statements:

- Observation: the current high exceeds the earlier high.
- Observation: the indicator peak is lower under unchanged settings.
- Interpretation: upside momentum is weaker across those two comparable swings.
- Decision criterion: watch whether the last meaningful higher low holds and whether a retest is accepted.



### Bollinger's own instruction

John Bollinger describes bands as a relative high/low framework. A band touch alone is not a buy or sell; strong trends can continue along an outer band. BandWidth describes compression/expansion, while %b describes location within the bands. He also recommends complementary rather than redundant indicators. Those distinctions make bands useful for asking whether a move is extending, compressing or changing character, rather than assigning the same meaning to every touch. Source read: [Bollinger Band Rules](https://www.bollingerbands.com/bollinger-band-rules).

Original exercise: construct two sequences that both close at the upper band. In A, the average rises, pullbacks are shallow, and closes remain near the highs. In B, the average is flat, the price reaches a previously rejected range ceiling, and the next bar closes back in the range. Explain why identical band location does not imply identical trade structure. State the next observation that would change each interpretation.


## Ichimoku as a coordinated system

The package author's reference specifies Tenkan and Kijun as high/low-range midpoints over 9 and 26 periods, not close-based moving averages. Leading spans form the displaced cloud; Chikou is the current close displayed backward. Its example of a strong upward configuration places candles, Tenkan, Kijun and cloud in order. Plot displacement must be understood before comparing lines at a given date. Source read: [Ichimoku reference manual](https://r-multiverse.r-universe.dev/ichimoku/doc/reference.html).

Original practice sequence: hide all labels and identify which plotted element can change because today's price changes. Restore labels, mark both computation date and display date, then write a plain-language reading. A forward-drawn cloud is calculated from already available information; its placement on a future portion of the x-axis does not make it future observations. 

Compare a clean separation above the cloud with repeated crossings through a flat cloud. In each case, describe the space between price and nearby references, the order of lines, their slopes, and whether a fresh cross occurs in open space or within congestion. Use unchanged settings for the comparison.
## Plotted location and information availability
Midna's `quant-research/indicators/ichimoku.py` explicitly stores computed, displayed and available indices for every point. It puts leading spans ahead and Chikou behind while retaining the actual computation index. This is a useful teaching companion: ask which values could have been known at the replay cutoff, not just where a line appears on the completed chart. Its `known_at` function selects by availability rather than visual coordinate.


[Archived Ichimoku implementation](https://github.com/dwj9ddyvf6-hub/Midna/blob/6bbb2c8b304d8cd2b15fbcd30eca8ed842bdb0ed/quant-research/indicators/ichimoku.py)

## VWAP construction and a concrete recipe
The archived Quant Charts example obtains a VWAP series from a helper and computes a cumulative volume-weighted squared deviation from it. The helper body was not part of these five reads, so its fallback/session behavior is documented but not independently traced here. The shown band calculation itself uses cumulative arrays over the supplied frame. For chart interpretation, preserve the session or event anchor and the precise band definition; “two sigma” is not enough to reproduce a drawing.


[Archived VWAP example](https://github.com/dwj9ddyvf6-hub/Silicon/blob/3815c4b223be493704850519656fa7e7b3e3750b/research/rea_teardowns/artifacts/quantcharts/quant-charts-examples-source/quant-charts-examples-main/examples/workspace/indicators/built-in/python/vwap.py)

The Test repository's Griffith recipe combines a short-term average relationship, proximity to VWAP, RSI, market context and a scan score, with fixed numerical stop/target assumptions. The document labels the historical sleeve live; this study did not verify current operation. Its educational contribution is how a broad idea becomes a specific recipe. The exact fractions, universe and sizing are that recipe's parameters, not the definition of every VWAP pullback.


[Archived Griffith recipe](https://github.com/dwj9ddyvf6-hub/Test/blob/5b13da715e96f7d38397e6799caf8ec96a3b8994/strategies/griffith/griffith-vwap-pullback.md)

## Timestamp the divergence anchors
The archived scanner description pairs consecutive same-type price-close swings and compares RSI/OBV at those anchors. Regular bullish divergence means lower price but higher oscillator; regular bearish is the reverse. Its windows, minimum separation, one-bar interior-pivot confirmation, strength threshold, five-bar active life and near-30/70 labels are **that implementation**, not universal definitions. An overlap label is usable only when both component records already exist. The archive documents an earlier future-record overlap bug; visual historical labels can therefore look cleaner than signals available in real time.

Learn to draw and timestamp the anchors, then ask what price must do to confirm the interpretation. Do not treat an oscillator disagreement as an automatic reversal or transplant a single instrument/horizon result to all divergence. The later canonical-universe report changes the earlier daily-stock findings, so the early blanket headline is not the complete chronology. These are archived research claims, not freshly verified outcomes.


Source versions: [earlier RSI and OBV study](https://github.com/dwj9ddyvf6-hub/quant-research-critical/blob/f74ab2acf945220ba34099951982225e8238d386/galath-research/RSI_OBV_DIVERGENCE/REPORT.md); [later canonical universe study](https://github.com/dwj9ddyvf6-hub/quant-research-critical/blob/f74ab2acf945220ba34099951982225e8238d386/galath-research/RSI_OBV_DIVERGENCE/canon_v1/REPORT.md).


# 8 Advanced indicators overlays and market internals

This chapter extends the basic indicator panel with distinct questions about range position, momentum, volatility, flow and participation. It synthesizes three fully read archived method studies, with fresh primary-source checks for the formula corrections identified below.

## Oscillator literacy

### Range position, momentum, and exhaustion are different

- **Williams %R:** the latest close's position inside a 14-bar high-low range, scaled from −100 to 0. On identical unsmoothed windows it equals stochastic %K minus 100. Near zero means closing near the range high; it does not mean price must fall. In a strong advance, repeated high-end readings describe persistence. For a pullback read, ask whether the gauge resets while the price structure remains intact, then whether price resumes through a trigger.
- **CMO:** net positive versus negative close changes over its window, on a symmetric −100 to +100 scale. Its unsmoothed rolling sums differ from Wilder RSI smoothing. A close-to-close shock can dominate until it rolls out. It is not independent confirmation merely because its scale differs.
- **Vortex:** cross-bar upward/downward movement divided by summed true range. Relative position and separation of VI+ and VI− describe directional movement. Different 14/25-period choices change responsiveness; a cross in a range and a cross leaving a base are not the same setup.
- **TRIX:** percentage change of a triple-smoothed EMA, with a separately specified signal average. It is deliberately smooth; use its turning/slope/zero-line information on a matching horizon rather than demanding candle-level timing. Preserve EMA versus SMA signal identity.
- **KST:** a weighted blend of smoothed rates of change over several horizons. The archived daily recipe uses ROC 10/15/20/30, SMA smoothing 10/10/10/15 and weights 1/2/3/4. Weekly parameter sets must be named separately; weekly aggregation is not merely a daily chart zoom.
- **Awesome Oscillator:** SMA5(midpoint) minus SMA34(midpoint), where midpoint is (high+low)/2. Its bars can be red while positive: red means the oscillator fell from its prior value, not that the short average is below the long average. A positive-side saucer is a change in momentum within that side; a zero crossing is a different event. **It is not MACD minus its signal line.** [TradingView AO](https://www.tradingview.com/support/solutions/43000501826-awesome-oscillator-ao/), [MetaTrader AO](https://www.metatrader5.com/en/terminal/help/indicators/bw_indicators/awesome).
- **Ultimate Oscillator:** combines buying-pressure/true-range ratios over 7/14/28 periods, weighted 4:2:1. Learn the full divergence sequence, not just 30/70 zones: oscillator divergence and the qualifying extreme precede an oscillator breakout of the intervening peak/trough. The archived design explicitly distinguishes incomplete divergence from a completed event.
- **Coppock:** WMA10 of the sum of monthly ROC14 and ROC11 in the archived standard recipe. Its classic buy concept is an upturn while below zero, not necessarily a zero-line crossing. Its monthly index context should not silently become a daily single-stock short signal. Completed-month observations and live partial-month observations must be distinguished.
- **DeMARK Sequential:** nine consecutive qualifying close comparisons form a Setup; the subsequent Countdown may be nonconsecutive. Exhaustion duration differs from momentum magnitude. Completion, risk boundary, recycling/cancellation and response time all matter; a bare 9 or 13 is not the entire method. The source owner's 13-vs-8 qualifier compares the candidate 13's low for a buy, or high for a sell, against countdown bar 8's close. The archive's close-to-close qualifier is not that rule. DeMARK also describes a 12-bar response metric. [DeMARK's own explanation](https://demark.com/9-13/).

### Elder's useful separation: trend, pullback, permission

Elder-Ray measures high and low relative to EMA13. Bull Power positive and Bear Power negative can coexist on an ordinary bar straddling the EMA; neither sign alone establishes control. The useful read is the change: in a rising trend, negative Bear Power becoming less negative describes weakening downside pressure during a pullback. Elder Impulse combines the EMA slope and MACD-histogram change: both rising, both falling, or disagreement. Treat its colors as a constraint within that particular system, not as a substitute for location and an entry pattern.

Force Index adds another distinction: raw force is close change multiplied by volume. Its fast EMA2 can dip against positive EMA13 force during a broader advance. A practical sequence is: confirm the higher-level trend; observe the countertrend force reset; locate support; wait for the price trigger appropriate to the setup; define what failure of that support means. The archive adds a close-above-SMA50 rule for its own implementation; that is a desk convention, not a universal Elder definition.

### Volatility and flow need their own vocabulary

Mass Index tracks range expansion/contraction through a ratio of smoothed ranges; its bulge is directionless. Choppiness compares accumulated true range with the high-low envelope; its low reading says movement has been directional/efficient over the window, not which direction. DPO deliberately displaces the comparison into prior time; record the effective date rather than reading its last plotted crossing as today's momentum event.

Chaikin Oscillator measures momentum of the Chaikin accumulation/distribution line. VWMA is a rolling volume-weighted average of closes; an anchored HLC3 VWAP has a different price source and sample boundary. Ease of Movement relates midpoint displacement and range to volume: light-volume movement is not the same thing as heavy-volume demand. Klinger is stateful and implementation-dependent, so pin the volume-force formula and smoothing before comparing platforms. PVT weights volume by percentage price change; NVI and PVI condition updates on lower/higher volume than the preceding bar. Their labels do not identify actual smart-money participants.

The 50-session up/down-volume ratio is useful for grading sustained participation, especially alongside accumulation/distribution weeks. But one extraordinary earnings-volume session can carry the ratio for many weeks. Inspect the underlying event and absolute liquidity, not just a threshold.

**Historical-volatility percentile is not rank.** Percentile counts the fraction of historical readings below today's; min-max rank measures location between the window's lowest and highest readings. A single panic spike can leave min-max rank low even when current volatility exceeds most observations. Report the window, horizon, sampling convention and tie rule. Realized-volatility position alone does not say options are cheap.


## Overlays as reproducible maps

1. **Begin with dated real prices.** Prior session/week/month high, low and open are different from a confirmed swing. At a prior high distinguish intrabar breach, close beyond it, later acceptance, and breach followed by close back inside. The same line supports breakout, retest and failed-break narratives depending on the sequence.
2. **Know the channel boundary used at decision time.** Donchian breakout thresholds should reference the preceding N bars if the question is whether today's bar breaks the existing channel. Inclusive channels are useful for current range position, but testing today's high against a channel already including today's high changes the question.
3. **Read compression without choosing its direction prematurely.** Bollinger-inside-Keltner requires both upper and lower band containment; comparing widths alone is insufficient when their centers differ. Archive parameters EMA20 ±2×ATR10 are a named Keltner variant, not an assurance of matching every TTM implementation. Distinguish squeeze-on, release, momentum direction, price breakout and follow-through.
4. **Ichimoku is midpoint equilibrium plus displaced geometry.** Current cloud values originated earlier; the forward cloud is calculated from information available now and drawn ahead. Neither is future data. Distinguish cloud location, TK cross, Kijun interaction and Chikou clearance. A cloud twist is a change in projected span ordering, not a guarantee of a price reversal. Record calculation date and plot date separately.
5. **Pivot systems are not interchangeable.** Floor, Fibonacci, Camarilla, Woodie and DeMark pivots differ. Weekly/monthly arithmetic levels can frame swing trades, but dozens of overlapping pivot formulas manufacture apparent confluence if each gets an independent vote. TradingView Woodie uses current-period open with previous high/low; the archive's double-prior-close variant must be labeled differently. [TradingView formulas and session distinctions](https://www.tradingview.com/support/solutions/43000521824-pivot-points-standard/).
6. **Central Pivot Range is a band, not a directional prediction.** Compute pivot=(H+L+C)/3, raw BC=(H+L)/2, raw TC=2×pivot−BC; sort the two endpoints for display. The archive swaps the raw names but obtains the same sorted band. Width and acceptance above/below can be studied with price behavior; narrowness alone does not promise a trend. [Frank Ochoa's explanation](https://pivotboss.com/2010/05/31/a-quick-guide-to-the-pivot-range/).
7. **Separate trailing references.** SAR accelerates toward an extreme; Supertrend ratchets ATR bands from a midpoint; Chandelier offsets a rolling extreme by ATR. Their values answer different questions. A rolling Chandelier can loosen as volatility expands; it is not necessarily an entry-anchored ratcheted stop. The archive's SAR uses a close-crossing convention, whereas StockCharts' bullish/bearish scan examples use highs/lows crossing SAR. Name the convention before testing. [StockCharts SAR](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/parabolic-sar).
8. **Anchor VWAP to a meaningful event and say which one.** Swing, gap, earnings, IPO, ATH and year-start anchors ask about participation since different dates. Daily typical-price approximations are not tick-exact participant cost bases or intraday session VWAP. Standard-deviation bands measure dispersion in the specified sample; riding a +2σ band can be trend persistence rather than reversal. An IPO/ATH anchor requires appropriately complete history.
9. **Guppy ribbons summarize relationships.** Short EMAs 3/5/8/10/12/15 and long 30/35/40/45/50/60 reveal compression, expansion, ordering and overlap. Twelve smoothers do not make twelve independent observations. Study how the short ribbon repairs after a pullback relative to the slower ribbon, then verify price structure.
10. **Draw tools with auditable anchors.** A pitchfork depends on three selected pivots and the median through the midpoint of the latter pair. Log their dates and confirmation availability. For a Raff channel, fit the center to closes, but set parallel widths using the most distant HIGH or LOW; the archive's close-residual-only rail is a different regression channel. [StockCharts Raff construction](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-annotation-tools/raff-regression-channel).
11. **Heikin-Ashi is a transformed view.** Same-color wick patterns can clarify trend smoothness. Its synthesized opens/closes are not tradeable bar prices; use real OHLC for triggers, fills, gaps and stop tests.
12. **ATH and profile language needs precision.** Above the prior all-time high means no earlier traded prices above that high in the verified history; it does not mean no sellers, supply, hedging or issuance. TPO counts time brackets at price, while volume profile counts volume. D/P/b/elongated/double-distribution shapes organize auction observations, not uniquely identifiable participant motives. A daily bar cannot reconstruct a 30-minute TPO profile. Treat the archive's 20-session/40-bucket shape thresholds as custom classifiers, not canonical definitions.


## Market and group context

**Distribution/FTD is a sequence.** Track rally-attempt origin, day count, qualifying thrust, subsequent distribution and the failure boundary. A down day on increased volume is not automatically the same as a proprietary editorial distribution count. The archive explicitly uses SPY/QQQ ETF volume proxies, a simplified stall rule, fixed 1.25% FTD threshold and a trailing-60-session attempt anchor. Those are reproducible desk variants, not exact IBD reproductions. ETF flow and index-wide activity differ. Read improving participation and healthy individual breakouts alongside the market sequence, rather than treating a label as an entry.

**Breadth asks who participates.** A cumulative advance/decline line describes participation over time; McClellan's 19/39 EMA difference describes breadth momentum, and its summation describes a further accumulated measure. Compare index highs/lows with the corresponding breadth structure. A universe-specific series needs its membership, denominator and history documented; canonical NYSE thresholds do not transfer automatically to a small changing watchlist. Percentage above 50/200-day averages adds breadth of trend, but short-history names change the eligible denominator.

**TRIN asks whether volume participation matches issue participation.** Correct formula: (advancers/decliners)/(advancing volume/declining volume). The archive's purported equivalent flips both ratios and is actually the reciprocal. A worked check: 200 advancers, 100 decliners, 600 units up-volume, 100 down-volume gives TRIN=2/6=1/3, not 3. Lower readings indicate relative strength of advancing-volume participation. A smoothed series has a different extreme range from raw daily readings. [StockCharts TRIN](https://chartschool.stockcharts.com/table-of-contents/market-indicators/arms-index-trin).

**Zweig thrust is a transition, not a high reading.** The archived standard is EMA10(advancers/(advancers+decliners)) moving from below .40 to above .615 within ten sessions. Both thresholds and the timing matter. A watchlist analogue is useful to study but must not inherit a whole-exchange historical success claim.

**Relative strength has multiple benchmarks.** Compare name versus market, name versus sector, and sector versus market; conflicting readings are information. Rotation trails show change in relative trend and momentum, not absolute price direction. The archive's SMA-normalized two-axis recipe is a desk approximation, not an authenticated proprietary JdK formula; its assertion of an exact canonical EMA recipe was not established in this pass. Group ranks likewise depend on taxonomy, membership, weighting and horizon. The archive's equal-weighted GICS ret126 rank is not IBD's proprietary industry rank.

**Slow context stays slow.** AAII/II survey opinions differ from NAAIM reported exposure; publication date matters. Sponsorship snapshots grade the institutional backdrop but do not time today's entry. A 13F-manager count is not literally a mutual-fund count, and aggregated reported holdings require amendment, duplicate-reporting, security-class and denominator controls before an ownership percentage is trusted. Beta/correlation describe historical coupling on matched returns; they do not dictate the next move. A peer-relative trail with overlapping return windows is a trajectory view, not independent weekly evidence.


## Preserve the accumulation distribution distinction

The archived cumulative close-location-value times volume formula is Chaikin ADL, not a universal Williams accumulation/distribution definition. Sierra documents a Williams form based on close versus true high/low without volume. Identify the exact calculation before interpreting divergence. [Chaikin ADL](https://www.tradingview.com/support/solutions/43000501770-accumulation-distribution-adl/); [Sierra Williams formula](https://www.sierrachart.com/index.php?ID=42&page=doc/StudiesReference.php).

## Source studies
[Oscillators and volume study](https://github.com/dwj9ddyvf6-hub/galath-desk-backup/blob/70e3033dcda8a36a1da2cf70cc609401b603b2ad/corpus-2026-10-21/workspace/.scratch-setups-build/canon-gaps/study-oscillators.md); [Overlays and levels study](https://github.com/dwj9ddyvf6-hub/galath-desk-backup/blob/70e3033dcda8a36a1da2cf70cc609401b603b2ad/corpus-2026-10-21/workspace/.scratch-setups-build/canon-gaps/study-overlays.md); [Market internals study](https://github.com/dwj9ddyvf6-hub/galath-desk-backup/blob/70e3033dcda8a36a1da2cf70cc609401b603b2ad/corpus-2026-10-21/workspace/.scratch-setups-build/canon-gaps/study-market.md); [Femto V5 visual-learning research](https://github.com/dwj9ddyvf6-hub/Femto-lean/blob/58244bf2e020b1ed4b269b0c4f30638be456deb2/eyes/V5/RESEARCH_LLM_CHART_VISION.md)

# 9 Timeframes gaps and relative strength

Build a four-row worksheet:

- **Weekly background:** major trend/range, location within it, nearest substantial opposing zone, last completed week.
- **Daily structure:** active swing, pullback or base, important shelf, distance to invalidation, next obstacle.
- **Hourly timing:** sequence of lower highs/higher lows, reclaim or failure, quality of retest, current session context.
- **10-minute refinement:** trigger formation and execution geometry; do not allow a tiny pattern to erase the daily map.

Example of original reasoning: weekly uptrend; daily pullback approaching a prior breakout shelf; hourly still lower highs; 10-minute bullish reversal. Interpretation: favorable higher-level location but timing has not yet resolved. A candidate may improve if the hourly lower high is reclaimed and retained. A bullish 10-minute candle alone does not complete that event. Conversely, an hourly breakdown through daily support changes the thesis even if the weekly uptrend has not yet reversed. This is alignment by role, not “three green panels beat one red panel.”

Label every observation with its timeframe. A stop based on a 10-minute wick and a thesis based on a weekly trend are not automatically compatible. The duration and normal noise of the chosen setup must fit the invalidation method. If a live weekly candle is incomplete, distinguish its present shape from a confirmed weekly close.


## Gaps and comparative performance

Distinguish a gap between yesterday's close and today's open from a full gap between the prior range and current range. Context separates common congestion gaps, breakaway gaps, continuation/runaway gaps and possible exhaustion gaps. A gap out of a base should be inspected differently from a late gap after a long extended run. Do not assume every gap must fill immediately. [S31]

An original gap worksheet: prior range, opening price, gap size in ATR units, catalyst/time if known, first completed response, whether the old range was reclaimed, and end-of-period acceptance. A gap can remain open while the new session is weak; measure both the gap and the subsequent auction.

Relative strength is comparative performance, not RSI. The ratio of stock price to a relevant benchmark rises with outperformance, which can occur while both prices decline. Inspect both stock/index and stock/sector comparisons to separate broad exposure from individual leadership. [S32]

**Original example:** stock falls 2% while its sector falls 5%. It is relatively stronger but still losing absolute value. That can place it on a watchlist for recovery; it does not independently establish an upward entry trigger. Conversely, a stock up 3% while its sector gains 8% is rising but lagging.
## Screening and chart reading are distinct steps
Lector material separates relative strength, trend stage, extension, volatility, breadth and rotation. These answer different questions. The time-series percentile of a stock/SPY ratio is not its cross-sectional return rank. Raw distance from SMA50 in ATR units differs from the normalized-percent extension variant. A score can help order a reading list without being a calibrated probability or an entry trigger.

The feature code makes an additional ranking distinction: universe percentile uses the share of eligible names strictly below the value, while list percentile uses pandas ranking with its tie convention. Universe composition and ties can therefore change ranks even without a new price pattern. Preserve the observation date, data universe and missing-data treatment.

Two necessary source corrections: (1) the deep-analysis R1/V2 proposal incorrectly suggests replacing prior intraday-high thresholds with prior closing-high thresholds will demote existing breakouts. Since prior closing highs cannot exceed corresponding intraday highs, this is generally an easier test; only separately specified strict/tolerance details could alter boundary cases. (2) early source notes call composite weights unknown, whereas later feature code labels coefficients exact-by-fit. Fitting screenshots is not author disclosure. Dashboard agreement measures reproduction, not forecast accuracy.

Practice by selecting a strong relative name, inspecting its actual stage and extension, comparing market participation, then defining a chart-specific trigger. Keep rank, context, entry location and invalidation as separate statements.

Sources: [Lector deep analysis](https://github.com/dwj9ddyvf6-hub/Silicon/blob/3815c4b223be493704850519656fa7e7b3e3750b/research/lector-systems/research/SYSTEMS_DEEP_ANALYSIS.md), [feature implementation](https://github.com/dwj9ddyvf6-hub/quant-research-critical/blob/f74ab2acf945220ba34099951982225e8238d386/galath-research/CHARTSLECTOR/systems/ranker_feats.py) and [dashboard reproduction map](https://github.com/dwj9ddyvf6-hub/quant-research-critical/blob/f74ab2acf945220ba34099951982225e8238d386/galath-research/CHARTSLECTOR/out/faith_map.md).

## Selection timing excursion and holding horizon
The recovered [Grand Gestalt algorithm](https://github.com/dwj9ddyvf6-hub/Midna/blob/96e36e379cbe9330441221554d848f270d288800/workspace/research/grand-gestalt/GRAND_GESTALT_ALGORITHM.md) and [companion synthesis](https://github.com/dwj9ddyvf6-hub/Midna/blob/96e36e379cbe9330441221554d848f270d288800/workspace/research/grand-gestalt/SYNTHESIS.md) concern a cross-system allocation proposal, not simply the earlier visual Grand Synthesis under a new title. Their useful chart distinction is between why a name is selected, where an entry activates, whether the opportunity is a brief excursion, and what ends the holding thesis. A favorable maximum excursion does not establish an executable exit or a favorable final return.

**Original four clock exercise:** annotate a weekly selection thesis, an hourly trigger, a short event-driven excursion and a holding plan on one chart. Give each its own evidence and boundary. At activation measure distance from the trigger, distance to structural failure and room to the nearest obstacle. High ATR and poor entry location are not synonyms.

Two engines can agree because they share the same breakout inputs. List input, mechanism, timeframe, activation and management clock before treating their agreement as additional evidence. Combining an hourly trigger with a thirteen-week holding rule creates a new strategy; it does not inherit validation merely from the two ingredients. The archive's conflicting penalty signs, confidence scales and historical approval passages remain specification issues, not rules adopted by this study.

## Label the empty interval precisely
An open-to-previous-close gap compares two prints; the new bar may later overlap the old range. A body gap separates the open-close intervals while wicks may overlap. A full-range window separates the entire high-low ranges. A rising window can coexist with a red candle if the session falls from its own open while remaining wholly above the earlier range.

Mark both window edges and distinguish entering the interval, traversing it and subsequently accepting or rejecting it. Filling a gap and sustained structural failure are different events. Session boundaries, halts, sparse trading and missing data require separate checks; an intraday discontinuity is not automatically meaningless, and a data omission is not a market window. This refines the overly broad intraday language in the [archived taxonomy addendum](https://github.com/dwj9ddyvf6-hub/Midna/blob/96e36e379cbe9330441221554d848f270d288800/workspace/alpaca-swing-desk/desk/research/candlestick-patterns-v2/TAXONOMY_ADDENDUM.md).


# 10 Relative rotation and point and figure

Changing the representation changes the question. A relative chart asks about leadership; point and figure filters movement into events. Neither replaces the price chart needed to locate an actual boundary.

## Relative strength and rotation

### Originator-hosted RRG guide — full six-page text read; one chart inspected

The [Thomson Reuters RRG guide hosted by Relative Rotation Graphs](https://relativerotationgraphs.com/wp-content/uploads/2024/10/Relative-Rotation-Graph-Thomson-Reuters-Guide.pdf) is an older, copyright-2013 guide, despite its recent upload path. Its conceptual explanation remains the relevant material here; its platform limits are historical, not verified current product facts. JdK RS-Ratio is horizontal, RS-Momentum vertical, with the center at 100. These are proprietary formulas. Relative leadership can coexist with an absolute loss; smooth clockwise rotation is not guaranteed.

**Actual visual reading:** page 2 uses OMXC20 and seven daily tail observations. CARLb.CO and PNDORA.CO remain in the leading quadrant while their tails descend toward the horizontal boundary. TDC.CO lies in improving, left of the relative-trend boundary. This teaches an important distinction: a green endpoint need not mean improving momentum. Color classifies the current quadrant; trajectory adds information. The PDF prose mistakenly calls blue “LEADING”; the chart itself labels blue “IMPROVING.” Do not propagate the typo.

### Dorsey Wright FAQ — full methodology section read

[Dorsey Wright’s P&F University FAQ](https://oxlive.dorseywright.com/university/faq.html) explicitly separates a bullish absolute-price chart from negative relative strength: a stock can rise while trailing a faster-rising index. It compares a technically elaborate breakout with weak context against a simpler breakout supported by trend and relative strength, preferring the latter. It also describes adjusting box size for perspective rather than automatically discarding the default view. These are methodology preferences, not measured probabilities.

**Original drill: two-axis leader sheet.** Select a fixed historical date and six instruments. Without later data, assign each to one of four cells: price rising/relative line rising; price rising/relative line falling; price falling/relative line rising; price falling/relative line falling. Then ask a separate question: is relative improvement accelerating or fading? Before seeing outcomes, record which instruments deserve closer examination and which have no actionable price location. The learning objective is to avoid buying “least weak” as if it meant “strong uptrend.”

### Community application — main post and first discussion read, not entire thread

[u/kronegker’s r/thetagang post](https://www.reddit.com/r/thetagang/comments/m0c0pv/anticipating_the_rotation_relative_rotation_graphs/) shows a practitioner using sector/ETF rotation to organize options ideas. The thread raises horizon alignment: a rotation sample should relate to the intended trade duration. Its option actions and performance implications are the author’s proposal, not a recommendation here. This is useful experiential evidence of how a chart becomes a watchlist, but the public post does not establish that its custom calculations exactly reproduce licensed JdK indicators.

**Original annotation format:** benchmark; absolute trend; relative trend; relative momentum; observation interval; tail length; relevant support/resistance; next observable event. Do not count the same price-derived information repeatedly as independent evidence.


## Point and figure construction

### Nasdaq Dorsey Wright construction — complete substantive text read

[Point & Figure Basics](https://nasdaqdorseywright.zendesk.com/hc/en-us/articles/12906431410829-Point-Figure-Basics) documents a three-box reversal and an intraday-high/low method. When one daily bar could both extend and reverse a column, the current-column extension takes precedence in its method. Columns are movement events, not equal units of elapsed time. A P&F double-top buy signal means an X column exceeds the preceding X-column top; it is not the bearish two-peak reversal familiar from bar charts. The page separates short-term signals from the bullish support/bearish resistance line used for trend context. Smaller boxes reveal finer movement; larger boxes suppress it.

### Public tool: swaschke/pypnf

Read the [complete README](https://github.com/swaschke/pypnf/blob/main/README.md), package initializer, and first 230 lines of [chart.py](https://github.com/swaschke/pypnf/blob/main/pypnf/chart.py), not the complete implementation. The interface supports close, high/low, low/high, HLC, and OHLC methods and absolute, ATR, classic, and logarithmic scales. It exposes a box matrix, column indices, trends, trendlines, and breakouts. README examples include ASCII charts, useful for manual verification. The full repository was not audited or tested. Readme/core identify GPL licensing; a permissive header remains in the initializer, so anyone redistributing should resolve license scope rather than assume uniformity.

**Original manual exercise:** choose a simple close series and a fixed one-unit box with three-box reversals. Plot it on paper. Label every new column with its first date. Now repeat with two-unit boxes, without changing the price series. Explain which resistance levels survive, which disappear, and why the passage of ten calendar days may add no column. Then compare a close-only version with an explicitly specified high/low version. A disagreement is initially a construction question, not proof one chart reader is wrong.

**What to inspect before trusting a P&F chart:** adjusted versus unadjusted prices; price sampling; box rule; reversal count; handling of same-bar ambiguity; initial state; treatment of the still-forming last bar. Treat ATR-based box construction as a separate audit question: determine which observations set the scale and whether extending the dataset changes earlier geometry. That last check is proposed here, not a finding that this library necessarily repaints.



# 11 Auction profiles Wyckoff and participation

Wyckoff's practical sequence links market position, comparative stock strength, a base's potential, readiness and timing. Springs test below a range and return; upthrusts do the converse. A sign of strength followed by a controlled backup, or a sign of weakness followed by a weak rally, organizes the change in control. [S33]

The phase framework distinguishes stopping the prior move, building a range, testing, directional development and leaving the range. Springs are not mandatory in every accumulation schematic; upthrusts after distribution are not mandatory in every distribution schematic. Compare effort (activity) with result (price progress) while treating labels as hypotheses about the sequence. The Composite Man is a heuristic, not identification of an actual hidden actor. [S34]

**Original practice adaptation:** annotate events first in neutral language: “new low, immediate recovery,” “smaller retest,” “strong advance through range,” “shallow return.” Only then add Wyckoff labels. If the neutral description cannot be supported, the specialized vocabulary does not improve it.


## Volume profile and time price opportunity

### What the displays measure

TradingView documents volume profile as a distribution of volume across price bins, often reconstructed from lower-timeframe bars. Its up/down classification is based on bar direction, not a direct identification of buyer-initiated and seller-initiated trades. POC denotes the greatest-volume bin; a value area encloses a selected portion of volume. Construction range, session selection, bin size and input granularity therefore belong in the chart description. Source read: [Volume Profile: basic concepts](https://www.tradingview.com/support/solutions/43000502040-volume-profile-indicators-basic-concepts/).

TPO is a different display: it records which time blocks visited each price level. Its initial balance, value area, distributions and single prints organize the sequence of an auction. Do not substitute time concentration for volume concentration or assume identical POCs. Source read: [Time Price Opportunity indicator](https://www.tradingview.com/support/solutions/43000713306-time-price-opportunity-tpo-indicator/).

### Original profile-reading worksheet

Suppose yesterday's selected session traded between 98 and 104, with a volume concentration at 101 and a value area from 100 to 102. Today opens at 103. Record three competing paths before the outcome:

- **Acceptance outside old value:** repeated trading remains above 102; pullbacks stop above or around that boundary; new volume accumulates higher. The working interpretation is migration, not an automatic return to yesterday's POC.
- **Rejection outside old value:** the excursion above 102 fails, price returns inside the old value area, and attempts to recover 102 fail. The working interpretation is a failed higher auction. The prior POC becomes a reference, not a promised destination.
- **Unresolved rotation:** price crosses 102 repeatedly without sustained progress. The label is unresolved. A marginal new high does not establish a directional auction by itself.

For each path, draw the price trace and a developing profile. Mark exactly when the evidence first supports the label. If you change the profile's start time, record that change; otherwise a moving reference can make the analysis appear more accurate than it was.

The value of profile work is relational: where prior business occurred, where new business is occurring, and how price behaves between the two. It is not an instruction to fill a chart with every historical node.


## Futures volume and open interest

CME distinguishes trading volume during a period from outstanding contracts represented by open interest. Its educational treatment uses changes in open interest alongside price to assess trend participation. Daily preliminary figures can later differ from official bulletin values. Sources read: [Open interest](https://www.cmegroup.com/education/courses/introduction-to-futures/open-interest) and [Volume and open-interest reports](https://www.cmegroup.com/market-data/volume-open-interest.html).

For chart work, record contract and expiry before reading the series. A transition between futures contracts can change price and volume without being the same event as a breakout in one unchanged contract. Every open contract has both a long and short side; open interest alone does not identify which side is informed. Study whether price progress, volume and participation tell a coherent story, while keeping the observed quantities distinct from the proposed explanation.
## Wyckoff sequence and implementation
## Practical teaching, checked against the method's publisher

Start with the trend before the range. In a prospective accumulation, look for the decline slowing, a selling climax and automatic rally defining the range, then a secondary test with reduced spread and volume. A spring briefly breaches support and returns inside, but it is optional: supply can be tested higher in the range. Afterward, look for strength on wider bars and increased volume, followed by a quieter pullback or last point of support. The transition matters more than matching a perfect diagram. [Wyckoff Analytics tutorial](https://www.wyckoffanalytics.com/wyckoff-method/)

For distribution, watch what follows an upthrust: weakness toward support, then a feeble rally that struggles to progress. This makes the post-test response an essential part of the interpretation rather than shorting every apparent false breakout. [Wyckoff Analytics: reaccumulation versus distribution](https://www.wyckoffanalytics.com/wyckoff-reaccumulation-vs-distribution-how-to-tell-which-one-youre-in/)

## What the archived engines actually implement

[Static event detector](https://github.com/dwj9ddyvf6-hub/Femto-lean/blob/ac989b5e51c8cc6ec96147f7974d2e41c19bdbae/desk/terminal/read/wyckoff.py) and [phase parser](https://github.com/dwj9ddyvf6-hub/Femto-lean/blob/ac989b5e51c8cc6ec96147f7974d2e41c19bdbae/desk/terminal/read/wyckoff_phase.py). Full static reads: Femto-lean `desk/terminal/read/wyckoff.py` and `wyckoff_phase.py`, commit`ac989b5e51c8cc6ec96147f7974d2e41c19bdbae`; plus the archived Wyckoff method note. No code executed. The note itself used indexed/mirrored text; the web check above improves provenance for the teaching claims.

The event detector looks for a bounded, approximately flat range with separated contacts on both sides, then a recent spring/upthrust whose recovery remains intact through the current observation. It separately detects candidate climaxes from range, relative volume, prior advance/decline and close location. Its phase companion traces climax → confirmed opposite swing → quieter secondary test → optional spring/upthrust → strength/weakness → departure from the range. It permits a no-spring path to phase D. Phase facts are context rather than a second vote for the same underlying events.

These are explicit operational choices: 20-session minimum range, six-ATR maximum width, 1.5 ATR fitted-line drift limit, 2.5× relative-volume climax and other numerical thresholds come from this implementation, not the published method. The phase parser requires a qualifying climax and a particular secondary test, so its silence does not establish that all legitimate Wyckoff interpretations are absent. It does not implement an explicit LPS/LPSY detector or point-and-figure cause count; therefore it is not the entire method.

Three details matter when learning from its outputs:

1. The standalone SOS predicate requires a close above the range midpoint and the prior day's high—not necessarily above the range ceiling—while its prose says price rose out of the range. Describe the actual condition, not a stronger breakout claim.
2. 'Buyers absorbing selling' and 'sellers trapped' are interpretations attached to OHLCV behavior, not directly observed participant identities. Keep observation and explanation separate.
3. `EFFORT_VOTE=False` explicitly converts effort-versus-result outputs to nonvoting context. A printed observation is not necessarily an active decision rule.

Practice by drawing the range boundaries and dating each event before assigning a phase. State the event still missing, the next confirmation you would watch, and the price behavior that would invalidate the sequence. Compare several legitimate variants rather than force every range to contain a spring.
## Reconstructing the profile

### Sierra Chart implementation reference — selected substantive sections read

[Sierra’s TPO documentation](https://www.sierrachart.com/index.php?page=doc/StudiesReference/TimePriceOpportunityCharts.html) distinguishes TPO count from volume count, documents POC tie-breaking, value-area expansion, and optional two-level counting. Initial balance is configurable in subperiods; two 30-minute periods produce an hour, not a universal definition for every instrument. It supports both consolidated profiles and each subperiod in its own column, plus splitting/merging. Its comparison checklist stresses matching sessions, row increments, percentages, and data resolution; it recommends tick-by-tick data for volume-profile accuracy. Read sections: elements, display modes, splitting/merging, POC/value-area calculation, and discrepant-value troubleshooting. Not all 1,525 web lines were read.

### Public tool: bfolkens/py-market-profile — full README and core module read

The [core implementation](https://github.com/bfolkens/py-market-profile/blob/master/src/market_profile/__init__.py) rounds each **Close** upward to a row, then groups by that rounded close. In volume mode it sums each record’s volume; in TPO mode it counts closes. This is valuable for reproducible histograms, but feeding daily OHLCV does not reconstruct every intraday price visited or the actual volume traded at each price. The [README](https://github.com/bfolkens/py-market-profile/blob/master/README.rst) demonstrates daily AMZN data and exposes initial balance/open-range functions; those function names do not magically provide missing intraday granularity. Its value-area tie logic also differs from Sierra’s documented simultaneous inclusion of equal adjacent rows. No runtime testing occurred.

### Tim Racette’s practitioner walkthrough — complete article body read

[EminiMind’s guide](https://eminimind.com/the-ultimate-guide-to-market-profile/) walks through a TPO value-area calculation and compares developing value with prior value. It treats range extension, trending profiles, and double distributions as interpretable day structures, while saying the profile is not an entry/exit method by itself. The normal-distribution language and day-type tendencies are the author’s teaching heuristics, not a requirement that every profile be bell-shaped. Its worked method combines two adjacent rows; that is a concrete reason implementations may differ even before data quality enters the discussion.

### Forum worked explanation — complete main post, partial comments

[u/bmac1993’s profile walkthrough](https://www.reddit.com/r/Daytrading/comments/iw7u69/introduction_to_market_profile_volume_profile/) explains a combined time/volume display and a poor-low interpretation. It is useful because it makes the visual reading explicit, rather than merely listing terms. However, it sometimes speaks generically about value and POC while showing both measures. Its expectation that a poor low will be repaired is practitioner interpretation, not a deadline or certainty. The text names 9/20/2020 for the example, but the underlying instrument/session was not independently resolved here. Images linked from this forum were not visually inspected in this pass.

**Original observation exercise:** take two profiles with similar overall outlines. First inspect only their final histograms and write a neutral description. Then reveal subperiod columns. Ask which high came first, whether later trade returned to the same prices, and whether the last portion was building new activity outside old value or merely probing and retreating. The skill is distinguishing two sessions that finish with similar distributions but took different paths.

**Original configuration card:** symbol/contract; timezone; session start/end; overnight included?; bar or tick source; row increment; TPO subperiod; volume/TPO mode; value percentage; tie rule; composite start/end; completed versus developing. Keep the card next to the screenshot so later review compares like with like.


## Two data allocation conventions in your archive
The archived Quant Charts `volume_profile.py` offers two different constructions. With high/low/volume bars it distributes each bar's volume uniformly across covered bins; with price/size arrays it bins the supplied observations at their prices. POC and value-area outputs follow the selected construction and window. The latter input can represent trade prints, but supplying bar closes does not turn them into prints. This distinction helps explain why two visually similar profiles need not give identical levels.

The practical habit is to record window, bin size, data granularity and allocation convention before comparing POC/VAH/VAL. The code's nodes are thresholded local histogram peaks/troughs. They should be read as that algorithm's outputs, not proof of hidden orders.


[Archived Quant Charts profile implementation](https://github.com/dwj9ddyvf6-hub/Silicon/blob/3815c4b223be493704850519656fa7e7b3e3750b/research/rea_teardowns/artifacts/quantcharts/quant-charts-examples-source/quant-charts-examples-main/python/quant_charts/volume_profile.py)


# 12 Wave counts and competing scenarios

Elliott Wave International's impulse teaching specifies a five-wave motive structure with subdivisions, distinguishes rules from guidelines, and excludes overlap of waves 1 and 4 in the ordinary impulse form. Its introductory rules also prohibit wave 2 from retracing beyond wave 1's origin and wave 3 from being the shortest of the three advancing waves. Alternation concerns the differing form of corrections. These are rules for constructing that analytical interpretation, not numerical probabilities. Sources read: [Impulse](https://www.elliottwave.com/waveopedia/impulse/) and [Rules and guidelines](https://www.elliottwave.com/articles/elevate-your-elliott-wave-analysis/).

Original counting exercise: use turning points 100 → 110 → 104 → 124 → 115 → 130. Advancing lengths are 10, 20 and 15; the second correction stays above 110. This is geometrically compatible with the elementary impulse rules, but the internal subdivisions still require inspection. Now change the fourth endpoint from 115 to 108. Do not preserve the ordinary impulse label by moving an earlier pivot after the fact. Reassess the pattern family or retain an alternate count.

For practical study, keep a count sheet with: degree/timeframe, labeled pivots, proposed primary count, alternate count, rule-based boundary, and the next swing that discriminates between counts. Labeling two different paths in advance is useful only when their consequences are explicit. “Either up or down” is not a completed analysis; “above 124 the extension scenario remains coherent, whereas a return below the stated boundary changes the count” is a testable reading.

Use wave work to inspect sequence, proportionality and scenario boundaries. Then translate it back into ordinary chart language so the action does not depend on a label alone: trend, correction depth, important swing, acceptance or rejection, and available room.


## Counting as a repeatable procedure

The recovered Galath study turns wave work into a practical sequence. Start with the clearest larger completed move; mark its swings; enumerate plausible forms; reject counts that violate the applicable rules; compare the remaining counts using guidelines; inspect smaller subdivisions; retain an alternate; and state the boundary that changes the interpretation. The important distinction is between a rule and a preference. Alternation, channel shape, momentum character and ratio fit can rank valid counts; they cannot repair a count that breaks an ordinary impulse rule. [Galath Elliott study](https://github.com/dwj9ddyvf6-hub/quant-research-critical/blob/f74ab2acf945220ba34099951982225e8238d386/galath-research/shadow/terminal/bestsetups/out/elliott_1016/ELLIOTT_STUDY.md)

**Original counting card:** record the larger trend and degree; the ordered anchor dates and prices; proposed form; rules checked; guidelines supporting it; the strongest alternate; the price event that separates the alternatives; and the first time each anchor was actually available. Keep the card short enough to update when one new swing appears.

The study separates several possible trade locations: the end of wave 2 before a proposed wave 3; clearance of the wave-1 high during that third-wave scenario; completion of wave 4 before a proposed fifth; a completed fifth before correction; completion of C before resumption; and a move out of a triangle after E. These are different situations. Their invalidation, overhead obstacles and objective constructions should be written separately instead of being collapsed into a generic bullish count.

**Original comparison drill:** a chart has recovered above the first-wave high but remains below a major daily supply zone. Write one reading about count development and another about available trading room. A count can become more convincing while a new entry becomes less attractive. Then compare an entry near the proposed end of wave 2 with a later confirmation entry. The earlier entry has less confirmation; the later one pays more for it. Neither difference disappears because both belong to the same preferred count.

## Two different implementations in your archive

The Galath specification and Femto source do not define the same wave engine. Both can be studied, but their outputs should retain their own settings and conventions. The study team read both files completely as static sources. [Galath build specification](https://github.com/dwj9ddyvf6-hub/quant-research-critical/blob/f74ab2acf945220ba34099951982225e8238d386/galath-research/shadow/terminal/bestsetups/out/elliott_1016/ELLIOTT_SPEC.md) and [Femto Elliott implementation](https://github.com/dwj9ddyvf6-hub/Femto-lean/blob/f714cc78f50b871e8346e3e725c7a92ebd95521b/core/elliott_wave.py)

| Aspect | Galath proposed layer | Femto source implementation |
|---|---|---|
| Swing construction | Three ATR directional-change sizes | Williams pivots with two bars each side plus separation filters |
| Price coordinates | Log price with mirrored downtrend treatment | Arithmetic price differences |
| Count selection | Guideline fit and agreement across swing sizes | Pattern-family priority then score with stated exceptions |
| State language | Per-degree weak ambiguous stale or valid | Active ambiguous or no-valid with lifecycle events |
| Reading status | Specification read | Implementation read statically |

Multiple swing sizes on daily bars are not three genuinely different timeframes. Log-price distances and arithmetic distances are also not interchangeable on large moves. A comparison must hold the input history, cutoff and intended degree explicit before deciding which count is more persuasive.

A concrete source difference concerns invalidation after a completed impulse. The Galath proposal frames a correction scenario as invalidated beyond the completed fifth-wave high. Femto's completed-impulse parser uses the original impulse origin. These are different questions: whether the expected correction has been disproved, and whether a much broader structural boundary remains intact. A reader should name the question rather than quote an unlabeled invalidation number.

**Original drill:** take one six-pivot sequence and write both a trend-continuation scenario and an imminent-correction scenario. Give each its own invalidation and the observations that matter next. Notice how the same visible history supports different questions without making every answer equally useful. The purpose of an alternate is to identify a discriminating event, not to avoid having a view.

## Convert the count back to chart language

Finish a wave reading with ordinary structure: advancing or declining swings; depth and duration of the correction; the most important reclaimed or lost boundary; nearby support and resistance; and whether the next move is actually underway. This makes the work useful even to a reader who prefers a different wave label. A count-fit score describes conformity to the implementation's template. It should be presented separately from any outcome-frequency estimate and from an entry decision.
## Momentum sequencing and internal subdivision

The recovered [Elliott research report](https://github.com/dwj9ddyvf6-hub/Midna/blob/96e36e379cbe9330441221554d848f270d288800/workspace/research_notes/elliott-wave-phd-deep-dive-20261016-1907/report.md) adds a useful distinction between counting price and using momentum to help locate a stage. Its Advanced GET-style 5-versus-35 oscillator is not identical to Williams' 5-versus-34 midpoint-price Awesome Oscillator. Record inputs, averaging and periods before interpreting the panel.

First mark the candidate move without oscillator labels. Then locate its strongest directional momentum expansion; inspect the subsequent reset while price support remains intact; and compare the next price push with its corresponding momentum peak. A higher price high with weaker oscillator expansion can support a terminal-advance hypothesis, but does not prove wave 5 or complete a price reversal. The strongest oscillator point can change as the move develops, so freeze the observation window.

**Original contrast drill:** draw expansion, a momentum reset above support, and a marginal higher price high with weaker momentum. Write a continuation scenario and a terminal-advance scenario. Name the price event separating them. Repeat with the oscillator hidden and explain exactly what the panel added.

The report's initial engine specification does not recursively validate every lower-degree subdivision. A six-pivot impulse candidate therefore remains an outer-shape candidate, even after passing its price rules. Add three fields to the count sheet: outer pivots that pass, internal legs actually inspected, and unresolved interior structure. An algorithmic pivot scale is not automatically a classical named degree. A genuinely supplied lower-timeframe chart can help inspect subdivisions; a second daily swing threshold cannot pretend to be that chart.

## Diagonal and impulse details worth getting right

Primary-source checks corrected several loose statements in the archived report. An ending diagonal's fifth-wave throw-over crosses the boundary through waves **1 and 3**, not the 2–4 boundary. EWI discusses uncertainty between 3-3-3-3-3 and 5-3-5-3-5 for leading diagonals and recognizes expanding examples. An engine that admits only a contracting 5-3-5-3-5 form has selected a narrower grammar, not settled every valid human interpretation. [EWI diagonals](https://www.elliottwave.com/waveopedia/elliott-wave-pattern-diagonals/)

Within an ordinary impulse, wave 3 is itself an impulse. Ordinary wave-4 non-overlap is not merely a closing-price condition; a source's close-breach state transition may be its execution convention rather than the structural rule. EWI describes a limited futures caveat, not general permission to disregard overlap. [EWI impulse](https://www.elliottwave.com/waveopedia/impulse/)

Keep hard construction rules, comparative guidelines and implementation choices in separate columns. A ratio fit cannot repair an invalid structure, while a deliberately narrower software parser should not be mistaken for the entire discretionary method.


# 13 Four worked decision cases

These four hypothetical numerical cases train the reasoning that a visual chart must support.

## Case A: a promising breakout that is already extended

Daily resistance was marked at 50.0–50.5 from three earlier interactions. A base low is 45.0. The latest daily candle opens 49.8, trades down to 49.4, reaches 54.0 and closes 53.6. Recent ATR is 1.6. Activity is 1.9 times the chosen comparable baseline.

**Read:** the close is beyond the zone; the body retains much of the advance. But the close is 3.1 above the top of the old zone, about 1.94 ATR. A stop beneath a hypothetical 49.4 reaction low would create 4.2 points of risk from that close. If the nearest significant overhead area is 56, the immediate route offers only 2.4 points before an obstacle, approximately 0.57 times that risk before costs.

**Better chart conclusion:** the breakout and the entry are different judgments. Record positive directional evidence, then watch for a compact consolidation or orderly retest. Do not redraw support at 53 merely to manufacture a smaller stop. If price continues without offering acceptable geometry, the reading can remain correct without a trade.

**What to inspect next:** is the return to 50–51 slow and overlapping, or fast and forceful? Does the next advance emerge from a defined higher low? Does participation expand on the rebound? This is how chart reading turns into a conditional plan.

## Case B: triple bottom or descending triangle?

Three lows occur around 80. The rebounds peak at 94, 90 and 86. A fourth approach reaches 80.4. There is no completed close above any recent declining high.

**Read:** the equal lows alone invite a triple-bottom label. The declining rebound peaks supply a competing and more immediately important feature: each recovery has made less progress. Draw both the floor and declining highs. The current state is unresolved pressure around support, not a completed bullish reversal.

**Bullish development:** a firm recovery through the latest meaningful lower high followed by a higher low would change the local sequence. A later break above the larger intervening resistance would strengthen the larger reversal interpretation.

**Bearish development:** a close below the floor with continued trade below it, followed by a failed recovery, would confirm a different resolution. The analyst does not need to know which will happen to identify exactly what matters.

## Case C: failed breakdown and a constructive test

A range has existed between 100 and 110. Price trades to 98.8 but closes 101.2. Two bars later it returns to 100.4, with a smaller range than the 98.8 bar, then closes 102.0. The next bar reaches 104.0. These figures describe a possible failed breakdown and a higher test, not yet a range breakout.

**Read:** the first event is a rejection below the floor. The second shows that the next test did not reach the same low and the market subsequently moved away. That is a stronger sequence than either candle alone. The original 110 ceiling remains relevant. A move through 104 is a local development, not proof that 110 has vanished.

**Training decision:** label the early idea “range recovery,” with a distinct plan from a future “range breakout.” Track whether price can reach the middle and then upper boundary. If the recovery collapses and accepts below 100, retire the earlier spring interpretation rather than moving its definition downward.

## Case D: weekly uptrend, daily correction, hourly turn

The weekly chart has higher swing lows at 120, 135 and 150. The daily chart has corrected from 176 to a previously marked 156–160 area. Hourly peaks during the correction are 168, 164 and 161.5. Price then closes hourly at 162.2, retests 160.5 and moves back above 162.2.

**Read:** weekly structure is still constructive; daily price is at a meaningful area; hourly behavior has begun to repair its own descending sequence. The hourly development gives timing information. It does not guarantee the daily correction has ended, and the weekly 150 structure is not a sensible substitute for a deliberately smaller timing risk without considering position size.

**What makes the case stronger:** the daily close retains the area, the next hourly impulse makes progress, the stock's ratio to its sector stops deteriorating, and the next daily obstacle leaves useful room. **What changes it:** acceptance below the zone, renewed hourly lower lows, or a broad-market deterioration affecting the setup. The lower timeframe refines the larger plan; it does not create one from nothing.

# 14 Practitioner and community lessons

Five public Echo Analysis lessons contribute a coherent method: classify structure, choose meaningful anchors, locate a support area, and wait for a response. The study read their text; the separately inspected email screenshot is identified below. Source-return claims and complete image coverage are outside the stated reading scope.

### Reaction rather than arrival
Echo's [What I wait for before I buy](https://echoanalysis.kit.com/posts/what-i-wait-for-before-i-buy) distinguishes a planned higher-timeframe support area from actual response there. He watches candles, participation on the rebound, momentum divergence, moving-average recovery, and break/retest behavior. His failed TMC example illustrates that a preselected zone without a satisfactory reaction is not automatically a setup. Starter-and-add execution is described with the total intended position's risk in mind. Study takeaway: explicitly label the evidence needed to move from location to entry; do not silently equate touching a Fibonacci line with confirmation.

### Fibonacci anchors and constructions
[How to use Fibonacci](https://echoanalysis.kit.com/posts/how-to-use-fibonacci) separates two-anchor retracements from three-anchor extensions and emphasizes meaningful swings, wick extremes, higher-timeframe context, and scale choice for very large moves. Those are distinct constructions; identical ratio names need not produce identical prices. Study takeaway: every saved chart should include anchor timestamps, anchor prices, scale, and tool type. When revising anchors, retain the previous version and the reason. This creates a traceable learning record rather than making the finished chart look as if its anchors were obvious all along.

### Impulse versus correction
[How to tell a real impulse from a fake one](https://echoanalysis.kit.com/posts/how-to-tell-a-real-impulse-from-a-fake-one) teaches wave degree, momentum character, non-overlapping progression, volume behavior, extensions, and truncation. It contrasts forceful orderly progression with fast but overlapping corrective movement. Echo's preferred sequence is to let a prospective first impulse develop, observe a corrective retracement, then assess the reaction at support rather than assume every bounce is wave 1. Study takeaway: annotate the larger degree separately from its subdivisions, and keep a corrective alternative until the relevant structural conditions resolve it. Elliott impulse rules require care with exceptions such as diagonal structures; a simplified newsletter checklist is not the entire theory.

### Corrective families
[The three corrections](https://echoanalysis.kit.com/posts/the-three-corrections-and-how-to-tell-them-apart) distinguishes zigzags, flats, and triangles using subdivisions and the relationship of successive legs. It introduces combinations and alternation, and explains a breakout/retest approach after a triangle. Study takeaway: record competing structures by the features that would distinguish them, not just a preferred letter count. Triangle location and thrust targets are the author's framework, not certainty that every narrowing range must resolve in one direction. The useful discipline is recognizing that a vigorous countertrend leg can coexist with an unfinished correction.

### Confluence with explicit failure
[How I find support](https://echoanalysis.kit.com/posts/how-i-find-support) combines structural levels, moving averages, channels, retracements, momentum divergence, and volume behavior. The operational point is to wait for price response and maintain an invalidation for the proposed structure. Study takeaway: organize confluence by evidence category. Three price-derived indicators are not necessarily three independent facts. A helpful chart annotation separates price location, momentum, participation, and actual reaction rather than counting every line as an additional vote. The source's sizing choices and numerical success examples are practitioner statements, not a universal position-sizing prescription.


## Additional Echo newsletter case

The newsletter study fully read six substantive lessons dated September 7 to October 25, 2026. Five overlap the public articles above and are counted once as intellectual sources. The additional September 20 WYFI lesson asks whether an apparent bull flag is really an unfinished correction. [Newsletter archive and source note](https://echoanalysis.kit.com/)

Echo compares the pause with its preceding impulse: shallow retracement under his proposed wave count, heavier selling than buying activity, an incomplete corrective sequence, and a 15-day pause after an 87-day advance. He interprets the rebound into a 0.618 retracement as a possible B wave and retains alternative paths rather than treating the silhouette as sufficient continuation evidence.

**Original application:** compare two charts with similarly sloping flags. For each, write the prior impulse, retracement depth and duration, volume balance, number of corrective legs, and what would establish a fresh impulse. Then state which observation would make the continuation interpretation more convincing. The useful skill is recognizing when the same outline belongs to a different larger sequence.

One chart-bearing WYFI screenshot embedded in the email was visually inspected; it contains the author's wave-B warning and chart annotations. It has no visible original post identifier or timestamp, so it is not treated as independent proof of an advance call. The remaining editorial images were not inspected after access failures. This review does not claim coverage of the author's lifetime archive. No public permalink was verified for the WYFI issue; the archive link is navigation only.

## Independent practitioner studies

### Trader Stewie: higher-timeframe setup, lower-timeframe execution
[How to Trade the Pullback](https://www.artoftrading.net/post/how-to-trade-the-pullback) walks through BBAI: prior momentum, declining-volume retracement, a daily 20 EMA reference, and a lower-timeframe opening-low/red-to-green sequence. The article explicitly separates the daily location from intraday execution and discusses the possibility of a day trade becoming a swing only after reassessment. This is a useful example of resolving timeframe roles instead of choosing whichever timeframe supports an existing opinion. The published trade narrative was read; execution records were not audited.

### Failed breaks are sequences
[The Shakeout Before the Breakout](https://www.artoftrading.net/post/the-shakeout-before-the-breakout) describes temporary excursions beyond levels followed by re-entry, with retests, multi-timeframe alignment, divergence, and rejection candles as context. It includes NBIS, TSLA, and other historical illustrations. Observable teaching point: distinguish crossing, acceptance, rejection, and recovery. The article's attribution to manipulation or intentional stop harvesting is a possible explanation, not something OHLC candles identify by themselves. We can learn the recovery pattern without claiming to know who caused it.

### Reversal setup versus continuation setup
[Trading a Reversal: SOXL Review](https://www.artoftrading.net/post/trading-a-reversal-soxl-review) describes a consecutive-down-day context, a hammer followed by an inside day, an explicit stop, nearby rebound targets, and event-aware management. Its educational value is matching the expected holding period and target to a bounce thesis instead of assuming an immediate return to old highs. 

### Focused refinement
Stockbee's [Do deep reflection](https://stockbee.blogspot.com/2022/11/do-deep-reflection.html) advocates studying a defined setup and timeframe deeply, including alternatives in entry timing, stop placement, exit, liquidity, and sizing. The transferable practice is structured counterfactual review: what changed when one decision changed? Do not change every variable simultaneously, because then the source of improvement becomes unknowable. The author's learning-time estimates are not a promise.

Brian Shannon's [Anchored VWAP explainer](https://alphatrends.net/anchored-vwap/) supplies an additional event-based reference: volume-weighted price since an identified anchor, viewed with price location and the line's slope. For study, preserve the event and anchor rationale. An arbitrary anchor discovered after the outcome is a different exercise from a preselected earnings, breakout, or major reversal anchor.


## Public forum lessons

The [RealDayTrading wiki](https://www.reddit.com/r/RealDayTrading/wiki/index/) was used as an index, not read in its entirety. Its profitability and member-experience assertions are not treated as independently verified statistics.

1. OptionStalker's [How to read price action](https://www.reddit.com/r/RealDayTrading/comments/vjnwe4/how_to_read_price_action_lesson/) compares daily context with 15-minute and 5-minute detail. Candle overlap, direction, range, and the speed/depth of pullbacks inform scenario maps. Useful exercise: describe the same move in these observable terms before naming a pattern. The author's numerical scenario odds are not imported as calibrated probabilities.
2. HSeldon 2020's [How to read the market—an exercise](https://www.reddit.com/r/RealDayTrading/comments/sghaxi/how_to_read_the_market_an_exercise/) recommends writing the market narrative and rationale before the outcome, then reviewing missed evidence and directional bias. This is a practical antidote to merely recognizing attractive completed charts. Claims about institutional motives remain interpretations unless separately evidenced.
3. OptionStalker's [Is this breakout real or fake?](https://www.reddit.com/r/RealDayTrading/comments/yxs2vu/how_to_tell_if_this_breakout_is_real_or_fake/) focuses on what follows the initial expansion: follow-through, volume, and whether dips are bought promptly. Useful exercise: define acceptance after a break in advance, rather than retrospectively calling winners real and losers fake.
4. [Trading compression breakouts](https://www.reddit.com/r/RealDayTrading/comments/tpp6tt/trading_compression_breakouts/) links narrowing price action with relative performance versus the market and nearby boundaries. The alert is an invitation to examine the chart, not an automatic trade. Study compression with its preceding impulse and market backdrop still visible.
5. [A beginner chart-reading discussion](https://www.reddit.com/r/technicalanalysis/comments/wnntnz/looking_for_a_good_beginners_guide_on_how_to_read/) provides book-discovery leads and the suggestion of hand-drawing bars. Treat community reading suggestions as leads, not a consensus credential or proof of the comments' indicator claims.
6. [EliteTrader's Spydertrader/Hershey journal, page 27](https://www.elitetrader.com/et/threads/spydertraders-jack-hershey-futures-trading-journal.83604/page-27) contains a useful practical exchange about bar identification and changing provisional channel annotations as later points become known. Only this selected page of the much longer historical thread was inspected. Study lesson: agree on bar start/end timestamps and distinguish proposed from confirmed anchors. Attached charts were not inspected.


## Advanced discretionary reading

These are selected lawful excerpts and firsthand teaching, not a claim to have read every author's books or watched entire paid courses. They complement the original handbook rather than establish universal success rates.

### Adam Grimes: structure, action and the quality of the pause

The publisher's authorized *The Art and Science of Technical Analysis* excerpt distinguishes the arrangement of pivots and levels from the evolving behavior that produces them. Selected passages also discuss consistent chart conventions, swing relationships and lower-timeframe detail. This suggests a useful two-column practice: record the stable map separately from the latest evidence that confirms or challenges it. [S35]

Grimes's author-hosted flag article treats the preceding directional impulse and subsequent pause as a linked sequence. It distinguishes anticipatory entry during consolidation from confirmation entry as the pause breaks. The nearest prior extreme can matter before more ambitious projected targets. A flag's quality is therefore not established by drawing two parallel lines alone. [S36]

In his firsthand interview, Grimes explains failure tests around readily recognizable levels, the importance of prompt movement after the failed probe, and the danger of forcing countertrend interpretations everywhere. He gives a nested example: a failure test at the bottom of a bullish complex pullback. His timeframe discussion ties the relevance of a level to the timeframe actually being traded. [S37]

### Al Brooks: a vocabulary for evolving bars

Brooks's glossary makes context central and distinguishes breakout, breakout pullback, breakout test and follow-through. His double-bottom terminology can describe a brief continuation structure inside a bull flag; it need not mean a major classical reversal. His “failed failure” describes an apparent breakout failure that reverses again into continuation. These distinctions are useful, but his terminology and numerical assertions should not be silently treated as interchangeable with ChartSchool's definitions or as verified probabilities. [S38]

### Original synthesis: three layers of a discretionary reading

**Layer 1 — the map.** Mark the prevailing swing sequence and meaningful price zones before interpreting the newest candle. Example: the prior impulse is 200 to 220, the latest higher low is 210, and resistance above is 228–230.

**Layer 2 — the contest.** Describe how the two sides interact inside that map. Price declines 220 to 214 in three bars, rebounds to 218 in two, then declines to 213.5 in five smaller overlapping bars. This is not automatically bearish because it contains a lower low. Compared with the first decline, the second travels less distance despite more time. That is a measurable observation, not proof of exhausted supply.

**Layer 3 — resolution.** Require behavior that distinguishes the alternatives. A move through 218 with sustained closes above the internal pivot supports resumption. A fast decline through 210 with weak rebound changes the higher-low map. Repeated oscillation between 213.5 and 218 without progress leaves a balance, not a compulsory entry.

The same sequence can be called a complex pullback, a small trading range, or an unfinished double bottom. The useful agreement is the set of pivots and what their break would mean. Do not force the labels to agree before making a factual description.

### Original exercise: the failed failure without hindsight

A marked range is 40–44. Price closes 44.6, next closes 43.7, then 44.8. At each close write only what is known:

1. **44.6:** initial breakout; no multi-bar acceptance yet.
2. **43.7:** return into the range; bullish continuation now needs renewed evidence. This is not permission to assert an inevitable collapse.
3. **44.8:** re-expansion above the boundary; the first rejection has itself failed so far. The next test is whether price can stay outside and progress, not whether the prior bearish label was embarrassing.

Compare two continuations: (a) 45.2 then a controlled test of 44.3, versus (b) 44.0 then 42.8. Update the state table without redrawing historical levels. Record the transaction costs of acting on every reversal versus waiting for the preselected confirmation rule. This is an exercise in state transitions, not an instruction to reverse positions at every close.

### Original exercise: anticipation and confirmation are different trades

Use the 200–220 impulse and 213.5–218 pause above. A hypothetical anticipatory long at 214.5 with structural invalidation below 210 offers a different risk distribution than a confirmation entry at 218.5 using the same invalidation. The first may never receive a valid trigger; the second pays more for evidence and may be too close to the 220 obstacle. A tighter stop below a timing-chart pivot is not equivalent to the original structural stop: it can exit while the larger setup remains intact. Record which hypothesis each stop actually tests. Distinguish an invalidated entry from an invalidated market thesis.

### Original practice: make intuition inspectable

For every discretionary adjective, supply a measurement or comparison:

- “Strong” → distance per bar, proportion of closes near extremes, limited overlap, or progress beyond a prior pivot.
- “Orderly” → narrower ranges, modest retracement, limited adverse gaps and no destruction of the controlling swing.
- “Absorbing” → repeated tests with less adverse progress; treat absorption as an inference, since candles do not reveal all resting liquidity.
- “Exhausted” → extended movement followed by failed continuation and reversal evidence; extension alone is not exhaustion.
- “Clean” → few competing pivots between entry and obstacle, not simply an attractive screenshot.

Build an atlas with twenty accepted examples and twenty near-misses of one setup. Preserve both the before chart and later outcome. Have a second reader label it without knowing the result. Resolve disagreements by tightening observable definitions rather than making the chart more persuasive. This converts visual familiarity into a reproducible skill while retaining room for expert contextual judgment.

# 15 Echo chart sequences and direct visual lessons

## How the evidence was combined

Echo's retained posts, replies, newsletters and annotated charts teach a staged process: find a meaningful location, inspect the response, distinguish an early position from stronger confirmation, and revise the plan when its boundary fails. This chapter combines the newly reviewed archive text with the team's **15 direct original-resolution image readings**. The newsletter lessons are discussed separately; overlapping posts are not additional independent examples. The images are not reproduced here. Their observations are attributed to the research team's exposed retrospective readings, not to this book's masked exercise.

The [retained text archive](https://github.com/dwj9ddyvf6-hub/ClaudeDesk/blob/5fad5264d9b56dee7ec9c7d13164d55f5072d06f/wt_sec/docs/research/2026-10-18-terminal/echo-harvest/posts_all.json.gz) supplied the text. Its source-status limits and exact review counts appear in the coverage chapter. Direct X links identify the archived posts; they do not mean the live originals were independently authenticated in this study.

## AAOI from location to stronger confirmation

The [September 9 plan](https://x.com/EchoAnalysis/status/2097785111672459683) asks for a 50-day-average recovery and a quieter support retest. The matched image is labeled **2D**, while the text discusses daily averages. Its latest price is beneath the yellow curve and above a rising blue curve. No volume panel is displayed. Thus the picture supports an unresolved overhead barrier, but does not establish the requested low-volume retest. Candle aggregation and the reference average's interval are separate fields.

The [September 29 explanation](https://x.com/EchoAnalysis/status/2105040419365265460) describes an initial position near the weekly-average/retracement area, then a potential add after the daily average becomes support. The daily image shows a narrower cluster above the 94.38 reference, beneath the yellow 111.54 average. Its projected 175.03 B-wave objective belongs to a future corrective upswing, not a price already achieved. The local floor attempt and confirmed breakout are different stages.

By [October 4](https://x.com/EchoAnalysis/status/2106852358336438442), the image's last strong green candle is beyond the descending line, with price 115.59 above the yellow 111.15 label. That is visible progress. It still does not show a subsequent successful retest. The projected 175.03 line has not changed, although the percentage bracket has: a changed starting point changes the displayed upside distance.

**Practice:** annotate three rows—location, initial response, stronger confirmation. In each row write what is actually visible, what the author asserts, and what remains to happen. Keep the starter and add conditions separate. A reported buy is not a general sizing formula.

## KRMN preserve the failed thesis and the new one

The [August 29 hourly chart](https://x.com/EchoAnalysis/status/2093776196173508881) shows a decline from roughly 63, price 45.59 beneath the yellow curve, and a red invalidation at 43.80. Circled older lows explain why support matters; they do not reverse the current lower path. The text invokes divergence and reduced selling participation, but neither supporting panel is visible.

The [August 31 update](https://x.com/EchoAnalysis/status/2094523620945248629) changes to a two-day view. Price 41.46 is below the earlier defended area; new lower references appear near 35.67 and 34.49. The author reports an exit and loss. The observable breakdown and reported execution are separate evidence types. The earlier [nested plan](https://x.com/EchoAnalysis/status/2091254580738679065) already distinguished a deeper retracement, a confirmed bottom and a lower-low failure branch.

The [September 19 chart](https://x.com/EchoAnalysis/status/2101446739131797757) then shows a short cluster around 35.75 near the new area, with the average still far overhead. Its starter proposal and below-34 failure reference describe a **new setup**. They do not retroactively repair the August thesis.

**Practice:** save two separate cards. Card one ends at its declared failure; card two begins with the new location and fresh evidence. Record why a divergence kept the old setup under observation but did not overrule its invalidation. Never improve a historical decision by substituting a later boundary.

## Nasdaq make the alternate operational

The [October 3 post](https://x.com/EchoAnalysis/status/2106414472994984085) is tagged QQQ, but the inspected chart is **NQ1! Nasdaq-100 E-mini futures**, daily, with an NQZ2026 quote. The depicted price has broken a declining line and recovered the 30,810.50 area. These are futures points, not QQQ dollars. A nearby extension and alternative wave labels are scenario references.

The [October 10 update](https://x.com/EchoAnalysis/status/2108951188159037799) retains a primary continuation interpretation above the 50-day average and favors a larger correction if that reference fails. The image separates the nearby 30,810.50 shelf from the lower yellow average at 29,926.86. Losing the first does not automatically satisfy the second condition.

**Practice:** write the exact observation that promotes the alternate. Then state which interpretation is retired and which targets become relevant. Two arrows become useful analysis only when their branching conditions and instrument identity are clear.

## UBER separate the first line break from the next test

The [October 8](https://x.com/EchoAnalysis/status/2108324558847529249) daily image shows price above a declining trendline but still below the yellow average: 70.25 against 73.06. By [October 10](https://x.com/EchoAnalysis/status/2108996486369579087), price is 71.51 and the average 73.08. The line break has progressed, while the average test remains unresolved. A fixed red 64.23 invalidation and 94.90 projection organize the picture.

The text's claim of relative resilience needs a market comparison; this single-symbol image cannot establish it. Its longer-term target is also a different horizon from the displayed nearer objective.

**Practice:** draw one row for trendline confirmation and another for moving-average support conversion. Give each its own required response and information time. Recompute distance from the contemplated entry, not from the attractive low where a projected return bracket begins.

## ASML and BE distinguish trend strength from entry quality

The [ASML weekly example](https://x.com/EchoAnalysis/status/2007859700763869567) shows a large advance from a labeled C/(4) low toward the top of its visible range. Its projected references lie above the right edge. This supports a mature-advance interpretation; the author's divergence claim requires an oscillator that is absent from the image. Planning a trim at a future reaction is different from observing that reaction now.

BE makes the owner-versus-new-buyer distinction across three snapshots. [September 17](https://x.com/EchoAnalysis/status/2100679936466096576) shows a local line break inside a larger recovery, with nearby overhead references. [October 4](https://x.com/EchoAnalysis/status/2106855629470203939) shows further progress, but less remaining room to the mapped destination. [October 11](https://x.com/EchoAnalysis/status/2109392344810209761) shows an upward-sloping overlapping channel near 284.98, above a yellow average at 246.48. The author's bear-flag interpretation requires a break of the flag and loss of that average; the image does not show both completed.

**Practice:** write a neutral geometry description before reading the author's label. Then make two different plans: how an existing owner interprets the next obstacle, and what a non-owner needs before initiating. A bullish direction can coexist with waiting for a better location. A rising channel is observable geometry; its bearish interpretation and confirming break are additional layers.

## NVAX map a staged exit rather than one distant target

The [October 6 weekly chart](https://x.com/EchoAnalysis/status/2107441239020757323) shows price beyond a long descending boundary, with two nearer profit-taking references around 15.2 and 17.9. The author proposes successive reductions and a residual position. The image does not reveal universal reduction fractions or a complete residual-position stop rule.

**Practice:** label first obstacle, second obstacle and remaining-position review separately. Keep projected distances distinct from reported realized gains. A weekly candle may still be developing; do not silently treat an intraweek snapshot as a completed weekly confirmation.

## What the replies add to the chart pictures

**Define support conversion as behavior.** The [September 22 reply](https://x.com/EchoAnalysis/status/2102307135203807395) describes crossing the average, returning to it and advancing again. Another [support-confirmation reply](https://x.com/EchoAnalysis/status/2097058596311663075) combines a quieter approach with stronger rebound participation, higher highs and short-average recovery. A [later clarification](https://x.com/EchoAnalysis/status/2107735491332145458) emphasizes test-and-bounce behavior rather than a fixed waiting period. Do not substitute an invented three-day rule.

**Know what the box means.** A [buy-zone explanation](https://x.com/EchoAnalysis/status/2105678273137234184) distinguishes an acceptable average-entry area from the particular ratio at which the author expects a turn. [RCAT](https://x.com/EchoAnalysis/status/2094108385020883021) can reach such a box while a corrective leg remains unfinished. The price coordinate alone is not the completed sequence.

**Record indicator identity and corrections.** A [settings reply](https://x.com/EchoAnalysis/status/2097790579111313874) names SMA50 and SMA200 on daily, weekly and monthly horizons. [AAOI's correction](https://x.com/EchoAnalysis/status/2102864033770844483) identifies a weekly rather than daily reference. Other posts discuss EMAs, so preserve type, period, timeframe and identification source per chart rather than impose one universal legend.

**Keep nested structure explicit.** A [five-wave clarification](https://x.com/EchoAnalysis/status/2097996094059741241) explains that a local advancing C inside B can itself contain five waves. A [later reply](https://x.com/EchoAnalysis/status/2109437642966286754) warns that an apparent completed five can be part of an extended third. [SNDK](https://x.com/EchoAnalysis/status/2101774649671528591) uses the same ratio for different directional swings. Record the containing wave and each measurement's two anchors.

**Keep alternatives genuinely different.** [XPEV](https://x.com/EchoAnalysis/status/2092009556226232487) distinguishes an initial small position from a later corrective-leg add. [SIVE](https://x.com/EchoAnalysis/status/2097105634311450728) offers either deeper support or a fresh initial advance followed by its correction. A [missed XGN entry](https://x.com/EchoAnalysis/status/2104258516735217863) motivates a later setup rather than a fictional earlier fill. These are different routes to information and risk location, not inconsistent forecasts.

**Preserve the mandate.** [PNG](https://x.com/EchoAnalysis/status/2105398528537407706) and [SIDU](https://x.com/EchoAnalysis/status/2108332108988973433) demonstrate holding preferences different from KRMN's stop. [RR](https://x.com/EchoAnalysis/status/2075958793070919835) distinguishes a later tactical idea from an invalidated investment interpretation. Do not combine the tight-risk benefit of one example with the patience of another only after seeing the outcome. State the intended horizon first.

**An attractive chart is not a transaction.** [VELO](https://x.com/EchoAnalysis/status/2091941015359770841) explicitly considers existing sector exposure. [Buy-marker clarification](https://x.com/EchoAnalysis/status/2097607458868940908) separates favorable ideas from author-reported ownership. Analysis, planned entry, reported execution and allocation constraint belong in different fields.

## A practical reconstruction worksheet

For one dated sequence, complete: chart identity; larger context; local structure; measurement anchors; watch zone; actual response; starter condition; add condition; execution failure; larger thesis failure; exit or partial-exit map; and revision history. Label evidence as pixels, retained author text, previous researcher's interpretation or your own inference.

Then hide the next update. Write which single observation would most change the interpretation. Reveal it and record only the new information. Score faithful observation and disciplined updating separately from subsequent direction. This makes the archived material a method lesson rather than a collection of impressive projections.


# 16 Qullamaggie and Raschke setup sequences

## Qullamaggie setup lifecycle
[Archived Qullamaggie superthesis with third pass corrections](https://github.com/dwj9ddyvf6-hub/quant-research-critical/blob/f74ab2acf945220ba34099951982225e8238d386/quallamaggie_superthesis_v3.md). Full static read: `quallamaggie_superthesis_v3.md`, including its third-pass addendum. This pass read the archived reconstruction, not every underlying interview or video. Source metadata and byte reconciliation are in `full_reads_ledger.json`. Its primary-source pointers are useful for verification; claims about personal performance remain source-qualified, not independently audited here.

## Three distinct setups

**Leader breakout:** first find exceptional prior strength, then study the pause. The useful visual sequence is impulse → orderly base → tightening range/higher lows → break of the relevant pivot or opening range. Short averages help describe the pullback; they do not replace inspecting the base. A wide, loose series of bars is not equivalent to a tight base merely because both sit above an average. Determine where the structure fails before deciding whether the entry has sensible risk.

**Episodic pivot:** first understand the information change. A gap is not itself the whole setup. Combine a meaningful catalyst, unusually strong early volume, prior quietness or neglect, and price strength after the opening range. A stock can look like an EP in retrospect because it later rose; that does not establish that the catalyst and volume were knowable at the proposed entry time. In practice, write down exactly what new information became public and when, then inspect how price accepts or rejects the repricing.

**Parabolic short:** distinguish extension from exhaustion. A vertical run identifies a candidate for attention, not an automatic short. The studied method waits for observable weakness: an opening-range-low break, a red candle, or a failed VWAP reclaim, depending on the specified version. Risk is qualitatively different from the long setups because squeezes, halts, gaps and borrow availability can dominate the chart. Study the geometry without treating an attractive screenshot as executable evidence.

## Why the exit belongs to the setup

The reconstructed long-side process protects an initial chart-defined stop, takes a partial after several successful sessions, and attempts to retain a runner with a 10- or 20-day average trail. The purpose is to combine repeated manageable failures with occasional long continuations. A small hit rate is neither a success nor a failure by itself: the sizes of gains, losses, costs and missed exceptional winners jointly matter. A fixed quick target may materially change the intended method by removing its long right tail.

## What to practice visually

Create paired charts of constructive and noisy bases that share similar numerical width. Mark prior impulse, compression, higher lows, close overlap, volume change, relative strength against a contemporaneous index, and the actual invalidation. Then hide future bars and write a decision. For EPs, add a timestamped catalyst card and the opening-volume curve. For parabolic candidates, distinguish the last strong continuation from the first actual failure. Preserve both rejected and selected cases: winner-first study is useful for learning the pattern vocabulary, while the full candidate set teaches discrimination.

## Preserve the difference between public teaching and engineering choices

The thesis separates direct rules from its own thresholds. A top 2% rank union, ten-session base, 28% maximum base width, 70% moving-average support,0.5×ADV after 20 minutes, QQQ regime proxy, and 1.5 ATR trail-switch threshold are prototype choices—not a recovered private algorithm. Public accounts also differ by date about typical base duration, risk, opening-range choices and management. Keep those as versions rather than manufacture one timeless exact formula.

The third-pass addendum corrects the main manuscript's fill assumption. It reports a first-person rejection of buy-stop orders and therefore separates an observed breakout from an assumed standing order filled exactly at the line. Its next-bar-open model is a simulation choice, not proof of the trader's precise execution. Likewise, 20-minute volume cannot justify a five-minute entry retroactively. A daily closing moving-average breach cannot be used to claim an earlier intraday exit.

A practical chart-reading lesson follows: **setup, trigger, invalidation, execution and management are separate steps**. Mastering one recognizable shape is not the same as learning the whole method.

## Archived source status to retain

The earlier body mentions 11 tests; the later third-pass addendum reports 27 after further corrections. The addendum also corrects an earlier Finnish-program attribution: the located program analyzes the strategy rather than being an interview with Kullamägi. These are internal version updates, not independently rerun results in this pass. Empirical replication remains blocked in the archived package by missing point-in-time data, especially event timing and historical short mechanics; no new strategy test was run here.
## Raschke next swing reading
Two archived teaching syntheses were read in full and hash-verified: [official method reconstruction](https://github.com/dwj9ddyvf6-hub/Silicon/blob/3815c4b223be493704850519656fa7e7b3e3750b/research/linda_raschke/research/official_methods.md) and [CMT notes](https://github.com/dwj9ddyvf6-hub/Silicon/blob/3815c4b223be493704850519656fa7e7b3e3750b/research/linda_raschke/research/cmt2019_methods_notes.md). Their prior PDF/slide inspections are not new inspections in this study. Two author-bylined web articles were independently opened and read as text; their embedded charts were not visually inspected.

## Practical lessons

**Choose the market mode first.** A compression breakout, established-trend pullback and failed breakout are different opportunities. They can use similar indicators while needing different triggers and management. Do not average their instructions into one generic strategy.

**Momentum can confirm expansion rather than signal a fade.** Raschke's breakout lesson begins with higher-timeframe contraction. A lower chart then provides a simultaneous price/momentum high. Her oscillator is SMA3 minus SMA10, not default exponential MACD. The example stages entry and uses the price associated with the preceding oscillator swing low for protection. This is a conditional recipe, not a reason to buy every high oscillator reading. [Author's article](https://www.traderslog.com/buying-new-momentum-highs)

**Read responses at visible reference points.** Mark prior-session high, low and close plus today's open. Observe direction, speed, distance and response: acceleration through, rejection, acceptance, or failure to follow through. A range edge may be an objective in congestion but a waypoint in a trend. A failed downside excursion that re-enters and breaks upward is information, not merely an imperfect original pattern. This is price-response reading, not a disclosed order-book imbalance formula. [Author's tape-reading lesson](https://www.traderslog.com/tape-reading)

**Preserve sequence and version.** The archive describes Grail as strong/rising ADX first, then the initial EMA20 retracement; the cited 1997 trigger uses the previous bar's high, not automatically the touch bar's high. First Cross is not silently interchangeable with Anti. Two-period price difference is not percentage ROC. A failed pullback does not automatically mandate reversing. These details remain archival source findings until the original publications receive a new audit.

Practice three separate chart exercises: identify contraction before expansion; distinguish initial qualified pullbacks from late repeated touches; and document the expected response at a level before revealing subsequent bars. Record what would change the reading. None requires inventing exact probabilities from a selected example.
## A specific momentum and first pullback example

### Raschke — all four pages of interview text read

The [March 2004 Active Trader interview hosted on Linda Raschke’s site](https://lindaraschke.net/wp-content/uploads/2026/03/raschke_pt2_0304.pdf) gives an S&P example: consolidation breakout, new momentum, ADX above 30 on a specified timeframe, then its first retracement to the 20-period EMA. It follows the sequence from 30-minute to hourly and 120-minute opportunities; each timeframe must independently meet the condition. Her 3–10 oscillator uses simple averages, with a 16-period simple average of their difference—not an unmodified standard exponential MACD. She also distinguishes forecasting a price being **traded through** from forecasting the subsequent **close**. Reported percentages are historical source claims, not recalculated contemporary odds. Text and figure captions were read; the chart bitmap was not successfully inspected through the available screenshot response.

**Original sequence card:** expansion event → momentum evidence → first pullback → response at the reference → opportunity expires. Record all five before choosing a trade label. Distinguish a pullback in an established move from repeated tests after that move has lost urgency. Do not silently replace “first pullback” with “every touch of the moving average.”

### TEAM visual comparison and event context

[His EP mastery article](https://qullamaggie.com/how-to-master-a-setup-episodic-pivots/) describes building a large historical screenshot/news database, then recognizing variants. His definition emphasizes a substantial gap and exceptional early volume, often after prolonged quiet trading, followed by an opening-range trigger with a day-low stop. These are his preferences; the article itself admits stopped-out trades. Its aspirational financial claims are not adopted.

**Actual chart reading:** [TEAM before](https://qullamaggie.com/wp-content/uploads/2021/11/team1-1024x969.png) shows prolonged overlap, a later shelf near the old high, then a conspicuous upside gap with expanded volume. [TEAM after](https://qullamaggie.com/wp-content/uploads/2021/11/team2-1024x964.png) reveals a sustained advance and later earnings-gap area. The daily image does not establish the intraday entry, stop sequence, fills, or whether a particular trader survived the pullbacks. “Before” here already contains the event bar: it is not a fully pre-event prediction test.

**Original case-library schema:** event timestamp; what was known then; higher-timeframe structure; pre-event compression/extension; relative volume measured at a stated elapsed time; first eligible decision; invalidation; no-trade reason; subsequent path; lesson. Keep a separate page for visually similar non-examples. The point is to build discriminating perception rather than accumulate attractive screenshots.



# 17 Saty conditional maps and chart tool vocabulary

## 1. Learn to draw a conditional map

The practical contribution of the Saty material is a map with **several relevant clocks and alternative routes**. Price may be approaching a daily ATR reference while the displayed candles are ten-minute and the ribbon represents an hourly or weekly trend. These are three different objects. State each before interpreting the chart.

The archived [official-rules reconstruction](https://github.com/dwj9ddyvf6-hub/Silicon/blob/3815c4b223be493704850519656fa7e7b3e3750b/research/saty_mahajan/research/official_rules.md) explains the ATR ladder as prior reference close plus or minus a multiplier of prior ATR. It distinguishes the original ribbon from Pro, and describes the Phase Oscillator as smoothed, ATR-normalized displacement from EMA21. Volume Stack divides volume according to the close's position within the candle; it is not an observed order book. The useful learning distinction is between a price map, trend state, displacement state and close-location display. Treat them as separate descriptions rather than four interchangeable votes.

The [proposed operating playbook](https://github.com/dwj9ddyvf6-hub/Silicon/blob/3815c4b223be493704850519656fa7e7b3e3750b/research/saty_mahajan/research/operating_playbook.md) organizes compression, transition, continuation and mean reversion as different setup families. It requires an arming event and selected confirmation, then identifies the nearest obstacle and a lifecycle. This is the archive author's proposed mechanical interpretation, not a universal personal rulebook from Saty.

## 2. What the retained visual casebooks teach

The [YouTube casebook](https://github.com/dwj9ddyvf6-hub/Silicon/blob/3815c4b223be493704850519656fa7e7b3e3750b/research/saty_mahajan/youtube/CHART_CASEBOOK.md) contains fourteen detailed historical chart readings. Its strongest transferable distinctions are: divergence inside an intact trend versus actual trend failure; weekly support overlaid on daily candles; local recovery below higher-timeframe supply; and a prospective pattern whose neckline has not broken. The [Community synthesis](https://github.com/dwj9ddyvf6-hub/Silicon/blob/3815c4b223be493704850519656fa7e7b3e3750b/research/saty_mahajan/youtube/COMMUNITY_SYNTHESIS.md) describes 200 retained posts and the recurring preparation sequence: prior close, overnight range, ATR levels, ribbon, structural zones, then conditional paths. Option strikes named beside a chart are not underlying entry prices.

The [expanded X visual survey](https://github.com/dwj9ddyvf6-hub/Silicon/blob/3815c4b223be493704850519656fa7e7b3e3750b/research/saty_mahajan/posts/x_visual_survey.md) shows the method evolving across versions and emphasizes structure alongside indicators. Its older AMZN/FB examples describe a sequence of ribbon change, revisit, entry, partials and later exit rather than an immediate trade on a crossover. The [additional X notes](https://github.com/dwj9ddyvf6-hub/Silicon/blob/3815c4b223be493704850519656fa7e7b3e3750b/research/saty_mahajan/posts/x_additional_visual_notes.md) add an important management-reading distinction: a stopped runner after earlier profit-taking is different from a full initial-position stop. A nearby higher-timeframe barrier can interrupt an otherwise plausible path toward a more distant target.

The [Bluesky survey](https://github.com/dwj9ddyvf6-hub/Silicon/blob/3815c4b223be493704850519656fa7e7b3e3750b/research/saty_mahajan/posts/bluesky_visual_survey.md) contributes examples of supply becoming demand, conditional additions, repeated ribbon rejection and event-shock recovery. Dashed projected paths are scenarios, not candles. A chart header can describe a selected historical bar rather than its last bar. These are practical visual-reading details that matter when learning from published examples.

## 3. Original worked exercise: a target is also a decision point

Invented chart: price declines from a prior close of 100 toward support at 97.5, with a falling hourly ribbon around 99. The smaller timeframe reaches an unusually low oscillator reading. There are three different questions:

1. Is the original downward path still progressing? Inspect lower highs, retained closes and the next support test.
2. Can a local rebound occur? Inspect rejection at 97.5, a higher test, then a break of the smaller reaction high.
3. Has the hourly trend reversed? A rebound toward 99 is not enough by itself; inspect whether price can retain the ribbon region and form a new higher low.

A rebound can satisfy the second question while leaving the third unresolved. A short-term target at 99 therefore need not imply a longer-horizon bullish forecast. Conversely, failure of 97.5 opens a new downside route, not a reason to keep calling the oscillator extreme a floor.

Draw all three paths before revealing later candles. Label the timeframe of each confirmation. This exercise trains a useful skill: holding several conditional ideas without treating them as contradictory predictions.

## 4. Interpret commercial indicator vocabulary precisely

The retained [ChartPrime order-block documentation](https://docs.chartprime.com/market-dynamics/order-blocks.md) describes inferred volume zones with relative-volume shares and strength categories. Those shares compare displayed blocks; they are not the probability that a level will hold. The [reversal guide](https://docs.chartprime.com/market-oracle/reversal-signals.md) treats reversal signals as contrarian assistance and distinguishes ranging from trending conditions. The [trend-signal guide](https://docs.chartprime.com/market-oracle/trend-signals.md) describes trend states, tuning choices and profit-taking annotations. The [oscillator guide](https://docs.chartprime.com/prime-oscillators/prime-oscillator.md) describes its centerline, colors, divergence, bands and extremity labels. These are product semantics, not interchangeable definitions of every similarly named tool.

For practical learning, open the legend before reading the marks. Write what each mark claims to measure, whether it describes an event or a continuing condition, and what price behavior would make it useful in the current location. A visually similar green arrow in another system may have an entirely different definition.

The archived [Milkman manual extract](https://github.com/dwj9ddyvf6-hub/Silicon/blob/3815c4b223be493704850519656fa7e7b3e3750b/research/rea-teardowns/saty-stack/references/milkman-manual-2.1-2.4.md) is a third-party interpretation. It includes implementation choices such as session treatment and wick clipping that must not be silently imported into the original author's indicator definitions. The lesson is to preserve lineage: author method, community adaptation and our own operational rule are separate layers.

## 5. A reusable method-comparison card

When studying any chart teacher or tool, complete these fields:

- **What is the map?** Horizontal levels, moving references, wave anchors, profile areas or volatility ladder.
- **What is the state?** Trend, range, transition, extension or compression.
- **What is the trigger?** Exact price response, completed bar, crossover, retest or sequence.
- **What is the next obstacle?** The nearest meaningful opposing structure, not merely the most ambitious projection.
- **What changes the interpretation?** Local entry failure, larger structural failure, or lack of progress.
- **How is it managed?** Initial position, additions, partials, residual exposure and new entries.
- **Which clock belongs to each feature?** Candle interval, reference interval, session and time when it was known.

This card allows useful techniques to be combined without flattening different discretionary styles into one rigid system. It also preserves the human lesson inside the archive's engineering: the chart supplies an evolving situation, and the analyst chooses the relevant relationship and next decision.

# 18 Reading specialized indicator displays

These distinctions come from complete retained text or visible-text extractions, not newly watched product videos or inspected embedded images. Read the display's legend and method before transferring a familiar-looking mark from another system.

## ChartPrime state direction and exhaustion

### MVP oscillator
MVP runs between -100 and +100. Its zero line describes bullish/bearish state; blue/purple ribbon describes upward/downward movement. Agreement (purple below zero, blue above) differs from disagreement (blue below zero, purple above). The latter can be a counter-move or transition rather than a completed reversal. Divergence on this mode is identified manually. The guide treats extreme readings, green extension bars and arrow signals as reversal warnings and recommends confirmation back through an extreme boundary before acting. Construction formulas are not disclosed in this page. [MVP manual](https://docs.chartprime.com/prime-oscillators/mvp-oscillator.md)

### Trend Fusion oscillator
This combines a price-volume wave and adaptive comparison plot; their intersection changes the trend band. Separate features mark regular divergences, reversal dots and an MFI background histogram. Reversal-dot inputs are described as trend duration, ATR, deviation, volatility and gaps, but exact weights and thresholds are not supplied. A dot and the trend band answer different questions: possible exhaustion versus current directional state. Green money flow plus a positive wave is the manual’s example of agreement. [Trend Fusion manual](https://docs.chartprime.com/prime-oscillators/trend-fusion-oscillator.md)

**Original practice drill:** Cover price after the signal. Write four independent observations: location relative to the centerline; ribbon slope/color; agreement with money flow; distance from actual price support/resistance. Then state what price must do to confirm. This prevents treating every colored mark as the same kind of evidence. Count correlated price-derived readings as related observations, not four independent votes.


## AlgoAlpha map and timing

ILPAC’s documented layers are swing structure (HH/HL/LH/LL and BOS/CHoCH), multi-timeframe liquidity heatmaps, trendline breaks, and volume-surge FOMO bubbles. The archive describes feature roles, not the heatmap’s numerical construction. Therefore call the displayed areas *potential* liquidity/reaction zones, not observed stop inventories. Its sensible reading order is structure first, nearby zone second, breakout/rejection behavior third; volume-surge bubbles warn against entering after extension. [Archived ILPAC documentation](https://github.com/dwj9ddyvf6-hub/Silicon/blob/3815c4b223be493704850519656fa7e7b3e3750b/research/rea-teardowns/algoalpha/docs/premium-indicators_institutional-liquidity-and-price-action-concepts.txt)

Momentum Concepts describes six components and four algorithm choices, regular versus hidden divergence, volatility-adaptive reversal areas, a fast scalping component, and an 18-asset screener. This is a feature overview, not an exact formula manual. Regular divergence asks whether an existing push is weakening; hidden divergence asks whether a pullback fits continuation. Screening identifies charts to inspect; it does not replace drawing the relevant swings on the selected chart. [Archived Momentum Concepts overview](https://github.com/dwj9ddyvf6-hub/Silicon/blob/3815c4b223be493704850519656fa7e7b3e3750b/research/rea-teardowns/algoalpha/pages/momentum-concepts.txt)


## Zeiierman sweep and aftermath

The liquidity manual explicitly separates sweep direction from trade direction. An Up label means movement above highs, not “buy”; Down means movement below lows, not “sell.” Its workflow contrasts a break that holds outside a range with a sweep that returns and is reaccepted inside. Trend continuation needs directional structure; late-trend reversal needs failed follow-through, rejection, or a lower-timeframe structural change. One terminology caution matters: the page swaps conventional buy-side/sell-side stop names in its opening bullets. Use unambiguous descriptions—short-covering buy stops above highs, long-stop sell orders below lows—rather than copying that wording. [Liquidity signals](https://docs.zeiierman.com/signals/liquidity-signals.md)

The Trend Analysis strategy separates midline trend state, retracement histogram, early impulse triangles, actual entries, trailing stops and partial exits. Its entry description combines directional bias, fractal-zone alignment and a retracement impulse. Lower sensitivity lengths react faster; a larger stop multiplier allows more movement. Two retracement paragraphs contradict their own stated trend direction, so their color-only continuation instructions remain unresolved. Later examples offer the coherent chart lesson: when the expected bounce fails and price respects a structural break, stop calling the movement an ordinary pullback. Exact fractal/smoothing formulas are not disclosed. [Trend Analysis manual](https://docs.zeiierman.com/script/bot/trend-analysis-strategy.md)

**Original paired exercise:** Take two upward sweeps of the same resistance. In one, subsequent closes hold above and a pullback preserves the level; in the other, the next closes return inside and a retest fails. Label the first acceptance/continuation candidate and the second failed-break/reversal candidate. The initial sweep alone cannot distinguish them. Record the observation that changed the classification.


## Raindrop participation within a bar

The archived Raindrop reconstruction splits each bar into equal time halves, computes each half’s VWAP, and displays volume-at-price width. Comparing second-half with first-half VWAP asks whether volume-weighted participation moved upward or downward during that bar. This is different from comparing open with close. A wide section indicates concentrated traded volume, not the passage of more time. Complete both halves before making a final bar comparison. The archive’s ATR-normalized drift and proposed next-bar entry are local research additions, not original vendor rules. [Pinned reconstruction SPEC](https://github.com/dwj9ddyvf6-hub/Silicon/blob/3815c4b223be493704850519656fa7e7b3e3750b/research/rea-teardowns/trendspider/SPEC.md)

**Original exercise:** Compare two identical OHLC bars with different intrabar volume distributions. Ask whether late participation accepted the high or merely left a thin excursion there. This teaches why candlesticks and volume profiles can describe different aspects of the same interval.


## Options context horizon and regime

### Trade Echo (a distinct product, not an established identity match to the user's Echo)
Its setup library defines a 1–5 GEX rating as volatility regime, not bullish/bearish conviction. Anchor Approach applies in positive-gamma ratings 4–5; At Gamma Flip describes transitional rating 3; Flip Reclaim concerns negative-gamma ratings 1–2 near the boundary. Flip Cross is an event between snapshots, not persistent proximity. Clear Path to Anchor is about intervening obstacles, while Charm Stack combines anchor proximity with charm overhead. Agent playbooks are explicitly distinguished from price setups. Read regime → level → approach/cross/acceptance; do not translate the rating directly into long/short. [Pinned setup library](https://github.com/dwj9ddyvf6-hub/Silicon/blob/3815c4b223be493704850519656fa7e7b3e3750b/research/rea-teardowns/tradeecho/pages/setups.html)

### SqueezeMetrics
The primary archived DIX page calls DIX a dollar-weighted dark-pool short-sale ratio, a proxy for otherwise less-visible buying—not an actual customer-buy count. GEX estimates potential dealer hedge response: positive can damp movement, negative can amplify it; neither determines direction. Its local reconstruction SPEC additionally describes daily trend/volatility/convexity/short-volume measurements and a historical-analogue forecast. The practical chart lesson is to separate volatility environment from price direction and match daily context to the intended horizon. No vendor entry rule is extracted. [DIX/GEX source](https://github.com/dwj9ddyvf6-hub/Silicon/blob/3815c4b223be493704850519656fa7e7b3e3750b/research/rea-teardowns/squeezemetrics/pages/monitor_dix.html)

### Prospero and MenthorQ
Prospero’s Upside/Downside Breakout scores concern potential gains/losses over the next year, despite updating every few minutes. They combine options-market information, coverage and momentum; they are not chart-pattern breakout detections, and low downside is not equivalent to high upside. [Upside description](https://github.com/dwj9ddyvf6-hub/Silicon/blob/3815c4b223be493704850519656fa7e7b3e3750b/research/rea-teardowns/prospero/pages/learn-upside-breakout.txt)

MenthorQ’s swing overview describes upper/lower projected levels and a risk trigger for 5- and 20-day horizons. It names implied-volatility/options inputs but does not disclose the model or a numerical trade rule. These are projected context levels, not observed historical support. The archived momentum-model page contains only a verification loader, so no momentum lesson was recovered. [Swing model source](https://github.com/dwj9ddyvf6-hub/Silicon/blob/3815c4b223be493704850519656fa7e7b3e3750b/research/rea-teardowns/menthorq/pages/quantitative-model_swing-trading-model.txt)


## Market Cipher layers and timeframe

The archived FAQ is mostly access/billing material, but it directs readers to public tutorials and emphasizes matching the chart’s exchange feed to the traded venue. The current official tutorial-page descriptions teach higher-timeframe context with lower-timeframe timing; separate EMA ribbon, momentum waves, money-flow and support/VWAP layers; and explain that extreme momentum can persist. The uptrend example combines higher-chart trend, lower-chart pullback, weakening adverse money flow and support-based invalidation. The descriptions alone do not provide a complete executable Blue Wave rule; linked videos and guide were not consumed. [Official tutorial descriptions](https://marketciphertrading.com/tutorial-videos/)


## Where the retained sources did not teach a method
The GainzAlgo tutorial supplied activation instructions; TJR's listing did not disclose its stages; the GammaEdge comparison was promotional rather than an operational method. OTT here means Options Trading Toolbox, whose payoff visualizer belongs to a different task. MenthorQ's momentum page was a verification loader. These are explicit source gaps or scope dispositions, not adverse conclusions about those methods.


# 19 TheStrat range grammar and timeframe continuity

This chapter synthesizes the retained Alex Sopa explanations of TheStrat, attributed in those materials to Rob Smith. The study fully read eight English automatic-caption transcripts, five captured documentation pages and one catalog. These are text readings, not newly watched video frames. The source links identify the original teaching; the exact archived versions and hashes are retained in the read ledger. Particular execution conventions below are attributed to this teaching rather than assumed universal across practitioners.

## Separate the bar number from its color

Compare the current high and low with the previous completed bar's extremes. A **1** remains inside; **2u** exceeds only the previous high; **2d** exceeds only the previous low; **3** exceeds both. Separately compare price with the current bar's own open to describe color. A green 2d and red 2u are therefore possible: boundary crossing and net open-to-close direction answer different questions. [Scenario introduction](https://www.youtube.com/watch?v=UuTzwwBtVgo); [color conflict](https://www.youtube.com/watch?v=I0_2uQu5CKo).

For this book's exercises, use strict exceedance and treat exact touches as unbroken. That is an explicit practice convention; the retained teaching does not settle every equality, rounding or feed edge case. A live 1 can become 2, then 3. A final 3 does not reveal which boundary broke first. Gaps can open directly outside the previous range, so the illustrated inside-to-directional progression is not a claim that every opening print begins inside.

**Original drill:** the previous range is 100–110. A bar opens 104, trades 111, then 102 and closes 103. It is a red 2u. If it subsequently trades 99 before that same period ends, it becomes 3 even if it later closes 108. If instead its range is 101–109 and it closes 108, it is a green 1. State number, color and larger containment independently.

## Read a combination as an event sequence

In the retained 2-2 lesson, a 2d followed by 2u reverses the immediate downward attempt; the mirror reverses an upward attempt. For X–2d–2u, the bullish trigger crosses the 2d high and the initial magnitude reference is X's high. Taking both sides of X across the combination produces a compound 3. A 2u–2d–2u sequence can reverse a local pullback while continuing the larger advance. Specify the reference range and aggregation window; it need not coincide with a clock-aligned higher-timeframe candle. [2-2 reversal lesson](https://thestrat.ai/docs/2-2-reversal/).

**Original example:** X spans 100–110. The next bar spans 98–106 and closes 105 after opening 102: a green 2d. A subsequent trade above 106 triggers the bullish reversal route. The first mapped objective is 110; 100 is a separate reclaim reference. Trigger, reclaim and objective are three different prices with different jobs.

An inside pause changes the sequence. In 2d–1–2u, the new break opposes the earlier downward 2; in 2u–1–2u it continues the earlier upward 2. The retained lesson also includes 3–1–2, with the reversal variant opposing the outside bar's close direction. Qualifiers such as 3u/3d describe the outside bar's direction or color, not the one-sided rule for 2u/2d. [Reversal types](https://thestrat.ai/docs/types-of-reversals/).

**Room test:** put an inside range of 102–105 within a 2d range of 98–106. A break just above 105 has only about one unit to the earlier high, versus about three to the inside low. Naming the combination does not create extra room. The next meaningful larger obstacle matters.

When a live bar crosses the previous low and later crosses its high, it becomes 3 at the second crossing. The previous high was already the range-crossing objective; entering there cannot claim that same completed movement as prospective reward. Look for a genuinely further reference. [Outside-bar lesson](https://www.youtube.com/watch?v=_K8HV1zymtA).

## Momentum and continuation are different labels here

The captured momentum/retracement page uses a specific color test on the bar before the actionable signal: color aligned with the intended direction is called momentum; opposing color is retracement. This is the source's label, not a general definition of momentum. A red 2u–1–2u can therefore be structural continuation yet a long retracement entry; red 2u–1–2d can be structural reversal yet a short momentum entry. The retracement explanation emphasizes the relevant color flip. It does not universally require waiting for a completed close; the docs describe intrabar trade-through triggers. [Momentum versus retracement](https://thestrat.ai/docs/momentum-vs-retracement/).

## Full timeframe continuity describes live context

The October lesson's simplified example compares latest price with 60-minute, daily, weekly and monthly opens; a longer-horizon version uses quarter, month, week and day. Record each open, previous high/low, running scenario and whether the period is live. Color alignment is not identical to directional boundary alignment. Several opens may coincide, so several labels can represent one price rather than independent evidence. The teaching uses larger-timeframe context to organize smaller reconfirming signals while requiring the original break to remain in force. [October lesson](https://www.youtube.com/watch?v=i4UzNsv-7Dc).

**Original continuity worksheet:** make a row for each relevant period with open, prior extremes, current relation to open, live scenario and next boundary. Write which period governs the setup, which supplies timing and what would negate each. Calendar validity cannot overrule a failed price condition.

## Mother bars prevent a small reversal from masquerading as a large trend

A local signal can be genuine relative to adjacent bars while remaining inside an earlier enclosing range. Mark that mother high and low before interpreting an internal reversal as a larger escape. The September lesson also warns that an auto-fitted small-timeframe chart can magnify a narrow internal oscillation. Inspect the enclosing range and actual distance, not apparent screen height. [September direction lesson](https://www.youtube.com/watch?v=NhjsVNsjDjg); [mother-bar short](https://www.youtube.com/watch?v=AngD5h5iuZ0); [scale short](https://www.youtube.com/watch?v=Pyjfqud7BeY).

**Original annotation:** “local bullish 2-1-2, still below the weekly mother high.” Count contained bars, locate the signal within the enclosing range and measure room to its edge. This preserves both the local fact and the larger unresolved condition.

Broadening formations describe progressively expanding extremes. Start with actual pivots and the boundary being reclaimed before drawing diagonal rails. The sources use taken-out extremes and permit lines to evolve with new bars; an attractive megaphone silhouette is not enough. Nested inside periods become useful when their release resolves a larger containment boundary. [Broadening-formation short](https://www.youtube.com/watch?v=953TDLF-V-4); [timing breakouts](https://thestrat.ai/docs/timing-breakouts/).

## Group agreement adds context without revealing hidden owners

The simultaneous-break lesson looks for related instruments crossing comparable boundaries in a common window, with sector or group context. Its documentation discusses 80% participation as a stronger condition, whereas the video introduces two or more correlated names. These are different specifications, not one established universal cutoff. Freeze the basket and observation window before counting. The observable evidence is synchronized crossing; institutional ownership and remaining orders are the speaker's causal interpretation, not information proven by OHLC. Ten correlated names also need not create ten independent exposures. [Simultaneous-break lesson](https://thestrat.ai/docs/simultaneous-break-diversification/).

## Preserve the stop clock as carefully as the trigger

The reversal documentation uses setup-dependent references: the other inside-bar edge for specified inside combinations; the developing entry-bar extreme for certain variants; and near-entry protection for an entry as a bar becomes outside. It rejects automatically putting that outside-bar entry's stop across the entire wide bar. Its penny offsets are equity-specific language, not universal tick sizes. [Reversal types](https://thestrat.ai/docs/types-of-reversals/).

A developing low/high is a live quantity. Freeze what was known at entry and document permitted subsequent tightening; do not use the eventual completed-bar extreme as information supposedly available earlier. The retained materials contain nuances about initial width and re-entry rather than a single complete automated rule. State the chosen convention before replay.

## A compact practice routine

1. Fix instrument, session, timezone, aggregation and after-hours treatment.
2. Hide later bars; mark enclosing ranges and meaningful extremes.
3. Label number and color separately, keeping live classifications provisional.
4. Record the relevant opens and which boundary broke first when known.
5. State the sequence, larger location, trigger, reclaim, failure reference and first obstacle.
6. Check whether the intended objective is still ahead at the actual trigger.
7. Reveal one bar at a time and distinguish activation with continuation, activation with negation and no activation.
8. Grade classification, context, chronology and available room separately from final direction.

Classical swing analysis and this adjacent-bar grammar can complement one another. An outside range is not the same as body engulfment; a directional bar is not automatically a multi-swing trend; and this source's trade-through trigger is not a universal close-and-retest rule. Use the vocabulary to describe changing evidence precisely rather than to replace the larger chart read.

# 20 Five actual archived chart readings

Inspected October 30, 2026. These are archived market-chart renderings from the user's GitHub corpus, not newly acquired market data. The actual image pixels were inspected. The analysis below is the research team’s direct visual reading, distinguished from the chart's saved engine markers and metadata. Approximate levels are read from axes, not reconstructed exact OHLC values. Source-provider, engine-parity and signal claims in companion JSON files are reported as repository metadata, not independently reverified facts.

The four Agentic-Trading-Desk images explicitly include future bars after an interior event line. They are labeled RETROSPECTIVE_VISUAL_RESEARCH_ONLY in their JSON. Thus this is **exposed retrospective practice**, not a blind prediction test. Event-era observations below describe what the left portion supports, but the analyst has seen the full image. A later blind drill must hide future bars *before* inspection. Source image links are supplied rather than reproducing these archived images in the written handout.

## 1. MELI weekly: trend resumption within a larger advance

[Open the exact archived chart](https://github.com/dwj9ddyvf6-hub/Agentic-Trading-Desk/blob/4c8c179c5988d6e603c1f3c5f28f93e2344ca225/research_archive/tensor_full_chart_golden/MELI-1wk-2023-08-28-6049537b3cb401ad66f3.png) · [Companion metadata](https://github.com/dwj9ddyvf6-hub/Agentic-Trading-Desk/blob/4c8c179c5988d6e603c1f3c5f28f93e2344ca225/research_archive/tensor_full_chart_golden/MELI-1wk-2023-08-28-6049537b3cb401ad66f3.json)

**Identity and canvas.** MELI, weekly, visible approximately August 2022–February 2024. The event is August 28, 2023, index 54 of 81 bars; 26 subsequent bars are deliberately visible. The green 1,420 label is aligned with the event crosshair, not the final bar. The price axis appears linear. Ribbon, envelope, volume and squeeze panels are visible; adjustment/session/feed coverage details are not specified in the image.

**Direct visual observation.** The left portion progresses from a broad low area around 800–950 into an early-2023 rise, followed by a prolonged shallower consolidation generally above the old low area. The ribbon rises, then flattens as price moves sideways. Around the event line, price is pushing above the local consolidation with a positive squeeze histogram. The event is not the original low of the whole move. The displayed volume label is only modestly above its stated average, not an extraordinary participation burst.

**Interpretation at the event region.** This is more naturally read as potential resumption of an established larger advance than as bottom fishing. A useful question is whether the market can retain the upper part of the consolidation and establish a higher low after the push. The strongest competing reading is another excursion within a still-unresolved weekly range.

**Decision criteria.** Look for completed weekly trade retained above the local shelf or a constructive retest; failure back into the body of the range and loss of the prior swing low weaken the continuation interpretation. Exact execution levels need the underlying bars rather than these approximate pixels. The saved metadata lists buy-cyan, consensus-buy and extension-warning together: positive direction and extension risk can coexist.

**Visible later development, not foreknowledge.** A pullback toward roughly 1,200 occurs before the later advance toward 1,750–1,850. The late-chart pullback toward the rising ribbon demonstrates why “event followed by an eventual rally” does not settle the best entry, intervening risk or holding policy.

**Learning takeaway.** Read trend phase, entry distance and pullback behavior separately. A favorable weekly structure does not erase the need to time the location within it.

## 2. SQM daily: expansion, exhaustion of progress, then structural deterioration

[Exact chart](https://github.com/dwj9ddyvf6-hub/Agentic-Trading-Desk/blob/4c8c179c5988d6e603c1f3c5f28f93e2344ca225/research_archive/tensor_full_chart_golden/SQM-1d-2021-11-01-6e19b731780219e0f07a.png) · [Metadata](https://github.com/dwj9ddyvf6-hub/Agentic-Trading-Desk/blob/4c8c179c5988d6e603c1f3c5f28f93e2344ca225/research_archive/tensor_full_chart_golden/SQM-1d-2021-11-01-6e19b731780219e0f07a.json)

**Identity and canvas.** SQM daily; visible July–December 2021. Event November 1, 2021, index 78 of 121; 42 later bars visible. Green 49.18 is the event reference, not the right-edge price, which is around 44. Linear-looking price axis, ribbon, envelope, volume and squeeze. The underlying data and event timestamps were not independently recomputed.

**Event-region observation.** The chart has recovered from its earlier lows and spent time trading around the mid-to-upper 40s. The event appears near a fresh push from that area with the fast lines curling upward. A large subsequent advance to the upper 50s is already visible to the right, but is not information available to an actual November 1 decision.

**Event-region inference and alternative.** A continuation attempt from a local base is plausible. The alternative is another failed move through nearby prior highs. Useful confirmation would be retention of the breakout zone and follow-through rather than immediate return below the base. The metadata again combines a buy marker with an extension warning; marker semantics should not be collapsed into a single unqualified green light.

**Read the transition on the right.** Following the expansion, candles overlap near the upper range, then a later upward excursion fails to produce sustained new progress. Price loses the fast ribbon, the ribbon begins bending down, and later bars move toward the slower references in the mid-40s. The squeeze panel changes from a large positive pulse to negative values. This is a sequence of evidence, not one oscillator suddenly commanding an exit.

**Competing explanation during the first pullback.** The first decline can still be a normal correction. The interpretation becomes materially less constructive when lower highs develop and prior support fails to hold or reclaim. A fresh reclaim would be a new observable event, not something to assume because an old buy marker remains on the screen.

**Learning takeaway.** Practice the management read as carefully as the entry read. Distinguish waning upside momentum, actual loss of support and completed downtrend structure. The image illustrates all three stages without providing trade fills or a tested exit rule.

## 3. TGT weekly: a repair process rather than instant trend reversal

[Exact chart](https://github.com/dwj9ddyvf6-hub/Agentic-Trading-Desk/blob/4c8c179c5988d6e603c1f3c5f28f93e2344ca225/research_archive/tensor_full_chart_golden/TGT-1wk-2023-12-04-a0c41f275aaef0003506.png) · [Metadata](https://github.com/dwj9ddyvf6-hub/Agentic-Trading-Desk/blob/4c8c179c5988d6e603c1f3c5f28f93e2344ca225/research_archive/tensor_full_chart_golden/TGT-1wk-2023-12-04-a0c41f275aaef0003506.json)

**Identity and canvas.** TGT weekly, roughly November 2022–June 2024. Event December 4, 2023, index 54/81, with 26 future bars. Green 122.37 is the interior event level. Ribbon, AVWAP-style references, envelope, volume and squeeze are shown. Linear-looking price axis; exact settings not all recoverable from the pixels.

**Observed structure.** A sustained decline from the 150s reaches a broad low area in the 90s. A large upward weekly bar interrupts that decline. Around the event, price continues improving while faster ribbon lines turn upward, but several slower lines above remain flat or downward. The event-region displayed relative volume is 78%, which is not the same as the conspicuous participation on a different, later bar.

**Interpretation.** The key event is a transition from persistent downside progression into repair. It is too coarse to label the entire scene “bullish” without saying what has improved: price has displaced upward from the lows, momentum has turned positive and fast trend references are changing. The larger downtrend's overhead structure still matters.

**Competing explanation.** This could initially be a strong bear-market rally into prior supply. To favor a more durable reversal, observe the next pullback: does it form a higher low, and can price subsequently overcome another meaningful lower high? Those are sequential structure tests. A moving-average cross alone cannot tell the whole story.

**Visible later evidence.** The chart shows a multiweek pause around the upper 120s, another advance into the 150s/160s and then a pullback toward the 140 area. This later development is useful for studying repair → consolidation → expansion → retest. It does not retroactively make the first weekly surge a riskless entry.

**Learning takeaway.** Separate “the decline has been interrupted,” “a base is forming” and “an uptrend is established.” A skilled reader can act at an earlier stage if the permitted strategy supports it, but should name the actual stage and its competing interpretation.

## 4. VRNS daily: rounding repair, local balance and delayed expansion

[Exact chart](https://github.com/dwj9ddyvf6-hub/Agentic-Trading-Desk/blob/4c8c179c5988d6e603c1f3c5f28f93e2344ca225/research_archive/tensor_full_chart_golden/VRNS-1d-2023-06-29-b740ce72ea8f7e8a0025.png) · [Metadata](https://github.com/dwj9ddyvf6-hub/Agentic-Trading-Desk/blob/4c8c179c5988d6e603c1f3c5f28f93e2344ca225/research_archive/tensor_full_chart_golden/VRNS-1d-2023-06-29-b740ce72ea8f7e8a0025.json)

**Identity and canvas.** VRNS daily, approximately March–August 2023. Event June 29, 2023, index 78/121; 42 future bars. Green 26.53 is the interior event level, not the final price in the low 30s. Ribbon, envelope, volume and squeeze shown. Displayed units and source metadata do not establish consolidated exchange volume.

**Observed event context.** The earlier decline bottoms in the low 20s and then rounds upward. Price later stalls near 26–27, retraces toward the clustered ribbon around 25 and recovers toward the upper portion of that local balance. Around the event line the ribbon is comparatively compact. The very large later volume spike and sharp advance are still to the right.

**Working interpretation.** The chart presents an improving base with a local recovery, rather than an already completed major breakout. This distinction matters: a buy marker inside a base may be an early-location signal whose path includes further waiting and overlap. The competing interpretation is continued range trading with another rejection near the ceiling.

**Decision criteria.** For a breakout-style reading, require price actually to leave and retain the upper boundary. For a pullback-style reading, the recovered local floor and the character of the next test matter more than a future breakout not yet observed. The exact trigger should follow the selected strategy rather than being reverse-engineered from the eventual high.

**Visible later evidence.** The chart continues balancing, then accelerates upward near late July with a pronounced volume expansion. It consolidates around 30–31, retraces toward the rising ribbon and advances again near the right edge. The constructive lesson is that a tight, improving base and a later expansion are different stages worth learning separately.

**Learning takeaway.** Do not demand that every technically sensible early setup move immediately. Equally, do not use a later successful breakout as proof that every earlier bar was an ideal entry. Define the setup's allowed time and structural persistence.

## 5. AMD Tensor daily: distinguish background, transition and trend-following cluster

[Exact archived chart](https://github.com/dwj9ddyvf6-hub/ClaudeDesk/blob/85b3bb0ca88c6f5a8a2529825a770bc29992743e/eyes/canon/amd_TD.png)

**Identity and canvas.** File identifies AMD; title reads TENSOR 1D, FolioTend v698 canonical, last 160 bars, **rebased last close = 100**. The horizontal axis is relative bar index, not calendar dates. No calendar endpoint or absolute dollar scale can be established from the image alone. The archive's canonical label is a provenance assertion, not a current deployed-version verification.

**Observed price structure.** Most of the left and center is a relatively broad, overlapping region near rebased 40–50 with several swings that fail to become sustained trends. Near relative bar −40, the chart changes character: higher lows lead into a sustained advance, the fast averages rise and separate, candles increasingly occupy the upper portion of the envelope, and the final segment approaches rebased 100. Several bullish markers appear *during* the advance, not only at its origin.

**Indicator-panel inspection.** The WaveTrend-style momentum lines rise into a high region; the squeeze bars become predominantly positive on the right; the OBV-like lower panel trends upward. Stoch RSI cycles within the rising phase, so its local declines do not automatically equal breakdown of the price trend. Numerous colored signals and symbols are visible, but one should use the actual legend/source mapping before assigning meaning to every glyph.

**Interpretation.** The useful visual distinction is the shift from overlapping balance into persistent directional progression. Later bullish marker clusters may be describing trend continuation, not independent new opportunities with equal risk. The primary observation remains the changing path of price.

**Competing reading near the right edge.** A strong trend can also be extended from its slower support references. Constructive trend evidence and unattractive immediate entry distance can coexist. A pullback might provide a new location, while a sharp loss of a recent higher low would require reassessment. The image alone does not specify an executable stop or current quote.

**Learning takeaway.** Start with price behavior, then ask which panels add distinct information. Do not let a crowded indicator dashboard hide the simple transition from overlap to higher highs/higher lows. Also, never report rebased 100 as AMD's dollar price.

## What this practice adds to the operating method

1. Always distinguish an interior event/cursor reference from the last visible bar.
2. Treat chart metadata as useful provenance, but do not confuse a saved assertion with a newly reproduced calculation.
3. Read the pre-event structure and subsequent path as separate learning objects.
4. Do not evaluate an early setup solely by the final high; inspect the intervening pullbacks, delay and changes of structure.
5. Separate direction, phase, location and timing. They are related questions, not synonyms.
6. Indicators are most useful when their role is explicit: trend background, momentum character, participation or timing.
7. Label visual approximations and missing settings instead of manufacturing numerical precision.

**Completion and limits.** Five actual corpus images inspected. Four companion JSON files read in full. All five local PNGs independently matched the Git blob hashes in the pinned repository inventory. TGT and VRNS were newly retrieved for this pass; the remaining source files were retrieved separately. No source image was edited, no trade/performance result was calculated, and no claim of blind predictive accuracy is made.

# 21 Your recovered visual research methods

Source context includes [the standing chart read protocol](https://github.com/dwj9ddyvf6-hub/Midna/blob/6bbb2c8b304d8cd2b15fbcd30eca8ed842bdb0ed/quant-research/reports/TA_CHART_READ_PROTOCOL_2026-10-07.md), [original chart method](https://github.com/dwj9ddyvf6-hub/ClaudeDesk/blob/bd160ed2e98cbd12908713ef7e58975677eaf2e8/midna-corpus/gestalt/CHART_READING_METHOD.md) and [later Grand Synthesis](https://github.com/dwj9ddyvf6-hub/quant-research-critical/blob/f74ab2acf945220ba34099951982225e8238d386/scratch/cc/GRAND_SYNTHESIS_2026-10-07.md). These are dated versions; retain the later synthesis's small-sample qualifications rather than an older universal stop floor or unqualified archetype rate.

[Winner-Phenotype Doctrine](https://github.com/dwj9ddyvf6-hub/Agentic-Trading-Desk/blob/4c8c179c5988d6e603c1f3c5f28f93e2344ca225/docs/TENSOR_WINNER_PHENOTYPE_RESEARCH_DOCTRINE_2026-08-28.md) gives the best concise principle: **Observe first, name second, quantify third, encode fourth, test last.**

The meaningful unit is the entire constellation, not one marker. Ask:

- What was forming before price accelerated?
- Where was price relative to the base, old supply, ribbons, anchors, and the larger trend?
- Which marks appeared first, which reinforced them, which disappeared, and which conflicted?
- Did price accept the new area through closes and retests, or merely touch it?
- Was the breakout immediate, delayed, or conditional on a later shelf?
- How did the move pause, resume, exhaust, and possibly repair for re-entry?

The doctrine intentionally begins with exceptional winners as a positive discovery class. That is a useful way to learn anatomy. Subsequent blind examples tell us whether the recognition transfers. Neither stage needs to become a philosophical referendum on technical analysis.

### Study the relationships, not a shopping list

The doctrine specifically calls for bar separation and ATR-normalized distances among markers, ribbon, cloud, pivots and price; marker density and conflict; ribbon slope, curvature and compression; volume contraction/expansion; and weekly/daily handoffs. These are relational features a checklist of isolated bullish indicators often misses.

A practical reading sentence therefore looks like: “The weekly range has stopped making lower lows; daily price is reclaiming the slow ribbon; two tests of the same floor have held; the latest pullback is shorter and quieter; the bullish marker sequence is improving while sell marks thin out; the nearest overhead shelf remains the decision point.” This is richer than “five indicators bullish.”


## Recovered visual protocols

### ClaudeDesk/eyes/PROTOCOL_V3.md: the full examination

[Protocol V3](https://github.com/dwj9ddyvf6-hub/ClaudeDesk/blob/85b3bb0ca88c6f5a8a2529825a770bc29992743e/eyes/PROTOCOL_V3.md) uses four plates:

- TW: weekly Tensor, 160-bar window; last week may be partial and must be read as unfinished.
- TD: daily Tensor, 160 bars.
- TH: hourly Tensor, where available, with session boundaries.
- LV: monthly map plus a 252-session daily chart with traditional levels and indicators.

First inspect every visible panel. Then write observations. Only after that synthesize two to five material relationships and a trade thesis. Fields cover trend quality, swing sequence, stage, location, moving-average arrangement, pattern status, breakout hold/stretch, divergences, candle location, gaps, volume, bands, support/resistance, level stacking, VWAPs, volume-profile value, relative strength and market regime. It explicitly allows “none,” borderline confidence, and a novel-observation field.

This separates three abilities that should be practiced independently:

1. **Perception:** Is the line rising? Is the candle closing above the level? Is the visible mark really present?
2. **Interpretation:** Is this a pullback within an advance or a bounce within a decline?
3. **Decision:** What level would make an entry attractive, what would prove the read wrong, and where is the next obstacle?

The first protocol also requires a specific answer to what a numerical detector would miss. V3 expands that into spatial context and unusual relationships.

### Code-versus-eyes audit

[PROTOCOL_A](https://github.com/dwj9ddyvf6-hub/ClaudeDesk/blob/85b3bb0ca88c6f5a8a2529825a770bc29992743e/eyes/PROTOCOL_A.md) draws a code-generated zone, trigger, stop and targets on the chart. The visual reader judges every numbered assertion as right, partly right, wrong, or impossible to determine from the image. It then judges entry timing, stop placement, targets and the most consequential missed feature.

This is a particularly useful learning exercise for the existing engines: do not ask whether “the algorithm works” in the abstract. Ask whether its proposed stop is beneath the structural shelf or randomly inside it, whether its target collides with obvious supply, and whether its bullish pattern is already extended.

### Model book

[PROTOCOL_MB](https://github.com/dwj9ddyvf6-hub/ClaudeDesk/blob/85b3bb0ca88c6f5a8a2529825a770bc29992743e/eyes/PROTOCOL_MB.md) compares 10 strong winners and 10 strong losers per batch, with outcomes known for discovery. For every chart it records visible traits, regime and the most specific feature. The synthesis must define testable distinctions rather than “looks good.” Its example grammar combines a distance to a high, a recent range width and volume relative to a baseline.

This is a discovery exercise, not blind forecasting. It can teach what to look for before a second, unseen set is used to test recognition.

### Matched signal twins

[PROTOCOL_TWINS](https://github.com/dwj9ddyvf6-hub/ClaudeDesk/blob/85b3bb0ca88c6f5a8a2529825a770bc29992743e/eyes/PROTOCOL_TWINS.md) pairs two charts with the same Tensor signal and similar liquidity, regime, date and volatility. First choose which has better prospects using only the charts. Then reveal outcomes and write the conditions that separated them.

This is ideal deliberate practice for context. It teaches why identical signals can mean different things without dismissing the signals: different location, overhead supply, phase, cross-timeframe alignment, participation or extension.


## Setup families in the sampled reviews

The sampled full-chart review files repeatedly distinguish five useful families:

### Ordered continuation with retained shelf

Price is already above rising, separated averages. Pullbacks are controlled and preserve a higher platform. Momentum can cool without price losing the shelf. Entry grammar is a new shelf clearance or measured retest; protection belongs below the platform. A second Green/Cyan in the same campaign is reinforcement, not automatically a new independent trade.

### Long-ribbon repair into retained structure

Price emerges from damage, first regains intermediate structure and then accepts the long ribbon. The early marker can be permission to watch, while the later held reclaim or higher shelf supplies the entry. Learn to distinguish a transient touch of resistance from several closes and a successful retest above it.

### Discontinuous repricing with post-gap shelf

The gap or vertical bar carries information, but frequently leaves no sensible initial risk location. The first quiet, liquid two-sided shelf after repricing offers a more usable trigger and invalidation point. Subsequent continuation and failure are read against that shelf, not against the original signal alone.

### Range compression with conditional permission

A signal appears within a base but the upper boundary remains intact. The useful work is mapping tightening, higher lows, declining pullback volume and overhead supply. Price must actually escape and hold. A compressed base is a condition of readiness, not proof of direction.

### Pre-repair permission without visible completion

Buy marks appear while the slow structure still slopes down and price remains below it. The chart can be interesting without being ready. The next observable requirement is a stable floor, reclaim and accepted higher platform. This interpretation preserves the signal as an early clue without forcing a premature entry.


## Numerical companions

The [Winner Genome feature registry](https://github.com/dwj9ddyvf6-hub/Agentic-Trading-Desk/blob/4c8c179c5988d6e603c1f3c5f28f93e2344ca225/tensor_winner_genome_feature_registry.json) provides 28 implemented fields plus four unavailable source families. Useful visual-to-numeric bridges include:

- Price-to-EMA21/50/200 distance and EMA200 slope.
- Bollinger width and compression age.
- Up-volume share and prior-volume-relative RVOL.
- Kaufman path efficiency: net movement divided by total traveled path.
- Return-sign entropy: alternation versus directional persistence.
- Distance from VWAP anchored at the trailing low/high.
- Approximate overhead volume burden and coarse volume-profile point of control.
- Number of resistance tests, a close beyond the prior 20-bar high, and gap acceptance.
- Tensor conflict burden and ordered marker appearances over the trailing 12 bars.

The [pipeline](https://github.com/dwj9ddyvf6-hub/Agentic-Trading-Desk/blob/4c8c179c5988d6e603c1f3c5f28f93e2344ca225/tensor_winner_genome.py) samples a sequence at -12, -8, -4, -1, event-close and +1 bars, masking later bars at each snapshot. This is a strong teaching device: instead of studying only a finished winner, ask when its structure became legible and when it became actionable.

Implementation details matter when these tools are reused. The registry calls RSI “Wilder-style,” but the read implementation averages a short recent-return slice without Wilder recursion; the separate weekly feature file uses simple rolling averages. Its volume profile assigns bar volume to typical-price bins, not actual tick-by-price volume. These are useful proxies, but their labels must not be mistaken for exact canonical indicators. 


## Build the next visual lesson

Choose one coherent family and inspect it at several masked cutoffs. Mark the floor, first reclaim, accepted shelf, trigger and nearest resistance. Describe two to five material relationships before adding specialized labels. Compare another chart with the same signal but a different structure. Reveal the next segment and preserve the original reading beside the update. Use the full-resolution image whenever a contact sheet hides wick detail, marker identity or distance.
## Nested conditional structure in the analyst rulebook
The study fully read [the October chart study](https://github.com/dwj9ddyvf6-hub/quant-research-backup/blob/d17352421810995729739dfe0815d46e5e60cddc/galath-research/shadow/terminal/bestsetups/out/CHART_RESEARCH_1016.md) and [the larger analyst rulebook](https://github.com/dwj9ddyvf6-hub/foliotend-chart-renderer/blob/c969aa58c4456d79eac2c88a9327ea4aaadff96e/docs/hypedesk/chart-visual-study-2026-09-07/analyst-rulebook.md). The latter is a more substantial observational archive: it reports 279 additional chart inspections—Echo 100, BP 100, Mind 79—and explicitly distinguishes observed behavior (O), inferred workflow (I), and unknown private rules (U). Those are the earlier researcher's inspections, not 279 new images personally inspected in this pass. Its 180 numbered observations are categories of behavior, not 180 independent strategies or performance tests.

The strongest teaching is **nested, conditional structure**. A macro bullish thesis can contain an immediate bearish correction; a local B/X rally can be a legitimate opportunity within a larger decline. A projected first-wave completion may be followed by a future wave-2 buy zone, rather than an instruction to buy the current rally. Different zones belong to different stages and different structural degrees. A clean analysis keeps these relationships visible instead of flattening the entire chart to bullish/bearish.

Six inferred practice sequences emerge: initial impulse → wave-2 retracement → wave 3; terminal C/Y → reversal area → new cycle; breakout → retest → continuation; corrective rebound → risk area → renewed decline; wave 4 → wave 5 with a deeper-reset alternate; and macro thesis paired with a separate local timing chart. Practice each by naming its anchors, the present stage, the next observable condition, competing interpretation, and invalidation.

The rulebook provides specific visual operations: retain broken boundaries for retests; nest a small channel within a large correction; separate a trigger from a final target; preserve distinct origins for coincident measurements; mark the exact bars that justify a claim; compare breakout volume with the quieter retest when present; and separate realized gain brackets from projected returns. A gain arrow may start at a historical low rather than today's price. A future label's horizontal location is not automatically a time forecast.

**Important correction to simplistic imitation:** Echo need not draw one continuous forecast arrow; future wave labels and local target segments can carry the analysis. BP can show several staged turns rather than one decisive arrow. Mind does not always display RSI/MACD. The sample does not reveal universal pivot thresholds, line-fitting tolerances, Fibonacci anchors, indicator periods, execution rules or sizing. Unknown private rules remain unknown. The Oct16 small-sample renderer study's 'one idea per chart' and 'at most one indicator' are design suggestions, not universal analyst methods; the larger September rulebook explicitly corrects over-narrow small-sample conclusions.

Implementation lesson: retain a structured map of which wave contains which, which anchors produce each line or ratio, which level activates each branch, and which observation promotes an alternate. Copying colors without these relationships would not reproduce the method.



:::pagebreak

## Geometry before narrative
The recovered protocol adds a useful measurement discipline to the price-first workflow: distinguish a return through a tested level, residence near it and arrival beyond it. A wick through, a close through and a gap through are different events. Normalize the probe against typical movement when appropriate. The implementation's 0.20 ATR test, 0.10 ATR residence and 0.15 ATR zone-merging thresholds are its definitions, not universal chart rules. Preserve the questions: did price interact with this boundary, where did it finish, how large was the probe and what happened next? Several swing sizes on daily bars are not several timeframes. Missing volume is missing evidence, not evidence of weak participation.


# 22 Lessons from your chart perception thesis

## Use the archive as a grammar rather than a collection of signals

The thesis reconstructs several recurring preferences: location before timing; named and traceable support references; confirmation on completed bars; separate roles for weekly, daily, hourly and 10-minute views; and a distinction between an existing holder's continuation assessment and a prospective buyer's entry location. These are archived requirements, not a newly verified description of every current system. Their learning value is considerable. They force a chart reading to answer both “What is price doing?” and “Where would this interpretation become useful?”

**Original practice translation:** read one chart twice. First write a holder's interpretation using only the existing structure and its deterioration boundary. Then write a non-holder's interpretation using current distance to that boundary and nearby obstacles. A healthy uptrend can produce “continuation remains intact” in the first reading and “wait for a better location” in the second. There is no contradiction: the two decisions begin from different positions.

The thesis describes Fibonacci, verified EMA references and confirmed lows as distinct support families. Preserve the family name and calculation frame. “EMA200 daily” and “EMA200 weekly” are different objects. A tolerance around a Fibonacci price is not itself another Fibonacci level. An observed prior low is useful without being relabeled as an indicator. The practical improvement is to attach a short provenance label to every important line: what it is, which inputs create it, and when it became available.

## Separate Deep Reset from Leaders Rest

In the archived specification, Deep Reset is a progression, not a synonym for a large selloff. It starts with an eligible underlying candidate, then substantial displacement, arrival near meaningful structure, deceleration, basing or compression, and emerging demand. Leaders Rest begins with established leadership and an intact trend, then a controlled pause or pullback. An oversold bounce in a broken trend should not inherit the second label simply because its last three candles look similar. [Archived chart perception thesis sections 1 and 4](https://github.com/dwj9ddyvf6-hub/quant-research-critical/blob/f74ab2acf945220ba34099951982225e8238d386/archives/2026-10-08-chart-thesis-tensor-research/artifacts/stock-chart-perception-thesis.html)

**Original drill:** make six successive screenshots of one decline and recovery. On each, assign only the most advanced state supported at that moment: falling, arriving, decelerating, basing, turning, or confirmed under the chosen timing rule. State the missing evidence for the next state. This makes the transition visible and prevents a final recovery from turning every earlier candle into an obvious entry in hindsight.

For a Leaders Rest comparison, record the prior advance, depth and duration of the rest, overlap, volume behavior, proximity to prior breakout structure, and the first renewed directional response. Compare these with a lower-high rally in a damaged chart. The exercise is discrimination between families, not memorizing a universal numerical threshold.

## Learn to distinguish what you see from what you calculate

The thesis proposes combining the image with the exact underlying bars and indicator settings when available. This is a practical division of labor. The image makes hierarchy, shape, congestion and context easy to grasp. Calculation resolves exact distances, wick fractions and near-crosses. If they disagree, check timeframe, selected bar, session, adjustment basis and unfinished-bar status before inventing an explanation.

**Original inspection sequence:** use an overview to identify the dominant structure; a medium crop to inspect the active base or swing; and a native-resolution detail to inspect the last few candles at the decision boundary. Keep the axes and crop location attached. Enlarging a low-resolution screenshot cannot recover a wick that was never resolved. Ask for better input when the answer depends on an unreadable distinction.

For a numerical claim, record whether it came from canonical data, a visible chart label or an estimate from the axis. Those are different precision levels. For a visual claim, point to the relevant bars or region. For an interpretive claim, name the observations supporting it. This is how a reader becomes more precise without losing the ability to see the whole chart.

## Give a pivot two dates

An important archived lesson is that a turning point's location and its confirmation are not the same time. If a study rule confirms a low only after three subsequent bars, the low is drawn at the earlier bar but becomes usable under that rule only after the third later bar closes. The study record should contain both dates. A finished zigzag line makes this distinction easy to forget. [Archived chart perception thesis sections 2 and 5](https://github.com/dwj9ddyvf6-hub/quant-research-critical/blob/f74ab2acf945220ba34099951982225e8238d386/archives/2026-10-08-chart-thesis-tensor-research/artifacts/stock-chart-perception-thesis.html)

**Original drill:** replay a 30-bar sequence one bar at a time. Mark tentative pivots in pencil and confirmed pivots in a different style. When a new bar invalidates a tentative turn, retain that revision in the record. At the end compare the online map with a hindsight map. The difference shows precisely what confirmation costs in delay and what it contributes in structural clarity.

Apply the same discipline to divergence, trendlines and Fibonacci anchors. A line cannot use a second point before that point exists. An indicator trough may not be settled while the current bar remains open. In a live chart, a forming pattern is still valuable information, but it must be described at its actual stage.

## Train sensitivity to meaningful differences

The thesis proposes paired chart exercises: keep almost everything constant and change one consequential feature. This is a powerful learning design. Move a close from just below to just above a shelf; change an indicator's label from daily to weekly; remove the volume panel; hide the original impulse needed to justify the word flag; or replace a completed final candle with a provisional one. Ask exactly which conclusions must change.

Then change irrelevant presentation features: candle colors, theme, grid density or the location of an otherwise legible legend. The factual reading should remain stable. A useful learner is sensitive to structural differences and relatively insensitive to decoration. Neither a pretty chart nor a familiar ticker should substitute for identifying the evidence.

This handbook's synthetic breakout branches apply the same idea. They share the entire history through bar 19. Later continuation and failure are different lessons in updating, not proof that the reader could know the branch in advance.

## Preserve different kinds of progress

The archived thesis distinguishes accurate perception, coherent interpretation, forecasting and trading-policy utility. This is useful for learning rather than a reason to abandon chart craft. A reader can improve at detecting a failed breakout, identifying timeframe conflict or measuring a retest even before claiming a measurable trading advantage. Score those skills directly. A lucky outcome should not excuse an invented level; an adverse outcome should not erase a faithful, conditional reading.

The thesis itself is a research specification, not a trained engine. Its proposed scene graph, visual curriculum, model comparisons and acceptance thresholds were not reported as completed experiments. Its historical statistics and inherited corpus counts are archived claims with their own original scope. This handbook does not advance them to current verified performance, does not claim to have reread all underlying artifacts through reading the thesis, and does not change Tensor timing authority or any trading configuration. [Archived chart perception thesis abstract and coverage register](https://github.com/dwj9ddyvf6-hub/quant-research-critical/blob/f74ab2acf945220ba34099951982225e8238d386/archives/2026-10-08-chart-thesis-tensor-research/artifacts/stock-chart-perception-thesis.html)

**Reading receipt:** the present handbook team read the complete extracted text of this pinned thesis: 1,055 lines and 25,444 words, including its bibliography and all 81 archive-register entries. Some displayed equations were absent from the text extraction; no full rendered HTML or original embedded-chart audit is claimed. Its 81-entry historical register is not added to this run's independently read-file count.

# 23 The Femto numerical reader as a tutor

## Source and reading scope

Source: [Femto-lean/core/chart_read.py](https://github.com/dwj9ddyvf6-hub/Femto-lean/blob/f714cc78f50b871e8346e3e725c7a92ebd95521b/core/chart_read.py), commit f714cc78f50b871e8346e3e725c7a92ebd95521b, blob 74a51c27de13657548aabb0ca34f026a2bec2a95. The complete source was retrieved and statically read in contiguous sections on October 30, 2026. No repository code was installed or executed. This is a reading of the implementation and its documented reasoning, not a verification of its historical calibration or current deployment.

The module is substantial prior work: a deterministic daily-chart reader operating on OHLCV bars. It reconstructs many relationships that a visual reader looks for, then emits dated facts and a drawing contract. This makes it useful as a measuring partner for discretionary visual inspection. Its numerical thresholds are house definitions, not universal definitions of technical analysis.

## 1. Its chart-reading sequence

The entry point cleans the supplied bars, requires at least 60 usable observations, applies a series-integrity review, and requires a positive ATR. It then computes confirmed pivots, Wilder RSI, ATR and MACD. Price spans of at least twofold switch its line-fitting space to logarithms. The pattern window attempts to follow the dominant completed swing rather than indiscriminately connecting remote extremes.

Next, it selects upper and lower boundaries, classifies geometry, clusters swing levels, describes averages and volume, enriches divergences, scans an accumulation sequence, and selects a relevant shelf. Specialized pattern detectors compete with the line-based reading. The final output includes pattern state, dated swing sequence, levels, divergences, indicator context, volume, a zone, invalidation and numerical geometry for rendering.

**Learning application:** read the naked chart first, then use this kind of numerical output to check measurements. If the visual description and measured geometry disagree, inspect the same dates, prices, scale and window before adding interpretation. A deterministic detector and a visual reading can be complementary rather than rivals.

## 2. Pivots have two dates

The implementation uses five bars on each side and strict extreme comparisons. A high at index i is available only after the right-side bars exist. Its pivot record stores the extreme's date; an analyst using it in replay must also preserve when that pivot became knowable.

For a learning exercise, stop a chart immediately after a new high, label it a candidate, then reveal five bars. Record whether it becomes a confirmed swing under this convention. A faster discretionary swing definition can be studied too, but should be named explicitly rather than silently borrowing the slower definition's certainty.

## 3. Trendlines are relationships with a lifecycle

The fitter compares lines through pivot extremes with internal lines through pivot-bar closes. It labels the latter, so wick omission is visible. Candidates need separation between anchors; the score weighs touch count, span, recentness, dominant-swing anchoring and violations. Distant or already-spent lines are filtered.

The operative implementation distinguishes holding, warning and broken/lost states. It examines consecutive closes beyond a tolerance and whether the earlier swing is also exceeded. This is more nuanced than the module's older introductory shorthand about a single decisive close. Learn the current logic from the body, not just the header.

**Practical translation:** when drawing manually, record the two anchors, scale, whether the line uses extremes or bodies, and the event that changes its status. Do not repeatedly redraw a broken line to keep a preferred story alive. But also distinguish losing a diagonal rate of advance from losing the horizontal swing structure.

## 4. Pattern recognition is more than outline resemblance

The line classifier checks narrowing or approximate parallelism, slope direction and whether the boundaries actually contain the closes. Triangles require touches on both sides and interior crossings. Wedges additionally require duration and a preceding directional move. The flag/pennant path looks for a strong pole and a restrained consolidation. These gates are a useful lesson in **context plus geometry**, even when another technician chooses different thresholds.

Specialized detectors inspect:

- Double tops/bottoms: comparable extremes, separation, a substantial intervening swing, prior trend, an actual second turn, and a close through the intervening extreme. A third comparable test disqualifies this implementation's double-pattern label rather than being silently included.
- Head-and-shoulders: alternating pivots, a distinct head, shoulder comparability and timing, usable neckline geometry, and confirmation. Excessively separated armpits use a stated alternate confirmation reference.
- Cup with handle: comparable rims, adequate duration and depth, a bottom occupied by several observations rather than a single V, then a shallow handle and confirmation.
- Rounding bottom: a sustained bowl with positive fitted curvature, sufficient depth, time near the low and recovery toward the rim.
- Climax-and-base: a measured sequence derived from the Wyckoff-style scan.

**Practical translation:** ask what distinguishes the candidate from a nearby alternative. Why is this a double bottom rather than three tests of a range floor? Why is this a handle rather than a collapse back into the lower cup? Why is this a wedge rather than two lines drawn through a drift? State those differences before accepting the label.

## 5. Formation, confirmation, age and completion are separate

The code treats forming and confirmed patterns differently. It also rejects some ancient or subsequently broken patterns as the current headline. Divergence annotations can remain in the record after becoming too old or too extended to dominate the current drawing.

A good manual chart read should do the same: retain the historical event, but say whether it is still actionable context. “A breakout occurred two months ago” and “price is triggering now” are not interchangeable. Likewise, a pattern can explain an existing trend without offering an attractive new entry.

## 6. Divergence deserves an explicit comparison

The implementation compares successive confirmed highs or lows and also retains a major-pivot comparison. It separates regular and hidden bullish/bearish divergence, calculates the oscillator difference, and records both dated price pivots. RSI and MACD are evaluated using their own numerical scales.

It then searches for confirmation through price structure, an oscillator failure-swing interpretation or an oscillator trendline break, with a finite attribution window. Location near tested levels affects prominence. The full ledger is retained, while only the salient subset is drawn.

**Practical translation:** draw the exact two price pivots and corresponding indicator values. Say whether the claim concerns fading momentum against the current price move or a reset within a continuing price structure. Identify what has happened since the second pivot. Several price-derived indicators agreeing should be described as related observations, not automatically independent evidence.

## 7. Shelves, not arbitrary line counts

Pivot prices are grouped into zones and separated tests are counted as episodes. The zone chooser gives preference to structural shelves, adds averages, retracement measurements and round numbers, and ranks proximity. This captures an important trading distinction: the most heavily annotated distant area is not necessarily the next useful location.

The exact implementation permits fallback groups when a structurally anchored group is absent. Therefore its output name should not replace inspection of the actual basis list. “Three references near 50” is a description; whether those references add independent information is a further judgment.

The Fibonacci helper selects a largest-distance confirmed-pivot pair and emits its dates, endpoints, direction and 38.2%, 50%, 61.8% measurements. The transferable lesson is **name the swing before naming the ratio**. The selected swing is this engine's convention, not a requirement that every reader must choose the same anchors.

## 8. Volume and Wyckoff as sequences

The volume module describes recent versus prior average participation, contraction between halves of the pattern and expansion events. The Wyckoff-style scan looks for a wide, high-volume decline, recovery, automatic rally and a lower-volume test. Spring candidates are separated from tested springs; sign-of-strength and later support behavior precede stronger markup language.

Use this as a sequence-reading exercise. For each stage, identify the bar and measured relationship that makes the label plausible. Then ask what the next stage would look like. Do not infer the identity of traders from the bar geometry; the learning target is the observable sequence and response.

## 9. Know which parts are measurements and which are design choices

The source contains historical pattern tables, a small desk calibration claim, tier labels and a rule that scales a measured objective by a historical target-hit fraction. Those are retained research/design choices, not newly verified forecasts. In particular, multiplying height by a hit fraction is not by itself a derivation of expected price. This does not diminish the usefulness of learning measured moves; it means describing the chosen projection honestly as a planning convention.

Other useful distinctions from the source: “three touches” is the program's line-validation label, not proof that future support will hold; its RSI regime classification comes from its own average-based rule; its average names and seeds matter; its historical integrity gate uses later bars relative to an earlier discontinuity, so an as-of replay must pass only the information available at that replay edge.

These implementation details make the study more useful. 

## 10. An original exercise using this engine as a tutor

Choose a historical chart and hide its later segment. Write a visual read containing trend, key swings, candidate pattern, most important zone, momentum comparison and next observable trigger. Separately calculate the engine's numerical facts from the same truncated history. Compare disagreements in four categories: different definitions; different window/scale; a missed observation; or an unsupported inference. Reveal later bars and update both records without rewriting the original.

Keep the most educational disagreements as reusable cases. The aim is a reader who understands the chart and the tool, rather than a reader who merely repeats an engine's label.

# 24 Public code for a chart learning workbench

These are candidates for a learning workbench, not an endorsement of all files in each repository. Full fetched source files are retained privately for reference with available licenses; only the stated portions were closely inspected. The following SHA values identify file blobs, not whole-repository commits. No runtime tests, maintenance audit, or security audit was conducted.

### TA-Lib: explicit candle definitions
Repository: [TA-Lib/ta-lib](https://github.com/TA-Lib/ta-lib). File `src/ta_func/ta_CDLHAMMER.c`, blob `28e512bfccf2befe029772e20448abb6f3359966`. BSD-3-Clause license fetched.

The inspected hammer kernel compares real-body length, lower shadow, upper shadow, and proximity to the previous low with configurable candle averages. It returns 100 or 0 for this pattern. The kernel does not establish a preceding downtrend or future reversal outcome. Best educational use: compare hand-labeled anatomy with a precise detector, then add trend and location as separate fields. A pattern value is not a 100% confidence score. Inspecting one candle detector is not an audit of TA-Lib's entire indicator catalog.

### mplfinance: reproducible visual presentation
Repository: [matplotlib/mplfinance](https://github.com/matplotlib/mplfinance). File `src/mplfinance/plotting.py`, blob `3f5350e8e6fed1acdf04d6348b18a1ff43284f84`. Matplotlib license fetched.

The README documents OHLC data indexed by datetime, candle and other plot styles, volume, overlays, and panels. Relevant plotting configuration explicitly handles whether to show non-trading intervals. Best educational use: render identical snapshots for comparisons and replay. Fix scale, session inclusion, timezone, adjustment policy, and overlays before asking a vision model or human to compare charts. It renders charts; it does not turn chart appearance into a validated signal. Full source was fetched, but only selected implementation/configuration portions were reviewed.

### trendln: candidate lines with fit diagnostics
Repository: [GregoryMorse/trendln](https://github.com/GregoryMorse/trendln). File `trendln/__init__.py`, blob `a3c46508bb1e573a9c74691a37ab2a6fb1116679`. MIT license fetched.

The implementation provides extrema and candidate support/resistance-line methods, including slope-based and Hough alternatives and fitting/error summaries. Closely inspected extrema logic includes centered windows, forward-neighbor tests, and optional edge treatment. Such a point can be drawn at its historical pivot date even though it becomes recognizable later. Best use: compare alternative candidate lines and their tolerances, then keep the analyst's chosen structural line and rationale. For replay, run only on the available prefix and record when anchors became available; do not overlay lines fitted to the whole future history on an earlier decision.

### pytrendline: explicit geometric search
Repository: [ednunezg/pytrendline](https://github.com/ednunezg/pytrendline). File `pytrendline/detect.py`, blob `c9944b238c47d895ac9eb4fe2a7b399a7c79ffbb`. MIT license fetched.

The README describes exhaustive candidate search and grouping of similar lines. Reviewed code defines tolerances/scoring and pivot detection; pivot checks look forward, while first and last points receive boundary treatment. Some default tolerances use statistics of the supplied dataset. Best use: a transparent alternative-line laboratory, not an oracle. Supply only data available at the snapshot and compare stability when a new bar arrives. Record minimum contacts, wick/body convention, allowed violations, and how many nearly identical lines are consolidated. Only the opening portion of this detector was reviewed closely, not the whole repository.

### smart-money-concepts: useful taxonomy with label-time semantics
Repository: [joshyattridge/smart-money-concepts](https://github.com/joshyattridge/smart-money-concepts). File `smartmoneyconcepts/smc.py`, blob `110759cc8e063773f4905d437f15932534e7f3b4`; source version 0.0.27. MIT license fetched, retaining its actual attribution.

The source exposes FVG, swing, BOS/CHoCH, order-block, liquidity, prior-high/low, and session functions. The reviewed FVG definition depends on a next bar; its middle-bar label is not known at that middle bar's close. Mitigation indices search later data. Swing logic uses a forward-containing window and cleans sequences, including boundary handling. Best use: standardize candidate annotations while separating formation time, confirmation time, and eventual outcome. Terms such as liquidity and order block describe the implementation's price/volume rules; they do not identify trader intention. Session definitions require market/timezone/calendar review before use.

### TradingPatternScanner: instructive prototype, not textbook-equivalent detector
Repository: [white07S/TradingPatternScanner](https://github.com/white07S/TradingPatternScanner). File `tradingpatterns/tradingpatterns.py`, blob `8ae3473ff974f330f79283632303fdf8a623ad53`. Entire 188-line file read. License fetched: **CC BY-NC-SA 4.0**, not an unrestricted commercial code license.

Several masks use the next bar. The head-and-shoulders mask is a short local comparison, not an explicit ordered five-extrema/neckline construction. Its support/resistance function computes statistical bands, not clustered structural levels. Static inspection finds trendline regression fitted against bar index but then evaluated against closing price, a dimensional mismatch. A multiple-top condition asks a rolling close maximum to be less than the previous close, which cannot occur for ordinary finite values when that prior observation lies inside the window. These are reasons to study and specify algorithms carefully, not arguments against chart patterns. No code execution was used to reach these observations.


## Use the tools in distinct layers
The following workflow and hypothetical numbers are our synthesis, not copied practitioner trades or tested results.

### A concrete decision sequence
Suppose a daily advance runs from 80 to 100 and a retracement approaches 87.64 (61.8% of the 20-point rise subtracted from 100). Earlier price structure occupies 87–89. Do not call that confluence a completed reversal. Mark it as a watch zone.

Snapshot A: three down days have smaller ranges and lighter volume. Description: selling pressure appears less forceful on these measurements. Status: watching. It is not yet proof of a new up-leg.

Snapshot B: price trades to 87.50, recovers, and closes at 89.10 near the upper end of its range. A subsequent intraday retracement holds above 88.20 and price breaks the local reaction high. Status: a predefined trigger has occurred, if those were the rules written before the bar arrived.

The analysis card should separate:
- structural hypothesis invalidation, perhaps the original 80 swing origin for one wave count;
- execution invalidation, perhaps loss of the newly established 87.50 reaction low under a specified closing/intrabar rule;
- target reference, perhaps nearby supply before 100, not an automatic distant extension;
- expiration, such as failure to make progress within a declared observation window.

A tighter execution stop and a wider structural invalidation answer different questions. If stopped out, the entry thesis can fail while the larger structure remains possible. This prevents the common mistake of widening an execution stop merely because a broader chart interpretation has not yet failed. 

### A compact annotation contract
For every candidate event record:
`instrument, venue, source, adjustment, timezone, session, timeframe, as_of_time, bar_closed, chart_scale, pattern_name, observable_features, anchor_times, anchor_prices, confirmation_time, trigger, invalidation, alternative, outcome_horizon`.

Store geometric facts separately from interpretations. For example, `low_t < low_tminus1` is a fact; `liquidity_sweep` is an interpretation requiring a declared recovery condition. Store pattern revisions as new versions, not silent replacements. Numerical values should come from underlying bars where available; screenshots alone may not support exact pennies or dates.

### Twenty-chart deliberate-practice set
Prepare five examples each of continuation pullbacks, range breakouts, failed breaks/reclaims, and reversals. Include attractive failures and unattractive successes, not just textbook winners. First hide all bars after the decision point. For each snapshot:
1. Describe trend/range and location in no more than three sentences.
2. Mark only the two most decision-relevant zones.
3. Write a base case and contrary case with observable distinguishing conditions.
4. Declare whether an actionable trigger exists; passing is a valid answer.
5. Reveal one bar at a time and record which fact changed the view.
6. Review recognition, timing, invalidation, and outcome as separate grades.

Repeat the same charts later with names removed and consistent scale. Compare annotation agreement and whether the proposed trigger was actually visible at the time. These are skill measures. Strategy profitability requires additional representative samples, realistic execution assumptions, and risk analysis; it is a separate question from whether a chart was read accurately.

### Tool stack roles
A clean workbench has distinct layers: data normalization → deterministic rendering → numerical features → candidate geometry → analyst explanation → time-aware replay. Use mplfinance for controlled visual presentation, TA-Lib for explicit indicator/anatomy comparisons, and line/SMC prototypes for candidate annotations. The human or model must still explain why a candidate matters here. Do not give a screenshot classifier unchecked authority to invent unavailable volume, exact levels, or institutional intent.

An emerging [Fin-Thinker paper abstract](https://arxiv.org/abs/2610.16587) frames candlestick reasoning around tool execution and evidence grounding. Only the abstract was read; reported benchmark gains were not reproduced and are not trading profitability. Its useful research direction is to make visual claims traceable to chart regions and numeric checks rather than judge fluency alone.

# 25 A practical curriculum and replay workbook

The CMT Association describes technical-analysis education as moving through terminology, classical techniques and application, including chart interpretation, risk, relative strength and volatility. This is a useful coverage reference, not a credential earned by reading this report. Sources: [CMT program FAQ](https://cmtassociation.org/cmt-program/frequently-asked-questions/) and [knowledge domains](https://content.cmtassociation.org/hub?source=tsa_0626).

The following is an original practice plan for the assistant's chart-reading work, not a newly enabled schedule:

1. **Construction:** correctly identify symbol, venue/feed, timeframe, session, scale, adjustments, final completed bar and indicator settings. Demonstration: explain how the same series changes under log scale or a different session.
2. **Structure:** mark swings and zones without indicators. Demonstration: distinguish a pullback in an uptrend from a confirmed change in that timeframe's swing structure.
3. **Behavior:** compare impulses and corrections by distance, duration, overlap and volume. Demonstration: identify what is changing before naming a reversal.
4. **Pattern differentiation:** compare a flag, range, wedge and unresolved congestion. Demonstration: supply defining geometry and the boundary that matters, including an ambiguous case.
5. **Context:** combine weekly background, daily structure, hourly timing and finer entry refinement. Demonstration: explain a bullish hourly move inside a bearish daily structure without forcing agreement.
6. **Integration:** add indicators only after a price-first reading. Demonstration: state precisely which observation each panel adds.
7. **Replay:** freeze an unseen right edge, write the reading, reveal subsequent bars, and update. Demonstration: preserve the original reading and explain the change rather than rewriting history.
8. **Transfer:** repeat on different instruments and volatility conditions. Demonstration: preserve reasoning while adapting distances and data conventions.

### Original evaluation rubric

Score each dimension from 0 to 2: 0 absent/wrong, 1 partial, 2 clear and supported. Dimensions: chart identity; observable structure; meaningful zones; impulse/correction comparison; participation reading; timeframe hierarchy; pattern differentiation; scenario/trigger clarity; disciplined update; readable communication. Maximum 20. This is a learning rubric, not a trading edge score or a win probability.

Any fabricated price, unseen-image claim, future-confirmed pivot presented as known at the right edge, or unmarked synthetic example requires correction regardless of total score. After a correction, replay the case with the error explicitly identified. Record profitable and unprofitable outcomes separately from whether the contemporaneous chart reading was well formed.


## Replay exercises and answer keys

Use unseen right edges, not only attractive historical winners. Freeze a chart at a date. Write the map and conditional interpretations before revealing the next bars. This is a learning drill: it separates visual recognition from hindsight narration.

### Exercise set with answer keys

1. **Two highs, rising intervening lows:** Name two interpretations. Answer: possible repeated resistance/ascending triangle; a completed double top requires the relevant support break.
2. **Steep trendline break but no important low broken:** Answer: deceleration or consolidation is possible; do not equate line break with confirmed structural reversal.
3. **Green candle closing below yesterday's close after a down gap:** Answer: intrabar recovery and negative close-to-close change can coexist. Candle color is not the full session result.
4. **Price rises while stock/sector ratio falls:** Answer: absolute gain, relative lag. Do not call it leadership solely because the chart is green.
5. **A bullish daily setup with an incomplete weekly candle:** Answer: separate the completed weekly background from the current week's developing information.
6. **Very high volume, small range at resistance:** Answer: active opposition; inspect the next boundary test. Neither accumulation nor distribution is proven by the single bar.
7. **Flag without a preceding impulse:** Answer: call it a small range or channel until the defining context exists.
8. **Falling wedge breaks upward, immediately returns and loses its low:** Answer: original bullish completion failed; map the actual new structure before considering an opposite idea.
9. **A 52 breakout target and 51 major resistance:** Answer: the target is a projection; the nearer obstacle remains part of route planning.
10. **A pivot drawn on Monday confirmed Wednesday:** Answer: date the turning point Monday and the information availability Wednesday.
11. **Breakout hold for three hourly bars but no daily close yet:** Answer: hourly acceptance has evidence; daily completion remains developing.
12. **A hammer at the center of a broad range:** Answer: local rejection is observable, but its location provides less structural specificity than a test of a premarked boundary.

Score a review on observation accuracy, level selection, timeframe consistency, pattern differentiation, useful conditional forecasts and adaptation to new bars. Score the economic outcome separately. A clear, disciplined reading can lose; a vague reading can get lucky. 

## The reusable reading card

- Instrument / feed / timestamp / completed-bar status:
- Weekly state and principal boundaries:
- Daily swing highs/lows with confirmation dates:
- Current setup location and pattern alternatives:
- Hourly sequence and 10-minute refinement:
- Candle and volume evidence:
- Benchmark and sector comparison:
- Setup state: forming / triggered / retesting / extended / failed:
- What should happen next if this reading is useful:
- What changes the reading:
- Entry alternatives and nearest obstacle:
- Management observations and time horizon:
- Outcome later, without rewriting the original reading:

Mastery is the ability to make these observations quickly, accurately and consistently across unfamiliar charts, then improve through feedback. The deliverable establishes an explicit reading method and study base. Demonstrated skill comes from applying it to many dated charts with preserved before-and-after reasoning.


## Preserve the learning record

Use a portable record with these fields: source and date; symbol/feed; chart settings; visible horizon; latest completed bar; primary timeframe; state; dated swing map; support/resistance zones; candle/volume observations; pattern hypothesis and alternatives; indicator contributions; trigger; structural invalidation; likely obstacles; management interpretation; uncertainty; next observation needed; later review.

For visual work, add image identity and what was actually visible. For code-derived work, add engine/version and the actual output fields. A repository's historical visual-observation ledger is valuable training material, but reading its text is not the same as independently inspecting its original chart. Combining both permits a stronger lesson: compare one's own reading against the retained annotation, explain disagreements, and preserve both.

This learning record can inform future authorized research. It does not silently alter the existing simulated book, its risk limits, Tensor timing authority, or automation schedules. The deliverable is a growing, reviewable body of knowledge and demonstrated chart-reading behavior.
## Improve the practice protocol
## Useful habits to learn

**Use several questions, not one score.** [Holistic synthesis protocol](https://github.com/dwj9ddyvf6-hub/ClaudeDesk/blob/bd160ed2e98cbd12908713ef7e58975677eaf2e8/midna-corpus/gestalt/HOLISTIC_SYNTHESIS_PROTOCOL.md). The holistic procedure distinguishes structure, why price is moving, business context, broader market, relevant research, existing exposure, and synthesis. Its useful discipline is to name the two or three factors that actually change the interpretation. Its seven-lens version was later narrowed to four lenses in the already-read Grand Synthesis; preserve that chronology instead of treating both as simultaneously binding. A number summarizing judgment is not a probability.

**Learn to separate a setup from location.** [Archived dip score design](https://github.com/dwj9ddyvf6-hub/ClaudeDesk/blob/bd160ed2e98cbd12908713ef7e58975677eaf2e8/midna-corpus/gestalt/DIP_SCORE_SPEC.md). The dip-score document asks whether price is merely red or actually interacting with a meaningful predeclared level while the relevant structure remains intact. That question is useful; its exact point weights, Fibonacci ranking, percent tolerances and regime multipliers are uncalibrated house design. Its claim that a particular confluence is the highest-probability zone is not established by the arithmetic. Keep the measured relationships and explain the judgment rather than borrowing precision from the 100-point scale.

**Practice without future bars.** [Archived calibration protocol](https://github.com/dwj9ddyvf6-hub/ClaudeDesk/blob/bd160ed2e98cbd12908713ef7e58975677eaf2e8/midna-corpus/gestalt/calibration/CALIBRATION_PROTOCOL.md). Sample past charts before seeing the outcome; freeze the visible window, anchors, scenarios and rationale; record the result only afterward. Separate a forecast-quality exercise from a trade-management exercise. Directional movement, reaching an objective first, range containment, and profit after fills are different tasks. Include a concise reason for rejection and review the specific observation that failed, not just whether the direction was right. Return to ambiguous examples and compare independent readings.

The archived calibration file is useful but internally versioned: its v2 removes a 1.5:1 R:R tripwire, while the old anti-gaming paragraph still repeats it. A consistent new exercise must choose and state one version. Its 'coin flip' language is also not a suitable generic baseline for unequal target/stop distances, and n 20 is a pilot rather than a reliable skill verdict. Preserve positive learning—blindness, frozen predictions, outcome checks, autopsy—without reproducing those evaluation shortcuts.

**Compare trend with initiation quality.** [Three archived live readings](https://github.com/dwj9ddyvf6-hub/ClaudeDesk/blob/bd160ed2e98cbd12908713ef7e58975677eaf2e8/midna-corpus/gestalt/live-reads/LIVE_READS_2026-10-07.md). The three live example readings contrast an orderly base breakout, a second-leg recovery, and a vertical extension. They illustrate the same important distinction: the trend can remain strong while the present entry is comparatively poor. The archived prices and 'magnet' interpretations were not independently replayed here; do not promote these prose examples into demonstrated hit rates or historical-market facts.

## Make the chart carry the reasoning

[The Best Setups benchmark](https://github.com/dwj9ddyvf6-hub/galath-desk-backup/blob/65f9351af4b72682973e452e9db6b6ddc7ace8aa/best-setups/CHART-BENCHMARK.md) improves communication by requiring the operative geometry on the price pane, not only a pattern name in prose. Connect each line to its role: entry area, trigger, invalidation, interim obstacle, first target, final target. A trigger should not be labeled as a target. Show the particular averages and divergence pivots actually used by the read.

Reserve space to the right for conditional scenarios, and visually distinguish them from realized price—dashed, thinner, less saturated. A future path is a plan illustration, not invented future candles. Keep an alternate visible when the analysis has one. Declutter near-coincident decision levels with a shared bracket or grouped label, but retain each underlying level's identity. Include timestamp, expiry if the plan has one, and enough labels to check the picture against the written read.

The benchmark's volume/RSI/MACD pane requirement was a specific user preference for that desk. It is not a universal rule of Echo, BP, Mind or Long Investor; the larger analyst rulebook documents variation. The same applies to exact whitespace percentages and label spacing. The transferable lesson is legibility plus faithful mapping between measured structure, interpretation and conditional action.
## Preparation and repetition

### Dalton’s routine — full article read

[Jim Dalton’s preparation article](https://jimdaltontrading.com/routine/) starts monthly, weekly, then daily, allowing different states on each. He reviews the prior session’s attempted direction, value migration, relative volume, profile shape, and behavior at predefined references. He prunes obsolete levels, prioritizes longer-timeframe references within reach, builds up/range/down scenarios, and revises them after overnight inventory and opening-location review. This is a workflow for contextual judgment, not a requirement that all three timeframes agree.

### Dalton on repetition and observation — two short articles fully read

[Repetition with Variation](https://jimdaltontrading.com/repetition-with-variation-the-year-is-ending/) argues for task-specific practice and adaptation to changing conditions. [Learning to Observe](https://jimdaltontrading.com/welcome-to-short-term-trading-learning-to-observe/) emphasizes accumulating observations rather than immediately acting on each new insight. These are practitioner learning philosophies, not clinical evidence about cognition. His stronger claims about intuition, hidden intent, or superiority to mechanical methods are not established by these articles. A third, longer mastery page was only partially read and is not treated as completed.

### Public replay tool — full README and roadmap read, not executed

[Market Replay Trainer](https://github.com/SigaukeCogitater/trading-simulator-app) offers a chart/replay core, drawing tools, and multi-timeframe replay. The README says the public demo uses synthetic candles; real-data support is currently local-proxy crypto, not verified real stocks/forex. The [roadmap](https://github.com/SigaukeCogitater/trading-simulator-app/blob/main/docs/ROADMAP.md) says order simulation, account state, fees, journal, scoring, and review analytics are not yet built. It also distinguishes a visually hidden future from server-side anti-cheat: the browser currently holds the full loaded series. Intrabar paths are synthesized. Thus this is a promising visual-practice prototype, not a verified fill simulator or evidence of a strategy’s performance.


## Cross representation practice

This program is a proposed application of the reading, not a source claim or tested curriculum.

### Session A: representation fluency

Take one fixed interval and view price, relative-price ratio, P&F, and profile. For each, write two things it makes easier to see and two things it hides. Example: an equal-width P&F column should not be interpreted as equal elapsed time; a final profile compresses sequence; an RRG cannot directly give a stop price. Finish by answering: which representation is relevant to my current question?

### Session B: a left-to-right narration

Hide later observations. At five successive checkpoints write only: location, directional attempt, response, continuation/failure condition, and uncertainty. Avoid predicting the exact next candle. Reveal the next section and update only what changed. Save both versions so the later explanation cannot overwrite the original perception.

### Session C: contrastive pairs

Choose two charts that share a label but differ in context, then two that look different but imply a similar decision. Examples: upward break in a rising leader versus upward break in a relative laggard; opening outside old value and staying outside versus opening outside and returning; a first retracement versus a sixth test. Explain the decisive difference in one sentence, not a list of indicators.

### Session D: execution feasibility, kept separate

For a selected setup, specify the actual available order, invalidation, plausible gap risk, and missing intrabar information. If a bar contains both entry and stop and no lower-resolution record resolves the order, label the path ambiguous. Keep that uncertainty separate from whether the chart structure was correctly recognized. A strong recognition score does not prove tradable expectancy.

### Session E: teach-back and calibration

Explain a case to a reader without using the setup’s name. Give the visible observations, competing interpretation, and the next piece of evidence that would distinguish them. Ask the reader to reconstruct the same decision boundary. If they cannot, the rule may be too vague—or a construction setting may be missing.

### Review rubric

- **Observation fidelity:** Are claims visible at the timestamp, or imported from the future?
- **Context:** Are market/sector/benchmark and higher-timeframe states explicit where relevant?
- **Construction literacy:** Could another reader reproduce the chart?
- **Sequence:** Is attempted action separated from market response?
- **Decision clarity:** Is there an actionable condition, invalidation, or reason to wait?
- **Adaptation:** Does the explanation change when evidence changes, without rewriting history?
- **Transfer:** Can the distinction be recognized in another instrument or a less textbook example?

Measure progress by fewer category errors, more reproducible annotations, faster recognition of genuinely relevant differences, and better explanations of why a case is not ready. Keep financial outcomes as a separate later validation task, not the sole score for the perceptual exercise.


## A visual acuity exam

The Femto V5 document's most transferable idea is to separate **seeing**, **interpreting**, and **forecasting**.

### A repeatable reading session

1. Inspect a clean weekly/context chart, then daily, then a recent-bar magnification. Verify symbol, timeframe, session, scale, adjustments and cutoff. Keep outcome labels and model opinions off the initial plates.
2. State the first overall impression briefly, but do not allow it to replace the observations.
3. Fill a factual sheet: trend and swing structure; price versus named average; average slope; distance to visible high; recent displacement; last bar body/range/close position; inside/outside relationship; volume versus baseline; gaps; earnings reactions; contraction; nearest levels above/below.
4. Reinspect uncertain marks at higher resolution. Give lines distinct dashes and direct labels. Use neutral lettered candidate levels when axis precision is poor, then map letters to exact data prices separately.
5. Write the setup, trigger, failure condition, target/next obstacle, alternate path and explicit wait/no-trade state. Every rationale should point back to an observed feature.
6. Freeze this read before revealing future bars. Grade perception independently of the outcome: a well-seen chart can fail; a profitable call can arise from a misread.

### An eye exam, not just a return contest

Use real charts plus synthetic charts with planted controlled features. Grade bar color, close location, gaps, average ordering, swing counts, contraction, volume comparison and numeric-level reading. Report performance by feature size and boundary distance: a close 0.1% from an average is harder than one 5% away. Test palette changes, chart density and image order. Use an image-without-opinion arm, a text factual-sheet arm and image-plus-sheet arm to locate the actual bottleneck. Pairwise chart comparisons can exercise relative judgment, but swap order to detect presentation bias.

Several V5 exam details need refinement before adoption: zero-range bars need explicit close-location handling; a true-range maximum is not necessarily the widest visible high-low candle; pivot labels must respect right-side confirmation delay; a shuffled finite series can still contain accidental trends, so 'all shuffles must look trendless' is not a valid truth rule. Its prose says twelve observation items while its numbered sheet contains thirteen. Correct the benchmark specification before counting scores.

The archived V4 experiments were not rerun in this study. V5's larger exam and model-specific resource estimates are proposals rather than new completed results. The useful lesson is to test seeing, interpreting and forecasting separately. [V5 visual learning design](https://github.com/dwj9ddyvf6-hub/Femto-lean/blob/58244bf2e020b1ed4b269b0c4f30638be456deb2/eyes/V5/RESEARCH_LLM_CHART_VISION.md).

## Verify the decisive observation
Source studies: [visual acuity research](https://github.com/dwj9ddyvf6-hub/Midna/blob/96e36e379cbe9330441221554d848f270d288800/workspace/research_notes/llm-visual-acuity-enhancement-20261008-0254/report.md) and [chart annotation research](https://github.com/dwj9ddyvf6-hub/Midna/blob/96e36e379cbe9330441221554d848f270d288800/workspace/research_notes/chart-reading-mastery-and-annotation-cra-20261015-2352/report.md). These are retained research syntheses, not newly reproduced benchmark results.

**Audit encodings before judging shapes.** Explicitly check axis direction, log/linear scaling, breaks, dual axes and cropped context. Make a short legend-to-series registry where overlays are ambiguous; identify a series by its label and line style, not color alone. A slope or crossing claim is meaningless if the compared lines use different scales.

**Verify the observation that carries the conclusion.** If the reading hinges on one wick, close, label or line interaction, inspect that exact region at adequate resolution while keeping the overview available. A fluent description is not verification. Cropping can remove the prior impulse or relevant support, so preserve crop coordinates and context. Prefer source OHLCV for precise values; do not transcribe hundreds of unreadable candles merely to satisfy a generic chart-QA procedure.

**Count explicitly when the count matters.** Mark candidate swings or bars with identifiers, separate regions carefully, and avoid counting boundary objects twice. If the image cannot support the required count, say so. More verbal reasoning does not recover missing pixels.


## Annotation and verification
Separate level coordinates from explanatory prose: exact price labels can sit at the axis; explanations use offset callouts linked to their anchors. Reserve a stable distinction for observed history versus provisional/projected structure. Preserve level provenance even when several near-coincident levels share a displayed zone.

Run a collision pass against both labels **and candles/data marks**. Place high-priority labels first, then move, merge or omit lower-priority ones rather than obscure the evidence. Occupancy-bitmap layout is a concrete researched implementation, not just an aesthetic preference. The report misattributes this paper: its author is Chanwut Kittivorawong. [Primary paper record](https://arxiv.org/abs/2405.10953)

Inspect at the actual delivery size. A mobile view should preserve the decisive evidence with fewer simultaneous annotations, not shrink a dense desktop chart until the labels disappear. Numerical caps such as five mobile labels or fifteen desktop labels are adjustable house choices. Use redundant shape/text/style cues for meaning, and sufficient text contrast: WCAG's normal-text threshold is 4.5:1, with 3:1 for qualifying large text. These are accessibility thresholds, not a universal minimum chart font size. [W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)


A geometric measured move, a nearer conservative objective and a probability of reaching either are separate quantities. Multiplying a pattern height by an old target-hit percentage does not automatically produce an expected price. Preserve the full conditional geometry while marking actual intervening obstacles.


# 26 Four frozen chart readings with masked and revealed futures

This is an actual before-and-after learning exercise, not a reconstruction written with the answer visible. The lead researcher inspected four masked charts and froze the readings before seeing the next 24 bars. The instrument identity had been disclosed as ADAUSD; the cutoffs and later paths were hidden. Thus the test used right-edge masking, not complete identity blinding.

Each case contains 96 visible four-hour bars, a trailing SMA20 and per-bar volume. The four nonoverlapping windows were selected by fixed indices rather than outcomes. The archived values were unchanged; source adjustment metadata was absent and the acquisition feed was only inferred from its Kraken-compatible schema. The potentially unfinished final source bar was excluded. [Pinned source data](https://github.com/dwj9ddyvf6-hub/ClaudeDesk/blob/bd160ed2e98cbd12908713ef7e58975677eaf2e8/probe/ohlc_ada.json); [schema reference](https://docs.kraken.com/api-reference/market-data/get-ohlc-data).

These eight book figures were reformatted from the same data after the freeze for print readability. The original masked charts, frozen written record and exact numeric audit remain in the research files. No threshold or assessment below was optimized after the reveal. First-person wording in the case readings belongs to the lead researcher's frozen record. Its immutable identity and the source data hash are retained in the freeze and evaluation receipts.

## Read before turning to the reveals

First write five observations, the primary interpretation, a serious alternative, a precise trigger, the invalidation and a reason to wait. Treat the final visible close as the decision time. Use the four case pages before looking at the reveal pages.

The frozen path question asks which of two price references is touched first within 24 future bars, or 96 hours. Touches use inclusive highs/lows. The separate close-confirmation route expires after 12 bars, or 48 hours; its inequalities are strict. A same-bar dual touch would remain ambiguous. No fills or transaction costs are modeled.

:::pagebreak

## Case A before reveal

![Case A with future bars hidden. Real archived OHLCV, not synthetic market data. Book layout of the original frozen exercise.](assets/masked_A_decision.png)

**Five observations:** (1) Early range around .160–.163 gives way to a lower-low decline toward .140. (2) The middle section stops making comparably deep lows and overlaps around .144–.148. (3) Around observed index 76 price accelerates upward and clears earlier intermediate highs. (4) The final advance reaches above .180 and the last three candles pull back toward .176, with smaller volume than the largest advancing bar. (5) The SMA20 is sharply rising but far below price around .162, so trend direction and immediate entry location differ.

**Primary interpretation:** a newly established strong advance undergoing its first visible late pullback. I favor consolidation/retest over immediate failure all the way into the old base, but the move is too extended for me to call the final close a good fresh entry.

**Serious alternative:** the late vertical expansion is an exhaustion move; the small pullback becomes a sharp return through .170 toward .160. The final three bars alone do not settle this.

**Frozen 24-bar path hypothesis:** price will trade .180 again before trading .169. This is a directional path comparison, not an executable trade with favorable reward/risk. If both are touched in the same four-hour bar, ordering is ambiguous.

**Action/trigger:** WAIT at the final displayed close. For a later continuation read, require a completed close above .180 within the next 12 bars while no preceding close has fallen below .169. Cancel that trigger route for this exercise if .169 closes first. A subsequent orderly higher-low structure would be needed to define an attractive fresh-entry risk, rather than use the remote SMA as a convenient stop. Reference objective .184, not a guaranteed destination.

**Confidence:** moderate that the local trend has turned up; low-to-moderate on the next 24 bars because of extension. Expansion on a breakdown through .170 changes the reading materially.


:::pagebreak

## Case B before reveal

![Case B with future bars hidden. Real archived OHLCV, not synthetic market data. Book layout of the original frozen exercise.](assets/masked_B_decision.png)

**Five observations:** (1) A decline from about .175 bottoms near .154 around the middle of the window. (2) Recovery builds a platform around .162–.164, then another around .168–.173. (3) The later advance makes highs near .198–.199. (4) Its recent pullback is relatively small and overlapping, ending with a green recovery bar near .193 after approaching .190. (5) Price remains near/above a rising SMA20 around .190; recent pullback volume is lower than the conspicuous prior advancing-volume burst.

**Primary interpretation:** a controlled pullback within a local uptrend, offering a more coherent nearby reference than A. The final green bar is early response, not proof the pullback has finished.

**Alternative:** the recent high is a distribution peak and the slow pullback is about to lose the average and return to the prior .182–.184 shelf.

**Frozen 24-bar path hypothesis:** price will trade .198 before trading .182. Same-bar dual touches remain ambiguous.

**Action/trigger:** watch for a completed close above .194 within next 12 bars, provided no earlier close has fallen below .189. A close below .189 cancels this timing route for the exercise. First objective/reference .198; stop-condition for the timing thesis is a completed close below .189, not the distant .154 base. Since .194-to-.198 room is smaller than .194-to-.189 timing risk before costs, this is a valid chart confirmation to observe but insufficient by itself to justify a trade. No actual entry is recorded.

**Confidence:** moderate on continuation structure, not a calibrated probability. Failure to retain .190 and a weak rebound from below it would weaken the read.


:::pagebreak

## Case C before reveal

![Case C with future bars hidden. Real archived OHLCV, not synthetic market data. Book layout of the original frozen exercise.](assets/masked_C_decision.png)

**Five observations:** (1) A very early spike above .240 is rejected on the largest displayed volume. (2) The broad earlier sequence declines through successively lower shelves toward .193–.200. (3) The late section recovers through .200 and reaches .222–.225. (4) A pullback holds around .210 and the latest rebound returns toward .223 without yet clearly exceeding that local high. (5) The SMA20 turns upward, with final price above it near .219; the sharp pullback bar had notable volume, followed by quieter overlapping bars and recovery.

**Primary interpretation:** repair into a new local range, with an attempted higher-low continuation, but still confronting nearby prior supply. I favor another test of .225 before loss of the latest .210 shelf. This is not yet an established new high across the full visible window.

**Alternative:** the recovery is only a countertrend rally that fails around .225 and returns toward .200.

**Frozen 24-bar path hypothesis:** .225 trades before .209. If neither trades, call unresolved; if both occur in one bar, ambiguous.

**Action/trigger:** a completed close above .226 within next 12 bars, with no prior close below .209, confirms the local escape for observation. Cancel the route if .209 closes first. Nearby objective .231. A timing entry would need new narrower structure; the full .209 invalidation is too far from .226 relative to that first obstacle. WAIT rather than invent a tighter stop. If price instead closes below .209, investigate a return toward .200.

**Confidence:** low-to-moderate because local repair and larger declining structure are competing. A sustained .226 recovery or an accepted .209 loss resolves much more than another small candle in the middle.


:::pagebreak

## Case D before reveal

![Case D with future bars hidden. Real archived OHLCV, not synthetic market data. Book layout of the original frozen exercise.](assets/masked_D_decision.png)

**Five observations:** (1) Much of the window rotates broadly between about .238 and .260. (2) A later expansion clears .260 and pushes to .278–.283. (3) The move then loses momentum and a large red bar returns below .260. (4) Subsequent candles remain below that broken area and form a weak overlapping shelf around .253–.258; the latest close is nearer .252. (5) The SMA20 is above price around .265 and flattening, while a notable later volume burst does not create a sustained upside recovery.

**Primary interpretation:** failed upside expansion with current downside pressure; a return toward the old range interior is more plausible than immediately reclaiming the upper trend. This is structurally weaker than A/B and weaker than C's higher-low repair.

**Alternative:** this is a deep but temporary retest of the larger breakout area; reclaiming .260 and holding it restores a constructive interpretation, with .267 next.

**Frozen 24-bar path hypothesis:** .245 trades before .267. Same-bar ambiguity is retained.

**Action/trigger:** completed close below .250 within next 12 bars, provided no prior close has exceeded .260, activates a bearish observation route toward .245. A prior close above .260 cancels it for this exercise. After activation, a completed close above .259 invalidates this narrow continuation hypothesis. No short trade is entered; nearby target room versus stop distance again needs a separate execution assessment.

**Confidence:** moderate on current weakness, lower on whether .245 is reached within 24 bars. A strong recovery through .260 would be the most important contrary observation.


:::pagebreak

## Case A after reveal

![Case A with 24 later bars shown. The dashed line separates the frozen history from the reveal; +12 and +24 label future bar counts.](assets/masked_A_reveal.png)

**Exact audit:** The .180 path reference traded at future bar 2; .169 first traded at bar 24. The close route confirmed at bar 2 with .190878, above .180, without earlier cancellation.

**A: correct near-term continuation need not persist.** The market resumed up with a large green bar 2 and ultimately reached .199779, then retraced across the later window to a final .169218. The stated .184 reference was already passed within the candle that finally confirmed a close above .180. Thus that reference cannot be credited as a post-confirmation profit target at a hypothetical .180 fill. The pre-reveal distinction between trend direction and poor extended entry location was useful. A successful first-touch comparison does not mean the end-of-horizon return was positive.


:::pagebreak

## Case B after reveal

![Case B with 24 later bars shown. The dashed line separates the frozen history from the reveal; +12 and +24 label future bar counts.](assets/masked_B_reveal.png)

**Exact audit:** The .198 path reference traded at future bar 1; .182 did not trade in the reveal. Bar 1 confirmed the close route at .194934, but bar 2 closed .188843, below the specified .189 timing invalidation.

**B: path agreement and timing-thesis failure coexist.** Bar 1 high .198658 reached the first path objective before that candle closed at .194934. Bar 2 then closed .188843, below the explicitly specified .189 timing invalidation. Price later recovered, with full reveal high .211474 and final .198480. That later recovery does not erase the failed timing thesis or authorize retrospectively ignoring its invalidation. No “winning trade” claim follows from the first-touch result; target was touched before the close-confirmed route could be known.


:::pagebreak

## Case C after reveal

![Case C with 24 later bars shown. The dashed line separates the frozen history from the reveal; +12 and +24 label future bar counts.](assets/masked_C_reveal.png)

**Exact audit:** The .225 path reference traded at future bar 5; .209 at bar 22. No close above .226 or below .209 occurred during the first 12 bars. The initial route expired without activation.

**C: wick penetration is not close acceptance.** Bar 5 high .226335 satisfied the .225 path touch, but its .219499 close rejected the upper area rather than satisfying >.226. No eligible close confirmation appeared in the first 12 bars. A later escape beyond the initial window cannot be silently admitted under the frozen rules. The chart eventually dipped through .209 at bar 22. The correct output is primary reference first, but no qualifying initial route—not a fabricated execution or a failed close signal that never occurred.


:::pagebreak

## Case D after reveal

![Case D with 24 later bars shown. The dashed line separates the frozen history from the reveal; +12 and +24 label future bar counts.](assets/masked_D_reveal.png)

**Exact audit:** The .245 path reference traded at future bar 2; .267 did not trade. Bar 1 confirmed at .249634, below .250; no prior close exceeded .260. No later close exceeded .259 during the 24-bar reveal.

**D: weakness followed through, then recovered.** Bar 1 close .249634 confirmed the narrow bearish observation. Bar 2 dropped through .245, closing .231425; the full-window low was .223147. Later price rebounded into the .250s, ending .253478. The specified post-activation close above .259 did not occur; full-window maximum high .259106 itself is insufficient because the rule required a close. This reinforces the distinction between candle extremes and closes, and between an initial move and perpetual directional ownership.


## What changed in the reading practice

All four first-touch statements matched the observed order. These are four descriptive path checks, not four trades or a measured mastery rate. Their reference distances differed, and all four original actions were wait or no-entry observations. Case B failed its narrow timing condition; C never activated; A passed its stated objective before the confirming close could be known. D followed through before a later rebound.

The constructive lesson is specific: trend, first-touch path, close confirmation, entry geometry and management are different questions. At the confirming bar, inspect whether the objective is still ahead and whether a new retest can provide a usable boundary. Preserve the original rule even when later price would make a different rule look better.

For the next practice set, use several instruments and comparable predeclared horizons. Score observation fidelity, scenario discrimination and execution geometry separately. Keep the frozen reading beside the update; do not let a persuasive retrospective story replace it.




# 27 Research coverage repository map and remaining gaps

## What this edition completed

The study combined practical technical-analysis teaching, selected public methods and code, recovered research from the studied GitHub repositories, direct chart-image inspection and a frozen right-edge exercise. Discovery and learning coverage are different achievements. The reachable branch-tip tree inventory is complete for the captured account scope; the semantic reading of every discovered candidate is not.

Research cutoff is 30 October 2026. Repository branches and public pages can change; the substantive archived-source citations use specific commits wherever verified. A navigation link to a repository is not a claim that its current contents were all read.

## GitHub discovery boundary

- **Repositories:** 33 returned by the connected listing, paged to an empty final page.
- **Branches:** 504 named entries, representing 499 distinct repository and commit roots. 498 roots were reachable; InfinityBlade's single captured root returned 404.
- **Tree closure:** 3,430,274 file-location rows across reachable tips; 382,823 unique Git blob SHAs; zero unresolved subtree SHAs. Identical tree content was reused rather than repeatedly fetched. Four cross-repository locations are explicit aliases in the intermediate export; the memoized final count expands their locations.
- **Candidate search:** 181,081 unique blobs matched broad TA/chart-related discovery rules; 22,665 were text, document or code candidates. These are permissive metadata matches, not 181,081 verified lessons. Generated data, images, vendors, duplicates and irrelevant pathname matches are present.
- **Historical boundary:** captured branch tips, not every historical commit or independent tag-only history. Midna changed during collection; distinct captured tips remain distinct.

The authoritative discovery receipt is `github/final_tree_coverage.json`. Complete location and candidate exports are retained as compressed JSON-lines files; the smaller queue and repository map support continued triage. Older intermediate summaries are superseded by this final receipt.

## Completed reading is much smaller than discovery

The merged SHA-deduplicated ledger records **133 unique Git source blobs with completed review**: **128 complete raw text or code reviews and 5 complete extracted or visible-text reviews**. The latter are the chart-perception thesis extraction and four vendor HTML visible-text extractions, not audits of every HTML tag, embedded image or equation glyph. The total includes methodology, tools, research, evaluations, provenance, catalogs and nonlesson receipts; it is not 133 independent manuals or strategies.

Several sources have both selected-section and later full-read receipts, or copies in multiple repositories. Their bytes count once in the full-read union. Repository-specific counts below attribute a reviewed blob to the recorded source repository; zero does not mean the repository contains no useful material or no identical blob was read elsewhere. Source-specific ledgers retain commit, path, Git blob SHA, local integrity evidence and access depth.

Separately, **133 structured JSON source blobs were completely parsed**, yielding **12,950 unique historical chart-review records**. Parsing those records is not individual semantic reading of every record, and is not fresh inspection of 12,950 chart images. Earlier reported 279-image and other large visual studies remain historical researchers' observations unless this edition inspected their underlying pixels.

The merged machine receipt is `github/study_coverage_summary.json`, with `github/merged_read_evidence.json` preserving contributing read statuses. Eight sources also have selected-section coverage rather than a blanket whole-source claim. The final text-candidate queue contains 130 known full-reviewed blobs; three completed source reviews fall outside the broad pathname filter but remain indexed. These dimensions are not added into a single absorption total. The separate family ledgers identify exact contiguous or full-document reads. No retrieved repository program was installed, imported or executed as part of the source study; original plotting and document-production code ran locally.

## Echo available text review and newsletter overlap

The recovered [Echo archive](https://github.com/dwj9ddyvf6-hub/ClaudeDesk/blob/5fad5264d9b56dee7ec9c7d13164d55f5072d06f/wt_sec/docs/research/2026-10-18-terminal/echo-harvest/posts_all.json.gz) has 16,659 unique records. All 3,213 nonempty main text fields received content review. The other 13,446 main fields were empty and were not reconstructed.

- **Full retained-field reading:** 1,474 technical or longer candidates. The selection includes some contextual/promotional material; it is not a count of independent teaching lessons.
- **Brief-content review:** 1,739 records through 887 distinct cleaned-text groups. Twenty-four clear method or market replies were specifically retained as useful; the remainder was not falsely labeled uniformly irrelevant.
- **Additional nested text:** 138 unique texts absent from the main nonempty set were fully read: 115 attributed to Echo and 23 reposted from other authors. These are nested-text units, not automatically additional unique archive records.

Full retained text is not necessarily the complete original post: truncations, snippets and seven id-less paraphrases exist. Archive class A/B/C describes acquisition provenance, not reliability or trading skill. Mirror-derived retained text was substantively studied; it was not merely a discovery lead. This study did not independently authenticate every live X original, the top-level author field or reported execution.

Six substantive newsletter lessons were read. Five overlap the public article study and are represented once; the WYFI false-flag lesson is the additional case. One WYFI email screenshot was inspected. Thirty-five remaining email images were not inspected after access failures. Selected public newsletter editorial embeds that failed retrieval must not be confused with the separate successfully inspected archived image set.

Exact Echo receipts are `public_community/archive/complete_coverage_counts.json` and `complete_text_reading_ledger.json`; the initial 216/410-record study is superseded as a coverage total. Max's original 34 post texts were not independently recovered in the Echo-only compressed corpus; the older joint playbook is a secondary research source.

## Direct visual work and original teaching charts

The final visual ledger verifies **24 distinct source-image files by SHA256**, not 24 independent strategies: 15 retained Echo charts, five additional archived market charts, one WYFI email screenshot, and three public teaching images or PDF chart pages. The public set comprises the RRG guide's page-two chart and TEAM before/after charts. Individual study image counts are subsets, not additions to this union.

The Echo images cover seven method sequences: AAOI, KRMN, Nasdaq futures, UBER, ASML, BE and NVAX. The five other archived chart readings are MELI, SQM, TGT, VRNS and AMD. These are exposed retrospective readings, with the source author's annotations visible where present. Original pixels were inspected individually, not inferred from filenames or earlier written image descriptions. A matching stored CELH image was not found for its specified post ID.

The book also contains **eight original synthetic teaching figures** and **eight original data plots for four masked/reveal pairs**. Synthetic figures teach controlled differences and are not market observations. The exercise plots use one archived ADAUSD four-hour series; the lead researcher froze the original four masked readings before the 24-bar reveals. Symbol identity was known, cutoffs and future paths hidden. These are not eight more third-party source images or four executed trades.

All four selected first-touch checks matched their observed ordering. That narrow result is retained alongside the more instructive qualifications: B's timing condition failed, C never activated within its window, and A's objective was passed before close confirmation. The frozen reading, data identities and exact evaluator output remain preserved.

## Public and community study scope

Primary documentation and originator-hosted teaching supplied definitions and construction rules; practitioner articles, selected forum discussions and public GitHub files supplied application examples. The craft ledger contains 38 source entries and the advanced extension 18, with overlaps retained rather than added into an inflated distinct-source total. The bibliography lists cited URLs, not an assertion that every linked website, repository, comment thread, book or video was consumed.

The research includes explicit text-versus-pixel distinctions. The Raschke interview's four-page text was read, but its chart bitmap was not successfully inspected. The RRG guide's complete six-page text and one chart page were inspected. TheStrat study read retained captions and documentation, not video frames. Public code reads range from complete small files to identified excerpts; no runtime validation or deployment is implied. Vendor pages disclose some roles without disclosing formulas, and several access or sales pages yielded no chart-method lesson.

Live X accessibility was limited. The recovered archive allowed a much deeper dated text study without treating current live access as established. Selected Reddit main posts and portions of discussion were read; entire communities and all replies were not. Books, paid courses and unavailable pages were not silently counted as completed sources.

## Repository map

The table covers every enumerated repository. File locations include repeated paths at different captured commits; they are not distinct lessons. Full-review counts refer to source blobs directly attributed to that repository and include visible-text reviews. Repository links are navigation links; evidence pins appear in the source citations and read ledgers.

| Repository | Branches | File locations | Reviewed blobs |
|---|---:|---:|---:|
| [galath-desk](https://github.com/dwj9ddyvf6-hub/galath-desk) | 17 | 32,313 | 0 |
| [galath-desk-backup](https://github.com/dwj9ddyvf6-hub/galath-desk-backup) | 10 | 19,647 | 6 |
| [foliotend-tensor-release](https://github.com/dwj9ddyvf6-hub/foliotend-tensor-release) | 2 | 8,984 | 0 |
| [aftershift](https://github.com/dwj9ddyvf6-hub/aftershift) | 4 | 2,174 | 0 |
| [autopilot-desk](https://github.com/dwj9ddyvf6-hub/autopilot-desk) | 1 | 569 | 0 |
| [ChatGPT](https://github.com/dwj9ddyvf6-hub/ChatGPT) | 14 | 8,889 | 0 |
| [Ledge](https://github.com/dwj9ddyvf6-hub/Ledge) | 9 | 12,727 | 0 |
| [Agentic-Trading-Desk](https://github.com/dwj9ddyvf6-hub/Agentic-Trading-Desk) | 7 | 185,101 | 14 |
| [InfinityBlade](https://github.com/dwj9ddyvf6-hub/InfinityBlade) | 1 | 0 | 0 |
| [foliotend-chart-renderer](https://github.com/dwj9ddyvf6-hub/foliotend-chart-renderer) | 10 | 42,625 | 3 |
| [span-harvest-unified](https://github.com/dwj9ddyvf6-hub/span-harvest-unified) | 1 | 19 | 0 |
| [foliotend-research-operations-archive](https://github.com/dwj9ddyvf6-hub/foliotend-research-operations-archive) | 3 | 10,382 | 0 |
| [codex-complete-archive](https://github.com/dwj9ddyvf6-hub/codex-complete-archive) | 19 | 63,039 | 0 |
| [FolioTendV265](https://github.com/dwj9ddyvf6-hub/FolioTendV265) | 1 | 2 | 0 |
| [Codex](https://github.com/dwj9ddyvf6-hub/Codex) | 1 | 10 | 0 |
| [Femto](https://github.com/dwj9ddyvf6-hub/Femto) | 1 | 262 | 0 |
| [InfinityBladeV2](https://github.com/dwj9ddyvf6-hub/InfinityBladeV2) | 1 | 11 | 0 |
| [InfinityBlade-Engineering-Doctrine](https://github.com/dwj9ddyvf6-hub/InfinityBlade-Engineering-Doctrine) | 1 | 16 | 0 |
| [quant-research-backup](https://github.com/dwj9ddyvf6-hub/quant-research-backup) | 20 | 2,375,394 | 3 |
| [galath-desk-terminal](https://github.com/dwj9ddyvf6-hub/galath-desk-terminal) | 1 | 23 | 0 |
| [quant-research-critical](https://github.com/dwj9ddyvf6-hub/quant-research-critical) | 11 | 126,354 | 11 |
| [Midna](https://github.com/dwj9ddyvf6-hub/Midna) | 7 | 75,115 | 11 |
| [Cursor2](https://github.com/dwj9ddyvf6-hub/Cursor2) | 1 | 280 | 0 |
| [qullamaggie-research-pass3](https://github.com/dwj9ddyvf6-hub/qullamaggie-research-pass3) | 1 | 8 | 2 |
| [lazarus-desk](https://github.com/dwj9ddyvf6-hub/lazarus-desk) | 2 | 282 | 0 |
| [Femto-lean](https://github.com/dwj9ddyvf6-hub/Femto-lean) | 115 | 258,292 | 7 |
| [dwj9ddyvf6-hub.github.io](https://github.com/dwj9ddyvf6-hub/dwj9ddyvf6-hub.github.io) | 1 | 65 | 0 |
| [ClaudeDesk](https://github.com/dwj9ddyvf6-hub/ClaudeDesk) | 221 | 105,064 | 16 |
| [Silicon](https://github.com/dwj9ddyvf6-hub/Silicon) | 12 | 93,114 | 59 |
| [Edge](https://github.com/dwj9ddyvf6-hub/Edge) | 1 | 167 | 0 |
| [Test](https://github.com/dwj9ddyvf6-hub/Test) | 1 | 4,656 | 1 |
| [master-desk](https://github.com/dwj9ddyvf6-hub/master-desk) | 6 | 4,688 | 0 |
| [thestrat-ai-public-teardown](https://github.com/dwj9ddyvf6-hub/thestrat-ai-public-teardown) | 1 | 2 | 0 |

## Where the useful families live

- **galath-desk-backup:** Gestalt chart-reading method, holistic protocol, calibration, frameworks and live-read teaching; archive branches.
- **Agentic-Trading-Desk:** Tensor phenotype/gestalt tools, visual research doctrine, chart atlas and review corpus; research sleeves/MOSAIC PRs.
- **foliotend-chart-renderer:** Chart evidence synthesis, annotation rendering, visual study ledger and analyst rulebook.
- **quant-research-backup:** Repeated research/archive copies, CANDLES shape library, grand synthesis and extensive study/artifact branches.
- **quant-research-critical:** Chart perception thesis, Elliott studies, CHARTSLECTOR, Qulla thesis and canonical research.
- **Midna:** TA chart-read protocol, Ichimoku engine, embedded research corpus.
- **qullamaggie-research-pass3:** Primary-vs-inferred rule registry and Qulla setup modeling.
- **Femto-lean:** Chart-read and Elliott engines, calibration, Wyckoff, visual and indicator research; 115 branches.
- **ClaudeDesk:** Eyes visual-study protocols, model books/twins, perception exam, Echo archives; 221 archive branches.
- **Silicon:** Saty, ChartPrime, TheStrat, indicator and platform teardown instructional/source corpus.
- **Test:** Griffith anchored-VWAP pullback method.

The remaining repositories were discovered and mapped, not assumed to contain no relevant method. Shared branch trees, release lineage, infrastructure and operational copies require blob-level deduplication before prioritizing further reading. `github/repository_learning_map.json` retains the exact reviewed paths behind each family.

## Unread and unavailable surfaces

- **Release payloads:** 15 releases and 532 asset metadata entries were enumerated, totaling 109,352,230,702 declared bytes. Their names, URLs and sizes are metadata; the payloads were not read. The total includes general backups, data and encrypted archives, not exclusively TA.
- **LFS:** 12 pointer objects declare 4,118,021,724 underlying bytes. The pointer files and 11 distinct default-tree attribute blobs were inspected; the LFS payloads were not downloaded. These bookkeeping reads are not additional method lessons.
- **Archives and binaries:** seeing a ZIP, database, model or image path does not enumerate its nested contents. Binary-download limitations and encrypted material were not bypassed; an extracted counterpart is not presumed complete without a matching manifest.
- **Issues and pull requests:** all 33 issue collections were paged to termination: 57 items, comprising 42 issues and 15 PRs. Twelve broadly relevant PR collection bodies were read. Comments, review threads, patches and complete PR histories remain outside that read scope.
- **Unsupported endpoints:** the connector rejected generic tags and Actions-artifact collections as unsupported. Those endpoint families were stopped. Independent tag histories, Actions payloads, Discussions and wikis are unenumerated.
- **Substantive backlog:** the broad candidate inventory greatly exceeds completed semantic reading. Remaining method originals, inaccessible books/pages, ambiguous source settings, uninspected images and binary release contents remain explicit work, not a hidden claim of completion.

## Use the coverage to continue intelligently

Choose one learning question and its exact source family. Prefer a distinct unread substantive blob over another byte-identical copy. Recover original method definitions where a reconstruction leaves a rule ambiguous; inspect the actual chart when a text claim depends on geometry; obtain matching data when a price label needs measurement. Then add a new frozen practice example with a stated cutoff and evaluation rule.

This edition establishes a substantial working study and a reproducible discovery boundary. Continued learning should deepen specific skills and close documented gaps rather than turn the size of an inventory into a claim that every file was absorbed.