# tr-ro-deep-reset-cross-scan: Recreation package

## Provenance

- Canonical id: `tr-ro-deep-reset-cross-scan`; canonical name: Deep Reset cross-scan; aliases: ro_deep_reset_cross_scan.
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, local census copy in research_notes/sleeve-census-20261029/accounting.json): type mean reversion, family tensor_research, algorithm grade PARTIAL; accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source. Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Deep Reset cross-scan" (also docs/ALL-SLEEVES.md); Test catalog entry 'tr-ro-deep-reset-cross-scan' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree; no matching sleeve path); dwj9ddyvf6-hub/Midna (recursive tree; research notes only as noted in Provenance, no deployable sleeve code for these ids).
- Code found: dwj9ddyvf6-hub/Test (code already in Test): sleeves/tensor_research/tensor_research.py + sleeves/tensor_research/feedlib/. No code was vendored for this strategy because the code already lives in Test at the paths below.

## What this strategy is

Deep Reset cross-scan: buys a name with a fresh Tensor buy (daily green, weekly green or cyan) that is not extended and reads as a deep reset, and sells at the close of its 15th session. Type: mean reversion. Accounting grade PARTIAL (entry, exit and sizing recorded as gaps in the accounting); the card and rule lines in this repo record all three.

## Full algorithm

From the strategy card `strategies/tensor_research/tr-ro-deep-reset-cross-scan.md` and the family module, in evaluation order:

1. Groups: a fresh daily buy-green, or a fresh weekly buy-green or buy-cyan, while the daily bar before the latest closes under 8% above its EMA 21 (not extended).
2. Deep Reset score >= 60, computed on the group's last 2 years: 35 x the drawdown from the 60-bar high (full at 35%) + 30 x closeness to the nearest of the 12-bar low, EMA 21 and EMA 50 (zero at 8% away) + 20 when 3-12% under the 20-bar high + 15 when RSI(14) is 45-60.
3. Entry at the next session's open; a weekly signal counts from the week's last session.
4. Exit: the close of the 15th session. No other exit is recorded.
5. Sizing: one slot per event, the $100,000 book / (1,838 x 2 timeframes) = about $27; the engine's own fees.

Where the accounting graded this strategy PARTIAL, the gaps it recorded are listed in Provenance; the algorithm above writes everything the record and the code hold, and anything neither holds is marked 'not in the record' rather than invented.

## Files in this repo

- Shared engine (already in Test): `sleeves/tensor_research/tensor_research.py` (the master-desk forward-test book module for the tensor_research family), with feedlib `sleeves/tensor_research/feedlib/tensor_research.py` and `sleeves/tensor_research/feedlib/tensor_research.mjs` (for the paper-hands book: `sleeves/tensor_research/feedlib/tensor_research_hands.mjs`).
- Strategy card (already in Test): `strategies/tensor_research/tr-ro-deep-reset-cross-scan.md`.
- Rule lines (already in Test): `docs/verify/tensor_research.md`.
- Accounting entry: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, strategy entry for this canonical name; Test catalog entry in `docs/CATALOG.json`.
- Named on the card as not in this repo: `desk/vendor/foliotend_research/doorway/prepare_current_doorway_inputs.py`. The Tensor engine itself is a hard rail and is not part of this package.

## Configuration

Universe: 1,838-name genome roster. Asset: US equities. Timeframes: 1d, 1wk. Book $100,000; slot about $27 per event. Card status: live.

## Data inputs

Completed regular-session daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 and the vendored research sources.

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch; keep the repo directory layout unchanged, because the modules import each other by the paths listed above.
2. Place or confirm every file listed in 'Files in this repo' at its stated path.
3. Register the sleeve with the desk cycle using exactly the configuration values in the Configuration section (no parameter overrides).
4. Wire the producers / data inputs named in 'Data inputs' so every evaluation receives them in the shapes the Full algorithm describes; an absent input must leave the sleeve in its stated no-input state (no intent / UNFED), never fake-fed.
5. Call the module's evaluate entry point named in the Full algorithm on its stated cadence, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

- A fresh buy whose daily bar before the latest closes 8% or more above EMA 21: no entry (extended).
- A Deep Reset score below 60: no entry; at or above 60: entry at the next session's open.
- A held position exits at the close of the 15th session and at no other recorded trigger.
- Slot size equals $100,000 / (1,838 x 2), about $27.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
