# ausar_pb159: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name recorded for this entry, type forecast and ML models, family tensor. Algorithm grade PARTIAL, with the single recorded gap: sizing not recorded in any consulted source. Algorithm sources per the accounting: ausar_map params/variant and md2 catalog entry/exit/strategy text. Alias `ausar_pb159` status in the accounting: blocked (md2_catalog), present in roster (md2_ausar_map). No Test catalog entry for the alias itself (test_entries empty); the family catalog entry is `daily20` (below). The sizing the accounting lacked is held in the code and card in this repo (see Full algorithm); nothing beyond the record and that code is claimed.
- Accounting algorithm text for this entry: "[ausar_pb159] A frozen tree ensemble starts from its baseline and adds one selected leaf value per tree. Missing features use frozen training medians; entry requires prediction >= the frozen model threshold. The price/volume arm uses its fixed price/volume feature set. Requires ready inputs, at least 234 bars, price >= $5, twenty-bar dollar volume >= $1 million, positive ATR and the symbol's twenty-bar sampling ph" (the accounting's entry text ends mid-word, truncated in the source record; the parallel tensor-arm text completes the phrase as "phase"). Exit: "[ausar_pb159] Exit after twenty completed daily holding bars."
- Identification of the arm: the Daily20 family in Test (strategy card `strategies/ausar/daily20.md`; Test catalog entry `daily20` in `docs/CATALOG.json`) has exactly two models: D20_PV (price-volume features, master-desk row `ausar_daily20_price_volume`, v3 row `aster_tensor_d20_pv`) and D20_TENSOR (Tensor features, master-desk row `ausar_daily20_tensor`, v3 row `aster_tensor_d20_tensor`). This entry is the price/volume arm: its accounting text names that arm, and its recorded gates (at least 234 bars, price at least $5, twenty-bar dollar volume at least $1 million, positive ATR, the symbol's twenty-bar sampling phase) and its recorded exit (after twenty completed daily holding bars) match that arm's recorded rules in Test exactly. The code-derived per-arm algorithm doc is `docs/ASTER_TENSOR_D20_PV-ALGORITHM.md`.
- Code search record: fresh recursive trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna were taken at batch start and searched by filename for the canonical id, its aliases and its distinguishing tokens; the contents of the Test files named in this package were read from GitHub. Every fact below names the repo and path it came from (all paths are in Test unless stated).

## What this strategy is

One of the two Daily20 frozen tree-ensemble forecast books: every 20 sessions per name, a frozen 100-tree gradient-boosted model forecasts 20-day excess return over QQQ; names scoring at or above the model's frozen threshold are bought for a 20-bar hold. This entry is the price/volume model (price_volume). Paper only. Fixed enrollment of 1,815 names (strategy card; the v3 engine's asset manifest checks 1,817 canonical symbols).

## Full algorithm

Accounting record, in evaluation order: a frozen tree ensemble starts from its baseline and adds one selected leaf value per tree; missing features use frozen training medians; entry requires prediction at least the frozen model threshold; requires ready inputs, at least 234 bars, price at least $5, twenty-bar dollar volume at least $1 million, positive ATR and the symbol's twenty-bar sampling phase; exit after twenty completed daily holding bars. Data per the accounting: completed Yahoo bars, canonical v698 where applicable, actual received execution quotes.

v3 implementation in Test (`docs/ASTER_TENSOR_D20_PV-ALGORITHM.md`, derived from `desk3/aster_batch16.py` kind="d20", model="price_volume", wrapper `sleeves/aster_tensor_d20_pv.py`):

- Spec: inputs (tensor_daily20, bars, positions), cadence_s 86400, session rth, slice capital $10,000 (SLICE = 10000.0). Hold 20 bars; slots 10; caps 0.10 of equity and 0.01 of dollar_volume20. Excluded symbols: QQQ, SPY, B, GOLD. Model features: only the 6 price/volume columns (return20, return60, atr_pct, rvol, log_dollar_volume20, close_ema21_distance_atr).
- Frozen asset integrity: the manifest SHA-256 and every consumed asset hash are verified at load (1,817 canonical symbols, phases checked); any integrity failure fails closed with no intents.
- Entry rules, in the engine's order: (1) the 20-bar exit is evaluated first; if any exit is emitted the evaluation returns with no entry. (2) Decision gates for a symbol's candidate series: a canonical anchor must exist for the symbol; the history must be non-empty; every row must carry the required native columns, match the symbol, have bar_index equal to its ordinal, and match the anchor origin timestamps; the symbol must not be excluded; at least 234 rows (index >= 233, warmup); native_status must be "ready"; the last close must be at least $5; dollar_volume20 must be at least $1,000,000; ATR14 must be positive; and the last row index modulo 20 must equal the symbol's canonical phase (SHA-256 of the symbol modulo 20). (3) The frozen feature frame is computed, missing values imputed with the model's frozen medians, and the score is the model baseline plus one leaf value per tree (100 trees); selected means score >= the model's frozen threshold. (4) Fresh-row gate (ENH-B26-D20FRESH-20261024, switch default ON; exits are never gated): when the symbol's 1Day bars are present, a selected candidate whose last decision row predates the last bar by more than 4 days is refused; no bars means no evidence and the gate passes. (5) Selected candidates are ranked by score descending, symbol ascending; sizing cap = min(equity x 0.10, dollar_volume20 x 0.01, available cash); shares = int(cap // close); fewer than 1 share emits nothing; at most 10 slots. Entries are market, day, buy_to_open intents at the decision row's close.
- Exit: the only designed exit is a position held at least 20 completed daily holding bars, sold in full (reason naming hold_20_bars), market, day, sell_to_close. There is no price stop.

Master-desk form (in Test at `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/ausar_daily20.py`, whose header carries out the source runtime's D20 rules):

- Producer job ausar_daily20, each weekday evening after the close: every enrolled name's canonical daily tape from its anchored first session (Yahoo daily), identity-checked against its anchor (first timestamp and original endpoint ordinal); a name whose newest ordinal is in its phase (ordinal % 20 = anchor phase) is computed by the engine and evaluated by both models; a selected decision becomes a candidate unless inside its cooldown (next eligible ordinal = selected ordinal + 20). Census rule: every enrolled name assessed and at least 99% known.
- Books trade in the next regular opening's window (300 s): owed exits first (20 observed sessions from the entry session's opening, sell the whole position at the next opening; while an exit is pending no entry is ranked); then ranked candidates (prediction descending, symbol ascending) while slots remain (10 including pending), each with a quote observed at/after the opening: shares = floor(min(10% equity, 1% of its 20-session dollar volume, cash) / (price x 1.001)) per the strategy card (the family module's header states the same sizing with the fee/slippage divisor price x (1 + max(10 bps, 10 bps slippage)) and a $0 fee); market order (marketable limit).
- The family module's named divergences D1-D4 (canonical tapes stand in for the runtime's seeded research tapes with a vendor-backfill quarantine inside the frozen prefix; off-phase names assessed from tape identity alone; the 20 observed bars counted on the exchange calendar from the entry fill's session; sizing price is the desk quote's last trade, its mid when absent) are recorded in that module's header in Test and are part of this package by that reference.

## Files in this repo

- This package: `docs/AUSAR_PB159-RECREATE.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Strategy card: `strategies/ausar/daily20.md`; catalog entry `daily20` in `docs/CATALOG.json`; rule lines: `docs/verify/ausar.md` (Daily20 section)
- v3 code (already in Test): `sleeves/aster_tensor_d20_pv.py`, `adapters3/aster_tensor_d20_pv.py`, `integration/aster_tensor_d20_pv_adapter.py`; shared engine `desk3/aster_batch16.py`; code-derived algorithm doc `docs/ASTER_TENSOR_D20_PV-ALGORITHM.md`
- Master-desk code (already in Test): `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/ausar_daily20.py` (books ausar_daily20_price_volume / ausar_daily20_tensor); parity copy `packages/claude/master-desk-parity-tools/tools/parity/ausar_daily20.py`
- Vendored model runtime and frozen assets (already in Test): `packages/ausar/aster-desk-r13-baseline/desk/backend/tensor_daily_models.py` and `packages/ausar/aster-desk-r13-baseline/desk/strategies/tensor_daily20/models/` (MANIFEST.json with per-file SHA-256, both 100-tree model JSONs and joblib exports, DAILY_SOURCE_ANCHORS.json, oracles, EXPORT_PROVENANCE.json); the same set also exists under `packages/ausar/aster-execution-r15/desk/`
- Tests in Test: `packages/ausar/aster-desk-r13-baseline/desk/tests/test_tensor_daily_models.py` (copy also under aster-execution-r15)
- Recorded gap: the v3 algorithm doc names model assets under `desk3/aster_d20_assets/`; no such directory appears in the fresh Test tree taken at batch start. The frozen model assets present in Test are the packages/ausar copies named above.
- Nothing was vendored: all code for this strategy was already in Test.

## Configuration

- Model: price_volume; book row ausar_daily20_price_volume (master desk) / aster_tensor_d20_pv (v3). Universe: fixed enrollment, 1,815 names (card) / 1,817 canonical symbols in the v3 asset manifest. Asset class US equities; timeframe 1d.
- v3: slice $10,000; slots 10; caps 0.10 of equity and 0.01 of dollar_volume20; cadence 86400 s; session rth; paper only. Status in Test catalog entry daily20: blocked: 2 (both rows).
- Master-desk producer: weekday evenings after the close; entry window 300 s at the next regular opening; census at least 99% known.

## Data inputs

- Accounting note: completed Yahoo bars, canonical v698 where applicable, actual received execution quotes. Card: Yahoo daily bars; Tensor v690 engine features (Node) for the master-desk form.
- v3 declared inputs: tensor_daily20, bars, positions. Producers named in `desk3/aster_batch16.py`: tensor_daily20_bundle (93600 s freshness), bars (900 s), broker_readback (900 s, positions). The batch-16 note states run_live registers only bars and broker_readback today, so the tensor_daily20 input has no live producer yet and the sleeve is visibly UNFED on that input rather than fake-fed.

## Install and run

1. Clone the Test repo.
2. For the v3 form: place `desk3/aster_batch16.py` under `desk3/` and the wrapper at `sleeves/aster_tensor_d20_pv.py` (SLEEVE_ID = "aster_tensor_d20_pv"), with the frozen model assets from `packages/ausar/aster-desk-r13-baseline/desk/strategies/tensor_daily20/models/` available to the engine's asset loader; the loader verifies the manifest and asset hashes at load and fails closed on any mismatch.
3. Wire the view with tensor_daily20 decision rows, daily bars and broker-readback positions, and a $10,000 slice.
4. Call the wrapper's evaluate(view, ctx) once per day in the regular session; the 20-bar exit scan runs first, then ranked entries.
5. For the master-desk form: use `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/ausar_daily20.py` with its vendored ausar_tensor dependencies in the same port library, select book ausar_daily20_price_volume, and run the weekday-evening producer and next-opening book rules in the Full algorithm.
6. Verify against the Verification section before treating the recreation as faithful.

## Verification

- Run the vendored model tests in Test: `packages/ausar/aster-desk-r13-baseline/desk/tests/test_tensor_daily_models.py` must pass.
- Behaviour checklist from the algorithm above:
  - No entry for a symbol with fewer than 234 rows, native_status not "ready", last close below $5, dollar_volume20 below $1,000,000, non-positive ATR14, an off-phase last row (index mod 20 not equal to the symbol's canonical phase), or a score below the model's frozen threshold.
  - Excluded symbols QQQ, SPY, B, GOLD never enter.
  - Ranking is score descending, symbol ascending; shares = int(min(equity x 0.10, dollar_volume20 x 0.01, cash) // close); at most 10 slots.
  - The only exit is the full sale after 20 completed daily holding bars; an evaluation that emits an exit emits no entry.
  - Any model-asset hash mismatch at load produces no intents (fail-closed).
