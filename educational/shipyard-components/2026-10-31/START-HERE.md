# Start here — public education component collection

This is a **readable educational source collection for LLM-assisted study**, not the terminal UI, live service, training system, self-training loop, or a deployable backup. It was assembled locally from source commit `6ef9c064517f57a969fd4b44345306edd9e7956c`. Source checkout and private corpus originals were preserved; no external publication or remote write was performed.

## Read first

1. [Component catalog](COMPONENT-CATALOG.md) — what each reusable module computes, its inputs and limits.
2. [Integration boundaries](INTEGRATION-BOUNDARIES.md) — what host dependencies are intentionally missing.
3. [Scope and omissions](SCOPE-AND-OMISSIONS.md) — private/sensitive exclusions and redactions.
4. [Finite component coverage](references/component-coverage.md) — 32 engine IDs, 31 surfaces, and 36 tool contracts; no runtime state is copied.
5. [Source provenance](references/extracted-component-provenance.json) — exact extraction function names, source file hashes and transformations.
6. [License inventory](LICENSE-INVENTORY.md) — upstream/source rights caveats.

## Namespace warning: forecast-engine IDs are not universal

Treat an engine ID as a namespaced identifier, not a globally stable number. This collection’s `FE01`–`FE30` are the Silicon scorer namespace at source commit `6ef9c064517f57a969fd4b44345306edd9e7956c`; similarly numbered `Engine 13/17/26` designs in the separately pinned Test `terminal-lineup/` are different systems. Their formulas, targets, and inputs do not match this collection’s `FE13/17/26`, and the audited Test paths did **not** close any producer gap. The Test design document labels its 30 engines as design-only, with no forward record. Never join by a bare `FE##`/engine number: require namespace, repository+commit, source path, and formula/target/input contract.

Pinned evidence: [Engine 13 workflow](https://github.com/dwj9ddyvf6-hub/Test/blob/0c96771950c2fa7d19833d1c44cd4c8a542f1455/terminal-lineup/workflow-build-engine13.js), [Engine 17 workflow](https://github.com/dwj9ddyvf6-hub/Test/blob/0c96771950c2fa7d19833d1c44cd4c8a542f1455/terminal-lineup/workflow-build-engine17.js), [Engine 26 workflow](https://github.com/dwj9ddyvf6-hub/Test/blob/0c96771950c2fa7d19833d1c44cd4c8a542f1455/terminal-lineup/workflow-build-engine26.js), [Test design-only engine list](https://github.com/dwj9ddyvf6-hub/Test/blob/0c96771950c2fa7d19833d1c44cd4c8a542f1455/terminal-lineup/FORECAST-ENGINES-30.md), [picker-replay report](https://github.com/dwj9ddyvf6-hub/Test/blob/0c96771950c2fa7d19833d1c44cd4c8a542f1455/terminal-lineup/records/picker-replay-2026-10-27/forecast-p1-2026-10-27.md), and [Snowflake semantics (separate tools)](https://github.com/dwj9ddyvf6-hub/Test/blob/0c96771950c2fa7d19833d1c44cd4c8a542f1455/terminal-lineup/specs/snowflake-semantics.md).

## Reusable components

- `components/` — eight analytical labs extracted from the client bundle, shared CSV/date validators, plus public-source parsers. Manual CSV tools are local input logic, not live provider integrations.
- `dist/` — evidence contract, daily research adapters, selected forecast scorers/catalog, market-overview helpers, and a separated generic evidence-CSV parser. Private vendor catalogs are absent.
- The research tree contains selected forecast features, the ChartsLector adapter and owner-supplied archival algorithms/inert harness text ([per-file archive guide](research/chartslector/archive_reference/README.md)), Live Lector and experimental/retired Live Aperture source.
- `worker/` — selected host-bound adapters/producers only; no whole Worker/router/MCP app.
- `deploy/python-research-service/` — local Saty/RRE source plus bounded service adapter, not configured for production deployment.
- `tests/` — synthetic fixtures, component tests and known-answer/negative tests. No tests contact a provider or prove current operation.

Useful public reference projects already published elsewhere (not duplicated here): [technical analysis study](https://github.com/dwj9ddyvf6-hub/Test/tree/main/research/technical-analysis-study-2026-10-30), [technical analysis mastery notes](https://github.com/dwj9ddyvf6-hub/Test/tree/main/docs/research/technical-analysis-mastery-20261030), [Psychology engine](https://github.com/dwj9ddyvf6-hub/Test/tree/main/psychology-engine), and [Psychology research notes](https://github.com/dwj9ddyvf6-hub/Test/tree/main/docs/research/psychology-engine-2026-10-30). These links identify educational resources, not live tool access. Agent-methods publication is pending on a separate branch and is not claimed on `main`.

## Checks

Requirements: Node.js 20+ (tested with Node `24.22.1`), pinned pnpm 11.25.0 for the full Node suite, and Python 3.10+ for Python components. No `node_modules` is included. Smoke, the direct extracted-module suite and the Python suite use installed language runtimes; the full selected Node component suite imports packages pinned in `package.json` / `pnpm-lock.yaml`.

```sh
# dependency-free smoke and extracted-module checks
node scripts/test-smoke.mjs
node --test tests/component-labs.test.mjs tests/market-overview.test.mjs tests/research-adapters-freshness.test.mjs
python3 scripts/test-python.py

# optional full selected Node suite; installs only pinned lockfile dependencies
pnpm install --frozen-lockfile
node scripts/test-components.mjs
```

The ChartsLector archive-reference suite is optional and requires NumPy/Pandas; its test-only no-op Numba decorator is documented in that package README. It does not run the inert .reference.txt harnesses. The smoke and included synthetic tests validate only the exact assertions executed. They do not establish provider entitlement, fresh data, deployed behavior, method calibration, profitability, or operational readiness. The source package versions and exact test execution evidence are in `VALIDATION-RESULTS.md`.

## Safe adaptation

Start from an individual module. Keep credentials at the host boundary, use synthetic or independently licensed data, preserve source clocks, units, missingness and rights metadata, and fail closed on unverified/incomplete inputs. Treat `__…__` and `[...NOT_INCLUDED]` bindings as explicit missing integrations, never working defaults. This collection grants no blanket reuse license. That is not a finding that owner-controlled publication is forbidden; applicable per-file/upstream rights and provider terms require separate review.
