# tr-ro-weekly-cyan-accumulation: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Weekly cyan accumulation", type breakout, family tensor_research, style "Base breakout", universe "1,838-name genome roster", asset class US equities, timeframe 1wk, creator "FolioTend / Griffith Tensor research (archived desk research), as a forward-test book". Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `tr-ro-weekly-cyan-accumulation` (`docs/CATALOG.json`): status waiting (1), card `strategies/tensor_research/tr-ro-weekly-cyan-accumulation.md`, master-desk row `ro_weekly_cyan_accumulation`.
- Alias: `ro_weekly_cyan_accumulation`.

## What this strategy is

Buys a stock on a weekly Tensor buy-cyan with a bullish consensus out of a compressed base, and sells at the close of week 20.

## Full algorithm

From `strategies/tensor_research/tr-ro-weekly-cyan-accumulation.md` and `sleeves/tensor_research/tensor_research.py` (PHENOTYPES mapping this id to `WEEKLY_CYAN_ACCUMULATION_RECOVERY` on 1wk), in evaluation order:

1. A completed weekly bar with a Tensor 5-of-7 bullish consensus (at least 5 bullish votes, at least 4 more than bearish), bullish votes at least bearish + 2, dollar volume at or above $10M and relative volume 0.8-2.
2. A buy-cyan marker and the last 20 weeks' mean range at or below 0.55 times the 40 weeks before.
3. Only the bar just completed counts, and the roster's run publishes once at least half its names reach it.
4. Entry: the next week's first open, a market order within that session; skipped once it has passed.
5. Exit: the close of week 20 (market-on-close when it ends a session).
6. Gap in the record in Test: the card names `desk/vendor/foliotend_research/v619/app/lib/foliotend-research-sidecar.ts` and notes the Tensor engine and FolioTend research code are not published in this repo; that file was not found in the Test tree searched for this package.

## Files in this repo

- This doc: `docs/TR_RO_WEEKLY_CYAN_ACCUMULATION-RECREATE.md`
- Strategy card: `strategies/tensor_research/tr-ro-weekly-cyan-accumulation.md`
- Code (already in Test): `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.mjs`
- Rule lines: `docs/verify/tensor_research.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, tests/), Silicon tree, quant-research-backup tree and Midna tree were searched for the canonical id, its alias and family terms. No distinct code for this phenotype was found in Silicon, quant-research-backup or Midna.

## Configuration

- Universe: 1,838-name genome roster. Timeframe: 1wk. Asset class: US equities.
- Book: $100,000. Sizing: one equal slot per event, $100,000 / (1,838 names times 1 timeframe) = about $54; skipped when the book lacks the cash; a modeled cost of 25.5 bp a side.

## Data inputs

- Completed regular-session weekly bars (10 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 and the vendored research sources (per the card).

## Install and run

1. Clone the Test repo.
2. Read `strategies/tensor_research/tr-ro-weekly-cyan-accumulation.md` and `docs/verify/tensor_research.md`.
3. Open `sleeves/tensor_research/tensor_research.py` with the feedlib modules in Files.
4. Provide 10 years of completed weekly bars and the Tensor consensus / buy-cyan feed; supply the FolioTend sidecar from the original desk if available, recording its absence in Test rather than inventing it.
5. Run weekly on completed bars and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist:

- No event with fewer than 5 bullish votes, or bullish votes under bearish + 2, or dollar volume under $10M, or relative volume outside 0.8-2.
- No event without a buy-cyan marker, or when the last 20 weeks' mean range is over 0.55 times the prior 40 weeks.
- Entry is at the next week's first open only; exit is exactly at the close of week 20, sized at about $54 per event on a $100,000 book.
