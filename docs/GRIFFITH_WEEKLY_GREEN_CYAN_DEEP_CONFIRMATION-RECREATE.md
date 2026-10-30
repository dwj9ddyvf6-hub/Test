# griffith-weekly-green-cyan-deep-confirmation: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Tensor weekly green / cyan deep confirmation (WG / WC)", type "forecast and ML models", family "griffith", style evidence "Tensor signal + context", universe "Tensor research roster's operating companies", asset class "US equities", timeframe "1w", creator/source "Griffith Tensor HTF research (TENSOR_WEEKLY_GREEN_CYAN_DEEP_CONFIRMATION_1_0_0), as a forward-test book". Algorithm grade PARTIAL (sources: Test catalog entry/variants); the accounting records no entry, exit or sizing rules and lists the gaps: entry/signal rule not in the record, exit rule not in the record, sizing not in the record. The rules below therefore come from the strategy card and the code/spec files in Test named in Files, not from the accounting.
- Test catalog entry `griffith-weekly-green-cyan-deep-confirmation` in `docs/CATALOG.json` (card and code list as in Files).
- Frozen spec in Test: `sleeves/griffith/vendor/griffith/tensor_htf_weekly_color_spec.json` (version TENSOR_WEEKLY_GREEN_CYAN_DEEP_CONFIRMATION_1_0_0, frozen 2026-08-27, purgeDays 84, adverse round-trip cost 100 bps in the spec).
- Searched at batch start (fresh trees, 2026-10-30 run): Test, Silicon, quant-research-backup and Midna, for the canonical id, its alias and family terms. No code for this id was found in Silicon, quant-research-backup or Midna (except the Anna replica traces noted where applicable); the code named below is already in Test.

## What this strategy is

A deep-confirmation book (spec TENSOR_WEEKLY_GREEN_CYAN_DEEP_CONFIRMATION_1_0_0, waiting status) that buys a fresh weekly buy-green or buy-cyan meeting any of 24 frozen two-condition candidates WG01-WC14 and holds it 12 weeks, at most once per candidate and name every 84 days. Universe is the roster's operating companies.

## Full algorithm

From the card `strategies/griffith/griffith-weekly-green-cyan-deep-confirmation.md` and the weekly color spec, in evaluation order:

1. Universe: the roster's operating companies (current metadata).
2. Candidates on a fresh weekly buy-green: WG01 ATR >= 12% of price and close at or above the upper Bollinger band. WG02 ATR >= 12% and the Tensor cycle over 10 bars old. WG03 ADX 20-35 and >= 15% over EMA 21. WG04 SPY above a rising EMA 200 and up-week volume >= 60% of 13 weeks'. WG05 SPY above a rising EMA 200 and 4-week volume >= 1.35 x the 20-week. WG06 ATR >= 12% and 20/60-week range ratio <= 0.45. WG07 a close at or above the prior 13-week high and a bullish candle regime. WG08 range ratio <= 0.45 and relative volume >= 1.2. WG09 26-week beta >= 1.5 and a close at or above the prior 26-week high. WG10 13- and 26-week returns above SPY's.
3. Candidates on a fresh weekly buy-cyan: WC01 >= 15% over EMA 21 and SPY above a rising EMA 200. WC02 the Tensor cycle BULL_WEAK and 4-week volume >= 1.35 x the 20-week. WC03 Bollinger bandwidth >= 0.50 and SPY above a rising EMA 200. WC04 ATR >= 12% and SPY above a rising EMA 200. WC05 the cycle's momentum diverging and SPY above a rising EMA 200. WC06 26-week beta >= 1.5 and the cycle BULL_WEAK. WC07 SPY above a rising EMA 200 and 4-week volume >= 1.35 x the 20-week. WC08 ATR >= 12% and fast and slow states bullish. WC09 26-week return above SPY's and SPY above a rising EMA 200. WC10 range ratio 0.45-0.75 and SPY above a rising EMA 200. WC11 ATR >= 12% and a close at or above the prior 13-week high. WC12 Bollinger bandwidth >= 0.50 and the cycle's momentum diverging. WC13 a bounce buy 1-8 weeks before. WC14 the cycle BULL_WEAK and a buy-green 1-8 weeks before.
4. Each match is a sub-lot. Purge: a candidate takes a name again only 84 days after its last event there (spec purgeDays 84).
5. Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it. Entry: the next session's open, a market order within that session; skipped once it has passed.
6. Exit: close of week 12, market-on-close (spec primaryHorizonWeeks 12).
7. Sizing: one slot per event: the $100,000 book / (1,838 names x 1 timeframe) = about $54, split equally among the event's sub-lots; skipped when the book lacks the cash; a modeled cost of 50 bp a side.

## Files in this repo

- This doc: `docs/GRIFFITH_WEEKLY_GREEN_CYAN_DEEP_CONFIRMATION-RECREATE.md`
- Strategy card: `strategies/griffith/griffith-weekly-green-cyan-deep-confirmation.md`
- Rule lines: `docs/verify/griffith.md`
- Code (already in Test): `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_features.py`, `sleeves/griffith/vendor/griffith/tensor_htf_weekly_color_spec.json`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`

## Configuration

- Universe: Tensor research roster's operating companies. Timeframe: 1w only. Book: $100,000.
- Candidates WG01-WG10 and WC01-WC14 as listed; purge 84 days per candidate and name. Horizon: 12 weeks. Modeled cost: 50 bp a side.
- Slot: about $54 per event.
- State: per-candidate last-event date per name (purge), entry week, and matched candidate ids.

## Data inputs

Completed regular-session daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 (card Data section). Weekly-only variants use weekly bars (10 years) only.

## Install and run

1. Clone the Test repo.
2. Read this doc, the strategy card named in Files, and the accounting entry for `griffith-weekly-green-cyan-deep-confirmation` in `docs/ALL-SLEEVES.json`.
3. Open `sleeves/tensor_research/tensor_research.py` and the frozen spec `sleeves/griffith/vendor/griffith/tensor_htf_weekly_color_spec.json`; confirm the candidate/hypothesis ids and horizons match Configuration. Serve the completed daily/weekly roster bars listed under Data inputs, run the roster scan, and enter only on the bar just completed as the algorithm states.
4. Verify against the Verification section before any live use.

## Verification

No dedicated test file for this sleeve was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- A fresh weekly marker meeting none of the 24 candidates produces no entry; both conditions of a candidate must pass.
- A candidate does not take a name again within 84 days of its last event there.
- Green candidates apply only to buy-green markers and cyan candidates only to buy-cyan markers.
- Only a signal new on the bar just completed enters, at the next session's open, within that session only; every position exits at the close of week 12.
- Each event takes one about-$54 slot, split equally among its sub-lots, at a modeled 50 bp a side.
