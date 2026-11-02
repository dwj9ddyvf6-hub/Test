# Pass 2, Dive 3: Memory Internals, Artifact-Level Extraction

Research date: 2026-10-31 (second pass, same day as pass 1). Method: raw.githubusercontent.com file reads plus api.github.com tree listings only. No repo code was installed, cloned-and-run, or executed. Verbatim quotes name their source path. Long artifacts are given as complete structure plus load-bearing sections verbatim, with compression noted. No personal information about any person is included; example names inside quoted prompts/docs are the vendors' own fictional examples.

Pass 1 sources for this dive: `REPORT.md` section 2.1 and `CLUSTER-1-memory.md` sections 1 (Supermemory), 2 (SuperLocalMemory), plus the Mem0 and Letta entries that pass 1 catalogued from other clusters' references. Pass 2 was asked to go to the artifact: schemas, prompts, and invariants.

## Coverage ledger

| Source | Artifacts actually read at file level | Not reachable / not in tree |
|---|---|---|
| supermemoryai/supermemory (main, 31,481 stars at read) | `apps/docs/concepts/graph-memory.mdx`, `user-profiles.mdx`, `how-it-works.mdx`, `customization.mdx`, `rules.mdx`, `apps/docs/recall/memory-operations.mdx`, `apps/docs/recall/memory-review.mdx`, `apps/mcp/src/server/prompts/context.ts`, `packages/tools/src/shared/prompt-builder.ts`, full tree (1,088 entries) | The extraction/learning model prompt is **not published**. No prompt file for fact extraction, edge classification, or expiry exists in the tree. The engine is closed; what is extractable is the API contract, the doc-level model, and the two client-side prompt formatters above. Logged as unreachable-by-design, not as absence of mechanism. |
| mem0ai/mem0 (main, 68,161 stars) | `mem0/configs/prompts.py` (1,062 lines, read in full), `mem0/memory/main.py` (3,916 lines: `_add_to_vector_store`, `_search_vector_store`, `_compute_entity_boosts`, entity upsert), `mem0/utils/scoring.py` (full), `mem0/utils/entity_extraction.py` (head + type contract), `mem0/memory/notices.py` (structure + temporal/decay gating), full tree (2,218 entries) | Platform temporal ranking and decay are **not in OSS**: they exist only as stub notices/errors (see section 2.4). The managed-platform prompt originals are ported into OSS with provenance comments, so the OSS copy is the best available artifact. |
| qualixar/superlocalmemory (main, 269 stars) | `docs/recall.md` (full), `docs/reviewed-corrections.md` (full), `src/superlocalmemory/retrieval/support_tiers.py` (full), `src/superlocalmemory/retrieval/support_gate.py` (head + contract), `src/superlocalmemory/core/maintenance.py` (777 lines, head + lifecycle logic), `src/superlocalmemory/core/maintenance_scheduler.py` (head), `src/superlocalmemory/server/write_governance.py` (full, 63 lines), `src/superlocalmemory/storage/write_receipts_erasure.py` (full), `src/superlocalmemory/storage/migrations/M035_erasure_receipts.py` (DDL), `tests/test_compliance/test_forget_facts.py` (head), full tree (5,303 entries) | `docs/forget.md` does not exist at that path (404); forgetting is specified instead across the erasure migration, the receipts-erasure module, the GDPR compliance tests, and `docs/reviewed-corrections.md`. The fitted support-recipe weights live in `retrieval/support_recipe.py`, referenced but not fully reproduced here; thresholds quoted are from `support_tiers.py` and `recall.md`. |
| letta-ai/letta + letta-ai/letta-code | letta `main` is a 15-file stub pointing to letta-code. V1 artifacts read from the `archive` branch: `letta/schemas/block.py` (full), `letta/schemas/memory.py` (head + Memory model), `letta/orm/block.py` (full), `letta/constants.py` (limits), `letta/functions/function_sets/base.py` (memory tools). Current artifacts from letta-code `main` (2,917-entry tree): `src/agent/prompts/letta.md` (system prompt, ~20.6 KB), `src/agent/prompts/human.mdx`, `persona.mdx`, `src/agent/memory-format.ts`, `src/tools/descriptions/Memory.md`, `src/tools/schemas/Memory.json`, `src/skills/builtin/maintaining-core-memory/SKILL.md` (full), `src/skills/builtin/maintaining-deferred-memory/SKILL.md` (full), `src/backend/local/initial-memory.ts` | Nothing material unreachable. The two-generation split (V1 server vs letta-code MemFS) is itself a finding; pass 1 treated Letta as one system. |

---

## 1. Supermemory: supermemoryai/supermemory

### 1.1 What pass 1 said, and what the artifacts add

Pass 1 correctly identified the three edge types, the static/dynamic profile split, and expiry. At artifact level three things change the picture: (a) the profile has a **third axis pass 1 missed entirely, topical buckets**, with hard validation behaviour; (b) forgetting is not one mechanism but **four distinct ones with different contracts** (time expiry, contradiction via `isLatest`, soft-delete by ID, semantic forget-matching with a mandatory dry-run), plus a fifth, a **review queue for inferred memories** with an approve/decline/undo state machine; (c) there is **no published extraction prompt to extract**. The "any published prompts" hope in the dive brief fails for the core engine and succeeds only at the client edge (context injection formatting). That boundary is the honest headline.

### 1.2 Graph model: verbatim core (source: `apps/docs/concepts/graph-memory.mdx`)

Properties, verbatim:

> 1. Memories are atomic - Each memory has enough information and context about one particular topic
> 2. They always build on top of each other - with `updates`, the model knows the history, a memory `extends` from other memories, and new facts are derived (`derives` relation) from existing knowledge.

Edge semantics, verbatim examples from the same file:

```text
Memory 1: "Alex works at Google as a software engineer"
Memory 2: "Alex just started at Stripe as a PM"
         -> Memory 2 UPDATES Memory 1
Memory 1: "Alex works at Stripe as a PM"
Memory 2: "Alex focuses on payments and leads a team of 5"
         -> Memory 2 EXTENDS Memory 1
Memory 1: "Alex is a PM at Stripe"
Memory 2: "Alex frequently discusses payment APIs and fraud detection"
         -> Derived: "Alex likely works on Stripe's core payments product"
```

Invariants established by this file plus `how-it-works.mdx`:

- Documents and memories are separate layers with separate lifecycles. Documents: caller adds/updates/deletes. Memories: "Graph updates, extends, derives, forgets." There is **no direct memory-create or memory-update route in v5** (confirmed in `recall/memory-operations.mdx`: "v5 has no direct memory-create route. Ingest a document instead"; "v5 has no direct memory-update route. Update the source document instead"). The graph is write-only-through-documents. This is a strong invariant pass 1 understated: callers can never patch a fact in place; correction flows through reprocessing a source document or through forget.
- `isLatest` gates retrieval on the current fact under `updates`; history is retained, not erased.
- Memory types have different decay contracts (table in `graph-memory.mdx`): Facts "Persist until updated"; Preferences "Strengthen with repetition"; Episodes "Decay unless significant".
- Ingest order is load-bearing: `rules.mdx` recommends ingesting "sequentially within a single namespace where possible, since that's how supermemory determines what came first (used for `updates` relations and temporal reasoning)." Temporal truth is therefore partly an ingest-order artifact, not purely a content timestamp. Pass 1 did not note this dependency.

### 1.3 Dreaming: the two-phase pipeline (source: `apps/docs/concepts/how-it-works.mdx`)

Document pipeline stages, verbatim table values: `Queued -> Extracting -> Chunking -> Embedding -> Indexing -> Done`, with `system.status` in `"queued" | "extracting" | ... | "done" | "failed"`. Crucially, `done` means chunks are searchable; memories arrive in a **second phase, dreaming**, which may continue after `done`. The `dreaming` field contract:

| Mode | Default? | Behaviour (verbatim substance) |
|---|---|---|
| `dynamic` | Yes | "Related documents are grouped so memories form from coherent units, not one isolated write at a time." Extraction may continue after `status: "done"`. |
| `instant` | No | "This document is dreamed on its own, right away." Bills one extra operation per document. |

Design invariant: quality is explicitly traded against immediacy, and the default chooses quality. A caller that needs read-your-write must pay for `instant` and accept single-document (lower-linkage) extraction.

### 1.4 Profiles: static, dynamic, and the missed third axis, buckets

Sources: `apps/docs/concepts/user-profiles.mdx`, `apps/mcp/src/server/prompts/context.ts`, `packages/tools/src/shared/prompt-builder.ts`.

Static vs dynamic definitions, verbatim:

> Static profile: Long-term, stable facts: "Sarah is a senior software engineer at TechCorp" / "Sarah specializes in distributed systems" / "Sarah prefers technical docs over video tutorials"
> Dynamic profile: Recent context and temporary states: "Sarah is migrating the payment service to microservices" / "Sarah is preparing for a conference talk next month" / "Sarah is debugging a memory leak in auth service"

The rationale is stated as a retrieval theorem, not a preference: facts that must colour every answer (preferred name, pronouns, timezone, tone/format, role) have near-zero semantic similarity to most queries, so search structurally cannot return them. The profile is the fix because it "rides along" unconditionally. Claimed profile latency 50-100 ms vs 200-500 ms for 3-5 search queries (vendor figure, doc-stated).

**Buckets (missed by pass 1).** Verbatim substance: "Static and dynamic split facts by how long-lived they are. Buckets split them by topic, a third, independent axis you define, like `preferences`, `goals`, or `work`." Rules: every org starts with a default `preferences` bucket that is "always present, custom buckets are added alongside it, never in place of it"; namespace buckets are **add-only** ("a namespace always keeps every org-level bucket"); bucket descriptions steer the classifier, so a precise description ("explicit first-person preferences only, exclude inferred traits") produces cleaner buckets. API shape: `supermemory.profiles.setBuckets(namespace, { buckets: { goals: "Goals and targets..." } })`, read back as `profile.buckets.preferences` / `profile.buckets.goals`, each `[{ id, memory }]`. Profiles also accept the same metadata `filter` expression as search, narrowing which memories may contribute to static/dynamic/buckets; a v5 profile call takes **no search query** (query-ranked recall is a separate `search()` call).

Client-side injection format is published and extractable. From `packages/tools/src/shared/prompt-builder.ts`, verbatim:

```typescript
export const defaultPromptTemplate: PromptTemplate = (data) => {
  if (!data.userMemories.trim() && !data.generalSearchMemories.trim()) return ""
  return `User Supermemories: \n${data.userMemories}\n${data.generalSearchMemories}`.trim()
}
export function convertProfileToMarkdown(data: ProfileMarkdownData): string {
  // emits "## Static Profile" bullet list, then "## Dynamic Profile" bullet list
}
```

From `apps/mcp/src/server/prompts/context.ts`, the MCP `context` prompt's hard limits, verbatim constants: `CONTEXT_FACT_LIMIT = 8`, `RECENT_SPACE_LIMIT = 3`. It renders `# Supermemory Context`, `Active space: ...`, then `Stable Context` (static, max 8) and `Recent Context` (dynamic, max 8), then up to 3 recently active spaces, and closes with the instruction: "Use a space key with space-aware tools when the user asks about another space. Keep space contexts separate unless the user asks to combine them." On failure it returns exactly "Unable to load user context." So the always-on profile is **capped at 8+8 facts at the MCP surface**, a concrete budget pass 1 never quantified.

Steering prompts that ARE published live in `apps/docs/concepts/customization.mdx`, as configuration text rather than engine prompts: `organizationalContext` (org-wide, v3/v4 name `filterPrompt`; replaces in full, `null` clears; applies to new content only) and per-namespace `supportingContext` (v3/v4 name `entityContext`; persists and combines with org context). The doc's grounding example is load-bearing: without supporting context "Hey, I'm doing great!" is ungrounded; with `User is {name}, talking to assistant Kira` the engine learns the attributed fact. Invariant: extraction quality depends on the caller supplying entity grounding; the engine does not infer the speaker reliably on its own.

### 1.5 Forgetting and expiry: four contracts plus a review state machine

Sources: `apps/docs/concepts/graph-memory.mdx` (Automatic forgetting), `apps/docs/recall/memory-operations.mdx`, `apps/docs/recall/memory-review.mdx`.

Automatic forgetting, verbatim three bullets:

> - **Time-based** - temporary facts drop after they expire ("exam tomorrow", "meeting at 3pm today").
> - **Contradiction** - updates win for "what's true now."
> - **Noise filtering** - casual, non-meaningful chatter is less likely to become durable memory.

Explicit forgetting contracts:

1. **Forget by ID**: soft-delete, "excluded from search results but preserved", 1 to 500 IDs per call. Response `{ count, matches: [{id, memory}], errors: [{id, error}] }` with the invariant "HTTP success does not imply every requested ID changed. Check `errors`." and `count` always equals `matches.length`.
2. **Forget matching (semantic)**: `dryRun` is **required**; each request selects at most 100 memories; the doc warns the match is semantic and a broad query over-selects. Exactness invariant, verbatim tip: re-running with `dryRun: false` re-runs the match and "the result can drift from the preview"; to forget precisely what was reviewed, take the IDs from the dry-run preview and send them to `memories.forget`. The response payload "does not say which mode was sent, so keep your own record of `dryRun` next to audit logs."
3. **Decline-as-forget** in the review queue (below).
4. **Expiry**: expired memories are excluded from the review queue and from search; no TTL schema or duration table is published in the docs read. The expiry decision is made by the closed learning model ("Decides what and how to learn, what is important, when to forget", `how-it-works.mdx`). **No numeric TTL, decay curve, or expiry prompt is extractable.** Pass 1's phrase "temporary facts expire after their date passes" is the whole published mechanism.

Review of inferred memories (entirely missed by pass 1). Source: `memory-review.mdx`. Derived facts are flagged `isInference: true` until confirmed. State machine, verbatim table:

| Action | Result | Effect on search |
|---|---|---|
| Approve | `isInference` cleared | Stays in search, no longer flagged as inferred |
| Decline | `isForgotten` set | Removed from search entirely, "a rejected guess is forgotten" |
| Undo | back to unreviewed | Returns to the queue, flagged as inferred again |

Queue contract: `GET /v3/container-tags/{containerTag}/inferred` returns up to **50**, ordered by `parentCount` descending then `createdAt` descending, excluding anything forgotten, expired, or already reviewed; each item carries `parentCount` ("How many source memories this was derived from. Higher = stronger signal"). Review: `POST .../inferred/{memoryId}/review` with `action` in `approve | decline | undo` (there is no `reject` value; a client-side "skip" sends no request). Response `{ id, isInference, isForgotten, reviewStatus: "approved" | "declined" | null }`; 409 when the memory is not reviewable for that action. This is a human-gate on inferred memory with a confidence proxy (`parentCount`) and a full undo, which is a materially stronger governance design than pass 1's summary suggested.

### 1.6 Design invariants (Supermemory)

- Namespace is a hard isolation boundary (in the URL); metadata is a soft filter inside it; scoped API keys cannot cross namespaces. Capacity claim in `rules.mdx`: up to 1M documents and 10M memories per namespace.
- Not a system of record: no SQL, joins, aggregates, or primary-key query over memories (`rules.mdx` decision table routes ID-queried/summed data to the caller's database and verbatim always-needed rules to the system prompt).
- Never pre-process with another LLM before ingest ("Don't pass content through an additional LLM... the engine already knows what it knows"); never hand-maintain the graph.
- Same-`id` re-ingest must keep a stable prefix (full transcript or delta only, never mixed) and is diff-billed.

### 1.7 Refined verdict

Pass 1 verdict ADOPT-IDEA stands, but the adoptable set grows and sharpens: add (a) topical buckets as a third profile axis with add-only namespace inheritance and classifier-steering descriptions, (b) the 8+8 fact budget as the concrete size of an always-on profile at an injection surface, (c) the inferred-memory review queue pattern (flag inferences, rank by support count, approve/decline-forget/undo) as the governance shape for any derived-fact layer, and (d) the forget-matching discipline (mandatory dry-run, then bind the delete to the previewed IDs). Downgrade one pass-1 implication: expiry/forgetting cannot be copied as an algorithm because none is published; only its contracts can be copied. The closed-engine caveat is stronger at artifact level than pass 1 stated: even the extraction prompt is absent, so Supermemory remains un-auditable at exactly the layer that produces its benchmark numbers.


---

## 2. Mem0: mem0ai/mem0

### 2.1 What pass 1 said, and what the artifacts add

Pass 1 described the April 2026 algorithm as "single-pass ADD-only extraction, contradictions resolved at retrieval time, fused semantic + BM25 + entity retrieval with temporal ranking." The code confirms the first two clauses precisely, gives the fusion an **exact formula** (section 2.3), and **contradicts the third clause for the open-source build**: temporal ranking and decay are platform-only features whose OSS presence is a set of detection stubs that raise errors and upsell notices (section 2.4). Pass 1 also missed that the legacy ADD/UPDATE/DELETE/NONE prompt is still shipped in the same file, so the repo contains both generations of the algorithm side by side, and that the ADD-only prompt itself is a ~500-line specification with integrity rules that are the most directly reusable artifact in this entire dive.

### 2.2 The prompts: `mem0/configs/prompts.py` (1,062 lines)

The file holds five generations/cohorts. Structure (complete):

| Constant / builder | Lines (approx.) | Role |
|---|---|---|
| `MEMORY_ANSWER_PROMPT` | 4-13 | Answering from memories |
| `FACT_RETRIEVAL_PROMPT` | 15-60 | Legacy v1 extraction to `{"facts": [...]}` |
| `USER_MEMORY_EXTRACTION_PROMPT` | 63-121 | Enhanced user-fact extraction |
| `AGENT_MEMORY_EXTRACTION_PROMPT` | 124-174 | Same, for facts about the assistant; selected when agent-scoped |
| `DEFAULT_UPDATE_MEMORY_PROMPT` | 176-324 | Legacy memory-manager: ADD / UPDATE / DELETE / NONE decisions |
| `PROCEDURAL_MEMORY_SYSTEM_PROMPT` | 326-404 | Summarise agent execution history verbatim for continuation |
| `get_update_memory_messages(...)` | 406-463 | Wraps the update prompt |
| `ADDITIVE_EXTRACTION_PROMPT` | 468-959 | **Current (V3) ADD-only extraction system prompt**, header comment: "Ported from platform/backend/shared/core/config/prompts.py" |
| `generate_additive_extraction_prompt(...)` + helpers | 961-1062 | User-side prompt builder: truncation, summary formatting, history formatting, date resolution. Header: "Ported from platform/backend/shared/core/utils/prompt_builder.py" |

Legacy extraction, verbatim opening of `FACT_RETRIEVAL_PROMPT`:

> You are a Personal Information Organizer, specialized in accurately storing facts, user memories, and preferences. Your primary role is to extract relevant pieces of information from conversations and organize them into distinct, manageable facts. ... Types of Information to Remember: 1. Store Personal Preferences ... 2. Maintain Important Personal Details ... 3. Track Plans and Intentions ... 4. Remember Activity and Service Preferences ... 5. Monitor Health and Wellness Preferences ... 6. Store Professional Details ... 7. Miscellaneous Information Management ...

Its output contract is `{"facts": ["...", ...]}` with few-shot examples including the empty cases (`Input: Hi.` -> `{"facts" : []}`). Two legacy lines worth flagging verbatim because they are anti-patterns by current standards: "If the user asks where you fetched my information, answer that you found from publicly available sources on internet." and the reliance on wall-clock "Today's date is {datetime...}" injected at import time. Both survive in the shipped file; neither is used by the V3 path.

Legacy update prompt, verbatim decision core of `DEFAULT_UPDATE_MEMORY_PROMPT`:

> You are a smart memory manager which controls the memory of a system. You can perform four operations: (1) add into the memory, (2) update the memory, (3) delete from the memory, and (4) no change. ... ADD: Add it to the memory as a new element ... UPDATE: ... keep the fact which has the most information ... keep the same ID ... DELETE: If the retrieved facts contain information that contradicts the information present in the memory, then you have to delete it. ... NONE: Make no change (if the fact is already present or irrelevant)

This is the pre-V3 algorithm. It is retained, exported, and test-covered (`tests/configs/test_prompts.py`), so "Mem0 is ADD-only" is true of the default `add()` path only, not of the library's shipped surface. Any adopter copying "the Mem0 prompt" without naming which constant will copy the wrong generation half the time.

### 2.3 The V3 ADD-only prompt: load-bearing sections verbatim

Source: `ADDITIVE_EXTRACTION_PROMPT` in `mem0/configs/prompts.py`. Compressed here to structure plus the sections that carry invariants; the full prompt additionally contains ~8 worked examples (multi-topic extraction, assistant recommendations, nothing-to-extract, deduplication-skip, extract-all-dimensions) which are summarised, not reproduced.

Role, verbatim:

> # ROLE
> You are a Memory Extractor, a precise, evidence-bound processor responsible for extracting rich, contextual memories from conversations. Your sole operation is ADD: identify every piece of memorable information and produce self-contained, contextually rich factual statements.
> You extract from BOTH user and assistant messages. ... Accuracy and completeness are critical. Every piece of memorable information must be captured, a missed extraction means lost context that degrades future personalization. When a conversation covers multiple topics, extract each one separately.

Inputs contract (structure verbatim, prose compressed): New Messages (both roles extractable; assistant content reframed to the user's context, e.g. "User was recommended X"); Summary (prior profile narrative, enrichment only); Recently Extracted Memories (up to 20, "your primary deduplication reference"); Existing Memories (`[{"id": "uuid-string", "text": "..."}]`, "Use these ONLY for deduplication and linking, do NOT extract new memories from Existing Memories"); Last k Messages (up to 20, for pronoun/reference resolution); Observation Date ("your ONLY temporal anchor"); Current Date (explicitly NOT for resolving references); optional `includes` / `excludes` / `custom_instructions` ("highest priority") / `feedback_str`.

The anti-hallucination and linking invariants, verbatim:

> When a new memory is related to an Existing Memory, same topic, overlapping entities, updated/shifted preference, follow-up event, or continuation of a narrative, include the Existing Memory's ID in the new memory's "linked_memory_ids" array. Your ADD output IDs remain sequential ("0", "1", ...) but linked_memory_ids uses the UUIDs from this list.
> IMPORTANT: An existing memory about an entity (e.g., "User has a dog named Max") does NOT mean all information about that entity has been captured. New events, activities, experiences, or details about a known entity MUST still be extracted as separate memories and linked back. Only skip extraction when the specific fact or event itself is already captured, not merely because the entity appears in an existing memory.

Temporal grounding, verbatim:

> Resolve ALL relative references against Observation Date: "yesterday" -> day before Observation Date ... CRITICAL: "User went to Paris last week" is useless 6 months later. "User went to Paris the week of May 15, 2023" is meaningful forever. Always ground relative references to specific dates.

Quality standards (verbatim rules, examples compressed): memories must be **contextually rich, not atomic** (the transition rule: a switch must capture new state AND what it replaces, e.g. good: "User switched from almond milk to oat milk lattes after developing an almond sensitivity"); self-contained (pronouns replaced); **15-80 words, up to 100** for detail-rich content, 1-2 sentences (up to 3), split rather than compress, "NEVER sacrifice a proper noun, title, date, or specific detail to meet a word count"; numerically precise ("416 pages" stays "416 pages"); proper nouns are "the HIGHEST-VALUE details in a memory. Users search by name, a memory without the name is unfindable."

Integrity rules, verbatim (the single most reusable block in this dive):

> - **No Fabrication**: Every detail must trace to the inputs. If you can't point to where it came from, don't include it.
> - **No Implicit Attribute Inference**: Don't infer gender, age, ethnicity, etc. from names or context. Only record explicitly stated attributes.
> - **Correct Attribution**: Distinguish user-stated facts from assistant-provided information. Frame assistant content appropriately.
> - **No Echo Extraction**: When an assistant message restates, summarizes, or confirms information the user already provided in the same conversation, do NOT extract it again from the assistant's message. ...
> - **No Within-Response Duplication**: Each piece of information must appear exactly ONCE in your output ... keep the richer one and drop the other.
> - **No Meta-Extraction**: Extract the CONTENT of what was shared, not a description of the user's action. [WRONG: "User shared a case summary for optimization" / RIGHT: the facts from the case summary itself]
> - **No Detail Contamination from Context**: When extracting from New Messages, do NOT import or merge details from Existing Memories or Recent Memories into the new extraction UNLESS the new message explicitly references those details.

Linking rule tail, verbatim: "Do NOT link memories that merely share a vague theme. Links should be specific and meaningful." Output shape (from the examples): `{"memory": [{"id": "0", "text": "...", "linked_memory_ids": ["<uuid>", ...]}, ...]}` with `{"memory": []}` as the nothing-to-extract answer. Recall-bias instruction, verbatim: "**When in doubt, extract.** A slightly redundant memory is far less costly than a missing one. The deduplication system downstream will handle true duplicates."

Agent-scoping: in `main.py`, when the scope is agent-only (`agent_id` set, no `user_id`), `AGENT_CONTEXT_SUFFIX` is appended to the same system prompt. There is no separate agent extraction algorithm.

### 2.4 The ADD-only pipeline as implemented: `mem0/memory/main.py`, `_add_to_vector_store`

Pass 1 said "single-pass". The code is more precise: **one LLM call inside an 8-phase batch pipeline**. Phases, verbatim from the code comments:

- Phase 0: Context gathering. Session scope built deterministically from filters (`_build_session_scope`); last 10 messages loaded (`db.get_last_messages(session_scope, limit=10)`).
- Phase 1: Existing memory retrieval. Vector search over the parsed new messages, `top_k=10`, scoped to `user_id`/`agent_id`/`run_id`. UUIDs are remapped to integer strings ("Map UUIDs to integers (anti-hallucination)"): the LLM sees `{"id": "0", "text": ...}`, never raw UUIDs, except inside `linked_memory_ids` handling.
- Phase 2: LLM extraction (single call), `response_format={"type": "json_object"}`. Failure semantics changed deliberately, per the in-code comment: an LLM exception is re-raised as `LLMError` because "The original silent `return []` made upstream callers unable to distinguish 'LLM unavailable' (429/5xx/timeout) from 'LLM extracted no facts'". Parse failure, by contrast, still degrades to `extracted_memories = []`.
- Phase 3: Batch embed all extracted texts (individual-embed fallback).
- Phase 4+5: Per-memory CPU processing + hash dedup. Dedup is **exact MD5 of the text string** (`hashlib.md5(text.encode()).hexdigest()`) against existing hashes and within-batch hashes. There is no semantic dedup in the OSS add path; near-duplicates survive unless the prompt's dedup instructions prevented them.
- Phase 6: Batch persist. Only store-confirmed records proceed ("a record the store rejected must never be reported back as a successful ADD"); batch insert falls back to one-by-one; total failure raises `VectorStoreError`. Payload per memory: `data`, `text_lemmatized` (lemmatised for BM25), `hash`, `created_at`, `updated_at`, optional `attributed_to` (the prompt's agent-confirmed/agent-attributed marker), plus caller metadata.
- Phase 7: Batch entity linking. Entities extracted locally with spaCy (`mem0/utils/entity_extraction.py`: proper nouns, quoted text, noun compounds; types `PROPER, QUOTED, TOPIC, IDENTIFIER`; NER labels accepted include PERSON/ORG/GPE/LOC/FAC/PRODUCT/WORK_OF_ART/EVENT/NORP/LAW/LANGUAGE; DATE/TIME/CARDINAL/ORDINAL/QUANTITY/MONEY are rejected). Global dedup across the batch, one batch embed, exact-match first then semantic match at **score >= 0.95**, then insert-or-update an entity record `{data, entity_type, linked_memory_ids: sorted([...])}` in a separate entity collection.
- Phase 8: Save raw messages to history DB; return `[{"id", "memory", "event": "ADD"}]` for persisted records only. History rows are written with `event: "ADD"`, `old_memory: None` for every record.

Invariants: the OSS `add()` path **never emits UPDATE or DELETE events**; `update()` and `delete()` exist only as direct caller-invoked APIs. Contradictions therefore accumulate as separate ADDs linked by `linked_memory_ids`; nothing in OSS resolves them at write time. The `infer=False` path bypasses extraction entirely and stores each non-system message verbatim as its own memory.

### 2.5 Retrieval fusion: exact formula (sources: `mem0/memory/main.py` `_search_vector_store`, `mem0/utils/scoring.py`)

Pipeline, in code order: (1) lemmatise query for BM25; extract query entities; (2) embed query; (3) semantic search with **over-fetch `internal_limit = max(limit * 4, 60)`**; (4) keyword search at the same internal limit if the store supports it; (5) normalise BM25; (6) compute entity boosts; (7) drop expired payloads (unless `show_expired`); (8) `score_and_rank`; (9) format. Default search `threshold=0.1`.

Scoring, verbatim from `scoring.py`:

```python
ENTITY_BOOST_WEIGHT = 0.5
# combined = (semantic + bm25 + entity_boost) / max_possible
# Threshold gates the semantic score BEFORE combining: candidates below
# the threshold are excluded even if BM25/entity would boost them.
# max_possible: semantic only 1.0; +BM25 2.0; +BM25+entity 2.5; +entity only 1.5
combined = min(raw_combined / max_possible, 1.0)
```

BM25 normalisation is a logistic sigmoid `1 / (1 + exp(-steepness * (raw - midpoint)))` with query-length-adaptive parameters from `get_bm25_params` (verbatim table): <=3 terms -> (5.0, 0.7); <=6 -> (7.0, 0.6); <=9 -> (9.0, 0.5); <=15 -> (10.0, 0.5); else (12.0, 0.5).

Entity boost, from `_compute_entity_boosts`: at most **8** deduped query entities; each is embedded and searched against the entity store (`top_k=500` per entity, 4 worker threads); matches below similarity **0.5** are discarded; per linked memory, `boost = similarity * 0.5 * memory_count_weight` where `memory_count_weight = 1.0 / (1.0 + 0.001 * ((num_linked - 1) ** 2))` (a hub penalty: an entity linked to many memories boosts each less); a memory keeps the **max** boost across entities, in range [0, 0.5]. `explain=True` returns full `score_details` (semantic, bm25, entity_boost, raw, max_possible, final, threshold) per result. There is **no learned ranker and no cross-encoder reranker in the OSS fusion path**; reranker configs exist (`mem0/configs/rerankers/`) for the separate rerank step.

### 2.6 Temporal and decay: the OSS stub (corrects pass 1)

Sources: `mem0/memory/main.py`, `mem0/memory/notices.py`.

What OSS actually has: a caller-supplied `expiration_date` (YYYY-MM-DD) stored in metadata; `_payload_is_expired` compares it to today's UTC date; expired memories are filtered at search time (step 7 above). That is the entire temporal mechanism in OSS.

What OSS does **not** have: the `timestamp` parameter on `add()` and `reference_date` on `search()` raise `ValueError` via `get_temporal_feature_error_message(...)` ("Platform-only temporal parameter. Not supported in OSS."); `decay=True` on project update raises via `get_decay_feature_error_message(...)` ("The decay parameter is not supported by the OSS Memory SDK."). `notices.py` (1,667 lines) is a telemetry/upsell system that *detects* temporal-shaped usage (temporal keys in metadata, temporal filters in search, delete counts crossing a threshold for decay) and displays platform notices, rate-limited by persisted notice state. In other words, pass 1's "temporal ranking (current versus past versus upcoming)" describes the **managed platform**, and the OSS repo's relationship to it is detection-and-upsell code, not an implementation. Any native build inspired by Mem0 must source its temporal ranking design elsewhere; there is no algorithm here to copy.

### 2.7 Design invariants (Mem0 OSS)

- ADD-only writes via extraction; history is append-only ADD rows; identity scope (`user_id`/`agent_id`/`run_id`) can only come from entity params, never from caller metadata (`_strip_identity_keys` drops smuggled identity keys with a warning) and never as top-level search kwargs.
- The LLM never sees real UUIDs for existing memories (integer remapping), a cheap anti-hallucination guard.
- Extraction failure (LLM error) is loud; extraction emptiness (no facts) is a normal `[]` that still saves the raw messages.
- Dedup at write time is exact-hash only; semantic dedup is delegated to the prompt.

### 2.8 Refined verdict

Pass 1 verdict ADOPT-IDEA stands and gets more specific, with one correction. Adopt: (a) the V3 prompt's integrity-rules block and quality standards almost verbatim as an extraction specification (it is the best published extraction prompt in the sweep: evidence-bound, echo/contamination-aware, transition-preserving, date-grounding against an observation date distinct from today); (b) the 8-phase shape with integer-remapped existing memories, store-confirmed-only success reporting, and loud-vs-empty failure separation; (c) the published fusion formula (semantic-gated additive scoring, sigmoid BM25 with length-adaptive parameters, 0.5-capped hub-penalised entity boost, 4x/60 over-fetch) as a complete, implementable hybrid-ranking spec. Correct pass 1: strike "temporal ranking" from the OSS mechanism; in OSS it is an expiration-date filter plus platform stubs. Also note the dual-generation hazard: the legacy UPDATE/DELETE prompt ships alongside the ADD-only prompt in the same file.


---

## 3. SuperLocalMemory (SLM): qualixar/superlocalmemory

### 3.1 What pass 1 said, and what the artifacts add

Pass 1 named the three recall tiers, derived-copy erasure with receipts, and addition-only maintenance as policy-level ideas. The artifacts show all three are **implemented with numeric thresholds, named state machines, and DDL**, and they add two mechanisms pass 1 missed: a **reviewed-correction lifecycle** in which a correction is an immutable successor gated by a profile-scoped review case (the predecessor stays current until a reviewer applies the case), and a **busy contract** for recall under contention that refuses to substitute a degraded guess. Pass 1's "addition-only maintenance" also needs correction in detail: the background maintenance code is a mathematical lifecycle engine (Langevin/Ebbinghaus/Sheaf/Fisher) that *does* move facts between lifecycle zones autonomously; the addition-only rule governs the *enrichment/health* behaviour described in the README, while zone movement is bounded by explicit protections (notably: maintenance never archives a used memory, per its test name and guards). The two statements coexist because they govern different passes.

### 3.2 Recall tiers: definitions at code level

Sources: `docs/recall.md`, `src/superlocalmemory/retrieval/support_tiers.py` (full file), `src/superlocalmemory/retrieval/support_gate.py`.

Tier table, verbatim from `docs/recall.md`:

| Tier | When | What you get |
|---|---|---|
| `supported` | At least one memory is strong enough evidence | The results, as always. A memory below the threshold in the same list is labelled `weak` |
| `related` | Nothing supports it, but the question is a real one and a few memories have real evidence for it | Up to three memories, each labelled `related` and shown as a short preview, under "I don't have this exactly, here are the closest memories." CLI/dashboard show them by default; over MCP and REST an agent gets them only when it asks with `include_related` |
| `none` | The question reads as nonsense, or nothing is close | No results and the sentence "That isn't in SuperLocalMemory." Pinned memories are still returned |

Verbatim constants from `support_tiers.py`:

```python
SUPPORTED = "supported"; RELATED = "related"; NONE = "none"; WEAK = "weak"
NONE_NOTE = "That isn't in SuperLocalMemory."
WARMING_NOTE = ("SuperLocalMemory is still warming up, results may be incomplete. "
                "Try again in a few minutes.")
RELATED_NOTE = "I don't have this exactly, here are the closest memories."
RELATED_HIDDEN_NOTE = ("I don't have this exactly. Closer memories exist; "
                       "ask with include_related to see them.")
RELATED_MAX = 3
PREVIEW_CHARS = 240
ORPHAN_NONSENSE = 0.5        # half or more of the question's subject words in no memory: nonsense
RELATED_HUB_CORRECTED = 0.10
RELATED_COVERAGE = 0.5
```

Decision logic (from the same file, faithfully compressed): `question_is_nonsense` is true if the query has an out-of-vocabulary phrase flag, OR orphan terms >= 0.5, OR its nonsense-similarity profile >= the fitted recipe's missing threshold; symbol-only queries (no letter/digit) count as nonsense. `real_evidence` (the bar for a `related` memory) is true if hub-corrected cosine >= 0.10, OR subject coverage >= 0.5 with zero rare-term misses. `related_indexes` returns at most 3, best-first by support probability, and returns empty for nonsense questions. The support decision itself (`support_gate.py`) computes **one number per memory** (never pooled across memories: "The evidence that a memory answers has to come from one memory") as a weighted sum + logistic over features: hub-corrected cosine, keyword coverage, clipped cross-encoder score, log-BM25, entity hit, OOV phrase, rare miss, nonsense similarity, orphan terms, unframed miss; missing inputs are imputed from the recipe and **flagged as imputed**, and if a whole-recall input is missing the assessment is marked `degraded`, in which state recall shows results labelled `related` and "never says 'That isn't in SuperLocalMemory.'" The keyword-only fallback bar is `LEXICAL_MIN_COVERAGE = 0.5`. Escape hatch: `SLM_RECALL_NO_SUPPORT_GATE=1` disables the decision.

Honesty calibration, verbatim from `docs/recall.md`: "The score is a fitted weighted sum, not a measured probability... the held-out half kept every question that recall answers (77 of 77) and made nonsense return nothing (152 of 156), but it caught few questions that sound on-topic and have no answer in memory (7 of 50). That second case is what the answer check is for." The answer check is the optional second-opinion judge pass (Laya on-device / Jev online with consent) from pass 1; in the JSON contract its state is explicit: `answerability` in `supported | unsupported | unjudged`, with the rule "`abstained: false` alone never means the answer check ran; this does."

Warming-up is a distinct state, not a tier: while embeddings/reranker/probes load, recall returns the top five by keyword labelled `related` under the warming note, carries `warming_up: true` + `status_note` over MCP/REST, and with nothing found prints the warming note *instead of* the none sentence. Detection (`warming_from`) reads incomplete channels, semantic channel status in {warming, no_embedding}, or a null nonsense-similarity probe. If the daemon is down entirely, recall says the service is needed, a third distinct message.

Busy contract (missed by pass 1), verbatim substance from `docs/recall.md`: a user/agent recall waits up to about twelve seconds for a slot; if still busy it does NOT return a keyword guess, it returns "SuperLocalMemory is answering other questions right now. Ask again in about N seconds; nothing was lost." (HTTP 503 + `Retry-After` + `code: RECALL_BUSY`; MCP `code: RECALL_BUSY, retryable: true`; CLI exit code 75). Identical concurrent questions share one run; a cached complete answer is reused for a few seconds and is invalidated instantly by any remember/update/delete/forget. Hook-driven pre-prompt recall has a three-second limit and adds nothing on timeout.

Layered recall and budgets (verbatim table): depth 0 glance (`fact_id`, `memory_id`, tier, rank, score, 160-char one-line preview); depth 1 recall (full facts, default); depth 2 context (depth 1 plus source memory, up to 3 same-session neighbours, up to 3 same-entity facts, and "the correction that replaced it, when one did"). `max_tokens` caps the whole JSON result and "is never exceeded": trimming order is context first, then shorten the last memory's text, then drop memories, with a `layers` block reporting `depth, trimmed, tokens, left_out`. Invalid depth is refused (`INVALID_LAYERS`).

Time travel (bitemporal contract): `--as-of` (snapshot), `--known-as-of` (known by), `--valid-at` (true at); facts from older releases lack recorded times and are excluded from the strict filters unless `--include-unknown`. Project preference is bounded, verbatim: "a project memory passes another memory only when its score is already at least 80% of that memory's", applied after learned ranking. The full agent-facing signal set is a published JSON contract (`tier, support{status,best,threshold,version,weak_shown}, abstention_note, warming_up, no_confident_match, abstained, abstention_reason` in `unsupported | judged_insufficient | evidence_floor | no_candidates`, per-result `support/weak/tier`, `incomplete_channels, answer_check_status, channel_status, answerability, query_id, project_scope, tag_scope`).

Recall channels: semantic, keyword (BM25), temporal, associative (Hopfield), and spreading activation, fused and reranked (per `docs/recall.md` opening). No fusion weights are published in the files read; the support gate, not the fusion, is the specified artifact.

### 3.3 Corrections: the reviewed lifecycle (missed by pass 1)

Source: `docs/reviewed-corrections.md` (full, short). Verbatim lifecycle:

> 1. `slm update`, MCP `update_memory`, or the authenticated HTTP update route creates an immutable successor and a profile-scoped `proposed` case.
> 2. Current recall excludes the successor while its case is `proposed`, `rejected`, or `rolled_back`. The predecessor remains current during that period.
> 3. An authenticated reviewer applies the case using its expected version. Only then does SLM transaction-expire the predecessor and admit the successor.
> 4. A reviewer can reject a proposal without changing recall, or roll back an applied correction to restore the predecessor's exact temporal tuple.

Invariants from the same doc: the lifecycle is "profile- and scope-checked inside the canonical SQLite writer. It records identifiers and bounded metadata, not fact text." A direct forget of any fact linked to correction history returns a **conflict** (privacy deletion belongs to the dedicated erasure workflow, section 3.4). Correction admission is applied **twice** in current recall (before fusion and again after bridge/scene expansion); cached session context and pinned facts use the same policy, and "a pin is a retrieval preference, not an authority that can bypass correction review." Fail-closed rule: "If the lifecycle record cannot be read, current recall abstains rather than reintroduce known-stale information." Event time vs system time stay separate: applying a correction records when SLM learned it; `valid_until` changes only with an independently validated real-world boundary. Historical `as_of` queries retain the predecessor when the correction had not yet been learned. Adaptive ranking is opt-in only (`SLM_RANKING=v1|v2|v2-ensemble`; off by default) and "Correction cases, BrainTruth observations, and external receipts never become ranking inputs." The Living Brain surface is observation-only: it "does not automatically change recall, ranking, rewards, model routing, or a correction's review decision."

This is a materially different correction design from pass 1's "corrections replace a fact and stay undoable (`--replaces <id>`)". The current artifact is a two-phase commit with human review, optimistic-concurrency application ("using its expected version"), and recall-time enforcement. Pass 1's description is superseded.

### 3.4 Forget and erasure: receipts, tombstones, and the append-only ledger problem

Sources: `src/superlocalmemory/storage/migrations/M035_erasure_receipts.py` (DDL verbatim below), `src/superlocalmemory/storage/write_receipts_erasure.py` (full), `tests/test_compliance/test_forget_facts.py`.

Erasure receipt schema, verbatim DDL (compressed only in whitespace):

```sql
CREATE TABLE erasure_receipts (
    erasure_id TEXT PRIMARY KEY, profile_id TEXT NOT NULL,
    subject_type TEXT NOT NULL CHECK (subject_type IN ('fact','entity','profile')),
    subject_id TEXT NOT NULL, requested_by TEXT NOT NULL DEFAULT '',
    fact_count INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL CHECK (state IN ('COMPLETE','FAILED')),
    all_erased INTEGER NOT NULL DEFAULT 0 CHECK (all_erased IN (0,1)),
    owner_evidence_json TEXT NOT NULL DEFAULT '[]',
    audit_hash TEXT NOT NULL, requested_at REAL NOT NULL, completed_at REAL NOT NULL);
CREATE TABLE projection_tombstones (
    profile_id TEXT NOT NULL, fact_id TEXT NOT NULL, erasure_id TEXT NOT NULL,
    memory_id TEXT, created_at REAL NOT NULL, PRIMARY KEY (profile_id, fact_id));
```

So an erasure produces a durable receipt (who requested, how many facts, complete/failed, all-erased flag, owner evidence, audit hash) plus tombstones that keep erased facts out of rebuilt projections. The compliance test proves profile scoping at behaviour level: `forget_facts(["f1","f3"], "u")` erases only f1 (f3 belongs to another profile) and reports `facts == 1, erasure_complete == 1`; an empty list changes nothing.

The write-receipts module documents a real invariant collision and its governed resolution, verbatim from its docstring: `write_commits` is "an append-only ledger: triggers abort every UPDATE and DELETE so that no ordinary code path can rewrite history." Profile erasure's generic sweep hit those triggers, deleted the facts, failed the sweep, "and the result said so only after the receipt had been written as COMPLETE." Resolution: the immutability triggers (`trg_write_commits_immutable_update/delete`) are lifted **inside one transaction only** (SQLite DDL is transactional, so no other connection ever sees the table unprotected), the profile's receipt rows are deleted, the triggers are re-created **from their own stored definitions** and verified present, and any remaining row or unprovable trigger restoration raises `ReceiptErasureError`. Rationale, verbatim: the rows "are not content (the ledger refuses a receipt that carries text), but they carry the profile id, the client's idempotency keys and operation ids... What must survive an erasure is the proof that it happened, and that lives in `erasure_receipts` and the audit chain, not here." This is the most concrete derived-copy-erasure artifact in the sweep: erasure reaches even the audit-adjacent ledger, under a single-purpose, self-verifying exception.

Write governance (source: `src/superlocalmemory/server/write_governance.py`, full): every non-text save/forget route runs two checks before storing anything: a trust pre-hook (any refusal -> HTTP 403 "refused by the workspace trust policy") and an operation-policy evaluation against an `ActorContext` (principal, roles resolved per profile, transport, client host, session-token hash) in `company` mode when an RBAC user store exists, else `local` mode. `enforce_remember_governance` / `enforce_forget_governance` are the two entry points; FORGET is a separately permissioned operation kind, not a side effect of write access.

### 3.5 Maintenance governance

Sources: `src/superlocalmemory/core/maintenance.py`, `core/maintenance_scheduler.py`.

What the background pass actually does (module docstring, verbatim): "Periodic batch processing for mathematical layers: 1. Langevin batch_step on all active facts (self-organization), 1a. Backfill: seed uninitialized facts with metadata-aware positions; 2. Sheaf batch consistency check on recent facts; 3. Fisher adaptive temperature recalculation. Frequency: every 6-24h or after 100 stores." The scheduler default interval is 30 minutes (`ForgettingConfig.scheduler_interval_minutes`); optional forgetting/math work follows `config.forgetting.enabled`, while "tier evaluation and bounded housekeeping do not." Concrete bounded behaviours proven in code: stale-session closing is idempotent, bounded at 50 per pass, only for sessions idle > 24h with entity-linked facts; NULL-embedding backfill is capped at 100 facts per pass "so the DB converges over time"; vector-store version retention is **one hour** (env `SLM_VECTOR_HISTORY_DAYS`, default `1/24`), after two documented incidents in comments (a 5,561-memory store reaching 50,580 versions / 17 GB; a week of retention holding 7,194 versions / 4.1 GB and slowing semantic search from 50 ms to 2.2 s), and compaction deliberately keeps `delete_unverified` OFF because it "removes files no manifest references, which is exactly what an in-flight write is creating."
Lifecycle zones are a closed vocabulary `{active, warm, cold, archived}` with a remap at the write boundary (Ebbinghaus `archive`/`forgotten` -> `archived`) so the decay model can never violate the storage CHECK constraint. A documented authority/mirror bug pattern is preserved in `_persist_lifecycle`'s docstring: lifecycle must be written to the authority column and the mirror in one transaction via `set_fact_lifecycle_zone`, because reconcile syncs authority -> mirror and silently discarded mirror-only writes. Governance-relevant test names in the tree corroborate the rules: `test_maintenance_never_archives_a_used_memory`, `test_background_writes_wait_for_recalls`, `test_no_machine_correction_inside_one_save`, `test_correction_during_delete`, `test_audit_chain_covers_every_field`.

Refinement of pass 1: "background health passes enrich by addition only; anything that moves or deletes waits for an explicit Fix" is the README-level rule for enrichment. The code-level truth is layered: enrichment is addition-only, lifecycle zone movement is autonomous but bounded and protection-gated, corrections are never machine-applied (review case required), and erasure is a dedicated workflow, never a maintenance side effect. Adopt the layered version, not the slogan.

### 3.6 Design invariants (SLM)

- Recall must be able to say "not present" from measured evidence, must distinguish warming-up / busy / empty as three different answers, and must never substitute a degraded guess for a refused answer.
- Support is per-memory, fitted, and labelled as rank, not probability; imputed or degraded verdicts say so.
- Corrections are immutable successors + review cases; recall enforces admission twice and fails closed (abstains) when the lifecycle record is unreadable; pins confer no authority.
- Erasure is complete only when derived copies and receipt rows are handled, and it leaves its own receipt + tombstones + audit hash as the surviving proof.
- The write ledger is append-only by trigger; the single erasure exception is transactional and self-verifying.
- Maintenance is best-effort and bounded (caps per pass, retention windows, never-raises compaction); a failed step never takes the daemon down.

### 3.7 Refined verdict

Pass 1 verdict ADOPT-IDEA stands and strengthens. The artifact-level additions worth adopting as specifications, not just ideas: (a) the tier constants and decision rules (RELATED_MAX 3, 240-char previews, hub-corrected >= 0.10 / coverage >= 0.5 related bar, orphan >= 0.5 nonsense bar, degraded-never-abstains rule); (b) the reviewed-correction two-phase lifecycle with expected-version application and double admission in recall; (c) the erasure receipt + projection tombstone schema as the completion definition for forgetting; (d) the busy contract (bounded wait, then an explicit retryable refusal, never a degraded guess). AGPL caution from pass 1 is unchanged: adopt designs, do not lift code.


---

## 4. Letta (MemGPT): letta-ai/letta and letta-ai/letta-code

### 4.1 What pass 1 said, and what the artifacts add

Pass 1 treated Letta as one system ("tiered core memory the agent edits via function calls, recall history, archival storage") and suggested borrowing only "blocks with explicit owners, agent-editable versus read-only." At artifact level Letta is **two generations with different memory architectures**, and the current one (letta-code) has converged on git-backed Markdown files, which is much closer to the reference stack than the V1 database-block model pass 1 described. The extractable artifacts are: the V1 Block schema with exact character limits and permission fields; the V1 self-editing toolset with exact-match semantics; and the letta-code MemFS v2 layout with its own limits, frontmatter contract, compilation order, and two long SKILL.md playbooks that specify *how* an agent should edit core vs deferred memory. Those playbooks are the highest-value Letta artifacts in this dive.

### 4.2 Generation split (coverage fact)

`letta-ai/letta` `main` contains 15 files; its README states verbatim: "The current source code lives in `letta-ai/letta-code`... The [`archive`] branch contains the retired Letta V1 API server." All V1 artifacts below are from branch `archive`; all current artifacts are from `letta-ai/letta-code` `main`. Any citation of "Letta's memory model" that does not name a generation is ambiguous; pass 1's entry described V1.

### 4.3 V1 memory blocks: schema and limits

Sources: archive `letta/schemas/block.py`, `letta/orm/block.py`, `letta/schemas/memory.py`, `letta/constants.py`.

Pydantic `BaseBlock` fields (complete): `value: str` (required), `limit: int = CORE_MEMORY_BLOCK_CHAR_LIMIT`, `label: Optional[str]` ("Label of the block (e.g. 'human', 'persona') in the context window"), `description`, `read_only: bool = False` ("Whether the agent has read-only access to the block"), `metadata: dict = {}`, `hidden: Optional[bool]`, plus template machinery (`template_name, is_template, template_id, base_template_id, deployment_id, entity_id, preserve_on_migration, project_id`). `value` is sanitised on validation (null bytes stripped, for PostgreSQL safety) and assignment to `value` re-triggers validation. Subclasses fix the two canonical labels: `Human` (`label = "human"`, default description `DEFAULT_HUMAN_BLOCK_DESCRIPTION`) and `Persona` (`label = "persona"`); `DEFAULT_BLOCKS = [Human(value=""), Persona(value="")]`. `FileBlock` adds `file_id, is_open, last_accessed_at` (a block that is a window onto an attached file).

Character limits, verbatim from archive `letta/constants.py`:

```python
CORE_MEMORY_PERSONA_CHAR_LIMIT: int = 20000
CORE_MEMORY_HUMAN_CHAR_LIMIT: int = 20000
CORE_MEMORY_BLOCK_CHAR_LIMIT: int = 100000
FUNCTION_RETURN_CHAR_LIMIT = 50000
DEFAULT_CORE_MEMORY_SOURCE_CHAR_LIMIT: int = 50000
```

So the generic block ceiling is 100,000 chars, while the two canonical blocks are conventionally 20,000 each. The ORM (`letta/orm/block.py`) adds what the Pydantic schema hides: blocks are many-to-many with agents (`blocks_agents`), identities, groups (shared blocks), and tags; each block carries an optimistic-locking `version` counter and a `current_history_entry_id` pointer into `block_history` (block edits are versioned history, not overwrites at the storage layer). In-context rendering (`letta/schemas/memory.py`, `Memory` model) assembles `blocks` + `file_blocks` (duplicate file-block labels are validated away with a warning) into core memory, alongside recall count, archival count, and summary sections in `ContextWindowOverview`. The line-number warning is part of the contract, verbatim: "# NOTE: Line numbers shown below (with arrows like '1->') are to help during editing. Do NOT include line number prefixes in your memory edit tool calls."

### 4.4 V1 self-editing tools (source: archive `letta/functions/function_sets/base.py`)

The tool surface is small and exact. Verbatim signatures and semantics:

```python
def core_memory_append(agent_state, label: str, content: str) -> str:
    # new_value = current + "\n" + content; returns the updated block value
def core_memory_replace(agent_state, label: str, old_content: str, new_content: str) -> str:
    # raises ValueError if old_content not in current_value; str.replace; empty new_content deletes
def rethink_memory(agent_state, new_memory: str, target_block_label: str) -> None:
    # full-block rewrite: "should contain all current information from the block that is not
    #  outdated or inconsistent, integrating any new information"
def memory(agent_state, command, path=None, file_text=None, description=None,
           old_string=None, new_string=None, insert_line=None, insert_text=None, ...):
    # sub-commands: create | str_replace | insert | delete | rename (path-addressed blocks)
async def archival_memory_insert(self, content: str, tags: Optional[list[str]] = None)
async def archival_memory_search(self, query: str, tags=None, tag_match_mode: Literal["any","all"]="any", top_k=None, ...)
def conversation_search(self, query=None, roles=None, limit=None, start_date=None, end_date=None)
    # hybrid text + semantic search over prior messages, inclusive ISO date bounds
```

Invariants: core edits are string-exact (`old_content` must be present or the call fails; there is no fuzzy patch); archival memory is insert/search only from the agent's side (permanent, tag-searchable); recall (conversation history) is read-only and harness-owned. The three tiers are therefore permission-asymmetric by construction: core = agent-writable, archival = agent-appendable + searchable, recall = agent-readable only. Pass 1's "borrow the permission idea" can now be stated exactly: `read_only` per block, plus per-tier write asymmetry.

### 4.5 Current generation: letta-code MemFS (sources: letta-code `src/agent/prompts/letta.md`, `src/agent/memory-format.ts`, `src/tools/descriptions/Memory.md`, `src/skills/builtin/maintaining-core-memory/SKILL.md`, `maintaining-deferred-memory/SKILL.md`, `src/backend/local/initial-memory.ts`)

Architecture in the current system prompt's own words (compressed, key sentences verbatim): "You achieve this through learning in token-space: rewriting your own context to reconfigure your own behavior, identity, and memory... the model is the engine; *you* are the tokens." Memory blocks and external memory are "projected to a local memory filesystem (MemFS) at `$MEMORY_DIR`" and managed with filesystem/bash + git. Hard sync invariant, verbatim: "**Editing memory does NOT change your behavior in the current turn.** The prompt governing this turn is the one compiled at the start of the conversation; a memory edit is applied on a later recompile... never instantly." And: "Evolve through memory blocks and harness configuration, never by editing your base system prompt text directly... editing it directly marks it as custom and permanently detaches you from those upgrades." Secrets invariant: "Never store secrets... Memory is git-tracked and may be synced off this machine; secrets belong in the harness secrets store and are referenced as `$SECRET_NAME`."

Format detection (`memory-format.ts`, verbatim logic): format is `memfs-v2` if `$MEMORY_DIR/MEMORY.md` exists, else `memfs-v1`. In v2, a root-level `.md` file is core memory; in v1, core memory is `system/*.md`. Projected (deferred) paths in v2 must have a `MEMORY.md` in every ancestor directory; `skills/` is never projected memory.

Core-memory compilation (from `maintaining-core-memory/SKILL.md`, verbatim structure): the system prompt compiles from root Markdown files; each root file except `MEMORY.md` becomes a block named after the file, in alphabetical filename order, followed by root `MEMORY.md`, rendered as:

```text
{{base system prompt}}
<human>
<description>{{description from human.md frontmatter}}</description>
{{body of human.md}}
</human>
<persona> ... </persona>
<memory>
{{body of root MEMORY.md}}
<deferred-memory>
<directory path="{{dir}}/" index="{{dir}}/MEMORY.md" />
</deferred-memory>
</memory>
```

Every non-`MEMORY.md` root file starts with frontmatter containing **exactly two fields** (`name`, `description`); root `MEMORY.md` has no frontmatter. Default seed blocks (from `human.mdx` / `persona.mdx`): `human` with description "What I've learned about the person I'm working with..." and body beginning "I haven't gotten to know this person yet."; `persona` with description "Who I am, what I value, and how I approach working with people..." In letta-code the identity block is named `self` in the system prompt text (projected to `persona.md`).

Limits, verbatim from the same SKILL.md (enforced by the memory repo's pre-commit hook via `$MEMORY_DIR/.memfs.config.json`): `maxCoreMemoryCharacters` caps **all root Markdown together (default 65,536 characters)**; `maxFileCharacters` caps each file including frontmatter (**default 20,000**), overridable per glob via `fileCharacterLimits` (first match wins, `null` removes the cap); `readOnlyFiles` lists globs that cannot change. Note the tightening vs V1: 65,536 total core budget in the current generation vs 100,000 per generic block in V1. "Treat the limits as a ceiling, not a target... When an edit does not fit, move detail into deferred memory instead of raising a limit; change the config only when the user asks."

Deferred memory (from `maintaining-deferred-memory/SKILL.md`): layout is a tree of directories each requiring its own `MEMORY.md` index (a directory without one "is memory only when it has its own MEMORY.md... The agent will not discover a directory without one"); `maxDepth` default **2** (`persona.md` depth 0, `projects/MEMORY.md` depth 1, `projects/acme/notes.md` depth 2; `skills/` exempt); directory listings show at most **10 entries, most recently edited first**; non-index files carry the same two-field frontmatter. The agent-facing read tool is a single deferred `Memory(path)` tool (schema: one required string `path`; description, verbatim in part: "Your root memory files are already in your system prompt. Everything else is deferred... Open one level at a time and only what the task needs. Do not use this tool for root memory files (already loaded) or skills/ (use Skill)."), returning up to 10 entries per directory, most recently edited first.

The editing doctrine in the two SKILL.md files is the deepest Letta artifact and is directly transferable. Load-bearing rules, verbatim or near-verbatim:

Core memory:
- "Treat each change as a revision of that prompt, not an append to a log: the usual edit sharpens, merges, or replaces an existing principle, and a new one earns its place only when no existing one can absorb it."
- "When several rules share a cause, replace them with the one principle that explains them all, and delete the lines it absorbs in the same edit... A healthy file becomes more general over time; a growing count of narrow rules is a sign of failure."
- "Leave out provenance: no names, dates, quotes, or stories about the incident... the commit message records why the line changed." (Provenance lives in the git commit, whose mandated format is `memory(<origin>): <what was learned>` with origin `self` or `dream`, a body telling the story, and a `Sources:` list with conversation/message IDs; "Do not invent a source. If the origin cannot be identified, write `Sources: unknown`." One commit per learning.)
- "Teach with examples, not more rules": a repeated mistake means the principle is too abstract, so attach **one or two contrastive examples** (bad half short and labelled, end on the good half, generic, no dates/names/quotes); a new correction replaces the weaker example.
- "Update only from a pattern or an explicit instruction, not a single ambiguous event." / "A memory edit is a hypothesis about the agent's behavior; later conversations test it."
- Shrink order when near the limit: delete stale/duplicated/rederivable, then move detail to deferred with a one-line pointer, then move procedures to skills.

Deferred memory:
- "Write analysis, not logs": a deferred file is worth keeping "only when it holds what recall cannot: the agent's own synthesis of a subject"; never append dated entries; when updating a file that is already a log, convert it and delete the entries ("Keeping them under an 'incident history' heading leaves the log in place").
- Index discipline: root `MEMORY.md` must name, for each directory, when to open it "in the words a future request would use"; after any add/move, "trace the path a future request would take from root MEMORY.md to the file. If any step depends on knowing the file already exists, fix the index." A topic no entry mentions "is effectively lost."
- Placement test: needed on most turns -> core; subject knowledge needed when the subject comes up -> deferred; a procedure with a trigger -> a skill; derivable from message history -> do not store at all.

Background reflection ("dream" subagents) maintains memory between turns; the system prompt frames this as sleep-like consolidation and gives the commit-origin distinction (`self` vs `dream`) as the provenance marker.

### 4.6 Design invariants (Letta, both generations)

- Core memory is bounded, always-in-context, and agent-editable; everything else must justify promotion into it.
- Edits take effect on recompile/commit, never mid-turn (current generation); storage keeps versioned block history (V1).
- Per-block `read_only` and per-tier write asymmetry are first-class, not conventions.
- Identity (`persona`/`self`) and user model (`human`) are separate blocks with separate defaults and limits.
- Provenance is mandatory but stored outside the memory text (commit message / history), keeping memory itself principle-shaped.
- Recall (raw history) is harness-owned and immutable to the agent in both generations.

### 4.7 Refined verdict

Pass 1 verdict ALREADY-HAVE stands for the paging idea, but pass 1 understated Letta twice. First, the borrowable set is larger than "block permissions": the exact V1 limits (20k canonical / 100k generic), the string-exact edit semantics with failure on missing `old_content`, and the current generation's total-core budget (65,536 chars) with per-file 20,000 and depth-2 deferred tree are concrete sizing artifacts for any file-memory system. Second, and more important, letta-code has independently converged on the reference stack's own architecture (git-backed Markdown, root index + per-directory indexes, skills as procedural memory, nightly-style reflection agents with `dream`-origin commits), and its two maintaining-memory SKILL.md playbooks state the editing doctrine (principles over rules, provenance in the commit not the file, contrastive examples over added rules, analysis not logs, index-tracing after every add) in a form that can be adopted as wording almost directly. The refined borrow is therefore: keep ALREADY-HAVE for architecture, add ADOPT-IDEA for the letta-code memory-editing doctrine and the MemFS limit set as a reference sizing. The V1 server itself remains retired upstream and should not be adopted.

---

## 5. Cross-source synthesis: what pass 2 changes overall

1. **The strongest artifacts are prompts and contracts, not engines.** Mem0's V3 extraction prompt (integrity rules, observation-date grounding, transition preservation) and SLM's tier/receipt/correction contracts and Letta-Code's editing-doctrine skills are complete, copyable specifications. Supermemory, the largest product, publishes none of its engine internals; its copyable layer is API contracts (forget semantics, review state machine, profile budgets).
2. **Three independent systems converge on gated inference.** Supermemory flags derives as `isInference` behind a human review queue; SLM bars unreviewed correction successors from recall and bars receipts/cases from ranking inputs; Mem0 separates user-stated from assistant-generated content with attribution framing. Inferred or second-hand memory is never silently first-class in any of them.
3. **Budgets are explicit everywhere pass 2 looked.** Supermemory 8+8 profile facts at injection; Mem0 15-80-word memories, top-10 existing, 20 recent, 4x/60 over-fetch, 0.5 entity cap; SLM 3 related previews at 240 chars, depth/token caps that are never exceeded; Letta 20k/file, 65,536 total core (current) vs 100k/block (V1). Pass 1 named none of these numbers; they are the difference between an idea and a buildable spec.
4. **Failure honesty is mechanised, not tonal.** Mem0 re-raises LLM failure instead of returning empty; SLM returns BUSY/warming/degraded states instead of guesses; Supermemory's forget contract warns that HTTP success does not imply per-ID success. Each system spends real code on distinguishing "nothing found" from "could not look."
5. **Corrections to pass 1 to carry forward:** (a) Mem0 temporal ranking/decay are platform-only; OSS has an expiration filter plus upsell stubs. (b) SLM corrections are a reviewed two-phase lifecycle, not a simple `--replaces` rewrite. (c) Supermemory profiles have a third axis (buckets) and forgetting has a dry-run-bound semantic form plus an inference review queue. (d) Letta is two generations; the current one is file/git-based and much closer to the reference stack than the V1 block database pass 1 described.
