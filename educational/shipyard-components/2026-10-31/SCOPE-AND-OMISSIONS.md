# Scope and omissions

## Purpose and evidence model

This local collection is a component-oriented public education/resource handoff for LLMs, not a terminal archive, app migration, production backup, live terminal, or self-training loop. It preserves selected engine/tool/module source, associated tests and synthetic fixtures, necessary shared dependencies, license notices and wiring boundaries. “Included” describes source availability at a pinned commit or a documented extraction, not deployment status. `references/component-coverage.json` is the finite coverage index for the 32 source-declared engine IDs, 31 surface IDs and all 36 MCP tool names.

## Intentionally absent or contract-only

- Browser UI, bundled site/app code, app bootstrap/router, complete Worker entrypoint, MCP dispatcher, server package, deployment bundle, hosting configuration, private URLs/site/account identifiers, credentials, and runtime/database bindings. A deployable terminal cannot be reconstructed from this collection.
- Private account/portfolio data, paper-book snapshots, strategy outputs/rankings, operational receipts/logs, runtime capability receipts, databases, provider captures and raw evidence/corpus data. No raw market/evidence capture is included.
- Full tool implementations for host-bound reads/writes. Sanitized MCP input JSON Schemas and operation classes are documented, but call routing, output projection, provider access, persistence and side effects are absent. Provider-bound modules included under `worker/` require a separately authorized host to exercise.
- Private vendor coverage/source catalog rows, internal audit/research/installation notes, compiled UI bundle, engine-survivor/family-crosswalk catalogs, feed/snapshot metadata, and app-level dependency/audit table. Only the generic public evidence CSV parser was separated from `dist/convergence-engine.mjs`; this source has no hidden scoring function and is not included as a “convergence engine.”
- `dist/morgue-adapter.mjs` and private Morgue snapshot/runtime metadata. Its helpers are coupled to internal source registries and feed paths; no source rows or readiness snapshots are retained.
- research/chartslector raw provider evidence, captured market panels, fitted model coefficients, generated research outputs, and staged runtime datasets remain excluded. All eight remaining owner-supplied archive source files are represented in archive_reference/: two byte-identical pure modules, two path-sanitized analytical modules, and four source-only/inert algorithm-or-harness references. Harnesses with top-level reads/writes are .py.reference.txt and not run. The source is not omitted for a third-party-license reason; no blanket reuse license is granted by this handoff.
- FE11 and FE13–FE26 producer modules: the pinned source has scorer/catalog ports for FE01–FE30, but does not contain producer modules for these IDs. The included catalog is not a claim that those feature builders exist.
- Non-selected UI/browser/integration tests and tests requiring a whole app/router, private data, real provider, or private service. Their absence is not a pass.
- Full standalone Psychology v0.4.1 package is not duplicated. The current Psychology bridge/migration/test boundary is included; standalone package and research materials are linked in START-HERE.
- The InfinityBlade Engineering Doctrine corpus remains in its original local location and is referenced by the exact pinned public repository/commit only; it is not vendored.

## Redaction and provenance

`SOURCE-MANIFEST.json` contains exact public source paths/hashes for included code and stable opaque IDs/category/reason for omitted/private source records. The complete per-path private reconciliation mapping is kept separately outside this export directory; it is not part of the public handoff. `references/extracted-component-provenance.json` records source hashes and per-declaration hashes for component extraction, including intentional pure-function API adaptations. Never treat a redacted or contract-only entry as live functionality.

## Rights caveat

No repository-wide license for the terminal source was found in the pinned tracked tree. This collection grants no blanket reuse license; applicable per-file and separately pinned upstream rights remain distinct. A separate review of included third-party source rights is being handled independently, and provider terms are separate. This caveat is not a finding that owner-controlled publication is forbidden; it does not settle whether any particular portion may be published or reused.
