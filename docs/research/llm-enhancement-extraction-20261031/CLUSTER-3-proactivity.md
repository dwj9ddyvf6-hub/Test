# Cluster 3: Proactivity and Initiation

Date inspected: 2026-10-31
Method: live GitHub API metadata via `curl api.github.com/repos/<owner>/<repo>`, README via `raw.githubusercontent.com`, file trees via `git/trees/HEAD`, and key source files read raw. No code installed, cloned-and-run, or executed. Judgement from actual files where the mechanism matters, not README marketing alone.
Target stack for transfer judgement: file-based memory with nightly synthesis, a skills library of `SKILL.md` playbooks, scheduled cron / hook proactivity, a strict engineering doctrine (scope first, proof before green, regression blockers), and a personal trading book with its own memory system.

Cluster thesis in one line: the hard problem is not generating a proactive suggestion, it is deciding whether to surface it at all. Every credible system in this cluster converges on a gate between sensing and acting, and on pricing the interruption, not just the suggestion.

---

## 1. thunlp/ProactiveAgent

### Metadata

| Field | Value |
|---|---|
| Repo | thunlp/ProactiveAgent |
| Description | "A LLM-based Agent that predict its tasks proactively." |
| Stars / Forks | 684 / 63 |
| Created | 2024-09-19 |
| Last push | 2026-05-12T08:51:07Z |
| Archived | false |
| License | Apache-2.0 |
| Language | Python |
| Default branch | main |
| Paper | arXiv 2410.12361, ICLR 2025 |

### What it is

A research system from Tsinghua NLP for a desktop agent that watches what the user is doing and offers help unprompted, plus the full apparatus around it: a synthetic data-generation gym, a human-annotated benchmark (ProactiveBench, 6,790 events), a separate reward model that judges whether a proposed intervention should have been offered, fine-tuned 7-8B models, and a runnable Windows / macOS demo that pops a toast.

It is a paper repo, not a product. That matters for the verdict.

### Mechanism in plain terms

Verified in `agent/prompt.py`, `agent/ragent.py`, `agent/README.md`, `gym/components/activeagent.py`, `gym/components/reward.py`, and the tree:

1. Sensing. ActivityWatch buckets plus `pynput` keyboard / mouse capture, a Chrome extension (tabs, page HTML), and a VS Code extension (project, language, current file). The `ActionListener` splices these into an event stream and drops periods where the user is not focused on Chrome or VS Code. AFK bucket tells it if the user is idle.
2. Proposal on a timer. Every interval (default 15 seconds, `ragent.py --interval`) the LLM receives the aggregated event history and must return strict JSON: `Purpose`, `Thoughts`, `Proactive_Task` (or literal `null`), `Response`, `Operation`. The null case is a first-class, instructed output: "Only propose assistance when you fully understand the user's actions" and "Set Proactive_Task to null if no assistance is needed."
3. Reward gate. A separate fine-tuned reward model, trained on human accept / reject labels, judges the proposed task before or alongside surfacing. In the Gym loop (`gym/components/activeagent.py`) a rejected proposal is fed back with the judge's thought and the agent must produce a *different* prediction, up to 3 retries at higher temperature. README reports reward-model F1 0.918, accuracy 0.9167 on the test set, versus GPT-4o at F1 0.67 on the same judgement task. The general models failed specifically on False-Alarm detection (GPT-4o scored 0.0 on that slice in their table).
4. Human feedback as three distinct signals. Accept (click toast body): execute the operation. Reject (dismiss): try a different approach next turn. Ignore (do nothing): the toast times out and the prompt instruction is to propose less in following turns, interpreted as "user is busy." The system prompt in `agent/prompt.py` encodes all three explicitly, plus "even if the user accepts, do not propose related tasks in the next turn."
5. Gym for training data. `gym/` is an Environment Gym with three simulated components: Environment, Proactive Agent, Reward Model, plus a simulated User. It generates event sequences where user feedback affects later events, producing the training set used to fine-tune Llama-3.1-8B and Qwen2-7B into "Proactive" variants.

Results that bound the claim: even the fine-tuned models reach only F1 66.47% (Qwen2-7B-Proactive) and 66.25% (Llama) on ProactiveBench, with precision about 49.8% and a false-alarm rate still about 50%. Base GPT-4o: recall 98.1%, precision 48.2%, false-alarm 51.9%. In plain terms, an ungated frontier model wants to help almost always and is wrong about half the time. Fine-tuning mainly buys a small precision gain, not a solved gate.

### Trait map

- Primary: initiation / proactivity
- Secondary: real-time (continuous sensing loop), conscientiousness (the reward gate is a restraint mechanism), execution (operation selection after acceptance)

### Quality evidence

684 stars is modest but real for a niche ICLR paper repo. 63 forks. Last push 2026-05-12, so maintained into 2026 but on a research cadence, not a product cadence. Model release 2025-03-21 on Hugging Face. 7 open issues. Apache-2.0 is clean. The evaluation is unusually honest: they publish the false-alarm rates that make their own system look weak, and they built a dedicated human-labelled test set instead of only reporting training metrics.

Weaknesses: the demo is desktop-toast and ActivityWatch-specific, Windows / macOS only, Chrome + VS Code only. The "connect the reward model" section of the README still says "TO BE UPDATE." The live demo and the benchmark are different things: the benchmark gains do not prove the toast demo is usable day to day.

### Transferable value for the target stack

High as ideas, low as code.

- The explicit null action plus a separate judge is directly transferable to cron / hook proactivity. The target stack already fires on schedules and events; what it lacks, by comparison, is a cheap second pass whose only job is "should this surface at all, given recent dismissals and current focus," scored separately from the generator. ProactiveAgent proves that job is learnable / promptable separately and that general LLMs are specifically bad at the false-alarm slice without it.
- The three-way feedback taxonomy (accept / reject / ignore-means-busy, with different policy consequences for each) maps cleanly onto any notification or suggestion surface. Ignore is not a weak reject; in their design it throttles rate. That is a concrete policy rule worth copying verbatim in spirit.
- The four evaluation cells, Missed-Needed / Non-Response / Correct-Detection / False-Alarm, are a better scorecard for proactive behaviour than "suggestions sent." A proactive lane should be graded on false alarms and missed needs separately, because optimising only for helpfulness drives false alarms to about 50%.
- The retry-with-rejection-reason loop in the Gym (judge thought fed back, must propose something different, bounded retries) is a reusable pattern for any gated suggestion pipeline, including trading-book alerts where a rejected framing should not simply repeat.

What does not transfer: ActivityWatch screen/keyboard surveillance (privacy cost, wrong surface for a chat / cron agent), the toast UX, and fine-tuning a 7B model for this one task when a prompted gate plus logged feedback gets most of the structure.

### Risks

- Abandonment: medium-low. Research repo, may go quiet after the paper cycle, but the artefacts (data, prompts, benchmark) remain usable.
- Privacy / security if code were adopted: high. Continuous keyboard, browser HTML, and workspace capture is a large attack and leakage surface. Research-only inspection avoids it; any real adoption of the sensing layer would need a separate ruling.
- Hype: low. Their own numbers undercut hype.
- Platform lock-in: none. Apache-2.0, local models available.

### Verdict

**ADOPT-IDEA** — adopt the gated-proposal architecture (explicit null, separate reward/judge pass, accept/reject/ignore with distinct policy effects, false-alarm as a headline metric). Do not adopt the code or the sensing layer.

---

## 2. tao-hpu/awesome-proactive-agents (the list itself)

### Metadata

| Field | Value |
|---|---|
| Repo | tao-hpu/awesome-proactive-agents |
| Description | "When should an always-on agent intervene? A field map of proactive AI assistance: signals, decision, action, memory, evaluation & self-improvement." |
| Stars / Forks | 7 / 1 |
| Created | 2026-07-13 |
| Last push | 2026-10-16T04:30:39Z |
| Archived | false |
| License | None in GitHub API; README footer states CC0 |
| Language | Python (the pilot) |
| Tree | README.md, README.zh-CN.md, pilot/pilot.py, pilot/README.md, pilot/results.txt |
| Companion | Survey: "When Should the Agent Speak? A Survey of Intervention Timing for Always-On AI Assistants," TMLR 2026, OpenReview forum b0yKEdAXEr |

### What it is

Not a conventional awesome list. It is a field map organised around a single decision rule, companion to a TMLR 2026 survey, with a small deterministic pilot program that actually scores intervention policies. The star count (7) radically understates its value for this cluster; it is three months old and written by one maintainer at FIM Labs.

### Mechanism in plain terms

Verified in the full README and in `pilot/pilot.py` read in full:

The organising thesis, stated as an inequality:

```
intervene iff E[benefit of acting] - E[cost of interrupting] > theta
```

Every entry is placed by which term of that inequality it advances, across five layers:

1. Signals: what to watch (gaze, scene change, temporal context, user behaviour, egocentric video).
2. Decision: when to act (the core layer, with two lineages deliberately reconnected: the 1999-2017 decision-theoretic notification literature, Horvitz and successors, and the 2024- LLM-era work).
3. Action: what to do (GUI operation, speech, physical guidance; including graduated actions, see below).
4. Memory: what it knows (session, episodic, user profile, personal thresholds).
5. Evaluation and self-improvement: the loop that re-tunes theta.

Concrete, checkable contributions inside the list:

- The pilot (`pilot/pilot.py`, standard library only, seed 13, deterministic, `results.txt` is the expected output). It seeds must / may / must-not windows from HoloAssist's public annotations by a documented rule: MUST = wrong action corrected or uncorrected by an instructor, benefit 4; MAY = instructor-initiated follow-up / high-level instruction / confirmation, benefit 2; MUST-NOT = student-initiated conversation (interrupting a speaking user is a social violation), cost 4; anywhere else a fire pays base false-alarm cost 1. It scores five policies (always at 1s, always at 10s, never, random, cost-sensitive) on timing recall, violation rate, and a cost-weighted score `score(lambda) = sum(benefit) - lambda * sum(cost)` swept over lambda in [0.25, 4]. The lambda sweep is the point: it exposes the regime where silence is optimal, which a single accuracy number hides.
- A feedback-depth table, L0 to L3: L0 explicit (accept / dismiss / snooze, free but sparse and biased), L1 implicit behavioural (did the user follow it, gaze dwell vs aversion, recovery time, undo; dense, moderate attribution), L2 outcome (task completion delta, time saved; delayed, credit-assignment problem), L3 long-term (retention, trust, user disabling proactivity entirely, named as "the ultimate negative reward"). Plus the observation that "snooze for 3 days" is doubly informative: a negative reward and a hard constraint the user writes into the policy.
- Three maturity levels for using that feedback: (1) log only (most products), (2) threshold adaptation, per-user per-context updates to theta, described as "the smallest possible RL" and probably where always-on assistants should start, (3) policy learning with a learned reward model, of which ProactiveAgent is the offline version.
- A convergence the list claims the field has not remarked on: three independent 2026 papers converge on a cheap-gate / expensive-actor architecture (PRISM's deliberation gate, a temporal-graph trigger that only calls the LLM after firing, and pre-reasoning perception). Gate cheap, act expensive.
- Graduated action, from Full-Duplex-Bench: backchanneling as evidence that intervention is not binary (silence / full interruption) but a menu of escalating costs.
- Historical cost evidence that reprices intuition: Iqbal and Horvitz field data, about a 20-minute disruption arc per alert and 27% of suspended windows unresumed after two hours; InterruptMe, sentiment toward a notification more than halves after eight others in the prior two hours, so back-to-back firing is worse than random; Precision Proactivity (2025), AI-initiated task switching as the strongest predictor of performance decline in 1,178 observations of real professional work.

### Trait map

- Primary: initiation / proactivity (it is a theory of initiation)
- Secondary: conscientiousness (cost, restraint, thresholds), intelligence (decision under uncertainty), memory (layer 4, personalised theta), real-time (timing as the metric)

### Quality evidence

Stars are meaningless here (7, created 2026-07). Quality rests on: citations are verifiable (arXiv / DOI / official pages required by its own contributing rule), entries carry honest one-line corrections (VisionClaw is explicitly corrected from its abstract's framing after a full-text read: always-on perception, strictly reactive action, proactivity as future work), the companion survey is peer-reviewed at TMLR with public reviews, and the pilot is runnable, deterministic, and honest about what it does not show (seeded labels are not human-judged; inter-annotator agreement is future work). Last push 2026-10-16, README states "Last verified: 2026-07," v0.2, actively maintained per its status line.

Risk on quality: several cited arXiv IDs are dated 2026 and could not all be independently verified in this pass; treat individual futuristic entries as pointers, not proof. The framework, the historical lineage, and the pilot do not depend on those entries.

### Transferable value for the target stack

Highest in the cluster. The target stack already has the machinery this map theorises: cron and hooks are the signals and decision points, the Feed and chat surfaces are the action layer, file memory is layer 4, and nightly synthesis is a slow version of layer 5. What the map adds is the missing decision discipline between them:

- Price every proactive surface with the inequality, explicitly. For each cron / hook that can interrupt, write down its expected benefit, its interruption cost, and its theta. Surfaces that cannot state a cost should default to silent logging (maturity level 1) until they can.
- Adopt must / may / must-not windows and the lambda-swept cost-weighted score as the evaluation shape for any proactive lane, instead of counting deliveries. The pilot is about 200 lines of standard-library Python; its scoring shape, not its HoloAssist data, is the transferable artefact.
- Adopt threshold adaptation (maturity level 2) before any learned policy: per-context theta tuned by logged accept / dismiss / snooze events. This fits the existing stack (a small state file per lane, updated by feedback) with no new platform.
- Adopt the cheap-gate / expensive-actor split as an architectural rule: a cheap deterministic or small-model check decides whether a scheduled wake is worth a full reasoning pass at all. This is also a cost control on the cron fleet itself.
- Adopt graduated action: silent log, then digest inclusion, then direct message, as escalating costs of the same intervention, chosen by the gate, rather than each lane hard-coding its own loudness.
- The historical findings justify existing restraints in the target stack (silent checks, ping only on a real event) and give them numbers: interruption cost is measured in tens of minutes and in exhaustion across repeated alerts, not in seconds of reading time.

### Risks

- Abandonment: medium. Single maintainer, new repo. Mitigated by CC0 framing and by the value being in the text, which can be cited and internalised without a dependency.
- Hype: low. The list is actively deflationary about its own field.
- Security / lock-in: none. It is a document plus one dependency-free script (inspected, not run, per the rails of this task).

### Verdict

**ADOPT-IDEA** — the cluster's top find. Adopt the benefit-minus-cost-over-theta rule, must/may/must-not scoring with a lambda sweep, L0-L3 feedback logging, and per-context threshold adaptation as the governing design for all cron / hook proactivity. No code dependency needed.

---

## 3. Deep-dive: letta-ai/letta (MemGPT, from the list's Memory layer)

### Metadata

| Field | Value |
|---|---|
| Repo | letta-ai/letta |
| Description | "Platform for stateful agents: AI with advanced memory that can learn and self-improve over time." |
| Stars / Forks | 25,306 / 2,664 |
| Last push | 2026-10-18T22:28:04Z |
| Archived | false |
| License | Apache-2.0 |
| Note | README now states current source lives in letta-ai/letta-code (3,748 stars, pushed 2026-10-31, verified via API); this repo's `archive` branch holds the retired V1 API server |

### What it is and mechanism

MemGPT's idea, productised as Letta: treat LLM context like an operating system's virtual memory. Memory is tiered (in-context core memory the agent can edit, recall history, and archival storage), and the agent itself issues function calls to page information in and out and to rewrite its own core memory blocks (persona, human profile). Agents are stateful services with persistent identity across sessions, now delivered as a terminal UI, app server, channels (Slack / Telegram / Discord), an SDK, and a cloud offering.

The tree of `letta-ai/letta` itself is now mostly governance and docs files, which corroborates the README's pointer: the living system has moved repos. Judging "letta" today means judging a platform, not a library.

### Trait map

Primary: memory. Secondary: conscientiousness (self-editing memory is a curation discipline), execution (stateful agent runtime).

### Quality evidence

25k stars, active pushes, Apache-2.0, a real company and docs site behind it. Also real churn: a rename (MemGPT to Letta), a retired V1 server, and a repo migration within the last cycle. That churn is itself evidence about adoption cost.

### Transferable value

The target stack already implements the core insight in a more auditable form: file-based memory with nightly synthesis is OS-style paging done in plain text, where every "page" can be read, diffed, and corrected by a human. Letta's transferable ideas are narrower: (a) memory blocks with explicit owners and purposes (core blocks the agent may edit vs archival it may only read) is a clean permission model for memory writes; (b) letting the agent propose its own memory edits as discrete, reviewable operations rather than silent overwrites. Both are adoptable as conventions on top of files. The platform itself would replace a transparent store with a service and a database, a downgrade in inspectability for this stack.

### Risks

Platform weight and migration churn; cloud upsell path; adopting the runtime would be a second source of truth for memory alongside the existing file system and the trading book's own memory, which the governing doctrine forbids.

### Verdict

**ALREADY-HAVE** — equivalent: file-based memory with nightly synthesis, plus the skills library. Borrow only the block-permission idea. Do not adopt the platform. **REFERENCE** for memory-tier terminology.

---

## 4. Deep-dive: mem0ai/mem0 (Mem0, from the list's Memory layer)

### Metadata

| Field | Value |
|---|---|
| Repo | mem0ai/mem0 |
| Description | "The Memory Layer for AI Agents - Drop-in memory infrastructure for AI agents and apps. Context that persists. Built for production." |
| Stars / Forks | 68,158 / 8,083 |
| Last push | 2026-10-30T21:36:23Z |
| Archived | false |
| License | Apache-2.0 |

### What it is and mechanism

A production memory layer with library, self-hosted server, and cloud tiers. The README documents its April 2026 algorithm change in unusual detail, which is where the transferable mechanism lives:

- Single-pass ADD-only extraction: one LLM call extracts facts, nothing is updated or deleted in place; memories accumulate and contradictions are resolved at retrieval / reasoning time rather than by overwriting.
- Agent-generated facts are first-class: what the agent confirmed by acting is stored with equal weight to what the user said.
- Entity linking: entities are extracted, embedded, and linked across memories, boosting retrieval when the same entity recurs.
- Multi-signal retrieval: semantic similarity, BM25 keyword match, and entity matching scored in parallel and fused, in a single retrieval pass (no agentic loop), at a top-200 budget.
- Temporal reasoning: time-aware ranking that prefers the dated instance appropriate to whether the query is about current state, a past event, or an upcoming plan.
- Multi-level scoping: user, session, and agent memories kept distinct.

Benchmarks claimed for the managed platform: LoCoMo 92.5, LongMemEval 94.4, BEAM 64.1 at 1M tokens, at about 7K tokens and about 1s p50 latency. The README itself adds the caveat that these are managed-platform numbers including proprietary optimisations, and open-source users should expect directionally similar, not identical, results. That caveat is credited in this assessment.

### Trait map

Primary: memory. Secondary: intelligence (retrieval fusion, temporal ranking), real-time (about 1s retrieval latency as a design target).

### Quality evidence

Largest repo in the cluster by an order of magnitude (68k stars, 8k forks), pushed the day before inspection, Y Combinator S24 company, PyPI and npm packages, an open-sourced evaluation framework for reproducing numbers. Maintenance risk is low; commercial-capture risk is the real one (see Risks).

### Transferable value

Three ideas transfer directly onto a file-based memory without adopting the product:

1. ADD-only with resolution at read time. The target stack's nightly synthesis currently curates and rewrites. An append-only raw layer underneath the curated layer, with synthesis reading from the append log, would make every memory claim traceable to its source event and make bad syntheses recoverable. This aligns with the doctrine's provenance requirements.
2. Multi-signal retrieval for memory search. A file memory searched only semantically will miss exact names, dates, and identifiers; searched only by keyword it will miss paraphrase. Fusing keyword, semantic, and entity-match signals is a concrete upgrade path for memory search quality, implementable over files and a local index.
3. Temporal ranking as an explicit rule: when memories conflict, the right answer depends on whether the question is about now, then, or next. Stating that rule in the synthesis and retrieval prompts is free and prevents a common failure (surfacing a superseded fact because it matches best).

The user / session / agent scoping distinction is already present in the target stack in another form (main memory, per-goal workspaces, side chats) and needs no import.

### Risks

Benchmark numbers are for the paid platform, not the OSS SDK (their own caveat). The cloud path creates data-residency and lock-in questions for a personal memory store. Adopting the server would again create a second memory truth alongside files. The agent self-signup flow advertised in the README (an agent minting its own API key in seconds) is a governance pattern this stack should explicitly not copy without a human approval step.

### Verdict

**ADOPT-IDEA** — adopt ADD-only accumulation under the curated layer, multi-signal (keyword + semantic + entity) retrieval, and temporal ranking. Do not adopt the platform or the cloud.

---

## 5. Deep-dive: MemTensor/MemOS (from the list's Memory layer)

### Metadata

| Field | Value |
|---|---|
| Repo | MemTensor/MemOS |
| Description | "Self-evolving memory OS for LLM & AI Agents: ultra-persistent memory, hybrid-retrieval, and cross-task skill reuse..." |
| Stars / Forks | 12,208 / 1,101 |
| Last push | 2026-10-29T11:26:35Z |
| Archived | false |
| License | Apache-2.0 |
| Language | TypeScript |

### What it is and mechanism

A "memory operating system" that unifies three memory kinds in a composable unit (MemCube): parametric memory (in weights / adapters), activation memory (KV-style runtime state), and plaintext memory (explicit text, knowledge bases, tool traces). Around that: a unified add / retrieve / edit / delete API with graph-structured, inspectable storage; multi-cube management for isolating and sharing memory across users, projects, and agents; a MemScheduler running memory operations asynchronously; and natural-language feedback correction of stored memories.

The most relevant part for this stack is its local plugin line (Hermes / OpenClaw / DeepSeek Harness plugins, 2026): a tiered model, L1 traces, L2 policies, L3 world models, and crystallised Skills, with hybrid FTS5 + vector retrieval, deduplication, and feedback-driven retrieval, running locally on SQLite in the local variant. Cloud and self-host variants add Neo4j + Qdrant.

Benchmarks claimed: LoCoMo 88.83, LongMemEval 89.20, plus an OmniMemEval suite of their own; and an agent-task claim that adding MemOS raised one agent framework's average task completion from 36.63% to 50.87% across five tasks.

### Trait map

Primary: memory. Secondary: execution (tool memory, skill reuse), creativity in a narrow sense (skill crystallisation from traces is a form of compounding experience).

### Quality evidence

12k stars, 1.1k forks, pushed two days before inspection, 147 open issues (active, with real load). Apache-2.0. Evidence quality is weaker than Mem0's: the headline suite (OmniMemEval) is their own, and the agent-completion claim is a single-framework before / after without a visible independent replication in the README. Treat numbers as vendor claims.

### Transferable value

MemOS is the deep-dive that most closely resembles the target stack already: L1 traces to L2 policies to L3 world models to crystallised Skills is, almost term for term, daily logs to curated memory to synthesis to `SKILL.md` playbooks. That resemblance is the value: it is external validation of the existing architecture, plus two refinements worth stealing:

- Skill crystallisation as an explicit, gated promotion: a repeated successful trace pattern becomes a candidate skill only after a threshold, with feedback continuing to revise it. The target stack creates skills, but a stated promotion rule (from traces, with counts) would make the library's growth more systematic and auditable.
- Memory cubes as a scoping concept: named, composable memory partitions with explicit sharing rules across agents / projects. The target stack has this implicitly in goal workspaces; making the sharing rule explicit per partition prevents cross-contamination, a failure mode the doctrine already worries about.
- Natural-language correction as a memory API ("that is wrong, it is X now") with the correction stored as an event, not a silent edit. This pairs well with the ADD-only idea from Mem0.

The parametric / activation tiers do not transfer: this stack does not fine-tune its model, and activation state is the provider's concern.

### Risks

Heaviest infrastructure in the memory trio for self-hosting (Neo4j + Qdrant in the server variant). Vendor-run benchmarks. Very broad surface (plugins for three other agent ecosystems) suggests focus diffusion. Plugin installation into other agents is exactly the kind of supply-chain step that needs separate scrutiny; none was performed here and none is recommended by this report.

### Verdict

**REFERENCE**, with two **ADOPT-IDEA** elements (gated skill crystallisation from traces; explicit per-partition sharing rules). The overall architecture is **ALREADY-HAVE** in file form. Do not adopt the code.

---

## 6. Deep-dive: bytedance/UI-TARS (UI-TARS-2 in the list's Action layer)

### Metadata

| Field | Value |
|---|---|
| Repo | bytedance/UI-TARS |
| Description | "Pioneering Automated GUI Interaction with Native Agents" |
| Stars / Forks | 11,654 / 888 |
| Last push | 2026-01-27T04:57:26Z |
| Archived | false |
| License | Apache-2.0 |
| Related | bytedance/UI-TARS-desktop, 39,484 stars (via GitHub search, 2026-10-31) |

### What it is and mechanism

A native GUI agent model family: a vision-language model trained end-to-end to perceive screenshots, reason, and emit grounded actions (clicks at absolute coordinates, drags, key presses, scrolls, mobile gestures), rather than a pipeline of separate OCR / grounding / planning components. The repo holds the 1.5-era code: an action parser (`codes/ui_tars/action_parser.py`), prompt templates for computer use, mobile use, and pure grounding (`codes/ui_tars/prompt.py`), deployment guides, and coordinate-processing documentation. UI-TARS-2 (arXiv 2509.02544, the version the awesome list cites) is described there as adding multi-turn reinforcement learning, a data flywheel, and a hybrid environment spanning GUI, file system, and terminal in a unified sandbox; the 2.0 model itself is not in this repo, which is a coverage fact, not a criticism.

Reported results: UI-TARS-1.5 at OSWorld 42.5 (100 steps), Windows Agent Arena 42.1, AndroidWorld 64.2, ScreenSpot-V2 grounding 94.2. The awesome list cites UI-TARS-2 at OSWorld 47.5 and AndroidWorld 73.3 and places it, correctly, as proof that multi-turn RL works when reward has ground truth (task completion), in deliberate contrast to intervention timing, where it does not.

### Trait map

Primary: execution. Secondary: real-time (perceive-act loop), intelligence (reasoning before action, with an explicit Thought field whose presence measurably improves their game and Minecraft results).

### Quality evidence

11.6k stars for the model repo and 39.5k for the desktop app indicate genuine adoption. ByteDance Seed is a well-resourced lab; benchmarks are standard public suites. Last push to this repo 2026-01-27 is the stalest in the deep-dives, consistent with development having moved to the 2.0 report and the desktop repo.

### Transferable value

Low for code, modest for ideas, and the awesome list itself explains why: action is not this stack's bottleneck. The target stack already has browser and device execution with human approval gates, which is a safer action layer than an autonomous coordinate-clicking model for a personal agent handling real accounts.

Ideas that do transfer:

- Thought-before-action as an emitted, logged artefact. Their ablations (with Thought vs without, e.g. Minecraft task averages 0.42 vs 0.35) are evidence that a short explicit reasoning trace before an irreversible UI action improves outcomes and, for this stack, doubles as the audit record the doctrine requires.
- Grounding evaluation as a separate score: an agent can plan correctly and still click the wrong element. Any future expansion of the stack's GUI work should measure grounding (did it act on the intended target) separately from task success.
- The list's framing: GUI RL works because completion is checkable. The same standard should be demanded of any proactive or execution feature in this stack: if success cannot be checked from the final state, the feature is not ready to act autonomously.

### Risks

Running a GUI agent model means hosting or calling a large VLM and giving it pointer control; the safety and approval model would be a step backwards from the current gated browser route. Model weights and inference cost are non-trivial. Repo / report split (2.0 described, 1.5 shipped) is a documentation trap for casual adopters.

### Verdict

**REFERENCE** — for thought-before-action logging and grounding-as-a-metric. **SKIP** the code for this stack: the action layer is already covered, with stronger approval gates.

---

## 7. Deep-dive: liutj9/ProactiveEval (from the list's Evaluation layer)

### Metadata

| Field | Value |
|---|---|
| Repo | liutj9/ProactiveEval |
| Description | "ProactiveEval: A Unified Evaluation Framework for Proactive Dialogue Agents." |
| Stars / Forks | 5 / 0 |
| Created | 2025-08-28 |
| Last push | 2025-08-28T13:25:57Z (single-day push pattern) |
| Archived | false |
| License | None listed |
| Language | Python |
| Note | README file is lowercase `readme.md`; tree: dataset/, dataset_generation/, eval/, requirements.txt |

### What it is and mechanism

Verified in `readme.md` (lowercase; the conventional path 404s, a small maintenance tell) and the tree. ProactiveEval splits proactive dialogue into two sequential, separately scored tasks:

1. Target Planning: given raw environment data, anticipate the user's need and formulate a target. Scored by an LLM judge against a reference target and guidelines.
2. Dialogue Guidance: given the target, steer a multi-turn conversation with a simulated user toward it. Scored separately on guidance quality.

Around that: a data-synthesis framework generating evaluation scenarios across 6 domains, 328 scenarios, with a topic-tree built by human-AI collaboration, environment and target generation, refinement passes (rewrite, add noise), and multi-model reasonableness checks. Default judge is GPT-4o (2024-11-20) via an OpenAI-format API.

Its headline finding is worth repeating: reasoning models showed degraded interaction and instruction-following in proactive dialogue compared with non-reasoning models, limiting their proactive capability. More reasoning, worse proactive conversation, in their setup.

### Trait map

Primary: initiation / proactivity (evaluation of it). Secondary: intelligence (it measures a failure mode of reasoning-heavy models), conscientiousness (evaluation discipline).

### Quality evidence

Weakest in the cluster: 5 stars, no forks, no licence, all pushes on one day in August 2025 and nothing since. This is a paper artefact drop, not a maintained framework. LLM-as-judge evaluation also inherits judge bias, and with a single default judge the leaderboard should be read as indicative only.

### Transferable value

The two-stage split is the transferable idea, and it is cheap: score any proactive behaviour in the target stack first on "was the identified need / target correct" and only then on "was the intervention well executed." Conflating the two hides whether failures are perception failures or delivery failures, which have different cures. ProactiveAgent's benchmark makes the same point from the other side (detection vs false alarm). A lightweight rubric version, a handful of logged real interventions hand-scored on both stages monthly, would give the cron / hook fleet a quality signal without adopting any code. The topic-tree scenario generation is a reasonable recipe if a larger synthetic evaluation set is ever wanted.

The reasoning-model finding is a useful caution for model selection on proactive / conversational surfaces: benchmark the actual surface, do not assume the strongest reasoning configuration is best at it.

### Risks

Abandonment: high (already stale). No licence means no clear reuse rights for the code or data; ideas are fine, copying is not. Judge-dependent scores can be gamed and drift when the judge model changes.

### Verdict

**ADOPT-IDEA** (the two-stage target-then-guidance rubric only) / **REFERENCE**. **SKIP** the code: unlicensed and unmaintained.

---

## Cluster summary: ranking by transferable value

| Rank | Repo | Verdict | One-line reason |
|---|---|---|---|
| 1 | tao-hpu/awesome-proactive-agents | ADOPT-IDEA | The benefit-minus-cost-over-theta rule, must/may/must-not scoring, and threshold adaptation give the existing cron/hook fleet its missing decision discipline |
| 2 | thunlp/ProactiveAgent | ADOPT-IDEA | Working proof of the gated proposal: explicit null, separate reward judge, accept/reject/ignore with distinct effects, false-alarm as a headline metric |
| 3 | mem0ai/mem0 | ADOPT-IDEA | ADD-only accumulation, multi-signal retrieval, and temporal ranking upgrade file memory without replacing it |
| 4 | MemTensor/MemOS | REFERENCE (+ 2 ideas) | Validates the traces-to-policies-to-skills architecture already in place; steal gated skill crystallisation and explicit partition sharing rules |
| 5 | liutj9/ProactiveEval | ADOPT-IDEA (rubric) / REFERENCE | Two-stage scoring (target correctness, then guidance quality) is a cheap quality signal for proactive lanes |
| 6 | letta-ai/letta (MemGPT) | ALREADY-HAVE | File memory with nightly synthesis is the same OS-paging idea in auditable form; borrow only memory-block permissions |
| 7 | bytedance/UI-TARS | REFERENCE / SKIP code | Action is not the bottleneck; keep thought-before-action logging and grounding-as-a-metric, keep the existing gated execution layer |

Three cross-cluster conclusions:

1. Gate before actor, everywhere. ProactiveAgent's reward model, PRISM's calibrated threshold (via the list), and the temporal-graph trigger all implement the same split independently. For this stack that means: no cron, hook, or suggestion lane should both generate and decide to surface its own output in one pass.
2. Proactivity quality is mostly a cost-accounting problem. Base frontier models over-propose (about 50% false alarms on ProactiveBench). The fix is not a better generator; it is a priced interruption, a personalised theta, and feedback that throttles. The stack's existing restraint instincts (silent checks, ping only on real events) are supported by the historical evidence the list assembles.
3. Memory improvements worth taking are all file-compatible. ADD-only provenance, multi-signal retrieval, temporal ranking, and gated skill crystallisation strengthen the existing memory and skills systems. None of the three memory platforms justifies replacing files with a service; each would create a second source of truth, which the governing doctrine prohibits.

No repo in this cluster earned ADOPT-CODE. That is a finding, not a gap: the cluster's value is decision architecture and evaluation shapes, and the target stack's advantage is precisely that its memory and execution layers are transparent and already integrated.

---

## Coverage ledger

Inspected (live API metadata + README + tree; key source files where noted):

- thunlp/ProactiveAgent: metadata, README, full tree, `agent/prompt.py`, `agent/ragent.py`, `agent/README.md`, `gym/README.md`, `gym/components/activeagent.py`, `gym/components/reward.py`.
- tao-hpu/awesome-proactive-agents: metadata, full README, full tree, `pilot/pilot.py` and `pilot/README.md` read in full.
- letta-ai/letta: metadata, README, root tree. letta-ai/letta-code: metadata only, to verify the migration the README declares.
- mem0ai/mem0: metadata, README (including the April 2026 algorithm section), root tree.
- MemTensor/MemOS: metadata, README, root tree.
- bytedance/UI-TARS: metadata, README, root tree. bytedance/UI-TARS-desktop star count via GitHub search API.
- liutj9/ProactiveEval: metadata, contents listing, `readme.md` in full.

Unreachable / not found, logged honestly:

- bytedance/UI-TARS-2 as a standalone repo: API returns no repo; UI-TARS-2 exists as a technical report (arXiv 2509.02544) and a section of the UI-TARS repo. Assessed via the 1.5 repo plus the list's placement.
- microsoft/HoloAssist as a GitHub repo: API returns no repo under that name; HoloAssist is a Microsoft dataset / project used as substrate by the pilot. Not deep-dived as a repo; its role is covered through the pilot's seeding rule.
- YETI and PRISM as code repos: GitHub search returned no matching repositories in this pass. They are assessed only as entries in the awesome list (arXiv 2501.09355 and 2602.01532 respectively), not as inspected code, and no verdict is issued on them individually.
- ProactiveEval `README.md` (capitalised): 404; the file is `readme.md`. Content was read from the correct path.

Redirected:

- letta-ai/letta README redirects current development to letta-ai/letta-code; both were checked and the assessment covers the platform as a whole.

Out of scope by design: the awesome list contains dozens of arXiv-only entries (signals and egocentric-vision papers especially) with no code artefact; they are represented through the list's own synthesis rather than individual deep-dives, and none is claimed as inspected.
