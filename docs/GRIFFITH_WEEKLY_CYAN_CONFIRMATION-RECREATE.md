# griffith-weekly-cyan-confirmation: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Tensor weekly cyan confirmation (CY01-CY18)", type "forecast and ML models", family "griffith", style evidence "Tensor signal + context", universe "Tensor research roster's operating companies", asset class "US equities", timeframe "1w", creator/source "Griffith Tensor HTF research (TENSOR_WEEKLY_CYAN_CONFIRMATION_1_0_0), as a forward-test book". Algorithm grade PARTIAL (sources: Test catalog entry/variants); the accounting records no entry, exit or sizing rules and lists the gaps: entry/signal rule not in the record, exit rule not in the record, sizing not in the record. The rules below therefore come from the strategy card and the code/spec files in Test named in Files, not from the accounting.
- Test catalog entry `griffith-weekly-cyan-confirmation` in `docs/CATALOG.json` (card and code list as in Files).
- Frozen spec in Test: `sleeves/griffith/vendor/griffith/tensor_htf_weekly_cyan_spec.json` (version TENSOR_WEEKLY_CYAN_CONFIRMATION_1_0_0, frozen 2026-08-27, purgeDays 84, negativeControlIds CY17 and CY18 in the spec).
- Searched at batch start (fresh trees, 2026-10-30 run): Test, Silicon, quant-research-backup and Midna, for the canonical id, its alias and family terms. No code for this id was found in Silicon, quant-research-backup or Midna (except the Anna replica traces noted where applicable); the code named below is already in Test.

## What this strategy is

A confirmation book (spec TENSOR_WEEKLY_CYAN_CONFIRMATION_1_0_0, waiting status) that buys a fresh weekly buy-cyan fitting any of 18 frozen context hypotheses CY01-CY18 (two of them negative controls, traded like the rest) and holds it 12 weeks, at most once per hypothesis and name every 84 days. Universe is the roster's operating companies.

## Full algorithm

From the card `strategies/griffith/griffith-weekly-cyan-confirmation.md` and the cyan spec, in evaluation order:

1. Universe: the roster's operating companies (current metadata).
2. Hypotheses (each on the fresh weekly buy-cyan; each match is a sub-lot): CY01 above a rising EMA 200, compressed (20/60-week range ratio <= 0.75). CY02 CY01 plus a close at or above the prior 20-week high. CY03 above a rising EMA 200, the first cyan in 26 weeks. CY04 above a rising EMA 200, participation footprint active. CY05 above a rising EMA 200, consensus-buy active. CY06 above a rising EMA 200, fast and slow states bullish. CY07 compressed, a 20-week breakout, the prior 52-week high <= 15% above, not extended. CY08 the first cyan in 26 weeks, compressed, a 20-week breakout, not extended. CY09 repaired, the active call bullish after a reversal. CY10 repaired, participation footprint active. CY11 >= 30% under the prior 52-week high, repaired. CY12 a bounce buy 1-8 weeks before, repaired. CY13 a sell-red, sell-magenta or consensus-sell 1-8 weeks before, repaired. CY14 the first cyan in 26 weeks, the prior 52-week high <= 15% above, not extended. CY15 above a rising EMA 200, within 15% of the prior 52-week high, not extended. CY16 tight (range ratio <= 0.45), a bullish candle regime, not extended. CY17 below a falling EMA 200 (a negative control). CY18 extended (a negative control).
3. Definitions from the card: Repaired = not below a falling EMA 200, above EMA 21, no more than 3% under EMA 50, a positive 20-week return. Extended = >= 15% over EMA 21 or a 20-week return >= 50%.
4. Purge: a hypothesis takes a name again only 84 days after its last event there (spec purgeDays 84).
5. Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it. Entry: the next session's open, a market order within that session; skipped once it has passed.
6. Exit: close of week 12, market-on-close (spec primaryHorizonWeeks 12).
7. Sizing: one slot per event: the $100,000 book / (1,838 names x 1 timeframe) = about $54, split equally among the event's sub-lots; skipped when the book lacks the cash; a modeled cost of 50 bp a side.

## Files in this repo

- This doc: `docs/GRIFFITH_WEEKLY_CYAN_CONFIRMATION-RECREATE.md`
- Strategy card: `strategies/griffith/griffith-weekly-cyan-confirmation.md`
- Rule lines: `docs/verify/griffith.md`
- Code (already in Test): `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_features.py`, `sleeves/griffith/vendor/griffith/tensor_htf_weekly_cyan_spec.json`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`

## Configuration

- Universe: Tensor research roster's operating companies. Timeframe: 1w only. Book: $100,000.
- Hypotheses CY01-CY18 as listed; purge 84 days per hypothesis and name. Horizon: 12 weeks. Modeled cost: 50 bp a side.
- Slot: about $54 per event.
- State: per-hypothesis last-event date per name (purge), entry week, and matched hypothesis ids.

## Data inputs

Completed regular-session daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 (card Data section). Weekly-only variants use weekly bars (10 years) only.

## Install and run

1. Clone the Test repo.
2. Read this doc, the strategy card named in Files, and the accounting entry for `griffith-weekly-cyan-confirmation` in `docs/ALL-SLEEVES.json`.
3. Open `sleeves/tensor_research/tensor_research.py` and the frozen spec `sleeves/griffith/vendor/griffith/tensor_htf_weekly_cyan_spec.json`; confirm the candidate/hypothesis ids and horizons match Configuration. Serve the completed daily/weekly roster bars listed under Data inputs, run the roster scan, and enter only on the bar just completed as the algorithm states.
4. Verify against the Verification section before any live use.

## Verification

No dedicated test file for this sleeve was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- A fresh weekly buy-cyan matching no hypothesis produces no entry; CY17 and CY18 (negative controls) are traded like the other hypotheses.
- A hypothesis does not take a name again within 84 days of its last event there.
- The Repaired and Extended definitions are applied exactly as stated in step 3 wherever a hypothesis uses them.
- Only a signal new on the bar just completed enters, at the next session's open, within that session only; every position exits at the close of week 12.
- Each event takes one about-$54 slot, split equally among its sub-lots, at a modeled 50 bp a side.
