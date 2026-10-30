# tr-ro-hourly-transition-core-burst: Recreation package

## Provenance

- Canonical id: `tr-ro-hourly-transition-core-burst`; canonical name: Hourly Core / Burst transition; aliases: ro_hourly_transition_core_burst.
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, local census copy in research_notes/sleeve-census-20261029/accounting.json): type other, family tensor_research, algorithm grade PARTIAL; accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source. Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Hourly Core / Burst transition" (also docs/ALL-SLEEVES.md); Test catalog entry 'tr-ro-hourly-transition-core-burst' (docs/CATALOG.json per accounting test_entries); algorithm sources per accounting: Test catalog entry/variants; alias record sources: test_catalog
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree; no matching sleeve path); dwj9ddyvf6-hub/Midna (recursive tree; research notes only as noted in Provenance, no deployable sleeve code for these ids).
- Code found: dwj9ddyvf6-hub/Test (code already in Test): sleeves/tensor_research/tensor_research.py + sleeves/tensor_research/feedlib/. No code was vendored for this strategy because the code already lives in Test at the paths below.

## What this strategy is

Hourly Core / Burst transition: buys a confirmed hourly Tensor Swing on a daily buy-cyan name when its hourly volatility and EMA distance read Core or Burst, with the Swing's own target and invalidation. Accounting grade PARTIAL (entry, exit and sizing recorded as gaps in the accounting); the card and rule lines in this repo record all three.

## Full algorithm

From the strategy card `strategies/tensor_research/tr-ro-hourly-transition-core-burst.md` and the family module, in evaluation order:

1. Entry conditions: a confirmed v615 hourly Swing; the name's latest daily bar carrying a buy-cyan; and no sell-red or sell-magenta on the confirmation bar.
2. Regime tag: Core = hourly ATR 1-2% of price with the nearest of EMA 21 / 50 / 200 0.5-1.0 ATR away; Burst = hourly ATR 2-4% with a daily supply or range breakout; both tags split the slot.
3. Only the bar just completed counts, and the roster's run publishes once at least half its names reach it.
4. Entry: the next hour's open, a market order within that hour; skipped once it has passed.
5. Exit (first that fires): the Swing's frozen target (the nearest supply above, else close + 2 ATR) or invalidation (the nearest demand below, else the bar's low), on the bid; a later hourly sell-red or sell-magenta exits after its bar; else the close of hour 20.
6. Sizing: one equal slot per event, the $100,000 book / (1,838 names x 1 timeframe) = about $54; skipped when the book lacks the cash; a modeled cost of 25.5 bp a side.

Where the accounting graded this strategy PARTIAL, the gaps it recorded are listed in Provenance; the algorithm above writes everything the record and the code hold, and anything neither holds is marked 'not in the record' rather than invented.

## Files in this repo

- Shared engine (already in Test): `sleeves/tensor_research/tensor_research.py` (the master-desk forward-test book module for the tensor_research family), with feedlib `sleeves/tensor_research/feedlib/tensor_research.py` and `sleeves/tensor_research/feedlib/tensor_research.mjs` (for the paper-hands book: `sleeves/tensor_research/feedlib/tensor_research_hands.mjs`).
- Strategy card (already in Test): `strategies/tensor_research/tr-ro-hourly-transition-core-burst.md`.
- Rule lines (already in Test): `docs/verify/tensor_research.md`.
- Accounting entry: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, strategy entry for this canonical name; Test catalog entry in `docs/CATALOG.json`.
- Named on the card as not in this repo: `desk/vendor/foliotend_research/v615/lib/tensor-swing-signals.mjs`, `desk/vendor/foliotend_research/v615/lib/tensor-enrichment-signals.mjs`. The Tensor engine itself is a hard rail and is not part of this package.

## Configuration

Universe: 1,838-name genome roster. Asset: US equities. Timeframe: 1h. Book $100,000; slot about $54 per event; modeled cost 25.5 bp a side. Card status: waiting.

## Data inputs

Completed regular-session hourly bars (1 year) and daily bars (2 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 and the vendored research sources.

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch; keep the repo directory layout unchanged, because the modules import each other by the paths listed above.
2. Place or confirm every file listed in 'Files in this repo' at its stated path.
3. Register the sleeve with the desk cycle using exactly the configuration values in the Configuration section (no parameter overrides).
4. Wire the producers / data inputs named in 'Data inputs' so every evaluation receives them in the shapes the Full algorithm describes; an absent input must leave the sleeve in its stated no-input state (no intent / UNFED), never fake-fed.
5. Call the module's evaluate entry point named in the Full algorithm on its stated cadence, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

- A confirmed Swing on a name whose latest daily bar is not buy-cyan, or with a sell-red/sell-magenta on the confirmation bar: no entry.
- A Swing reading neither Core nor Burst on the ATR / EMA-distance tests: no entry.
- Exit fires on the first of the frozen target, the frozen invalidation, a later hourly sell-red/sell-magenta, or the close of hour 20.
- Slot size equals $100,000 / 1,838, about $54, skipped when the book lacks the cash.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
