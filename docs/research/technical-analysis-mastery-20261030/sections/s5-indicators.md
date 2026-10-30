# Section 5: Indicators as Servants of the Eye

## The doctrine

Read price first. Read indicators second, and only to answer a question price has already raised.

That order is the whole section. In the Echo and Max playbook (PLAYBOOK_echo_max_2026-10-12.md, from 134 X charts) the chart answers one question before any pane is quoted: where are we in the cycle, and what single level decides it. The local stock analysis skill states the same rule as procedure: name the cycle position first, covering impulse leg, correction leg, terminal pattern or base, and let the lean follow from that position. Divergence is counted only at pattern extremes. Volume is given as the tell that can falsify or cap conviction. Everything else in this section is an application of those three sentences.

An indicator is a servant in three specific jobs:

1. **Confirmation.** Price has reached a level, formed a shape, or broken a line. The indicator says whether momentum and participation agree with what the eye thinks it sees.
2. **Contradiction.** Price looks fine and the indicator does not. That disagreement does not create a trade in the opposite direction. It lowers conviction, tightens what counts as confirmation, and forces the reader to name the level that would settle the argument.
3. **Timing inside a level.** Price is already at a buy zone built from confluence. The indicator helps judge whether the reaction at that zone is real: a bounce on rising volume, an RSI turn from a divergent low, a MACD histogram that has stopped contracting.

An indicator never does these jobs: it never creates a level, never replaces a pattern, never turns a mid-structure chart into a setup, and never overrides a broken invalidation. If you remove every pane and the read collapses, there was no read. There was only a pane.

The Best Setups chart law makes the doctrine visible. Every finished setup chart carries price with its buy zone, invalidation, targets labelled by role, the named pattern itself, and a dashed expected path into reserved future space, and only then, underneath, volume, RSI and MACD panes, with divergences drawn only where the record carries them (Silicon census: femto/core/setup_brief.py; Terminal census: Femto Setup Charts library, 233 PNGs across 27 tickers). The panes are part of the standard. They are also placed last, smallest, and under a rule that forbids inventing a divergence to fill the space. Learn to draw your own charts in that order, even on paper: structure, levels, plan, then panes.

### The reading order for this section

Use this sequence on every chart, in this order, until it is automatic:

1. Cycle position and structure, from price alone.
2. Key level or zone, with its confluence count.
3. Volume: what participation did inside the structure and at the level.
4. Relative strength line against the index: is this name leading, following, or lagging the market it lives in.
5. RSI: momentum context first, divergence second, and divergence only at an extreme.
6. MACD: trend regime and momentum confirmation, in that order.
7. Breadth and market context: what the wider tape permits this single name to claim.
8. Verdict in conditional language, with trigger and invalidation named in advance, in the Echo and Max grammar: losing a named level confirms a move to a named zone; patience when price is mid-structure.

Steps 3 to 7 can each veto or cap the read. None of them can promote a chart that failed steps 1 and 2.

## 1. Volume first

Volume is the first servant because it is the closest to price itself. It is not an oscillator derived from closes. It is a count of what actually changed hands, bar by bar. The Wyckoff tradition in the census (external canon: ChartSchool Wyckoff Method) states it as a law: volume is effort, price spread and close location are result. Harmony between effort and result means the move is genuine. Divergence between them, heavy volume with narrow spread and little progress, is absorption by the other side and the earliest warning of a turn. Every volume tell below is that law applied at a different place in a structure.

Practical setup: plot volume under price, with a 20-session average line through it. The desk calibration work uses that same baseline: volume confirmation in the pattern census is defined as signal-session volume at or above its own 20-session average, and the stronger breakout test in the terminal read engine (Test census: read/volume.py and read/patterns.py) requires 1.4 times average on the break. Keep two numbers in mind while you read: the ratio of today's bar to the 20-session average, and the trend of volume inside the pattern, rising, falling, or flat. The ratio judges a single bar. The trend judges the whole structure.

Data discipline matters here. Desk law from the operating record: hourly and finer volume from Yahoo is corrupt and disqualified; volume work on hourly or finer bars uses Alpaca SIP only. On daily bars, use split-adjusted data from a single consistent source, and say so when you quote a ratio. A volume tell built on bad volume is not a tell.

### 1.1 Accumulation and distribution tells, read bar by bar

Forget the labels for a moment and read the sequence. Inside any base or top, sort the bars into up bars and down bars and compare their volume and their closes.

Signs that favour accumulation inside a base:

* Down bars shrink as the base develops. Each test of the low prints on less volume than the test before it. Sellers are spending more effort for less result.
* Up bars expand first. The earliest sign of strength inside a range is not the breakout. It is an up bar that travels wider, closes in its upper half, and prints clearly above-average volume, while the following down bar gives back little ground on light volume. In Wyckoff vocabulary this is a Sign of Strength followed by a Last Point of Support that holds.
* Closes migrate. The Accumulation and Distribution Line logic in the canon captures this mechanically: the Money Flow Multiplier is positive when the close sits in the upper half of the range, negative when it sits in the lower half. You do not need the line to use the idea. Watch where closes sit, session after session. A base whose closes creep from the lower half to the upper half is changing hands in a different way than a base whose closes stay pinned to the lows.
* On-Balance Volume leads quietly. OBV is cumulative and can trend while price ranges. An OBV line that makes a new high while price is still inside the base is the volume version of a relative strength line breaking out early, covered later in this section. Treat it as one confirming witness, not as proof on its own.

Signs that favour distribution inside a top:

* Up bars need more and more volume to gain less and less ground. Wide effort, narrow result, closes slipping toward the middle of the range.
* Down bars expand first. The ChartSchool Wyckoff account of the 2007 Dow top names the tell plainly: inside the topping range, down-day volume began exceeding up-day volume before price broke. Learn to see that flip inside the range, not after the break.
* Rallies die on volume. Price returns to the prior high on heavy volume and closes poorly. That is supply meeting demand at the same price, in size. Compare it with the first advance to that high, which should have closed strongly on its volume.

How to practise this: take any completed base from the Femto setup chart library and cover the right half. Read only the volume inside the left half, bar by bar, and write one sentence: who is winning inside this range, buyers or sellers, and which three bars prove it. Then uncover and check whether the eventual break agreed with your sentence. That drill, repeated, is how accumulation and distribution stop being story words and become a reading skill. The local stock analysis skill enforces the honest version of this language: describe what price and volume did in verifiable words, and do not claim hidden actors that OHLCV cannot prove. You are reading effort and result, not minds.

### 1.2 Climax volume

A climax is volume so far beyond the recent norm that it marks exhaustion of the current push, in either direction. It is a location tool, not a direction tool. Climax volume at the end of a long decline and climax volume at the end of a long advance are the same bar shape with opposite implications, and both need the price action that follows to complete the read.

Selling climax, at a low:

* The bar, or tight cluster of bars, prints the largest volume in the structure, often two to three times the 20-session average or more, on a wide spread down, and then closes well off the low. In the Wyckoff schematic this is the SC, the Selling Climax, preceded by Preliminary Support where spreads first widen on increased volume inside the downtrend.
* The tell that matters most comes next: the Automatic Rally sets the top of the new range, and the Secondary Test revisits the climax area on narrower spread and clearly decreased volume, holding at or above the climax low. A test on climax-level volume again is not a test. It is a continuation.
* The terminal read engine in the Test repo carries this as graded code (read/wyckoff.py and read/wyckoff_phase.py: spring, upthrust, climax, Sign of Strength judged against a tested trading range, with evidence grades). Use the grades as a self-check: name the phase, name the event, and name the volume evidence for each. If you cannot name the evidence, you do not have the phase.

Buying climax, at a high:

* The mirror: a sharp advance on heavy volume met by selling, a wide bar that closes in the middle or lower half, followed by an Automatic Reaction down. Volume stays high but progress stops. That stall, effort without result at new highs, is the climax.
* Exhaustion gaps belong in this family (external canon, ChartSchool gaps): a gap in the trend direction late in an extended move, on exceptionally high volume, that fills quickly when price reverses. The discriminator against a runaway gap is exactly the combination of climax volume and a fast fill.

What the reader does next at any climax: nothing aggressive on the climax bar itself. Mark the climax low or high as the boundary of a new range, mark the reaction high or low as the other boundary, and let the tests of those boundaries, on their volume, tell you whether a base or a top is building. The climax tells you the old move spent itself. The range that follows tells you what replaces it.

### 1.3 Volume dry-up in bases

If climax is the loudest volume signal, dry-up is the most useful quiet one. A base that is nearly ready has a recognisable volume shape: volume contracts as the base matures, pullbacks inside the base get progressively lighter, and the final approach to the pivot is often the quietest trading in the whole structure.

Read it in three places:

* **Across the whole base.** Volume should trend down from the left side to the right side in a healthy cup, flat base, or volatility contraction. Bulkowski's descending triangle work in the census puts a number on the general principle: volume recedes 78 percent of the time inside the pattern and is quite low just before the breakout. Triangles, wedges and flags share the script in the ChartSchool canon: contract inside the consolidation, expand on resolution. A base whose volume rises steadily toward the right side is not tightening. It is churning, and churn at lows or highs deserves a different, more cautious read.
* **On the pullbacks inside the base.** In the Echo Algorithm (ECHO-ALGORITHM.md, Step 5, volume grammar), the test is explicit: pullback-leg mean volume is compared with impulse-leg mean volume. Falling volume into the zone means sellers are exhausting. A pullback whose mean volume equals or exceeds the impulse leg's mean volume fires the VOLUME WRONG trap sign in Step 7, and two or more trap signs reclassify the whole apparent continuation as a trap. Steal that comparison for all base reading, not only Elliott work: every decline inside a structure gets compared, in average volume, with the advance that preceded it.
* **At the pivot.** The ChartsLector and Minervini traditions inventoried in the X census prize the same detail the desk does: the tightest, quietest area right before the pivot, the final contraction printing the lowest volume in the base, sometimes the lowest in months. When you annotate a base, mark the dry-up point by name and date. It is evidence the supply that created the base has been absorbed, and it is the detail that separates a base you watch from a base you prepare to act on.

Dry-up also disciplines patience. A base with no dry-up anywhere is not finished merely because its shape looks complete. Shape without the volume script is a drawing. Shape with the volume script is a structure.

### 1.4 Volume on the breakout

The breakout is where volume stops being background and becomes the verdict. The local stock analysis protocol gives volume the formal role: give the volume verdict as the tell and let it falsify or cap conviction. Work it as a checklist at the moment of the break:

* **Expansion.** The breakout bar should expand clearly over its average. The terminal read engine's standard is 1.4 times average volume for a confirmed pattern break (Test census: read/patterns.py). The Weinstein and TraderLion material in the X census asks for more on weekly breakouts, roughly two times normal on the breakout week, with a multi-week build-up accepted as an alternative form. Use 1.4 times as the daily floor for calling a break confirmed, treat anything near or below average as unconfirmed, and say which it is in the read.
* **Close location.** Expansion means little if the bar closes back in the lower half of its range or back inside the pattern. Wide spread, close near the high, volume expanded: all three together are the break. Any one missing is a question to carry into the next session, not a confirmation to round up.
* **The retest.** A healthy breakout often throws back to the broken line. That retest should print on contracting volume and hold above the line, which has now flipped from resistance to support. A retest on expanding volume that closes back inside the pattern is the classic failed break, and the desk handles busted patterns as a new signal in the opposite direction, per the Bulkowski doctrine in the census. Your job is only to name it quickly and honestly.
* **Calibration humility.** The desk pattern calibration on the 1,838-name genome universe (PATTERN-CALIBRATION.md, 2,390,032 instances, Alpaca SIP daily bars, 2020 to 2026) sliced outcomes by a simple volume confirmation flag, signal-session volume at or above its 20-session average. That flag alone moved objective-first rates only modestly for most families, and for breakout events the present slice did not beat the absent slice on that crude definition. The lesson is precise, not discouraging: a single session clearing its own average is a weak test. The master's test is the fuller script, expansion ratio plus close location plus contraction inside the base plus retest behaviour, judged together. Do not let one green volume bar do the work of four checks, and do not discard volume because a crude slice of it is weak. The census itself notes the stronger expansion ratio is recorded only for retest instances, which is why the headline slice understates the real craft test.

After the breakout session, keep reading volume for three to five sessions. Follow-through means up bars keep their volume and down bars lose theirs. A breakout that immediately trades on declining volume in both directions is stalling at higher prices, and the read should say so while price is still above the line, not after it fails.

### 1.5 Volume failure modes to learn by sight

* **Breakout on light volume in a thin name.** Note the absolute volume, not only the ratio. Ratios lie in illiquid names. The desk caps conviction when volume data is missing or the name is too thin to judge, and states the cap in the read. Copy that.
* **One enormous bar that is news, not structure.** Earnings and headlines print climax-sized volume inside ranges. A single news bar does not rewrite the volume trend of the base. Judge the bars around it.
* **Rising volume on a decline inside an uptrend base.** This is the distribution tell arriving early. It does not end the read, but it forbids calling the pullback healthy until a later pullback proves lighter.

## 2. RSI: momentum context first, divergence craft second

RSI, the Relative Strength Index, is Wilder's 14-period bounded oscillator, running from 0 to 100, built from average gains over average losses with Wilder smoothing (external canon: ChartSchool RSI article, read in full in the census). Learn the standard settings and keep them: RSI(14) on closes, on the timeframe of the read. Changing lengths to make a divergence appear is the beginner's tell. The masters in the corpus use the plain 14 and spend their skill on where they look, not on tuning.

### 2.1 Momentum context: what RSI says about the regime of the move

Before any divergence, read RSI as a regime gauge:

* **Bull range and bear range.** In a healthy uptrend RSI tends to live between roughly 40 and 80, dipping toward 40 to 50 on pullbacks and reaching 70 or above on pushes. In a downtrend it tends to live between roughly 20 and 60, rallying toward 50 to 60 and failing. A pullback that holds RSI above 40 inside an established uptrend is momentum behaving as the trend says it should. An RSI that loses 40 on a routine pullback is telling you the character of the move changed before price structure broke. That range shift is often the first honest change on the chart.
* **Overbought is a condition, not a sell signal.** Inside a strong trend RSI can stay above 70 for weeks, a behaviour called band walking in the BB RSI divergence specification (Test census: indicator/BB_RSI_Divergence_Algorithm.md v2.2), which explicitly warns that a band touch alone is not a signal and that trend context halves or confirms risk. The master reads RSI above 70 inside an intact uptrend as strength to respect, and only starts hunting for a turn when price reaches a known level, a terminal pattern, or a measured objective at the same time.
* **The 50 line as a quiet pivot.** RSI crossing and holding above 50 on a base breakout corroborates that average gains now exceed average losses. RSI failing at 50 on a bounce inside a downtrend corroborates that they do not. It is a modest witness. Use it to agree or disagree with the price break, never to replace it.
* **ChartsLector's calibrated RSI.** The ChartsLector rebuild in the quant-research-backup census carries a Calibrated RSI among its Pine tools, part of a toolkit that also includes a ranker, breadth tables and an ATR matrix. The transferable idea is calibration itself: RSI levels mean slightly different things on different instruments and regimes, so a careful reader learns each important name's own RSI habits over time, where its pullbacks usually stop and where its pushes usually stall, instead of applying one textbook band to everything.

### 2.2 Divergence craft, the Echo rule

The rule from the playbook, stated once and applied everywhere: **divergence is a turning-point tool only.** Bearish RSI divergence belongs at pattern tops and wedge terminals. Bullish RSI divergence belongs at correction lows, at the end of a C wave, at a tested buy zone. Never in the middle of a structure, never as a standalone entry. It arms the level. The trigger is always something price does: the 50MA reclaim or loss, the zone reaction, the break of the divergence's own neckline (PLAYBOOK_echo_max_2026-10-12.md, rules 6 and adopted rule 4).

Max Williamson's template shows the working form (playbook, Max section): an RSI Divergences panel on top of every chart, with hand-drawn lines across the pivots. His long bearish divergence lines across an entire advance, RSI printing lower highs from November to June while price tripled in WDC, are read as momentum decaying inside an intact trend: a warning to demand that the level hold, not a short. Echo uses it more sparingly, mainly at extremes, as with OSCR's rising wedge up 189 percent printing bearish RSI divergence into its terminal, where the call was a breakdown expectation tied to the wedge, not to RSI alone. Two practitioners, one discipline: the longer and more dramatic the divergence, the more it is context. The shorter, sharper divergence exactly at a terminal level is the one that arms a trigger.

Work a divergence properly, in this order:

1. **Confirm the price pivots first.** Divergence is a comparison between two price pivots and the two RSI pivots that correspond to them. Use confirmed swing pivots, the kind the desk detectors require: the BB RSI specification demands a 3-left, 3-right confirmed pivot at a Bollinger band touch, with RSI pivots 5 to 60 bars apart and at least 2 RSI points of separation, and it timestamps the signal at the confirmation bar, never at the pivot candle itself. That honesty about timing is the craft. A divergence you can only see by pretending you knew the pivot in real time is a study artefact, not a read.
2. **Classify it.** Regular bearish: price higher high, RSI lower high, at a top, warns of a turn down. Regular bullish: price lower low, RSI higher low, at a bottom, warns of a turn up. Hidden divergence is the continuation form: price higher low with RSI lower low in an uptrend suggests the trend resumes, and the mirror holds in downtrends. Name which one you have. Half of all divergence confusion is an unnamed hidden divergence being read as a regular one.
3. **Check the location.** Is price at a level that matters independently: a fib zone with confluence, a prior pivot shelf, the 200MA, the boundary of a terminal wedge or triangle, a measured objective. If not, log the divergence as background and move on. The Echo Algorithm (Step 5) applies exactly this placement: RSI divergence is evaluated at the zone, as evidence for a setup that already exists on price and fib grounds.
4. **Check whether the divergence is broken.** The Echo Algorithm names the kill condition plainly: if RSI makes the new low together with price, the divergence is broken and the setup loses that evidence. Divergence can also resolve by price going sideways until RSI resets. A divergence is perishable. Date it, and re-check it every session it is meant to be arming.
5. **Name the trigger in advance and wait for it.** Bullish divergence at a low arms the level. The trigger is the reaction: a bullish engulfing or hammer at the zone, a close back above the short EMAs after touching the zone, with bounce volume above the pullback's mean volume (Echo Algorithm, Step 6), or the 50MA reclaim in Echo and Max daily grammar. Until the trigger prints, the state is WATCH, in their capitalisation and in yours.
6. **Size the claim by the stack.** In the Echo Algorithm's conviction ladder, divergence is one element of the stack alongside at least two fib confluences and the reaction itself for a HIGH grade. One element alone earns the lowest grade that still counts as a setup, and a lone divergence with no zone and no reaction earns none.

Two more implementations in the census sharpen the craft:

* **The BB RSI method as a complete trade grammar** (Test census: BB_RSI_Divergence_Algorithm.md v2.2, with its frozen Pine indicator). Bollinger(20,2) touch at the confirmed pivot, RSI divergence as the entry condition, entry at the ask, stop at the pivot extreme minus 0.5 ATR, target at the Bollinger basis (the 20-period middle line), minimum 1.2 R to risk required, and risk halved when a 12-bar efficiency ratio says the name is in a strong downtrend that can band-walk against you. Study what it teaches beyond its own setup: every divergence claim should be able to state its pivot rule, its stop in ATR terms, its target with a reason, and the regime in which it should be trusted less.
* **Trullas divergence counting** (Test census: docs/TRULLAS_DIVERGENCE-RECREATE.md, QQQ 1-minute). Here divergence is counted as risk, not just signal: across consecutive confirmed pivots (k equals 5 in the recreate), MACD divergence is required, while RSI and volume divergences are counted as risk units, one to three, inside a fully specified method with a Fibonacci entry trigger at 23.6 percent, first target at 38.2 percent with the stop moved to breakeven, second target at 61.8 percent, stop one tick beyond the pivot extreme, and a 30-bar expiry on a pending setup. The intraday timeframe is not your daily practice, but the discipline transfers whole: count how many independent series diverge, require the most important one, expire the setup if price does not confirm promptly, and never let a divergence float without a stop defined by the pivot that created it.

The RSI and OBV divergence study in quant-research-backup (RSI_OBV_DIVERGENCE/REPORT.md with code/divlib.py) adds the pairing worth adopting: check price against both RSI and OBV at the same pivots. Momentum divergence plus participation divergence at the same low or high is a stronger stack than either alone, because the two series fail to confirm price for different reasons.

### 2.3 Calibration: what the desk measurement says about divergence

Calibration in this playbook means checking your own reads against measured outcomes, and the desk has measured divergence at a scale few practitioners ever see. In the genome pattern calibration (1,838 names, 2,390,032 instances), battery divergences recorded 471,049 instances with 367,180 measured, reaching objective before invalidation 48.34 percent of the time with a median R of 0.553; core divergences recorded 215,395 instances with 158,201 measured, at 42.32 percent and a median R of 0.56; weekly divergences were harder, 45.01 percent objective-first against 48.46 percent invalidation-first on 27,984 measured. Read those numbers as a master should: divergence families are among the strongest measured families in the whole census, clearly ahead of raw breakout events and most single candlestick families, and they are still not coin-flip-proof certainties. They reward exactly the craft above, confirmed pivots, a real level, a defined objective and invalidation, and a trigger. The census measured divergences that already carried lawful geometry. Your job is to refuse the ones that do not.

Self-check drill for RSI: once a week, pull five charts where you called a divergence in the last month. For each, grade four rows pass or fail: confirmed pivots on both series, extreme location at a named level, trigger named in advance and actually awaited, invalidation honoured. That four-row audit, borrowed from the Echo checklist habit, improves divergence reading faster than any new indicator setting.

## 3. MACD: trend and momentum confirmation

MACD is the trend servant. Where RSI is bounded and quick, MACD is unbounded and deliberate, and its best use is answering slower questions: which regime is momentum in, is the current push accelerating or decelerating, and does momentum confirm or diverge at this price extreme.

Construction, standard and unchanged: MACD line equals the 12-period EMA minus the 26-period EMA of closes; signal line equals a 9-period EMA of the MACD line; histogram equals MACD minus signal (external canon: ChartSchool MACD article, Gerald Appel, late 1970s; histogram by Thomas Aspray, 1986). Because MACD values scale with price, absolute MACD levels are not comparable between a 20 dollar stock and a 100 dollar stock. For cross-name comparison the canon points to the percentage form, PPO. Inside one name over time, plain MACD is the working tool, and it is the form every asset in this census uses.

### 3.1 The three signal families, in the order a master uses them

ChartSchool lists three families. Reorder them by importance for chart reading:

1. **Centreline position: the regime read.** MACD above zero means the 12 EMA sits above the 26 EMA: upside momentum regime. Below zero, the reverse. This is the MACD fact to state in every read, in one clause: MACD above zero and rising, above zero and falling, below zero and recovering, and so on. Its durability depends entirely on whether a real trend follows, as the canon's own examples show: one centreline cross in 3M lasted ten months inside a trend, while Cummins printed seven whipsaw crosses without one. In a range, centreline crosses are noise with good branding. In a trend, a centreline cross that agrees with price structure is meaningful regime confirmation.
2. **Divergence: the extreme read.** Bullish MACD divergence is price lower low with MACD higher low, identified on clear reaction troughs in both series, and confirmed, in the canon's worked GOOG 2008 example, by a signal-line cross plus a resistance break. Bearish divergence mirrors it, with the GameStop example completing on a support break and a throwback that turned support into resistance. Note that even the textbook requires price confirmation. MACD divergence follows the same Echo rule as RSI divergence: extremes only, arms the level, price pulls the trigger. It also carries the canon's shared caution: early in strong trends, divergences print routinely as momentum normalises from its first surge while MACD stays on the trend side of zero. A first divergence against a young trend is character, not a call.
3. **Signal-line crossovers: the timing read.** MACD turning up through its signal line inside a bullish regime, at a price level you already care about, is a reasonable timing corroboration for a reaction. On its own, mid-range, it is the weakest of the three. Treat crosses at extreme positive or negative values with extra caution, and expect volatility to inflate their count.

### 3.2 The histogram: reading acceleration

The histogram is the difference between MACD and its signal, which makes it a picture of acceleration. Expanding bars mean momentum is pulling away from its own average. Contracting bars mean it is converging back. Two uses earn their keep:

* **Slant and peak-trough divergence in the histogram anticipates the signal cross,** because MACD itself lags. A histogram that has printed successively shallower negative peaks across two price lows is showing deceleration before the MACD line itself turns. Use it as an early warning inside a level watch, with the same discipline: it arms, it does not trigger.
* **Histogram contraction inside a trend pullback** is the MACD version of volume dry-up. A healthy pullback in an uptrend often shows the histogram dipping negative briefly and recovering as price holds its level. A pullback whose histogram keeps deepening while price holds is a disagreement to name in the read.

The Femto setup chart standard draws the MACD pane on every plan chart alongside volume and RSI, with divergences marked only where the record carries them. When you study those 233 worked charts, practise reading the three panes as one sentence: participation, momentum range, momentum regime. If the three sentences disagree, the read says so and conviction follows the weakest.

### 3.3 MACD in the desk corpus, and an honest note on double MACD

MACD appears in the census in specific, grounded roles rather than as crossover folklore (Test census summary of its 11 MACD paths). It is the required divergence leg in the Trullas method, where an RSI or volume divergence without MACD agreement does not complete the setup. The desk carries MACD sleeves in code (adapters/s_mn_macd.py, and MACD plus CCI combinations in strategies/midna/mn-macd-cci.md), treating MACD as a trend and divergence engine. The MarketCipher teardown in the Silicon REA corpus (research/rea-teardowns/marketcipher) dissects a popular composite oscillator built in this family, waves and money flow combined into one visual, which is a useful study in what layered oscillators are actually computing under the branding.

On double MACD specifically: the census was searched for it and holds no dedicated double-MACD asset. No file in the Test, Silicon, quant-research-backup, local or REA index material teaches a named two-MACD system. This section therefore does not invent one. What the corpus does support, and what serves the same purpose honestly, is a two-lens MACD practice:

* **Two timeframes, one setting.** Keep 12,26,9 on both the daily and the weekly chart. The weekly MACD centreline position states the regime the daily read lives inside; the daily MACD and histogram time the move within it. Weekly above zero with daily recovering from a divergent low at a buy zone is a coherent stack. Daily enthusiasm against a weekly MACD still falling below zero is a bounce until proven otherwise. This is the multi-timeframe habit the whole playbook uses for counts and levels, applied to momentum.
* **Line plus histogram as the two lenses on one timeframe.** The line gives regime and divergence; the histogram gives acceleration and early contraction. Reading both is the desk's actual double view, and it is drawn that way on every setup chart.

If a future corpus adds a true double-MACD method with its own rules, it should enter this section by name, with its source, the way Trullas and BB RSI entered the divergence material above. Until then, two timeframes and line-plus-histogram is the complete and honest practice.

## 4. Relative strength lines versus the index

The relative strength line is the simplest indicator in this section and, for stock selection, the most consequential. Divide the stock's price by the index's price, usually SPY for the broad market, QQQ where the name lives in the growth and technology complex, and a sector ETF where the real contest is inside a sector. Plot that ratio as a line under price. It rises when the stock outperforms and falls when it underperforms, regardless of whether both are going up.

This is not the same thing as RSI, despite the shared words. RSI compares a stock with its own recent past. The RS line compares it with the market, today. Wyckoff's Step 2 in the canon is built on it: select stocks in harmony with the broad trend, showing relative strength, judged in uptrends by bigger percentage rises on rallies and smaller percentage falls on reactions than the index. The X census teachers converge on the same line: Minervini's codifications want the RS line making 52-week highs while the base is still building, called the strongest accumulation tell in that tradition; the forum material in the census adds the working protocol of always naming the benchmark and lookback, and checking RS on a second timeframe, because short-term RS rising while weekly RS still falls is a bounce, not a leadership change (external forums census: Relative Strength line protocol).

Read the RS line in four moments:

* **Inside the base.** An RS line that flattens and then rises while price is still ranging is quiet leadership. Institutions cannot accumulate size without leaving this trace, and it appears before the price breakout because the ratio moves on relative resilience during market dips. When you annotate a base, annotate its RS line's behaviour in the same sentence as its volume dry-up. The two together, quieter supply and improving relative performance, are the classic pre-breakout signature across the Weinstein, Minervini and Lector material in the census.
* **At the breakout.** The powerful confirmation, in the All Star Charts formulation inventoried in the X census, is price breaking out and its RS line breaking out at the same time, ideally RS to a new high through its own prior peak. A price breakout whose RS line stays under its prior high is a stock being carried by the index. It can still work, but it is not leadership, and the read should not call it that.
* **On pullbacks.** Leaders fall less. In a market correction, watch which RS lines hold near their highs while price pulls back in an orderly way. Those names are the first watchlist when the market turns, a selection habit the Wyckoff five steps and every breadth-first routine in the census share.
* **Against the right benchmark.** The desk grades performance as percentage gain compared with SPY and QQQ over the same window, and the same dual comparison belongs in the read. A software name should also be checked against its sector, IGV in the forum protocol's example, because beating a falling sector while lagging SPY is a different fact from leading the whole market. Name the benchmark in the read, every time. An RS claim without a named benchmark is not a claim.

The Morgue board features library (Terminal census: board_features.py) computes this family mechanically for every name: an RS line against SPY, QQQ and sector, alongside OBV and close-location accumulation evidence, up and down volume agreement, and volume-validated triggers. That list is worth memorising as a checklist of what a complete servant panel covers. When your manual read and a computed panel disagree on RS direction, stop and reconcile before narrating, the same stop rule the local stock analysis skill applies whenever the image and the computed pass disagree on a material fact.

Failure mode: RS lines in a violent market-wide decline rise for stocks that are merely falling more slowly. A rising RS line with price below a falling 200MA is relative resilience, not a buy setup. Location and regime still govern. The servant confirms; it does not promote.

## 5. Breadth as market context

Breadth answers the question a single chart cannot: how many stocks are participating in what the index appears to be doing. An index can rise on a narrowing handful of names or on a broad advance, and the same individual breakout means different things inside those two tapes. Breadth is therefore the outermost servant. It never speaks about a single name directly. It sets the ceiling on what any single name's indicators are allowed to claim.

The tools in the corpus:

* **Percent above key averages.** The terminal's Breadth Meter (Tool 31, Terminal census) renders market health as percent of stocks above their 50-day and 200-day averages, with advancers against decliners, on a dial. Read it as participation behind the index trend. An index at new highs with percent above the 200-day falling for weeks is a narrowing market; breakouts fail faster there, and position-level conviction should be capped accordingly, in advance, in writing.
* **Advance and decline lines.** The cumulative advance-decline line making new highs alongside the index is the definition of broad participation in the material inventoried from Brian Shannon's Chart of the Day tradition (X census). An A/D line lagging below its prior high while the index exceeds its own is breadth divergence, the market-level version of the same non-confirmation craft taught for RSI and MACD. Same rule: it arms caution, it does not call a top by itself.
* **The Lector systems.** ChartsLector's rebuilt toolkit (Silicon census: lector-systems, with breadth.py, a dated breadth readout, pulse.py and pulse_v2.py, and SYSTEMS_DEEP_ANALYSIS.md) computes breadth tables, a theme and RS and relative volume leaderboard, and a Market Action Pulse from index and ETF daily and weekly bars, including equal-weight QQQE and RSP data. The transferable craft is the routine: breadth first, themes second, single names third. His framework, as inventoried in the X census, is stated in his own terms as based on market breadth, with every setup qualified against it.
* **Hand-posted breadth as a discipline.** The X census includes Helene Meisler, the first technical analyst at Goldman Sachs in 1989, who still hand-posts roughly 200 daily charts and computes summation arithmetic as a daily routine, judging trend inertia by how many bad breadth days it would take to stop the Summation Index rising. You do not need her instruments to adopt her lesson: breadth is a daily habit with a memory, not a glance before a trade. Note yesterday's reading when you make today's.

How breadth enters a single-name read, concretely:

1. State the market's breadth condition in one line at the top of the read, with the date: for example, participation expanding, index and A/D line at highs together; or participation narrowing, index high on falling percent above the 50-day.
2. Let it set the cap. Expanding breadth permits normal conviction for a well-formed setup with confirming volume and RS. Narrowing breadth caps conviction one grade, demands the strongest RS lines only, and raises the standard for breakout volume, because breakouts in narrowing tapes have less following wind.
3. Let sector breadth refine it. A name in a sector whose own breadth and RS are improving, inside a flat broad market, is a local leadership story and should be read against its sector first and the index second, the same benchmark discipline as the RS line section.
4. Never reverse the logic. Good breadth does not make a broken chart buyable, and poor breadth does not make a perfect chart unownable. It conditions confidence and selection order. That is the servant role at market scale.

The Elliott canon adds one breadth observation worth carrying (external canon: wave personality). Wave 3 is described as the strongest, broadest and most unmistakable leg, with expanding breadth, while wave 5 arrives as a climax on narrower breadth and momentum divergence. Whether or not you count waves, the pairing is a durable diagnostic: broad participation plus strong momentum is the middle of a move; narrow participation plus divergence at new highs is the character of a late one.

## 6. Putting the servants together: a worked pass

Take a daily chart you have never seen and work it in the section's order, writing each step before moving to the next. This is the pass the Femto plan chart draws, translated into a reading routine:

1. **Price only, panes covered.** Name the cycle position, the structure, and the deciding level or zone, with its confluence count. Draw at most two trendlines, on confirmed major pivots, per the Echo and Max discipline. If there is no level, stop. The read is patience, and no pane can change that.
2. **Volume uncovered.** Write the volume sentence: trend inside the structure, behaviour on the last pullback against the last advance, dry-up present or absent, and what the most recent climax or expansion bar, if any, actually did. Let it falsify or cap, in writing.
3. **RS line.** Name the benchmark. State whether the RS line leads, confirms, or lags, inside the base and at any break. Downgrade leadership language if it lags.
4. **RSI.** State the range it is living in and what that says about the move's character. Then, and only if price sits at an extreme or a terminal pattern, evaluate divergence with confirmed pivots, classify it, and check whether it is broken.
5. **MACD.** State centreline regime on the weekly, then the daily line and histogram: confirming, decelerating, or diverging, and whether any of it changes the timing inside the level you already have.
6. **Breadth.** One line, dated, with the cap it imposes, if any.
7. **Verdict.** One conditional sentence in the playbook grammar, trigger and invalidation named, followed by the fuller notes. Example shape: holding the zone on light test volume with the RS line at highs keeps the primary count live; losing the 50MA on expanding volume confirms the move to the deeper zone. Patience until one of those prints.

Notice what this pass never does: it never starts at step 4 because a divergence looked pretty, never promotes a name at step 3 because one bar expanded, and never lets step 6 rescue a chart that failed step 1. Order is the skill. The indicators are easy to compute and the desk computes them everywhere, in Pass A geometry, in board features, in the terminal read modules. The mastery is in subordination, asking each servant the one question it is good at, in sequence, and letting any of them say no.

### The one-page checklist

Copy this onto the first page of a chart notebook:

* Cycle position named before any indicator quoted.
* Zone built from confluence; lone indicator signal is not a zone.
* Volume trend inside the structure stated; pullback volume compared with impulse volume.
* Dry-up marked by date, or its absence stated.
* Breakout judged on ratio to 20-session average (1.4 times floor), close location, and retest volume.
* Climax, if present, treated as a range boundary, with its test judged on contracting volume.
* RS line benchmark named; RS behaviour inside the base and at the break stated; second timeframe checked.
* RSI range stated; divergence only at an extreme, on confirmed pivots, classified regular or hidden, checked for breakage, trigger named in advance.
* MACD weekly regime stated; daily line and histogram read for confirmation, deceleration or divergence; crossovers never used alone mid-range.
* Breadth dated and stated in one line; conviction cap applied if narrowing.
* Verdict conditional, trigger and invalidation priced, both scenarios carried.
* Any disagreement between eye, computed pass and panes reconciled before the read is delivered, never narrated through.

### Sources named in this section

Echo and Max playbook and the ECHO-ALGORITHM (Echo Algorithm Steps 5 to 7), local files under research/chart-methodology and .scratch-x-charts/echo-algorithm. Local stock analysis skill, Pass A and Pass B protocol, custom skills. Best Setups chart law and Femto setup chart library, Silicon and Terminal censuses: setup_brief.py, chart_spec.py, 233 setup PNGs. Terminal read engine, Test census: read/volume.py, read/patterns.py (1.4 times breakout standard), read/wyckoff.py and wyckoff_phase.py, read/divergence.py, read/indicators.py. BB RSI Divergence Algorithm v2.2 and Pine indicator, Test repo. Trullas Divergence RECREATE and variants, Test repo. RSI and OBV Divergence study, quant-research-backup: RSI_OBV_DIVERGENCE. ChartsLector systems, Silicon lector-systems and quant-research-backup CHARTSLECTOR. Morgue board_features.py, Terminal census. Breadth Meter Tool 31, Terminal census. Desk pattern calibration on the 1,838-name genome universe, PATTERN-CALIBRATION.md: 2,390,032 instances, divergence family outcomes and volume confirmation slices. External canon census: ChartSchool RSI, MACD and histogram, Wyckoff Method, gaps and volume doctrine; Bulkowski pattern volume scripts. X census and forums census: Weinstein and TraderLion breakout volume, Minervini RS line doctrine, RS line protocol, All Star Charts RS confirmation, Lector breadth-first framework, Meisler breadth routine.
