# Terminal morgue adapter

Created by Ausar. Packaged into the Test repo on 2026-10-29 (packaging pass).

Origin: dwj9ddyvf6-hub/Silicon branch main, apps/silicon-market-terminal/ (morgue-adapter.mjs and MORGUE-ADAPTER.md, carried in the Silicon Market Terminal package).

A metadata-only adapter over a saved Morgue snapshot file. It exposes GET /api/engines/morgue/v1/snapshot on the local terminal server (read-only, loopback-bound, Host/Origin checked; it never calls a provider or launches a build). Version 1.1 returns only the registered source ID and registry version (rights marked unknown, sole allowed purpose integrity inspection), the snapshot generation time and as_of_session date, a SHA-256 integrity hash of the saved bytes, and presence flags for the ten expected top-level sections. It never returns ticker values, rankings, payloads, account data, or order instructions, and it reports decision, performance-claim, and order use as blocked. Operational readiness is reported separately at GET /api/health/readiness with freshness left unknown until session-calendar budgets are configured.

## Files in this package


Source files are verbatim copies from the origin location named above unless a sanitization note appears in this doc.
