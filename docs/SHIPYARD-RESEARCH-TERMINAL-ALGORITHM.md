# Shipyard Research Terminal

Created by Ausar. Packaged into the Test repo on 2026-10-29 (packaging pass).

Origin: dwj9ddyvf6-hub/Silicon branch main, apps/shipyard-research-terminal/.

A public, read-only research workspace (hosted Site plus Worker) built on the Shipyard Sites project. The browser app carries the Silicon Market Terminal tool set (market overview, charts, options flow, GEX, screeners, labs, vendor coverage, watchlists, browser-local alerts) fed by read-only endpoints: GET /api/alpaca/bars returns one symbol of split-adjusted Alpaca IEX daily bars (SMA20/SMA50, RSI14, ATR14 calculated locally; a bar dated today in New York is excluded from close metrics until 16:15 ET), GET /api/terminal/context serves market context, a metadata-only Morgue readiness intake reports timestamp and section presence only, and POST /mcp exposes read-only tools. The package preserves the full source tree: db schema, drizzle migrations (both source and dist copies), Worker code (alpaca, mcp, morgue, operations, reports, terminal), build and test scripts, and the built dist bundle. Binary release bundles under artifacts/ and screenshots were not part of the indexed file manifest and are not included.

## Files in this package

- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/INSTALLATION-AUDIT-2026-10-28.md`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/PUBLICATION-RECORD.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/README.md`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle.config.ts`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/package-lock.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/package.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/.openai/hosting.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/db/schema.ts`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/app-bootstrap.mjs`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/app.js`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/candidate-calculation-fixtures.mjs`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/convergence-engine.mjs`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/evidence-contract.mjs`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/favicon.svg`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/index.html`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/market-overview.mjs`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/morgue-adapter.mjs`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/morgue-readiness-fixtures.mjs`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/research-adapters.mjs`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/styles.css`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/vendor-coverage.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/hosting.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/0000_tidy_spitfire.sql`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/0001_round_gladiator.sql`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/0002_rich_morg.sql`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/0003_lethal_zzzax.sql`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/0004_deep_major_mapleleaf.sql`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/0005_same_daredevil.sql`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/0006_watery_siren.sql`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/0007_calm_alerts.sql`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/0008_heavy_vance_astro.sql`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/0009_ancient_joseph.sql`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/meta/0000_snapshot.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/meta/0001_snapshot.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/meta/0002_snapshot.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/meta/0003_snapshot.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/meta/0004_snapshot.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/meta/0005_snapshot.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/meta/0006_snapshot.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/meta/0007_snapshot.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/meta/0008_snapshot.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/meta/0009_snapshot.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/.openai/drizzle/meta/_journal.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/server/index.js`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/0000_tidy_spitfire.sql`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/0001_round_gladiator.sql`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/0002_rich_morg.sql`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/0003_lethal_zzzax.sql`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/0004_deep_major_mapleleaf.sql`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/0005_same_daredevil.sql`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/0006_watery_siren.sql`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/0007_calm_alerts.sql`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/0008_heavy_vance_astro.sql`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/0009_ancient_joseph.sql`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/meta/0000_snapshot.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/meta/0001_snapshot.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/meta/0002_snapshot.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/meta/0003_snapshot.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/meta/0004_snapshot.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/meta/0005_snapshot.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/meta/0006_snapshot.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/meta/0007_snapshot.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/meta/0008_snapshot.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/meta/0009_snapshot.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/drizzle/meta/_journal.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/scripts/build_worker.py`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/scripts/market-overview.test.mjs`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/scripts/worker-smoke.mjs`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/tests/convergence-engine.test.mjs`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/tests/research-adapters-freshness.test.mjs`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/tests/test_build_worker_asset_versions.py`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/worker/README.md`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/worker/alpaca.js`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/worker/index.js`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/worker/mcp.js`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/worker/morgue-snapshot-metadata.json`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/worker/morgue.js`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/worker/operations.js`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/worker/reports.js`
- `packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/worker/terminal.js`

Source files are verbatim copies from the origin location named above unless a sanitization note appears in this doc.

## Sanitization note

This copy was sanitized at 21 point(s) to pass the public-repo privacy gate; the private original in dwj9ddyvf6-hub/Silicon branch main : apps/shipyard-research-terminal/ is the verbatim source.
Sanitized files in this package (non-verbatim copies):
- packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/INSTALLATION-AUDIT-2026-10-28.md: 15 occurrence(s) replaced
- packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/dist/server/index.js: 3 occurrence(s) replaced
- packages/ausar/shipyard-research-terminal/apps/shipyard-research-terminal/worker/terminal.js: 3 occurrence(s) replaced
