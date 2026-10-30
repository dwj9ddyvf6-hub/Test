# Section 3: The Patterns Canon

## How to use this canon

A pattern is not a picture to recognise. It is a record of a fight, drawn in a strict order, with a trigger, an invalidation, and a target that were all named before price resolved. Read every pattern in this section the same way.

1. Name the cycle position first. Is this a base after a decline, a pause inside an advance, or a top after a long run? The local stock analysis skill requires cycle position before any indicator is quoted, and the Echo and Max playbook at `~/workspace/research/chart-methodology/PLAYBOOK_echo_max_2026-10-12.md` opens every chart with one question: where are we in the cycle, and what single level decides it?
2. Draw with at most two boundary lines, anchored on confirmed major pivots that span the whole pattern. If a pattern needs five lines, there is no pattern. A line price has already closed through is dead. Do not redraw it to save the idea.
3. Read volume inside the shape before you read the breakout. Contraction inside, expansion on resolution is the house rhythm. Volume is the tell, and it can cap or falsify conviction.
4. Wait for the confirmation close. Never label a pattern confirmed before its confirmation close, a rule stated in the Chart Reading Mastery and Annotation CRA report (Bulkowski evidence base, read 2026-10-15). An intraday poke through a line is an alert, not a confirmation.
5. Draw both scenarios and the full plan on the chart. Under the Best Setups chart law, preserved in the Silicon best-setups-engine tree (`femto/core/setup_brief.py`, `setup_card.py`, `setup_call.py`, `chart_spec.py`), every plan chart draws the buy zone, the invalidation, targets labelled by role, the named pattern itself, a dashed expected path into reserved future space, and volume, RSI, and MACD panes, with R and the expiry clock printed on the chart. The Test repo engine makes the same demand in code: `packages/claude/master-desk-terminal-builder/desk/terminal/read/patterns.py` gives each pattern a trigger line, a break line, and a measured move target, and `read/plan.py` turns that read into a plan.
6. Scale the measured move. The CRA rule is absolute: compute the target as breakout price plus or minus pattern height multiplied by the share of cases that actually reached the full height. Never annotate the unscaled height as the target. Then place the first target at a recorded level where one exists, because the desk calibration found recorded levels were reached before invalidation more often than pure pattern projections.
7. Expect the retest. Throwbacks and pullbacks to the breakout level occur in roughly 62 to 68 percent of cases across cup and handle, head and shoulders, double bottoms, and triangles in the Bulkowski sample. Draw a retest zone at the breakout level by default, and judge the breakout after the retest resolves, not during it.

### The house calibration: how a master checks her own reads

The desk measured its own patterns instead of borrowing someone else's confidence. The genome calibration (`~/workspace/.scratch-setups-build/pattern-calibration/PATTERN-CALIBRATION.md`, live product at `~/workspace/femto-lean/core/pattern_calibration.py`) covered the canonical 1,838 name genome roster, 1,514 served names, Alpaca SIP split adjusted daily bars, signal dates 2020-01-02 to 2026-10-16, and 2,390,032 pattern instances, scored in R and ATR(14) units with objective first, invalidation first, or neither within the family horizon. Use it as a master uses any calibration: to set how far to trust a target, how long a pattern normally takes, and which direction slice you are actually in.

Selected readings that shape the practice in this section:

| Family, desk slice | Measured n | Objective first | Invalidation first | Median sessions | What the master does with it |
|---|---:|---:|---:|---:|---|
| Cup with handle, long | 7,064 | 25.2% | 61.5% | 17 | Treat the full cup depth as a ceiling, not a promise. Work the scaled target and the retest. |
| Symmetrical triangle, long slice | 5,064 | 58.5% | 39.8% | 6 | Direction matters enormously. Grade a long resolution and a short resolution as different patterns. |
| Symmetrical triangle, pooled | 10,880 | 28.2% | 70.3% | 5 | Do not trade the pooled label. Trade the resolved direction with its own record. |
| Ascending triangle, long slice | 2,425 | 42.1% | 54.9% | 7 | Respect the flat top, but require the close and the volume. |
| Head and shoulders bottom, long | 2,865 | 44.2% | 39.7% | 25 | One of the sturdier reversal shapes. Give it time, weeks not days. |
| Head and shoulders top, short | 2,924 | 43.2% | 46.1% | 21 | A slow top. The neckline close is the event, not the right shoulder alone. |
| Double bottom, confirmed with lawful objective | 140 | 54.3% | 20.7% | 30.5 | Small measured subset, strong record. The confirmation filter is doing the work. |
| Double top, short | 356 | 55.9% | 19.4% | 24 | Same lesson mirrored. Wait for the peak between the tops to break. |
| Pennant, pooled | 972 | 18.3% | 72.4% | 6 | Demand the pole, the tightness, and the expansion. A loose pennant is just drift. |
| Falling wedge, long slice | 1,006 | 46.5% | 48.9% | 9 | A genuine contest. Confirmation decides, not the wedge label. |
| Rising wedge, pooled | 1,551 | 13.3% | 85.2% | 5 | Treat a rising wedge inside an advance as a warning shape first, in the Echo and Max manner: divergence at a wedge terminal arms the level below. |

Two calibration disciplines follow from the full tables. First, bull flags, bear flags, channels, and horizontal bases carried no lawful objective in the census, so they were counted and left unmeasured rather than given invented targets. Do the same on a live chart: if a flag has no clean pole and no recorded level beyond it, say the target is unmeasured and work from the pole and the next recorded level only. Second, targets split by kind. Recorded level objectives were reached first 39.9% of the time, pattern measured moves 27.0%, and projected objectives 30.4%. So the house order for targets is: recorded level first, scaled measured move second, projection last and labelled as a projection.

For cross checking, the Bulkowski bull market samples in the CRA report rank the same families the master should prioritise: cup with handle (5% break even failure, 61% reached the full target, n 913), rounding bottoms, double bottoms (about 12% break even failure, 65 to 72% reached target depending on the Adam and Eve variant), and head and shoulders. Symmetrical triangles, wedges, and pennants sit lower in those ranks, which is exactly why this canon demands stricter confirmation from them.

## 1. Bases: the ground every other pattern stands on

A base is a sideways repair after a decline or a long advance, long enough for supply to be absorbed and for the last weak holder to leave. The desk engine in `read/patterns.py` bounds a base at roughly 15 to 65 bars and no more than about 5 ATR or 25% deep. Deeper and longer is no longer a base on that timeframe. Call it a stage change and move up a timeframe.

Common drawing rules for all bases:

- Draw the top as a horizontal resistance zone across the base highs, not a single price line. Draw the bottom across the base lows. Levels are zones in this house, following the Echo and Max skeleton: boxes, not lines.
- Mark the pivot: the highest high of the final contraction or the right rim of the base. That is the buy point. Mark the invalidation at the low of the final contraction, or below the base low for a wider base.
- Inside a good base, ranges narrow from left to right, closes improve, and down days get quieter. Inside a poor base, ranges stay wide, closes stay weak, and every rally is sold within days.
- Volume should dry up in the base, ideally to multi week lows in the final contraction, then expand on the breakout. The Test engine uses 1.4 times average volume as its breakout confirmation in `read/patterns.py` and `read/volume.py`. Treat that as the house expansion test: present, the breakout has participation; absent, it is on probation until a retest holds.

### 1a. Volatility Contraction Pattern (VCP)

Source lineage: Mark Minervini, carried in the census teacher and X files, and Qullamaggie style tightness in the terminal Breakout Scanner (Tool 66), which reads proximity to highs plus base tightness as its two axes.

**How it is drawn.** Find 2 to 4 contractions, occasionally up to 6, each a pullback inside a Stage 2 advance. Label each contraction by its depth from high to low, T1, T2, T3, T4, left to right. In a textbook VCP each contraction is roughly half the prior one, for example minus 25%, then minus 12%, then minus 5%. Draw one horizontal pivot line at the high of the final, tightest contraction. Draw nothing else. The footprint is the pattern: number of contractions, depth of the largest, tightness of the rightmost, and volume at each point.

**Volume inside.** Volume falls with each contraction, lowest in the final one, often at multi week lows. That dry up is the evidence that supply is absorbed. A contraction on expanding volume is not a contraction in this sense. It is distribution inside the base, and it resets the count.

**What confirms.** A close through the pivot on expanding volume, codified in the census at about 1.4 times the 50 day average or better. Do not chase an entry extended far above the pivot. The tight final contraction is what makes the stop small, typically 3 to 5% in a quality VCP, with 7 to 8% as the outer limit in the Minervini codifications. A close back below the pivot, then below the final contraction low, invalidates.

**Measured move.** A VCP has no classical height target of its own. Work in this order: the next recorded overhead level, then the depth of the largest contraction projected from the pivot as an outer reference, labelled as a projection. The desk calibration rule applies: never present that projection as the target.

**Expected path.** Draw the dashed path as a quick first leg up from the pivot, a shallow retest of the pivot zone that holds on light volume, then continuation. If the retest closes back inside the final contraction, the path is void and the base needs more time.

### 1b. Cup and handle

**How it is drawn.** The cup is U shaped, never V shaped, 7 to 65 weeks on a weekly read or the equivalent span on a daily read, with left and right rims near the same price. The decline into the cup and the recovery out of it should look symmetrical in time, even if not in every bar. The handle forms in the upper half of the cup only, lasts at least a week, and drifts down or sideways on a gentle slope. Draw the rim line across both rims, a short downtrend line across the handle highs for the early trigger, and the cup low as the structural floor. Bulkowski tolerances in the CRA report: a handle below the cup midpoint disqualifies the pattern, and rims far apart disqualify it.

**Volume inside.** Volume is heaviest at the left rim and the cup low, dries up along the bottom and through the handle, and is quietest at the handle low. Rising volume inside the handle while price drifts down is the wrong character. That is supply, not a shakeout.

**What confirms.** A close above the right rim, or for the early entry a close above the handle trendline, on heavy volume versus its average. Bulkowski break even failure is 5% in his bull market sample, the best headline number in this canon, and the desk still requires the close, because the genome calibration shows how demanding unfiltered mechanical detection is (cup with handle, 7,064 measured, median 17 sessions to resolution, median maximum favourable excursion 2.07 ATR). The master's edge is in the filtering: U shape, upper half handle, dry handle, rim confluence.

**Measured move.** Height is rim minus cup low. Scaled target: breakout price plus height multiplied by 0.61, the Bulkowski full target share. Record the full height only as the outer reference. First target: the nearest recorded level inside the scaled target where one exists.

**Expected path.** Expect the throwback. It occurs about 62% of the time. Draw the path up from the rim, back to a retest zone at the rim that holds and turns up on lighter volume, then toward the scaled target. A retest that closes below the handle low ends the pattern, not the retest.

### 1c. Flat base

**How it is drawn.** A flat base is a tight sideways shelf after an advance of at least about 20%, correcting no more than roughly 15%, lasting at least 5 weeks on a weekly read. Draw a box: top at the repeated highs, bottom at the repeated lows. The tighter and more even the box, the better the base. This is the Darvas box in modern dress, and the O'Neil lineage in the census X file lists flat bases and Darvas boxes among its core shapes.

**Volume inside.** Quiet and even, drying toward the right side, with any down days inside the box on lighter volume than the up days. One high volume down day that closes at the box low and is not recovered within days damages the base.

**What confirms.** A close above the box top on expansion, 1.4 times average as the house test. A close below the box bottom invalidates the base as a continuation pattern, though it may start a different, lower base.

**Measured move.** Height is box top minus box bottom. Project one box height from the breakout as the first objective, then check it against recorded levels and scale it if the move has already run far from the prior advance. Flat bases that form after a cup or after a first breakout often stack: measure each box separately and let the second box become the new plan when price reaches it.

**Expected path.** A direct move to the first objective, a retest of the box top, then a second leg. Draw it that way, with the box top becoming the support shelf in the dashed path.

### 1d. Coils and squeezes

**How it is drawn.** A coil is the smallest base: a run of progressively narrower ranges, often inside a Bollinger Band squeeze or a sequence of inside days, sitting near highs or above a rising moving average. Draw the small narrowing range with two short converging lines, or a tight box if the coil is flat. Mark the coil high as the trigger and the coil low as the invalidation. The distance between them is the risk unit, and in a good coil it is small enough to say in one breath.

**Volume inside.** Volume contracts to the lowest readings of the move. The desk census treats the Bollinger squeeze as its own family (51,515 measured, median 14 sessions, with a large neither at cap share), which teaches the right temperament: a squeeze promises expansion, not direction or timing. Direction comes from location, trend, and the break itself.

**What confirms.** A close outside the coil, in the direction of the larger trend, on expanding volume. A break against the larger trend needs a stronger close and a follow through day before it earns the same trust.

**Measured move.** Project the width of the base the coil sits on, or the prior leg, not the tiny coil width alone. The coil width sets risk, not reward. First target remains the next recorded level.

**Expected path.** Fast first, then judgement. Coils resolve quickly when they resolve at all. Draw a steep dashed first leg, then a decision point at the first recorded level. If price stalls back inside the coil range for two closes, retire the coil and redraw from the new structure.

## 2. Flags and pennants

**How they are drawn.** No steep pole, no flag. That is the CRA rule, and it is the first filter. The pole is a near vertical advance (or decline, for bear flags) over days to a few weeks. The flag then drifts against the pole at a gentle slope, bounded by two roughly parallel lines, lasting about 1 to 4 weeks. A pennant is the same idea compressed: a pole, then a tiny symmetrical triangle lasting days to about 3 weeks. Shorter and tighter than that is a coil. Longer and looser than that is a base. Draw the pole from its base to its tip, the two flag boundaries, the flag breakout line, and the flag low as invalidation.

**Volume inside.** Heavy on the pole, drying steadily through the flag or pennant, quietest just before the break. Volume that expands while the flag drifts down is the classic character failure. Price is resting, but someone is leaving in size.

**What confirms.** A close through the flag boundary in the direction of the pole, on expanding volume. For high tight flags, the CRA carries Bulkowski's stricter guidance: confirm on a close above the highest high of the whole pattern including the pole, not merely on a flag trendline break, which fails too often. Prefer tight flags. Skip loose, jagged ones whose price pokes outside the boundaries.

**Measured move.** Classical: pole height added to the flag breakout. House version, following the high tight flag evidence: target half the pole height added from the flag low, a level met about 82% of the time in the Bulkowski extraction, and treat the full pole projection as the outer reference. The genome calibration left bull and bear flags unmeasured for lack of a lawful objective, so on any flag with no recorded level near the half pole target, label the target as a pole projection and size your confidence accordingly. Desk pennant record: 972 measured, median 6 sessions, long slice objective first 36.9% against short slice 0.8%. Direction and pole quality are the whole game.

**Expected path.** Continuation at pole speed for the first leg, then a slowing into the half pole target, then either a new base or a retest of the flag. Draw the dashed path steep, then flattening. A flag that breaks, then immediately closes back inside its boundaries, has failed fast, and fast failure is information: exit the idea, do not average into it.

## 3. Triangles

General drawing law for all triangles, from the CRA touch and crossing test: a valid triangle needs at least 3 touches on one boundary and at least 2 on the other, with price repeatedly crossing the interior and filling it, not hugging one side and leaving white space. Draw both boundaries from confirmed pivots, extend them to the apex, and mark the apex date on the chart. Time box the pattern: symmetrical triangle breakouts occur on average about 74% of the way to the apex, ascending triangles about 64%. A triangle that drifts into its apex unbroken has lost its premise. Retire it.

Volume in every healthy triangle contracts as the apex approaches, then expands on the break. Inside volume in the Bulkowski sample declined 84 to 86% of the time in symmetrical triangles, so treat expanding internal volume as a warning, not an automatic disqualification, and treat breakout volume as the hard test.

### 3a. Symmetrical triangle

**How it is drawn.** Descending top boundary across lower highs, ascending bottom boundary across higher lows, converging to an apex. Neither side has the flat edge. That neutrality is the point: the pattern records balance, and the prior trend plus the resolution supply the direction.

**What confirms.** A close outside either boundary, with expansion, followed by follow through or a successful retest. Grade the two directions separately. In the desk calibration the long slice reached objective first 58.5% of the time (n 5,064) and the short slice 1.9% (n 5,816) under the census geometry, while Bulkowski's bull market sample breaks upward about 60% of the time. The master's habit from both records is identical: never quote a symmetrical triangle without naming the resolved direction and its own record.

**Measured move.** Height is the widest leg, first high to first low inside the pattern. Scaled targets from the CRA: breakout plus height multiplied by 0.58 for an upward break, breakout minus height multiplied by 0.36 for a downward break. The Elliott target zone in the census basis, 0.618 to 1.0 times the widest leg, is a useful outer band to draw as a zone, not a line.

**Expected path.** A thrust out of the break, a throwback to the broken boundary in about 62 to 65% of cases, then continuation to the scaled target. Draw the boundary, once broken, as the new support or resistance shelf in the dashed path.

### 3b. Ascending triangle

**How it is drawn.** A flat top, drawn as a horizontal zone across repeated highs at the same price, and a rising bottom across higher lows. Each test of the top that fails by less, on a shorter pullback, is the pattern working. The flat top is a shelf of supply being absorbed one test at a time.

**Volume inside.** Contracts on each pullback, with pullbacks getting shorter and quieter, and ticks up on each test of the top. Heavy volume on a failed test that drives price deep back into the pattern is a crack in the story.

**What confirms.** A close above the flat top on expansion. An early, lower conviction entry exists on the final higher low with a stop under it, but the canon entry is the close through the top. Desk record: long slice objective first 42.1%, median 7 sessions. Bulkowski: about 70% reached the full target on upward breaks, 44% on downward breaks, so a downside break of the rising bottom is a real pattern too, with a smaller scaled target.

**Measured move.** Height is flat top minus the first low. Scaled upward target: breakout plus height multiplied by 0.70. Downward, if the rising line breaks: breakout minus height multiplied by 0.44.

**Expected path.** Break, retest of the flat top from above (about 64% throwback rate), then the scaled move. The retest holding exactly at the old top is the cleanest continuation tell in this whole section. Draw it as the centre of the dashed path.

### 3c. Descending triangle

**How it is drawn.** Mirror image: a flat bottom across repeated lows, a descending top across lower highs. Each rally is sold sooner. Draw the flat floor as a zone, because repeated tests thin it.

**Volume inside.** Contracts overall, with the heaviest readings often on tests of the floor. A floor tested many times on rising volume is a floor being consumed.

**What confirms.** A close below the floor on expansion for the short or exit read, or, for the reversal reader, a close back above the descending top, which converts the pattern into a failed breakdown and a base candidate. Desk calibration warns against lazy direction assumptions here too: its long slice, which captures upside resolutions, reached objective first 49.0% (n 2,261). Read the resolution, not the label.

**Measured move.** Height is first high minus flat bottom, scaled by the same triangle factors as the direction of the break, and checked first against recorded levels below, which in a breakdown are often thin. Thin air below a broken floor is itself a fact to state in the read.

**Expected path.** Downward: a quick first drop, a pullback to the underside of the floor, then continuation. Upward resolution: a fast reclaim, because shorts built on the floor must cover, then a base building phase. Draw both until one confirms.

## 4. Wedges

**How they are drawn.** Two converging lines, both sloping the same way. A rising wedge slopes up with the lower line steeper, so the range narrows as price rises. A falling wedge slopes down with the upper line steeper. Bulkowski tolerances in the CRA: at least 5 touches in total, 3 on one side and 2 on the other, and at least 3 weeks of duration. Shorter than that, classify it as a pennant, not a wedge. Wedges are terminal shapes more often than continuation shapes, so always name what trend the wedge is ending or pausing.

**Volume inside.** Usually declines through the wedge, about 79% of the time in the Bulkowski tendency data, while range narrows. In a rising wedge late in an advance, watch for the Max Williamson tell from the Echo and Max playbook: RSI making lower highs across the whole advance while price still rises. Max draws those long divergence lines as a warning inside an intact trend, and Echo uses the same pairing, rising wedge plus bearish divergence at the terminal, to expect a breakdown. Divergence arms the wedge. The break of the lower line pulls the trigger.

**What confirms.** Rising wedge: a close below the lower boundary, ideally on expansion, with the prior swing low as the second confirmation. Falling wedge: a close above the upper boundary on expansion. Desk record keeps the reader honest and directional: falling wedge long slice objective first 46.5% with invalidation first 48.9%, a true contest decided by confirmation quality; rising wedge pooled objective first only 13.3%, which is why this canon treats a rising wedge resolution upward as the exception that must prove itself with volume and follow through.

**Measured move.** First target: the origin of the wedge, the swing where the converging move began. Wedges commonly retrace the entire wedge move. Outer target: height of the widest part of the wedge projected from the break, scaled down and labelled a projection. Do not draw the full height as the target.

**Expected path.** Rising wedge breakdown: a drop to the wedge origin, often faster than the wedge rose, with a pullback to the broken lower line on the way if the break is orderly. Falling wedge breakout: an accelerating rise as the narrowing resolves, a retest of the upper line, then continuation toward the wedge origin high and beyond. Draw speed honestly in the dashed path. Wedge resolutions are usually quicker than wedge formations.

## 5. Head and shoulders

### 5a. Head and shoulders top

**How it is drawn.** Three peaks: left shoulder, a higher head, and a right shoulder near the left shoulder in price, roughly equidistant from the head, and of similar width. Reject lopsided formations, per the CRA shape tolerances. Draw the neckline through the two troughs between the peaks. The neckline may slope. Its slope is information: a down sloping neckline says sellers are early, an up sloping one says the top is taking longer to build. Mark the right armpit, the trough low on the right side, because it is part of the confirmation rule.

**Volume inside.** In the classical record, volume is highest on the left shoulder, lighter on the head, and lightest on the right shoulder, trending down about 61% of the time. Treat that sequence as a strong tendency check, not a gate. A right shoulder that rallies on heavier volume than the head is a warning that the top may fail and become a base.

**What confirms.** A close below the neckline when the neckline slopes up, or a close below the right armpit when the neckline slopes down. That is the CRA confirmation rule, and it exists to stop the most common error in this canon: calling the top on the right shoulder alone. Desk record: 2,924 measured, objective first 43.2%, invalidation first 46.1%, median 21 sessions. This is a slow, contested pattern. The neckline close plus a failed retest is the master's full confirmation.

**Measured move.** Height is head peak minus the neckline at the head. Scaled target: breakdown price minus height multiplied by 0.51, the Bulkowski full target share for head and shoulders tops. Average decline in that sample was about 16%, far less than the full height in most cases, which is exactly why scaling is law here.

**Expected path.** Breakdown, then a pullback to the neckline in about 68% of cases, the highest retest rate in this section. Draw the neckline retest as the central event of the dashed path: a retest that is rejected at the neckline confirms and offers the second entry; a retest that closes back above the neckline and holds voids the top.

### 5b. Head and shoulders bottom (inverse)

**How it is drawn.** The mirror: three troughs, the middle one deepest, shoulders near each other in price and time, a neckline across the two intervening peaks. At bottoms, look also for the Echo signature underneath the shape: bullish divergence at the final low, and a neckline that arrives at a moving average cluster or a prior pivot shelf. Confluence upgrades the pattern from a shape to a zone.

**Volume inside.** Volume often expands into the head low in a climax, dries on the right shoulder, and must expand on the neckline break. A quiet neckline break at a bottom is weaker than a loud one.

**What confirms.** A close above the neckline, on expansion, with the 50 day average turning or reclaimed in the Max grammar: the reclaim is the trigger working alongside the neckline. Desk record: 2,865 measured, objective first 44.2%, invalidation first 39.7%, median 25 sessions, and the trend aligned slice improves to 50.8% objective first. Bottoms take time. Budget weeks in the plan and say so.

**Measured move.** Height is neckline at the head minus the head low, projected up from the breakout and scaled by the same family discipline as the top, then checked against recorded overhead levels, which at a real bottom are plentiful and should supply the first two targets.

**Expected path.** Breakout, retest of the neckline from above, then a stair step advance as overhead shelves are reclaimed one at a time. Draw the path as steps, not a straight line. Straight line paths at bottoms are fantasy drafting.

## 6. Double tops and double bottoms

**How they are drawn.** Two peaks or two troughs at near the same price. Bulkowski tolerances from the CRA: the two extremes within about 0 to 4% of each other, the intervening peak or trough at least about 10% away from them, and the pair typically 2 to 7 weeks apart, median about 23 days for one double bottom variant. Draw a horizontal zone across the two extremes, and a confirmation line across the intervening peak (for a bottom) or intervening trough (for a top). Note the Adam and Eve distinction where it is visible: a sharp, spiky extreme is Adam, a rounded one is Eve, and the variants carry slightly different records in the Bulkowski table. Name the variant when you can see it. It is free precision.

**Volume inside.** Double bottom: volume is often heavy at the first low, lighter at the second low, which is the supply drying tell, then heavy on confirmation. A second low on heavier volume than the first, with a weak close, is not the same pattern. Double top: lighter volume on the second peak is the classic tell, especially with divergence at the second peak, which in the Echo and Max grammar arms the intervening trough as the deciding level.

**What confirms.** Double bottom: a close above the peak between the two valleys. Without it, roughly 48% of apparent double bottoms in the Bulkowski record simply continued lower. That single statistic should govern your patience. Double top: a close below the trough between the two peaks. The genome calibration shows what the filter buys: double bottoms with a lawful confirmed objective reached it first 54.3% of the time against only 20.7% invalidation first, and double tops 55.9% against 19.4%, the two cleanest records in the desk tables, on small measured subsets (n 140 and n 356) precisely because most forming records never confirmed and were excluded. Confirmation is not ceremony. It is the edge filter.

**Measured move.** Height is extreme minus the intervening peak or trough. Scaled targets: breakout plus or minus height multiplied by 0.65 to 0.72 for double bottoms by variant, with the same scaling discipline applied to tops. Median resolution in the desk record is slow, 30.5 sessions for bottoms and 24 for tops, and median favourable excursion is large (3.32 ATR for bottoms), so plan for a long, wide move and do not judge the pattern in its first week.

**Expected path.** Confirmation, a throwback to the confirmation line in about 65 to 67% of cases, then the scaled move. Before confirmation, the expected path is a range between the extremes and the middle line, and the correct action inside that range is patience, in the Echo grammar: mid structure is corrective, not buy time. Draw the pre confirmation chart with both scenarios visible, primary and alternate, each with its terminus.

## 7. Ascending bases

The ascending base is the least famous pattern in this canon and one of the most useful, because it is how strong names climb stairs instead of elevators. It comes from the O'Neil lineage carried in the census X file, where ascending bases sit alongside cup and handle, flat bases, and double bottoms in the core vocabulary.

**How it is drawn.** Three successive pullbacks, each starting and ending higher than the last, like three steps up a staircase inside an advance. Each pullback corrects roughly 10 to 20% from its own peak in the classical description, lasts a few weeks, and the low of each pullback sits above the high ground of the prior one. Draw each small base as its own little box, three boxes ascending, and a rising line under the three pullback lows. If the boxes do not ascend, it is not an ascending base. It is a range.

**Volume inside.** Each pullback dries up relative to the advance before it, and each breakout from a step expands. The tell across the whole pattern is consistency: three quiet pullbacks in a row say holders are not leaving between advances.

**What confirms.** Each step confirms itself on its own close above its box top, so the pattern is tradable step by step, with the third step carrying the most information: by then the name has proven three times that pullbacks get bought higher. The full pattern fails when a pullback closes below the prior step's low. That breaks the staircase.

**Measured move.** Measure each step separately: box height projected from each box top, checked against recorded levels. Then measure the whole: first step low to third step high gives the outer frame. Work the step targets in the plan and keep the whole frame as context. Stacked measurements are the honest way to draw this pattern, the same stacking used for flat bases after cups in Section 1c.

**Expected path.** Step, rest, step. Draw the dashed path as three rising steps with flat rests, extending the rhythm one step beyond the chart only as a scenario, never as a promise. When an ascending base finally produces a wide range expansion day after the third step, treat it in the Minervini manner: volatility expansion after long contraction late in a move is a reason to tighten the read and watch for the first failed step, which is where this pattern ends.

## Closing discipline: the pattern checklist

Before any pattern in this canon enters a read, run the checklist the house sources agree on:

- Cycle position named, timeframe stated, prior trend stated.
- Boundaries drawn from confirmed pivots, at most two lines, touches counted, interior filled.
- Volume read inside the pattern and the expansion test named for the break, 1.4 times average in the desk engine.
- Confirmation close defined in advance, with its exact price.
- Invalidation defined in advance, with its exact price, and R computable from entry, target, and invalidation.
- First target at a recorded level where one exists; scaled measured move second; projection last and labelled.
- Retest zone drawn at the breakout level, and the read scheduled to be judged after the retest, not before.
- Desk calibration slice checked: family, direction, and measured n quoted where the calibration covers it, and unmeasured stated plainly where it does not, as with flags.
- Both scenarios drawn, primary and alternate, each with a terminus, in the Echo and Max manner.
- The chart itself carries the plan under the Best Setups chart law: buy zone, invalidation, labelled targets, named pattern, dashed expected path, volume, RSI, and MACD panes, R and expiry printed.

A pattern that passes this checklist is a plan. A pattern that fails it is a sketch, and sketches are allowed, as long as the read calls them sketches and waits.
