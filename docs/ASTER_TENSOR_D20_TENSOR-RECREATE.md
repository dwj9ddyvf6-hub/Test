# aster_tensor_d20_tensor: Recreation package

Provenance: Ausar R11/R12 Tensor daily research (Source row in strategies/ausar/daily20.md in this repo).

## What this sleeve is
This is a frozen daily tree-ensemble forecast sleeve on a fixed 1,815-name enrollment (1,817 canonical symbols in the model assets). Every 20 sessions per name its price-volume-plus-Tensor model forecasts 20-day excess return; a score at or above the frozen threshold buys a 20-session hold on the $10,000 slice. Sources: desk adapters3/aster_tensor_d20_tensor.py and desk3/aster_batch16.py.

## Full algorithm
This sleeve is a thin wrapper: adapters3/<id>.py evaluate(view, ctx) delegates to desk3/aster_batch16.py evaluate(sleeve_id, view, ctx), which dispatches on SPEC kind="d20" to _eval_d20 with SPEC model="price_volume_plus_tensor". Sources: desk adapters3/<id>.py and desk3/aster_batch16.py SPECS, _d20_decision, _eval_d20, _load_d20_models.

SPEC (desk3/aster_batch16.py): kind="d20", model="price_volume_plus_tensor", inputs=("tensor_daily20", "bars", "positions"), cadence_s=86400. Constants: SLICE=10000.0; D20_HOLD_BARS=20, D20_SLOTS=10; D20_CAP_EQUITY=0.10, D20_CAP_DV=0.01; D20_EXCLUDED=frozenset(("QQQ", "SPY", "B", "GOLD")); D20_ROW_MAX_AGE_DAYS=4. Features for this model: the 6 price/volume columns (return20, return60, atr_pct, rvol, log_dollar_volume20, close_ema21_distance_atr) plus the Tensor columns (7 vote columns and balance_delta3, ribbon features, normalised OBV slope, squeeze features, UT state, MCDX position, normalised MACD histogram, normalised sign entropy, efficiency, prior-sell AVWAP distance and overhead60_atr): 35 columns in total.

Evaluation order in _eval_d20():
1. Exits first. The ONLY designed exit: a held position with at least 20 completed daily holding bars (bars_held from the position record, else sessions counted on 1Day bars after opened_at) is sold in full as a market, day, sell_to_close intent at the last 1Day close (or avg_price fallback), reason naming hold_20_bars. If any exit is emitted, return with no entry. There is no price stop.
2. Load the frozen model bundle from desk3/aster_d20_assets/ (hash-verified at load: manifest SHA-256 and every consumed asset hash, 1,817 canonical symbols and phases checked). Any integrity failure fails closed with no intents and no refit.
3. Decision gates per symbol in _d20_decision(), in order: a canonical anchor must exist; the candidate history (view tensor_daily20 rows for the symbol) must be non-empty; every row must carry the required native columns, match the symbol, have bar_index equal to its ordinal, and match the anchor origin timestamps (first_timestamp); the symbol must not be excluded; at least 234 rows (last index at least 233, warmup); native_status must be "ready"; last close at least 5.00; dollar_volume20 at least 1,000,000; ATR14 above 0; and the last row index modulo 20 must equal the symbol's canonical phase.
4. Scoring: the frozen feature frame is computed past-only, missing values are imputed with the model's frozen medians, and the score is the model baseline plus one leaf value per tree (100 trees). Selected means score at or above the model's frozen threshold (the threshold value lives in the frozen model assets, not in code; the entry reason prints score and threshold).
5. Fresh-row gate ENH-B26-D20FRESH-20261024 (default ON via extra enh switches; exits never gated): when the symbol's own 1Day bars are present, a selected candidate whose last decision row predates the last bar by more than 4 days is refused, with a paired journal record. No bars means no evidence and the gate passes.
6. Ranking and sizing: selected candidates ranked by score descending, then symbol ascending. Slots = 10 minus held count. Cap = min(equity times 0.10, dollar_volume20 times 0.01, available cash); shares = int(cap // close); fewer than 1 share emits nothing. Entries are market, day, buy_to_open intents at the decision row's close, reason naming frozen_price_volume_plus_tensor, the score, the threshold and hold=20bars.

## Files in this repo
- Adapter: adapters3/aster_tensor_d20_tensor.py (SLEEVE_ID=aster_tensor_d20_tensor; evaluate(view, ctx) delegates to desk3/aster_batch16.evaluate; INPUTS imported as D20_INPUTS from that engine).
- Shared engine file: desk3/aster_batch16.py (SPECS entry for aster_tensor_d20_tensor, _eval_d20, _d20_decision, _d20_feature_frame, _load_d20_models).
- Model assets: desk3/aster_d20_assets/ on the desk (frozen tree ensembles, manifest and anchors for model "price_volume_plus_tensor"); per strategies/ausar/daily20.md these assets are NOT in this repo, so a recreation must copy them from the desk source tree and verify their hashes at load exactly as _load_d20_models does.
- Existing strategy doc: strategies/ausar/daily20.md. Per-sleeve algorithm doc in this repo: docs/ASTER_TENSOR_D20_TENSOR-ALGORITHM.md.
- Config: engines/config/sleeves.json (row id=aster_tensor_d20_tensor), also at config/sleeves.json.

## Configuration
Module adapters3.aster_tensor_d20_tensor; cadence_s 86400; session rth; slice capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null; params {}; inputs [tensor_daily20, bars, positions]; parked false. Universe: fixed 1,815-name enrollment stated in strategies/ausar/daily20.md (1,817 canonical symbols in the frozen assets), excluding QQQ, SPY, B and GOLD at decision time; timeframe 1d (daily bars, 20-bar phase and 20-bar hold). Source: muse-desk-v3/config/sleeves.json row id=aster_tensor_d20_tensor.

## Data inputs
Inputs are tensor_daily20, bars and positions. Producers named in desk3/aster_batch16.py PRODUCERS: tensor_daily20_bundle (outputs tensor_daily20, freshness_sla_s 93600), bars (freshness_sla_s 900) and broker_readback (outputs positions, freshness_sla_s 900). The batch-16 note states run_live registers only bars and broker_readback today, so tensor_daily20 has no live producer yet and the sleeve is visibly UNFED on that input rather than fake-fed. Bars are daily (1Day) bars per symbol, used for bars_held counting and the fresh-row gate.

## Install and run
1. Place the sleeve module and adapter at the paths listed under Files in this repo, and place every listed shared engine file at its listed repo path (an engines/ path maps back to the desk path after engines/; a desk3/ path is the same path on a fresh desk).
2. Register the config row for `aster_tensor_d20_tensor` from engines/config/sleeves.json (repo copy of config/sleeves.json, also at config/sleeves.json) in the fresh desk's config/sleeves.json, exactly as given in the Configuration section, with no parameter overrides.
3. Wire the producers named in Data inputs so the inputs listed in the Configuration section arrive in the cycle snapshot (view) in the shapes the Full algorithm section describes.
4. Entry point: the adapter module adapters3/aster_tensor_d20_tensor.py, whose evaluate(view, ctx) calls desk3/aster_batch16.evaluate(SLEEVE_ID, view, ctx).
5. First evaluation: run one cycle on a fixture snapshot that satisfies the entry conditions in the Full algorithm section and confirm the expected intent (symbol, side, quantity rule and reason string naming this sleeve) is emitted before enabling live paper routing. If the Configuration section says parked is true, keep entries disabled exactly as in that row; exits are still managed where the algorithm says so.

## Verification
- No per-sleeve test file for this sleeve exists in this repo (audit: no tests/test_aster_* in the Test tree); use this behaviour checklist instead.
- Fixture with a held position at 20 or more completed holding bars: exactly one full-qty sell_to_close exit, reason containing hold_20_bars, and no entry in the same evaluation.
- Fixture with a selected candidate (eligible gates all passing, score at or above the frozen threshold in the copied assets, fresh row within 4 days): exactly one market buy_to_open entry, shares int(min(0.10 times equity, 0.01 times dollar_volume20, cash) // close), reason naming frozen_price_volume_plus_tensor with the score and threshold.
- Fixture with an excluded symbol (QQQ, SPY, B or GOLD), a close below 5.00, dollar_volume20 below 1,000,000, a phase mismatch, or a corrupted model asset hash: no entry.
- No entry intent is emitted when a required input is missing or a filter, gate or age check has no evidence: the code fails closed.
- Quantity, price hint, stop price and reason on every emitted intent match the sizing and price rules in the Full algorithm section for the fixture inputs.
- The config row used by the recreation matches engines/config/sleeves.json for this sleeve id (module, cadence, session, slice, parked state and inputs).
