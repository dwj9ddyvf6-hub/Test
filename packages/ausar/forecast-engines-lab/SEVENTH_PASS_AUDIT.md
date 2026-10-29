# Seventh-pass audit: freeze the estimand before its outcome

**Date:** 2026-10-29
**Scope:** fresh pass over all 30 catalog targets, all 30 Edge-card target definitions, the forecast contract, and the append-only outcome/evaluation path.
**Files changed:** confined to `research/forecast_engines/`.

## New finding: an outcome could be “complete” at the wrong time

The sixth pass reconstructed realized intervals from `as_of` to `observed_at`, but the ledger only required an outcome timestamp later than `as_of` and trusted a boolean `horizon_complete`. The forecast horizon was often a range such as 5–20 sessions. Nothing bound a particular forecast attempt to one chosen horizon, exact end time, or version of the code that produced its target label. A 1-session mark could therefore be attached to a 20-session forecast and pass the old ledger's timing checks.

Re-reading the full 30-card target inventory found a related estimand problem: several cards described multiple possible labels in one sentence. Examples included return plus barrier events, transition plus transition direction, cash-conversion change plus a forward quality class, and commodity return plus tail events. A single realized scalar cannot silently stand for each of those outcomes. FE15 was a conditional spot-path sensitivity, not an unconditional realized-return target. FE25 used causal “price-support contribution” language for a quantity that a forward return alone cannot identify.

Forecast verification depends on pairing the issued forecast with the observation for the declared variable. Gneiting and Raftery's proper-scoring-rule treatment motivates that alignment requirement; it does not itself prescribe this package's hash or window protocol.

## What changed

- Added a v2 target-contract fingerprint for each engine. It binds target name, units, forecast semantics, the full Edge-card target text, one explicit primary label definition, allowed window IDs, and excluded secondary estimands.
- Added an explicit primary-label inventory for FE01–FE30. FE15 is marked `scenario_only` and cannot be submitted as an observed-return label. FE25 now forecasts issuer residual return conditional on verified executed buyback pace; it makes no causal price-support claim.
- Forecast requests can freeze an allowed `target_window_id`, exact UTC `target_window_start_at`/`target_window_end_at`, and expected `label_transform_id/hash`. The start may be a future event/open after `as_of`; the end must follow the start. The engine rejects malformed, disallowed, or non-labelable bindings.
- Current outcome appends must repeat the frozen target-contract, window, and transform identity. `observed_at` must equal the frozen window end; a caller cannot attach an earlier or later mark to the same forecast.
- Ledger reads reject mismatched contract/window/transform records from evaluation joins and report each failure class. Old records without target-contract identity remain readable as `legacy_unbound`; no historical definition is reconstructed or guessed.
- Coverage and horizon-overlap diagnostics now partition by target contract, chosen window ID, and label-transform hash. Horizon overlap uses the declared target start/end; for event-driven targets this prevents counting the pre-event wait as part of the realized label interval. A 5-session label can no longer be silently pooled with a 20-session label under one wide horizon string.
- Added `target-contracts` and `target-provenance` CLI views to inspect all registered definitions, frozen versions, window coverage, and label-transform lineage.

## How to bind a label

For an evaluable request, supply the exact allowed window and the digest of the label-construction code *before* issuing the forecast:

```json
{
  "engine_id": "FE01",
  "symbol": "SPY",
  "as_of": "2026-10-01T20:00:00Z",
  "target_window_id": "5-session",
  "target_window_start_at": "2026-10-01T20:00:00Z",
  "target_window_end_at": "2026-10-08T20:00:00Z",
  "label_transform_id": "excess-return-close-v1",
  "label_transform_hash": "sha256:<64 lowercase hex>",
  "features": {}
}
```

When the label matures, `append_outcome` (or the abstention-only audit method) repeats the exact forecast contract fingerprint, window ID/end, and transform ID/hash. The observed outcome timestamp must equal the target-window end; publication and ingestion can follow it.

## Limits of the binding

The target-contract hash pins the registered semantic description. The window fields pin a selected endpoint. The label-transform hash is a caller attestation that names a code version; it does not prove that the code ran, that its data were correct, or that the declared label is economically useful. A target threshold or event classifier that is changed must use a new transform hash, and transform versions are kept in distinct diagnostic groups. Legacy outcomes remain unbound and are not presented as current-contract examples.

The inventory is a research contract, not a validation result. The 30 formulas remain untrained hypotheses; this pass adds no price panel, outcome data, execution connector, paper trading, or profitability evidence.

## Primary methodological source

- Gneiting and Raftery, [Strictly Proper Scoring Rules, Prediction, and Estimation](https://doi.org/10.1198/016214506000001437). It treats forecast scoring as a forecast/observation pairing. The precise target/window/version binding added here is the package's engineering control.
