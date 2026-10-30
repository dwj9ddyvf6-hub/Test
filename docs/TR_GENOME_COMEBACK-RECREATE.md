# tr-genome-comeback: Recreation package

## Provenance

- Canonical id: `tr-genome-comeback`; canonical name: Comeback genome; aliases: genome_comeback.
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, local census copy in research_notes/sleeve-census-20261029/accounting.json): type other, family tensor_research, algorithm grade PARTIAL; accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source. Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Comeback genome" (also docs/ALL-SLEEVES.md); Test catalog entry 'tr-genome-comeback' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree; no matching sleeve path); dwj9ddyvf6-hub/Midna (recursive tree; research notes only as noted in Provenance, no deployable sleeve code for these ids).
- Code found: dwj9ddyvf6-hub/Test (code already in Test): sleeves/tensor_research/tensor_research.py + sleeves/tensor_research/feedlib/. No code was vendored for this strategy because the code already lives in Test at the paths below.

## What this strategy is

Comeback genome: buys a stock when the Tensor research sidecar marks a Comeback (a repair back over EMA 21) on a completed buy bar, hourly, daily or weekly, and sells at the close of bar 20. Accounting grade PARTIAL (entry, exit and sizing all recorded as gaps in the accounting); the strategy card and rule lines in this repo record all three, and the code is the truth where they differ.

## Full algorithm

From the strategy card `strategies/tensor_research/tr-genome-comeback.md` and the family module `sleeves/tensor_research/tensor_research.py`, in evaluation order:

1. Comeback tests (5), read on the bar before the event: close >= EMA 21; the Tensor medium RSI up >= 5 points from 11 bars earlier; the MACD histogram above its value 4 bars earlier; bearish votes plus markers fewer than 11 bars earlier; close at or above the 52-bar low.
2. The event bar must carry a Tensor buy marker or a phenotype, and at least 3 of the 5 tests must pass.
3. Only the bar just completed counts, and the roster's run publishes once at least half its names reach it.
4. Entry: the next bar's open, a market order within that hour (hourly) or session (daily, weekly); skipped once it has passed.
5. Exit: the close of bar 20 (market-on-close when it ends a session). No other exit is recorded.
6. Sizing: one equal slot per event, the $100,000 book / (1,838 names x 3 timeframes) = about $18; skipped when the book lacks the cash; a modeled cost of 25.5 bp a side.

Where the accounting graded this strategy PARTIAL, the gaps it recorded are listed in Provenance; the algorithm above writes everything the record and the code hold, and anything neither holds is marked 'not in the record' rather than invented.

## Files in this repo

- Shared engine (already in Test): `sleeves/tensor_research/tensor_research.py` (the master-desk forward-test book module for the tensor_research family), with feedlib `sleeves/tensor_research/feedlib/tensor_research.py` and `sleeves/tensor_research/feedlib/tensor_research.mjs` (for the paper-hands book: `sleeves/tensor_research/feedlib/tensor_research_hands.mjs`).
- Strategy card (already in Test): `strategies/tensor_research/tr-genome-comeback.md`.
- Rule lines (already in Test): `docs/verify/tensor_research.md`.
- Accounting entry: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, strategy entry for this canonical name; Test catalog entry in `docs/CATALOG.json`.
- Named on the card as not in this repo: `desk/vendor/foliotend_research/v619/app/lib/foliotend-research-sidecar.ts`. The Tensor engine itself is a hard rail and is not part of this package.

## Configuration

Universe: 1,838-name genome roster. Asset: US equities. Timeframes: 1h, 1d, 1wk. Book $100,000; slot about $18 per event; modeled cost 25.5 bp a side. Card status: live.

## Data inputs

Completed regular-session hourly bars (1 year), daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 and the vendored research sources.

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch; keep the repo directory layout unchanged, because the modules import each other by the paths listed above.
2. Place or confirm every file listed in 'Files in this repo' at its stated path.
3. Register the sleeve with the desk cycle using exactly the configuration values in the Configuration section (no parameter overrides).
4. Wire the producers / data inputs named in 'Data inputs' so every evaluation receives them in the shapes the Full algorithm describes; an absent input must leave the sleeve in its stated no-input state (no intent / UNFED), never fake-fed.
5. Call the module's evaluate entry point named in the Full algorithm on its stated cadence, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

- A bar with fewer than 3 of the 5 Comeback tests passing, or without a Tensor buy marker or phenotype: no entry.
- An event whose next-bar entry window has passed: skipped, no late entry.
- A held position exits at the close of bar 20 and at no other recorded trigger.
- Slot size equals $100,000 / (1,838 x 3), about $18, and is skipped when the book lacks the cash.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
