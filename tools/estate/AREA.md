# tools/estate/: the estate tooling kit

Standalone Python tools built and used daily by the desk's operator agent:
verification and evidence checking (claim_ledger.py, check_evidence.py,
delivery_checklist.py, done_check.py), status and honesty gates
(status_evidence_check.py, freshness_lint.py, fragment_lint.py), memory
machinery (memory_search.py, memory_reconcile.py, memory_edges.py,
memory_op_score.py), evaluation (eval_score.py, judge_calibration.py,
lane_scorer.py, priced_initiative_score.py), and spend accounting
(api_spend.py).

Published 2026-11-16 from the live workspace tools directory: code and
docs only. State and data files (ledgers, indexes, calibration sets) stay
local by design; the tools regenerate or re-read them at runtime.
