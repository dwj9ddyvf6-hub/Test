# Cluster 4: Prompting and Custom Instructions

Research date: 2026-10-31. Method: live GitHub API metadata (api.github.com), README and key files via raw.githubusercontent.com, file-tree skim via the git/trees API. No code installed, cloned-and-run, or executed. All findings are judged from the actual files, not README marketing alone.

Reference stack for transfer judgments: file-based memory with nightly synthesis, a skills library of SKILL.md playbooks, scheduled cron/hook proactivity, a strict engineering doctrine (scope-first, proof-before-green, gate-wired regression blockers), and a personal trading book with its own memory system.

Traits used throughout: memory, initiation/proactivity, creativity, abstract thinking, conscientiousness, execution, intelligence, real-time.

---

## 1. DenisSergeevitch/chatgpt-custom-instructions (the substance repo)

| Field | Value |
|---|---|
| URL | https://github.com/DenisSergeevitch/chatgpt-custom-instructions |
| Description (API) | "My own Prompts for Custom instructions ChatGPT" |
| Stars / forks | 2,810 / 141 |
| Created | 2024-11-29 |
| Last push | 2026-03-14 |
| Archived | No |
| License | None declared in API (README says "Feel free to use and modify") |
| Default branch | main |
| Open issues | 7 |
| Size | 399 KB |

### What it is
A tiny repo (README.md, v1.md, v2.md, plus MMLU chart images) containing one evolving ChatGPT Custom Instructions text, in three versions, plus an Operator (browser-agent) instruction block in v2. There is no code. The instructions themselves are the entire substance, so they are extracted in full pattern form below.

### Mechanism, in plain terms, with the actual instruction patterns

**v3 (current, README.md).** Two tagged blocks the model must always follow:

1. `<self_reflection>` block (the core invention):
   - "Spend time thinking of a rubric, from a role POV, until you are confident"
   - "Think deeply about every aspect of what makes for a world-class answer. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but never show this to the user."
   - "Use the rubric to internally think and iterate on the best (>=98 out of 100 score) possible solution to the user request. IF your response is not hitting the top marks across all categories in the rubric, you need to start again"
   - "Keep going until solved with a best score"
   - README prose adds: while thinking, the model self-scores each rubric dimension 0-100 and rewrites if any dimension is weak.
2. `<answering_rules>` block:
   - Answer in the language of the user's message.
   - In the first message, self-assign a real-world expert role with a prestige credential ("I'll answer as a world-famous <role> PhD <detailed topic> with <most prestigious LOCAL topic REAL award>"), then act as that role.
   - Answer naturally and human-like, with concrete step-by-step detail.
   - Always use a fixed message structure: role line, then "**TL;DR**: ..." (skipped for rewriting tasks), then the step-by-step answer.
   - Defaults: no tables unless requested; no unsolicited actionable "what to do next" suggestions.
3. Version hygiene: v3 explicitly removed v1/v2 hacks that the author found empirically non-working, citing three SSRN papers: the "$1,000,000 tip" line, penalty threats, and the "I have no fingers, return the full code / no placeholders" trauma framing.

**v1/v2 (archived in v1.md / v2.md), for contrast.** Strict-order answering rules, ALL-CAPS imperatives ("You will be PENALIZED for wrong answers", "Your answer is critical for my career", the $1M tip), read-the-whole-history-first, abrupt-stop-on-character-limit with a user "continue" protocol, and "never use placeholders" for code. v2 claims ~7% MMLU improvement from ~$200 of testing on GPT-4o.

**Operator block (in v2.md).** Behavioral rules for a browser agent, and the most transferable part after the rubric:
   - Count each attempt to resolve a problem; after 3 consecutive failures on the same problem, web-search for a solution, then continue.
   - Never just click the first search result; consider more than one.
   - Write your own code before looking for someone else's.
   - Concrete UI hygiene rules (selection method, click-before-keys, close unneeded tabs, clipboard holds one value).

**Author's v3 evaluation (self-reported, in README):** MMLU-PRO on GPT-5 Nano (medium reasoning), 8,447/12,032 = 70.20% overall, with per-domain table (Math 86.75%, Law 46.78%). The author discloses an evaluation bug (the template's first-line TL;DR caused a subset of answers to be misclassified by the grader) and says a rerun is pending. Treat the number as a claim with a disclosed caveat, not as verified proof. No baseline figure is printed next to it in the README table itself.

### Trait map
- Intelligence: primary. Hidden rubric generation plus iterate-until->=98 is inference-time self-evaluation inside a single response.
- Conscientiousness: secondary. Fixed output structure, language matching, no-placeholder completeness (v1/v2), attempt-counting (Operator).
- Abstract thinking: mild. Role-POV rubric construction forces the model to define "what good is" for the domain before answering.
- Execution: mild, via the Operator 3-failures-then-search rule.
- Memory, initiation, creativity, real-time: not addressed, except "read the entire conversation history" in v1.

### Quality evidence
2,810 stars for a 3-file prompt repo is strong signal of perceived value. Maintained into the GPT-5 era (last push 2026-03-14, v3 aligned to OpenAI's GPT-5 prompting guide). The author spent real money on benchmark runs and, unusually, publishes what stopped working and removed it, with citations. Weaknesses: no license file, single author, benchmark is self-run and self-graded with a disclosed grader bug, no independent replication in the repo.

### Transferable value for this stack
- The hidden-rubric loop is the single most portable idea in this cluster: a per-task, role-specific 5-7 category rubric, scored 0-100 internally, with a rewrite trigger below a threshold. This stack already enforces quality externally (doctrine proof gates, regression blockers), but those gates check artifacts and code. A rubric pass is a cheap in-generation check for the large class of outputs no gate covers: analyses, summaries, research syntheses, recommendations. Adopt as a pattern inside relevant SKILL.md playbooks (e.g. "before delivering, score against these 5 criteria; revise any dimension under X"), not as a global always-on instruction, because rubric generation costs thinking tokens on every trivial reply too.
- The Operator 3-consecutive-failures rule maps directly onto this stack's existing anti-spiral doctrine (revise hypothesis after repeated same-class failure). The repo's version is simpler and cruder: count attempts, at 3 search externally, then continue. Already substantially covered; the count-and-escalate-explicitly framing is a useful wording tightening.
- The negative findings are as valuable as the positives: tip/penalty/career-pressure lines and "no fingers" framing are dead weight per the author's cited studies. Any legacy prompts in this stack carrying emotional-pressure lines can be deleted with evidence behind the deletion.
- Structure defaults (TL;DR first, no tables unless asked, no unsolicited next-steps) are user-preference settings, not intelligence gains; this user already has stronger, personal versions of these in standing instructions.

### Risks
- Platform lock-in: written for ChatGPT web's Custom Instructions field and Operator; the text transfers, the delivery mechanism does not.
- The ">=98/100 or start again" loop is unbounded in the original; in an agent with tool costs it needs a retry cap or it becomes a token furnace.
- Role self-assignment with a fabricated prestige credential is a persona flourish that can read as false authority if surfaced verbatim in user-facing output.
- No license file: reuse is invited in the README but not legally formalized.

### Verdict: ADOPT-IDEA
Adopt the hidden-rubric self-scoring pattern (bounded, per-playbook) and the negative-results cleanup. The doctrine and gates already cover the Operator retry idea in stronger form (ALREADY-HAVE for that part).

---

## 2. taishi-i/awesome-ChatGPT-repositories (the index repo, also mined below)

| Field | Value |
|---|---|
| URL | https://github.com/taishi-i/awesome-ChatGPT-repositories |
| Description (API) | "A curated list of open source GitHub repositories related to ChatGPT, the OpenAI API, and Codex. Searchable via Claude Code and Codex skills." |
| Stars / forks | 3,336 / 529 |
| Created | 2023-04-02 |
| Last push | 2026-10-29 |
| Archived | No |
| License | CC0-1.0 |
| Default branch | main |
| Open issues | 83 |
| Size | 34,719 KB |

### What it is and mechanism
A curated awesome-list of ~2,500+ ChatGPT/OpenAI-ecosystem repos. The README alone is 493 KB; the machine-readable index is `awesome-ChatGPT-repositories.json` (4.0 MB). The interesting mechanism, found in the file tree rather than the list itself, is that the list now ships as an agent-searchable skill:

- `skills/awesome-chatgpt-search/SKILL.md` (15.4 KB) plus a duplicated plugin copy under `plugins/awesome-chatgpt-search/`, a Claude Code command (`.claude/commands/awesome-chatgpt.md`), and a Codex entry point (`.agents/skills/awesome-chatgpt/SKILL.md`) that defers to the same search skill.
- Data is pre-split into per-category JSON files (prompts, chatbots a/b, CLIs a/b, langchain, NLP a/b, openai a/b, others a/b, browser-extensions a/b, awesome-lists, reimplementations, tutorials, unity). Each record is one JSON object with compact fields: `u` URL, `n` name, `d` description, `c` category, `l` language, `t` topics, `sc` quality score 0-8, `st` star count, `ns` normalized star score.
- The SKILL.md instructs the agent to grep the minimum category files with stemmed keywords (3-6 keywords, stems like `retriev`, `generat`), rather than loading the corpus, explicitly to keep token use low.
- Ground rules in the skill are strict and notable: present only repos from the bundled data (never fill gaps from memory or web), copy names/URLs/star counts exactly as recorded, treat the curated snapshot as the source of truth, keep fixed output templates, and if the data files cannot be read, say so and link the repo instead of substituting other sources.

### Trait map
- Memory (external/catalog memory): primary. A large curated corpus made cheaply retrievable at inference time.
- Intelligence: secondary. Stemmed-keyword routing and category pre-filtering are retrieval discipline.
- Conscientiousness: secondary. The "only from the data, copy exactly, admit when unreadable" rules are anti-hallucination guardrails.
- Execution: mild. One skill works across Claude Code, Codex, and generic agents via thin per-platform entry points pointing at one canonical SKILL.md.

### Quality evidence
Actively maintained (pushed 2026-10-29, two days before this inspection), 3,336 stars, CC0. The skill/plugin packaging is recent and deliberate, with the same skill maintained in three locations (a drift risk the repo accepts). Star counts inside the data are snapshots and include duplicates across categories (the same repo appears in multiple category files, verified during mining: e.g. langflow and opencompass appear twice), so the "2,500+" count overstates unique repos; the 7 files sampled for this cluster held 1,221 records including duplicates.

### Transferable value for this stack
- The pattern, not the list, is the prize: a large reference corpus split into greppable per-category JSONL-style files, a thin SKILL.md with stemmed-keyword search discipline, exact-copy rules, and a fail-closed fallback. This stack's skills library could use the same treatment for any future large catalog (vendor/teardown indexes, sleeve catalogs) instead of loading whole indexes into context.
- The one-canonical-skill, many-thin-entry-points layout is a clean way to expose the same capability to different agent surfaces without forking content.
- The list itself is a mining source (used for sections 3-8 below), not a runtime dependency.

### Risks
- Snapshot staleness: star counts and even repo existence in the data lag reality (one mined entry had moved owners; see optillm in the coverage ledger). Any use must re-verify against the live API, exactly as done here.
- Duplicated skill copies inside the repo can drift.
- CC0 list content is fine to reuse; the repos it points to carry their own licenses.

### Verdict: ADOPT-IDEA (pattern) / REFERENCE (list itself)
Adopt the greppable-catalog-as-skill pattern for future large indexes. Keep the list as a reference mining source only; never trust its snapshots without live re-verification.

---

## Mined entries from awesome-ChatGPT-repositories

Selection rule applied: highest-star / highest-quality entries whose mechanism enhances a trait in a way not already covered by the two repos above or by this stack's existing systems. Six were inspected properly (live API metadata, README, tree skim). Star counts below are live API values from 2026-10-31, which differ from the list's snapshots; both are noted where the gap matters.

---

## 3. dair-ai/prompt-engineering-guide (mined: Prompts)

| Field | Value |
|---|---|
| URL | https://github.com/dair-ai/prompt-engineering-guide |
| Live stars / forks | 79,699 / 8,750 (list snapshot said 74,000) |
| Last push | 2026-03-11 |
| Archived | No |
| License | MIT |
| Description | "Guides, papers, lessons, notebooks and resources for prompt engineering, context engineering, RAG, and AI Agents." |

### Mechanism
Not software: a canonical technique curriculum. The file tree (`pages/techniques/`) enumerates the field's named techniques, verified from its `_meta.en.json`: zero-shot, few-shot, chain-of-thought, meta-prompting, self-consistency, generate-knowledge, prompt chaining, Tree of Thoughts, RAG, automatic reasoning and tool-use (ART), Automatic Prompt Engineer (APE), Active-Prompt, Directional Stimulus Prompting (DSP), Program-Aided Language Models (PAL), ReAct, Reflexion, multimodal CoT, graph prompting. Each technique gets a page with the source paper and worked examples, in 13 languages.

### Trait map
Intelligence and abstract thinking (primary): this is the menu of reasoning scaffolds. Reflexion and self-consistency also touch conscientiousness.

### Quality evidence
79.7k stars, MIT, maintained (though the last push is 7 months old, the content is reference material that ages slowly), 3M+ learners claimed by the project, published by DAIR.AI.

### Transferable value
This stack already uses CoT-style reasoning, ReAct-style tool loops, retrieval, and self-reflection (via doctrine). The genuinely uncovered items are the named, citable ones a playbook author can lift precisely:
- APE (Automatic Prompt Engineer): generate candidate instructions, score them on examples, keep the best. Directly applicable to improving SKILL.md playbooks empirically instead of by feel.
- Active-Prompt: select few-shot examples by model uncertainty (disagreement across samples) rather than by intuition.
- Generate Knowledge: have the model write down relevant facts first, then answer conditioned on them. Useful for domain reads where retrieval is thin.
- PAL: offload arithmetic/logic to code execution instead of mental math.
- DSP: a small "stimulus" hint steers a frozen model toward a task framing.
Verdict rationale: the repo is a textbook; you do not adopt a textbook, you cite it when writing playbooks.

### Risks
Low. Content risk only: some techniques are superseded by native reasoning models, and the guide now funnels readers toward paid courses. No code risk; nothing to run.

### Verdict: REFERENCE
Keep as the citable source when a SKILL.md needs a named technique (APE and Active-Prompt are the two with real headroom for this stack).

---

## 4. promptfoo/promptfoo (mined: Prompts / evaluation)

| Field | Value |
|---|---|
| URL | https://github.com/promptfoo/promptfoo |
| Live stars / forks | 26,669 / 2,621 (list snapshot said 21,000) |
| Last push | 2026-10-31 (same day as inspection) |
| Archived | No |
| License | MIT |
| Description | "Test your prompts, agents, and RAGs. Red teaming / vulnerability scanning for AI. Declarative configs, CLI and CI/CD integration. Used by OpenAI and Anthropic." README notes Promptfoo is now part of OpenAI, remaining MIT open source. |

### Mechanism
A CLI/library that treats prompts like code under test: declarative YAML configs declare providers (models), prompts, test cases with assertions (deterministic checks plus LLM-graded rubrics), and run a comparison matrix; `promptfoo eval` executes, `promptfoo view` shows results. It integrates with CI/CD, compares models side by side, and includes a red-teaming mode that generates adversarial cases (injection, leakage, jailbreak classes) and scans for vulnerabilities. The repo itself ships agent skills for eval authoring (`.claude/skills/promptfoo-evals/SKILL.md`, verified in tree).

### Trait map
Conscientiousness (primary): prompts get regression tests. Execution (secondary): CI gating for prompt changes. Intelligence: only indirectly, via model/prompt comparison data.

### Quality evidence
26.7k stars, pushed today, MIT, used by both major labs per its own description, active Discord and release cadence. Acquisition by OpenAI is a continuity signal and a roadmap-capture risk at once.

### Transferable value
This stack's doctrine already demands regression blockers for code and state invariants, wired into a gate. Prompts and SKILL.md playbooks are the one artifact class that currently changes without an equivalent eval harness: a playbook edit is judged by feel. promptfoo's model, declarative test cases plus assertions plus a graded rubric plus CI gating, is the missing blocker pattern for prompts. The transferable unit is the pattern: a small fixed eval set per important skill (inputs, expected properties, rubric grader), run before a revised playbook ships, with regressions blocking. The red-team case generation is also directly relevant to an agent that reads untrusted web and message content: a standing adversarial prompt suite for the agent's own instruction stack.

### Risks
- Toolchain weight: Node CLI plus provider API keys for graders; adopting the code is a new dependency for a benefit the pattern alone mostly delivers.
- LLM-graded assertions can be flaky and cost money per run; needs small, stable eval sets.
- OpenAI ownership may steer provider support over time (MIT license limits the damage).

### Verdict: ADOPT-IDEA
Adopt declarative prompt/skill regression evals (promptfoo's config shape is the template) as the blocker pattern for SKILL.md changes. Do not install the tool under this research pass; if the pattern proves wanted, evaluate the code separately.

---

## 5. optillm (mined: Prompts / inference optimization) — note the redirect

| Field | Value |
|---|---|
| URL (current) | https://github.com/algorithmicsuperintelligence/optillm |
| URL in awesome-list | https://github.com/codelion/optillm (old owner; API lookup under that name returned no repo record on 2026-10-31, the project now lives under the organization above) |
| Live stars / forks | 4,333 / 397 |
| Last push | 2026-10-31 |
| Archived | No |
| License | Apache-2.0 |
| Description | "Optimizing inference proxy for LLMs" |

### Mechanism
An OpenAI-API-compatible proxy that wraps any model call with one of 20+ inference-time techniques, selected by a slug prefix on the model name or an `optillm_approach` field, verified from the README's technique table: best-of-N sampling, self-consistency, majority voting (k=6), mixture-of-agents (multiple critiques merged), MCTS search, prover-verifier game, chain-of-code, CoT-with-reflection (explicit thinking/reflection/output sections), LEAP (learns task-specific principles from few-shot examples, including from errors), plansearch, rstar, and CePO (a composite: best-of-N + CoT + self-reflection + self-improvement). A router variant picks the technique per request with a small classifier model. No training; the gains come from spending more inference compute per answer. README claims 2-10x accuracy improvements on reasoning tasks; that range is the project's claim, not verified here.

### Trait map
Abstract thinking and intelligence (primary): search, sampling, and verification at inference time. Creativity (mild): mixture-of-agents and best-of-N diversify candidate generation before selection.

### Quality evidence
4.3k stars, Apache-2.0, pushed the day of inspection, PyPI package with production users claimed. Smaller and younger than the other mined entries; the headline multiplier is self-reported.

### Transferable value
This stack cannot insert a proxy into its own model serving, so the code does not transfer. The technique menu does, as orchestration patterns the agent can perform itself on hard problems:
- Best-of-N + verifier for high-stakes single answers (generate several candidate plans/analyses, score against explicit criteria, ship the best) — a multi-sample cousin of the Denis rubric loop in section 1.
- Majority voting / self-consistency for factual or classification calls where samples are cheap.
- LEAP is the sleeper: extract explicit principles from a handful of worked examples (including failures) and prepend them as task rules. That is exactly how this stack's playbooks could be improved from logged failures, in miniature, without a full eval harness.
- CePO's lesson is compositional: the wins come from stacking generate + reflect + verify, not from any single trick.

### Risks
- Latency and cost multiply per call; indiscriminate use is a token furnace (same rail as section 1).
- Proxy architecture is a non-fit; any adoption is pattern-level only.
- Self-reported benchmark multipliers should not be quoted as expectations.

### Verdict: ADOPT-IDEA
Adopt best-of-N-with-verifier and LEAP-style principle extraction as named patterns for hard tasks. Skip the proxy code (architecture mismatch, not quality).

---

## 6. kyegomez/tree-of-thoughts (mined: Prompts / reasoning)

| Field | Value |
|---|---|
| URL | https://github.com/kyegomez/tree-of-thoughts |
| Live stars / forks | 4,593 / 373 (list snapshot said 4,600) |
| Last push | 2026-09-29 |
| Archived | No |
| License | Apache-2.0 |
| Description | "Plug in and Play Implementation of Tree of Thoughts: Deliberate Problem Solving with Large Language Models" (the original paper implementation is princeton-nlp/tree-of-thought-llm, linked from this README) |

### Mechanism
Implements the Tree of Thoughts paper (arXiv 2305.10601) as a searchable reasoning loop, verified from README and tree: generate `num_thoughts` candidate next steps from a node (propose or sample mode), evaluate each 0-1 (value scoring or comparative voting), search breadth-first with a beam or depth-first with backtracking, prune below a value threshold, then answer from the best path. All model outputs are function calls validated against Pydantic schemas. The paper's headline result, quoted in the README: GPT-4 with chain-of-thought solved 4% of Game of 24 puzzles; with ToT, 74%. The repo now ships as part of the author's Swarms framework (`pip install swarms`), with worked examples (logic grids, physics, Frontier Math) and a `prompts/` folder of expert-persona prompt templates.

### Trait map
Abstract thinking (primary): explicit search over reasoning paths with backtracking, instead of one linear chain. Creativity (secondary): branching candidate generation is structured divergent thinking with a pruning rule.

### Quality evidence
4.6k stars, Apache-2.0, pushed about a month before inspection. The underlying paper is well known and peer-discussed; this particular implementation is one author's port now folded into his broader framework, which is a maintenance-coupling risk. The "elevates reasoning by at least 70%" line in the repo description is marketing phrasing of the Game of 24 result, not a general claim anyone should rely on.

### Transferable value
Narrower than optillm's menu but deeper on one point this stack can use: for genuinely combinatorial or backtracking-prone problems (schedule construction under constraints, debugging with branching hypotheses, plan search), an explicit generate-score-prune-backtrack loop, performed by the agent across subagent branches or sequential passes, beats a single chain. This stack's workflow engine already provides the branching substrate; ToT supplies the discipline (score partial states, prune, backtrack) that plain fan-out lacks. The prompts/ folder templates (step-by-step experts, collaborative experts, iterative refinement) are minor and largely covered by existing playbook style.

### Risks
- Code adoption drags in the Swarms framework; disproportionate for one algorithm.
- Search multiplies model calls; only worth it where a wrong single-pass answer is expensive.
- Single-author ecosystem with heavy self-promotion; prefer the paper (and the Princeton implementation) as the reference.

### Verdict: ADOPT-IDEA (bounded) / SKIP code
Adopt ToT discipline for named hard-problem classes only. Reference the paper, not this repo's code.

---

## 7. assafelovic/gpt-researcher (mined: Others / autonomous research agent)

| Field | Value |
|---|---|
| URL | https://github.com/assafelovic/gpt-researcher |
| Live stars / forks | 30,402 / 4,164 (list snapshot said 27,000) |
| Last push | 2026-10-10 |
| Archived | No |
| License | Apache-2.0 |
| Description | "An autonomous agent that conducts deep research on any data using any LLM providers" |

### Mechanism
A planner/executor/publisher agent pipeline for deep research, verified from README and tree: a planner agent decomposes a query into research sub-questions; parallel execution agents retrieve from web and local documents per question; a "Jev" smart context-filtering step keeps only context useful for each question (embedding-free by default); an aggregator/publisher synthesizes a cited report (2,000+ words, exportable to PDF/Word). Recursive "deep research" mode explores breadth and depth trees of sub-questions. It ships multi-agent variants, MCP support, and its own agent skill files (`.claude/SKILL.md` plus references, verified in tree).

### Trait map
Initiation/proactivity (primary): given one query, it self-decomposes and runs a whole research program without further prompting. Real-time (secondary): live web retrieval is integral, not bolted on. Execution (secondary): parallel retrieval with context budgeting.

### Quality evidence
30.4k stars, Apache-2.0, actively maintained, PyPI and Docker distribution, large community. The most substantial working system among the mined entries.

### Transferable value
Mostly ALREADY-HAVE: this stack already runs exactly this shape through workflow-orchestrated subagents (decompose, fan out researchers, synthesize), with stricter evidence rules. Two refinements are not yet standard here and are worth lifting:
- A named context-filtering step between retrieval and synthesis, with an explicit keep/drop judgment per source against the specific sub-question (their Jev step). This stack's research passes filter informally; making it a distinct, logged step improves synthesis quality and auditability.
- Recursive breadth/depth deep-research mode as a named escalation pattern: when a first pass shows the question is wider than scoped, expand the question tree deliberately rather than widening ad hoc.

### Risks
- Adopting the code would duplicate the existing subagent/workflow machinery with a second, less-governed research stack (a second source of truth; doctrine forbids the workaround pattern).
- Autonomous web research without this stack's citation and coverage-ledger rules can produce fluent, weakly-sourced reports; its defaults are looser than this stack's doctrine.

### Verdict: ALREADY-HAVE (equivalent: workflow/subagent research pipeline), with ADOPT-IDEA for the explicit context-filter step
Name the equivalent plainly: this stack's multi-agent research workflows already implement planner/executor/synthesizer. Lift the Jev-style filter step only.

---

## 8. langfuse/langfuse (mined: Prompts / observability and prompt management)

| Field | Value |
|---|---|
| URL | https://github.com/langfuse/langfuse |
| Live stars / forks | 36,796 / 4,130 (list snapshot said 27,000) |
| Last push | 2026-10-31 (same day as inspection) |
| Archived | No |
| License | NOASSERTION via API (repo README badge states MIT for the core; some enterprise features are separately licensed, per project convention) |
| Description | "Open source agent evals & observability: Trace, evaluate, and improve LLM applications with one open platform." |

### Mechanism
A self-hostable platform (built on ClickHouse) with four coupled parts, verified from README: tracing/observability for every LLM call and agent action in a session; prompt management (prompts as versioned, centrally managed artifacts with caching, iterated without redeploying code); evaluations (LLM-as-a-judge, code evaluators, user feedback, manual labeling, custom pipelines); and datasets for benchmark/test-set runs across prompt or model versions.

### Trait map
Conscientiousness (primary): every call traced, every prompt versioned, quality scored continuously. Memory (secondary, organizational): traces and datasets are a queryable history of what the system actually did and how well.

### Quality evidence
36.8k stars, pushed today, YC-backed company behind it, very active. The heaviest infrastructure in this cluster by far.

### Transferable value
The platform does not fit this stack's architecture (a file-and-skills agent, not an instrumented LLM app with a serving layer), and self-hosting ClickHouse-backed observability to watch a personal agent is disproportionate. Two ideas transfer cheaply:
- Prompts as versioned artifacts with changelogs: SKILL.md files already live in version control here, so this is mostly ALREADY-HAVE; the gap langfuse highlights is linking a prompt version to measured outcomes on a fixed dataset — which is precisely the promptfoo pattern in section 4. Take the idea from there, not from here.
- LLM-as-a-judge scoring on sampled real outputs (not just fixed test sets) as a periodic quality audit of the agent's own deliverables. This stack grades its trading record rigorously; a lightweight sampled-output grading pass for research/report quality is the analogous habit, implementable with existing synthesis machinery.

### Risks
- Infrastructure weight and a second data store for traces (which would contain sensitive personal context; self-hosting mitigates but does not erase the exposure surface).
- License is mixed (open core plus enterprise parts); the API's NOASSERTION reflects that.
- Platform gravity: prompt management wants prompts to live in langfuse, which conflicts with this stack's files-as-source-of-truth rule.

### Verdict: REFERENCE
Reference for the prompt-version-to-outcome linkage idea; do not adopt the platform. The actionable half of its value is already captured by the promptfoo verdict above.

---

## Cluster summary: ranking by transferable value

1. **DenisSergeevitch hidden-rubric self-reflection (ADOPT-IDEA)** — highest value per unit effort in the cluster. A bounded rubric-and-rescore pass upgrades every ungated prose deliverable, costs nothing but thinking tokens, and its companion negative results (tip/penalty/pressure lines do not work) clean up legacy prompting debt with citations.
2. **promptfoo's declarative prompt-eval pattern (ADOPT-IDEA)** — fills the one real hole in this stack's blocker law: SKILL.md playbooks currently change untested. A small fixed eval set per important skill, gated like code blockers, is a direct doctrine extension. Its red-team generation also hardens an agent that ingests untrusted content.
3. **optillm's technique patterns (ADOPT-IDEA)** — best-of-N with a verifier for high-stakes answers, and LEAP (extract principles from worked failures) as a lightweight playbook-improvement loop. CePO's composition lesson (generate + reflect + verify) reinforces finding 1.
4. **taishi-i's catalog-as-skill pattern (ADOPT-IDEA / REFERENCE)** — greppable per-category data files plus a strict exact-copy SKILL.md is the right shape for any future large index this stack maintains; the list itself is a mining source whose snapshots must always be re-verified live.
5. **gpt-researcher's context-filter step (ALREADY-HAVE + one idea)** — the planner/executor/publisher pipeline already exists here as workflows; making retrieval-to-synthesis filtering an explicit logged step is a genuine small upgrade.
6. **Tree of Thoughts discipline (ADOPT-IDEA, bounded)** — real but narrow: score-and-prune branching for combinatorial problems only. Cite the paper; skip the Swarms-coupled code.
7. **dair-ai Prompt Engineering Guide (REFERENCE)** — the technique canon. APE and Active-Prompt are the two entries with actual headroom for playbook authoring; the rest is already in use or superseded by reasoning models.
8. **langfuse (REFERENCE)** — sound ideas (versioned prompts tied to measured outcomes, sampled-output judging) that are either already-have here or better obtained via finding 2. Platform adoption would violate the files-as-source-of-truth and minimum-sufficient-change rules.

Cross-cluster note: this cluster's center of gravity is conscientiousness and intelligence, applied at the level of individual responses and prompts. It contains nothing that improves long-term memory, scheduled proactivity, or real-time data access beyond what the reference stack already has; gpt-researcher's proactivity is task-scoped autonomy, not standing initiation.

## Coverage ledger

Inspected properly (live API metadata + README + tree skim): 
- DenisSergeevitch/chatgpt-custom-instructions (all three versions read in full; they total ~10 KB)
- taishi-i/awesome-ChatGPT-repositories (metadata, tree, both SKILL.md variants, and 7 of its per-category data files: prompts, langchain, openai a/b, others a/b, tutorials — 1,221 records parsed for mining)
- dair-ai/prompt-engineering-guide (plus its techniques index file)
- promptfoo/promptfoo
- algorithmicsuperintelligence/optillm
- kyegomez/tree-of-thoughts
- assafelovic/gpt-researcher
- langfuse/langfuse

Redirected:
- codelion/optillm (as listed in the awesome-list data) returned no repo record from the API on 2026-10-31; the project was located at algorithmicsuperintelligence/optillm and inspected there. Recorded as a redirect, not a failure of the project.

Unreachable: none. All eight target repos returned live API metadata and readable READMEs.

Not claimed: the awesome-list's remaining ~19 category data files and its full 493 KB README were not read end to end; mining covered the seven category files most relevant to the eight traits (prompts, langchain, openai, others, tutorials). Entries in categories not sampled (chatbots, browser extensions, CLIs, NLP, unity, reimplementations, awesome-lists) were excluded by scope, and no claim is made about them.
