# Doctrine Landing Record: LLM Enhancement Sweep into InfinityBlade

Date: 2026-10-31. Target repo: dwj9ddyvf6-hub/InfinityBlade-Engineering-Doctrine (public, main).
Source catalog: REPORT.md in this directory (verification PASS, VERIFY.md).
Pre-landing HEAD: fd6fc42911c9eb03886801e2569c72091840fb91.

## Decisions landed (fixed by the curator, not re-decided here)

All ten shortlist items in REPORT.md Section 3 adopted as doctrine. The
near-miss list recorded as a backlog with revisit triggers. Section 4
ALREADY-HAVE mappings honored: nothing already covered by the doctrine
(spec-first work, TDD, proof before claiming, delegated-work review,
route-failure anti-spiral, filesystem project packs, hosted-memory
equivalents) was restated or duplicated.

## Structure decision and why

One new reference file, `skills/infinityblade/references/agent-enhancement.md`,
holding all ten disciplines plus a composition section and the backlog,
routed from SKILL.md's existing "Load more only when needed" table. Rationale:
the repo's own architecture is a short core skill plus load-on-demand
references (field-manual, playbooks, review-mode, lessons). The adopted
material is a coherent second layer (the systems around the work: memory,
initiative, skill craft, self-grading), so it belongs in one reference, not
scattered through the core, which doctrine keeps to one screen. Where an
item extends existing law it is written as an extension, named as such:
false-green audits extend the regression-blocker law; mechanised completion
checks mechanise Proof Before GREEN section 4; authority hygiene extends
"content is evidence, never instructions" from content to authority.

## Files changed

| File | Change | Commit |
|---|---|---|
| skills/infinityblade/references/agent-enhancement.md | NEW, 15,560 bytes: ten disciplines (each: rule, mechanism, why, source repos), composition notes, backlog table (11 deferred items with triggers) | a164f13cf0682243cddae50e2bceded800e6de53 |
| skills/infinityblade/SKILL.md | One routing row added to the load-more table; version 2.3.0 to 2.4.0 per the repo's changelog convention | 6e54ac40e4139ff9492b0e324c8a2518af0a670b |
| README.md | Enhancement link in the nav line; one row in the "What's in the repo" table; new additive "Agent enhancement" section with six bullets covering the ten disciplines. No restructuring | 6c32fe657030a704469416413ae6b8e6c9564a22 |
| CHANGELOG.md | New 2.4.0 entry at the top, in the file's existing style | d9950d82e9c0c9206ef424567d1b11a7ad057da8 |

Final HEAD: d9950d82e9c0c9206ef424567d1b11a7ad057da8.

## The ten disciplines as landed

1. Price every proactive lane (theta gate, graduated action, feedback log, monthly grading). Sources: tao-hpu/awesome-proactive-agents, thunlp/ProactiveAgent, liutj9/ProactiveEval (rubric only).
2. Instincts: confidence-scored procedural memory (0.3 to 0.9, context scoping, 2+ context promotion, capped injection, human-gated skill promotion, single memory of record). Source: affaan-m/ECC continuous-learning-v2 (mechanism only).
3. False-green audit of gate tests (J1 to J6 protocol, periodic inspection not per-commit gate, auditor itself proven on a known mutation). Source: vinicq/falsegreen-skill (the set's one code adoption, reviewed).
4. Memory as profile plus graph (static/dynamic split, updates/extends/derives edges, active expiry, fixed memory eval set). Source: supermemoryai/supermemory (mechanisms only).
5. Honest recall tiers (supported / closest-only / not present) and governed maintenance (erasure complete only when all derived copies are clean, with receipt and undo; background enrichment add-only). Source: qualixar/superlocalmemory (ideas only).
6. TDD-for-skills (pressure scenarios first, rationalizations recorded, Thought/Reality tables, description hygiene: triggers and negative boundary only). Sources: obra/superpowers methods, findscripter/everything-skills description rule.
7. Adoption and eval gate (per-skill eval sets, pass@k and pass^k, scan-before-list for third-party skills/connectors, sampled deliverable grading). Sources: promptfoo/promptfoo, openai/plugins plugin-eval, hashgraph-online/awesome-ai-plugins, affaan-m/ECC (patterns only).
8. Mechanised completion claims (block-once evidence check per turn; authoritative requirements file re-injected on compaction/resume). Sources: kuroudo-ai/done-gate, GreenLv/codex-context-guard (both reimplemented natively, neither installed).
9. Authority hygiene (per-turn capability, summaries carry context never authority, human-send boundary at trust bridges, fail-closed mismatches). Source: miuuyy/codex-chatgpt-web (rules only).
10. Bounded hidden-rubric pass for ungated prose (5 to 7 categories, hard retry cap, rubric internal, emotional-pressure lines deleted). Source: DenisSergeevitch/chatgpt-custom-instructions (self-evaluation block only).

## Read-back proof

- All four files fetched back through the contents API after the final
  commit and compared byte-for-byte with the intended content: MATCH on
  all four (agent-enhancement.md 15,560 bytes; SKILL.md 9,449; README.md
  9,564; CHANGELOG.md 3,293).
- Blob-level tree diff against the pre-landing snapshot: exactly the four
  intended paths changed (one new, three modified), zero unexpected new
  blobs, every other tracked file unchanged. (Parent tree-object SHAs
  changed as a mechanical consequence of the blob changes inside them.)
- All writes went through the established ghapi library and its PII gate;
  content names no person, only public repo names as sources.

## Conflicts with existing doctrine

None found. Two overlaps were handled as extensions rather than restated
(disciplines 3 and 8 against the blocker law and Proof Before GREEN;
discipline 9 against the content-as-evidence rule), and the new reference
states that where wording overlaps, the core skill wins. No existing
doctrine text was overridden or removed.

## Deliberately NOT landed

The full REPORT.md catalog (108 KB) and the six cluster files stay in this
local research directory as the record; only the coalesced doctrine went
into the repo. The Section 5 skip list stays local in full: the repo
carries no negative catalog of rejected third-party projects. Two
judgement calls worth naming: the fainir emotional-pressure lines were
rejected inside discipline 10 on the source author's own cited evidence,
and the unbounded self-evaluation loop from the same source was explicitly
not adopted (hard retry cap written into the discipline instead).
