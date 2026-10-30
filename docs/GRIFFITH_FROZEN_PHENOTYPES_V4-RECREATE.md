# griffith-frozen-phenotypes-v4: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Tensor frozen phenotypes v4", type "forecast and ML models", family "griffith", style evidence "Tensor phenotype", universe "Tensor research roster: 1,838 US names", asset class "US equities", timeframe "1d · 1w", creator/source "Griffith Tensor research (tensor-frozen-phenotype-specifications/4.0.0), as a forward-test book". Algorithm grade PARTIAL (sources: Test catalog entry/variants); the accounting records no entry, exit or sizing rules and lists the gaps: entry/signal rule not in the record, exit rule not in the record, sizing not in the record. The rules below therefore come from the strategy card and the code/spec files in Test named in Files, not from the accounting.
- Test catalog entry `griffith-frozen-phenotypes-v4` in `docs/CATALOG.json` (card and code list as in Files).
- Frozen spec in Test: `sleeves/griffith/vendor/griffith/tensor_phenotype_registry.json` (version tensor-frozen-phenotype-specifications/4.0.0, status FROZEN_PENDING_PROSPECTIVE_OBSERVATIONS, selection count 4, prospective horizons [4, 13, 26] bars in each frame, minimum 30 events / 20 distinct symbols / 2 calendar regimes before inference in the registry contract).
- Searched at batch start (fresh trees, 2026-10-30 run): Test, Silicon, quant-research-backup and Midna, for the canonical id, its alias and family terms. No code for this id was found in Silicon, quant-research-backup or Midna (except the Anna replica traces noted where applicable); the code named below is already in Test.

## What this strategy is

A forward-test book trading the four enabled frozen Tensor phenotypes of registry version tensor-frozen-phenotype-specifications/4.0.0: one daily green base-expansion phenotype and three weekly consensus-buy phenotypes. Positions close in thirds after 4, 13 and 26 bars.

## Full algorithm

From the card `strategies/griffith/griffith-frozen-phenotypes-v4.md` and the registry `tensor_phenotype_registry.json`, in evaluation order:

1. Scope: phenotypes are evaluated on the market-scan context (the last 420 daily or 260 weekly bars), only on bars after the registry's late-August 2026 freeze (registry freezeCutoffEpoch 1788246012; feature version tensor-market-features/1.2.0).
2. The four enabled phenotypes: (a) a daily buy-green passing the base-expansion test (above a rising EMA 200, a range ratio <= 0.75, a 20-bar breakout, under 15% over EMA 21, constructive participation); registry source H4_DAILY_GREEN_BASE_EXPANSION. (b) A weekly buy-green early markup out of a recovery. (c) A weekly buy-cyan accumulation out of a recovery. (d) A weekly buy-cyan early markup. The weekly three are each READY with bullish-aligned energy, deep normal participation and a consensus-buy enrichment.
3. Only the bar just completed counts, its signal new on that bar, and the roster's run publishes once at least half its names reach it. Entry: the next session's open, a market order within that session; skipped once it has passed.
4. Exit: three equal sub-lots at the close of bars 4, 13 and 26, market-on-close.
5. Sizing: One slot per event: the $100,000 book / (1,838 names x 2 timeframes) = about $27, split equally among the event's sub-lots; skipped when the book lacks the cash; a modeled cost of 15 bp a side.

## Files in this repo

- This doc: `docs/GRIFFITH_FROZEN_PHENOTYPES_V4-RECREATE.md`
- Strategy card: `strategies/griffith/griffith-frozen-phenotypes-v4.md`
- Rule lines: `docs/verify/griffith.md`
- Code (already in Test): `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_features.py`, `sleeves/griffith/vendor/griffith/tensor_phenotype_registry.json`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`

## Configuration

- Universe: Tensor research roster, 1,838 US names. Timeframes: 1d and 1w. Book: $100,000.
- Phenotypes enabled: 4 (1 daily, 3 weekly) as listed in the algorithm. Scan context: last 420 daily / 260 weekly bars.
- Slot: about $27 per event; modeled cost 15 bp a side. Exit thirds at bars 4, 13, 26.
- State: per-event sub-lot schedule (4/13/26) and frame.

## Data inputs

Completed regular-session daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 (card Data section). Weekly-only variants use weekly bars (10 years) only.

## Install and run

1. Clone the Test repo.
2. Read this doc, the strategy card named in Files, and the accounting entry for `griffith-frozen-phenotypes-v4` in `docs/ALL-SLEEVES.json`.
3. Open `sleeves/tensor_research/tensor_research.py` and the frozen spec `sleeves/griffith/vendor/griffith/tensor_phenotype_registry.json`; confirm the candidate/hypothesis ids and horizons match Configuration. Serve the completed daily/weekly roster bars listed under Data inputs, run the roster scan, and enter only on the bar just completed as the algorithm states.
4. Verify against the Verification section before any live use.

## Verification

No dedicated test file for this sleeve was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- A phenotype match on a bar at or before the registry freeze cutoff produces no entry.
- Only a signal new on the bar just completed enters, at the next session's open, and only within that session.
- Each position exits in three equal sub-lots at the closes of bars 4, 13 and 26 of its own frame, with no other exit.
- A weekly phenotype without READY state, bullish-aligned energy, deep normal participation and consensus-buy enrichment does not qualify.
- Each event takes one about-$27 slot, split equally among its sub-lots, at a modeled 15 bp a side.
