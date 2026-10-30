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
