# griffith-htf-conditional-h1-h8: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Tensor HTF conditional holdout (H1-H8)", type "forecast and ML models", family "griffith", style evidence "Tensor signal + context", universe "Tensor research roster's operating companies", asset class "US equities", timeframe "1d · 1w", creator/source "Griffith Tensor HTF research (TENSOR_HTF_CONDITIONAL_HOLDOUT_1_0_0), as a forward-test book". Algorithm grade PARTIAL (sources: Test catalog entry/variants); the accounting records no entry, exit or sizing rules and lists the gaps: entry/signal rule not in the record, exit rule not in the record, sizing not in the record. The rules below therefore come from the strategy card and the code/spec files in Test named in Files, not from the accounting.
- Test catalog entry `griffith-htf-conditional-h1-h8` in `docs/CATALOG.json` (card and code list as in Files).
- Frozen spec in Test: `sleeves/griffith/vendor/griffith/tensor_htf_holdout_spec.json` (version TENSOR_HTF_CONDITIONAL_HOLDOUT_1_0_0, frozen 2026-08-27, holdout from 2025-01-01, minimum 20 mature events and 20 matched controls in the spec gates).
- Searched at batch start (fresh trees, 2026-10-30 run): Test, Silicon, quant-research-backup and Midna, for the canonical id, its alias and family terms. No code for this id was found in Silicon, quant-research-backup or Midna (except the Anna replica traces noted where applicable); the code named below is already in Test.

## What this strategy is

A forward-test book (spec TENSOR_HTF_CONDITIONAL_HOLDOUT_1_0_0) that buys fresh daily or weekly Tensor signals matching one of eight frozen conditional labels H1-H8, and holds them 20 sessions (daily) or 12 weeks (weekly). Universe is the roster's operating companies.

## Full algorithm

From the card `strategies/griffith/griffith-htf-conditional-h1-h8.md` and the holdout spec, in evaluation order:

1. Universe: the roster's operating companies (current metadata).
2. Labels: H1 a weekly buy-cyan with an annualized 20-bar volatility >= 60% and a 20-bar median dollar volume of $20-100M; H2 a weekly buy-cyan above a rising EMA 200; H3 a weekly buy-cyan with the fast and slow states bullish; H4 a daily buy-green above a rising EMA 200 with a 20/60-bar range ratio <= 0.75 and a 20-bar breakout; H5 a daily bounce buy above a rising EMA 200; H6 a daily buy-green with a participation footprint active; H7 a fresh daily participation footprint; H8 a weekly bounce buy while consensus-sell is active. Spec ids H1_WEEKLY_CYAN_HIGH_VOL_MID_LIQ through H8_WEEKLY_BOUNCE_DURING_CONSENSUS_SELL, all LONG.
3. Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it. Entry: the next session's open, a market order within that session; skipped once it has passed.
4. Exit: close of bar 20 (daily) or week 12 (weekly), market-on-close. Spec primaryHorizon: 1d 20, 1wk 12.
5. Sizing: One slot per event: the $100,000 book / (1,838 names x 2 timeframes) = about $27, split equally among the event's sub-lots; skipped when the book lacks the cash; a modeled cost of 50 bp a side (spec adverse round-trip cost 100 bps).
6. Card note, preserved: on the desk's 10-year weekly tape the 20-bar volatility is annualized with sqrt(252) (the feature code treats any tape over 300 bars as daily), so H1's 60% line sits near 27% on a weekly sqrt(52) basis.

## Files in this repo

- This doc: `docs/GRIFFITH_HTF_CONDITIONAL_H1_H8-RECREATE.md`
- Strategy card: `strategies/griffith/griffith-htf-conditional-h1-h8.md`
- Rule lines: `docs/verify/griffith.md`
- Code (already in Test): `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_features.py`, `sleeves/griffith/vendor/griffith/tensor_htf_holdout_spec.json`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`

## Configuration

- Universe: Tensor research roster's operating companies. Timeframes: 1d and 1w. Book: $100,000.
- Labels H1-H8 as listed. Horizons: 20 daily bars / 12 weekly bars. Modeled cost: 50 bp a side.
- Slot: about $27 per event.
- State: per-event label, frame and entry bar for the horizon count.

## Data inputs

Completed regular-session daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 (card Data section). Weekly-only variants use weekly bars (10 years) only.

## Install and run

1. Clone the Test repo.
2. Read this doc, the strategy card named in Files, and the accounting entry for `griffith-htf-conditional-h1-h8` in `docs/ALL-SLEEVES.json`.
3. Open `sleeves/tensor_research/tensor_research.py` and the frozen spec `sleeves/griffith/vendor/griffith/tensor_htf_holdout_spec.json`; confirm the candidate/hypothesis ids and horizons match Configuration. Serve the completed daily/weekly roster bars listed under Data inputs, run the roster scan, and enter only on the bar just completed as the algorithm states.
4. Verify against the Verification section before any live use.

## Verification

No dedicated test file for this sleeve was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- A fresh signal matching none of H1-H8 produces no entry; a non-operating-company name produces no entry.
- Only a signal new on the bar just completed enters, at the next session's open, within that session only.
- Daily positions exit at the close of bar 20 and weekly positions at the close of week 12, market-on-close, with no earlier signal exit.
- H1 requires both the volatility line and the $20-100M median dollar-volume band.
- Each event takes one about-$27 slot at a modeled 50 bp a side.
