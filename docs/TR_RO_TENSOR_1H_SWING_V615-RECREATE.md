# tr-ro-tensor-1h-swing-v615: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Tensor 1H Swing (v615)", type forecast and ML models, family tensor_research, style Swing confirmation, universe 1,838-name genome roster, asset class US equities, timeframe 1h, creator recorded as "FolioTend v615 Tensor Swing (full-universe study) and its corrected 10 / 20 / 30-bar winner census, as forward-test books". Algorithm grade PARTIAL: the accounting's algorithm entry/exit/sizing lists are empty and its gaps record all three as not recorded in any consulted source; what it does record is the variant table (below). Test catalog entry `tr-ro-tensor-1h-swing-v615` is the accounting's algorithm source. Aliases `ro_tensor_1h_swing_v615` and `ro_winner_census_10_20_30`, merged at Tier A on the evidence that the Test catalog entry groups both rows (status_counts live: 2).
- The full rule record is the strategy card in Test: `strategies/tensor_research/tr-ro-tensor-1h-swing-v615.md` (fetched at batch time; quoted in the Full algorithm section). Rule lines: `docs/verify/tensor_research.md`.
- Search record: fresh recursive trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were taken at batch start (b26_*_tree.txt in the run workspace) and searched by filename for this id and its aliases. The strategy code in Test is listed in Files. The card itself names three v615 library files as "not in this repo" (`desk/vendor/foliotend_research/v615/lib/tensor-swing-signals.mjs`, `desk/vendor/foliotend_research/v615/lib/tensor-swing-notification.mjs`, `desk/vendor/foliotend_research/v615/lib/tensor-enrichment-signals.mjs`) and notes "The Tensor engine and the FolioTend research code these rules run are not published in this repo"; no file with those names was found in any of the four trees.

## What this strategy is

An hourly Tensor swing-confirmation book over the 1,838-name genome roster: it buys when a completed hourly Tensor green arrow confirms a black-square setup within 3 bars, and sells at the close of hour 20. Its corrected winner-census twin splits each episode into three equal sub-lots closing at hours 10, 20 and 30.

## Full algorithm

From the card in Test, in evaluation order:

1. Setup (a black square): an hourly bar with no primary marker, at least 5 of 7 bullish votes, the fast state bullish and the slow state not bullish.
2. Confirmation: a green arrow (at least 5 bullish votes, and at least 4 more bullish than bearish votes) on the current completed hour, within 3 bars of the setup bar. One episode per setup bar.
3. Only the bar just completed counts, and the roster's run publishes once at least half its names reach it.
4. Entry: the next hour's open, a market order within that hour; skipped once that hour has passed. The 1H Swing book fires once per notification episode; the census book splits each episode into three equal sub-lots.
5. Exit (1H Swing, row `ro_tensor_1h_swing_v615`): one lot at the close of hour 20 (market-on-close when it ends a session).
6. Exit (Winner census, row `ro_winner_census_10_20_30`): three equal sub-lots at the closes of hours 10, 20 and 30.
7. Sizing: one equal slot per event: the $100,000 book / (1,838 names x 1 timeframe) = about $54 (a third of it per census sub-lot); skipped when the book lacks the cash; a modeled cost of 25.5 bp a side.
8. No stop, target or other exit is recorded on the card; anything beyond the above is not in the record.

## Files in this repo

- This package: `docs/TR_RO_TENSOR_1H_SWING_V615-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Strategy card: `strategies/tensor_research/tr-ro-tensor-1h-swing-v615.md`; catalog entry `tr-ro-tensor-1h-swing-v615` in `docs/CATALOG.json`; rule lines: `docs/verify/tensor_research.md`
- Code (already in Test): `sleeves/tensor_research/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.mjs`, and the rest of `sleeves/tensor_research/feedlib/` (canonical.py, canonical_alpaca.py, tensor.py, tensor_features.py, tensor_research_hands.mjs); a master-desk port copy at `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/tensor_research.py` with feedlib copies under `packages/claude/master-desk-feedlib/`
- Not in this repo (named on the card): the three v615 library files listed in Provenance and the Tensor engine v698 itself. Nothing was vendored.

## Configuration

- Book capital $100,000; equal slot about $54 per event (book / (1,838 names x 1 timeframe)); modeled cost 25.5 bp a side.
- Universe: 1,838-name genome roster; asset class US equities; timeframe 1h; family Tensor research; status 2 live (card).
- Cadence, session and state beyond the hourly evaluation described above: not in the record.

## Data inputs

- Completed regular-session hourly bars (1 year) of the roster, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 and the vendored research sources (card Data row).

## Install and run

1. Clone the Test repo.
2. Place the strategy card and the `sleeves/tensor_research/` tree (sleeve plus feedlib) at the paths in Files.
3. Provide completed regular-session hourly bars for the 1,838-name roster (Alpaca SIP, else Yahoo) and a Tensor engine v698 reading; note the three v615 library files named in Provenance are not in this repo, so the notification/signal layer must be supplied from the original desk before a faithful run is possible.
4. Run the roster scan on each completed hour; publish the run once at least half the roster's names reach the completed bar.
5. For each confirmed episode, enter at the next hour's open with one equal slot (about $54 on the $100,000 book); for the census book split the episode into three equal sub-lots.
6. Exit the 1H Swing lot at the close of hour 20; exit census sub-lots at the closes of hours 10, 20 and 30.
7. Verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this strategy was found in the fresh Test tree; the rule lines live at `docs/verify/tensor_research.md`. Behaviour checklist from the card:

- A setup requires an hourly bar with no primary marker, at least 5 of 7 bullish votes, fast state bullish and slow state not bullish; a confirmation requires a green arrow (at least 5 bullish votes, at least 4 more than bearish) on the current completed hour within 3 bars of the setup.
- Only the just-completed bar counts, one episode per setup bar, and the run publishes only once at least half the roster reaches the bar.
- Entry is at the next hour's open and is skipped once that hour has passed; quantity is one equal slot of about $54 on a $100,000 book (about $18 per census sub-lot), skipped when the book lacks the cash.
- The 1H Swing lot exits at the close of hour 20; census sub-lots exit at the closes of hours 10, 20 and 30; no other exit fires.
