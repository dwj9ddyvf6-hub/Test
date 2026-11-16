# Instincts checklist (discipline 2, round-5 concretion)

The pre-action checklist for the local instincts layer: learned units
extracted from trajectories that may influence later inference. Sources:
round-5 SYNTHESIS items 10 to 12 (ECC runtime, optillm SPL, LangMem),
CLUSTER-skills.md and CLUSTER-prompting.md, 2026-11-02.

## Admission (a learned unit may influence inference only if all hold)
- [ ] Confidence at or above 0.7 (ECC `DEFAULT_INSTINCT_CONFIDENCE_THRESHOLD`).
- [ ] Success rate at or above the store's MIN_SUCCESS_RATE (optillm SPL gate).
- [ ] Not a near-duplicate of an existing unit; near-duplicates merge on the
      maintenance interval instead of accumulating.
- [ ] Per-type / per-domain cap not exceeded (hard cap, SPL `MAX_STRATEGIES_PER_TYPE` shape).
- [ ] Extraction coalescing respected: a new extraction for a scope with a
      pending extraction cancels and replaces the pending one; a scope is
      extracted once, over its settled state (LangMem).

## Injection (at session start or task start)
- [ ] At most 6 instincts injected (ECC cap).
- [ ] Each injected unit's summary is at most 220 chars.
- [ ] Total injected context at most 8,000 chars, with an explicit truncation
      marker when cut; never silent truncation.
- [ ] Ranking score = confidence + 0.25 if project-scoped + 0.20 if
      stack-matching. Boosts are ranking only, constants in code, never
      configurable knobs, and never lower the admission floor.

## Conduct
- [ ] An instinct is a prior, not proof: InfinityBlade evidence rules still
      govern any claim it informs.
- [ ] A contradicted instinct is frozen from strengthening (discipline 5/12
      anti-popularity rule); retrieval alone never strengthens a unit.
- [ ] Promotion of an instinct into a skill or doctrine text is a separate,
      recorded step, never automatic.

Status: executed mechanically by ~/workspace/tools/instincts_inject.py
(T-68, adoption 2026-11-03), which tools_gate.py runs over the live store on
every gate run and records in its receipt. The platform's own session-start
injection is runtime-managed and untouched; this checklist's live path is
the local memory lane (tools_gate / memory store).
