# Section 2: Structure and Levels

## What this section teaches

Structure is the skeleton of a chart. Levels are the places where that skeleton has already borne weight. Everything else in this playbook, patterns, divergences, entries, targets, hangs off these two things. A reader who cannot state the trend, name the swings that define it, and draw the two or three levels that actually decide the chart has nothing to attach a pattern to.

The method here is the desk method, assembled from named sources and stated so it can be run by eye on any chart. The core grammar comes from the Echo and Max playbook (PLAYBOOK_echo_max_2026-10-12.md, reverse engineered from 134 X charts): one question per chart, at most two trendlines, levels drawn as zones, the 50 day average as the actionable pivot and the 200 day average as the regime line. The executable form of the same grammar lives in the desk chart reader, chart_read.py in the Best Setups engine (Silicon, best-setups-engine branch, femto/core/chart_read.py): confirmed 5 bar fractal pivots, ATR scaled level clusters, dead trendlines reported rather than hidden, and buy zones built only from confluence. The local stock analysis skill (local-stock-analysis, Pass A geometry plus Pass B perceptual read) supplies the working discipline: pivots carry both an extreme time and an availability time, level tests are kind aware, and clusters are built as 2.5 ATR scaled pivot zones counted by independent episodes. The Echo Algorithm (ECHO-ALGORITHM.md, from the six Kit newsletter issues and the 240 chart X corpus) supplies the swing, confluence, and reaction rules in Echo's own published constants. The TA Deep Dive brief (quant-research-backup, research/ta-deep-dive/BRIEF.md) supplies the rigorous variants: convex hull trendlines with a break defined as a close at least 0.25 ATR beyond the line, and support and resistance zones built from pivot clusters, volume distribution, and round numbers. The x_charts annotation standard (quant-research-backup, cursor-shadow-rig/x_charts/README.md) supplies the finished chart: what a completed structure read must actually show.

Posture, stated once and used throughout: a level is not a trade. Price arriving at a level is an area to watch. The trade is the reaction at the level. That sentence is Echo's, from his newsletter issue How I Find Support (2026-09-07), and it governs every section below.

## 1. The reading order: structure before everything

Run this order on every chart, in this sequence, before naming any pattern or indicator. The local chart reading method (CHART_READING_METHOD.md in the composite-confidence corpus) sequences the eye the same way: whole before parts, context before pattern names.

1. Frame first. Name the timeframe, the span visible, and whether the scale is arithmetic or log. On a move of several hundred percent, switch to log scale or flag that arithmetic lines will mislead. The Echo Algorithm flags moves above 300 percent with a log scale advisory for exactly this reason.
2. Weekly regime first, daily structure second, intraday timing last. The weekly count governs, the daily times it (Echo and Max playbook). A daily shelf that contradicts the weekly regime is a trade location, not a regime call.
3. Trend in words. Uptrend, downtrend, range, or transition, with the swing sequence that proves it. Section 2 below gives the test.
4. Mark the swings. Only confirmed major swings. These are the anchors for everything else.
5. Build the level map. Horizontal zones first, then at most two trendlines, then the 50 and 200 averages, then anchored VWAP where an anchor event exists, then gaps left open. Rank the levels. Most charts have two or three that matter.
6. State the deciding level. Finish the sentence: this chart is decided at this zone, because these independent constructions meet there. If you cannot finish it, the chart is mid structure and the correct read is patience. Echo's mid structure call is exactly that: corrective, not buy time.
7. State both scenarios with prices. Primary path and alternate path, each with its trigger close and its terminus zone. A read without its own invalidation geometry is an opinion, not a read (Echo and Max playbook, point 5).

Calibration habit that belongs at the start, not the end: write the level map before you look at any indicator panel. Momentum panels confirm or arm a level. They never create one.

## 2. Trend: a definition a reader can apply by eye

### 2.1 The swing sequence test

Trend is a sequence of swing highs and swing lows. Nothing else is needed to define it, and nothing else can substitute for it.

- Uptrend: each successive swing high is higher than the prior swing high, and each successive swing low is higher than the prior swing low. Higher highs and higher lows, in that order, bar by bar through the pivots.
- Downtrend: lower highs and lower lows.
- Range: highs stall near one zone and lows hold near another, with no sustained progression in either direction. Highs and lows overlap heavily and the middle of the range is crossed repeatedly.
- Transition: one side of the sequence breaks while the other has not yet followed. Example: price makes a lower low after a run of higher lows, but has not yet made a lower high. Name it transition, not downtrend. The break of the last higher low is the first structural warning. The lower high that follows is the confirmation that sellers now control the sequence.

Apply it in three passes. First pass: cover the right half of the chart and read the left half's sequence aloud. Second pass: uncover and read the full sequence. Third pass: name the last three swing highs and last three swing lows with dates and prices. If you cannot name six pivots, you do not yet have a trend call. You have an impression.

### 2.2 The four questions that make the definition usable

1. Where is the most recent swing high, and is it above or below the one before it?
2. Where is the most recent swing low, and is it above or below the one before it?
3. Which swing, if broken on a close, changes the sequence? That price is the structure invalidation for the trend leg. In an uptrend it is the last higher low. In a downtrend it is the last lower high.
4. How mature is the sequence? A trend with two higher lows is young. A trend with six higher lows, each shallower, with highs extending less each time, is mature and tiring in its geometry even before it breaks. Maturity is read from the swings themselves: shortening advances, deepening pullbacks, and more time spent recovering old highs all say the sequence is working harder for less progress.

### 2.3 Trend on two timeframes

Read trend twice, once on the governing timeframe and once on the trading timeframe. The Echo grammar is explicit: the weekly count governs, the daily times it. Three combinations cover most charts:

- Weekly up, daily up: trend alignment. Pullbacks to daily levels are locations inside a governing advance.
- Weekly up, daily down: a correction inside a governing advance, until the weekly sequence breaks. The daily downtrend is real on its own frame and subordinate on the governing frame. Say both facts. Collapsing them into one word loses the trade location.
- Weekly range, daily trend: the daily trend is travelling between weekly zones. Its target is the far weekly zone, not open space. Size expectation to the width of the governing range.

Never average the two frames into a vague verdict. State each frame's sequence separately, then state which one governs the decision you are about to make.

### 2.4 What trend is not

- Trend is not the slope of a moving average alone. Averages summarise trend. Section 8 covers them as levels. If price is above a rising 50 day average but the swing sequence just printed a lower low and a lower high, the sequence wins the argument and the average is now a level being tested from below.
- Trend is not a single line. A trendline break warns. A swing break decides. See Section 5 for the division of labour.
- Trend is not direction of the last five bars. Minor swings inside a major sequence are texture. The Echo Algorithm makes this mechanical: structure pivots come from a coarse swing filter (its default is a 10 percent reversal for major anchors), and a fine filter is used only inside legs to read sub structure. By eye the rule is: choose the swing size that matches the pattern you are reading, and do not let a wave's own texture impersonate the wave.

## 3. Swing points: the anchors everything hangs from

### 3.1 What a swing point is

A swing high is a high that stands above the highs around it. A swing low is a low that stands below the lows around it. The desk standard, shared by Pass A and chart_read.py, is the confirmed 5 bar fractal: a high higher than the two bars on each side is a candidate, and in the stricter desk implementation a left 5, right 5 window is used for major pivots. The exact window matters less than the two disciplines that come with it.

First discipline: confirmation lag. A pivot is learned only when the bars to its right have printed. Pass A therefore records two times for every pivot: the extreme time, when the high or low occurred, and the availability time, when a reader could first know it was a pivot. Never draw a line, a Fibonacci tool, or a divergence from a pivot as if it was known at its extreme bar. That single honesty rule removes most repainting from hand reads.

Second discipline: wick to wick anchoring. Swings are measured from high to low, using extremes, never closes (Echo Algorithm, Step 1, his published rule). A Fibonacci retracement anchored on closes measures a different move from the one the chart actually travelled, and its zones will sit in the wrong places.

### 3.2 Two tiers of swings

Keep two tiers separate on the chart, as the Echo Algorithm does:

- Structure swings: the major highs and lows that span the pattern, often months apart on a daily chart. These anchor trendlines, Fibonacci tools, and horizontal zones. A working chart rarely needs more than four to six of them labelled.
- Texture swings: the smaller highs and lows inside each leg. These tell you whether a leg is impulsive or corrective in character, whether a pullback segments into three waves, and whether momentum is shortening. They inform the read. They do not anchor the main tools.

The most common beginner error is tier mixing: anchoring a trendline on one structure high and one texture high, then wondering why the line means nothing. If the two anchors are not the same kind of object, the line between them is decoration.

### 3.3 How to mark swings in practice

1. Start at the left edge and move right, marking only highs that exceed everything since the last marked low, and lows that undercut everything since the last marked high. This alternating pass gives a clean zigzag and prevents double marking one extreme.
2. Promote a swing to structure tier only if price travelled a meaningful distance from it, scaled by ATR, or if it turned price for a meaningful time. The desk pattern work uses ATR scaled significance throughout: a wiggle of a fraction of one ATR is not a swing, whatever the fractal window says.
3. Label each structure swing with date and price on the chart. The x_charts standard and the Best Setups chart law both require labelled anchors, because an unlabelled line cannot be checked later.
4. Leave dead swings visible but demoted. When a level is broken decisively, its swing stays on the chart as history and as a polarity candidate (Section 4.4). Deleting it erases the map you will need on the retest.

### 3.4 Swing failure as information

A failed swing attempt is itself a structure event. When price pushes above the prior swing high and closes back below it, or pushes below the prior swing low and closes back above it, the chart has printed a rejection at a known level. Record it as a test of that zone with outcome rejected (Section 10 gives the test ledger). Failed swings at the edge of a long range, after a climax, are the raw material of springs and upthrusts in the Wyckoff vocabulary carried inside chart_read.py. You do not need the full Wyckoff grammar to use the observation: an extreme that cannot hold a close beyond the prior extreme is a level defending itself.

## 4. Support and resistance as zones, not lines

### 4.1 Why zones

Price turns in areas, not at ticks. Different participants anchor on the high, the close, the round number, and the average, all near the same shelf, so reactions scatter across a band. Drawing a single line and demanding a tick perfect touch guarantees two errors: calling a good level broken because one wick crossed the line, and calling a level respected because one close happened to land on it. Every source in this section agrees on the correction. Echo draws buy zones and target zones as rectangles (Echo and Max playbook, point 3). The desk chart reader builds ATR scaled pivot clusters. ChartSchool, summarised in the companion identification section, teaches zones whenever the reaction points span a wide range or the level is old. The TA Deep Dive brief builds zones from three independent ingredients: pivot clusters, volume distribution, and round numbers.

### 4.2 How to build a zone, step by step

1. Collect the reaction points. Gather every structure swing high (for resistance) or swing low (for support) that sits near the same price area, plus any closes that stalled there. You are looking for a shelf: at least two independent reaction points. One touch is a level candidate. Two or more touches make it a shelf worth drawing.
2. Set the band edges from the points themselves. The top of a support zone is the highest of its reaction lows and closes. The bottom is the lowest extreme. Do not widen the band to include a distant outlier that belongs to a different episode.
3. Scale the band against ATR. Pass A builds level clusters as 2.5 ATR scaled pivot zones, and chart_read.py uses ATR bands for confluence for the same reason: a zone that is a fraction of one ATR wide on a volatile name and a zone that is three ATR wide are different objects. If your hand drawn band is far wider than about one ATR on the trading timeframe, you have probably merged two shelves. Split them.
4. Add the volume shelf if you have it. The Grok support and resistance system for SPY (grokbot-inbox summary in quant-research-backup, and sleeves/grok_sr_spy.py in the Test repo) builds zones from clustered swing pivots plus high volume nodes, ranked by touches and volume, in narrow price bands. The TA Deep Dive brief reaches the same construction with a volume density estimate. By eye: a price area where many sessions changed hands, visible as a thick shelf on a volume by price display or as a long sideways base on the price chart, belongs inside the zone even if its swing points are untidy. Price spent time there. Participants have positions there.
5. Add the round number only if it falls inside or beside the band. Round numbers attract orders and attention, and the desk confluence count credits them, but a round number alone, with no reaction points, is a watch level, not a zone.
6. Label the zone with its provenance. Example form: Support zone 61.74 to 67.47. Sources: 0.5 to 0.618 retracement band, 200 day average inside, prior pivot shelf from March. That is the CAVA construction from the Echo and Max playbook, and the label format is the point: anyone can check each claimed source on the chart.

### 4.3 Zone behaviour: the close decides

Judge a zone by closes, not wicks. The Echo Algorithm states it as a rule: zones are treated as zones, close not wick, and a wick through the zone does not kill it while a close below the zone's bottom does. Apply the same standard in both directions:

- Wick into the zone, close back outside it: the zone was tested and held on this attempt. The longer the wick relative to the bar's body, the stronger the rejection evidence.
- Close inside the zone: price is in the shelf. No verdict yet. The next closes decide whether the zone absorbs price or price is chewing through it.
- Close beyond the far edge of the zone: the zone has failed on a closing basis. Now polarity (Section 4.4) and the retest govern what happens next.
- Multiple closes inside the zone with shrinking range: absorption in progress. Each additional session spent inside the shelf spends its stored orders. A zone that has absorbed price for many sessions is weaker than its touch count suggests. Time inside a zone is consumption, not respect.

### 4.4 Polarity: broken levels flip

Broken resistance becomes support. Broken support becomes resistance. This is the single most reliable behaviour in level work, and every corpus here teaches it. The mechanism is positional: participants who bought at a shelf that broke are waiting to exit near breakeven on a return, and participants who missed the break are waiting to enter at the same price. Both groups place orders at the old level from the other side.

How to use it concretely:

1. When a zone breaks on a close, do not delete it. Relabel it with its flipped role and extend it forward.
2. Expect the retest. Name it in advance in the read: throwback after an upward break, pullback after a downward break. The retest is the highest information event in level work, because it tests the break with the other side in control.
3. Grade the retest. A retest that touches the flipped zone on falling volume and turns away on rising volume confirms the break (Echo's break, retest, bounce sequence in How I Find Support, taught on RDW and BABA). A retest that closes back through the zone negates the break and restores the old range. Write the grade on the chart.
4. Set invalidation against the flipped zone, not against empty space. A long taken on a retest of broken resistance holds while price holds above that zone. A close back below it is the defined failure.

### 4.5 Prior highs and lows: the shelf inventory

Prior extremes are the raw material of zones. Keep an inventory, in this priority order, and check price against it before consulting any computed tool:

- Prior day high and low, prior week high and low, prior month high and low. These are the session shelves every timeframe of participant watches. The Saty method (Saty ATR levels and pivot ribbon, in the REA teardown and the desk Saty sleeves) formalises the intraday version: pre planned levels drawn from prior structure and ATR fractions, read as a ladder price travels between. The habit transfers to any timeframe: yesterday's high is a level today whether or not you find it interesting.
- The base edges. The high and low of the most recent completed base or consolidation. A base is a range with a memory: its top is the last price sellers defended repeatedly, its bottom the last price buyers defended repeatedly. Patterns in the Test repo terminal reader (read/patterns.py) define bases by length and depth limits for this reason: the edges only mean something if the range was tight enough to be one shelf.
- Swing shelves from Section 3. The last structure high above price is the first resistance. The last structure low below price is the first support. The all time high and the multi year high carry extra weight because above them there is no overhead shelf at all, a condition worth stating plainly in a read: above this price, no prior resistance exists on this timeframe.
- Gap edges. An unfilled gap's two edges are prior extremes created by a jump. Section 6 treats them in full.
- The 52 week high and low and any widely published extreme. Widely watched levels gather orders because they are watched. Note them, but rank them below shelves with actual repeated reactions on your own chart.

For each shelf in the inventory, record the same four fields: price band, dates of the reactions, number of independent test episodes (Section 10.2), and current role (support, resistance, or flipped). That inventory, kept current, is most of a level map.

## 5. Trendlines and channels: drawing lines that mean something

### 5.1 The discipline in one paragraph

At most two trendlines on a chart (Echo and Max playbook, point 2; local-stock-analysis skill, same rule). Each line is anchored on confirmed major pivots spanning the whole pattern, months not wiggles. A line that price has already closed through decisively is dead: report it as broken, do not quietly redraw it to fit. If a pattern seems to need five lines, there is no pattern. This economy is not minimalism for style. It is what makes a line break falsifiable. With two lines, a break is an event. With nine lines, price is always breaking something and touching something else, and the chart can never be wrong.

### 5.2 How to draw a trendline, step by step

1. Choose the job first. A support trendline connects swing lows beneath an advance and answers: where does rising support meet price if the advance continues at this slope? A resistance trendline connects swing highs above a decline or across a corrective structure. Echo draws trendlines on the corrective structure specifically: a descending line across the two most recent countertrend highs, and a rising line across the base's higher lows (Echo and Max playbook, Echo section).
2. Anchor on the two most significant confirmed pivots of the correct tier and type. Wick extremes, consistently, for both anchors (Section 3.1). Never anchor one end on a wick and the other on a close to make the line prettier.
3. Extend the line forward without moving it. The extension is the hypothesis: if this slope governs, price meets the line at a future date at a computable price. That future meeting point is often the trade, because it is where line, zone, and time meet (Max's triangles are drawn exactly to locate that confluence point: NBIS, resistance from the top, support from the July low, apex as the decision).
4. Count validation honestly. Two points make a hypothesis. Three or more distinct touches make a validated line (chart_read.py states the same grades: 2 points hypothesis, 3 plus touches validated). A touch means price reached the line and turned, as a distinct episode, not three bars sliding along it.
5. Check the scale. On spans where price has moved two times or more, check the line on a semi log scale before trusting it (chart_read.py validation rule). Percentage slope is constant on log scale. A line that only fits on arithmetic scale across a multi year advance is fitting the scale, not the price.
6. Write the line's credentials on the chart: anchors with dates, touch count, and status (hypothesis, validated, broken). The Best Setups chart_spec.py enforces the labelling half of this in code: drawn lines carry their reader labels, Resistance line and Support line, where drawn, and an unlabelled fitted line is a defect.

### 5.3 What a break means, and what it does not

- A break is a close beyond the line, with distance. The TA Deep Dive brief quantifies it: a close at least 0.25 ATR beyond the line. chart_read.py uses the equivalent idea in its own terms: a line closed through decisively is dead. An intraday poke through a line that closes back on the governing side is a test, not a break, and often a rejection worth more than the line itself.
- A trendline break warns that the slope has changed. It does not by itself reverse the swing sequence. Price can break a rising support line and go sideways, building a range above the last higher low, which is transition (Section 2.1), not downtrend. Upgrade the call only when the swing sequence confirms: a lower low, then a lower high.
- Confirmation pairing: Echo's confirmation event is a close through the line plus the horizontal level together, for example a close through a descending corrective line and through the Fibonacci horizontal at the same shelf. A line break that also takes out a zone is a different class of event from a line break into open space. Always report which horizontal zone sits just beyond a broken line. That zone is where the break will be tested.
- Never resurrect a dead line by re anchoring it on newer pivots and presenting it as the same line. Draw the new line as a new hypothesis with its own anchors, and keep the dead line's break on the record. Serial redrawing is how a reader avoids ever being wrong, and the desk rule exists to forbid it.

### 5.4 Common drawing errors

- Anchoring on texture swings (Section 3.2) so the line spans two weeks inside a six month pattern.
- Cutting through bodies. A support line that slices through the bars it supposedly supports is misdrawn. Refit it to the extremes, or accept that no single slope fits and the structure is a range, not a tilted trend.
- Steepness blindness. Very steep lines break quickly and carry little weight. A line governing price for months at a moderate slope outranks a line governing price for days at a near vertical slope, even if the steep line has more touches.
- Fan drawing. A fan of three or more near parallel lines is a refusal to choose. Keep the line with the most distinct touches and the smallest misses, delete the rest, and say why you kept it.

### 5.5 Channels

A channel is a trendline plus a parallel return line through the opposite extremes. It adds one piece of information the single line cannot give: the width of the trend's travel, and therefore where the far side of a healthy move sits.

Drawing protocol:

1. Establish the main line first, by the full protocol above, on at least two confirmed pivots.
2. Place the parallel line on the most significant opposite extreme between or beyond those anchors. One anchor for the return line is acceptable to place it, and the line stays provisional until a second touch validates it, the same grading as any line.
3. Require travel. Price must cross the channel from side to side and nearly fill it. Two lines drawn around price that hugs one edge are a trendline plus a guess, not a channel.
4. Read the midline with respect and without superstition. Price that repeatedly turns near the channel middle is telling you the width is right. State it as an observation from touches, never as a law.

Using a channel:

- Trade location with the slope. In a rising channel, the support line is the location shelf and the return line is the measured objective area. In a falling channel, mirror it. A close outside the channel on the trendline side is the exit signal for a channel read and the start of a new structure question. A close outside on the return line side is acceleration: the slope has steepened, and the channel, not the trend, is what failed.
- The mechanical cousin is worth knowing: a Donchian channel (Test repo Donchian family, including the 55 day Turtle form) draws its lines at the highest high and lowest low of a fixed window, no anchor judgment at all. Comparing your hand drawn channel with the Donchian edges teaches you what your anchor choices are adding. If your channel and the Donchian channel tell different stories, the difference is your judgment, and you should be able to defend it pivot by pivot.
- Channels are structure, not statistics. The companion identification section records Bulkowski's honesty on this point: no performance statistics are published for channels. Draw them for location and invalidation, and let zones and closes do the deciding.

## 6. Gaps: levels created by a jump

### 6.1 What a gap is, exactly

An up gap: today's low is above yesterday's high. A down gap: today's high is below yesterday's low. Between the two extremes is a price band where no trade occurred. That empty band is a level object with two edges, and it behaves like a zone on any return (x_charts draws unfilled gaps as a standing layer, and ChartsLector's Pine tools include unfilled gaps for the same reason).

### 6.2 The four gap types, identified by location and volume

Classification is by where the gap occurs and what volume does, in that order:

1. Common gap. Inside a trading range or congestion area. No change in structure. Tends to fill, because the range it sits inside is still the governing structure. Mark it, expect the fill, build nothing on it.
2. Breakaway gap. Gaps out of a base, a range, or a completed pattern, on above average volume. This gap is a break that arrived by jump. Its near edge becomes the polarity shelf: for an up breakaway gap, the bottom of the gap and the top of the prior range are now the support zone a retest must hold. A breakaway gap that stays open while price advances is structure confirming itself.
3. Runaway or measuring gap. In the direction of an established trend, near the middle of the move, sometimes in a series. Its measuring use is a projection: the distance travelled before the gap, projected forward from the gap, estimates the second half. Treat that projection like every measured move in this playbook: a guide that must yield to the next real zone in its path.
4. Exhaustion gap. In the trend direction at the end of an extended move, on climactic volume, followed promptly by reversal and a fill. You cannot finally separate exhaustion from runaway on the gap day. Write the candidate label and its test on the chart: fills within days and price reverses, exhaustion. Holds open and trend continues, runaway. The following sessions complete the identification.

### 6.3 How to work a gap as a level

1. Draw the gap as a band, both edges labelled with prices and the gap date, and extend it forward until it fills or is superseded.
2. On a return into the gap, expect reaction at the near edge first. Partial fills that turn at the near edge or near the middle are the gap defending itself. A close through the far edge fills the gap and negates its support or resistance claim. Update the label rather than defending the old read.
3. Note the gap's role in the level map. A breakaway gap whose near edge coincides with a prior shelf and a moving average is confluence (Section 10), and it upgrades the whole shelf. A gap sitting alone in open space is a weaker level than its drama suggests.
4. Retire the slogan that all gaps fill. Common and exhaustion gaps fill as part of their definition. Breakaway and runaway gaps are defined in part by not filling promptly. The desk weekly gaps study (quant-research-backup, cursor-shadow-rig/WEEKLY_GAPS) exists because weekly gaps, the larger timeframe version, repay the same discipline: classify by location, track the fill as an event with a date, and reconcile earlier labels when behaviour contradicts them.

Intraday note: the same geometry applies to opening gaps on intraday charts, where the opening range and the gap edges together frame the session's first decision. The opening range breakout family (Test repo, teddy_orb_spy and the Milkman ORB card) is the systematic form: the range defines the lines, a decisive close beyond them is the trigger, and a close back inside is the invalidation.

## 7. Moving averages as dynamic levels: the Echo grammar

### 7.1 Geography, not signals

Echo uses only two averages, and the playbook states their roles in one sentence each: the 50 period average is the actionable pivot, the 200 period average is the regime line and final backstop (Echo and Max playbook, point 4). Max draws the same pair on every chart, green 50, red 200, with volume below and momentum above (Max template in the playbook). Neither analyst treats a cross as a signal. The averages are geography: moving shelves that price travels between, tests, reclaims, and loses.

Echo's newsletter states the principle behind the pair: he uses the 50 and 200 on daily, weekly, and monthly frames, the longer the period and the higher the timeframe the stronger the level and the more attention it deserves, and a 200 week average carries far more weight than a 50 day (How I Find Support). A moving average is a level whose authority comes from how many participants, over how long a window, measure their average cost or their regime against it.

### 7.2 The 50: the actionable pivot

- Price above a rising 50, pullbacks holding at or above it: the advance has a working floor. The 50 is the first dynamic support and the shelf pullbacks are expected to respect.
- Reclaim as trigger. Max's trigger discipline is the canonical form: 50 average reclaim equals entry, needs to stay above the 50, below the 50 equals danger of a melt to the next shelf. Echo's version is identical in structure: starters are allowed at a deep zone, full size waits for the average flip, buys when averages are reclaimed. The reclaim is a close back above the 50 after a period below it, ideally followed by a low volume retest of the average from above and a bounce on returning volume (Echo's break, retest, bounce sequence, Section 7.4).
- Loss as danger. A decisive close below the 50, especially a close below it that also loses a horizontal zone, downgrades the chart from advance to correction or transition. Name the next shelf below at the moment of the loss. Max's BTC form of the sentence is the template: below the 50, melts to the named next level.
- The 50 as resistance. Averages cut both ways (Echo, How I Find Support). A declining 50 above price is dynamic resistance: rallies travel to it and are judged there. A rally that reaches the underside of a falling 50 and rejects is the mirror of a pullback holding at a rising 50, and it grades the downtrend as intact.

### 7.3 The 200: the regime line

- Regime definition. Sustained trade above the 200 day or 200 week average is a bull regime for that timeframe. Sustained trade below it is a bear regime. One close across the line is a test. A retest that holds from the new side is the regime change confirming itself, by the same break and retest grammar as any zone (Section 4.4).
- Final backstop. In Echo's buy zone construction, the 200 printing inside a Fibonacci band is what promotes a support test into a buy zone (CAVA: the 0.5 to 0.618 band sitting exactly on the 200 day average). The 200 week average is his deepest backstop: the stop for his generational bottom trades sits below the zone and below the 200 week average, stated in the post.
- Tests accumulate authority. BABA in Echo's newsletter retested its 200 day average several times, with a substantial move following every touch. His rule: the more times a support level is tested and holds, the stronger it gets, and the same applies to resistance. Section 10 qualifies this with the absorption warning: tests that hold with decisive reactions add authority, while long residence inside a level spends it. The distinction is reaction quality, not touch count alone.
- Slope matters. A rising 200 far below price is a distant backstop, not a near level. A flat 200 that price crosses repeatedly is telling you the timeframe is in a range regime, and the average in that condition is a magnet and a mean, not a floor. Read the average's slope and price's distance from it, in ATR, before assigning it a role in today's map.

### 7.4 The break, retest, bounce sequence: how any dynamic level is traded

Echo teaches one sequence for averages, and it generalises to every level in this section. Learn it once, on averages, and apply it everywhere:

1. Break. Price closes beyond the level in the new direction, on expanding volume for the break to carry weight.
2. Retest. Price returns to the level from the new side, on falling volume. The retest is low volume by definition in this grammar. A high volume return is not a retest, it is a counterattack.
3. Bounce. Price turns at the level with returning volume and a decisive candle: an engulfing or hammer at the level in Echo's checklist, plus reclaiming the shorter averages.
4. Action. Buy the reaction, size into strength. Where you are wrong is stated in advance: a decisive close back beyond the level on volume. Cut and wait for the next one.

Echo adds the honest footnote every master keeps: the retest does not always come. The choice is explicit. Wait for the confirmed retest and miss the names that never retest, or take a small starter on the break when confluences stack and add heavily on the retest. Either is a complete plan. Chasing the break at full size with no retest rule is not.

### 7.5 Average clusters and the confluence rule for averages

A single average at a zone is one witness. A cluster, the 50 and 200 near each other, or a daily average and a weekly average printing at nearly the same price, is a shelf with multiple independent measurement windows agreeing. Echo's rule from the playbook: a Fibonacci zone only becomes a buy zone when an average cluster or a trendline confirms the same shelf. Zones without that confluence are support tests, not buys. When you score confluence in Section 10, count an average cluster as one strong construction, not as two separate ones: the 50 and the 200 are correlated witnesses when they sit together, because both are averages of the same closes.

Shorter averages have one defined job in this grammar. The 9 and 21 exponential averages are reaction gauges, not levels: Echo's reaction test includes a close back above the 9 and 21 after touching a zone (Echo Algorithm, Step 6), and the Echo swing rules in the Test repo (cursor-shadow-rig-echo-swing) add only at support defined in part by proximity to the 21 day exponential average. Use them to judge whether a reaction is underway. Do not draw them as shelves and do not build zones on them.

## 8. Anchored VWAP: the average that starts at an event

### 8.1 What anchored VWAP is

Ordinary VWAP restarts every session: the volume weighted average price of the day, a fair value line for that session alone. Anchored VWAP, AVWAP, starts its accumulation at a chosen event bar and runs forward: the volume weighted average price paid by everyone who traded since that event. The x_charts annotation standard includes AVWAP as a standing drawn layer alongside the exponential averages, and the desk EMA VWAP sleeves (Test repo ema_vwap family, and femto-lean ema_vwap.py) trade VWAP as a level with the same reclaim and loss grammar as the averages above. Session VWAP and anchored VWAP answer different questions. Session VWAP asks where today's fair value is. AVWAP asks where the participants in this move, from its defining event, break even on average.

That break even property is what makes AVWAP a level rather than a statistic. Anchored from a major low, the line approximates the average cost of everyone who bought the advance. While price holds above it, the average participant in the move is in profit and pullbacks meet holders with a cushion. When price loses it, the average participant is underwater, and the line flips to resistance by the same polarity logic as Section 4.4.

### 8.2 Choosing the anchor: the event is the method

An AVWAP is only as meaningful as its anchor. Arbitrary anchors produce arbitrary lines. Use anchors that mark a genuine change in who owns the stock or what the stock is worth:

- A major structure swing low (for an advance) or swing high (for a decline). The line then tracks the average cost of the whole current leg.
- An earnings release or other repricing event bar. The line tracks everyone who traded the new information.
- A breakout bar from a completed base, or the high volume capitulation bar at a low. The line tracks the post base or post climax population.
- A gap bar. The line tracks the post gap population, and pairs naturally with the gap band from Section 6.

Rules: one or two anchors per chart, each labelled with its event and date. An AVWAP whose anchor you cannot name in five words is not a level, it is curve fitting. When two anchors from different genuine events produce lines that converge at nearly the same price, that convergence is confluence, counted in Section 10.

### 8.3 Reading AVWAP in practice

1. Trend location. Price above a rising AVWAP from the leg's low: the leg's participants are in profit, pullbacks to the line are the dynamic location shelf for that leg, analogous to the 50's role but specific to this move rather than to a fixed window.
2. The test. A pullback that tags AVWAP and turns, with the same reaction evidence required at any level (decisive candle, returning volume, close back in the direction of the leg), confirms the line is being defended. A close through it on volume says the leg's average holder is now losing, and the burden of proof shifts.
3. Deviation as context. Distance from AVWAP, measured in ATR or in the line's own deviation bands where drawn, tells you how stretched a move is from its own participants' average. Extensions far above AVWAP after a vertical run describe a move whose late buyers are far from the average cost of the move: a location warning, not a timing signal. The trade decision still waits for a level reaction or a structure break.
4. Timeframe honesty. AVWAP inherits its anchor's timeframe. An AVWAP anchored on a daily earnings bar is a daily level. Do not import it onto an intraday chart and trade its touches as if they were session levels. Session VWAP governs the session. Anchored lines govern the move they are anchored to.

## 9. How levels gain authority: tests, time, and confluence

### 9.1 The authority ledger

A level's authority is earned in public, on the chart, in four currencies. Score every candidate level against all four before ranking it:

1. Reactions. How many times has price turned at this zone, and how decisively? A level that produced a 20 percent advance carries more authority than a level that produced three 2 percent bounces. Measure reaction size in ATR so volatile and quiet names grade on the same ruler.
2. Independent episodes. Episodes, not touches. Pass A counts level tests against independent episodes because three touches inside one week, in one approach, are one test of the level spread over three bars, not three separate proofs. A level tested in March, forgotten for two months, and tested again in May has two episodes. That second, separated test is worth more than the last three bars of the first test combined.
3. Timeframe and age. A weekly shelf tested over two years outranks a daily shelf tested over two weeks. Higher timeframe shelves govern: when a daily level and a weekly level conflict, the weekly one frames the expectation and the daily one times the entry.
4. Volume at the level. Reactions on expanding volume at the turn, and quiet approaches into the level, grade a test up. The chart reader's volume rule is that volume acts as a falsifier: contraction inside a pattern and expansion on its resolution is the healthy script, and volume that contradicts the script caps the read (chart_read.py volume grammar; Echo's volume checklist in How I Find Support: capitulation spike into a low counts for a bottom test, volume drying into support counts for exhaustion, volume returning on the bounce is required for the reaction).

One honest measurement belongs in every student's notebook here. In the desk AI 50 pattern study recorded in the grokbot inbox (quant-research-backup), support and resistance first touches rejected price 65.1 percent of the time on daily charts, the strongest single result in that study. First touches are powerful precisely because the level is unspent. That number is a prior for humility in both directions: a first touch deserves respect, and a level on its fourth or fifth approach deserves suspicion, because each approach consumes the orders resting there. Authority rises with proven reactions and falls with prolonged residence and repeated unproductive testing. Hold both halves at once: tested and held, stronger. Tested and lingered in, weaker.

### 9.2 Confluence: independent constructions agreeing

Confluence is the desk's central level concept, and its definition is strict: independent constructions, built by different methods from different inputs, landing in the same price band. The desk confluence engine (quant-research-backup, cursor-shadow-rig/x_charts/confluence.py) builds the support band exactly this way, listing each contributor on the chart: prior low, round number, average, Fibonacci of the larger range, clustered pivots. The Echo Algorithm requires at least two Fibonacci constructions in the same zone before calling it high probability, and then asks what else is there: an average, a trendline, old support (Step 4 and the Step 9 checklist). chart_read.py states the output grades: a confluence zone, where several constructions agree inside one ATR band, is a buy zone candidate, while a lone level is only a watch level.

Score a zone like this, in writing, one line per construction with its price:

- Fibonacci retracement band of a named swing (anchors, dates, and prices stated; see the Fibonacci section of this playbook for tool discipline).
- A second Fibonacci construction from a different swing or degree landing in the same band. Two tools, two prices, one band is Echo's high probability test.
- The 50 or 200 average, or an average cluster, printing inside the band (Section 7.5: a cluster counts once, strongly).
- A prior pivot shelf with at least two reaction points inside the band (Section 4.5).
- A trendline arriving at the band at the relevant date (Section 5). Time confluence: the line reaches the zone when price does.
- Anchored VWAP from a genuine event printing inside the band (Section 8).
- A gap edge or a base edge inside the band.
- A round number inside the band (weakest witness, never sufficient alone).

Counting rules that keep the score honest:

- Correlated witnesses count once. The 50 average and a Fibonacci band derived from a swing whose high the average also tracks are not fully independent. When in doubt, count the construction that was built from different data: pivots versus averages versus volume nodes versus time.
- Distance is measured in ATR. Constructions within roughly one ATR band of each other are confluent. Constructions two ATR apart are two levels, and pretending they are one zone widens your stop and falsifies your risk.
- Provenance is printed. Every construction in the stack is listed with its own price, as the x_charts confluence layer does on the chart. A score without the list is a claim. A list that a second reader can verify on the chart is evidence.

### 9.3 From level to trade: the reaction rule

The stack promotes a price area through three grades. Use these words exactly, as the Echo Algorithm does (Step 6 and Step 8):

- WATCH: a zone is identified and scored, but price has not reacted. No position logic beyond a possible small starter at the zone when the stack is exceptional, sized as a starter, with the starter's loss defined in advance.
- SETUP: price has reacted at the zone on closes: a bullish engulfing or hammer at the zone, or a close back above the short averages after touching the zone, with bounce volume above the pullback's average volume. The invalidation is the zone's far edge on a close, or the structure invalidation below it (for Echo impulse entries, the start of the move: a full retracement kills the count and the trade together).
- No trade: the zone failed on a close, or the reaction never came and price left without you. Both are complete outcomes. The second one, the missed move, is the tuition this method charges in exchange for never buying a level blind.

Targets come from the level map, not from hope: the next zone above is the first objective area, the zone beyond it the second, with any measured move or Fibonacci extension checked against those shelves and subordinated to them. Risk is the distance from entry to invalidation. The Best Setups call discipline states the board rule that follows: reward to risk is computed to the final objective, reward to the first target is shown, and a call whose reward to risk is below 1 never boards. A beautiful zone with the next shelf sitting immediately overhead is a bad trade location, and the map tells you so before you enter.

## 10. The level ledger and the worked sequence

### 10.1 Keep a ledger for every chart you read seriously

For each level on the map, one row:

| Field | What to write |
|---|---|
| Role | Support, resistance, or flipped, with the date of any flip |
| Band | Top and bottom prices of the zone |
| Constructions | Each independent source with its own price |
| Episodes | Number of independent test episodes, with dates |
| Last test | Date, approach volume, reaction (turned, absorbed, failed), reaction size in ATR |
| Status | Watch, setup (reacted), broken, or spent |
| Decides what | The sentence this level settles if it breaks or holds |

Update the ledger on closes, not intraday. A ledger kept this way turns a folder of old reads into calibration material: you can grade whether your zone construction, your break calls, and your reaction judgments were right, level by level, instead of grading only whether the stock went up.

### 10.2 The full sequence on one chart, start to finish

1. Set the frame. Daily chart, log scale checked, weekly chart open beside it.
2. State both trends in swing words (Section 2), weekly first.
3. Mark structure swings, wick to wick, with dates and prices. Confirm each pivot was knowable when you claim it (Section 3.1).
4. Build horizontal zones from the shelf inventory: prior week and month extremes, base edges, structure shelves, open gaps (Sections 4 and 6).
5. Draw at most two trendlines from structure pivots. Label anchors and touch counts. Mark any dead line as broken, with its break date (Section 5).
6. Add the 50 and 200 in the Echo roles. Note slope, price distance in ATR, and any cluster (Section 7).
7. Add AVWAP only from a named event anchor, labelled (Section 8).
8. Score every zone for confluence with the one line per construction list. Promote only confluent zones to decision levels (Section 9.2).
9. Name the deciding level and write both scenarios: primary and alternate, each with trigger close, target zones in order, and invalidation close (Section 1, step 7).
10. Wait for the reaction or the break. Act on the close that the plan names, at the size the stack and the risk distance justify. Journal the outcome against the ledger row, not against your memory.

### 10.3 Calibration drills for structure and levels

Mastery here is a drawing accuracy problem, and it trains like one:

- Blind level drill. Take historical charts cut off at a random date, from the desk blind calibration sets where available. Draw the full level map and the deciding level, commit it in writing, then reveal the following 20 and 60 sessions and grade the map: did price react at your zones, did your break calls hold, did your deciding level actually decide? The desk composite confidence calibration programme runs exactly this protocol and keeps scorecards and autopsies, which is why its failure lessons (vague neutral leans, confidence without a named level) are worth rereading before your own drills.
- Redraw drill. Read the same chart fresh one week later without looking at your prior map. Diff the two maps line by line. Every line that moved needs a reason that is a new pivot or a break, not a preference. Lines that move without events are the reader fitting the conclusion.
- One level post mortem. After any notable move, ask which single level, visible in advance, best explained the turn or the acceleration. If the answer is a level you did not draw, find the construction you missed and add its check to your sequence. If the answer is a level you drew and dismissed, find why your scoring demoted it. Both errors are curriculum.

## Section checklist: structure and levels

Before calling any chart read complete, confirm each row in writing:

- Trend stated per timeframe as a swing sequence, with the structure invalidation price named.
- Structure swings marked wick to wick, confirmation lag respected, texture swings not used as tool anchors.
- Every level drawn as a zone with band edges from its own reaction points, scaled against ATR.
- Polarity applied: broken zones relabelled and extended, retests named in advance.
- Trendlines at most two, anchored on confirmed structure pivots, touch counts stated, dead lines marked dead.
- Channels, if drawn, validated by travel between the lines, with the return line's provisional status stated.
- Open gaps drawn as bands, classified by location and volume, with the fill test written for any exhaustion candidate.
- 50 read as the actionable pivot, 200 as the regime line, both with slope and distance noted. Reclaim and loss language stated as closes, with the next shelf named.
- AVWAP present only with a named event anchor, and read as the move's average cost line.
- Confluence scored as a printed list of independent constructions with prices, correlated witnesses counted once, lone levels graded as watch only.
- Deciding level named, both scenarios drawn with trigger, targets from the level map, and invalidation.
- Reaction rule respected: level identified is watch, reaction on closes is setup, close through the far edge is failure.

Sources for this section: PLAYBOOK_echo_max_2026-10-12.md (Echo and Max grammar); Echo newsletter How I Find Support, 2026-09-07 (averages, break and retest sequence, reaction rule); ECHO-ALGORITHM.md Steps 1, 4, 6, 8, 9 (swings, confluence minimums, reaction, checklist); femto/core/chart_read.py and chart_spec.py, Best Setups engine (pivots, clusters, trendline grades, dead lines, labelling); local-stock-analysis skill Pass A and Pass B (pivot availability, 2.5 ATR clusters, episode counting, max two trendlines); research/ta-deep-dive/BRIEF.md, quant-research-backup (0.25 ATR trendline break, zones from clusters, volume, round numbers); cursor-shadow-rig/x_charts README, render_chart.py, and confluence.py (annotation layers, AVWAP, confluence band construction); sleeves/grok_sr_spy.py and the thiccteddy and Grok SPY support and resistance summary (zones from pivot clusters and volume nodes); Test repo terminal read/levels.py, lines.py, structure.py, pivots.py, patterns.py and the Donchian and Saty families (mechanical levels, base edges, ATR ladders); desk pattern calibration and composite confidence calibration scorecards (grading maps against outcomes).
