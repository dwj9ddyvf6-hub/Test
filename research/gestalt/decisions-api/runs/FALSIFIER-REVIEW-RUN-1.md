# Falsifier Review Run 1 (S7 seat, first run)

Run Sat 2026-11-14 evening (Sunday Program prep) by
tools/falsifier_review.py through the governed harness
(decisions_harness, gpt-6-luna, bank falsifier-review-v1). The seat
is a disagreement flag only under the 2026-11-12 second-seat
override; it gates nothing. Records:
runs/falsifier_review_ledger.jsonl (21 rows).

## Result over the candidate registry (21 registrations)

- Falsifier quality: measurable 17, vague 4, absent 0.
- The four vague flags (a kill condition exists but lacks a metric,
  a threshold, or a horizon): invention-execution-alpha,
  invention-negative-space-mining, invention-predator-sleeves,
  invention-trade-the-forced. Each is a named amendment candidate:
  the registration's falsifier gets a metric and a horizon added at
  its next revision, or the vagueness is accepted in writing.
- Strongest failure modes named by the seat: sample_too_small 7,
  regime_dependent 5, expectancy_too_thin 3, data_unavailable 2,
  identity_erosion 2, none_apparent 2, costs_swamp_edge 0.
- Testability: now 12, after_build 9, not_testable 0.
- Deterministic string check (does the file contain a falsifier
  section at all): true for all 21, so the string check and the seat
  agree on presence; the seat's added value is the measurable versus
  vague distinction the string check cannot make.

## Method note (route failure, preserved)

The first invocation failed with HTTP 400, missing parameter
questions[0].type: the tool's question dicts used a guessed shape.
The proven posing shape from run_bank_v2.api_questions (type, name,
instructions, choices as value plus description) fixed it on the
second route; no other change was needed.

## Spend

Harness budget file before: 2026-11-14 count 32, cost $0.008652.
After: count 53, cost $0.01133. This run: 21 requests, $0.002678.

STATUS: seat built and proven on the full registry. EVIDENCE
POINTER: tools/falsifier_review.py, runs/falsifier_review_ledger.jsonl.
