# psychology-engine/live-engine/: the current working source

The live psychology engine as it runs on the desk, snapshotted 2026-11-16:
the engine core (psychology_engine.py), the daily pipeline (pipeline.py,
run_daily.py), collectors/, compiler/, publish/, and its test suite.

This sits alongside the curated public releases in the parent area
(README.md, PUBLIC_VALIDATION.md, audit/, engine/) and does not replace
them. Code and docs only: the engine's data (history/, live/, output/,
backfill/, exhibits/) and its name registry stay local by design.
