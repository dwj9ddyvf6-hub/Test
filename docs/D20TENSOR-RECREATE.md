# D20TENSOR: Recreation Package
Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "D20TENSOR", type forecast and ML models, family unrecorded. Algorithm grade PARTIAL with every element gapped: entry/signal rule, exit rule and sizing are each "not recorded in any consulted source", and the accounting records no algorithm sources at all. The only alias record is `D20TENSOR` itself, source ausar_deployed, status "mode=original_independent_local_paper running=False". No Test catalog entry in the accounting (test_entries empty). The accounting's unresolved note: "singleton with no Test entry and no recorded strategy description; would be settled by the sleeve module docstring or a catalog description".
- Best evidence on file in Test: the catalog entry `daily20` (`docs/CATALOG.json`) and its card `strategies/ausar/daily20.md` record a Daily20 variant row `ausar_daily20_tensor` whose model is named "D20_TENSOR (Tensor features)", mapped on the Midna v3 desk to the sleeve `aster_tensor_d20_tensor` running on `desk3/aster_batch16.py` (kind d20, model "price_volume_plus_tensor"), with a code-derived algorithm doc at `docs/ASTER_TENSOR_D20_TENSOR-ALGORITHM.md`. The accounting did not merge this id with that variant, so this package does not claim they are the same strategy; it records the v3 sleeve as the closest evidenced implementation of a D20 Tensor daily model.
- Search record: fresh recursive trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were taken at batch start (b26_*_tree.txt in the run workspace) and searched by filename for D20TENSOR / d20tensor and the D20 tokens; no file named for this id exists in any of the four trees. The D20 code that does exist in Test is listed in Files.

## What this strategy is

Not in the record. The name and the ausar_deployed record place it among the Ausar daily Tensor tree-model books; the evidenced Daily20 Tensor arm in Test is described in the Full algorithm section, labelled as evidence, not as this id's settled algorithm.

## Full algorithm

For this canonical id itself: entry rule, exit rule and sizing are not in the record (accounting gaps, quoted in Provenance).

Best evidence on file (the Test v3 Daily20 Tensor arm, `aster_tensor_d20_tensor` on `desk3/aster_batch16.py`, per `docs/ASTER_TENSOR_D20_TENSOR-ALGORITHM.md`):

1. Exits first: a position held at least 20 completed daily holding bars is sold in full (market, day, sell_to_close, reason naming hold_20_bars); if any exit is emitted the evaluation returns with no entry. There is no price stop.
2. Entry gates, in engine order: canonical anchor exists; history non-empty; every row carries the required native columns, matches the symbol, has bar_index equal to its ordinal and matches the anchor origin timestamps; symbol not excluded (QQQ, SPY, B, GOLD); at least 234 rows; native_status "ready"; last close at least $5; dollar_volume20 at least $1,000,000; ATR14 positive; last row index modulo 20 equal to the symbol's canonical phase (SHA-256 of the symbol modulo 20).
3. Scoring: the frozen 35-column feature frame (6 price/volume columns plus the Tensor columns) is computed, missing values imputed with the frozen training medians, and the score is the model baseline plus one leaf value per tree (100 trees, hash-verified frozen assets, no refit). Selected means score >= the model's frozen threshold.
4. Fresh-row gate (default ON; exits never gated): a selected candidate whose last decision row predates the last 1Day bar by more than 4 days is refused when bars are present.
5. Ranking by score descending, symbol ascending; sizing cap = min(equity x 0.10, dollar_volume20 x 0.01, available cash), shares = int(cap // close), at most 10 slots, on a $10,000 slice; entries are market, day, buy_to_open at the decision row's close.

## Files in this repo

- This package: `docs/D20TENSOR-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Closest evidenced implementation (already in Test): `sleeves/aster_tensor_d20_tensor.py`, `adapters3/aster_tensor_d20_tensor.py`, `integration/aster_tensor_d20_tensor_adapter.py`; shared engine `desk3/aster_batch16.py`; algorithm doc `docs/ASTER_TENSOR_D20_TENSOR-ALGORITHM.md`; card `strategies/ausar/daily20.md`; catalog entry `daily20` in `docs/CATALOG.json`
- Frozen model assets: `packages/ausar/aster-desk-r13-baseline/desk/strategies/tensor_daily20/models/` and `packages/ausar/aster-execution-r15/desk/strategies/tensor_daily20/models/`
- No file for the id `D20TENSOR` itself was found in any searched repo, and nothing was vendored.

## Configuration

- For this id: not in the record, beyond the ausar_deployed status "mode=original_independent_local_paper running=False".
- For the evidenced v3 arm: sleeve id `aster_tensor_d20_tensor`, kind d20, model price_volume_plus_tensor, inputs (tensor_daily20, bars, positions), cadence_s 86400, session rth, slice $10,000, hold 20 bars, slots 10, caps 0.10 of equity and 0.01 of dollar_volume20; universe fixed 1,815-name enrollment per the card (engine integrity check covers 1,817 canonical symbols); timeframe 1d; US equities.

## Data inputs

- For this id: not in the record.
- For the evidenced v3 arm: completed daily bars, frozen tensor_daily20 decision rows and model assets, positions (broker readback), slice cash/equity; producers tensor_daily20_bundle (93600s), bars (900s), broker_readback (900s), with the tensor_daily20 input having no live producer registered today per the algorithm doc.

## Install and run

1. Clone the Test repo.
2. This package cannot install the `D20TENSOR` book as such: no code or config for that id is on file in any searched repo.
3. The closest evidenced implementation can be installed as the v3 arm: place `desk3/aster_batch16.py` under `desk3/` and the wrapper as `sleeves/aster_tensor_d20_tensor.py` (or the `adapters3/` copy), with the frozen model assets at the packages paths in Files.
4. Register the roster row for `aster_tensor_d20_tensor` from `config/sleeves.json` and wire the view with tensor_daily20, bars, positions and a slice.
5. Call the wrapper's `evaluate(view, ctx)` once per day in the regular session; it delegates to `desk3.aster_batch16.evaluate("aster_tensor_d20_tensor", view, ctx)`.
6. Treat any result as the v3 Daily20 Tensor arm's behaviour, not as proof of the original D20TENSOR book's behaviour.

## Verification

No dedicated test file for this id or for the v3 arm was found in the fresh Test tree. Behaviour checklist for the evidenced v3 arm (from its algorithm doc):

- No entry for an excluded symbol, with fewer than 234 rows, native_status not "ready", last close below $5, dollar_volume20 below $1,000,000, non-positive ATR14, or a phase mismatch.
- Score below the frozen threshold emits nothing; a position held at least 20 completed daily holding bars is sold in full before any entry is considered.
- Shares equal int(min(equity x 0.10, dollar_volume20 x 0.01, cash) // close), at most 10 positions, ranked score descending with symbol-ascending ties.
- Open item: this id stays UNRESOLVED until a sleeve module docstring or a catalog description for D20TENSOR itself is found.
