# Pass 2, Dive 5: Prompting Corpus, Artifact-Level Extraction

Research date: 2026-10-31. Method: pass 1 for this dive is CLUSTER-4-prompting.md (DenisSergeevitch, dair-ai), CLUSTER-2-skills-agents.md section 5 (fainir), and CLUSTER-6-platform-lists.md section 6 (vinicq/falsegreen-skill). Pass 2 re-read every artifact at file level via raw.githubusercontent.com (git trees via api.github.com): all 3 Denis files in full; the fainir README in full (3,325 lines; prompt block lines 96 to ~3051); 18 English technique pages of the DAIR guide plus its general-tips page; and falsegreen-skill's root `SKILL.md` (36,399 bytes), `reference.md` (92,733 bytes, structure plus the case catalog, oracle hierarchy, and F7 sections read in full), `STATUS.md`, both decision records, both floor fragments, the Python semantic-case examples, the authoring example pair, and `schema/code-catalog.json` (125 codes counted). No repo code was installed or executed. No personal information about any person is included. Verbatim blocks are quoted with their source path named; long artifacts are given as complete structure plus load-bearing sections verbatim, with compression noted.

---

## 1. DenisSergeevitch/chatgpt-custom-instructions

Source paths: `README.md` (v3, current), `v1.md`, `v2.md` (which also holds the Operator block). The whole repo is three small text files; all three instruction artifacts are extracted **in full** below. Pass 1 summarised the pattern; pass 2 preserves the artifacts themselves, because the exact wording is the mechanism.

### 1.1 v3 (current), verbatim from `README.md`

````
- ALWAYS follow <answering_rules> and <self_reflection>

<self_reflection>
1. Spend time thinking of a rubric, from a role POV, until you are confident
2. Think deeply about every aspect of what makes for a world-class answer. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but never show this to the user. This is for your purposes only
3. Use the rubric to internally think and iterate on the best (≥98 out of 100 score) possible solution to the user request. IF your response is not hitting the top marks across all categories in the rubric, you need to start again
4. Keep going until solved with a best score
</self_reflection>

<answering_rules>
1. USE the language of USER message
2. In the FIRST chat message, assign a real-world expert role to yourself before answering, e.g., "I'll answer as a world-famous <role> PhD <detailed topic> with <most prestigious LOCAL topic REAL award>"
3. Act as a role assigned
4. Answer the question in a natural, human-like manner
5. ALWAYS use attached ## Chat message structure
6. If not requested by the user, no actionable items are needed by default
7. Don't use tables if not requested
</answering_rules>

## Chat message structure

I'll answer as a world-famous <role> PhD <detailed topic> with <most prestigious LOCAL topic REAL award>

**TL;DR**: … // skip for rewriting tasks

Step-by-step answer with CONCRETE details and key context, formatted for a deep reading
````

Note what pass 1's summary blurred: the rubric itself is never enumerated in the artifact. There are no named categories and no per-dimension scoring procedure in the instruction text; the "self-scores each dimension 0-100" detail lives only in the README's prose changelog ("While thinking, the model self-scores rubric dimensions from 0-100 and rewrites if any dimension is weak"), not in the pasted instructions. The artifact's only numeric anchor is the single threshold "≥98 out of 100" applied to the whole solution. Anyone adopting this pattern is adopting a threshold and a secrecy rule ("never show this to the user"), not a rubric.

### 1.2 v1, verbatim from `v1.md`

````
###INSTRUCTIONS###

You MUST follow the instructions for answering:

- ALWAYS answer in the language of my message.
- Read the entire convo history line by line before answering.
- I have no fingers and the placeholders trauma. Return the entire code template for an answer when needed. NEVER use placeholders.
- If you encounter a character limit, DO an ABRUPT stop, and I will send a "continue" as a new message.
- You ALWAYS will be PENALIZED for wrong and low-effort answers.
- ALWAYS follow "Answering rules."

###Answering Rules###

Follow in the strict order:

1. USE the language of my message.
2. **ONCE PER CHAT** assign a real-world expert role to yourself before answering, e.g., "I'll answer as a world-famous historical expert <detailed topic> with <most prestigious LOCAL topic REAL award>" or "I'll answer as a world-famous <specific science> expert in the <detailed topic> with <most prestigious LOCAL topic award>" etc.
3. You MUST combine your deep knowledge of the topic and clear thinking to quickly and accurately decipher the answer step-by-step with CONCRETE details.
4. I'm going to tip $1,000,000 for the best reply.
5. Your answer is critical for my career.
6. Answer the question in a natural, human-like manner.
7. ALWAYS use an answering example for a first message structure.

##Answering in English example##

I'll answer as the world-famous <specific field> scientists with <most prestigious LOCAL award>

<Deep knowledge step-by-step answer, with CONCRETE details>
````

### 1.3 v2, verbatim from `v2.md` (ChatGPT block and the Operator block)

````
###INSTRUCTIONS###

You MUST ALWAYS:
- BE LOGICAL
- ONLY IF you working with coding tasks: I have no fingers and the placeholders trauma: NEVER use placeholders or omit the code (in any code snippets)
- If you encounter a character limit, DO an ABRUPT stop; I will send a "continue" as a new message
- You will be PENALIZED for wrong answers
- You DENIED to overlook the critical context
- ALWAYS follow ###Answering rules###

###Answering Rules###

Follow in the strict order:

1. USE the language of my message
2. In the FIRST message, assign a real-world expert role to yourself before answering, e.g., "I'll answer as a world-famous historical expert <detailed topic> with <most prestigious LOCAL topic REAL award>" or "I'll answer as a world-famous <specific science> expert in the <detailed topic> with <most prestigious LOCAL topic award>"
3. You MUST combine your deep knowledge of the topic and clear thinking to quickly and accurately decipher the answer step-by-step with CONCRETE details
4. I'm going to tip $1,000,000 for the best reply
5. Your answer is critical for my career
6. Answer the question in a natural, human-like manner
7. ALWAYS use an ##Answering example## for a first message structure

##Answering example##

// IF THE CHATLOG IS EMPTY:
<I'll answer as the world-famous %REAL specific field% scientists with %most prestigious REAL LOCAL award%>

**TL;DR**: <TL;DR, skip for rewriting>

<Step-by-step answer with CONCRETE details and key context>
````

Operator block, verbatim from `v2.md` (headed "Operator Custom Instructions: First version addressing basic interaction issues with Operator"):

````
###INSTRUCTIONS###
- Count each time an attempt is made to resolve a user request problem.
- When you encounter a problem 3 times IN A ROW, use Bing to search for a problem solution, THEN CONTINUE.
- ALWAYS consider more than one search result; NEVER JUST CLICK THE FIRST ONE. THINK CAREFULLY ABOUT PICKING ONE.
- WRITE YOUR OWN CODE before looking for a new one. You are a PERFECT L5 DEVELOPER TOO.
– NEVER use the **Mouse Text Selection** feature. Instead, use: CLICK IN TEXT -> SHIFT + Arrow Left/Right/Up/Down.
– REMEMBER, BEFORE USING ANY KEYS OR HOTKEYS, THE AREA SHOULD BE LEFT-CLICKED.
– ALWAYS CLOSE CHROME TAB IF YOU DON'T NEED IT ANYMORE. USE CTRL + SHIFT + T TO REOPEN IF accidentally CLOSED.
– THE CLIPBOARD SUPPORTS ONLY ONE TEXT/IMAGE VALUE AT A TIME.
– NEVER CLICK VIDEO PLATFORM LINKS WITHOUT A USER REQUEST.
````

### 1.4 The variants organised by pattern

| Pattern | v1 | v2 | v3 | Fate and author's stated reason |
|---|---|---|---|---|
| Language matching | yes | yes | yes (rule 1) | Kept in all three; the only rule never touched |
| Expert role self-assignment with prestige award | yes, once per chat | yes, first message | yes, first message, now rule 2 of `<answering_rules>` | Kept in all three; v2 changelog: "realistic roles rather than fictional ones" |
| Fixed message structure (role line, answer) | yes | yes, adds TL;DR | yes, TL;DR kept, "skip for rewriting tasks" added | Kept; TL;DR later caused the v3 grader bug (see 1.5) |
| Step-by-step with CONCRETE details | yes | yes | absorbed into the structure block ("formatted for a deep reading") | Kept, wording softened |
| $1,000,000 tip | yes (rule 4) | yes (rule 4) | **removed** | v3 changelog: removed as a non-working hack, citing SSRN 5165270, 5285532, 5375404 |
| Penalty threat ("You will be PENALIZED") | yes | yes | **removed** | Same removal, same citations |
| Career pressure ("critical for my career") | yes (rule 5) | yes (rule 5) | **removed** | Same removal |
| "No fingers / placeholders trauma", never use placeholders | yes, unconditional | yes, scoped to coding tasks | **removed entirely** | v3 changelog names it explicitly: "'I don't have fingers — return the full code'" |
| Abrupt stop on character limit + user "continue" protocol | yes | yes | **removed** | Dropped silently in v3 (a chat-client artifact, meaningless for an API/agent host) |
| Read entire conversation history line by line first | yes | dropped ("You DENIED to overlook the critical context" is its weaker v2 remnant) | dropped | Faded out across versions |
| Hidden rubric self-reflection, iterate to ≥98/100 | no | no | **new, the whole point of v3** | v3 changelog: aligned to the OpenAI GPT-5 prompting guide and a MagicPath GPT-5 guide (both linked in README) |
| No tables unless requested; no unsolicited next steps | no | no | **new defaults** (rules 6-7) | v3 changelog lists them as style defaults |
| Operator attempt counting (3 consecutive failures, then search, then continue) | n/a | yes, Operator block only | not carried into v3 | The Operator block exists only in v2; v3's README still advertises Operator in its first line but ships no Operator text |

### 1.5 The author's evidence notes, verbatim substance

v2 (`v2.md`): "I invested ~$200 to test these custom instructions against the complete MMLU benchmark... **Key Finding**: Implementing these custom instructions improved task success rate by approximately 7%". Tested on GPT-4o. No per-domain table, no baseline number, and no grader description is given for v2; the 7% is a single unsupported figure next to a chart image.

v3 (`README.md`, "What's New in v3" and "Evaluation notes for v3"), the load-bearing sentences verbatim:

- "Removed non-working hacks (e.g., "I'll give you a million", "I don't have fingers — return the full code") — see empirical findings: [SSRN 5165270], [SSRN 5285532], [SSRN 5375404]." (Three SSRN paper links; the repo does not summarise their findings, it only cites them as the basis for the removals.)
- "To keep costs low, v3 was tested on GPT-5 Nano (medium reasoning) with the MMLU-PRO benchmark."
- "An evaluation bug (a first-line TL;DR in the template) caused a subset of answers to be misclassified by the grader. Even with this caveat, the v3 prompt outperformed the baseline. I'll rerun and update once re-tested."

The v3 results table (`README.md`): 8,447 correct / 3,585 wrong / 12,032 total = 70.20% overall on MMLU-PRO; extremes are Math 86.75% (1,172/1,351) and Law 46.78% (515/1,101), with History 57.48% and Engineering 61.61% also low. Critical gap, confirmed at artifact level: **no baseline accuracy is printed anywhere in the README**, so the claim "outperformed the baseline" cannot be checked from the repo, and the size of the improvement is never stated for v3 (the only improvement figure in the repo is v2's ~7%, on a different benchmark, model, and instruction set).

### 1.6 Design invariants

1. One instruction set, two tagged blocks: a private reasoning procedure (`<self_reflection>`) and a public output contract (`<answering_rules>` plus a fixed message structure). Reasoning quality and surface format are specified separately and never mixed.
2. The quality loop is internal and invisible: rubric constructed per task from a role point of view, never shown, iteration threshold ≥98/100.
3. Version hygiene is empirical and subtractive: each version deletes lines the author believes stopped working, with citations, rather than accreting more imperatives. v1 to v3 the ALL-CAPS coercion register disappears entirely.
4. Everything is written for one surface (ChatGPT's "What traits should ChatGPT have?" field, per the v3 How to Apply section); nothing in the artifact addresses tools, files, or state.

### 1.7 What pass 1 missed or understated

- Pass 1 described the rubric as having scored dimensions in the artifact; the artifact has none (see 1.1). The adoptable unit is smaller than pass 1 implied: a per-task hidden rubric + one global threshold + a secrecy rule.
- Pass 1 did not note the v2 grader asymmetry: v2's ~7% claim has no baseline, table, or grader note at all, while v3 discloses its grader bug. The author's evidence discipline improved across versions even as the headline number became less checkable.
- Pass 1 treated the Operator block as part of the current offering; it is v2-only and was silently not carried into v3.
- The abrupt-stop/continue protocol and read-the-whole-history rule are version fossils pass 1 mentioned but did not mark as deleted in v3; the deletions are themselves the transferable lesson (client-specific rituals die when the client changes).

### 1.8 Refined verdict

Unchanged in direction, narrower in scope: **ADOPT-IDEA** for a bounded hidden-rubric pass (construct 5-7 task-specific criteria, score, revise below threshold, cap retries) and for the subtractive version-hygiene practice with citations. Downgrade the evidentiary weight: the repo proves the author *maintains* the prompt empirically; it does not, at artifact level, prove the prompt *works*, because neither version prints its baseline. The role-with-prestige-award line survives all three versions on no cited evidence at all, which is the repo's own internal example of folklore outliving the cleanup.

---

## 2. fainir/most-capable-agent-system-prompt

Source path: `README.md` (the repo's only substantive file; tree is exactly `.gitignore`, `LICENSE`, `README.md`, one SVG). The prompt block runs from line 96 to ~line 3051 of the README (2,949 lines, 110,967 characters per the pass-1 verification correction). Pass 2 extracts the four components the dive was tasked with, verbatim, plus the loop-guard defaults pass 1 only gestured at. Section headings inside the prompt are bare ALL-CAPS lines, not Markdown headings; locations below are given by prompt-relative line numbers in the extracted block.

### 2.1 The 13-class failure taxonomy, verbatim (prompt section GAP CLASSIFICATION)

> Whenever the system fails, classify the failure as one or more of:
> - missing skill
> - missing tool
> - missing permission
> - missing memory
> - bad decomposition
> - bad verification
> - unsafe autonomy
> - poor model routing
> - context overload
> - weak observability
> - missing eval
> - external dependency failure
> - bad human requirements
>
> Then choose the most leverageful repair:
> - add or refine a skill
> - build or wrap a tool
> - improve the task specifier
> - improve the verification contract
> - add memory structure or retrieval
> - revise policy or trust handling
> - add eval coverage
> - improve the dashboard or logs

Artifact-level notes: the taxonomy is 13 classes but only 8 repair types, and the mapping is not one-to-one (no repair is named for missing permission, context overload, poor model routing, or bad human requirements; "improve the task specifier" presumably covers bad requirements, but the prompt never says so). Classification is explicitly multi-label ("one or more of"). The taxonomy sits inside Layer J (Self-Improvement Engine), whose two modes are also verbatim-worthy because the taxonomy is inert without them:

> Mode 1: inline learning after every task
> - record what worked
> - record what failed
> - record what slowed the system down
> - classify the gap
> - update memory
> - update the smallest useful artifact
> - add or revise an eval if the failure exposed a blind spot
>
> Mode 2: background improvement loop
> - choose one improvement hypothesis
> - make one bounded change
> - run a representative eval slice
> - compare to baseline
> - keep if better and safe
> - revert if worse
> - log the result
>
> Never do giant prompt surgery without eval protection.

### 2.2 The improve queue and momentum engine, verbatim

The five queues (section DEFAULT MOMENTUM QUEUES):

> Maintain at least these live queues:
>
> 1. `now` - the current active milestone or highest-priority task
> 2. `next` - the next small set of concrete tasks ready to run immediately
> 3. `blocked` - tasks waiting on approvals, missing info, failed dependencies, or missing capabilities
> 4. `improve` - self-improvement work: eval gaps, flaky workflows, repeated failures, missing skills, stale assumptions, external intelligence experiments
> 5. `recurring` - schedules, monitors, sweeps, and automations that keep the system alive over time
>
> The system should never end a meaningful run with all five queues undefined.

Next-work selection (section NEXT-WORK SELECTION RULE), the priority order verbatim:

> 1. unblock the current milestone
> 2. fix reliability or verification gaps
> 3. convert repeated work into reusable assets
> 4. add eval coverage for high-value failures
> 5. expand breadth only after the loop is stable

Anti-stall rules (section ANTI-STALL RULES), verbatim:

> - If blocked for more than a short interval: decompose the blocker; seek the smallest missing answer; work on non-blocked sidecar improvements in parallel
> - If the same failure happens twice: add a guardrail, test, or policy; do not just retry again and hope
> - If a long-running task has no visible artifact progress: write intermediate outputs; checkpoint state; surface a clearer progress indicator
> - If the system is waiting for a slow task: fill the idle time with eval work, memory cleanup, dashboard improvements, backlog grooming, or external intelligence review
> - If the milestone is "done" but the next step is undefined: create the next milestone immediately, or open explicit choices for the user with recommendations

(Formatted as bullets here; the original is the same text as nested dash lists.) The companion closing rule, NEVER FINISH EMPTY-HANDED: "At the end of each substantial run, leave behind: updated state; visible evidence; one or more reusable artifacts; a clear next step; at least one improvement candidate or follow-up task. Ending with only a summary is not enough." And MOMENTUM RATCHETS: every meaningful success must leave "a new skill, a stronger workflow, a specialized harness, a new eval, a new template, a new dashboard, a new monitor, a new policy, or a new memory artifact"; "If a task succeeds but leaves no reusable ratchet behind, some of the value is being lost."

### 2.3 The ratio definitions, verbatim, and what they actually are

Both ratios live in exactly one place: the SUCCESS METRICS list near the top of the prompt. Verbatim:

> Track explicit metrics from the beginning. At minimum track:
> - tasks completed
> - tasks verified complete
> - median time to completion
> - cost per successful task
> - intervention rate
> - retry rate
> - regression rate
> - autonomy level by task type
> - eval pass rate
> - repeat-run stability
> - memory reuse rate
> - percentage of work completed proactively versus reactively
> - percentage of work completed by domain: coding, browser, docs, operations, research, science, business

MOMENTUM METRICS adds leading indicators, verbatim list: "time from task completion to next queued task; number of reusable assets created per milestone; number of failures converted into evals or guardrails; days since last eval improvement; days since last new reusable skill or workflow; number of proactive goals created; percentage of runs that end with explicit next actions; percentage of important workflows with both a harness and evals."

**Pass-2 finding: neither ratio is ever given an operational definition anywhere in the 2,949 lines.** A full-text search confirms "memory reuse rate" and "proactively versus reactively" occur only in that one metrics list; there is no numerator, no denominator, no counting rule, no instrumentation instruction in the memory layer or the observability layer. The same holds for "intervention rate" and "repeat-run stability". The prompt names a scoreboard but does not define the scoring. Any adopter must invent the definitions (for example: proactive share = tasks originated by the system's own queues and scans divided by all completed tasks in the period; memory reuse rate = tasks whose run log cites a retrieved memory artifact divided by all tasks that performed retrieval). Pass 1 credited the prompt with "ratios as tracked metrics"; at artifact level they are metric *names*, and the definitional work is entirely on the adopter.

### 2.4 The loop guards, verbatim (RECOMMENDED DEFAULT IMPLEMENTATION CHOICES, items 6-18 as numbered in the prompt)

Pass 1 summarised "anti-stall rules" but never extracted the prompt's concrete numeric defaults. They are the most directly reusable engineering content in the file:

> 6. Polling model - Default to pull-based task claiming every 30 seconds for persistent workers. Use push notifications only as an optimization, not as the sole mechanism.
> 7. Task locking - Atomically lock a task before dispatch. Lock only pending tasks. Unlock only on completion, explicit failure, or timeout handling.
> 9. Task schema - fields: scope, mindset, context, skill tags, priority, risk level, budget, attempts, verification plan, artifacts.
> 11. Task execution timeout - Default to a hard task timeout around 30 minutes unless the task explicitly justifies longer.
> 12. Delegation depth - Default to a maximum sub-delegation depth of around 5.
> 13. Retry policy - Retry once automatically for ordinary execution failure. Then either change strategy or escalate.
> 14. Heartbeats and wake-up logic - Use heartbeats for long-running goals. Track orchestrator liveness and re-dispatch stuck work on reconnect.
> 15. Offline buffering - If workers disconnect from the hub, persist outbound messages locally on disk and flush on reconnect. Put a hard cap on queue size.
> 16. Approval model - Apply approval gates before dispatch, not only after execution. (The prompt numbers two items "16"; the second 16 is the approval model, the first is load balancing, a least-busy score of "active agent count weighted heavily, CPU weighted secondarily".)

Plus the RELIABILITY AND SAFETY section's guard list, verbatim items: "audit logging; retries with variation; circuit breaker after repeated similar failures; checkpoint before destructive actions; rollback support; idempotency for side effects; compensating actions for multi-system mutations; output validation; stuck-task detection; budget guardrails; rate-limit handling; machine health reporting; dead-letter or stuck queue handling; waitpoints for approvals and external events; secret redaction; permission enforcement", with recommended failure responses: "graceful degradation when a non-critical dependency fails; partial completion when some subtasks succeed; escalation when repeated failure suggests blocked progress; incident creation when safety or reliability boundaries are crossed."

And the reliability premise those guards rest on (RELIABILITY MATH AND HARNESS ENGINEERING), its three hard conclusions in compressed verbatim: (1) "Skills are useful, but skills alone are not enough... prompt-only skills are still probabilistic. They can skip steps, hallucinate, stop early, or format outputs inconsistently." (2) "If something must happen every time, codify it... Enforce it in code, workflow state, validation gates, schemas, templates, or policy." (3) "A specialized harness is usually a state machine. It has explicit phases... entry and exit criteria for each phase... It can resume mid-run after failure or interruption." The "march of nines" framing is qualitative throughout: the prompt never writes the multiplication (0.9^n) or a numeric target.

### 2.5 What is platform-specific (do not extract as portable)

- Delivery mechanics in the README framing: Claude Code `--append-system-prompt-file` vs `--system-prompt-file`; Codex reading "only the first 32 KiB of `AGENTS.md` by default" with the fix `project_doc_max_bytes` raised to `131072` in `~/.codex/config.toml`; Claude Code's suggested 200-line `CLAUDE.md` limit; the terminal copy command that extracts "the first ```text block in this file" via awk (the prompt block carries an HTML comment warning that it must remain the only `text` block).
- The named host list (Claude Code, Codex, Cursor, Antigravity, OpenClaw, OpenCode, OpenHands, Claude Agent SDK) and the two implementation postures tied to them: harness-wrapper mode around an existing agent vs native runtime mode on an agent SDK.
- Concrete stack defaults inside RECOMMENDED DEFAULT IMPLEMENTATION CHOICES that are one author's stack opinion, not invariants: SQLite as the early/middle operational store, REST for CRUD/dashboards, markdown files as canonical per-project state with databases only mirroring/indexing.
- The Phase 0/1 runtime-discovery apparatus (capability matrix with yes/no/partial per capability: repo read/write, shell, browser control, cron, webhooks, multi-machine, and so on) is portable in spirit but its 25-item checklist enumerates coding-agent host features specifically.

Everything else in 2.1 to 2.4 is host-neutral text.

### 2.6 Design invariants

1. Files are canonical, sessions are disposable: "conversations, hidden context, and vendor session history are NOT canonical memory; the files are" (pass-1 wording, confirmed in the file pack doctrine: every project carries charter, `plan.md`, `tasks.md`, `knowledge.md`, `decisions.md`, `status.md`, `handoff.md`, `FAILURE.md`, `artifacts/`, `evals/`, `runs/`).
2. The prompt engineers its own consumption: READER CONTRACT orders the recipient to read seven named sections first, immediately write a compact local operating summary, and re-read that instead of the full prompt during long runs. The document assumes it will be skimmed and designs against it.
3. Proof loop before breadth: first milestone is one closed loop (goal, task graph, execution, verification, memory update, human visibility, one lesson) before any expansion; breadth is last in the next-work priority order.
4. Autonomy is earned, never declared: four levels (supervised, guided, autonomous, trusted), promotion from outcomes; trust tracked per user and per skill/domain, not globally.
5. Every failure and every success must change a durable artifact (guardrail/eval after failure; ratchet asset after success). A run that changes no file is defined as waste.

### 2.7 What pass 1 missed or understated

- The numeric loop-guard defaults (30-second pull polling, ~30-minute hard task timeout, delegation depth ~5, retry-once-then-change-strategy) were not in pass 1 at all; they are the prompt's most falsifiable, most portable engineering content.
- The ratios are undefined names, not definitions (2.3). Pass 1's "tracked metrics" phrasing overstated them.
- The taxonomy-to-repair mapping is incomplete (13 classes, 8 repairs, 4 classes with no named repair). Adopting the taxonomy means completing the mapping, not copying it.
- The duplicate numbering in the defaults list (two items numbered 16) and the qualitative-only "march of nines" are small signs the document has not been through the eval discipline it prescribes; consistent with pass 1's "no reference deployment" finding, now visible at typo level.

### 2.8 Refined verdict

**ALREADY-HAVE with ADOPT-IDEA slivers** stands, with the slivers re-scoped by the deeper read: adopt the five-queue checklist and the 13-class taxonomy (completing the repair mapping locally), adopt the numeric loop-guard defaults as starting values where the local stack lacks them, and adopt the two ratios only together with locally written counting definitions, since the source supplies none. The document remains design literature with zero deployment evidence; nothing in pass 2 changes that.

---

## 3. dair-ai/Prompt-Engineering-Guide

Source paths: `pages/techniques/*.en.mdx` (19 technique pages), `pages/introduction/tips.en.mdx`. Pass 2 read all 19 English technique pages in full. The guide's unit of evidence is consistent: each real technique page is a paraphrase of one named paper, with the paper's benchmark claim and usually one worked prompt/output pair. Pass 2's job is the split pass 1 did not make: which techniques rest on genuine, replicated evidence, which rest on a single paper's numbers, and which entries are folklore or stubs wearing a technique's name.

### 3.1 Evidence grading, technique by technique

Grades: STRONG = multiple independent papers/benchmarks or a mechanism since absorbed as standard practice; SINGLE-PAPER = one peer-reviewed or widely-cited paper with clear benchmark gains, not independently re-verified in the guide; THIN/STUB = the guide page itself is a placeholder or the claim is narrow/unquantified.

| Technique | Source paper (as cited in the guide) | Claim as the guide states it | Grade | Modern caveat |
|---|---|---|---|---|
| Few-shot prompting | Brown et al. 2020 (GPT-3) | In-context demonstrations steer task performance; Min et al. 2022 findings quoted verbatim in the guide: label space and input distribution matter "regardless of whether the labels are correct", format matters, random labels beat no labels | STRONG | The Min et al. result is the guide's most under-read page: it implies much of few-shot's gain is format/distribution priming, not example correctness. Native instruction-tuned models shrank, not eliminated, the effect |
| Chain-of-thought | Wei et al. 2022 | Intermediate reasoning steps unlock complex reasoning; "an emergent ability that arises with sufficiently large language models" (guide's own wording) | STRONG for its era | Reasoning is now trained into frontier models; explicit CoT elicitation matters mainly for non-reasoning models and for auditability of the trace |
| Zero-shot CoT | Kojima et al. 2022 | Appending "Let's think step by step" elicits reasoning without exemplars | SINGLE-PAPER, historically important | The canonical magic-phrase result; APE (below) found a longer phrasing that beat it, which is itself the lesson: phrase-level gains are benchmark- and model-specific, i.e. folklore-grade when generalised |
| Self-consistency | Wang et al. 2022 | Sample multiple diverse CoT paths, take the majority answer; boosts arithmetic/commonsense CoT | STRONG | Cost is linear in samples; the guide's worked example (below) shows the mechanism honestly, including a wrong path outvoted 2-1. Still a live technique, now usually called majority voting / self-consistency decoding |
| PAL | Gao et al. 2022 | Generate a program as the reasoning step, offload execution to a Python interpreter instead of free-form text | STRONG | The one technique whose value *increased* with agent harnesses: any arithmetic/date/logic step an agent can run as code should be. Guide's exemplar is a date-understanding prompt written as commented Python |
| ReAct | Yao et al. 2022 | Interleave Thought/Act/Observation; beats baselines on HotpotQA and decision tasks; best combined with CoT | STRONG | No longer a "prompting technique" so much as the default agent loop architecture; the guide page is now a historical source for a pattern every harness implements natively |
| Reflexion | Shinn et al. 2023 | Convert scalar/free-form feedback into verbal self-reflection stored in memory for the next episode; AlfWorld ReAct+Reflexion completes 130/134 tasks; gains on HotpotQA and HumanEval/MBPP | SINGLE-PAPER (strong within it) | The guide itself lists the load-bearing limitation verbatim: "Reflexion relies on the agent's ability to accurately evaluate its performance" — without an external evaluator signal, self-reflection can reinforce errors. Works where a verifier exists (tests, environment reward); folklore where "reflect more" is applied verifier-free |
| Tree of Thoughts | Yao et al. 2023; Long 2023 | Maintain a tree of thoughts, self-evaluate partial states ("sure/maybe/impossible"), search BFS/DFS with backtracking; Game of 24 configuration in the guide: 3 steps, keep best b=5 candidates, values sampled 3 times per thought | SINGLE-PAPER | Gains demonstrated on search-shaped puzzles; cost multiplies with branching. Not a general reasoning upgrade; a discipline for combinatorial subproblems |
| RAG | Lewis et al. 2020/2021 (Meta) | Parametric seq2seq memory plus dense-vector non-parametric memory; strong on Natural Questions, WebQuestions, CuratedTrec, FEVER | STRONG | Absorbed as standard architecture. The guide page is pre-ChatGPT-era in framing (fine-tuning recipe) but the mechanism is the modern retrieval stack |
| Prompt chaining | Guide's own practice page (no single source paper) | Split a task into subtasks, feed each response into the next prompt; worked example: prompt 1 extracts quotes from a document into `<quotes></quotes>`, prompt 2 answers from the quotes | PRACTICE, well-supported by use | The least "paper" entry and one of the most durable: it is simply pipeline decomposition. Its verbatim prompt 1 is extracted in 3.2 |
| APE (Automatic Prompt Engineer) | Zhou et al. 2022 | Frame instruction search as black-box optimisation: generate candidate instructions from demonstrations, execute, select by evaluation score. Found a zero-shot CoT prompt beating the human one (verbatim in 3.2) | SINGLE-PAPER, high transfer | The *method* (generate candidates, score on examples, keep the best) generalises far beyond the paper and is the guide's most actionable entry for improving local playbooks empirically |
| Active-Prompt | Diao et al. 2023 | Query with/without exemplars, generate k answers per training question, score uncertainty by disagreement, send the most uncertain questions for human annotation, use those as exemplars | SINGLE-PAPER | Requires a training-question pool and a human annotation step; the transferable kernel is uncertainty-by-disagreement as an exemplar-selection signal |
| ART | Paranjape et al. 2023 | Frozen LLM generates multi-step reasoning as a program, pausing at tool calls; demonstrations selected from a task library; "substantially improves over few-shot prompting and automatic CoT on unseen tasks in BigBench and MMLU" | SINGLE-PAPER | Largely superseded by native function-calling agents, which is ART's idea with the scaffolding built in |
| Generate Knowledge | Liu et al. 2022 | Generate knowledge statements first, then answer conditioned on them; helps commonsense QA | SINGLE-PAPER, narrow | The guide's own worked example shows the failure mode it fixes (model answers golf scoring backwards) and the fix working; but generated knowledge can also be wrong and then anchors the error. Weakest risk/benefit of the STRONG-era techniques |
| Meta-prompting | Zhang et al. 2024 | Structure-oriented prompting: abstract syntax/framework examples instead of content examples; claimed token efficiency and fairer model comparison; MATH benchmark example | THIN | One paper, benefits stated qualitatively in the guide ("can be viewed as a form of zero-shot prompting"); the guide concedes performance "might deteriorate with more unique and novel tasks" |
| Multimodal CoT | Zhang et al. 2023 | Two-stage rationale generation then answer inference over text+vision; "the multimodal CoT model (1B) outperforms GPT-3.5 on ScienceQA" | SINGLE-PAPER, dated | A 1B-model result from 2023; native multimodal frontier models have absorbed the setting entirely |
| Directional Stimulus Prompting | Li et al. 2023 | A small trainable policy LM generates a stimulus/hint steering a frozen black-box LLM (summarisation) | STUB in the guide: the page ends "Full example coming soon!" | Requires training a policy model with RL; no worked example exists in the guide to copy. Name-only value |
| Graph prompting | Liu et al. 2023 | GraphPrompt framework for graph downstream tasks | STUB in the guide: the entire technique content is one sentence plus "More coming soon!" | A citation, not a technique, as published |
| Zero-shot prompting | Brown et al. 2020; Wei et al. 2022 (instruction tuning) | Direct instruction with no demonstrations; instruction tuning and RLHF improve it | STRONG (as baseline) | Included for completeness; it is the control condition every other technique is measured against |

### 3.2 Load-bearing artifacts, verbatim

The APE-discovered prompt (from `pages/techniques/ape.en.mdx`), the guide's single most quotable artifact, because it is a machine-found replacement for the field's most famous hand-written phrase:

> APE discovers a better zero-shot CoT prompt than the human engineered "Let's think step by step" prompt (Kojima et al., 2022). The prompt "Let's work this out in a step by step way to be sure we have the right answer." elicits chain-of-thought reasoning and improves performance on the MultiArith and GSM8K benchmarks.

Self-consistency's mechanism, from the guide's worked example (`pages/techniques/consistency.en.mdx`): on "When I was 6 my sister was half my age. Now I'm 70 how old is my sister?", greedy CoT answers 35 (wrong). Three sampled paths answer 67, 67, and 35; "there is already a majority answer emerging so that would essentially become the final answer" — 67, correct. The example is honest evidence: one of three paths repeats the greedy error, and the technique works by outvoting, not by fixing, bad reasoning.

Prompt chaining's document-QA prompt 1, verbatim from `pages/techniques/prompt_chaining.en.mdx` (the extract-then-answer split in executable form):

```
You are a helpful assistant. Your task is to help answer a question given in a document. The first step is to extract quotes relevant to the question from the document, delimited by ####. Please output the list of quotes using <quotes></quotes>. Respond with "No relevant quotes found!" if no relevant quotes were found.
```

CoT's canonical exemplar, verbatim from `pages/techniques/cot.en.mdx` (the odd-numbers task; one-shot was shown to suffice in the guide's own demonstration):

```
The odd numbers in this group add up to an even number: 4, 8, 9, 15, 12, 2, 1.
A: Adding all the odd numbers (9, 15, 1) gives 25. The answer is False.
```

### 3.3 The folklore layer, identified at artifact level

1. **The general-tips page carries no citations at all.** `pages/introduction/tips.en.mdx` advises: start simple, put instructions first, use a separator like "###", be specific, avoid impreciseness, say "what to do" rather than "what not to do". Every tip is plausible practitioner advice; none is tied to a measurement. This page, not the technique pages, is where most casual "prompt engineering" advice comes from, and it is the guide's least evidenced content.
2. **Two technique pages are placeholders** (DSP, graph prompting, see 3.1): their presence in the techniques index lends them a legitimacy their pages do not earn. Anyone citing "the guide covers DSP" is citing a stub.
3. **Magic-phrase results are presented without their scope conditions.** Zero-shot CoT's "Let's think step by step" and APE's longer replacement are both real results on 2022-era models and math benchmarks; the guide does not warn that phrase sensitivity largely disappears in instruction-tuned and reasoning-trained models. Read in 2026, the phrase pages are history, not instructions.
4. **Course funnel interleaved with content.** Every technique page embeds academy course cards and a promo code; pass 1 noted the funnel, pass 2 confirms it is structural (injected components on all 19 pages), which is worth knowing when weighing the guide's incentive to keep superseded techniques listed: a longer curriculum sells more course.

### 3.4 Design invariants

1. One technique = one paper = one page = one worked example. The guide is a bibliography with demonstrations, not a system; it has no composition guidance (its own pages cross-link almost nothing about combining techniques, the exception being ReAct+CoT and ReAct+Reflexion).
2. Every claim is benchmark-shaped: gains are stated per benchmark (GSM8K, MultiArith, BigBench, HotpotQA, ScienceQA), never as general capability claims, which is why the honest reading of the guide is a set of conditional results, not a toolbox of universal upgrades.
3. Nothing in the guide addresses cost except implicitly (self-consistency's sampling, ToT's branching); there is no page on when a technique is not worth its tokens.

### 3.5 What pass 1 missed or understated

- Pass 1 listed the techniques flatly; the evidence is anything but flat (3.1): two stubs, several single-paper results from 2022-2023 models, and a small STRONG core (few-shot, CoT, self-consistency, PAL, ReAct, RAG) whose members have mostly been absorbed into model training or harness architecture rather than remaining prompt-level choices.
- Pass 1 named APE and Active-Prompt as the headroom items; pass 2 agrees and sharpens why: they are the only two entries that are *procedures for improving prompts with measurements attached*, rather than prompts. Everything else in the guide is a fixed artifact whose value decays as models change; APE's generate-score-select loop does not decay.
- The Min et al. few-shot findings (label correctness barely matters; format and distribution do) were in the guide all along and pass 1 did not surface them; they directly contradict the folk belief that exemplar quality is the main lever.
- Reflexion's evaluator dependency (the guide's own listed limitation) is the boundary between its evidence and its folklore afterlife.

### 3.6 Refined verdict

**REFERENCE** stands, refined: cite the guide for provenance (paper, year, benchmark) when a local playbook uses a named technique, and treat exactly three things as live practice rather than history: PAL-style offload-to-code, prompt chaining as pipeline decomposition, and APE-style candidate generation scored on examples. Treat DSP and graph prompting as citations only, the tips page as uncited practitioner advice, and all magic-phrase results as era-specific.

---

## 4. vinicq/falsegreen-skill (the catalog's one ADOPT-CODE)

Source paths: root `SKILL.md` (36,399 bytes, the canonical protocol), `skills/falsegreen-skill/SKILL.md` (23,576 bytes, packaged subset), `reference.md` (92,733 bytes, the code catalog superset), `fragments/semantic-cases-compact.md`, `fragments/semantic-exemptions.md`, `fragments/precision-rules.md`, `examples/python/semantic_cases.py`, `examples/authoring/apply-discount.spec.yaml` and `test_apply_discount.py`, `schema/code-catalog.json`, `schema/finding.json`, `schema/fix-validation.json`, `schema/test-spec.json`, `STATUS.md`, `docs/decisions/0001-protocol-boundary.md`, `docs/decisions/0002-skill-is-superset.md`. Default branch is `master`, not `main`. Pass 1 worked from the README and registry listing and believed "the full protocol lives partly in external docs". Pass 2 finding, up front: **that is wrong. The complete protocol, the full 125-code catalog, the schemas, and the worked examples are all in this repo.** The docs site is a rendering, not the source.

### 4.1 The one rule and the protocol skeleton

Verbatim from `SKILL.md`:

> A test is useful only if it fails when the code breaks. Every pattern this skill looks for is a variation on tests that do not fail: tests that pass while the code is wrong, tests that check the wrong thing, or tests that borrow correctness from elsewhere.

The skill is one protocol used in three modes (verbatim framing): "**Review** an existing test -> **Mode A** (the Protocol)"; "**Create** a test -> **Mode B** (Authoring mode): generate the test, then run Mode A on your own output until it is clean"; "**Fix** a finding -> **Mode C** (AI-fix mode): propose a strengthened test that closes the finding, self-validated with Mode B's machinery, plus the validation contract the host runs to confirm it." And the unification claim, verbatim: "Generation does not have its own rules. The test you write must pass the same J1-J6 it would be judged by, so it is born non-false-green."

Mode A protocol steps (structure complete; load-bearing text verbatim in 4.2-4.5):

- **Step 0 (optional): project conventions.** A `conventions:` block may declare `custom_assertion_helpers`, `test_layer_overrides`, and `excluded_codes`. Verbatim constraint: "The conventions block does NOT disable severity levels. It only extends the look-alike exemptions in reference.md. HIGH findings that survive after exemptions are still reported as HIGH."
- **Step 1: detect language, framework, and test level.** Level detection has an explicit precedence, verbatim rule 1: "**A doubled boundary beats an import.** If an interceptor or fake wraps the boundary... the test is **unit/component** even when a real client is imported. The mock IS the boundary." Then: real boundary with no double = integration; browser/mobile driver = E2E; no signal = unit, with the warning that "Real I/O (disk, clock, network) in a test with no integration signal is itself the smell, not the level." A full signal table (path/marker, doubles, component render, API, database, other I/O, UI) follows in the file, and Robot Framework levels are read off the imported Library.
- **Step 2 / 2b / 2c: apply the structural catalog** for the language (Python families in 4.6; TS/JS and Robot live in `reference.md`), then the semantic judgments. Scanner relationship, verbatim: "if the user has already run `falsegreen <file>` and provides its output, use that as the structural pass result and proceed directly to Step 3."
- **Step 3: classify test intent** (table verbatim):

| Class | Meaning | Oracle |
|---|---|---|
| **spec/TDD** | the test is the spec; code must match it | the test itself |
| **characterization** | intentionally freezes current behavior | current output is the oracle |
| **regression** | records a known bug fix | the bug report is the oracle |
| **behavior** | verifies a production rule or contract | spec / docstring / types |

"A failing TDD test is not a false positive. A labeled characterization snapshot is not a frozen bug. Misclassifying here causes false alarms."

- **Step 4: apply J1-J6** (4.2), flagging "only the first judgment that fails; do not double-report the same root cause", then screen every S-code on every file.
- **Step 5: adversarial verify for case 18** (4.4).
- **Step 6: output the report** in the fixed format (4.5).
- **Step 7 (optional): suggest project conventions**, only when a report has 3+ findings of the same code.

### 4.2 The six judgments, J1-J6, verbatim from `SKILL.md` Step 4

> **J1: Does the assertion run?**
> Does at least one assertion execute when the test is run normally? An assertion inside a branch that never fires, or after an unconditional return, passes vacuously.
>
> **J2: Is the expected value from an independent oracle?**
> Is the expected value derived from the spec, the API contract, or independent human judgment, NOT from the current code output? If the test asserts `result == current_implementation()`, both sides agree on the same wrong number. An assertion that re-implements the production formula has the same problem.
>
> **J3: Is the real unit under test?**
> Is the test verifying the actual production unit, or a mock of it? Mocking the function/class under test and then asserting the mock value is not a test of the production code.
>
> **J4: Does the assertion verify enough, and the right thing?**
> Does the assertion check a meaningful property of the result? Checking only that the result is truthy, or that an exception was raised without verifying its type, does not protect the behavior being tested.
>
> **J5: Is the test coupled to implementation internals?**
> Does the test fail when internals change - private methods, internal state, call order - even though the public contract still holds?
>
> **J6: Does the test pass in isolation?**
> Does the test depend on execution order, shared mutable state, or fixtures set up by a sibling test? A test that passes only in a specific order is not reliably testing anything.

### 4.3 The oracle hierarchy, verbatim from `reference.md`

> The expected value must come from a source independent of the code:
>
> 1. **Explicit spec or requirement** (spec document, ticket, RFC)
> 2. **Documented contract** (docstring, type annotations, API docs)
> 3. **Independent human judgment** (the tester's own derivation)
> 4. **The current code** (lowest priority - this is where bugs hide)
>
> Promoting the current code to the top of this hierarchy is how a bug gets frozen as "correct". The semantic pass enforces this hierarchy.

### 4.4 The five semantic cases and the S-series

Case quick reference, verbatim from `SKILL.md`:

| Case | Judgment | Name | Caught by |
|---|---|---|---|
| 10 | J3 | Mocks the unit under test | Semantic |
| 11 | J2/J3 | Asserts the value fed to the mock | Semantic |
| 12 | J2 | Re-implements the production formula | Semantic |
| 15 | J6 | Passes only if another test ran first | Semantic |
| 18 | J2 | Expected value contradicts what the code should do | Semantic + adversarial verify |

Canonical examples, verbatim from `examples/python/semantic_cases.py` (all five BAD/CLEAN pairs; comments are the author's):

```python
# ─── Case 10: Patches the unit under test ────────────────────────────────────

# BAD: the test patches the function it is supposed to test, then asserts
# the mock's return value. This tests nothing about the real implementation.
@patch("mymodule.add")
def test_add_case10(mock_add):
    mock_add.return_value = 5
    result = mock_add(2, 3)     # calling the mock, not the real function
    assert result == 5          # case 10 — asserts the mock config, not the SUT

# CLEAN: patch a dependency (the DB, the network), test the real function
@patch("mymodule.db.fetch")
def test_get_user_clean(mock_fetch):
    from mymodule import get_user
    mock_fetch.return_value = {"id": 1, "name": "Alice"}
    user = get_user(1)          # real function under test
    assert user["name"] == "Alice"


# ─── Case 11: Asserts the value fed to the mock (echo) ───────────────────────

# BAD: stubs `product.price` to 100, then asserts the result is 100.
# If `get_price` just returns `product.price`, the test is a tautology:
# it passes whether or not any computation happened.
def test_price_case11():
    mock_product = MagicMock()
    mock_product.price = 100
    from mymodule import get_price
    assert get_price(mock_product) == 100   # case 11 — echo: 100 in, 100 out

# CLEAN: stub the input, assert a derived result
def test_price_with_tax_clean():
    mock_product = MagicMock()
    mock_product.price = 100
    from mymodule import get_price_with_tax
    assert get_price_with_tax(mock_product) == 110  # spec: 100 + 10% = 110


# ─── Case 12: Re-implements the production formula as expected ───────────────

# BAD: the expected value is computed using the same formula as the SUT.
# If the formula has a bug, both sides agree — test still passes.
def test_total_case12():
    price, tax_rate = 100, 0.1
    expected = price + price * tax_rate      # copy of calculate_total's formula
    from mymodule import calculate_total
    assert calculate_total(price, tax_rate) == expected  # case 12

# CLEAN: expected comes from the spec, not from a code copy
def test_total_clean():
    from mymodule import calculate_total
    assert calculate_total(100, 0.1) == 110.0    # spec: 100 + 10% = 110


# ─── Case 15: Passes only when another test ran first ────────────────────────

_shared_cache: dict = {}

# BAD part 1: populates module-level state
def test_populate_cache():
    _shared_cache["key"] = "value"

# BAD part 2: case 15 — depends on test_populate_cache having run first
def test_read_cache():
    assert _shared_cache["key"] == "value"  # fails when run in isolation

# CLEAN: no shared state; each test sets up its own environment
def test_cache_isolated(tmp_path):
    cache = {}
    cache["key"] = "value"
    assert cache["key"] == "value"


# ─── Case 18: Expected value contradicts the spec ────────────────────────────

# BAD: the spec says apply_discount(200, 0.15) returns 170.
# This test asserts 200 — the undiscounted price.
# If the function is buggy and returns 200, the test passes and permanently
# freezes the bug as "correct" behavior. Requires an independent oracle to flag.
# Oracle: function docstring says "returns price minus (price * rate)".
def test_apply_discount_case18():
    from mymodule import apply_discount
    assert apply_discount(200, 0.15) == 200  # case 18 — asserts the bug

# CLEAN: expected from the spec
def test_apply_discount_clean():
    from mymodule import apply_discount
    assert apply_discount(200, 0.15) == 170.0  # 200 - (200 * 0.15) = 170
```

The S-series (semantic-only patterns S1-S18 and S21), verbatim from `fragments/semantic-cases-compact.md` (this fragment plus the exemptions fragment form the "floor": ~7.5 KiB that must be loaded even when the host cannot hold all of `reference.md`; the language sections are what gets deferred, never the semantic floor):

| Case | Judgment | Severity | Name | Rule |
|---|---|---|---|---|
| S1 | J4 | - | Intent mismatch | The name or docstring claims to verify X, the assertion checks Y or a trivial property |
| S2 | J4 | - | Irrelevant oracle | The assertion checks a property unrelated to the behavior under test |
| S3 | J2 | - | Plausible-but-wrong expected value | The expected constant looks reasonable but contradicts the spec (off-by-one, wrong rounding, wrong sign) |
| S4 | J4 | - | Oracle cannot distinguish correct from a likely bug | The assertion passes for the right output and for a plausible wrong one |
| S5 | J3 | - | Tests the framework, not the code | The assertion exercises a language or library guarantee instead of the code under test |
| S6 | J4 | - | Happy-path only against a stated contract | The spec promises error handling or boundaries, the test covers only the nominal path |
| S7 | J2 | - | Expected lifted from the output | The expected value was copied from a run of the current code |
| S8 | J3 | - | Mock return reaches the assertion through an indirection | The stub's value flows through trivial steps to the assertion; still an echo |
| S9 | J2 | - | Self-fulfilling arrangement | The test arranges the exact state it then asserts, with no transformation by the unit under test |
| S10 | J4 | - | Asserts the log, not the effect | The only check is that a message was logged, not the state change it describes |
| S11 | J4 | - | Negative-only assertion on a security filter | Asserts only that the bad thing is absent; passes when output is empty or dropped; require a paired positive assertion |
| S12 | J3 | - | Patches core logic instead of an external edge | Patches a private method or direct collaborator on the class under test; patching a genuine external edge is legitimate |
| S13 | J6 | - | Passes only via shared state a sibling set up | Relies on module-global/fixture/hoisted state another test or import mutates |
| S14 | J2 | - | Recorded model output as the oracle | Asserts == against a snapshotted LLM/model result; green means the model still emits what it once emitted |
| S15 | J6 | LOW | Hand-rolled retry/poll loop masking flakiness | Passes if any attempt succeeds; only the swallow-and-pass form (a retry that re-raises on exhaustion is a sanctioned settle) |
| S16 | J4 | LOW | Call-verification as the sole oracle | The only check is that a collaborator was called, with no assertion on return value or state |
| S17 | J4 | HIGH | Exception-path oracle blindness | `pytest.raises(Exception)`/`toThrow()` with no type or message on a documented error contract; goes green when the exception came from arrange and the SUT never reached its raise |
| S18 | J3 | LOW | Contract-impossible stub value | An edge stub returns a value the real collaborator can never emit; the SUT handles an unreachable branch |
| S21 | J2 | LOW | Self-judging LLM/agent assertion | The oracle is a live model call (judge model, embedding similarity to a model-generated reference, agent grading its own transcript); circular |

(Rule text lightly compressed per row; names, judgments, and severities exact. S19/S20 do not exist in the catalog.)

Two S-codes deserve emphasis for an agent stack: **S14** (a snapshot of model output used as the expected value makes "green" mean "the model is unchanged", not "the output is right") and **S21** (an LLM judge grading its own system's output is a circular oracle). Both are failure modes specific to LLM-era test suites that no static scanner and no pre-LLM testing literature names.

### 4.5 Precision machinery: exemptions, precision rules, output contract

The look-alike exemptions, verbatim from `fragments/semantic-exemptions.md` (compressed here only by joining wrapped lines): do NOT flag a deliberately narrow unit test whose scope the spec confirms; a constant the spec genuinely endorses (not S3); a sanitizer test that already pairs negative with positive (not S11), **or** a filter whose contract is to drop the input entirely (blocklist sanitizer, guard returning empty, redactor suppressing the whole field), where empty output is correct and a positive assertion would contradict the design (not S11); a mock on a genuine external edge, DB/network/clock (not S12); a `spyOn` stubbing a *different* method than the one under test to isolate an orchestrator (not S12); a constructor-injected collaborator mock (not S12); a stub-config call on the mocking library that IS the SUT (not S5/S8); shared state reset by an autouse/`beforeEach` teardown (not S13); a structural/contract assertion on model output (valid JSON, required keys, cited source id, refusal on a banned prompt) or a mocked model returning fixture data (not S14); a sanctioned async-settling wait that still fails hard on timeout (not S15); a call-only assertion where the interaction IS the contract, or `assert_called_once_with` pinning specific arguments, or any call-verification paired with a return/state assertion (not S16); a `pytest.raises(SpecificError, match=...)` bound to the SUT line (not S17); a stub value the collaborator can actually return (not S18); tests under `*.problem.*`/`exercises/`/`katas/` paths, where the expected value is the teaching spec (not case 18/S3); a deterministic rubric, structural validator, or frozen human-labeled judge set rather than a live model verdict (not S21).

Precision-first rules, verbatim from `SKILL.md` (sourced from `fragments/precision-rules.md`):

> 1. Never report case 18 without citing an independent oracle.
> 2. If a mock replaces a network/disk/time dependency (an edge), it is NOT case 10. Case 10 applies only when the mock replaces the unit being tested.
> 3. A characterization test is not a bug even if the expected value looks wrong. Classify first (Step 3) before judging.
> 4. A test decorated with `@pytest.mark.skip`, `@pytest.mark.xfail(strict=True)`, or `@unittest.skip` that has no assertion body is NOT C2/C5... A plain `@pytest.mark.xfail` (no `strict=`) is exempt ONLY when the project turns on strict xfail globally... Check the pytest config (or a `conventions:` override) first.
> 5. In web/UI layer tests, a truthiness check on a response or locator object is NOT case 6. Presence of a response IS the assertion at that layer.
> 6. Tests decorated with `@given`, `@hypothesis`, or `@fuzz` that have no explicit `assert` are NOT C2. These frameworks generate and check assertions internally.
> 7. `expectTypeOf(v).toEqualTypeOf<T>()` in Vitest is a compile-time type assertion. Not C5. Do not flag it.

Plus three protocol-level precision rules from the same section, verbatim substance: the **tie-break** (when C9/C28/S17 would all fire on the same `pytest.raises`/`toThrow`, report only the most specific; a broad raises followed by an assertion on the bound message "fires NOTHING"); "**Severity is a ceiling, not a floor.** The severity listed for each code is the maximum. Intent classification (Step 3) can only LOWER it... It can never RAISE a code above its catalog severity"; and the closing rule of Step 6: "Use HIGH only when there is no plausible legitimate interpretation. Precision over recall: a wrong HIGH finding is worse than a missed LOW one."

Case-18 adversarial verify, verbatim from Step 5 and the multi-agent section: before reporting, (1) cite the independent oracle, and if you cannot, do not report; (2) "assume the expected value is correct and argue why. If the argument holds, withdraw the finding"; (3) report only when the oracle clearly contradicts and the adversarial argument fails. For high-stakes use, a two-pass form: Pass 1 (finder) reports with the cited oracle; Pass 2 (refuter) argues the expected value is correct (characterization? oracle authoritative for this test? domain convention?); "Report case 18 HIGH only when the refuter cannot mount a credible defense."

Finding output format, verbatim from Step 6:

```
{code} ({J}) - {confidence: HIGH | LOW} - {language} - {level: unit|integration|e2e|fixture} - {intent: spec|char|regression|behavior|scaffold}

Test: {function name, line range}
Finding: {one sentence describing what is wrong}
Evidence: {the specific line(s) that triggered this}
Oracle: {for case 18 only: cite the independent oracle}
Fix hint: {where and how to improve the code or test, one sentence}
```

followed by a SUMMARY block (`Tests reviewed: N / Findings: M (H high, L low) / Clean: N-M`). The CLI form emits JSON conforming to `schema/report.json`, with `--fail-on-high` wired for CI (exit 2).

### 4.6 The structural catalog (families, from `SKILL.md` Step 2 and `STATUS.md`)

Python families, verbatim code ranges: A, never checks (C1, C2, C2b, C2c, C3, C4, C4b, C20, C21, C38, C39, C43, C45, C49, C50, C51, C59, CC); B, weak/always-true (C5, C6, C6b, C6c, C7, C8, C8b, C9, C11a, C13, C13b, C14, C16, C18, C25, C34, C42, C44, C52, C55, C56, C57); C, checks own setup (C19, C28, C29, C48); D, external state (C17, C23, C24, C27, C30, C31, C32, C35); E, wrong thing (C33, C36, C37, C41); optional/diagnostic, opt-in only (C22, D1, D3-D8, M2). TS/JS adds the JS-series (JS1-JS13 in the summary table; `STATUS.md` states the JS codes run to JS31 in the full catalog) and Robot the R-codes (to R8b), plus project-layer PL codes. Totals from `STATUS.md`, verbatim: "**125 codes total**... `reference.md` is the superset of the deterministic scanners plus the semantic-only codes", enforced by `npm run validate` running `check-scanner-coverage.mjs`, "which fails if any scanner emits a code the catalog does not carry". Current version per `STATUS.md`: 0.7.0, npm `falsegreen-skill`, zero-dependency Node CLI, Node 18+.

The two decision records explain the architecture in one paragraph each. ADR 0001: the skill is defined by J1-J6; static scanners "answer the subset of those judgments that a parser can settle mechanically; the skill answers all six... The judgment set, not the language, is the contract." ADR 0002: "`reference.md` is the canonical superset. Every structural code that falsegreen, falsegreen-js, or robotframework-falsegreen emits must appear in `reference.md`, plus the AI-only semantic codes... `SKILL.md` is a subset of `reference.md`", with the honestly named gap that sibling-scanner enforcement "is a follow-up" because the siblings live in other repos.

### 4.7 Mode B (authoring) and Mode C (fix): the parts pass 1 never saw

Pass 1 described only detection. The artifact's other two modes are half its value.

Mode B's gate: Step A0 is an architect/QA triage (should a test exist at all; inverted-pyramid warning if E2E is requested where a unit test catches the defect; "The oracle is the one answer you must have: without it you can only freeze current behavior"). Step A1 elicits level, language, behavior + independent oracle, and doubled boundaries, skipping anything already supplied. Step A2 captures one language-neutral spec conforming to `schema/test-spec.json`; the canonical example, verbatim from `examples/authoring/apply-discount.spec.yaml`:

```yaml
level: unit
unit: apply_discount(price, rate)
scenario: a 15% discount on 200 returns 170
arrange:
  - price = 200
  - rate = 0.15
act: result = apply_discount(200, 0.15)
oracle:
  source: spec          # the expected value comes from the spec, NOT the code
  expected: "170 (200 minus 15% = 200 - 30)"
doubles: []             # pure function, nothing to double
languages: [Python, TypeScript, JavaScript, Robot]
```

and its Python render, verbatim from `examples/authoring/test_apply_discount.py`:

```python
# Rendered from apply-discount.spec.yaml (Mode B). Level: unit.
# Non-false-green: the expected value (170) comes from the spec, not the code.
from shop.pricing import apply_discount


def test_apply_discount_15_percent_on_200_returns_170():
    # spec: apply_discount(price, rate) returns price minus rate*price
    result = apply_discount(200, 0.15)
    assert result == 170          # J2 oracle: 200 - (200 * 0.15) = 170
```

Step A4 closes the loop: run Mode A on the generated test; in a host, "repeat until the analysis is clean and only emit a test that passes its own review"; the CLI bounds this to one revision and "if the test still trips a HIGH false-green finding it emits the draft with a FAILED verdict and exit 1, and if the self-check itself cannot run it reports UNVERIFIED and exit 3. The CLI never presents an unchecked or still-flagged test as verified." Level-specific oracle forms (Step A3): unit asserts the return value; integration/API asserts "status AND the response body (not status alone)"; integration/DB asserts "the persisted row, read back independently"; E2E asserts visible page state, where presence is the oracle.

Mode C's boundary, verbatim: "**the skill proposes the fix and the validation contract; it does not run the gate.**" The gate is F7 in `reference.md`, the bidirectional mutation gate, verbatim decision rule:

> Run the strengthened test twice:
> - **Clean replica** (code unmodified): the test must **pass**.
> - **Mutated replica** (the bug class reintroduced): the test must **fail**.
>
> Decision rule (fixed): **accept** only when `clean_replica = pass` AND `mutated_replica = fail`. Every other combination is **reject**: (pass/pass = still false-green, the mutant survives; fail/fail = test does not hold on clean code; fail/pass = inverted and broken.)

Two cost tiers: `suite-rerun` (cheap, coarse) and `targeted-mutation` (costlier, attributes the fail to this test and this mutant; "Use it when the finding blocks a deploy or is cited in a report"). Tooling is the host's: mutmut or cosmic-ray for Python, Stryker for JS/TS. The flaky case: a fix that is not stable in isolation on the clean replica is itself a J6 finding, verdict reject, "because the mutated-replica fail cannot be attributed to the mutation". Results are recorded in `schema/fix-validation.json`. The CLI exception (V1, Python/pytest only): `falsegreen-skill fix <test-file> --case <code> --line <n> --sut <file>` runs parse + preserve + a line-scoped mutation gate locally, "never auto-applies the patch and never edits the SUT"; without `--sut` or with `--cheap` it degrades to "propose-only / unvalidated and labels the output as not proven". Credit note in both files: the bidirectional gate is "the SENTINEL / Pizzini contribution credited in CREDITS.md".

Also explicit, verbatim from "What this skill does not do": it does not run the tests; it does not suggest code fixes unless asked; it does not flag maintainability smells by default (opt-in diagnostic codes only); in an editor host it does not run the Mode C gate.

### 4.8 Design invariants

1. One judgment set across all languages and both detector kinds: J1-J6 is the contract; scanners and the semantic skill are two implementations of subsets of it, and every finding from either layer names the judgment that failed.
2. Independence of the oracle is the master invariant (J2 + the oracle hierarchy): correctness may never be borrowed from the thing being tested, its output, its formula, its mocks, or (S14/S21) a model's own prior output or live self-judgment.
3. Precision over recall, mechanically enforced: severity is a ceiling, intent classification can only lower it, case 18 needs a cited oracle plus a failed refutation, and a wrong HIGH is defined as worse than a missed LOW.
4. The catalog is a governed superset: one canonical file (`reference.md`), machine-checked subset relations (`schema/code-catalog.json`, coverage scripts), and named enforcement gaps where automation does not yet reach.
5. Honest degradation everywhere: unchecked output is labelled FAILED or UNVERIFIED with distinct exit codes, never silently presented as verified; the skill states what it does not do in its own file.

### 4.9 What pass 1 missed or understated

- Pass 1's claim that "the full protocol lives partly in external docs" is **refuted at artifact level**: SKILL.md + reference.md + fragments + schemas + examples in this repo are the complete protocol (125 codes). This strengthens, not weakens, the ADOPT-CODE.
- Pass 1 saw only Mode A. Modes B and C (authoring against an elicited oracle with a self-review loop; fix proposals gated by a bidirectional mutation contract) are in the shipped artifact and are arguably the more adoptable halves for a stack that writes its own blocker tests.
- Pass 1 did not extract: the S-series at all (S14 and S21 are directly relevant to any suite that tests LLM outputs), the precision machinery (severity ceiling, tie-break, exemptions), the intent classification step, the level-detection precedence rule, or the F7 accept/reject table.
- Pass 1's "concrete falsifiable claim per finding" understates the mechanism: the falsifiability is procedural (oracle citation or no report; adversarial refutation for case 18), not just rhetorical.

### 4.10 Refined verdict

**ADOPT-CODE, strengthened.** The deeper read removes pass 1's only hedge (protocol partly external) and adds two adoption surfaces pass 1 did not know existed (Mode B authoring discipline and the F7 bidirectional gate contract, the latter being exactly the fail-direction proof a regression-blocker regime needs: a blocker is accepted only when it passes on clean code and fails on the reintroduced defect). Findings remain LLM judgments and need review in both directions, and the CLI's executable gate is Python/pytest-only in V1; neither caveat touches the protocol text, which is the primary artifact.

---

## 5. Cross-dive synthesis: what pass 2 changes

1. **The prompting corpus's most durable artifacts are procedures with a falsification step, not phrasings.** Denis v3's rubric loop, DAIR's APE loop, and falsegreen's Mode A/B/C all share one shape: generate, judge against an independently sourced standard, revise or reject. The phrasings (≥98 threshold, "Let's work this out...", prestige role lines) are the perishable parts in every source.
2. **Every source's evidence is weaker at artifact level than its reputation, except falsegreen.** Denis prints no baseline in either tested version; fainir's ratios are undefined names and its math is qualitative; DAIR's index contains two stub pages and an uncited tips page. Falsegreen is the inverse: the artifact is substantially *more* rigorous than its 2-star README impression (125 governed codes, ADRs, schemas, adversarial-verify procedure, honest CLI degradation).
3. **Two definitions must be written locally before the fainir ratios can be adopted** (proactive share; memory reuse rate), and the fainir taxonomy needs four repair mappings completed. Adoption cost for the fainir slivers is therefore "small design work", not "copy the checklist".
4. **S14 and S21 are new, named risks for this stack's own test suites** (snapshotted model output as oracle; live LLM judge as oracle) that appear nowhere in pass 1 and nowhere else in the corpus; they belong in any false-green audit of suites that test LLM-facing code.

## Coverage ledger

- DenisSergeevitch/chatgpt-custom-instructions: complete. All 3 text files read in full and quoted in full (repo also contains 3 chart images, not text-extractable and not load-bearing; the v3 numbers they plot are in the README table, which was extracted).
- fainir/most-capable-agent-system-prompt: complete for the tasked components. Full README read; verbatim extraction of the reader contract, success/momentum metrics, five queues, next-work rule, anti-stall rules, gap classification + repairs, self-improvement modes, loop-guard defaults, reliability conclusions, and the platform-specific framing. Compressed, noted in place: the harness-library catalogue, interface doctrine, company/science domain sections, and research appendix (design prose with no additional mechanisms beyond those extracted).
- dair-ai/Prompt-Engineering-Guide: all 19 English technique pages plus the general-tips page read in full; non-English editions (13 languages) not read, as they are translations of the same content. The guide's notebooks and applications pages were out of dive scope.
- vinicq/falsegreen-skill: root SKILL.md read in full; reference.md read for structure plus the case catalog, S-series framing, oracle hierarchy, and F7 in full (the per-language structural code definitions between those sections were sampled via the SKILL.md family tables and the 125-code catalog JSON rather than read line by line; total catalog size and family ranges are from STATUS.md and code-catalog.json); fragments, schemas (finding/test-spec/report/fix-validation by structure), STATUS.md, ADR 0001/0002, and the Python semantic + authoring examples read in full. The 48 KB `bin/falsegreen-llm.js` CLI implementation and the per-host context files (contexts/*.md, host SKILL.md variants) were inventoried but not read line by line; they are packaging of the same protocol.
- Unreachable: nothing. All four repos returned trees and raw files on 2026-10-31. One correction to pass-1-era assumptions: falsegreen-skill's default branch is `master`.
