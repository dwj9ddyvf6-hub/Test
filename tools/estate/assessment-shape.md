# Host-validated assessment shape (Round-4, discipline 1 note)

Any LLM triage that can start work (desk-entry checks, mail triage, feed
lanes, quant reads, any accept/ignore judgement) must satisfy this shape
before its verdict is acted on. The host (caller code or the supervising
agent) validates the shape; the judge cannot skip a rule silently.

## Required shape (all fields mandatory)

- `candidate_id`: deterministic ID from tools/dedup_ids.py over the trigger parts.
- `rules_judged`: one entry per enabled rule, each rule judged exactly once.
  Each entry: `rule_id`, `verdict` (match | no_match), `evidence` (non-empty
  quote, ID, or observed value). A missing rule, a duplicate judgement, or
  empty evidence invalidates the whole assessment.
- `strength`: explicit | inferred | not_admitted.
- `decision`: accept | ignore | would_accept.
- `intent_evidence`: non-empty when decision is accept. Accept with no
  matched rule or empty intent_evidence is refused.
- `mode_check`: if strength is inferred and the lane mode is not `auto`,
  decision is downgraded to `would_accept` and logged to
  ~/workspace/proactivity/WOULD-ACCEPT.md. It never fires.

## Host checklist (validate in order, fail closed)

1. Every enabled rule appears exactly once in `rules_judged`.
2. Every judgement carries non-empty evidence.
3. Accept implies at least one matched rule and non-empty `intent_evidence`.
4. Inferred accept outside `auto` mode is downgraded, never executed.
5. Any shape failure: no work starts; the failure is logged with the candidate ID.

Provenance: adapted from the host-validated assessment in
deepseek-ai/dsh-superagent-prototype at commit 6337fc8 (policy gate).
