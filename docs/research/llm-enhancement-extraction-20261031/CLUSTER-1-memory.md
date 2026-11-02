# Cluster 1: Memory Systems

Research date: 2026-10-31. Method: live GitHub API metadata, raw README and docs files, and file-tree inspection only. No repo code was installed, cloned-and-run, or executed.

Baseline stack used for transfer judgments: a file-based memory with nightly synthesis, a skills library of SKILL.md playbooks, scheduled cron/hook proactivity, a strict engineering doctrine requiring proof before a green status, and a personal trading book with its own memory system.

---

## 1. supermemoryai/supermemory — Supermemory

### Metadata

| Field | Value (live API, 2026-10-31) |
|---|---|
| Repo | supermemoryai/supermemory |
| Description | "Memory and context engine + app that is extremely fast, scalable, and can be run fully locally. The Memory API for the AI era." |
| Stars / forks | 31,480 / 2,762 |
| Created / last push | 2024-02-27 / 2026-10-30T21:21:21Z |
| Archived | No |
| License | MIT |
| Language / default branch | TypeScript / main |
| Homepage | https://supermemory.ai/docs |

### What it is

A hosted memory and context API plus a consumer app, MCP server, per-client plugins (Claude Code, Cursor, Codex, OpenCode, OpenClaw, Hermes, and a Muse plugin), SDKs, and a self-hosted "Supermemory local" single-binary/Docker variant. It is a product and platform first; the open repo is dominated by `apps/` (web, docs), SDK/tool packages, and plugin glue. The core learning model and temporal vector-graph engine are described in the docs as built internally, so the decisive extraction engine is not fully auditable from this repo's tree.

### Mechanism, in plain terms

Judged from `apps/docs/concepts/how-it-works.mdx`, `graph-memory.mdx`, `user-profiles.mdx`, `memory-vs-rag.mdx`, and `rules.mdx`, plus the README:

1. **Documents in, facts out.** Raw input (chats, text, PDFs, images with OCR, audio/video transcription, code with AST-aware chunking, URLs, connector syncs from Drive/Gmail/Notion/OneDrive/GitHub/S3) is ingested without the caller choosing chunking or an embedding model. A learning model extracts atomic facts ("memories") from the documents. Documents and memories are kept as distinct layers: documents are the source material, memories are the evolving personal state.
2. **A temporal fact graph, not a vector pile.** New facts link to old ones with exactly three edge types: **updates** (new fact supersedes the old for retrieval, history retained, `isLatest` flag), **extends** (new fact enriches without invalidating), and **derives** (a fact inferred across sources that was never stated in one place). Contradictions are resolved through the updates path rather than returned side by side.
3. **Automatic forgetting.** Temporary facts expire after their date passes; superseded and irrelevant facts stop surfacing. Forgetting is a first-class engine job, not a manual delete.
4. **User profiles: static + dynamic.** Each namespace (container tag, used as project/user scope) gets an auto-maintained profile split into static long-term facts and dynamic recent activity. One `profile()` call returns profile plus relevant search results in a claimed ~50-100ms. This solves the known failure of pure search: facts that should colour every answer (preferred name, timezone, format preferences) are not semantically similar to most queries, so search alone misses them; the profile rides along unconditionally.
5. **Hybrid search.** One query searches memories and document chunks together (memory plus RAG), with search modes for memories vs chunks and a cheaper search-only ingest mode.
6. **Agent-facing tools are tiny.** The MCP/plugin surface is three verbs: `memory` (save/forget), `recall` (search plus profile summary), `context` (inject full profile at session start). Plugins run extraction in the background so the host agent does nothing special in conversation.

### Trait map

| Trait | Effect |
|---|---|
| Memory | Primary. Temporal fact graph, contradiction handling, expiry, profiles. |
| Intelligence | Secondary. Cross-source derived facts and hybrid memory+RAG retrieval improve grounding. |
| Real-time | Secondary. Connector webhooks and instant ("dreaming: instant") availability keep memory current. |
| Execution | Minor. Three-verb tool surface reduces agent bookkeeping errors. |
| Conscientiousness, initiation, creativity, abstract thinking | No direct mechanism. |

### Quality evidence

- 31,480 stars and 2,762 forks, pushed the day before inspection, not archived. This is the most adopted project in the cluster by an order of magnitude.
- Benchmark claims in the README: #1 on LongMemEval, LoCoMo, and ConvoMem; LongMemEval 95% Recall@15 at ~720 added context tokens (99.4% context reduction), with per-category recall: knowledge updates 99%, temporal reasoning 91%, preference 90%, multi-session 93%. These are vendor-reported, not independently re-run here, but the benchmarks are public and the vendor ships **MemoryBench**, an open framework for head-to-head runs against other providers, plus a **Supermemory Filesystem (SMFS)** claim of 3.0x fewer tokens on Claude and 1.75x fewer on Codex over its own xAFS benchmark.
- Docs quality is high and unusually honest in places: `rules.mdx` explicitly says Supermemory is not a system of record, has no SQL/joins/aggregates, and that transactional data and verbatim system-prompt rules belong elsewhere. That boundary discipline is credible engineering, not just marketing.
- Caveat: the headline engine is closed. MIT on the repo does not mean the learning model and graph engine that produce the benchmark numbers are in the tree.

### Transferable value for the baseline stack

High, as ideas, in four concrete forms:

1. **Static/dynamic profile split.** The baseline nightly synthesis already produces a curated long-term file and daily notes. Making the split explicit and operational (an always-injected static profile of facts that must colour every response, separate from dynamic recent context that is search-led) directly attacks the "search missed the standing preference" failure. This is the single highest-value transfer in the cluster.
2. **Typed fact edges: updates / extends / derives.** The baseline synthesis currently supersedes claims (its memory system tracks replaced claims). Naming the three relations explicitly, especially keeping "extends" distinct from "updates" and labelling "derives" as inferred rather than stated, would make contradiction handling and provenance audits sharper at near-zero cost.
3. **Expiry as a synthesis job.** Temporary facts should carry an expiry and be actively forgotten by the nightly pass, not just outranked. Supermemory treats forgetting as part of correctness.
4. **Benchmark your own memory.** MemoryBench's premise, evaluating recall on knowledge-update, temporal, and preference categories separately, is transferable as an evaluation habit for the existing file memory: a small fixed question set run against the synthesis output would catch regressions that anecdote misses.

Not transferable: the hosted API itself (a second source of truth beside the file memory, which the baseline doctrine forbids working around), the connector sync layer (the baseline already has purpose-built connectors), and the closed extraction engine (cannot be adopted as code from this repo).

### Risks

- **Platform dependence:** the full-quality path is a paid hosted API or a closed local binary; adopting the product means the memory of record lives outside the auditable file tree.
- **Second source of truth:** running it beside the existing file memory would create exactly the divergence the baseline doctrine prohibits.
- **Vendor benchmark hype:** #1 claims are self-reported; only the MemoryBench route is independently checkable.
- **Privacy surface:** connector sync of mail/drive content into a third-party memory cloud is a large trust grant.

### Verdict: ADOPT-IDEA

Adopt the static/dynamic profile split, the updates/extends/derives edge vocabulary, expiry-driven forgetting, and per-category memory evaluation. Do not adopt the hosted product or attempt a code lift; the engine that makes it good is not in the open tree.

---

## 2. qualixar/superlocalmemory — SuperLocalMemory (SLM)

### Metadata

| Field | Value (live API, 2026-10-31) |
|---|---|
| Repo | qualixar/superlocalmemory |
| Description | "Open-source governed, local-first memory control plane for AI agents and teams. arXiv:2608.08253" |
| Stars / forks | 269 / 37 |
| Created / last push | 2026-02-05 / 2026-10-28T15:22:49Z |
| Archived | No |
| License | AGPL-3.0 (with a separate commercial license file in tree) |
| Language / default branch | Python / main |
| Homepage | https://www.superlocalmemory.com |

### What it is

A very large, genuinely open, local-first memory system: Python package (`src/superlocalmemory/`, the recursive tree has ~5,303 entries) shipped via npm and pip, with an MCP server (58 tools in the full profile), CLI, REST, dashboard, and generated plugin bundles for many hosts (Claude Code, Cursor, Codex, Antigravity and others, each carrying its own SKILL.md set). Four arXiv preprints by its authors describe successive versions. Mode A runs remember/recall with no model-provider call at all (local nomic text embeddings); Mode B uses a local model (Ollama); Mode C uses a cloud endpoint. SQLite + sqlite-vec is the canonical store, with LanceDB and CozoDB copies that serve only after they verify against SQLite.

### Mechanism, in plain terms

Judged from the README's capability tables, the architecture description, and the source tree (modules for access/RBAC, attribution, brain/truth, cache, code graph, governance, corrections, GDPR):

1. **Honest, tiered recall (the headline mechanism).** Every recall returns one of three tiers: a supported answer; the closest memories explicitly labelled "I don't have this exactly, here are the closest memories"; or an outright "That isn't in SuperLocalMemory" for questions nothing answers. A warm-up state is reported as warming up rather than as empty. An optional second-opinion checker (Laya, a small on-device model on Apple Silicon; Jev, an online checker behind explicit consent) judges whether the retrieved memories actually answer the question. Scores are documented as ranks, not probabilities.
2. **Governed writes.** Every save passes an admission check and gets a receipt; secrets are redacted on outbound paths; corrections replace a fact and stay undoable (`--replaces <id>` with a rollback path). Every action lands in a hash-chained audit trail. Roles/workspaces/scopes gate reads (personal by default, cross-profile recall denied by default). GDPR export and erasure reach every derived copy (summaries, caches, indexes, image mirrors) and return a verifiable receipt.
3. **Bitemporal facts and decay.** Each fact records when it happened and when the system learned it, so "what was true last month" and "what did we know before date X" are answerable. An Ebbinghaus-style retention cycle plus a lifecycle process fade unused memories toward archive, quantizing and folding them into a gist rather than hard-deleting.
4. **Layered, budgeted recall.** Recall returns a one-line glance, the facts, or full context under a hard token budget, with an `expand` step for depth, plus an exact-output cache and reversible compression for repeated tool output.
5. **Self-maintenance ("living brain").** A memory-health pass enriches old memories in the background by addition only; anything that moves or deletes waits for an explicit Fix, and Undo restores. A document index and health check (empty pages, unlinked documents, duplicates, contradicted facts) implement the Karpathy LLM-wiki pattern. Opt-in learning-to-rank promotes a new ranker only on a statistically valid win and auto-rolls back on regression. Stable behaviour patterns can become soft prompts; agent skills are measured and revised under blind verification.
6. **Multi-agent sharing with poisoning defence.** Writes are attributed per agent with Bayesian trust scores against memory poisoning. SLM-Mesh lets local agents and permitted web bots exchange messages, waits, locks, and shared state, with inbound messages labelled as data, never instructions. Work can run as bounded loops/graphs (via the companion `qualixar/bounded-loops` project) where "done" requires an independent gate to pass, and finished runs are kept as read-only evidence.

### Trait map

| Trait | Effect |
|---|---|
| Memory | Primary. Governed, bitemporal, decaying, self-maintaining local memory. |
| Conscientiousness | Strong secondary. Admission checks, receipts, audit chain, undoable corrections, erasure that reaches derived copies. This is memory operated like a system of record. |
| Intelligence | Secondary. Answer-check gate and honest abstention stop the agent building on wrong recall, which is a reasoning-quality gain, not just a storage gain. |
| Execution | Secondary. Bounded loops with independent gates; mesh locks prevent two agents editing the same file. |
| Initiation/proactivity | Minor. Background health/enrichment and daily learning run without being asked. |
| Real-time, creativity, abstract thinking | No direct mechanism (mesh is coordination, not real-time data). |

### Quality evidence

- 269 stars, 37 forks, active (pushed 2026-10-28), not archived. Small audience relative to Supermemory, but the tree shows a real, broad implementation (dedicated modules for RBAC, attribution signing, GDPR IO, integrity repair, calibration), not a README shell.
- Benchmark honesty is notably good: the README states its LoCoMo numbers (Mode A + GPT-4.1-mini 74.8%; Mode A raw, no LLM, 60.4%; Mode C 87.7% on a single conversation) come from the earlier architecture paper, are "not a fresh run of the current package," and are comparable only when subset, answer model, and judge match. That caveat discipline is rare and raises trust in the rest.
- Four arXiv preprints are linked (2608.08253, 2604.04514, 2603.14588, 2603.02240). They are preprints, not peer-reviewed results, and are authored by the vendor.
- Risks to quality judgment: the feature surface is enormous for a 269-star project (58 MCP tools, mesh, media embeddings, code graph, skill evolution), which usually means uneven depth per feature; several headline capabilities are opt-in or platform-specific (Laya is Apple Silicon only).

### Transferable value for the baseline stack

Highest idea density in the cluster, because SLM is solving the baseline's exact problems in the open:

1. **Three-tier honest recall with abstention.** The baseline memory search always returns nearest neighbours, and an agent can silently build on an irrelevant hit. Adding an explicit tier label (supported / closest-only / not present) plus a "warming up vs empty" distinction to memory search results is a small, high-leverage change that directly serves the doctrine's "route failure is not impossibility" and "never claim absence from a failed lookup" rules. This is the cluster's best single idea alongside Supermemory's profile split.
2. **Erasure and correction that reach derived copies, with receipts.** The baseline has a forget skill and claim-supersession tracking; SLM's standard (an erasure is not done until summaries, caches, and indexes are also clean, and it produces a verifiable receipt; corrections are undoable) is a stricter completion definition worth adopting verbatim as policy.
3. **Addition-only background health, human-gated destructive fixes.** The nightly synthesis could adopt SLM's rule exactly: enrichment may add, never rewrite, autonomously; moves and deletes queue for approval; every fix is undoable.
4. **Bounded loops with independent gates as memory.** "Done means a gate passed, never the agent's word, and the run is stored as read-only evidence" is the baseline engineering doctrine restated; SLM shows it implemented inside a memory product, which validates the doctrine rather than adding to it. Worth citing as external corroboration, not adopting as code.
5. **Per-agent write attribution with trust scoring** matters if multiple agent tracks keep writing shared memory; the baseline already separates some peer lanes by rule, and attribution would make violations detectable rather than conventional.

Not transferable as code: AGPL-3.0 licensing, a second canonical store beside the file memory, and a 58-tool surface that would swamp the existing tooling. The mesh and media-embedding layers duplicate existing coordination and media systems.

### Risks

- **License:** AGPL-3.0 with a commercial-license upsell; embedding its code into a broader stack carries copyleft obligations.
- **Scope/hype risk:** the breadth (four papers, twelve "superpowers," mesh, code graph, skill evolution) outruns its small user base; individual features may be shallow or break.
- **Maintenance concentration:** appears to be a very small team; abandonment risk is materially higher than Supermemory's.
- **Complexity cost:** adopting the product would replace a transparent file memory with a multi-store system (SQLite, LanceDB, CozoDB) whose failure modes are harder to audit by eye.

### Verdict: ADOPT-IDEA

Adopt tiered honest recall/abstention, derived-copy erasure with receipts, and addition-only self-maintenance with gated destructive fixes. Reference the code for how those are implemented. Do not adopt the product or lift code under AGPL into the stack.

---

## 3. MemoryPlugin — resolved as memoryplugin/mcp-server (with memoryplugin/agent-skills)

### How the ambiguity was resolved

"MemoryPlugin" is a product name (memoryplugin.com), not a unique repo name. GitHub search was run three ways on 2026-10-31:

- `MemoryPlugin in:name` returned mostly unrelated projects (a C# plugin loader, an iOS sample, two tiny personal repos named MemoryPlugin with 0-1 stars and no memory-for-AI function).
- `memory plugin chatgpt` by stars surfaced the organisation `memoryplugin`: its `mcp-server` repo is described as "MCP server for MemoryPlugin: long-term memory shared across ChatGPT, Claude, Gemini, and 21+ AI tools," and its sibling `agent-skills` repo as "One memory. Every AI. Agent skill + Claude Code plugin that teaches AI agents to use the user's MemoryPlugin long-term memory automatically."
- The `memoryplugin` account owns exactly these two repos, both MIT, both pointing at memoryplugin.com.

Resolution: the intended target is the MemoryPlugin product's open surface, i.e. **memoryplugin/mcp-server** as the primary repo, with **memoryplugin/agent-skills** inspected as its companion. Confidence is high: organisation name, product name, descriptions, and website all agree.

### Metadata

| Field | mcp-server (live API, 2026-10-31) | agent-skills |
|---|---|---|
| Description | MCP server for MemoryPlugin: long-term memory shared across ChatGPT, Claude, Gemini, and 21+ AI tools | One memory. Every AI. Agent skill + Claude Code plugin for automatic MemoryPlugin use |
| Stars / forks | 1 / 0 | 6 / 1 |
| Last push | 2026-08-05T05:51:44Z | 2026-07-24T14:28:17Z |
| Archived | No | No |
| License | MIT | MIT |

### What it is

A hosted, cross-tool personal memory service (buckets of memories, imported chat history from ChatGPT/Claude/other tools, uploaded documents) exposed to agents through a thin MCP server. The `mcp-server` repo's whole implementation is a single source file, `src/index.ts`, a bridge that forwards tool calls to the MemoryPlugin account API with a user token. All extraction, categorisation, and search intelligence lives in the closed hosted service.

### Mechanism, in plain terms

From the README tool list and the agent-skills README:

1. **Buckets and Smart Memory categories.** Memories are stored as short texts in user-named buckets; the hosted service auto-groups them into "Smart Memory" categories, each with a generated summary. Tools: store, hybrid semantic+keyword search, list buckets/categories, load a category's memories, edit or move memories between buckets.
2. **Imported chat-history recall.** Past conversations imported from other AI tools are searchable (`recall_chat_history` with parallel queries, token budgets, date bounds, a quality mode), with per-conversation summaries (only for conversations over 5,000 tokens), full transcripts, and an export tool that returns a temporary 15-minute unauthenticated download URL for file-based processing of long transcripts.
3. **Uploaded-file search** over documents in file buckets.
4. **The agent-skills discipline (the interesting part).** The companion skill teaches the agent a working protocol: recall before assuming (targeted search with the task's concrete nouns at task start, category summaries for orientation, chat-history recall when a past conversation is referenced); store before finishing (preferences with the why, decisions with rationale, project snapshots at milestones, corrections when reality changes; atomic, dated, filed in the right bucket, with a one-line receipt the user can veto); and an explicit do-not-store list (no secrets, no transient debugging noise, no repo conventions, which belong in project instruction files). The plugin bundles a session-start reminder so this happens without being told.

### Trait map

| Trait | Effect |
|---|---|
| Memory | Primary, but shallow: bucketed text store plus chat-history import/search. No temporal graph, contradiction model, or forgetting mechanism is visible in the open surface. |
| Conscientiousness | Minor, via the skill protocol: dated atomic stores, receipts, do-not-store rules. |
| Initiation/proactivity | Minor, via the session-start reminder pattern in the plugin. |
| All other traits | No mechanism. |

### Quality evidence

- Adoption and maintenance are weak: 1 star on the MCP server, 6 on the skills repo, no forks of consequence, last pushes 2026-08-05 and 2026-07-24 (roughly three months stale at inspection).
- The README itself documents that the recommended `npx` install path is "currently experiencing issues" and offers a manual global-install workaround. A broken front door, disclosed but unfixed in the repo, is a fair maintenance signal.
- The open code proves the bridge works as a tool list; it proves nothing about the hosted service's extraction or search quality, which is where all the value would have to live. No benchmarks are published in either repo.

### Transferable value for the baseline stack

Low as a product; the baseline already exceeds it (file memory with claim supersession, provenance, and nightly synthesis vs buckets of text in a third-party cloud). Two small things are genuinely worth noting:

1. **The recall-before-assuming / store-before-finishing protocol, written as a skill.** The baseline has the behaviours, but MemoryPlugin's formulation is crisp: search with the task's concrete nouns at task start; store decisions with rationale and preferences with the why before finishing; publish a one-line receipt the user can veto; keep an explicit do-not-store list. If the baseline's memory habits are ever re-documented, this is a good template. The baseline's own memory tooling and synthesis already implement most of it, hence ALREADY-HAVE for the substance.
2. **Cross-tool chat-history import as a concept.** Searching past conversations held in other AI tools from inside the current one is a real gap in most stacks. The baseline covers its own transcripts directly, so the transfer is conceptual only.

### Risks

- **Platform lock-in, maximal in this cluster:** memories live in a small vendor's cloud, in its bucket model; the MCP server is useless without the paid account and token. This is the ChatGPT-web-era plugin pattern (a hosted store behind a thin bridge) carried into MCP form.
- **Abandonment:** tiny, stale open repos around a closed service; if the service folds, the memory goes with it.
- **Security:** the export tool mints unauthenticated URLs (15-minute expiry) to full conversation transcripts; token-in-environment MCP config is the only auth on the bridge.
- **Privacy:** imported chat history from every AI tool concentrated in one small vendor's store.

### Verdict: SKIP

Reason: a thin, stale bridge to a closed hosted bucket store that the baseline file memory already exceeds, with maximal lock-in. Exception noted: its agent-skills protocol wording is REFERENCE-grade as a template for recall/store discipline, a discipline the baseline already has in substance (ALREADY-HAVE equivalent: the existing memory search/store tools, nightly synthesis, and forget skill).

---

## Other serious memory layers referenced inside these repos

Not inspected as cluster members; recorded because the task asked for them and later clusters may want them.

| System | Referenced from | Note |
|---|---|---|
| Mem0 | Supermemory (MemoryBench comparison target) | The other major hosted memory API; Supermemory's MemoryBench runs it head-to-head. If any hosted memory API beyond Supermemory is ever evaluated, this is the comparison baseline. |
| Zep / Graphiti | Supermemory (MemoryBench comparison target) | Temporal knowledge-graph memory; conceptually closest to Supermemory's updates/extends model. |
| qualixar/bounded-loops | SuperLocalMemory (companion project, live API: 4 stars, pushed 2026-10-02) | 69 agent loops and reference graphs with independent gates and verifiable receipts. Not a memory layer itself, but SLM stores its finished runs as memory evidence; relevant to execution/conscientiousness clusters. |
| Karpathy LLM-wiki pattern | SuperLocalMemory (implemented as document index + health check) | A pattern, not a repo product: raw documents compiled into an organised, health-checked wiki. The baseline nightly synthesis is a relative of this pattern. |
| Supermemory plugin repos (claude-supermemory, muse-supermemory, cursor-supermemory, codex-supermemory, openclaw-supermemory, opencode-supermemory) and MemoryBench / SMFS | Supermemory README | Separate repos under the same org; the Muse plugin is directly relevant if Supermemory's ideas are ever trialled, and MemoryBench is the evaluation harness named in the verdict above. |
| Squish (michielhdoteth/squish-memory) | Found during the MemoryPlugin disambiguation search, not inside a cluster repo | Local-first memory runtime advertising calibrated recall confidence and honest abstention. Same idea family as SLM's tiered recall; noted as a search by-catch only, not inspected. |

---

## Cluster summary: ranking by transferable value

1. **SuperLocalMemory (ADOPT-IDEA)** — highest idea density for this exact stack. Tiered honest recall with abstention, erasure/correction reaching derived copies with receipts, and addition-only self-maintenance are direct upgrades to an existing file memory's operating rules, available to copy as policy today at zero dependency cost.
2. **Supermemory (ADOPT-IDEA)** — the strongest product and evidence base in the cluster, and its static/dynamic profile split plus updates/extends/derives graph vocabulary are the other half of the upgrade. Ranked second only because its value is conceptual here (engine closed, product adoption would violate the single-source-of-truth rule), and its best ideas overlap SLM's.
3. **MemoryPlugin (SKIP)** — a hosted bucket store behind a thin, stale MCP bridge; the baseline already exceeds it. Its one crisp contribution, the recall-before-assuming / store-before-finishing skill protocol, is already held in substance.

Combined takeaway: the cluster's real gift is not a product to install. It is a sharper operating standard for the memory the stack already has: always-on static profile separate from searched dynamic context; typed supersession instead of silent overwrite; expiry as active forgetting; recall that can say "not present" and label "closest only"; and maintenance that may add freely but may only delete under gate, with a receipt and an undo.

## Coverage ledger

| Repo / target | Status | Notes |
|---|---|---|
| supermemoryai/supermemory | Inspected | Live API metadata, full README, root tree, and five docs concept files (how-it-works, graph-memory, user-profiles, memory-vs-rag, rules) read via raw URLs. Core engine is closed, so mechanism is judged from docs plus tree shape; that limitation is stated in its section. |
| qualixar/superlocalmemory | Inspected | Live API metadata, full README (44.8 KB), root tree and full recursive tree (~5,303 entries), source module layout. Individual source files beyond module structure were not read line by line; mechanism is judged from README capability tables corroborated by the module tree. |
| "MemoryPlugin" (ambiguous) | Resolved, then inspected | Resolved to the memoryplugin organisation via three GitHub searches (see its section). memoryplugin/mcp-server: metadata, full README, tree (single-file implementation). memoryplugin/agent-skills: metadata and README. The hosted service itself is closed and was not (and cannot be) inspected. |
| m1k0s/MemoryPlugin, CreatorXuYuFei/MemoryPlugin and other name matches | Excluded with reason | Unrelated or negligible projects found by the name search; not the ChatGPT/AI memory product. Listed here so the exclusion is auditable. |
| Referenced systems (Mem0, Zep/Graphiti, bounded-loops, plugin repos, Squish) | Noted, not inspected | Recorded in the references table with provenance. bounded-loops metadata was pulled to confirm it exists and is active; the rest are names from cluster-repo text only. |
| Unreachable | None | Every assigned repo and every file requested was reachable via the API or raw URLs on 2026-10-31. No repo is claimed inspected beyond what is listed above. |
