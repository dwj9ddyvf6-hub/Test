# Silicon Market Terminal

Created by Ausar. Packaged into the Test repo on 2026-10-29 (packaging pass).

Origin: dwj9ddyvf6-hub/Silicon branch main, apps/silicon-market-terminal/.

A dependency-free, local-first market-intelligence terminal prototype (Node server.mjs on port 4173, plain browser modules, no build step). It runs in synthetic demo mode unless a read-only vendor API key is set server-side. Included workflows, per its own README: market overview, searchable options-flow table, GEX/Greek exposure views, dark-pool prints, congressional and insider activity, screener, event calendar, ticker research with options chain, watchlists and local alert rules, a vendor coverage map for the teardown target families, and a set of local labs (Confluence, Sector Portfolio, Static GEX, 15.87 Rule map, option strategy payoff, Options Activity Profile, Filter Contract, Stock Rover Factor Profile, and a close-only Strategy Lab with SMA long-or-flat rule, one-bar delay, and per-side costs). All state persists in browser storage; the server proxies only an allowlist of read-only GET market-data routes.

## Files in this package

- `packages/ausar/silicon-market-terminal/apps/silicon-market-terminal/EVIDENCE-CONTRACT.md`
- `packages/ausar/silicon-market-terminal/apps/silicon-market-terminal/MORGUE-ADAPTER.md`
- `packages/ausar/silicon-market-terminal/apps/silicon-market-terminal/README.md`
- `packages/ausar/silicon-market-terminal/apps/silicon-market-terminal/app-bootstrap.mjs`
- `packages/ausar/silicon-market-terminal/apps/silicon-market-terminal/app.js`
- `packages/ausar/silicon-market-terminal/apps/silicon-market-terminal/candidate-calculation-fixtures.mjs`
- `packages/ausar/silicon-market-terminal/apps/silicon-market-terminal/evidence-contract.mjs`
- `packages/ausar/silicon-market-terminal/apps/silicon-market-terminal/index.html`
- `packages/ausar/silicon-market-terminal/apps/silicon-market-terminal/morgue-adapter.mjs`
- `packages/ausar/silicon-market-terminal/apps/silicon-market-terminal/morgue-readiness-fixtures.mjs`
- `packages/ausar/silicon-market-terminal/apps/silicon-market-terminal/server-smoke.mjs`
- `packages/ausar/silicon-market-terminal/apps/silicon-market-terminal/server.mjs`
- `packages/ausar/silicon-market-terminal/apps/silicon-market-terminal/styles.css`
- `packages/ausar/silicon-market-terminal/apps/silicon-market-terminal/vendor-coverage.json`

Source files are verbatim copies from the origin location named above unless a sanitization note appears in this doc.
