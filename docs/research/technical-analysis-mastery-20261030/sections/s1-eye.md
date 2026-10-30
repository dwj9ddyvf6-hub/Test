# Section 1: The Eye First: The Visual Inspection Protocol

## What this section teaches

A master does not start with an indicator, a pattern name, or a trade idea. She starts with her eyes, in a fixed order, and she earns each next step from what the chart actually shows.

This section is the first pass: the protocol you run on every chart, on every timeframe, before any measurement, any lens, and any plan. It is built from the desk assets that already encode this craft: the Echo and Max playbook at `research/chart-methodology/PLAYBOOK_echo_max_2026-10-12.md`, the five account X chart study in `.scratch-x-charts/` including XCHART-STUDY.md and its addendum, the Echo Algorithm in `.scratch-x-charts/echo-algorithm/ECHO-ALGORITHM.md`, the local stock analysis skill with its Pass A geometry and Pass B perceptual read, the chart reading method in `research/composite-confidence/CHART_READING_METHOD.md`, the Best Setups chart law in Silicon `femto/core/chart_read.py`, `chart_spec.py`, `setup_brief.py` and `setup_call.py`, and the desk pattern calibration on the 1,838 name genome universe in `.scratch-setups-build/pattern-calibration/PATTERN-CALIBRATION.md`.

Learn the order until it is automatic. Order is the skill. When the order slips, the eye finds the pattern it wanted to find and stops looking.

## Rule zero: gestalt before measurement

Open the chart at the highest resolution available and look at the whole thing before you look at any part of it.

The chart reading method puts perception first for a practical reason: in the CharXiv work cited there, most chart failures were early perception errors, such as a misread axis, a confused series, or an invented label, and an early error cascades through everything built on it. The master counters that failure mode with discipline, not talent.

Do these five things before you interpret anything:

1. Inventory the frame. Name the symbol, the timeframe, the date range shown, whether the scale is linear or log, whether the axis is normal, and whether the last bar is complete or still forming. On a multi hundred percent move, note that Echo's rule calls for log scale, a point the Echo Algorithm records explicitly.
2. Register every series. Say, out loud in your notes, what each colour and line is: price, volume, the 20, 50 and 200 period averages if they are drawn, RSI, MACD, VWAP, or a drawn trendline. Never read a value off a series you have not registered.
3. Transcribe before you interpret. Write down the recent swing high, the recent swing low, where price sits relative to the key averages, and the largest recent volume bars. Numbers first, story second.
4. State the gestalt in one sentence. Examples: a long base breaking upward, a steep advance now going sideways at the highs, a fall that has stopped falling and is carving a floor, a range with no direction. One sentence, shape only, no pattern name yet and no direction call yet.
5. Run a counter check. Ask what in this frame could mislead you: a cropped window that hides a prior top, a timeframe chosen to flatter a view, smoothed candles that hide wicks, missing volume, or a line that was drawn after the fact. The Long Investor corpus in the X chart study uses Heikin Ashi in every verified chart. That smoothing makes trends look clean and it discards wick information that stops depend on. The desk reads true OHLC for that reason. Name the smoothing if it is present.

Only after those five steps do you measure. Pass A in the local stock analysis skill is the desk version of this separation: a deterministic geometry pass computes pivots, averages, ATR, clusters and divergences, and Pass B is the human visual read of the rendered weekly, daily, 1 hour and 10 minute charts. If the image and the geometry disagree on a material fact, you stop and reconcile the bar, the adjustment basis or the scale. You do not narrate through a disagreement.

## The first pass, in order

Work these seven questions in this exact sequence. Each question has a job, a set of marks to look for, and a written output. Do not move on while the current output is vague.

### 1. Trend: who is in control, and on which timeframe

Look first at direction, not at setups.

Check three things:

* Price against its averages as geography. In the Echo and Max playbook the 50 period average is the actionable pivot and the 200 period average, or the 200 week average, is the regime line and final backstop. Above the 200, buyers hold the regime. Below it, sellers do. The 50 is where that regime gets tested in the near term.
* The swing sequence. A series of higher highs and higher lows is an uptrend in structure, whatever an oscillator says. Lower highs and lower lows is a downtrend. A sequence that stops making progress in either direction is transition.
* Slope and spacing. A rising average with price holding above it on pullbacks reads differently from a flat average with price crossing it every week. The first is a trend with a floor. The second is a balance.

Output: one word for regime, bullish, bearish or transitioning, plus the structural reason in one line. Example form: bullish regime, price above a rising 200 day average, daily higher lows intact, 50 day average rising beneath price. That is the weekly regime line from the chart reading method, Step 1.

If you cannot write that line, you do not have a trend read yet. Stay here.

### 2. Structure: what shape is price building

Now name the structure that contains the trend. Structure is the arrangement of swings, not a single candle and not a single bar.

Look for, in order:

* Confirmed pivots. In `chart_read.py` and in Pass A, a pivot is a 5 bar fractal high or low, and it is only known when it is confirmed, not at the extreme bar itself. Use pivots with both their extreme time and their availability time. Unconfirmed wiggles do not anchor lines or zones.
* Bases and ranges. A base is weeks or months of sideways work after a fall, with higher lows forming inside it. A range is sideways work with clear upper and lower bounds and no progress. Wyckoff vocabulary in the desk reader names the parts when they are present: selling climax, automatic rally, secondary test, spring only when its test follows, sign of strength, then last point of support.
* Continuation shapes in context. Flags, pennants and triangles are context until they confirm. The Best Setups confirmation law is strict and worth copying as a habit of the eye: no pattern is a call before its confirmation close. A triangle is lines converging on a decision point. A flag is a pause after a sharp leg. The shape tells you where the decision will happen. The close through the boundary, with volume, tells you the decision was made.
* Failure shapes. Double tops and double bottoms, head and shoulders, wedges that exhaust. In Wedge work the desk reader requires repeated touches over weeks before the shape earns weight, and in pattern work generally, two points make a hypothesis about a trendline, three or more touches validate it.

Output: the named structure, its boundaries in price, and its age. Long bases and mature structures carry different expectations from a three day pause, and the reader states which she is looking at.

### 3. Location: where is price inside its own range

A good structure at a bad location is not a good read. Location is the question most beginners skip and the question Echo and Max answer on every chart.

Place price in three ranges at once:

* Inside the current structure. Is price at the top of the range, the middle, or the bottom? Mid structure, between zones, is where the Echo and Max playbook says patience, in its words corrective, not buy time. At a boundary, price must decide. In the middle, it does not.
* Inside the larger move. How far has price travelled from the base or from the last major swing low, and how much room is left to the next major shelf above or below? Name the overhead magnet if there is one, such as a prior high, an all time high, or a round number that has acted as a shelf. The chart reading method separates extension with a structural magnet from extension with nothing overhead. They read very differently even when the slope looks the same.
* Against its key shelves. List the nearest levels above and below as zones, not thin lines. A zone in desk practice is a band built from confluence: a Fibonacci shelf from a named swing, an average cluster inside the same band, a trendline arriving there, a prior pivot shelf, and a round number are independent constructions. Count how many land in the same ATR scaled band. The playbook rule, carried into the local stock analysis skill, is that a lone Fibonacci level is a watch level. A band where two or more independent constructions agree is a zone that can carry a plan. Pass A builds those clusters at 2.5 ATR scale and counts touches by independent episode, not by repeated bars on the same episode.

Output: a location sentence. Example form: price is in the upper third of a six week range, 0.4 ATR below the prior swing high, 2.1 ATR above the 50 day average, with the next shelf above at the all time high and the first real shelf below at the base top. Every level named by its anchor and its distance in ATR, as the local skill requires.

### 4. Volatility state: is the chart quiet, normal, or expanding

Read volatility as a state, not as a feeling.

* Range size against ATR(14). Are recent bars small against ATR, near ATR, or multiples of ATR? Note gaps, wide range bars, and wick length at the extremes.
* Compression. A squeeze, a narrowing triangle, a base that gets quieter, or Bollinger Bands pinching all say the same thing visually: energy is being stored and the next expansion will travel. The genome calibration measures families such as bollinger_squeeze and breakout_event precisely so the reader can quote a measured prior for that state instead of a hunch.
* Expansion. Parabolic slope, bars growing as price rises, long upper wicks at new highs, and price far from every average describe late expansion. Volatility expanding at lows after a climax bar is a different state from volatility expanding at highs. Name which one it is.
* What volatility does to risk. The chart reading method sets a practical floor learned from its own scored reads: stops placed inside normal noise, below about 1.5 ATR, get eaten before a thesis can work. Your volatility read therefore feeds position construction directly. A quiet chart can carry a tighter invalidation than a wild one, and the chart tells you which you are holding.

Output: quiet, normal or expanding, where in the structure that state sits, and the current ATR value you will use for distances.

### 5. Life stage: where is this move in its life

This is the Echo question, and the playbook puts it first in spirit: where are we in the cycle, and what single level decides it?

Name the cycle position before you quote any indicator. The local stock analysis skill makes that an explicit rule, and the Echo Algorithm makes it Step 2, impulse or correction, before any Fibonacci is drawn.

Work through the candidates:

* Impulse leg. Five legs in the trend direction, with the third leg normally the strongest and carrying the momentum peak. Echo and the desk Elliott counter in Silicon `elliott_wave.py` hold counts to three hard rules: wave 2 never retraces all of wave 1, wave 3 is never the shortest of waves 1, 3 and 5, and wave 4 does not overlap wave 1 in a standard impulse. A count that breaks a rule is not a creative count. It is a dead count, and the counter outputs invalidated with its invalidation price rather than quietly relabelling.
* Correction leg. Three legs, A, B and C, or a complex W, X and Y when the first correction does not finish the job. Echo classifies corrections by the shape of A, the depth of B, and whether C completes, fails or runs. Corrections after a completed impulse commonly end in the deep retracement bands the playbook hunts, 0.5 to 0.618 for a shallow end and 0.786 to 0.887 for the deep ends Echo calls his signature territory. Those bands become interesting only with confluence, per Step 3 above.
* Base and reversal attempt. A climax, a stop of the fall, higher lows, and a first sign of strength belong here. So does a breakdown that fails and reclaims, which traps late sellers and fuels the move back.
* Terminal pattern. A wedge reaching its apex, a distribution top after a long advance, a pattern completing its fifth leg into a measured objective. Terminal means the move is old. Old moves can continue, and the master says so plainly when she separates her two closing questions in the chart reading method: is it still going up, and is it safe to buy here. Those are different questions with different answers on a late stage chart. AMD in that method is the teaching case: trend intact and worst initiation quality at the same time.

Output: the life stage in plain words, the evidence for it in swings, and the level that would prove the stage call wrong. A stage call with no deciding level is an opinion. A stage call with a deciding level is a read.

### 6. Participation: what volume is saying about the story so far

Volume is the tell, in the gestalt synthesis and in every framework in the corpus that carries weight. Look at it after structure and location, and let it confirm or cap what you have seen. It does not create a read on its own.

Check four things:

* Volume on the climax or the low. A capitulation bar on extreme volume at the lows is bottoming fuel in the chart reading method archetype list, its highest quality long archetype when a base and a volume breakout follow.
* Volume on the break. A breakout on the largest volume in months confirms. A breakout on thin volume is a claim without evidence, and in `chart_read.py` volume acts as falsifier: contraction inside the pattern and expansion on the break is the healthy sequence.
* Volume on pullbacks. Drying volume on a pullback is the best evidenced pullback filter in the corpus. Rising volume on a pullback says sellers are active, not resting.
* Volume on the 1 hour for distribution. Wide range red bars on expanding volume on the intraday frame are the first distribution tell. The chart reading method tells the reader to check that before reaching for any other bearish argument.

If volume is not shown, say so and cap conviction. The X chart study is instructive here: Echo's verified exemplar carries no volume pane at all, price and drawings only. That is his choice for a weekly cycle chart. For a desk read that will carry risk, missing volume is a stated limitation, not a detail to glide past.

Output: volume confirms, volume is neutral, or volume contradicts, with the specific bars that earn the verdict.

### 7. The deciding level: what single price settles the argument

End the first pass where Echo and Max end it: with the one level that decides.

Every expert chart in the corpora does this. Max states it as a condition on the 50 period average: needs to stay above the 50, the 50 reclaim is the entry, below the 50 the next shelf is the destination. Echo states it as a Fibonacci shelf: losing a named level confirms the move to the next zone. The desk turns the same habit into law: a verdict that cannot name its invalidation is not emitted, in both the Echo Algorithm checklist and the Best Setups call.

Write three prices before you leave the first pass:

* The deciding level for the current stage call.
* The zone where the opposite scenario becomes the working scenario, with its terminus. Both scenarios are always drawn in the playbook: primary in one colour, alternate in another, with the alternate terminus visible on the same chart. In words, when you have no chart to draw on yet, you still owe both termini.
* The trigger that converts a watch into a setup. Echo never buys the level itself. In the Echo Algorithm, Step 6, a zone becomes a setup only on a reaction: a bullish engulfing or hammer at the zone, or a close back above the fast averages after touching it, on bounce volume above the pullback mean. A wick through a zone does not kill it. A close below the bottom of the zone does. Copy that distinction exactly. Reaction is the trigger. Arrival is not.

Output: a conditional sentence in the playbook grammar. Losing X confirms the move to the zone at Y to Z. Reclaiming A on a close, with volume, opens B. Patience while price sits between X and A. Conditional, level named, patience explicit when patience is the call.

## Multi timeframe alignment: the cascade

No timeframe reads alone. The rule from the playbook and the local skill is consistent: the weekly count governs, the daily times it, the intraday refines it. Higher timeframe wins conflicts in the Echo Algorithm as well.

Run the cascade in this order, every time:

### Weekly: the frame

The weekly chart answers regime and life stage. Price against the 10 and 40 week averages, or the 50 and 200 day averages read on a weekly scale, the major swing sequence over months to years, and the position inside the multi year range. Echo labels counts on daily and weekly, with the weekly governing. The Long Investor weekly variant in the X study drops wave labels entirely and lets one large channel over fourteen years carry the whole argument, with RSI and MACD panes added only at that horizon. The lesson is not the channel. The lesson is that the weekly drawing is allowed to be simple, because its job is posture, not timing.

Output from the weekly: regime, life stage, and the two shelves that matter most above and below. Nothing else is required from this frame.

### Daily: the structure

The daily chart answers structure, location, volatility and the deciding level, using the full first pass above. This is the primary working frame for a swing read, the frame Max builds his template on, with a momentum panel above, price with the 50 and 200 averages in the middle, volume below, and range noted. It is also the frame the Best Setups plan chart is drawn on.

Treat agreement across timeframes honestly. The local skill warns that the 10 minute, 1 hour and daily frames share the same underlying transactions, so agreement among them is one witness, not three independent witnesses. Name what the lower frame adds that the daily does not already show. If it adds nothing, say so.

### Intraday: the rhythm and the refinement

The 1 hour answers rhythm: are the averages stacked or crossed, is the intraday sequence a staircase of higher lows or overlapping chop, and are there distribution bars. That is the 1 hour honesty check in the chart reading method, Step 4. The 10 minute frame refines an entry or an exit around a level the daily already chose. It never invents a level of its own and never overturns the weekly regime by itself.

When frames disagree, downgrade and name the disagreement. The veto framework in the chart reading method is the working rule: weekly, daily and 1 hour in agreement allows full conviction for the read. Any frame in disagreement lowers conviction by a step and the read states which frame disagrees and why. A bullish daily inside a bearish weekly is a countertrend bounce until the weekly shelf is reclaimed. A bullish weekly with a broken 1 hour rhythm is a good chart having a bad week, and the trigger waits for the rhythm to repair.

## History on the left, plan on the right

The five account X chart study found the same staging habit in trader after trader, confirmed at scale for Echo in the addendum at 240 charts, and it is the single most useful layout lesson in the corpus.

Expert charts are built in two halves:

* The left half is history, staged as evidence. Swings are labelled at their pivots, in two degrees when the method uses degrees, major degree in one style and sub degree in another. Trendlines are sparse: one to two lines maximum in the Echo and Max playbook, anchored on major swing extremes spanning the whole pattern, months not wiggles. If a pattern needs five lines, there is no pattern. Levels on the left are drawn as zones and boxes, not hairlines, and a measured level always carries its derivation with its price, in the form ratio and price together, such as 0.786 and its price on the same short line.
* The right half is empty future, reserved for the plan. This is the signature the X study names in Echo's verified weekly exemplar: the right half of the canvas is empty, the projected path is pre labelled in the void, future pivots wait at their prices, and an arrow rises to the extension level with the size of the move printed beside it. The Long Investor does the same work with a connected zigzag polyline drawn into future space, or a single bold arrow from a completed low toward the objective. In both cases the chart is built around the forecast, not decorated with it after the fact.

The desk version of that staging is the Best Setups chart law, and it is stricter, which is why it is worth learning as the standard:

* History on the left carries the named pattern itself, drawn on its pivots, plus volume, RSI and MACD panes below and beside price, with divergences drawn only where the record actually carries them.
* The plan on the right carries a shaded buy zone, a labelled invalidation line, labelled targets by role, and a dashed expected path running through reserved future space to the objective. R to the first target and to the final objective, and the expiry clock, are printed on the chart itself, never traded away for a cleaner picture. `chart_spec.py` enforces that the setup card and the plan chart draw the same averages and the same labelled support and resistance lines, cross checked against the geometry, so the reader never gets two versions of the same read.
* The future is drawn as a plan, not as price. The X study makes the honesty distinction sharply and the desk adopts it: the expected path stays dashed, thinner and visually subordinate to real price history. Drawing the future in the same ink and weight as history is the hype trick in the genre. Drawing it dashed, labelled as stages rather than dates, is the craft version of the same instinct. It gives the reader the path at a glance while keeping the difference between what happened and what is expected visible at a glance too.

Practice the staging as a reading habit even when you are not drawing. Mentally split every chart you open into left and right. Left: what structure has actually printed, with its labels and zones. Right: what path you expect, in stages, to which objective, by what trigger, and wrong if what. If the right half of your mental chart is blank, you have a description, not a read. If the left half has no labels, you have a forecast with no evidence under it.

The 5 second test from the X study is the check on the finished staging. A well staged chart gives a reader, in about five seconds, where we are in the structure, the two prices that matter now, and the destination. The desk card takes longer by design because it also prints invalidation, opposition and R, and that extra honesty is kept. The staging lesson still applies inside it: position the call, the deciding level and the path so they register first, and let the supporting evidence sit underneath for the second read.

## What confirms, and what the reader does next

A first pass ends in one of four states. Name yours before you do anything else.

1. Watch. A zone is identified with confluence, price has not reached it or has reached it without a reaction. Next action: set the trigger in advance, in the conditional grammar above, and wait. No trade is taken on arrival alone.
2. Setup. Price has reacted at a confluent zone, volume supports the reaction, and the deciding level and invalidation are named with room of at least about 1.5 ATR for the stop. Next action: build the full scenario tree, primary and alternate with a terminus for each, a target with its method stated, and confidence capped at medium on a single read, per the local skill.
3. In motion. The confirmation close has printed through the pattern boundary or the average reclaim, on expanding volume. Next action: read the move as in motion, locate the next shelf and the trailing invalidation, and separate the trend question from the initiation question. A move can be in motion and still be a poor place to start.
4. No read. The frames conflict without resolution, the structure needs more lines than the discipline allows, volume is missing where the call depends on it, or the data is stale or partial. Next action: abstain as an evidence status, state exactly what is missing, and name what new information would reopen the read. No view is not a bearish call, and the master never dresses insufficient evidence as one.

## Checking your own eye: the calibration habit

Mastery includes a routine for checking the eye itself, and the desk assets supply it without any need to argue about the craft in the abstract.

* Keep the base rate beside the pattern. The genome pattern calibration measured 2,390,032 pattern instances on the 1,838 name roster from 2020 to 2026, in R and ATR units, family by family. When you name a pattern in a read, look up its measured family state in `pattern_calibration_v1.json` through `pattern_calibration.py`: measured, thin, unmeasured or unavailable. A measured family gives you a prior to quote. An unmeasured family, and the product names several, including wyckoff_spring, wyckoff_sos, bull_flag and bear_flag, gives you a read with no quoted rate, stated as such. Never invent a rate from impression.
* Grade the read against its own geometry. The Best Setups calibration module scores a call as target hit, invalidated, expired triggered or expired untriggered, and keeps a ledger of where the visual read and the computed geometry disagreed. Reviewing that disagreement is how the eye improves: was the perception wrong, the stage call wrong, or the trigger wrong. Process and outcome are graded separately, because a good read can lose and a sloppy read can win once.
* Practise blind. The composite confidence calibration ran blind as of charts, with the symbol and the future hidden, a committed written read, and mechanical scoring at set horizons, then an autopsy per sample. Its scorecards and autopsies are a casebook for this section: they name the recurring eye failures a student can train against, such as reaching for a neutral lean when the protocol asks for a primary scenario, and confidence that ran ahead of the evidence. Repeating that loop, read, score, autopsy, is the training method this playbook recommends throughout.

## The first pass, on one card

Copy this order onto the top of every read until it is habit:

1. Frame: symbol, timeframe, scale, last bar status, series registered.
2. Gestalt: one sentence, shape only.
3. Weekly regime: one word, one structural reason.
4. Daily structure: named shape, boundaries, age, confirmed pivots only.
5. Location: thirds of the range, nearest shelves above and below as confluence zones, distances in ATR.
6. Volatility: quiet, normal or expanding, current ATR, what that means for the stop.
7. Life stage: impulse, correction, base, reversal attempt or terminal, with its deciding level.
8. Volume: confirms, neutral or contradicts, with the bars that earn it.
9. Intraday rhythm: staircase or chop, distribution present or absent.
10. Alignment: frames agree, or the disagreeing frame named and conviction lowered.
11. Deciding level, trigger, invalidation, both scenarios with termini.
12. State: watch, setup, in motion or no read, and the next action that state requires.

Run it in order. Write each line. When a line cannot be written from what the chart shows, that blank is the finding, and the read waits there until the chart fills it in.
