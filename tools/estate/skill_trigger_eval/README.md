# Skill trigger eval format (round-5 item 27, phase 1)

Eval set: one JSON file per skill: `{"skill": "<name>", "cases": [{"query": "...", "expect": "trigger"|"no-trigger", "split": "train"|"test"}]}`.
Stratified train/test split; description winner selected on TEST score only.
Runner: `runner.py selftest`; production scoring takes a matcher recording
the host trigger decision, 3 runs per query, threshold 0.5.
Every change record carries a benchmark delta line (pass rate; time and
tokens when telemetry exists).
Phase 2 (built 2026-11-02, wiring pass): `phase2.py` — holdout-selected
improver loop fed only failures plus attempt history, do-not-repeat
instruction enforced before scoring, blind A/B with hash-masked labels.
Change record: `CHANGELOG.md` in this directory (benchmark delta line
format stated in its header). First real run: `eval_local-stock-analysis.json`
with `candidates_local-stock-analysis.json`; winner `current` (the live
description), test accuracy 0.667 under the token-overlap matcher.

Analyst pass (A-13, landed 2026-11-03): `analyst.py` — the Executor /
Analyst / Mutator split. The runner is the Executor; before any Mutator
edit, an analyst pass must name exactly one mutation strategy per change
from the four-value enum `add_example | add_constraint | restructure |
add_edge_case`, recorded in the change record beside the benchmark delta
line. `analyst.py selftest` enforces the enum; a change record with a
missing or invalid strategy is rejected. Keep-or-revert rule unchanged:
kept only if the TEST (holdout) score improves.

GEPA reflective revision (A-28, landed 2026-11-03): `gepa.py` — for a
skill with an eval set, a failed fixture produces a score plus exactly one
paragraph of textual feedback naming the failure; the revision edits only
the skill's SKILL.md text; few-shot examples are harvested only from
outputs that passed the playbook's own metric, with metric name and
threshold recorded beside the example. `gepa.py selftest` enforces all three.

A-26 additions (2026-11-03, `eval_extensions.py` beside this file):
record-only assertions carry weight 0 with a per-set threshold and run
one full cycle reported-but-not-gating before they may gate; one
trajectory fixture type states the expected tool sequence in order,
forbidden tools by absence, and args checked partially with volatile
fields ignored; every reported metric row states measured or replayed
per row (a row without provenance is refused); named redteam case
generators for memory poisoning, cross-session leakage, and excessive
agency join the standing adversarial set. Runner: `eval_extensions.py
selftest`. The phase-1 runner above is unchanged.
