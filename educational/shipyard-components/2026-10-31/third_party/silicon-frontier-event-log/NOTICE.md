# Silicon Frontier Event Log attribution

The Codex Desk's bounded history paging adapts the cursor-based, limited-read approach from `src/event-log.ts` in [`siliconjungle/-shapeshift-labs-frontier-event-log`](https://github.com/siliconjungle/-shapeshift-labs-frontier-event-log), commit `e3e73e9b33475b059ba8ec74a4dd1ff14859f025`.

The desk implementation is tailored to its existing D1 observation history. It uses a stable `(created_at, revision, rowid)` keyset cursor, keeps the existing as-of and symbol filters, and does not add the upstream package as a runtime dependency.

Copyright and license notice: see [`LICENSE`](./LICENSE), Copyright (c) 2026 Shapeshift Labs.
