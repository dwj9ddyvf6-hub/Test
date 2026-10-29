# Shipyard live-site runtime (shipyard branch)

Created by Ausar. Packaged into the Test repo on 2026-10-29 (packaging pass).

Origin: dwj9ddyvf6-hub/Silicon branch codex/shipyard-live-terminal, apps/silicon-market-terminal/live-site-runtime/.

The owner-only live-site runtime of the Shipyard Research Terminal: the deployed dist bundle plus Worker and docs. Per its README and live-data audit: Trade Brain streams actual Alpaca SIP quotes while entitled and falls back to the real-time IEX feed when SIP is denied (server-side credentials never enter the browser, at most five watchlist symbols, origin validated); it rechecks quotes, completed IEX daily bars, session hours, and Alpaca indicative option snapshots once per minute, and stale or missing inputs produce no setup. Market Overview and chart pages load split-adjusted IEX daily bars refreshed every five minutes; Market Context refreshes every fifteen minutes. There is no background scan: closing the page stops the stream. Options flow, dark pool, news, and screener feeds remain disconnected and show unavailable states rather than sample data.

## Files in this package

- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/INSTALLATION-AUDIT-2026-10-28.md`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/PRODUCTION-VERIFICATION-2026-10-29.md`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/README.md`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/.openai/hosting.json`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/dist/app-bootstrap.mjs`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/dist/app.js`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/dist/candidate-calculation-fixtures.mjs`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/dist/convergence-engine.mjs`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/dist/evidence-contract.mjs`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/dist/favicon.svg`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/dist/index.html`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/dist/market-overview.mjs`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/dist/morgue-adapter.mjs`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/dist/morgue-readiness-fixtures.mjs`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/dist/research-adapters.mjs`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/dist/styles.css`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/dist/vendor-coverage.json`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/dist/.openai/hosting.json`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/dist/server/index.js`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/docs/LIVE-DATA-OPERATIONAL-AUDIT-2026-10-29.md`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/docs/OPTIONS-DATA-ACCESS-2026-10-28.md`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/scripts/build_worker.py`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/scripts/market-overview.test.mjs`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/scripts/worker-smoke.mjs`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/worker/README.md`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/worker/alpaca.js`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/worker/index.js`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/worker/mcp.js`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/worker/morgue-snapshot-metadata.json`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/worker/morgue.js`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/worker/operations.js`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/worker/reports.js`
- `packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/worker/terminal.js`

Source files are verbatim copies from the origin location named above unless a sanitization note appears in this doc.

## Sanitization note

This copy was sanitized at 21 point(s) to pass the public-repo privacy gate; the private original in dwj9ddyvf6-hub/Silicon branch codex/shipyard-live-terminal : apps/silicon-market-terminal/live-site-runtime/ is the verbatim source.
Sanitized files in this package (non-verbatim copies):
- packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/INSTALLATION-AUDIT-2026-10-28.md: 15 occurrence(s) replaced
- packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/dist/server/index.js: 3 occurrence(s) replaced
- packages/ausar/shipyard-live-site-runtime/apps/silicon-market-terminal/live-site-runtime/worker/terminal.js: 3 occurrence(s) replaced
