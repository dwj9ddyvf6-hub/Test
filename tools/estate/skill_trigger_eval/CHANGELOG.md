# Skill trigger eval change record
Benchmark delta line format (mandatory in every change record): `benchmark delta: accuracy <before> -> <after> (test split, holdout-selected; train <score>)`, plus time and tokens when telemetry exists.
Mutation strategy line (mandatory since 2026-11-03, A-13): `mutation strategy: add_example | add_constraint | restructure | add_edge_case` (exactly one, named by the analyst pass in analyst.py). GEPA feedback (A-28): a failed fixture's change record also carries its one-paragraph textual feedback from gepa.py.

## eval_local-stock-analysis.json winner=current
benchmark delta: accuracy 0.667 -> 0.667 (test split, holdout-selected; train 0.667)
