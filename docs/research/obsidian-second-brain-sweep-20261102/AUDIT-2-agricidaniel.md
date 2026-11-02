# AUDIT 2 — AgriciDaniel/claude-obsidian

Program: Obsidian second-brain sweep, 2026-11-02. Auditor: research subagent (read-only).
Standard: InfinityBlade. Status of this audit: **PARTIAL-to-GREEN on the audit itself** —
the repo, README, schema, all core skills, both contracts, hooks, privacy/security docs and
templates were read in full from the live repo; the ~38 MB Python core was read selectively
(tree, egress surfaces, file sizes) rather than line by line, and that bound is stated here
rather than smoothed over. Nothing from the repo was executed, cloned-and-run, or installed.

---

## 1. Resolution (how the repo was found)

Hint given: `github.com/AgriciDaniel/c...`, "a wiki-ingest flow: drop text into inbox/,
review the generated plan, get linked notes out (likely AgriciDaniel/claude-obsidian)."

Three independent routes, all agreeing:

1. **Web search** ("AgriciDaniel claude-obsidian GitHub wiki ingest inbox") returned the
   GitHub repo as result 1 and the author's own v3 launch article
   (agricidaniel.com/blog/claude-obsidian-v3), whose install section names the exact flow in
   the hint: `/claude-obsidian:wiki`, `/claude-obsidian:wiki-ingest` on `inbox/`,
   `/claude-obsidian:wiki-query`.
2. **GitHub API, user repo listing** (`api.github.com/users/AgriciDaniel/repos`): contains
   exactly one matching repo, `AgriciDaniel/claude-obsidian`, described as "Self-organizing
   AI second brain for Obsidian + Claude Code. Drop any source and Claude reads, links, and
   files it into one connected knowledge graph of plain Markdown you own… Based on Karpathy's
   LLM Wiki pattern."
3. **GitHub API, repo metadata + recursive tree** confirmed identity, license and contents.

**Resolved: `AgriciDaniel/claude-obsidian` — https://github.com/AgriciDaniel/claude-obsidian**

Facts from the API (2026-11-02): MIT license; created 2026-04-07; 16,075 stars; 1,587 forks;
24 open issues; default branch `main`; current release v3.0.1 (2026-10-21, per CHANGELOG.md
and .claude-plugin/plugin.json); last push 2026-10-25. Lineage note: the project previously
lived as `AgriciDaniel/cosmicbrain` (v1.x docs still circulate under that name; same
inbox/.raw + /wiki design).

## 2. What was read (provenance)

From `raw.githubusercontent.com/AgriciDaniel/claude-obsidian/main/` and the GitHub API,
read as text only:

- `README.md` (full), `WIKI.md` (the vault schema, full), `PRIVACY.md` (full),
  `SECURITY.md` (grepped + key sections), `CHANGELOG.md` (head + secrets grep),
  `.claude-plugin/plugin.json`, repo JSON metadata, full recursive git tree (351 entries).
- Skills (full): `skills/wiki/SKILL.md`, `skills/wiki-ingest/SKILL.md`,
  `skills/wiki-query/SKILL.md`, `skills/wiki-lint/SKILL.md`, `skills/save/SKILL.md`,
  `skills/wiki-fold/SKILL.md`, `skills/wiki-retrieve/SKILL.md`; (head + structure)
  `skills/wiki-mode/SKILL.md`, `skills/autoresearch/SKILL.md`, `skills/think/SKILL.md`.
- Contracts (full): `skills/wiki/references/provenance.md`,
  `skills/wiki/references/operation-transactions.md`,
  `skills/wiki/references/frontmatter.md`.
- Agents: `agents/wiki-ingest.md` (head + contract); `agents/wiki-lint.md`,
  `agents/verifier.md` exist and are read-only by contract (README "Meet the crew" +
  verifier grep evidence).
- Hooks: `hooks/hooks.json`, `hooks/README.md` (full).
- Templates: `templates/vault/wiki/{hot,index,log,overview}.md` (full);
  `examples/sample-vault/` layout from the tree.
- Code as evidence (never executed): file sizes from the tree (`claude_obsidian/transaction.py`
  195,146 bytes; `lint_engine.py` 85,520; `capture.py` 85,077; `ledgers.py` 55,407);
  egress grep over `claude_obsidian/ollama.py`, `transport_probe.py`, `url_safety.py`,
  `scripts/retrieve.py`, `scripts/rerank.py` (rerank defaults to `http://127.0.0.1:11434`,
  localhost Ollama).

Local comparison sources read: `workspace/research_notes/midna-trader-formation-20261029/MEMORY-SYSTEM.md`
(design of our existing system), the heading structure of `~/MEMORY.md`, the file list of
`~/workspace/midna-book/` and of `~/workspace/midna-book/memory/` (CONFIRMATION-TALLY.md,
LESSONS.md, OPEN-THREADS.md, RULINGS.md, STATE.md, STRATEGIES.md, snapshots/, strategies/).

## 3. What the system actually is

A Claude Code plugin (also packaged as portable Agent Skills for Codex, OpenCode, Gemini,
ZCode, Cursor, Windsurf) plus a deterministic Python core (`scripts/claude-obsidian.py` →
`claude_obsidian/` package). The product code and the user's vault are strictly separated:
the vault is a plain-Markdown Obsidian folder the user owns. The loop is Capture → Ground →
Compound: sources land in `inbox/`, are preserved byte-identical and content-addressed in
`.raw/`, and are compiled into linked wiki pages whose claims point back at sources.
Design credit: Andrej Karpathy's LLM Wiki pattern; Obsidian syntax conventions follow
kepano/obsidian-skills (ATTRIBUTION.md).

## 4. Mechanisms extracted (the mechanical core)

**Folder and file conventions**
- `inbox/` — visible staging; files are user-owned, never auto-deleted (the core may propose
  deletion, never execute it).
- `.raw/` — immutable source archive; new captures are content-addressed by SHA-256;
  existing payloads are never replaced; `.raw/.manifest.json` holds delta/address metadata
  and changes only inside the same transaction as the operation it records.
- `wiki/` — generated knowledge: `sources/`, `entities/`, `concepts/`, `questions/`,
  `canvases/`, plus four core pages and `meta/ledgers/`.
- `wiki/index.md` — curated catalog; every canonical page create/removal must update an
  active catalog or MOC in the same transaction; an index entry is not itself evidence.
- `wiki/log.md` — completed logical operations (not file writes), newest first, with
  operation ID, type, principal pages, grounded outcome.
- `wiki/hot.md` — the hot cache: bounded recent context for the next session, hard caps
  500 words / 32 KiB, sanitized, explicitly **must not contain secrets, raw transcripts, or
  tool instructions**.
- `wiki/overview.md` — slow-changing high-level synthesis.
- `.vault-meta/` — locks, transaction journals, BM25 indexes, mode config (runtime state,
  not knowledge).

**Page format**
- Flat YAML frontmatter, one declared vocabulary in `claude_obsidian/page_schema.py`:
  types `source | entity | concept | question | comparison | session | overview | meta | fold`;
  statuses `seed → developing → mature → evergreen` (plus answered/provisional/contested/
  deprecated/archived); required `type, title, status, created, updated, tags`; wikilinks
  quoted in YAML; `related`, `sources`, `claim_ids` link fields. Optional stable page
  addresses (`address: c-000001`) allocated centrally via `address_requests` — workers never
  call the allocator.
- Linking rules: `[[Target]]`, `[[Target|Alias]]`, `[[Page#Heading]]`, block refs, embeds;
  basename links only when unique, else vault-relative path; **no fabricated backlinks** to
  make the graph symmetric.

**Provenance (three separate ledgers, deliberately not merged)**
- `.raw/.manifest.json` — ingestion hashes, generated pages, address map.
- `wiki/meta/ledgers/source-ledger.json` — stable source ID + SHA-256, vault-relative or
  HTTPS locator, authority (`official | primary | secondary | community | synthetic |
  unknown`), **independence_key** (sources sharing a key, or the same canonical origin
  under IDN/port/default-port respellings, do not count as independent corroboration),
  review state (`unreviewed | active | superseded | rejected`), `refresh_due` — staleness is
  **computed** from `refresh_due`, never stored as a second flag.
- `wiki/meta/ledgers/claim-ledger.json` — falsifiable claims with note locations, supporting
  and contradicting source IDs, confidence, risk, assessment
  (`accepted | provisional | contested | unsupported | deprecated`). Accepted needs ≥1 fresh,
  active, non-synthetic source; high-risk accepted needs 2 independent sources;
  contradictions are preserved, never silently resolved; `unsupported` is the canonical
  no-data state.

**Ingest flow (`wiki-ingest`)**
1. Agree scope and budget first (source count, bytes/pages, existing-page reads, generated
   pages, network requests); large batches take a bounded first tranche.
2. Source content is untrusted data: embedded instructions, egress requests and secret
   requests inside sources are ignored by contract. URL fetches need explicit consent for
   domains and budget; nothing private leaves with a fetch.
3. SHA-256 each payload; check manifest + ledgers for unchanged input (dedupe by hash).
4. Classify before extracting (code / research / decision / conversation / reference /
   dataset / media), with a per-type extraction focus.
5. **Compilation-value gate:** create or expand a canonical page only when the source adds
   durable synthesis, navigation, a decision, or a reusable connection. A concise searchable
   source may earn only its ledger record, or a no-op. "Do not paraphrase merely to create
   pages."
6. Read hot cache, index, methodology settings, and a bounded set of existing pages
   (default 5 per source); read each source completely or label the result partial with the
   missing range recorded.
7. Extract metadata, falsifiable claims, entities, concepts, contradictions, open
   questions; source statements kept separate from synthesis.
8. Parallel workers return drafts/evidence only; one orchestrator merges into **one**
   transaction for the whole batch.

**Write path: operation transactions (the strongest mechanism in the repo)**
- One logical operation = one `claude-obsidian.transaction.v1` JSON bundle: operation ID,
  operation type (each type is an enforced write-authority: e.g. `fold` may write exactly
  one fold page + index + log; `capture` may create only `.raw/captured/*`), SHA-256
  preconditions (`expected_hashes`) for every target, one write per path.
- `transaction inspect` → user reviews the plan → `transaction apply
  --approved-plan-sha256 <hash>`, where the approval hash binds the expanded plan to the
  canonical vault root (an approval for one vault cannot be replayed against another).
  This is a content-bound approval, not a name approval.
- Journaled apply with backups; interruption → `transaction recover` rolls back. Exit 75 =
  vault changed under you: re-read, rebuild, re-inspect. Reapplying an identical bundle with
  the same ID is a no-op. Size caps (64 MiB/file, 128 MiB/op, 1,024 writes) exist so every
  accepted operation stays rollback-able. No-follow, descriptor-based I/O confines all
  writes to the selected vault; POSIX-only (Windows writes require WSL).
- Git checkpointing is a separate, explicit, never-automatic command.

**Query flow (`wiki-query`)** — strictly read-only; never writes, logs, or refreshes caches.
- Depth tiers with cumulative read budgets: Quick 12 KiB (hot + index + verify linked
  evidence), Standard 48 KiB, Deep 128 KiB (broader candidates, competing pages, gaps
  stated). Budgets are context budgets, not silent-truncation permission.
- Retrieval chain: prebuilt contextual BM25 index (read-only use) → fallback to index,
  sub-indexes, plain text search, with the fallback named in the answer.
- Answers are claim-state aware: accepted stated as established, provisional labelled
  tentative, contested presented with both positions, unsupported labelled unsupported and
  never filled from model memory; stale (past `refresh_due`) evidence flagged. Citations are
  specific wikilinks `[[Page#Heading]]` plus source locators. Keeping an answer is a separate
  explicit `save` operation.

**Save flow (`save`)** — only user-selected conversation content, never automatic, never a
whole transcript by default; one transaction coupling note + index + log entry + refreshed
hot cache; conversation assertions are classified synthetic/provisional and can never by
themselves make a claim `accepted`.

**Lint (`wiki-lint`)** — deterministic, read-only health check (an 85 KB parser engine, not
an LLM opinion): dead/ambiguous links, orphan pages, duplicate basenames, required-frontmatter
gaps, empty sections, stale index entries, ledger contract violations. Reports facts only;
repairs are a separate reviewed transaction; lint never auto-fixes and never claims semantic
or contradiction analysis it did not perform.

**Fold (`wiki-fold`)** — extractive rollup of `wiki/log.md`: batch size 2^k (default k=4,
no partial batches, no fold-of-folds, children never modified). The fold ID is derived
deterministically from its inputs (`fold-k{K}-from-{date}-to-{date}-n{count}`), so re-running
is a structural no-op. Pre-write checks: exact entry count, frontmatter↔table bijection
(every child entry has exactly one `child_key` and one table row), numeric traceability
(every number verifiable in its source entry), a citation for every outcome and theme,
"ambiguous in source" preferred over invention. A fold adds no evidence and never upgrades
a claim assessment.

**Retrieval (`wiki-retrieve`)** — paragraph chunking with page-level contextual prefixes,
stdlib BM25 index under `.vault-meta/`, optional cosine rerank via local Ollama
(`nomic-embed-text-v2-moe`, localhost only by default). Integrity rules: hash-matched
chunks/pages/index or the record is rejected; a missing/corrupt index exits 10 with a
rebuild command rather than fabricating matches; an empty index is an honest no-result.
A labelled-query bench (`bench --queries FILE`) measures recall/MRR including negative
cases, read-only, never silently rebuilding. The Anthropic-API prefix profile exists but
requires explicit consent + `--allow-egress` + an API key, and the docs state plainly that
it sends page bodies off-machine.

**Session rituals (hooks)** — `hooks/hooks.json` registers two Claude Code command hooks:
SessionStart (startup|resume|clear|compact|fork) and Stop, both invoking the Python core
with a 5-second timeout. SessionStart is **silent by default**; only with
`CLAUDE_OBSIDIAN_SESSION_CONTEXT=1` does it emit a bounded, sanitized `wiki/hot.md` block
into session context (with an exact-path guard so a hostile project config cannot redirect
injection to another vault). Stop emits only an aggregate recovery-needed systemMessage —
no operation IDs, paths, or note content. Hooks never write knowledge, update the hot
cache, stage files, commit, or call the network (hooks/README.md, PRIVACY.md).

**Modes (`wiki-mode`)** — filing methodology for *new* pages only: Generic (type folders),
LYT (atomic notes + MOCs), PARA (Projects/Areas/Resources/Archives), Zettelkasten (stable
IDs, dense links). Switching never moves existing notes; config lives in
`.vault-meta/mode.json`; a corrupt mode file fails closed rather than silently defaulting.

**Autoresearch** — bounded web research under an explicit contract (topic, exclusions,
egress consent, approved domains, max rounds/searches/fetches/pages, stop condition;
defaults 3 rounds × 5 fetches × 15 pages). Output is a cited dossier; merging into
canonical pages is a separate reviewed transaction.

**Capability states** — `configured` (prerequisites present) vs `verified` (a declared
behavioral check passed); a schema/self-check cannot promote a capability to verified, and
an unverifiable capability stays `configured` with the reason tracked (WIKI.md, Safety).

**Input limits (honest ones)** — local files captured content-addressed; images/PDF/EPUB
are metadata + hash only, **no built-in text extraction**; web pages and YouTube are
prepared as an approved plan needing a separate runner; OCR needs an external tool.

## 5. Classification against what already exists here

Our existing architecture (per MEMORY-SYSTEM.md and the live tree): `~/MEMORY.md` +
`~/memory/` daily logs with claim-id/quote/source-message provenance + people/groups pages
(Tier 0, runtime-owned); `~/workspace/midna-book/` registers (Tier 1 CONTEXT-SNAPSHOT.md;
Tier 2 STATE.md, RULINGS.md, OPEN-THREADS.md; LESSONS.md; STRATEGIES.md + per-strategy
records; dated snapshot archives), all maintained by the daily audit job and governed by
InfinityBlade proof rules and the 2026-10-31 memory governance rulings.

| Mechanism | Verdict | Basis |
|---|---|---|
| Hot cache (`hot.md`) | ALREADY-HAVE | CONTEXT-SNAPSHOT.md is the same layer, with dated archives and a monthly recovery drill the vault lacks. |
| Index catalog / overview / operation log | ALREADY-HAVE | People/groups INDEX.md, alignment synthesis, daily logs + JOURNAL.md cover all three roles. |
| Save-on-explicit-request only | ALREADY-HAVE | Our memory write boundary + governance rulings already forbid automatic/parallel capture. |
| Claim/source provenance with citations | ALREADY-HAVE (different substrate) | Daily-log claim/quote/source-id format + `muse.memory_explain` + the 2026-10-13 provenance-grade recall standard. |
| Contradictions preserved, never silently resolved | ALREADY-HAVE | Dated-conflict practice (MEMORY-SYSTEM §8.2) and supersession in MEMORY.md. |
| Content-bound plan approval (inspect → approval hash → apply) | ALREADY-HAVE | InfinityBlade discipline 18: `~/workspace/tools/approvals.py` binds approval to action, target identity and content sha256. Their transaction bundle is the same idea, vault-scoped. |
| Deterministic lint of the store | ALREADY-HAVE | `memory_store_check.py`, `memory_reconcile.py`, done_check and the twice-daily inspections; ours checks index presence/budgets/frontmatter rather than link graphs. |
| Configured vs verified capability states | ALREADY-HAVE | Proof-before-green is the same rule stated as doctrine. |
| Bounded, consent-first research loop (autoresearch) | ALREADY-HAVE | Our research programs run under scope/budget contracts; dossier-then-merge matches our readback-verification practice. |
| **Content-addressed immutable source archive (`.raw/` + SHA-256 manifest, create-only)** | **CANDIDATE** | Our research_notes keep sources ad hoc; nothing hash-pins a source at capture or forbids overwrite. Adopting the rule for research source drops (hash at capture, changed source = new capture, manifest per program folder) hardens every later citation. Cheap, native, no code import. |
| **Compilation-value gate at ingest** | **CANDIDATE** | The explicit rule "a source may earn only a ledger record or a no-op; never paraphrase merely to create pages" is a crisp anti-bloat gate our research-note ingest does not state. One paragraph in the ingest convention; prevents note sprawl in research_notes. |
| **Claim ledger with independence keys + computed `refresh_due`** | **CANDIDATE** | Our claim provenance is per-log-entry; a small machine-readable ledger for research/forecast claims, with assessment states, an independence key (syndicated copies do not corroborate) and staleness computed from a due date, is genuinely new and matches the forecast estate's ledger-before-display standard. Scope it to research claims, never user facts (MEMORY.md stays canonical there). |
| **Extractive log fold with deterministic ID + bijection checks** | **CANDIDATE** | Our governed compaction (2026-10-31 ruling) is exact-duplicate based with receipts. A fold mechanism (input-derived ID, one row per child, numeric traceability, children immutable, no fold-of-folds) is a stronger rollup for daily-log and snapshot-archive growth if volume ever demands it. Adopt the checks, not the tool. |
| **Tiered query read budgets (Quick/Standard/Deep)** | **CANDIDATE (minor)** | Explicit KiB read budgets with stop rules and a named fallback chain is a tidy ritual for research-note questions; our memory_search has result limits but no stated read-budget tiers. Low cost, modest gain. |
| **Labelled-query retrieval bench** | **CANDIDATE (minor)** | A fixed local query set with expected hits + negative cases, run read-only, would grade our own memory retrieval quality instead of assuming it. Only useful against stores we control (research_notes, midna-book), not the platform search. |
| Stable page addresses (`c-000001`) | SKIP | Solves Obsidian rename/basename fragility. Our files are path-addressed and claims already carry permanent ids; a second addressing layer adds bookkeeping without a failure it prevents. |
| Methodology modes (LYT/PARA/Zettelkasten switching) | SKIP | Our layout is fixed by law (MEMORY.md + midna-book registers). A switchable filing methodology is a fork risk against the single source of truth, with no unmet need. |
| Obsidian surface (Canvas, Bases, graph view, CSS) | SKIP | We do not run Obsidian; the terminal is the user's surface. Nothing to adopt. |
| Local BM25 + Ollama rerank stack | SKIP | Platform `muse.memory_search` already provides retrieval over the memory store; a second local embedding index would duplicate it and add a ~1 GB model dependency. (The bench idea above is the only piece worth keeping.) |
| Plugin install + SessionStart/Stop hooks | SKIP (do not install) | See Risks. The bounded-sanitized-context-injection *idea* is already how our runtime injects standing context; the third-party hook itself must not run in our host. |
| Per-operation Git checkpoints | SKIP | The backup seal system already versions the workspace with proven restores; per-operation commits would flood history. |
| `think` 10-stage loop | SKIP | A generic reasoning ritual; InfinityBlade review-mode order already governs our reasoning gates. |
| defuddle / external web-capture runner | SKIP | Our browser tooling already captures pages under our own rules. |

## 6. Risks, stated honestly

1. **Hooks execute third-party code in the host.** Installing the plugin registers
   SessionStart and Stop command hooks that run the repo's Python core on every Claude Code
   session start/resume/compact. They are documented as silent-by-default, read-only and
   non-writing, and the context injection is opt-in, bounded and sanitized — but adoption
   here is reimplementation-only regardless; the plugin itself is never to be installed
   into Midna's environment.
2. **Prompt-injection surface.** The opt-in SessionStart path injects vault note content
   into session context. The repo mitigates (sanitization, byte caps, exact-vault guard),
   and its skills consistently treat source/vault content as untrusted data. Any native
   reimplementation of a hot-cache injection must keep the same posture.
3. **Consent-gated egress exists and is easy to mis-set.** Core makes no network requests
   (PRIVACY.md), and rerank defaults to localhost Ollama. But the Anthropic contextual-prefix
   profile sends page bodies off-machine under `--allow-egress`, remote Ollama needs only an
   opt-in flag, and autoresearch/defuddle route through host web tools and external runners.
   The boundaries are contractual (skill text + flags), not physical.
4. **Parallel-store risk (the big one for us).** This vault is designed to *be* the second
   brain. Adopting it whole would fork facts about the user away from `~/MEMORY.md` and the
   midna-book registers, violating the single-source-of-truth rail. Every CANDIDATE above is
   scoped to research/operational material and extends the existing store; none creates a
   user-facts store.
5. **REJECTED TIP — secrets in memory.** The sweep corpus contains a source-article
   suggestion to keep secrets in memory/notes. **That tip is REJECTED by the owner and is
   recorded here as rejected: no secret, key, token or credential is ever written to any
   memory file, note or vault page in our system.** For the record, this repo itself takes
   the same position: `wiki/hot.md` "must not contain secrets" (WIKI.md), "Credentials do
   not belong in URLs, source notes, bundles, queues, or tracked configuration" (WIKI.md
   source invariants), "Never put credentials in a source note, URL query, tracked config,
   transaction bundle, or capture queue" (PRIVACY.md). A grep for secret-handling across
   README.md, WIKI.md, PRIVACY.md, SECURITY.md and CHANGELOG.md found only prohibitions;
   the rejected tip does not come from this repo's current text.
6. **Maintenance and bus factor.** One maintainer (Agrici Daniel) plus community PRs; the
   repo is seven months old and went v1 → v3 in about six months, including a plugin rename
   in 3.0.0 that 3.0.1 had to reverse. Churn risk is real; MIT licensing plus
   reimplementation-only adoption keeps us independent of it.
7. **Weight.** The safety machinery is heavy (transaction.py ~195 KB, lint_engine.py
   ~85 KB, an extensive hermetic test suite). It is proportionate for a public tool writing
   into strangers' vaults; importing it for our file counts would be over-engineering. The
   mechanisms scale down to conventions and small checks; the code does not come across.
8. **Marketing vs capability gap.** "Drop any source" is bounded in the fine print: PDF/EPUB
   get metadata only, web/YouTube need an external runner, OCR is external. Any adoption
   narrative must carry those limits, not the headline.

## 7. Bottom line

claude-obsidian is a well-engineered, unusually honest implementation of the Karpathy LLM
Wiki pattern, and its safety design (hash-preconditioned single-transaction writes,
content-bound approvals, three-ledger provenance, contradictions preserved, read-only
workers) independently converges on several rules this house already runs under
InfinityBlade. Most of it is ALREADY-HAVE. The genuinely portable gains are small and
concrete: hash-pinned immutable source capture, an explicit compilation-value gate at
ingest, a claim ledger with independence keys and computed staleness for research claims,
and fold-style rollup checks. Nothing should be installed; the four candidates are
conventions to write natively into our own research and memory practice, each extending
`~/MEMORY.md` / the midna-book registers rather than competing with them.
