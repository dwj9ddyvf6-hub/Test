# tr-genome-coiled-spring: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Coiled Spring genome", type breakout, family tensor_research, style "Base breakout", universe "1,838-name genome roster", asset class US equities, timeframe "1h, 1d, 1wk", creator "FolioTend / Griffith Tensor research (archived desk research), as a forward-test book". Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `tr-genome-coiled-spring` (`docs/CATALOG.json`): status live (1), card `strategies/tensor_research/tr-genome-coiled-spring.md`, master-desk row `genome_coiled_spring`.
- Alias: `genome_coiled_spring`.

## What this strategy is

Buys a stock when the Tensor research sidecar marks a Coiled Spring (a tight, constructive base) on a completed buy bar, hourly, daily or weekly, and sells at the close of bar 20. Each timeframe's event is its own lot.

## Full algorithm

From `strategies/tensor_research/tr-genome-coiled-spring.md` and `sleeves/tensor_research/tensor_research.py` (GENOMES mapping `genome_coiled_spring` to `COILED_SPRING`), in evaluation order:

1. Coiled Spring tests: 20-bar mean range at or below 0.75 times the 40 bars before; at or below 65% of the last 52 bars' volume traded above the close; up-volume at or above 52% of the last 13 bars'; 20-bar path efficiency at or above 0.30; bearish votes plus bearish markers at or below 2.
2. Shown only on a bar with a Tensor buy marker or a phenotype; at least 3 of the 5 tests pass, read on the bar before the event.
3. Only the bar just completed counts, and the roster's run publishes once at least half its names reach it.
4. Entry: the next bar's open, a market order within that hour (hourly) or session (daily, weekly); skipped once it has passed.
5. Exit: the close of bar 20 (market-on-close when it ends a session).
6. Gap in the record in Test: the card and catalog name `desk/vendor/foliotend_research/v619/app/lib/foliotend-research-sidecar.ts` and note the Tensor engine and FolioTend research code are not published in this repo; that sidecar file was not found in the Test tree searched for this package. The in-repo book code in Files is what Test holds.

## Files in this repo

- This doc: `docs/TR_GENOME_COILED_SPRING-RECREATE.md`
- Strategy card: `strategies/tensor_research/tr-genome-coiled-spring.md`
- Code (already in Test): `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.mjs`
- Rule lines: `docs/verify/tensor_research.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, tests/), Silicon tree, quant-research-backup tree and Midna tree were searched for the canonical id, its alias and family terms. No distinct Coiled Spring sleeve code was found in Silicon, quant-research-backup or Midna (Midna genome hits were calibration research, not this sleeve).

## Configuration

- Universe: 1,838-name genome roster. Timeframes: 1h, 1d, 1wk. Asset class: US equities.
- Book: $100,000. Sizing: one equal slot per event, $100,000 / (1,838 names times 3 timeframes) = about $18; skipped when the book lacks the cash; a modeled cost of 25.5 bp a side.
- State: not in the record beyond the per-timeframe lot rule.

## Data inputs

- Completed regular-session hourly bars (1 year), daily bars (2 years) and weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 and the vendored research sources (per the card).

## Install and run

1. Clone the Test repo.
2. Read `strategies/tensor_research/tr-genome-coiled-spring.md` and `docs/verify/tensor_research.md`.
3. Open `sleeves/tensor_research/tensor_research.py` with the feedlib modules in Files.
4. Provide the completed hourly, daily and weekly bars above and the Tensor buy-marker / phenotype feed; supply the FolioTend sidecar from the original desk if available, recording its absence in Test rather than inventing it.
5. Run on completed bars for all three timeframes and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist:

- Fewer than 3 of the 5 Coiled Spring tests passing means no event.
- No event on a bar without a Tensor buy marker or phenotype, and stale (not just-completed) bars do not count.
- Entry is at the next bar's open only, within that hour or session.
- Exit is exactly at the close of bar 20, and each timeframe's event is a separate lot sized at about $18 on a $100,000 book.
