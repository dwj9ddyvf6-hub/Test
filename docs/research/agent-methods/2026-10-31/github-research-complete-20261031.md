# GitHub research handbook for reliable agents

Memory initiative creativity and verified execution

Research snapshot dated 31 October 2026

## Main conclusion

The useful finding across these repositories is not a larger prompt or a wholesale plugin installation. It is a set of small, testable software contracts: source-linked memory, hard time and scope eligibility, explicit failure states, exact-input checkpoints, bounded initiative, independent review and fresh evidence before completion claims. These mechanisms can improve a project when implemented and measured. They do not permanently retrain a model, guarantee reliability or establish trading profitability.

This handbook brings together the substantive findings from 22 public repositories, including the memory and proactivity deep review, the broader execution and creativity review, and the corrected application plan for Shipyard. It preserves useful negative findings and explains what is already present, what has been tested locally and what remains a proposal. The research is relevant to a simulated research and trading workflow, but most of the engineering methods apply to other agents as well.

**Current implementation status:** a separate local shadow receipt-binding validator has an independently rerun result of **83 passing tests**, comprising **53 legacy tests and 30 new tests**. It is not adopted into the canonical workflow and does not authorize execution or strategy adoption. An existing isolated HOLD/TRIM/EXIT position-review candidate must be reused rather than redesigned: its retained receipt reports **64 of 64 focused tests**, but those tests were not rerun for this research correction, and actual receipt-to-position-field source binding remains missing.

This is a dated research snapshot, not a claim about every repository's latest version. Changes to InfinityBlade being reviewed separately are outside this snapshot; no unseen updated doctrine is claimed to have been applied.

## How to use this handbook

- Read the conclusions and implementation status first to separate findings from completed work.
- Use the repository chapters for the specific mechanisms, limitations and code-level cautions.
- Use the implementation and evaluation chapters as a checklist for narrow, reviewable changes.
- Use the final appendix for immutable source links, exact review scope and unexamined coverage. The Markdown companion contains the same substantive handbook; the separate public coverage inventory is a structured index, not additional private research material.

## Evidence and scope

All 16 originally named repositories were resolved as public. MemoryPlugin was resolved to two additional source-linked repositories, and four relevant siliconjungle repositories were inspected. Complete available recursive tree inventories were obtained, but tree enumeration is not content review. The memory and proactivity pass substantively inspected 23 files; large files in both passes were sometimes reviewed by selected sections. The source appendix distinguishes selected content from the much larger unexamined remainder.

Third-party repository tests were read where relevant, not executed. No whole-repository certification, hosted-backend audit, dependency audit, current extension-store verification or financial performance validation follows from this source pass. The locally run 83-test validator result is separate project evidence, not an upstream test result. No third-party package installation, new hosted memory connection or repository-code execution was required for the source research.

## Principles worth adopting

1. **Memory is evidence with scope and time, not merely similar text.** Recover original sources, preserve revisions and recheck eligibility after retrieval and expansion.
2. **A valid schema or self-hash is not source proof.** Bind values and clocks to independently anchored captured receipts; preserve the limits of that binding.
3. **Completion is a claim requiring current evidence.** Read full test output and exit status on the final immutable candidate, and separate independent review from implementation.
4. **Initiative should improve an outcome, not increase activity.** Observe, abstain, ask and propose are legitimate outcomes; evaluate false alerts, missed events and interruption costs.
5. **Creativity needs falsifiers and lineage.** Generate distinct mechanisms, preserve rejected alternatives and promote only through leakage-controlled comparisons and holdouts.
6. **Durability comes from project state.** Code, storage, versioned procedures and authorized schedules can persist. A conversation or prompt does not permanently change model weights.

## Memory and retrieval findings

### Supermemory

Explicit spaces source recovery and careful mutation semantics

- The search tool resolves a namespace and returns memory IDs, similarity, optional document IDs, total, and timing. It separates memory search from user-profile lookup, preventing broad profile injection from being mistaken for task evidence. [Search implementation](https://github.com/supermemoryai/supermemory/blob/d53d124e4769e34c4be8bcc5d21eed1855b090ef/apps/mcp/src/server/tools/search-memory.ts)
- Saving requires a namespace and returns the created ID; that is a useful receipt contract. The caller should still distinguish acceptance/processing from fully indexed availability. [Save implementation](https://github.com/supermemoryai/supermemory/blob/d53d124e4769e34c4be8bcc5d21eed1855b090ef/apps/mcp/src/server/tools/save-memory.ts)
- Forgetting accepts bounded explicit IDs. With text alone, only an exact match is removed; otherwise candidates are returned without deletion. This is a concrete guard against destructive semantic ambiguity. [Forget implementation](https://github.com/supermemoryai/supermemory/blob/d53d124e4769e34c4be8bcc5d21eed1855b090ef/apps/mcp/src/server/tools/forget-memory.ts)
- The client requests source documents in search, preserves versions and flags such as latest/forgotten/inference when listing memories, separates static and dynamic profile entries, and disables retries for forgetting because a committed mutation retried after uncertain delivery could produce misleading failure. Search uses a fixed similarity threshold; it does not establish truth or financial relevance. The API remains an external dependency and this wrapper does not expose its full internal retrieval algorithm. [Client](https://github.com/supermemoryai/supermemory/blob/d53d124e4769e34c4be8bcc5d21eed1855b090ef/apps/mcp/src/server/client/index.ts)
- Inferred-memory review is documented as approve/decline/undo; confirmation changes the inference flag while decline forgets it. Treat this as a documented API contract, not a source audit of the hosted backend. [Review API documentation](https://github.com/supermemoryai/supermemory/blob/d53d124e4769e34c4be8bcc5d21eed1855b090ef/apps/docs/recall/memory-review.mdx)
- The inspected scope test checks that per-call namespace schema fields remain exposed despite an obsolete header. It skips without OAuth credentials. It is **not** a demonstrated end-to-end isolation/security proof. [Scope test](https://github.com/supermemoryai/supermemory/blob/d53d124e4769e34c4be8bcc5d21eed1855b090ef/apps/mcp/e2e/space-scope.test.ts)

**Practical application:** namespace every memory by project and environment; never mix production, simulation, user preference, hypothesis, and verified market fact. Retain source document ID, evidence URI, observation time, source publication time, review state, and supersession link. Prefer reversible supersession over deleting research history. On uncertain writes, reconcile by immutable receipt or idempotency key before retrying.

### SuperLocalMemory

Evidence support and temporal admission are separate gates
- A provenance record stores profile/fact/source type/source ID/creator/timestamp. This is useful lineage, but a timestamped provenance record alone does not prove the source claim. [Provenance](https://github.com/qualixar/superlocalmemory/blob/93e58692ce51b196a879a43e3974d378652db748/src/superlocalmemory/trust/provenance.py)
- Candidate generation is not treated as authorization. Scope policy rechecks candidate IDs through canonical database visibility and scope predicates, with empty authorization on failure. This matters when embeddings, graph expansion, or caches accidentally cross boundaries. [Scope policy](https://github.com/qualixar/superlocalmemory/blob/93e58692ce51b196a879a43e3974d378652db748/src/superlocalmemory/retrieval/scope_policy.py)
- The support gate combines measured signals per memory, returns recipe version and threshold, records imputed inputs, and distinguishes degraded retrieval from confident absence. An unmeasured/missing evidence object cannot support an answer. A sigmoid output is only as calibrated as its fitted recipe; do not call it a reliable probability without external evaluation. The gate is configurable/off-switchable, so Shipyard’s safety-critical gates should not silently inherit an optional setting. [Support gate](https://github.com/qualixar/superlocalmemory/blob/93e58692ce51b196a879a43e3974d378652db748/src/superlocalmemory/retrieval/support_gate.py)
- Tests cover deterministic recipe mechanics, unsupported/empty results, missing evidence, conservative imputation, rare-term misses, metadata bonuses, and keyword fallback. These are good regression-test patterns, but the handwritten test recipe deliberately tests mechanics rather than statistical calibration. [Support tests](https://github.com/qualixar/superlocalmemory/blob/93e58692ce51b196a879a43e3974d378652db748/tests/test_retrieval/test_support_gate.py)
- Important nuance: the temporal module contains both **soft demotion** and **strict admission**. Legacy expiry demotion can retain expired memories and event-time lookup is best effort. Separate admission helpers exclude correction-invalid or strict-time-invalid candidates, fail closed on unavailable authority, and reapply checks after graph/scene expansion. A per-recall cache does not cross requests/profiles/writes. Do not mistake ordinary ranking demotion for a no-lookahead guarantee. [Temporal filter and admission](https://github.com/qualixar/superlocalmemory/blob/93e58692ce51b196a879a43e3974d378652db748/src/superlocalmemory/retrieval/temporal_validity_filter.py)
- Snapshot admission intersects known-time and valid-time and excludes records created after the point-in-time boundary, including records whose creation time cannot be established. [Snapshot admission](https://github.com/qualixar/superlocalmemory/blob/93e58692ce51b196a879a43e3974d378652db748/src/superlocalmemory/retrieval/snapshot_admission.py)
- Migration M013 historically introduced nullable validity windows without immediately changing retrieval. This is a useful warning that a schema feature’s presence does not establish runtime enforcement. [Migration](https://github.com/qualixar/superlocalmemory/blob/93e58692ce51b196a879a43e3974d378652db748/src/superlocalmemory/storage/migrations/M013_bi_temporal_columns.py)
- Save/remove governance invokes hooks and operation policy before mutation. However, policy-mode detection falls back to local mode if reading RBAC state errors. This deserves explicit audit before any institutional deployment; source inspection here does not determine whether that fallback widens permission in every runtime. [Write governance](https://github.com/qualixar/superlocalmemory/blob/93e58692ce51b196a879a43e3974d378652db748/src/superlocalmemory/server/write_governance.py)

**Practical application:** use hard temporal eligibility predicates for simulated-trade evidence: `published_at <= decision_at`, `available_at <= decision_at`, valid session/calendar, permitted revision, allowed namespace, and freshness. A fresh fetch of a historical bar does not make revised information historically knowable. Apply gates again after joins, fallback providers, graph expansion, and cache hydration. Preserve “unsupported,” “provider unavailable,” “stale,” and “clock ambiguous” separately rather than collapsing them into “no signal.”

### MemoryPlugin

Focused recall staged archive access and deliberate memory formation
- The skill distinguishes curated memories from chat-history archives. It suggests noun-specific recall, progressively deeper retrieval, date windows, atomic dated facts, topical buckets, milestone snapshots, and distinguishing correction of a false fact from a genuinely changed fact. It also explicitly says recalled text is context, not instruction. These are useful workflow methods, not guarantees that the model follows them. Its broad save-by-default guidance should not override user consent or project retention policy, especially for financial information. [Skill](https://github.com/memoryplugin/agent-skills/blob/56b64b5bad61e868d8a5f932d79394a2532099cf/skills/memoryplugin/SKILL.md)
- The MCP adapter implements bucket/category navigation, search, chat-history retrieval, summary/full transcript/export, uploaded-file search, and memory updates against memoryplugin.com. Recall schemas include dates, per-query token budgets, and speed/quality modes; source references include conversation/message IDs and dates. It checks token availability and reports API errors. The public adapter does not establish hosted retrieval quality, isolation, retention, or backend implementation, and no tests were present in its eight-entry tree. [Adapter source](https://github.com/memoryplugin/mcp-server/blob/dd27c76a9a12818c64f71e49cd9b3a56dc8dd54d/src/index.ts)

**Practical application:** keep a compact decision ledger separate from full transcripts. Each ledger entry should state decision, rationale, rejected alternatives, evidence IDs, date, status, and reopening trigger. Retrieve the original receipt before consequential reuse. Preserve user-request changes as dated transitions rather than overwriting history. Export format should retain message IDs, timestamps, and lineage; a summary is an index, not the authoritative audit record.

### ProactiveAgent

Do not optimize for unsolicited activity
- The event-driven agent gathers observations, proposes a task or null, and uses locks/listener suspension while executing. With its optional reward model it retries rejected proposals up to three times, then skips. The useful structure is observe → propose/abstain → evaluate → authorized execution, not “always do something.” Repeated proposal generation can also encourage judge gaming; bound it by utility and interruption costs. [Agent loop](https://github.com/thunlp/ProactiveAgent/blob/3fcf9beebe256b86871659fbb12541c41c9381b9/gym/components/activeagent.py)
- The desktop agent module uses an acceptance callback for proposal execution. This is a useful approval boundary, but UI acceptance is not a substitute for scoped authorization checks on each consequential tool. [Desktop module](https://github.com/thunlp/ProactiveAgent/blob/3fcf9beebe256b86871659fbb12541c41c9381b9/agent/agentmodule.py)
- Evaluation computes precision, recall, accuracy, F1, false alarm, and acceptance rates. Here false alarm is FP/(TP+FP), i.e. false-discovery share, **not** conventional FP/(FP+TN). Acceptance rate algebraically duplicates precision under the same counting. The loop zips predictions/judgments, so incomplete paired data can silently undercount observations. [Metrics source](https://github.com/thunlp/ProactiveAgent/blob/3fcf9beebe256b86871659fbb12541c41c9381b9/eval/calculate_agent_performance.py)
- Judgments use a model, not observed economic outcomes. The offline judge bounds retries, while the reward component’s Tenacity retry loop lacks an explicit stop condition in the inspected file. For Shipyard add retry count, absolute deadline, request budget, and cancellation. [Offline judge](https://github.com/thunlp/ProactiveAgent/blob/3fcf9beebe256b86871659fbb12541c41c9381b9/eval/judge_agent_prediction.py) · [Reward component](https://github.com/thunlp/ProactiveAgent/blob/3fcf9beebe256b86871659fbb12541c41c9381b9/gym/components/reward.py)

**Practical application:** proactive actions should be triggered by concrete events: awaited CI completed, evidence became stale, a market session opened, a prior hypothesis hit an invalidation condition, or a pending provider recovered. Distinguish read-only investigation from order-like mutation. Track false alerts per session, missed critical events, median time-to-detection, interruption cost, provider spend, and whether the next action actually improved a verified outcome.


## Execution creativity and workflow findings


### Custom instruction methods

Repository: [DenisSergeevitch/chatgpt-custom-instructions](https://github.com/DenisSergeevitch/chatgpt-custom-instructions).

Inspected v2 in full. Useful: preserve context, concrete answers, consult multiple search results, count repeated failures. Reject invented expert/award identities, tips/penalties as evidence, blanket 'write your own code before looking' and context-free retry rules. README-style +7% MMLU claim is not a reproduced trading-task evaluation; no benchmark harness appears in the six-entry tree.

**Pinned source references**
- [v2.md](https://github.com/DenisSergeevitch/chatgpt-custom-instructions/blob/908b18e13e33b86736e4d2eecb76245e9c33a474/v2.md)

### Repository discovery and selective retrieval

Repository: [taishi-i/awesome-ChatGPT-repositories](https://github.com/taishi-i/awesome-ChatGPT-repositories).

Inspected search data builder and selected search-skill portions. Builder creates compact category shards and deterministic standalone copies with exactly-once replacement checks. Its quality score measures description/topic/language/license metadata richness and its normalized stars measure popularity—not correctness, security, or expected trading value. Reuse selective retrieval and generated-copy drift checks; never rank adoption by stars alone.

**Pinned source references**
- [plugins/awesome-chatgpt-search/build_data.py](https://github.com/taishi-i/awesome-ChatGPT-repositories/blob/0e5cbe4bb147d74ee5b38028fd8da0632e6cc1ee/plugins/awesome-chatgpt-search/build_data.py)
- [skills/awesome-chatgpt-search/SKILL.md](https://github.com/taishi-i/awesome-ChatGPT-repositories/blob/0e5cbe4bb147d74ee5b38028fd8da0632e6cc1ee/skills/awesome-chatgpt-search/SKILL.md)

### Verification and independent development review

Repository: [obra/superpowers](https://github.com/obra/superpowers).

Read verification-before-completion and pressure-testing reference; inspected subagent-development workflow. Strongest transfer: identify a claim's proof, run full check, read output/exit status, and only then claim success. Reviewer must independently inspect code/spec, not trust implementer. Test procedural skills with baseline-versus-candidate pressure scenarios. Do not import absolute rhetoric, automatic deletion of work, claims of 'bulletproof' reliability, or discretionary scope expansion; preserve actual authorization and holdout scenarios.

**Pinned source references**
- [skills/verification-before-completion/SKILL.md](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/verification-before-completion/SKILL.md)
- [skills/subagent-driven-development/SKILL.md](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/subagent-driven-development/SKILL.md)
- [skills/writing-skills/references/testing-skills-with-subagents.md](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/writing-skills/references/testing-skills-with-subagents.md)

### Explicit browser workflow states

Repository: [Wangnov/chatgpt-skill](https://github.com/Wangnov/chatgpt-skill).

Read Codex workflow and error/limit guidance. Useful: exact conversation/model/app context, visible-state-based action, no silent model downgrade, terminal states COMPLETE/NEEDS_USER_INPUT/TIMEOUT/ERROR, no session-token extraction. Browser-completion heuristics (disclaimer plus absence of stop) are not robust causal proof. Its specific polling timeouts, browser runtime, download confirmations and defaults are repository guidance, not the active project policy. Prefer official connected tools already present.

**Pinned source references**
- [codex-chatgpt-skill/SKILL.md](https://github.com/Wangnov/chatgpt-skill/blob/0dab47ec4bd7966e1a714bac45ad3c4e935f0f4c/codex-chatgpt-skill/SKILL.md)
- [codex-chatgpt-skill/references/error-and-limits.md](https://github.com/Wangnov/chatgpt-skill/blob/0dab47ec4bd7966e1a714bac45ad3c4e935f0f4c/codex-chatgpt-skill/references/error-and-limits.md)

### Strict output validation and exact parent checkpoints

Repository: [miuuyy/codex-chatgpt-web](https://github.com/miuuyy/codex-chatgpt-web).

Read strict output validator, retry policy, rolling checkpoint, and selected security-model sections. Validator disables coercion, default insertion and removal of extra properties; malformed/schema-invalid output is explicit failure. Retry count is process-local across adapter instances with TTL, not globally durable. Checkpoint is bound to exact parent answer SHA-256, thread and source turn, rejects user-revision changes, bounds size/count/age and writes atomically. Strong patterns for resume/replay; browser bridge itself adds session/tunnel trust boundaries and is not recommended for installation.

**Pinned source references**
- [src/adapters/chatgpt-web/retry-policy.ts](https://github.com/miuuyy/codex-chatgpt-web/blob/860fa576eb47d9e20d7d8289235bfea94392d2fd/src/adapters/chatgpt-web/retry-policy.ts)
- [src/adapters/chatgpt-web/output-validation.ts](https://github.com/miuuyy/codex-chatgpt-web/blob/860fa576eb47d9e20d7d8289235bfea94392d2fd/src/adapters/chatgpt-web/output-validation.ts)
- [src/adapters/chatgpt-web/rolling-checkpoint.ts](https://github.com/miuuyy/codex-chatgpt-web/blob/860fa576eb47d9e20d7d8289235bfea94392d2fd/src/adapters/chatgpt-web/rolling-checkpoint.ts)
- [docs/security-model.md](https://github.com/miuuyy/codex-chatgpt-web/blob/860fa576eb47d9e20d7d8289235bfea94392d2fd/docs/security-model.md)

### A taxonomy for useful initiative

Repository: [tao-hpu/awesome-proactive-agents](https://github.com/tao-hpu/awesome-proactive-agents).

Inspected taxonomy and decision/evaluation sections. Useful field-map distinction: signals -> decision -> action -> memory -> evaluation; intervention has benefit and interruption cost, with stay-silent/ask/act alternatives. Cited papers and numerical claims were not independently audited; repository is a secondary discovery map, not a validated model or Shipyard alpha evidence.

**Pinned source references**
- [README.md](https://github.com/tao-hpu/awesome-proactive-agents/blob/d2696d99d30c74d9f98724d230c7fb8fd27fc5fb/README.md)

### Architecture specifications versus executable guarantees

Repository: [fainir/most-capable-agent-system-prompt](https://github.com/fainir/most-capable-agent-system-prompt).

Inspected introduction and targeted reliability, memory, governance, eval sections of long README; did not read every 134,610 character. It explicitly distinguishes probabilistic prompting from enforced schemas/state machines. Useful: goal-to-task-to-verification-to-memory closed loop, hot/warm/cold plus episodic/semantic/procedural memory, evidence-backed autonomy and failure-injection/holdout evals. This is an architecture specification, not proof its promised runtime exists. Do not paste giant prompt or auto-bootstrap it into existing project.

**Pinned source references**
- [README.md](https://github.com/fainir/most-capable-agent-system-prompt/blob/d2e533d6b489550e23ee038e6e4dd3510b3b5263/README.md)

### Conversation graphs and reusable prompt chains

Repository: [saeedezzati/superpower-chatgpt](https://github.com/saeedezzati/superpower-chatgpt).

Inspected manifest and relevant autosave/prompt-chain code portions. Autosave preserves conversation graph, parent/child IDs, current node and updates local storage; prompt chains save ordered steps and user controls. Useful archival/recipe concepts, not self-improving intelligence. Snapshot manifest targets chat.openai.com and broad local storage; source snapshot cannot establish current store-extension behavior. Archive permissions/privacy and UI drift need separate review.

**Pinned source references**
- [scripts/content/autoSave.js](https://github.com/saeedezzati/superpower-chatgpt/blob/d10a491cd1e45104ee31b8c43816dafb2ccd4ed4/scripts/content/autoSave.js)
- [scripts/content/promptChain.js](https://github.com/saeedezzati/superpower-chatgpt/blob/d10a491cd1e45104ee31b8c43816dafb2ccd4ed4/scripts/content/promptChain.js)
- [manifest.json](https://github.com/saeedezzati/superpower-chatgpt/blob/d10a491cd1e45104ee31b8c43816dafb2ccd4ed4/manifest.json)

### Citation preserving and idempotent exports

Repository: [pionxzh/chatgpt-exporter](https://github.com/pionxzh/chatgpt-exporter).

Inspected JSON export and conversation/citation tests. Tests preserve raw conversation, merge continuation nodes deterministically, retain citation URLs and make repeated processing idempotent. Useful two-layer archival: raw source stays untouched; normalized human-readable view retains provenance. Tests were read, not run; export completeness against current live UI is unverified.

**Pinned source references**
- [src/exporter/json.ts](https://github.com/pionxzh/chatgpt-exporter/blob/6935bc1f9aba3a8767755d01fecaf31420f3bc19/src/exporter/json.ts)
- [tests/citations.test.ts](https://github.com/pionxzh/chatgpt-exporter/blob/6935bc1f9aba3a8767755d01fecaf31420f3bc19/tests/citations.test.ts)
- [tests/process-conversation.test.ts](https://github.com/pionxzh/chatgpt-exporter/blob/6935bc1f9aba3a8767755d01fecaf31420f3bc19/tests/process-conversation.test.ts)

### Stale result protection and redaction limits

Repository: [ChatGPTBox-dev/chatGPTBox](https://github.com/ChatGPTBox-dev/chatGPTBox).

Read redaction source/tests and stale-task test cases; inspected toolbar implementation. Tests require newest async result to win, ignore late results after unmount, contain stale errors, and preserve usability after current failure. Redaction handles nested/circular structures and key-based sensitive fields, but arbitrary secret values under innocuous keys can remain; prefer allowlisted public receipts. Apply request-generation IDs to Shipyard UI so old provider results cannot overwrite newer runs.

**Pinned source references**
- [tests/unit/background/redact.test.mjs](https://github.com/ChatGPTBox-dev/chatGPTBox/blob/827f43f6d9212356f1d5dc686c718f41f1345011/tests/unit/background/redact.test.mjs)
- [tests/unit/components/floating-toolbar-stale-tasks.test.mjs](https://github.com/ChatGPTBox-dev/chatGPTBox/blob/827f43f6d9212356f1d5dc686c718f41f1345011/tests/unit/components/floating-toolbar-stale-tasks.test.mjs)

### Least privilege scanning and public output allowlists

Repository: [hashgraph-online/awesome-ai-plugins](https://github.com/hashgraph-online/awesome-ai-plugins).

Read scanner guide and sanitizer code. Useful: pin source SHA/workflow identity, least-privilege scans, sanitize by allowlisting fields, omit source snippets/freeform scanner text, validate path/rule/severity/line ranges. A >=75 listing score and advisory severity are catalog policy, not a safety guarantee. Do not let scanner badge authorize execution; the project's high-risk gates should be explicit.

**Pinned source references**
- [SCANNER_GUIDE.md](https://github.com/hashgraph-online/awesome-ai-plugins/blob/b827da80ad8653a40b7d11d5f66b44b0e9bbb10d/SCANNER_GUIDE.md)
- [scripts/sanitize-scan-report.py](https://github.com/hashgraph-online/awesome-ai-plugins/blob/b827da80ad8653a40b7d11d5f66b44b0e9bbb10d/scripts/sanitize-scan-report.py)

### Plugin catalogs as discovery aids

Repository: [Asdivyansh/Awesome-ChatGPT-Plugins](https://github.com/Asdivyansh/Awesome-ChatGPT-Plugins).

Inspected README introductory structure and scientific-research catalog. It is a categorized snapshot with links, not implementation evidence for listed plugins. Use to discover capabilities, then verify publisher/source, current tool schemas, permissions, live availability and relevance. No catalog entry was connected or installed.

**Pinned source references**
- [README.md](https://github.com/Asdivyansh/Awesome-ChatGPT-Plugins/blob/af16f22c10cf18d572359eea6683bce11d432308/README.md)
- [catalog/scientific-research.md](https://github.com/Asdivyansh/Awesome-ChatGPT-Plugins/blob/af16f22c10cf18d572359eea6683bce11d432308/catalog/scientific-research.md)

### Invariants hypothesis lineage and disconfirming search

Repository: [findscripter/everything-skills](https://github.com/findscripter/everything-skills).

Read invariant-contract, idea-evolution, self-reflection skills and disconfirming-search script. Useful: contract/invariant/termination/boundary table before nontrivial algorithms; provenance and parent/child lineage for hypotheses; novelty must be balanced by feasibility, value and verifiability; explicit step-back bias check. Found denominator bug in search-remediation calculation: `ceil(.3*N-D)` is insufficient when additional searches grow total; use `max(0,ceil((.3*N-D)/.7))`. For N=10,D=2, existing recommendation 1 produces 27.3%, correct minimum 2 gives 33.3%. Threshold and weighted idea scores remain unvalidated heuristics. Preserve upstream licenses; some adaptation revision provenance is explicitly unrecorded.

**Pinned source references**
- [00-meta/invariant-guard-correctness/SKILL.md](https://github.com/findscripter/everything-skills/blob/060d87e68bd0c1f8e50747d7c7782bb41d165058/00-meta/invariant-guard-correctness/SKILL.md)
- [00-meta/idea-darwin-evolution/SKILL.md](https://github.com/findscripter/everything-skills/blob/060d87e68bd0c1f8e50747d7c7782bb41d165058/00-meta/idea-darwin-evolution/SKILL.md)
- [00-meta/agent-self-reflection/SKILL.md](https://github.com/findscripter/everything-skills/blob/060d87e68bd0c1f8e50747d7c7782bb41d165058/00-meta/agent-self-reflection/SKILL.md)
- [00-meta/entity-research-dossier/scripts/disconfirming_evidence_balance.py](https://github.com/findscripter/everything-skills/blob/060d87e68bd0c1f8e50747d7c7782bb41d165058/00-meta/entity-research-dossier/scripts/disconfirming_evidence_balance.py)

## Selected siliconjungle findings

### Fact extraction and unsafe entity matching

Repository: [siliconjungle/llm-fact-log](https://github.com/siliconjungle/llm-fact-log).

Pinned commit `23cca3fbc7c7e6cb377269019d33b421856f02ce`. The index.js source was inspected. Extracts subject/relation/object triples and uses embeddings to map unknown entities, but lacks source/time/confidence fields and silently returns [] on extraction failure. findClosestEmbedding minimizes the imported cosine-similarity result; under ordinary cosine similarity semantics this picks least similar, not nearest. Treat as a prototype/negative lesson, not factual memory for trading. Preserve canonical entity IDs and return unknown rather than force-match.

- [index.js](https://github.com/siliconjungle/llm-fact-log/blob/23cca3fbc7c7e6cb377269019d33b421856f02ce/index.js)

### Minimal retry helpers and missing production controls

Repository: [siliconjungle/cascade-retries](https://github.com/siliconjungle/cascade-retries).

Pinned commit `a4a63aacbddda9179bf9fca52ef60b99a881a35a`. The complete index.js was inspected. Small recursive retry/backoff and debounce helpers. No error classification, Retry-After handling, jitter, cancellation, idempotency, shared budget or telemetry. Useful minimal mechanism, not production provider-policy design; retries must never evade denial or duplicate simulated/external actions.

- [index.js](https://github.com/siliconjungle/cascade-retries/blob/a4a63aacbddda9179bf9fca52ef60b99a881a35a/index.js)

### Target owned evidence and failure preserving benchmarks

Repository: [siliconjungle/-shapeshift-labs-evidence-kit](https://github.com/siliconjungle/-shapeshift-labs-evidence-kit).

Pinned commit `be1bfdac003704ebe73520bdf76ee707558b48d3`. Read target-evidence-designer and benchmark-guardian skills plus result schema. Best transfer: derive contracts from target sources before fuzz generator; preserve reduced failure corpus; benchmark a specific hypothesis with fixture/metric/threshold; retain timeout/error/unsupported/bad-result rows; cite source manifests and dirty-baseline caveats. JSON schema is permissive (free-form status, additionalProperties), so it alone cannot enforce safe promotion.

- [schemas/benchmark-result.schema.json](https://github.com/siliconjungle/-shapeshift-labs-evidence-kit/blob/be1bfdac003704ebe73520bdf76ee707558b48d3/schemas/benchmark-result.schema.json)
- [skills/target-evidence-designer/SKILL.md](https://github.com/siliconjungle/-shapeshift-labs-evidence-kit/blob/be1bfdac003704ebe73520bdf76ee707558b48d3/skills/target-evidence-designer/SKILL.md)
- [skills/benchmark-guardian/SKILL.md](https://github.com/siliconjungle/-shapeshift-labs-evidence-kit/blob/be1bfdac003704ebe73520bdf76ee707558b48d3/skills/benchmark-guardian/SKILL.md)

### Explicit gates and protected acceptance policy

Repository: [siliconjungle/-shapeshift-labs-frontier-agent-kit](https://github.com/siliconjungle/-shapeshift-labs-frontier-agent-kit).

Pinned commit `f731df03fea608b642d68ba2db0d132100f72c9f`. Read evidence-plan functions and relevant types. Explicit gate status passed/failed/skipped/missing and acceptance passed/failed/missing/unknown; evidence IDs and checkpoints. Default evidence-present criterion is only a custom expression, not adequate proof of financial correctness. Gate merging allows manifest overrides by ID, so required gate policy should be protected outside a proposed feature manifest.

- [src/evidence.ts](https://github.com/siliconjungle/-shapeshift-labs-frontier-agent-kit/blob/f731df03fea608b642d68ba2db0d132100f72c9f/src/evidence.ts)
- [src/types.ts](https://github.com/siliconjungle/-shapeshift-labs-frontier-agent-kit/blob/f731df03fea608b642d68ba2db0d132100f72c9f/src/types.ts)


## A reliable agent system blueprint

### Evidence is a typed contract

Every forecast, signal, backtest row and simulated-order proposal should refer to a run manifest containing:
- run ID; code commit; configuration, model/prompt and data/schema versions; environment=simulation;
- source IDs/URIs and content hashes; symbol/canonical instrument; dataset and adjustment/revision policy;
- observation, publication, availability, fetch, market-session and decision timestamps with timezone;
- explicit gate states: passed, failed, missing, degraded, stale, clock-ambiguous, skipped, not-applicable;
- exact check command/fixture, exit code, raw receipt location, reviewer finding and unresolved limitations;
- provider call budget, retries, cache origin and cancellation identity.

Only the documented mandatory subset may authorize the next phase. Missing is not passed. Similarity is not truth. Schema-valid is not economically correct. Data freshness is not historical availability. Put deterministic gates in code; prompting explains them, but cannot replace them.

### Durable memory with retrieval discipline
Use separate stores/views for raw receipts, decision ledger, hypotheses, validated procedures and preferences. Each memory has namespace, source ID, known-at/valid-at times, status, supersedes link, review state and expiry/revalidation trigger. Recall narrow IDs/subjects first, then inspect originals. Reject forbidden namespaces and future knowledge after retrieval, joins, graph expansion and cache hydration. Preserve original data, keep normalized display reversible where practical, and distinguish extraction failure from an empty fact set.

Resume only from a checkpoint tied to exact task/run/commit/input hashes. Recover pending state and reconcile uncertain effects before retry. Atomic persistence protects against torn files; it does not by itself prove truth, authorization or durable multi-process concurrency.

### Initiation policy
Eligible triggers: awaited CI reaches terminal state; data freshness expires; source correction arrives; hypothesis falsifier is hit; provider recovers; authorized session milestone occurs. Maintain an event fingerprint and cooldown, suppress duplicates, and allow observe/abstain/ask/propose as first-class results. Evaluate expected usefulness against notification, provider and error costs. Existing user monitoring instructions determine stopping conditions; do not invent early cutoffs.

Read-only investigation may proceed within scope. Scope expansion, plugin connections, sensitive uploads, order submission, deployment or other external mutation still need the applicable authority. Nothing learned from a repository grants authority.

### Independent review and promotion
Separate implementer from reviewer. Reviewer receives requirement contract, exact diff/commit, fixtures, receipts and known gaps. Verify both specification and correctness. Review cannot be replaced by repeated agreement from similar agents. Before promotion, rerun affected gates on the final immutable candidate and record unrun checks.

A skill/prompt change is a versioned candidate, not a permanent increase in intelligence. Compare baseline and candidate on the same frozen corpus, then untouched holdout cases; repeat trials to estimate instability. Preserve old artifacts and rollback path. Do not tune to the holdout or hide abstentions, failed retrievals, timeouts and over-budget runs.

### Useful creativity
Keep hypothesis cards with mechanism, source, parent hypotheses, predicted observable, falsifier, data eligibility, baseline, cost model and evaluation status. Generate genuinely different mechanisms rather than paraphrases. Screen feasibility and verifiability before costly simulations. Promote only on held-out, leakage-controlled evidence, not weighted prose scores, popularity, judge approval or a good narrative. Log rejected hypotheses and reasons to avoid rediscovery loops.


## Applying the findings without duplicating existing work

### Existing controls and their limits

The project inspection found substantial related work already present. The following statements describe inspected source and protocols, not a new deployment validation.

- **Layered durable memory and contrary cases:** the existing design already separates evidence, semantic, episodic, portfolio and prospective memory, with source IDs, precedence and contrary examples. The useful next step is measuring retrieval and closing handoff gaps, not introducing another memory service.
- **Recovery and uncertain writes:** existing protocols specify guarded replacement, backup, reload on conflict and independently retained heads, with no speculative replay. Cross-environment recovery was not tested in this pass.
- **Chronology and value integrity:** existing verification enforces exact evidence fields, finite JSON, a value hash, ordered observation and availability clocks, rejection of unknown clocks and stale-data flags. The remaining distinction is important: caller-supplied clock and source strings are claims, and a hash of the supplied value proves self-consistency rather than linkage to original receipt bytes.
- **Holdouts and learning review:** existing candidate evaluation includes prospective cohorts, first families, no holdout reuse, complete grades and disabled adoption. Source authenticity, resolution and independence remain explicitly unverified; these honest restrictions must not be weakened.
- **Bounded initiative:** the existing implementation includes denial handling, budgets, claims, expiry to uncertain state, freshness dependencies and inspection of outcomes before replay. It does not need a second scheduler or an unbounded proactive loop.
- **Mutation receipts:** the existing boundary uses scoped atomic insertion, exact input hashes, immutable terminal status, sanitized projections and readback, with associated tests. Reuse it rather than adding another receipt store.
- **Content pinned continuation:** content identity already covers data, selection, quality and build, while actual acquisition clocks remain separate per page. Equal content identity must not be interpreted as one acquisition event.
- **Status distinctions and redaction:** existing projections preserve stored but not requalified, research only and decision ineligible states; tests include secret canaries. New ingestion must preserve these restrictions, not merely display warning text.

### What has actually been implemented

A local, isolated shadow receipt-binding validator now exists. An independent local rerun recorded 83 passing tests on 31 October 2026 at 16:14:59 UTC: 53 legacy tests and 30 new tests. The test run did not mutate an operational ledger or canonical project state, access a database or network, or deploy anything. A builder's separate dry validation against an archived receipt was not repeated by the independent test rerun and is not interchangeable with that 83-test result.

This is **tested local shadow code, not adopted production behavior**. It does not establish source authenticity, resolve the external trust-anchor problem, prove historical availability, produce financial eligibility or adopt a strategy. The expanded contract below is the design target; the aggregate test count should not be read as proof that every future producer adapter or downstream integration requirement has been completed.

### The lifecycle correction

An earlier project mapping looked at the core entry workflow and missed a preserved isolated position-review candidate. That led to an unnecessary suggestion to start a new lifecycle design. The corrected recommendation is to review and extend the existing candidate, not duplicate it.

The candidate already provides HOLD, TRIM and EXIT review intents while leaving legacy WAIT and TRADE behavior unchanged. It includes position, source, mark and risk schemas; strict quantity and risk non-increase; separate subjective management-quality review; and provisional lessons. Its retained receipt reports exact-patch clean replay with 64 of 64 focused tests. The archived patch digest was checked against the retained receipt, but this correction did not rerun those tests, apply the patch, verify packaging or establish canonical integration.

The genuine missing boundary is source reconciliation. The candidate checks the shape of a source reference hash and cross-checks supplied snapshots and evidence, but does not hash-bind original receipt bytes to position identity, instrument, quantity, cost basis, risk and mark. It deliberately leaves source reconciliation and authenticity false. Operational and forward-validation eligibility remain false, and execution and automatic adoption remain disabled.

Before integration, the existing candidate needs independent current-baseline compatibility review and exact-candidate replay. Entry-output and hash compatibility must remain unchanged, and management-review metrics must retain denominators separate from entry decisions. An advisory receipt-binding success must not elevate its existing false eligibility flags. This was a correction to our project mapping, not a defect attributed to any external repository.

### Durable improvement versus proposals

A durable implementation means versioned project code, tests, persistent records and recoverable state, plus explicitly authorized schedule changes where needed. A prompt or skill can express a procedure, but does not install storage, guarantee that a gate runs or permanently increase model intelligence. This research itself did not add a new hosted memory service, scheduler or automatic strategy-adoption path.

Authorization to implement useful findings is a separate fact from completion. At this snapshot, the new receipt-binding work remains shadow-only and unadopted; the position-review candidate remains isolated; the remaining experiments below remain proposals. Any subsequent deployment or adoption needs its own current receipts and status report.

## Receipt binding design and acceptance contract

### A narrow offline boundary

The smallest useful next boundary is a pure standard-library validator with an interface equivalent to `validate_receipt_binding(case, bindings, captured_receipts, trusted_manifest)`. Begin with exactly one versioned captured-receipt format from a verified producer. Unknown producer and schema versions fail closed. Do not generalize prematurely across every engine.

Inputs are local in-memory JSON and original bytes supplied by an authorized caller. The validator does not need network access, shell execution, dynamic imports, URL fetching, user-selected filesystem paths, account access, order calls, automatic adoption or raw-provider republication. Keep bindings in a separate sidecar because the current evidence schema is exact; adding fields casually would break compatibility.

### Required validation sequence

1. Verify raw receipt bytes against an independently selected trusted manifest before extraction. Reject duplicate evidence IDs, missing artifacts, unknown schemas or fields and nonfinite values.
2. Extract through a fixed, versioned producer adapter. Compare the canonical typed value to the case value and existing value hash without number-to-string coercion.
3. Compare source, instrument, observation and availability clocks to the verified receipt fields. A caller must not backdate availability or remove research-only and decision-ineligible restrictions.
4. Keep content pagination identity distinct from capture identity. Equal content hashes with different acquisition clocks do not prove one capture. Bind every page to its own receipt and identify any combined collection explicitly.
5. Run the existing learning verification after binding checks. Unknown or ambiguous availability remains blocked. Receipt integrity does not establish historical publication availability, source authenticity, episode resolution, blind review or alpha.
6. Return explicit verified, mismatch, unsupported, missing or degraded binding states, reason codes and content-free hashes. Keep source authenticity false and adoption disabled.
7. Roll out as a shadow report first. Only after independent review should new automated real-receipt ingestion require binding. Legacy cases remain immutable and explicitly unbound; synthetic fixtures remain synthetic.

### Exact proposed envelope

This is a versioned target contract, not a claim that all current producers already emit it.

- Envelope fields: `schema=PRACTICE_RECEIPT_BINDING_V1`, `case_id`, `decision_at` and `bindings`.
- Each binding: `evidence_id`, `artifact_id`, `producer_schema`, `adapter_version`, `selector_id`, `expected_instrument`, `value_sha256` and `capture_bytes_sha256`.
- Reject additional fields initially. Digests are 64 lowercase hexadecimal characters; IDs are bounded strings; timestamps require timezone information.
- Selector IDs resolve to fixed, source-owned adapter functions, never executable JSONPath, scripts, URLs or filesystem paths.
- The separately obtained trusted manifest maps artifact identities to a capture digest and canonical version anchor. Calling a manifest trusted does not authenticate it. Its authority must be established independently of the receipt under test.
- Captured receipts map those identities to immutable original bytes. Validate the byte digest before parsing; enforce byte, nesting-depth and container limits; reject duplicate JSON keys to prevent parser disagreement.

### Four hashes with different meanings

- `value_sha256` is the hash of the canonical evidence value. It detects inconsistency only relative to the value being hashed.
- `capture_bytes_sha256` identifies the exact original receipt bytes.
- `content_snapshot_sha256`, when present, represents producer content or pagination identity, not an acquisition event.
- An optional `collection_sha256` identifies an ordered list of captures. It does not imply simultaneous acquisition.

These hashes are not interchangeable. Altering a case and recomputing its value hash must not defeat the source comparison. Altering a receipt and supplying a new digest must not defeat an unchanged independently anchored manifest. Rewriting both receipt and manifest exposes the external trust problem that a pure validator cannot solve alone.

### Temporal trust boundary

The adapter extracts original source and instrument, value, observation time, original availability time, capture time and restrictions from verified bytes, not envelope assertions. Require `observation_at <= original_available_at <= decision_at`. A recent fetch of old data does not prove that revised information was available historically.

When a producer exposes only retrieval time, that field documents capture rather than earlier publication. A post-decision capture can receive integrity-only verification, while historical eligibility remains unverified unless an independently anchored contemporaneous receipt establishes original availability. Missing publication or availability semantics must not be invented. Original position, event and decision identity, quantity, cost, risk and mark need the same treatment when extending the existing management candidate.

### Public result allowlist

The intended output fields are schema, case identity, binding status, reason codes, adapter version, value and capture hashes, historical eligibility, and fixed restriction flags. Binding status is one of verified, mismatch, unsupported, missing or degraded. Historical eligibility is verified, unverified or ineligible. Keep `source_authenticity_verified=false`, `decision_eligible=false`, `adoption_disabled=true` and `mode=shadow`.

Do not expose evidence values, raw provider text, secret-bearing URLs, local paths or private account and request identifiers. A shadow report does not record a case, establish source independence, deploy code or adopt a strategy. Exposure restrictions remain authoritative.

### Exact acceptance cases

- A synthetic versioned receipt with trusted digest and matching value and clocks binds successfully.
- Change a value and recompute only the case hash: the old self-hash check may pass, but source comparison must reject it. Preserve a red-to-green regression for this case.
- Change the claimed source or backdate availability without changing receipt bytes: reject.
- Alter receipt bytes and recompute only the caller-supplied digest while the independent manifest remains unchanged: reject.
- Give equal content hashes different acquisition clocks: never conflate the captures.
- Reject an unknown producer version, absent artifact, naive or future clock, wrong instrument, duplicate binding, nonfinite JSON, duplicate JSON keys and unsupported field selection with explicit reasons.
- Do not turn a research-only receipt into decision-eligible evidence or relabel a retrospective case as prospective. Integrity cannot prove an administrator had not already seen the outcome.
- Keep output free of raw values and private identifiers. Keep legacy practice, simulation, initiative and packaging behavior unchanged on the final candidate.

Acceptance requires the exact expected result for every fixture, no permission or eligibility elevation, and unchanged legacy replay behavior. An aggregate score or a passing subset cannot replace that contract. Canonical writeback remains a separate reviewed step.

## Evaluation and remaining implementation priorities

### A minimum regression matrix


1. Future-published revision of old bar; unknown timestamp; DST boundary; holiday/weekend; incomplete current session.
2. Wrong-symbol/entity near-match; wrong namespace; deleted/superseded memory returned by cache.
3. Malformed JSON, unexpected fields, nonfinite numeric value, schema-valid but impossible return.
4. Timeout after accepted mutation; duplicate request; cancellation; quota exhaustion; revoked permission.
5. Out-of-order provider completion; old result after navigation/unmount; stale error after fresh success.
6. Summary omits contrary evidence; citation URL lost; raw conversation mutated by rendering.
7. Candidate passes focused test but fails full gate; stale evidence from pre-fix commit; missing reviewer artifact.
8. No-event proactivity; duplicate-event proactivity; important event missed; rejected notification repeated.
9. Memory/skill prompt injection; public receipt contains secret under innocent field name.
10. Search-budget denominator invariant: after suggested additions, target ratio actually holds.

### Metrics and decision criteria
Report end-to-end verified completion, coverage, abstention/degraded rates, false alerts and misses, latency p50/p95, provider requests/cost, intervention rate, replay stability, regressions and evidence completeness. Keep per-case rows. Distinguish a conditional accuracy denominator from all attempted tasks. Project owners must define acceptable thresholds before seeing candidate results. No repository's generic score is an institutional acceptance threshold.


### Memory and initiative cases that must remain visible

Memory tests should include a stale correction resurrected through cache, a wrong-project candidate, an unsupported lexical near-match, a later-published historical revision, an unknown clock, a future fact introduced after expansion, incomplete provenance, an unavailable authority database and a duplicate or uncertain write. Reapply hard scope and temporal admission after joins, fallback providers, graph expansion and cache hydration.

Initiative tests should include no event and no alert, duplicate-event deduplication, accepted and rejected proposals, revoked scope, expired permission, an unavailable judge, exhausted budgets, cancellation and ownership of a terminal outcome. Existing user monitoring instructions define the stopping condition; a pending or unchanged result is not automatically completion.

### Honest measurement

Freeze code, data, calendar and configuration in a run manifest before comparing baseline and candidate. Run identical traces and preserve failures, abstentions, unsupported cases, timeouts, budget failures and missing observations. Report all attempted tasks separately from conditional answer accuracy, together with p50 and p95 latency and cost. A model judge's preference is not an observed economic result.

Supermemory's benchmark documentation excludes failed questions from accuracy and reports success separately. That distinction is useful when presented transparently; a success-only headline would be misleading. Its generic production-readiness bands are not a trading acceptance threshold. [Pinned benchmark measurement documentation](https://github.com/supermemoryai/supermemory/blob/d53d124e4769e34c4be8bcc5d21eed1855b090ef/apps/docs/memorybench/memscore.mdx).

ProactiveAgent's false-alarm label measures false discoveries among positive proposals rather than conventional false-positive rate. Preserve the actual formula and denominator. Its acceptance metric duplicates precision under the same counting, and zipped unmatched predictions and judgments can disappear. Evaluate unmatched records explicitly and retain a per-case ledger rather than trusting aggregate labels.

### Prioritized remaining work

1. **Review the existing position-management candidate.** Apply the offline receipt-binding contract to its actual missing reconciliation boundary. Recheck compatibility and exact replay before integration; preserve all operational, forward-validation and adoption restrictions.
2. **Derive receipt-level operating metrics.** Count attempted, succeeded, degraded, abstained and missing outcomes from existing immutable records. Test denominator completeness and unmatched records rather than creating a second telemetry store. Readiness is dependency-specific, not an all-green headline.
3. **Measure retrieval alternatives.** Compare the existing compact decision ledger with a source-linked index on frozen cases. Measure contrary-case recall, chronology violations, unsupported citations and token cost. Use existing local storage; a hosted memory upload is unnecessary.
4. **Pressure-test narrow procedural skills.** Compare a baseline with a versioned procedural addition on frozen scenarios, then untouched holdouts and repeated trials. Accept only measurable benefit without permission drift; preserve the prior version and rollback path.

### Methods to reject or constrain

Do not treat invented expert credentials, rewards or penalties in prompts, popularity, catalog scores, a scanner badge, weighted idea scores, judge approval or confident narrative as empirical evidence. Do not copy context-free retry rules, unbounded reward retries, blanket deletion of work, automatic installation or bootstrap instructions, or claims of bulletproof reliability. Browser completion heuristics and presentational schemas are not causal proof of a completed or economically correct task.

Do not force semantic entity matches, silently convert extraction errors into empty factual results, treat soft time demotion as strict point-in-time exclusion, or let a feature manifest override mandatory safety gates. Do not mistake an optional support gate or newly added time column for enforced runtime policy. Preserve uncertainty where the evidence is absent.

### Licensing security and privacy

No third-party code was adopted by the research pass. Prefer small originally written implementations of behavior contracts using the standard library where practical, while retaining source attribution. Before copying source, inspect the exact pinned license and per-file notices, including transitive or adapted skills; repository metadata is insufficient. The reviewed skills collection includes adapted material with mixed provenance and at least one unrecorded adaptation revision.

Browser extensions and bridges introduce session, tunnel, UI-drift and software-supply-chain risks. Hosted memory adds data transfer, retention, tenancy and backend-isolation questions. Neither is required to obtain the useful engineering lessons here. A service wrapper's public source does not audit the hosted service. Catalog inclusion does not establish availability or authorize connecting a tool.

Use allowlisted public receipts and synthetic fixtures. Key-name redaction alone can miss secret values under harmless keys. Preserve immutable originals privately where authorized, but do not publish personal account information, private conversations, credentials, raw licensed provider captures or internal working records. Public material should contain the methodology, public source pins and privacy-safe evidence summaries.

## Complete public source appendix

The following records identify the exact commits and selected source files behind the findings. A selected file may have been read in full or by substantive sections as described in its chapter. Counts of tree entries include directories; unexamined file counts refer to file paths and therefore are not obtained by subtracting selected files from all tree entries.

MemoryPlugin's skill identifies MemoryPlugin as author and memoryplugin.com as homepage; the adapter uses the same service API. That is a strong source-level identity link, not an independent corporate-ownership attestation. Similarly named unrelated repositories were not substituted.

The requested siliconjungle page-three URL failed with a web cache miss. Search yielded 200 repositories over two result pages; the four below were relevance-selected from that discovery. Search ordering does not prove page-three membership. The exact requested roster and the remaining account repositories remain unresolved or unexamined; this was an access-result limitation, not a permission denial.

### Source record 1

**[supermemoryai/supermemory](https://github.com/supermemoryai/supermemory)**

Default branch: main. Exact commit: [d53d124e4769e34c4be8bcc5d21eed1855b090ef](https://github.com/supermemoryai/supermemory/commit/d53d124e4769e34c4be8bcc5d21eed1855b090ef).

Enumerated tree entries: 1088. Selected content files: 7. Other file paths not substantively reviewed: 932. [Browse the pinned tree](https://github.com/supermemoryai/supermemory/tree/d53d124e4769e34c4be8bcc5d21eed1855b090ef).

- [apps/docs/memorybench/memscore.mdx](https://github.com/supermemoryai/supermemory/blob/d53d124e4769e34c4be8bcc5d21eed1855b090ef/apps/docs/memorybench/memscore.mdx)
- [apps/docs/recall/memory-review.mdx](https://github.com/supermemoryai/supermemory/blob/d53d124e4769e34c4be8bcc5d21eed1855b090ef/apps/docs/recall/memory-review.mdx)
- [apps/mcp/e2e/space-scope.test.ts](https://github.com/supermemoryai/supermemory/blob/d53d124e4769e34c4be8bcc5d21eed1855b090ef/apps/mcp/e2e/space-scope.test.ts)
- [apps/mcp/src/server/client/index.ts](https://github.com/supermemoryai/supermemory/blob/d53d124e4769e34c4be8bcc5d21eed1855b090ef/apps/mcp/src/server/client/index.ts)
- [apps/mcp/src/server/tools/forget-memory.ts](https://github.com/supermemoryai/supermemory/blob/d53d124e4769e34c4be8bcc5d21eed1855b090ef/apps/mcp/src/server/tools/forget-memory.ts)
- [apps/mcp/src/server/tools/save-memory.ts](https://github.com/supermemoryai/supermemory/blob/d53d124e4769e34c4be8bcc5d21eed1855b090ef/apps/mcp/src/server/tools/save-memory.ts)
- [apps/mcp/src/server/tools/search-memory.ts](https://github.com/supermemoryai/supermemory/blob/d53d124e4769e34c4be8bcc5d21eed1855b090ef/apps/mcp/src/server/tools/search-memory.ts)

### Source record 2

**[qualixar/superlocalmemory](https://github.com/qualixar/superlocalmemory)**

Default branch: main. Exact commit: [93e58692ce51b196a879a43e3974d378652db748](https://github.com/qualixar/superlocalmemory/commit/93e58692ce51b196a879a43e3974d378652db748).

Enumerated tree entries: 5303. Selected content files: 9. Other file paths not substantively reviewed: 4833. [Browse the pinned tree](https://github.com/qualixar/superlocalmemory/tree/93e58692ce51b196a879a43e3974d378652db748).

- [src/superlocalmemory/retrieval/scope_policy.py](https://github.com/qualixar/superlocalmemory/blob/93e58692ce51b196a879a43e3974d378652db748/src/superlocalmemory/retrieval/scope_policy.py)
- [src/superlocalmemory/retrieval/snapshot_admission.py](https://github.com/qualixar/superlocalmemory/blob/93e58692ce51b196a879a43e3974d378652db748/src/superlocalmemory/retrieval/snapshot_admission.py)
- [src/superlocalmemory/retrieval/support_gate.py](https://github.com/qualixar/superlocalmemory/blob/93e58692ce51b196a879a43e3974d378652db748/src/superlocalmemory/retrieval/support_gate.py)
- [src/superlocalmemory/retrieval/temporal_validity_filter.py](https://github.com/qualixar/superlocalmemory/blob/93e58692ce51b196a879a43e3974d378652db748/src/superlocalmemory/retrieval/temporal_validity_filter.py)
- [src/superlocalmemory/server/write_governance.py](https://github.com/qualixar/superlocalmemory/blob/93e58692ce51b196a879a43e3974d378652db748/src/superlocalmemory/server/write_governance.py)
- [src/superlocalmemory/storage/migrations/M013_bi_temporal_columns.py](https://github.com/qualixar/superlocalmemory/blob/93e58692ce51b196a879a43e3974d378652db748/src/superlocalmemory/storage/migrations/M013_bi_temporal_columns.py)
- [src/superlocalmemory/trust/provenance.py](https://github.com/qualixar/superlocalmemory/blob/93e58692ce51b196a879a43e3974d378652db748/src/superlocalmemory/trust/provenance.py)
- [tests/test_retrieval/test_support_gate.py](https://github.com/qualixar/superlocalmemory/blob/93e58692ce51b196a879a43e3974d378652db748/tests/test_retrieval/test_support_gate.py)
- [tests/test_retrieval/test_temporal_validity_filter.py](https://github.com/qualixar/superlocalmemory/blob/93e58692ce51b196a879a43e3974d378652db748/tests/test_retrieval/test_temporal_validity_filter.py)

### Source record 3

**[DenisSergeevitch/chatgpt-custom-instructions](https://github.com/DenisSergeevitch/chatgpt-custom-instructions)**

Default branch: main. Exact commit: [908b18e13e33b86736e4d2eecb76245e9c33a474](https://github.com/DenisSergeevitch/chatgpt-custom-instructions/commit/908b18e13e33b86736e4d2eecb76245e9c33a474).

Enumerated tree entries: 6. Selected content files: 1. Other file paths not substantively reviewed: 5. [Browse the pinned tree](https://github.com/DenisSergeevitch/chatgpt-custom-instructions/tree/908b18e13e33b86736e4d2eecb76245e9c33a474).

- [v2.md](https://github.com/DenisSergeevitch/chatgpt-custom-instructions/blob/908b18e13e33b86736e4d2eecb76245e9c33a474/v2.md)

### Source record 4

**[taishi-i/awesome-ChatGPT-repositories](https://github.com/taishi-i/awesome-ChatGPT-repositories)**

Default branch: main. Exact commit: [0e5cbe4bb147d74ee5b38028fd8da0632e6cc1ee](https://github.com/taishi-i/awesome-ChatGPT-repositories/commit/0e5cbe4bb147d74ee5b38028fd8da0632e6cc1ee).

Enumerated tree entries: 84. Selected content files: 2. Other file paths not substantively reviewed: 59. [Browse the pinned tree](https://github.com/taishi-i/awesome-ChatGPT-repositories/tree/0e5cbe4bb147d74ee5b38028fd8da0632e6cc1ee).

- [plugins/awesome-chatgpt-search/build_data.py](https://github.com/taishi-i/awesome-ChatGPT-repositories/blob/0e5cbe4bb147d74ee5b38028fd8da0632e6cc1ee/plugins/awesome-chatgpt-search/build_data.py)
- [skills/awesome-chatgpt-search/SKILL.md](https://github.com/taishi-i/awesome-ChatGPT-repositories/blob/0e5cbe4bb147d74ee5b38028fd8da0632e6cc1ee/skills/awesome-chatgpt-search/SKILL.md)

### Source record 5

**[obra/superpowers](https://github.com/obra/superpowers)**

Default branch: main. Exact commit: [2ce8aa15d05bd57213e6f746f953aafb7ded7a8b](https://github.com/obra/superpowers/commit/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b).

Enumerated tree entries: 300. Selected content files: 3. Other file paths not substantively reviewed: 228. [Browse the pinned tree](https://github.com/obra/superpowers/tree/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b).

- [skills/subagent-driven-development/SKILL.md](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/subagent-driven-development/SKILL.md)
- [skills/verification-before-completion/SKILL.md](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/verification-before-completion/SKILL.md)
- [skills/writing-skills/references/testing-skills-with-subagents.md](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/writing-skills/references/testing-skills-with-subagents.md)

### Source record 6

**[Wangnov/chatgpt-skill](https://github.com/Wangnov/chatgpt-skill)**

Default branch: main. Exact commit: [0dab47ec4bd7966e1a714bac45ad3c4e935f0f4c](https://github.com/Wangnov/chatgpt-skill/commit/0dab47ec4bd7966e1a714bac45ad3c4e935f0f4c).

Enumerated tree entries: 39. Selected content files: 2. Other file paths not substantively reviewed: 27. [Browse the pinned tree](https://github.com/Wangnov/chatgpt-skill/tree/0dab47ec4bd7966e1a714bac45ad3c4e935f0f4c).

- [codex-chatgpt-skill/SKILL.md](https://github.com/Wangnov/chatgpt-skill/blob/0dab47ec4bd7966e1a714bac45ad3c4e935f0f4c/codex-chatgpt-skill/SKILL.md)
- [codex-chatgpt-skill/references/error-and-limits.md](https://github.com/Wangnov/chatgpt-skill/blob/0dab47ec4bd7966e1a714bac45ad3c4e935f0f4c/codex-chatgpt-skill/references/error-and-limits.md)

### Source record 7

**[miuuyy/codex-chatgpt-web](https://github.com/miuuyy/codex-chatgpt-web)**

Default branch: main. Exact commit: [860fa576eb47d9e20d7d8289235bfea94392d2fd](https://github.com/miuuyy/codex-chatgpt-web/commit/860fa576eb47d9e20d7d8289235bfea94392d2fd).

Enumerated tree entries: 378. Selected content files: 4. Other file paths not substantively reviewed: 345. [Browse the pinned tree](https://github.com/miuuyy/codex-chatgpt-web/tree/860fa576eb47d9e20d7d8289235bfea94392d2fd).

- [docs/security-model.md](https://github.com/miuuyy/codex-chatgpt-web/blob/860fa576eb47d9e20d7d8289235bfea94392d2fd/docs/security-model.md)
- [src/adapters/chatgpt-web/output-validation.ts](https://github.com/miuuyy/codex-chatgpt-web/blob/860fa576eb47d9e20d7d8289235bfea94392d2fd/src/adapters/chatgpt-web/output-validation.ts)
- [src/adapters/chatgpt-web/retry-policy.ts](https://github.com/miuuyy/codex-chatgpt-web/blob/860fa576eb47d9e20d7d8289235bfea94392d2fd/src/adapters/chatgpt-web/retry-policy.ts)
- [src/adapters/chatgpt-web/rolling-checkpoint.ts](https://github.com/miuuyy/codex-chatgpt-web/blob/860fa576eb47d9e20d7d8289235bfea94392d2fd/src/adapters/chatgpt-web/rolling-checkpoint.ts)

### Source record 8

**[thunlp/ProactiveAgent](https://github.com/thunlp/ProactiveAgent)**

Default branch: main. Exact commit: [3fcf9beebe256b86871659fbb12541c41c9381b9](https://github.com/thunlp/ProactiveAgent/commit/3fcf9beebe256b86871659fbb12541c41c9381b9).

Enumerated tree entries: 136. Selected content files: 5. Other file paths not substantively reviewed: 113. [Browse the pinned tree](https://github.com/thunlp/ProactiveAgent/tree/3fcf9beebe256b86871659fbb12541c41c9381b9).

- [agent/agentmodule.py](https://github.com/thunlp/ProactiveAgent/blob/3fcf9beebe256b86871659fbb12541c41c9381b9/agent/agentmodule.py)
- [eval/calculate_agent_performance.py](https://github.com/thunlp/ProactiveAgent/blob/3fcf9beebe256b86871659fbb12541c41c9381b9/eval/calculate_agent_performance.py)
- [eval/judge_agent_prediction.py](https://github.com/thunlp/ProactiveAgent/blob/3fcf9beebe256b86871659fbb12541c41c9381b9/eval/judge_agent_prediction.py)
- [gym/components/activeagent.py](https://github.com/thunlp/ProactiveAgent/blob/3fcf9beebe256b86871659fbb12541c41c9381b9/gym/components/activeagent.py)
- [gym/components/reward.py](https://github.com/thunlp/ProactiveAgent/blob/3fcf9beebe256b86871659fbb12541c41c9381b9/gym/components/reward.py)

### Source record 9

**[tao-hpu/awesome-proactive-agents](https://github.com/tao-hpu/awesome-proactive-agents)**

Default branch: main. Exact commit: [d2696d99d30c74d9f98724d230c7fb8fd27fc5fb](https://github.com/tao-hpu/awesome-proactive-agents/commit/d2696d99d30c74d9f98724d230c7fb8fd27fc5fb).

Enumerated tree entries: 7. Selected content files: 1. Other file paths not substantively reviewed: 5. [Browse the pinned tree](https://github.com/tao-hpu/awesome-proactive-agents/tree/d2696d99d30c74d9f98724d230c7fb8fd27fc5fb).

- [README.md](https://github.com/tao-hpu/awesome-proactive-agents/blob/d2696d99d30c74d9f98724d230c7fb8fd27fc5fb/README.md)

### Source record 10

**[fainir/most-capable-agent-system-prompt](https://github.com/fainir/most-capable-agent-system-prompt)**

Default branch: main. Exact commit: [d2e533d6b489550e23ee038e6e4dd3510b3b5263](https://github.com/fainir/most-capable-agent-system-prompt/commit/d2e533d6b489550e23ee038e6e4dd3510b3b5263).

Enumerated tree entries: 4. Selected content files: 1. Other file paths not substantively reviewed: 3. [Browse the pinned tree](https://github.com/fainir/most-capable-agent-system-prompt/tree/d2e533d6b489550e23ee038e6e4dd3510b3b5263).

- [README.md](https://github.com/fainir/most-capable-agent-system-prompt/blob/d2e533d6b489550e23ee038e6e4dd3510b3b5263/README.md)

### Source record 11

**[saeedezzati/superpower-chatgpt](https://github.com/saeedezzati/superpower-chatgpt)**

Default branch: main. Exact commit: [d10a491cd1e45104ee31b8c43816dafb2ccd4ed4](https://github.com/saeedezzati/superpower-chatgpt/commit/d10a491cd1e45104ee31b8c43816dafb2ccd4ed4).

Enumerated tree entries: 139. Selected content files: 3. Other file paths not substantively reviewed: 124. [Browse the pinned tree](https://github.com/saeedezzati/superpower-chatgpt/tree/d10a491cd1e45104ee31b8c43816dafb2ccd4ed4).

- [manifest.json](https://github.com/saeedezzati/superpower-chatgpt/blob/d10a491cd1e45104ee31b8c43816dafb2ccd4ed4/manifest.json)
- [scripts/content/autoSave.js](https://github.com/saeedezzati/superpower-chatgpt/blob/d10a491cd1e45104ee31b8c43816dafb2ccd4ed4/scripts/content/autoSave.js)
- [scripts/content/promptChain.js](https://github.com/saeedezzati/superpower-chatgpt/blob/d10a491cd1e45104ee31b8c43816dafb2ccd4ed4/scripts/content/promptChain.js)

### Source record 12

**[pionxzh/chatgpt-exporter](https://github.com/pionxzh/chatgpt-exporter)**

Default branch: master. Exact commit: [6935bc1f9aba3a8767755d01fecaf31420f3bc19](https://github.com/pionxzh/chatgpt-exporter/commit/6935bc1f9aba3a8767755d01fecaf31420f3bc19).

Enumerated tree entries: 172. Selected content files: 3. Other file paths not substantively reviewed: 146. [Browse the pinned tree](https://github.com/pionxzh/chatgpt-exporter/tree/6935bc1f9aba3a8767755d01fecaf31420f3bc19).

- [src/exporter/json.ts](https://github.com/pionxzh/chatgpt-exporter/blob/6935bc1f9aba3a8767755d01fecaf31420f3bc19/src/exporter/json.ts)
- [tests/citations.test.ts](https://github.com/pionxzh/chatgpt-exporter/blob/6935bc1f9aba3a8767755d01fecaf31420f3bc19/tests/citations.test.ts)
- [tests/process-conversation.test.ts](https://github.com/pionxzh/chatgpt-exporter/blob/6935bc1f9aba3a8767755d01fecaf31420f3bc19/tests/process-conversation.test.ts)

### Source record 13

**[ChatGPTBox-dev/chatGPTBox](https://github.com/ChatGPTBox-dev/chatGPTBox)**

Default branch: master. Exact commit: [827f43f6d9212356f1d5dc686c718f41f1345011](https://github.com/ChatGPTBox-dev/chatGPTBox/commit/827f43f6d9212356f1d5dc686c718f41f1345011).

Enumerated tree entries: 369. Selected content files: 4. Other file paths not substantively reviewed: 279. [Browse the pinned tree](https://github.com/ChatGPTBox-dev/chatGPTBox/tree/827f43f6d9212356f1d5dc686c718f41f1345011).

- [src/background/redact.mjs](https://github.com/ChatGPTBox-dev/chatGPTBox/blob/827f43f6d9212356f1d5dc686c718f41f1345011/src/background/redact.mjs)
- [src/components/FloatingToolbar/index.jsx](https://github.com/ChatGPTBox-dev/chatGPTBox/blob/827f43f6d9212356f1d5dc686c718f41f1345011/src/components/FloatingToolbar/index.jsx)
- [tests/unit/background/redact.test.mjs](https://github.com/ChatGPTBox-dev/chatGPTBox/blob/827f43f6d9212356f1d5dc686c718f41f1345011/tests/unit/background/redact.test.mjs)
- [tests/unit/components/floating-toolbar-stale-tasks.test.mjs](https://github.com/ChatGPTBox-dev/chatGPTBox/blob/827f43f6d9212356f1d5dc686c718f41f1345011/tests/unit/components/floating-toolbar-stale-tasks.test.mjs)

### Source record 14

**[hashgraph-online/awesome-ai-plugins](https://github.com/hashgraph-online/awesome-ai-plugins)**

Default branch: main. Exact commit: [b827da80ad8653a40b7d11d5f66b44b0e9bbb10d](https://github.com/hashgraph-online/awesome-ai-plugins/commit/b827da80ad8653a40b7d11d5f66b44b0e9bbb10d).

Enumerated tree entries: 46. Selected content files: 2. Other file paths not substantively reviewed: 37. [Browse the pinned tree](https://github.com/hashgraph-online/awesome-ai-plugins/tree/b827da80ad8653a40b7d11d5f66b44b0e9bbb10d).

- [SCANNER_GUIDE.md](https://github.com/hashgraph-online/awesome-ai-plugins/blob/b827da80ad8653a40b7d11d5f66b44b0e9bbb10d/SCANNER_GUIDE.md)
- [scripts/sanitize-scan-report.py](https://github.com/hashgraph-online/awesome-ai-plugins/blob/b827da80ad8653a40b7d11d5f66b44b0e9bbb10d/scripts/sanitize-scan-report.py)

### Source record 15

**[Asdivyansh/Awesome-ChatGPT-Plugins](https://github.com/Asdivyansh/Awesome-ChatGPT-Plugins)**

Default branch: main. Exact commit: [af16f22c10cf18d572359eea6683bce11d432308](https://github.com/Asdivyansh/Awesome-ChatGPT-Plugins/commit/af16f22c10cf18d572359eea6683bce11d432308).

Enumerated tree entries: 40. Selected content files: 2. Other file paths not substantively reviewed: 30. [Browse the pinned tree](https://github.com/Asdivyansh/Awesome-ChatGPT-Plugins/tree/af16f22c10cf18d572359eea6683bce11d432308).

- [README.md](https://github.com/Asdivyansh/Awesome-ChatGPT-Plugins/blob/af16f22c10cf18d572359eea6683bce11d432308/README.md)
- [catalog/scientific-research.md](https://github.com/Asdivyansh/Awesome-ChatGPT-Plugins/blob/af16f22c10cf18d572359eea6683bce11d432308/catalog/scientific-research.md)

### Source record 16

**[findscripter/everything-skills](https://github.com/findscripter/everything-skills)**

Default branch: main. Exact commit: [060d87e68bd0c1f8e50747d7c7782bb41d165058](https://github.com/findscripter/everything-skills/commit/060d87e68bd0c1f8e50747d7c7782bb41d165058).

Enumerated tree entries: 2835. Selected content files: 4. Other file paths not substantively reviewed: 1628. [Browse the pinned tree](https://github.com/findscripter/everything-skills/tree/060d87e68bd0c1f8e50747d7c7782bb41d165058).

- [00-meta/agent-self-reflection/SKILL.md](https://github.com/findscripter/everything-skills/blob/060d87e68bd0c1f8e50747d7c7782bb41d165058/00-meta/agent-self-reflection/SKILL.md)
- [00-meta/entity-research-dossier/scripts/disconfirming_evidence_balance.py](https://github.com/findscripter/everything-skills/blob/060d87e68bd0c1f8e50747d7c7782bb41d165058/00-meta/entity-research-dossier/scripts/disconfirming_evidence_balance.py)
- [00-meta/idea-darwin-evolution/SKILL.md](https://github.com/findscripter/everything-skills/blob/060d87e68bd0c1f8e50747d7c7782bb41d165058/00-meta/idea-darwin-evolution/SKILL.md)
- [00-meta/invariant-guard-correctness/SKILL.md](https://github.com/findscripter/everything-skills/blob/060d87e68bd0c1f8e50747d7c7782bb41d165058/00-meta/invariant-guard-correctness/SKILL.md)

### Source record 17

**[memoryplugin/agent-skills](https://github.com/memoryplugin/agent-skills)**

Default branch: main. Exact commit: [56b64b5bad61e868d8a5f932d79394a2532099cf](https://github.com/memoryplugin/agent-skills/commit/56b64b5bad61e868d8a5f932d79394a2532099cf).

Enumerated tree entries: 15. Selected content files: 1. Other file paths not substantively reviewed: 9. [Browse the pinned tree](https://github.com/memoryplugin/agent-skills/tree/56b64b5bad61e868d8a5f932d79394a2532099cf).

- [skills/memoryplugin/SKILL.md](https://github.com/memoryplugin/agent-skills/blob/56b64b5bad61e868d8a5f932d79394a2532099cf/skills/memoryplugin/SKILL.md)

### Source record 18

**[memoryplugin/mcp-server](https://github.com/memoryplugin/mcp-server)**

Default branch: main. Exact commit: [dd27c76a9a12818c64f71e49cd9b3a56dc8dd54d](https://github.com/memoryplugin/mcp-server/commit/dd27c76a9a12818c64f71e49cd9b3a56dc8dd54d).

Enumerated tree entries: 8. Selected content files: 1. Other file paths not substantively reviewed: 6. [Browse the pinned tree](https://github.com/memoryplugin/mcp-server/tree/dd27c76a9a12818c64f71e49cd9b3a56dc8dd54d).

- [src/index.ts](https://github.com/memoryplugin/mcp-server/blob/dd27c76a9a12818c64f71e49cd9b3a56dc8dd54d/src/index.ts)

### Source record 19

**[siliconjungle/llm-fact-log](https://github.com/siliconjungle/llm-fact-log)**

Default branch: main. Exact commit: [23cca3fbc7c7e6cb377269019d33b421856f02ce](https://github.com/siliconjungle/llm-fact-log/commit/23cca3fbc7c7e6cb377269019d33b421856f02ce).

Enumerated tree entries: 2. Selected content files: 1. Other file paths not substantively reviewed: 1. [Browse the pinned tree](https://github.com/siliconjungle/llm-fact-log/tree/23cca3fbc7c7e6cb377269019d33b421856f02ce).

- [index.js](https://github.com/siliconjungle/llm-fact-log/blob/23cca3fbc7c7e6cb377269019d33b421856f02ce/index.js)

### Source record 20

**[siliconjungle/cascade-retries](https://github.com/siliconjungle/cascade-retries)**

Default branch: main. Exact commit: [a4a63aacbddda9179bf9fca52ef60b99a881a35a](https://github.com/siliconjungle/cascade-retries/commit/a4a63aacbddda9179bf9fca52ef60b99a881a35a).

Enumerated tree entries: 2. Selected content files: 1. Other file paths not substantively reviewed: 1. [Browse the pinned tree](https://github.com/siliconjungle/cascade-retries/tree/a4a63aacbddda9179bf9fca52ef60b99a881a35a).

- [index.js](https://github.com/siliconjungle/cascade-retries/blob/a4a63aacbddda9179bf9fca52ef60b99a881a35a/index.js)

### Source record 21

**[siliconjungle/-shapeshift-labs-evidence-kit](https://github.com/siliconjungle/-shapeshift-labs-evidence-kit)**

Default branch: main. Exact commit: [be1bfdac003704ebe73520bdf76ee707558b48d3](https://github.com/siliconjungle/-shapeshift-labs-evidence-kit/commit/be1bfdac003704ebe73520bdf76ee707558b48d3).

Enumerated tree entries: 59. Selected content files: 3. Other file paths not substantively reviewed: 34. [Browse the pinned tree](https://github.com/siliconjungle/-shapeshift-labs-evidence-kit/tree/be1bfdac003704ebe73520bdf76ee707558b48d3).

- [schemas/benchmark-result.schema.json](https://github.com/siliconjungle/-shapeshift-labs-evidence-kit/blob/be1bfdac003704ebe73520bdf76ee707558b48d3/schemas/benchmark-result.schema.json)
- [skills/benchmark-guardian/SKILL.md](https://github.com/siliconjungle/-shapeshift-labs-evidence-kit/blob/be1bfdac003704ebe73520bdf76ee707558b48d3/skills/benchmark-guardian/SKILL.md)
- [skills/target-evidence-designer/SKILL.md](https://github.com/siliconjungle/-shapeshift-labs-evidence-kit/blob/be1bfdac003704ebe73520bdf76ee707558b48d3/skills/target-evidence-designer/SKILL.md)

### Source record 22

**[siliconjungle/-shapeshift-labs-frontier-agent-kit](https://github.com/siliconjungle/-shapeshift-labs-frontier-agent-kit)**

Default branch: main. Exact commit: [f731df03fea608b642d68ba2db0d132100f72c9f](https://github.com/siliconjungle/-shapeshift-labs-frontier-agent-kit/commit/f731df03fea608b642d68ba2db0d132100f72c9f).

Enumerated tree entries: 54. Selected content files: 2. Other file paths not substantively reviewed: 38. [Browse the pinned tree](https://github.com/siliconjungle/-shapeshift-labs-frontier-agent-kit/tree/f731df03fea608b642d68ba2db0d132100f72c9f).

- [src/evidence.ts](https://github.com/siliconjungle/-shapeshift-labs-frontier-agent-kit/blob/f731df03fea608b642d68ba2db0d132100f72c9f/src/evidence.ts)
- [src/types.ts](https://github.com/siliconjungle/-shapeshift-labs-frontier-agent-kit/blob/f731df03fea608b642d68ba2db0d132100f72c9f/src/types.ts)

### Remaining scope and meaning of completeness

This handbook is complete with respect to the substantive findings produced by the dated research passes. It is not an assertion that every file in the 22 repositories was read. Most repository files, historical branches, issue and pull-request histories, deployment configuration, dependency implementations, cited papers and hosted service internals remain unexamined. Some large README files, catalogs and browser modules were inspected selectively. Source tests were not run and their current passing status is unverified.

All named repository identities were found; none was missing or permission-denied during these passes. The unresolved siliconjungle page-three roster remains an explicit limitation. The accompanying public coverage inventory lists every selected source and every enumerated but unexamined file path, without embedding raw source captures or private project records.

The next useful research pass should focus on the actual project contracts and runtime paths needed for a specific accepted change. Indiscriminate ingestion of thousands of unrelated files would not itself establish better memory, reliable execution or a trading edge.
