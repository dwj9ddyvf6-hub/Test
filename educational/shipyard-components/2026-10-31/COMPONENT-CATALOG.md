# Component catalog

Status terms: **source included** means present at pinned source commit or extracted with provenance in `references/extracted-component-provenance.json`; this does not mean deployed or operational. **Experimental candidate** means local source is retained but no adoption/deployment is claimed. **Contract only** means the tool/interface shape is described while host execution is omitted.

## Namespace warning — do not match engines by number alone

`FE01`–`FE30` below name scorer ports in this collection’s Silicon namespace at pinned source commit `6ef9c064517f57a969fd4b44345306edd9e7956c`. The separate Test `terminal-lineup/` namespace labels different designs `Engine 13/17/26`: their specified systems and formula/input contracts are not this collection’s `FE13/17/26`. The audited Test files are design/workflow evidence, not producers, and did not close a producer gap. Establish identity only with a namespace + repository/commit + source path + formula/target/input contract; never crosswalk on `FE##`/engine number alone. See the [pinned Test Engine 13, 17, and 26 workflow files](https://github.com/dwj9ddyvf6-hub/Test/tree/0c96771950c2fa7d19833d1c44cd4c8a542f1455/terminal-lineup) and [design-only engine list](https://github.com/dwj9ddyvf6-hub/Test/blob/0c96771950c2fa7d19833d1c44cd4c8a542f1455/terminal-lineup/FORECAST-ENGINES-30.md); the detailed evidence links are in [START-HERE](START-HERE.md).

## Forecast scorers and source-feature builders — source included; operation unverified

- `dist/forecast-engines.mjs` exposes 30 pure scorer ports (`FE01`–`FE30`); `dist/forecast-engine-catalog.mjs` supplies their input schemas, ranges, horizons and provenance status. The selected scorer tests use synthetic/golden values. These are descriptive research calculations; missing, unknown or out-of-range values abstain.
- Producer/builder modules present at this source commit are selected: `FE01`–`FE10` (FE07–FE10 share a bundle), `FE12`, and `FE27`–`FE30`, plus the individually included source readers under `research/forecast-features/`. **FE11 and FE13–FE26 have scorer/catalog entries only; no producer module for those IDs exists in the pinned tree.** Do not infer builders or runtime coverage from the scorer catalog.
- `worker/forecast-fe*.js` plus `worker/forecast-tools.js` provide bounded source adapters for selected policies; host router and deployment are absent. Newly reconstructed policies are experimental/unvalidated and decision-ineligible unless a policy says otherwise.

## Evidence and source adapters — source included; host calls unavailable

- `dist/evidence-contract.mjs` is a schema/hash/source-registry layer; `dist/research-adapters.mjs` selects and labels completed daily bars and computes deterministic daily indicators. Stale, future-dated or incomplete evidence must remain unavailable/abstained.
- `worker/alpaca.js`, `market-readers.js`, `intraday-reader.js`, `exchange-calendar.js`, `official-events.js`, `preopen-inputs.js`, `options-research.js`, `brokers.js`, `connected-research.js`, `research-outputs.js`, and `source-research-routes.js` are adapters, not standalone engines. They expect a caller/host and may require a provider credential or database. Do not infer entitlement, freshness or operational state from source code.
- `components/public-feed-parsers.mjs` contains only pure parsers for synthetic Treasury/Federal Reserve/Cboe sample data. Fetchers, routes, caches, remote URLs and data captures remain out of scope.
- `worker/psychology.js` is the current bridge integration source in this checkout; live binding/deployment is unverified. It applies a transparent lexicon-derived descriptive headline-tone method to existing news; it is not validated as predictive. No private history or raw headlines are in this collection.

## Component-only analytical labs extracted from `dist/app.js`

These eight groups are local-input logic, **not** provider integrations or a terminal UI. Their declaration provenance and source hashes are in `references/extracted-component-provenance.json`; synthetic/known-answer tests are in `tests/component-labs.test.mjs`.

| Module | Source behavior retained | Inputs and key limits | Important boundary |
|---|---|---|---|
| `components/static-gex.mjs` | CSV validation, Black–Scholes gamma, signed OI GEX by strike and spot-grid zero crossing | One symbol/date/spot; CSV OI/IV/DTE and explicit rates/multiplier/grid | Open interest is not dealer inventory; model does not forecast; no live chain |
| `components/bullflow-activity.mjs` | CSV print/coverage validation and completeness-aware activity ratios | User print rows, source/side/timestamp labels, explicit session coverage; 20 prior complete baseline sessions required for ratios | Unknown/incomplete/cancelled/side provenance is preserved; not OPRA or a live tape |
| `components/finviz-filter.mjs` | CSV parsing, documented filter subset, sorting and tag mapping | User cross-sectional rows; tags are accepted as supplied, not detected | No vendor API; subset implementation only |
| `components/stockrover-factors.mjs` | 23-field metric schema, cross-sectional midrank percentiles, category/composite completeness | Single decision-date user CSV; no imputation; fixed desk-defined equal weights | Not the vendor model; no vendor feed or PIT verification |
| `components/confluence.mjs` | Manual eight-category candidate and effective-leaf aggregations | Explicit manual 0–100 scores and optional confidence/index count | Manual candidate, not an authenticated score or sourced evidence |
| `components/portfolio.mjs` | Candidate eligibility, sector/name ranking, equal weighting and dated rebalance review schedule | User CSV; dated schedule requires declared snapshot completeness/freshness | Not an account connector, holdings book, advice or order route |
| `components/daily-change-alerts.mjs` | Daily close-to-close alert condition | Explicit alert definitions and daily bars | Pure-function adaptation returns new alert state; host persistence/polling/push omitted |
| `components/strategy-sma.mjs` | Close-only SMA replay with one-bar delay, costs and in/out-of-sample split | Explicit Date/Close CSV and parameters | Not Saty/RRE, a forecast, or an execution engine; no orders |

The source alert callback’s browser-state mutation/persist behavior was changed to a pure return value. The SMA analyzer no longer defaults to app-global state; pass its settings explicitly. Those are documented integration adaptations, not silent formula changes.

## Chart / market technical modules

- `dist/market-overview.mjs`: pure session-date formatting, chart axis layout, daily-bar summary and refresh-age utilities. Its original component test is included; one defective synthetic prior-bar fixture was corrected in the exported test only.
- research/chartslector/adapter.mjs: bounded relative-strength/stage/ratio/momentum calculations on aligned daily OHLCV panels; no acquisition, ranking, sizing or orders. original.py uses three pinned owner-supplied archive sources. Additional owner-supplied archived sources are represented in archive_reference/: pure cl_core, ranker features, screen masks, scalar Pine references, and inert source-text research/test harnesses. Harnesses are not executed; raw capture evidence, input panels, fitted ranker coefficients, outputs and staged runtime are absent. NumPy/Pandas are required and the shared indicator imports Numba; no Python dependency lock or JIT validation is supplied. See [ChartsLector archive reference](research/chartslector/archive_reference/README.md) for per-file provenance, dependencies, and include/hold reasons.
- `research/live-lector/`: pinned chart-only technical/setup research engine and source manifest. Source is retained; the local registry was cleared of private entries and a bundle recreation check was run.
- `research/live-aperture/`: bounded engine/adapter source with synthetic fixtures. It is an **experimental/retired candidate**, not asserted as a deployed baseline.

## Python research runners

- `deploy/python-research-service/engine_adapters.py` maps timestamped, explicit input payloads to pinned Saty/RRE engines; `service.py` provides bounded local job storage/API. Expected inputs include source/feed/adjustment, calendar and event-coverage lineage; stale/missing/inconsistent inputs are rejected. Tests use synthetic fixtures and temporary databases. No broker/account/order modules are included.
- It is calculation/reference code, not a deployable production service package: systemd/Nginx/certificates/host bindings are excluded.

## Coverage indexes and reference corpus

- `references/component-coverage.md` and `.json` map **32 engine IDs, 31 surface IDs, and all 36 MCP tool names** to included source versus host-bound/contract-only boundaries. Sanitized JSON schemas preserve tool input shape; no router, live URL, credential, output receipt or runtime-status response is included.
- The public InfinityBlade Engineering Doctrine repository is referenced at commit `11aae28d5072dc81ec6cdb32b26d4ed8f3ec7614`; its 17-file coverage was verified locally. The full corpus is not copied here.
