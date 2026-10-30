# griffith-weekly-color-forward-shadow: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Tensor weekly color forward shadow (FG / FC)", type "forecast and ML models", family "griffith", style evidence "Tensor signal + context", universe "Tensor research roster's operating companies", asset class "US equities", timeframe "1w", creator/source "Griffith Tensor HTF research (TENSOR_WEEKLY_COLOR_FORWARD_SHADOW_1_0_0), as a forward-test book". Algorithm grade PARTIAL (sources: Test catalog entry/variants); the accounting records no entry, exit or sizing rules and lists the gaps: entry/signal rule not in the record, exit rule not in the record, sizing not in the record. The rules below therefore come from the strategy card and the code/spec files in Test named in Files, not from the accounting.
- Test catalog entry `griffith-weekly-color-forward-shadow` in `docs/CATALOG.json` (card and code list as in Files).
- Frozen spec in Test: `sleeves/griffith/vendor/griffith/tensor_htf_weekly_color_forward_spec.json` (version TENSOR_WEEKLY_COLOR_FORWARD_SHADOW_1_0_0, frozen and effective 2026-08-28, forward-shadow observation only in the spec, horizons [1, 2, 4, 8, 12, 26, 52] weeks recorded).
- Searched at batch start (fresh trees, 2026-10-30 run): Test, Silicon, quant-research-backup and Midna, for the canonical id, its alias and family terms. No code for this id was found in Silicon, quant-research-backup or Midna (except the Anna replica traces noted where applicable); the code named below is already in Test.

## What this strategy is

A forward-shadow book (spec TENSOR_WEEKLY_COLOR_FORWARD_SHADOW_1_0_0, waiting status) that buys a fresh weekly buy-green or buy-cyan meeting any of 9 frozen two-condition candidates FG01-FC06 and holds it 12 weeks. Universe is the roster's operating companies.

## Full algorithm

From the card `strategies/griffith/griffith-weekly-color-forward-shadow.md` and the forward spec, in evaluation order:

1. Universe: the roster's operating companies (current metadata).
2. Candidates (each on the fresh weekly marker named; each match is a sub-lot; no purge): FG01 buy-green: SPY above a rising EMA 200 and 4-week volume >= 1.35 x the 20-week. FG02 buy-green: SPY above a rising EMA 200 and up-week volume >= 60% of 13 weeks'. FG03 buy-green: 13- and 26-week returns above SPY's. FC01 buy-cyan: a 13-week return of 25-60% and >= 20 points over SPY's. FC02 buy-cyan: the Tensor cycle over 10 bars old and ADX 20-35. FC03 buy-cyan: the cycle BULL_WEAK and up-week volume >= 60% of 13 weeks'. FC04 buy-cyan: a buy-green 1-8 weeks before and the cycle over 10 bars old. FC05 buy-cyan: the 4-week range under half the 13-week and a 13-week return >= 20 points over SPY's. FC06 buy-cyan: participation footprint active and a 13-week return of 25-60%.
3. Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it. Entry: the next session's open, a market order within that session; skipped once it has passed.
4. Exit: close of week 12, market-on-close.
5. Sizing: one slot per event: the $100,000 book / (1,838 names x 1 timeframe) = about $54, split equally among the event's sub-lots; skipped when the book lacks the cash; a modeled cost of 50 bp a side.

## Files in this repo

- This doc: `docs/GRIFFITH_WEEKLY_COLOR_FORWARD_SHADOW-RECREATE.md`
- Strategy card: `strategies/griffith/griffith-weekly-color-forward-shadow.md`
- Rule lines: `docs/verify/griffith.md`
- Code (already in Test): `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_features.py`, `sleeves/griffith/vendor/griffith/tensor_htf_weekly_color_forward_spec.json`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`

## Configuration

- Universe: Tensor research roster's operating companies. Timeframe: 1w only. Book: $100,000.
- Candidates FG01-FG03 and FC01-FC06 as listed; no purge. Horizon: 12 weeks. Modeled cost: 50 bp a side.
- Slot: about $54 per event.
- State: per-event candidate id(s) and entry week for the 12-week count.

## Data inputs

Completed regular-session daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 (card Data section). Weekly-only variants use weekly bars (10 years) only.

## Install and run

1. Clone the Test repo.
2. Read this doc, the strategy card named in Files, and the accounting entry for `griffith-weekly-color-forward-shadow` in `docs/ALL-SLEEVES.json`.
3. Open `sleeves/tensor_research/tensor_research.py` and the frozen spec `sleeves/griffith/vendor/griffith/tensor_htf_weekly_color_forward_spec.json`; confirm the candidate/hypothesis ids and horizons match Configuration. Serve the completed daily/weekly roster bars listed under Data inputs, run the roster scan, and enter only on the bar just completed as the algorithm states.
4. Verify against the Verification section before any live use.

## Verification

No dedicated test file for this sleeve was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- A fresh weekly marker meeting none of the 9 candidates produces no entry; both conditions of a candidate must pass.
- No purge applies: the same candidate may take the same name again on a later fresh marker.
- Only a signal new on the bar just completed enters, at the next session's open, within that session only.
- Every position exits at the close of week 12, market-on-close, with no earlier signal exit.
- Each event takes one about-$54 slot, split equally among its sub-lots, at a modeled 50 bp a side.
