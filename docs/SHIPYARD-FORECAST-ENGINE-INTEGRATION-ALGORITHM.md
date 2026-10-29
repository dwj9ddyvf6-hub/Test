# Shipyard forecast-engine integration

Created by Ausar. Packaged into the Test repo on 2026-10-29 (packaging pass).

Origin: dwj9ddyvf6-hub/Silicon branch codex/forecast-engines-2026-10-29, apps/shipyard-research-terminal/scripts/.

The integration scripts that connect the Shipyard Research Terminal to the Silicon forecast engines. sync_silicon_forecast_engines.py exports the pinned Silicon forecast contracts and scorer parity vectors: it samples deterministic values per engine/feature (range-fraction sampling for ranged features, fixed heuristics for staleness, confidence-like, and ratio features) so the terminal side can verify its scorers against the pinned contracts. build_worker.py assembles the terminal Worker bundle, market-overview.test.mjs tests the market-overview module, and worker-smoke.mjs smoke-tests the built worker.

## Files in this package

- `packages/ausar/shipyard-forecast-engine-integration/apps/shipyard-research-terminal/scripts/build_worker.py`
- `packages/ausar/shipyard-forecast-engine-integration/apps/shipyard-research-terminal/scripts/market-overview.test.mjs`
- `packages/ausar/shipyard-forecast-engine-integration/apps/shipyard-research-terminal/scripts/sync_silicon_forecast_engines.py`
- `packages/ausar/shipyard-forecast-engine-integration/apps/shipyard-research-terminal/scripts/worker-smoke.mjs`

Source files are verbatim copies from the origin location named above unless a sanitization note appears in this doc.
