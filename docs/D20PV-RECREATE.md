# D20PV: Recreation package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- Canonical id: `D20PV`; canonical name: D20PV; aliases: D20PV.
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, local census copy in research_notes/sleeve-census-20261029/accounting.json): type forecast and ML models, family unrecorded, algorithm grade PARTIAL; accounting gaps: entry/signal rule not recorded in any consulted source; exit rule not recorded in any consulted source; sizing not recorded in any consulted source. Accounting home: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "D20PV" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: none recorded; alias record sources: ausar_deployed
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree at batch start plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree; no matching sleeve path for these ids); dwj9ddyvf6-hub/quant-research-backup (recursive tree; no matching sleeve path); dwj9ddyvf6-hub/Midna (recursive tree; research notes only as noted in Provenance, no deployable sleeve code for these ids).
- Code found: dwj9ddyvf6-hub/Test (closest evidenced implementation, already in Test): sleeves/aster_tensor_d20_pv.py + desk3/aster_batch16.py (SPECS D20_PV_ID, kind d20, model price_volume); no file for the D20PV id itself in any searched repo. No code was vendored for this strategy because the code already lives in Test at the paths below.

## What this strategy is

D20PV is an UNRESOLVED singleton in the accounting: no Test entry and no recorded strategy description; the accounting says it would be settled by the sleeve module docstring or a catalog description. The closest evidenced implementation in this repo is the Aster batch-16 D20 price/volume sleeve: the engine's own spec id is D20_PV_ID with model 'price_volume' (PV), a frozen Tensor daily-20 tree ensemble scored on 6 price/volume features only, buying a 20-bar hold at or above the model's frozen threshold. This package records that implementation as the best evidence on file; it does not claim the deployed D20PV record and this sleeve are proven identical.

## Full algorithm

From `docs/ASTER_TENSOR_D20_PV-ALGORITHM.md` in this repo (derived from `desk3/aster_batch16.py` on 2026-10-29), in evaluation order. SPEC: kind="d20", model="price_volume", inputs=("tensor_daily20", "bars", "positions"), cadence_s=86400, session="rth", slice capital $10,000 (SLICE = 10000.0). Hold 20 bars; slots 10; caps 0.10 of equity and 0.01 of dollar_volume20. Excluded symbols: QQQ, SPY, B, GOLD. Model features: only the 6 price/volume columns (return20, return60, atr_pct, rvol, log_dollar_volume20, close_ema21_distance_atr). Frozen asset integrity: the manifest SHA-256 and every consumed asset hash are verified at load (1,817 canonical symbols, phases checked); any integrity failure fails closed with no intents.

1. The 20-bar exit is evaluated first; if any exit is emitted the evaluation returns with no entry. The only designed exit: a position held at least 20 completed daily holding bars is sold in full, reason naming hold_20_bars. There is no price stop. Exits are market, day, sell_to_close intents, in full.
2. Decision gates for a symbol's candidate series, in the engine's order: a canonical anchor must exist; the history must be non-empty; every row must carry the required native columns, match the symbol, have bar_index equal to its ordinal, and match the anchor origin timestamps; the symbol must not be excluded; at least 234 rows (index >= 233, warmup); native_status must be "ready"; the last close must be at least $5; dollar_volume20 must be at least $1,000,000; ATR14 must be positive; and the last row index modulo 20 must equal the symbol's canonical phase (SHA-256 of the symbol modulo 20).
3. The frozen feature frame is computed (the 6 price/volume columns for this model), missing values are imputed with the model's frozen medians, and the score is the model baseline plus one leaf value per tree (100 trees). Selected means score >= the model's frozen threshold.
4. Fresh-row gate (ENH-B26-D20FRESH-20261024, switch default ON; exits are never gated): when the symbol's 1Day bars are present, a selected candidate whose last decision row predates the last bar by more than 4 days is refused. No bars means no evidence and the gate passes.
5. Selected candidates are ranked by score descending, symbol ascending. Sizing: cap = min(equity x 0.10, dollar_volume20 x 0.01, available cash); shares = int(cap // close); fewer than 1 share emits nothing. At most 10 slots.
6. Entries are market, day, buy_to_open intents at the decision row's close.

Where the accounting graded this strategy PARTIAL, the gaps it recorded are listed in Provenance; the algorithm above writes everything the record and the code hold, and anything neither holds is marked 'not in the record' rather than invented.

## Files in this repo

- Sleeve wrapper (already in Test): `sleeves/aster_tensor_d20_pv.py` (also `adapters3/aster_tensor_d20_pv.py`, `integration/aster_tensor_d20_pv_adapter.py`); SLEEVE_ID `aster_tensor_d20_pv`, delegating to `desk3/aster_batch16.evaluate` with D20_INPUTS.
- Shared engine (already in Test): `desk3/aster_batch16.py` (SPECS entry D20_PV_ID: kind="d20", model="price_volume"); frozen model assets under `desk3/aster_d20_assets/` (hash-verified at load).
- Existing algorithm and recreation docs for the aster id (already in Test): `docs/ASTER_TENSOR_D20_PV-ALGORITHM.md`, `docs/ASTER_TENSOR_D20_PV-RECREATE.md`.
- Accounting entry: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, strategy entry "D20PV" (UNRESOLVED, PARTIAL).

## Configuration

- For the D20PV accounting entry itself: universe, timeframe, asset class and parameters are not in the record.
- For the closest evidenced implementation: slice capital_usd 10000.0 / cash_usd 10000.0; cadence_s 86400; session rth; inputs tensor_daily20, bars, positions; hold 20 daily bars; slots 10; excluded QQQ, SPY, B, GOLD.

## Data inputs

Declared inputs of the implementation: tensor_daily20, bars, positions. Producers named in `desk3/aster_batch16.py`: tensor_daily20_bundle (93600 s freshness, outputs tensor_daily20), bars (900 s), broker_readback (900 s, positions). The batch-16 note states run_live registers only bars and broker_readback today, so the tensor_daily20 input has no live producer yet and the sleeve is visibly UNFED on that input rather than fake-fed. For the D20PV record itself, data inputs are not in the record.

## Install and run

1. Clone the Test repo (dwj9ddyvf6-hub/Test) and check out the main branch; keep the repo directory layout unchanged, because the modules import each other by the paths listed above.
2. Place or confirm every file listed in 'Files in this repo' at its stated path.
3. Register the sleeve with the desk cycle using exactly the configuration values in the Configuration section (no parameter overrides).
4. Wire the producers / data inputs named in 'Data inputs' so every evaluation receives them in the shapes the Full algorithm describes; an absent input must leave the sleeve in its stated no-input state (no intent / UNFED), never fake-fed.
5. Call the module's evaluate entry point named in the Full algorithm on its stated cadence, and route the returned intents through the desk dispatcher.
6. Run the Verification checks below before trusting any output.

## Verification

- A candidate failing any decision gate in step 2 (no anchor, fewer than 234 rows, native_status not "ready", close < $5, dollar_volume20 < $1,000,000, ATR14 <= 0, wrong phase): no entry.
- A score below the model's frozen threshold: no entry; at or above it, ranked by score descending then symbol ascending, sized at int(min(equity x 0.10, dollar_volume20 x 0.01, cash) // close), at most 10 slots.
- A held position exits in full at 20 completed daily holding bars and at no other trigger; there is no price stop.
- Any frozen-asset integrity failure at load fails closed with no intents.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
