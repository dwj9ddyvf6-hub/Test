# Morgue snapshot metadata adapter

The local terminal exposes `GET /api/engines/morgue/v1/snapshot`, backed by the checked-in `research/morgue-engine/output/morgue-feed.json` snapshot. The route is read-only, loopback-bound, and protected by the server's local Host/Origin checks. It does not call a provider or launch a Morgue build.

The version 1.1 adapter returns only:

- the registered source ID and source-registry version, with rights explicitly marked unknown and the sole allowed purpose set to integrity inspection;
- the snapshot's timezone-qualified generation time and `as_of_session` date;
- a SHA-256 integrity hash of the saved bytes (this does not establish authenticity);
- presence flags for the ten expected top-level sections.

It never returns ticker-level values, rankings, source payloads, account data, or order instructions. The Data & Privacy screen requests the summary only after the user selects **Inspect saved snapshot metadata** and displays the registered source ID, rights/redistribution state, allowed purpose, registry version, and snapshot metadata.

The shared source registry records `morgue.local-snapshot` as `metadata_only`, with rights and redistribution unknown; the adapter verifies this registry entry at startup and echoes its ID and version. The response also reports availability as unknown, point-in-time validation as not run, and decision, performance-claim, and order use as blocked. The session date is not a timestamp and is not converted into one. This metadata-only slice does not make the Morgue feed a canonical observation or feature under Evidence Contract v1.0.0. Any adapter that exposes measurements needs source-specific rights, availability, clocks, coverage, and lineage review first.

The currently checked-in feed is generated at `2026-10-27T23:19:28.722710+00:00` for session `2026-10-26`. Its date labels describe that saved artifact only; they do not establish that it is current for a later date.

Operational readiness is exposed separately at `GET /api/health/readiness`. It reports artifact presence/validity, section counts, snapshot age relative to the local clock, and current evidence gates. Freshness remains `unknown` until an exchange-session calendar and source-specific freshness budgets are configured. This endpoint returns no market values and never marks the feed eligible for a decision, performance claim, or order.
