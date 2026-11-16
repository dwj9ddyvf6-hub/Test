"""core.raschke_rre — Astra's RRE Adaptive Desk v0.2.0 brain,
ported faithfully (PORT-SPEC.md, workflow raschke-rre-20261023).

Lineage: the underlying methods are Linda Raschke's; the engine
design is Astra's ("RRE Adaptive Desk v0.2.0", RRE = Raschke
Research Engine), Silicon dwj9ddyvf6-hub/Silicon
research/linda_raschke/v02/, commit 59b11df1a3ff.

raschke_core.py, raschke_engine.py, awareness.py and router.py
are BYTE-IDENTICAL to the shipped package (MANIFEST.json hashes
pinned by the trap blocker). admission.py is the adapted
SPY-linear admission decision from his execution.py (section
2.5 of the spec). His broker/SQLite/service layers do not exist
here: the desk dispatcher, Ink filing door and virtual slices
own execution and accounting. RRE3 / options / futures are not
ported.
"""
