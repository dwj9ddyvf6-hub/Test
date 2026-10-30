# Section 6: The Working Read

## The protocol as one job

A working read is not an impression. It is a sequence that runs in the same order every time, so that a later reader can see where a judgment came from and where it can be checked. The operative standard is the local stock analysis skill (`~/workspace/custom-skills/local-stock-analysis/SKILL.md`), which defines two modes. Chart read mode answers what a named ticker is doing. Full analysis mode adds strategy lenses, a structural screen, market context, and synthesis to the same visual work. Both modes are paper only. A read is not an order and never implies one.

The order matters and is not interchangeable:

1. Geometry first, computed blind.
2. The perceptual read, with the eye on the actual renders.
3. Strategy lenses, each speaking only for itself.
4. Market context, as a conditioner and a cap.
5. Synthesis, with conflicts stated plainly.
6. Construction of the plan: buy zone, invalidation, targets, and R.
7. Drawing to the annotation standard.
8. Logging, then the 2 to 4 week review.

Skipping ahead is the most common way a read goes wrong. Naming a pattern before the geometry is transcribed, or quoting an indicator before the cycle position is named, inverts the method that the Echo and Max playbook (`~/workspace/research/chart-methodology/PLAYBOOK_echo_max_2026-10-12.md`) and the chart reading method (`~/workspace/research/composite-confidence/CHART_READING_METHOD.md`) both enforce: location and cycle first, pattern as an interpretation of those relationships second.

## Step 1: Geometry first, Pass A

Run Pass A fresh for every read. Do not work from memory and do not extend a verdict from an earlier run.

In practice:

- Run `python3 bin/pass_a.py --symbol SYM` from the chart read skill directory. Save the JSON to `~/workspace/research/composite-confidence/reads/<SYM>_<date>_passa.json`.
- Read the `data_status` field before anything else. On `NO_VIEW`, stop with no analysis at all. On `STALE`, carry the staleness caveat through the whole output. On `PARTIAL`, name what is missing in the read itself.
- After any edit to `pass_a.py`, rerun `python3 bin/test_pass_a.py` and require all 18 parity checks green before trusting the output.

What Pass A supplies, and what the reader uses it for:

- Weekly regime, daily structure, and the 1H rhythm and 10m refinement.
- Confirmed pivots, with both their extreme time and their availability time. A pivot is learned only at confirmation, never at the extreme bar itself. This single distinction prevents the most common form of lookahead in hand drawn work.
- EMA and ATR values, volume against its average, close location inside the bar and inside the range, gaps, and momentum indicators including RSI, MACD, StochRSI, CCI, ADX, CMF, MFI, OBV, and session VWAP where the timeframe carries them.
- Kind aware level tests on recent swings. A bar below a prior high can never be counted as a rejected low test. Each test kind carries its own meaning, so touches are read by episode, not by raw count.
- Level clusters built as 2.5 ATR scaled pivot zones. Independent episodes count as evidence. Repeated touches inside one episode do not multiply the evidence.
- Divergence pairs, pattern primitives, and fib retracement zones labelled as policy levels. In this system a fib zone is a place where a hypothesis gets tested, not a forecast by itself.

The desk geometry engine in Silicon, `femto/core/chart_read.py`, states the same discipline as code: confirmed 5 bar fractal pivots with no lookahead, Wilder RSI(14) and ATR(14), ATR scaled pivot clusters with touch episodes, at most two trendlines on confirmed major pivots, Fibonacci only on a named swing with its dates and prices emitted, buy zones as confluence zones, and volume as a falsifier using Alpaca SIP only. When Pass A and that engine agree on the vocabulary, the eye and the machine are talking about the same objects.

Calibration note, used the master way: quote a base rate only from a published table or state that the base rate is not established here. The desk genome pattern calibration (`PATTERN-CALIBRATION.md`, 1,838 name roster, 2,390,032 instances, Alpaca SIP daily bars, outcomes in R and ATR units) is the published table for this desk. It also teaches restraint: families with no lawful objective carry no invented rate, and thin cells with measured n below 30 are excluded from calibration use. A master checks her prior before she leans, and she leaves the cell blank when the table leaves it blank.

## Step 2: The perceptual read, Pass B

Geometry does not replace looking. Render and look.

- Render weekly, daily, 1H, and 10m charts with `render_asof.py` into the dated reads folder at `~/workspace/research/composite-confidence/reads/<SYM>_<date>/`.
- View the actual PNG files. Never narrate from Pass A numbers alone.
- If the image and Pass A disagree on a material fact, stop and reconcile before narrating further. Check bar completeness, provisional status, adjustment basis, and axis scale.

The perceptual protocol runs whole before parts, in the order set by `CHART_READING_METHOD.md`. That method carries a research finding the master keeps in view: in chart vision studies, more than half of failures are early perception errors, not reasoning errors, and an early error cascades. The cure is procedural, not motivational.

1. Whole chart first. State the one sentence shape of the whole chart before studying any region. Place zooms deliberately. Do not auto crop.
2. Axis and frame inventory. Confirm axis direction, log or linear scale, timeframe, and any breaks. Never assume the frame.
3. Legend and series registry. Map every colour and line to its series before reading a value off it: which line is the 20, the 50, the 200, which pane is volume, which is RSI, which is MACD.
4. Transcribe before interpreting. Write down the key values first: swing highs and lows, moving average values, volume extremes, the distance from price to each level in ATR. Eyeball arithmetic is forbidden for load bearing numbers.
5. Context before pattern names. List trend, structure, volume regime, and market regime before any pattern word is used.
6. Describe, then decide, with verification. Narrate observations, then interpret them, and reverify each load bearing observation against the pixels and against Pass A.
7. Counter deception sweep. Ask explicitly: is the axis inverted, is the timeframe cherry picked, is volume missing, is the visible window survivorship in disguise?
8. Mark and enumerate for counts. When the read depends on a count of touches, tests, or legs, mark each one and count per region.

Two further rules from the skill govern the multi timeframe work. Agreement across timeframes is one witness, not confirmation, because the 10m, 1H, and daily frames share the same underlying transactions. Name what the lower frame adds that the daily does not already show, or do not cite it as separate support. When the whole read hinges on one contested visual feature, render the chart twice, with and without that feature, and drop the read if it does not survive the pair.

### The Pass B write up, in order

- Open with the reference class in one line: the setup family the name resembles, or a plain statement that no family is established here.
- Name the cycle position before any indicator: impulse leg, correction leg, terminal pattern, or base. This is rule 1 adopted from the Echo and Max playbook.
- Describe structure next: weekly regime, daily stage, and 1H rhythm, with every level named by its anchor and its distance in ATR. Lead with location, trend and regime, volatility, participation, and structural maturity. A named pattern is an interpretation of those relationships, not a starting point.
- Give the volume verdict as the tell, and let it falsify or cap conviction. The working questions are concrete: selling climax at the lows, breakout on expanding volume, volume drying on pullbacks, expanding red volume on the 1H as the first distribution tell. No volume shown means the read says so and conviction is capped.
- Answer the two questions separately: is the name still going up, and is it safe to buy here. Never merge them. A yes to the first never implies a yes to the second.
- Build the three branch scenario tree described in the synthesis step below.
- Close with a pre-mortem on how the read is wrong in two weeks and a self critique that states the strongest case against the delivered lean.
- Tag every substantive claim with one evidence class: computed, measured, lit derived, derived inference, validated model, or judgment. Drop any claim that has no computed or measured anchor.
- Keep language neutral and verifiable. Describe what price did. Do not use claims about hidden actors or trapped participants that OHLCV cannot prove.

Volume discipline has a desk wide data rule behind it, recorded in the standing desk law: any volume weighted signal on hourly or finer bars uses Alpaca SIP. Yahoo hourly volume is disqualified for that use. A master does not build a volume tell on a feed she knows is corrupt.

## Step 3: Strategy lenses

In full analysis mode only, run the lenses after the visual read is written, so the lenses cannot contaminate the eye.

- Run `python3 bin/lenses.py --symbol SYM` from the stock analysis skill. Report each lens from its own ledger and universe. Do not reimplement sleeve rules inside the read.
- Label every lens with its edge class: CORE, VALIDATED, WATCH, CONTESTED, or EXPERIMENTAL.
- Report a CONTESTED lens with both verdicts and lean on it with nothing.
- Let a lens that does not apply say so once and go silent. Report no signal on record where that is the state. Never present a missing lens as neutral bullish.
- Exclude the GBM rule sleeves and morning_dip from the lens set entirely.
- Run the structural screen, `python3 -m desk.structural_screen SYM`, and report its verdict as INTACT, WATCH, BROKEN, or UNKNOWN with its reasons. On BROKEN, the final stance is capped at neutral negative no matter what any lens says.

The Echo lens in Silicon, `femto/core/echo_lens.py`, is the model for how a lens should behave. It produces evidence from frozen published constants drawn from six Kit newsletter issues and a 240 chart X corpus. It gates nothing and vetoes nothing. A lens adds a voice. It does not become the verdict.

## Step 4: Market context

No single name read is allowed to claim more than its market allows.

- Run a quick Pass A on SPY, and add QQQ where relevant. Name the index regime in the read: price against its 50 and 200, SPY above or below its 200 day line as the regime proxy used by the genome calibration slices.
- Name sector membership and relative strength. Compare the name against its sector and against SPY before raising conviction on a single name pattern.
- Add the context conditioners where present: Wikipedia attention tags, the sentiment composite with the components driving it rather than the headline alone, and ChartsLector pulse and theme state. Report a missing Wikipedia row as no or low attention record, not as a positive. All three conditioners can strengthen or weaken a stance. None of them creates one.
- Add positioning terrain where the terminal carries it. The Morning Map in the terminal census is the teaching example: call wall as ceiling, put wall as floor, zero gamma flip as the regime divider, net GEX sign as amplifier above or absorber below, read beside dark pool pressure and never substituted for it. Wall Check then grades whether those walls held, touched and held, or blew through, so the level is read with its own record attached.
- Treat breadth the same way: percent above the 50 day and 200 day, advancers against decliners, and sector rotation over 5 and 21 sessions. Breadth confirms or contradicts an index trend. It does not rescue a broken single name structure.

Market location caps the read. State the cap in words when it binds: for example, a constructive single name structure inside a SPY regime below its 200 day line carries lower conviction and a shorter leash than the identical structure with the index above it.

## Step 5: Synthesis

Synthesis is not averaging. It is accounting.

- Present the lens table first: whether each lens applies, its edge label, and its signal state.
- State consilience where VALIDATED and CORE lenses agree. Count agreement among correlated lenses once and say so. The terminal Second Opinion and Echo Board visuals teach the same rule visually: agreement is drawn by independent family, not by raw count.
- State every conflict between lenses, and between the technical read and the lenses, baldly in its own section. Never smooth or average a conflict away.
- Name the gap as the finding when it is the finding: the chart is bullish but no validated lens has a signal, or the reverse.
- Name what would change the read per lens, with the trigger or invalidation for each.
- Deliver a final stance only as strong as the weakest required evidence. Name which layer owns it: signal, structure, or context. Abstention is a valid final stance and is never converted into a call. ABSTAIN is an evidence status, not a bearish call, and insufficient evidence is never dressed up as AVOID.

### The scenario tree

Every full read carries a three branch scenario tree. For each branch that has a visible trigger, state:

- Trigger: the price event that activates the branch, named in advance with its price.
- Confirmation: the close or reaction that confirms it.
- Target: the price, with its method named (see construction below).
- Invalidation: the price and condition that kills the branch.
- Confidence: LOW or MED only. Never HIGH on a single read.

Leave a branch empty when it has no visible trigger. An empty branch is information. Inventing a trigger to fill the tree is a failure mode, not completeness.

Close the tree with one conditional verdict line in the Echo and Max grammar, level named and patience explicit: losing a named level confirms the move to the named buy zone. Draw both the primary and the alternate scenario in words, each with its terminus price, so the read carries its own invalidation geometry on the page.

Use the cadence limits the skill imposes. At most one read per ticker per day unless new information arrives, and at most ten reads per calendar day. Fatigue is a measured failure source in the desk calibration record, not a character flaw to push through.

## Step 6: Constructing the plan

### The buy zone

A buy zone is a box, not a line, and it is earned by confluence. This is the shared rule of the Echo and Max playbook, the Echo Algorithm (`~/workspace/.scratch-x-charts/echo-algorithm/ECHO-ALGORITHM.md`), and `chart_read.py`.

Construction, step by step:

1. Start from a named swing, wick to wick. Swings use highs and lows, never closes. Name the swing by its dates and prices in the read.
2. Draw the retracement on that swing for pullback depth. For the core trade in the Echo method, a completed impulse followed by a correction terminating at the fib band is the structure: 0.5 to 0.618 for a shallow correction, 0.786 to 0.887 for the deep bottoms Echo hunts. In the coded Echo lens the wave 2 zone is 0.5 to 0.786 with the sweet spot at 0.618 to 0.786, and a retrace beyond 0.886 downgrades conviction rather than extending the zone indefinitely.
3. Score the candidate zone for independent shelves landing inside the same ATR band:
   - a fib retracement of the parent move,
   - a fib extension of a sibling leg,
   - a moving average cluster inside the zone, with the 50 as the actionable pivot and the 200 or 200 week as the regime line and final backstop,
   - a trendline arriving at the zone,
   - a prior pivot shelf that acted as support or resistance,
   - a round number.
4. Apply the threshold. A lone fib is a watch level, not a zone. The Echo Algorithm requires at least two fib constructions in the same zone before it is called high probability, and the playbook requires an MA cluster, trendline arrival, or prior shelf to promote a fib band to a buy zone. CAVA in the playbook is the worked example: a 0.5 to 0.618 band sitting exactly on the 200DMA.
5. Wait for the reaction. Echo does not buy the level itself. A zone becomes a setup only when price reacts at it on closes: a bullish engulfing or hammer at the zone, or a close back above the 9 or 21 EMA after touching the zone, with bounce bar volume above the pullback mean. Until a reaction prints, the state is WATCH. A starter at the zone and full size on the moving average flip is the sizing grammar in the playbook. The trigger is always named in advance: the 50MA reclaim or loss, or the zone reaction itself.
6. Check the trap screen before promoting any apparent flag or continuation. The Echo Algorithm names four signs: too shallow, volume wrong, no three waves in the pullback, and too quick, with pullback duration below 25 percent of the impulse duration as the quickness test. Two or more signs reclassify the expected path to a B wave rejection watched at the 0.5 to 0.786 retrace of the pullback, with a C leg to follow.

Trendline discipline applies inside the zone work. Draw at most two trendlines, anchored on confirmed major pivots spanning the whole pattern, months not wiggles. Two points make a hypothesis. Three or more touches validate it. A line price has already closed through decisively is dead, reported as dead, and not redrawn to fit.

### Invalidation

Invalidation is born with the read, not added after a loss. A verdict that cannot name its invalidation is not emitted. That is Echo law and desk law.

- State invalidation as a close based condition at a named price: a close below the bottom of the buy zone, below the 200 week average, or below the start of the move, according to the structure claimed.
- For an Echo impulse entry, invalidation is the start of wave 1, the 1.0 retracement, as the absolute. For the nested 1 to 2, 1 to 2, it is below the start of the larger wave 1.
- For an Elliott count, use the structural invalidation price the counter in `femto/core/elliott_wave.py` emits with every count. Its three inviolable rules are checked in code, counts are classified as ACTIVE_COUNT, AMBIGUOUS, NO_VALID_COUNT, or INVALIDATED, and ambiguity is a first class answer. The anti repaint audit, streaming against prefix, is the standard: a count that changes its past when new bars arrive was never a count.
- Respect the stop distance lesson from the desk chart reading method: stops tighter than 1.5 ATR were consumed by noise before the thesis could work in the autopsied record, so 1.5 ATR is the floor and 1.5 to 2.5 ATR is the working band for swing reads. State the ATR at the time of the read, so the distance can be checked later.
- Distinguish wick from close in the invalidation sentence itself. A wick through the zone does not kill it. A close below the zone bottom does. Write which one applies before price gets there.

### Targets, labelled by role and by method

Every target carries two labels: its role and its method. A price with neither label is decoration.

Roles, in ladder order:

- T1: the first stall or partial zone. In the Echo ladder, T1 is the wave 3 1.272 stall watch.
- Objective: the primary target the plan is judged against. In the Echo ladder, the 1.618 extension of wave 1, measured with the trend based extension tool.
- Extended: the 2.0 to 2.618 case, flagged only when momentum carries through 1.618.

Methods, kept separate because the calibration record shows they are not interchangeable:

- Recorded level: the nearest material tested level, a prior high, a round number, a measured base top, a wall. In the genome calibration cross check, recorded level objectives reached first most often among the three kinds.
- Pattern measured move: the height of the named pattern projected from the breakout or trigger line, as coded in the Test repo `patterns.py` for bases, flags, double tops and bottoms, and triangles, with confirmation and trigger lines drawn. The CRA report on Bulkowski verified patterns adds the scaling discipline: targets are scaled by the target percent for the pattern, not taken at full height by default, and a confirmation close is required before the target is live.
- Projected: a fib extension or wave projection with no recorded level behind it. Label it projected wherever it appears. The retracement tool and the extension tool produce different 1.618 prices, and substituting one for the other is, in Echo words, the mistake that costs people money. Use retracement for pullback depth on waves 2 and 4 and post cycle corrections. Use the three point trend based extension for targets on waves 3, 5, and C.

Volume confirms the target path or it does not. The Test repo pattern engine uses expansion on the break, with 1.4 times as its breakout volume confirmation reference, and the desk chart law uses contraction inside the pattern and expansion on the break. A breakout toward a target on contracting volume caps conviction and is stated as a cap in the read.

### R to target

R is printed, computed, and judged to the final objective.

- Define risk per unit as entry reference minus invalidation. Define reward to a target as target minus entry reference. R to that target is reward divided by risk.
- Compute and show R to T1 and R to the objective. The Best Setups chart law, carried in `setup_call.py`, is explicit: logical R to the final objective governs, R to T1 is shown, and a setup with R below 1 to its objective never boards.
- Print R on the chart itself, not only in the text. A reader who has to calculate R from three separate numbers scattered across a brief does not have R.
- Record R in the log at read time. In the desk calibration design, R and R:R are recorded for scoring, not used as a tripwire to force a call. Expectancy, built from the base rate and the R actually on offer, is the decision variable. A beautiful R attached to an unmeasured pattern is still unmeasured.

Worked arithmetic, in the form every read should show: entry reference at the zone reaction close, invalidation at the zone bottom close, objective at the recorded level above. If entry is 62, invalidation is 58, and the objective is 74, risk is 4, reward is 12, and R to objective is 3.0. If T1 is 68, R to T1 is 1.5 and is shown beside it. Change any one of the three prices and both Rs are recomputed and reprinted. Never carry an old R onto a new chart.

## Step 7: Drawing the chart, the annotation standard

The annotation standard comes from the Best Setups chart law, implemented in Silicon in `femto/core/chart_spec.py`, `setup_brief.py`, and `setup_card.py`, and visible as a finished corpus in the Femto setup charts library: 233 PNGs across 27 tickers with daily, weekly, monthly, card, and plan variants.

One spec, two surfaces. A single chart spec object is consumed by both the card renderer and the plan chart renderer, so the setup card and the plan chart draw and label identically. If the two surfaces disagree, the chart is defective, not artistic.

What every finished plan chart draws, without exception:

- The buy zone as a shaded box, labelled, at the forefront in layman clear language.
- Invalidation as an explicit labelled line, with its price.
- Targets labelled by role: T1, objective, extended where it exists, each with its price and, in the brief, its method.
- The named pattern itself, drawn on the price pane: the base, flag, triangle, double bottom, wedge, or wave count that the call claims. A pattern that is named in text but not drawn is not yet a call.
- At most two trendlines, labelled where drawn as Resistance line or Support line, anchored on the confirmed pivots the read cites.
- Every moving average the call cites in its why, and no uncited average clutter. `chart_spec.py` cross checks the drawn averages against the geometry to the cent and fails closed on a mismatch. The palette is single and fixed: one colour per average across every surface.
- The dashed expected path into reserved future space. Reserve empty space to the right of the last bar before drawing. The primary path is drawn dashed from the trigger area to the objective, with its shape honest to the scenario: direct, pullback then advance, or rejection then decline. The alternate scenario path is drawn as well, in the alternate colour Echo uses, orange or red against the primary white, with its terminus box visible on the same chart. The chart carries its own alternative.
- Volume, RSI, and MACD panes below price, in that stack. Divergences are drawn only where the record carries them: a divergence line appears on price and on the indicator pane only when Pass A or the chart record actually contains that divergence pair at a pattern extreme. No decorative divergence lines. Divergence at extremes only is also a reading rule: bearish divergence at a pattern top or wedge terminal, bullish divergence at a correction low, arming the level while the moving average reclaim or loss pulls the trigger.
- The expiry clock on the chart: the date or session count at which the setup expires untriggered. A setup without an expiry is a permanent opinion.
- R printed on the chart, to T1 and to the objective.
- The trigger price, named as the trigger.

What never gets traded away under deadline pressure: the buy zone, the invalidation, the labelled targets, the named pattern drawn, the dashed expected path, the three panes with honest divergences, the expiry clock, and R on the chart. The Femto census records the same list as the standing law for its setup charts. Removing any one of them to make a chart cleaner makes it less of a plan and more of a picture.

Reader surface discipline, from the same law: the front of the card is layman clear, with buy zone, invalidation, and target at the forefront, the full gestalt and the evidence list underneath with origin stamped numbers, present tense and actionable only. Internal codenames and disclaimer style copy do not belong on the reader surface.

Before a chart is finished, run the fail closed cross checks the spec enforces in code, by eye if necessary: do the drawn averages match the geometry values, do the trendline labels match the lines drawn, does the zone on the chart match the zone in the text to the cent, does the invalidation on the chart match the invalidation in the scenario tree, and does the printed R recompute from the three printed prices? Any no stops the publish.

## Step 8: Logging the read

A read that is not logged cannot be graded, and a reader who cannot be graded cannot improve on purpose.

Log, at read time, in the places the skill specifies:

- The Pass A JSON at `~/workspace/research/composite-confidence/reads/<SYM>_<date>_passa.json`.
- The renders in `~/workspace/research/composite-confidence/reads/<SYM>_<date>/`.
- The written read at `~/workspace/research/composite-confidence/reads/<SYM>_<date>.md`, containing the reference class, cycle position, structure, volume tell, lens table in full mode, market context, conflicts, the three branch tree with triggers and invalidations, the plan construction with zone, invalidation, targets by role and method, both Rs, the pre-mortem, the self critique, and the evidence tag on each load bearing claim.
- Dated triggers for every branch with a clean trigger. Those logs are the raw material of the prospective scored record. Where the user asks for it, offer a trigger watch that stays silent unless a trigger fires. A paper order is placed only on the user explicit word, through the paper skill. The log entry is not an order.

The grading machinery in Silicon, `femto/core/calibration.py`, shows what the log must contain to be gradeable later: each call is scored against its own geometry as target hit, invalidated, expired triggered, or expired untriggered, with per voice and per class scorecards, process grade separated from outcome grade, and a visual against geometry disagreement ledger. If the log does not record the geometry, there is nothing to score against, and the review degenerates into memory.

## The 2 to 4 week review loop

Every read is reviewed at two horizons. Two weeks tests whether the timing and the trigger were honest. Four weeks tests whether the structure and the target were honest. Swing reads in this system are built for that window, and the desk calibration scorecards use 20 day and 60 day outcome windows for the same reason at a larger scale.

At each review, in order:

1. Pull the original log entry, the original renders, and the original Pass A. Do not review from a fresh chart alone. The question is what the read said then, judged on what happened after.
2. Score the branch first. Which branch triggered, if any? Did price reach the objective before invalidation, hit invalidation first, expire triggered without resolution, or expire untriggered? Use the call own geometry, with the same session both hit rule the genome calibration uses: on daily bars, when objective and invalidation are both touched in one session, count invalidation first, because daily bars cannot order intraday events.
3. Grade process separately from outcome. A correct process that lost is a keep. A sloppy process that won is a defect to cure, not a win to celebrate. Name which failure, if any, was perceptual, geometric, contextual, or judgmental.
4. Run the disagreement check. Where did the eye and Pass A disagree, then or now? Log the disagreement. The disagreement ledger is where the next perception cure comes from.
5. Check the volume tell and the trigger honesty. Did volume confirm or falsify as the read predicted it would? Did the reader wait for the reaction or front run the level?
6. Check the plan arithmetic. Was the invalidation respected as a close based rule? Was R as printed the R that was actually on offer at the trigger close?
7. Write the autopsy in the read file or its review companion, in plain sentences: what the read got right, what it got wrong, and the one change the next read will make because of it. The composite confidence calibration record, 30 blind reads with scorecards and per sample autopsies, is the local model: wins and losses mined for what separated them, with the changes carried into the next protocol version.
8. Aggregate monthly. Count by setup family, by reader voice or lens, and by confidence label. A label that wins less often than the label below it is uncalibrated and gets renamed or retrained before it is used again. A family with enough scored calls and no expectancy loses decisive eligibility until its reads improve. That leash rule is stated in `calibration.py` and it applies to Midna own families first.

The review loop is also where base rates get earned personally. A master quotes the genome table for the prior and her own scored log for the posterior about her own eye. Both numbers travel with the next read when they exist. When neither exists, the read says so.

## Master failure modes of the eye, and their cures

These are not moral failings. They are known operating characteristics of a visual system reading noisy series, and each one has a procedural cure already built into the protocol above. The master runs the cure before the failure costs money.

### 1. Recency: the last bars shout, the pattern whispers

Symptom: the read is dominated by the last three to five bars. A strong final bar turns a basing structure into a breakout in the prose. A weak final bar turns an intact uptrend into a breakdown. The weekly chart, which governs, gets one sentence.

Cure: enforce the order. Weekly regime first, written before the daily is described. Render all four timeframes before writing the reference class line. Transcribe the full pattern swing anchors, with dates, before transcribing the last bar. If the one sentence gestalt of the whole chart and the one sentence summary of the last week disagree, name the disagreement in the structure section and let the higher timeframe govern, with the daily timing it. The Echo rule is the same: the weekly count governs, the daily times it.

### 2. Anchoring: the first level named becomes the level defended

Symptom: an early price, a round number mentioned in conversation, a prior read invalidation, or the first fib drawn becomes the anchor, and later geometry is bent around it. Zones migrate toward the anchor instead of toward confluence.

Cure: compute blind and transcribe first. Pass A runs before any level is discussed, and its clusters are written down before the eye draws anything. Score every candidate zone by its confluence stack on paper, including the anchor candidate, and let the count decide. Draw the alternate scenario with its own terminus on every chart, which forces a second anchor into view. On a re read, recompute Pass A fresh rather than extending the earlier verdict, as the skill alternative directs. If a level cannot cite its anchor swing, its MA, or its shelf, it leaves the chart.

### 3. Forcing patterns: seeing the beloved shape in ordinary noise

Symptom: every consolidation becomes a flag, every three pushes become a head and shoulders, every correction becomes the wave count the reader wanted to trade. The pattern name arrives in the first minute, the checklist never runs, and the confirmation close is waived because the shape looks right.

Cure: confirmation law and checklists, run out loud. In `chart_read.py` no pattern is a call before its confirmation close. Elite detectors go first, cup with handle, rounding bottom, double bottom and top, head and shoulders, selling climax base, while triangles and pennants are demoted to context until they confirm. Wedges carry gates: five or more touches and three or more weeks in that engine record, or the wedge word is not used. Run the Echo checklist for the claimed family: for an impulse, five legs not three, the three inviolable rules held, wave 3 the strongest leg, pullbacks smaller and quieter, each wave in its fib zone. Run the WYFI trap screen on every claimed continuation. Run the CRA triangle touch and crossing test and the pattern shape tolerances before the name is kept. If a rule fails, the impulse or pattern claim ends there and the read falls back to structure language: range, base, extension, breakdown recovery. ABSTAIN and NO TRADE are valid outputs of the Echo Algorithm, and leaving a scenario branch empty is the same discipline at tree level.

### 4. Wick versus close confusion: treating an intraday probe as a decision

Symptom: a long wick through support is read as a breakdown, or a wick into a zone is read as a rejection and an entry, depending on which story the reader prefers. Stops are placed inside wick noise, and reactions are claimed on bars that never closed anywhere near the level.

Cure: predefine the rule per level before looking at the outcome, and write it in the invalidation and trigger sentences. The desk default is close based: zones are judged on closes, a wick through the zone does not kill it, a close below the zone bottom does. The sweep section of the chart reading method states the same requirement: predefine wick versus close rules before looking or the read is unfalsifiable, then trade the reaction after a sweep, acceptance with closes back inside and follow through against rejection with a wick and immediate reversal. Anchoring for fib and swings is wick to wick, because swings are defined by extremes, while decisions on those swings are close based, because entries and invalidations are decisions. Confusing the two jobs is the error. Keep them in separate sentences: anchors from extremes, triggers and invalidations from closes. Apply the kind aware test rule as well: a test is classified by what the bar actually did against the level, extreme and close both recorded, not by the story told about it afterwards.

### Supporting cures the master also runs

- Pattern name before context: cured by the perceptual protocol step that inventories context before any pattern call.
- Counting one episode as many touches: cured by episode based cluster accounting in Pass A.
- Stacking correlated evidence: cured by counting correlated lenses and correlated timeframes once in synthesis.
- Inventing a base rate from impression: cured by quoting only the published genome table or her own scored log, or stating that no base rate is established.
- Confidence inflation: cured by the LOW or MED cap on a single read and by the monthly label calibration in the review loop.
- Missing volume treated as neutral: cured by the explicit cap. No volume, capped conviction, stated in the read.

## The one page checklist

Before a read leaves the desk, confirm each line:

- Pass A run fresh, data status handled, JSON saved.
- Four renders viewed, image and geometry reconciled.
- Cycle position named before indicators.
- Whole chart gestalt, axis inventory, series registry, transcription done before interpretation.
- Structure described with levels anchored and distances in ATR.
- Volume verdict stated as the tell, with its cap if volume is missing.
- Two questions answered separately.
- Lenses run in full mode, labelled by edge class, structural screen verdict applied as a cap.
- SPY and QQQ context, sector, and conditioners stated, with the cap they impose.
- Lens table first in synthesis, consilience counted once, conflicts stated baldly, gap named where it is the finding.
- Three branch tree complete, empty branches left empty, confidence LOW or MED, conditional verdict line written.
- Buy zone built from a named swing with confluence scored, reaction state named as WATCH or SETUP.
- Invalidation named as a close based price, born with the count or structure claimed.
- Targets labelled by role and method, retracement and extension tools not substituted.
- R to T1 and R to objective computed, shown, and printed on the chart, with R below 1 to objective excluded from boarding.
- Chart drawn to spec: pattern drawn, at most two labelled trendlines, cited averages only, dashed primary and alternate paths into reserved future space, volume RSI MACD panes, divergences only where the record carries them, expiry clock present.
- Read logged with Pass A, renders, and dated triggers.
- Review dates set at two weeks and four weeks.

A read that passes this checklist is a working read: geometric, perceptual, contextual, falsifiable, drawn, and gradeable. That is the standard this playbook teaches, and it is the standard the next section assumes.
