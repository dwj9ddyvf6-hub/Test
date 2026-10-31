# Live Lector engine source (historical candidate)

This is a bounded chart-pattern/technical-analysis code component extracted from the pinned source tree. It is retained as educational source, not presented as the deployed terminal or as a proven model. `build_bundle.py` validates the exported source files in `SOURCE_MANIFEST.json`; `engine.mjs` and `run.mjs` expose the local computation.

The input contract is a completed, timestamped primary bar series plus explicit provider/feed/adjustment and observation clocks; source gaps, invalid history and stale data should remain abstentions. It omits portfolio, account, news, broker, order, and UI state. Run `node --test ../..` only from the test list in the root `START-HERE.md`; no live provider access is performed by component tests.

The source manifest validates exported bytes and retains original Git blob claims; the full source-tree manifest records the export redactions. The historical registry of internal research/navigation notes was replaced with an empty array to keep the code boundary without carrying those notes. A pin proves source bytes only, not license rights, historical availability, performance, current deployment, or operational access. Adapt only after independently reviewing provenance, provider licensing, and test fixtures.
