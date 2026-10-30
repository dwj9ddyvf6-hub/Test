# tr-genome-daily-green-base-expansion: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Daily green base expansion", type breakout, family tensor_research, style "Base breakout", universe "1,838-name genome roster", asset class US equities, timeframe 1d, creator "FolioTend / Griffith Tensor research (archived desk research), as a forward-test book". Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `tr-genome-daily-green-base-expansion` (`docs/CATALOG.json`): status live (1), card `strategies/tensor_research/tr-genome-daily-green-base-expansion.md`, master-desk row `genome_daily_green_base_expansion`.
- Alias: `genome_daily_green_base_expansion`.

## What this strategy is

Buys a stock on a daily Tensor buy-green that breaks out of a quiet base above a rising 200-day average, and sells at the close of day 20.

## Full algorithm

From `strategies/tensor_research/tr-genome-daily-green-base-expansion.md` and `sleeves/tensor_research/tensor_research.py` (PHENOTYPES mapping this id to `DAILY_GREEN_BASE_EXPANSION` on 1d), in evaluation order:

1. A completed daily bar with a buy-green marker; close above EMA 200, which is above its level 20 bars back; 20-bar mean range at or below 0.75 times the 40 bars before; close above the prior 20 highs; under 15% above EMA 21; up-volume at or above 50% of the last 13 bars' (or a high-participation footprint).
2. Only the bar just completed counts, and the roster's run publishes once at least half its names reach it.
3. Entry: the next session's open, a market order within that session; skipped once it has passed.
4. Exit: the close of day 20 (market-on-close when it ends a session).
5. Gap in the record in Test: as for the other Tensor research sleeves, the card names `desk/vendor/foliotend_research/v619/app/lib/foliotend-research-sidecar.ts` and notes the Tensor engine and FolioTend research code are not published in this repo; that file was not found in the Test tree searched for this package.

## Files in this repo

- This doc: `docs/TR_GENOME_DAILY_GREEN_BASE_EXPANSION-RECREATE.md`
- Strategy card: `strategies/tensor_research/tr-genome-daily-green-base-expansion.md`
- Code (already in Test): `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.mjs`
- Rule lines: `docs/verify/tensor_research.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- """ + SEARCHED + """ No distinct code for this phenotype was found in Silicon, quant-research-backup or Midna.

## Configuration

- Universe: 1,838-name genome roster. Timeframe: 1d. Asset class: US equities.
- Book: $100,000. Sizing: one equal slot per event, $100,000 / (1,838 names times 1 timeframe) = about $54; skipped when the book lacks the cash; a modeled cost of 25.5 bp a side.

## Data inputs

- Completed regular-session daily bars (2 years) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 and the vendored research sources (per the card).

## Install and run

1. Clone the Test repo.
2. Read `strategies/tensor_research/tr-genome-daily-green-base-expansion.md` and `docs/verify/tensor_research.md`.
3. Open `sleeves/tensor_research/tensor_research.py` with the feedlib modules in Files.
4. Provide 2 years of completed daily bars and the Tensor buy-green feed; supply the FolioTend sidecar from the original desk if available, recording its absence in Test rather than inventing it.
5. Run daily on completed bars and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist:

- No event without a buy-green marker, a close above a rising EMA 200, and a close above the prior 20 highs.
- A name 15% or more above EMA 21, or with 20-bar mean range over 0.75 times the prior 40, is not an event.
- Entry is at the next session's open only; exit is exactly at the close of day 20, sized at about $54 per event on a $100,000 book.
