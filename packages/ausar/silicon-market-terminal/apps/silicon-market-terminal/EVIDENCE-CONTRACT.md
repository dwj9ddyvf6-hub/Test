# Evidence and source-rights contract

Version 1.0.0 establishes the shared data boundary for Silicon's local terminal. The Option Strategy Lab and close-only Strategy Lab now emit contract-validated observation and derived-feature records. Other labs and displayed calculations are not yet retrofitted, and this does not certify the current prototype.

## What the contract records

- **Canonical observation:** stable observation ID, canonical entity and venue, typed measure and unit, evidence state, source/version/capture hash, source rights, coverage/missingness, and correction revision.
- **Five separate clocks:** event time, publication time, first-available time, ingestion time, and decision/as-of time. Unknown or inapplicable values are `null` with a reason. Availability must carry `verified`, `source_reported`, or `unknown` evidence and a traceable reference when claimed; event time is never silently substituted for availability time.
- **Derived feature lineage:** versioned method reference and implementation hash, parameter hash, parent observation IDs, source-family IDs, as-of/computation times, evidence status, coverage status, and optional result hash. Shared source-family IDs expose correlated inputs so transformed copies of one feed cannot be counted as independent confirmation.
- **Explicit absence states:** `no_data`, `partial`, `stale`, `delayed`, `known_zero`, `rejected`, and `inferred` remain distinct. `known_zero` requires literal numeric zero; `no_data` and `rejected` require `null` and an explicit reason. Complete coverage also has to reconcile observed and expected counts.

The machine-readable schemas, registry, cross-runtime SHA-256/stable-ID helpers, validators, and decision/lineage eligibility gates live in [`evidence-contract.mjs`](./evidence-contract.mjs). The browser bootstrap and local server load that same contract module; the API serves it from `GET /api/evidence-contract` behind the existing loopback host/origin checks and GET-only API boundary.

## Initial source registry

| Source | Current disposition | Allowed scope in this prototype |
|---|---|---|
| Silicon synthetic fixtures | Internal fixture only | Illustration and UI exercise; blocked for trading decisions and performance claims. |
| User-selected CSV | User-asserted local scope; file rights are not independently verified | Browser-memory analysis; no upload or raw-row persistence. |
| User-entered values | User-asserted local scope | Browser-memory calculation; provenance and timing must still be recorded. |
| Unusual Whales API proxy | Entitlement and redistribution rights unverified | Diagnostic read-through only. The key does not prove entitlement; terminal ingestion and persistence remain disabled. |

The registry is intentionally narrow: it describes the actual prototype sources. It is not a blanket clearance for the 86 REA families, any vendor artifacts, market-data redistribution, or future providers. Adding a source requires a separate source record with an evidence-backed rights/entitlement decision.

## Decision eligibility

`assessDecisionEligibility` fails closed unless the observation validates, its source is registered for the requested purpose, copied rights status matches the registry, availability is verified and its reference appears in the reviewed availability-evidence registry, availability and ingestion are no later than the decision time, the state is observed or known-zero, and coverage is complete or not applicable. That reviewed reference registry is deliberately empty in v1.0.0 because none of the current terminal adapters has source-level availability evidence wired into it; therefore no observation is decision-eligible by default. Synthetic fixtures, unknown entitlements, stale/partial/missing data, and unverified point-in-time availability cannot pass this gate. A reference string supplied by an observation is not itself proof.

`assessFeatureLineage` also requires every parent observation to be supplied and eligible at the feature's as-of time. A feature with missing parents is not replayable. The Option Strategy Lab records the user's scenario assumptions as an inferred local input pack. Strategy Lab hashes the imported file bytes, retains canonical rows only in the browser tab, and downloads a JSON evidence bundle containing those rows, the analysis records, method/parameter/result hashes, and eligibility blockers. For both labs, source availability remains unknown and the CSV coverage is not independently verified, so neither record is decision-eligible. The other labs have not yet been converted, so their outputs should not be described as contract-validated.

## Remaining Phase 4 work

1. Reconcile instrument identifiers, corporate actions, calendars, sessions, contract terms, units, and timezone/DST handling across the current CSV labs.
2. Add immutable correction/revision storage and a persisted, content-addressed lineage DAG.
3. Record provider-specific retention and output/redistribution terms before enabling any external source ingestion.
4. Migrate the remaining labs to emit observation and feature envelopes, then show source, as-of time, freshness, coverage, and eligibility with every displayed value. Strategy Lab is now the second migrated surface; seven other candidate labs remain open.
5. Expand contract fixtures and boundary tests for no-data versus known-zero, missing clocks, late availability, corrections, and correlated parents. Current Option Strategy and Strategy Lab fixtures cover valid records whose decision and lineage eligibility fail closed for unknown availability or coverage.

Phase 4 is **in progress**, not complete. End-to-end replayability for every displayed value remains an acceptance gate.
