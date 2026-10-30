# tr-ro-tensor-1h-swing-v615: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Tensor 1H Swing (v615)", type forecast and ML models, family tensor_research, style Swing confirmation, universe 1,838-name genome roster, asset class US equities, timeframe 1h, creator "FolioTend v615 Tensor Swing (full-universe study) and its corrected 10 / 20 / 30-bar winner census, as forward-test books". Algorithm grade PARTIAL with gaps: entry/signal rule, exit rule and sizing not recorded in the accounting's consulted sources (Test catalog entry/variants only). Those gaps are filled in Test by the strategy card, the verify rule lines and the code below, all named here; nothing is filled from outside Test. Merge evidence (Tier A): the Test catalog entry groups rows ro_tensor_1h_swing_v615 and ro_winner_census_10_20_30; the accounting records variant_not_recorded_count 1 (the census alias's distinguishing variant is not recorded in the accounting; the card and code below record it).
- Test catalog entry (Test `docs/CATALOG.json`): id `tr-ro-tensor-1h-swing-v615`, status live: 2, card `strategies/tensor_research/tr-ro-tensor-1h-swing-v615.md`, rows master_desk: [ro_tensor_1h_swing_v615, ro_winner_census_10_20_30], code list as in Files (including three vendor files the card marks as not in this repo).
- Strategy card in Test: `strategies/tensor_research/tr-ro-tensor-1h-swing-v615.md` (Entry / Exit / Sizing / Data text reproduced in the Full algorithm). Rule lines with file-and-line citations: `docs/verify/tensor_research.md`, section "Tensor 1H Swing (v615)".
- Code in Test: `sleeves/tensor_research/tensor_research.py` carries both rows: the module header describes ro_tensor_1h_swing_v615 as "FolioTend v615 buildTensorSwingSignal (executed): a confirmed 1H Swing, one episode per production notification eventKey; the full-universe study's trade (next 1H open, close of bar 20, 25.5 bp/side)" and ro_winner_census_10_20_30 as "the same deduplicated v615 Swing episodes under the corrected winner-census contract: three equal sub-lots closing at bars 10 / 20 / 30"; DETECTORS registers ("ro_tensor_1h_swing_v615", detect_swing615(..., (20,))) and ("ro_winner_census_10_20_30", detect_swing615(..., (10, 20, 30))) on the 1h frame.
- Code search record: fresh recursive trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were taken at batch start and searched by filename for the canonical id, its aliases and its distinguishing tokens; the contents of the Test files named in this package were read from GitHub. Every fact below names the repo and path it came from (all paths are in Test unless stated). The three vendor source files the card lists under Code as not in this repo (desk/vendor/foliotend_research/v615/lib/tensor-swing-signals.mjs, tensor-swing-notification.mjs, tensor-enrichment-signals.mjs) do not appear in the fresh Test tree, nor in the Silicon, quant-research-backup or Midna trees; the v615 swing computation is executed by the vendored research sources through the feedlib research plane (the frame's swing615 field) rather than re-ported, and the desk's engine pin is v698, not the research-era v615 (a named divergence in the code header). The book logic that runs in Test (detection of confirmed episodes, lot splitting, entry and exit timing, sizing) is in `sleeves/tensor_research/tensor_research.py` and its feedlib.

## What this strategy is

A forward-test book over the 1,838-name genome roster on completed hourly bars: when a Tensor black-square setup is confirmed by a green arrow within 3 bars, buy at the next hour's open and sell at the close of hour 20. The winner-census book trades the same deduplicated episodes in three equal sub-lots closing at hours 10, 20 and 30. Modeled cost 25.5 bp a side.

## Full algorithm

From the strategy card and the verify rule lines in Test, confirmed against the code:

1. Setup (black square): an hourly bar with no primary marker, at least 5 of 7 bullish votes, the fast state bullish and the slow not.
2. Confirmation (green arrow): at least 5 bullish votes and at least 4 more bullish than bearish votes, on the current completed hour, within 3 bars of the setup; one episode per setup bar. In the code, detect_swing615 emits an event only when the frame's last row carries a swing615 record with confirmed set and an eventKey; the event key is the sleeve id plus the eventKey (one event per notification episode).
3. Publication gate (card): only the bar just completed counts, and the roster's run publishes once at least half its names reach it.
4. Entry: the next hour's open, a market order within that hour; skipped once it has passed. The code header states the same desk rule: a lot enters at the open of the bar after the event bar (1h: at once while the next bar is still open).
5. Exit: the 1H Swing book exits one lot at the close of hour 20 (market-on-close when that bar ends a session, else a market order when the bar ends). The census book's three equal sub-lots close at hours 10, 20 and 30. In the code these are the event horizons (20,) and (10, 20, 30).
6. Sizing: one equal slot per event: the $100,000 book / (1,838 names x 1 timeframe) = about $54 (a third of it per census sub-lot); a lot is skipped when the book lacks the cash for its slot; modeled cost 25.5 bp a side (25 bp slippage + 0.5 bp fee per side in the code header, STUDY_SIDE_BPS = 25.5).
7. Named divergence recorded in the code header: the engine is v698 (the desk's pin), not the row's research-era engine v615; the bars are Yahoo's (production FolioTend input); entry at the next bar's open is a market order on the first desk pass at or after it, so the 1h fill is the price when the job publishes, minutes after the bar closes.

## Files in this repo

- This package: `docs/TR_RO_TENSOR_1H_SWING_V615-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json` entry `tr-ro-tensor-1h-swing-v615`
- Strategy card: `strategies/tensor_research/tr-ro-tensor-1h-swing-v615.md`; rule lines: `docs/verify/tensor_research.md`
- Code (already in Test): `sleeves/tensor_research/tensor_research.py` (rows ro_tensor_1h_swing_v615 and ro_winner_census_10_20_30; detect_swing615; DETECTORS 1h registration), with the same file also under `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/tensor_research.py`; feedlib `sleeves/tensor_research/feedlib/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor.py`, `sleeves/tensor_research/feedlib/tensor_features.py`, `sleeves/tensor_research/feedlib/canonical.py` (copies also under `packages/claude/master-desk-feedlib/`)
- Not in this repo (per the card, confirmed against the fresh trees): `desk/vendor/foliotend_research/v615/lib/tensor-swing-signals.mjs`, `desk/vendor/foliotend_research/v615/lib/tensor-swing-notification.mjs`, `desk/vendor/foliotend_research/v615/lib/tensor-enrichment-signals.mjs`. The card's closing note stands: "The Tensor engine and the FolioTend research code these rules run are not published in this repo." The recreation therefore runs on the in-repo research plane's executed sources exactly as the desk book does; the three .mjs files cannot be re-supplied from any GitHub repo searched.
- Nothing was vendored for this package.

## Configuration

- Book capital $100,000; slot = book / (1,838 names x 1 timeframe) = about $54 per event (about $18 per census sub-lot); modeled cost 25.5 bp a side.
- Universe: 1,838-name genome roster; asset US equities; timeframe 1h (completed regular-session hourly bars); status live: 2 (both rows).
- Horizons: 20 bars (1H Swing); 10 / 20 / 30 bars (winner census sub-lots).

## Data inputs

- Completed regular-session hourly bars (1 year) of the roster, from Alpaca SIP with keys, else Yahoo (card Data section); read by the pinned Tensor engine v698 and the vendored research sources via the tensor_research feedlib research plane, which publishes the events the sleeves read cache-only.

## Install and run

1. Clone the Test repo.
2. Place `sleeves/tensor_research/tensor_research.py` at its path with its feedlib package (`sleeves/tensor_research/feedlib/`) so the research plane can build the FolioTend production chart inputs for the 1,838-name roster and publish events.
3. Register the two 1h rows exactly as in DETECTORS: ro_tensor_1h_swing_v615 with horizons (20,) and ro_winner_census_10_20_30 with horizons (10, 20, 30), both through detect_swing615.
4. Fund the book at $100,000; each event takes one equal slot (book / (roster x timeframes)), split into equal sub-lots per its horizons, skipped when cash is short.
5. Run the hourly publication: only the just-completed bar counts, and a run publishes once at least half the roster reaches it; entries fill at the next hour's open within that hour.
6. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this row was found in the fresh Test tree. Behaviour checklist from the recorded algorithm:

- An event fires only on a confirmed swing615 record with an eventKey: a black-square setup (no primary marker, at least 5 of 7 bullish votes, fast state bullish, slow not) confirmed by a green arrow (at least 5 bullish votes, at least 4 more than bearish) within 3 bars; one episode per setup bar / eventKey.
- Entry is at the next hour's open and is skipped once that hour has passed; no entry on an unconfirmed or stale bar.
- The 1H Swing lot exits in full at the close of hour 20; census sub-lots (equal thirds) exit at the closes of hours 10, 20 and 30.
- Slot size is $100,000 / (1,838 x 1) (about $54); a lot is skipped when the book lacks cash; modeled cost is 25.5 bp a side.
