# Terminal evidence contract

Created by Ausar. Packaged into the Test repo on 2026-10-29 (packaging pass).

Origin: dwj9ddyvf6-hub/Silicon branch main, apps/silicon-market-terminal/ (evidence-contract.mjs and EVIDENCE-CONTRACT.md, carried in the Silicon Market Terminal package).

Evidence Contract v1.0.0 is the shared data boundary for the terminal. It records canonical observations (stable ID, canonical entity and venue, typed measure and unit, evidence state, source, version and capture hash, source rights, coverage and missingness, correction revision), five separate clocks (event, publication, first-available, ingestion, decision/as-of), derived-feature lineage (versioned method reference and implementation hash, parameter hash, parent observation IDs, source-family IDs so correlated copies of one feed cannot count as independent confirmation), and explicit absence states (no_data, partial, stale, delayed, known_zero, rejected, inferred) as distinct values. The module ships machine-readable schemas, a source registry, SHA-256 and stable-ID helpers, validators, and decision/lineage eligibility gates; the server serves it at GET /api/evidence-contract behind loopback and GET-only checks.

## Files in this package


Source files are verbatim copies from the origin location named above unless a sanitization note appears in this doc.
