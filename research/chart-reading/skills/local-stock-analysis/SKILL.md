---
name: stock-analysis
description: Full stock analysis and on-demand chart reading in one protocol, running Pass A geometry, the perceptual Pass B read, edge labeled strategy lenses, market context and a rigorous synthesis whenever the user names a ticker to read or analyze.
version: 1.0.0
---

# Stock and Chart Analysis

## Why this skill exists

The default: Scoring a name on whichever facts are loudest today.
The cost: A ranking assembled from raw fields and fresh headlines moved on noise and stood still on facts, the exact inversion of a discipline.
The replacement: Run the frozen lenses in order, move a score only on a new fact, and log every read so the next read answers to it.



# Stock and Chart Analysis

## Choose the mode

- Run chart read mode when the user names a ticker and asks for a read, a chart check or what the name is doing, and deliver Pass A, the renders and Pass B only.

- Run full analysis mode when the user asks to analyze a stock, and add the strategy lenses, the structural screen, market context and the synthesis to the same Pass A and Pass B work.

- Keep both modes paper only and state that a read is not an order and never implies one.

## Run Pass A geometry

- Run `python3 bin/pass_a.py --symbol SYM` from ~/workspace/skills/chart-read for a fresh deterministic compute and never work from memory.

- Read the data_status field first and stop with no analysis at all on NO_VIEW, carry the staleness caveat through the whole output on STALE, and name what is missing on PARTIAL.

- Save the Pass A JSON to ~/workspace/research/composite-confidence/reads/<SYM>_<date>_passa.json with the symbol and date in the file name.

- Use the Pass A output for weekly regime, daily structure, confirmed pivots, EMA and ATR values, volume against its average, close location, level tests, gaps, level clusters, momentum indicators, divergence pairs, pattern primitives, the 1H rhythm and the 10m refinement.

- Use pivots with both their extreme time and their availability time, because a pivot is learned only at confirmation and never at the extreme bar itself.

- Use kind-aware level tests on recent swings, because a bar below a prior high can never be a rejected-low-test and each test kind carries its own meaning.

- Use level clusters built as 2.5 ATR-scaled pivot zones, and read touches against independent episodes rather than counting repeated touches on one episode as separate evidence.

- Re run `python3 bin/test_pass_a.py` after any edit to pass_a.py and require all 18 checks green before trusting the output, because the parity test carries 18 checks and all must pass.

## Render and look

- Render weekly, daily, 1H and 10m charts with `python3 render_asof.py --symbol SYM` from ~/workspace/research/composite-confidence/calibration into the dated reads folder at ~/workspace/research/composite-confidence/reads/<SYM>_<date>/.

- View the actual PNG files with `muse.read` and never narrate from Pass A numbers alone.

- Work the perceptual protocol in order, covering the whole chart before its parts, the axis and frame inventory, the legend and series registry, transcription of key values before interpretation, context before pattern names, and a counter deception sweep.

- Stop and reconcile when the image and Pass A disagree on a material fact, checking bar completeness, provisional status, adjustment basis and axis scale instead of narrating through the disagreement.

- Treat agreement across timeframes as one witness rather than confirmation, because the 10m, 1H and daily frames share the same underlying transactions, and name what the lower frame adds that the daily does not already show.

- Render the chart twice, with and without a contested visual feature, when the whole read hinges on that feature, and drop the read if it does not survive the pair.

## Deliver the Pass B read

- Open with the reference class in one line, naming the setup family the name resembles or stating that no family is established here.

- Describe structure next, covering weekly regime, daily stage and 1H rhythm, with every level named by its anchor and its distance in ATR.

- Lead the structure section with location, trend and regime, volatility, participation and structural maturity, and treat a named pattern as an interpretation of those relationships rather than a starting point.

- Give the volume verdict as the tell and let it falsify or cap conviction.

- Answer the two questions separately, whether the name is still going up and whether it is safe to buy here, and never merge them.

- Build a three branch scenario tree with a trigger, a confirmation, a target with its method, an invalidation and a confidence of LOW or MED for each branch, never HIGH on a single read, and leave a branch empty when it has no visible trigger.

- Close with a pre-mortem on how the read is wrong in two weeks and a self critique that states the strongest case against the delivered lean.

- Tag every substantive claim with one evidence class from computed, measured, lit-derived, derived-inference, validated-model or judgment, and drop any claim that has no computed or measured anchor.

- Keep language neutral and measured, describing what price did in verifiable words, and never use claims about smart money, genuine accumulation, distribution or trapped participants that OHLCV cannot prove.

- Treat ABSTAIN as an evidence status rather than a call, and never convert no view into a bearish call or dress insufficient evidence up as AVOID.

- Quote a base rate only from a published table or state that the base rate is not established here, and never invent a base rate from impression or memory.

- Name the cycle position before indicators, covering impulse leg, correction leg, terminal pattern or base, and let the lean follow from that position.

- Build levels as zones with confluence, scoring each candidate fib zone for an MA cluster inside it, a trendline arriving there, a prior pivot shelf and a round number, and treat a lone fib as a watch level rather than a zone.

- Draw at most two trendlines anchored on confirmed major pivots spanning the whole pattern, and treat a line price has already closed through as dead.

- Count RSI or MACD divergence only at pattern extremes, let it arm a level, and name the 50MA reclaim or loss or the zone reaction as the trigger in advance with its price.

- Draw both the primary and alternate scenarios with a terminus price for each, and close the read with one conditional verdict line in the form of losing a named level confirms the move to the named buy zone.

- Save the read to ~/workspace/research/composite-confidence/reads/<SYM>_<date>.md with the symbol and date in the file name.

- Run at most one read per ticker per day unless new information arrives, cap reads at 10 per calendar day, cap conviction when volume is missing and state that cap, and treat anything not visible as not known.

## Add lenses and structure in full analysis mode

- Run `python3 bin/lenses.py --symbol SYM` from ~/workspace/skills/stock-analysis and report each strategy lens from its own ledger and universe without reimplementing sleeve rules.

- Label every lens with its edge class from CORE, VALIDATED, WATCH, CONTESTED or EXPERIMENTAL, report a CONTESTED lens with both verdicts, and lean on it with nothing.

- Let a lens that does not apply say so once and go silent, report no signal on record where that is the state, and never present a missing lens as neutral bullish.

- Exclude the GBM rule sleeves and morning_dip from the lens set entirely.

- Run `python3 -m desk.structural_screen SYM` from ~/workspace/alpaca-swing-desk and report the INTACT, WATCH, BROKEN or UNKNOWN verdict with its reasons, capping the final stance at neutral negative on BROKEN no matter what any lens says.

- Read SPY regime with a quick Pass A on SPY, add QQQ where relevant, and name sector membership, letting market location cap what any single name read can claim.

- Add Wikipedia attention tags, the sentiment composite with the components driving it, and ChartsLector pulse and theme state where present, and treat all three as context conditioners that can strengthen or weaken a stance but never create one.

- Report a missing Wikipedia row as no or low attention record rather than as a positive, and report the sentiment components rather than the headline alone.

## Synthesize the full analysis

- Present a lens table first, covering whether each lens applies, its edge label and its signal state.

- State consilience where VALIDATED and CORE lenses agree, counting agreement among correlated lenses once and saying so.

- State every conflict between lenses and between the technical read and the lenses baldly in its own section, and never smooth or average a conflict away.

- Name the gap as the finding when the chart is bullish but no validated lens has a signal, or the reverse.

- Name what would change the read per lens, with the trigger or invalidation for each.

- Deliver a final stance only as strong as the weakest required evidence, name which layer owns it from signal, structure or context, and treat abstention as a valid final stance that is never converted into a call.

- Run batch mode for two to ten tickers by completing every phase per name, then delivering a comparative table ordered by structural quality with INTACT first and BROKEN last, never ordered by raw signal strength.

## Turn a read into action

- Offer a trigger watch for any branch with a clean trigger, setting a cron that runs `bin/watch_trigger.py --symbol SYM --read-date <date> --bullish-above X --bearish-below Y` from the chart-read skill and notifies the user only when a trigger fires and stays silent otherwise.

- Place a paper order only on the user explicit word through the alpaca paper skill, because a read is not an order.

- Log every read with dated triggers, because those logs are the raw material for the prospective scored record.

## Available connectors

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Alternatives for better results

- Recompute Pass A fresh when a read feels stale instead of extending a verdict from an earlier run.

- Compare the name against its sector and against SPY before raising conviction on a single name pattern.


## Addenda (fragments, load before applying addendum rules)

- Technical Analysis Mastery addendum: {{fragment:ta-mastery-addendum@d0101d5527e0a108}}
- External Canon addendum: {{fragment:external-canon-addendum@f8aa6340a86f2ac5}}
Fragment files live in the fragments/ directory beside this SKILL.md; resolve each reference by name and verify its sha256 pin before use.

## Dependencies, named

This skill runs Pass A from the chart-read skill folder. Install chart-read beside it; without that folder, Pass A does not run and any read produced is UNVERIFIED.
