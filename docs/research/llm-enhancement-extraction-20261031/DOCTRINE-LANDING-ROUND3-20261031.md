# Doctrine Landing, Round 3 (Final), 2026-10-31

Source: REPORT-PASS3.md (verified, VERIFY-PASS3.md verdict PASS, 16 claims sampled against primary sources). Target: dwj9ddyvf6-hub/InfinityBlade-Engineering-Doctrine (public, main). All writes via ghapi and its PII gate; content names no person, sources by repo name only.

Pre-landing HEAD: `d86c5d5c385a` (round-2 state). Post-landing HEAD: `11aae28d5072`.

## Commits

| File | Commit | Bytes before -> after |
|---|---|---|
| `skills/infinityblade/references/agent-enhancement.md` | `df403fe4bf9a` | 40,131 -> 62,544 |
| `skills/infinityblade/SKILL.md` | `023c606fe9e9` | 10,156 -> 10,156 (version line only) |
| `README.md` | `cfd44f8d3807` | 10,860 -> 11,224 |
| `CHANGELOG.md` | `11aae28d5072` | 7,735 -> 12,544 |

## What landed in the reference (47 asserted edits, all anchors matched exactly once)

- **Intro and composition**: third pass described; per-discipline standings announced; composition section carries the ledger outcome (2 confirmed, 8 qualified, 1 warned, 1 untested).
- **Confidence standings (Section 1)**: a "Standing after the third pass" note at the end of all 12 disciplines with the report's verdict and its load-bearing evidence: D1 QUALIFIED (with the blocking-gate warning), D2 QUALIFIED, D3 QUALIFIED (with warned component), D4 WARNED (full production evidence), D5 CONFIRMED (by counterexample), D6 QUALIFIED (strengthened confirmations), D7 QUALIFIED (four-direction confirmation), D8 QUALIFIED, D9 QUALIFIED, D10 NO CONTACT (recorded as untested, not upgraded), D11 CONFIRMED, D12 QUALIFIED (margins only).
- **Round-3 adoption set (Section 2, all 10 items)**: item 1 scope-creep diff-vs-intent audit (discipline 8); item 2 user-thrown gate enforcement + specify-the-HOW, fail-open explicitly not carried over (discipline 8, source pcvelz/superpowers); item 3 operation-level memory scoring + scheduled junk-rate audit with the 97.8% production base rate (discipline 4); item 4 planted-defect probes as the skill release gate (discipline 6) + vendor eval additions: reference solution, balanced cases, isolated trials, "Unknown" exit, 0%-pass-is-broken-task (discipline 7); item 5 transactional compaction with bounds blockers and clear/compact/remember triage, plus named bounded history-edit operations (discipline 9, point 5); item 6 skill-description testing at vendor numbers, 20 queries, 60/40 split (discipline 6); item 7 content-addressed fragments (discipline 11, source simonw/llm); item 8 confidence-gated adaptive recall with the 0.8/0.5 thresholds and the simple composite weighting (discipline 5, source CrewAI); item 9 episodic exemplars (discipline 11, LangMem guide), per-directory L0/L1 self-description and delta-style benchmark reporting (discipline 7, source volcengine/OpenViking), observed-by/knows-about scoping (discipline 7, source plastic-labs/honcho); item 10 tracker-and-gate hygiene pair: merged-state closure checks (discipline 7) and scoped disable named in every gate's deny message (discipline 8).
- **Section 4 ADOPT-IDEA slivers, one line or short paragraph each inside the named discipline**: firing example + look-alike rule and oracle staleness (D3); date-ordered presentation and per-item index opt-out/field selection (D4); omission-disclosed injection, unchecked-is-not-rejected, migration fixtures (D5; unchecked also restated for D7); Executor/Analyst/Mutator single-mutation loop and ceremony cost budget (D6); measured-vs-replayed metric provenance, structural parsing over regex with seam-case regression sets, tool descriptions as eval-tested artifacts, release gates living in owned files (D7); plan list in JSON with status-only edits and verdict-point self-consistency vote, numeric effort scaling in delegation prompts (D8); refresh-on-read as a named contract (D12); experience-memory eval shape (D11); superseded entries never injected (D11).

## Corrections applied (Section 3, all 7)

1. **Honcho**: no landed text carried the "hosted-only thin harness" error (checked: the name does not occur in the reference), so there was nothing to strike in place. The correction is disclosed in the CHANGELOG 2.7.0 entry, and its one transferable element (perspective scoping) is adopted in discipline 7.
2. **LoCoMo**: the reference cited no LoCoMo percentage (checked: no occurrence), so nothing to strike in place. The retirement of LoCoMo ranks as supporting evidence, the 6.4% wrong-golden figure, and the "#1 on three benchmarks" reduction are recorded in discipline 4's WARNED standing note and in the CHANGELOG.
3. **Description rule**: discipline 6's triggers-only bullet rewritten assertive ("pushy" against undertriggering, all trigger context in the description), with the one-step-task structural limit added; item 6's numbers landed alongside.
4. **Ledger capture**: discipline 8 now states runner-aware capture explicitly (named pass/fail token, never "the last log line"; the duration-as-outcome defect named), with the plan-list-in-JSON hardening folded into the same bullet.
5. **Letta limits**: discipline 5's sizing bullet now states the figures describe the letta-code generation only and must not be cited as enforced V1 behaviour (0.16.7 removed enforcement).
6. **S-code catalog**: discipline 3 gained the qualification bullet (19 of 24 semantic codes with no firing example and no look-alike; S14/S21 inherit the qualification) plus the general firing-example-plus-look-alike gate rule that is its cure.
7. **Mode C executor**: discipline 3 carries a prominent blockquote warning immediately after the Mode B bullet (full ambient environment, credentials included, self-disclosed, unfixed; permitted forms: environment allowlist + jailed working directory, or a locally controlled executor), the F7 contract explicitly standing, and the discipline's Sources line now states the shipped executor is not adopted.

## SKILL, README, CHANGELOG

- SKILL.md: version 2.6.0 -> 2.7.0 only. The whole-doctrine-first gate section and the agent-enhancement routing row were asserted byte-preserved by a round-trip check (reverting the version string reproduces the pre-edit file exactly) before commit, and the committed file read back byte-identical.
- README: the "Agent enhancement" section gained one bullet ("Third-pass hardening") summarising the re-grade outcome. It fits the section's bold-lead bullet style, so the README was touched; the mandatory full-read note at the top is byte-exact (round-trip assert: removing the inserted bullet reproduces the pre-edit file exactly).
- CHANGELOG: 2.7.0 entry in the file's style: the concretions in brief, the confidence ledger outcome (2 confirmed, 8 qualified, 1 warned, 1 warned component in discipline 3 plus a warned design constraint in discipline 1, 1 no contact), the seven corrections named one line each, and the 97.8% junk production finding behind the warned discipline.

## Proof (read-back from the final state)

- All four modified files fetched back via the contents API after the final commit and byte-compared against the intended content: **byte-identical**, all four.
- Tree diff before/after: path sets identical (25 paths); changed blobs are exactly the four intended paths, each commit touching exactly one file.
- Final-state probes on the reference: Mode C warning present, junk-rate figures present, WARNED and NO CONTACT standings present, specify-the-HOW and diff-vs-intent and runner-aware all present, standing notes count = 12, discipline headings 1-12 in order, no renumbering.
- SKILL.md on the final state carries version 2.7.0.

Verdict: GREEN, proven on the final repo state.
