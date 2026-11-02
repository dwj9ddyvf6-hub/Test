# Doctrine Landing Record, Round 2: LLM Enhancement Pass 2 into InfinityBlade

Date: 2026-10-31. Target repo: dwj9ddyvf6-hub/InfinityBlade-Engineering-Doctrine (public, main).
Source catalog: REPORT-PASS2.md in this directory (verification PASS, VERIFY-PASS2.md).
Pre-landing HEAD: 901ac965c93c674c982911e5f7125319ac154ee8 (the mandatory full-read note commits).
Final HEAD: d86c5d5c385a5ce1942e5ce2ccdff83bc72d5662.

## Decision landed (fixed by the curator, not re-decided here)

The full pass-2 Section 3 adoption set (12 items), applied as revisions to the
same reference round 1 created, `skills/infinityblade/references/agent-enhancement.md`:
the corrections replace the round-1 wording they correct, the completions extend
their disciplines, and two genuinely new items land as disciplines 11
(rationale memory) and 12 (freshness). Discipline numbering 1 to 10 is stable.

## Files changed

| File | Change | Commit |
|---|---|---|
| skills/infinityblade/references/agent-enhancement.md | Revised in place, 15,558 to 40,131 bytes: corrections and completions in disciplines 1, 2, 3, 4, 5, 6, 7, 8, 10; discipline 9 untouched (byte-identical); new disciplines 11 and 12; composition section updated; backlog corrected (Mem0 row) and one row removed (fainir, adopted) | 222c5315a47e29ef59e20dc2f2ad3d1100853eae |
| skills/infinityblade/SKILL.md | Version 2.5.0 to 2.6.0 only. The whole-doctrine-first gate section and the round-1 routing row are byte-preserved (the edit was a single-string version replace, round-trip asserted) | 4f9ae352041fab087882db40607965bcc87ccdba |
| README.md | Additive only: "ten adopted disciplines" to twelve, and two new bullets in the Agent enhancement section (Rationale memory, Freshness). The mandatory full-read note at the top is untouched | de045eec40173d831dbe2f63951d6cf21018816a |
| CHANGELOG.md | New 2.6.0 entry: additions summarised, then eight correction bullets naming the revised round-1 claims one by one | d86c5d5c385a5ce1942e5ce2ccdff83bc72d5662 |

## What changed per discipline

- **1 (proactivity)** rewritten around the composed design: offline scorer
  (MUST/MAY/MUST-NOT windows, benefit 4/2, cost 4/1, single-credit benefit,
  per-fire cost, lambda sweep {0.25, 0.5, 1, 2, 4}, silence-as-policy), a
  designed fire-time gate (separate judge, bounded different retries,
  default-on, calibrated acceptance threshold in the PRISM shape), expectation
  setting (labelling pipeline; general-model F1 0.67 until it exists), the
  two-stage delivery rubric (local example bank; 10 minus 2 to 4 across five
  criteria), graduated action and feedback logging retained from round 1.
- **2 (instincts)** build spec corrected and completed: capture layer
  (dual redaction, anti-self-observation, rotation/purge), project identity
  (credential-stripped normalised remote hash, worktree collapsing), the
  extraction prompt's untrusted-data clause and exact-final-line completion
  contract, the confidence table (0.5 / 0.7 / 0.85 cap; 0.9 only from direct
  analysis; time adjustments recorded as model judgement, not mechanism),
  promotion on 2+ contexts plus 0.8 average (the code's rule), injection
  stated as an open local design decision, overlap clustering, 30-day
  pending TTL, import hardening, off-by-default noted.
- **3 (false-green)** completed: F7 bidirectional mutation contract as the
  acceptance gate for fixes, Mode B oracle-first authoring, Name the Break,
  precision machinery (severity ceiling, intent can only lower, case-18
  standard), S14 and S21 named risks, per-fix revert-proof. The J1 to J6
  table and round-1 bullets are byte-preserved.
- **4 (memory profile/graph)** completed at numeric level: 8+8 always-on
  cap, buckets as third axis, bi-temporal supersession (true-from /
  true-until / learned-on), the Mem0 V3 extraction spec named by constant
  (integrity properties, integer-remapped IDs, store-confirmed success,
  loud-failure distinction) and its fusion formula, the inferred-memory
  review queue (flag, support-count ranking, approve / decline-forget /
  undo), and forgetting restated as four contracts.
- **5 (honest recall)** completed: tier constants (3 previews at 240 chars,
  related bar, nonsense bar, degraded-never-abstains), the reviewed
  two-phase correction lifecycle with fail-closed recall, layered
  addition-only, erasure receipt plus projection tombstone, the busy
  contract, Cognee's session-to-permanent promotion gate, calibration
  measurement of the tier boundary, and Letta-Code's memory-editing wording
  with reference sizing.
- **6 (skills)** upgraded with pass 2's deepest find: the Match the Form to
  the Failure table as authoring law, the two supporting prohibitions (no
  nuance clauses; exemption clauses do not scope), the wording micro-test
  protocol (fresh-context samples, no-guidance control, 5+ reps, manual
  read, variance as metric), APE-style generation-and-selection plus the
  two other surviving prompting practices, the session-diagnosis bullet
  corrected to the forensic protocol (citation-or-discard), and a
  corpus-drift caution (adopt methods, not current texts wholesale).
- **7 (library gate)** concretised: pass@3 0.90 / pass^k 1.00 thresholds and
  define-evals-first; the eval evidence layer (effect classes SE0 to SE4,
  hash-chained append-only capsules, fail-closed replay, offline receipts,
  refusal posture); the AgentShield checklist at corrected scale (268 rules,
  15 modules; secrets 10 over 25 patterns, permissions 17, hooks 40, MCP 49,
  prompt-defense 1 rule with 12 checks) with its scoring-honesty mechanisms
  and deep-mode shape; scan-before-list grounded in hol-guard's published
  HCS-28 rubric with both aggregation rules and the anti-self-grading guard;
  the commit-boundary guard as the third enforcement boundary; the fainir
  self-audit instruments at corrected scope.
- **8 (completion)** strengthened: freshness unit copied literally
  ("in this message", satisfaction words are claims, agent reports are not
  evidence), the scope-versus-verification split, fix-loop arithmetic
  (5-round cap, resume-then-fresh split, scoped re-review, ledger line per
  round), rulings-not-stalls with the four stop conditions, the 3-fix
  debugging stop, gate protection (forbid list, declared bounds file,
  shipped negative control, configured-is-not-active), and loop-guard
  defaults.
- **9 (authority)** untouched; pass 2 changed nothing here.
- **10 (hidden rubric)** narrowed: constructed rubric plus one global
  threshold plus secrecy rule plus hard cap; the implied named categories
  and per-dimension scoring removed; subtractive prompt maintenance added.
- **11 (new, rationale memory)**: the keep-the-why schema as required fields
  (UUID identity, rejected alternatives with why they lost, evidence grade,
  revisit trigger, supersession naming its successor), pending-confirmation
  capture, structural lint in the existing gate, truth explicitly left to
  human judgement.
- **12 (new, freshness)**: the OKM rule (timeless, dated, or pointer), the
  one illegal form named, the heuristic nightly check (FRESH-1/2/3 shape),
  and the three-answer refresh loop. Bilinc recorded as independent
  corroboration.

## Corrections applied (round-1 claim, then pass-2 correction)

1. **Proactivity gate.** Round 1: the pilot implements "intervene iff
   E[benefit] minus E[cost] exceeds theta". Pass 2: the pilot contains no
   theta and never evaluates that inequality; it is an evaluation scorer,
   `score(lambda) = total benefit - lambda * total cost` over
   lambda in {0.25, 0.5, 1, 2, 4}. The gate is designed, not adopted.
2. **Proactivity quality.** Round 1 implied the reward gate's F1 0.918 is
   available from the artifact. Pass 2: 0.918 is a fine-tuning result
   measured on a 120-row test set; a prompt-only rebuild should expect the
   general-model numbers (F1 0.6704). "False-Alarm" is defined as
   FP/(TP+FP), i.e. 1 minus precision; the corpus is 6,790 events, the
   shipped agent test set 227. The feedback policy and the gate are,
   respectively, one prompt sentence and an opt-in env var in the source.
3. **ProactiveEval.** Round 1 treated the rubric as portable text. Pass 2:
   Stage 1's operative rubric is a ~42 KB per-domain few-shot example bank;
   only Stage 2 transfers as text.
4. **Instincts injection.** Round 1: "injected in a small ranked budget
   (about 6, threshold 0.7)". Pass 2: no injection mechanism, ranking, 0.7
   injection threshold, or cap of 6 exists anywhere in
   continuous-learning-v2; the only coded thresholds are evolve (0.7
   workflow, 0.75 agent-cluster) and promotion (0.8, 2+ projects).
5. **Instincts confidence.** Round 1: "0.3 to 0.9" as one scale with
   adjustment rules. Pass 2: the observation path caps at 0.85 by count
   (0.5 / 0.7 / 0.85); the 0.9 tier comes only from repo analysis; the
   +0.05 / -0.1 / -0.02-per-week adjustments are instructions to the
   observer model, with no adjusting code and no decay job. The observer
   ships disabled by default (and silently non-functional on native
   Windows); round 1 presented the system as running.
6. **Instincts promotion.** Round 1: appearance in 2+ contexts. Pass 2: the
   shipped CLI also requires average confidence at least 0.8; the docs'
   third condition (global-friendly domain list) is not enforced by code.
7. **Supermemory.** Round 1: static/dynamic split plus one expiry
   mechanism. Pass 2: a third axis (buckets), a concrete always-on cap
   (8 static + 8 dynamic at the MCP surface), forgetting as four contracts
   plus an inferred-memory review queue, and no published extraction,
   edge-classification, or expiry prompt or numeric TTL anywhere: expiry
   is adoptable only as contracts, and the benchmark-producing layer is
   closed.
8. **Mem0.** Round 1: temporal ranking is part of the mechanism, and "Mem0
   is ADD-only" without qualification. Pass 2: temporal ranking is
   platform-only in the open-source build (the parameters raise errors;
   `notices.py` is an upsell detector); OSS behaviour is a caller-supplied
   expiration-date filter. ADD-only is true only of the default path; the
   same prompts file ships the legacy ADD/UPDATE/DELETE/NONE prompt, so
   the adopted constant is named (V3). Temporal ranking struck from the
   discipline's backlog row as well.
9. **Superlocalmemory corrections.** Round 1: simple replace-and-undo via
   `--replaces`. Pass 2: a reviewed two-phase lifecycle (immutable
   successor, proposed review case, expected-version apply, double
   admission, fail-closed abstention when the record is unreadable); and
   "addition-only" is layered (enrichment add-only; zone movement
   autonomous but bounded and protection-gated; corrections never
   machine-applied; erasure a dedicated workflow).
10. **Letta.** Round 1 described the retired V1 database-block server.
    Pass 2: the current letta-code system is git-backed Markdown (MemFS)
    with indexes and reflection agents, much closer to this stack; the
    borrowable set (editing doctrine, limit set) is larger than pass 1's
    "block permissions".
11. **False-green protocol.** Round 1: the full protocol "lives partly in
    external docs". Pass 2: refuted; the complete protocol, 125-code
    catalog, schemas, and worked examples are all in the repo. Modes B
    (authoring) and C (fix, gated by F7) were entirely missed by round 1.
12. **Eval-harness.** Round 1 implied ECC grades changes by executing
    candidates in a harness. Pass 2: candidate execution is disabled on
    every OS and refuses with `gate.isolation_required`; no trust flag
    bypasses it. What exists is recording, static inspection, fixture
    replay, and offline verification, with an explicit disclaimer against
    presenting receipts as containment.
13. **AgentShield scale and scoring.** Round 1: "102 rules", five
    categories. Pass 2: 268 rules in 15 modules in the product repo; the
    five are score buckets. Scoring is per-category (start 100, floor 0,
    plain average), runtime-confidence weighted 0.25x to 1.0x with secrets
    always at full weight, template deductions capped, defences listed
    but never scored.
14. **Rationalization tables.** Round 1 adopted them unqualified as the
    skills discipline's core. Pass 2: they are one of four matched forms,
    correct only for discipline failures; on shape and omission failures
    the prohibition form produced more unwanted content than a
    no-guidance control in the corpus's own wording tests, a single
    nuance clause degraded a winning recipe from consistent to noisy, and
    exemption clauses do not scope. Form-matching and micro-testing now
    lead discipline 6.
15. **Session diagnosis.** Round 1: a retrospective over cost, plan
    adherence, quality evidence, repeated work. Pass 2: a forensic
    protocol (case-file intake, eight report dimensions,
    citation-or-discard, redaction with scrub audit, approval gates, an
    involvement verdict forbidden from proposing fixes).
16. **Hidden rubric.** Round 1 implied named categories and per-dimension
    scoring in the source instruction. Pass 2: the pasted v3 artifact
    names no categories and no per-dimension procedure; its only numeric
    anchor is one global threshold (at least 98 of 100) plus the secrecy
    rule. Neither tested version prints a baseline; the Operator block
    exists only in v2 and was not carried into v3 (a catalog-level
    correction; round 1's reference never carried the Operator block, so
    no reference text changed for it).
17. **Fainir metrics.** Round 1's backlog phrasing ("tracked metrics")
    overstated four named ratios that have no definition anywhere in the
    source. They are now adopted only with locally written counting
    definitions; the 13-class taxonomy's four missing repair mappings are
    named and completed locally; the loop-guard defaults pass 1 never
    extracted (30-second pull polling, ~30-minute hard timeout, depth
    ~5, retry once then change strategy) are landed in discipline 8.
18. **Scan-before-list grounding.** Round 1's policy rested on the
    awesome list's guide. Pass 2 read the scanner itself (hol-guard):
    the HCS-28 weighting and its two aggregation rules (missing universal
    scores 0; conditional adapters enter the denominator only when they
    emit) are now the grounding, plus the anti-self-grading trust flag.
    Evaluating the hol-guard tool itself was explicitly deferred by
    pass 2 and is not decided here.
19. **Execution pipeline verdict.** Pass 1 graded the Superpowers
    execution pipeline ALREADY-HAVE. Pass 2: the generic shape is
    covered, but the specific mechanics (5-round fix cap with
    resume/fresh split, adjudication only at the cap, four stop
    conditions, per-plan ledger formats, evidence freshness "in this
    message", the scope-versus-verification split, the 3-fix debugging
    stop) have no equivalent precision and are landed in discipline 8,
    together with the gate-protection transfers (forbid list, declared
    bounds, negative control, configured-is-not-active).

## Read-back proof

- All four modified files fetched back through the contents API after the
  final commit and compared byte-for-byte with the intended content:
  MATCH on all four (agent-enhancement.md 40,131 bytes; SKILL.md 10,156;
  README.md 10,860; CHANGELOG.md 7,735).
- Blob-level tree diff between pre-landing HEAD 901ac965 and final HEAD
  d86c5d5c: path sets identical (25 entries, no additions or deletions);
  changed blobs are exactly the four intended paths; the only other
  changed entries are their parent tree objects, a mechanical
  consequence. Each of the four commits touches exactly its one file.
- Discipline 9 and the J1 to J6 table verified byte-identical to round 1
  before committing; SKILL.md's change is the version string only
  (round-trip assertion in the landing script).
- All writes went through the established ghapi library and its PII gate;
  content names no person, only public repo names as sources.

## Deliberately NOT landed

The verbatim artifacts themselves (extraction prompts, pilot scoring code,
instinct file bytes, the 125-code catalog, the HCS-28 tables in full) stay
in the local PASS2 dive files, which are the build-level record; the
reference carries the buildable specifications and invariants, per the
repo's coalesced-doctrine convention from round 1. Expansion finds outside
the adoption set (the obsidian vault product, the Khoj and MoonMind
systems, the prompts.chat corpus, the Graphiti and Cognee engines as
products) stay local with their verdicts; their transferable slivers
(freshness rule, bi-temporal window, promotion gate, calibration,
configured-is-not-active) are the parts that landed. The pass-2 dive's
brainstorming correction (#5 in REPORT-PASS2 Section 1) changed no
reference text, because round 1's reference never carried a brainstorming
claim; the correction stands in the catalog record.
