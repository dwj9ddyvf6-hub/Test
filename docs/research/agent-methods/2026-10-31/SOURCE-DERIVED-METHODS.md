# Source-derived reliability methods for simulated research agents

Public-safe research note • 2026-10-31 • PROPOSED METHODS, NOT DEPLOYED IMPLEMENTATION

**Reading this note:** this is the earlier concise proposal-stage design note. The [complete handbook](github-research-complete-20261031.md) contains all substantive findings and the later local implementation status: 83 passing shadow-validator tests, with no canonical adoption. The acceptance cases below remain the full target contract; that test count is not a claim that every future adapter or downstream integration requirement is complete. The [public coverage inventory](github-research-public-coverage-20261031.json) records all selected and unexamined source paths.

Use narrow, evaluated software contracts rather than wholesale prompts or memory-service installation. Prompting does not retrain model weights or guarantee reliability. No inspected repository demonstrates trading profitability.

## Findings
Preserve scoped, source-linked memory; separate known-time from event-time; distinguish unsupported from degraded retrieval; bind resumable tasks to exact inputs; require fresh completion evidence and independent review; retain failed/abstained cases in evaluation denominators; measure proactive usefulness rather than activity; retain immutable originals and citation-preserving views. Catalog scores are discovery aids, not permission or proof.

Concrete caution: everything-skills’ counterevidence helper computes `ceil(0.30*N-D)`, but new searches enlarge the denominator. Correct added count is `max(0,ceil((0.30*N-D)/0.70))`. N=10,D=2 needs two additions, not one. ProactiveAgent’s False-Alarm is FP/(TP+FP), not conventional FPR; zip can omit unmatched records. siliconjungle’s fact-log minimizes imported cosine similarity, which under ordinary similarity semantics chooses the least similar vector. These are source-level observations, not executed test results.

## Scope correction — 2026-10-31
The project mapping has been corrected to recognize an existing isolated HOLD/TRIM/EXIT position-review candidate. Its retained receipt reports exact-patch replay with 64/64 focused tests, not operational integration. The next experiment should review and complement that candidate’s missing receipt-to-position-field binding, not create a duplicate lifecycle design. Reference-hash shape validation is not source reconciliation. Operational and forward-validation eligibility remain false; execution and automatic adoption remain disabled. These tests were not rerun for this correction. The prior public note did not explicitly propose a separate lifecycle project; this addition clarifies the intended implementation target.

## Minimal next experiment
A pure offline, advisory receipt-binding validator can prevent evidence self-hashes being mistaken for source proof. No network, journal mutation, trading-policy change, automatic adoption or new service dependency. Begin with one explicitly versioned producer format and synthetic tests.

## Exact proposed offline contract and temporal trust boundary
Design only; current producers do not necessarily emit this envelope.

Input envelope fields: schema=PRACTICE_RECEIPT_BINDING_V1; case_id; decision_at; bindings[]. Each binding requires evidence_id, artifact_id, producer_schema, adapter_version, selector_id, expected_instrument, value_sha256 and capture_bytes_sha256. Reject additional fields initially. All digests are 64 lowercase hex; IDs are bounded strings; timestamps require timezone. Selector IDs map to source-owned fixed adapter functions, never executable JSONPath/scripts/URLs/filesystem paths.

The separate trusted_manifest maps artifact_id to capture_bytes_sha256 and canonical version anchor. Caller must obtain that manifest independently from verified canonical metadata; naming it trusted cannot authenticate it. Captured_receipts maps artifact_id to immutable original bytes. Validate digest before parsing/extraction. Restrict byte/depth/container limits and reject duplicate JSON keys so different parsers cannot resolve different claims.

value_sha256 hashes canonical evidence value (existing learning.py behavior). capture_bytes_sha256 hashes raw receipt bytes. content_snapshot_sha256, if present, is only producer content/pagination identity. Optional collection_sha256 hashes the ordered list of captures; it never means simultaneous acquisition. These hashes are not interchangeable.

Producer adapter extracts original source/instrument, value, observation_at, original_available_at, capture_at and restrictions from verified bytes, not envelope assertions. Require observation_at <= original_available_at <= decision_at. Unknown historical availability cannot be manufactured from post-hoc metadata. When the only availability field is retrieval time, it documents that capture rather than earlier publication. A post-decision capture may receive integrity-only verification, but historical_eligibility remains unverified unless an independently anchored contemporaneous receipt establishes the original availability. A wholly rewritten receipt plus manifest requires an independent external anchor to detect; the pure validator cannot solve that trust problem.

Output allowlist: schema, case_id, binding_status (verified/mismatch/unsupported/missing/degraded), reason_codes, adapter_version, value_sha256, capture_bytes_sha256, historical_eligibility (verified/unverified/ineligible), source_authenticity_verified=false, decision_eligible=false, adoption_disabled=true, mode=shadow. No evidence values, raw provider text, URLs, local paths, account/request identifiers or ledger writes. Shadow success does not record a case, establish source authenticity/independence, deploy anything or adopt a strategy. Exposure labels remain authoritative.

## Acceptance tests
Matching synthetic receipt binds; altered value plus recomputed self-hash fails; altered source/backdated availability fails; modified receipt cannot pass against unchanged trusted manifest; equal content identity cannot conflate separate acquisition clocks; unknown schema/missing artifact/naive clock/nonfinite value/duplicate JSON keys fail explicitly. Unknown historical eligibility stays unknown. Existing restriction flags cannot be elevated. Public outputs contain no evidence values or private identifiers. Tests are proposed, not executed.

## Licensing and privacy
No third-party code adopted. Review pinned licenses/per-file notices and dependencies before copying; adapted skill collections can have mixed provenance. Reimplement small original contracts locally where feasible. Browser bridges and hosted memory introduce session, transfer, retention and isolation risks; none is needed for this experiment. Use only synthetic public fixtures. No private conversation, portfolio, account information or raw provider payload is included.

## Coverage
All 16 named repository identities resolved, plus two source-linked MemoryPlugin repositories and four relevance-selected siliconjungle repositories. Tree enumeration is not full-file review. Large files were selectively inspected; most files, dependencies, hosted internals and cited papers remain unexamined. Exact requested siliconjungle page-3 membership remains unresolved after a web cache miss. No installs or repository-code execution occurred.

| Repository | Default branch | Exact commit |
|---|---|---|
| [supermemoryai/supermemory](https://github.com/supermemoryai/supermemory) | main | `d53d124e4769e34c4be8bcc5d21eed1855b090ef` |
| [qualixar/superlocalmemory](https://github.com/qualixar/superlocalmemory) | main | `93e58692ce51b196a879a43e3974d378652db748` |
| [DenisSergeevitch/chatgpt-custom-instructions](https://github.com/DenisSergeevitch/chatgpt-custom-instructions) | main | `908b18e13e33b86736e4d2eecb76245e9c33a474` |
| [taishi-i/awesome-ChatGPT-repositories](https://github.com/taishi-i/awesome-ChatGPT-repositories) | main | `0e5cbe4bb147d74ee5b38028fd8da0632e6cc1ee` |
| [obra/superpowers](https://github.com/obra/superpowers) | main | `2ce8aa15d05bd57213e6f746f953aafb7ded7a8b` |
| [Wangnov/chatgpt-skill](https://github.com/Wangnov/chatgpt-skill) | main | `0dab47ec4bd7966e1a714bac45ad3c4e935f0f4c` |
| [miuuyy/codex-chatgpt-web](https://github.com/miuuyy/codex-chatgpt-web) | main | `860fa576eb47d9e20d7d8289235bfea94392d2fd` |
| [thunlp/ProactiveAgent](https://github.com/thunlp/ProactiveAgent) | main | `3fcf9beebe256b86871659fbb12541c41c9381b9` |
| [tao-hpu/awesome-proactive-agents](https://github.com/tao-hpu/awesome-proactive-agents) | main | `d2696d99d30c74d9f98724d230c7fb8fd27fc5fb` |
| [fainir/most-capable-agent-system-prompt](https://github.com/fainir/most-capable-agent-system-prompt) | main | `d2e533d6b489550e23ee038e6e4dd3510b3b5263` |
| [saeedezzati/superpower-chatgpt](https://github.com/saeedezzati/superpower-chatgpt) | main | `d10a491cd1e45104ee31b8c43816dafb2ccd4ed4` |
| [pionxzh/chatgpt-exporter](https://github.com/pionxzh/chatgpt-exporter) | master | `6935bc1f9aba3a8767755d01fecaf31420f3bc19` |
| [ChatGPTBox-dev/chatGPTBox](https://github.com/ChatGPTBox-dev/chatGPTBox) | master | `827f43f6d9212356f1d5dc686c718f41f1345011` |
| [hashgraph-online/awesome-ai-plugins](https://github.com/hashgraph-online/awesome-ai-plugins) | main | `b827da80ad8653a40b7d11d5f66b44b0e9bbb10d` |
| [Asdivyansh/Awesome-ChatGPT-Plugins](https://github.com/Asdivyansh/Awesome-ChatGPT-Plugins) | main | `af16f22c10cf18d572359eea6683bce11d432308` |
| [findscripter/everything-skills](https://github.com/findscripter/everything-skills) | main | `060d87e68bd0c1f8e50747d7c7782bb41d165058` |
| [siliconjungle/llm-fact-log](https://github.com/siliconjungle/llm-fact-log) | main | `23cca3fbc7c7e6cb377269019d33b421856f02ce` |
| [siliconjungle/-shapeshift-labs-evidence-kit](https://github.com/siliconjungle/-shapeshift-labs-evidence-kit) | main | `be1bfdac003704ebe73520bdf76ee707558b48d3` |
| [siliconjungle/-shapeshift-labs-frontier-agent-kit](https://github.com/siliconjungle/-shapeshift-labs-frontier-agent-kit) | main | `f731df03fea608b642d68ba2db0d132100f72c9f` |
| [siliconjungle/cascade-retries](https://github.com/siliconjungle/cascade-retries) | main | `a4a63aacbddda9179bf9fca52ef60b99a881a35a` |
| [memoryplugin/agent-skills](https://github.com/memoryplugin/agent-skills) | main | `56b64b5bad61e868d8a5f932d79394a2532099cf` |
| [memoryplugin/mcp-server](https://github.com/memoryplugin/mcp-server) | main | `dd27c76a9a12818c64f71e49cd9b3a56dc8dd54d` |

## Exact primary-source file references
- [obra/superpowers: skills/verification-before-completion/SKILL.md](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/verification-before-completion/SKILL.md)
- [obra/superpowers: skills/subagent-driven-development/SKILL.md](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/subagent-driven-development/SKILL.md)
- [obra/superpowers: skills/writing-skills/references/testing-skills-with-subagents.md](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/writing-skills/references/testing-skills-with-subagents.md)
- [DenisSergeevitch/chatgpt-custom-instructions: v2.md](https://github.com/DenisSergeevitch/chatgpt-custom-instructions/blob/908b18e13e33b86736e4d2eecb76245e9c33a474/v2.md)
- [fainir/most-capable-agent-system-prompt: README.md](https://github.com/fainir/most-capable-agent-system-prompt/blob/d2e533d6b489550e23ee038e6e4dd3510b3b5263/README.md)
- [findscripter/everything-skills: 00-meta/invariant-guard-correctness/SKILL.md](https://github.com/findscripter/everything-skills/blob/060d87e68bd0c1f8e50747d7c7782bb41d165058/00-meta/invariant-guard-correctness/SKILL.md)
- [findscripter/everything-skills: 00-meta/idea-darwin-evolution/SKILL.md](https://github.com/findscripter/everything-skills/blob/060d87e68bd0c1f8e50747d7c7782bb41d165058/00-meta/idea-darwin-evolution/SKILL.md)
- [findscripter/everything-skills: 00-meta/agent-self-reflection/SKILL.md](https://github.com/findscripter/everything-skills/blob/060d87e68bd0c1f8e50747d7c7782bb41d165058/00-meta/agent-self-reflection/SKILL.md)
- [findscripter/everything-skills: 00-meta/entity-research-dossier/scripts/disconfirming_evidence_balance.py](https://github.com/findscripter/everything-skills/blob/060d87e68bd0c1f8e50747d7c7782bb41d165058/00-meta/entity-research-dossier/scripts/disconfirming_evidence_balance.py)
- [Wangnov/chatgpt-skill: codex-chatgpt-skill/SKILL.md](https://github.com/Wangnov/chatgpt-skill/blob/0dab47ec4bd7966e1a714bac45ad3c4e935f0f4c/codex-chatgpt-skill/SKILL.md)
- [Wangnov/chatgpt-skill: codex-chatgpt-skill/references/error-and-limits.md](https://github.com/Wangnov/chatgpt-skill/blob/0dab47ec4bd7966e1a714bac45ad3c4e935f0f4c/codex-chatgpt-skill/references/error-and-limits.md)
- [miuuyy/codex-chatgpt-web: src/adapters/chatgpt-web/retry-policy.ts](https://github.com/miuuyy/codex-chatgpt-web/blob/860fa576eb47d9e20d7d8289235bfea94392d2fd/src/adapters/chatgpt-web/retry-policy.ts)
- [miuuyy/codex-chatgpt-web: src/adapters/chatgpt-web/output-validation.ts](https://github.com/miuuyy/codex-chatgpt-web/blob/860fa576eb47d9e20d7d8289235bfea94392d2fd/src/adapters/chatgpt-web/output-validation.ts)
- [miuuyy/codex-chatgpt-web: src/adapters/chatgpt-web/rolling-checkpoint.ts](https://github.com/miuuyy/codex-chatgpt-web/blob/860fa576eb47d9e20d7d8289235bfea94392d2fd/src/adapters/chatgpt-web/rolling-checkpoint.ts)
- [miuuyy/codex-chatgpt-web: docs/security-model.md](https://github.com/miuuyy/codex-chatgpt-web/blob/860fa576eb47d9e20d7d8289235bfea94392d2fd/docs/security-model.md)
- [taishi-i/awesome-ChatGPT-repositories: plugins/awesome-chatgpt-search/build_data.py](https://github.com/taishi-i/awesome-ChatGPT-repositories/blob/0e5cbe4bb147d74ee5b38028fd8da0632e6cc1ee/plugins/awesome-chatgpt-search/build_data.py)
- [taishi-i/awesome-ChatGPT-repositories: skills/awesome-chatgpt-search/SKILL.md](https://github.com/taishi-i/awesome-ChatGPT-repositories/blob/0e5cbe4bb147d74ee5b38028fd8da0632e6cc1ee/skills/awesome-chatgpt-search/SKILL.md)
- [tao-hpu/awesome-proactive-agents: README.md](https://github.com/tao-hpu/awesome-proactive-agents/blob/d2696d99d30c74d9f98724d230c7fb8fd27fc5fb/README.md)
- [saeedezzati/superpower-chatgpt: scripts/content/autoSave.js](https://github.com/saeedezzati/superpower-chatgpt/blob/d10a491cd1e45104ee31b8c43816dafb2ccd4ed4/scripts/content/autoSave.js)
- [saeedezzati/superpower-chatgpt: scripts/content/promptChain.js](https://github.com/saeedezzati/superpower-chatgpt/blob/d10a491cd1e45104ee31b8c43816dafb2ccd4ed4/scripts/content/promptChain.js)
- [saeedezzati/superpower-chatgpt: manifest.json](https://github.com/saeedezzati/superpower-chatgpt/blob/d10a491cd1e45104ee31b8c43816dafb2ccd4ed4/manifest.json)
- [pionxzh/chatgpt-exporter: src/exporter/json.ts](https://github.com/pionxzh/chatgpt-exporter/blob/6935bc1f9aba3a8767755d01fecaf31420f3bc19/src/exporter/json.ts)
- [pionxzh/chatgpt-exporter: tests/citations.test.ts](https://github.com/pionxzh/chatgpt-exporter/blob/6935bc1f9aba3a8767755d01fecaf31420f3bc19/tests/citations.test.ts)
- [pionxzh/chatgpt-exporter: tests/process-conversation.test.ts](https://github.com/pionxzh/chatgpt-exporter/blob/6935bc1f9aba3a8767755d01fecaf31420f3bc19/tests/process-conversation.test.ts)
- [ChatGPTBox-dev/chatGPTBox: tests/unit/background/redact.test.mjs](https://github.com/ChatGPTBox-dev/chatGPTBox/blob/827f43f6d9212356f1d5dc686c718f41f1345011/tests/unit/background/redact.test.mjs)
- [ChatGPTBox-dev/chatGPTBox: tests/unit/components/floating-toolbar-stale-tasks.test.mjs](https://github.com/ChatGPTBox-dev/chatGPTBox/blob/827f43f6d9212356f1d5dc686c718f41f1345011/tests/unit/components/floating-toolbar-stale-tasks.test.mjs)
- [hashgraph-online/awesome-ai-plugins: SCANNER_GUIDE.md](https://github.com/hashgraph-online/awesome-ai-plugins/blob/b827da80ad8653a40b7d11d5f66b44b0e9bbb10d/SCANNER_GUIDE.md)
- [hashgraph-online/awesome-ai-plugins: scripts/sanitize-scan-report.py](https://github.com/hashgraph-online/awesome-ai-plugins/blob/b827da80ad8653a40b7d11d5f66b44b0e9bbb10d/scripts/sanitize-scan-report.py)
- [Asdivyansh/Awesome-ChatGPT-Plugins: README.md](https://github.com/Asdivyansh/Awesome-ChatGPT-Plugins/blob/af16f22c10cf18d572359eea6683bce11d432308/README.md)
- [Asdivyansh/Awesome-ChatGPT-Plugins: catalog/scientific-research.md](https://github.com/Asdivyansh/Awesome-ChatGPT-Plugins/blob/af16f22c10cf18d572359eea6683bce11d432308/catalog/scientific-research.md)
- [siliconjungle/llm-fact-log: index.js](https://github.com/siliconjungle/llm-fact-log/blob/23cca3fbc7c7e6cb377269019d33b421856f02ce/index.js)
- [siliconjungle/-shapeshift-labs-evidence-kit: schemas/benchmark-result.schema.json](https://github.com/siliconjungle/-shapeshift-labs-evidence-kit/blob/be1bfdac003704ebe73520bdf76ee707558b48d3/schemas/benchmark-result.schema.json)
- [siliconjungle/-shapeshift-labs-evidence-kit: skills/target-evidence-designer/SKILL.md](https://github.com/siliconjungle/-shapeshift-labs-evidence-kit/blob/be1bfdac003704ebe73520bdf76ee707558b48d3/skills/target-evidence-designer/SKILL.md)
- [siliconjungle/-shapeshift-labs-evidence-kit: skills/benchmark-guardian/SKILL.md](https://github.com/siliconjungle/-shapeshift-labs-evidence-kit/blob/be1bfdac003704ebe73520bdf76ee707558b48d3/skills/benchmark-guardian/SKILL.md)
- [siliconjungle/-shapeshift-labs-frontier-agent-kit: src/evidence.ts](https://github.com/siliconjungle/-shapeshift-labs-frontier-agent-kit/blob/f731df03fea608b642d68ba2db0d132100f72c9f/src/evidence.ts)
- [siliconjungle/-shapeshift-labs-frontier-agent-kit: src/types.ts](https://github.com/siliconjungle/-shapeshift-labs-frontier-agent-kit/blob/f731df03fea608b642d68ba2db0d132100f72c9f/src/types.ts)
- [siliconjungle/cascade-retries: index.js](https://github.com/siliconjungle/cascade-retries/blob/a4a63aacbddda9179bf9fca52ef60b99a881a35a/index.js)
- [qualixar/superlocalmemory: src/superlocalmemory/retrieval/snapshot_admission.py](https://github.com/qualixar/superlocalmemory/blob/93e58692ce51b196a879a43e3974d378652db748/src/superlocalmemory/retrieval/snapshot_admission.py)
- [qualixar/superlocalmemory: src/superlocalmemory/retrieval/support_gate.py](https://github.com/qualixar/superlocalmemory/blob/93e58692ce51b196a879a43e3974d378652db748/src/superlocalmemory/retrieval/support_gate.py)
- [supermemoryai/supermemory: apps/mcp/src/server/tools/forget-memory.ts](https://github.com/supermemoryai/supermemory/blob/d53d124e4769e34c4be8bcc5d21eed1855b090ef/apps/mcp/src/server/tools/forget-memory.ts)
- [thunlp/ProactiveAgent: eval/calculate_agent_performance.py](https://github.com/thunlp/ProactiveAgent/blob/3fcf9beebe256b86871659fbb12541c41c9381b9/eval/calculate_agent_performance.py)
- [memoryplugin/agent-skills: skills/memoryplugin/SKILL.md](https://github.com/memoryplugin/agent-skills/blob/56b64b5bad61e868d8a5f932d79394a2532099cf/skills/memoryplugin/SKILL.md)
- [memoryplugin/mcp-server: src/index.ts](https://github.com/memoryplugin/mcp-server/blob/dd27c76a9a12818c64f71e49cd9b3a56dc8dd54d/src/index.ts)

