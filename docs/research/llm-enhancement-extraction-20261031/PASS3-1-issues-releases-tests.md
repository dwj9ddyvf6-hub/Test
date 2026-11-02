# LLM Enhancement Extraction: Pass 3, Dive 1 — Issues, Releases, Tests inside the known repos

Compiled: 2026-10-31. Scope: obra/superpowers, affaan-m/ECC, supermemoryai/supermemory, mem0ai/mem0, thunlp/ProactiveAgent, vinicq/falsegreen-skill, letta-ai/letta, promptfoo/promptfoo. Layers mined (the ones passes 1-2 skipped): (a) GitHub issues, top by comment count via the search API (`type:issue`, sort=comments) for open and closed, plus full comment threads on 14 highest-signal issues; (b) the 10 most recent GitHub releases per repo; (c) tests/examples directories (tree-level for falsegreen-skill and ProactiveAgent; issue/release evidence for the rest). Passes 1-2 read READMEs, trees, and load-bearing artifacts; they did not read issue threads, release notes, or test corpora. Nothing here re-reads those layers.

Method and budget: unauthenticated GitHub API (60/hr core, 10/min search). Counts recorded before deep reads: issue totals from search (`total_count`), listed per repo below. No repo code was installed or executed. No personal information about any person is included; GitHub usernames are quoted only where they carry maintainer/collaborator authority on a thread.

Verdict vocabulary for adopted disciplines (numbered as in REPORT-PASS2 Section 3): CONFIRMED (the unexamined layer supports the discipline as landed), QUALIFIED (stands, with the stated qualification), WARNED (evidence of a failure mode the landing must design against). New finds use the standing vocabulary: ADOPT-CODE, ADOPT-IDEA, ALREADY-HAVE, REFERENCE, SKIP.

---

## 1. obra/superpowers — discipline #1 (form-matching / TDD-for-skills), #10 (execution arithmetic and ledger), #2 (Name the Break)

Issue corpus: 195 open / 877 closed issues (search totals).

### Findings

1. **The cost of the discipline is the top user complaint, in the repo's own top threads.** Open issue #743 "Im seeing slowness in responses since using the skill" (27 comments, 32 reactions, the most-reacted open issue in the repo): "since installation my claude code has started to slow down quite a bit. Maybe the context of the superpower skill is eating up too much space." Open #1152: a "relatively simple plan" executed with subagent-driven development "consumes full 5h token budget in a single run." Open #512 is titled "brainstorming/writing-plans SKILL efficiency." The maintainer's only reply on #743 asks for specifics; the thread stays open. The discipline's overhead is real, recurring, and unpriced in the skill texts passes 1-2 read.
2. **v7 brainstorming is a maintainer-confirmed form-matching failure, fixed in public.** Open #2530 "v7's brainstorm questions are rather annoying" (27 comments, 29 reactions) documents the rebuilt brainstorming skill asking questions the user's own materials already answered ("What made you decide to fix <tech-debt-item>?"). The maintainer's thread replies are a live demonstration of the corpus's own micro-testing method, including two reproduced failures of the fix attempts: in 6 of 6 runs the agent "decided on its own that this was 'a small change,' skipped the written design, and built"; in a follow-up, 24 of 24 runs settled the design in the first message and built with no design doc. Release v7.0.1 (2026-10-21) then shipped the retune: "Many of you told us, rightly, that the new default questions got annoying fast and felt formulaic. Brainstorming now [reads context first]… It offers to skip the questions only when it started on its own."
3. **Plans over-specifying was a closed, fixed defect, and the fix validates pass 2's "proportionality" reading.** Closed #895 "writing-plans: plans over-specify implementation, leaving no room for executor judgment" (24 comments, 38 reactions, the most-reacted closed issue): plans contained "full function bodies, 70-line test files… the executor had no decisions to make — it was copy-pasting code from the plan." Release v6.4.2 (2026-09-25) shipped the cure ("A plan records decisions. It's not a transcript of the code") with an eval claim: "Every plan written by the new skill executed 9/9 against planted-defect probes on Sonnet 5, the same result as full-code plans. (#2333)."
4. **The per-plan ledger, adopted in discipline #10, has an open correctness defect in its evidence field.** Open #2342: `executing-plans`' `task-done` script "ledgers the last log line as the test result, so `node --test` runs record `# duration_ms …` instead of pass/fail." The script takes the last non-blank line of the test log (`last=$(grep -v '^[[:space:]]*$' "$log" | tail -n 1)`) and writes it into the ledger's `tests: … → <result>` field. The ledger line therefore can record a duration as if it were a test outcome: the ledger format is sound, its automated evidence capture is not runner-aware. The reporter notes sibling open issues (#2267, #2293, #2253) about what the ledger omits.
5. **The verification gate's own users are extending it with instrument-failure classes.** Open #2186 proposes "a distilled set of instrument-failure classes the gate doesn't yet name (positive controls, reported≠verified…)" for verification-before-completion. Production use is generating gate taxonomy the skill text does not contain.
6. **Release cadence shows continuous retuning, not stability.** v6.2.0-v7.0.1 in roughly three months: SDD ledger became plan-scoped because "a follow-up plan in the same working tree could read the previous plan's ledger" (v6.2.0), executing-plans was a "64-line stub that measured the same as running with no plugin at all" before its v6.4.1 rebuild, and v7.0.0 rebuilt brainstorming from scratch before v7.0.1 retuned it. Pass 2's corpus-drift caution (its correction 7) is confirmed by the release layer.

### Verdicts

- Discipline #1 (Match the Form to the Failure + micro-testing): **CONFIRMED, strengthened.** The #2530 thread is the method working in public: user reports, fresh-context reproductions with run counts (6/6, 24/24), form change, release. It also confirms the backfire direction: the v7 opener was a fixed template applied regardless of context, and it produced worse-than-baseline behaviour until retuned.
- Discipline #10 (execution arithmetic and ledger): **QUALIFIED.** The ledger discipline stands, but the ledger's automated `tests:` field must not be copied as "last log line": evidence capture has to be runner-aware (a named pass/fail token), or the ledger records noise as proof. Add: budget the ceremony; #743/#1152 show the execution pipeline's cost is the first thing users rebel against, and an unpriced fix-loop will be disabled rather than obeyed.
- Discipline #2 (Name the Break): **CONFIRMED (indirect).** The v6.4.2 planted-defect probes (9/9) are the same mutation-first idea run as a release gate by the source repo itself.

### New finds

- **ADOPT-IDEA:** planted-defect probes as a release gate for skill changes (v6.4.2 pattern): before shipping a revised skill, run it against tasks with known planted defects and require detection parity with the prior version. This is the skill-level analogue of the F7 gate, run by the source repo in production.
- **REFERENCE:** #2186's instrument-failure classes (positive controls, reported≠verified) as candidate additions to the verification gate's named failure list.

---

## 2. affaan-m/ECC — discipline #6 (instincts), #8 (eval evidence), #9 (AgentShield audit), #10 (gate protection)

Issue corpus: only 77 open / 855 closed issues (search totals); the closed list is dominated by bot-generated "[Feedback]" and "[ECC 2.0]" tracking issues, and the issues endpoint's top-commented items are almost all PRs. The issue layer is thin relative to the repo's size, which is itself the finding: most real defect signal lives in PR threads, not issues.

### Findings

1. **Instinct injection, which pass 2 proved does not exist in the shipped system, is being built in an open PR, not by the core.** Open PR #3189 "feat(hooks): enforce high-confidence instincts at PreToolUse" (138 comments, the most-discussed open item in the repo) proposes enforcing instincts as a PreToolUse hook. The injection gap pass 2 found at artifact level is corroborated from the other side: the community is having to add it. Discipline #6's instruction to "design session-start injection locally" is the right posture; there is still no field-tested reference implementation to copy.
2. **The observer has live scope bugs.** Open PR #3528 "fix(observer): preserve explicit event scope after missing cwd" and closed PR #3511 "fix: integrate nine focused skill, instinct and documentation repairs" (136 comments) show the continuous-learning machinery under active repair in exactly the areas pass 2 specified (scope, instinct handling). The system is maintained, but it is not settled.
3. **GateGuard's destructive-command regex has a proven bypass on the current release.** Open issue #2642: "destructive commands ending in / . or a quote bypass DESTRUCTIVE_BASH (installed release; fixed on main)." The comment thread refutes even the "fixed on main" half: a collaborator reproduced on the published v2.1.0 tag that `dd if=/dev/zero of=/dev/sda` is still allowed "because the trailing word boundary after if= cannot match before /"; a second audit on current main (656d4b57) confirms the dd arm still carries the trailing `\b`; a user confirms it still reproduces on released 2.2.1. The thread's own diagnosis generalises: "regexes keep failing at seams" where a word boundary meets a non-word character, and the proposed durable cure is a structural operand check mirroring the git-subcommand parser.
4. **The fact-forcing gate fires on read-only work and its tuning knobs are undiscoverable.** Open #2573: the first Bash call of a fresh session, a plain `ls`/`find`, "was denied by the routine-Bash gate," and three of the four `GATEGUARD_*` env vars "appear in no markdown file in the repo"; the deny message offers only the nuclear options (`ECC_GATEGUARD=off`). A mechanical gate whose scoped off-switch is undocumented trains users to disable the whole gate.
5. **The repo's own issue-closing hygiene failed an audit.** Open #3223 "process: three issues closed with references that don't hold up (#2269, #2074, #3133)": a contributor verified that cited fix PRs (#2099, #2104) "are closed without merging, so neither should be cited as delivered," and that a cited release (v2.2.2) does not exist ("releases end at v2.2.1… no v2.2.2 tag or release, so the closed-as-shipped reference does not hold"). A collaborator confirmed the audit on the live records and kept the issue open rather than substituting a new claim. The contributor's proposed cure is mechanical: gate any "fix tracked in PR #N" close on `merged == true` via the API.
6. **Releases confirm churn in the enforcement layer.** v2.2.1 (2026-09-08) is "a bug and security patch" extending GateGuard to destructive PowerShell; v2.2.0 requires "the exact npm archive must pass lifecycle tests on Linux, macOS, and Windows before `latest` moves"; issue #3492 reports 2.2.3 impossible to install on a current Claude Code. (Note the date skew: #3223's audit predates the v2.2.2/v2.2.3 releases now visible, which is precisely the stale-reference failure it describes.)

### Verdicts

- Discipline #6 (instincts): **QUALIFIED.** The build spec stands, but the issue layer adds two facts: injection is still unbuilt upstream (open PR, not shipped), and the observer's scoping is buggy in the wild (#3528). Treat the observer/capture layer as a design to harden, not a reference implementation to trust.
- Discipline #9 (AgentShield-style audit): **CONFIRMED with a sharpening.** #2642 is a production instance of the exact class the audit exists to catch, inside the audit vendor's own sibling product: regex-based destructive-command rules fail at operand seams. Any locally mirrored checklist should prefer structural parsing over pattern lists for command classification, and every regex rule needs a seam-case regression (slash/dot/quote-prefixed operands).
- Discipline #8 (eval evidence): **WARNED (process-level).** #3223 shows the failure mode the capsule/evidence design targets, occurring in this repo's own tracker: completion claims citing unmerged PRs and a nonexistent release. Evidence discipline has to cover tracker claims, not only eval artifacts.
- Discipline #10 (gate protection): **QUALIFIED.** #2573 adds a usability law the bounded-loops transfer did not state: a gate's scoped escape knob must be named in the gate's own deny message, or users take the global off-switch and the gate dies entirely.

### New finds

- **ADOPT-IDEA:** merged-state gate for closure claims: no issue/defect may be closed citing a PR or release without a mechanical check that the PR merged / the release exists. Directly from #3223, with the one-line API check supplied in-thread.
- **ADOPT-IDEA:** deny messages must name the narrowest scoped disable for the specific gate that fired (from #2573).

---

## 3. supermemoryai/supermemory — discipline #7 (memory discipline: profiles, review queue, forget contracts)

Issue corpus: only 23 open / 393 closed issues. The open list is dominated by self-hosted server defects, which is where the testable claims are.

### Findings

1. **Users cannot find the server source, and say so in the top open issue.** Open #1299 "Where is the source for supermemory-server?" (5 comments, 5 reactions, the most-reacted open issue): a commenter states the community position verbatim: "supermemory isn't open source, its closed source with a distributable compiled binary. Trying to say its open source just creates distrust in the community." No maintainer clarification appears in the thread (only a Linear linkback bot). Pass 2's correction 17 (extraction is not extractable; closed engine) is confirmed from the user side, in stronger terms.
2. **The benchmark claims are not locally reproducible, per an open issue.** Open #1787 "Memory Benchmarks are not open-sourced and crash during locally run tests": a 6-question LongMemEval run on a 64 GB / RTX 3070Ti host "crashed after spending 3 hours over 6 questions," and the reporter asks for the benchmark runner and run conditions to be open-sourced. Pass 1 already labelled the headline numbers vendor claims; the issue layer shows they are also unverifiable in practice by users.
3. **The expiry contract is broken in the shipped self-hosted build.** Open #1806: "Self-hosted v0.0.9 clears elapsed forgetAfter during extraction, leaving expired backfill memories in the default profile." The one maintainer-side artefact in the thread is a Linear linkback (ENG-1316); the defect is open. Pass 2 adopted Supermemory's expiry as contracts only; the issue layer shows even the contract is not honoured by the current build.
4. **Silent non-indexing of non-ASCII memories, measured on a real store.** Open #1740: memories whose content contains no ASCII `\w` character "are written to the DB but never becomes searchable — no error, no warning, no log line"; on a real 4,845-memory store, 254/254 pure-CJK memories were unretrievable, and `PATCH` with new content "does NOT re-embed… Repair requires insert + delete, not patch." A write that reports success while the fact can never be recalled is the precise failure the honest-recall discipline exists to prevent.
5. **The release layer shows a silent-data-loss upgrade bug, caught and repaired.** Release server-v0.0.8 (2026-08-17) is an "Emergency patch": upgrading from a 0.0.7 release candidate to 0.0.7 "silently wiped search vectors… pre-existing documents stayed list[ed]" but unsearchable; 0.0.8 auto-repairs on boot by re-embedding rows whose text survived. Its notes add the durable half: "The migration test matrix now seeds real vectors into its legacy-store fixtures and asserts they survive upgrades." Release server-v0.0.9 then adds an API v5 migration with breaking local changes (localhost now requires the API key; `WORKFLOW_ENGINE=direct` no longer supported).

### Verdicts

- Discipline #7 (Supermemory parts: buckets, 8+8 budget, review queue, forget-matching, expiry contracts): **QUALIFIED.** The contracts remain the adoptable unit, but the source's own shipped implementation currently violates the expiry contract (#1806) and the write-then-recall contract (#1740). Adopt the contracts as specifications to test against, never as behaviours the source can be assumed to have. The closed-engine caveat upgrades from "un-auditable" to "un-auditable and user-contested" (#1299).

### New finds

- **ADOPT-IDEA:** migration fixtures seeded with real data that must survive upgrades (from the v0.0.8 notes): any local memory-store migration ships with a fixture containing real vectors/records from the prior format and an assertion they remain retrievable after migration. This is a blocker shape passes 1-2 did not surface.
- **REFERENCE:** #1740's ASCII-anchor workaround is product-specific; the transferable lesson (a silent candidate-set exclusion is worse than a low score) is already inside discipline #7's tiered-recall design and is now evidenced.

---

## 4. mem0ai/mem0 — discipline #7 (Mem0 parts: V3 extraction, fusion formula, ADD-only)

Issue corpus: 440 open / 1,900 closed issues, the largest real-issue corpus of the eight repos.

### Findings

1. **A production audit of 10,134 entries found 97.8% junk. This is the single highest-value find of this dive.** Closed issue #4573 "What we found after auditing 10,134 mem0 entries: 97.8% were junk" (25 comments): 32 days of production use, one agent, Qdrant backend, two extraction models (a small local model for 20 days, then a frontier model for 12). After hash-duplicate removal, near-duplicate clustering, and reading every remaining entry: "224 entries survived the full process. Out of 10,134. That's 97.8% junk across the entire collection. And of those 224 survivors, 186 had to be deleted and rewritten from scratch… Only 38 entries in the entire collection were clean enough to keep as-is." Failure clusters named in the report include hallucinated category clusters and "668 copies of a single feedback-loop hallucination" (the agent re-extracting its own prior output). No maintainer or collaborator comment appears anywhere in the thread; the issue is closed without a maintainer response in the record read.
2. **ADD-only's stale-fact failure is reproduced in production, still unfixed on main, and the thread independently converges on pass 2's adopted cure.** Open #4956 "ADD-only extraction in v3 may surface stale/contradictory facts for time-sensitive attributes" (23 comments): "contradictory memories accumulate over time instead of the newer fact superseding the older one… the scoring signals don't incorporate recency." A production user confirms against current code: "`score_and_rank` in `mem0/utils/scoring.py` orders purely by `semantic + bm25 + entity_boost` with **no temporal term** — and it is byte-identical to upstream `main`, so this is still unaddressed," with a worked stale-employer reproduction. Two candidate fix PRs are recorded as dead ends (one closed unmerged, one stalled dirty). Thread participants independently propose exactly what discipline #7 adopted from Graphiti: bi-temporal `valid_from`/`valid_to` with write-time invalidation and `as_of` replay. A controlled measurement in-thread: on 76 LongMemEval-S knowledge-update questions, date-sorting the same memories before answering moved 59/76 to 68/76, "on par with putting the whole ~105k-token history in the prompt."
3. **The V3 pipeline's "store-confirmed-only success" property, adopted in pass 2, is violated by the shipped pipeline.** Open #5245 "Silent memory loss when batch embedding partially fails in V3 add pipeline" (22 comments): when per-item embedding fails in the fallback path, the text "is **never added to `embed_map`**… the fact is silently dropped. No exception escapes the function, the caller of `Memory.add()` receives a normal response." The reporter names four more swallow-and-log sites in the same file. Release v2.2.1 (2026-09-25) partially answers the class on a neighbouring path: "`add()` no longer reports records the vector store rejected as successful `ADD` events" — i.e., the false-success defect was real enough to be release-noted, and the embedding path in #5245 remains open.
4. **Forgetting does not reach derived/session state.** Open #7452: since the v3 pipeline, `add()` keeps the last 10 raw messages per scope and feeds them back as context, but "`delete_all()` cleans up the scope's memories and its entity records, but never touches `messages`… after `delete_all(user_id="alice")`, Alice's recent messages are still on disk, and her next `add()` sends them to the LLM again, where they can get re-extracted into new memories. For someone who asked to have their data removed, that's the part that matters." This is a direct, reproduced violation of the erasure-reaches-derived-copies standard discipline #7 adopted from SLM, inside the other adopted memory system.
5. **The headline benchmark numbers are platform numbers; a maintainer confirms it.** Closed #2800 "Unable to reproduce locomo eval scores locally" (25 comments, 24 reactions, the most-reacted closed issue): the closing collaborator reply states verbatim: "The scores in the paper were from our SaaS platform (`MemoryClient`), not the OSS `Memory` class. These have different pipelines under the hood, so the numbers won't match up directly… we know the eval story for OSS isn't great right now." Pass 1's README-level caveat is now maintainer-confirmed.
6. **Users are asking for the faithfulness gate pass 2 designed around.** Open #7283 (34 comments, the second-most-commented open issue): "Faithfulness check before memory write, interested in contributing a pluggable verification hook." Open #5867 restates the ADD-only conflict problem; open #5352 (54 comments, the most-commented open issue) is a user-built workaround for "time-blindness, semantic conflicts, and missing CRUD in Mem0 OSS."

### Verdicts

- Discipline #7 (Mem0 parts): **WARNED.** Three of the properties pass 2 adopted as specifications are contradicted by the shipped OSS implementation in production reports: store-confirmed-only success (#5245, partially release-fixed on one path), retrieval that resolves contradictions (the fusion formula has no temporal term; #4956), and extraction quality at volume (#4573: an unreviewed ADD-only accumulation reached 97.8% junk in 32 days, including self-extraction feedback loops). The adopted designs (V3 integrity block, review queue, bi-temporal supersession) are not weakened; they are shown to be load-bearing, because their absence is exactly what failed. But no behaviour may be assumed from "Mem0 does it this way": each adopted property needs its own local test, and extraction must ship with a junk-rate audit (sampled human/automated review of stored entries) rather than trusting the integrity prompt alone.
- Discipline #7 (SLM erasure standard): **CONFIRMED by counterexample.** #7452 is the derived-copy failure occurring in the wild, in the form SLM's receipt/tombstone design is built to prevent.

### New finds

- **ADOPT-IDEA:** a periodic extraction junk-rate audit as part of any native ADD-only layer: sample stored memories, classify (clean / duplicate / hallucinated / malformed / feedback-loop), and report the rate; #4573 supplies both the method (hash dedup, cosine clustering, full read of survivors) and the base rate to beat.
- **ADOPT-IDEA:** date-order presentation as a cheap partial mitigation for stale-fact retrieval (in-thread controlled result, 59/76 → 68/76 with no deletion or rewrite), usable until write-time supersession lands.
- **REFERENCE:** #7283's pluggable pre-write faithfulness hook as the community's name for the review-queue gate.

---

## 5. thunlp/ProactiveAgent — discipline #5 (proactivity: scorer, gate, rubric)

Issue corpus: 7 open / 35 closed issues, nearly all setup and data questions. No releases exist (releases endpoint returns an empty list): the repo has never cut a GitHub release.

### Findings

1. **The reward-model headline is not reproducible by an independent trainer.** Closed #21 "Reward model training implementation fails" (12 comments, the most-commented issue in the repo): a user training with the paper's stated setup on 8xA100 reports per-category statistics of 0.59 / 0.54 / 0.57 / 0.74 against the paper's numbers, a training time of ~20 minutes against the reported 1.5 hours, and asks for the differing settings; the thread closes without the gap being explained in the record read. This corroborates pass 2's correction 25 (gate quality is a fine-tuning result) from the reproduction side: even the fine-tuning does not transfer with the published materials.
2. **The remaining issue layer is friction, not mechanism.** Open issues ask how raw data becomes processed events (#41), how training events are delimited (#44), and how to configure an alternative model (#34); closed issues are dominated by demo/Gym setup failures (ImportError, missing requirements file, config errors). The repo functions as a paper artefact with a support queue, not a maintained product.
3. **Tests layer confirms pass 2's reconciliation.** The tree's `eval/results/` ships per-model CSVs (including `judged.csv`) and `dataset/test_data/` holds the shipped splits; there is no test suite in the software sense, only the eval harness and its frozen outputs. Nothing in the tree contradicts pass 2's counts (6,790 corpus / 227 agent test / 120 reward test).

### Verdicts

- Discipline #5 (proactivity): **QUALIFIED.** The composed design (scorer first, locally built gate, quality rubric) stands, and #21 strengthens its central expectation-setting: do not budget for the fine-tuned F1 0.918 from any rebuild, including one that follows the repo's own training recipe. Add: the gate's quality claims need a local holdout before any lane relies on them, because the source's own numbers did not survive an independent reproduction attempt.

### New finds

- None with an adoption verdict. The reproduction gap is recorded as evidence under the verdict above. Looked-and-empty for new mechanisms: the entire open-issue list (7 items) contains no mechanism proposal.

---

## 6. vinicq/falsegreen-skill — discipline #2 (false-green defence: J1-J6, F7, Mode B)

Issue corpus: 4 open / 84 closed issues. The tracker is unusually disciplined: closed PRs cite issue numbers, and the open issues are self-filed defect reports against the skill itself.

### Findings

1. **The S-series codes shipped with no worked examples, and the author traces a two-release silent breakage to exactly that.** Open #170 "The S-series ships with no examples: 19 codes have neither a firing case nor a look-alike": "No S-code has an example in this repo… So 19 of the 24 advertised semantic codes ship with no example that proves they fire, and none with a look-alike that proves they do not." The root-cause claim is the load-bearing part: the S-series load path "was broken for two releases" and "nothing exercised an S-code, so nothing could detect that no S-code was loading. #169 adds a static gate that catches the specific regression, but a gate over instruction text cannot tell you whether a model, given the codes, applies them correctly." The tree confirms the example layout: `examples/{python,javascript,typescript}/semantic_cases.*` cover only cases 10, 11, 12, 15, 18 (as pass 2 extracted), five family files per language exist, `examples/robot/` has no semantic file, and the repo's own test directory is two files (`test/fix-gate.cjs`, `test/smoke.cjs`) — the protocol's real test corpus is its examples, and the semantic fifth of it is missing.
2. **Mode C's fix path executes model-generated code with the user's full credentials in its environment. Self-disclosed, unfixed.** Open #180: "`falsegreen-skill fix` asks the model for a strengthened test file and then executes that generated file… `process.env` is inherited in full, so a generated test can read the user's `ANANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `FALSEGREEN_API_KEY`… Absolute paths write anywhere… The network is open." The author deliberately disclosed before fixing ("the disclosure is a docs change, real isolation is a design change"), and the cheapest proposed cure is an environment allowlist. Pass 2 adopted the F7 gate as an acceptance contract; the issue shows the shipped executor that runs F7 does not practise the effect-class discipline discipline #8 adopted from ECC (generated-code execution is an SE4-class effect run with full ambient authority).
3. **The release layer shows the protocol still correcting itself in public.** v0.8.2 (2026-08-11): "fix(protocol): route every language through the semantic catalog (#168)" — the load-path fix behind #170 — plus "fix(registry): fill the interface metadata the scanner flags," i.e. the repo's own scan-before-list surface (discipline #11) flagging its metadata. v0.7.0 brought Mode B to the CLI as the `generate` command with a "fail-closed exit." Closed issue #52 records a research direction pass 2 did not surface: "suspect-link traceability — flag a green test whose traced spec changed (oracle staleness)."

### Verdicts

- Discipline #2 (false-green defence): **QUALIFIED, with one WARNED component.** ADOPT-CODE stands for the J1-J6 audit and the F7 contract. But: (a) QUALIFIED — the S14/S21-era semantic codes adopted as named risks rest on a catalog of which 19 of 24 codes have no firing example; treat S-code detection as unproven until each code carries a firing case and a look-alike, exactly as #170 demands of its own repo. (b) WARNED — do not run the shipped Mode C `fix` executor as-is: it executes model-generated tests with the full environment inherited. If Mode C is adopted, adopt it with an environment allowlist and a jailed working directory first (the issue's own option 1), or run F7 as a protocol with a locally controlled executor.

### New finds

- **ADOPT-IDEA:** oracle staleness as a named false-green class (from closed #52): a blocker whose traced specification changed since the test was written is suspect even if it still passes; pair the audit with a spec-change check.
- **ADOPT-IDEA:** every catalog code in any locally adopted audit taxonomy must ship with one firing example and one look-alike non-example, gate-checked (the contributing rule #170 quotes, generalised).

---

## 7. letta-ai/letta — discipline #7 (Letta parts: memory-editing doctrine, limits)

Issue corpus: 0 open / 1,304 closed issues. The search API returns zero open issues for the repo: the tracker is closed to new signal in this layer (consistent with the pass-2 finding that development moved to letta-code), so the issue layer here is historical. Releases, however, are current (0.16.8, 2026-05-14).

### Findings

1. **Compaction, the mechanism the whole paging design rests on, has a closed full-wipe defect at production scale.** Closed #3270 "sliding_window compaction ignores percentage, performs full context wipe": with `sliding_window_percentage: 0.15`, "compaction wipes the entire conversation history and replaces it with a single summary message. Behavior is identical to `mode: all` regardless of the configured percentage," reproduced at 0.15, 0.25, and 0.50 on a self-hosted 0.16.6 deployment. Closed #2605: "Agent crashes when summarization trims tool call without trimming tool response" — summarisation breaking the tool-call/response pairing invariant and crashing the client.
2. **The 0.16.7 release notes confirm compaction was the dominant production failure class.** "Context Window & Compaction (21 fixes). The biggest category of fixes. Self-hosted users were hit hardest by these." The same release **deprecates and removes block-limit enforcement**: "Block limits are no longer enforced — block limit validation has been deprecated and removed from the git memory sync path… Blocks can now grow freely." Pass 2 recorded Letta's character limits (20,000 canonical / 100,000 generic; 65,536 total core in letta-code) as reference sizing; the V1 server line has now abandoned enforcing its own limits, so those numbers describe letta-code only.
3. **Users asked for the standard memory benchmarks in-repo.** Closed #3115 "Feature Request: Add Standard Memory Evaluation Benchmarks (LOCOMO, MemBench, LongMemEval)" (14 comments) — the eval gap discipline #7's calibration measurement addresses was felt by the user base as well.

### Verdicts

- Discipline #7 (Letta parts): **QUALIFIED.** The memory-editing doctrine wording and letta-code limit set stand (they come from letta-code, which this dive's scope did not re-mine). The qualification: compaction/summarisation in the V1 line demonstrably violated its own configured bounds (full wipe at a 15% setting; broken message pairing), so any locally built compaction or summarisation step needs a bounds test (eviction fraction honoured; tool-call/response pairs never split) rather than trusting the pattern. The V1 block limits should no longer be cited as enforced behaviour.

### New finds

- **ADOPT-IDEA:** compaction bounds tests as named blockers for any summarisation step: configured eviction fraction is honoured within tolerance, and structural pairs (tool call/response, question/answer) are never split by a trim. Derived from #3270 and #2605.

---

## 8. promptfoo/promptfoo — discipline #8/#11 (declarative eval pattern, scan/eval gate)

Issue corpus: 152 open / 1,198 closed issues, but engagement is strikingly low for a repo of this size: the most-commented open issue has 7 comments and the most-commented closed issue 19. The top-commented items on the issues endpoint are all PRs (provider and red-team plumbing). There are no maintainer-pinned threads in the material returned.

### Findings

1. **The eval layer's own measurement-semantics defects are the signal that exists.** Open #10595 "Should avgLatencyMs reflect replayed latency for cache-hit responses?" traces the chain in current code: on a fully cache-hit re-run, "`avgLatencyMs` is bit-for-bit identical to the first run: the latency of the *original* run is replayed as if it were a property of the response, rather than a measurement of the current run," and latency does not distinguish "'measured this run' from 'replayed'." An eval tool whose headline metrics silently replay prior measurements is the measurement analogue of a false-green test.
2. **Releases are a high-cadence provider treadmill with recurring breaking changes.** 0.124.0-0.125.1 within October 2026: each release carries ⚠ BREAKING CHANGES that are mostly dependency posture changes (provider SDKs made opt-in one by one: WatsonX, Langfuse, Slack, Codex Security, OpenAI Agents, Claude Agent/Codex). The declarative eval pattern is stable; the tool's surface churns weekly. This supports pass 1's decision to adopt the pattern and not the tool, and pass 2 did not revisit it.
3. **Tests layer:** not tree-mined in this dive (the repo is too large for the remaining API budget; see ledger). The closed-PR layer shows test-hygiene work being taken seriously at maintainer level ("test(hygiene): track hoisted mock reset ownership," 33 comments), but no issue or release contradicts or extends the pass-1/pass-2 account of what the tool tests.

### Verdicts

- Discipline #8 (eval evidence layer): **QUALIFIED.** The capsule/effect-class design stands; add a measurement-provenance rule drawn from #10595: every reported metric must distinguish measured-this-run from replayed/cached, at the row level and in the run summary, or the evidence artifact overstates what was observed.
- Discipline #11 (scan-before-list): **CONFIRMED (directionally).** The release treadmill is the cost side of adopting the tool itself; the pattern-level adoption (declarative fixtures, thresholds) avoids it. No change.

### New finds

- **ADOPT-IDEA:** measured-vs-replayed provenance on eval metrics (from #10595), folded into discipline #8 above.

---

## 9. Cross-repo synthesis

Three patterns recur across independent repos and mechanisms, and each lands on a landed discipline:

1. **Silent success is the commonest production failure of adopted mechanisms.** Supermemory writes that can never be searched (#1740) and vectors silently wiped on upgrade (v0.0.8 notes); Mem0 extractions silently dropped (#5245) and success reported for rejected records (v2.2.1 fix); Letta compaction silently exceeding its bound (#3270). In every case the API reported success. The doctrine's proof-before-green rule is the right shape; these threads say the proof must include a read-back of the specific artefact (retrievable? stored? within bound?), not the operation's return code.
2. **Accumulation without a review/supersession mechanism degrades measurably and fast.** Mem0's 97.8% junk in 32 days (#4573) is the quantified version; the stale-fact thread (#4956) is the retrieval version; Supermemory's review queue and SLM's reviewed corrections exist precisely because the unreviewed path fails this way. Discipline #7's inferred-memory review queue moves from "pattern worth adopting" to "the thing standing between a memory layer and a junk majority."
3. **Gates die by usability or by seam, not by concept.** ECC's fact-force gate fires on `ls` with its scoped knob undocumented (#2573); its destructive-command regex is bypassed at an operand seam on the current release (#2642); Superpowers' ceremony cost is its top complaint (#743, #1152); falsegreen's F7 executor runs generated code with full credentials (#180). Every adopted gate needs three companions the original adoptions did not all state: a seam-case regression set, a scoped and discoverable escape, and an execution sandbox proportionate to what the gate runs.

## 10. Looked-and-empty ledger

Places checked in this dive that yielded nothing load-bearing. Each is a valid result.

| Place | Result |
|---|---|
| thunlp/ProactiveAgent releases | Empty: the repo has never cut a GitHub release (releases endpoint returned an empty list). |
| thunlp/ProactiveAgent open issues (all 7) | No mechanism proposals; setup/data questions and two collaboration solicitations only. |
| letta-ai/letta open issues | Empty by construction: search total for open issues is 0; the tracker carries no current signal (development moved to letta-code, per pass 2). Closed issues were mined as history instead. |
| promptfoo/promptfoo pinned/maintainer threads | None found in the returned material; open-issue engagement tops out at 7 comments. No maintainer correction thread exists in the top layer. |
| promptfoo/promptfoo tests tree | Not mined: repo too large for the remaining unauthenticated API budget after issues/releases; logged as not-fetched rather than sampled silently. |
| affaan-m/ECC discussions / pinned issues | No pinned flag is exposed on the issue objects returned; the top-commented closed items are bot-generated tracking issues with no mechanism content beyond what is reported above. |
| vinicq/falsegreen-skill issue #180 comments | Zero comments; the issue body itself is the complete disclosure and is quoted from the body. |
| supermemoryai/supermemory issue #1806 comments | Only a Linear linkback bot comment; no maintainer text. The defect stands on the body alone, marked as such. |
| Mem0 issue #4573 maintainer response | None exists in the 25-comment thread; the issue is closed with no maintainer/collaborator comment in the record. Recorded as absence, not filled in. |
| obra/superpowers tests directory | Not re-mined: pass 2 already enumerated `tests/` and logged the live-session evals as external (prime-radiant-inc/superpowers-evals, not fetched in either pass). The release-layer probe evidence (v6.4.2) is reported instead. |

## 11. Coverage counts for this dive

- Issue search totals (open/closed): superpowers 195/877; ECC 77/855; supermemory 23/393; mem0 440/1,900; ProactiveAgent 7/35; falsegreen-skill 4/84; letta 0/1,304; promptfoo 152/1,198.
- Per repo: top 15 open + top 15 closed issues by comment count read (titles, bodies); top 30 open + top 20 closed items on the issues endpoint read (PR/issue separation recorded); full comment threads read for 14 issues (mem0 #4573, #4956, #5245, #7452, #2800; superpowers #743, #2530, #895, #2342; ECC #3223, #2642; supermemory #1299, #1806; falsegreen #180, zero comments).
- Releases: 10 most recent per repo read (ProactiveAgent: none exist).
- Trees: full recursive trees read for falsegreen-skill (153 paths) and ProactiveAgent (136 paths), tests/examples paths extracted.
