# ausar_pb158: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Daily price, volume and trend model · daily", type forecast and ML models, family tensor. Algorithm grade PARTIAL, sources ausar_map params/variant and md2 catalog entry/exit/strategy text; recorded gap: sizing not recorded in any consulted source. This canonical id is the alias `ausar_pb158` itself (accounting status history: md2_catalog "blocked", md2_ausar_map "present in roster"). No Test catalog entry under this id in the accounting (test_entries empty); the strategy is catalogued in Test under the catalog id `daily20` (see below). The sizing the accounting lacked is held in the code in this repo (see Full algorithm).
- Test catalog entry `daily20` (`docs/CATALOG.json`) and its card `strategies/ausar/daily20.md` ("Daily20 tree-model forecasts", family Ausar, source Ausar R11/R12 Tensor daily research, asset US equities, timeframe 1d, universe fixed 1,815-name enrollment, style Model forecast, status 2 blocked): variants row `ausar_daily20_tensor` = the model for this alias; the catalog rows map the Midna v3 implementation to `aster_tensor_d20_tensor` running on `desk3/aster_batch16.py`, and name master-desk code not in this repo (`desk/vendor/ausar_tensor/tensor_daily_models.py`, `desk/sleeves/families/ausar_daily20.py`).
- Code-derived algorithm doc in Test: `docs/ASTER_TENSOR_D20_TENSOR-ALGORITHM.md` (derived from the sleeve code on 2026-10-29; no author spec on file). Frozen model files are in Test under `packages/ausar/aster-desk-r13-baseline/desk/strategies/tensor_daily20/models/` and `packages/ausar/aster-execution-r15/desk/strategies/tensor_daily20/models/` (the `price_volume_plus_tensor` model JSON / joblib, its oracle JSON, MANIFEST.json and DAILY_SOURCE_ANCHORS.json).
- Search record: fresh recursive trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were taken at batch start (b26_Test_tree.txt, b26_Silicon_tree.txt, b26_quant-research-backup_tree.txt, b26_Midna_tree.txt in the run workspace) and searched by filename for the canonical id, its aliases and its distinguishing tokens. The D20 code was found in Test (paths in Files); no file named for `ausar_pb158` was found in the other three trees.

## What this strategy is

A frozen daily tree-ensemble forecast sleeve: every 20 sessions per name, the frozen gradient-boosted model forecasts 20-day excess return over QQQ from the 6 price/volume columns plus the Tensor columns (7 vote columns and balance_delta3, ribbon features, normalised OBV slope, squeeze features, UT state, MCDX position, normalised MACD histogram, normalised sign entropy, efficiency, prior-sell AVWAP distance and overhead60_atr): 35 columns in total; names scoring at or above the model's frozen threshold are bought for a 20-session hold. Paper only, on a $10,000 v3 slice. The two Daily20 arms differ only in the model feature set.

## Full algorithm

From `aster_tensor_d20_tensor` delegating to `desk3/aster_batch16.py` `evaluate` with kind="d20", model="price_volume_plus_tensor" (per the code-derived algorithm doc in Test):

1. Exits first: the 20-bar exit is evaluated before any entry; if any exit is emitted the evaluation returns with no entry.
2. Decision gates for a symbol's candidate series, in the engine's order: a canonical anchor must exist for the symbol; the history must be non-empty; every row must carry the required native columns, match the symbol, have bar_index equal to its ordinal, and match the anchor origin timestamps; the symbol must not be excluded (excluded: QQQ, SPY, B, GOLD); at least 234 rows (index >= 233, warmup); native_status must be "ready"; the last close must be at least $5; dollar_volume20 must be at least $1,000,000; ATR14 must be positive; and the last row index modulo 20 must equal the symbol's canonical phase (SHA-256 of the symbol modulo 20).
3. Scoring: the frozen feature frame is computed, missing values are imputed with the model's frozen training medians, and the score is the model baseline plus one selected leaf value per tree (100 trees; the ensemble is hash-verified at load from its frozen assets, no refit). Selected means score >= the model's frozen threshold.
4. Fresh-row gate (ENH-B26-D20FRESH-20261024, switch default ON; exits are never gated): when the symbol's 1Day bars are present, a selected candidate whose last decision row predates the last bar by more than 4 days is refused; no bars means no evidence and the gate passes.
5. Ranking and sizing: selected candidates are ranked by score descending, symbol ascending on ties. cap = min(equity x 0.10, dollar_volume20 x 0.01, available cash); shares = int(cap // close); fewer than 1 share emits nothing. At most 10 slots. (The master-desk card `strategies/ausar/daily20.md` records the same sizing as floor(min(10% equity, 1% of 20-day dollar volume, cash) / (price x 1.001)) and entry at the next open within 300 s; the v3 engine above enters as in step 6.)
6. Entry intent: market, day, buy_to_open, at the decision row's close.
7. Exit: the only designed exit is a position held at least 20 completed daily holding bars, sold in full as a market, day, sell_to_close intent with reason naming hold_20_bars. There is no price stop. Accounting record for this alias: "Exit after twenty completed daily holding bars."

## Files in this repo

- This package: `docs/AUSAR_PB158-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Sleeve code (already in Test): `sleeves/aster_tensor_d20_tensor.py`, with copies at `adapters3/aster_tensor_d20_tensor.py` and `integration/aster_tensor_d20_tensor_adapter.py`
- Shared engine that runs the logic: `desk3/aster_batch16.py` (kind d20, model "price_volume_plus_tensor")
- Code-derived algorithm doc: `docs/ASTER_TENSOR_D20_TENSOR-ALGORITHM.md`
- Strategy card: `strategies/ausar/daily20.md`; catalog entry `daily20` in `docs/CATALOG.json`; rule lines: `docs/verify/ausar.md`
- Frozen model assets: `packages/ausar/aster-desk-r13-baseline/desk/strategies/tensor_daily20/models/` and `packages/ausar/aster-execution-r15/desk/strategies/tensor_daily20/models/`
- Roster config: `config/sleeves.json` and `engines/config/sleeves.json`, row `aster_tensor_d20_tensor`
- Nothing was vendored: all code for this strategy was already in Test.

## Configuration

- Sleeve (engine) id: `aster_tensor_d20_tensor`; kind d20; model "price_volume_plus_tensor"; inputs (tensor_daily20, bars, positions); cadence_s 86400; session rth; slice capital $10,000; paper only.
- Hold 20 bars; slots 10; caps 0.10 of equity and 0.01 of dollar_volume20; excluded symbols QQQ, SPY, B, GOLD.
- Universe: fixed 1,815-name enrollment (card); the engine's frozen asset integrity check covers 1,817 canonical symbols with phases checked (algorithm doc). Asset class US equities; timeframe 1d.
- Declared producers in the engine: tensor_daily20_bundle (93600s freshness), bars (900s), broker_readback (900s, positions). The batch-16 note in the algorithm doc states run_live registers only bars and broker_readback today, so the tensor_daily20 input has no live producer yet and the sleeve is visibly UNFED on that input rather than fake-fed; the card status is "2 blocked", matching the accounting's "blocked" status for this alias.

## Data inputs

- Completed daily bars per enrolled symbol (at least 234 for signals), the frozen tensor_daily20 decision rows and model assets, positions (broker readback), and the slice cash/equity. Accounting data note for this alias: Completed Yahoo bars, canonical v698 where applicable, actual received execution quotes. The card records Yahoo daily bars and Tensor v690 engine features (Node).

## Install and run

1. Clone the Test repo.
2. Place `desk3/aster_batch16.py` under `desk3/` and the wrapper as `sleeves/aster_tensor_d20_tensor.py` (or the `adapters3/` copy), with the frozen model assets at the packages paths listed in Files.
3. Register the roster row for `aster_tensor_d20_tensor` from `config/sleeves.json` (cadence 86400, session rth, $10,000 slice, inputs tensor_daily20/bars/positions).
4. Wire the view with `tensor_daily20` decision rows, daily `bars`, `positions`, and a `slice`.
5. Call the wrapper's `evaluate(view, ctx)` once per day in the regular session; it delegates to `desk3.aster_batch16.evaluate("aster_tensor_d20_tensor", view, ctx)`. First check is the 20-bar exit scan, then gated, ranked entries.
6. Verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in the fresh Test tree. Behaviour checklist from the algorithm above:

- No entry for an excluded symbol (QQQ, SPY, B, GOLD), with fewer than 234 rows, native_status not "ready", last close below $5, dollar_volume20 below $1,000,000, non-positive ATR14, or a last-row index modulo 20 different from the symbol's canonical phase.
- A candidate whose frozen-model score is below the model's frozen threshold emits nothing; missing features are imputed with the frozen training medians and the score equals the baseline plus one leaf value per tree over 100 trees.
- With the fresh-row gate on, a selected candidate whose last decision row predates the last 1Day bar by more than 4 days is refused; exits are never gated by it.
- Ranking is score descending with symbol-ascending ties; shares equal int(min(equity x 0.10, dollar_volume20 x 0.01, cash) // close); no more than 10 positions are held.
- A position held at least 20 completed daily holding bars is sold in full (hold_20_bars) before any new entry is considered, and there is no other exit.
